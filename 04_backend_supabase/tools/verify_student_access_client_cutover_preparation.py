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
WORKOUT = APP / "features" / "student" / "student_workout_repository.dart"
FEEDBACK = APP / "features" / "student" / "student_feedback_repository.dart"

FAILURE_CLASSES = [
    "BGF-CLIENT-EDGE-CUTOVER-PREMATURE-195",
    "BGF-CLIENT-TRANSPORT-PARTIAL-CUTOVER-196",
    "BGF-EDGE-FAILOPEN-DIRECT-FALLBACK-197",
    "BGF-DIRECT-RPC-REVOCATION-BEFORE-ROLLBACK-198",
    "BGF-CLIENT-CUTOVER-SELF-ATTESTATION-199",
]
COMMENT_FALSE_POSITIVE_FAILURE_CLASS = "BGF-GUARD-COMMENT-SEMANTIC-FALSE-POSITIVE-201"
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
    """Remove Dart comments before semantic-token checks.

    BGF-GUARD-COMMENT-SEMANTIC-FALSE-POSITIVE-201 was created after a guard
    interpreted the documentation phrase `no try/catch` as executable catch
    syntax. Security decisions must be based on code tokens, not comments.
    """
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
    workout = text(WORKOUT)
    feedback = text(FEEDBACK)

    if authority.get("schema_version") != 1 or authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("Stage 30 authority identity drifted")
    if authority.get("failure_classes") != FAILURE_CLASSES:
        fail("Stage 30 failure-class authority drifted")
    if authority.get("current_state") != "CLIENT_SINGLE_TRANSPORT_SOURCE_INTEGRATED_DIRECT_MODE":
        fail(f"{FAILURE_CLASSES[4]} Stage 30 source-integration state drifted")
    if authority.get("baseline_main_sha") != "a484b759e9aca0bb3761d6e58919e682b4795e5b":
        fail("Stage 30 source-integration baseline SHA drifted")

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
        count = repository_source.count(f"action: '{action}'")
        if count != 1:
            fail(f"{FAILURE_CLASSES[1]} action must enter the single transport exactly once: {action}={count}")
    if repository_source.count("StudentAccessTransport.instance.invoke(") != 5:
        fail(f"{FAILURE_CLASSES[1]} expected exactly five repository transport call sites")

    contract = authority.get("transport_contract", {})
    for key, expected in {
        "active_mode": "directRpc",
        "edge_function_name": "student-access-gateway",
        "edge_gateway_selected": False,
        "automatic_edge_to_direct_fallback": False,
        "direct_rpc_execute_revoked": False,
        "rollback_verified": False,
        "client_cutover_verified": False,
        "exact_route_count": 5,
        "edge_candidate_path_compiled_behind_inactive_mode": True,
        "behavioral_transport_change": False,
    }.items():
        if contract.get(key) != expected:
            fail(f"transport contract authority drift for {key}")

    required_contract = (
        "StudentAccessTransportMode.directRpc",
        "static const String edgeFunctionName = 'student-access-gateway';",
        "static const bool edgeGatewaySelected = false;",
        "static const bool automaticEdgeToDirectFallback = false;",
        "static const bool directRpcExecuteRevoked = false;",
        "static const bool rollbackVerified = false;",
        "static const bool clientCutoverVerified = false;",
    )
    missing_contract = [fragment for fragment in required_contract if fragment not in contract_source]
    if missing_contract:
        fail(f"transport contract source drifted: {missing_contract}")
    for action, rpc in ROUTES.items():
        if contract_source.count(f"'{action}': '{rpc}'") != 1:
            fail(f"{FAILURE_CLASSES[1]} transport route map drift: {action}")

    for fragment in (
        "return _client.rpc(directRpc, params: directParams);",
        "return _invokeEdge(action: action, payload: edgePayload);",
        "_client.functions.invoke(",
        "StudentAccessTransportContract.edgeFunctionName",
    ):
        if fragment not in transport_code:
            fail(f"single transport runtime incomplete: {fragment}")
    if re.search(r"\bcatch\s*\(", transport_code) and "_client.rpc" in transport_code:
        fail(f"{FAILURE_CLASSES[2]} transport contains potential Edge -> direct exception fallback")
    if "automaticEdgeToDirectFallback = true" in contract_source:
        fail(f"{FAILURE_CLASSES[2]} automatic Edge -> direct fail-open fallback enabled")

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
        "launch_gate_promotion_forbidden",
    ):
        if invariants.get(key) is not True:
            fail(f"cutover invariant missing: {key}")

    before_edge = authority.get("required_before_edge_selection", {})
    for key in (
        "edge_transport_implementation_compiles",
        "all_five_repository_calls_routed_through_single_transport",
    ):
        if before_edge.get(key) is not True:
            fail(f"source integration prerequisite missing: {key}")
    for key in (
        "edge_error_contract_mapped_to_existing_student_errors",
        "read_only_edge_runtime_smoke_after_client_source_change",
        "command_edge_runtime_smoke_with_synthetic_fixture",
        "explicit_rollback_proof",
        "cutover_receipt_materialized",
    ):
        if before_edge.get(key) is not False:
            fail(f"{FAILURE_CLASSES[4]} future Edge-selection proof self-attested: {key}")

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
    if next_stage.get("name") != "STAGE30_EDGE_ERROR_CONTRACT_AND_ROLLBACK_HARNESS":
        fail("Stage 30 next-stage authority drifted")
    if next_stage.get("allowed_now") is not True:
        fail("error-contract/rollback harness work unexpectedly blocked")
    if next_stage.get("may_select_edge_gateway_now") is not False:
        fail(f"{FAILURE_CLASSES[0]} Edge selection prematurely authorized")
    if next_stage.get("may_revoke_direct_rpc_execute_now") is not False:
        fail(f"{FAILURE_CLASSES[3]} direct RPC revocation prematurely authorized")

    if any(value is not False for value in authority.get("launch_authority", {}).values()):
        fail("Stage 30 source integration gained launch authority")

    print("STUDENT_ACCESS_CLIENT_CUTOVER_PREPARATION_GUARD=PASS")
    print("CURRENT_STATE=CLIENT_SINGLE_TRANSPORT_SOURCE_INTEGRATED_DIRECT_MODE")
    print("STAGE29_VALID_ROUTE_AND_CLEANUP=VERIFIED")
    print("EDGE_RUNTIME_VERSION=3")
    print("SINGLE_TRANSPORT_CALL_SITES=5")
    print("ACTIVE_TRANSPORT=directRpc")
    print("EDGE_CANDIDATE_COMPILED_BEHIND_INACTIVE_MODE=true")
    print("AUTOMATIC_EDGE_TO_DIRECT_FALLBACK=false")
    print(f"COMMENT_FALSE_POSITIVE_PREVENTION={COMMENT_FALSE_POSITIVE_FAILURE_CLASS}")
    print("ROLLBACK_VERIFIED=false")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")
    print("NEXT=STAGE30_EDGE_ERROR_CONTRACT_AND_ROLLBACK_HARNESS")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
