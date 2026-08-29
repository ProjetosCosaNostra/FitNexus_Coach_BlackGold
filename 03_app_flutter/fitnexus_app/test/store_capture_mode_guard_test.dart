import 'package:flutter_test/flutter_test.dart';
import 'package:fitnexus_app/features/professor/professor_coach_action_repository.dart';

void main() {
  test('Play Store synthetic capture mode is disabled in normal builds', () {
    expect(fitNexusStoreCaptureMode, isFalse);
  });
}
