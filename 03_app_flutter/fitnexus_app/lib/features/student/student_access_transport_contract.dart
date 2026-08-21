enum StudentAccessTransportMode {
  directRpc,
  edgeGateway,
}

StudentAccessTransportMode resolveStudentAccessTransportMode({
  required StudentAccessTransportMode configuredMode,
  required bool explicitRollbackRequested,
  required bool explicitRollbackAuthorized,
}) {
  if (!explicitRollbackRequested) return configuredMode;
  if (!explicitRollbackAuthorized) {
    throw StateError('Rollback do transporte estudantil não autorizado.');
  }
  if (configuredMode != StudentAccessTransportMode.edgeGateway) {
    throw StateError('Rollback explícito exige Edge como transporte configurado.');
  }
  return StudentAccessTransportMode.directRpc;
}

/// Repository-first client transport contract for the student possession-token
/// surface. Stage 30 still keeps [activeMode] on [directRpc]. The rollback
/// controls are explicit configuration, never an exception-driven fallback.
abstract final class StudentAccessTransportContract {
  static const StudentAccessTransportMode activeMode =
      StudentAccessTransportMode.directRpc;

  static const String edgeFunctionName = 'student-access-gateway';

  static const bool edgeGatewaySelected = false;
  static const bool automaticEdgeToDirectFallback = false;
  static const bool explicitRollbackRequested = false;
  static const bool explicitRollbackAuthorized = false;
  static const bool directRpcExecuteRevoked = false;
  static const bool rollbackVerified = false;
  static const bool clientCutoverVerified = false;

  static StudentAccessTransportMode get resolvedMode =>
      resolveStudentAccessTransportMode(
        configuredMode: activeMode,
        explicitRollbackRequested: explicitRollbackRequested,
        explicitRollbackAuthorized: explicitRollbackAuthorized,
      );

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
