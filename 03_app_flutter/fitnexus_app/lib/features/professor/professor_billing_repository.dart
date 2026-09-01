import 'package:supabase_flutter/supabase_flutter.dart';

import '../auth/auth_service.dart';

class BillingProviderDescriptor {
  const BillingProviderDescriptor({
    required this.code,
    required this.displayName,
    required this.selectionState,
    required this.capabilities,
    required this.evidenceVersion,
  });

  final String code;
  final String displayName;
  final String selectionState;
  final Map<String, bool> capabilities;
  final String evidenceVersion;

  bool capability(String key) => capabilities[key] ?? false;

  factory BillingProviderDescriptor.fromJson(Map<String, dynamic> json) {
    final Map<String, dynamic> raw = _map(json['capabilities']);
    return BillingProviderDescriptor(
      code: json['code'] as String? ?? 'unknown',
      displayName: json['display_name'] as String? ?? 'Provedor',
      selectionState: json['selection_state'] as String? ?? 'unknown',
      capabilities: raw.map(
        (String key, dynamic value) => MapEntry<String, bool>(key, value == true),
      ),
      evidenceVersion: json['evidence_version'] as String? ?? 'unknown',
    );
  }
}

class BillingPricingReadiness {
  const BillingPricingReadiness({
    required this.state,
    required this.mode,
    required this.decisionVersion,
    required this.annualStrategy,
    required this.activePriceCount,
    required this.expectedPriceCount,
    required this.complete,
  });

  final String state;
  final String mode;
  final String decisionVersion;
  final String annualStrategy;
  final int activePriceCount;
  final int expectedPriceCount;
  final bool complete;

  bool get promoted =>
      state == 'PROMOTED' &&
      complete &&
      expectedPriceCount > 0 &&
      activePriceCount == expectedPriceCount;

  bool get experiment => mode == 'EXPERIMENT';

  factory BillingPricingReadiness.fromJson(Map<String, dynamic> json) {
    final int active = (json['active_price_count'] as num?)?.toInt() ?? 0;
    final int expected = (json['expected_price_count'] as num?)?.toInt() ?? 0;
    return BillingPricingReadiness(
      state: json['state'] as String? ?? 'UNFROZEN',
      mode: json['mode'] as String? ?? 'NONE',
      decisionVersion: json['decision_version'] as String? ?? '',
      annualStrategy: json['annual_strategy'] as String? ?? '',
      activePriceCount: active,
      expectedPriceCount: expected,
      complete: json['complete'] as bool? ?? (expected > 0 && active == expected),
    );
  }
}

class BillingCredentialReadiness {
  const BillingCredentialReadiness({
    required this.state,
    required this.secretExposedToFlutter,
  });

  final String state;
  final bool secretExposedToFlutter;

  bool get configured => state == 'EXTERNAL_AUTHORITY_CONFIGURED';

  factory BillingCredentialReadiness.fromJson(Map<String, dynamic> json) {
    return BillingCredentialReadiness(
      state: json['state'] as String? ?? 'PENDING_EXTERNAL_CREDENTIAL_BOUNDARY',
      secretExposedToFlutter: json['secret_exposed_to_flutter'] as bool? ?? false,
    );
  }
}

class BillingCheckoutReadiness {
  const BillingCheckoutReadiness({
    required this.ready,
    required this.serverAmountAuthority,
    required this.clientAmountAllowed,
    required this.silentProviderFallback,
    required this.pricingDecisionBound,
  });

  final bool ready;
  final bool serverAmountAuthority;
  final bool clientAmountAllowed;
  final bool silentProviderFallback;
  final bool pricingDecisionBound;

  factory BillingCheckoutReadiness.fromJson(Map<String, dynamic> json) {
    return BillingCheckoutReadiness(
      ready: json['ready'] as bool? ?? false,
      serverAmountAuthority: json['server_amount_authority'] as bool? ?? true,
      clientAmountAllowed: json['client_amount_allowed'] as bool? ?? false,
      silentProviderFallback: json['silent_provider_fallback'] as bool? ?? false,
      pricingDecisionBound: json['pricing_decision_bound'] as bool? ?? false,
    );
  }
}

