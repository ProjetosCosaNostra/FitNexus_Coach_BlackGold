import 'package:fitnexus_app/features/professor/professor_progress_repository.dart';
import 'package:fitnexus_app/features/student/student_feedback_repository.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('student feedback context restores submitted values', () {
    final StudentFeedbackContext context = StudentFeedbackContext.fromJson(
      <String, dynamic>{
        'eligible': true,
        'submitted': true,
        'session_id': 'session-1',
        'plan_name': 'Treino A',
        'feedback': <String, dynamic>{
          'perceived_exertion': 9,
          'pain_score': 7,
          'energy_score': 2,
          'pain_location': 'Joelho direito',
          'note': 'Desconforto no agachamento',
          'submitted_at': '2026-08-18T20:00:00Z',
        },
      },
    );

    expect(context.eligible, isTrue);
    expect(context.submitted, isTrue);
    expect(context.sessionId, 'session-1');
    expect(context.perceivedExertion, 9);
    expect(context.painScore, 7);
    expect(context.energyScore, 2);
    expect(context.painLocation, 'Joelho direito');
  });

  test('progress model accepts feedback-aware risk signals', () {
    final StudentProgressRecord record = StudentProgressRecord.fromJson(
      <String, dynamic>{
        'student_id': 'student-1',
        'name': 'Mariana',
        'objective': 'Força',
        'level': 'Intermediário',
        'status': 'Treino concluído',
        'adherence': 88,
        'sessions_30d': 6,
        'completed_30d': 6,
        'completion_rate_30d': 100,
        'risk_level': 'high',
        'risk_reason': 'Dor relatada em 8/10 no último feedback',
        'next_best_action': 'Revisar antes da próxima sessão',
        'latest_feedback': <String, dynamic>{
          'session_id': 'session-2',
          'perceived_exertion': 8,
          'pain_score': 8,
          'energy_score': 3,
          'submitted_at': '2026-08-18T20:10:00Z',
        },
      },
    );

    expect(record.riskLevel, 'high');
    expect(record.riskReason, contains('Dor relatada'));
    expect(record.latestFeedback, isNotNull);
    expect(record.latestFeedback!.painScore, 8);
  });

  test('progress summary parses feedback signal counts', () {
    final ProfessorProgressSummary summary =
        ProfessorProgressSummary.fromJson(<String, dynamic>{
      'students': 4,
      'active_plans': 4,
      'average_adherence': 78,
      'sessions_7d': 8,
      'completed_7d': 7,
      'completion_rate_7d': 88,
      'high_risk': 1,
      'medium_risk': 1,
      'new_students': 0,
      'feedback_7d': 6,
      'pain_alerts_7d': 1,
    });

    expect(summary.feedback7d, 6);
    expect(summary.painAlerts7d, 1);
  });
}
