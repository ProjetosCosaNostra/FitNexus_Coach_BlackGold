import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:in_app_purchase/in_app_purchase.dart';
import 'package:in_app_purchase_android/in_app_purchase_android.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../auth/auth_service.dart';

/// Canonical Google Play subscription contract.
///
/// Product IDs are immutable once created in Play Console. Keep these values
/// stable and create two auto-renewing base plans for every product:
/// - monthly
/// - annual
class PlayBillingContract {
  const PlayBillingContract._();

  static const String soloProductId = 'fitnexus_solo';
  static const String proProductId = 'fitnexus_pro';
  static const String studioProductId = 'fitnexus_studio';

  static const String monthlyBasePlanId = 'monthly';
  static const String annualBasePlanId = 'annual';

  static const Set<String> productIds = <String>{
    soloProductId,
    proProductId,
    studioProductId,
  };

  static String productIdForPlan(String planCode) {
    switch (planCode) {
      case 'solo':
        return soloProductId;
      case 'pro':
        return proProductId;
      case 'studio':
        return studioProductId;
      default:
        throw ArgumentError.value(planCode, 'planCode', 'INVALID_PLAY_PLAN_CODE');
    }
  }

  static String basePlanIdForInterval(String interval) {
    switch (interval) {
      case 'month':
        return monthlyBasePlanId;
      case 'year':
        return annualBasePlanId;
      default:
        throw ArgumentError.value(interval, 'interval', 'INVALID_PLAY_BILLING_INTERVAL');
    }
  }
}

class PlaySubscriptionOffer {
  const PlaySubscriptionOffer({
    required this.planCode,
    required this.billingInterval,
    required this.productId,
    required this.basePlanId,
    required this.details,
  });

  final String planCode;
  final String billingInterval;
  final String productId;
  final String basePlanId;
  final GooglePlayProductDetails details;

  String get displayPrice => details.price;
  String? get offerToken => details.offerToken;
}

enum PlayBillingEventType {
  pending,
  verified,
  restored,
  canceled,
  error,
}

class PlayBillingEvent {
  const PlayBillingEvent({
    required this.type,
    required this.message,
    this.productId,
  });

  final PlayBillingEventType type;
  final String message;
  final String? productId;
}

class PlayBillingService {
  PlayBillingService._();

  static final PlayBillingService instance = PlayBillingService._();

  final InAppPurchase _iap = InAppPurchase.instance;
  final StreamController<PlayBillingEvent> _events =
      StreamController<PlayBillingEvent>.broadcast();

  StreamSubscription<List<PurchaseDetails>>? _purchaseSubscription;
  Map<String, PlaySubscriptionOffer> _offers =
      <String, PlaySubscriptionOffer>{};
  bool _initialized = false;

  Stream<PlayBillingEvent> get events => _events.stream;

  bool get isAndroidPlayRuntime =>
      !kIsWeb && defaultTargetPlatform == TargetPlatform.android;

  Future<void> initialize() async {
    if (_initialized || !isAndroidPlayRuntime) return;
    _purchaseSubscription = _iap.purchaseStream.listen(
      _handlePurchaseUpdates,
      onError: (Object error, StackTrace stackTrace) {
        _events.add(
          PlayBillingEvent(
            type: PlayBillingEventType.error,
            message: 'PLAY_PURCHASE_STREAM_ERROR:$error',
          ),
        );
      },
    );
    _initialized = true;
  }

  Future<Map<String, PlaySubscriptionOffer>> loadOffers() async {
    if (!isAndroidPlayRuntime) return <String, PlaySubscriptionOffer>{};
    await initialize();
    if (!await _iap.isAvailable()) {
      throw StateError('GOOGLE_PLAY_BILLING_UNAVAILABLE');
    }

    final ProductDetailsResponse response =
        await _iap.queryProductDetails(PlayBillingContract.productIds);
    if (response.error != null) {
      throw StateError('GOOGLE_PLAY_PRODUCT_QUERY_FAILED:${response.error!.code}');
    }
    if (response.notFoundIDs.isNotEmpty) {
      throw StateError(
        'GOOGLE_PLAY_PRODUCTS_NOT_CONFIGURED:${response.notFoundIDs.join(',')}',
      );
    }

    final Map<String, PlaySubscriptionOffer> resolved =
        <String, PlaySubscriptionOffer>{};
    for (final ProductDetails product in response.productDetails) {
      if (product is! GooglePlayProductDetails) continue;
      final int? subscriptionIndex = product.subscriptionIndex;
      final offers = product.productDetails.subscriptionOfferDetails;
      if (subscriptionIndex == null ||
          offers == null ||
          subscriptionIndex < 0 ||
          subscriptionIndex >= offers.length) {
        continue;
      }

      final String basePlanId = offers[subscriptionIndex].basePlanId;
      final String? planCode = _planCodeForProductId(product.id);
      final String? interval = _intervalForBasePlanId(basePlanId);
      if (planCode == null || interval == null) continue;
      resolved['$planCode:$interval'] = PlaySubscriptionOffer(
        planCode: planCode,
        billingInterval: interval,
        productId: product.id,
        basePlanId: basePlanId,
        details: product,
      );
    }

    for (final String planCode in const <String>['solo', 'pro', 'studio']) {
      for (final String interval in const <String>['month', 'year']) {
        if (!resolved.containsKey('$planCode:$interval')) {
          throw StateError('GOOGLE_PLAY_BASE_PLAN_NOT_CONFIGURED:$planCode:$interval');
        }
      }
    }

    _offers = Map<String, PlaySubscriptionOffer>.unmodifiable(resolved);
    return _offers;
  }

