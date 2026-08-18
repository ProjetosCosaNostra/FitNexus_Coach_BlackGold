import 'package:supabase_flutter/supabase_flutter.dart';

class StudentWorkoutExercise {
  const StudentWorkoutExercise({
    required this.id,
    required this.position,
    required this.name,
    required this.prescription,
    required this.completed,
    this.completedAt,
  });

  final String id;
  final int position;
  final String name;
  final String prescription;
  final bool completed;
  final DateTime? completedAt;

  int get restSeconds {
    final RegExpMatch? match = RegExp(
      r'(?:descanso\s*)?(\d{1,3})\s*s',
      caseSensitive: false,
    ).firstMatch(prescription);
    return int.tryParse(match?.group(1) ?? '') ?? 60;
  }

  factory StudentWorkoutExercise.fromJson(Map<String, dynamic> json) {
    return StudentWorkoutExercise(
      id: json['id'] as String,
      position: (json['position'] as num?)?.toInt() ?? 0,
      name: json['name'] as String? ?? 'Exercício',
      prescription: json['prescription'] as String? ?? '',
      completed: json['completed'] as bool? ?? false,
      completedAt: _dateTime(json['completed_at']),
    );
  }
}

class StudentWorkoutHistoryItem {
  const StudentWorkoutHistoryItem({
    required this.id,
    required this.planName,
    required this.status,
    required this.completedExercises,
    required this.totalExercises,
    required this.startedAt,
    this.completedAt,
  });

  final String id;
  final String planName;
  final String status;
  final int completedExercises;
  final int totalExercises;
  final DateTime startedAt;
  final DateTime? completedAt;

  int get percent => totalExercises == 0
      ? 0
      : ((completedExercises / totalExercises) * 100).round().clamp(0, 100);

  factory StudentWorkoutHistoryItem.fromJson(Map<String, dynamic> json) {
    return StudentWorkoutHistoryItem(
      id: json['id'] as String,
      planName: json['plan_name'] as String? ?? 'Treino',
      status: json['status'] as String? ?? 'in_progress',
      completedExercises: (json['completed_exercises'] as num?)?.toInt() ?? 0,
      totalExercises: (json['total_exercises'] as num?)?.toInt() ?? 0,
      startedAt: _dateTime(json['started_at']) ?? DateTime.fromMillisecondsSinceEpoch(0),
      completedAt: _dateTime(json['completed_at']),
    );
  }
}

class StudentWorkoutSnapshot {
  const StudentWorkoutSnapshot({
    required this.studentName,
    required this.objective,
    required this.level,
    required this.adherence,
    required this.studentStatus,
    required this.exercises,
    required this.history,
    this.planId,
    this.planName,
    this.planNotes,
    this.nextSession,
    this.sessionId,
    this.sessionStatus,
  });

  final String studentName;
  final String objective;
  final String level;
  final int adherence;
  final String studentStatus;
  final String? planId;
  final String? planName;
  final String? planNotes;
  final String? nextSession;
  final String? sessionId;
  final String? sessionStatus;
  final List<StudentWorkoutExercise> exercises;
  final List<StudentWorkoutHistoryItem> history;

  bool get hasPlan => (planId ?? '').isNotEmpty;
  bool get inProgress => sessionStatus == 'in_progress';
  bool get completed => sessionStatus == 'completed';

  int get completedExercises =>
      exercises.where((StudentWorkoutExercise item) => item.completed).length;

  int get completionPercent => exercises.isEmpty
      ? 0
      : ((completedExercises / exercises.length) * 100).round().clamp(0, 100);

  factory StudentWorkoutSnapshot.fromJson(Map<String, dynamic> json) {
    final Map<String, dynamic> student = _map(json['student']);
    final Map<String, dynamic> plan = _map(json['plan']);
    final Map<String, dynamic> session = _map(json['session']);
    final List<dynamic> exerciseRows = json['exercises'] as List<dynamic>? ?? const <dynamic>[];
    final List<dynamic> historyRows = json['history'] as List<dynamic>? ?? const <dynamic>[];

    return StudentWorkoutSnapshot(
      studentName: student['name'] as String? ?? 'Aluno FitNexus',
      objective: student['objective'] as String? ?? 'Geral',
      level: student['level'] as String? ?? 'Iniciante',
      adherence: (student['adherence'] as num?)?.toInt() ?? 0,
      studentStatus: student['status'] as String? ?? 'Ativo',
      planId: plan['id'] as String?,
      planName: plan['name'] as String?,
      planNotes: plan['notes'] as String?,
      nextSession: plan['next_session'] as String?,
      sessionId: session['id'] as String?,
      sessionStatus: session['status'] as String?,
      exercises: exerciseRows
          .map((dynamic row) => StudentWorkoutExercise.fromJson(_map(row)))
          .toList(growable: false),
      history: historyRows
          .map((dynamic row) => StudentWorkoutHistoryItem.fromJson(_map(row)))
          .toList(growable: false),
    );
  }
}

class StudentWorkoutRepository {
  StudentWorkoutRepository._();

  static final StudentWorkoutRepository instance = StudentWorkoutRepository._();

  SupabaseClient get _client => Supabase.instance.client;

  Future<StudentWorkoutSnapshot> fetchSnapshot(String token) async {
    final dynamic response = await _client.rpc(
      'get_student_workout',
      params: <String, dynamic>{'p_token': token.trim()},
    );
    return StudentWorkoutSnapshot.fromJson(_map(response));
  }

  Future<String> startWorkout(String token) async {
    final dynamic response = await _client.rpc(
      'start_student_workout',
      params: <String, dynamic>{'p_token': token.trim()},
    );
    final String id = response?.toString() ?? '';
    if (id.isEmpty) {
      throw StateError('O FitNexus não retornou a sessão iniciada.');
    }
    return id;
  }

  Future<void> setExerciseCompletion({
    required String token,
    required String sessionId,
    required String exerciseId,
    required bool completed,
  }) async {
    await _client.rpc(
      'set_student_exercise_completion',
      params: <String, dynamic>{
        'p_token': token.trim(),
        'p_session_id': sessionId,
        'p_exercise_id': exerciseId,
        'p_completed': completed,
      },
    );
  }
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
