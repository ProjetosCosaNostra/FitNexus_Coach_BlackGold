from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
APP = ROOT / "03_app_flutter" / "fitnexus_app"

RUNTIME_AUTHORITY = BACKEND / "student_access_stage32_post_cutover_runtime_proof_authority.json"
RECOVERY_AUTHORITY = BACKEND / "stage32_post_cutover_live_proof_failure_r0_authority.json"
CONTRACT = APP / "lib" / "features" / "student" / "student_access_transport_contract.dart"
TEST = APP / "test" / "student_access_stage32_post_cutover_live_edge_proof_test.dart"

RUNTIME_STATE = "POST_CUTOVER_EDGE_RUNTIME_PROOF_FIXTURE_REMOTE_LIVE_PROOF_PENDING_EDGE_MODE"
RECOVERY_STATE = "PRE_NETWORK_FAILURE_RECORDED_FIXTURE_REARMED_R1_LIVE_PROOF_R1_PENDING"
REARM_VERSION = "20260821214005"
OLD_RUN = 32508349425
OLD_JOB = 96853509377
OLD_PROOF_HEAD = "370cfe65d3df5188c3f840d84b5a8748f1357cf2"
OLD_TRIGGER_HEAD = "84a51d97f3b7a7c53965567e21760d5d59c85f5a"
REEXECUTION_CLASS = "BGF-STAGE32-POST-CUTOVER-PROOF-REEXECUTION-233"
SINGLETON_CLASS = "BGF-STAGE32-PRODUCTION-SINGLETON-BYPASS-234"
PLUGIN_CLASS = "BGF-STAGE32-FLUTTER-TEST-SHARED-PREFERENCES-PLUGIN-235"
TTL_CLASS = "BGF-STAGE32-SYNTHETIC-FIXTURE-TTL-EXPIRED-BEFORE-RETRY-236"
READONLY_CLASS = "BGF-SUPABASE-EXECUTE-SQL-READONLY-DML-237"


def fail(message: str, failure_class: str = REEXECUTION_CLASS) -> None:
    raise SystemExit(
        "STUDENT_ACCESS_STAGE32_LIVE_PROOF_R1_CANDIDATE_GUARD=FAIL\n"
        f"FAILURE_CLASS={failure_class}\n"
        f"DETAIL={message}"
    )


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


