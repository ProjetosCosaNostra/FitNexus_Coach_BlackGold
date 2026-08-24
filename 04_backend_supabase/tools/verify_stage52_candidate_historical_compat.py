from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
MIGRATION = BACKEND / "migrations/20260824203000_stage52_student_issuance_target_privacy_hardening.sql"
HIDDEN = BACKEND / ".stage52_student_issuance_target_privacy_hardening.promotion-hidden"
CANDIDATE_GUARD = BACKEND / "tools/verify_stage52_student_issuance_target_privacy_candidate.py"
FAILURE_CLASS = "BGF-STAGE52-HISTORICAL-GUARD-FUTURE-MIGRATION-PINNING-489"


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE52_CANDIDATE_HISTORICAL_COMPAT=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\n"
        f"DETAIL={detail}"
    )


def main() -> None:
    if HIDDEN.exists():
        fail("historical projection scratch path already exists")

    migration_present = MIGRATION.exists()
    try:
        if migration_present:
            MIGRATION.rename(HIDDEN)
        result = subprocess.run(
            [sys.executable, str(CANDIDATE_GUARD)],
            cwd=ROOT,
            check=False,
        )
        if result.returncode != 0:
            fail(f"sealed Stage52 candidate guard failed under historical projection: exit={result.returncode}")
    finally:
        if HIDDEN.exists():
            HIDDEN.rename(MIGRATION)

    if migration_present and not MIGRATION.exists():
        fail("promotion migration was not restored after historical projection")
    if HIDDEN.exists():
        fail("historical projection scratch residue remained")

    print("STAGE52_CANDIDATE_HISTORICAL_COMPAT=PASS")
    print(f"PROMOTION_MIGRATION_PRESENT={str(migration_present).lower()}")
    print("PROJECTED_CANDIDATE_FRONTIER=true")
    print("PROMOTION_MIGRATION_RESTORED=true")
    print("CURRENT_REPOSITORY_MUTATED_PERSISTENTLY=false")
    print("REMOTE_MUTATION=false")


if __name__ == "__main__":
    main()
