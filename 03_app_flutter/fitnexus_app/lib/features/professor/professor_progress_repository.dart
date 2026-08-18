import 'package:supabase_flutter/supabase_flutter.dart';

import '../auth/auth_service.dart';

class ProfessorProgressSummary {
  const ProfessorProgressSummary({
    required this.students,
    required this.activePlans,
    required this.averageAdherence,
    required this.sessions7d,
    required this.completed7d,
    required this.completionRate7d,
    required this.highRisk,
    required this.mediumRisk,
    required this.newStudents,
  });

  final int students;
  final int activePlans;
  final int averageAdherence;
  final int sessions7d;
  final int completed7d;
  final int completionRate7d;
  final int highRisk;
  final int mediumRisk;
  final int newStudents;

  factory ProfessorProgressSummary.fromJson(Map<String, dynamic> json) {
    int number(String key) => (json[key] as num?)?.toInt() ?? 0;

    return ProfessorProgressSummary(
      students: number('students'),
      activePlans: number('active_plans'),
      averageAdherence: number('average_adherence'),
      sessions7d: number('sessions_7d'),
      completed7d: number('completed_7d'),
      completionRate7d: number('completion_rate_7d'),
      highRisk: number('high_risk'),
      mediumRisk: number('medium_risk'),
      newStudents: number('new_students'),
    );
  }
}

class StudentProgressRecord {
  const StudentProgressRecord({
    required this.studentId,
    required this.name,
    required this.objective,
    required this.level,
    required this.status,
    required this.adherence,
    required this.sessions30d,
    required this.completed30d,
    required this.completionRate30d,
    required this.riskLevel,
    required this.riskReason,
    required this.nextBestAction,
    this.lastSessionAt,
    this.lastCompletedAt,
  });

  final String studentId;
  final String name;
  final String objective;
  final String level;
  final String status;
  final int adherence;
  final int sessions30d;
  final int completed30d;
  final int completionRate30d;
  final DateTime? lastSessionAt;
  final DateTime? lastCompletedAt;
  final String riskLevel;
  final String riskReason;
  final String nextBestAction;

  factory StudentProgressRecord.fromJson(Map<String, dynamic> json) {
    return StudentProgressRecord(
      studentId: json['student_id'] as String? ?? '',
      name: json['name'] as String? ?? 'Aluno',
      objective: json['objective'] as String? ?? 'Geral',
      level: json['level'] as String? ?? 'Iniciante',
      status: json['status'] as String? ?? 'Ativo',
      adherence: (json['adherence'] as num?)?.toInt() ?? 0,
      sessions30d: (json['sessions_30d'] as num?)?.toInt() ?? 0,
      completed30d: (json['completed_30d'] as num?)?.toInt() ?? 0,
      completionRate30d:
          (json['completion_rate_30d'] as num?)?.toInt() ?? 0,
      lastSessionAt: _dateTime(json['last_session_at']),
      lastCompletedAt: _dateTime(json['last_completed_at']),
      riskLevel: json['risk_level'] as String? ?? 'new',
      riskReason: json['risk_reason'] as String? ?? 'Sem dados suficientes',
      nextBestAction: json['next_best_action'] as String? ??
          'Acompanhar a próxima execução',
    );
  }
}

class RecentWorkoutSessionRecord {
  const RecentWorkoutSessionRecord({
    required this.sessionId,
    required this.studentId,
    required this.studentName,
    required this.planName,
    required this.status,
    required this.startedAt,
    required this.completedExercises,
    required this.totalExercises,
    required this.completionPercent,
    this.completedAt,
  });

  final String sessionId;
  final String studentId;
  final String studentName;
  final String planName;
  final String status;
  final DateTime startedAt;
  final DateTime? completedAt;
  final int completedExercises;
  final int totalExercises;
  final int completionPercent;

  factory RecentWorkoutSessionRecord.fromJson(Map<String, dynamic> json) {
    return RecentWorkoutSessionRecord(
      sessionId: json['session_id'] as String? ?? '',
      studentId: json['student_id'] as String? ?? '',
      studentName: json['student_name'] as String? ?? 'Aluno',
      planName: json['plan_name'] as String? ?? 'Treino',
      status: json['status'] as String? ?? 'in_progress',
      startedAt: _dateTime(json['started_at']) ??
          DateTime.fromMillisecondsSinceEpoch(0),
      completedAt: _dateTime(json['completed_at']),
      completedExercises:
          (json['completed_exercises'] as num?)?.toInt() ?? 0,
      totalExercises: (json['total_exercises'] as num?)?.toInt() ?? 0,
      completionPercent:
          (json['completion_percent'] as num?)?.toInt() ?? 0,
    );
  }
}

class ProfessorProgressSnapshot {
  const ProfessorProgressSnapshot({
    required this.summary,
    required this.students,
    required this.recentSessions,
    required this.generatedAt,
  });

  final ProfessorProgressSummary summary;
  final List<StudentProgressRecord> students;
  final List<RecentWorkoutSessionRecord> recentSessions;
  final DateTime generatedAt;

  factory ProfessorProgressSnapshot.fromJson(Map<String, dynamic> json) {
    final Map<String, dynamic> summary = _map(json['summary']);
    final List<dynamic> students =
        json['students'] as List<dynamic>? ?? const <dynamic>[];
    final List<dynamic> recent =
        json['recent_sessions'] as List<dynamic>? ?? const <dynamic>[];

    return ProfessorProgressSnapshot(
      summary: ProfessorProgressSummary.fromJson(summary),
      students: students
          .map((dynamic row) => StudentProgressRecord.fromJson(_map(row)))
          .toList(growable: false),
      recentSessions: recent
          .map((dynamic row) => RecentWorkoutSessionRecord.fromJson(_map(row)))
          .toList(growable: false),
      generatedAt: _dateTime(json['generated_at']) ?? DateTime.now(),
    );
  }
}

class ProfessorProgressRepository {
  ProfessorProgressRepository._();

  static final ProfessorProgressRepository instance =
      ProfessorProgressRepository._();

  SupabaseClient get _client => Supabase.instance.client;

  Future<ProfessorProgressSnapshot> fetchDashboard() async {
    final String organizationId =
        await AuthService.instance.ensureProfessorOrganization();

    final dynamic result = await _client.rpc(
      'get_professor_progress_dashboard',
      params: <String, dynamic>{'p_organization_id': organizationId},
    );

    return ProfessorProgressSnapshot.fromJson(_map(result));
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
