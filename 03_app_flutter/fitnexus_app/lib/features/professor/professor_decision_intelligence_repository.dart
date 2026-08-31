import 'package:supabase_flutter/supabase_flutter.dart';

import '../auth/auth_service.dart';
import 'professor_data_repository.dart';
import 'professor_lineage_repository.dart';

class DecisionEvidence {
  const DecisionEvidence({
    required this.type,
    required this.label,
    this.value,
    this.unit,
  });

  final String type;
  final String label;
  final dynamic value;
  final String? unit;

  factory DecisionEvidence.fromJson(Map<String, dynamic> json) {
    return DecisionEvidence(
      type: json['type'] as String? ?? 'unknown',
      label: json['label'] as String? ?? 'Evidência',
      value: json['value'],
      unit: json['unit'] as String?,
    );
  }

  String get displayValue {
    final dynamic current = value;
    if (current == null) return 'sem dado';
    if (current is Map) {
      final Map<String, dynamic> map = Map<String, dynamic>.from(current);
      if (type == 'latest_feedback') {
        return 'dor ${map['pain_score'] ?? '—'}/10 • esforço ${map['perceived_exertion'] ?? '—'}/10 • energia ${map['energy_score'] ?? '—'}/5';
      }
      if (type == 'active_plan') {
        return '${map['plan_name'] ?? 'Treino'} • ${map['exercise_count'] ?? 0} exercícios';
      }
    }
    return '$current${unit ?? ''}';
  }
}

class DecisionCandidate {
  const DecisionCandidate({
    required this.templateId,
    required this.templateName,
    required this.objective,
    required this.level,
    required this.exercises,
    required this.diff,
  });

  final String templateId;
  final String templateName;
  final String objective;
  final String level;
  final List<TrainingExerciseDraft> exercises;
  final TrainingChangePreview diff;

  factory DecisionCandidate.fromJson(Map<String, dynamic> json) {
    final List<dynamic> exercises =
        json['proposed_exercises'] as List<dynamic>? ?? const <dynamic>[];
    return DecisionCandidate(
      templateId: json['template_id'] as String? ?? '',
      templateName: json['template_name'] as String? ?? 'Smart Template',
      objective: json['objective'] as String? ?? 'Geral',
      level: json['level'] as String? ?? 'Iniciante',
      exercises: exercises.map((dynamic row) {
        final Map<String, dynamic> map = _map(row);
        return TrainingExerciseDraft(
          name: map['name'] as String? ?? 'Exercício',
          prescription: map['prescription'] as String? ?? '',
        );
      }).toList(growable: false),
      diff: TrainingChangePreview.fromJson(_map(json['proposed_diff'])),
    );
  }
}

class DecisionIntelligenceBrief {
  const DecisionIntelligenceBrief({
    required this.runId,
    required this.studentId,
    required this.studentName,
    required this.objective,
    required this.level,
    required this.adherence,
    required this.riskLevel,
    required this.confidenceScore,
    required this.confidenceLabel,
    required this.recommendationType,
    required this.recommendationTitle,
    required this.recommendationReason,
    required this.evidence,
    required this.engineVersion,
    required this.engineMode,
    required this.generatedAt,
    this.candidate,
    this.candidateBlockReason,
  });

  final String runId;
  final String studentId;
  final String studentName;
  final String objective;
  final String level;
  final int adherence;
  final String riskLevel;
  final int confidenceScore;
  final String confidenceLabel;
  final String recommendationType;
  final String recommendationTitle;
  final String recommendationReason;
  final List<DecisionEvidence> evidence;
  final DecisionCandidate? candidate;
  final String? candidateBlockReason;
  final String engineVersion;
  final String engineMode;
  final DateTime generatedAt;

  bool get hasCandidate => candidate != null && candidate!.exercises.isNotEmpty;

