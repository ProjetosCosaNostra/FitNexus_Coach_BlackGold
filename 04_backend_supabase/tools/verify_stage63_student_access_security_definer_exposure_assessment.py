from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage63_student_access_security_definer_exposure_assessment_authority.json"
MIGRATIONS = BACKEND / "migrations"
FAILURE_CLASS = "BGF-STAGE63-SECURITY-DEFINER-EXPOSURE-ASSESSMENT-GUARD-610"
EXPECTED_BASELINE = "5889ca5337a6dff23c88e05dd8e226fb0664dde8"
EXPECTED_STATE = "EXPECTED_GUARDED_EXPOSURE_NO_PRIVILEGE_CHANGE_REQUIRED"

SEALED = {
    "security_definer_exposure_authority": (
        "04_backend_supabase/security_definer_exposure_authority.json",
        "e00fa2577f2a06eee6a0ef430f3aba79aa4f358e",
    ),
    "security_definer_exposure_guard": (
        "04_backend_supabase/tools/verify_security_definer_exposure_authority.py",
        "3081f3f94da6af9a1b00494b46ff159d302e0e2e",
    ),
    "stage51_advisor_reconciliation_authority": (
        "04_backend_supabase/stage51_security_definer_advisor_reconciliation_authority.json",
        "e2d90eb485d0e6eea68dee05533ff9b762f9f982",
    ),
    "stage51_advisor_reconciliation_guard": (
        "04_backend_supabase/tools/verify_stage51_security_definer_advisor_reconciliation.py",
        "117459b8311168db417368c431097b56c4ec2710",
    ),
    "stage52_final_authority": (
        "04_backend_supabase/stage52_student_issuance_target_privacy_final_authority.json",
        "075824c55ce463a0863211e4bffecdd8b111a4e9",
    ),
    "stage52_final_guard": (
        "04_backend_supabase/tools/verify_stage52_student_issuance_target_privacy_final_reconciliation.py",
        "93680df30749dd2abdd668dfc28c80ac1f2ba380",
    ),
    "stage52_hardening_migration": (
        "04_backend_supabase/migrations/20260824203000_stage52_student_issuance_target_privacy_hardening.sql",
        "80529ec11b923d83d10e01bb846ed284d34442f6",
    ),
    "stage62_final_authority": (
        "04_backend_supabase/stage62_stage61_final_reconciliation_authority.json",
        "4c9c99ecb2f3f016287e9d5c7de1888e6e2c846f",
    ),
}

EXPECTED_FAILURE_CLASSES = {
    "BGF-STAGE63-SECURITY-DEFINER-ALLOWLIST-DRIFT-602",
    "BGF-STAGE63-V2-RUNTIME-GRANT-DRIFT-603",
    "BGF-STAGE63-V1-DIRECT-AUTHENTICATED-EXPOSURE-604",
    "BGF-STAGE63-TARGET-PRIVACY-REGRESSION-605",
    "BGF-STAGE63-TENANT-RELATIONAL-BOUNDARY-DRIFT-606",
    "BGF-STAGE63-DIRECT-LINK-MUTATION-EXPOSURE-607",
    "BGF-STAGE63-UNPROVEN-PRIVATE-REST-ASSUMPTION-608",
    "BGF-STAGE63-ADVISOR-AUTO-REMEDIATION-609",
    FAILURE_CLASS,
}


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE63_STUDENT_ACCESS_SECURITY_DEFINER_EXPOSURE_ASSESSMENT=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\nDETAIL={detail}"
    )


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to load {path.relative_to(ROOT)}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"expected JSON object: {path.relative_to(ROOT)}")
    return value


