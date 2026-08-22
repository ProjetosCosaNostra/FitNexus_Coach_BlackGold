from __future__ import annotations

import importlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
SEAL = BACKEND / "stage32_post_cutover_rollback_live_proof_workflow_seal_authority.json"
ROLLBACK_AUTHORITY = BACKEND / "stage32_post_cutover_rollback_proof_authority.json"
WORKFLOW = ROOT / ".github" / "workflows" / "stage32_post_cutover_rollback_live_proof.yml"

FAILURE_CLASS = "BGF-STAGE32-ROLLBACK-PROOF-REEXECUTION-242"
ROLLBACK_STATE = "POST_CUTOVER_ROLLBACK_FIXTURE_REMOTE_LIVE_PROOF_PENDING_EDGE_MODE"
PROOF_PR = 84
PROOF_BRANCH = "blackgold/stage32-post-cutover-rollback-live-proof-candidate"
PROOF_HEAD = "cb734b3ef51fe607d7d4de2709d517625a9c8101"
TRIGGER_BRANCH = "blackgold/stage32-post-cutover-rollback-live-proof-open-trigger"
TRIGGER_HEAD = "777bb51f698c0648cf641bba1070f5f71f001e87"
CANDIDATE_RUN = 32539035186
CANDIDATE_JOB = 96945178233


