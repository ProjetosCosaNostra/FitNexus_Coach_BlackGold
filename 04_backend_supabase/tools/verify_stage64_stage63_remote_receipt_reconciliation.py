from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage64_stage63_remote_receipt_reconciliation_authority.json"
FAILURE_CLASS = "BGF-STAGE64-STAGE63-REMOTE-RECEIPT-RECONCILIATION-GUARD-618"
EXPECTED_BASELINE = "e478f7c6bbbd5f985d7ef6f9a47342ae36129921"

SEALED = {
    "stage63_authority": ("04_backend_supabase/stage63_student_access_security_definer_exposure_assessment_authority.json", "c20cdc38c56808bc355e64d84ef3af5e46b0bcae"),
    "stage63_guard": ("04_backend_supabase/tools/verify_stage63_student_access_security_definer_exposure_assessment.py", "142afd5f6f8d888b7f619f8385ce4f137bdd09ce"),
    "stage1_auth_tenancy_foundation": ("04_backend_supabase/migrations/20260818113806_stage1_auth_tenancy_foundation.sql", "fd8dc2671d367be95e4a14be35cfa240cffb253b"),
    "stage3_students_training_domain": ("04_backend_supabase/migrations/20260818134341_stage3_students_training_domain.sql", "83a4408c8d48b51a96f909ef6817f2cebd7074aa"),
    "stage5_student_access_workout_execution": ("04_backend_supabase/migrations/20260818152500_stage5_student_access_workout_execution.sql", "9b3719fef110a082e811aaee35df2cf285514435"),
    "stage52_final_authority": ("04_backend_supabase/stage52_student_issuance_target_privacy_final_authority.json", "075824c55ce463a0863211e4bffecdd8b111a4e9"),
    "security_definer_exposure_authority": ("04_backend_supabase/security_definer_exposure_authority.json", "e00fa2577f2a06eee6a0ef430f3aba79aa4f358e"),
}

CORRECTED = {
    "public.issue_student_access_token_v2(p_student_id uuid)": ("6b47a21a83e884710447da01c6a5c95b8ff3e7bc7d415484a9ff698ba7b2a343", False, True, True),
    "public.issue_student_access_token(p_student_id uuid)": ("a04d80af9947f5f6780d1d3a70da4f0d6ca6d9f6bc65cdea3c5a840d8891dc2e", False, False, True),
    "private.is_org_manager(target_org uuid)": ("040c514af336ae2c8453ae89889ed3dcea14791e855b4420a0a9bd56bbf21fa0", False, True, False),
    "private.is_org_member(target_org uuid)": ("0ef1c6d13f2807e476b6c144a4db021265aea974a93d00ba1498e7419934969d", False, True, False),
    "private.is_org_owner(target_org uuid)": ("90933c1d1ef891a36e10be8c0aa0a5497d987182e0ecb42cf11778428beca17f", False, True, False),
}


def fail(detail: str) -> None:
    raise SystemExit(f"STAGE64_STAGE63_REMOTE_RECEIPT_RECONCILIATION=FAIL\nFAILURE_CLASS={FAILURE_CLASS}\nDETAIL={detail}")


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to load {path.relative_to(ROOT)}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"expected object: {path.relative_to(ROOT)}")
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


