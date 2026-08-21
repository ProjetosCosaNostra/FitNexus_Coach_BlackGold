import 'package:fitnexus_app/features/student/student_access_transport.dart';
import 'package:fitnexus_app/features/student/student_access_transport_contract.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

void main() {
  group('Stage 31 client Edge verification seam', () {
    test('production transport constants remain direct and rollback-inert', () {
      expect(
        StudentAccessTransportContract.activeMode,
        StudentAccessTransportMode.directRpc,
      );
      expect(StudentAccessTransportContract.edgeGatewaySelected, isFalse);
      expect(StudentAccessTransportContract.automaticEdgeToDirectFallback, isFalse);
      expect(StudentAccessTransportContract.explicitRollbackRequested, isFalse);
      expect(StudentAccessTransportContract.explicitRollbackAuthorized, isFalse);
      expect(StudentAccessTransportContract.directRpcExecuteRevoked, isFalse);
      expect(StudentAccessTransportContract.clientCutoverVerified, isFalse);
    });

    test('verification factory accepts an explicit Edge mode without network I/O',
        () async {
      final client = SupabaseClient(
        'https://stage31-verification.invalid',
        'stage31-public-synthetic-key',
      );
      final transport = StudentAccessTransport.forVerification(
        client: client,
        configuredMode: StudentAccessTransportMode.edgeGateway,
      );

      await expectLater(
        transport.invoke(
          action: 'stage31_unsupported_action',
          directParams: const <String, dynamic>{},
          edgePayload: const <String, dynamic>{},
        ),
        throwsStateError,
      );
    });
  });
}
