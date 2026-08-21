from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
APP = ROOT / "03_app_flutter" / "fitnexus_app"
AUTHORITY = BACKEND / "student_access_runtime_rollback_authority.json"
SMOKE = BACKEND / "student_access_client_runtime_smoke_authority.json"
CUTOVER = BACKEND / "student_access_client_cutover_authority.json"
LEDGER = BACKEND / "migration_ledger_authority.json"
CONTRACT = APP / "lib" / "features" / "student" / "student_access_transport_contract.dart"
TEST = APP / "test" / "student_access_runtime_rollback_proof_test.dart"
WORKFLOW = ROOT / ".github" / "workflows" / "stage30_runtime_rollback_proof.yml"

FAILURE_CLASSES = [
    "BGF-ROLLBACK-PROOF-PRODUCTION-MODE-MUTATION-208",
    "BGF-ROLLBACK-PROOF-UNAUTHORIZED-FAILOPEN-209",
    "BGF-ROLLBACK-PROOF-AUTOMATIC-FALLBACK-210",
    "BGF-ROLLBACK-PROOF-DIRECT-GRANT-REVOCATION-211",
    "BGF-ROLLBACK-PROOF-REEXECUTION-212",
]
STATE_CANDIDATE = "RUNTIME_ROLLBACK_PROOF_CANDIDATE_DIRECT_MODE"
STATE_VERIFIED = "RUNTIME_ROLLBACK_PROOF_VERIFIED_DIRECT_MODE"
SEALED_RUN = 32464990624
SEALED_JOB = 96719614075


def fail(message: str) -> None:
    raise SystemExit("STUDENT_ACCESS_RUNTIME_ROLLBACK_CANDIDATE_GUARD=FAIL\n" + message)


def text(path: Path) -> str:
    if not path.is_file():
        fail(f"missing source: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def data(path: Path) -> dict:
    try:
        value = json.loads(text(path))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path.relative_to(ROOT)}: {exc}")
    if not isinstance(value, dict):
        fail(f"expected JSON object: {path.relative_to(ROOT)}")
    return value


def require(mapping: dict, expected: dict, label: str) -> None:
    for key, value in expected.items():
        if mapping.get(key) != value:
            fail(f"{label} drift: {key}")


def verify_prerequisites(authority: dict, smoke: dict, cutover: dict, ledger: dict) -> None:
    prerequisites = authority.get("prerequisites", {})
    require(
        prerequisites,
        {
            "runtime_smoke_authority_file": "04_backend_supabase/student_access_client_runtime_smoke_authority.json",
            "runtime_smoke_required_state": "EDGE_RUNTIME_SMOKE_LIVE_VERIFIED_CLEANUP_COMPLETE",
            "runtime_smoke_routes_verified": 5,
            "runtime_smoke_cleanup_completed": True,
            "runtime_smoke_synthetic_residue_zero": True,
            "cutover_authority_file": "04_backend_supabase/student_access_client_cutover_authority.json",
            "cutover_required_state": "CLIENT_EDGE_ERROR_CONTRACT_ROLLBACK_HARNESS_READY_DIRECT_MODE",
            "edge_runtime_version": 3,
        },
        "rollback prerequisites",
    )

    if smoke.get("current_state") != prerequisites["runtime_smoke_required_state"]:
        fail("Stage 30 smoke cleanup prerequisite not sealed")
    runtime = smoke.get("runtime_proof", {})
    if runtime.get("all_five_routes_verified") is not True or runtime.get("cleanup_completed") is not True:
        fail("Stage 30 live smoke/cleanup proof prerequisite missing")
    for key in (
        "synthetic_business_rows_remaining",
        "synthetic_security_rows_remaining",
        "synthetic_network_proof_rows_remaining",
    ):
        if runtime.get(key) != 0:
            fail(f"synthetic residue prerequisite drift: {key}")

    if cutover.get("current_state") != prerequisites["cutover_required_state"]:
        fail("cutover authority moved before rollback-proof reconciliation stage")
    inventory = cutover.get("current_client_inventory", {})
    require(
        inventory,
        {
            "transport_mode": "direct_rpc",
            "flutter_uses_edge_gateway": False,
            "direct_v2_rpc_path_active": True,
            "direct_anon_v2_rpc_execute_revoked": False,
            "repositories_call_supabase_rpc_directly": False,
            "repositories_call_single_transport": True,
        },
        "current client inventory",
    )
    transport = cutover.get("transport_contract", {})
    require(
        transport,
        {
            "active_mode": "directRpc",
            "resolved_mode": "directRpc",
            "edge_gateway_selected": False,
            "automatic_edge_to_direct_fallback": False,
            "explicit_rollback_requested": False,
            "explicit_rollback_authorized": False,
            "direct_rpc_execute_revoked": False,
            "rollback_verified": False,
            "client_cutover_verified": False,
            "behavioral_transport_change": False,
        },
        "cutover transport",
    )

    if any(
        isinstance(row, dict) and row.get("direction") == "repo_only"
        for row in ledger.get("declared_divergences", [])
    ):
        fail("rollback proof must not carry a migration repo_only divergence")
    remote = {
        row.get("name"): row.get("version")
        for row in ledger.get("remote_migrations", [])
        if isinstance(row, dict)
    }
    if remote.get("stage30_edge_runtime_smoke_cleanup") != "20260821083507":
        fail("Stage 30 cleanup migration is not reconciled before rollback proof")


