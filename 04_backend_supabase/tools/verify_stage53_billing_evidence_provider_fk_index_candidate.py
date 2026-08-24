from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage53_billing_evidence_provider_fk_index_candidate_authority.json"
CANDIDATE = BACKEND / "operations/stage53_billing_evidence_provider_fk_index_candidate.sql"
STAGE38 = BACKEND / "migrations/20260823174500_stage38_billing_evidence_bound_activation.sql"
STAGE52_FINAL = BACKEND / "stage52_student_issuance_target_privacy_final_authority.json"
MIGRATIONS = BACKEND / "migrations"

FAILURE_CLASS = "BGF-STAGE53-BILLING-EVIDENCE-FK-INDEX-GUARD-498"
BASELINE_MAIN = "64d9ddbbb010a0f11895a99b998fce479db2fb0c"
CANDIDATE_BLOB = "af05593cbb3dc35e692c35700d9f44e2b65c8875"
STAGE38_BLOB = "a09aa83eb6eb24739ad0a73b7c08db3185eb4f63"
STAGE52_FINAL_BLOB = "075824c55ce463a0863211e4bffecdd8b111a4e9"
EXPECTED_INDEX = "billing_provider_external_evidence_provider_code_idx"


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE53_BILLING_EVIDENCE_PROVIDER_FK_INDEX_CANDIDATE=FAIL\n"
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