def blob(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def require(mapping: Any, expected: dict[str, Any], label: str) -> None:
    if not isinstance(mapping, dict):
        fail(f"{label} must be object")
    for key, value in expected.items():
        if mapping.get(key) != value:
            fail(f"{label} drift: {key}; expected={value!r}; actual={mapping.get(key)!r}")


def verify_sealed(authority: dict[str, Any]) -> None:
    declared = authority.get("sealed_repository_inputs")
    if not isinstance(declared, dict) or set(declared) != set(SEALED):
        fail("sealed repository input registry drift")
    for label, (rel, expected_blob) in SEALED.items():
        entry = declared.get(label)
        if not isinstance(entry, dict):
            fail(f"sealed input missing: {label}")
        if entry.get("path") != rel or entry.get("git_blob_sha") != expected_blob:
            fail(f"sealed input declaration drift: {label}")
        path = ROOT / rel
        if not path.is_file() or blob(path) != expected_blob:
            fail(f"sealed input byte drift: {label}")


def verify_historical_authority() -> None:
    exposure = load(BACKEND / "security_definer_exposure_authority.json")
    approved = exposure.get("repository_target_approved_exposures")
    if not isinstance(approved, list) or len(approved) != 1:
        fail("repository SECURITY DEFINER allowlist must contain exactly one target exposure")
    require(
        approved[0],
        {
            "function": "issue_student_access_token_v2",
            "identity_arguments": "uuid",
            "roles": ["authenticated"],
            "boundary": "professor_manager_authority",
        },
        "repository target allowlist",
    )
    policy = exposure.get("policy")
    require(
        policy,
        {
            "public_security_definer_default_execute": "denied",
            "new_exposure": "fail_closed_until_explicitly_reviewed_and_allowlisted",
            "legacy_student_rpc_exposure": "denied",
            "issue_student_access_token_v2_authenticated_authority": "preserved",
        },
        "SECURITY DEFINER policy",
    )

    stage51 = load(BACKEND / "stage51_security_definer_advisor_reconciliation_authority.json")
    require(
        stage51,
        {
            "stage": "STAGE51_SECURITY_DEFINER_ADVISOR_RECONCILIATION",
            "current_state": "ADVISOR_WARNING_RECONCILED_AS_INTENTIONAL_MANAGER_BOUNDARY_NO_PRIVILEGE_CHANGE_NO_REMOTE_MUTATION",
        },
        "Stage51 authority",
    )
    require(
        stage51.get("decision"),
        {
            "authenticated_v2_execute_is_intentional": True,
            "authenticated_v2_execute_is_explicitly_allowlisted": True,
            "anonymous_v2_execute_must_remain_denied": True,
            "v1_direct_authenticated_execute_must_remain_denied": True,
            "advisor_warning_is_equivalent_to_vulnerability": False,
            "automatic_revoke_execute_allowed": False,
            "automatic_switch_to_security_invoker_allowed": False,
            "automatic_move_out_of_public_schema_allowed": False,
            "privilege_change_required_now": False,
            "ddl_change_required_now": False,
            "remote_mutation_required_now": False,
        },
        "Stage51 decision",
    )

    stage52 = load(BACKEND / "stage52_student_issuance_target_privacy_final_authority.json")
    require(
        stage52.get("security_invariants"),
        {
            "authenticated_manager_wrapper_intentionally_preserved": True,
            "anonymous_v2_execute_denied": True,
            "authenticated_v2_execute_preserved": True,
            "v1_authenticated_execute_denied": True,
            "authorization_and_target_resolution_coalesced": True,
            "owner_or_admin_membership_required": True,
            "unauthorized_and_nonexistent_targets_indistinguishable": True,
            "student_id_existence_oracle_closed": True,
            "rotation_cooldown_preserved": True,
            "v1_defensive_authorization_recheck_preserved": True,
        },
        "Stage52 security invariants",
    )


def verify_stage52_source() -> None:
    path = BACKEND / "migrations/20260824203000_stage52_student_issuance_target_privacy_hardening.sql"
    source = path.read_text(encoding="utf-8")
    required = (
        "SECURITY DEFINER",
        "set search_path = ''",
        "if auth.uid() is null then",
        "join public.organization_members m",
        "and m.user_id = (select auth.uid())",
        "and m.role in ('owner', 'admin')",
        "message = 'STUDENT_ACCESS_TARGET_UNAVAILABLE'",
        "v_token := public.issue_student_access_token(p_student_id);",
        "and l.student_id = p_student_id",
        "and l.organization_id = v_org",
        "revoke all on function public.issue_student_access_token_v2(uuid) from public;",
        "revoke all on function public.issue_student_access_token_v2(uuid) from anon;",
        "grant execute on function public.issue_student_access_token_v2(uuid) to authenticated;",
    )
    for marker in required:
        if marker not in source:
            fail(f"Stage52 hardening marker missing: {marker}")
    if "message = 'STUDENT_NOT_FOUND'" in source or "message = 'ORG_MANAGER_REQUIRED'" in source:
        fail("Stage52 hardened wrapper reintroduced distinguishable target errors")


def verify_remote_receipt(authority: dict[str, Any]) -> None:
    remote = authority.get("fresh_remote_read_only_snapshot")
    require(
        remote,
        {
            "observed_at_utc": "2026-08-25T11:59:37.987884+00:00",
            "remote_mutation_performed": False,
            "security_advisor_warning_count": 1,
            "security_advisor_lint": "authenticated_security_definer_function_executable",
            "security_advisor_function": "public.issue_student_access_token_v2(p_student_id uuid)",
            "security_advisor_level": "WARN",
            "security_advisor_classification": "EXPECTED_INTENTIONAL_AUTHENTICATED_MANAGER_WRAPPER",
            "private_rest_exposure_guc_proven": False,
        },
        "fresh remote read-only snapshot",
    )
    note = str(remote.get("private_rest_exposure_guc_note", ""))
    if "non-evidence" not in note or "not used" not in note:
        fail("unproven private REST configuration must remain explicit non-evidence")

    funcs = authority.get("remote_function_inventory")
    expected_funcs = {
        "public.issue_student_access_token_v2(p_student_id uuid)": {
            "security_definer": True,
            "safe_empty_search_path": True,
            "public_execute": False,
            "anon_execute": False,
            "authenticated_execute": True,
            "service_role_execute": True,
            "definition_sha256": "6b47a21a83e884710447da01c6a5c95b8ff3e7bc7d415484a9ff698ba7b2a343",
            "requires_auth_uid": True,
            "authorization_and_target_lookup_coalesced": True,
            "manager_roles": ["owner", "admin"],
            "unauthorized_and_nonexistent_targets_share_error": "STUDENT_ACCESS_TARGET_UNAVAILABLE",
            "rotation_cooldown_present": True,
            "calls_v1_only_after_wrapper_authorization": True,
            "new_link_lookup_bound_to_student_and_org": True,
            "link_updates_bound_to_org": True,
        },
        "public.issue_student_access_token(p_student_id uuid)": {
            "security_definer": True,
            "safe_empty_search_path": True,
            "public_execute": False,
            "anon_execute": False,
            "authenticated_execute": False,
            "service_role_execute": True,
            "definition_sha256": "e94ec8b489635fe22ce67536753279b8770e268a16e7bcbf999936df6644a61f",
            "manager_recheck_present": True,
            "raw_token_returned_once": True,
            "token_stored_hashed": True,
        },
        "private.is_org_manager(target_org uuid)": {
            "security_definer": True,
            "safe_empty_search_path": True,
            "public_execute": False,
            "anon_execute": False,
            "authenticated_execute": True,
            "service_role_execute": True,
            "definition_sha256": "040c533cdce62a40e4eef46c7c4b2bb196ba2df63646649c5728e535c61596a5",
            "self_scoped_to_auth_uid": True,
            "roles": ["owner", "admin"],
            "mutates_state": False,
        },
        "private.is_org_member(p_org_id uuid)": {
            "security_definer": True,
            "safe_empty_search_path": True,
            "public_execute": False,
            "anon_execute": False,
            "authenticated_execute": True,
            "service_role_execute": True,
            "definition_sha256": "b016c44ab1ab827bedace3f0ded174c79a7102fa239d996ef44adecabf9f31ae",
            "self_scoped_to_auth_uid": True,
            "mutates_state": False,
        },
        "private.is_org_owner(p_org_id uuid)": {
            "security_definer": True,
            "safe_empty_search_path": True,
            "public_execute": False,
            "anon_execute": False,
            "authenticated_execute": True,
            "service_role_execute": True,
            "definition_sha256": "795933356fb5beda52de5da4fb9ebe48c35e12c1dd3305270a461404412fcaa8",
            "self_scoped_to_auth_uid": True,
            "role": "owner",
            "mutates_state": False,
        },
    }
    if not isinstance(funcs, dict) or set(funcs) != set(expected_funcs):
        fail("remote function inventory key drift")
    for label, expected in expected_funcs.items():
        require(funcs[label], expected, label)

    tables = authority.get("remote_table_boundary")
    require(tables.get("private.student_access_security_events") if isinstance(tables, dict) else None, {
        "rls_enabled": False,
        "authenticated_select": False,
        "authenticated_insert": False,
        "authenticated_update": False,
        "authenticated_delete": False,
        "service_role_full_crud": True,
    }, "security event table")
    require(tables.get("public.student_access_links") if isinstance(tables, dict) else None, {
        "rls_enabled": True,
        "authenticated_select": False,
        "authenticated_insert": False,
        "authenticated_update": False,
        "authenticated_delete": False,
        "service_role_full_crud": True,
    }, "student access links table")
    for table in ("public.students", "public.organization_members", "public.organizations"):
        entry = tables.get(table) if isinstance(tables, dict) else None
        if not isinstance(entry, dict) or entry.get("rls_enabled") is not True:
            fail(f"RLS boundary drift: {table}")

    constraints = authority.get("critical_relational_constraints")
    if not isinstance(constraints, dict):
        fail("critical relational constraints missing")
    required_constraint_markers = {
        "organization_members_pkey": "PRIMARY KEY",
        "organization_members_role_check": "owner, admin, coach",
        "students_pkey": "PRIMARY KEY",
        "students_id_organization_id_key": "UNIQUE",
        "student_access_links_student_same_org_fk": "FOREIGN KEY",
        "student_access_links_rotation_same_student_org_fk": "FOREIGN KEY",
        "student_access_links_token_hash_key": "UNIQUE",
    }
    for key, marker in required_constraint_markers.items():
        if marker not in str(constraints.get(key, "")):
            fail(f"critical constraint drift: {key}")


def verify_decision(authority: dict[str, Any]) -> None:
    attacks = authority.get("attack_class_assessment")
    if not isinstance(attacks, dict) or len(attacks) < 12:
        fail("attack-class assessment incomplete")
    for key, value in attacks.items():
        if not str(value).startswith("PASS_"):
            fail(f"attack class is not fail-closed PASS: {key}")

    require(
        authority.get("decision"),
        {
            "advisor_warning_is_expected_by_current_architecture": True,
            "advisor_warning_is_equivalent_to_confirmed_vulnerability": False,
            "authenticated_v2_execute_is_intentional": True,
            "authenticated_v2_execute_must_remain_explicitly_allowlisted": True,
            "automatic_revoke_authenticated_execute_allowed": False,
            "automatic_switch_to_security_invoker_allowed": False,
            "automatic_move_out_of_public_schema_allowed": False,
            "privilege_change_required_now": False,
            "ddl_change_required_now": False,
            "migration_required_now": False,
            "remote_mutation_required_now": False,
            "future_new_security_definer_advisor_warning_requires_fail_closed_review": True,
            "future_v2_body_or_grant_drift_requires_fail_closed_review": True,
        },
        "Stage63 decision",
    )
    gates = authority.get("gates")
    require(gates, {
        "stage63_security_definer_assessment": "PASS_EXPECTED_GUARDED_EXPOSURE_NO_CHANGE_REQUIRED_PENDING_CI",
        "security_advisor_reconciliation": "PASS_INTENTIONAL_AUTHENTICATED_MANAGER_WRAPPER_TARGET_PRIVACY_HARDENED",
        "privilege_change": "DENIED_NOT_REQUIRED",
        "remote_mutation": "DENIED_NOT_REQUIRED",
        "production_deployment": "DENIED",
        "incident_response": "DENIED",
        "controlled_launch": "DENIED",
        "paid_media": "DENIED",
        "launch": "DENIED",
    }, "Stage63 gates")


def verify_no_stage63_migration_or_side_effect_tooling() -> None:
    if any("stage63" in path.name.lower() for path in MIGRATIONS.glob("*.sql")):
        fail("Stage63 assessment must not introduce a migration")
    source = Path(__file__).read_text(encoding="utf-8").lower()
    forbidden = (
        "requests.",
        "urllib.request",
        "subprocess.",
        "supabase.",
        "apply_migration(",
        "execute_sql(",
    )
    for marker in forbidden:
        if marker in source:
            fail(f"Stage63 guard contains forbidden execution surface: {marker}")


def main() -> None:
    authority = load(AUTHORITY)
    require(authority, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE63_STUDENT_ACCESS_SECURITY_DEFINER_EXPOSURE_ASSESSMENT",
        "baseline_main_sha": EXPECTED_BASELINE,
        "current_state": EXPECTED_STATE,
        "assessment_scope": "READ_ONLY_REPOSITORY_AND_REMOTE_SECURITY_BOUNDARY_REASSESSMENT",
    }, "Stage63 authority")
    if set(authority.get("failure_classes", [])) != EXPECTED_FAILURE_CLASSES:
        fail("Stage63 failure-class registry drift")
    verify_sealed(authority)
    verify_historical_authority()
    verify_stage52_source()
    verify_remote_receipt(authority)
    verify_decision(authority)
    verify_no_stage63_migration_or_side_effect_tooling()
    print("STAGE63_STUDENT_ACCESS_SECURITY_DEFINER_EXPOSURE_ASSESSMENT=PASS")
    print("CLASSIFICATION=EXPECTED_GUARDED_EXPOSURE_NO_PRIVILEGE_CHANGE_REQUIRED")
    print("SECURITY_ADVISOR_WARNING_COUNT=1")
    print("AUTHENTICATED_V2_EXECUTE=INTENTIONAL_ALLOWLISTED")
    print("AUTHENTICATED_V1_EXECUTE=DENIED")
    print("STUDENT_IDENTIFIER_EXISTENCE_ORACLE=CLOSED")
    print("PRIVILEGE_CHANGE_REQUIRED=false")
    print("REMOTE_MUTATION_PERFORMED=false")
    print("LAUNCH_GATE=DENIED")


if __name__ == "__main__":
    main()