def verify_sources() -> None:
    contract = text(CONTRACT)
    proof_test = text(TEST)
    workflow = text(WORKFLOW)

    for fragment in (
        "StudentAccessTransportMode resolveStudentAccessTransportMode",
        "if (!explicitRollbackRequested) return configuredMode;",
        "if (!explicitRollbackAuthorized)",
        "configuredMode != StudentAccessTransportMode.edgeGateway",
        "return StudentAccessTransportMode.directRpc;",
        "static const StudentAccessTransportMode activeMode =",
        "StudentAccessTransportMode.directRpc;",
        "static const bool edgeGatewaySelected = false;",
        "static const bool automaticEdgeToDirectFallback = false;",
        "static const bool explicitRollbackRequested = false;",
        "static const bool explicitRollbackAuthorized = false;",
        "static const bool directRpcExecuteRevoked = false;",
        "static const bool rollbackVerified = false;",
        "static const bool clientCutoverVerified = false;",
    ):
        if fragment not in contract:
            fail(f"rollback resolver/production contract drift: {fragment}")

    for fragment in (
        "Stage 30 runtime rollback proof",
        "production transport remains direct and rollback controls stay inert",
        "configured Edge stays Edge when rollback was not requested",
        "unauthorized rollback request fails closed",
        "authorized explicit Edge rollback resolves to direct RPC",
        "rollback is rejected when the configured transport is already direct",
        "authorized resolver is deterministic and does not require a network client",
        "configuredMode: StudentAccessTransportMode.edgeGateway",
        "explicitRollbackRequested: true",
        "explicitRollbackAuthorized: true",
        "throwsA(isA<StateError>())",
    ):
        if fragment not in proof_test:
            fail(f"focused rollback proof test drift: {fragment}")
    lower_test = proof_test.lower()
    for forbidden in ("supabase", "dart:io", "http://", "https://", "functions.invoke", ".rpc("):
        if forbidden in lower_test:
            fail(f"rollback proof unexpectedly depends on network/client material: {forbidden}")

    for fragment in (
        "types: [opened]",
        "Runtime rollback candidate guard",
        "flutter test test/student_access_runtime_rollback_proof_test.dart --reporter expanded",
        "PRODUCTION_TRANSPORT_CHANGE=false",
        "NETWORK_CALL_EXECUTED=false",
        "REAL_CUSTOMER_DATA_USED=false",
        "DIRECT_RPC_GRANTS_CHANGED=false",
        "EDGE_SELECTION=false",
        "LAUNCH_GATE_PROMOTION=DENIED",
    ):
        if fragment not in workflow:
            fail(f"one-shot rollback workflow drift: {fragment}")
    for forbidden in ("workflow_dispatch:", "types: [synchronize]", "types: [opened, synchronize]", "schedule:"):
        if forbidden in workflow:
            fail(f"{FAILURE_CLASSES[4]} rollback proof workflow became replayable: {forbidden}")


def verify_production_boundary(authority: dict, verified: bool) -> None:
    production = authority.get("production_boundary", {})
    require(
        production,
        {
            "active_transport": "directRpc",
            "resolved_transport": "directRpc",
            "edge_gateway_selected": False,
            "automatic_edge_to_direct_fallback": False,
            "explicit_rollback_requested": False,
            "explicit_rollback_authorized": False,
            "direct_rpc_execute_revoked": False,
            "client_cutover_verified": False,
            "runtime_rollback_verified": verified,
            "behavioral_transport_change": False,
        },
        "rollback production boundary",
    )


def verify_candidate(authority: dict) -> None:
    proof = authority.get("runtime_proof", {})
    for key in (
        "focused_test_passed",
        "production_constants_unchanged",
        "edge_without_rollback_verified",
        "unauthorized_rollback_fail_closed_verified",
        "authorized_edge_to_direct_verified",
        "rollback_from_direct_rejected_verified",
        "deterministic_resolution_verified",
        "network_call_executed",
        "real_customer_data_used",
        "direct_rpc_grants_changed",
        "proof_reexecution_allowed",
    ):
        if proof.get(key) is not False:
            fail(f"rollback proof self-attested before execution: {key}")
    if proof.get("workflow_run_id") is not None or proof.get("result") is not None:
        fail("rollback workflow receipt appeared before one-shot proof")

    next_stage = authority.get("next_stage", {})
    require(
        next_stage,
        {
            "name": "EXECUTE_STAGE30_RUNTIME_ROLLBACK_PROOF_ONCE",
            "allowed_now": True,
            "requires_one_shot_workflow": True,
            "requires_production_transport_change": False,
        },
        "rollback candidate next stage",
    )


