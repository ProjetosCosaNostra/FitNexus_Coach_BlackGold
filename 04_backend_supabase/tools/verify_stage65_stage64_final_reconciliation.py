from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage65_stage64_final_reconciliation_authority.json"
FAILURE_CLASS = "BGF-STAGE65-FINAL-RECONCILIATION-GUARD-626"
EXPECTED_BASELINE = "301f37c650175e71e182a267781565ce4df50aa5"

SEALED = {
    "authority": ("04_backend_supabase/stage64_stage63_remote_receipt_reconciliation_authority.json", "f23843ff9e03842e420e6eda4735d28ce20e2d11"),
    "guard": ("04_backend_supabase/tools/verify_stage64_stage63_remote_receipt_reconciliation.py", "0d1a44516c7e98edb16c1fb8a302f2aef24fca2e"),
}

EXPECTED_FUNCTIONS = {
    "public.issue_student_access_token_v2(p_student_id uuid)": ("6b47a21a83e884710447da01c6a5c95b8ff3e7bc7d415484a9ff698ba7b2a343", False, True, True),
    "public.issue_student_access_token(p_student_id uuid)": ("a04d80af9947f5f6780d1d3a70da4f0d6ca6d9f6bc65cdea3c5a840d8891dc2e", False, False, True),
    "private.is_org_manager(target_org uuid)": ("040c514af336ae2c8453ae89889ed3dcea14791e855b4420a0a9bd56bbf21fa0", False, True, False),
    "private.is_org_member(target_org uuid)": ("0ef1c6d13f2807e476b6c144a4db021265aea974a93d00ba1498e7419934969d", False, True, False),
    "private.is_org_owner(target_org uuid)": ("90933c1d1ef891a36e10be8c0aa0a5497d987182e0ecb42cf11778428beca17f", False, True, False),
}


def fail(detail: str) -> None:
    raise SystemExit(f"STAGE65_STAGE64_FINAL_RECONCILIATION=FAIL\nFAILURE_CLASS={FAILURE_CLASS}\nDETAIL={detail}")


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
        "stage": "STAGE65_STAGE64_FINAL_RECONCILIATION",
        "baseline_main_sha": EXPECTED_BASELINE,
        "current_state": "STAGE64_MERGED_GREEN_POSTMERGE_REMOTE_TRUTH_MATCHES_CORRECTED_RECEIPT_NO_REMOTE_MUTATION",
    }, "Stage65 authority")

    sealed = authority.get("sealed_stage64_inputs")
    if not isinstance(sealed, dict) or set(sealed) != set(SEALED):
        fail("sealed Stage64 input registry drift")
    for label, (rel, expected_blob) in SEALED.items():
        require(sealed[label], {"path": rel, "git_blob_sha": expected_blob}, f"sealed Stage64 {label}")
        path = ROOT / rel
        if not path.is_file() or blob(path) != expected_blob:
            fail(f"sealed Stage64 byte drift: {label}")

    promotion = authority.get("stage64_repository_promotion")
    require(promotion, {
        "pull_request": 155,
        "head_sha": "20384a54c231697408a8739413b4267784d04449",
        "merge_main_sha": EXPECTED_BASELINE,
        "stage64_workflow_run": 32853189431,
        "stage64_workflow_result": "SUCCESS",
        "flutter_quality_gate_run": 32853189702,
        "flutter_quality_gate_result": "SUCCESS",
        "consumed_live_proof_workflows_reexecuted": False,
    }, "Stage64 promotion")

    snapshot = authority.get("fresh_postmerge_remote_read_only_snapshot")
    require(snapshot, {
        "function_snapshot_observed_at_utc": "2026-08-25T13:29:05.698071Z",
        "table_snapshot_observed_at_utc": "2026-08-25T13:29:22.820139Z",
        "read_only": True,
        "remote_mutation_performed": False,
    }, "postmerge snapshot")

    funcs = snapshot.get("functions") if isinstance(snapshot, dict) else None
    if not isinstance(funcs, dict) or set(funcs) != set(EXPECTED_FUNCTIONS):
        fail("postmerge function inventory drift")
    for identity, (sha, anon, authenticated, service_role) in EXPECTED_FUNCTIONS.items():
        require(funcs[identity], {
            "security_definer": True,
            "safe_empty_search_path": True,
            "definition_sha256": sha,
            "anon_execute": anon,
            "authenticated_execute": authenticated,
            "service_role_execute": service_role,
        }, identity)

    require(snapshot.get("zero_data"), {
        "auth_users": 0,
        "organizations": 0,
        "students": 0,
    }, "zero-data boundary")

    access = snapshot.get("authenticated_direct_table_access")
    expected_denied = {"select": False, "insert": False, "update": False, "delete": False}
    require(access.get("public.student_access_links") if isinstance(access, dict) else None, expected_denied, "student_access_links auth direct access")
    require(access.get("private.student_access_security_events") if isinstance(access, dict) else None, expected_denied, "student_access_security_events auth direct access")

    require(snapshot.get("security_advisor"), {
        "warning_count": 1,
        "lint": "authenticated_security_definer_function_executable",
        "level": "WARN",
        "function": "public.issue_student_access_token_v2(p_student_id uuid)",
        "classification": "EXPECTED_INTENTIONAL_AUTHENTICATED_MANAGER_WRAPPER",
    }, "security advisor")

    require(authority.get("final_decision"), {
        "stage64_corrected_receipt_matches_fresh_postmerge_remote_truth": True,
        "stage63_security_classification_remains_supported": True,
        "stage63_original_non_v2_receipt_fields_remain_superseded": True,
        "runtime_security_drift_detected": False,
        "privilege_change_required": False,
        "ddl_change_required": False,
        "remote_mutation_required": False,
        "future_security_definer_receipts_require_postmerge_remote_recheck": True,
    }, "final decision")

    if any("stage65" in path.name.lower() for path in (BACKEND / "migrations").glob("*.sql")):
        fail("Stage65 final reconciliation must not introduce a migration")

    serialized = json.dumps(authority, sort_keys=True).lower()
    for key in ('"api_key"', '"access_token"', '"password"', '"webhook_token"', '"credential_secret_value"'):
        if key in serialized:
            fail(f"secret-bearing key found: {key}")

    print("STAGE65_STAGE64_FINAL_RECONCILIATION=PASS")
    print("STAGE64_POSTMERGE_REMOTE_MATCH=PASS")
    print("STAGE63_SECURITY_CLASSIFICATION=RETAINED")
    print("REMOTE_MUTATION=false")
    print("LAUNCH_GATE=DENIED")


if __name__ == "__main__":
    main()
