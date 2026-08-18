import 'package:fitnexus_app/features/professor/professor_template_repository.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Training template keeps exercise order and prescription data', () {
    final TrainingTemplateRecord template = TrainingTemplateRecord.fromJson(
      <String, dynamic>{
        'id': 'template-1',
        'organization_id': 'org-1',
        'name': 'Hipertrofia A',
        'objective': 'Hipertrofia',
        'level': 'Intermediário',
        'is_active': true,
        'training_template_exercises': <Map<String, dynamic>>[
          <String, dynamic>{
            'id': 'e2',
            'position': 1,
            'name': 'Supino reto',
            'prescription': '3x10 • descanso 75s',
          },
          <String, dynamic>{
            'id': 'e1',
            'position': 0,
            'name': 'Agachamento livre',
            'prescription': '4x10 • descanso 90s',
          },
        ],
      },
    );

    expect(template.name, 'Hipertrofia A');
    expect(template.exercises, hasLength(2));
    expect(template.exercises.first.name, 'Agachamento livre');
    expect(template.exercises.last.prescription, contains('75s'));
  });
}
