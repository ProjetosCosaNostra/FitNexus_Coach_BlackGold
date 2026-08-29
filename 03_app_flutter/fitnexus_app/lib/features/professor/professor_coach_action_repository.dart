import 'package:supabase_flutter/supabase_flutter.dart';

import '../auth/auth_service.dart';

const bool fitNexusStoreCaptureMode = bool.fromEnvironment(
  'FITNEXUS_STORE_CAPTURE',
  defaultValue: false,
);

class CoachActionSummary {
  const CoachActionSummary({
    required this.activeActions,
    required this.urgent,
    required this.attention,
    required this.setup,
    required this.monitor,
    required this.completedToday,
    required this.snoozed,
  });

  final int activeActions;
  final int urgent;
  final int attention;
  final int setup;
  final int monitor;
  final int completedToday;
  final int snoozed;

  factory CoachActionSummary.fromJson(Map<String, dynamic> json) {
    int number(String key) => (json[key] as num?)?.toInt() ?? 0;
    return CoachActionSummary(
      activeActions: number('active_actions'),
      urgent: number('urgent'),
      attention: number('attention'),
      setup: number('setup'),
      monitor: number('monitor'),
      completedToday: number('completed_today'),
      snoozed: number('snoozed'),
    );
  }
}

class CoachActionEvidence {
  const CoachActionEvidence({
    this.painScore,
    this.painLocation,
    this.perceivedExertion,
    this.energyScore,
    this.feedbackSubmittedAt,
    this.activePlanId,
    this.activePlanName,
    this.hasActiveAccess,
    this.unresolvedDecisionRunId,
    this.unresolvedDecisionCreatedAt,
  });

  final int? painScore;
  final String? painLocation;
  final int? perceivedExertion;
  final int? energyScore;
  final DateTime? feedbackSubmittedAt;
  final String? activePlanId;
  final String? activePlanName;
  final bool? hasActiveAccess;
  final String? unresolvedDecisionRunId;
  final DateTime? unresolvedDecisionCreatedAt;

  factory CoachActionEvidence.fromJson(Map<String, dynamic> json) {
    return CoachActionEvidence(
      painScore: (json['pain_score'] as num?)?.toInt(),
      painLocation: json['pain_location'] as String?,
      perceivedExertion: (json['perceived_exertion'] as num?)?.toInt(),
      energyScore: (json['energy_score'] as num?)?.toInt(),
      feedbackSubmittedAt: _dateTime(json['feedback_submitted_at']),
      activePlanId: json['active_plan_id'] as String?,
      activePlanName: json['active_plan_name'] as String?,
      hasActiveAccess: json['has_active_access'] as bool?,
      unresolvedDecisionRunId: json['unresolved_decision_run_id'] as String?,
      unresolvedDecisionCreatedAt:
          _dateTime(json['unresolved_decision_created_at']),
    );
  }
}

class CoachActionItem {
  const CoachActionItem({
    required this.studentId,
    required this.studentName,
    required this.objective,
    required this.level,
    required this.studentStatus,
    required this.adherence,
    required this.sessions30d,
    required this.completed30d,
    required this.priorityScore,
    required this.priorityLabel,
    required this.actionType,
    required this.actionTitle,
    required this.actionReason,
    required this.target,
    required this.actionFingerprint,
    required this.evidence,
    required this.humanActionRequired,
    this.lastSessionAt,
  });

  final String studentId;
  final String studentName;
  final String objective;
  final String level;
  final String studentStatus;
  final int adherence;
  final int sessions30d;
  final int completed30d;
  final DateTime? lastSessionAt;
  final int priorityScore;
  final String priorityLabel;
  final String actionType;
  final String actionTitle;
  final String actionReason;
  final String target;
  final String actionFingerprint;
  final CoachActionEvidence evidence;
  final bool humanActionRequired;

  bool get urgent => priorityLabel == 'urgent';

