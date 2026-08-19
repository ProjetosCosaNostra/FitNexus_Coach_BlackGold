import 'package:fitnexus_app/features/professor/professor_coach_action_repository.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('action center parses priority, evidence and human guardrail', () {
    final CoachActionSnapshot snapshot = CoachActionSnapshot.fromJson(
      <String, dynamic>{
        'summary': <String, dynamic>{
          'active_actions': 3,
          'urgent': 1,
          'attention': 1,
          'setup': 1,
          'monitor': 0,
          'completed_today': 2,
          'snoozed': 1,
        },
        'actions': <Map<String, dynamic>>[
          <String, dynamic>{
            'student_id': 'student-1',
            'student_name': 'Mariana',
            'objective': 'Hipertrofia',
            'level': 'Intermediário',
            'student_status': 'Ativo',
            'adherence': 84,
            'sessions_30d': 4,
            'completed_30d': 4,
            'last_session_at': '2026-08-18T20:00:00Z',
            'priority_score': 100,
            'priority_label': 'urgent',
            'action_type': 'feedback_priority_review',
            'action_title': 'Revisar dor/desconforto agora',
            'action_reason': 'Dor alta registrada.',
            'target': 'feedback',
            'action_fingerprint':
                'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
            'evidence': <String, dynamic>{
              'pain_score': 8,
              'pain_location': 'joelho',
              'perceived_exertion': 9,
              'energy_score': 2,
              'has_active_access': true,
            },
            'guardrails': <String, dynamic>{
              'auto_execute': false,
              'auto_change_prescription': false,
              'human_action_required': true,
            },
          },
        ],
        'principle':
            'O FitNexus prioriza e explica; o professor decide e executa.',
        'generated_at': '2026-08-18T23:00:00Z',
      },
    );

    expect(snapshot.summary.activeActions, 3);
    expect(snapshot.summary.completedToday, 2);
    expect(snapshot.actions.single.urgent, isTrue);
    expect(snapshot.actions.single.priorityScore, 100);
    expect(snapshot.actions.single.target, 'feedback');
    expect(snapshot.actions.single.evidence.painScore, 8);
    expect(snapshot.actions.single.evidence.hasActiveAccess, isTrue);
    expect(snapshot.actions.single.humanActionRequired, isTrue);
  });

  test('empty action center remains a valid clean queue', () {
    final CoachActionSnapshot snapshot = CoachActionSnapshot.fromJson(
      <String, dynamic>{
        'summary': <String, dynamic>{},
        'actions': <dynamic>[],
        'principle': 'Professor mantém autoridade.',
      },
    );

    expect(snapshot.actions, isEmpty);
    expect(snapshot.summary.activeActions, 0);
    expect(snapshot.summary.urgent, 0);
  });
}
