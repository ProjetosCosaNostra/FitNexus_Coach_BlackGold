import 'package:flutter_test/flutter_test.dart';
import 'package:fitnexus_app/features/student/student_access_transport_contract.dart';

void main() {
  group('StudentAccessTransportContract', () {
    test('Stage 30 keeps the direct transport active', () {
      expect(
        StudentAccessTransportContract.activeMode,
        StudentAccessTransportMode.directRpc,
      );
      expect(StudentAccessTransportContract.edgeGatewaySelected, isFalse);
      expect(StudentAccessTransportContract.directRpcExecuteRevoked, isFalse);
      expect(StudentAccessTransportContract.clientCutoverVerified, isFalse);
      expect(StudentAccessTransportContract.rollbackVerified, isFalse);
    });

    test('never permits automatic Edge to direct fail-open fallback', () {
      expect(
        StudentAccessTransportContract.automaticEdgeToDirectFallback,
        isFalse,
      );
    });

    test('owns exactly the five student routes', () {
      expect(StudentAccessTransportContract.actionToDirectRpc, <String, String>{
        'get_workout': 'get_student_workout_v2',
        'start_workout': 'start_student_workout_v2',
        'set_completion': 'set_student_exercise_completion_v2',
        'get_feedback_context': 'get_student_feedback_context_v2',
        'submit_feedback': 'submit_student_workout_feedback_v2',
      });
      expect(
        StudentAccessTransportContract.readOnlyActions,
        <String>{'get_workout', 'get_feedback_context'},
      );
      expect(
        StudentAccessTransportContract.commandActions,
        <String>{'start_workout', 'set_completion', 'submit_feedback'},
      );
    });
  });
}
