import 'package:supabase_flutter/supabase_flutter.dart';

import '../auth/auth_service.dart';

class StudentRecord {
  const StudentRecord({
    required this.id,
    required this.organizationId,
    required this.name,
    required this.objective,
    required this.level,
    required this.adherence,
    required this.status,
    this.email,
    this.lastWorkout,
    this.lastWorkoutDate,
    this.nextSession,
  });

  final String id;
  final String organizationId;
  final String name;
  final String? email;
  final String objective;
  final String level;
  final String? lastWorkout;
  final DateTime? lastWorkoutDate;
  final int adherence;
  final String? nextSession;
  final String status;

  factory StudentRecord.fromJson(Map<String, dynamic> json) {
    return StudentRecord(
      id: json['id'] as String,
      organizationId: json['organization_id'] as String,
      name: json['name'] as String,
      email: json['email'] as String?,
      objective: json['objective'] as String? ?? 'Geral',
      level: json['level'] as String? ?? 'Iniciante',
      lastWorkout: json['last_workout'] as String?,
      lastWorkoutDate: json['last_workout_date'] == null
          ? null
          : DateTime.tryParse(json['last_workout_date'] as String),
      adherence: (json['adherence'] as num?)?.toInt() ?? 0,
      nextSession: json['next_session'] as String?,
      status: json['status'] as String? ?? 'Ativo',
    );
  }
}

class TrainingExerciseDraft {
  const TrainingExerciseDraft({
    required this.name,
    required this.prescription,
  });

  final String name;
  final String prescription;

  Map<String, dynamic> toJson() => <String, dynamic>{
        'name': name.trim(),
        'prescription': prescription.trim(),
      };
}

class TrainingPlanRecord {
  const TrainingPlanRecord({
    required this.id,
    required this.organizationId,
    required this.studentId,
    required this.name,
    required this.isActive,
    this.nextSession,
    this.notes,
  });

  final String id;
  final String organizationId;
  final String studentId;
  final String name;
  final String? nextSession;
  final String? notes;
  final bool isActive;

  factory TrainingPlanRecord.fromJson(Map<String, dynamic> json) {
    return TrainingPlanRecord(
      id: json['id'] as String,
      organizationId: json['organization_id'] as String,
      studentId: json['student_id'] as String,
      name: json['name'] as String,
      nextSession: json['next_session'] as String?,
      notes: json['notes'] as String?,
      isActive: json['is_active'] as bool? ?? true,
    );
  }
}

class ProfessorDataRepository {
  ProfessorDataRepository._();

  static final ProfessorDataRepository instance = ProfessorDataRepository._();

  SupabaseClient get _client => Supabase.instance.client;

  Future<String> _organizationId() {
    return AuthService.instance.ensureProfessorOrganization();
  }

  Future<List<StudentRecord>> fetchStudents() async {
    final String organizationId = await _organizationId();
    final List<dynamic> rows = await _client
        .from('students')
        .select()
        .eq('organization_id', organizationId)
        .order('updated_at', ascending: false);

    return rows
        .map(
          (dynamic row) => StudentRecord.fromJson(
            Map<String, dynamic>.from(row as Map),
          ),
        )
        .toList(growable: false);
  }

  Future<StudentRecord> createStudent({
    required String name,
    String? email,
    String objective = 'Geral',
    String level = 'Iniciante',
    String? nextSession,
  }) async {
    final String organizationId = await _organizationId();

    final Map<String, dynamic> row = await _client
        .from('students')
        .insert(<String, dynamic>{
          'organization_id': organizationId,
          'name': name.trim(),
          'email': _nullable(email),
          'objective': objective.trim(),
          'level': level.trim(),
          'next_session': _nullable(nextSession),
        })
        .select()
        .single();

    return StudentRecord.fromJson(row);
  }

  Future<void> updateStudent({
    required String studentId,
    String? name,
    String? email,
    String? objective,
    String? level,
    int? adherence,
    String? nextSession,
    String? status,
  }) async {
    final String organizationId = await _organizationId();
    final Map<String, dynamic> patch = <String, dynamic>{};

    if (name != null) patch['name'] = name.trim();
    if (email != null) patch['email'] = _nullable(email);
    if (objective != null) patch['objective'] = objective.trim();
    if (level != null) patch['level'] = level.trim();
    if (adherence != null) patch['adherence'] = adherence.clamp(0, 100);
    if (nextSession != null) patch['next_session'] = _nullable(nextSession);
    if (status != null) patch['status'] = status.trim();

    if (patch.isEmpty) return;

    await _client
        .from('students')
        .update(patch)
        .eq('id', studentId)
        .eq('organization_id', organizationId);
  }

  Future<void> deleteStudent(String studentId) async {
    final String organizationId = await _organizationId();
    await _client
        .from('students')
        .delete()
        .eq('id', studentId)
        .eq('organization_id', organizationId);
  }

  Future<List<TrainingPlanRecord>> fetchTrainingPlans({String? studentId}) async {
    final String organizationId = await _organizationId();
    var query = _client
        .from('training_plans')
        .select()
        .eq('organization_id', organizationId);

    if (studentId != null && studentId.isNotEmpty) {
      query = query.eq('student_id', studentId);
    }

    final List<dynamic> rows = await query.order('updated_at', ascending: false);

    return rows
        .map(
          (dynamic row) => TrainingPlanRecord.fromJson(
            Map<String, dynamic>.from(row as Map),
          ),
        )
        .toList(growable: false);
  }

  Future<String> createTrainingPlan({
    required String studentId,
    required String name,
    required List<TrainingExerciseDraft> exercises,
    String? nextSession,
    String? notes,
    String? decisionReason,
    String? decisionIntelligenceRunId,
    String? sourceTemplateId,
  }) async {
    if (exercises.isEmpty) {
      throw ArgumentError.value(exercises, 'exercises', 'Informe pelo menos um exercício.');
    }

    final String? intelligenceRun = _nullable(decisionIntelligenceRunId);
    final String? templateId = _nullable(sourceTemplateId);
    final dynamic result = await _client.rpc(
      'create_training_plan_v2',
      params: <String, dynamic>{
        'p_student_id': studentId,
        'p_name': name.trim(),
        'p_next_session': _nullable(nextSession),
        'p_notes': _nullable(notes),
        'p_exercises': exercises
            .map((TrainingExerciseDraft exercise) => exercise.toJson())
            .toList(growable: false),
        'p_decision_reason': _nullable(decisionReason),
        'p_source_template_id': templateId,
        'p_trigger_context': <String, dynamic>{
          'source': intelligenceRun == null
              ? 'professor_dashboard'
              : 'decision_intelligence',
          'human_confirmed': true,
          if (intelligenceRun != null)
            'decision_intelligence_run_id': intelligenceRun,
          if (templateId != null) 'source_template_id': templateId,
        },
      },
    );

    final String planId = result?.toString() ?? '';
    if (planId.isEmpty) {
      throw StateError('O treino foi processado sem retornar um identificador.');
    }

    return planId;
  }

  Future<String> issueStudentAccessToken(String studentId) async {
    final dynamic result = await _client.rpc(
      'issue_student_access_token',
      params: <String, dynamic>{'p_student_id': studentId},
    );

    final String token = result?.toString() ?? '';
    if (!RegExp(r'^[0-9a-fA-F]{64}$').hasMatch(token)) {
      throw StateError('O FitNexus não retornou um acesso de aluno válido.');
    }
    return token;
  }

  String? _nullable(String? value) {
    final String normalized = (value ?? '').trim();
    return normalized.isEmpty ? null : normalized;
  }
}
