from __future__ import annotations

import importlib
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
LEDGER = BACKEND / "migration_ledger_authority.json"

REARM_NAME = "stage32_rearm_expired_fixture_r1"
REARM_FAILURE_CLASS = "BGF-SUPABASE-EXECUTE-SQL-READONLY-DML-237"
HISTORICAL_LEDGER_BASELINE = "cd1f4a476ff9b0dc7ea378974a87c254f4bbbc64"
HISTORICAL_LEDGER_OBSERVED = "2026-08-21T17:13:56.735665Z"


def fail(message: str) -> None:
    raise SystemExit("STAGE32_REARM_REPO_ONLY_WORKFLOW_SEAL_COMPAT=FAIL\n" + message)


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to read {path.relative_to(ROOT)}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"expected JSON object: {path.relative_to(ROOT)}")
    return value


def main() -> None:
    # Validate the real current rearm frontier first. This prevents a historical
    # consumed R0 seal from becoming an alternate current authority.
    rearm_guard = importlib.import_module("verify_stage32_rearm_repo_only_current_compat")
    rearm_guard.main()

    ledger = load(LEDGER)
    repo_only = [
        row
        for row in ledger.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    ]
    if len(repo_only) != 1:
        fail("expected exactly one rearm repo_only divergence")
    if repo_only[0].get("name") != REARM_NAME:
        fail("unexpected repo_only migration while preserving R0 seal")
    if repo_only[0].get("related_failure_class") != REARM_FAILURE_CLASS:
        fail("rearm repo_only failure class drifted")

    projected = json.loads(json.dumps(ledger))
    projected["baseline_main_sha"] = HISTORICAL_LEDGER_BASELINE
    projected["observed_at_utc"] = HISTORICAL_LEDGER_OBSERVED
    projected["declared_divergences"] = [
        row
        for row in projected.get("declared_divergences", [])
        if not (
            isinstance(row, dict)
            and row.get("direction") == "repo_only"
            and row.get("name") == REARM_NAME
        )
    ]

    current = importlib.import_module(
        "verify_student_access_stage32_post_cutover_runtime_preparation"
    )
    seal = importlib.import_module("verify_stage32_post_cutover_live_proof_workflow_seal")

    with tempfile.TemporaryDirectory(prefix="fitnexus-stage32-r0-seal-history-") as tmp:
        temp_ledger = Path(tmp) / "migration_ledger_authority.json"
        temp_ledger.write_text(json.dumps(projected, indent=2) + "\n", encoding="utf-8")
        original_ledger = current.LEDGER
        try:
            current.LEDGER = temp_ledger
            seal.main()
        finally:
            current.LEDGER = original_ledger

    print("STAGE32_REARM_REPO_ONLY_WORKFLOW_SEAL_COMPAT=PASS")
    print("HISTORICAL_R0_SEAL_PRESERVED=true")
    print(f"PROJECTED_REARM_REMOVED={REARM_NAME}")
    print("R0_REEXECUTION_ALLOWED=false")
    print("R1_LIVE_PROOF_EXECUTED=false")
    print("PRODUCTION_ACTIVE_TRANSPORT=edgeGateway")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
