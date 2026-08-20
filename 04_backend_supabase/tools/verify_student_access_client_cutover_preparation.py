from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
APP = ROOT / "03_app_flutter" / "fitnexus_app" / "lib"

AUTHORITY = BACKEND / "student_access_client_cutover_authority.json"
VALID_ROUTE = BACKEND / "student_access_valid_route_authority.json"
EDGE_AUTHORITY = BACKEND / "student_access_edge_gateway_authority.json"
RATE_AUTHORITY = BACKEND / "student_access_network_rate_limit_authority.json"
NETWORK_AUTHORITY = BACKEND / "student_access_network_origin_boundary.json"
TRANSPORT = APP / "features" / "student" / "student_access_transport_contract.dart"
WORKOUT = APP / "features" / "student" / "student_workout_repository.dart"
FEEDBACK = APP / "features" / "student" / "student_feedback_repository.dart"

FAILURE_CLASSES = [
    "BGF-CLIENT-EDGE-CUTOVER-PREMATURE-195",
    "BGF-CLIENT-TRANSPORT-PARTIAL-CUTOVER-196",
    "BGF-EDGE-FAILOPEN-DIRECT-FALLBACK-197",
    "BGF-DIRECT-RPC-REVOCATION-BEFORE-ROLLBACK-198",
    "BGF-CLIENT-CUTOVER-SELF-ATTESTATION-199",
]
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


def main() -> None:
    authority = data(AUTHORITY)
    valid_route = data(VALID_ROUTE)
    edge = data(EDGE_AUTHORITY)
    rate = data(RATE_AUTHORITY)
    network = data(NETWORK_AUTHORITY)
    transport = text(TRANSPORT)
    workout = text(WORKOUT)
    feedback = text(FEEDBACK)

    if authority.get("schema_version") != 1 or authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("Stage 30 authority identity drifted")
    if authority.get("failure_classes") != FAILURE_CLASSES:
        fail("Stage 30 failure-class authority drifted")
    if authority.get("current_state") != "CLIENT_EDGE_CUTOVER_PREPARATION_DIRECT_PATH_ACTIVE":
        fail(f"{FAILURE_CLASSES[4]} Stage 30 preparation self-promoted")
    if authority.get("baseline_main_sha") != "983d28ad64b7d1d931a3cb7266e92167e7d8d026":
        fail("Stage 30 baseline main SHA drifted")

    prerequisites = authority.get("prerequisites", {})
    if valid_route.get("current_state") != "VALID_ROUTE_LIVE_VERIFIED_CLEANUP_COMPLETE":
        fail("Stage 29 valid-route proof/cleanup prerequisite missing")
    vr_runtime = valid_route.get("runtime_verification", {})
    if vr_runtime.get("valid_token_edge_route_verified_live") is not True:
        fail("valid-token Edge route was not verified")
    if vr_runtime.get("student_rpc_forwarding_with_valid_token_verified_live") is not True:
        fail("valid-token student RPC forwarding proof missing")
    if vr_runtime.get("cleanup_completed") is not True or vr_runtime.get("synthetic_business_rows_remaining") != 0:
        fail("Stage 29 synthetic cleanup is incomplete")
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
    spoof = network.get("observed_runtime", {}).get("spoof_resistance_receipt", {})
    if spoof.get("client_can_force_cf_connecting_ip") is not False:
        fail("trusted origin spoof resistance disappeared")

    inventory = authority.get("current_client_inventory", {})
    for key, expected in {
        "transport_mode": "direct_rpc",
        "flutter_uses_edge_gateway": False,
        "direct_v2_rpc_path_active": True,
        "direct_anon_v2_rpc_execute_revoked": False,
        "client_direct_rpc_fallback_removed": False,
    }.items():
        if inventory.get(key) != expected:
            fail(f"current client inventory drift for {key}")
    if inventory.get("direct_routes") != ROUTES:
        fail(f"{FAILURE_CLASSES[1]} route inventory drifted")

    direct_sources = workout + "\n" + feedback
    direct_counts = {rpc: direct_sources.count(f"'{rpc}'") for rpc in ROUTES.values()}
    missing = [rpc for rpc, count in direct_counts.items() if count != 1]
    if missing:
        fail(f"{FAILURE_CLASSES[1]} direct call-site inventory must contain each route exactly once: {missing}")
    if ".functions.invoke(" in direct_sources or "student-access-gateway" in direct_sources:
        fail(f"{FAILURE_CLASSES[0]} repositories started Edge cutover during preparation")

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
    }.items():
        if contract.get(key) != expected:
            fail(f"transport contract authority drift for {key}")

    required_transport = (
        "StudentAccessTransportMode.directRpc",
        "static const String edgeFunctionName = 'student-access-gateway';",
        "static const bool edgeGatewaySelected = false;",
        "static const bool automaticEdgeToDirectFallback = false;",
        "static const bool directRpcExecuteRevoked = false;",
        "static const bool rollbackVerified = false;",
        "static const bool clientCutoverVerified = false;",
    )
    missing_transport = [fragment for fragment in required_transport if fragment not in transport]
    if missing_transport:
        fail(f"transport source contract drifted: {missing_transport}")
    for action, rpc in ROUTES.items():
        if f"'{action}': '{rpc}'" not in transport:
            fail(f"{FAILURE_CLASSES[1]} transport route missing: {action}")
    if "automaticEdgeToDirectFallback = true" in transport:
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
    if any(value is not False for value in before_edge.values()):
        fail(f"{FAILURE_CLASSES[4]} Edge selection prerequisites were self-attested")
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
    if next_stage.get("name") != "STAGE30_SINGLE_TRANSPORT_SOURCE_INTEGRATION":
        fail("Stage 30 next-stage authority drifted")
    if next_stage.get("allowed_now") is not True:
        fail("single-transport source integration unexpectedly blocked")
    if next_stage.get("may_select_edge_gateway_now") is not False:
        fail(f"{FAILURE_CLASSES[0]} Edge selection prematurely authorized")
    if next_stage.get("may_revoke_direct_rpc_execute_now") is not False:
        fail(f"{FAILURE_CLASSES[3]} direct RPC revocation prematurely authorized")

    if any(value is not False for value in authority.get("launch_authority", {}).values()):
        fail("Stage 30 preparation gained launch authority")

    print("STUDENT_ACCESS_CLIENT_CUTOVER_PREPARATION_GUARD=PASS")
    print("CURRENT_STATE=CLIENT_EDGE_CUTOVER_PREPARATION_DIRECT_PATH_ACTIVE")
    print("STAGE29_VALID_ROUTE_AND_CLEANUP=VERIFIED")
    print("EDGE_RUNTIME_VERSION=3")
    print("DIRECT_CLIENT_ROUTES=5")
    print("EDGE_GATEWAY_SELECTED=false")
    print("AUTOMATIC_EDGE_TO_DIRECT_FALLBACK=false")
    print("ROLLBACK_VERIFIED=false")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")
    print("NEXT=STAGE30_SINGLE_TRANSPORT_SOURCE_INTEGRATION")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
