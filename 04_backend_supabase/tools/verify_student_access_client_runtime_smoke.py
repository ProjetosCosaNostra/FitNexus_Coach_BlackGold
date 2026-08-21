from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "student_access_client_runtime_smoke_authority.json"
CUTOVER = BACKEND / "student_access_client_cutover_authority.json"
LEDGER = BACKEND / "migration_ledger_authority.json"
MIGRATION = BACKEND / "migrations" / "20260821063000_stage30_edge_runtime_smoke_fixture.sql"

FAILURE_CLASS = "BGF-STAGE30-RUNTIME-SMOKE-FIXTURE-RESIDUE-203"
REEXECUTION_CLASS = "BGF-STAGE30-RUNTIME-SMOKE-PROOF-REEXECUTION-204"
DATA_LEAK_CLASS = "BGF-STAGE30-RUNTIME-SMOKE-RESPONSE-DATA-LEAK-205"
COMMAND_FLOW_CLASS = "BGF-STAGE30-RUNTIME-SMOKE-COMMAND-FLOW-206"
MIGRATION_NAME = "stage30_edge_runtime_smoke_fixture"
REMOTE_VERSION = "20260821075532"
SEED = "fitnexus-stage30-edge-runtime-smoke-fixture-v1"
STATE_REPO = "EDGE_RUNTIME_SMOKE_FIXTURE_REPO_ONLY"
STATE_REMOTE = "EDGE_RUNTIME_SMOKE_FIXTURE_REMOTE_LIVE_PROOF_PENDING"
ALLOWED_STATES = {STATE_REPO, STATE_REMOTE}
BASELINES = {
    STATE_REPO: "59385ef6a7b4d8ad90703b1cbb52c0755f1f8948",
    STATE_REMOTE: "ff29a59626f7a4ab5e198cfef2c27b5cd1dfde1b",
}
EXPECTED_IDS = {
    "user_id": "33e39af7-f470-510e-8a9c-fc70b16ba26e",
    "organization_id": "a0749405-6367-52d5-ad8b-5115b8d3a905",
    "student_id": "81d3be6f-824e-59bc-8fa0-27acf046d6d3",
    "plan_id": "82b92191-a8e3-5bb2-8f5d-fec9a59a57bb",
    "exercise_id": "fe116050-9061-5627-8e3a-dedd863d6447",
    "link_id": "53dfab53-5ff8-573a-ab2a-faaea24107db",
}
ROUTES = [
    "get_workout",
    "start_workout",
    "set_completion",
    "get_feedback_context",
    "submit_feedback",
]


def fail(message: str) -> None:
    raise SystemExit("STUDENT_ACCESS_CLIENT_RUNTIME_SMOKE_GUARD=FAIL\n" + message)


def read(path: Path) -> str:
    if not path.is_file():
        fail(f"missing source: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def load(path: Path) -> dict:
    try:
        value = json.loads(read(path))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path.relative_to(ROOT)}: {exc}")
    if not isinstance(value, dict):
        fail(f"expected JSON object: {path.relative_to(ROOT)}")
    return value


