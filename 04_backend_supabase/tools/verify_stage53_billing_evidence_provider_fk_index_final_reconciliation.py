from __future__ import annotations

import hashlib
import json
from pathlib import Path

from stage53_billing_evidence_migration_frontier import (
    FINAL_BASELINE,
    FINAL_OBSERVED,
    NAME,
    REMOTE_VERSION,
    divergences,
    remote_map,
    state,
    to_promotion,
)

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
LEDGER = BACKEND / "migration_ledger_authority.json"
AUTHORITY = BACKEND / "stage53_billing_evidence_provider_fk_index_final_authority.json"
PROMOTION = BACKEND / "stage53_billing_evidence_provider_fk_index_promotion_authority.json"
CANDIDATE = BACKEND / "operations/stage53_billing_evidence_provider_fk_index_candidate.sql"
MIGRATION = BACKEND / "migrations/20260824211500_stage53_billing_evidence_provider_fk_index_hardening.sql"
EXPECTED_BLOB = "af05593cbb3dc35e692c35700d9f44e2b65c8875"
FAILURE_CLASS = "BGF-STAGE53-FINAL-REMOTE-RECONCILIATION-GUARD-505"


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE53_BILLING_EVIDENCE_PROVIDER_FK_INDEX_FINAL_RECONCILIATION=FAIL\n"
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
            fail("migration ledger is not exact Stage53 final frontier")
        if state(to_promotion(ledger)) != "promotion":
            fail("historical Stage53 promotion projection invalid")
    except ValueError as exc:
        fail(str(exc))

    require(
        ledger,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "baseline_main_sha": FINAL_BASELINE,
            "observed_at_utc": FINAL_OBSERVED,
            "source": "Supabase.list_migrations+Supabase.execute_sql",
            "comparison_key": "migration_name",
        },
        "final ledger",
    )
    if remote_map(ledger).get(NAME) != REMOTE_VERSION:
        fail("Stage53 remote migration version drift")
    remote_only, repo_only = divergences(ledger)
    if len(remote_only) != 3 or repo_only:
        fail("final divergence frontier drift")

    if blob(CANDIDATE) != EXPECTED_BLOB or blob(MIGRATION) != EXPECTED_BLOB:
        fail("candidate/migration blob drift")
    if CANDIDATE.read_bytes() != MIGRATION.read_bytes():
        fail("candidate/migration exact-byte invariant failed")

    require(
        promotion,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "stage": "STAGE53_BILLING_EVIDENCE_PROVIDER_FK_INDEX_PROMOTION",
            "baseline_main_sha": "21eead9f99236f2bb1711b3d3356cfc1d79751c2",
            "current_state": "REPO_ONLY_VERSIONED_MIGRATION_EXACT_CANDIDATE_NO_REMOTE_APPLY",
        },
        "promotion authority",
    )

    require(
        promotion.get("migration", {}),
        {
            "name": NAME,
            "file": "04_backend_supabase/migrations/20260824211500_stage53_billing_evidence_provider_fk_index_hardening.sql",
            "git_blob_sha": EXPECTED_BLOB,
            "exact_candidate_blob_reused": True,
            "repo_only": True,
            "remote_apply_count": 0,
            "apply_allowed_before_green_merge": False,
            "apply_method_after_green_merge": "Supabase.apply_migration",
            "execute_sql_for_dml_or_ddl_allowed": False,
        },
        "promotion migration",
    )

    require(
        authority,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "stage": "STAGE53_BILLING_EVIDENCE_PROVIDER_FK_INDEX_FINAL_RECONCILIATION",
            "baseline_main_sha": FINAL_BASELINE,
            "current_state": "PROVIDER_FK_INDEX_REMOTE_APPLIED_UNINDEXED_FK_LINT_CLEARED_ZERO_CUSTOMER_DATA_PROVIDER_STILL_PENDING",
        },
        "final authority",
    )

    require(
        authority.get("candidate", {}),
        {
            "file": "04_backend_supabase/operations/stage53_billing_evidence_provider_fk_index_candidate.sql",
            "git_blob_sha": EXPECTED_BLOB,
            "merged_by_pr": 142,
            "merged_main_sha": "21eead9f99236f2bb1711b3d3356cfc1d79751c2",
        },
        "candidate receipt",
    )

    require(
        authority.get("promotion", {}),
        {
            "pull_request": 143,
            "head_sha": "a38c47696ced49365f917c2e176eaa751d093ea4",
            "merge_main_sha": FINAL_BASELINE,
            "migration_file": "04_backend_supabase/migrations/20260824211500_stage53_billing_evidence_provider_fk_index_hardening.sql",
            "migration_git_blob_sha": EXPECTED_BLOB,
            "candidate_git_blob_sha": EXPECTED_BLOB,
            "exact_candidate_blob_reused": True,
            "first_promotion_run": 32779066227,
            "first_promotion_result": "FAIL_STAGE52_PROMOTION_HISTORICAL_PROJECTION_RETAINED_FUTURE_REPO_ONLY",
            "corrected_promotion_run": 32779184039,
            "corrected_promotion_result": "SUCCESS",
            "flutter_quality_gate_run": 32779184019,
            "flutter_quality_gate_result": "SUCCESS",
            "stage52_promotion_future_frontier_guard_repaired": True,
            "consumed_live_proofs_reexecuted": False,
        },
        "promotion receipt",
    )

    require(
        authority.get("remote_apply", {}),
        {
            "migration_name": NAME,
            "remote_version": REMOTE_VERSION,
            "applied_via": "Supabase.apply_migration",
            "apply_count": 1,
            "reapply_allowed": False,
            "execute_sql_used_for_dml_or_ddl": False,
            "index_drop_performed": False,
            "provider_activation_performed": False,
            "provider_called": False,
            "customer_data_used": False,
        },
        "remote apply",
    )

    require(
        authority.get("fresh_post_apply_remote_receipt", {}),
        {
            "observed_at_utc": "2026-08-24T21:28:44.870436+00:00",
            "billing_evidence_rows": 0,
            "auth_users": 0,
            "organizations": 0,
            "runtime_role_table_grant_count": 0,
            "provider_code_index_present": True,
            "provider_code_index_definition": "CREATE INDEX billing_provider_external_evidence_provider_code_idx ON private.billing_provider_external_evidence USING btree (provider_code)",
            "unindexed_foreign_key_lint_present": False,
            "new_index_reported_unused": True,
            "unused_index_is_drop_authority": False,
            "asaas_state": "selected_pending_credentials",
            "asaas_activated_at": None,
            "stage52_target_privacy_preserved": True,
            "remote_mutation_after_apply": False,
        },
        "post-apply receipt",
    )

    require(
        authority.get("migration_ledger", {}),
        {
            "comparison_key": "migration_name",
            "baseline_main_sha": FINAL_BASELINE,
            "observed_at_utc": FINAL_OBSERVED,
            "stage53_remote_version": REMOTE_VERSION,
            "stage53_repo_only_count": 0,
            "historical_stage17_remote_only_count": 3,
            "other_repo_only_count": 0,
            "undeclared_divergence_allowed": False,
        },
        "migration ledger receipt",
    )

    require(
        authority.get("performance_policy", {}),
        {
            "unindexed_foreign_key_fixed": True,
            "covering_index_added": True,
            "existing_indexes_removed": False,
            "unused_index_lints_removed": False,
            "future_index_removal_requires_representative_workload_evidence": True,
        },
        "performance policy",
    )

    require(
        authority.get("security_and_product_invariants", {}),
        {
            "foreign_key_definition_changed": False,
            "billing_evidence_rows_changed": False,
            "runtime_grants_changed": False,
            "billing_provider_state_changed": False,
            "stage52_student_target_privacy_changed": False,
            "security_definer_authenticated_manager_boundary_changed": False,
            "billing_provider_credentials_ready": False,
            "provider_activation_performed": False,
            "provider_call_performed": False,
        },
        "security/product invariants",
    )

    require(
        authority.get("gates", {}),
        {
            "stage53_hardening": "PASS_REMOTE_RECONCILED",
            "billing_provider_credentials": "DENIED_AWAITING_REAL_ASAAS_PRODUCTION_OPERATOR_EVIDENCE",
            "provider_activation": "DENIED",
            "provider_call": "DENIED",
            "production_deployment": "DENIED",
            "incident_response": "DENIED",
            "controlled_launch": "DENIED",
            "paid_media": "DENIED",
            "launch": "DENIED",
        },
        "gates",
    )

    serialized = json.dumps(authority, sort_keys=True).lower()
    for key in (
        '"api_key"',
        '"access_token"',
        '"password"',
        '"webhook_token"',
        '"credential_secret_value"',
        '"asaas_api_key"',
    ):
        if key in serialized:
            fail(f"secret-bearing key found: {key}")

    print("STAGE53_BILLING_EVIDENCE_PROVIDER_FK_INDEX_FINAL_RECONCILIATION=PASS")
    print(f"FINAL_BASELINE_MAIN_SHA={FINAL_BASELINE}")
    print(f"STAGE53_REMOTE_VERSION={REMOTE_VERSION}")
    print("STAGE53_REPO_ONLY_COUNT=0")
    print("PROVIDER_CODE_INDEX_PRESENT=true")
    print("UNINDEXED_FOREIGN_KEY_LINT_PRESENT=false")
    print("UNUSED_INDEX_IS_DROP_AUTHORITY=false")
    print("BILLING_PROVIDER_ACTIVATED=false")
    print("CUSTOMER_DATA_USED=false")
    print("LAUNCH_GATE=DENIED")


if __name__ == "__main__":
    main()
