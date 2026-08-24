from __future__ import annotations

import hashlib
import json
from pathlib import Path

from stage52_student_issuance_migration_frontier import FINAL_BASELINE, FINAL_OBSERVED, NAME, REMOTE_VERSION, divergences, remote_map, state, to_promotion

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
LEDGER = BACKEND / "migration_ledger_authority.json"
AUTHORITY = BACKEND / "stage52_student_issuance_target_privacy_final_authority.json"
PROMOTION = BACKEND / "stage52_student_issuance_target_privacy_promotion_authority.json"
CANDIDATE = BACKEND / "operations/stage52_student_issuance_target_privacy_candidate.sql"
MIGRATION = BACKEND / "migrations/20260824203000_stage52_student_issuance_target_privacy_hardening.sql"
EXPECTED_BLOB = "80529ec11b923d83d10e01bb846ed284d34442f6"
FAILURE_CLASS = "BGF-STAGE52-REMOTE-RECONCILIATION-493"


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE52_STUDENT_ISSUANCE_TARGET_PRIVACY_FINAL_RECONCILIATION=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\n"
        f"DETAIL={detail}"
    )


def load(path: Path) -> dict:
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


def require(mapping: dict, expected: dict, label: str) -> None:
    if not isinstance(mapping, dict):
        fail(f"{label} must be object")
    for key, value in expected.items():
        if mapping.get(key) != value:
            fail(f"{label} drift: {key}; expected={value!r}; actual={mapping.get(key)!r}")


