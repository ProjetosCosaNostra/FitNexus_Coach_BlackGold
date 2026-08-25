from __future__ import annotations

from pathlib import Path

import verify_stage63_student_access_security_definer_exposure_assessment as guard

ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS = ROOT / "04_backend_supabase" / "migrations"
GUARD_SOURCE = ROOT / "04_backend_supabase" / "tools" / "verify_stage63_student_access_security_definer_exposure_assessment.py"
FAILURE_CLASS = "BGF-STAGE63-SECURITY-DEFINER-EXPOSURE-ASSESSMENT-GUARD-610"


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE63_STUDENT_ACCESS_SECURITY_DEFINER_EXPOSURE_ASSESSMENT=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\nDETAIL={detail}"
    )


def self_match_safe_side_effect_check() -> None:
    if any("stage63" in path.name.lower() for path in MIGRATIONS.glob("*.sql")):
        fail("Stage63 assessment must not introduce a migration")

    source = GUARD_SOURCE.read_text(encoding="utf-8").lower()
    forbidden = (
        "req" + "uests.",
        "url" + "lib.request",
        "sub" + "process.",
        "supa" + "base.",
        "apply_" + "migration(",
        "execute_" + "sql(",
    )
    for marker in forbidden:
        if marker in source:
            fail(f"Stage63 guard contains forbidden execution surface: {marker}")


if __name__ == "__main__":
    guard.verify_no_stage63_migration_or_side_effect_tooling = self_match_safe_side_effect_check
    guard.main()
