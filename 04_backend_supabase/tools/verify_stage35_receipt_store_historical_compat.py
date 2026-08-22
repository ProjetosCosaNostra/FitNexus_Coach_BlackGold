from __future__ import annotations

import importlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
LEDGER = BACKEND / "migration_ledger_authority.json"

CURRENT_BASELINE = "6aad66c159c82c634af8ec58f0ec742267484b70"
CURRENT_OBSERVED = "2026-08-22T07:54:12.776139Z"
HISTORICAL_STAGE33_BASELINE = "e30aa197fe5d19b9e385a8720944c6c9c10d34ee"
HISTORICAL_STAGE33_OBSERVED = "2026-08-22T06:11:53.105067Z"
STAGE35_NAME = "stage35_alert_delivery_receipt_store"
MODES = {
    "current_cleanup",
    "cleanup", "current_rearm", "r0_seal", "r1_recovery", "stage31",
    "rate_limit", "valid_route", "smoke", "rollback", "rollback_prep", "rollback_seal",
    "assessment", "preparation", "promotion", "seal",
}


def fail(message: str) -> None:
    raise SystemExit("STAGE35_RECEIPT_STORE_HISTORICAL_COMPAT=FAIL\n" + message)


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to read {path.relative_to(ROOT)}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"expected JSON object: {path.relative_to(ROOT)}")
    return value


def project_ledger(current: dict) -> dict:
    if current.get("baseline_main_sha") != CURRENT_BASELINE:
        fail("current Stage35 ledger baseline drifted")
    if current.get("observed_at_utc") != CURRENT_OBSERVED:
        fail("current Stage35 ledger observation drifted")

    remote = {
        row.get("name"): row.get("version")
        for row in current.get("remote_migrations", []) if isinstance(row, dict)
    }
    if STAGE35_NAME in remote:
        fail("Stage35 receipt store unexpectedly remote during repo-only promotion")
    if remote.get("stage33_direct_rpc_revocation_and_post_revocation_fixture") != "20260822032456":
        fail("Stage33 revocation remote receipt drifted")
    if remote.get("stage33_post_revocation_proof_cleanup") != "20260822061133":
        fail("Stage33 cleanup remote receipt drifted")

    repo_only = [
        row for row in current.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    ]
    if len(repo_only) != 1 or repo_only[0].get("name") != STAGE35_NAME:
        fail("Stage35 receipt store must be the unique current repo-only divergence")

    value = json.loads(json.dumps(current))
    value["baseline_main_sha"] = HISTORICAL_STAGE33_BASELINE
    value["observed_at_utc"] = HISTORICAL_STAGE33_OBSERVED
    value["source"] = "Supabase.list_migrations+Supabase.execute_sql"
    value["declared_divergences"] = [
        row for row in value.get("declared_divergences", [])
        if not (
            isinstance(row, dict)
            and row.get("direction") == "repo_only"
            and row.get("name") == STAGE35_NAME
        )
    ]
    return value


def run(mode: str) -> None:
    if mode not in MODES:
        fail(f"unsupported mode: {mode}")

    # Prove the actual Stage35 repo-only frontier before projecting any historical ledger.
    stage35 = importlib.import_module("verify_stage35_alert_receipt_store_migration_promotion")
    stage35.main()

    current = load(LEDGER)
    projected = project_ledger(current)

    cleanup_guard = importlib.import_module("verify_stage33_post_revocation_proof_cleanup_preparation")
    stage33_history = importlib.import_module("verify_stage33_cleanup_historical_compat")

    with tempfile.TemporaryDirectory(prefix="fitnexus-stage35-history-") as tmp:
        temp_ledger = Path(tmp) / "migration_ledger_authority.json"
        temp_ledger.write_text(json.dumps(projected, indent=2) + "\n", encoding="utf-8")

        old_cleanup_ledger = cleanup_guard.LEDGER
        old_stage33_ledger = stage33_history.LEDGER
        try:
            cleanup_guard.LEDGER = temp_ledger
            stage33_history.LEDGER = temp_ledger
            if mode == "current_cleanup":
                cleanup_guard.main()
            else:
                stage33_history.run(mode)
        finally:
            cleanup_guard.LEDGER = old_cleanup_ledger
            stage33_history.LEDGER = old_stage33_ledger

    print("STAGE35_RECEIPT_STORE_HISTORICAL_COMPAT=PASS")
    print(f"MODE={mode}")
    print("ACTUAL_STAGE35_STATE=RECEIPT_STORE_MIGRATION_REPO_ONLY_DISPATCHER_DEPLOYMENT_SEAL_PENDING")
    print(f"ACTUAL_STAGE35_REPO_ONLY={STAGE35_NAME}")
    print("ACTUAL_STAGE35_REMOTE_APPLIED=false")
    print("PROJECTED_STAGE35_REPO_ONLY_VISIBLE=false")
    print("PROJECTED_STAGE33_REMOTE_COMPLETE=true")
    print("PROOF_REEXECUTION_ALLOWED=false")
    print("STAGE33_CLEANUP_REAPPLY_ALLOWED=false")
    print("STAGE35_REMOTE_APPLY_ALLOWED=false")
    print("ALERT_DISPATCHER_DEPLOY_ALLOWED=false")
    print("LAUNCH_GATE_PROMOTION=DENIED")


def main() -> None:
    if len(sys.argv) != 2:
        fail(
            "usage: verify_stage35_receipt_store_historical_compat.py "
            "<current_cleanup|assessment|preparation|promotion|seal|cleanup|current_rearm|r0_seal|r1_recovery|stage31|rate_limit|valid_route|smoke|rollback|rollback_prep|rollback_seal>"
        )
    run(sys.argv[1])


if __name__ == "__main__":
    main()
