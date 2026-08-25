from __future__ import annotations

from pathlib import Path

import verify_stage63_student_access_security_definer_exposure_assessment as guard

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
MIGRATIONS = BACKEND / "migrations"
GUARD_SOURCE = BACKEND / "tools" / "verify_stage63_student_access_security_definer_exposure_assessment.py"
STAGE52_MIGRATION = BACKEND / "migrations" / "20260824203000_stage52_student_issuance_target_privacy_hardening.sql"
FAILURE_CLASS = "BGF-STAGE63-SECURITY-DEFINER-EXPOSURE-ASSESSMENT-GUARD-610"


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE63_STUDENT_ACCESS_SECURITY_DEFINER_EXPOSURE_ASSESSMENT=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\nDETAIL={detail}"
    )


def sealed_stage52_source_check() -> None:
    source = STAGE52_MIGRATION.read_text(encoding="utf-8")
    required = (
        "security definer",
        "set search_path = ''",
        "if auth.uid() is null then",
        "join public.organization_members m",
        "and m.user_id = (select auth.uid())",
        "and m.role in ('owner', 'admin')",
        "message = 'STUDENT_ACCESS_TARGET_UNAVAILABLE'",
        "v_token := public.issue_student_access_token(p_student_id);",
        "and l.student_id = p_student_id",
        "and l.organization_id = v_org",
        "revoke all on function public.issue_student_access_token_v2(uuid) from public, anon;",
        "grant execute on function public.issue_student_access_token_v2(uuid) to authenticated;",
    )
    lower = source.lower()
    for marker in required:
        if marker.lower() not in lower:
            fail(f"sealed Stage52 hardening marker missing: {marker}")
    body_start = lower.find("create or replace function public.issue_student_access_token_v2")
    body_end = lower.find("revoke all on function public.issue_student_access_token_v2", body_start)
    if body_start < 0 or body_end < 0:
        fail("unable to isolate Stage52 hardened function body")
    body = lower[body_start:body_end]
    if "message = 'student_not_found'" in body or "message = 'org_manager_required'" in body:
        fail("Stage52 hardened function body reintroduced distinguishable target errors")


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
    guard.verify_stage52_source = sealed_stage52_source_check
    guard.verify_no_stage63_migration_or_side_effect_tooling = self_match_safe_side_effect_check
    guard.main()
