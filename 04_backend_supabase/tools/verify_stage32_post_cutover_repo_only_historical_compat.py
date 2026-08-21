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
FAILURE_CLASS = "BGF-STAGE32-POST-CUTOVER-RUNTIME-FIXTURE-231"
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


def projected_ledger(current: dict) -> dict:
    repo_only = [
        row
        for row in current.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    ]
    if len(repo_only) != 1 or repo_only[0].get("name") != FIXTURE_NAME:
        fail("Stage 32 fixture is not the unique repository-only divergence")
    if repo_only[0].get("related_failure_class") != FAILURE_CLASS:
        fail("Stage 32 fixture divergence failure-class authority drifted")

    value = json.loads(json.dumps(current))
    value["declared_divergences"] = [
        row
        for row in value.get("declared_divergences", [])
        if not (
            isinstance(row, dict)
            and row.get("direction") == "repo_only"
            and row.get("name") == FIXTURE_NAME
        )
    ]
    return value


def run(mode: str) -> None:
    if mode not in MODES:
        fail(f"unsupported mode: {mode}")

    current_guard = importlib.import_module(
        "verify_student_access_stage32_post_cutover_runtime_preparation"
    )
    current_guard.main()

    ledger = load(LEDGER)
    with tempfile.TemporaryDirectory(prefix="fitnexus-stage32-post-cutover-historical-") as tmp:
        temp_ledger = Path(tmp) / "migration_ledger_authority.json"
        temp_ledger.write_text(
            json.dumps(projected_ledger(ledger), indent=2) + "\n",
            encoding="utf-8",
        )

        historical = importlib.import_module(
            "verify_stage31_live_proof_cleanup_reconciliation"
        )
        historical.LEDGER = temp_ledger
        historical.run(mode)

    print("STAGE32_POST_CUTOVER_REPO_ONLY_HISTORICAL_COMPAT=PASS")
    print(f"MODE={mode}")
    print(f"PROJECTED_REPO_ONLY_REMOVED={FIXTURE_NAME}")
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