def fail(message: str) -> None:
    raise SystemExit(
        "STAGE32_POST_CUTOVER_ROLLBACK_LIVE_PROOF_WORKFLOW_SEAL_GUARD=FAIL\n"
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


def require(mapping: dict, expected: dict, label: str) -> None:
    for key, value in expected.items():
        if mapping.get(key) != value:
            fail(f"{label} drift: {key}")


def main() -> None:
    current = importlib.import_module(
        "verify_stage32_post_cutover_rollback_proof_preparation"
    )
    current.main()

    seal = load(SEAL)
    rollback = load(ROLLBACK_AUTHORITY)
    workflow = text(WORKFLOW)

    require(
        seal,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "stage": "STAGE32_POST_CUTOVER_ROLLBACK_LIVE_PROOF_WORKFLOW_SEAL",
            "prevention_class": FAILURE_CLASS,
            "required_rollback_state": ROLLBACK_STATE,
        },
        "rollback workflow seal authority",
    )
    if rollback.get("current_state") != ROLLBACK_STATE:
        fail("rollback authority is not at the remote-fixture proof-pending frontier")

    require(
        seal.get("proof_pr", {}),
        {
            "number": PROOF_PR,
            "head_branch": PROOF_BRANCH,
            "head_sha": PROOF_HEAD,
            "base_branch": "main",
            "draft_when_sealed": True,
            "merge_allowed": False,
            "candidate_ci_run_id": CANDIDATE_RUN,
            "candidate_ci_job_id": CANDIDATE_JOB,
            "candidate_ci_conclusion": "success",
            "candidate_guard_passed": True,
        },
        "proof PR seal",
    )
    require(
        seal.get("open_trigger", {}),
        {
            "branch": TRIGGER_BRANCH,
            "head_sha": TRIGGER_HEAD,
            "merge_allowed": False,
            "open_before_seal_merge_allowed": False,
        },
        "fallback trigger seal",
    )

    contract = seal.get("workflow_contract", {})
    require(
        contract,
        {
            "file": ".github/workflows/stage32_post_cutover_rollback_live_proof.yml",
            "event": "pull_request",
            "event_types": ["ready_for_review", "opened"],
            "ready_path_requires_exact_pr_number": True,
            "ready_path_requires_exact_head_branch": True,
            "ready_path_requires_exact_head_sha": True,
            "opened_fallback_requires_exact_head_branch": True,
            "opened_fallback_requires_exact_head_sha": True,
            "job_requires_run_attempt_one": True,
            "checkout_ref_is_exact_proof_head_sha": True,
            "candidate_guard_runs_before_flutter_setup": True,
            "live_test_requires_explicit_enable_environment": True,
            "synthetic_token_derived_from_public_seed_at_runtime": True,
            "authorized_rollback_proof_object_required": True,
            "production_singleton_must_remain_edge": True,
            "automatic_fallback_forbidden": True,
            "workflow_dispatch_allowed": False,
            "synchronize_allowed": False,
            "reopened_allowed": False,
            "schedule_allowed": False,
            "service_role_secret_used": False,
            "synthetic_token_printed": False,
        },
        "workflow contract",
    )

    required_fragments = (
        "types: [ready_for_review, opened]",
        "github.event.pull_request.number == 84",
        f"github.event.pull_request.head.ref == '{PROOF_BRANCH}'",
        f"github.event.pull_request.head.sha == '{PROOF_HEAD}'",
        f"github.event.pull_request.head.ref == '{TRIGGER_BRANCH}'",
        f"github.event.pull_request.head.sha == '{TRIGGER_HEAD}'",
        "github.run_attempt == 1",
        f"ref: {PROOF_HEAD}",
        "verify_stage32_post_cutover_rollback_live_proof_candidate.py",
        "fitnexus-stage32-post-cutover-rollback-proof-v1",
        "STAGE32_POST_CUTOVER_ROLLBACK_PROOF_ENABLED=1",
        "STAGE32_ROLLBACK_SYNTHETIC_TOKEN=$TOKEN",
        "student_access_stage32_post_cutover_live_rollback_proof_test.dart",
        "AUTHORIZED_ROLLBACK_OBJECT=StudentAccessTransport.forAuthorizedRollbackProof",
        "PRODUCTION_SINGLETON=StudentAccessTransport.instance",
        "PRODUCTION_ACTIVE_TRANSPORT=edgeGateway",
        "PRODUCTION_ROLLBACK_REQUESTED=false",
        "PRODUCTION_ROLLBACK_AUTHORIZED=false",
        "AUTOMATIC_EDGE_TO_DIRECT_FALLBACK=false",
        "DIRECT_RPC_BRANCH_EXPECTED=true",
        "PROOF_REEXECUTION_ALLOWED=false",
        "CLEANUP_REQUIRED=true",
        "LAUNCH_GATE_PROMOTION=DENIED",
    )
    for fragment in required_fragments:
        if fragment not in workflow:
            fail(f"rollback workflow drift: {fragment}")

    for forbidden in ("workflow_dispatch:", "schedule:", "synchronize", "reopened"):
        if forbidden in workflow:
            fail(f"rollback workflow became replayable through {forbidden}")
    candidate_pos = workflow.find(
        "verify_stage32_post_cutover_rollback_live_proof_candidate.py"
    )
    flutter_pos = workflow.find("Set up Flutter stable")
    if candidate_pos < 0 or flutter_pos < 0 or candidate_pos > flutter_pos:
        fail("candidate guard does not run before Flutter setup")

    gate = seal.get("pre_event_live_gate", {})
    require(
        gate,
        {
            "required_after_seal_merge": True,
            "required_immediately_before_event_delivery": True,
            "source": "Supabase.execute_sql",
            "minimum_remaining_fixture_ttl_minutes": 60,
            "requires_exact_single_rollback_fixture": True,
            "requires_workout_sessions_zero": True,
            "requires_workout_logs_zero": True,
            "requires_workout_feedback_zero": True,
            "requires_fixture_command_receipts_zero": True,
            "requires_fixture_rate_buckets_zero": True,
            "requires_fixture_security_events_zero": True,
            "requires_fixture_security_signals_zero": True,
            "requires_all_five_anon_execute_intact": True,
            "requires_all_five_authenticated_execute_intact": True,
            "requires_production_edge_gateway": True,
            "requires_production_rollback_requested_false": True,
            "requires_production_rollback_authorized_false": True,
            "requires_automatic_edge_to_direct_fallback_false": True,
            "requires_direct_rpc_execute_unrevoked": True,
            "receipt_observed_at_utc": None,
            "result": None,
        },
        "pre-event live gate",
    )

    require(
        seal.get("proof_boundary", {}),
        {
            "fixture_remote_version": "20260821235550",
            "production_active_transport": "edgeGateway",
            "production_singleton": "StudentAccessTransport.instance",
            "authorized_rollback_object": "StudentAccessTransport.forAuthorizedRollbackProof",
            "automatic_edge_to_direct_fallback": False,
            "production_explicit_rollback_requested": False,
            "production_explicit_rollback_authorized": False,
            "direct_rpc_execute_revoked": False,
            "post_cutover_edge_live_proof_verified": True,
            "post_cutover_edge_cleanup_verified": True,
            "post_cutover_rollback_verified": False,
            "real_customer_data_allowed": False,
            "production_transport_change_allowed": False,
            "launch_gate_promotion_allowed": False,
            "cleanup_required_after_proof": True,
        },
        "rollback proof boundary",
    )

    require(
        seal.get("execution_receipt", {}),
        {
            "workflow_run_id": None,
            "job_id": None,
            "result": None,
            "executed": False,
            "run_attempt": None,
            "routes_verified": 0,
            "proof_head_checked_out": None,
            "authorized_rollback_object_verified": False,
            "direct_rpc_branch_verified": False,
            "production_edge_mode_preserved": False,
            "automatic_fallback_remained_false": False,
            "raw_synthetic_token_printed": False,
            "direct_rpc_grants_changed": False,
            "direct_rpc_privilege_revocation": False,
            "real_customer_data_used": False,
            "launch_gate_promotion": False,
            "proof_reexecution_allowed": False,
            "cleanup_completed": False,
        },
        "execution receipt",
    )

    runtime = rollback.get("runtime_proof", {})
    if runtime.get("workflow_run_id") is not None or runtime.get("result") is not None:
        fail("rollback proof self-attested before sealed event delivery")
    if runtime.get("proof_reexecution_allowed") is not False:
        fail("rollback authority permits proof replay")

    require(
        seal.get("next_stage", {}),
        {
            "name": "MERGE_ROLLBACK_WORKFLOW_SEAL_THEN_DELIVER_EVENT_ONCE",
            "seal_pr_must_pass_ci": True,
            "seal_pr_must_merge_before_event": True,
            "fresh_pre_event_live_gate_required": True,
            "preferred_event": "ready_for_review",
            "fallback_event": "opened",
            "may_change_proof_head_after_seal": False,
            "may_execute_more_than_once": False,
            "may_reexecute_stage32_edge_live_proof": False,
            "may_reapply_rollback_fixture": False,
            "may_revoke_direct_rpc_execute_now": False,
            "may_promote_launch_gates": False,
        },
        "seal next stage",
    )

    print("STAGE32_POST_CUTOVER_ROLLBACK_LIVE_PROOF_WORKFLOW_SEAL_GUARD=PASS")
    print(f"SEALED_PROOF_PR={PROOF_PR}")
    print(f"SEALED_PROOF_HEAD={PROOF_HEAD}")
    print(f"CANDIDATE_CI_RUN={CANDIDATE_RUN}")
    print(f"CANDIDATE_CI_JOB={CANDIDATE_JOB}")
    print("CANDIDATE_CI=success")
    print(f"OPEN_TRIGGER_HEAD={TRIGGER_HEAD}")
    print("ROLLBACK_LIVE_PROOF_EXECUTED=false")
    print("PROOF_REEXECUTION_ALLOWED=false")
    print("FRESH_PRE_EVENT_LIVE_GATE_REQUIRED=true")
    print("PRODUCTION_ACTIVE_TRANSPORT=edgeGateway")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
