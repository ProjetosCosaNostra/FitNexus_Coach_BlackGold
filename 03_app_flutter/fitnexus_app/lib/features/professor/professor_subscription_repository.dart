import 'package:supabase_flutter/supabase_flutter.dart';

import '../auth/auth_service.dart';

class SubscriptionPlanInfo {
  const SubscriptionPlanInfo({
    required this.code,
    required this.displayName,
    required this.studentLimit,
    required this.memberLimit,
    required this.featureFlags,
  });

  final String code;
  final String displayName;
  final int studentLimit;
  final int memberLimit;
  final Map<String, bool> featureFlags;

  factory SubscriptionPlanInfo.fromJson(Map<String, dynamic> json) {
    final Map<String, dynamic> rawFeatures = _map(json['feature_flags']);
    return SubscriptionPlanInfo(
      code: json['code'] as String? ?? 'unknown',
      displayName: json['display_name'] as String? ?? 'FitNexus',
      studentLimit: (json['student_limit'] as num?)?.toInt() ?? 0,
      memberLimit: (json['member_limit'] as num?)?.toInt() ?? 0,
      featureFlags: rawFeatures.map(
        (String key, dynamic value) => MapEntry<String, bool>(key, value == true),
      ),
    );
  }
}

class SubscriptionStateInfo {
  const SubscriptionStateInfo({
    required this.status,
    required this.effectiveStatus,
    required this.writeEnabled,
    required this.trialSecondsRemaining,
    required this.cancelAtPeriodEnd,
    required this.providerConnected,
    required this.authoritySource,
    required this.authorityVersion,
    this.trialStartedAt,
    this.trialEndsAt,
    this.currentPeriodStart,
    this.currentPeriodEnd,
  });

  final String status;
  final String effectiveStatus;
  final bool writeEnabled;
  final int trialSecondsRemaining;
  final bool cancelAtPeriodEnd;
  final bool providerConnected;
  final String authoritySource;
  final int authorityVersion;
  final DateTime? trialStartedAt;
  final DateTime? trialEndsAt;
  final DateTime? currentPeriodStart;
  final DateTime? currentPeriodEnd;

  int get trialDaysRemaining {
    if (trialSecondsRemaining <= 0) return 0;
    return (trialSecondsRemaining / 86400).ceil();
  }

  factory SubscriptionStateInfo.fromJson(Map<String, dynamic> json) {
    return SubscriptionStateInfo(
      status: json['status'] as String? ?? 'unknown',
      effectiveStatus: json['effective_status'] as String? ?? 'unknown',
      writeEnabled: json['write_enabled'] as bool? ?? false,
      trialSecondsRemaining:
          (json['trial_seconds_remaining'] as num?)?.toInt() ?? 0,
      cancelAtPeriodEnd: json['cancel_at_period_end'] as bool? ?? false,
      providerConnected: json['provider_connected'] as bool? ?? false,
      authoritySource: json['authority_source'] as String? ?? 'unknown',
      authorityVersion: (json['authority_version'] as num?)?.toInt() ?? 0,
      trialStartedAt: _date(json['trial_started_at']),
      trialEndsAt: _date(json['trial_ends_at']),
      currentPeriodStart: _date(json['current_period_start']),
      currentPeriodEnd: _date(json['current_period_end']),
    );
  }
}

class SubscriptionUsageInfo {
  const SubscriptionUsageInfo({
    required this.students,
    required this.studentLimit,
    required this.studentRemaining,
    required this.members,
    required this.memberLimit,
    required this.memberRemaining,
  });

  final int students;
  final int studentLimit;
  final int studentRemaining;
  final int members;
  final int memberLimit;
  final int memberRemaining;

  double get studentRatio =>
      studentLimit <= 0 ? 0 : (students / studentLimit).clamp(0, 1).toDouble();
  double get memberRatio =>
      memberLimit <= 0 ? 0 : (members / memberLimit).clamp(0, 1).toDouble();

  factory SubscriptionUsageInfo.fromJson(Map<String, dynamic> json) {
    int number(String key) => (json[key] as num?)?.toInt() ?? 0;
    return SubscriptionUsageInfo(
      students: number('students'),
      studentLimit: number('student_limit'),
      studentRemaining: number('student_remaining'),
      members: number('members'),
      memberLimit: number('member_limit'),
      memberRemaining: number('member_remaining'),
    );
  }
}

