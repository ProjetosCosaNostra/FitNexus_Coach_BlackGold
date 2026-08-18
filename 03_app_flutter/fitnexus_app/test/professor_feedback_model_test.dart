import 'package:fitnexus_app/features/professor/professor_feedback_repository.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('feedback snapshot classifies high signals and pain alerts', () {
    final ProfessorFeedbackSnapshot snapshot =
        ProfessorFeedbackSnapshot.fromJson(<String, dynamic>{
      'items': <Map<String, dynamic>>[
        <String, dynamic>{
          'feedback_id': 'f1',
          'session_id': 's1',
          'student_id': 'student-1',
          'student_name': 'Mariana',
          'plan_name': 'Treino A',
          'perceived_exertion': 8,
          'pain_score': 8,
          'energy_score': 3,
          'risk_signal': 'high',
          'submitted_at': '2026-08-18T20:00:00Z',
        },
        <String, dynamic>{
          'feedback_id': 'f2',
          'session_id': 's2',
          'student_id': 'student-2',
          'student_name': 'Carlos',
          'plan_name': 'Treino B',
          'perceived_exertion': 6,
          'pain_score': 0,
          'energy_score': 4,
          'risk_signal': 'low',
          'submitted_at': '2026-08-18T20:05:00Z',
        },
      ],
      'generated_at': '2026-08-18T20:10:00Z',
    });

    expect(snapshot.items, hasLength(2));
    expect(snapshot.highSignals, 1);
    expect(snapshot.painAlerts, 1);
    expect(snapshot.items.first.studentName, 'Mariana');
  });
}
