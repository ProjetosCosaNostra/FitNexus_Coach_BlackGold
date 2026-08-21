from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"

SEAL = BACKEND / "stage32_post_cutover_live_proof_r1_workflow_seal_authority.json"
RECOVERY = BACKEND / "stage32_post_cutover_live_proof_failure_r0_authority.json"
RUNTIME = BACKEND / "student_access_stage32_post_cutover_runtime_proof_authority.json"
WORKFLOW = ROOT / ".github" / "workflows" / "stage32_post_cutover_edge_runtime_live_proof_r1.yml"
OLD_WORKFLOW = ROOT / ".github" / "workflows" / "stage32_post_cutover_edge_runtime_live_proof.yml"

FAILURE_CLASS = "BGF-STAGE32-POST-CUTOVER-PROOF-REEXECUTION-233"
PROOF_PR = 77
PROOF_BRANCH = "blackgold/stage32-post-cutover-live-proof-r1-candidate"
PROOF_HEAD = "344433bf502b519563fe328ab71e59249766e3dd"
TRIGGER_BRANCH = "blackgold/stage32-live-proof-r1-open-trigger"
TRIGGER_HEAD = "65e35282aa0e004134807553545e0859512cdef6"
CANDIDATE_RUN = 32531551273
CANDIDATE_JOB = 96924402174
OLD_RUN = 32508349425
OLD_HEAD = "370cfe65d3df5188c3f840d84b5a8748f1357cf2"
OLD_TRIGGER_HEAD = "84a51d97f3b7a7c53965567e21760d5d59c85f5a"
RECOVERY_STATUS = "PRE_NETWORK_FAILURE_RECORDED_FIXTURE_REARMED_R1_LIVE_PROOF_R1_PENDING"
RUNTIME_STATE = "POST_CUTOVER_EDGE_RUNTIME_PROOF_FIXTURE_REMOTE_LIVE_PROOF_PENDING_EDGE_MODE"