def verify_sealed(authority: dict) -> None:
    proof = authority.get("runtime_proof", {})
    require(
        proof,
        {
            "workflow_run_id": SEALED_RUN,
            "result": "PASS",
            "focused_test_passed": True,
            "focused_tests_passed_count": 6,
            "production_constants_unchanged": True,
            "edge_without_rollback_verified": True,
            "unauthorized_rollback_fail_closed_verified": True,
            "authorized_edge_to_direct_verified": True,
            "rollback_from_direct_rejected_verified": True,
            "deterministic_resolution_verified": True,
            "network_call_executed": False,
            "real_customer_data_used": False,
            "direct_rpc_grants_changed": False,
            "edge_selected": False,
            "launch_gate_promoted": False,
            "proof_reexecution_allowed": False,
        },
        "sealed rollback runtime proof",
    )

    receipt = authority.get("proof_receipt", {})
    require(
        receipt,
        {
            "workflow_run_id": SEALED_RUN,
            "job_id": SEALED_JOB,
            "result": "PASS",
            "focused_test_result": "All tests passed!",
            "focused_tests_passed_count": 6,
            "production_transport_change": False,
            "network_call_executed": False,
            "real_customer_data_used": False,
            "direct_rpc_grants_changed": False,
            "edge_selection": False,
            "launch_gate_promotion": False,
            "workflow_trigger": "pull_request_opened_one_shot",
            "proof_reexecution_allowed": False,
        },
        "sealed rollback receipt",
    )

    reconciliation = authority.get("cutover_reconciliation", {})
    require(
        reconciliation,
        {
            "cutover_authority_reconciled": False,
            "required_next_state": "CLIENT_RUNTIME_ROLLBACK_VERIFIED_DIRECT_MODE",
            "production_transport_change_allowed_in_reconciliation": False,
            "edge_selection_allowed_in_reconciliation": False,
            "direct_rpc_execute_revocation_allowed_in_reconciliation": False,
        },
        "rollback cutover reconciliation",
    )
    next_stage = authority.get("next_stage", {})
    require(
        next_stage,
        {
            "name": "RECONCILE_STAGE30_ROLLBACK_PROOF_IN_CUTOVER_AUTHORITY",
            "allowed_now": True,
            "requires_production_transport_change": False,
            "may_select_edge_gateway_now": False,
            "may_revoke_direct_rpc_execute_now": False,
        },
        "rollback verified next stage",
    )


def main() -> None:
    authority = data(AUTHORITY)
    smoke = data(SMOKE)
    cutover = data(CUTOVER)
    ledger = data(LEDGER)

    if authority.get("schema_version") != 1 or authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("rollback authority identity drifted")
    if authority.get("baseline_main_sha") != "f1b97f3b56124f2fd2d3edcff7060afd82f08c1e":
        fail("rollback proof baseline main SHA drifted")
    if authority.get("failure_classes") != FAILURE_CLASSES:
        fail("rollback proof failure-class authority drifted")

    state = authority.get("current_state")
    if state not in {STATE_CANDIDATE, STATE_VERIFIED}:
        fail(f"unsupported rollback proof state: {state}")

    verify_prerequisites(authority, smoke, cutover, ledger)
    verify_sources()
    verified = state == STATE_VERIFIED
    verify_production_boundary(authority, verified)

    promotion = authority.get("promotion_rules", {})
    for key in (
        "may_change_production_active_mode_during_proof",
        "may_select_edge_gateway_during_proof",
        "may_enable_automatic_edge_to_direct_fallback",
        "may_revoke_direct_rpc_execute_during_proof",
        "may_use_real_customer_data",
        "may_promote_launch_gates",
    ):
        if promotion.get(key) is not False:
            fail(f"rollback proof gained prohibited authority: {key}")
    if promotion.get("edge_selection_requires_separate_post_proof_stage") is not True:
        fail("separate post-proof Edge selection interlock missing")

    if verified:
        verify_sealed(authority)
    else:
        verify_candidate(authority)

    print("STUDENT_ACCESS_RUNTIME_ROLLBACK_CANDIDATE_GUARD=PASS")
    print(f"CURRENT_STATE={state}")
    print("PRODUCTION_ACTIVE_TRANSPORT=directRpc")
    print("EDGE_SELECTION=false")
    print("AUTOMATIC_EDGE_TO_DIRECT_FALLBACK=false")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")
    print("REAL_CUSTOMER_DATA_REQUIRED=false")
    print("NETWORK_CALL_REQUIRED=false")
    print("ROLLBACK_RUNTIME_PROOF=" + ("VERIFIED_SEALED" if verified else "READY_NOT_EXECUTED"))
    print("PROOF_REEXECUTION_ALLOWED=false")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