def blob(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def require(mapping: dict, expected: dict, label: str) -> None:
    if not isinstance(mapping, dict):
        fail(f"{label} must be object")
    for key, value in expected.items():
        if mapping.get(key) != value:
            fail(f"{label} drift: {key}; expected={value!r}; actual={mapping.get(key)!r}")


def executable_sql(text: str) -> str:
    lines = []
    for line in text.splitlines():
        if line.lstrip().startswith("--"):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def main() -> None:
    authority = load(AUTHORITY)
    stage52 = load(STAGE52_FINAL)

    if blob(CANDIDATE) != CANDIDATE_BLOB:
        fail("candidate Git blob drift")
    if blob(STAGE38) != STAGE38_BLOB:
        fail("Stage38 evidence-table migration blob drift")
    if blob(STAGE52_FINAL) != STAGE52_FINAL_BLOB:
        fail("Stage52 final authority blob drift")

    require(authority, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE53_BILLING_EVIDENCE_PROVIDER_FK_INDEX_CANDIDATE",
        "baseline_main_sha": BASELINE_MAIN,
        "current_state": "REPO_ONLY_INDEX_CANDIDATE_PERFORMANCE_LINT_CONFIRMED_NO_REMOTE_APPLY",
    }, "Stage53 authority")
    require(stage52, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE52_STUDENT_ISSUANCE_TARGET_PRIVACY_FINAL_RECONCILIATION",
        "current_state": "TARGET_PRIVACY_HARDENING_REMOTE_APPLIED_ZERO_CUSTOMER_DATA_PRIVILEGES_PRESERVED",
    }, "Stage52 final authority")

    require(authority.get("candidate", {}), {
        "file": "04_backend_supabase/operations/stage53_billing_evidence_provider_fk_index_candidate.sql",
        "git_blob_sha": CANDIDATE_BLOB,
        "index_name": EXPECTED_INDEX,
        "schema": "private",
        "table": "billing_provider_external_evidence",
        "columns": ["provider_code"],
        "method": "btree",
        "if_not_exists": True,
        "migration_created": False,
        "remote_apply_allowed": False,
    }, "candidate authority")

    receipt = authority.get("fresh_remote_read_only_receipt", {})
    require(receipt, {
        "observed_at_utc": "2026-08-24T21:05:37.446284+00:00",
        "provider_code_fk_definition": "FOREIGN KEY (provider_code) REFERENCES billing_provider_registry(provider_code) ON UPDATE RESTRICT ON DELETE RESTRICT",
        "provider_code_leading_index_present": False,
        "table_row_count": 0,
        "runtime_role_table_grants": [],
        "asaas_scope": "BR_V1",
        "asaas_provider": "asaas",
        "asaas_state": "selected_pending_credentials",
        "asaas_activated_at": None,
        "remote_mutation_performed": False,
    }, "fresh remote receipt")
    lint = receipt.get("unindexed_foreign_key_lint", {})
    require(lint, {
        "lint_name": "unindexed_foreign_keys",
        "schema": "private",
        "table": "billing_provider_external_evidence",
        "constraint": "billing_provider_external_evidence_provider_code_fkey",
        "column": "provider_code",
        "present": True,
    }, "performance lint")
    if receipt.get("existing_indexes") != ["billing_provider_external_evidence_pkey(scope,provider_code,evidence_version)"]:
        fail("baseline index inventory drift")

    policy = authority.get("advisor_policy", {})
    require(policy, {
        "fix_unindexed_foreign_key": True,
        "drop_unused_indexes_in_same_stage": False,
        "unused_index_findings_are_removal_authority": False,
    }, "advisor policy")

    contract = authority.get("hardening_contract", {})
    for key in (
        "dedicated_provider_code_leading_index_required",
        "primary_key_is_not_provider_code_leading",
        "foreign_key_definition_unchanged",
        "table_data_unchanged",
        "table_grants_unchanged",
        "billing_provider_state_unchanged",
        "billing_external_evidence_state_unchanged",
    ):
        if contract.get(key) is not True:
            fail(f"hardening invariant drift: {key}")
    for key in (
        "provider_activation_performed",
        "provider_call_performed",
        "controlled_launch_promoted",
        "production_deployment_promoted",
        "paid_media_promoted",
        "launch_promoted",
    ):
        if contract.get(key) is not False:
            fail(f"forbidden authority escalation: {key}")

    sql = executable_sql(CANDIDATE.read_text(encoding="utf-8"))
    normalized = re.sub(r"\s+", " ", sql).strip().lower()
    expected = (
        "create index if not exists billing_provider_external_evidence_provider_code_idx "
        "on private.billing_provider_external_evidence (provider_code);"
    )
    if normalized != expected:
        fail(f"candidate executable SQL is not the exact one-index contract: {normalized!r}")

    for forbidden in (
        "drop index", "alter table", "drop table", "create table", "insert into", "update ",
        "delete from", "grant ", "revoke ", "create or replace function", "alter function",
        "activate_billing_provider", "controlled_launch_gate_evidence",
    ):
        if forbidden in normalized:
            fail(f"forbidden candidate operation present: {forbidden}")

    if list(MIGRATIONS.glob("*stage53*.sql")):
        fail("Stage53 candidate phase must not create a versioned migration")

    gates = authority.get("gates", {})
    require(gates, {
        "stage53_candidate": "PENDING_CI",
        "stage53_migration_promotion": "DENIED_UNTIL_CANDIDATE_GREEN_MERGED",
        "stage53_remote_apply": "DENIED_UNTIL_VERSIONED_MIGRATION_GREEN_MERGED",
        "billing_provider_credentials": "DENIED_AWAITING_REAL_ASAAS_PRODUCTION_OPERATOR_EVIDENCE",
        "production_deployment": "DENIED",
        "incident_response": "DENIED",
        "controlled_launch": "DENIED",
        "paid_media": "DENIED",
        "launch": "DENIED",
    }, "gates")

    print("STAGE53_BILLING_EVIDENCE_PROVIDER_FK_INDEX_CANDIDATE=PASS")
    print("PERFORMANCE_LINT_UNINDEXED_FK=CONFIRMED")
    print(f"CANDIDATE_INDEX={EXPECTED_INDEX}")
    print("INDEX_DROP_PERFORMED=false")
    print("MIGRATION_CREATED=false")
    print("REMOTE_MUTATION=false")
    print("BILLING_PROVIDER_ACTIVATED=false")
    print("LAUNCH_GATE=DENIED")


if __name__ == "__main__":
    main()
