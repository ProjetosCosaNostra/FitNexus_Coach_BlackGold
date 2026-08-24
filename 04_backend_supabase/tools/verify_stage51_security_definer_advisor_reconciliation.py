from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

FAILURE_CLASS = "BGF-STAGE51-SECURITY-DEFINER-ADVISOR-RECONCILIATION-GUARD-480"
ROOT = Path(__file__).resolve().parents[2]
AUTHORITY = ROOT / "04_backend_supabase/stage51_security_definer_advisor_reconciliation_authority.json"

EXPECTED_BASELINE = "b0e750cbac2dc5f519400e5dbfab7fd5893cf497"
EXPECTED_STATE = "ADVISOR_WARNING_RECONCILED_AS_INTENTIONAL_MANAGER_BOUNDARY_NO_PRIVILEGE_CHANGE_NO_REMOTE_MUTATION"
EXPECTED_FAILURE_CLASSES = {
    "BGF-STAGE51-ADVISOR-WARNING-UNRECONCILED-474",
    "BGF-STAGE51-ISSUANCE-ALLOWLIST-DRIFT-475",
    "BGF-STAGE51-ANON-ISSUANCE-EXPOSURE-476",
    "BGF-STAGE51-MANAGER-AUTHORITY-ORDER-DRIFT-477",
    "BGF-STAGE51-V1-DIRECT-AUTHENTICATED-EXPOSURE-478",
    "BGF-STAGE51-ADVISOR-AUTO-REMEDIATION-479",
    "BGF-STAGE51-SECURITY-DEFINER-ADVISOR-RECONCILIATION-GUARD-480",
}


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE51_SECURITY_DEFINER_ADVISOR_RECONCILIATION=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\n"
        f"DETAIL={detail}"
    )


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"JSON unreadable: {path.name}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"JSON must be object: {path.name}")
    return value


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def main() -> None:
    authority = load_json(AUTHORITY)
    if authority.get("schema_version") != 1:
        fail("schema_version drift")
    if authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("project_ref drift")
    if authority.get("stage") != "STAGE51_SECURITY_DEFINER_ADVISOR_RECONCILIATION":
        fail("stage drift")
    if authority.get("baseline_main_sha") != EXPECTED_BASELINE:
        fail("baseline main SHA drift")
    if authority.get("current_state") != EXPECTED_STATE:
        fail("current state drift")

    advisor = authority.get("advisor_snapshot")
    if not isinstance(advisor, dict):
        fail("advisor snapshot missing")
    expected_advisor = {
        "security_warning_count": 1,
        "lint_name": "authenticated_security_definer_function_executable",
        "title": "Signed-In Users Can Execute SECURITY DEFINER Function",
        "level": "WARN",
        "facing": "EXTERNAL",
        "function": "public.issue_student_access_token_v2(p_student_id uuid)",
        "remediation_url": "https://supabase.com/docs/guides/database/database-linter?lint=0029_authenticated_security_definer_function_executable",
        "classification": "EXPECTED_INTENTIONAL_AUTHENTICATED_MANAGER_WRAPPER",
        "warning_suppressed_or_removed": False,
    }
    for key, expected in expected_advisor.items():
        if advisor.get(key) != expected:
            fail(f"advisor reconciliation drift: {key}")

    sealed = authority.get("sealed_repository_authority")
    if not isinstance(sealed, dict) or len(sealed) != 4:
        fail("sealed repository authority registry drift")
    loaded: dict[str, Path] = {}
    for key, item in sealed.items():
        if not isinstance(item, dict):
            fail(f"sealed item malformed: {key}")
        path = ROOT / str(item.get("path", ""))
        expected_blob = str(item.get("git_blob_sha", ""))
        if not path.is_file():
            fail(f"sealed file missing: {key}")
        if git_blob_sha(path) != expected_blob:
            fail(f"sealed file blob drift: {key}")
        loaded[key] = path

    exposure_authority = load_json(loaded["security_definer_exposure_authority"])
    if exposure_authority.get("schema_version") != 2:
        fail("historical SECURITY DEFINER authority schema drift")
    if exposure_authority.get("current_state") != "STAGE33_REVOCATION_REMOTE_RECONCILED_POST_REVOCATION":
        fail("historical SECURITY DEFINER lifecycle drift")
    policy = exposure_authority.get("policy")
    if not isinstance(policy, dict):
        fail("historical exposure policy missing")
    if policy.get("issue_student_access_token_v2_authenticated_authority") != "preserved":
        fail("historical policy no longer preserves authenticated v2 issuance")
    target = exposure_authority.get("repository_target_approved_exposures")
    if not isinstance(target, list) or len(target) != 1:
        fail("repository approved exposure set must contain exactly one function")
    row = target[0]
    if not isinstance(row, dict):
        fail("repository approved exposure row malformed")
    if row.get("function") != "issue_student_access_token_v2":
        fail("approved SECURITY DEFINER exposure function drift")
    if row.get("identity_arguments") != "uuid":
        fail("approved SECURITY DEFINER exposure signature drift")
    if row.get("roles") != ["authenticated"]:
        fail("approved SECURITY DEFINER exposure role drift")
    if row.get("boundary") != "professor_manager_authority":
        fail("approved SECURITY DEFINER boundary drift")

    migration = loaded["issuance_authority_migration"].read_text(encoding="utf-8").lower()
    required_migration_markers = (
        "create or replace function public.issue_student_access_token_v2(p_student_id uuid)",
        "security definer",
        "set search_path = ''",
        "if auth.uid() is null then",
        "select s.organization_id into v_org",
        "if not private.is_org_manager(v_org) then",
        "select l.id, l.rotation_number",
        "v_token := public.issue_student_access_token(p_student_id)",
        "revoke all on function public.issue_student_access_token_v2(uuid) from public, anon;",
        "grant execute on function public.issue_student_access_token_v2(uuid) to authenticated;",
    )
    for marker in required_migration_markers:
        if marker not in migration:
            fail(f"issuance migration invariant disappeared: {marker}")
    auth_pos = migration.find("if auth.uid() is null then")
    manager_pos = migration.find("if not private.is_org_manager(v_org) then")
    rotation_pos = migration.find("select l.id, l.rotation_number")
    v1_pos = migration.find("v_token := public.issue_student_access_token(p_student_id)")
    if min(auth_pos, manager_pos, rotation_pos, v1_pos) < 0:
        fail("could not resolve issuance authority ordering")
    if not (auth_pos < manager_pos < rotation_pos < v1_pos):
        fail("issuance authority ordering drift")

    remote = authority.get("fresh_remote_read_only_receipt")
    expected_remote = {
        "observed_at_utc": "2026-08-24T18:36:24.191541+00:00",
        "v2_owner": "postgres",
        "v2_security_definer": True,
        "v2_anon_execute": False,
        "v2_authenticated_execute": True,
        "v2_service_role_execute": True,
        "v2_auth_required_marker": True,
        "v2_student_org_lookup_marker": True,
        "v2_manager_check_marker": True,
        "v2_rotation_lookup_marker": True,
        "v2_v1_call_marker": True,
        "v2_auth_before_manager": True,
        "v2_manager_before_rotation_lookup": True,
        "v2_rotation_before_v1_call": True,
        "manager_security_definer": True,
        "manager_auth_uid_marker": True,
        "manager_owner_admin_marker": True,
        "v1_security_definer": True,
        "v1_anon_execute": False,
        "v1_authenticated_execute": False,
        "v1_service_role_execute": True,
        "v1_manager_check_marker": True,
        "remote_mutation_performed": False,
    }
    if not isinstance(remote, dict):
        fail("fresh remote receipt missing")
    for key, expected in expected_remote.items():
        if remote.get(key) != expected:
            fail(f"fresh remote issuance receipt drift: {key}")

    decision = authority.get("decision")
    if not isinstance(decision, dict):
        fail("reconciliation decision missing")
    required_true = {
        "authenticated_v2_execute_is_intentional",
        "authenticated_v2_execute_is_explicitly_allowlisted",
        "anonymous_v2_execute_must_remain_denied",
        "v2_security_definer_is_required_by_current_architecture",
        "v2_must_check_auth_uid_before_student_or_rotation_authority",
        "v2_must_check_org_manager_before_rotation_state_lookup",
        "v2_must_call_mature_v1_only_after_v2_authority_checks",
        "v1_direct_authenticated_execute_must_remain_denied",
        "service_role_v1_execute_must_remain_available",
        "future_drift_requires_fail_closed_review",
    }
    for key in required_true:
        if decision.get(key) is not True:
            fail(f"intentional SECURITY DEFINER boundary decision drift: {key}")
    required_false = {
        "advisor_warning_is_equivalent_to_vulnerability",
        "automatic_revoke_execute_allowed",
        "automatic_switch_to_security_invoker_allowed",
        "automatic_move_out_of_public_schema_allowed",
        "privilege_change_required_now",
        "ddl_change_required_now",
        "remote_mutation_required_now",
    }
    for key in required_false:
        if decision.get(key) is not False:
            fail(f"unsafe automatic remediation decision enabled: {key}")

    future = authority.get("future_fail_closed_conditions")
    if not isinstance(future, list) or len(future) != 8:
        fail("future fail-closed condition registry drift")
    if set(authority.get("failure_classes", [])) != EXPECTED_FAILURE_CLASSES:
        fail("Stage51 failure-class registry drift")

    gates = authority.get("gates")
    if not isinstance(gates, dict):
        fail("Stage51 gate registry missing")
    if gates.get("security_advisor_reconciliation") != "PASS_INTENTIONAL_EXPOSURE_REVIEWED_NO_CHANGE":
        fail("Stage51 advisor reconciliation result drift")
    for gate in ("production_deployment", "incident_response", "controlled_launch", "paid_media", "launch"):
        if gates.get(gate) != "DENIED":
            fail(f"Stage51 may not promote gate: {gate}")

    print("STAGE51_SECURITY_DEFINER_ADVISOR_RECONCILIATION=PASS")
    print("ADVISOR_WARNING=EXPECTED_INTENTIONAL_AUTHENTICATED_MANAGER_WRAPPER")
    print("ANON_EXECUTE=false")
    print("AUTHENTICATED_EXECUTE=true_INTENTIONAL")
    print("MANAGER_AUTHORITY_BEFORE_ROTATION_LOOKUP=PASS")
    print("V1_DIRECT_AUTHENTICATED_EXECUTE=false")
    print("AUTOMATIC_REMEDIATION=false")
    print("REMOTE_MUTATION=false")
    print("LAUNCH_GATE_PROMOTION=false")


if __name__ == "__main__":
    main()
