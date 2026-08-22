from __future__ import annotations

import importlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
LEDGER = BACKEND / "migration_ledger_authority.json"

STAGE33_NAME = "stage33_direct_rpc_revocation_and_post_revocation_fixture"
STAGE33_BASELINE = "2f8bd11ac0a4ba4e605807fb17c6c78ff3939041"
STAGE33_OBSERVED = "2026-08-22T02:15:46.465445Z"
STAGE32_BASELINE = "0e7324c47771be2c9c66e3c7bbf05481abea41aa"
STAGE32_OBSERVED = "2026-08-22T00:37:12.866972Z"
WRAPPED_MODES = {
    "cleanup", "current_rearm", "r0_seal", "r1_recovery", "stage31",
    "rate_limit", "valid_route", "smoke", "rollback",
}
MODES = WRAPPED_MODES | {"rollback_prep", "rollback_seal"}


def fail(message: str) -> None:
    raise SystemExit("STAGE33_REVOCATION_HISTORICAL_COMPAT=FAIL\n" + message)


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to read {path.relative_to(ROOT)}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"expected JSON object: {path.relative_to(ROOT)}")
    return value


def project_stage32_ledger(current: dict) -> dict:
    if current.get("baseline_main_sha") != STAGE33_BASELINE:
        fail("Stage33 current ledger baseline drifted")
    if current.get("observed_at_utc") != STAGE33_OBSERVED:
        fail("Stage33 current ledger observation drifted")
    repo_only = [
        row for row in current.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    ]
    if len(repo_only) != 1 or repo_only[0].get("name") != STAGE33_NAME:
        fail("Stage33 migration must be the unique repo-only divergence before proof seal")
    remote = {
        row.get("name"): row.get("version")
        for row in current.get("remote_migrations", []) if isinstance(row, dict)
    }
    if STAGE33_NAME in remote:
        fail("Stage33 migration unexpectedly remote during repo-only promotion")
    if remote.get("stage32_post_cutover_rollback_proof_cleanup") != "20260822003559":
        fail("Stage32 rollback cleanup remote receipt disappeared")

    value = json.loads(json.dumps(current))
    value["baseline_main_sha"] = STAGE32_BASELINE
    value["observed_at_utc"] = STAGE32_OBSERVED
    value["declared_divergences"] = [
        row for row in value.get("declared_divergences", [])
        if not (
            isinstance(row, dict)
            and row.get("direction") == "repo_only"
            and row.get("name") == STAGE33_NAME
        )
    ]
    return value


def run(mode: str) -> None:
    if mode not in MODES:
        fail(f"unsupported mode: {mode}")

    # Never project first: prove the actual current Stage33 authority and repo-only frontier.
    promotion = importlib.import_module(
        "verify_stage33_direct_rpc_revocation_migration_promotion"
    )
    promotion.main()

    projected = project_stage32_ledger(load(LEDGER))
    stage32_wrapper = importlib.import_module("verify_stage32_rollback_fixture_historical_compat")
    rollback_prep = importlib.import_module("verify_stage32_post_cutover_rollback_proof_preparation")
    rollback_seal = importlib.import_module("verify_stage32_post_cutover_rollback_live_proof_workflow_seal")

    with tempfile.TemporaryDirectory(prefix="fitnexus-stage33-history-") as tmp:
        temp_ledger = Path(tmp) / "migration_ledger_authority.json"
        temp_ledger.write_text(json.dumps(projected, indent=2) + "\n", encoding="utf-8")
        original_wrapper_ledger = stage32_wrapper.LEDGER
        original_prep_ledger = rollback_prep.LEDGER
        stage32_wrapper.LEDGER = temp_ledger
        rollback_prep.LEDGER = temp_ledger
        try:
            if mode in WRAPPED_MODES:
                stage32_wrapper.run(mode)
            elif mode == "rollback_prep":
                rollback_prep.main()
            else:
                # The seal guard imports/calls the same rollback preparation module;
                # its global LEDGER is already projected above.
                rollback_seal.main()
        finally:
            stage32_wrapper.LEDGER = original_wrapper_ledger
            rollback_prep.LEDGER = original_prep_ledger

    print("STAGE33_REVOCATION_HISTORICAL_COMPAT=PASS")
    print(f"MODE={mode}")
    print("ACTUAL_STAGE33_STATE=REVOCATION_MIGRATION_REPO_ONLY_PROOF_SEAL_PENDING")
    print(f"ACTUAL_STAGE33_MIGRATION={STAGE33_NAME}")
    print("ACTUAL_STAGE33_REMOTE_APPLIED=false")
    print("PROJECTED_STAGE33_REPO_ONLY_ROW_REMOVED=true")
    print(f"PROJECTED_LEDGER_BASELINE={STAGE32_BASELINE}")
    print(f"PROJECTED_LEDGER_OBSERVED={STAGE32_OBSERVED}")
    print("HISTORICAL_PROOF_REEXECUTION_ALLOWED=false")
    print("REMOTE_PRIVILEGE_REVOCATION=false")
    print("PRODUCTION_ACTIVE_TRANSPORT=edgeGateway")
    print("LAUNCH_GATE_PROMOTION=DENIED")


def main() -> None:
    if len(sys.argv) != 2:
        fail(
            "usage: verify_stage33_revocation_historical_compat.py "
            "<cleanup|current_rearm|r0_seal|r1_recovery|stage31|rate_limit|valid_route|smoke|rollback|rollback_prep|rollback_seal>"
        )
    run(sys.argv[1])


if __name__ == "__main__":
    main()