  factory CoachActionItem.fromJson(Map<String, dynamic> json) {
    final Map<String, dynamic> guardrails = _map(json['guardrails']);
    return CoachActionItem(
      studentId: json['student_id'] as String? ?? '',
      studentName: json['student_name'] as String? ?? 'Aluno',
      objective: json['objective'] as String? ?? 'Geral',
      level: json['level'] as String? ?? 'Iniciante',
      studentStatus: json['student_status'] as String? ?? 'Ativo',
      adherence: (json['adherence'] as num?)?.toInt() ?? 0,
      sessions30d: (json['sessions_30d'] as num?)?.toInt() ?? 0,
      completed30d: (json['completed_30d'] as num?)?.toInt() ?? 0,
      lastSessionAt: _dateTime(json['last_session_at']),
      priorityScore: (json['priority_score'] as num?)?.toInt() ?? 0,
      priorityLabel: json['priority_label'] as String? ?? 'monitor',
      actionType: json['action_type'] as String? ?? 'maintain_monitoring',
      actionTitle: json['action_title'] as String? ?? 'Manter acompanhamento',
      actionReason: json['action_reason'] as String? ?? '',
      target: json['target'] as String? ?? 'progress',
      actionFingerprint: json['action_fingerprint'] as String? ?? '',
      evidence: CoachActionEvidence.fromJson(_map(json['evidence'])),
      humanActionRequired:
          guardrails['human_action_required'] as bool? ?? true,
    );
  }
}

class CoachActionSnapshot {
  const CoachActionSnapshot({
    required this.summary,
    required this.actions,
    required this.principle,
    required this.generatedAt,
  });

  final CoachActionSummary summary;
  final List<CoachActionItem> actions;
  final String principle;
  final DateTime generatedAt;

  factory CoachActionSnapshot.fromJson(Map<String, dynamic> json) {
    final List<dynamic> actions =
        json['actions'] as List<dynamic>? ?? const <dynamic>[];
    return CoachActionSnapshot(
      summary: CoachActionSummary.fromJson(_map(json['summary'])),
      actions: actions
          .map((dynamic item) => CoachActionItem.fromJson(_map(item)))
          .toList(growable: false),
      principle: json['principle'] as String? ??
          'O FitNexus prioriza e explica; o professor decide e executa.',
      generatedAt: _dateTime(json['generated_at']) ?? DateTime.now(),
    );
  }
}

class ProfessorCoachActionRepository {
  ProfessorCoachActionRepository._();

  static final ProfessorCoachActionRepository instance =
      ProfessorCoachActionRepository._();

  SupabaseClient get _client => Supabase.instance.client;

  Future<String> _organizationId() {
    return AuthService.instance.ensureProfessorOrganization();
  }

  Future<CoachActionSnapshot> fetchActionCenter() async {
    if (fitNexusStoreCaptureMode) {
      return _storeCaptureSnapshot();
    }

    final String organizationId = await _organizationId();
    final dynamic response = await _client.rpc(
      'get_coach_action_center',
      params: <String, dynamic>{'p_organization_id': organizationId},
    );
    return CoachActionSnapshot.fromJson(_map(response));
  }

  Future<void> completeForToday(CoachActionItem action) async {
    if (fitNexusStoreCaptureMode) return;
    await _record(action: action, resolution: 'completed');
  }

  Future<void> snooze(
    CoachActionItem action, {
    Duration duration = const Duration(days: 1),
  }) async {
    if (fitNexusStoreCaptureMode) return;

    final DateTime until = DateTime.now().toUtc().add(duration);
    await _record(
      action: action,
      resolution: 'snoozed',
      snoozeUntil: until,
    );
  }

  Future<void> _record({
    required CoachActionItem action,
    required String resolution,
    DateTime? snoozeUntil,
  }) async {
    final String organizationId = await _organizationId();
    await _client.rpc(
      'record_coach_action_event',
      params: <String, dynamic>{
        'p_organization_id': organizationId,
        'p_student_id': action.studentId,
        'p_action_fingerprint': action.actionFingerprint,
        'p_resolution': resolution,
        'p_note': null,
        'p_snooze_until': snoozeUntil?.toUtc().toIso8601String(),
      },
    );
  }
}

