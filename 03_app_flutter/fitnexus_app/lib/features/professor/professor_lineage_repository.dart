import 'package:supabase_flutter/supabase_flutter.dart';

class TrainingLineageDiff {
  const TrainingLineageDiff({
    required this.added,
    required this.removed,
    required this.changed,
  });

  final List<String> added;
  final List<String> removed;
  final List<String> changed;

  int get addedCount => added.length;
  int get removedCount => removed.length;
  int get changedCount => changed.length;
  bool get hasChanges => added.isNotEmpty || removed.isNotEmpty || changed.isNotEmpty;

  factory TrainingLineageDiff.fromJson(Map<String, dynamic> json) {
    String name(dynamic row) {
      final Map<String, dynamic> map = _map(row);
      final String exercise = map['name'] as String? ?? 'Exercício';
      final String? before = map['before'] as String?;
      final String? after = map['after'] as String?;
      if (before != null || after != null) {
        return '$exercise: ${before ?? '—'} → ${after ?? '—'}';
      }
      return exercise;
    }

    List<String> list(String key) =>
        (json[key] as List<dynamic>? ?? const <dynamic>[])
            .map(name)
            .toList(growable: false);

    return TrainingLineageDiff(
      added: list('added'),
      removed: list('removed'),
      changed: list('changed'),
    );
  }
}

class TrainingLineageRecord {
  const TrainingLineageRecord({
    required this.lineageId,
    required this.planId,
    required this.planName,
    required this.isActive,
    required this.createdAt,
    required this.decisionType,
    required this.decisionReason,
    required this.exerciseCount,
    required this.diff,
    this.predecessorPlanId,
    this.predecessorPlanName,
    this.sourceTemplateId,
    this.sourceTemplateName,
  });

  final String lineageId;
  final String planId;
  final String planName;
  final bool isActive;
  final DateTime createdAt;
  final String? predecessorPlanId;
  final String? predecessorPlanName;
  final String? sourceTemplateId;
  final String? sourceTemplateName;
  final String decisionType;
  final String decisionReason;
  final int exerciseCount;
  final TrainingLineageDiff diff;

  String get decisionLabel => switch (decisionType) {
        'initial_prescription' => 'Prescrição inicial',
        'template_assignment' => 'Smart Template',
        'manual_revision' => 'Revisão manual',
        'legacy_import' => 'Histórico recuperado',
        _ => 'Decisão registrada',
      };

  factory TrainingLineageRecord.fromJson(Map<String, dynamic> json) {
    return TrainingLineageRecord(
      lineageId: json['lineage_id'] as String? ?? '',
      planId: json['plan_id'] as String? ?? '',
      planName: json['plan_name'] as String? ?? 'Treino',
      isActive: json['is_active'] as bool? ?? false,
      createdAt: DateTime.tryParse(json['created_at']?.toString() ?? '') ??
          DateTime.fromMillisecondsSinceEpoch(0),
      predecessorPlanId: json['predecessor_plan_id'] as String?,
      predecessorPlanName: json['predecessor_plan_name'] as String?,
      sourceTemplateId: json['source_template_id'] as String?,
      sourceTemplateName: json['source_template_name'] as String?,
      decisionType: json['decision_type'] as String? ?? 'legacy_import',
      decisionReason: json['decision_reason'] as String? ?? 'Sem justificativa registrada',
      exerciseCount: (json['exercise_count'] as num?)?.toInt() ?? 0,
      diff: TrainingLineageDiff.fromJson(_map(json['diff'])),
    );
  }
}

class TrainingLineageSnapshot {
  const TrainingLineageSnapshot({
    required this.studentId,
    required this.items,
    required this.generatedAt,
  });

  final String studentId;
  final List<TrainingLineageRecord> items;
  final DateTime generatedAt;

  factory TrainingLineageSnapshot.fromJson(Map<String, dynamic> json) {
    final List<dynamic> rows = json['items'] as List<dynamic>? ?? const <dynamic>[];
    return TrainingLineageSnapshot(
      studentId: json['student_id'] as String? ?? '',
      items: rows
          .map((dynamic row) => TrainingLineageRecord.fromJson(_map(row)))
          .toList(growable: false),
      generatedAt:
          DateTime.tryParse(json['generated_at']?.toString() ?? '') ?? DateTime.now(),
    );
  }
}

class TrainingChangePreview {
  const TrainingChangePreview({
    required this.hasPreviousPlan,
    required this.added,
    required this.removed,
    required this.changed,
    this.activePlanId,
    this.activePlanName,
  });

  final bool hasPreviousPlan;
  final String? activePlanId;
  final String? activePlanName;
  final List<String> added;
  final List<String> removed;
  final List<String> changed;

  factory TrainingChangePreview.fromJson(Map<String, dynamic> json) {
    String itemName(dynamic row) => _map(row)['name'] as String? ?? 'Exercício';
    String changedLabel(dynamic row) {
      final Map<String, dynamic> map = _map(row);
      return '${map['name'] ?? 'Exercício'}: ${map['before'] ?? '—'} → ${map['after'] ?? '—'}';
    }

    return TrainingChangePreview(
      hasPreviousPlan: json['has_previous_plan'] as bool? ?? false,
      activePlanId: json['active_plan_id'] as String?,
      activePlanName: json['active_plan_name'] as String?,
      added: (json['added'] as List<dynamic>? ?? const <dynamic>[])
          .map(itemName)
          .toList(growable: false),
      removed: (json['removed'] as List<dynamic>? ?? const <dynamic>[])
          .map(itemName)
          .toList(growable: false),
      changed: (json['changed'] as List<dynamic>? ?? const <dynamic>[])
          .map(changedLabel)
          .toList(growable: false),
    );
  }
}

class ProfessorLineageRepository {
  ProfessorLineageRepository._();

  static final ProfessorLineageRepository instance = ProfessorLineageRepository._();

  SupabaseClient get _client => Supabase.instance.client;

  Future<TrainingLineageSnapshot> fetchLineage(String studentId) async {
    final dynamic response = await _client.rpc(
      'get_student_training_lineage',
      params: <String, dynamic>{'p_student_id': studentId},
    );
    return TrainingLineageSnapshot.fromJson(_map(response));
  }

  Future<TrainingChangePreview> previewChange({
    required String studentId,
    required List<Map<String, dynamic>> exercises,
  }) async {
    final dynamic response = await _client.rpc(
      'preview_training_plan_change',
      params: <String, dynamic>{
        'p_student_id': studentId,
        'p_exercises': exercises,
      },
    );
    return TrainingChangePreview.fromJson(_map(response));
  }
}

Map<String, dynamic> _map(dynamic value) {
  if (value is Map<String, dynamic>) return value;
  if (value is Map) return Map<String, dynamic>.from(value);
  return <String, dynamic>{};
}