  factory DecisionIntelligenceBrief.fromJson(Map<String, dynamic> json) {
    final Map<String, dynamic> student = _map(json['student']);
    final Map<String, dynamic> risk = _map(json['risk']);
    final Map<String, dynamic> confidence = _map(json['confidence']);
    final Map<String, dynamic> recommendation = _map(json['recommendation']);
    final Map<String, dynamic> engine = _map(json['engine']);
    final List<dynamic> evidence =
        json['evidence'] as List<dynamic>? ?? const <dynamic>[];
    final Map<String, dynamic> candidateMap = _map(json['candidate']);

    return DecisionIntelligenceBrief(
      runId: json['run_id'] as String? ?? '',
      studentId: student['student_id'] as String? ?? '',
      studentName: student['name'] as String? ?? 'Aluno',
      objective: student['objective'] as String? ?? 'Geral',
      level: student['level'] as String? ?? 'Iniciante',
      adherence: (student['adherence'] as num?)?.toInt() ?? 0,
      riskLevel: risk['level'] as String? ?? 'new',
      confidenceScore: (confidence['score'] as num?)?.toInt() ?? 0,
      confidenceLabel: confidence['label'] as String? ?? 'low',
      recommendationType:
          recommendation['type'] as String? ?? 'maintain_and_monitor',
      recommendationTitle:
          recommendation['title'] as String? ?? 'Manter e acompanhar',
      recommendationReason: recommendation['reason'] as String? ?? '',
      evidence: evidence
          .map((dynamic row) => DecisionEvidence.fromJson(_map(row)))
          .toList(growable: false),
      candidate: candidateMap.isEmpty
          ? null
          : DecisionCandidate.fromJson(candidateMap),
      candidateBlockReason: json['candidate_block_reason'] as String?,
      engineVersion: engine['version'] as String? ?? 'unknown',
      engineMode: engine['mode'] as String? ?? 'deterministic_fallback',
      generatedAt: DateTime.tryParse(json['generated_at']?.toString() ?? '') ??
          DateTime.now(),
    );
  }
}

class DecisionIntelligenceHistoryItem {
  const DecisionIntelligenceHistoryItem({
    required this.runId,
    required this.createdAt,
    required this.brief,
  });

  final String runId;
  final DateTime createdAt;
  final DecisionIntelligenceBrief brief;

  factory DecisionIntelligenceHistoryItem.fromJson(Map<String, dynamic> json) {
    final Map<String, dynamic> briefJson = _map(json['brief']);
    final String runId = json['run_id'] as String? ?? '';
    return DecisionIntelligenceHistoryItem(
      runId: runId,
      createdAt: DateTime.tryParse(json['created_at']?.toString() ?? '') ??
          DateTime.fromMillisecondsSinceEpoch(0),
      brief: DecisionIntelligenceBrief.fromJson(
        briefJson..['run_id'] = runId,
      ),
    );
  }
}

class DecisionCalibrationSummary {
  const DecisionCalibrationSummary({
    required this.totalRuns,
    required this.resolvedRuns,
    required this.unresolvedRuns,
    required this.accepted,
    required this.modified,
    required this.rejected,
    required this.noAction,
    required this.adoptionRate,
    required this.exactAcceptanceRate,
    required this.modificationRate,
  });

  final int totalRuns;
  final int resolvedRuns;
  final int unresolvedRuns;
  final int accepted;
  final int modified;
  final int rejected;
  final int noAction;
  final int adoptionRate;
  final int exactAcceptanceRate;
  final int modificationRate;

  factory DecisionCalibrationSummary.fromJson(Map<String, dynamic> json) {
    int number(String key) => (json[key] as num?)?.toInt() ?? 0;
    return DecisionCalibrationSummary(
      totalRuns: number('total_runs'),
      resolvedRuns: number('resolved_runs'),
      unresolvedRuns: number('unresolved_runs'),
      accepted: number('accepted'),
      modified: number('modified'),
      rejected: number('rejected'),
      noAction: number('no_action'),
      adoptionRate: number('adoption_rate'),
      exactAcceptanceRate: number('exact_acceptance_rate'),
      modificationRate: number('modification_rate'),
    );
  }
}

class DecisionCalibrationSnapshot {
  const DecisionCalibrationSnapshot({
    required this.summary,
    required this.interpretation,
    required this.generatedAt,
  });

  final DecisionCalibrationSummary summary;
  final String interpretation;
  final DateTime generatedAt;

  factory DecisionCalibrationSnapshot.fromJson(Map<String, dynamic> json) {
    return DecisionCalibrationSnapshot(
      summary: DecisionCalibrationSummary.fromJson(_map(json['summary'])),
      interpretation: json['interpretation'] as String? ??
          'Calibração de uso e decisão humana.',
      generatedAt: DateTime.tryParse(json['generated_at']?.toString() ?? '') ??
          DateTime.now(),
    );
  }
}

class ProfessorDecisionIntelligenceRepository {
  ProfessorDecisionIntelligenceRepository._();

  static final ProfessorDecisionIntelligenceRepository instance =
      ProfessorDecisionIntelligenceRepository._();

  SupabaseClient get _client => Supabase.instance.client;

  Future<DecisionIntelligenceBrief> generateBrief(String studentId) async {
    if (fitNexusStoreCaptureDataMode) {
      return _storeCaptureBrief(studentId);
    }
    final dynamic response = await _client.rpc(
      'generate_decision_intelligence_brief',
      params: <String, dynamic>{'p_student_id': studentId},
    );
    return DecisionIntelligenceBrief.fromJson(_map(response));
  }

