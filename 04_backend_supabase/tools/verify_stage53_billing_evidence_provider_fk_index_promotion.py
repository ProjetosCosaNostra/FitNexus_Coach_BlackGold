from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage53_billing_evidence_provider_fk_index_promotion_authority.json"
CANDIDATE_AUTHORITY = BACKEND / "stage53_billing_evidence_provider_fk_index_candidate_authority.json"
LEDGER = BACKEND / "migration_ledger_authority.json"
CANDIDATE = BACKEND / "operations/stage53_billing_evidence_provider_fk_index_candidate.sql"
MIGRATION = BACKEND / "migrations/20260824211500_stage53_billing_evidence_provider_fk_index_hardening.sql"

BASELINE_MAIN = "21eead9f99236f2bb1711b3d3356cfc1d79751c2"
OBSERVED_AT = "2026-08-24T21:13:52.299927+00:00"
NAME = "stage53_billing_evidence_provider_fk_index_hardening"
EXPECTED_BLOB = "af05593cbb3dc35e692c35700d9f44e2b65c8875"
FAILURE_CLASS = "BGF-STAGE53-PROMOTION-GUARD-503"


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE53_BILLING_EVIDENCE_PROVIDER_FK_INDEX_PROMOTION=FAIL\n"
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
        fail(f"{label} must be object")
    for key, value in expected.items():
        if mapping.get(key) != value:
            fail(f"{label} drift: {key}; expected={value!r}; actual={mapping.get(key)!r}")


