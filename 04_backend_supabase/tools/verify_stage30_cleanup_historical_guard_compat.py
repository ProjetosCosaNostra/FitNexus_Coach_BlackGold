from __future__ import annotations

import importlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
LEDGER = BACKEND / "migration_ledger_authority.json"
SMOKE_AUTHORITY = BACKEND / "student_access_client_runtime_smoke_authority.json"
CLEANUP_SQL = BACKEND / "migrations" / "20260821081005_stage30_edge_runtime_smoke_cleanup.sql"

CLEANUP_NAME = "stage30_edge_runtime_smoke_cleanup"
CLEANUP_STATE = "EDGE_RUNTIME_SMOKE_LIVE_VERIFIED_CLEANUP_REPO_ONLY"
CLEANUP_FAILURE_CLASS = "BGF-STAGE30-RUNTIME-SMOKE-CLEANUP-SCOPE-207"
SEALED_RUN = 32461357789

TARGETS = {
    "rate_limit": "verify_student_access_network_rate_limit",
    "valid_route": "verify_student_access_valid_route_fixture",
}


def fail(message: str) -> None:
    raise SystemExit("STAGE30_CLEANUP_HISTORICAL_GUARD_COMPAT=FAIL\n" + message)


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to read {path.relative_to(ROOT)}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"expected JSON object: {path.relative_to(ROOT)}")
    return value


def validate_cleanup_authority(ledger: dict, smoke: dict) -> bool:
    repo_rows = [
        row
        for row in ledger.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    ]
    repo_names = {row.get("name") for row in repo_rows}

    if CLEANUP_NAME not in repo_names:
        return False
    if repo_names != {CLEANUP_NAME}:
        fail(f"cleanup compatibility refuses mixed repo_only set: {sorted(repo_names)}")

    row = repo_rows[0]
    if row.get("related_failure_class") != CLEANUP_FAILURE_CLASS:
        fail("cleanup divergence failure class drifted")
    if row.get("owner") != "BlackGold Forge":
        fail("cleanup divergence owner drifted")

    if smoke.get("schema_version") != 1 or smoke.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("Stage 30 smoke authority identity drifted")
    if smoke.get("current_state") != CLEANUP_STATE:
        fail("cleanup repo_only divergence is not backed by cleanup repository authority")
    if smoke.get("cleanup_scope_failure_class") != CLEANUP_FAILURE_CLASS:
        fail("cleanup scope failure class missing from smoke authority")
    if smoke.get("baseline_main_sha") != "aba1937b426c1bb681e4e39065fbfb840653c41e":
        fail("cleanup authority baseline main SHA drifted")

    fixture = smoke.get("fixture", {})
    if fixture.get("migration_name") != "stage30_edge_runtime_smoke_fixture":
        fail("Stage 30 fixture identity drifted")
    if fixture.get("remote_applied") is not True or fixture.get("remote_version") != "20260821075532":
        fail("Stage 30 fixture remote receipt missing")
    if fixture.get("migration_ledger_state") != "remote_reconciled":
        fail("Stage 30 fixture is not ledger-reconciled")

    proof = smoke.get("runtime_proof", {})
    for key in (
        "fixture_deployed",
        "get_workout_verified",
        "start_workout_verified",
        "set_completion_verified",
        "get_feedback_context_verified",
        "submit_feedback_verified",
        "all_five_routes_verified",
        "completed_session_verified",
        "feedback_submitted_verified",
    ):
        if proof.get(key) is not True:
            fail(f"cleanup missing sealed Stage 30 proof prerequisite: {key}")
    if proof.get("proof_workflow_run_id") != SEALED_RUN or proof.get("proof_result") != "PASS":
        fail("sealed Stage 30 workflow receipt drifted")
    for key in (
        "raw_token_returned",
        "raw_network_origin_returned",
        "real_student_data_used",
        "real_student_data_mutated",
        "proof_reexecution_allowed",
        "cleanup_completed",
    ):
        if proof.get(key) is not False:
            fail(f"cleanup proof invariant drifted: {key}")

    cleanup = smoke.get("cleanup_migration", {})
    expected_cleanup = {
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
        "raw_network_origin_embedded_in_repository": False,
        "network_origin_digest_embedded_in_repository": False,
        "organization_deleted_before_auth_user": True,
        "transactional_postcondition_required": True,
    }
    for key, expected in expected_cleanup.items():
        if cleanup.get(key) != expected:
            fail(f"cleanup migration authority drift for {key}")
    if cleanup.get("network_proof_windows_utc") != [
        "2026-08-21T08:02:00Z",
        "2026-08-21T08:03:00Z",
    ]:
        fail("cleanup network proof windows drifted")

    client = smoke.get("client_cutover_authority", {})
    if client.get("active_transport") != "directRpc":
        fail("cleanup attempted after Flutter transport changed")
    for key in ("edge_gateway_selected", "rollback_verified", "direct_rpc_execute_revoked"):
        if client.get(key) is not False:
            fail(f"cleanup client boundary self-promoted: {key}")

    next_stage = smoke.get("next_stage", {})
    if next_stage.get("name") != "APPLY_STAGE30_RUNTIME_SMOKE_CLEANUP":
        fail("cleanup next-stage authority drifted")
    if next_stage.get("allowed_now") is not True:
        fail("cleanup apply authority unexpectedly blocked")
    if next_stage.get("requires_ci_and_merge_first") is not True or next_stage.get("requires_exact_merged_sql") is not True:
        fail("cleanup apply interlock missing")

    try:
        sql = CLEANUP_SQL.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"cleanup migration source unavailable: {type(exc).__name__}")
    for fragment in (
        CLEANUP_FAILURE_CLASS,
        "STAGE30_CLEANUP_CUSTOMER_DOMAIN_NO_LONGER_SYNTHETIC_ONLY",
        "STAGE30_CLEANUP_POSTCONDITION_FAILED",
        "delete from public.organizations where id = v_org",
        "delete from auth.users where id = v_user",
    ):
        if fragment not in sql:
            fail(f"cleanup migration source drift: {fragment}")
    lower = sql.lower()
    if "origin_hash" in lower or "cf-connecting-ip" in lower or "x-forwarded-for" in lower or "x-real-ip" in lower:
        fail("cleanup migration source contains network-origin material")

    return True


