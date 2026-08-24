from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from stage52_student_issuance_migration_frontier import (
    PROMOTION_REPO_ONLY,
    clone,
    divergences,
    json_dump,
    state,
    to_promotion,
)

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "04_backend_supabase" / "migration_ledger_authority.json"
PROMOTION_GUARD = ROOT / "04_backend_supabase" / "tools" / "verify_stage52_student_issuance_target_privacy_promotion.py"
FAILURE_CLASS = "BGF-STAGE52-PROMOTION-HISTORICAL-GUARD-FUTURE-LEDGER-PINNING-492"


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE52_PROMOTION_HISTORICAL_COMPAT=FAIL\n"
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
        projected = to_promotion(value)
        remote_only, _repo_only = divergences(projected)
        projected["declared_divergences"] = remote_only + [clone(PROMOTION_REPO_ONLY)]
        if state(projected) != "promotion":
            fail("projected ledger is not exact Stage52 promotion frontier")
        LEDGER.write_text(json_dump(projected), encoding="utf-8")
        result = subprocess.run([sys.executable, str(PROMOTION_GUARD)], cwd=ROOT, check=False)
        if result.returncode != 0:
            fail(f"sealed Stage52 promotion guard failed under historical projection: exit={result.returncode}")
    except (ValueError, json.JSONDecodeError) as exc:
        fail(str(exc))
    finally:
        LEDGER.write_bytes(original)

    print("STAGE52_PROMOTION_HISTORICAL_COMPAT=PASS")
    print(f"ACTUAL_STAGE52_FRONTIER={current_kind}")
    print("PROJECTED_PROMOTION_FRONTIER=true")
    print("FUTURE_REPO_ONLY_DECLARATIONS_DROPPED_IN_PROJECTION=true")
    print("CURRENT_LEDGER_MUTATED_PERSISTENTLY=false")
    print("REMOTE_MUTATION=NOT_PERFORMED_BY_GUARD")


if __name__ == "__main__":
    main()
