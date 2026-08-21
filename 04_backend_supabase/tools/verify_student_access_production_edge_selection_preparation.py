from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
APP = ROOT / "03_app_flutter" / "fitnexus_app" / "lib" / "features" / "student"

AUTHORITY = BACKEND / "student_access_production_edge_selection_authority.json"
STAGE31 = BACKEND / "student_access_client_edge_runtime_proof_authority.json"
CUTOVER = BACKEND / "student_access_client_cutover_authority.json"
CONTRACT = APP / "student_access_transport_contract.dart"
TRANSPORT = APP / "student_access_transport.dart"
WORKOUT = APP / "student_workout_repository.dart"
FEEDBACK = APP / "student_feedback_repository.dart"

STATE = "PRODUCTION_EDGE_SELECTION_PREPARED_DIRECT_MODE"
BASELINE = "f205977e1721265a11071b30c89dbb04409979e7"
STAGE31_STATE = "CLIENT_EDGE_RUNTIME_PROOF_LIVE_VERIFIED_CLEANUP_COMPLETE_DIRECT_MODE"
CUTOVER_STATE = "CLIENT_RUNTIME_ROLLBACK_VERIFIED_DIRECT_MODE"
FAILURE_CLASSES = [
    "BGF-STAGE32-PRODUCTION-EDGE-SELECTION-PREMATURE-227",
    "BGF-STAGE32-PRODUCTION-EDGE-SELECTION-PARTIAL-228",
    "BGF-STAGE32-DIRECT-RPC-REVOCATION-PREMATURE-229",
    "BGF-STAGE32-POST-CUTOVER-ROLLBACK-GAP-230",
]
ROUTES = {
    "get_workout": "get_student_workout_v2",
    "start_workout": "start_student_workout_v2",
    "set_completion": "set_student_exercise_completion_v2",
    "get_feedback_context": "get_student_feedback_context_v2",
    "submit_feedback": "submit_student_workout_feedback_v2",
}


def fail(message: str) -> None:
    raise SystemExit("STUDENT_ACCESS_PRODUCTION_EDGE_SELECTION_PREPARATION_GUARD=FAIL\n" + message)


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to read {path.relative_to(ROOT)}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"expected JSON object: {path.relative_to(ROOT)}")
    return value


def text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"unable to read {path.relative_to(ROOT)}: {type(exc).__name__}")
    raise AssertionError("unreachable")


def require(mapping: dict, expected: dict, label: str) -> None:
    for key, value in expected.items():
        if mapping.get(key) != value:
            fail(f"{label} drift: {key}")


def without_comments(source: str) -> str:
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"//[^\n]*", "", source)


