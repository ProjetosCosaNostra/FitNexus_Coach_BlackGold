import 'package:fitnexus_app/features/professor/professor_decision_intelligence_repository.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('brief keeps confidence, guardrail recommendation and candidate diff', () {
    final DecisionIntelligenceBrief brief =
        DecisionIntelligenceBrief.fromJson(<String, dynamic>{
      'run_id': 'run-11',
      'engine': <String, dynamic>{
        'version': 'blackgold_deterministic_v1',
        'mode': 'deterministic_fallback',
      },
      'student': <String, dynamic>{
        'student_id': 'student-1',
        'name': 'Mariana',
        'objective': 'Hipertrofia',
        'level': 'Intermediário',
        'adherence': 92,
      },
      'risk': <String, dynamic>{'level': 'low'},
      'confidence': <String, dynamic>{'score': 90, 'label': 'high'},
      'recommendation': <String, dynamic>{
        'type': 'progression_candidate',
        'title': 'Elegível para revisar progressão',
        'reason': 'Aderência alta e execuções concluídas.',
      },
      'evidence': <Map<String, dynamic>>[
        <String, dynamic>{
          'type': 'adherence',
          'label': 'Aderência atual',
          'value': 92,
          'unit': '%',
        },
      ],
      'candidate': <String, dynamic>{
        'template_id': 'template-2',
        'template_name': 'Hipertrofia Progressão',
        'objective': 'Hipertrofia',
        'level': 'Intermediário',
        'proposed_exercises': <Map<String, dynamic>>[
          <String, dynamic>{'name': 'Agachamento', 'prescription': '4x8'},
          <String, dynamic>{'name': 'Remada', 'prescription': '4x10'},
        ],
        'proposed_diff': <String, dynamic>{
          'has_previous_plan': true,
          'active_plan_id': 'plan-1',
          'active_plan_name': 'Treino A',
          'added': <Map<String, dynamic>>[
            <String, dynamic>{'name': 'Remada'},
          ],
          'removed': <Map<String, dynamic>>[],
          'changed': <Map<String, dynamic>>[
            <String, dynamic>{
              'name': 'Agachamento',
              'before': '3x10',
              'after': '4x8',
            },
          ],
        },
      },
      'generated_at': '2026-08-18T21:03:00Z',
    });

    expect(brief.runId, 'run-11');
    expect(brief.engineMode, 'deterministic_fallback');
    expect(brief.confidenceScore, 90);
    expect(brief.hasCandidate, isTrue);
    expect(brief.candidate!.exercises.length, 2);
    expect(brief.candidate!.diff.added, contains('Remada'));
    expect(brief.candidate!.diff.changed.single, contains('3x10'));
    expect(brief.candidate!.diff.changed.single, contains('4x8'));
    expect(brief.evidence.single.displayValue, '92%');
  });

  test('high-risk brief can deliberately block automatic candidate', () {
    final DecisionIntelligenceBrief brief =
        DecisionIntelligenceBrief.fromJson(<String, dynamic>{
      'run_id': 'run-12',
      'engine': <String, dynamic>{
        'version': 'blackgold_deterministic_v1',
        'mode': 'deterministic_fallback',
      },
      'student': <String, dynamic>{
        'student_id': 'student-2',
        'name': 'Carlos',
        'objective': 'Condicionamento',
        'level': 'Iniciante',
        'adherence': 75,
      },
      'risk': <String, dynamic>{'level': 'high'},
      'confidence': <String, dynamic>{'score': 85, 'label': 'high'},
      'recommendation': <String, dynamic>{
        'type': 'priority_human_review',
        'title': 'Revisão prioritária antes de progredir',
        'reason': 'Dor ou desconforto alto no feedback recente.',
      },
      'evidence': <dynamic>[],
      'candidate': null,
      'candidate_block_reason': 'HIGH_PAIN_REQUIRES_HUMAN_REVIEW',
      'generated_at': '2026-08-18T21:04:00Z',
    });

    expect(brief.riskLevel, 'high');
    expect(brief.hasCandidate, isFalse);
    expect(
      brief.candidateBlockReason,
      'HIGH_PAIN_REQUIRES_HUMAN_REVIEW',
    );
  });
}
