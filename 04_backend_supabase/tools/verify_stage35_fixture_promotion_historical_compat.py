from __future__ import annotations

import importlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
LEDGER = BACKEND / "migration_ledger_authority.json"
FIXTURE_MIGRATION = BACKEND / "migrations" / "20260823091500_stage35_alert_delivery_controlled_proof_fixture.sql"

CURRENT_BASELINE = "8324413284aaad9fc932f8f86269b6c339f240e9"
CURRENT_OBSERVED = "2026-08-23T09:05:47.415327Z"
RECEIPT_BASELINE = "6aad66c159c82c634af8ec58f0ec742267484b70"
RECEIPT_OBSERVED = "2026-08-22T07:54:12.776139Z"
RECEIPT_NAME = "stage35_alert_delivery_receipt_store"
FIXTURE_NAME = "stage35_alert_delivery_controlled_proof_fixture"
MODES = {
    "receipt", "deployment_seal",
    "current_cleanup",
    "cleanup", "current_rearm", "r0_seal", "r1_recovery", "stage31",
    "rate_limit", "valid_route", "smoke", "rollback", "rollback_prep", "rollback_seal",
    "assessment", "preparation", "promotion", "seal",
}


def fail(message: str) -> None:
    raise SystemExit("STAGE35_FIXTURE_PROMOTION_HISTORICAL_COMPAT=FAIL\n" + message)


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to read {path.relative_to(ROOT)}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"expected object: {path.relative_to(ROOT)}")
    return value


def project_to_receipt_frontier(current: dict) -> dict:
    if current.get("baseline_main_sha") != CURRENT_BASELINE:
        fail("current fixture-promotion ledger baseline drifted")
    if current.get("observed_at_utc") != CURRENT_OBSERVED:
        fail("current fixture-promotion ledger observation drifted")

    remote = {
        row.get("name"): row.get("version")
        for row in current.get("remote_migrations", []) if isinstance(row, dict)
    }
    if RECEIPT_NAME in remote or FIXTURE_NAME in remote:
        fail("Stage35 migration unexpectedly remote during repository promotion")
    if remote.get("stage33_direct_rpc_revocation_and_post_revocation_fixture") != "20260822032456":
        fail("Stage33 revocation remote receipt drifted")
    if remote.get("stage33_post_revocation_proof_cleanup") != "20260822061133":
        fail("Stage33 cleanup remote receipt drifted")

    repo_only = [
        row for row in current.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    ]
    if {row.get("name") for row in repo_only} != {RECEIPT_NAME, FIXTURE_NAME} or len(repo_only) != 2:
        fail("expected exactly two Stage35 repo-only divergences")

    projected = json.loads(json.dumps(current))
    projected["baseline_main_sha"] = RECEIPT_BASELINE
    projected["observed_at_utc"] = RECEIPT_OBSERVED
    projected["source"] = "Supabase.list_migrations+Supabase.execute_sql+Supabase.list_edge_functions"
    projected["declared_divergences"] = [
        row for row in projected.get("declared_divergences", [])
        if not (
            isinstance(row, dict)
            and row.get("direction") == "repo_only"
            and row.get("name") == FIXTURE_NAME
        )
    ]
    return projected


def run(mode: str) -> None:
    if mode not in MODES:
        fail(f"unsupported mode: {mode}")

    fixture_guard = importlib.import_module("verify_stage35_alert_controlled_fixture_migration_promotion")
    fixture_guard.main()

    current = load(LEDGER)
    projected = project_to_receipt_frontier(current)

    receipt_guard = importlib.import_module("verify_stage35_alert_receipt_store_migration_promotion")
    receipt_history = importlib.import_module("verify_stage35_receipt_store_historical_compat")
    seal_guard = importlib.import_module("verify_stage35_alert_dispatcher_deployment_proof_seal")
    seal_lifecycle = importlib.import_module("verify_stage35_alert_dispatcher_deployment_proof_seal_lifecycle")

    migration_bytes = FIXTURE_MIGRATION.read_bytes()
    with tempfile.TemporaryDirectory(prefix="fitnexus-stage35-fixture-history-") as tmp:
        temp_ledger = Path(tmp) / "migration_ledger_authority.json"
        temp_ledger.write_text(json.dumps(projected, indent=2) + "\n", encoding="utf-8")
        hidden_migration = Path(tmp) / FIXTURE_MIGRATION.name

        old_receipt_ledger = receipt_guard.LEDGER
        old_history_ledger = receipt_history.LEDGER
        old_seal_ledger = seal_guard.LEDGER
        try:
            hidden_migration.write_bytes(migration_bytes)
            FIXTURE_MIGRATION.unlink()
            receipt_guard.LEDGER = temp_ledger
            receipt_history.LEDGER = temp_ledger
            seal_guard.LEDGER = temp_ledger
            if mode == "receipt":
                receipt_guard.main()
            elif mode == "deployment_seal":
                seal_lifecycle.main()
            else:
                receipt_history.run(mode)
        finally:
            receipt_guard.LEDGER = old_receipt_ledger
            receipt_history.LEDGER = old_history_ledger
            seal_guard.LEDGER = old_seal_ledger
            if not FIXTURE_MIGRATION.exists():
                FIXTURE_MIGRATION.write_bytes(hidden_migration.read_bytes() if hidden_migration.exists() else migration_bytes)

    print("STAGE35_FIXTURE_PROMOTION_HISTORICAL_COMPAT=PASS")
    print(f"MODE={mode}")
    print(f"ACTUAL_BASELINE_MAIN_SHA={CURRENT_BASELINE}")
    print(f"ACTUAL_REPO_ONLY={RECEIPT_NAME},{FIXTURE_NAME}")
    print("ACTUAL_RECEIPT_STORE_REMOTE_APPLIED=false")
    print("ACTUAL_FIXTURE_REMOTE_APPLIED=false")
    print("PROJECTED_FIXTURE_VISIBLE=false")
    print("PROJECTED_RECEIPT_FRONTIER=true")
    print("PROOF_REEXECUTION_ALLOWED=false")
    print("STAGE35_REMOTE_APPLY_ALLOWED=false")
    print("ALERT_DISPATCHER_DEPLOY_ALLOWED=false")
    print("TELEGRAM_PROVIDER_CALLED=false")
    print("LAUNCH_GATE_PROMOTION=DENIED")


def main() -> None:
    if len(sys.argv) != 2:
        fail(
            "usage: verify_stage35_fixture_promotion_historical_compat.py "
            "<receipt|deployment_seal|current_cleanup|assessment|preparation|promotion|seal|cleanup|current_rearm|r0_seal|r1_recovery|stage31|rate_limit|valid_route|smoke|rollback|rollback_prep|rollback_seal>"
        )
    run(sys.argv[1])


if __name__ == "__main__":
    main()
