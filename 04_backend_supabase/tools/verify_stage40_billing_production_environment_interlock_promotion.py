from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage40_billing_production_environment_interlock_promotion_authority.json"
CANDIDATE_AUTHORITY = BACKEND / "stage40_billing_production_environment_interlock_candidate_authority.json"
LEDGER = BACKEND / "migration_ledger_authority.json"
CANDIDATE = BACKEND / "operations" / "stage40_billing_production_environment_interlock_candidate.sql"
MIGRATION = BACKEND / "migrations" / "20260824003000_stage40_billing_production_environment_interlock.sql"

BASELINE_MAIN = "f3288d465cf6f3457ce2403b470a2546b5672d0f"
OBSERVED_AT = "2026-08-24T00:27:03.610215+00:00"
NAME = "stage40_billing_production_environment_interlock"
EXPECTED_BLOB = "9900408bec1b7d60f40c39f4e97e5e8c0c1c96cf"
FAILURE_CLASS = "BGF-STAGE40-BILLING-PROMOTION-GUARD-364"


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE40_BILLING_PRODUCTION_ENVIRONMENT_INTERLOCK_PROMOTION=FAIL\n"
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


def require(mapping: dict, expected: dict, label: str) -> None:
    if not isinstance(mapping, dict):
        fail(f"{label} must be object")
    for key, value in expected.items():
        if mapping.get(key) != value:
            fail(f"{label} drift: {key}; expected={value!r} actual={mapping.get(key)!r}")


