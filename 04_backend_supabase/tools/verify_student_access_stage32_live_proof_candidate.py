from __future__ import annotations

import importlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
APP = ROOT / "03_app_flutter" / "fitnexus_app"
AUTHORITY = BACKEND / "student_access_stage32_post_cutover_runtime_proof_authority.json"
CONTRACT = APP / "lib" / "features" / "student" / "student_access_transport_contract.dart"
TEST = APP / "test" / "student_access_stage32_post_cutover_live_edge_proof_test.dart"

STATE = "POST_CUTOVER_EDGE_RUNTIME_PROOF_FIXTURE_REMOTE_LIVE_PROOF_PENDING_EDGE_MODE"
FIXTURE_VERSION = "20260821171334"
FAILURE_CLASS = "BGF-STAGE32-POST-CUTOVER-PROOF-PREMATURE-232"
REEXECUTION_CLASS = "BGF-STAGE32-POST-CUTOVER-PROOF-REEXECUTION-233"
SINGLETON_CLASS = "BGF-STAGE32-PRODUCTION-SINGLETON-BYPASS-234"


def fail(message: str) -> None:
    raise SystemExit(
        "STUDENT_ACCESS_STAGE32_LIVE_PROOF_CANDIDATE_GUARD=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\n"
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


def main() -> None:
    # Current lifecycle validation remains the authority; this candidate guard only
    # narrows the already-approved frontier to a single one-shot live execution.
    lifecycle = importlib.import_module(
        "verify_student_access_stage32_post_cutover_runtime_preparation"
    )
    lifecycle.main()

    authority = load(AUTHORITY)
    if authority.get("current_state") != STATE:
        fail("Stage 32 fixture is not at the remote live-proof-pending frontier")

    fixture = authority.get("fixture", {})
    if fixture.get("migration_ledger_state") != "remote_reconciled":
        fail("fixture migration is not remote-reconciled")
    if fixture.get("remote_applied") is not True:
        fail("fixture is not remotely applied")
    if fixture.get("remote_version") != FIXTURE_VERSION:
        fail("fixture remote version drifted")

    production = authority.get("production_boundary", {})
    expected_production = {
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
    }
    for key, expected in expected_production.items():
        if production.get(key) != expected:
            fail(f"production boundary drifted: {key}")

    grants = authority.get("direct_rpc_grant_receipt", {})
    if grants.get("all_five_anon_execute_intact") is not True:
        fail("anonymous direct RPC rollback grants are not sealed intact")
    if grants.get("all_five_authenticated_execute_intact") is not True:
        fail("authenticated direct RPC rollback grants are not sealed intact")
    if grants.get("grants_changed_during_fixture_apply") is not False:
        fail("fixture apply changed direct RPC grants")

    proof = authority.get("runtime_proof", {})
    if proof.get("workflow_run_id") is not None:
        fail(f"{REEXECUTION_CLASS} workflow receipt already exists")
    if proof.get("workflow_job_id") is not None or proof.get("result") is not None:
        fail(f"{REEXECUTION_CLASS} proof receipt already exists")
    if proof.get("proof_reexecution_allowed") is not False:
        fail(f"{REEXECUTION_CLASS} proof reexecution authority must remain false")
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
            fail(f"runtime proof self-attested before execution: {key}")

    next_stage = authority.get("next_stage", {})
    if next_stage.get("name") != "PREPARE_STAGE32_POST_CUTOVER_LIVE_PROOF":
        fail("authority next-stage frontier drifted")
    if next_stage.get("requires_exact_pr_and_head_seal_before_first_execution") is not True:
        fail("exact PR/head seal requirement disappeared")
    if next_stage.get("requires_one_shot_workflow") is not True:
        fail("one-shot workflow requirement disappeared")
    if next_stage.get("requires_production_singleton") is not True:
        fail("production singleton requirement disappeared")
    if next_stage.get("may_execute_live_proof_before_workflow_seal") is not False:
        fail("authority permits proof before workflow seal")
    if next_stage.get("may_revoke_direct_rpc_execute_now") is not False:
        fail("authority permits premature direct RPC revocation")

    contract = text(CONTRACT)
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

    test = text(TEST)
    required_test_fragments = (
        "STAGE32_POST_CUTOVER_LIVE_PROOF_ENABLED",
        "final transport = StudentAccessTransport.instance;",
        "StudentAccessTransportMode.edgeGateway",
        "StudentAccessTransportContract.edgeGatewaySelected, isTrue",
        "StudentAccessTransportContract.directRpcExecuteRevoked, isFalse",
        "32000000000000000000000000000001",
        "32000000000000000000000000000002",
        "32000000000000000000000000000003",
    )
    for fragment in required_test_fragments:
        if fragment not in test:
            fail(f"focused live proof source drifted: {fragment}")
    if "StudentAccessTransport.forVerification" in test or ".forVerification(" in test:
        raise SystemExit(
            "STUDENT_ACCESS_STAGE32_LIVE_PROOF_CANDIDATE_GUARD=FAIL\n"
            f"FAILURE_CLASS={SINGLETON_CLASS}\n"
            "DETAIL=post-cutover live proof uses verification-only transport"
        )
    if ".rpc(" in test or ".functions.invoke(" in test:
        raise SystemExit(
            "STUDENT_ACCESS_STAGE32_LIVE_PROOF_CANDIDATE_GUARD=FAIL\n"
            f"FAILURE_CLASS={SINGLETON_CLASS}\n"
            "DETAIL=post-cutover live proof bypasses StudentAccessTransport.instance"
        )

    if any(value is not False for value in authority.get("launch_authority", {}).values()):
        fail("Stage 32 live proof candidate gained launch authority")

    print("STUDENT_ACCESS_STAGE32_LIVE_PROOF_CANDIDATE_GUARD=PASS")
    print(f"CURRENT_STATE={STATE}")
    print(f"FIXTURE_REMOTE_VERSION={FIXTURE_VERSION}")
    print("PRODUCTION_ACTIVE_TRANSPORT=edgeGateway")
    print("PRODUCTION_SINGLETON=StudentAccessTransport.instance")
    print("ROUTES_EXPECTED=5")
    print("DIRECT_RPC_GRANTS=INTACT")
    print("AUTOMATIC_EDGE_TO_DIRECT_FALLBACK=false")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")
    print("PROOF_REEXECUTION_ALLOWED=false")
    print("LIVE_PROOF_EXECUTED=false")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
