from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from stage38_billing_migration_frontier import json_dump, state, to_promotion

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "04_backend_supabase" / "migration_ledger_authority.json"
PROMOTION_GUARD = ROOT / "04_backend_supabase" / "tools" / "verify_stage38_billing_evidence_bound_activation_promotion.py"


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE38_PROMOTION_HISTORICAL_COMPAT=FAIL\n"
        "FAILURE_CLASS=BGF-STAGE38-HISTORICAL-GUARD-FUTURE-LEDGER-PINNING-347\n"
        f"DETAIL={detail}"
    )


def main() -> None:
    original = LEDGER.read_bytes()
    try:
        value = json.loads(original.decode("utf-8"))
        if not isinstance(value, dict):
            fail("migration ledger must be a JSON object")
        try:
            current_kind = state(value)
            projected = to_promotion(value)
        except ValueError as exc:
            fail(f"unable to project current ledger to Stage38 promotion frontier: {exc}")

        LEDGER.write_text(json_dump(projected), encoding="utf-8")
        result = subprocess.run([sys.executable, str(PROMOTION_GUARD)], cwd=ROOT, check=False)
        if result.returncode != 0:
            fail(f"sealed Stage38 promotion guard failed under historical projection: exit={result.returncode}")
    finally:
        LEDGER.write_bytes(original)

    print("STAGE38_PROMOTION_HISTORICAL_COMPAT=PASS")
    print(f"ACTUAL_STAGE38_FRONTIER={current_kind}")
    print("PROJECTED_PROMOTION_FRONTIER=true")
    print("CURRENT_LEDGER_MUTATED_PERSISTENTLY=false")
    print("PROVIDER_ACTIVATION=NOT_PERFORMED_BY_GUARD")
    print("PROVIDER_CALL=NOT_PERFORMED_BY_GUARD")


if __name__ == "__main__":
    main()
