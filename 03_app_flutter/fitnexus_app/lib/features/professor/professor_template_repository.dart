import 'package:supabase_flutter/supabase_flutter.dart';

import '../auth/auth_service.dart';
import 'professor_data_repository.dart';

class TrainingTemplateExerciseRecord {
  const TrainingTemplateExerciseRecord({
    required this.id,
    required this.position,
    required this.name,
    required this.prescription,
  });

  final String id;
  final int position;
  final String name;
  final String prescription;

  factory TrainingTemplateExerciseRecord.fromJson(Map<String, dynamic> json) {
    return TrainingTemplateExerciseRecord(
      id: json['id'] as String? ?? '',
      position: (json['position'] as num?)?.toInt() ?? 0,
      name: json['name'] as String? ?? 'Exercício',
      prescription: json['prescription'] as String? ?? '',
    );
  }
}

class TrainingTemplateRecord {
  const TrainingTemplateRecord({
    required this.id,
    required this.organizationId,
    required this.name,
    required this.objective,
    required this.level,
    required this.isActive,
    required this.exercises,
    this.notes,
  });

  final String id;
  final String organizationId;
  final String name;
  final String objective;
  final String level;
  final String? notes;
  final bool isActive;
  final List<TrainingTemplateExerciseRecord> exercises;

  factory TrainingTemplateRecord.fromJson(Map<String, dynamic> json) {
    final List<dynamic> exerciseRows =
        json['training_template_exercises'] as List<dynamic>? ??
            const <dynamic>[];

    final List<TrainingTemplateExerciseRecord> exercises = exerciseRows
        .map(
          (dynamic row) => TrainingTemplateExerciseRecord.fromJson(
            Map<String, dynamic>.from(row as Map),
          ),
        )
        .toList(growable: false)
      ..sort(
        (TrainingTemplateExerciseRecord a,
                TrainingTemplateExerciseRecord b) =>
            a.position.compareTo(b.position),
      );

    return TrainingTemplateRecord(
      id: json['id'] as String? ?? '',
      organizationId: json['organization_id'] as String? ?? '',
      name: json['name'] as String? ?? 'Modelo',
      objective: json['objective'] as String? ?? 'Geral',
      level: json['level'] as String? ?? 'Iniciante',
      notes: json['notes'] as String?,
      isActive: json['is_active'] as bool? ?? true,
      exercises: exercises,
    );
  }
}

class ProfessorTemplateRepository {
  ProfessorTemplateRepository._();

  static final ProfessorTemplateRepository instance =
      ProfessorTemplateRepository._();

  SupabaseClient get _client => Supabase.instance.client;

  Future<String> _organizationId() {
    return AuthService.instance.ensureProfessorOrganization();
  }

  Future<List<TrainingTemplateRecord>> fetchTemplates() async {
    final String organizationId = await _organizationId();

    final List<dynamic> rows = await _client
        .from('training_templates')
        .select('*, training_template_exercises(*)')
        .eq('organization_id', organizationId)
        .eq('is_active', true)
        .order('updated_at', ascending: false);

    return rows
        .map(
          (dynamic row) => TrainingTemplateRecord.fromJson(
            Map<String, dynamic>.from(row as Map),
          ),
        )
        .toList(growable: false);
  }

  Future<String> createTemplate({
    required String name,
    required String objective,
    required String level,
    required List<TrainingExerciseDraft> exercises,
    String? notes,
  }) async {
    if (exercises.isEmpty) {
      throw ArgumentError.value(
        exercises,
        'exercises',
        'Informe pelo menos um exercício.',
      );
    }

    final String organizationId = await _organizationId();

    final dynamic result = await _client.rpc(
      'create_training_template',
      params: <String, dynamic>{
        'p_organization_id': organizationId,
        'p_name': name.trim(),
        'p_objective': objective.trim(),
        'p_level': level.trim(),
        'p_notes': _nullable(notes),
        'p_exercises': exercises
            .map((TrainingExerciseDraft item) => item.toJson())
            .toList(growable: false),
      },
    );

    final String templateId = result?.toString() ?? '';
    if (templateId.isEmpty) {
      throw StateError('O modelo foi criado sem retornar identificador.');
    }
    return templateId;
  }

  Future<String> assignTemplate({
    required String templateId,
    required String studentId,
    String? nextSession,
  }) async {
    final dynamic result = await _client.rpc(
      'assign_training_template',
      params: <String, dynamic>{
        'p_template_id': templateId,
        'p_student_id': studentId,
        'p_next_session': _nullable(nextSession),
      },
    );

    final String planId = result?.toString() ?? '';
    if (planId.isEmpty) {
      throw StateError('O modelo não retornou o novo treino.');
    }
    return planId;
  }

  Future<String> createFromPlan({
    required String planId,
    String? name,
  }) async {
    final dynamic result = await _client.rpc(
      'create_training_template_from_plan',
      params: <String, dynamic>{
        'p_plan_id': planId,
        'p_name': _nullable(name),
      },
    );

    final String templateId = result?.toString() ?? '';
    if (templateId.isEmpty) {
      throw StateError('O treino não retornou o novo modelo.');
    }
    return templateId;
  }

  String? _nullable(String? value) {
    final String normalized = (value ?? '').trim();
    return normalized.isEmpty ? null : normalized;
  }
}
