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
PROOF_PR = 61
PROOF_BRANCH = "blackgold/stage31-client-edge-live-proof"
PROOF_HEAD = "b8be62be0ba36c61b9557bed03e72dc05b0a43f0"


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
        },
        "workflow seal authority",
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
            "candidate_quality_gate_run_id": 32478844026,
            "candidate_quality_gate_job_id": 96760703404,
            "candidate_quality_gate_result": "SUCCESS",
        },
        "sealed proof PR",
    )
    contract = seal.get("workflow_contract", {})
    for key in (
        "job_requires_exact_pr_number",
        "job_requires_exact_head_branch",
        "job_requires_exact_head_sha",
        "job_requires_run_attempt_one",
        "checkout_ref_is_exact_head_sha",
        "live_test_requires_explicit_enable_environment",
        "synthetic_token_derived_from_public_seed_at_runtime",
    ):
        if contract.get(key) is not True:
            fail(f"workflow seal invariant missing: {key}")
    for key in (
        "workflow_dispatch_allowed",
        "synchronize_allowed",
        "schedule_allowed",
        "synthetic_token_printed",
        "service_role_secret_used",
    ):
        if contract.get(key) is not False:
            fail(f"workflow seal prohibition drifted: {key}")

    boundary = seal.get("proof_boundary", {})
    require(
        boundary,
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
    receipt = seal.get("execution_receipt", {})
    require(
        receipt,
        {
            "workflow_run_id": None,
            "job_id": None,
            "result": None,
            "executed": False,
        },
        "pre-execution seal receipt",
    )

    if stage31.get("current_state") != "CLIENT_EDGE_RUNTIME_PROOF_FIXTURE_REMOTE_LIVE_PROOF_PENDING_DIRECT_MODE":
        fail("Stage 31 authority advanced before sealed live proof execution")
    fixture = stage31.get("fixture", {})
    if fixture.get("remote_applied") is not True or fixture.get("remote_version") != "20260821113205":
        fail("Stage 31 remote fixture receipt disappeared before workflow seal")
    runtime = stage31.get("runtime_proof", {})
    if runtime.get("workflow_run_id") is not None or runtime.get("result") is not None:
        fail("Stage 31 live proof already has a runtime receipt")
    if runtime.get("all_five_routes_verified") is not False:
        fail("Stage 31 live proof self-attested before workflow seal")

    transport = cutover.get("transport_contract", {})
    require(
        transport,
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
        "types: [ready_for_review]",
        f"github.event.pull_request.number == {PROOF_PR}",
        f"github.event.pull_request.head.ref == '{PROOF_BRANCH}'",
        f"github.event.pull_request.head.sha == '{PROOF_HEAD}'",
        "github.run_attempt == 1",
        f"ref: {PROOF_HEAD}",
        "verify_student_access_stage31_live_proof_candidate.py",
        "STAGE31_LIVE_PROOF_ENABLED=1",
        "fitnexus-stage31-client-edge-runtime-proof-v1",
        "STAGE31_SYNTHETIC_TOKEN=$TOKEN",
        "flutter test test/student_access_stage31_live_edge_proof_test.dart --reporter expanded",
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
        "types: [opened]",
        "schedule:",
        "SUPABASE_SERVICE_ROLE_KEY",
        "SUPABASE_SECRET_KEY",
    ):
        if forbidden in workflow:
            fail(f"sealed workflow became replayable or privileged: {forbidden}")

    print("STAGE31_LIVE_PROOF_WORKFLOW_SEAL_GUARD=PASS")
    print(f"PREVENTION_CLASS={PREVENTION_CLASS}")
    print(f"SEALED_PR={PROOF_PR}")
    print(f"SEALED_BRANCH={PROOF_BRANCH}")
    print(f"SEALED_HEAD={PROOF_HEAD}")
    print("TRIGGER=ready_for_review")
    print("RUN_ATTEMPT=1_ONLY")
    print("PRODUCTION_ACTIVE_TRANSPORT=directRpc")
    print("EDGE_SELECTION=false")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")
    print("LIVE_PROOF_EXECUTED=false")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