  Future<List<DecisionIntelligenceHistoryItem>> fetchHistory(
    String studentId, {
    int limit = 10,
  }) async {
    if (fitNexusStoreCaptureDataMode) {
      final DecisionIntelligenceBrief brief = _storeCaptureBrief(studentId);
      return <DecisionIntelligenceHistoryItem>[
        DecisionIntelligenceHistoryItem(
          runId: brief.runId,
          createdAt: brief.generatedAt,
          brief: brief,
        ),
      ];
    }
    final dynamic response = await _client.rpc(
      'get_decision_intelligence_history',
      params: <String, dynamic>{
        'p_student_id': studentId,
        'p_limit': limit,
      },
    );
    final Map<String, dynamic> root = _map(response);
    final List<dynamic> items =
        root['items'] as List<dynamic>? ?? const <dynamic>[];
    return items
        .map(
          (dynamic row) =>
              DecisionIntelligenceHistoryItem.fromJson(_map(row)),
        )
        .toList(growable: false);
  }

  Future<void> recordOutcome({
    required String runId,
    required String outcome,
    String? note,
  }) async {
    if (fitNexusStoreCaptureDataMode) {
      throw StateError('STORE_CAPTURE_REMOTE_MUTATION_FORBIDDEN');
    }
    await _client.rpc(
      'record_decision_intelligence_outcome',
      params: <String, dynamic>{
        'p_run_id': runId,
        'p_outcome': outcome,
        'p_note': _nullable(note),
      },
    );
  }

  Future<DecisionCalibrationSnapshot> fetchCalibration() async {
    if (fitNexusStoreCaptureDataMode) {
      return DecisionCalibrationSnapshot(
        summary: const DecisionCalibrationSummary(
          totalRuns: 24,
          resolvedRuns: 21,
          unresolvedRuns: 3,
          accepted: 9,
          modified: 7,
          rejected: 3,
          noAction: 2,
          adoptionRate: 76,
          exactAcceptanceRate: 43,
          modificationRate: 33,
        ),
        interpretation:
            'O professor mantém autoridade: 76% dos briefs viraram ação humana consciente, e 33% foram ajustados antes da prescrição final.',
        generatedAt: DateTime.utc(2026, 8, 31, 14, 0),
      );
    }
    final String organizationId =
        await AuthService.instance.ensureProfessorOrganization();
    final dynamic response = await _client.rpc(
      'get_decision_intelligence_calibration',
      params: <String, dynamic>{'p_organization_id': organizationId},
    );
    return DecisionCalibrationSnapshot.fromJson(_map(response));
  }
}

DecisionIntelligenceBrief _storeCaptureBrief(String studentId) {
  final bool marina = studentId == 'store-student-01' || studentId.isEmpty;
  return DecisionIntelligenceBrief(
    runId: 'store-decision-brief-20260831',
    studentId: marina ? 'store-student-01' : studentId,
    studentName: marina ? 'Marina Costa' : 'Aluno BlackGold',
    objective: marina ? 'Hipertrofia' : 'Condicionamento',
    level: 'Intermediário',
    adherence: 92,
    riskLevel: 'attention',
    confidenceScore: 91,
    confidenceLabel: 'high',
    recommendationType: 'review_progression',
    recommendationTitle: 'Revisar progressão antes do próximo treino',
    recommendationReason:
        'Aderência alta, mas o último feedback trouxe esforço 9/10 e energia 2/5. O FitNexus recomenda revisar a progressão; a decisão continua sendo do professor.',
    evidence: const <DecisionEvidence>[
      DecisionEvidence(
        type: 'latest_feedback',
        label: 'Feedback mais recente',
        value: <String, dynamic>{
          'pain_score': 1,
          'perceived_exertion': 9,
          'energy_score': 2,
        },
      ),
      DecisionEvidence(
        type: 'active_plan',
        label: 'Treino ativo',
        value: <String, dynamic>{
          'plan_name': 'Hipertrofia • Bloco 4',
          'exercise_count': 7,
        },
      ),
      DecisionEvidence(
        type: 'adherence',
        label: 'Aderência 30 dias',
        value: 92,
        unit: '%',
      ),
    ],
    candidate: null,
    candidateBlockReason:
        'O brief sugere revisão humana antes de qualquer mudança de prescrição.',
    engineVersion: 'blackgold-decision-v1',
    engineMode: 'explainable_human_in_loop',
    generatedAt: DateTime.utc(2026, 8, 31, 13, 52),
  );
}

String? _nullable(String? value) {
  final String normalized = (value ?? '').trim();
  return normalized.isEmpty ? null : normalized;
}

Map<String, dynamic> _map(dynamic value) {
  if (value is Map<String, dynamic>) return value;
  if (value is Map) return Map<String, dynamic>.from(value);
  return <String, dynamic>{};
}
