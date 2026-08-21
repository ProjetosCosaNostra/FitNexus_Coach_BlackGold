from __future__ import annotations

import importlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
LEDGER = BACKEND / "migration_ledger_authority.json"
FIXTURE_NAME = "stage32_post_cutover_edge_runtime_fixture"
FIXTURE_VERSION = "20260821171334"
FAILURE_CLASS = "BGF-STAGE32-POST-CUTOVER-RUNTIME-FIXTURE-231"
REARM_NAME = "stage32_rearm_expired_fixture_r1"
REARM_FAILURE_CLASS = "BGF-SUPABASE-EXECUTE-SQL-READONLY-DML-237"
HISTORICAL_STAGE31_BASELINE = "05b44ebda7976c679ec8198260def688d1e203f8"
HISTORICAL_STAGE31_OBSERVED = "2026-08-21T16:15:04Z"
MODES = {"stage31", "rate_limit", "valid_route", "smoke", "rollback"}


def fail(message: str) -> None:
    raise SystemExit("STAGE32_POST_CUTOVER_REPO_ONLY_HISTORICAL_COMPAT=FAIL\n" + message)


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to read {path.relative_to(ROOT)}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"expected JSON object: {path.relative_to(ROOT)}")
    return value


def projected_ledger(current: dict) -> tuple[dict, str]:
    repo_only = [
        row
        for row in current.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    ]
    remote = {
        row.get("name"): row.get("version")
        for row in current.get("remote_migrations", [])
        if isinstance(row, dict)
    }

    fixture_is_repo_only = (
        len(repo_only) == 1
        and repo_only[0].get("name") == FIXTURE_NAME
        and repo_only[0].get("related_failure_class") == FAILURE_CLASS
        and FIXTURE_NAME not in remote
        and REARM_NAME not in remote
    )
    fixture_is_remote = remote.get(FIXTURE_NAME) == FIXTURE_VERSION
    rearm_is_repo_only = (
        len(repo_only) == 1
        and repo_only[0].get("name") == REARM_NAME
        and repo_only[0].get("related_failure_class") == REARM_FAILURE_CLASS
        and fixture_is_remote
        and REARM_NAME not in remote
    )
    clean_remote = not repo_only and fixture_is_remote and REARM_NAME not in remote

    if fixture_is_repo_only:
        actual_state = "FIXTURE_REPO_ONLY"
    elif rearm_is_repo_only:
        actual_state = "FIXTURE_REMOTE_REARM_REPO_ONLY"
    elif clean_remote:
        actual_state = "FIXTURE_REMOTE_RECONCILED"
    else:
        fail(
            "Stage32 migration ledger must be exactly fixture-repo-only, fixture-remote, "
            "or fixture-remote plus the single declared rearm repo-only divergence"
        )

    value = json.loads(json.dumps(current))
    value["baseline_main_sha"] = HISTORICAL_STAGE31_BASELINE
    value["observed_at_utc"] = HISTORICAL_STAGE31_OBSERVED
    value["declared_divergences"] = [
        row
        for row in value.get("declared_divergences", [])
        if not (
            isinstance(row, dict)
            and row.get("direction") == "repo_only"
            and row.get("name") in {FIXTURE_NAME, REARM_NAME}
        )
    ]
    value["remote_migrations"] = [
        row
        for row in value.get("remote_migrations", [])
        if not (
            isinstance(row, dict)
            and row.get("name") in {FIXTURE_NAME, REARM_NAME}
        )
    ]
    return value, actual_state


def run(mode: str) -> None:
    if mode not in MODES:
        fail(f"unsupported mode: {mode}")

    ledger = load(LEDGER)
    repo_only_names = {
        row.get("name")
        for row in ledger.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    }

    # Validate the real current lifecycle before constructing a non-authoritative
    # Stage31 projection. When the rearm migration is repository-only, the dedicated
    # compatibility guard removes only that planned divergence before invoking the
    # unchanged Stage32 authority guard.
    if REARM_NAME in repo_only_names:
        current_guard = importlib.import_module(
            "verify_stage32_rearm_repo_only_current_compat"
        )
    else:
        current_guard = importlib.import_module(
            "verify_student_access_stage32_post_cutover_runtime_preparation"
        )
    current_guard.main()

    projected, actual_fixture_state = projected_ledger(ledger)
    with tempfile.TemporaryDirectory(prefix="fitnexus-stage32-post-cutover-historical-") as tmp:
        temp_ledger = Path(tmp) / "migration_ledger_authority.json"
        temp_ledger.write_text(
            json.dumps(projected, indent=2) + "\n",
            encoding="utf-8",
        )

        historical = importlib.import_module(
            "verify_stage31_live_proof_cleanup_reconciliation"
        )
        original_ledger = historical.LEDGER
        try:
            historical.LEDGER = temp_ledger
            historical.run(mode)
        finally:
            historical.LEDGER = original_ledger

    print("STAGE32_POST_CUTOVER_REPO_ONLY_HISTORICAL_COMPAT=PASS")
    print(f"MODE={mode}")
    print(f"ACTUAL_STAGE32_MIGRATION_STATE={actual_fixture_state}")
    print(f"PROJECTED_STAGE32_FIXTURE_REMOVED={FIXTURE_NAME}")
    print(f"PROJECTED_STAGE32_REARM_REMOVED={REARM_NAME}")
    print(f"PROJECTED_LEDGER_BASELINE={HISTORICAL_STAGE31_BASELINE}")
    print(f"PROJECTED_LEDGER_OBSERVED={HISTORICAL_STAGE31_OBSERVED}")
    print("ACTUAL_STAGE32_AUTHORITY_VALIDATED=true")
    print("ACTUAL_PRODUCTION_TRANSPORT=edgeGateway")
    print("PRODUCTION_SINGLETON=StudentAccessTransport.instance")
    print("AUTOMATIC_EDGE_TO_DIRECT_FALLBACK=false")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")
    print("LIVE_POST_CUTOVER_PROOF=NOT_EXECUTED")


def main() -> None:
    if len(sys.argv) != 2:
        fail(
            "usage: verify_stage32_post_cutover_repo_only_historical_compat.py "
            "<stage31|rate_limit|valid_route|smoke|rollback>"
        )
    run(sys.argv[1])


if __name__ == "__main__":
    main()
