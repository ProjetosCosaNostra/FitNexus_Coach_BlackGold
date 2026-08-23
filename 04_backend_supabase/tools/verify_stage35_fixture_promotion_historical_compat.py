from __future__ import annotations

import importlib
import json
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
LEDGER = BACKEND / "migration_ledger_authority.json"
FIXTURE_MIGRATION = BACKEND / "migrations" / "20260823091500_stage35_alert_delivery_controlled_proof_fixture.sql"
CLEANUP_MIGRATION = BACKEND / "migrations" / "20260823161000_stage35_alert_delivery_controlled_proof_cleanup.sql"

RECONCILED_BASELINE = "a23dd9d892189b92a633634caf750606504e83ee"
RECONCILED_OBSERVED = "2026-08-23T15:56:57.947085Z"
CLEANUP_PROMOTION_BASELINE = "db522140cc2b21840b5b48727cb15a82ca22f975"
CLEANUP_PROMOTION_OBSERVED = "2026-08-23T16:06:48.978350Z"
FIXTURE_BASELINE = "8324413284aaad9fc932f8f86269b6c339f240e9"
FIXTURE_OBSERVED = "2026-08-23T09:05:47.415327Z"
RECEIPT_BASELINE = "6aad66c159c82c634af8ec58f0ec742267484b70"
RECEIPT_OBSERVED = "2026-08-22T07:54:12.776139Z"
RECEIPT_NAME = "stage35_alert_delivery_receipt_store"
FIXTURE_NAME = "stage35_alert_delivery_controlled_proof_fixture"
CLEANUP_NAME = "stage35_alert_delivery_controlled_proof_cleanup"
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


def normalize_to_reconciled_frontier(current: dict) -> tuple[dict, bool]:
    remote = {
        row.get("name"): row.get("version")
        for row in current.get("remote_migrations", []) if isinstance(row, dict)
    }
    if remote.get(RECEIPT_NAME) != RECEIPT_REMOTE_VERSION:
        fail("current receipt-store remote version drifted")
    if remote.get(FIXTURE_NAME) != FIXTURE_REMOTE_VERSION:
        fail("current controlled-fixture remote version drifted")
    if remote.get("stage33_direct_rpc_revocation_and_post_revocation_fixture") != "20260822032456":
        fail("Stage33 revocation remote receipt drifted")
    if remote.get("stage33_post_revocation_proof_cleanup") != "20260822061133":
        fail("Stage33 cleanup remote receipt drifted")

    divergences = [row for row in current.get("declared_divergences", []) if isinstance(row, dict)]
    remote_only = [row for row in divergences if row.get("direction") == "remote_only"]
    repo_only = [row for row in divergences if row.get("direction") == "repo_only"]
    if len(remote_only) != 3:
        fail("historical remote-only divergence count drifted")

    baseline = current.get("baseline_main_sha")
    observed = current.get("observed_at_utc")
    if baseline == RECONCILED_BASELINE and observed == RECONCILED_OBSERVED:
        if repo_only:
            fail("reconciled frontier unexpectedly contains repo-only rows")
        return json.loads(json.dumps(current)), False

    if baseline == CLEANUP_PROMOTION_BASELINE and observed == CLEANUP_PROMOTION_OBSERVED:
        if {row.get("name") for row in repo_only} != {CLEANUP_NAME} or len(repo_only) != 1:
            fail("cleanup-promotion frontier must contain exactly one cleanup repo-only row")
        projected = json.loads(json.dumps(current))
        projected["baseline_main_sha"] = RECONCILED_BASELINE
        projected["observed_at_utc"] = RECONCILED_OBSERVED
        projected["declared_divergences"] = remote_only
        return projected, True

    fail("current ledger is neither reconciled nor cleanup-promotion frontier")
    raise AssertionError("unreachable")


def project_to_fixture_frontier(reconciled: dict) -> dict:
    if reconciled.get("baseline_main_sha") != RECONCILED_BASELINE:
        fail("reconciled projection baseline drifted")
    if reconciled.get("observed_at_utc") != RECONCILED_OBSERVED:
        fail("reconciled projection observation drifted")

    remote = {
        row.get("name"): row.get("version")
        for row in reconciled.get("remote_migrations", []) if isinstance(row, dict)
    }
    if remote.get(RECEIPT_NAME) != RECEIPT_REMOTE_VERSION:
        fail("reconciled receipt-store remote version drifted")
    if remote.get(FIXTURE_NAME) != FIXTURE_REMOTE_VERSION:
        fail("reconciled controlled-fixture remote version drifted")

    divergences = [row for row in reconciled.get("declared_divergences", []) if isinstance(row, dict)]
    remote_only = [row for row in divergences if row.get("direction") == "remote_only"]
    if [row for row in divergences if row.get("direction") == "repo_only"]:
        fail("reconciled frontier must have no repo-only rows")

    projected = json.loads(json.dumps(reconciled))
    projected["baseline_main_sha"] = FIXTURE_BASELINE
    projected["observed_at_utc"] = FIXTURE_OBSERVED
    projected["remote_migrations"] = [
        row for row in projected.get("remote_migrations", [])
        if not (isinstance(row, dict) and row.get("name") in {RECEIPT_NAME, FIXTURE_NAME})
    ]
    projected["declared_divergences"] = list(remote_only) + [
        {
            "direction": "repo_only",
            "name": RECEIPT_NAME,
            "reason": "Exact repository promotion of the reviewed Stage35 privacy-minimized alert delivery receipt-store candidate. Remote application remains forbidden until a separate dispatcher deployment and controlled external-delivery proof sequence is authorized.",
            "owner": "BlackGold Forge",
            "related_failure_class": "BGF-STAGE35-ALERT-CANDIDATE-REMOTE-MUTATION-281",
        },
        {
            "direction": "repo_only",
            "name": FIXTURE_NAME,
            "reason": "Exact repository promotion of the reviewed Stage35 synthetic controlled-delivery fixture after runtime secret-name readiness was proven. Remote application remains forbidden until this promotion is merged green and the receipt-store apply / dispatcher deployment sequence is separately authorized.",
            "owner": "BlackGold Forge",
            "related_failure_class": "BGF-STAGE35-ALERT-CONTROLLED-FIXTURE-PREMATURE-284",
        },
    ]
    return projected


