from __future__ import annotations

import importlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
LEDGER = BACKEND / "migration_ledger_authority.json"

CLEANUP_NAME = "stage32_post_cutover_live_proof_r1_cleanup"
CLEANUP_FAILURE = "BGF-STAGE32-POST-CUTOVER-R1-CLEANUP-239"
CURRENT_BASELINE = "6be68c35e4e7f1ec4e69bc0c8a9a872b62abad48"
CURRENT_OBSERVED = "2026-08-21T22:18:35.737097Z"
REARM_REMOTE_BASELINE = "71a4e8de96f903d142e63ab9fb98ff6d24035e6d"
REARM_REMOTE_OBSERVED = "2026-08-21T21:40:30.546568Z"
MODES = {
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
    raise SystemExit("STAGE32_R1_CLEANUP_HISTORICAL_COMPAT=FAIL\n" + message)


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to read {path.relative_to(ROOT)}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"expected JSON object: {path.relative_to(ROOT)}")
    return value


def projected_pre_cleanup_ledger(current: dict) -> dict:
    repo_only = [
        row
        for row in current.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    ]
    if len(repo_only) != 1:
        fail("R1 cleanup must be the unique repo_only divergence")
    row = repo_only[0]
    if row.get("name") != CLEANUP_NAME or row.get("related_failure_class") != CLEANUP_FAILURE:
        fail("R1 cleanup repo_only identity drifted")
    if current.get("baseline_main_sha") != CURRENT_BASELINE:
        fail("R1 cleanup ledger baseline drifted")
    if current.get("observed_at_utc") != CURRENT_OBSERVED:
        fail("R1 cleanup ledger observation drifted")

    remote = {
        item.get("name"): item.get("version")
        for item in current.get("remote_migrations", [])
        if isinstance(item, dict)
    }
    if remote.get("stage32_post_cutover_edge_runtime_fixture") != "20260821171334":
        fail("Stage32 fixture remote receipt disappeared")
    if remote.get("stage32_rearm_expired_fixture_r1") != "20260821214005":
        fail("Stage32 rearm remote receipt disappeared")
    if CLEANUP_NAME in remote:
        fail("R1 cleanup self-attested as remotely applied")

    value = json.loads(json.dumps(current))
    value["baseline_main_sha"] = REARM_REMOTE_BASELINE
    value["observed_at_utc"] = REARM_REMOTE_OBSERVED
    value["declared_divergences"] = [
        item
        for item in value.get("declared_divergences", [])
        if not (
            isinstance(item, dict)
            and item.get("direction") == "repo_only"
            and item.get("name") == CLEANUP_NAME
        )
    ]
    return value


def run(mode: str) -> None:
    if mode not in MODES:
        fail(f"unsupported mode: {mode}")

    # Validate the actual current frontier first. Historical projections below are
    # non-authoritative compatibility views only; they cannot promote current state.
    cleanup_guard = importlib.import_module(
        "verify_stage32_post_cutover_live_proof_r1_cleanup_preparation"
    )
    cleanup_guard.main()

    projected = projected_pre_cleanup_ledger(load(LEDGER))
    with tempfile.TemporaryDirectory(prefix="fitnexus-stage32-r1-cleanup-history-") as tmp:
        temp_ledger = Path(tmp) / "migration_ledger_authority.json"
        temp_ledger.write_text(json.dumps(projected, indent=2) + "\n", encoding="utf-8")

        rearm = importlib.import_module("verify_stage32_rearm_repo_only_current_compat")
        original_rearm_ledger = rearm.LEDGER
        rearm.LEDGER = temp_ledger
        try:
            if mode == "current_rearm":
                rearm.main()
            elif mode == "r0_seal":
                compat = importlib.import_module("verify_stage32_rearm_repo_only_workflow_seal_compat")
                original_compat_ledger = compat.LEDGER
                compat.LEDGER = temp_ledger
                try:
                    compat.main()
                finally:
                    compat.LEDGER = original_compat_ledger
            elif mode == "r1_recovery":
                recovery = importlib.import_module("verify_stage32_pre_network_failure_recovery_r1")
                original_recovery_ledger = recovery.LEDGER
                recovery.LEDGER = temp_ledger
                try:
                    recovery.main()
                finally:
                    recovery.LEDGER = original_recovery_ledger
            else:
                historical = importlib.import_module(
                    "verify_stage32_post_cutover_repo_only_historical_compat"
                )
                original_historical_ledger = historical.LEDGER
                historical.LEDGER = temp_ledger
                try:
                    historical.run(mode)
                finally:
                    historical.LEDGER = original_historical_ledger
        finally:
            rearm.LEDGER = original_rearm_ledger

    print("STAGE32_R1_CLEANUP_HISTORICAL_COMPAT=PASS")
    print(f"MODE={mode}")
    print(f"ACTUAL_CURRENT_STATE=POST_CUTOVER_EDGE_RUNTIME_PROOF_R1_VERIFIED_CLEANUP_REPO_ONLY")
    print(f"ACTUAL_CLEANUP_MIGRATION={CLEANUP_NAME}")
    print("ACTUAL_R1_LIVE_PROOF_VERIFIED=true")
    print("ACTUAL_R1_PROOF_REEXECUTION_ALLOWED=false")
    print("PROJECTED_CLEANUP_REMOVED=true")
    print(f"PROJECTED_LEDGER_BASELINE={REARM_REMOTE_BASELINE}")
    print(f"PROJECTED_LEDGER_OBSERVED={REARM_REMOTE_OBSERVED}")
    print("PRODUCTION_ACTIVE_TRANSPORT=edgeGateway")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")
    print("POST_CUTOVER_ROLLBACK_PROOF_REQUIRED=true")
    print("LAUNCH_GATE_PROMOTION=DENIED")


def main() -> None:
    if len(sys.argv) != 2:
        fail(
            "usage: verify_stage32_r1_cleanup_historical_compat.py "
            "<current_rearm|r0_seal|r1_recovery|stage31|rate_limit|valid_route|smoke|rollback>"
        )
    run(sys.argv[1])


if __name__ == "__main__":
    main()