def blob(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def executable_sql(text: str) -> str:
    return "\n".join(
        line for line in text.splitlines()
        if not line.lstrip().startswith("--")
    ).strip()


def main() -> None:
    authority = load(AUTHORITY)
    candidate_authority = load(CANDIDATE_AUTHORITY)
    ledger = load(LEDGER)

    if CANDIDATE.read_bytes() != MIGRATION.read_bytes():
        fail("versioned migration is not byte-identical to merged Stage53 candidate")
    if blob(CANDIDATE) != EXPECTED_BLOB or blob(MIGRATION) != EXPECTED_BLOB:
        fail("candidate/migration exact Git blob invariant failed")

    require(authority, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE53_BILLING_EVIDENCE_PROVIDER_FK_INDEX_PROMOTION",
        "baseline_main_sha": BASELINE_MAIN,
        "current_state": "REPO_ONLY_VERSIONED_MIGRATION_EXACT_CANDIDATE_NO_REMOTE_APPLY",
    }, "promotion authority")
    require(candidate_authority, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE53_BILLING_EVIDENCE_PROVIDER_FK_INDEX_CANDIDATE",
        "current_state": "REPO_ONLY_INDEX_CANDIDATE_PERFORMANCE_LINT_CONFIRMED_NO_REMOTE_APPLY",
    }, "candidate authority")
    if blob(CANDIDATE_AUTHORITY) != "0fe3df64afd64bb23ab034300328138cabf0581f":
        fail("sealed Stage53 candidate authority blob drift")

    require(authority.get("candidate", {}), {
        "file": "04_backend_supabase/operations/stage53_billing_evidence_provider_fk_index_candidate.sql",
        "git_blob_sha": EXPECTED_BLOB,
        "already_green_merged": True,
        "merged_by_pr": 142,
        "merged_main_sha": BASELINE_MAIN,
        "candidate_workflow_run": 32778087337,
        "candidate_workflow_result": "SUCCESS",
        "flutter_quality_gate_run": 32778087342,
        "flutter_quality_gate_result": "SUCCESS",
        "consumed_live_proofs_reexecuted": False,
    }, "candidate promotion evidence")
    require(authority.get("migration", {}), {
        "name": NAME,
        "file": "04_backend_supabase/migrations/20260824211500_stage53_billing_evidence_provider_fk_index_hardening.sql",
        "git_blob_sha": EXPECTED_BLOB,
        "exact_candidate_blob_reused": True,
        "repo_only": True,
        "remote_apply_count": 0,
        "apply_allowed_before_green_merge": False,
        "apply_method_after_green_merge": "Supabase.apply_migration",
        "execute_sql_for_dml_or_ddl_allowed": False,
    }, "migration promotion")

    require(authority.get("fresh_remote_preflight", {}), {
        "source": "Supabase.list_migrations+Supabase.execute_sql_read_only+Supabase.get_advisors(performance)",
        "observed_at_utc": OBSERVED_AT,
        "stage53_remote_migration_present": False,
        "provider_code_index_present": False,
        "unindexed_foreign_key_lint_present": True,
        "table_row_count": 0,
        "runtime_role_table_grant_count": 0,
        "asaas_state": "selected_pending_credentials",
        "asaas_activated_at": None,
        "stage52_target_unavailable_present": True,
        "stage52_student_not_found_present": False,
        "stage52_org_manager_required_present": False,
        "remote_mutation_performed": False,
        "customer_data_used": False,
    }, "fresh remote preflight")

    require(ledger, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "baseline_main_sha": BASELINE_MAIN,
        "observed_at_utc": "2026-08-24T21:13:52.299927Z",
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
    repo_only = [
        row for row in divergences
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    ]
    if remote_only != [
        "stage17_pricing_advisor_guard",
        "stage17_pricing_advisor_reconciliation",
        "stage17_pricing_guard_indexes_marker",
    ]:
        fail("historical Stage17 remote-only frontier drift")
    if len(repo_only) != 1 or repo_only[0].get("name") != NAME:
        fail("Stage53 must be unique repo-only migration divergence")
    if repo_only[0].get("related_failure_class") != "BGF-STAGE53-CANDIDATE-DIRECT-APPLY-497":
        fail("Stage53 repo-only prevention class drift")

    remote_rows = ledger.get("remote_migrations", [])
    if not isinstance(remote_rows, list) or len(remote_rows) != 66:
        fail("remote migration frontier count drift")
    remote_names = [row.get("name") for row in remote_rows if isinstance(row, dict)]
    if NAME in remote_names:
        fail("promotion ledger must not claim Stage53 was remotely applied")
    if remote_names.count("stage52_student_issuance_target_privacy_hardening") != 1:
        fail("Stage52 reconciled remote frontier missing or duplicated")

    normalized = re.sub(r"\s+", " ", executable_sql(MIGRATION.read_text(encoding="utf-8"))).strip().lower()
    expected = (
        "create index if not exists billing_provider_external_evidence_provider_code_idx "
        "on private.billing_provider_external_evidence (provider_code);"
    )
    if normalized != expected:
        fail("promoted migration executable SQL drift")
    for forbidden in (
        "drop index", "alter table", "drop table", "create table", "insert into", "update ",
        "delete from", "grant ", "revoke ", "create or replace function", "alter function",
        "activate_billing_provider", "controlled_launch_gate_evidence",
    ):
        if forbidden in normalized:
            fail(f"forbidden promotion operation present: {forbidden}")

    require(authority.get("hardening_contract", {}), {
        "exact_one_index_only": True,
        "index_name": "billing_provider_external_evidence_provider_code_idx",
        "index_schema": "private",
        "index_table": "billing_provider_external_evidence",
        "index_columns": ["provider_code"],
        "drop_unused_indexes_performed": False,
        "foreign_key_definition_changed": False,
        "billing_evidence_rows_changed": False,
        "runtime_grants_changed": False,
        "provider_state_changed": False,
        "provider_activation_performed": False,
        "provider_call_performed": False,
        "stage52_reapplied": False,
    }, "hardening contract")
    require(authority.get("promotion_boundaries", {}), {
        "supabase_mutation_performed": False,
        "customer_data_used": False,
        "privilege_change_performed": False,
        "deployment_action_performed": False,
        "production_deployment_promoted": False,
        "incident_response_promoted": False,
        "controlled_launch_promoted": False,
        "paid_media_promoted": False,
        "launch_promoted": False,
    }, "promotion boundaries")
    require(authority.get("gates", {}), {
        "stage53_migration_promotion": "PENDING_CI",
        "stage53_remote_apply": "DENIED_UNTIL_GREEN_EXACT_MERGE",
        "billing_provider_credentials": "DENIED_AWAITING_REAL_ASAAS_PRODUCTION_OPERATOR_EVIDENCE",
        "production_deployment": "DENIED",
        "incident_response": "DENIED",
        "controlled_launch": "DENIED",
        "paid_media": "DENIED",
        "launch": "DENIED",
    }, "gates")

    print("STAGE53_BILLING_EVIDENCE_PROVIDER_FK_INDEX_PROMOTION=PASS")
    print(f"BASELINE_MAIN_SHA={BASELINE_MAIN}")
    print(f"MIGRATION_BLOB={EXPECTED_BLOB}")
    print("EXACT_CANDIDATE_BLOB_REUSED=PASS")
    print("STAGE53_LEDGER_STATE=REPO_ONLY")
    print("DROP_UNUSED_INDEXES=false")
    print("REMOTE_APPLY_ALLOWED=false_until_green_exact_merge")
    print("REMOTE_MUTATION=false")
    print("LAUNCH_GATE=DENIED")


if __name__ == "__main__":
    main()
