from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage52_student_issuance_target_privacy_candidate_authority.json"
CANDIDATE = BACKEND / "operations/stage52_student_issuance_target_privacy_candidate.sql"
STAGE21 = BACKEND / "migrations/20260819105200_stage21_student_access_issuance_authority_hardening.sql"
STAGE51_AUTHORITY = BACKEND / "stage51_security_definer_advisor_reconciliation_authority.json"
STAGE51_GUARD = BACKEND / "tools/verify_stage51_security_definer_advisor_reconciliation.py"
PROFESSOR_REPOSITORY = (
    ROOT
    / "03_app_flutter/fitnexus_app/lib/features/professor/professor_data_repository.dart"
)
MIGRATIONS = BACKEND / "migrations"

FAILURE_CLASS = "BGF-STAGE52-STUDENT-ISSUANCE-TARGET-PRIVACY-GUARD-487"
EXPECTED_BASELINE = "9cbb05aed21e14ce1ff1b25efd2ceea14094a0ea"
EXPECTED_STATE = "REPO_ONLY_CANDIDATE_EXISTENCE_ORACLE_CLOSED_IN_SOURCE_NOT_REMOTE"
EXPECTED_FAILURE_CLASSES = {
    "BGF-STAGE52-AUTHENTICATED-STUDENT-ID-EXISTENCE-ORACLE-481",
    "BGF-STAGE52-TARGET-LOOKUP-BEFORE-AUTHORITY-482",
    "BGF-STAGE52-DISTINCT-UNAUTHORIZED-NOTFOUND-ERROR-483",
    "BGF-STAGE52-ISSUANCE-AUTHORITY-REGRESSION-484",
    "BGF-STAGE52-CANDIDATE-DIRECT-APPLY-485",
    "BGF-STAGE52-CLIENT-ERROR-CONTRACT-DEPENDENCY-486",
    FAILURE_CLASS,
}


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE52_STUDENT_ISSUANCE_TARGET_PRIVACY_CANDIDATE=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\n"
        f"DETAIL={detail}"
    )


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to read JSON {path.name}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"JSON root must be object: {path.name}")
    return value


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def require(text: str, needle: str, detail: str) -> None:
    if needle not in text:
        fail(detail)


def forbid(text: str, needle: str, detail: str) -> None:
    if needle in text:
        fail(detail)


