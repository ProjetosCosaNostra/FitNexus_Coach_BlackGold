from __future__ import annotations

import importlib
import json
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

from stage35_migration_frontier import state as frontier_state, to_fixture, to_receipt, to_reconciled

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
LEDGER = BACKEND / "migration_ledger_authority.json"
FIXTURE_MIGRATION = BACKEND / "migrations" / "20260823091500_stage35_alert_delivery_controlled_proof_fixture.sql"
CLEANUP_MIGRATION = BACKEND / "migrations" / "20260823161000_stage35_alert_delivery_controlled_proof_cleanup.sql"

RECEIPT_REMOTE_VERSION = "20260823092354"
FIXTURE_REMOTE_VERSION = "20260823145908"
MODES = {
    "fixture", "receipt", "deployment_seal",
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


@contextmanager
def temporarily_hide(path: Path):
    if not path.exists():
        yield
        return
    data = path.read_bytes()
    path.unlink()
    try:
        yield
    finally:
        path.write_bytes(data)


def run(mode: str) -> None:
    if mode not in MODES:
        fail(f"unsupported mode: {mode}")

    current = load(LEDGER)
    try:
        current_kind = frontier_state(current)
        reconciled = to_reconciled(current)
        fixture_frontier = to_fixture(current)
        receipt_frontier = to_receipt(current)
    except ValueError as exc:
        fail(f"Stage35 frontier projection failed: {exc}")

    fixture_guard = importlib.import_module("verify_stage35_alert_controlled_fixture_migration_promotion")
    fixture_guard.main()

    if mode == "fixture":
        print("STAGE35_FIXTURE_PROMOTION_HISTORICAL_COMPAT=PASS")
        print("MODE=fixture")
        print(f"ACTUAL_BASELINE_MAIN_SHA={current.get('baseline_main_sha')}")
        print(f"ACTUAL_STAGE35_FRONTIER={current_kind}")
        print(f"ACTUAL_RECEIPT_STORE_REMOTE_VERSION={RECEIPT_REMOTE_VERSION}")
        print(f"ACTUAL_FIXTURE_REMOTE_VERSION={FIXTURE_REMOTE_VERSION}")
        print("PROJECTED_RECONCILED_FRONTIER=true")
        print("PROJECTED_FIXTURE_PROMOTION_FRONTIER=true")
        print("PROOF_REEXECUTION_ALLOWED=false")
        print("TELEGRAM_PROVIDER_CALLED_BY_GUARD=false")
        print("LAUNCH_GATE_PROMOTION=DENIED")
        return

    if reconciled.get("baseline_main_sha") != "a23dd9d892189b92a633634caf750606504e83ee":
        fail("reconciled frontier projection baseline drifted")
    if fixture_frontier.get("baseline_main_sha") != "8324413284aaad9fc932f8f86269b6c339f240e9":
        fail("fixture frontier projection baseline drifted")
    if receipt_frontier.get("baseline_main_sha") != "6aad66c159c82c634af8ec58f0ec742267484b70":
        fail("receipt frontier projection baseline drifted")

    receipt_guard = importlib.import_module("verify_stage35_alert_receipt_store_migration_promotion")
    receipt_history = importlib.import_module("verify_stage35_receipt_store_historical_compat")
    seal_guard = importlib.import_module("verify_stage35_alert_dispatcher_deployment_proof_seal")
    seal_lifecycle = importlib.import_module("verify_stage35_alert_dispatcher_deployment_proof_seal_lifecycle")

    fixture_bytes = FIXTURE_MIGRATION.read_bytes()
    with tempfile.TemporaryDirectory(prefix="fitnexus-stage35-frontier-history-") as tmp:
        temp_ledger = Path(tmp) / "migration_ledger_authority.json"
        temp_ledger.write_text(json.dumps(receipt_frontier, indent=2) + "\n", encoding="utf-8")
        hidden_fixture = Path(tmp) / FIXTURE_MIGRATION.name

        old_receipt_ledger = receipt_guard.LEDGER
        old_history_ledger = receipt_history.LEDGER
        old_seal_ledger = seal_guard.LEDGER
        with temporarily_hide(CLEANUP_MIGRATION):
            try:
                hidden_fixture.write_bytes(fixture_bytes)
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
                    FIXTURE_MIGRATION.write_bytes(hidden_fixture.read_bytes() if hidden_fixture.exists() else fixture_bytes)

    print("STAGE35_FIXTURE_PROMOTION_HISTORICAL_COMPAT=PASS")
    print(f"MODE={mode}")
    print(f"ACTUAL_BASELINE_MAIN_SHA={current.get('baseline_main_sha')}")
    print(f"ACTUAL_STAGE35_FRONTIER={current_kind}")
    print(f"ACTUAL_RECEIPT_STORE_REMOTE_VERSION={RECEIPT_REMOTE_VERSION}")
    print(f"ACTUAL_FIXTURE_REMOTE_VERSION={FIXTURE_REMOTE_VERSION}")
    print("PROJECTED_RECONCILED_FRONTIER=true")
    print("PROJECTED_FIXTURE_PROMOTION_FRONTIER=true")
    print("PROJECTED_RECEIPT_PROMOTION_FRONTIER=true")
    print("PROOF_REEXECUTION_ALLOWED=false")
    print("STAGE35_REMOTE_REAPPLY_ALLOWED=false")
    print("TELEGRAM_PROVIDER_CALLED_BY_GUARD=false")
    print("LAUNCH_GATE_PROMOTION=DENIED")


def main() -> None:
    if len(sys.argv) != 2:
        fail(
            "usage: verify_stage35_fixture_promotion_historical_compat.py "
            "<fixture|receipt|deployment_seal|current_cleanup|assessment|preparation|promotion|seal|cleanup|current_rearm|r0_seal|r1_recovery|stage31|rate_limit|valid_route|smoke|rollback|rollback_prep|rollback_seal>"
        )
    run(sys.argv[1])


if __name__ == "__main__":
    main()
