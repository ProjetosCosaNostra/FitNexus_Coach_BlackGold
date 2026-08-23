from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from stage35_migration_frontier import json_dump, to_final

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "04_backend_supabase" / "migration_ledger_authority.json"
FINAL_GUARD = ROOT / "04_backend_supabase" / "tools" / "verify_stage35_external_delivery_cleanup_final_reconciliation.py"


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE35_FINAL_RECONCILIATION_HISTORICAL_COMPAT=FAIL\n"
        "FAILURE_CLASS=BGF-STAGE35-HISTORICAL-GUARD-FUTURE-LEDGER-PINNING-346\n"
        f"DETAIL={detail}"
    )


def main() -> None:
    original = LEDGER.read_bytes()
    try:
        value = json.loads(original.decode("utf-8"))
        if not isinstance(value, dict):
            fail("migration ledger must be a JSON object")
        try:
            projected = to_final(value)
        except ValueError as exc:
            fail(f"unable to project current ledger to sealed Stage35 final frontier: {exc}")

        LEDGER.write_text(json_dump(projected), encoding="utf-8")
        result = subprocess.run([sys.executable, str(FINAL_GUARD)], cwd=ROOT, check=False)
        if result.returncode != 0:
            fail(f"sealed Stage35 final guard failed under historical projection: exit={result.returncode}")
    finally:
        LEDGER.write_bytes(original)

    print("STAGE35_FINAL_RECONCILIATION_HISTORICAL_COMPAT=PASS")
    print("CURRENT_LEDGER_MUTATED_PERSISTENTLY=false")
    print("SEALED_STAGE35_FINAL_GUARD=PASS_UNDER_PROJECTED_FRONTIER")


if __name__ == "__main__":
    main()
