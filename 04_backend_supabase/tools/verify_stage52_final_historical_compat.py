from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from stage52_student_issuance_migration_frontier import (
    FINAL_BASELINE,
    FINAL_OBSERVED,
    FINAL_SOURCE,
    clone,
    divergences,
    json_dump,
    state,
)

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "04_backend_supabase" / "migration_ledger_authority.json"
FINAL_GUARD = ROOT / "04_backend_supabase" / "tools" / "verify_stage52_student_issuance_target_privacy_final_reconciliation.py"
FAILURE_CLASS = "BGF-STAGE53-STAGE52-FINAL-HISTORICAL-GUARD-FUTURE-LEDGER-PINNING-499"


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE52_FINAL_HISTORICAL_COMPAT=FAIL\n"
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
        if current_kind not in {"final", "post_final"}:
            fail(f"cannot project Stage52 final from frontier={current_kind}")

        projected = clone(value)
        projected["baseline_main_sha"] = FINAL_BASELINE
        projected["observed_at_utc"] = FINAL_OBSERVED
        projected["source"] = FINAL_SOURCE
        remote_only, _repo_only = divergences(projected)
        # A sealed historical final frontier must not inherit later repo-only
        # migration declarations. They belong to future stages and are removed
        # only from this temporary local projection.
        projected["declared_divergences"] = remote_only
        if state(projected) != "final":
            fail("projected ledger did not resolve to exact Stage52 final frontier")

        LEDGER.write_text(json_dump(projected), encoding="utf-8")
        result = subprocess.run([sys.executable, str(FINAL_GUARD)], cwd=ROOT, check=False)
        if result.returncode != 0:
            fail(f"sealed Stage52 final guard failed under historical projection: exit={result.returncode}")
    except (ValueError, json.JSONDecodeError) as exc:
        fail(str(exc))
    finally:
        LEDGER.write_bytes(original)

    print("STAGE52_FINAL_HISTORICAL_COMPAT=PASS")
    print(f"ACTUAL_STAGE52_FRONTIER={current_kind}")
    print("PROJECTED_STAGE52_FINAL_FRONTIER=true")
    print("FUTURE_REPO_ONLY_DECLARATIONS_DROPPED_IN_PROJECTION=true")
    print("CURRENT_LEDGER_MUTATED_PERSISTENTLY=false")
    print("REMOTE_MUTATION=false")


if __name__ == "__main__":
    main()