def main() -> None:
    authority = load(AUTHORITY)
    cutover = load(CUTOVER)
    ledger = load(LEDGER)
    migration = read(MIGRATION)
    lower = migration.lower()

    if authority.get("schema_version") != 1:
        fail("runtime smoke authority schema_version must be 1")
    if authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("wrong Supabase project")
    if authority.get("failure_class") != FAILURE_CLASS:
        fail("fixture failure class drifted")
    if authority.get("proof_reexecution_failure_class") != REEXECUTION_CLASS:
        fail("reexecution failure class drifted")
    if authority.get("response_data_leak_failure_class") != DATA_LEAK_CLASS:
        fail("response-data-leak failure class drifted")
    if authority.get("command_flow_failure_class") != COMMAND_FLOW_CLASS:
        fail("command-flow failure class drifted")

    state = authority.get("current_state")
    if state not in ALLOWED_STATES:
        fail(f"unsupported Stage 30 smoke lifecycle state: {state}")
    if authority.get("baseline_main_sha") != BASELINES[state]:
        fail("smoke lifecycle baseline main SHA drifted")

    cutover_ref = authority.get("client_cutover_authority", {})
    if cutover.get("current_state") != cutover_ref.get("required_state"):
        fail("Stage 30 cutover prerequisite state drifted")
    if cutover_ref.get("required_state") != "CLIENT_EDGE_ERROR_CONTRACT_ROLLBACK_HARNESS_READY_DIRECT_MODE":
        fail("unexpected cutover prerequisite")
    if cutover_ref.get("active_transport") != "directRpc":
        fail("runtime smoke must not select Edge in Flutter")
    for key in ("edge_gateway_selected", "rollback_verified", "direct_rpc_execute_revoked"):
        if cutover_ref.get(key) is not False:
            fail(f"runtime smoke prerequisite self-promoted: {key}")

    fixture = authority.get("fixture", {})
    expected_fixture = {
        "repository_file": "04_backend_supabase/migrations/20260821063000_stage30_edge_runtime_smoke_fixture.sql",
        "migration_name": MIGRATION_NAME,
        "requires_empty_customer_domain": True,
        "synthetic_only": True,
        "token_seed": SEED,
        "raw_token_is_public_synthetic_test_material": True,
        "database_stores_token_hash_only": True,
        "repository_contains_bearer_literal": False,
        "expiry_hours": 2,
        "cleanup_required_after_proof": True,
    }
    for key, expected in expected_fixture.items():
        if fixture.get(key) != expected:
            fail(f"fixture authority drift for {key}")
    for key, expected in EXPECTED_IDS.items():
        if fixture.get(key) != expected:
            fail(f"fixture identifier drift for {key}")

    if state == STATE_REPO:
        if fixture.get("migration_ledger_state") != "repo_only":
            fail("repository-only fixture ledger state drifted")
        if fixture.get("remote_applied") is not False or fixture.get("remote_version") is not None:
            fail("repository-only fixture self-promoted")
    else:
        if fixture.get("migration_ledger_state") != "remote_reconciled":
            fail("remote fixture is not reconciled")
        if fixture.get("remote_applied") is not True or fixture.get("remote_version") != REMOTE_VERSION:
            fail("remote fixture receipt missing")

    if authority.get("expected_route_sequence") != ROUTES:
        fail("five-route smoke sequence drifted")
    expected_inputs = authority.get("expected_command_inputs", {})
    if expected_inputs != {
        "set_completion_completed": True,
        "feedback_perceived_exertion": 5,
        "feedback_pain_score": 0,
        "feedback_energy_score": 4,
        "feedback_pain_location": None,
        "feedback_note": None,
        "expected_feedback_risk_signal": "low",
    }:
        fail("safe synthetic command inputs drifted")

    runtime = authority.get("runtime_proof", {})
    if runtime.get("edge_runtime_version") != 3:
        fail("runtime smoke not anchored to Edge v3")
    if runtime.get("fixture_deployed") is not (state == STATE_REMOTE):
        fail("fixture deployment authority drifted")
    for key in (
        "get_workout_verified",
        "start_workout_verified",
        "set_completion_verified",
        "get_feedback_context_verified",
        "submit_feedback_verified",
        "all_five_routes_verified",
        "completed_session_verified",
        "feedback_submitted_verified",
        "cleanup_completed",
    ):
        if runtime.get(key) is not False:
            fail(f"runtime proof self-attested before live smoke: {key}")
    if runtime.get("proof_workflow_run_id") is not None or runtime.get("proof_result") is not None:
        fail("runtime proof receipt appeared before execution")
    if runtime.get("proof_reexecution_allowed") is not False:
        fail("live smoke proof must become sealed after success")
    for key in ("raw_token_returned", "raw_network_origin_returned", "real_student_data_used", "real_student_data_mutated"):
        if runtime.get(key) is not False:
            fail(f"privacy/synthetic proof invariant drift: {key}")

    repo_only = {
        row.get("name")
        for row in ledger.get("declared_divergences", [])
        if row.get("direction") == "repo_only"
    }
    remote = {row.get("name"): row.get("version") for row in ledger.get("remote_migrations", [])}
    if state == STATE_REPO:
        if repo_only != {MIGRATION_NAME}:
            fail(f"expected only Stage 30 fixture repo_only, observed {sorted(repo_only)}")
        if MIGRATION_NAME in remote:
            fail("fixture migration self-attested as remotely applied")
    else:
        if repo_only:
            fail(f"remote-pending smoke has unexpected repo_only divergences: {sorted(repo_only)}")
        if remote.get(MIGRATION_NAME) != REMOTE_VERSION:
            fail("remote-pending smoke ledger receipt missing")

    required_sql = (
        FAILURE_CLASS,
        "STAGE30_EDGE_RUNTIME_SMOKE_FIXTURE_REQUIRES_EMPTY_CUSTOMER_DOMAIN",
        "STAGE30_SYNTHETIC_FIXTURE_POSTCONDITION_FAILED",
        SEED,
        "extensions.digest(v_token, 'sha256')",
        "now() + interval '2 hours'",
        "Stage30 Synthetic Student",
        "Stage30 Synthetic Plan",
        "Stage30 Synthetic Exercise",
    )
    missing = [fragment for fragment in required_sql if fragment not in migration]
    if missing:
        fail(f"fixture migration incomplete: {missing}")
    for identifier in EXPECTED_IDS.values():
        if identifier not in migration:
            fail(f"fixture migration missing expected identifier: {identifier}")

    bearer_literals = re.findall(r"(?<![0-9a-fA-F])[0-9a-fA-F]{64}(?![0-9a-fA-F])", migration)
    if bearer_literals:
        fail(f"{DATA_LEAK_CLASS} bearer-looking 64-hex literal committed in fixture migration")
    if "raw_network_origin" in lower or "cf-connecting-ip" in lower or "x-forwarded-for" in lower:
        fail(f"{DATA_LEAK_CLASS} network-origin material appeared in fixture migration")

    promotion = authority.get("promotion_rules", {})
    if promotion.get("may_apply_fixture_after_ci_and_merge") is not True:
        fail("fixture application authority drifted")
    for key in (
        "may_execute_live_smoke_before_fixture_remote_apply",
        "may_select_edge_gateway_after_fixture_apply_only",
        "may_revoke_direct_rpc_execute_now",
        "launch_gate_authority",
    ):
        if promotion.get(key) is not False:
            fail(f"premature promotion authority: {key}")
    for key in (
        "live_smoke_required_before_edge_selection",
        "cleanup_required_before_edge_selection",
        "runtime_rollback_proof_required_before_edge_selection",
    ):
        if promotion.get(key) is not True:
            fail(f"missing promotion interlock: {key}")

    next_stage = authority.get("next_stage", {})
    if state == STATE_REPO:
        if next_stage.get("name") != "APPLY_STAGE30_EDGE_RUNTIME_SMOKE_FIXTURE":
            fail("repository-only next stage drifted")
        if next_stage.get("allowed_now") is not True or next_stage.get("requires_ci_and_merge_first") is not True:
            fail("fixture application interlock drifted")
    else:
        if next_stage.get("name") != "EXECUTE_STAGE30_FIVE_ROUTE_EDGE_RUNTIME_SMOKE":
            fail("remote-pending next stage drifted")
        if next_stage.get("allowed_now") is not True or next_stage.get("requires_ci_and_merge_first") is not False:
            fail("live smoke execution interlock drifted")
        if next_stage.get("requires_one_shot_proof_workflow") is not True:
            fail("live smoke one-shot workflow interlock missing")

    print("STUDENT_ACCESS_CLIENT_RUNTIME_SMOKE_GUARD=PASS")
    print(f"CURRENT_STATE={state}")
    print("EDGE_RUNTIME_VERSION=3")
    print("SYNTHETIC_CUSTOMER_FIXTURE=" + ("REMOTE_VERIFIED" if state == STATE_REMOTE else "REPO_ONLY"))
    print("EXPECTED_EDGE_ROUTES=5")
    print("FLUTTER_ACTIVE_TRANSPORT=directRpc")
    print("LIVE_SMOKE_EXECUTED=false")
    print("FIXTURE_CLEANUP_REQUIRED=true")
    print("EDGE_SELECTION=DENIED")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