def main() -> None:
    authority = load(AUTHORITY)
    require(authority, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE64_STAGE63_REMOTE_RECEIPT_RECONCILIATION",
        "baseline_main_sha": EXPECTED_BASELINE,
        "current_state": "STAGE63_CLASSIFICATION_RETAINED_REMOTE_RECEIPT_PARTIALLY_SUPERSEDED_NO_REMOTE_MUTATION",
    }, "authority")

    declared = authority.get("sealed_repository_inputs")
    if not isinstance(declared, dict) or set(declared) != set(SEALED):
        fail("sealed input registry drift")
    for label, (rel, expected_blob) in SEALED.items():
        entry = declared.get(label)
        require(entry, {"path": rel, "git_blob_sha": expected_blob}, f"sealed input {label}")
        path = ROOT / rel
        if not path.is_file() or blob(path) != expected_blob:
            fail(f"sealed input byte drift: {label}")

    promo = authority.get("stage63_repository_promotion")
    require(promo, {
        "pull_request": 154,
        "head_sha": "e4c76bad8ace11a22ade6b735cf1e55c65a1055e",
        "merge_main_sha": EXPECTED_BASELINE,
        "stage63_workflow_run": 32846427857,
        "stage63_workflow_result": "SUCCESS",
        "flutter_quality_gate_run": 32846427863,
        "flutter_quality_gate_result": "SUCCESS",
    }, "Stage63 promotion receipt")

    remote = authority.get("fresh_postmerge_remote_read_only_receipt")
    require(remote, {
        "security_advisor_rechecked_after_merge": True,
        "security_advisor_warning_count": 1,
        "security_advisor_lint": "authenticated_security_definer_function_executable",
        "security_advisor_function": "public.issue_student_access_token_v2(p_student_id uuid)",
        "remote_mutation_performed": False,
        "auth_users": 0,
        "organizations": 0,
        "students": 0,
    }, "postmerge remote receipt")

    inventory = authority.get("corrected_remote_function_inventory")
    if not isinstance(inventory, dict) or set(inventory) != set(CORRECTED):
        fail("corrected remote function inventory drift")
    for identity, (sha, anon, authenticated, service_role) in CORRECTED.items():
        require(inventory[identity], {
            "security_definer": True,
            "safe_empty_search_path": True,
            "anon_execute": anon,
            "authenticated_execute": authenticated,
            "service_role_execute": service_role,
            "definition_sha256": sha,
        }, identity)

    if inventory["public.issue_student_access_token_v2(p_student_id uuid)"].get("stage63_value_was_correct") is not True:
        fail("critical v2 Stage63 value must remain explicitly correct")
    if inventory["public.issue_student_access_token(p_student_id uuid)"].get("stage63_hash_field_superseded") is not True:
        fail("v1 Stage63 hash supersession missing")
    for helper in (
        "private.is_org_manager(target_org uuid)",
        "private.is_org_member(target_org uuid)",
        "private.is_org_owner(target_org uuid)",
    ):
        if inventory[helper].get("stage63_fields_superseded") is not True:
            fail(f"helper Stage63 field supersession missing: {helper}")

    stage1 = (BACKEND / "migrations/20260818113806_stage1_auth_tenancy_foundation.sql").read_text(encoding="utf-8")
    stage3 = (BACKEND / "migrations/20260818134341_stage3_students_training_domain.sql").read_text(encoding="utf-8")
    stage5 = (BACKEND / "migrations/20260818152500_stage5_student_access_workout_execution.sql").read_text(encoding="utf-8")
    for marker in (
        "function private.is_org_member(target_org uuid)",
        "function private.is_org_owner(target_org uuid)",
        "grant execute on function private.is_org_member(uuid) to authenticated",
        "grant execute on function private.is_org_owner(uuid) to authenticated",
    ):
        if marker not in stage1.lower():
            fail(f"Stage1 source marker missing: {marker}")
    for marker in (
        "function private.is_org_manager(target_org uuid)",
        "and m.role in ('owner','admin')",
        "grant execute on function private.is_org_manager(uuid) to authenticated",
    ):
        if marker not in stage3.lower():
            fail(f"Stage3 source marker missing: {marker}")
    for marker in (
        "function public.issue_student_access_token(p_student_id uuid)",
        "if auth.uid() is null then",
        "if not private.is_org_manager(v_org) then",
        "extensions.digest(v_token, 'sha256')",
    ):
        if marker not in stage5.lower():
            fail(f"Stage5 v1 marker missing: {marker}")

    tables = authority.get("fresh_table_boundary")
    require(tables.get("public.student_access_links") if isinstance(tables, dict) else None, {
        "rls_enabled": True,
        "authenticated_select": False,
        "authenticated_insert": False,
        "authenticated_update": False,
        "authenticated_delete": False,
        "service_role_full_crud": True,
    }, "student_access_links boundary")
    require(tables.get("private.student_access_security_events") if isinstance(tables, dict) else None, {
        "rls_enabled": False,
        "authenticated_select": False,
        "authenticated_insert": False,
        "authenticated_update": False,
        "authenticated_delete": False,
        "service_role_full_crud": True,
    }, "student_access_security_events boundary")

    decision = authority.get("decision")
    require(decision, {
        "stage63_security_classification_remains_supported": True,
        "stage63_remote_receipt_is_fully_authoritative": False,
        "stage63_remote_receipt_superseded_for_enumerated_fields": True,
        "v2_authenticated_execute_remains_intentional": True,
        "v1_direct_authenticated_execute_remains_denied": True,
        "private_helper_service_role_execute_is_required": False,
        "narrower_helper_acl_is_not_a_security_regression": True,
        "automatic_revoke_authenticated_v2_execute_allowed": False,
        "automatic_switch_v2_to_security_invoker_allowed": False,
        "ddl_change_required_now": False,
        "remote_mutation_required_now": False,
        "future_remote_receipts_must_be_postmerge_rechecked_before_final_reconciliation": True,
    }, "decision")

    if any("stage64" in path.name.lower() for path in (BACKEND / "migrations").glob("*.sql")):
        fail("Stage64 reconciliation must not introduce a migration")

    serialized = json.dumps(authority, sort_keys=True).lower()
    for key in ('"api_key"', '"access_token"', '"password"', '"webhook_token"', '"credential_secret_value"'):
        if key in serialized:
            fail(f"secret-bearing key found: {key}")

    print("STAGE64_STAGE63_REMOTE_RECEIPT_RECONCILIATION=PASS")
    print("STAGE63_CLASSIFICATION=RETAINED_WITH_CORRECTED_RECEIPT")
    print("REMOTE_MUTATION=false")
    print("PRIVILEGE_CHANGE=DENIED_NOT_REQUIRED")
    print("LAUNCH_GATE=DENIED")


if __name__ == "__main__":
    main()
