from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
SEAL = BACKEND / "stage31_live_proof_workflow_seal_authority.json"
STAGE31 = BACKEND / "student_access_client_edge_runtime_proof_authority.json"
CUTOVER = BACKEND / "student_access_client_cutover_authority.json"
WORKFLOW = ROOT / ".github" / "workflows" / "stage31_client_edge_runtime_live_proof.yml"

PREVENTION_CLASS = "BGF-STAGE31-LIVE-PROOF-WORKFLOW-SEAL-223"
DELIVERY_FAILURE_CLASS = "BGF-STAGE31-READY-FOR-REVIEW-EVENT-NONDELIVERY-224"
POST_PROOF_REPO_STATE = "CLIENT_EDGE_RUNTIME_PROOF_LIVE_VERIFIED_CLEANUP_REPO_ONLY_DIRECT_MODE"
POST_PROOF_CLEAN_STATE = "CLIENT_EDGE_RUNTIME_PROOF_LIVE_VERIFIED_CLEANUP_COMPLETE_DIRECT_MODE"
POST_PROOF_STATES = {POST_PROOF_REPO_STATE, POST_PROOF_CLEAN_STATE}
PROOF_PR = 61
PROOF_BRANCH = "blackgold/stage31-client-edge-live-proof"
PROOF_HEAD = "b8be62be0ba36c61b9557bed03e72dc05b0a43f0"
FALLBACK_BRANCH = "blackgold/stage31-live-proof-open-trigger-224"
FALLBACK_HEAD = "8f1c1933c5822d4a20abc8bb9260007f1a109cc3"
RUN_ID = 32480597745
JOB_ID = 96765899124


def fail(message: str) -> None:
    raise SystemExit("STAGE31_LIVE_PROOF_WORKFLOW_SEAL_GUARD=FAIL\n" + message)