def fail(message: str) -> None:
    raise SystemExit(
        "STAGE32_POST_CUTOVER_LIVE_PROOF_R1_WORKFLOW_SEAL_GUARD=FAIL\n"
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


def require(mapping: dict, expected: dict, label: str) -> None:
    for key, value in expected.items():
        if mapping.get(key) != value:
            fail(f"{label} drift: {key}")


def main() -> None:
    seal = load(SEAL)
    recovery = load(RECOVERY)
    runtime = load(RUNTIME)
    workflow = text(WORKFLOW)
    old_workflow = text(OLD_WORKFLOW)

    require(
        seal,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "stage": "STAGE32_POST_CUTOVER_LIVE_PROOF_R1_WORKFLOW_SEAL",
            "prevention_class": FAILURE_CLASS,
            "required_recovery_status": RECOVERY_STATUS,
            "required_runtime_state": RUNTIME_STATE,
        },
        "R1 seal authority",
    )
    if recovery.get("status") != RECOVERY_STATUS:
        fail("recovery authority is not at the R1 proof-pending frontier")
    if runtime.get("current_state") != RUNTIME_STATE:
        fail("runtime proof authority is not at the live-proof-pending frontier")

    consumed = seal.get("consumed_r0", {})
    require(
        consumed,
        {
            "workflow_run_id": OLD_RUN,
            "workflow_job_id": 96853509377,
            "proof_pr": 71,
            "proof_head_sha": OLD_HEAD,
            "trigger_pr": 73,
            "trigger_head_sha": OLD_TRIGGER_HEAD,
            "routes_attempted": 0,
            "routes_verified": 0,
            "proof_credit": False,
            "reexecution_allowed": False,
        },
        "consumed R0",
    )

    proof_pr = seal.get("proof_pr", {})
    require(
        proof_pr,
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
        "R1 proof PR seal",
    )

    trigger = seal.get("open_trigger", {})
    require(
        trigger,
        {
            "branch": TRIGGER_BRANCH,
            "head_sha": TRIGGER_HEAD,
            "merge_allowed": False,
            "open_before_seal_merge_allowed": False,
        },
        "R1 fallback trigger",
    )

    contract = seal.get("workflow_contract", {})
    require(
        contract,
        {
            "file": ".github/workflows/stage32_post_cutover_edge_runtime_live_proof_r1.yml",
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
            "production_singleton_required": True,
            "verification_factory_forbidden": True,
            "shared_preferences_mock_required_before_supabase_initialize": True,
            "workflow_dispatch_allowed": False,
            "synchronize_allowed": False,
            "reopened_allowed": False,
            "schedule_allowed": False,
            "service_role_secret_used": False,
            "synthetic_token_printed": False,
        },
        "R1 workflow contract",
    )

    required_workflow_fragments = (
        "types: [ready_for_review, opened]",
        "github.event.pull_request.number == 77",
        f"github.event.pull_request.head.ref == '{PROOF_BRANCH}'",
        f"github.event.pull_request.head.sha == '{PROOF_HEAD}'",
        f"github.event.pull_request.head.ref == '{TRIGGER_BRANCH}'",
        f"github.event.pull_request.head.sha == '{TRIGGER_HEAD}'",
        "github.run_attempt == 1",
        f"ref: {PROOF_HEAD}",
        "verify_student_access_stage32_live_proof_r1_candidate.py",
        "fitnexus-stage32-post-cutover-edge-runtime-proof-v1",
        "STAGE32_POST_CUTOVER_LIVE_PROOF_ENABLED=1",
        "student_access_stage32_post_cutover_live_edge_proof_test.dart",
        "SEALED_PROOF_PR=77",
        f"SEALED_PROOF_HEAD={PROOF_HEAD}",
        f"OPEN_TRIGGER_HEAD={TRIGGER_HEAD}",
        "PRODUCTION_SINGLETON=StudentAccessTransport.instance",
        "PRODUCTION_ACTIVE_TRANSPORT=edgeGateway",
        "PROOF_REEXECUTION_ALLOWED=false",
        "CLEANUP_REQUIRED=true",
        "POST_CUTOVER_ROLLBACK_PROOF_REQUIRED=true",
        "LAUNCH_GATE_PROMOTION=DENIED",
    )
    for fragment in required_workflow_fragments:
        if fragment not in workflow:
            fail(f"R1 workflow drift: {fragment}")

    for forbidden in (
        "workflow_dispatch:",
        "schedule:",
        "synchronize",
        "reopened",
    ):
        if forbidden in workflow:
            fail(f"R1 workflow became replayable through: {forbidden}")

    candidate_pos = workflow.find("verify_student_access_stage32_live_proof_r1_candidate.py")
    flutter_pos = workflow.find("Set up Flutter stable")
    if candidate_pos < 0 or flutter_pos < 0 or candidate_pos > flutter_pos:
        fail("R1 candidate guard does not run before Flutter setup")

    # The consumed R0 workflow must remain sealed to its historical head. It is not
    # modified or repurposed for R1.
    for fragment in (
        "github.event.pull_request.number == 71",
        OLD_HEAD,
        OLD_TRIGGER_HEAD,
        "github.run_attempt == 1",
    ):
        if fragment not in old_workflow:
            fail(f"historical R0 workflow seal drifted: {fragment}")
    if "workflow_dispatch:" in old_workflow or "schedule:" in old_workflow:
        fail("historical R0 workflow became replayable")

    gate = seal.get("pre_event_live_gate", {})
    require(
        gate,
        {
            "required_after_seal_merge": True,
            "required_immediately_before_event_delivery": True,
            "source": "Supabase.execute_sql",
            "minimum_remaining_fixture_ttl_minutes": 60,
            "requires_exact_single_synthetic_fixture": True,
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
            "requires_automatic_edge_to_direct_fallback_false": True,
            "requires_direct_rpc_execute_unrevoked": True,
            "receipt_observed_at_utc": None,
            "result": None,
        },
        "pre-event live gate",
    )

    boundary = seal.get("proof_boundary", {})
    require(
        boundary,
        {
            "fixture_remote_version": "20260821171334",
            "rearm_remote_version": "20260821214005",
            "production_active_transport": "edgeGateway",
            "production_singleton": "StudentAccessTransport.instance",
            "edge_gateway_selected_in_production": True,
            "automatic_edge_to_direct_fallback": False,
            "direct_rpc_execute_revoked": False,
            "post_cutover_rollback_verified": False,
            "real_customer_data_allowed": False,
            "launch_gate_promotion_allowed": False,
            "cleanup_required_after_proof": True,
        },
        "R1 proof boundary",
    )

    execution = seal.get("execution_receipt", {})
    require(
        execution,
        {
            "workflow_run_id": None,
            "job_id": None,
            "result": None,
            "executed": False,
            "run_attempt": None,
            "routes_verified": 0,
            "proof_head_checked_out": None,
            "production_singleton_verified": False,
            "production_edge_mode_verified": False,
            "raw_synthetic_token_printed": False,
            "production_transport_change": False,
            "automatic_edge_to_direct_fallback": False,
            "direct_rpc_grants_changed": False,
            "direct_rpc_privilege_revocation": False,
            "real_customer_data_used": False,
            "launch_gate_promotion": False,
            "proof_reexecution_allowed": False,
            "cleanup_completed": False,
        },
        "R1 execution receipt",
    )

    runtime_proof = runtime.get("runtime_proof", {})
    if runtime_proof.get("workflow_run_id") is not None or runtime_proof.get("result") is not None:
        fail("runtime proof authority self-attested R1 execution before event delivery")
    if runtime_proof.get("proof_reexecution_allowed") is not False:
        fail("runtime authority allows proof replay")

    next_stage = seal.get("next_stage", {})
    require(
        next_stage,
        {
            "name": "MERGE_R1_WORKFLOW_SEAL_THEN_DELIVER_EVENT_ONCE",
            "seal_pr_must_pass_ci": True,
            "seal_pr_must_merge_before_event": True,
            "fresh_pre_event_live_gate_required": True,
            "preferred_event": "ready_for_review",
            "fallback_event": "opened",
            "may_change_proof_head_after_seal": False,
            "may_execute_more_than_once": False,
            "may_rerun_consumed_r0": False,
            "may_revoke_direct_rpc_execute_now": False,
            "may_promote_launch_gates": False,
        },
        "R1 seal next stage",
    )
    if any(value is not False for value in seal.get("launch_authority", {}).values()):
        fail("R1 workflow seal gained launch authority")

    print("STAGE32_POST_CUTOVER_LIVE_PROOF_R1_WORKFLOW_SEAL_GUARD=PASS")
    print(f"SEALED_PROOF_PR={PROOF_PR}")
    print(f"SEALED_PROOF_HEAD={PROOF_HEAD}")
    print(f"CANDIDATE_CI_RUN={CANDIDATE_RUN}")
    print("CANDIDATE_CI=success")
    print(f"OPEN_TRIGGER_HEAD={TRIGGER_HEAD}")
    print(f"CONSUMED_R0_RUN={OLD_RUN}")
    print("R0_REEXECUTION_ALLOWED=false")
    print("R1_LIVE_PROOF_EXECUTED=false")
    print("FRESH_PRE_EVENT_LIVE_GATE_REQUIRED=true")
    print("PRODUCTION_ACTIVE_TRANSPORT=edgeGateway")
    print("PRODUCTION_SINGLETON=StudentAccessTransport.instance")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
