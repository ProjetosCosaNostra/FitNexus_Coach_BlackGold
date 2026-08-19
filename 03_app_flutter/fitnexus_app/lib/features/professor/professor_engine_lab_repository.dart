import 'package:supabase_flutter/supabase_flutter.dart';

import '../auth/auth_service.dart';

class DecisionEngineDescriptor {
  const DecisionEngineDescriptor({
    required this.version,
    required this.role,
    required this.lifecycle,
    required this.description,
  });

  final String version;
  final String role;
  final String lifecycle;
  final String description;

  factory DecisionEngineDescriptor.fromJson(Map<String, dynamic> json) {
    return DecisionEngineDescriptor(
      version: json['engine_version'] as String? ?? 'unknown',
      role: json['role'] as String? ?? 'unknown',
      lifecycle: json['lifecycle'] as String? ?? 'unknown',
      description: json['description'] as String? ?? '',
    );
  }
}

class DecisionEngineEvaluationSnapshot {
  const DecisionEngineEvaluationSnapshot({
    required this.evaluationRunId,
    required this.challengerVersion,
    required this.status,
    required this.caseCount,
    required this.resolvedCount,
    required this.championAlignmentRate,
    required this.challengerAlignmentRate,
    required this.alignmentUplift,
    required this.recommendationChanges,
    required this.riskChanges,
    required this.safetyDowngrades,
    required this.unsafeActionabilityConflicts,
    required this.createdAt,
  });

  final String evaluationRunId;
  final String challengerVersion;
  final String status;
  final int caseCount;
  final int resolvedCount;
  final double championAlignmentRate;
  final double challengerAlignmentRate;
  final double alignmentUplift;
  final int recommendationChanges;
  final int riskChanges;
  final int safetyDowngrades;
  final int unsafeActionabilityConflicts;
  final DateTime createdAt;

  bool get safetyPassed =>
      safetyDowngrades == 0 && unsafeActionabilityConflicts == 0;

  factory DecisionEngineEvaluationSnapshot.fromJson(
    Map<String, dynamic> json,
  ) {
    int integer(String key) => (json[key] as num?)?.toInt() ?? 0;
    double decimal(String key) => (json[key] as num?)?.toDouble() ?? 0;
    return DecisionEngineEvaluationSnapshot(
      evaluationRunId: json['evaluation_run_id'] as String? ?? '',
      challengerVersion: json['challenger_version'] as String? ?? 'unknown',
      status: json['status'] as String? ?? 'unknown',
      caseCount: integer('case_count'),
      resolvedCount: integer('resolved_count'),
      championAlignmentRate: decimal('champion_alignment_rate'),
      challengerAlignmentRate: decimal('challenger_alignment_rate'),
      alignmentUplift: decimal('alignment_uplift'),
      recommendationChanges: integer('recommendation_changes'),
      riskChanges: integer('risk_changes'),
      safetyDowngrades: integer('safety_downgrades'),
      unsafeActionabilityConflicts: integer('unsafe_actionability_conflicts'),
      createdAt: DateTime.tryParse(json['created_at']?.toString() ?? '') ??
          DateTime.fromMillisecondsSinceEpoch(0),
    );
  }
}

class DecisionEngineLabSnapshot {
  const DecisionEngineLabSnapshot({
    required this.champion,
    required this.challengers,
    required this.shadowOnly,
    required this.productionEngineUnchanged,
    required this.autoActivation,
    this.latestEvaluation,
    this.promotionGateStatus,
  });

  final DecisionEngineDescriptor? champion;
  final List<DecisionEngineDescriptor> challengers;
  final DecisionEngineEvaluationSnapshot? latestEvaluation;
  final String? promotionGateStatus;
  final bool shadowOnly;
  final bool productionEngineUnchanged;
  final bool autoActivation;

  factory DecisionEngineLabSnapshot.fromJson(Map<String, dynamic> json) {
    final Map<String, dynamic> championJson = _map(json['champion']);
    final List<dynamic> challengersJson =
        json['challengers'] as List<dynamic>? ?? const <dynamic>[];
    final Map<String, dynamic> evaluationJson = _map(json['latest_evaluation']);
    final Map<String, dynamic> promotionJson = _map(json['promotion_packet']);

    return DecisionEngineLabSnapshot(
      champion: championJson.isEmpty
          ? null
          : DecisionEngineDescriptor.fromJson(championJson),
      challengers: challengersJson
          .map(
            (dynamic item) =>
                DecisionEngineDescriptor.fromJson(_map(item)),
          )
          .toList(growable: false),
      latestEvaluation: evaluationJson.isEmpty
          ? null
          : DecisionEngineEvaluationSnapshot.fromJson(evaluationJson),
      promotionGateStatus: promotionJson['gate_status'] as String?,
      shadowOnly: json['shadow_only'] as bool? ?? true,
      productionEngineUnchanged:
          json['production_engine_unchanged'] as bool? ?? true,
      autoActivation: json['auto_activation'] as bool? ?? false,
    );
  }
}

class ProfessorEngineLabRepository {
  ProfessorEngineLabRepository._();

  static final ProfessorEngineLabRepository instance =
      ProfessorEngineLabRepository._();

  SupabaseClient get _client => Supabase.instance.client;

  Future<DecisionEngineLabSnapshot> fetchStatus() async {
    final String organizationId =
        await AuthService.instance.ensureProfessorOrganization();
    final dynamic response = await _client.rpc(
      'get_decision_engine_lab_status',
      params: <String, dynamic>{'p_organization_id': organizationId},
    );
    return DecisionEngineLabSnapshot.fromJson(_map(response));
  }

  Future<DecisionEngineLabSnapshot> runShadowEvaluation() async {
    final String organizationId =
        await AuthService.instance.ensureProfessorOrganization();
    await _client.rpc(
      'run_decision_engine_evaluation',
      params: <String, dynamic>{
        'p_organization_id': organizationId,
        'p_challenger_version': 'blackgold_deterministic_v1_1_shadow',
      },
    );
    return fetchStatus();
  }
}

Map<String, dynamic> _map(dynamic value) {
  if (value is Map<String, dynamic>) return value;
  if (value is Map) return Map<String, dynamic>.from(value);
  return <String, dynamic>{};
}