def verify_authority() -> dict:
    authority = load_json(AUTHORITY)
    if authority.get("schema_version") != 1:
        fail("schema_version drift")
    if authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("project_ref drift")
    if authority.get("stage") != "STAGE52_STUDENT_ISSUANCE_TARGET_PRIVACY_CANDIDATE":
        fail("stage id drift")
    if authority.get("baseline_main_sha") != EXPECTED_BASELINE:
        fail("baseline main SHA drift")
    if authority.get("current_state") != EXPECTED_STATE:
        fail("current state drift")
    if set(authority.get("failure_classes", [])) != EXPECTED_FAILURE_CLASSES:
        fail("failure-class registry drift")

    problem = authority.get("problem_statement", {})
    if problem.get("student_identifier_existence_oracle_structurally_proven") is not True:
        fail("structural oracle finding missing")
    if problem.get("token_issuance_authorization_bypass_proven") is not False:
        fail("Stage52 must not overstate token-issuance bypass")
    if problem.get("live_cross_tenant_exploit_performed") is not False:
        fail("Stage52 must remain non-exploitative")
    if problem.get("real_customer_data_used") is not False:
        fail("real customer data use is forbidden")

    expected_pins = {
        "stage21_issuance_authority_migration": (STAGE21, "7a15f40b936c137c86735783179b1df4b6bc663d"),
        "stage51_advisor_reconciliation_authority": (STAGE51_AUTHORITY, "e2d90eb485d0e6eea68dee05533ff9b762f9f982"),
        "stage51_advisor_reconciliation_guard": (STAGE51_GUARD, "117459b8311168db417368c431097b56c4ec2710"),
        "candidate_sql": (CANDIDATE, "80529ec11b923d83d10e01bb846ed284d34442f6"),
    }
    sealed = authority.get("sealed_inputs", {})
    for key, (path, expected_sha) in expected_pins.items():
        row = sealed.get(key)
        if not isinstance(row, dict):
            fail(f"sealed input missing: {key}")
        if row.get("path") != str(path.relative_to(ROOT)).replace("\\", "/"):
            fail(f"sealed path drift: {key}")
        if row.get("git_blob_sha") != expected_sha or git_blob_sha(path) != expected_sha:
            fail(f"sealed blob drift: {key}")

    remote = authority.get("fresh_remote_read_only_receipt", {})
    expected_remote = {
        "observed_at_utc": "2026-08-24T20:16:14.137748+00:00",
        "auth_users": 0,
        "organizations": 0,
        "v2_security_definer": True,
        "v2_anon_execute": False,
        "v2_authenticated_execute": True,
        "v2_service_role_execute": True,
        "remote_student_lookup_precedes_manager_check": True,
        "remote_student_not_found_marker": True,
        "remote_org_manager_required_marker": True,
        "remote_distinct_target_errors_present": True,
        "manager_helper_uses_auth_uid": True,
        "manager_helper_requires_owner_or_admin": True,
        "remote_mutation_performed": False,
    }
    for key, expected in expected_remote.items():
        if remote.get(key) != expected:
            fail(f"remote read-only receipt drift: {key}")

    contract = authority.get("candidate_contract", {})
    required_true = {
        "candidate_is_operations_sql_only",
        "authenticated_execute_preserved",
        "anon_execute_denied",
        "security_definer_preserved",
        "auth_uid_required_before_target_lookup",
        "student_lookup_and_manager_authority_coalesced",
        "unauthorized_and_nonexistent_target_share_single_error",
        "historical_student_not_found_error_removed_from_candidate",
        "historical_org_manager_required_error_removed_from_candidate",
        "rotation_state_read_after_authorized_target_resolution",
        "rotation_cooldown_preserved",
        "mature_v1_call_after_authority_preserved",
        "token_hash_lookup_preserved",
        "thirty_day_expiry_preserved",
        "previous_link_revocation_preserved",
        "security_event_insert_preserved",
    }
    for key in required_true:
        if contract.get(key) is not True:
            fail(f"candidate invariant missing: {key}")
    for key in {
        "candidate_is_versioned_migration",
        "candidate_is_remote_apply_authority",
        "raw_token_storage_added",
        "flutter_client_specific_error_dependency_found",
    }:
        if contract.get(key) is not False:
            fail(f"forbidden candidate state enabled: {key}")
    if contract.get("single_target_error") != "STUDENT_ACCESS_TARGET_UNAVAILABLE":
        fail("single target error drift")
    if set(contract.get("manager_roles", [])) != {"owner", "admin"}:
        fail("manager role set drift")

    protocol = authority.get("promotion_protocol", {})
    if protocol.get("next_step_if_candidate_green") != "SEPARATE_VERSIONED_MIGRATION_PROMOTION_PR":
        fail("promotion next-step drift")
    for key in {
        "direct_operations_candidate_apply_allowed",
        "execute_sql_dml_or_ddl_allowed",
        "remote_apply_before_versioned_migration_green_merge_allowed",
        "live_cross_tenant_test_with_real_customer_data_allowed",
    }:
        if protocol.get(key) is not False:
            fail(f"forbidden promotion surface enabled: {key}")
    return authority


def verify_historical_oracle() -> None:
    text = STAGE21.read_text(encoding="utf-8").lower()
    student_lookup = text.find("select s.organization_id into v_org")
    not_found = text.find("message = 'student_not_found'")
    manager = text.find("if not private.is_org_manager(v_org) then")
    manager_error = text.find("message = 'org_manager_required'")
    rotation = text.find("select l.id, l.rotation_number")
    if min(student_lookup, not_found, manager, manager_error, rotation) < 0:
        fail("historical Stage21 oracle markers no longer resolvable")
    if not (student_lookup < not_found < manager < manager_error < rotation):
        fail("historical Stage21 target/error ordering drift")


