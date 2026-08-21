import 'package:flutter_test/flutter_test.dart';
import 'package:fitnexus_app/features/student/student_access_transport_contract.dart';

void main() {
  group('student transport rollback harness', () {
    test('direct mode remains direct without rollback request', () {
      expect(
        resolveStudentAccessTransportMode(
          configuredMode: StudentAccessTransportMode.directRpc,
          explicitRollbackRequested: false,
          explicitRollbackAuthorized: false,
        ),
        StudentAccessTransportMode.directRpc,
      );
    });

    test('Edge mode remains Edge without rollback request', () {
      expect(
        resolveStudentAccessTransportMode(
          configuredMode: StudentAccessTransportMode.edgeGateway,
          explicitRollbackRequested: false,
          explicitRollbackAuthorized: false,
        ),
        StudentAccessTransportMode.edgeGateway,
      );
    });

    test('rollback request fails closed without explicit authorization', () {
      expect(
        () => resolveStudentAccessTransportMode(
          configuredMode: StudentAccessTransportMode.edgeGateway,
          explicitRollbackRequested: true,
          explicitRollbackAuthorized: false,
        ),
        throwsStateError,
      );
    });

    test('authorized explicit rollback is a mode transition to direct RPC', () {
      expect(
        resolveStudentAccessTransportMode(
          configuredMode: StudentAccessTransportMode.edgeGateway,
          explicitRollbackRequested: true,
          explicitRollbackAuthorized: true,
        ),
        StudentAccessTransportMode.directRpc,
      );
    });

    test('rollback request is rejected when Edge was not configured', () {
      expect(
        () => resolveStudentAccessTransportMode(
          configuredMode: StudentAccessTransportMode.directRpc,
          explicitRollbackRequested: true,
          explicitRollbackAuthorized: true,
        ),
        throwsStateError,
      );
    });

    test('production constants do not request or self-authorize rollback', () {
      expect(StudentAccessTransportContract.activeMode,
          StudentAccessTransportMode.directRpc);
      expect(StudentAccessTransportContract.explicitRollbackRequested, isFalse);
      expect(StudentAccessTransportContract.explicitRollbackAuthorized, isFalse);
      expect(StudentAccessTransportContract.rollbackVerified, isFalse);
      expect(StudentAccessTransportContract.resolvedMode,
          StudentAccessTransportMode.directRpc);
    });
  });
}
