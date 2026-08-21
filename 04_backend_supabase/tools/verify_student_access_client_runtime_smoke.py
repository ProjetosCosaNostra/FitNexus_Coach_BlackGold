from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "student_access_client_runtime_smoke_authority.json"
CUTOVER = BACKEND / "student_access_client_cutover_authority.json"
LEDGER = BACKEND / "migration_ledger_authority.json"
FIXTURE_SQL = BACKEND / "migrations" / "20260821063000_stage30_edge_runtime_smoke_fixture.sql"
CLEANUP_SQL = BACKEND / "migrations" / "20260821081005_stage30_edge_runtime_smoke_cleanup.sql"
LIVE = BACKEND / "tools" / "verify_student_access_stage30_edge_runtime_live.py"

FAILURE_CLASS = "BGF-STAGE30-RUNTIME-SMOKE-FIXTURE-RESIDUE-203"
REEXECUTION_CLASS = "BGF-STAGE30-RUNTIME-SMOKE-PROOF-REEXECUTION-204"
DATA_LEAK_CLASS = "BGF-STAGE30-RUNTIME-SMOKE-RESPONSE-DATA-LEAK-205"
COMMAND_FLOW_CLASS = "BGF-STAGE30-RUNTIME-SMOKE-COMMAND-FLOW-206"
CLEANUP_CLASS = "BGF-STAGE30-RUNTIME-SMOKE-CLEANUP-SCOPE-207"
FIXTURE_NAME = "stage30_edge_runtime_smoke_fixture"
CLEANUP_NAME = "stage30_edge_runtime_smoke_cleanup"
FIXTURE_REMOTE_VERSION = "20260821075532"
SEALED_RUN = 32461357789
SEED = "fitnexus-stage30-edge-runtime-smoke-fixture-v1"

