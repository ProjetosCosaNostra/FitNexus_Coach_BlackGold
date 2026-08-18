import 'package:fitnexus_app/features/professor/professor_progress_repository.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Professor progress snapshot preserves explainable risk signals', () {
    final ProfessorProgressSnapshot snapshot =
        ProfessorProgressSnapshot.fromJson(<String, dynamic>{
      'summary': <String, dynamic>{
        'students': 2,
        'active_plans': 2,
        'average_adherence': 61,
        'sessions_7d': 3,
        'completed_7d': 2,
        'completion_rate_7d': 67,
        'high_risk': 1,
        'medium_risk': 0,
        'new_students': 1,
      },
      'students': <Map<String, dynamic>>[
        <String, dynamic>{
          'student_id': 'student-1',
          'name': 'Ana',
          'objective': 'Hipertrofia',
          'level': 'Intermediário',
          'status': 'Ativo',
          'adherence': 32,
          'sessions_30d': 4,
          'completed_30d': 1,
          'completion_rate_30d': 25,
          'risk_level': 'high',
          'risk_reason': 'Aderência abaixo de 40%',
          'next_best_action': 'Revisar treino e barreiras de execução com o aluno',
        },
      ],
      'recent_sessions': <Map<String, dynamic>>[
        <String, dynamic>{
          'session_id': 'session-1',
          'student_id': 'student-1',
          'student_name': 'Ana',
          'plan_name': 'Treino A',
          'status': 'completed',
          'started_at': '2026-08-18T12:00:00Z',
          'completed_at': '2026-08-18T12:40:00Z',
          'completed_exercises': 4,
          'total_exercises': 4,
          'completion_percent': 100,
        },
      ],
      'generated_at': '2026-08-18T13:00:00Z',
    });

    expect(snapshot.summary.students, 2);
    expect(snapshot.summary.highRisk, 1);
    expect(snapshot.students.single.riskLevel, 'high');
    expect(snapshot.students.single.riskReason, 'Aderência abaixo de 40%');
    expect(snapshot.students.single.nextBestAction, contains('Revisar treino'));
    expect(snapshot.recentSessions.single.completionPercent, 100);
  });

  test('Professor progress snapshot handles an empty workspace', () {
    final ProfessorProgressSnapshot snapshot =
        ProfessorProgressSnapshot.fromJson(<String, dynamic>{
      'summary': <String, dynamic>{},
      'students': <dynamic>[],
      'recent_sessions': <dynamic>[],
      'generated_at': '2026-08-18T13:00:00Z',
    });

    expect(snapshot.summary.students, 0);
    expect(snapshot.summary.completionRate7d, 0);
    expect(snapshot.students, isEmpty);
    expect(snapshot.recentSessions, isEmpty);
  });
}
