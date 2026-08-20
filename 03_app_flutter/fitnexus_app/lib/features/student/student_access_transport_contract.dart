enum StudentAccessTransportMode {
  directRpc,
  edgeGateway,
}

/// Repository-first client transport contract for the student possession-token
/// surface. Stage 30 intentionally keeps [activeMode] on [directRpc].
///
/// The Edge candidate is compiled/configured as a target contract only. A later
/// cutover stage may change the active mode after runtime rollback proof. There
/// is deliberately no per-request Edge -> direct fallback because that would
/// bypass the network-origin controls enforced by the Edge gateway.
abstract final class StudentAccessTransportContract {
  static const StudentAccessTransportMode activeMode =
      StudentAccessTransportMode.directRpc;

  static const String edgeFunctionName = 'student-access-gateway';

  static const bool edgeGatewaySelected = false;
  static const bool automaticEdgeToDirectFallback = false;
  static const bool directRpcExecuteRevoked = false;
  static const bool rollbackVerified = false;
  static const bool clientCutoverVerified = false;

  static const Map<String, String> actionToDirectRpc = <String, String>{
    'get_workout': 'get_student_workout_v2',
    'start_workout': 'start_student_workout_v2',
    'set_completion': 'set_student_exercise_completion_v2',
    'get_feedback_context': 'get_student_feedback_context_v2',
    'submit_feedback': 'submit_student_workout_feedback_v2',
  };

  static const Set<String> readOnlyActions = <String>{
    'get_workout',
    'get_feedback_context',
  };

  static const Set<String> commandActions = <String>{
    'start_workout',
    'set_completion',
    'submit_feedback',
  };
}
