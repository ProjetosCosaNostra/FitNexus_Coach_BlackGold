from __future__ import annotations

import importlib
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
LEDGER = BACKEND / "migration_ledger_authority.json"
REARM_NAME = "stage32_rearm_expired_fixture_r1"


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
    # Validate the real current rearm lifecycle first. This prevents the consumed R0
    # seal from becoming an alternate current authority. The compatibility guard also
    # owns the exact projection for either repo-only or remote-reconciled rearm state.
    rearm_guard = importlib.import_module("verify_stage32_rearm_repo_only_current_compat")
    rearm_guard.main()

    ledger = load(LEDGER)
    projected, state = rearm_guard.projected_ledger(ledger)

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
    print(f"ACTUAL_REARM_LEDGER={state}")
    print(f"PROJECTED_REARM_REMOVED={REARM_NAME}")
    print("R0_REEXECUTION_ALLOWED=false")
    print("R1_LIVE_PROOF_EXECUTED=false")
    print("PRODUCTION_ACTIVE_TRANSPORT=edgeGateway")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
