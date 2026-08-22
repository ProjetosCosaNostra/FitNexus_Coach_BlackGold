from __future__ import annotations

import importlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
APP = ROOT / "03_app_flutter" / "fitnexus_app"
AUTHORITY = BACKEND / "stage32_post_cutover_rollback_proof_authority.json"
TEST = APP / "test" / "student_access_stage32_post_cutover_live_rollback_proof_test.dart"
TRANSPORT = APP / "lib" / "features" / "student" / "student_access_transport.dart"
CONTRACT = APP / "lib" / "features" / "student" / "student_access_transport_contract.dart"

STATE = "POST_CUTOVER_ROLLBACK_FIXTURE_REMOTE_LIVE_PROOF_PENDING_EDGE_MODE"
FAILURE_CLASS = "BGF-STAGE32-ROLLBACK-PROOF-REEXECUTION-242"


def fail(message: str) -> None:
    raise SystemExit(
        "STAGE32_POST_CUTOVER_ROLLBACK_LIVE_PROOF_CANDIDATE_GUARD=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\nDETAIL={message}"
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
    # The full current lifecycle guard remains the first authority. The candidate
    # guard only narrows that already-valid frontier into an immutable proof head.
    current = importlib.import_module(
        "verify_stage32_post_cutover_rollback_proof_preparation"
    )
    current.main()

    authority = load(AUTHORITY)
    test = text(TEST)
    transport = text(TRANSPORT)
    contract = text(CONTRACT)

    if authority.get("current_state") != STATE:
        fail("rollback authority is not at the remote-fixture live-proof-pending frontier")
    fixture = authority.get("fixture", {})
    if fixture.get("migration_ledger_state") != "remote_reconciled":
        fail("rollback fixture is not remote-reconciled")
    if fixture.get("remote_applied") is not True or fixture.get("remote_version") != "20260821235550":
        fail("rollback fixture remote receipt drifted")

    runtime = authority.get("runtime_proof", {})
    for key in ("workflow_run_id", "workflow_job_id", "result", "proof_head_sha"):
        if runtime.get(key) is not None:
            fail(f"rollback live proof self-attested before sealed execution: {key}")
    for key in (
        "authorized_rollback_object_verified",
        "direct_rpc_branch_verified",
        "get_workout_verified",
        "start_workout_verified",
        "set_completion_verified",
        "get_feedback_context_verified",
        "submit_feedback_verified",
        "all_five_routes_verified",
        "production_edge_mode_preserved",
        "automatic_fallback_remained_false",
        "direct_rpc_grants_changed",
        "real_customer_data_used",
        "cleanup_completed",
        "proof_reexecution_allowed",
    ):
        if runtime.get(key) is not False:
            fail(f"rollback runtime proof drift before execution: {key}")

    required_test = (
        "STAGE32_POST_CUTOVER_ROLLBACK_PROOF_ENABLED",
        "StudentAccessTransport.forAuthorizedRollbackProof",
        "final transport = StudentAccessTransport.forAuthorizedRollbackProof(",
        "const emptyEdgePayload = <String, dynamic>{};",
        "explicitRollbackRequested: true",
        "explicitRollbackAuthorized: true",
        "33000000000000000000000000000001",
        "33000000000000000000000000000002",
        "33000000000000000000000000000003",
        "SharedPreferences.setMockInitialValues(<String, Object>{});",
        "StudentAccessTransportContract.activeMode",
        "StudentAccessTransportMode.edgeGateway",
    )
    for fragment in required_test:
        if fragment not in test:
            fail(f"focused rollback proof source drift: {fragment}")
    if ".rpc(" in test or ".functions.invoke(" in test:
        fail("focused rollback proof bypasses StudentAccessTransport")

    required_transport = (
        "factory StudentAccessTransport.forAuthorizedRollbackProof",
        "configuredModeOverride: StudentAccessTransportMode.edgeGateway",
        "explicitRollbackRequestedOverride: true",
        "explicitRollbackAuthorizedOverride: true",
        "return _client.rpc(directRpc, params: directParams);",
    )
    for fragment in required_transport:
        if fragment not in transport:
            fail(f"rollback proof transport seam drift: {fragment}")

    for fragment in (
        "StudentAccessTransportMode.edgeGateway;",
        "static const bool automaticEdgeToDirectFallback = false;",
        "static const bool explicitRollbackRequested = false;",
        "static const bool explicitRollbackAuthorized = false;",
        "static const bool directRpcExecuteRevoked = false;",
        "static const bool rollbackVerified = false;",
        "static const bool clientCutoverVerified = false;",
    ):
        if fragment not in contract:
            fail(f"production rollback boundary drift: {fragment}")

    next_stage = authority.get("next_stage", {})
    if next_stage.get("requires_new_exact_proof_head") is not True:
        fail("exact proof-head interlock disappeared")
    if next_stage.get("requires_new_one_shot_workflow_seal") is not True:
        fail("one-shot workflow seal interlock disappeared")
    if next_stage.get("may_execute_live_rollback_proof_before_workflow_seal") is not False:
        fail("rollback live proof became executable before workflow seal")
    if next_stage.get("may_revoke_direct_rpc_execute_now") is not False:
        fail("direct RPC revocation became allowed before rollback proof")
    if next_stage.get("may_promote_launch_gates") is not False:
        fail("launch promotion became allowed before rollback proof")

    print("STAGE32_POST_CUTOVER_ROLLBACK_LIVE_PROOF_CANDIDATE_GUARD=PASS")
    print(f"CURRENT_STATE={STATE}")
    print("FIXTURE_REMOTE_VERSION=20260821235550")
    print("ROLLBACK_PROOF_EXECUTED=false")
    print("PROOF_REEXECUTION_ALLOWED=false")
    print("PRODUCTION_ACTIVE_TRANSPORT=edgeGateway")
    print("PRODUCTION_SINGLETON=StudentAccessTransport.instance")
    print("AUTHORIZED_ROLLBACK_OBJECT=proof-only")
    print("EXPECTED_ROUTES=5")
    print("AUTOMATIC_EDGE_TO_DIRECT_FALLBACK=false")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
