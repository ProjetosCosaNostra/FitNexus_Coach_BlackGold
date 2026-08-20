import 'package:supabase_flutter/supabase_flutter.dart';

import 'student_access_transport_contract.dart';

/// Single client-side transport boundary for every student possession-token
/// action. Stage 30 keeps the active mode on direct RPC while compiling the
/// Edge path behind the same interface.
///
/// There is intentionally no try/catch that falls back from Edge to a direct
/// RPC. Once Edge becomes active, any Edge failure must remain fail-closed.
class StudentAccessTransport {
  StudentAccessTransport._();

  static final StudentAccessTransport instance = StudentAccessTransport._();

  SupabaseClient get _client => Supabase.instance.client;

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

    switch (StudentAccessTransportContract.activeMode) {
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
    final response = await _client.functions.invoke(
      StudentAccessTransportContract.edgeFunctionName,
      body: <String, dynamic>{
        'action': action,
        ...payload,
      },
    );
    return response.data;
  }
}
