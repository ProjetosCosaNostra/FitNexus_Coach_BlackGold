from __future__ import annotations

import importlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
SEAL = BACKEND / "stage32_post_cutover_live_proof_workflow_seal_authority.json"
PROOF_AUTHORITY = BACKEND / "student_access_stage32_post_cutover_runtime_proof_authority.json"
WORKFLOW = ROOT / ".github" / "workflows" / "stage32_post_cutover_edge_runtime_live_proof.yml"

PREVENTION_CLASS = "BGF-STAGE32-POST-CUTOVER-PROOF-REEXECUTION-233"
PROOF_STATE = "POST_CUTOVER_EDGE_RUNTIME_PROOF_FIXTURE_REMOTE_LIVE_PROOF_PENDING_EDGE_MODE"
PROOF_PR = 71
PROOF_BRANCH = "blackgold/stage32-post-cutover-live-proof"
PROOF_HEAD = "370cfe65d3df5188c3f840d84b5a8748f1357cf2"
TRIGGER_BRANCH = "blackgold/stage32-live-proof-open-trigger"
TRIGGER_HEAD = "84a51d97f3b7a7c53965567e21760d5d59c85f5a"


def fail(message: str) -> None:
    raise SystemExit("STAGE32_POST_CUTOVER_LIVE_PROOF_WORKFLOW_SEAL_GUARD=FAIL\n" + message)


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
    # The current Stage 32 lifecycle must be valid before workflow metadata can
    # grant event-delivery authority. The seal never substitutes for lifecycle authority.
    lifecycle = importlib.import_module(
        "verify_student_access_stage32_post_cutover_runtime_preparation"
    )
    lifecycle.main()

    seal = data(SEAL)
    proof = data(PROOF_AUTHORITY)
    workflow = text(WORKFLOW)

    require(
        seal,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "stage": "STAGE32_POST_CUTOVER_LIVE_PROOF_WORKFLOW_SEAL",
            "prevention_class": PREVENTION_CLASS,
            "proof_authority_file": "04_backend_supabase/student_access_stage32_post_cutover_runtime_proof_authority.json",
            "required_proof_authority_state": PROOF_STATE,
        },
        "Stage 32 workflow seal",
    )
    if proof.get("current_state") != PROOF_STATE:
        fail("proof authority left the sealed pre-execution state")

    require(
        seal.get("proof_pr", {}),
        {
            "number": PROOF_PR,
            "head_branch": PROOF_BRANCH,
            "head_sha": PROOF_HEAD,
            "base_branch": "main",
            "draft_when_sealed": True,
            "merge_allowed": False,
        },
        "sealed proof PR",
    )
    require(
        seal.get("open_trigger", {}),
        {
            "branch": TRIGGER_BRANCH,
            "head_sha": TRIGGER_HEAD,
            "merge_allowed": False,
        },
        "sealed fallback trigger",
    )

    contract = seal.get("workflow_contract", {})
    if contract.get("event") != "pull_request":
        fail("workflow event must remain pull_request")
    if contract.get("event_types") != ["ready_for_review", "opened"]:
        fail("workflow event type set drifted")
    for key in (
        "ready_path_requires_exact_pr_number",
        "ready_path_requires_exact_head_branch",
        "ready_path_requires_exact_head_sha",
        "opened_fallback_requires_exact_head_branch",
        "opened_fallback_requires_exact_head_sha",
        "job_requires_run_attempt_one",
        "checkout_ref_is_exact_proof_head_sha",
        "candidate_guard_runs_before_flutter_setup",
        "live_test_requires_explicit_enable_environment",
        "synthetic_token_derived_from_public_seed_at_runtime",
        "production_singleton_required",
        "verification_factory_forbidden",
    ):
        if contract.get(key) is not True:
            fail(f"workflow seal invariant missing: {key}")
    for key in (
        "workflow_dispatch_allowed",
        "synchronize_allowed",
        "reopened_allowed",
        "schedule_allowed",
        "service_role_secret_used",
        "synthetic_token_printed",
    ):
        if contract.get(key) is not False:
            fail(f"workflow seal prohibition drifted: {key}")

    require(
        seal.get("proof_boundary", {}),
        {
            "fixture_remote_version": "20260821171334",
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
        "sealed proof boundary",
    )

    receipt = seal.get("execution_receipt", {})
    require(
        receipt,
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
        "pre-execution receipt",
    )

    proof_runtime = proof.get("runtime_proof", {})
    if proof_runtime.get("workflow_run_id") is not None or proof_runtime.get("result") is not None:
        fail(f"{PREVENTION_CLASS} proof already has an execution receipt")
    if proof_runtime.get("proof_reexecution_allowed") is not False:
        fail(f"{PREVENTION_CLASS} proof reexecution authority drifted")

    required = (
        "types: [ready_for_review, opened]",
        "github.event.action == 'ready_for_review'",
        f"github.event.pull_request.number == {PROOF_PR}",
        f"github.event.pull_request.head.ref == '{PROOF_BRANCH}'",
        f"github.event.pull_request.head.sha == '{PROOF_HEAD}'",
        "github.event.action == 'opened'",
        f"github.event.pull_request.head.ref == '{TRIGGER_BRANCH}'",
        f"github.event.pull_request.head.sha == '{TRIGGER_HEAD}'",
        ") &&\n      github.run_attempt == 1",
        f"ref: {PROOF_HEAD}",
        "verify_student_access_stage32_live_proof_candidate.py",
        "STAGE32_POST_CUTOVER_LIVE_PROOF_ENABLED=1",
        "fitnexus-stage32-post-cutover-edge-runtime-proof-v1",
        "STAGE32_SYNTHETIC_TOKEN=$TOKEN",
        "flutter test test/student_access_stage32_post_cutover_live_edge_proof_test.dart --reporter expanded",
        "PRODUCTION_SINGLETON=StudentAccessTransport.instance",
        "PRODUCTION_ACTIVE_TRANSPORT=edgeGateway",
        "ROUTES_EXPECTED=5",
        "AUTOMATIC_EDGE_TO_DIRECT_FALLBACK=false",
        "DIRECT_RPC_GRANTS_CHANGED=false",
        "DIRECT_RPC_PRIVILEGE_REVOCATION=false",
        "REAL_CUSTOMER_DATA_USED=false",
        "RAW_SYNTHETIC_TOKEN_PRINTED=false",
        "PROOF_REEXECUTION_ALLOWED=false",
        "CLEANUP_REQUIRED=true",
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
            fail(f"{PREVENTION_CLASS} workflow became replayable or privileged: {forbidden}")

    next_stage = seal.get("next_stage", {})
    require(
        next_stage,
        {
            "name": "DELIVER_STAGE32_POST_CUTOVER_LIVE_PROOF_EVENT_ONCE",
            "allowed_now_after_ci_and_merge": True,
            "preferred_event": "ready_for_review",
            "fallback_event": "opened",
            "may_change_proof_head_after_seal": False,
            "may_execute_more_than_once": False,
            "may_revoke_direct_rpc_execute_now": False,
        },
        "workflow seal next stage",
    )
    if any(value is not False for value in seal.get("launch_authority", {}).values()):
        fail("workflow seal gained launch authority")

    print("STAGE32_POST_CUTOVER_LIVE_PROOF_WORKFLOW_SEAL_GUARD=PASS")
    print(f"PREVENTION_CLASS={PREVENTION_CLASS}")
    print(f"SEALED_PROOF_PR={PROOF_PR}")
    print(f"SEALED_PROOF_HEAD={PROOF_HEAD}")
    print(f"FALLBACK_HEAD={TRIGGER_HEAD}")
    print("LIVE_PROOF_EXECUTED=false")
    print("PRODUCTION_ACTIVE_TRANSPORT=edgeGateway")
    print("PRODUCTION_SINGLETON=StudentAccessTransport.instance")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")
    print("PROOF_REEXECUTION_ALLOWED=false")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
