from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage52_student_issuance_target_privacy_promotion_authority.json"
CANDIDATE_AUTHORITY = BACKEND / "stage52_student_issuance_target_privacy_candidate_authority.json"
LEDGER = BACKEND / "migration_ledger_authority.json"
CANDIDATE = BACKEND / "operations/stage52_student_issuance_target_privacy_candidate.sql"
MIGRATION = BACKEND / "migrations/20260824203000_stage52_student_issuance_target_privacy_hardening.sql"

BASELINE_MAIN = "b5f466ef09dd027f10c88d3d13726f3d7c0281ba"
OBSERVED_AT = "2026-08-24T20:27:07.829322+00:00"
NAME = "stage52_student_issuance_target_privacy_hardening"
EXPECTED_BLOB = "80529ec11b923d83d10e01bb846ed284d34442f6"
FAILURE_CLASS = "BGF-STAGE52-PROMOTION-GUARD-491"


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE52_STUDENT_ISSUANCE_TARGET_PRIVACY_PROMOTION=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\n"
        f"DETAIL={detail}"
    )


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to load {path.relative_to(ROOT)}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"expected JSON object: {path.relative_to(ROOT)}")
    return value


def require(mapping: dict, expected: dict, label: str) -> None:
    if not isinstance(mapping, dict):
        fail(f"{label} must be an object")
    for key, value in expected.items():
        if mapping.get(key) != value:
            fail(f"{label} drift: {key}; expected={value!r}; actual={mapping.get(key)!r}")


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def executable_sql(text: str) -> str:
    marker = "create or replace function public.issue_student_access_token_v2"
    index = text.lower().find(marker)
    if index < 0:
        fail("issuance function definition missing")
    return text[index:]


