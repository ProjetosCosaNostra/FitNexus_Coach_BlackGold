from __future__ import annotations

import importlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
LEDGER = BACKEND / "migration_ledger_authority.json"

FIXTURE_NAME = "stage32_post_cutover_rollback_fixture"
FIXTURE_VERSION = "20260821235550"
CURRENT_BASELINE = "4e686d526779cce4236b6e1b4fba42c4ba6ef3c7"
CURRENT_OBSERVED = "2026-08-21T23:56:22.809328Z"
CLEANUP_BASELINE = "62809bbd4f27d0616110dae19024b163a4911521"
CLEANUP_OBSERVED = "2026-08-21T22:27:43.951028Z"
MODES = {
    "cleanup",
    "current_rearm",
    "r0_seal",
    "r1_recovery",
    "stage31",
    "rate_limit",
    "valid_route",
    "smoke",
    "rollback",
}


def fail(message: str) -> None:
    raise SystemExit("STAGE32_ROLLBACK_FIXTURE_HISTORICAL_COMPAT=FAIL\n" + message)


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to read {path.relative_to(ROOT)}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"expected JSON object: {path.relative_to(ROOT)}")
    return value


def projected_pre_rollback_fixture_ledger(current: dict) -> dict:
    repo_only = [
        row
        for row in current.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    ]
    if repo_only:
        fail("rollback fixture remains repo_only after authoritative remote apply")
    if current.get("baseline_main_sha") != CURRENT_BASELINE:
        fail("rollback fixture remote ledger baseline drifted")
    if current.get("observed_at_utc") != CURRENT_OBSERVED:
        fail("rollback fixture remote ledger observation drifted")

    remote = {
        item.get("name"): item.get("version")
        for item in current.get("remote_migrations", [])
        if isinstance(item, dict)
    }
    if remote.get("stage32_post_cutover_live_proof_r1_cleanup") != "20260821222724":
        fail("R1 cleanup remote receipt disappeared")
    if remote.get(FIXTURE_NAME) != FIXTURE_VERSION:
        fail("rollback fixture remote receipt disappeared or changed")

    value = json.loads(json.dumps(current))
    value["baseline_main_sha"] = CLEANUP_BASELINE
    value["observed_at_utc"] = CLEANUP_OBSERVED
    value["remote_migrations"] = [
        item
        for item in value.get("remote_migrations", [])
        if not (isinstance(item, dict) and item.get("name") == FIXTURE_NAME)
    ]
    return value


def run(mode: str) -> None:
    if mode not in MODES:
        fail(f"unsupported mode: {mode}")

    current = importlib.import_module(
        "verify_stage32_post_cutover_rollback_proof_preparation"
    )
    current.main()

    projected = projected_pre_rollback_fixture_ledger(load(LEDGER))
    cleanup_guard = importlib.import_module(
        "verify_stage32_post_cutover_live_proof_r1_cleanup_preparation"
    )
    cleanup_history = importlib.import_module(
        "verify_stage32_r1_cleanup_historical_compat"
    )

    with tempfile.TemporaryDirectory(prefix="fitnexus-stage32-rollback-fixture-history-") as tmp:
        temp_ledger = Path(tmp) / "migration_ledger_authority.json"
        temp_ledger.write_text(json.dumps(projected, indent=2) + "\n", encoding="utf-8")

        original_cleanup_ledger = cleanup_guard.LEDGER
        original_history_ledger = cleanup_history.LEDGER
        cleanup_guard.LEDGER = temp_ledger
        cleanup_history.LEDGER = temp_ledger
        try:
            if mode == "cleanup":
                cleanup_guard.main()
            else:
                cleanup_history.run(mode)
        finally:
            cleanup_guard.LEDGER = original_cleanup_ledger
            cleanup_history.LEDGER = original_history_ledger

    print("STAGE32_ROLLBACK_FIXTURE_HISTORICAL_COMPAT=PASS")
    print(f"MODE={mode}")
    print("ACTUAL_CURRENT_STATE=POST_CUTOVER_ROLLBACK_FIXTURE_REMOTE_LIVE_PROOF_PENDING_EDGE_MODE")
    print(f"ACTUAL_ROLLBACK_FIXTURE={FIXTURE_NAME}")
    print(f"ACTUAL_ROLLBACK_FIXTURE_REMOTE_VERSION={FIXTURE_VERSION}")
    print("ACTUAL_ROLLBACK_FIXTURE_REMOTE_APPLIED=true")
    print("PROJECTED_ROLLBACK_FIXTURE_REMOTE_ROW_REMOVED=true")
    print(f"PROJECTED_LEDGER_BASELINE={CLEANUP_BASELINE}")
    print(f"PROJECTED_LEDGER_OBSERVED={CLEANUP_OBSERVED}")
    print("R1_EDGE_LIVE_PROOF_REEXECUTION_ALLOWED=false")
    print("PRODUCTION_ACTIVE_TRANSPORT=edgeGateway")
    print("ROLLBACK_PROOF_EXECUTED=false")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")
    print("LAUNCH_GATE_PROMOTION=DENIED")


def main() -> None:
    if len(sys.argv) != 2:
        fail(
            "usage: verify_stage32_rollback_fixture_historical_compat.py "
            "<cleanup|current_rearm|r0_seal|r1_recovery|stage31|rate_limit|valid_route|smoke|rollback>"
        )
    run(sys.argv[1])


if __name__ == "__main__":
    main()
