import 'package:flutter/foundation.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import 'student_access_edge_error_contract.dart';
import 'student_access_error_contract.dart';
import 'student_access_transport_contract.dart';

/// Single client-side transport boundary for every student possession-token
/// action. Stage 32 selects the authority-owned Edge gateway for all five
/// production routes as one security boundary. The direct RPC branch remains
/// present only for explicit controlled rollback while its grants are still
/// intentionally intact; Edge failures never trigger it automatically.
///
/// Verification seams are test/integration-proof only. Production feature
/// repositories continue to use [instance].
class StudentAccessTransport {
  StudentAccessTransport._({
    this._clientOverride,
    this._configuredModeOverride,
    this._explicitRollbackRequestedOverride,
    this._explicitRollbackAuthorizedOverride,
  });

  static final StudentAccessTransport instance = StudentAccessTransport._();

  /// Test/integration-proof seam only. Production feature repositories are
  /// forbidden by source guards from referencing this constructor.
  @visibleForTesting
  factory StudentAccessTransport.forVerification({
    required SupabaseClient client,
    required StudentAccessTransportMode configuredMode,
  }) {
    return StudentAccessTransport._(
      _clientOverride: client,
      _configuredModeOverride: configuredMode,
      _explicitRollbackRequestedOverride: false,
      _explicitRollbackAuthorizedOverride: false,
    );
  }

  /// Sealed post-cutover rollback-proof seam only. This exercises the same
  /// resolver and direct-RPC branch used by [invoke], but requires the configured
  /// mode to be Edge and forces both explicit rollback gates true inside the
  /// isolated proof object. It never mutates the production singleton or the
  /// production constants, and production repositories are forbidden from using
  /// it by the Stage 32 rollback source guard.
  @visibleForTesting
  factory StudentAccessTransport.forAuthorizedRollbackProof({
    required SupabaseClient client,
  }) {
    return StudentAccessTransport._(
      _clientOverride: client,
      _configuredModeOverride: StudentAccessTransportMode.edgeGateway,
      _explicitRollbackRequestedOverride: true,
      _explicitRollbackAuthorizedOverride: true,
    );
  }

  final SupabaseClient? _clientOverride;
  final StudentAccessTransportMode? _configuredModeOverride;
  final bool? _explicitRollbackRequestedOverride;
  final bool? _explicitRollbackAuthorizedOverride;

  SupabaseClient get _client => _clientOverride ?? Supabase.instance.client;

  StudentAccessTransportMode get _configuredMode =>
      _configuredModeOverride ?? StudentAccessTransportContract.activeMode;

  bool get _explicitRollbackRequested =>
      _explicitRollbackRequestedOverride ??
      StudentAccessTransportContract.explicitRollbackRequested;

  bool get _explicitRollbackAuthorized =>
      _explicitRollbackAuthorizedOverride ??
      StudentAccessTransportContract.explicitRollbackAuthorized;

  Future<dynamic> invoke({
    required String action,
    required Map<String, dynamic> directParams,
    required Map<String, dynamic> edgePayload,
  }) async {
    final String? directRpc =
        StudentAccessTransportContract.actionToDirectRpc[action];
    if (directRpc == null) {
      throw StateError('Ação de aluno não autorizada pelo transporte: $action');
    }

    final StudentAccessTransportMode configuredMode = _configuredMode;
    final StudentAccessTransportMode resolvedMode =
        resolveStudentAccessTransportMode(
      configuredMode: configuredMode,
      explicitRollbackRequested: _explicitRollbackRequested,
      explicitRollbackAuthorized: _explicitRollbackAuthorized,
    );
    if (!_explicitRollbackRequested && resolvedMode != configuredMode) {
      throw StateError('Divergência inesperada no transporte estudantil.');
    }

    switch (resolvedMode) {
      case StudentAccessTransportMode.directRpc:
        return _client.rpc(directRpc, params: directParams);
      case StudentAccessTransportMode.edgeGateway:
        return _invokeEdge(action: action, payload: edgePayload);
    }
  }

  Future<dynamic> _invokeEdge({
    required String action,
    required Map<String, dynamic> payload,
  }) async {
    try {
      final response = await _client.functions.invoke(
        StudentAccessTransportContract.edgeFunctionName,
        body: <String, dynamic>{
          'action': action,
          ...payload,
        },
      );
      return response.data;
    } on FunctionException catch (error) {
      final Map<String, dynamic> normalized =
          normalizeStudentEdgeFunctionException(
        status: error.status,
        details: error.details,
      );
      final String code = normalized['error']?.toString() ??
          'STUDENT_GATEWAY_REQUEST_FAILED';
      final StudentAccessErrorContext context =
          action == 'get_feedback_context' || action == 'submit_feedback'
              ? StudentAccessErrorContext.feedback
              : StudentAccessErrorContext.workout;
      throw studentAccessStateError(code, context: context);
    }
  }
}