  PlaySubscriptionOffer? offerFor(String planCode, String interval) =>
      _offers['$planCode:$interval'];

  Future<void> buy({
    required String planCode,
    required String billingInterval,
  }) async {
    if (!isAndroidPlayRuntime) {
      throw StateError('GOOGLE_PLAY_BILLING_ANDROID_ONLY');
    }
    if (_offers.isEmpty) await loadOffers();

    final PlaySubscriptionOffer? offer = offerFor(planCode, billingInterval);
    if (offer == null) {
      throw StateError('GOOGLE_PLAY_OFFER_NOT_FOUND:$planCode:$billingInterval');
    }

    final User? user = Supabase.instance.client.auth.currentUser;
    if (user == null) throw StateError('AUTH_REQUIRED');
    await AuthService.instance.ensureProfessorOrganization();

    final GooglePlayPurchaseParam purchaseParam = GooglePlayPurchaseParam(
      productDetails: offer.details,
      applicationUserName: user.id,
      offerToken: offer.offerToken,
    );

    final bool launched = await _iap.buyNonConsumable(
      purchaseParam: purchaseParam,
    );
    if (!launched) throw StateError('GOOGLE_PLAY_BILLING_FLOW_NOT_LAUNCHED');
  }

  Future<void> restore() async {
    if (!isAndroidPlayRuntime) return;
    await initialize();
    final User? user = Supabase.instance.client.auth.currentUser;
    await _iap.restorePurchases(applicationUserName: user?.id);
  }

  Future<void> _handlePurchaseUpdates(
    List<PurchaseDetails> purchases,
  ) async {
    for (final PurchaseDetails purchase in purchases) {
      switch (purchase.status) {
        case PurchaseStatus.pending:
          _events.add(
            PlayBillingEvent(
              type: PlayBillingEventType.pending,
              productId: purchase.productID,
              message: 'Pagamento pendente no Google Play.',
            ),
          );
          break;
        case PurchaseStatus.canceled:
          _events.add(
            PlayBillingEvent(
              type: PlayBillingEventType.canceled,
              productId: purchase.productID,
              message: 'Compra cancelada no Google Play.',
            ),
          );
          break;
        case PurchaseStatus.error:
          _events.add(
            PlayBillingEvent(
              type: PlayBillingEventType.error,
              productId: purchase.productID,
              message: purchase.error?.message ?? 'Falha na compra do Google Play.',
            ),
          );
          break;
        case PurchaseStatus.purchased:
        case PurchaseStatus.restored:
          final bool verified = await _verifyWithServer(purchase);
          if (!verified) {
            _events.add(
              PlayBillingEvent(
                type: PlayBillingEventType.error,
                productId: purchase.productID,
                message: 'A compra existe no Google Play, mas a validação do servidor ainda não foi concluída.',
              ),
            );
            // Do not acknowledge an unverified purchase. Google Play can
            // redeliver it and FitNexus can verify again later.
            continue;
          }

          if (purchase.pendingCompletePurchase) {
            await _iap.completePurchase(purchase);
          }
          _events.add(
            PlayBillingEvent(
              type: purchase.status == PurchaseStatus.restored
                  ? PlayBillingEventType.restored
                  : PlayBillingEventType.verified,
              productId: purchase.productID,
              message: purchase.status == PurchaseStatus.restored
                  ? 'Assinatura do Google Play restaurada e validada.'
                  : 'Assinatura confirmada pelo Google Play.',
            ),
          );
          break;
      }
    }
  }

  Future<bool> _verifyWithServer(PurchaseDetails purchase) async {
    final String purchaseToken =
        purchase.verificationData.serverVerificationData.trim();
    if (purchaseToken.isEmpty) return false;

    try {
      final String organizationId =
          await AuthService.instance.ensureProfessorOrganization();
      final FunctionResponse response =
          await Supabase.instance.client.functions.invoke(
        'play-billing-verify',
        body: <String, dynamic>{
          'organization_id': organizationId,
          'package_name': 'br.com.lafamigliaplayworks.fitnexuscoach',
          'product_id': purchase.productID,
          'purchase_token': purchaseToken,
          'purchase_id': purchase.purchaseID,
        },
      );
      final dynamic data = response.data;
      return data is Map && data['ok'] == true && data['entitlement_active'] == true;
    } catch (_) {
      return false;
    }
  }

  String? _planCodeForProductId(String productId) {
    switch (productId) {
      case PlayBillingContract.soloProductId:
        return 'solo';
      case PlayBillingContract.proProductId:
        return 'pro';
      case PlayBillingContract.studioProductId:
        return 'studio';
      default:
        return null;
    }
  }

  String? _intervalForBasePlanId(String basePlanId) {
    switch (basePlanId) {
      case PlayBillingContract.monthlyBasePlanId:
        return 'month';
      case PlayBillingContract.annualBasePlanId:
        return 'year';
      default:
        return null;
    }
  }

  Future<void> disposeForTests() async {
    await _purchaseSubscription?.cancel();
    _purchaseSubscription = null;
    _initialized = false;
    _offers = <String, PlaySubscriptionOffer>{};
  }
}
