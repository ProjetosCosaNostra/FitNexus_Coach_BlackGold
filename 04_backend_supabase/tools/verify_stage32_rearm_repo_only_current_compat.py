from __future__ import annotations

import importlib
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
LEDGER = BACKEND / "migration_ledger_authority.json"
RECOVERY = BACKEND / "stage32_post_cutover_live_proof_failure_r0_authority.json"
REARM_SQL = BACKEND / "migrations" / "20260821213000_stage32_rearm_expired_fixture_r1.sql"

REARM_NAME = "stage32_rearm_expired_fixture_r1"
REARM_FILE = "04_backend_supabase/migrations/20260821213000_stage32_rearm_expired_fixture_r1.sql"
FAILURE_CLASS = "BGF-SUPABASE-EXECUTE-SQL-READONLY-DML-237"
ORIGINAL_FIXTURE = "stage32_post_cutover_edge_runtime_fixture"
ORIGINAL_FIXTURE_VERSION = "20260821171334"
HISTORICAL_LEDGER_BASELINE = "cd1f4a476ff9b0dc7ea378974a87c254f4bbbc64"
HISTORICAL_LEDGER_OBSERVED = "2026-08-21T17:13:56.735665Z"
CURRENT_REARM_BASELINE = "2b3dbfa2543230f8ae17a9838c610b326d453d02"
CURRENT_REARM_OBSERVED = "2026-08-21T21:29:21.68853Z"


def fail(message: str) -> None:
    raise SystemExit("STAGE32_REARM_REPO_ONLY_CURRENT_COMPAT=FAIL\n" + message)


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


def projected_ledger(current: dict) -> dict:
    repo_only = [
        row
        for row in current.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    ]
    if len(repo_only) != 1:
        fail("rearm migration must be the unique repo_only divergence")
    row = repo_only[0]
    if row.get("name") != REARM_NAME or row.get("related_failure_class") != FAILURE_CLASS:
        fail("rearm repo_only divergence identity drifted")

    remote = {
        row.get("name"): row.get("version")
        for row in current.get("remote_migrations", [])
        if isinstance(row, dict)
    }
    if remote.get(ORIGINAL_FIXTURE) != ORIGINAL_FIXTURE_VERSION:
        fail("original Stage32 fixture remote receipt disappeared")
    if REARM_NAME in remote:
        fail("rearm migration self-attested as remote before apply")
    if current.get("baseline_main_sha") != CURRENT_REARM_BASELINE:
        fail("rearm ledger baseline drifted")
    if current.get("observed_at_utc") != CURRENT_REARM_OBSERVED:
        fail("rearm ledger observation receipt drifted")

    value = json.loads(json.dumps(current))
    value["baseline_main_sha"] = HISTORICAL_LEDGER_BASELINE
    value["observed_at_utc"] = HISTORICAL_LEDGER_OBSERVED
    value["declared_divergences"] = [
        item
        for item in value.get("declared_divergences", [])
        if not (
            isinstance(item, dict)
            and item.get("direction") == "repo_only"
            and item.get("name") == REARM_NAME
        )
    ]
    return value


def main() -> None:
    ledger = load(LEDGER)
    recovery = load(RECOVERY)
    sql = text(REARM_SQL)

    failure_ids = [
        item.get("id")
        for item in recovery.get("failure_classes", [])
        if isinstance(item, dict)
    ]
    if FAILURE_CLASS not in failure_ids:
        fail("read-only DML failure class missing from recovery authority")
    if recovery.get("r2_baseline_main_sha") != CURRENT_REARM_BASELINE:
        fail("recovery R2 baseline drifted")
    if recovery.get("status") != "PRE_NETWORK_FAILURE_RECORDED_REARM_MIGRATION_REPO_ONLY":
        fail("recovery authority is not at repo-only rearm frontier")

    dml = recovery.get("execute_sql_dml_failure_receipt", {})
    expected_dml = {
        "source": "Supabase.execute_sql",
        "result": "FAIL_READ_ONLY_TRANSACTION",
        "sqlstate": "25006",
        "transaction_mutation_applied": False,
        "retry_through_execute_sql_allowed": False,
        "replacement_mechanism": "Supabase.apply_migration",
    }
    for key, expected in expected_dml.items():
        if dml.get(key) != expected:
            fail(f"execute_sql DML failure receipt drift: {key}")

    repair = recovery.get("repair_r1", {})
    expected_repair = {
        "historical_operation_execution_allowed": False,
        "fixture_rearm_migration_file": REARM_FILE,
        "fixture_rearm_migration_name": REARM_NAME,
        "migration_ledger_state": "repo_only",
        "remote_applied": False,
        "remote_version": None,
        "authorized_remote_mutation_tool": "Supabase.apply_migration",
        "requires_fresh_migration_ledger_check_immediately_before_apply": True,
        "requires_exact_merged_sql": True,
    }
    for key, expected in expected_repair.items():
        if repair.get(key) != expected:
            fail(f"rearm migration authority drift: {key}")

    for fragment in (
        FAILURE_CLASS,
        "STAGE32_R1_REARM_CUSTOMER_DOMAIN_NOT_EXACT_SYNTHETIC_FIXTURE",
        "STAGE32_R1_REARM_FIXTURE_IDENTITY_OR_EXPIRY_MISMATCH",
        "STAGE32_R1_REARM_RUNTIME_RESIDUE_DETECTED",
        "STAGE32_R1_REARM_GROWTH_FIXTURE_DRIFT",
        "STAGE32_R1_REARM_UPDATE_COUNT_MISMATCH",
        "STAGE32_R1_REARM_POSTCONDITION_FAILED",
        "set expires_at = now() + interval '6 hours'",
        "expires_at <= now()",
        "token_hash = extensions.digest(v_token, 'sha256')",
        "fitnexus-stage32-post-cutover-edge-runtime-proof-v1",
    ):
        if fragment not in sql:
            fail(f"rearm migration SQL drift: {fragment}")
    lower = sql.lower()
    if "delete from" in lower or "insert into" in lower:
        fail("rearm migration may only update the exact existing synthetic link")
    if lower.count("update public.student_access_links") != 1:
        fail("rearm migration must contain exactly one link update")

    projected = projected_ledger(ledger)
    with tempfile.TemporaryDirectory(prefix="fitnexus-stage32-rearm-current-") as tmp:
        temp_ledger = Path(tmp) / "migration_ledger_authority.json"
        temp_ledger.write_text(json.dumps(projected, indent=2) + "\n", encoding="utf-8")

        current_guard = importlib.import_module(
            "verify_student_access_stage32_post_cutover_runtime_preparation"
        )
        original_ledger = current_guard.LEDGER
        try:
            current_guard.LEDGER = temp_ledger
            current_guard.main()
        finally:
            current_guard.LEDGER = original_ledger

    print("STAGE32_REARM_REPO_ONLY_CURRENT_COMPAT=PASS")
    print(f"REARM_MIGRATION={REARM_NAME}")
    print("ACTUAL_REARM_LEDGER=REPO_ONLY")
    print("PROJECTED_REARM_REMOVED_FOR_STAGE32_HISTORICAL_AUTHORITY=true")
    print("EXECUTE_SQL_DML_ALLOWED=false")
    print("AUTHORIZED_REMOTE_MUTATION_TOOL=Supabase.apply_migration")
    print("PRODUCTION_ACTIVE_TRANSPORT=edgeGateway")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")
    print("LIVE_PROOF_R1_EXECUTED=false")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
