from __future__ import annotations

import importlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
SEAL = BACKEND / "stage32_post_cutover_rollback_live_proof_workflow_seal_authority.json"
ROLLBACK = BACKEND / "stage32_post_cutover_rollback_proof_authority.json"
WORKFLOW = ROOT / ".github" / "workflows" / "stage32_post_cutover_rollback_live_proof.yml"

FAILURE_CLASS = "BGF-STAGE32-ROLLBACK-PROOF-REEXECUTION-242"
PROOF_HEAD = "cb734b3ef51fe607d7d4de2709d517625a9c8101"
TRIGGER_HEAD = "777bb51f698c0648cf641bba1070f5f71f001e87"


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
    # First prove the real current lifecycle frontier (successful proof, cleanup repo-only).
    current = importlib.import_module("verify_stage32_post_cutover_rollback_proof_preparation")
    current.main()

    seal = load(SEAL)
    rollback = load(ROLLBACK)
    workflow = text(WORKFLOW)

    # The seal authority is intentionally retained as the immutable PRE-EVENT snapshot.
    require(seal, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE32_POST_CUTOVER_ROLLBACK_LIVE_PROOF_WORKFLOW_SEAL",
        "prevention_class": FAILURE_CLASS,
        "required_rollback_state": "POST_CUTOVER_ROLLBACK_FIXTURE_REMOTE_LIVE_PROOF_PENDING_EDGE_MODE",
    }, "historical seal authority")
    require(seal.get("proof_pr", {}), {
        "number": 84,
        "head_branch": "blackgold/stage32-post-cutover-rollback-live-proof-candidate",
        "head_sha": PROOF_HEAD,
        "base_branch": "main",
        "draft_when_sealed": True,
        "merge_allowed": False,
        "candidate_ci_run_id": 32539035186,
        "candidate_ci_job_id": 96945178233,
        "candidate_ci_conclusion": "success",
        "candidate_guard_passed": True,
    }, "proof PR seal")
    require(seal.get("open_trigger", {}), {
        "branch": "blackgold/stage32-post-cutover-rollback-live-proof-open-trigger",
        "head_sha": TRIGGER_HEAD,
        "merge_allowed": False,
        "open_before_seal_merge_allowed": False,
    }, "fallback trigger seal")

    contract = seal.get("workflow_contract", {})
    require(contract, {
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
    }, "workflow contract")

    for fragment in (
        "types: [ready_for_review, opened]",
        "github.event.pull_request.number == 84",
        "github.event.pull_request.head.ref == 'blackgold/stage32-post-cutover-rollback-live-proof-candidate'",
        f"github.event.pull_request.head.sha == '{PROOF_HEAD}'",
        "github.event.pull_request.head.ref == 'blackgold/stage32-post-cutover-rollback-live-proof-open-trigger'",
        f"github.event.pull_request.head.sha == '{TRIGGER_HEAD}'",
        "github.run_attempt == 1",
        f"ref: {PROOF_HEAD}",
        "verify_stage32_post_cutover_rollback_live_proof_candidate.py",
        "STAGE32_POST_CUTOVER_ROLLBACK_PROOF_ENABLED=1",
        "student_access_stage32_post_cutover_live_rollback_proof_test.dart",
        "PROOF_REEXECUTION_ALLOWED=false",
        "CLEANUP_REQUIRED=true",
        "LAUNCH_GATE_PROMOTION=DENIED",
    ):
        if fragment not in workflow:
            fail(f"sealed workflow drift: {fragment}")
    for forbidden in ("workflow_dispatch:", "schedule:", "synchronize", "reopened"):
        if forbidden in workflow:
            fail(f"sealed workflow became replayable through {forbidden}")

    # Historical seal snapshot must still show that no execution had happened when sealed.
    require(seal.get("execution_receipt", {}), {
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
    }, "historical pre-event execution snapshot")

    # Actual execution truth lives in the current rollback authority after consumption.
    require(rollback.get("runtime_proof", {}), {
        "workflow_run_id": 32540031081,
        "workflow_job_id": 96948118831,
        "run_attempt": 1,
        "result": "SUCCESS",
        "proof_head_sha": PROOF_HEAD,
        "delivery_path": "fallback_pull_request_opened",
        "authorized_rollback_object_verified": True,
        "direct_rpc_branch_verified": True,
        "all_five_routes_verified": True,
        "production_edge_mode_preserved": True,
        "automatic_fallback_remained_false": True,
        "direct_rpc_grants_changed": False,
        "direct_rpc_privilege_revocation": False,
        "real_customer_data_used": False,
        "proof_reexecution_allowed": False,
        "cleanup_completed": False,
        "launch_gate_promotion": False,
    }, "consumed proof execution")

    print("STAGE32_POST_CUTOVER_ROLLBACK_LIVE_PROOF_WORKFLOW_SEAL_GUARD=PASS")
    print(f"SEALED_PROOF_HEAD={PROOF_HEAD}")
    print(f"OPEN_TRIGGER_HEAD={TRIGGER_HEAD}")
    print("ROLLBACK_LIVE_PROOF_RUN=32540031081")
    print("ROLLBACK_LIVE_PROOF_JOB=96948118831")
    print("ROLLBACK_LIVE_PROOF=SUCCESS")
    print("PROOF_REEXECUTION_ALLOWED=false")
    print("CLEANUP_LEDGER_STATE=repo_only")
    print("PRODUCTION_ACTIVE_TRANSPORT=edgeGateway")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