def main() -> None:
    runtime = load(RUNTIME_AUTHORITY)
    recovery = load(RECOVERY_AUTHORITY)
    contract = text(CONTRACT)
    test = text(TEST)

    if runtime.get("current_state") != RUNTIME_STATE:
        fail("runtime authority is not at the post-cutover live-proof-pending frontier")
    if recovery.get("status") != RECOVERY_STATE:
        fail("R0 recovery authority is not at the rearmed R1 proof frontier")

    failure_ids = {
        item.get("id")
        for item in recovery.get("failure_classes", [])
        if isinstance(item, dict)
    }
    for failure_class in (PLUGIN_CLASS, TTL_CLASS, READONLY_CLASS):
        if failure_class not in failure_ids:
            fail(f"recovery prevention class disappeared: {failure_class}")

    consumed = recovery.get("consumed_attempt", {})
    require(
        consumed,
        {
            "workflow_run_id": OLD_RUN,
            "workflow_job_id": OLD_JOB,
            "run_attempt": 1,
            "proof_head_sha": OLD_PROOF_HEAD,
            "trigger_head_sha": OLD_TRIGGER_HEAD,
            "result": "FAIL_PRE_NETWORK_BOOTSTRAP",
            "network_transport_reached": False,
            "production_singleton_invoke_reached": False,
            "routes_attempted": 0,
            "routes_verified": 0,
            "proof_credit": False,
            "same_workflow_rerun_allowed": False,
            "same_proof_head_reuse_allowed": False,
        },
        "consumed R0 proof",
    )

    rearm = recovery.get("rearm_remote_receipt", {})
    require(
        rearm,
        {
            "source": "Supabase.apply_migration",
            "migration_name": "stage32_rearm_expired_fixture_r1",
            "remote_version": REARM_VERSION,
            "apply_result": "SUCCESS",
            "rearm_horizon_ok": True,
            "expected_live_link": 1,
            "workout_sessions": 0,
            "workout_logs": 0,
            "workout_feedback": 0,
            "fixture_command_receipts": 0,
            "fixture_rate_buckets": 0,
            "fixture_security_events": 0,
            "fixture_security_signals": 0,
            "rpc_count": 5,
            "all_five_anon_execute_intact": True,
            "all_five_authenticated_execute_intact": True,
            "remote_mutation_was_only_exact_link_expiry_rearm": True,
            "live_proof_executed_during_rearm": False,
            "direct_rpc_grants_changed": False,
        },
        "rearm remote receipt",
    )

    production = runtime.get("production_boundary", {})
    require(
        production,
        {
            "active_transport": "edgeGateway",
            "resolved_transport": "edgeGateway",
            "edge_gateway_selected": True,
            "flutter_uses_edge_gateway_in_production": True,
            "production_singleton": "StudentAccessTransport.instance",
            "direct_v2_rpc_path_active_for_controlled_rollback": True,
            "direct_anon_v2_rpc_execute_revoked": False,
            "explicit_rollback_requested": False,
            "explicit_rollback_authorized": False,
            "automatic_edge_to_direct_fallback": False,
            "client_cutover_verified": False,
            "post_cutover_rollback_verified": False,
        },
        "production boundary",
    )

    proof = runtime.get("runtime_proof", {})
    if proof.get("workflow_run_id") is not None or proof.get("workflow_job_id") is not None:
        fail("runtime proof receipt exists before the new R1 sealed execution")
    if proof.get("result") is not None:
        fail("runtime proof result self-attested before the new R1 sealed execution")
    if proof.get("proof_reexecution_allowed") is not False:
        fail("runtime authority allows proof replay")
    for key in (
        "production_singleton_verified",
        "production_edge_mode_verified",
        "get_workout_verified",
        "start_workout_verified",
        "set_completion_verified",
        "get_feedback_context_verified",
        "submit_feedback_verified",
        "all_five_routes_verified",
        "synthetic_fixture_mutated_as_expected",
        "real_customer_data_used",
        "real_customer_data_mutated",
        "direct_rpc_grants_changed",
        "cleanup_completed",
    ):
        if proof.get(key) is not False:
            fail(f"runtime proof self-attested before R1 execution: {key}")

    next_stage = recovery.get("next_stage", {})
    require(
        next_stage,
        {
            "name": "PREPARE_STAGE32_POST_CUTOVER_LIVE_PROOF_R1",
            "allowed_now": True,
            "requires_rearm_remote_reconciled": True,
            "requires_shared_preferences_mock": True,
            "requires_new_exact_proof_head": True,
            "requires_new_one_shot_workflow_seal": True,
            "requires_new_trigger_head": True,
            "requires_fresh_fixture_expiry_check_immediately_before_event_delivery": True,
            "requires_fresh_direct_rpc_grant_check_immediately_before_event_delivery": True,
            "requires_zero_runtime_mutation_residue_before_event_delivery": True,
            "may_execute_before_new_workflow_seal": False,
            "may_rerun_consumed_workflow": False,
            "may_reuse_consumed_proof_head": False,
            "may_revoke_direct_rpc_execute_now": False,
            "may_promote_launch_gates": False,
        },
        "R1 next stage",
    )

    for fragment in (
        "StudentAccessTransportMode.edgeGateway;",
        "static const bool edgeGatewaySelected = true;",
        "static const bool automaticEdgeToDirectFallback = false;",
        "static const bool directRpcExecuteRevoked = false;",
        "static const bool rollbackVerified = false;",
        "static const bool clientCutoverVerified = false;",
    ):
        if fragment not in contract:
            fail(f"production transport contract drifted: {fragment}")

    mock_import = "import 'package:shared_preferences/shared_preferences.dart';"
    mock_call = "SharedPreferences.setMockInitialValues(<String, Object>{});"
    supabase_init = "await Supabase.initialize("
    if mock_import not in test or mock_call not in test:
        fail("SharedPreferences test backend is missing", PLUGIN_CLASS)
    if test.index(mock_call) > test.index(supabase_init):
        fail("SharedPreferences mock is initialized after Supabase.initialize", PLUGIN_CLASS)

    for fragment in (
        "STAGE32_POST_CUTOVER_LIVE_PROOF_ENABLED",
        "final transport = StudentAccessTransport.instance;",
        "StudentAccessTransportMode.edgeGateway",
        "StudentAccessTransportContract.edgeGatewaySelected, isTrue",
        "StudentAccessTransportContract.directRpcExecuteRevoked, isFalse",
        "32000000000000000000000000000001",
        "32000000000000000000000000000002",
        "32000000000000000000000000000003",
    ):
        if fragment not in test:
            fail(f"focused R1 live proof source drifted: {fragment}")

    if "StudentAccessTransport.forVerification" in test or ".forVerification(" in test:
        fail("R1 proof uses verification-only transport", SINGLETON_CLASS)
    if ".rpc(" in test or ".functions.invoke(" in test:
        fail("R1 proof bypasses StudentAccessTransport.instance", SINGLETON_CLASS)

    if any(value is not False for value in runtime.get("launch_authority", {}).values()):
        fail("runtime proof authority gained launch authority")
    boundary = recovery.get("production_boundary", {})
    if boundary.get("launch_gate_promotion") is not False:
        fail("recovery authority gained launch promotion")

    print("STUDENT_ACCESS_STAGE32_LIVE_PROOF_R1_CANDIDATE_GUARD=PASS")
    print(f"RUNTIME_STATE={RUNTIME_STATE}")
    print(f"RECOVERY_STATE={RECOVERY_STATE}")
    print(f"REARM_REMOTE_VERSION={REARM_VERSION}")
    print(f"CONSUMED_R0_RUN={OLD_RUN}")
    print("CONSUMED_R0_ROUTES_ATTEMPTED=0")
    print("R0_REEXECUTION_ALLOWED=false")
    print("R1_REQUIRES_NEW_EXACT_HEAD=true")
    print("R1_REQUIRES_NEW_ONE_SHOT_SEAL=true")
    print("R1_LIVE_PROOF_EXECUTED=false")
    print("SHARED_PREFERENCES_MOCK_INSTALLED=true")
    print("PRODUCTION_ACTIVE_TRANSPORT=edgeGateway")
    print("PRODUCTION_SINGLETON=StudentAccessTransport.instance")
    print("ROUTES_EXPECTED=5")
    print("AUTOMATIC_EDGE_TO_DIRECT_FALLBACK=false")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