def main() -> None:
    authority = load(AUTHORITY)
    stage31 = load(STAGE31)
    cutover = load(CUTOVER)
    contract_source = text(CONTRACT)
    transport_source = without_comments(text(TRANSPORT))
    repository_source = text(WORKOUT) + "\n" + text(FEEDBACK)

    require(
        authority,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "stage": "STAGE32_PRODUCTION_EDGE_SELECTION",
            "failure_classes": FAILURE_CLASSES,
            "current_state": STATE,
            "baseline_main_sha": BASELINE,
        },
        "Stage 32 authority",
    )

    prerequisites = authority.get("prerequisites", {})
    require(
        prerequisites,
        {
            "stage31_authority_file": "04_backend_supabase/student_access_client_edge_runtime_proof_authority.json",
            "stage31_required_state": STAGE31_STATE,
            "stage31_cleanup_complete": True,
            "stage31_flutter_edge_routes_verified": 5,
            "stage31_proof_reexecution_allowed": False,
            "cutover_authority_file": "04_backend_supabase/student_access_client_cutover_authority.json",
            "cutover_required_state": CUTOVER_STATE,
            "stage30_runtime_rollback_verified": True,
            "edge_runtime_version": 3,
            "direct_rpc_grants_required_intact": True,
        },
        "Stage 32 prerequisites",
    )

    if stage31.get("current_state") != STAGE31_STATE:
        fail("Stage 31 cleanup-complete authority disappeared")
    runtime = stage31.get("runtime_proof", {})
    require(
        runtime,
        {
            "result": "PASS",
            "flutter_transport_edge_path_verified": True,
            "get_workout_verified": True,
            "start_workout_verified": True,
            "set_completion_verified": True,
            "get_feedback_context_verified": True,
            "submit_feedback_verified": True,
            "all_five_routes_verified": True,
            "proof_reexecution_allowed": False,
            "cleanup_completed": True,
            "synthetic_business_rows_remaining": 0,
            "synthetic_security_rows_remaining": 0,
            "synthetic_network_proof_rows_remaining": 0,
        },
        "Stage 31 proof/cleanup receipt",
    )
    require(
        stage31.get("production_boundary", {}),
        {
            "active_transport": "directRpc",
            "resolved_transport": "directRpc",
            "edge_gateway_selected": False,
            "flutter_uses_edge_gateway_in_production": False,
            "direct_v2_rpc_path_active": True,
            "direct_anon_v2_rpc_execute_revoked": False,
            "automatic_edge_to_direct_fallback": False,
            "client_cutover_verified": False,
            "behavioral_transport_change": False,
        },
        "Stage 31 production boundary",
    )

    require(
        cutover,
        {
            "schema_version": 2,
            "project_ref": "mceukeondizkwlpfxzgf",
            "current_state": CUTOVER_STATE,
        },
        "cutover authority",
    )
    require(
        cutover.get("transport_contract", {}),
        {
            "active_mode": "directRpc",
            "resolved_mode": "directRpc",
            "edge_gateway_selected": False,
            "automatic_edge_to_direct_fallback": False,
            "explicit_rollback_requested": False,
            "explicit_rollback_authorized": False,
            "direct_rpc_execute_revoked": False,
            "client_cutover_verified": False,
            "exact_route_count": 5,
        },
        "cutover transport boundary",
    )
    require(
        cutover.get("rollback_harness", {}),
        {
            "production_active_mode": "directRpc",
            "explicit_rollback_requested": False,
            "explicit_rollback_authorized": False,
            "unauthorized_rollback_fails_closed": True,
            "rollback_from_non_edge_mode_rejected": True,
            "authorized_edge_to_direct_transition_unit_tested": True,
            "runtime_rollback_verified": True,
            "runtime_rollback_proof_kind": "isolated_resolver_no_network",
            "harness_ready": True,
        },
        "pre-cutover rollback harness",
    )

    live = authority.get("live_preparation_receipt", {})
    require(
        live,
        {
            "source": "Supabase.execute_sql",
            "observed_at_utc": "2026-08-21T16:26:59.368889Z",
            "auth_users": 0,
            "organizations": 0,
            "students": 0,
            "training_plans": 0,
            "workout_sessions": 0,
            "workout_feedback": 0,
            "command_receipts": 0,
            "security_events": 0,
            "customer_domain_empty": True,
            "network_rate_bucket_global_rows": 13,
            "network_rate_bucket_rows_are_not_customer_domain_authority": True,
            "direct_rpc_grants_intact": True,
        },
        "live preparation receipt",
    )
    grants = live.get("direct_rpc_execute_grants", {})
    if set(grants) != set(ROUTES.values()) or any(grants.get(name) is not True for name in ROUTES.values()):
        fail(f"{FAILURE_CLASSES[2]} direct RPC execution grants are not sealed intact")

    require(
        authority.get("current_production_boundary", {}),
        {
            "active_transport": "directRpc",
            "resolved_transport": "directRpc",
            "flutter_uses_edge_gateway": False,
            "edge_gateway_selected": False,
            "automatic_edge_to_direct_fallback": False,
            "direct_v2_rpc_path_active": True,
            "direct_rpc_execute_revoked": False,
            "production_behavior_changed_in_this_stage": False,
        },
        "Stage 32 current production boundary",
    )

    prepared = authority.get("prepared_cutover_contract", {})
    require(
        prepared,
        {
            "target_transport": "edgeGateway",
            "edge_function_name": "student-access-gateway",
            "route_count": 5,
            "all_five_routes_move_atomically": True,
            "partial_cutover_forbidden": True,
            "automatic_edge_to_direct_fallback_forbidden": True,
            "explicit_controlled_rollback_only": True,
            "direct_rpc_grants_must_remain_after_initial_selection": True,
            "post_cutover_five_route_live_proof_required": True,
            "post_cutover_rollback_proof_required": True,
            "post_cutover_observation_required_before_direct_rpc_revocation": True,
            "security_advisor_recheck_required_before_direct_rpc_revocation": True,
            "source_change_in_this_preparation_stage": False,
            "cutover_receipt_materialized": False,
        },
        "prepared cutover contract",
    )

    source_receipt = authority.get("source_receipt", {})
    require(
        source_receipt,
        {
            "active_mode": "directRpc",
            "edge_gateway_selected": False,
            "direct_rpc_execute_revoked": False,
            "repositories_use_single_transport": True,
            "repository_transport_call_sites": 5,
            "edge_path_compiled": True,
            "edge_exception_direct_fallback_absent": True,
        },
        "source receipt",
    )

    for fragment in (
        "StudentAccessTransportMode.directRpc;",
        "static const bool edgeGatewaySelected = false;",
        "static const bool automaticEdgeToDirectFallback = false;",
        "static const bool explicitRollbackRequested = false;",
        "static const bool explicitRollbackAuthorized = false;",
        "static const bool directRpcExecuteRevoked = false;",
        "static const bool clientCutoverVerified = false;",
    ):
        if fragment not in contract_source:
            fail(f"{FAILURE_CLASSES[0]} preparation changed the production transport source: {fragment}")
    for action, rpc in ROUTES.items():
        if contract_source.count(f"'{action}': '{rpc}'") != 1:
            fail(f"{FAILURE_CLASSES[1]} route map drifted: {action}")

    if repository_source.count("StudentAccessTransport.instance.invoke(") != 5:
        fail(f"{FAILURE_CLASSES[1]} all five repository call sites must stay on the single transport")
    if ".rpc(" in repository_source or ".functions.invoke(" in repository_source:
        fail(f"{FAILURE_CLASSES[1]} repository bypassed the single transport")
    for action in ROUTES:
        if repository_source.count(f"action: '{action}'") != 1:
            fail(f"{FAILURE_CLASSES[1]} repository action drifted: {action}")

    for fragment in (
        "return _client.rpc(directRpc, params: directParams);",
        "return _invokeEdge(action: action, payload: edgePayload);",
        "_client.functions.invoke(",
        "StudentAccessTransportContract.edgeFunctionName",
        "normalizeStudentEdgeFunctionException(",
    ):
        if fragment not in transport_source:
            fail(f"single transport implementation drifted: {fragment}")
    catch_match = re.search(
        r"on\s+FunctionException\s+catch\s*\(error\)\s*\{(?P<body>.*?)\n\s*\}",
        transport_source,
        flags=re.DOTALL,
    )
    if catch_match is None:
        fail("Edge FunctionException handler disappeared")
    catch_body = catch_match.group("body")
    if "_client.rpc" in catch_body or "directRpc" in catch_body:
        fail("BGF-STAGE32-PRODUCTION-EDGE-SELECTION-PREMATURE-227 Edge error path gained direct fallback")

    rules = authority.get("promotion_rules", {})
    for key in (
        "may_select_edge_gateway_during_preparation",
        "may_change_production_behavior_during_preparation",
        "may_revoke_direct_rpc_execute_before_post_cutover_proofs",
        "may_enable_automatic_edge_to_direct_fallback",
        "may_use_real_customer_data_for_cutover_proof",
        "may_reexecute_stage31_live_proof",
        "may_promote_launch_gates",
    ):
        if rules.get(key) is not False:
            fail(f"premature Stage 32 promotion authority: {key}")
    if rules.get("all_five_routes_cutover_only") is not True:
        fail(f"{FAILURE_CLASSES[1]} atomic five-route cutover rule disappeared")

    require(
        authority.get("next_stage", {}),
        {
            "name": "SELECT_PRODUCTION_EDGE_TRANSPORT_ALL_FIVE_ROUTES_CANDIDATE",
            "allowed_now": True,
            "requires_preparation_ci_and_merge_first": True,
            "requires_all_five_routes_atomic": True,
            "requires_no_automatic_edge_to_direct_fallback": True,
            "requires_direct_rpc_grants_intact": True,
            "requires_post_cutover_live_proof_after_selection": True,
            "requires_post_cutover_rollback_proof_after_selection": True,
            "may_revoke_direct_rpc_execute_now": False,
        },
        "Stage 32 next stage",
    )
    if any(value is not False for value in authority.get("launch_authority", {}).values()):
        fail("Stage 32 preparation gained launch authority")

    print("STUDENT_ACCESS_PRODUCTION_EDGE_SELECTION_PREPARATION_GUARD=PASS")
    print(f"CURRENT_STATE={STATE}")
    print(f"BASELINE_MAIN_SHA={BASELINE}")
    print("STAGE31_EDGE_ROUTES_VERIFIED=5")
    print("STAGE31_CLEANUP=COMPLETE")
    print("CUSTOMER_DOMAIN=EMPTY")
    print("ACTIVE_TRANSPORT=directRpc")
    print("TARGET_TRANSPORT=edgeGateway")
    print("ATOMIC_ROUTE_COUNT=5")
    print("AUTOMATIC_EDGE_TO_DIRECT_FALLBACK=false")
    print("DIRECT_RPC_GRANTS=INTACT")
    print("PRODUCTION_BEHAVIOR_CHANGE=false")
    print("NEXT=SELECT_PRODUCTION_EDGE_TRANSPORT_ALL_FIVE_ROUTES_CANDIDATE_AFTER_CI_AND_MERGE")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