def main() -> None:
    ledger = load(LEDGER)
    authority = load(AUTHORITY)
    promotion = load(PROMOTION)

    try:
        if state(ledger) != "final":
            fail("migration ledger is not exact Stage52 final frontier")
        if state(to_promotion(ledger)) != "promotion":
            fail("historical Stage52 promotion projection invalid")
    except ValueError as exc:
        fail(str(exc))

    require(ledger, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "baseline_main_sha": FINAL_BASELINE,
        "observed_at_utc": FINAL_OBSERVED,
        "source": "Supabase.list_migrations+Supabase.execute_sql",
        "comparison_key": "migration_name",
    }, "final ledger")
    if remote_map(ledger).get(NAME) != REMOTE_VERSION:
        fail("Stage52 remote migration version drift")
    remote_only, repo_only = divergences(ledger)
    if len(remote_only) != 3 or repo_only:
        fail("final divergence frontier drift")
    if blob(CANDIDATE) != EXPECTED_BLOB or blob(MIGRATION) != EXPECTED_BLOB:
        fail("candidate/migration blob drift")
    if CANDIDATE.read_bytes() != MIGRATION.read_bytes():
        fail("candidate/migration exact-byte invariant failed")

    require(promotion, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE52_STUDENT_ISSUANCE_TARGET_PRIVACY_PROMOTION",
        "baseline_main_sha": "b5f466ef09dd027f10c88d3d13726f3d7c0281ba",
        "current_state": "REPO_ONLY_VERSIONED_MIGRATION_EXACT_CANDIDATE_NO_REMOTE_APPLY",
    }, "promotion authority")

    require(authority, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE52_STUDENT_ISSUANCE_TARGET_PRIVACY_FINAL_RECONCILIATION",
        "baseline_main_sha": FINAL_BASELINE,
        "current_state": "TARGET_PRIVACY_HARDENING_REMOTE_APPLIED_ZERO_CUSTOMER_DATA_PRIVILEGES_PRESERVED",
    }, "final authority")

    require(authority.get("repository_promotion", {}), {
        "pull_request": 140,
        "head_sha": "4d3e499735283ae3cc86f81a7986e00eaada4d4d",
        "merge_main_sha": FINAL_BASELINE,
        "migration_git_blob_sha": EXPECTED_BLOB,
        "candidate_git_blob_sha": EXPECTED_BLOB,
        "exact_candidate_blob_reused": True,
        "stage52_workflow_run": 32775171057,
        "stage52_workflow_result": "SUCCESS",
        "flutter_quality_gate_run": 32775171077,
        "flutter_quality_gate_result": "SUCCESS",
        "postgres_compatibility_run": 32775170998,
        "postgres_compatibility_result": "SUCCESS",
        "consumed_live_proofs_reexecuted": False,
    }, "repository promotion")

    require(authority.get("remote_apply", {}), {
        "migration_name": NAME,
        "remote_version": REMOTE_VERSION,
        "applied_via": "Supabase.apply_migration",
        "apply_count": 1,
        "reapply_allowed": False,
        "execute_sql_used_for_dml_or_ddl": False,
        "live_cross_tenant_exploit_performed": False,
        "provider_called": False,
        "customer_data_used": False,
        "deployment_action_performed": False,
    }, "remote apply")

    require(authority.get("fresh_pre_apply_remote_receipt", {}), {
        "observed_at_utc": "2026-08-24T20:44:26.904279+00:00",
        "stage52_remote_migration_present": False,
        "auth_users": 0,
        "organizations": 0,
        "students": 0,
        "v2_anon_execute": False,
        "v2_authenticated_execute": True,
        "v2_service_role_execute": True,
        "v1_anon_execute": False,
        "v1_authenticated_execute": False,
        "v1_service_role_execute": True,
        "remote_contains_student_not_found": True,
        "remote_contains_org_manager_required": True,
        "remote_contains_target_unavailable": False,
    }, "pre-apply receipt")

    require(authority.get("fresh_post_apply_remote_receipt", {}), {
        "observed_at_utc": "2026-08-24T20:45:14.762907+00:00",
        "auth_users": 0,
        "organizations": 0,
        "students": 0,
        "v2_anon_execute": False,
        "v2_authenticated_execute": True,
        "v2_service_role_execute": True,
        "v1_anon_execute": False,
        "v1_authenticated_execute": False,
        "v1_service_role_execute": True,
        "remote_contains_student_not_found": False,
        "remote_contains_org_manager_required": False,
        "remote_contains_target_unavailable": True,
        "remote_contains_combined_membership_join": True,
    }, "post-apply receipt")

    require(authority.get("security_invariants", {}), {
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
        "hashed_at_rest_token_contract_preserved": True,
        "thirty_day_expiry_preserved": True,
        "security_event_insert_preserved": True,
        "real_customer_data_used": False,
    }, "security invariants")

    require(authority.get("migration_ledger", {}), {
        "baseline_main_sha": FINAL_BASELINE,
        "observed_at_utc": FINAL_OBSERVED,
        "stage52_remote_version": REMOTE_VERSION,
        "stage52_repo_only_count": 0,
        "historical_stage17_remote_only_count": 3,
        "other_repo_only_count": 0,
    }, "migration ledger receipt")

    require(authority.get("gates", {}), {
        "stage52_target_privacy_hardening": "PASS_REMOTE_RECONCILED",
        "security_advisor_reconciliation": "PASS_INTENTIONAL_AUTHENTICATED_MANAGER_WRAPPER_TARGET_PRIVACY_HARDENED",
        "production_deployment": "DENIED",
        "incident_response": "DENIED",
        "controlled_launch": "DENIED",
        "paid_media": "DENIED",
        "launch": "DENIED",
    }, "gates")

    serialized = json.dumps(authority, sort_keys=True).lower()
    for key in ('"api_key"', '"access_token"', '"password"', '"webhook_token"', '"credential_secret_value"'):
        if key in serialized:
            fail(f"secret-bearing key found: {key}")

    print("STAGE52_STUDENT_ISSUANCE_TARGET_PRIVACY_FINAL_RECONCILIATION=PASS")
    print(f"FINAL_BASELINE_MAIN_SHA={FINAL_BASELINE}")
    print(f"STAGE52_REMOTE_VERSION={REMOTE_VERSION}")
    print("STAGE52_REPO_ONLY_COUNT=0")
    print("STUDENT_ID_EXISTENCE_ORACLE=CLOSED")
    print("AUTHENTICATED_MANAGER_WRAPPER=PRESERVED")
    print("CUSTOMER_DATA_USED=false")
    print("LAUNCH_GATE=DENIED")


if __name__ == "__main__":
    main()