def verify_candidate_sql() -> None:
    text = CANDIDATE.read_text(encoding="utf-8").lower()
    required = (
        "stage52 operations candidate only",
        "create or replace function public.issue_student_access_token_v2(p_student_id uuid)",
        "security definer",
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
        "l.token_hash = extensions.digest(v_token, 'sha256')",
        "expires_at = now() + interval '30 days'",
        "rotated_from_link_id = v_previous_id",
        "insert into private.student_access_security_events",
        "revoke all on function public.issue_student_access_token_v2(uuid) from public, anon",
        "grant execute on function public.issue_student_access_token_v2(uuid) to authenticated",
    )
    for needle in required:
        require(text, needle, f"candidate lost required invariant: {needle}")

    forbid(text, "message = 'student_not_found'", "candidate retained distinguishable STUDENT_NOT_FOUND")
    forbid(text, "message = 'org_manager_required'", "candidate retained distinguishable ORG_MANAGER_REQUIRED")
    forbid(text, "if not private.is_org_manager(v_org) then", "candidate retained split target lookup / manager error branch")

    auth = text.find("if auth.uid() is null then")
    target = text.find("from public.students s")
    generic = text.find("message = 'student_access_target_unavailable'")
    rotation = text.find("select l.id, l.rotation_number")
    v1_call = text.find("v_token := public.issue_student_access_token(p_student_id)")
    if min(auth, target, generic, rotation, v1_call) < 0:
        fail("candidate ordering markers missing")
    if not (auth < target < generic < rotation < v1_call):
        fail("candidate authority/rotation ordering is unsafe")


def verify_client_compatibility() -> None:
    text = PROFESSOR_REPOSITORY.read_text(encoding="utf-8")
    if "'issue_student_access_token_v2'" not in text:
        fail("professor client no longer calls v2 issuance boundary")
    for marker in (
        "STUDENT_NOT_FOUND",
        "ORG_MANAGER_REQUIRED",
        "STUDENT_ACCESS_TARGET_UNAVAILABLE",
    ):
        if marker in text:
            fail(f"Flutter client has specific SQL error dependency: {marker}")


def verify_repo_only_boundary() -> None:
    if list(MIGRATIONS.glob("*stage52*.sql")):
        fail("Stage52 candidate stage must not create a versioned migration")
    guard_text = Path(__file__).read_text(encoding="utf-8").lower()
    for marker in (
        "supabase.apply_migration",
        "supabase.execute_sql",
        "requests.",
        "urllib.request",
        "urlopen(",
        "psycopg",
        "subprocess.run",
        "shell=true",
    ):
        if marker in guard_text:
            fail(f"Stage52 guard contains forbidden remote/execution surface: {marker}")


def main() -> None:
    verify_authority()
    verify_historical_oracle()
    verify_candidate_sql()
    verify_client_compatibility()
    verify_repo_only_boundary()

    print("STAGE52_STUDENT_ISSUANCE_TARGET_PRIVACY_CANDIDATE=PASS")
    print("HISTORICAL_STUDENT_ID_EXISTENCE_ORACLE=CONFIRMED_STRUCTURALLY")
    print("TOKEN_ISSUANCE_AUTHORIZATION_BYPASS=NOT_PROVEN")
    print("CANDIDATE_UNAUTHORIZED_NOTFOUND_ERROR_EQUIVALENCE=PASS")
    print("AUTHENTICATED_MANAGER_BOUNDARY=PRESERVED")
    print("ANON_EXECUTE=DENIED")
    print("FLUTTER_SPECIFIC_ERROR_DEPENDENCY=NONE")
    print("VERSIONED_MIGRATION_CREATED=false")
    print("REMOTE_MUTATION=false")


if __name__ == "__main__":
    main()