def data(path: Path) -> dict:
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
    seal = data(SEAL)
    stage31 = data(STAGE31)
    cutover = data(CUTOVER)
    workflow = text(WORKFLOW)

    require(
        seal,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "prevention_class": PREVENTION_CLASS,
            "delivery_failure_class": DELIVERY_FAILURE_CLASS,
        },
        "workflow seal authority",
    )
    require(
        seal.get("proof_pr", {}),
        {
            "number": PROOF_PR,
            "head_branch": PROOF_BRANCH,
            "head_sha": PROOF_HEAD,
            "base_branch": "main",
            "draft_when_sealed": True,
            "candidate_quality_gate_run_id": 32478844026,
            "candidate_quality_gate_job_id": 96760703404,
            "candidate_quality_gate_result": "SUCCESS",
        },
        "sealed proof PR",
    )
    require(
        seal.get("trigger_delivery", {}),
        {
            "ready_for_review_transitions_attempted": 2,
            "ready_for_review_actions_run_observed": False,
            "fallback_event": "pull_request.opened",
            "fallback_branch": FALLBACK_BRANCH,
            "fallback_head_sha": FALLBACK_HEAD,
            "fallback_trigger_pr": 64,
            "fallback_trigger_pr_closed_unmerged_after_execution": True,
            "fallback_head_consumed": True,
            "proof_checkout_still_used_original_proof_head": True,
        },
        "trigger delivery authority",
    )

    contract = seal.get("workflow_contract", {})
    if contract.get("event") != "pull_request" or contract.get("event_types") != ["ready_for_review", "opened"]:
        fail("workflow event contract drifted")
    for key in (
        "ready_path_requires_exact_pr_number",
        "ready_path_requires_exact_head_branch",
        "ready_path_requires_exact_head_sha",
        "opened_fallback_requires_exact_head_branch",
        "opened_fallback_requires_exact_head_sha",
        "job_requires_run_attempt_one",
        "checkout_ref_is_exact_proof_head_sha",
        "live_test_requires_explicit_enable_environment",
        "synthetic_token_derived_from_public_seed_at_runtime",
    ):
        if contract.get(key) is not True:
            fail(f"workflow seal invariant missing: {key}")
    for key in (
        "workflow_dispatch_allowed",
        "synchronize_allowed",
        "reopened_allowed",
        "schedule_allowed",
        "synthetic_token_printed",
        "service_role_secret_used",
    ):
        if contract.get(key) is not False:
            fail(f"workflow seal prohibition drifted: {key}")

    require(
        seal.get("proof_boundary", {}),
        {
            "fixture_remote_version": "20260821113205",
            "production_active_transport": "directRpc",
            "edge_gateway_selected_in_production": False,
            "automatic_edge_to_direct_fallback": False,
            "direct_rpc_execute_revoked": False,
            "real_customer_data_allowed": False,
            "launch_gate_promotion_allowed": False,
            "cleanup_required_after_proof": True,
        },
        "sealed proof boundary",
    )
    require(
        seal.get("execution_receipt", {}),
        {
            "workflow_run_id": RUN_ID,
            "job_id": JOB_ID,
            "result": "SUCCESS",
            "executed": True,
            "run_attempt": 1,
            "proof_test_result": "ALL_TESTS_PASSED",
            "routes_verified": 5,
            "proof_head_checked_out": PROOF_HEAD,
            "raw_synthetic_token_printed": False,
            "production_transport_change": False,
            "edge_selection": False,
            "automatic_edge_to_direct_fallback": False,
            "direct_rpc_grants_changed": False,
            "real_customer_data_used": False,
            "launch_gate_promotion": False,
            "proof_reexecution_allowed": False,
            "cleanup_completed": False,
        },
        "sealed execution receipt",
    )

    state = stage31.get("current_state")
    if state not in POST_PROOF_STATES:
        fail("Stage 31 authority is not at a verified post-proof state")
    cleanup_complete = state == POST_PROOF_CLEAN_STATE

    runtime_expected = {
        "workflow_run_id": RUN_ID,
        "workflow_job_id": JOB_ID,
        "result": "PASS",
        "proof_pr": PROOF_PR,
        "proof_head": PROOF_HEAD,
        "trigger_pr": 64,
        "trigger_head": FALLBACK_HEAD,
        "trigger_pr_closed_unmerged_after_execution": True,
        "flutter_transport_edge_path_verified": True,
        "get_workout_verified": True,
        "start_workout_verified": True,
        "set_completion_verified": True,
        "get_feedback_context_verified": True,
        "submit_feedback_verified": True,
        "all_five_routes_verified": True,
        "synthetic_fixture_mutated_as_expected": True,
        "raw_token_returned": False,
        "raw_network_origin_returned": False,
        "real_customer_data_used": False,
        "real_customer_data_mutated": False,
        "proof_reexecution_allowed": False,
        "cleanup_completed": cleanup_complete,
    }
    if cleanup_complete:
        runtime_expected.update(
            {
                "synthetic_business_rows_remaining": 0,
                "synthetic_security_rows_remaining": 0,
                "synthetic_network_proof_rows_remaining": 0,
            }
        )
    require(stage31.get("runtime_proof", {}), runtime_expected, "Stage 31 runtime receipt")

    require(
        cutover.get("transport_contract", {}),
        {
            "active_mode": "directRpc",
            "resolved_mode": "directRpc",
            "edge_gateway_selected": False,
            "automatic_edge_to_direct_fallback": False,
            "direct_rpc_execute_revoked": False,
            "client_cutover_verified": False,
        },
        "production client boundary",
    )

    required = (
        "types: [ready_for_review, opened]",
        "github.event.action == 'ready_for_review'",
        f"github.event.pull_request.number == {PROOF_PR}",
        f"github.event.pull_request.head.ref == '{PROOF_BRANCH}'",
        f"github.event.pull_request.head.sha == '{PROOF_HEAD}'",
        "github.event.action == 'opened'",
        f"github.event.pull_request.head.ref == '{FALLBACK_BRANCH}'",
        f"github.event.pull_request.head.sha == '{FALLBACK_HEAD}'",
        ") &&\n      github.run_attempt == 1",
        f"ref: {PROOF_HEAD}",
        "verify_student_access_stage31_live_proof_candidate.py",
        "STAGE31_LIVE_PROOF_ENABLED=1",
        "fitnexus-stage31-client-edge-runtime-proof-v1",
        "STAGE31_SYNTHETIC_TOKEN=$TOKEN",
        "flutter test test/student_access_stage31_live_edge_proof_test.dart --reporter expanded",
        f"OPEN_TRIGGER_FAILURE_CLASS={DELIVERY_FAILURE_CLASS}",
        f"OPEN_TRIGGER_HEAD={FALLBACK_HEAD}",
        "PRODUCTION_TRANSPORT_CHANGE=false",
        "EDGE_SELECTION=false",
        "DIRECT_RPC_GRANTS_CHANGED=false",
        "REAL_CUSTOMER_DATA_USED=false",
        "LAUNCH_GATE_PROMOTION=DENIED",
    )
    for fragment in required:
        if fragment not in workflow:
            fail(f"sealed workflow source drifted: {fragment}")
    for forbidden in (
        "workflow_dispatch:",
        "types: [synchronize]",
        "reopened",
        "schedule:",
        "SUPABASE_SERVICE_ROLE_KEY",
        "SUPABASE_SECRET_KEY",
    ):
        if forbidden in workflow:
            fail(f"sealed workflow became replayable or privileged: {forbidden}")

    print("STAGE31_LIVE_PROOF_WORKFLOW_SEAL_GUARD=PASS")
    print(f"PREVENTION_CLASS={PREVENTION_CLASS}")
    print(f"DELIVERY_FAILURE_CLASS={DELIVERY_FAILURE_CLASS}")
    print(f"SEALED_PR={PROOF_PR}")
    print(f"SEALED_PROOF_HEAD={PROOF_HEAD}")
    print(f"FALLBACK_HEAD={FALLBACK_HEAD}")
    print(f"WORKFLOW_RUN_ID={RUN_ID}")
    print(f"WORKFLOW_JOB_ID={JOB_ID}")
    print("LIVE_PROOF_EXECUTED=true")
    print("ROUTES_VERIFIED=5")
    print("PROOF_REEXECUTION_ALLOWED=false")
    print("PRODUCTION_ACTIVE_TRANSPORT=directRpc")
    print("EDGE_SELECTION=false")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")
    print("CLEANUP_COMPLETED=" + str(cleanup_complete).lower())
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