class BillingProviderReadiness {
  const BillingProviderReadiness({
    required this.organizationId,
    required this.scope,
    required this.provider,
    required this.pricing,
    required this.credentials,
    required this.checkout,
    required this.subscriptionProviderBound,
    required this.generatedAt,
  });

  final String organizationId;
  final String scope;
  final BillingProviderDescriptor provider;
  final BillingPricingReadiness pricing;
  final BillingCredentialReadiness credentials;
  final BillingCheckoutReadiness checkout;
  final bool subscriptionProviderBound;
  final DateTime generatedAt;

  bool get externalBoundaryPending =>
      !credentials.configured || !pricing.promoted || !checkout.ready;

  factory BillingProviderReadiness.fromJson(Map<String, dynamic> json) {
    return BillingProviderReadiness(
      organizationId: json['organization_id'] as String? ?? '',
      scope: json['scope'] as String? ?? 'BR_V1',
      provider: BillingProviderDescriptor.fromJson(_map(json['provider'])),
      pricing: BillingPricingReadiness.fromJson(_map(json['pricing'])),
      credentials: BillingCredentialReadiness.fromJson(_map(json['credentials'])),
      checkout: BillingCheckoutReadiness.fromJson(_map(json['checkout'])),
      subscriptionProviderBound: json['subscription_provider_bound'] as bool? ?? false,
      generatedAt: DateTime.tryParse(json['generated_at']?.toString() ?? '') ??
          DateTime.now(),
    );
  }
}

class PricingCatalogOffer {
  const PricingCatalogOffer({
    required this.planCode,
    required this.displayName,
    required this.studentLimit,
    required this.memberLimit,
    required this.monthlyAmountMinor,
    required this.annualAmountMinor,
    required this.annualSavingsMinor,
    required this.annualMonthlyEquivalentMinor,
    required this.pricingDecisionVersion,
  });

  final String planCode;
  final String displayName;
  final int studentLimit;
  final int memberLimit;
  final int monthlyAmountMinor;
  final int annualAmountMinor;
  final int annualSavingsMinor;
  final int annualMonthlyEquivalentMinor;
  final String pricingDecisionVersion;

  factory PricingCatalogOffer.fromJson(Map<String, dynamic> json) {
    int number(String key) => (json[key] as num?)?.toInt() ?? 0;
    return PricingCatalogOffer(
      planCode: json['plan_code'] as String? ?? 'unknown',
      displayName: json['display_name'] as String? ?? 'FitNexus',
      studentLimit: number('student_limit'),
      memberLimit: number('member_limit'),
      monthlyAmountMinor: number('monthly_amount_minor'),
      annualAmountMinor: number('annual_amount_minor'),
      annualSavingsMinor: number('annual_savings_minor'),
      annualMonthlyEquivalentMinor: number('annual_monthly_equivalent_minor'),
      pricingDecisionVersion: json['pricing_decision_version'] as String? ?? '',
    );
  }
}

class PricingCatalogSnapshot {
  const PricingCatalogSnapshot({
    required this.currency,
    required this.decisionVersion,
    required this.mode,
    required this.annualStrategy,
    required this.offers,
    required this.generatedAt,
  });

  final String currency;
  final String decisionVersion;
  final String mode;
  final String annualStrategy;
  final List<PricingCatalogOffer> offers;
  final DateTime generatedAt;

  bool get experiment => mode == 'EXPERIMENT';

  factory PricingCatalogSnapshot.fromJson(Map<String, dynamic> json) {
    final List<dynamic> rawOffers = json['offers'] is List
        ? json['offers'] as List<dynamic>
        : const <dynamic>[];
    return PricingCatalogSnapshot(
      currency: json['currency'] as String? ?? 'BRL',
      decisionVersion: json['decision_version'] as String? ?? '',
      mode: json['mode'] as String? ?? 'NONE',
      annualStrategy: json['annual_strategy'] as String? ?? '',
      offers: rawOffers
          .map((dynamic value) => PricingCatalogOffer.fromJson(_map(value)))
          .toList(growable: false),
      generatedAt: DateTime.tryParse(json['generated_at']?.toString() ?? '') ??
          DateTime.now(),
    );
  }
}

