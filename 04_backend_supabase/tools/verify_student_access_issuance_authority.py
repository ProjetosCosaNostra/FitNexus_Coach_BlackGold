from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MIGRATION = (
    ROOT
    / "04_backend_supabase"
    / "migrations"
    / "20260819105200_stage21_student_access_issuance_authority_hardening.sql"
)


def fail(detail: str) -> None:
    raise SystemExit(
        "STUDENT_ACCESS_ISSUANCE_AUTHORITY_GUARD=FAIL\n"
        "FAILURE_CLASS=BGF-STUDENT-ACCESS-ISSUANCE-AUTHORITY-153\n"
        f"DETAIL={detail}"
    )


def main() -> None:
    if not MIGRATION.exists():
        fail("issuance authority hardening migration is missing")

    text = MIGRATION.read_text(encoding="utf-8").lower()
    required = (
        "if auth.uid() is null then",
        "select s.organization_id into v_org",
        "if not private.is_org_manager(v_org) then",
        "and l.organization_id = v_org",
        "v_token := public.issue_student_access_token(p_student_id)",
        "expires_at = now() + interval '30 days'",
    )
    for needle in required:
        if needle not in text:
            fail(f"required issuance-authority invariant disappeared: {needle}")

    auth_pos = text.find("if auth.uid() is null then")
    manager_pos = text.find("if not private.is_org_manager(v_org) then")
    rotation_lookup_pos = text.find("select l.id, l.rotation_number")
    legacy_call_pos = text.find("v_token := public.issue_student_access_token(p_student_id)")

    if min(auth_pos, manager_pos, rotation_lookup_pos, legacy_call_pos) < 0:
        fail("could not resolve issuance authority ordering")

    if not (auth_pos < manager_pos < rotation_lookup_pos < legacy_call_pos):
        fail(
            "authorization must happen before rotation-state lookup, and the mature v1 mutation may only be called after that"
        )

    print("STUDENT_ACCESS_ISSUANCE_AUTHORITY_GUARD=PASS")
    print("AUTH_BEFORE_ROTATION_LOOKUP=PASS")
    print("MANAGER_BEFORE_ROTATION_LOOKUP=PASS")
    print("V1_MUTATION_AFTER_V2_AUTHORITY=PASS")


if __name__ == "__main__":
    main()
