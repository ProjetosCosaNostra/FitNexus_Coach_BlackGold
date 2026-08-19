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
    required this.activePriceCount,
  });

  final String state;
  final int activePriceCount;

  bool get promoted => state == 'PROMOTED' && activePriceCount > 0;

  factory BillingPricingReadiness.fromJson(Map<String, dynamic> json) {
    return BillingPricingReadiness(
      state: json['state'] as String? ?? 'UNFROZEN',
      activePriceCount: (json['active_price_count'] as num?)?.toInt() ?? 0,
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
  });

  final bool ready;
  final bool serverAmountAuthority;
  final bool clientAmountAllowed;
  final bool silentProviderFallback;

  factory BillingCheckoutReadiness.fromJson(Map<String, dynamic> json) {
    return BillingCheckoutReadiness(
      ready: json['ready'] as bool? ?? false,
      serverAmountAuthority: json['server_amount_authority'] as bool? ?? true,
      clientAmountAllowed: json['client_amount_allowed'] as bool? ?? false,
      silentProviderFallback: json['silent_provider_fallback'] as bool? ?? false,
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
}

Map<String, dynamic> _map(dynamic value) {
  if (value is Map<String, dynamic>) return value;
  if (value is Map) return Map<String, dynamic>.from(value);
  return <String, dynamic>{};
}