def main() -> None:
    authority = load(AUTHORITY)
    candidate_authority = load(CANDIDATE_AUTHORITY)
    ledger = load(LEDGER)

    if not CANDIDATE.is_file() or not MIGRATION.is_file():
        fail("candidate or promoted migration missing")
    if CANDIDATE.read_bytes() != MIGRATION.read_bytes():
        fail("versioned migration is not byte-identical to merged Stage52 candidate")
    if git_blob_sha(CANDIDATE) != EXPECTED_BLOB or git_blob_sha(MIGRATION) != EXPECTED_BLOB:
        fail("candidate/migration blob drifted")

    require(authority, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE52_STUDENT_ISSUANCE_TARGET_PRIVACY_PROMOTION",
        "baseline_main_sha": BASELINE_MAIN,
        "current_state": "REPO_ONLY_VERSIONED_MIGRATION_EXACT_CANDIDATE_NO_REMOTE_APPLY",
    }, "promotion authority")

    require(candidate_authority, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE52_STUDENT_ISSUANCE_TARGET_PRIVACY_CANDIDATE",
        "current_state": "REPO_ONLY_CANDIDATE_EXISTENCE_ORACLE_CLOSED_IN_SOURCE_NOT_REMOTE",
    }, "candidate authority")
    if git_blob_sha(CANDIDATE_AUTHORITY) != "bf4d008eb47e01ffece455f9bac3d6528bb4d74a":
        fail("sealed Stage52 candidate authority blob drifted")

    require(authority.get("candidate", {}), {
        "file": "04_backend_supabase/operations/stage52_student_issuance_target_privacy_candidate.sql",
        "git_blob_sha": EXPECTED_BLOB,
        "already_green_merged": True,
        "merged_by_pr": 139,
        "merged_main_sha": BASELINE_MAIN,
    }, "candidate pin")
    require(authority.get("migration", {}), {
        "name": NAME,
        "file": "04_backend_supabase/migrations/20260824203000_stage52_student_issuance_target_privacy_hardening.sql",
        "git_blob_sha": EXPECTED_BLOB,
        "exact_candidate_blob_reused": True,
        "repo_only": True,
        "remote_apply_count": 0,
        "apply_allowed_before_green_merge": False,
        "apply_method_after_green_merge": "Supabase.apply_migration",
        "execute_sql_for_dml_or_ddl_allowed": False,
    }, "migration promotion")

    require(authority.get("fresh_remote_preflight", {}), {
        "source": "Supabase.list_migrations+Supabase.execute_sql_read_only",
        "observed_at_utc": OBSERVED_AT,
        "stage52_remote_migration_present": False,
        "auth_users": 0,
        "organizations": 0,
        "students": 0,
        "v2_security_definer": True,
        "v2_anon_execute": False,
        "v2_authenticated_execute": True,
        "v2_service_role_execute": True,
        "v1_anon_execute": False,
        "v1_authenticated_execute": False,
        "v1_service_role_execute": True,
        "remote_contains_student_not_found": True,
        "remote_contains_org_manager_required": True,
        "remote_contains_target_unavailable": False,
        "remote_contains_combined_membership_join": False,
        "remote_mutation_performed": False,
        "customer_data_used": False,
    }, "fresh remote preflight")

    require(ledger, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "baseline_main_sha": BASELINE_MAIN,
        "observed_at_utc": "2026-08-24T20:27:07.829322Z",
        "source": "Supabase.list_migrations+Supabase.execute_sql",
        "comparison_key": "migration_name",
    }, "migration ledger")

    divergences = ledger.get("declared_divergences", [])
    if not isinstance(divergences, list):
        fail("declared_divergences must be array")
    remote_only = sorted(
        row.get("name") for row in divergences
        if isinstance(row, dict) and row.get("direction") == "remote_only"
    )
    repo_only_rows = [
        row for row in divergences
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    ]
    if remote_only != [
        "stage17_pricing_advisor_guard",
        "stage17_pricing_advisor_reconciliation",
        "stage17_pricing_guard_indexes_marker",
    ]:
        fail("historical Stage17 remote-only frontier drifted")
    if len(repo_only_rows) != 1 or repo_only_rows[0].get("name") != NAME:
        fail("Stage52 must be the unique repo-only migration divergence")
    if repo_only_rows[0].get("related_failure_class") != "BGF-STAGE52-CANDIDATE-DIRECT-APPLY-485":
        fail("Stage52 repo-only divergence prevention class drifted")

    remote_rows = ledger.get("remote_migrations", [])
    if not isinstance(remote_rows, list) or len(remote_rows) != 65:
        fail("remote migration frontier count drifted")
    remote_names = [row.get("name") for row in remote_rows if isinstance(row, dict)]
    if NAME in remote_names:
        fail("promotion ledger must not claim Stage52 was remotely applied")
    if remote_names.count("stage40_billing_production_environment_interlock") != 1:
        fail("Stage40 remote frontier missing or duplicated")

    executable = executable_sql(MIGRATION.read_text(encoding="utf-8"))
    lower = executable.lower()
    required = (
        "if auth.uid() is null then",
        "from public.students s",
        "join public.organization_members m",
        "m.organization_id = s.organization_id",
        "m.user_id = (select auth.uid())",
        "m.role in ('owner', 'admin')",
        "where s.id = p_student_id",
        "message = 'student_access_target_unavailable'",
        "student_access_rotation_cooldown",
        "v_token := public.issue_student_access_token(p_student_id)",
        "extensions.digest(v_token, 'sha256')",
        "expires_at = now() + interval '30 days'",
        "insert into private.student_access_security_events",
        "revoke all on function public.issue_student_access_token_v2(uuid) from public, anon",
        "grant execute on function public.issue_student_access_token_v2(uuid) to authenticated",
    )
    for fragment in required:
        if fragment not in lower:
            fail(f"required privacy/issuance invariant missing: {fragment}")

    forbidden = (
        "message = 'student_not_found'",
        "message = 'org_manager_required'",
        "if not private.is_org_manager(v_org) then",
        "grant execute on function public.issue_student_access_token_v2(uuid) to anon",
    )
    for fragment in forbidden:
        if fragment in lower:
            fail(f"promoted executable retained forbidden oracle/exposure fragment: {fragment}")

    auth_pos = lower.find("if auth.uid() is null then")
    target_pos = lower.find("from public.students s")
    error_pos = lower.find("message = 'student_access_target_unavailable'")
    rotation_pos = lower.find("select l.id, l.rotation_number")
    v1_pos = lower.find("v_token := public.issue_student_access_token(p_student_id)")
    if not (0 <= auth_pos < target_pos < error_pos < rotation_pos < v1_pos):
        fail("promotion changed authority/rotation ordering")

    require(authority.get("promotion_boundaries", {}), {
        "supabase_mutation_performed": False,
        "live_cross_tenant_exploit_performed": False,
        "real_customer_data_used": False,
        "privilege_change_performed": False,
        "deployment_action_performed": False,
        "production_deployment_promoted": False,
        "incident_response_promoted": False,
        "controlled_launch_promoted": False,
        "paid_media_promoted": False,
        "launch_promoted": False,
    }, "promotion boundaries")

    require(authority.get("gates", {}), {
        "stage52_migration_promotion": "PENDING_CI",
        "stage52_remote_apply": "DENIED_UNTIL_GREEN_EXACT_MERGE",
        "security_advisor_reconciliation": "PASS_INTENTIONAL_AUTHENTICATED_MANAGER_WRAPPER",
        "production_deployment": "DENIED",
        "incident_response": "DENIED",
        "controlled_launch": "DENIED",
        "paid_media": "DENIED",
        "launch": "DENIED",
    }, "gates")

    stage52_migrations = list((BACKEND / "migrations").glob("*stage52*.sql"))
    if stage52_migrations != [MIGRATION]:
        fail("unexpected Stage52 migration set")

    print("STAGE52_STUDENT_ISSUANCE_TARGET_PRIVACY_PROMOTION=PASS")
    print(f"BASELINE_MAIN_SHA={BASELINE_MAIN}")
    print(f"MIGRATION_BLOB={EXPECTED_BLOB}")
    print("EXACT_CANDIDATE_BLOB_REUSED=PASS")
    print("UNAUTHORIZED_NOTFOUND_ERROR_EQUIVALENCE=PASS")
    print("AUTHENTICATED_MANAGER_BOUNDARY=PRESERVED")
    print("STAGE52_LEDGER_STATE=REPO_ONLY")
    print("REMOTE_APPLY_ALLOWED=false_until_green_exact_merge")
    print("REMOTE_MUTATION=false")


if __name__ == "__main__":
    main()
