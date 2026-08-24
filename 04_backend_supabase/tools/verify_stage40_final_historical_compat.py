from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from stage40_billing_migration_frontier import json_dump, state, to_final

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "04_backend_supabase" / "migration_ledger_authority.json"
FINAL_GUARD = (
    ROOT
    / "04_backend_supabase"
    / "tools"
    / "verify_stage40_billing_production_environment_interlock_final_reconciliation.py"
)
FAILURE_CLASS = "BGF-STAGE52-HISTORICAL-GUARD-FUTURE-MIGRATION-PINNING-489"


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE40_FINAL_HISTORICAL_COMPAT=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\n"
        f"DETAIL={detail}"
    )


def main() -> None:
    original = LEDGER.read_bytes()
    current_kind = "unknown"
    try:
        value = json.loads(original.decode("utf-8"))
        if not isinstance(value, dict):
            fail("migration ledger must be object")
        current_kind = state(value)
        projected = to_final(value)
        LEDGER.write_text(json_dump(projected), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(FINAL_GUARD)],
            cwd=ROOT,
            check=False,
        )
        if result.returncode != 0:
            fail(
                "sealed Stage40 final reconciliation guard failed under "
                f"historical projection: exit={result.returncode}"
            )
    except ValueError as exc:
        fail(str(exc))
    finally:
        LEDGER.write_bytes(original)

    print("STAGE40_FINAL_HISTORICAL_COMPAT=PASS")
    print(f"ACTUAL_STAGE40_FRONTIER={current_kind}")
    print("PROJECTED_FINAL_FRONTIER=true")
    print("CURRENT_LEDGER_MUTATED_PERSISTENTLY=false")
    print("REMOTE_MUTATION=NOT_PERFORMED_BY_GUARD")


if __name__ == "__main__":
    main()
