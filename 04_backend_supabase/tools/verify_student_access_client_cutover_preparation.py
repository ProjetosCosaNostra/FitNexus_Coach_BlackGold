from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
APP = ROOT / "03_app_flutter" / "fitnexus_app" / "lib"

AUTHORITY = BACKEND / "student_access_client_cutover_authority.json"
VALID_ROUTE = BACKEND / "student_access_valid_route_authority.json"
EDGE_AUTHORITY = BACKEND / "student_access_edge_gateway_authority.json"
RATE_AUTHORITY = BACKEND / "student_access_network_rate_limit_authority.json"
NETWORK_AUTHORITY = BACKEND / "student_access_network_origin_boundary.json"
CONTRACT = APP / "features" / "student" / "student_access_transport_contract.dart"
TRANSPORT = APP / "features" / "student" / "student_access_transport.dart"
EDGE_ERRORS = APP / "features" / "student" / "student_access_edge_error_contract.dart"
ERROR_MESSAGES = APP / "features" / "student" / "student_access_error_contract.dart"
WORKOUT = APP / "features" / "student" / "student_workout_repository.dart"
FEEDBACK = APP / "features" / "student" / "student_feedback_repository.dart"

FAILURE_CLASSES = [
    "BGF-CLIENT-EDGE-CUTOVER-PREMATURE-195",
    "BGF-CLIENT-TRANSPORT-PARTIAL-CUTOVER-196",
    "BGF-EDGE-FAILOPEN-DIRECT-FALLBACK-197",
    "BGF-DIRECT-RPC-REVOCATION-BEFORE-ROLLBACK-198",
    "BGF-CLIENT-CUTOVER-SELF-ATTESTATION-199",
]
GUARD_FAILURE_CLASSES = [
    "BGF-GUARD-RPC-CALLSITE-COLOCATION-200",
    "BGF-GUARD-COMMENT-SEMANTIC-FALSE-POSITIVE-201",
]
EDGE_DETAIL_FAILURE_CLASS = "BGF-EDGE-CLIENT-ERROR-DETAIL-LEAK-202"
ROUTES = {
    "get_workout": "get_student_workout_v2",
    "start_workout": "start_student_workout_v2",
    "set_completion": "set_student_exercise_completion_v2",
    "get_feedback_context": "get_student_feedback_context_v2",
    "submit_feedback": "submit_student_workout_feedback_v2",
}


def fail(message: str) -> None:
    raise SystemExit("STUDENT_ACCESS_CLIENT_CUTOVER_PREPARATION_GUARD=FAIL\n" + message)


def text(path: Path) -> str:
    if not path.is_file():
        fail(f"missing source: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def data(path: Path) -> dict:
    try:
        return json.loads(text(path))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path.relative_to(ROOT)}: {exc}")
    raise AssertionError("unreachable")


def code_without_comments(source: str) -> str:
    without_blocks = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"//[^\n]*", "", without_blocks)