CoachActionSnapshot _storeCaptureSnapshot() {
  final DateTime generatedAt = DateTime.utc(2026, 8, 29, 15, 0);
  return CoachActionSnapshot(
    summary: const CoachActionSummary(
      activeActions: 3,
      urgent: 1,
      attention: 1,
      setup: 0,
      monitor: 1,
      completedToday: 4,
      snoozed: 1,
    ),
    actions: <CoachActionItem>[
      CoachActionItem(
        studentId: 'synthetic-marina-alves',
        studentName: 'Marina Alves',
        objective: 'Condicionamento',
        level: 'Intermediário',
        studentStatus: 'Ativo',
        adherence: 62,
        sessions30d: 10,
        completed30d: 7,
        lastSessionAt: DateTime.utc(2026, 8, 28, 18, 30),
        priorityScore: 92,
        priorityLabel: 'urgent',
        actionType: 'review_feedback',
        actionTitle: 'Revisar feedback antes do próximo treino',
        actionReason:
            'O último treino teve esforço acima do padrão recente e energia mais baixa. Revise o contexto antes de manter a progressão.',
        target: 'feedback',
        actionFingerprint: 'capture-marina-feedback-v1',
        evidence: CoachActionEvidence(
          perceivedExertion: 9,
          energyScore: 2,
          feedbackSubmittedAt: DateTime.utc(2026, 8, 28, 19, 10),
          activePlanId: 'synthetic-plan-01',
          activePlanName: 'Base de força • Semana 4',
          hasActiveAccess: true,
        ),
        humanActionRequired: true,
      ),
      CoachActionItem(
        studentId: 'synthetic-rafael-costa',
        studentName: 'Rafael Costa',
        objective: 'Força e consistência',
        level: 'Avançado',
        studentStatus: 'Ativo',
        adherence: 78,
        sessions30d: 14,
        completed30d: 11,
        lastSessionAt: DateTime.utc(2026, 8, 27, 7, 45),
        priorityScore: 74,
        priorityLabel: 'attention',
        actionType: 'review_plan',
        actionTitle: 'Confirmar continuidade da prescrição',
        actionReason:
            'A execução está consistente, mas houve duas sessões não concluídas nesta semana. Confira agenda e ajuste somente se fizer sentido.',
        target: 'training',
        actionFingerprint: 'capture-rafael-plan-v1',
        evidence: const CoachActionEvidence(
          perceivedExertion: 7,
          energyScore: 4,
          activePlanId: 'synthetic-plan-02',
          activePlanName: 'Força total • Bloco B',
          hasActiveAccess: true,
        ),
        humanActionRequired: true,
      ),
      CoachActionItem(
        studentId: 'synthetic-ana-rocha',
        studentName: 'Ana Rocha',
        objective: 'Mobilidade e rotina',
        level: 'Iniciante',
        studentStatus: 'Ativo',
        adherence: 91,
        sessions30d: 12,
        completed30d: 11,
        lastSessionAt: DateTime.utc(2026, 8, 29, 6, 40),
        priorityScore: 38,
        priorityLabel: 'monitor',
        actionType: 'maintain_monitoring',
        actionTitle: 'Manter acompanhamento',
        actionReason:
            'Aderência alta e feedback estável. Nenhuma intervenção é necessária agora; apenas mantenha o acompanhamento.',
        target: 'progress',
        actionFingerprint: 'capture-ana-monitor-v1',
        evidence: const CoachActionEvidence(
          perceivedExertion: 6,
          energyScore: 5,
          activePlanId: 'synthetic-plan-03',
          activePlanName: 'Mobilidade diária',
          hasActiveAccess: true,
        ),
        humanActionRequired: true,
      ),
    ],
    principle:
        'O FitNexus prioriza e explica; o professor decide e executa.',
    generatedAt: generatedAt,
  );
}

Map<String, dynamic> _map(dynamic value) {
  if (value is Map<String, dynamic>) return value;
  if (value is Map) return Map<String, dynamic>.from(value);
  return <String, dynamic>{};
}

DateTime? _dateTime(dynamic value) {
  if (value == null) return null;
  return DateTime.tryParse(value.toString());
}
