from __future__ import annotations

import ast
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


def ast_side_effect_check() -> None:
    if any("stage63" in path.name.lower() for path in MIGRATIONS.glob("*.sql")):
        fail("Stage63 assessment must not introduce a migration")

    tree = ast.parse(GUARD_SOURCE.read_text(encoding="utf-8"), filename=str(GUARD_SOURCE))
    forbidden_modules = {"requests", "subprocess", "supabase"}
    forbidden_calls = {"apply_migration", "execute_sql", "urlopen"}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".", 1)[0] in forbidden_modules:
                    fail(f"Stage63 guard imports forbidden execution module: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            module = (node.module or "").split(".", 1)[0]
            if module in forbidden_modules or (node.module or "").startswith("urllib.request"):
                fail(f"Stage63 guard imports forbidden execution module: {node.module}")
        elif isinstance(node, ast.Call):
            target = node.func
            if isinstance(target, ast.Name) and target.id in forbidden_calls:
                fail(f"Stage63 guard calls forbidden execution function: {target.id}")
            if isinstance(target, ast.Attribute) and target.attr in forbidden_calls:
                fail(f"Stage63 guard calls forbidden execution method: {target.attr}")


if __name__ == "__main__":
    guard.verify_stage52_source = sealed_stage52_source_check
    guard.verify_no_stage63_migration_or_side_effect_tooling = ast_side_effect_check
    guard.main()