def main() -> None:
    authority = data(AUTHORITY)
    valid_route = data(VALID_ROUTE)
    edge = data(EDGE_AUTHORITY)
    rate = data(RATE_AUTHORITY)
    network = data(NETWORK_AUTHORITY)
    contract_source = text(CONTRACT)
    transport_source = text(TRANSPORT)
    transport_code = code_without_comments(transport_source)
    edge_errors = code_without_comments(text(EDGE_ERRORS))
    error_messages = code_without_comments(text(ERROR_MESSAGES))
    workout = text(WORKOUT)
    feedback = text(FEEDBACK)

    if authority.get("schema_version") != 2 or authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("Stage 30 authority identity drifted")
    if authority.get("failure_classes") != FAILURE_CLASSES:
        fail("Stage 30 failure-class authority drifted")
    if authority.get("guard_failure_classes") != GUARD_FAILURE_CLASSES:
        fail("Stage 30 guard-failure prevention authority drifted")
    if authority.get("edge_error_detail_failure_class") != EDGE_DETAIL_FAILURE_CLASS:
        fail("Stage 30 Edge detail failure class drifted")
    if authority.get("current_state") != "CLIENT_EDGE_ERROR_CONTRACT_ROLLBACK_HARNESS_READY_DIRECT_MODE":
        fail(f"{FAILURE_CLASSES[4]} Stage 30 error/rollback state drifted")
    if authority.get("baseline_main_sha") != "5f088a361f2ee78a88fc0435250a83d571eda34c":
        fail("Stage 30 error/rollback baseline SHA drifted")

    prerequisites = authority.get("prerequisites", {})
    if valid_route.get("current_state") != "VALID_ROUTE_LIVE_VERIFIED_CLEANUP_COMPLETE":
        fail("Stage 29 valid-route proof/cleanup prerequisite missing")
    vr_runtime = valid_route.get("runtime_verification", {})
    for key in (
        "valid_token_edge_route_verified_live",
        "student_rpc_forwarding_with_valid_token_verified_live",
        "cleanup_completed",
    ):
        if vr_runtime.get(key) is not True:
            fail(f"Stage 29 prerequisite missing: {key}")
    if vr_runtime.get("synthetic_business_rows_remaining") != 0:
        fail("Stage 29 synthetic residue returned")
    for key, expected in {
        "stage29_required_state": "VALID_ROUTE_LIVE_VERIFIED_CLEANUP_COMPLETE",
        "edge_runtime_version": 3,
        "valid_token_edge_route_verified_live": True,
        "valid_route_synthetic_cleanup_complete": True,
        "network_origin_spoof_resistance_verified": True,
        "network_origin_rate_limit_threshold_429_verified": True,
    }.items():
        if prerequisites.get(key) != expected:
            fail(f"Stage 30 prerequisite authority drift for {key}")

    observed_edge = edge.get("observed_deployed_runtime", {})
    if observed_edge.get("version") != 3 or observed_edge.get("status") != "ACTIVE":
        fail("Edge v3 runtime prerequisite disappeared")
    if edge.get("runtime_verification", {}).get("invalid_token_network_origin_rate_limit_threshold_verified_live") is not True:
        fail("Edge exact 429 threshold proof disappeared")
    if rate.get("runtime_boundary", {}).get("invalid_token_network_origin_rate_limit_threshold_verified_live") is not True:
        fail("durable rate-limit authority lost threshold proof")
    if network.get("observed_runtime", {}).get("runtime_origin_candidate_trusted_for_security") is not True:
        fail("trusted network-origin authority disappeared")
    if network.get("observed_runtime", {}).get("spoof_resistance_receipt", {}).get("client_can_force_cf_connecting_ip") is not False:
        fail("trusted origin spoof resistance disappeared")

    inventory = authority.get("current_client_inventory", {})
    for key, expected in {
        "transport_mode": "direct_rpc",
        "flutter_uses_edge_gateway": False,
        "direct_v2_rpc_path_active": True,
        "direct_anon_v2_rpc_execute_revoked": False,
        "client_direct_rpc_fallback_removed": False,
        "repositories_call_supabase_rpc_directly": False,
        "repositories_call_single_transport": True,
    }.items():
        if inventory.get(key) != expected:
            fail(f"current client inventory drift for {key}")
    if inventory.get("direct_routes") != ROUTES:
        fail(f"{FAILURE_CLASSES[1]} route inventory drifted")

    repository_source = workout + "\n" + feedback
    if ".rpc(" in repository_source or ".functions.invoke(" in repository_source:
        fail(f"{FAILURE_CLASSES[1]} repository bypassed the single transport")
    for action in ROUTES:
        if repository_source.count(f"action: '{action}'") != 1:
            fail(f"{FAILURE_CLASSES[1]} action must enter the single transport exactly once: {action}")
    if repository_source.count("StudentAccessTransport.instance.invoke(") != 5:
        fail(f"{FAILURE_CLASSES[1]} expected exactly five repository transport call sites")

    contract = authority.get("transport_contract", {})
    for key, expected in {
        "active_mode": "directRpc",
        "resolved_mode": "directRpc",
        "edge_function_name": "student-access-gateway",
        "edge_gateway_selected": False,
        "automatic_edge_to_direct_fallback": False,
        "explicit_rollback_requested": False,
        "explicit_rollback_authorized": False,
        "direct_rpc_execute_revoked": False,
        "rollback_verified": False,
        "client_cutover_verified": False,
        "exact_route_count": 5,
        "edge_candidate_path_compiled_behind_inactive_mode": True,
        "behavioral_transport_change": False,
    }.items():
        if contract.get(key) != expected:
            fail(f"transport contract authority drift for {key}")

    for fragment in (
        "StudentAccessTransportMode.directRpc",
        "static const String edgeFunctionName = 'student-access-gateway';",
        "static const bool edgeGatewaySelected = false;",
        "static const bool automaticEdgeToDirectFallback = false;",
        "static const bool explicitRollbackRequested = false;",
        "static const bool explicitRollbackAuthorized = false;",
        "static const bool directRpcExecuteRevoked = false;",
        "static const bool rollbackVerified = false;",
        "static const bool clientCutoverVerified = false;",
        "if (!explicitRollbackRequested) return configuredMode;",
        "if (!explicitRollbackAuthorized)",
        "configuredMode != StudentAccessTransportMode.edgeGateway",
        "return StudentAccessTransportMode.directRpc;",
    ):
        if fragment not in contract_source:
            fail(f"transport/rollback contract source drifted: {fragment}")
    for action, rpc in ROUTES.items():
        if contract_source.count(f"'{action}': '{rpc}'") != 1:
            fail(f"{FAILURE_CLASSES[1]} transport route map drift: {action}")

    for fragment in (
        "return _client.rpc(directRpc, params: directParams);",
        "return _invokeEdge(action: action, payload: edgePayload);",
        "_client.functions.invoke(",
        "StudentAccessTransportContract.edgeFunctionName",
        "StudentAccessTransportContract.resolvedMode",
        "on FunctionException catch (error)",
        "normalizeStudentEdgeFunctionException(",
        "studentAccessStateError(code, context: context)",
    ):
        if fragment not in transport_code:
            fail(f"single transport runtime incomplete: {fragment}")

    catch_match = re.search(
        r"on\s+FunctionException\s+catch\s*\(error\)\s*\{(?P<body>.*?)\n\s*\}",
        transport_code,
        flags=re.DOTALL,
    )
    if catch_match is None:
        fail("Edge FunctionException handler disappeared")
    catch_body = catch_match.group("body")
    if "_client.rpc" in catch_body or "directRpc" in catch_body:
        fail(f"{FAILURE_CLASSES[2]} Edge exception handler can fall back to direct RPC")
    if "error.details" not in catch_body or "normalizeStudentEdgeFunctionException" not in catch_body:
        fail("Edge exception is not normalized through the bounded contract")

    for fragment in (
        "_trustedStudentEdgeErrorCodes",
        "STUDENT_NETWORK_RATE_LIMITED",
        "STUDENT_GATEWAY_UNAVAILABLE",
        "STUDENT_GATEWAY_REQUEST_FAILED",
        "parsed < 1 || parsed > 60",
    ):
        if fragment not in edge_errors:
            fail(f"{EDGE_DETAIL_FAILURE_CLASS} Edge error normalizer drift: {fragment}")
    for forbidden in ("...detailMap", "return detailMap", "'details':", '"details":'):
        if forbidden in edge_errors:
            fail(f"{EDGE_DETAIL_FAILURE_CLASS} arbitrary exception details can escape: {forbidden}")
    for fragment in (
        "case 'STUDENT_NETWORK_RATE_LIMITED':",
        "case 'STUDENT_GATEWAY_UNAVAILABLE':",
        "case 'STUDENT_GATEWAY_REQUEST_FAILED':",
        "Muitas ações em pouco tempo",
        "Não foi possível confirmar o acesso agora",
    ):
        if fragment not in error_messages:
            fail(f"student-facing Edge error mapping drift: {fragment}")

    error_authority = authority.get("edge_error_contract", {})
    for key, expected in {
        "function_exception_caught": True,
        "trusted_gateway_error_allowlist": True,
        "arbitrary_exception_details_returned": False,
        "raw_token_details_returned": False,
        "raw_network_origin_details_returned": False,
        "retry_after_min_seconds": 1,
        "retry_after_max_seconds": 60,
        "unknown_non_2xx_collapses_to_generic_code": True,
        "network_rate_limit_maps_to_existing_user_semantics": True,
        "automatic_direct_rpc_fallback_on_exception": False,
    }.items():
        if error_authority.get(key) != expected:
            fail(f"Edge error authority drift for {key}")

    rollback = authority.get("rollback_harness", {})
    for key, expected in {
        "resolver": "resolveStudentAccessTransportMode",
        "production_active_mode": "directRpc",
        "explicit_rollback_requested": False,
        "explicit_rollback_authorized": False,
        "unauthorized_rollback_fails_closed": True,
        "rollback_from_non_edge_mode_rejected": True,
        "authorized_edge_to_direct_transition_unit_tested": True,
        "runtime_rollback_verified": False,
        "harness_ready": True,
    }.items():
        if rollback.get(key) != expected:
            fail(f"rollback harness authority drift for {key}")

    invariants = authority.get("cutover_invariants", {})
    for key in (
        "all_five_routes_move_as_one_security_boundary",
        "partial_cutover_forbidden",
        "automatic_edge_failure_fallback_to_direct_rpc_forbidden",
        "edge_failure_must_fail_closed_after_cutover",
        "rollback_is_explicit_controlled_transition_not_per_request_fallback",
        "direct_execute_must_remain_until_rollback_proof",
        "direct_execute_revocation_requires_post_cutover_runtime_proof",
        "raw_possession_token_logging_forbidden",
        "raw_network_origin_logging_forbidden",
        "arbitrary_edge_exception_detail_echo_forbidden",
        "launch_gate_promotion_forbidden",
    ):
        if invariants.get(key) is not True:
            fail(f"cutover invariant missing: {key}")

    before_edge = authority.get("required_before_edge_selection", {})
    for key in (
        "edge_transport_implementation_compiles",
        "all_five_repository_calls_routed_through_single_transport",
        "edge_error_contract_mapped_to_existing_student_errors",
        "rollback_harness_ready",
    ):
        if before_edge.get(key) is not True:
            fail(f"source/harness prerequisite missing: {key}")
    for key in (
        "read_only_edge_runtime_smoke_after_client_source_change",
        "command_edge_runtime_smoke_with_synthetic_fixture",
        "explicit_rollback_proof",
        "cutover_receipt_materialized",
    ):
        if before_edge.get(key) is not False:
            fail(f"{FAILURE_CLASSES[4]} runtime/cutover proof self-attested: {key}")

    before_revoke = authority.get("required_before_direct_rpc_revocation", {})
    if before_revoke.get("automatic_direct_fallback_absent") is not True:
        fail(f"{FAILURE_CLASSES[2]} fail-open fallback invariant lost")
    for key in (
        "flutter_edge_gateway_active",
        "five_routes_verified_via_edge",
        "rollback_path_verified",
        "post_cutover_observation_window_passed",
        "security_advisor_rechecked",
    ):
        if before_revoke.get(key) is not False:
            fail(f"{FAILURE_CLASSES[3]} direct-RPC revocation prerequisite self-attested: {key}")

    next_stage = authority.get("next_stage", {})
    if next_stage.get("name") != "STAGE30_CONTROLLED_EDGE_RUNTIME_SMOKE_FIXTURE":
        fail("Stage 30 next-stage authority drifted")
    if next_stage.get("allowed_now") is not True:
        fail("controlled Edge runtime smoke work unexpectedly blocked")
    if next_stage.get("requires_synthetic_customer_fixture") is not True:
        fail("runtime smoke lost synthetic-fixture requirement")
    if next_stage.get("requires_migration_ledger_protocol") is not True:
        fail("runtime smoke lost migration-ledger interlock")
    if next_stage.get("may_select_edge_gateway_now") is not False:
        fail(f"{FAILURE_CLASSES[0]} Edge selection prematurely authorized")
    if next_stage.get("may_revoke_direct_rpc_execute_now") is not False:
        fail(f"{FAILURE_CLASSES[3]} direct RPC revocation prematurely authorized")

    if any(value is not False for value in authority.get("launch_authority", {}).values()):
        fail("Stage 30 source/harness work gained launch authority")

    print("STUDENT_ACCESS_CLIENT_CUTOVER_PREPARATION_GUARD=PASS")
    print("CURRENT_STATE=CLIENT_EDGE_ERROR_CONTRACT_ROLLBACK_HARNESS_READY_DIRECT_MODE")
    print("STAGE29_VALID_ROUTE_AND_CLEANUP=VERIFIED")
    print("EDGE_RUNTIME_VERSION=3")
    print("SINGLE_TRANSPORT_CALL_SITES=5")
    print("ACTIVE_TRANSPORT=directRpc")
    print("EDGE_ERROR_CONTRACT=BOUNDED_AND_USER_SAFE")
    print("EDGE_EXCEPTION_DIRECT_FALLBACK=DENIED")
    print("ROLLBACK_HARNESS=READY_NOT_RUNTIME_VERIFIED")
    print("ROLLBACK_VERIFIED=false")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")
    print("NEXT=STAGE30_CONTROLLED_EDGE_RUNTIME_SMOKE_FIXTURE")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