class HostedBillingCheckout {
  const HostedBillingCheckout({
    required this.checkoutIntentId,
    required this.providerCode,
    required this.planCode,
    required this.billingInterval,
    required this.checkoutUrl,
    required this.environment,
  });

  final String checkoutIntentId;
  final String providerCode;
  final String planCode;
  final String billingInterval;
  final Uri checkoutUrl;
  final String environment;

  factory HostedBillingCheckout.fromJson(Map<String, dynamic> json) {
    final String rawUrl = json['checkout_url'] as String? ?? '';
    final Uri? uri = Uri.tryParse(rawUrl);
    if (uri == null || uri.scheme != 'https' || uri.host.isEmpty) {
      throw StateError('BILLING_CHECKOUT_URL_INVALID');
    }
    final String intentId = json['checkout_intent_id'] as String? ?? '';
    final String provider = json['provider_code'] as String? ?? '';
    if (intentId.isEmpty || provider.isEmpty) {
      throw StateError('BILLING_CHECKOUT_RESPONSE_INVALID');
    }
    return HostedBillingCheckout(
      checkoutIntentId: intentId,
      providerCode: provider,
      planCode: json['plan_code'] as String? ?? '',
      billingInterval: json['billing_interval'] as String? ?? '',
      checkoutUrl: uri,
      environment: json['environment'] as String? ?? 'unknown',
    );
  }
}

class ProfessorBillingRepository {
  ProfessorBillingRepository._();

  static final ProfessorBillingRepository instance =
      ProfessorBillingRepository._();

  SupabaseClient get _client => Supabase.instance.client;

  Future<BillingProviderReadiness> fetchReadiness({String scope = 'BR_V1'}) async {
    final String organizationId =
        await AuthService.instance.ensureProfessorOrganization();
    final dynamic response = await _client.rpc(
      'get_billing_provider_readiness',
      params: <String, dynamic>{
        'p_organization_id': organizationId,
        'p_scope': scope,
      },
    );
    return BillingProviderReadiness.fromJson(_map(response));
  }

  Future<PricingCatalogSnapshot> fetchPricingCatalog({String currency = 'BRL'}) async {
    final dynamic response = await _client.rpc(
      'get_pricing_catalog',
      params: <String, dynamic>{'p_currency': currency},
    );
    return PricingCatalogSnapshot.fromJson(_map(response));
  }

  Future<HostedBillingCheckout> createHostedCheckout({
    required String planCode,
    required String billingInterval,
  }) async {
    if (!const <String>{'solo', 'pro', 'studio'}.contains(planCode)) {
      throw ArgumentError.value(planCode, 'planCode', 'INVALID_PLAN_CODE');
    }
    if (!const <String>{'month', 'year'}.contains(billingInterval)) {
      throw ArgumentError.value(
        billingInterval,
        'billingInterval',
        'INVALID_BILLING_INTERVAL',
      );
    }

    final String organizationId =
        await AuthService.instance.ensureProfessorOrganization();
    final FunctionResponse response = await _client.functions.invoke(
      'billing-checkout',
      body: <String, dynamic>{
        'organization_id': organizationId,
        'plan_code': planCode,
        'billing_interval': billingInterval,
      },
    );
    final Map<String, dynamic> data = _map(response.data);
    if (data['ok'] != true) {
      throw StateError(data['error']?.toString() ?? 'BILLING_CHECKOUT_FAILED');
    }
    return HostedBillingCheckout.fromJson(data);
  }
}

Map<String, dynamic> _map(dynamic value) {
  if (value is Map<String, dynamic>) return value;
  if (value is Map) return Map<String, dynamic>.from(value);
  return <String, dynamic>{};
}