def git_blob_sha(path: Path) -> str:
    import hashlib
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def main() -> None:
    authority = load(AUTHORITY)
    candidate_authority = load(CANDIDATE_AUTHORITY)
    ledger = load(LEDGER)

    if CANDIDATE.read_bytes() != MIGRATION.read_bytes():
        fail("versioned migration is not byte-identical to merged Stage40 candidate")
    if git_blob_sha(CANDIDATE) != EXPECTED_BLOB or git_blob_sha(MIGRATION) != EXPECTED_BLOB:
        fail("candidate/migration blob drifted")

    require(authority, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE40_BILLING_PRODUCTION_ENVIRONMENT_INTERLOCK_PROMOTION",
        "baseline_main_sha": BASELINE_MAIN,
        "current_state": "REPO_ONLY_VERSIONED_MIGRATION_EXACT_CANDIDATE_NO_REMOTE_APPLY_NO_PROVIDER_ACTIVATION",
    }, "promotion authority")

    require(candidate_authority, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE40_BILLING_PRODUCTION_ENVIRONMENT_INTERLOCK_CANDIDATE",
        "current_state": "REPO_ONLY_CANDIDATE_SANDBOX_CANNOT_PROMOTE_BR_V1_PRODUCTION_BINDING_NOT_YET_REMOTE",
    }, "candidate authority")
    require(candidate_authority.get("candidate", {}), {
        "file": "04_backend_supabase/operations/stage40_billing_production_environment_interlock_candidate.sql",
        "location_class": "OPERATIONS_CANDIDATE_NOT_MIGRATION",
        "remote_apply_allowed": False,
        "direct_apply_allowed": False,
        "promotion_requires_separate_versioned_migration_pr": True,
    }, "candidate promotion boundary")

    require(authority.get("candidate", {}), {
        "file": "04_backend_supabase/operations/stage40_billing_production_environment_interlock_candidate.sql",
        "git_blob_sha": EXPECTED_BLOB,
        "already_green_merged": True,
        "merged_by_pr": 125,
        "merged_main_sha": BASELINE_MAIN,
    }, "candidate pin")
    require(authority.get("migration", {}), {
        "name": NAME,
        "file": "04_backend_supabase/migrations/20260824003000_stage40_billing_production_environment_interlock.sql",
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
        "stage40_remote_migration_present": False,
        "external_evidence_rows": 0,
        "auth_users": 0,
        "organizations": 0,
        "activation_remote_contains_stage38_external_evidence_interlock": True,
        "activation_remote_contains_production_environment_interlock": False,
        "readiness_remote_contains_production_environment_interlock": False,
        "remote_mutation_performed": False,
        "provider_called": False,
        "customer_data_used": False,
    }, "fresh remote preflight")
    require(authority["fresh_remote_preflight"].get("selection", {}), {
        "scope": "BR_V1",
        "provider_code": "asaas",
        "state": "selected_pending_credentials",
        "evidence_version": "2026-08-18-official-docs-v1",
        "activated_at": None,
    }, "provider selection")

    require(ledger, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "baseline_main_sha": BASELINE_MAIN,
        "observed_at_utc": "2026-08-24T00:27:03.610215Z",
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
    repo_only = sorted(
        row.get("name") for row in divergences
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    )
    if remote_only != [
        "stage17_pricing_advisor_guard",
        "stage17_pricing_advisor_reconciliation",
        "stage17_pricing_guard_indexes_marker",
    ]:
        fail("historical Stage17 remote-only frontier drifted")
    if repo_only != [NAME]:
        fail("Stage40 must be the only repo-only migration divergence")

    remote_rows = ledger.get("remote_migrations", [])
    if not isinstance(remote_rows, list):
        fail("remote_migrations must be array")
    remote_names = [row.get("name") for row in remote_rows if isinstance(row, dict)]
    if NAME in remote_names:
        fail("promotion ledger must not claim Stage40 was remotely applied")
    if remote_names.count("stage38_billing_evidence_bound_activation") != 1:
        fail("Stage38 remote frontier missing or duplicated")

    sql = MIGRATION.read_text(encoding="utf-8")
    required = (
        "BILLING_PROVIDER_EXTERNAL_CREDENTIAL_EVIDENCE_REQUIRED",
        "BILLING_PROVIDER_PRODUCTION_ENVIRONMENT_EVIDENCE_REQUIRED",
        "v_external_evidence.provider_environment_id <> 'asaas-production'",
        "e.provider_environment_id='asaas-production'",
        "e.state='proof_complete'",
        "grant execute on function public.activate_billing_provider_selection(text,text,text) to service_role",
        "grant execute on function private.get_controlled_launch_readiness_authority() to service_role",
        "'production_billing_environment_required',true",
        "'paid_ads_auto_launch',false",
    )
    for fragment in required:
        if fragment not in sql:
            fail(f"required hardening fragment missing: {fragment}")

    forbidden = (
        "insert into private.billing_provider_external_evidence",
        "update private.billing_provider_external_evidence",
        "delete from private.billing_provider_external_evidence",
        "select public.activate_billing_provider_selection(",
    )
    lower_sql = sql.lower()
    for fragment in forbidden:
        if fragment.lower() in lower_sql:
            fail(f"promotion migration contains forbidden evidence/activation action: {fragment}")

    require(authority.get("promotion_boundaries", {}), {
        "supabase_mutation_performed": False,
        "provider_call_performed": False,
        "provider_activation_performed": False,
        "external_evidence_attested": False,
        "customer_data_used": False,
        "credential_secret_recorded": False,
        "billing_gate_promoted": False,
        "controlled_launch_promoted": False,
        "production_deployment_allowed": False,
        "incident_response_promotion_allowed": False,
        "paid_media_allowed": False,
        "stage35_proof_reexecution_allowed": False,
    }, "promotion boundaries")

    require(authority.get("gates", {}), {
        "stage40_migration_promotion": "PENDING_CI",
        "stage40_remote_apply": "DENIED_UNTIL_GREEN_MERGE",
        "billing_provider_credentials": "DENIED_AWAITING_REAL_ASAAS_PRODUCTION_OPERATOR_EVIDENCE",
        "provider_activation": "DENIED",
        "provider_call": "DENIED",
        "controlled_launch": "DENIED",
        "production_deployment": "DENIED",
        "incident_response": "DENIED",
        "paid_media": "DENIED",
        "launch": "DENIED",
    }, "gates")

    serialized = json.dumps(authority, sort_keys=True).lower()
    for forbidden_key in ('"api_key"', '"access_token"', '"password"', '"webhook_token"', '"credential_secret_value"'):
        if forbidden_key in serialized:
            fail(f"secret-bearing key found: {forbidden_key}")

    stage40_migrations = list((BACKEND / "migrations").glob("*stage40*.sql"))
    if stage40_migrations != [MIGRATION]:
        fail("unexpected Stage40 migration set")

    print("STAGE40_BILLING_PRODUCTION_ENVIRONMENT_INTERLOCK_PROMOTION=PASS")
    print(f"BASELINE_MAIN_SHA={BASELINE_MAIN}")
    print(f"MIGRATION_BLOB={EXPECTED_BLOB}")
    print("EXACT_CANDIDATE_BLOB_REUSED=PASS")
    print("STAGE40_LEDGER_STATE=REPO_ONLY")
    print("REMOTE_APPLY_ALLOWED=false_until_green_merge")
    print("PROVIDER_ACTIVATION=false")
    print("BILLING_GATE=DENIED_AWAITING_REAL_ASAAS_PRODUCTION_OPERATOR_EVIDENCE")


if __name__ == "__main__":
    main()
