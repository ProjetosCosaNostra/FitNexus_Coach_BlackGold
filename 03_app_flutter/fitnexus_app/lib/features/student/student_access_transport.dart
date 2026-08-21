import 'package:flutter/foundation.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import 'student_access_edge_error_contract.dart';
import 'student_access_error_contract.dart';
import 'student_access_transport_contract.dart';

/// Single client-side transport boundary for every student possession-token
/// action. Production remains on the authority-owned direct RPC mode until a
/// separate cutover stage explicitly changes that contract.
///
/// Stage 31 exposes a verification-only constructor so the already compiled
/// Edge path can be exercised with an injected client and explicit mode while
/// production repositories continue to use [instance]. Edge failures are
/// normalized and never trigger a per-request direct-RPC fallback.
class StudentAccessTransport {
  StudentAccessTransport._({
    SupabaseClient? clientOverride,
    StudentAccessTransportMode? configuredModeOverride,
    bool? explicitRollbackRequestedOverride,
    bool? explicitRollbackAuthorizedOverride,
  })  : _clientOverride = clientOverride,
        _configuredModeOverride = configuredModeOverride,
        _explicitRollbackRequestedOverride =
            explicitRollbackRequestedOverride,
        _explicitRollbackAuthorizedOverride =
            explicitRollbackAuthorizedOverride;

  static final StudentAccessTransport instance = StudentAccessTransport._();

  /// Test/integration-proof seam only. Production feature repositories are
  /// forbidden by source guards from referencing this constructor.
  @visibleForTesting
  factory StudentAccessTransport.forVerification({
    required SupabaseClient client,
    required StudentAccessTransportMode configuredMode,
  }) {
    return StudentAccessTransport._(
      clientOverride: client,
      configuredModeOverride: configuredMode,
      explicitRollbackRequestedOverride: false,
      explicitRollbackAuthorizedOverride: false,
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