STATE_REPO = "EDGE_RUNTIME_SMOKE_FIXTURE_REPO_ONLY"
STATE_REMOTE = "EDGE_RUNTIME_SMOKE_FIXTURE_REMOTE_LIVE_PROOF_PENDING"
STATE_PROVEN = "EDGE_RUNTIME_SMOKE_LIVE_VERIFIED_CLEANUP_PENDING"
STATE_CLEANUP_REPO = "EDGE_RUNTIME_SMOKE_LIVE_VERIFIED_CLEANUP_REPO_ONLY"
ALLOWED_STATES = {STATE_REPO, STATE_REMOTE, STATE_PROVEN, STATE_CLEANUP_REPO}
BASELINES = {
    STATE_REPO: "59385ef6a7b4d8ad90703b1cbb52c0755f1f8948",
    STATE_REMOTE: "ff29a59626f7a4ab5e198cfef2c27b5cd1dfde1b",
    STATE_PROVEN: "ff29a59626f7a4ab5e198cfef2c27b5cd1dfde1b",
    STATE_CLEANUP_REPO: "aba1937b426c1bb681e4e39065fbfb840653c41e",
}
ROUTES = ["get_workout", "start_workout", "set_completion", "get_feedback_context", "submit_feedback"]
EXPECTED_IDS = {
    "user_id": "33e39af7-f470-510e-8a9c-fc70b16ba26e",
    "organization_id": "a0749405-6367-52d5-ad8b-5115b8d3a905",
    "student_id": "81d3be6f-824e-59bc-8fa0-27acf046d6d3",
    "plan_id": "82b92191-a8e3-5bb2-8f5d-fec9a59a57bb",
    "exercise_id": "fe116050-9061-5627-8e3a-dedd863d6447",
    "link_id": "53dfab53-5ff8-573a-ab2a-faaea24107db",
}


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
    fixture_sql = read(FIXTURE_SQL)
    live = read(LIVE)

    if authority.get("schema_version") != 1 or authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("runtime smoke authority identity drifted")
    for key, expected in {
        "failure_class": FAILURE_CLASS,
        "proof_reexecution_failure_class": REEXECUTION_CLASS,
        "response_data_leak_failure_class": DATA_LEAK_CLASS,
        "command_flow_failure_class": COMMAND_FLOW_CLASS,
    }.items():
        if authority.get(key) != expected:
            fail(f"runtime smoke failure-class drift: {key}")

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
    for key, expected in {
        "repository_file": "04_backend_supabase/migrations/20260821063000_stage30_edge_runtime_smoke_fixture.sql",
        "migration_name": FIXTURE_NAME,
        "requires_empty_customer_domain": True,
        "synthetic_only": True,
        "token_seed": SEED,
        "raw_token_is_public_synthetic_test_material": True,
        "database_stores_token_hash_only": True,
        "repository_contains_bearer_literal": False,
        "expiry_hours": 2,
        "cleanup_required_after_proof": True,
    }.items():
        if fixture.get(key) != expected:
            fail(f"fixture authority drift: {key}")
    for key, expected in EXPECTED_IDS.items():
        if fixture.get(key) != expected:
            fail(f"fixture identifier drift: {key}")

    remote_fixture = state != STATE_REPO
    if state == STATE_REPO:
        if fixture.get("migration_ledger_state") != "repo_only" or fixture.get("remote_applied") is not False or fixture.get("remote_version") is not None:
            fail("repository-only fixture self-promoted")
    else:
        if fixture.get("migration_ledger_state") != "remote_reconciled" or fixture.get("remote_applied") is not True or fixture.get("remote_version") != FIXTURE_REMOTE_VERSION:
            fail("remote fixture receipt missing")

    if authority.get("expected_route_sequence") != ROUTES:
        fail("five-route smoke sequence drifted")
    if authority.get("expected_command_inputs") != {
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
    proof_complete = state in {STATE_PROVEN, STATE_CLEANUP_REPO}
    if runtime.get("edge_runtime_version") != 3 or runtime.get("fixture_deployed") is not remote_fixture:
        fail("runtime fixture/version authority drifted")
    for key in (
        "get_workout_verified", "start_workout_verified", "set_completion_verified",
        "get_feedback_context_verified", "submit_feedback_verified", "all_five_routes_verified",
        "completed_session_verified", "feedback_submitted_verified",
    ):
        if runtime.get(key) is not proof_complete:
            fail(f"runtime proof lifecycle drift: {key}")
    if runtime.get("cleanup_completed") is not False:
        fail("cleanup self-attested before remote cleanup")
    for key in ("raw_token_returned", "raw_network_origin_returned", "real_student_data_used", "real_student_data_mutated", "proof_reexecution_allowed"):
        if runtime.get(key) is not False:
            fail(f"privacy/reexecution invariant drift: {key}")

    if proof_complete:
        if runtime.get("proof_workflow_run_id") != SEALED_RUN or runtime.get("proof_result") != "PASS":
            fail("sealed smoke runtime receipt drifted")
        receipt = authority.get("live_proof_receipt", {})
        for key, expected in {
            "workflow_run_id": SEALED_RUN,
            "result": "PASS",
            "live_smoke_mode": "EXECUTED_ONCE",
            "gateway_health": "PASS",
            "routes_verified": 5,
            "get_workout": "PASS",
            "start_workout": "PASS",
            "set_completion": "PASS",
            "get_feedback_context": "PASS",
            "submit_feedback": "PASS",
            "completed_session_verified": True,
            "feedback_submitted_verified": True,
            "feedback_risk_signal": "low",
            "raw_synthetic_token_returned": False,
            "raw_network_origin_returned": False,
            "real_student_data_used": False,
            "real_student_data_mutated": False,
            "proof_reexecution_allowed": False,
        }.items():
            if receipt.get(key) != expected:
                fail(f"sealed live smoke receipt drift: {key}")
        db = authority.get("database_proof_receipt", {})
        for key, expected in {
            "sessions_total": 1, "session_completed": 1, "exercise_logs_total": 1,
            "exercise_log_completed": 1, "feedback_total": 1, "feedback_expected": 1,
            "link_last_used": 1, "student_status": "Treino concluído", "student_adherence": 100,
            "command_receipts_total": 3, "start_receipt_exact": 1,
            "completion_receipt_exact": 1, "feedback_receipt_exact": 1,
        }.items():
            if db.get(key) != expected:
                fail(f"database proof receipt drift: {key}")
        expected_rate = {route: 1 for route in ROUTES}
        if db.get("link_rate_bucket_request_counts") != expected_rate:
            fail("link rate-bucket proof drifted")
        network = db.get("network_rate_bucket_proof", {})
        if network.get("raw_origin_hash_read") is not False:
            fail(f"{DATA_LEAK_CLASS} network proof read pseudonymous digest")
        if {k: network.get(k) for k in ROUTES} != expected_rate:
            fail("network rate-bucket proof drifted")
        if db.get("allowed_security_events") != {"start_workout": 1, "set_completion": 1, "submit_feedback": 1}:
            fail("security-event proof drifted")
        for fragment in (REEXECUTION_CLASS, "SEALED_SKIP_REEXECUTION", f"SEALED_WORKFLOW_RUN = {SEALED_RUN}", "NETWORK_CALL_EXECUTED=false"):
            if fragment not in live:
                fail(f"{REEXECUTION_CLASS} sealed live verifier drift: {fragment}")
    else:
        if runtime.get("proof_workflow_run_id") is not None or runtime.get("proof_result") is not None:
            fail("runtime proof receipt appeared before proof completion")

    remote = {row.get("name"): row.get("version") for row in ledger.get("remote_migrations", [])}
    repo_only = {row.get("name") for row in ledger.get("declared_divergences", []) if row.get("direction") == "repo_only"}
    if state == STATE_REPO:
        if repo_only != {FIXTURE_NAME} or FIXTURE_NAME in remote:
            fail("fixture repo-only ledger mismatch")
    else:
        if remote.get(FIXTURE_NAME) != FIXTURE_REMOTE_VERSION:
            fail("remote fixture ledger receipt missing")
        expected_repo_only = {CLEANUP_NAME} if state == STATE_CLEANUP_REPO else set()
        if repo_only != expected_repo_only:
            fail(f"unexpected repo-only set for {state}: {sorted(repo_only)}")

    for fragment in (
        FAILURE_CLASS, "STAGE30_EDGE_RUNTIME_SMOKE_FIXTURE_REQUIRES_EMPTY_CUSTOMER_DOMAIN",
        "STAGE30_SYNTHETIC_FIXTURE_POSTCONDITION_FAILED", SEED,
        "extensions.digest(v_token, 'sha256')", "now() + interval '2 hours'",
        "Stage30 Synthetic Student", "Stage30 Synthetic Plan", "Stage30 Synthetic Exercise",
    ):
        if fragment not in fixture_sql:
            fail(f"fixture migration drift: {fragment}")
    if re.findall(r"(?<![0-9a-fA-F])[0-9a-fA-F]{64}(?![0-9a-fA-F])", fixture_sql):
        fail(f"{DATA_LEAK_CLASS} bearer-looking literal committed in fixture migration")

    if state == STATE_CLEANUP_REPO:
        if authority.get("cleanup_scope_failure_class") != CLEANUP_CLASS:
            fail("cleanup failure-class authority missing")
        cleanup = authority.get("cleanup_migration", {})
        for key, expected in {
            "repository_file": "04_backend_supabase/migrations/20260821081005_stage30_edge_runtime_smoke_cleanup.sql",
            "migration_name": CLEANUP_NAME,
            "migration_ledger_state": "repo_only",
            "remote_applied": False,
            "remote_version": None,
            "requires_synthetic_only_customer_domain": True,
            "expected_auth_users_before_cleanup": 1,
            "expected_organizations_before_cleanup": 1,
            "expected_students_before_cleanup": 1,
            "expected_training_plans_before_cleanup": 1,
            "expected_training_exercises_before_cleanup": 1,
            "expected_access_links_before_cleanup": 1,
            "expected_workout_sessions_before_cleanup": 1,
            "expected_workout_logs_before_cleanup": 1,
            "expected_workout_feedback_before_cleanup": 1,
            "expected_growth_events_for_fixture_org": 5,
            "expected_link_rate_bucket_rows": 5,
            "expected_command_receipt_rows": 3,
            "expected_allowed_security_events": 3,
            "expected_network_proof_bucket_rows": 5,
            "organization_deleted_before_auth_user": True,
            "transactional_postcondition_required": True,
        }.items():
            if cleanup.get(key) != expected:
                fail(f"cleanup authority drift: {key}")
        if cleanup.get("network_proof_windows_utc") != ["2026-08-21T08:02:00Z", "2026-08-21T08:03:00Z"]:
            fail("cleanup proof windows drifted")
        if cleanup.get("raw_network_origin_embedded_in_repository") is not False or cleanup.get("network_origin_digest_embedded_in_repository") is not False:
            fail("cleanup source privacy authority drifted")
        cleanup_sql = read(CLEANUP_SQL)
        for fragment in (
            CLEANUP_CLASS, "STAGE30_CLEANUP_CUSTOMER_DOMAIN_NO_LONGER_SYNTHETIC_ONLY",
            "STAGE30_CLEANUP_PROOF_MUTATION_STATE_DRIFT", "STAGE30_CLEANUP_NETWORK_BUCKET_SELECTOR_MISMATCH",
            "STAGE30_CLEANUP_POSTCONDITION_FAILED", "2026-08-21 08:02:00+00", "2026-08-21 08:03:00+00",
            "fadd0c2168b5e958a5e7497e3219c84e", "d3ecb7c48b714739111f99b9be656b85",
            "774b6b75ac6dce7f0467a28c9df68e62", "delete from public.organizations where id = v_org",
            "delete from auth.users where id = v_user",
        ):
            if fragment not in cleanup_sql:
                fail(f"cleanup migration drift: {fragment}")
        lowered = cleanup_sql.lower()
        if "origin_hash" in lowered or "cf-connecting-ip" in lowered or "x-forwarded-for" in lowered:
            fail(f"{DATA_LEAK_CLASS} cleanup source contains network-origin identifier material")

    promotion = authority.get("promotion_rules", {})
    for key in ("may_execute_live_smoke_before_fixture_remote_apply", "may_select_edge_gateway_after_fixture_apply_only", "may_revoke_direct_rpc_execute_now", "launch_gate_authority"):
        if promotion.get(key) is not False:
            fail(f"premature promotion authority: {key}")
    for key in ("live_smoke_required_before_edge_selection", "cleanup_required_before_edge_selection", "runtime_rollback_proof_required_before_edge_selection"):
        if promotion.get(key) is not True:
            fail(f"missing promotion interlock: {key}")

    next_stage = authority.get("next_stage", {})
    expected_next = {
        STATE_REPO: "APPLY_STAGE30_EDGE_RUNTIME_SMOKE_FIXTURE",
        STATE_REMOTE: "EXECUTE_STAGE30_FIVE_ROUTE_EDGE_RUNTIME_SMOKE",
        STATE_PROVEN: "PREPARE_STAGE30_RUNTIME_SMOKE_CLEANUP",
        STATE_CLEANUP_REPO: "APPLY_STAGE30_RUNTIME_SMOKE_CLEANUP",
    }[state]
    if next_stage.get("name") != expected_next or next_stage.get("allowed_now") is not True:
        fail("Stage 30 next-stage authority drifted")
    if state == STATE_CLEANUP_REPO:
        if next_stage.get("requires_ci_and_merge_first") is not True or next_stage.get("requires_exact_merged_sql") is not True:
            fail("cleanup application interlock missing")

    print("STUDENT_ACCESS_CLIENT_RUNTIME_SMOKE_GUARD=PASS")
    print(f"CURRENT_STATE={state}")
    print("EDGE_RUNTIME_VERSION=3")
    print("EXPECTED_EDGE_ROUTES=5")
    print("LIVE_SMOKE_EXECUTED=" + str(proof_complete).lower())
    print("LIVE_SMOKE_REEXECUTION=" + ("SEALED" if proof_complete else "NOT_YET_SEALED"))
    print("CLEANUP_REPO_ONLY=" + str(state == STATE_CLEANUP_REPO).lower())
    print("FLUTTER_ACTIVE_TRANSPORT=directRpc")
    print("EDGE_SELECTION=DENIED")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
