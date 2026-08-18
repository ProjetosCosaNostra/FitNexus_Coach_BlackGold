import 'package:fitnexus_app/features/professor/professor_lineage_repository.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('lineage record preserves decision origin and exercise diff', () {
    final TrainingLineageRecord record = TrainingLineageRecord.fromJson(
      <String, dynamic>{
        'lineage_id': 'lineage-2',
        'plan_id': 'plan-2',
        'plan_name': 'Treino B',
        'is_active': true,
        'created_at': '2026-08-18T20:30:00Z',
        'predecessor_plan_id': 'plan-1',
        'predecessor_plan_name': 'Treino A',
        'source_template_id': 'template-1',
        'source_template_name': 'Força Base',
        'decision_type': 'template_assignment',
        'decision_reason': 'Prescrição criada a partir do Smart Template “Força Base”',
        'exercise_count': 4,
        'diff': <String, dynamic>{
          'added': <Map<String, dynamic>>[
            <String, dynamic>{'name': 'Terra', 'prescription': '4x5'},
          ],
          'removed': <Map<String, dynamic>>[
            <String, dynamic>{'name': 'Leg press', 'prescription': '3x12'},
          ],
          'changed': <Map<String, dynamic>>[
            <String, dynamic>{
              'name': 'Agachamento',
              'before': '3x10',
              'after': '4x8',
            },
          ],
        },
      },
    );

    expect(record.decisionLabel, 'Smart Template');
    expect(record.sourceTemplateName, 'Força Base');
    expect(record.predecessorPlanName, 'Treino A');
    expect(record.diff.addedCount, 1);
    expect(record.diff.removedCount, 1);
    expect(record.diff.changedCount, 1);
    expect(record.diff.changed.single, contains('3x10'));
    expect(record.diff.changed.single, contains('4x8'));
  });

  test('initial prescription has an empty diff and remains explainable', () {
    final TrainingLineageRecord record = TrainingLineageRecord.fromJson(
      <String, dynamic>{
        'lineage_id': 'lineage-1',
        'plan_id': 'plan-1',
        'plan_name': 'Treino inicial',
        'is_active': false,
        'created_at': '2026-08-18T19:00:00Z',
        'decision_type': 'initial_prescription',
        'decision_reason': 'Prescrição inicial criada pelo professor',
        'exercise_count': 3,
        'diff': <String, dynamic>{
          'added': <dynamic>[],
          'removed': <dynamic>[],
          'changed': <dynamic>[],
        },
      },
    );

    expect(record.decisionLabel, 'Prescrição inicial');
    expect(record.diff.hasChanges, isFalse);
  });

  test('controlled restore has an explicit lineage label', () {
    final TrainingLineageRecord record = TrainingLineageRecord.fromJson(
      <String, dynamic>{
        'lineage_id': 'lineage-3',
        'plan_id': 'plan-3',
        'plan_name': 'Treino A',
        'is_active': true,
        'created_at': '2026-08-18T21:00:00Z',
        'predecessor_plan_id': 'plan-2',
        'decision_type': 'restoration',
        'decision_reason': 'Restaurado após revisão clínica do histórico',
        'exercise_count': 3,
        'diff': <String, dynamic>{
          'added': <dynamic>[],
          'removed': <dynamic>[],
          'changed': <dynamic>[],
        },
      },
    );

    expect(record.decisionLabel, 'Restauração controlada');
    expect(record.isActive, isTrue);
  });

  test('change preview parses added removed and changed exercises', () {
    final TrainingChangePreview preview = TrainingChangePreview.fromJson(
      <String, dynamic>{
        'has_previous_plan': true,
        'active_plan_id': 'plan-1',
        'active_plan_name': 'Treino A',
        'added': <Map<String, dynamic>>[
          <String, dynamic>{'name': 'Terra'},
        ],
        'removed': <Map<String, dynamic>>[
          <String, dynamic>{'name': 'Cadeira extensora'},
        ],
        'changed': <Map<String, dynamic>>[
          <String, dynamic>{
            'name': 'Remada',
            'before': '3x12',
            'after': '4x10',
          },
        ],
      },
    );

    expect(preview.hasPreviousPlan, isTrue);
    expect(preview.hasChanges, isTrue);
    expect(preview.added, contains('Terra'));
    expect(preview.removed, contains('Cadeira extensora'));
    expect(preview.changed.single, contains('3x12'));
    expect(preview.changed.single, contains('4x10'));
  });
}
