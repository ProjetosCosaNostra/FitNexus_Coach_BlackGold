import 'package:flutter_test/flutter_test.dart';
import 'package:fitnexus_app/features/student/student_access_transport_contract.dart';

void main() {
  group('Stage 30 runtime rollback proof', () {
    test('production transport remains direct and rollback controls stay inert - historical Stage 30 resolver receipt', () {
      expect(
        resolveStudentAccessTransportMode(
          configuredMode: StudentAccessTransportMode.directRpc,
          explicitRollbackRequested: false,
          explicitRollbackAuthorized: false,
        ),
        StudentAccessTransportMode.directRpc,
      );
      expect(StudentAccessTransportContract.automaticEdgeToDirectFallback, isFalse);
      expect(StudentAccessTransportContract.explicitRollbackRequested, isFalse);
      expect(StudentAccessTransportContract.explicitRollbackAuthorized, isFalse);
      expect(StudentAccessTransportContract.directRpcExecuteRevoked, isFalse);
      expect(StudentAccessTransportContract.rollbackVerified, isFalse);
      expect(StudentAccessTransportContract.clientCutoverVerified, isFalse);
    });

    test('Stage 32 current production selection is Edge and rollback-inert', () {
      expect(
        StudentAccessTransportContract.activeMode,
        StudentAccessTransportMode.edgeGateway,
      );
      expect(
        StudentAccessTransportContract.resolvedMode,
        StudentAccessTransportMode.edgeGateway,
      );
      expect(StudentAccessTransportContract.edgeGatewaySelected, isTrue);
      expect(StudentAccessTransportContract.directRpcExecuteRevoked, isFalse);
      expect(StudentAccessTransportContract.rollbackVerified, isFalse);
      expect(StudentAccessTransportContract.clientCutoverVerified, isFalse);
    });

    test('configured Edge stays Edge when rollback was not requested', () {
      expect(
        resolveStudentAccessTransportMode(
          configuredMode: StudentAccessTransportMode.edgeGateway,
          explicitRollbackRequested: false,
          explicitRollbackAuthorized: false,
        ),
        StudentAccessTransportMode.edgeGateway,
      );
    });

    test('unauthorized rollback request fails closed', () {
      expect(
        () => resolveStudentAccessTransportMode(
          configuredMode: StudentAccessTransportMode.edgeGateway,
          explicitRollbackRequested: true,
          explicitRollbackAuthorized: false,
        ),
        throwsA(isA<StateError>()),
      );
    });

    test('authorized explicit Edge rollback resolves to direct RPC', () {
      expect(
        resolveStudentAccessTransportMode(
          configuredMode: StudentAccessTransportMode.edgeGateway,
          explicitRollbackRequested: true,
          explicitRollbackAuthorized: true,
        ),
        StudentAccessTransportMode.directRpc,
      );
    });

    test('rollback is rejected when the configured transport is already direct', () {
      expect(
        () => resolveStudentAccessTransportMode(
          configuredMode: StudentAccessTransportMode.directRpc,
          explicitRollbackRequested: true,
          explicitRollbackAuthorized: true,
        ),
        throwsA(isA<StateError>()),
      );
    });

    test('authorized resolver is deterministic and does not require a network client', () {
      for (var i = 0; i < 3; i++) {
        expect(
          resolveStudentAccessTransportMode(
            configuredMode: StudentAccessTransportMode.edgeGateway,
            explicitRollbackRequested: true,
            explicitRollbackAuthorized: true,
          ),
          StudentAccessTransportMode.directRpc,
        );
      }
    });
  });
}