class SubscriptionEntitlementSnapshot {
  const SubscriptionEntitlementSnapshot({
    required this.organizationId,
    required this.plan,
    required this.subscription,
    required this.usage,
    required this.features,
    required this.pricingState,
    required this.providerBound,
    required this.guardrails,
    required this.generatedAt,
  });

  final String organizationId;
  final SubscriptionPlanInfo plan;
  final SubscriptionStateInfo subscription;
  final SubscriptionUsageInfo usage;
  final Map<String, bool> features;
  final String pricingState;
  final bool providerBound;
  final Map<String, bool> guardrails;
  final DateTime generatedAt;

  bool featureEnabled(String key) => features[key] ?? false;

  factory SubscriptionEntitlementSnapshot.fromJson(Map<String, dynamic> json) {
    final Map<String, dynamic> pricing = _map(json['pricing']);
    final Map<String, dynamic> featureMap = _map(json['features']);
    final Map<String, dynamic> guardrailMap = _map(json['guardrails']);
    return SubscriptionEntitlementSnapshot(
      organizationId: json['organization_id'] as String? ?? '',
      plan: SubscriptionPlanInfo.fromJson(_map(json['plan'])),
      subscription: SubscriptionStateInfo.fromJson(_map(json['subscription'])),
      usage: SubscriptionUsageInfo.fromJson(_map(json['usage'])),
      features: featureMap.map(
        (String key, dynamic value) => MapEntry<String, bool>(key, value == true),
      ),
      pricingState: pricing['state'] as String? ?? 'UNFROZEN',
      providerBound: pricing['provider_bound'] as bool? ?? false,
      guardrails: guardrailMap.map(
        (String key, dynamic value) => MapEntry<String, bool>(key, value == true),
      ),
      generatedAt: _date(json['generated_at']) ?? DateTime.now(),
    );
  }
}

class SubscriptionPlanCatalogItem {
  const SubscriptionPlanCatalogItem({
    required this.code,
    required this.displayName,
    required this.studentLimit,
    required this.memberLimit,
    required this.trialDays,
  });

  final String code;
  final String displayName;
  final int studentLimit;
  final int memberLimit;
  final int trialDays;

  factory SubscriptionPlanCatalogItem.fromJson(Map<String, dynamic> json) {
    return SubscriptionPlanCatalogItem(
      code: json['code'] as String? ?? 'unknown',
      displayName: json['display_name'] as String? ?? 'FitNexus',
      studentLimit: (json['student_limit'] as num?)?.toInt() ?? 0,
      memberLimit: (json['member_limit'] as num?)?.toInt() ?? 0,
      trialDays: (json['trial_days'] as num?)?.toInt() ?? 0,
    );
  }
}

class ProfessorSubscriptionRepository {
  ProfessorSubscriptionRepository._();

  static final ProfessorSubscriptionRepository instance =
      ProfessorSubscriptionRepository._();

  SupabaseClient get _client => Supabase.instance.client;

  Future<SubscriptionEntitlementSnapshot> fetchSnapshot() async {
    final String organizationId =
        await AuthService.instance.ensureProfessorOrganization();
    final dynamic response = await _client.rpc(
      'get_subscription_entitlement_snapshot',
      params: <String, dynamic>{'p_organization_id': organizationId},
    );
    return SubscriptionEntitlementSnapshot.fromJson(_map(response));
  }

  Future<List<SubscriptionPlanCatalogItem>> fetchCatalog() async {
    final List<dynamic> rows = await _client
        .from('subscription_plans')
        .select('code,display_name,student_limit,member_limit,trial_days,sort_order')
        .eq('lifecycle', 'active')
        .order('sort_order');
    return rows
        .map(
          (dynamic row) =>
              SubscriptionPlanCatalogItem.fromJson(_map(row)),
        )
        .toList(growable: false);
  }
}

Map<String, dynamic> _map(dynamic value) {
  if (value is Map<String, dynamic>) return value;
  if (value is Map) return Map<String, dynamic>.from(value);
  return <String, dynamic>{};
}

DateTime? _date(dynamic value) {
  if (value == null) return null;
  return DateTime.tryParse(value.toString());
}