def project_to_receipt_frontier(fixture_frontier: dict) -> dict:
    if fixture_frontier.get("baseline_main_sha") != FIXTURE_BASELINE:
        fail("fixture-promotion projection baseline drifted")
    if fixture_frontier.get("observed_at_utc") != FIXTURE_OBSERVED:
        fail("fixture-promotion projection observation drifted")

    remote = {
        row.get("name"): row.get("version")
        for row in fixture_frontier.get("remote_migrations", []) if isinstance(row, dict)
    }
    if RECEIPT_NAME in remote or FIXTURE_NAME in remote:
        fail("Stage35 migration unexpectedly remote during fixture-promotion projection")

    repo_only = [
        row for row in fixture_frontier.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    ]
    if {row.get("name") for row in repo_only} != {RECEIPT_NAME, FIXTURE_NAME} or len(repo_only) != 2:
        fail("fixture-promotion projection must contain exactly two Stage35 repo-only divergences")

    projected = json.loads(json.dumps(fixture_frontier))
    projected["baseline_main_sha"] = RECEIPT_BASELINE
    projected["observed_at_utc"] = RECEIPT_OBSERVED
    projected["declared_divergences"] = [
        row for row in projected.get("declared_divergences", [])
        if not (
            isinstance(row, dict)
            and row.get("direction") == "repo_only"
            and row.get("name") == FIXTURE_NAME
        )
    ]
    return projected


@contextmanager
def temporarily_hide_cleanup_migration():
    if not CLEANUP_MIGRATION.exists():
        yield
        return
    data = CLEANUP_MIGRATION.read_bytes()
    CLEANUP_MIGRATION.unlink()
    try:
        yield
    finally:
        CLEANUP_MIGRATION.write_bytes(data)


def run(mode: str) -> None:
    if mode not in MODES:
        fail(f"unsupported mode: {mode}")

    current = load(LEDGER)
    reconciled, cleanup_frontier = normalize_to_reconciled_frontier(current)
    fixture_frontier = project_to_fixture_frontier(reconciled)
    fixture_guard = importlib.import_module("verify_stage35_alert_controlled_fixture_migration_promotion")

    # The fixture guard itself is current-frontier aware. Run it against the real
    # repository before projecting older frontiers.
    fixture_guard.main()

    if mode == "fixture":
        print("STAGE35_FIXTURE_PROMOTION_HISTORICAL_COMPAT=PASS")
        print("MODE=fixture")
        print(f"ACTUAL_BASELINE_MAIN_SHA={current.get('baseline_main_sha')}")
        print(f"ACTUAL_RECEIPT_STORE_REMOTE_VERSION={RECEIPT_REMOTE_VERSION}")
        print(f"ACTUAL_FIXTURE_REMOTE_VERSION={FIXTURE_REMOTE_VERSION}")
        print(f"ACTUAL_CLEANUP_REPO_ONLY={str(cleanup_frontier).lower()}")
        print("PROJECTED_FIXTURE_PROMOTION_FRONTIER=true")
        print("PROOF_REEXECUTION_ALLOWED=false")
        print("TELEGRAM_PROVIDER_CALLED_BY_GUARD=false")
        print("LAUNCH_GATE_PROMOTION=DENIED")
        return

    projected = project_to_receipt_frontier(fixture_frontier)
    receipt_guard = importlib.import_module("verify_stage35_alert_receipt_store_migration_promotion")
    receipt_history = importlib.import_module("verify_stage35_receipt_store_historical_compat")
    seal_guard = importlib.import_module("verify_stage35_alert_dispatcher_deployment_proof_seal")
    seal_lifecycle = importlib.import_module("verify_stage35_alert_dispatcher_deployment_proof_seal_lifecycle")

    fixture_bytes = FIXTURE_MIGRATION.read_bytes()
    with tempfile.TemporaryDirectory(prefix="fitnexus-stage35-fixture-history-") as tmp:
        temp_ledger = Path(tmp) / "migration_ledger_authority.json"
        temp_ledger.write_text(json.dumps(projected, indent=2) + "\n", encoding="utf-8")
        hidden_fixture = Path(tmp) / FIXTURE_MIGRATION.name

        old_receipt_ledger = receipt_guard.LEDGER
        old_history_ledger = receipt_history.LEDGER
        old_seal_ledger = seal_guard.LEDGER
        with temporarily_hide_cleanup_migration():
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
    print(f"ACTUAL_RECEIPT_STORE_REMOTE_VERSION={RECEIPT_REMOTE_VERSION}")
    print(f"ACTUAL_FIXTURE_REMOTE_VERSION={FIXTURE_REMOTE_VERSION}")
    print(f"ACTUAL_CLEANUP_REPO_ONLY={str(cleanup_frontier).lower()}")
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