def sanitized_ledger(ledger: dict) -> dict:
    clone = json.loads(json.dumps(ledger))
    clone["declared_divergences"] = [
        row
        for row in clone.get("declared_divergences", [])
        if not (
            isinstance(row, dict)
            and row.get("direction") == "repo_only"
            and row.get("name") == CLEANUP_NAME
        )
    ]
    return clone


def run_target(mode: str) -> None:
    module_name = TARGETS.get(mode)
    if module_name is None:
        fail(f"unsupported mode: {mode}")

    ledger = load(LEDGER)
    smoke = load(SMOKE_AUTHORITY)
    cleanup_active = validate_cleanup_authority(ledger, smoke)

    module = importlib.import_module(module_name)
    if not cleanup_active:
        module.main()
        print("STAGE30_CLEANUP_HISTORICAL_GUARD_COMPAT=PASS")
        print(f"MODE={mode}")
        print("LEDGER_COMPATIBILITY=NOT_REQUIRED")
        return

    with tempfile.TemporaryDirectory(prefix="fitnexus-stage30-cleanup-ledger-") as tmp:
        temp_ledger = Path(tmp) / "migration_ledger_authority.json"
        temp_ledger.write_text(
            json.dumps(sanitized_ledger(ledger), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        module.LEDGER = temp_ledger
        module.main()

    print("STAGE30_CLEANUP_HISTORICAL_GUARD_COMPAT=PASS")
    print(f"MODE={mode}")
    print("LEDGER_COMPATIBILITY=STAGE30_CLEANUP_ONLY")
    print(f"FAILURE_CLASS={CLEANUP_FAILURE_CLASS}")


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: verify_stage30_cleanup_historical_guard_compat.py <rate_limit|valid_route>")
    run_target(sys.argv[1])


if __name__ == "__main__":
    main()
