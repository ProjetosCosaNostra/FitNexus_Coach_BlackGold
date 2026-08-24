from __future__ import annotations

import hashlib
import json
from pathlib import Path

from stage40_billing_migration_frontier import FINAL_BASELINE, FINAL_OBSERVED, NAME, REMOTE_VERSION, divergences, remote_map, state, to_promotion

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
LEDGER = BACKEND / "migration_ledger_authority.json"
AUTHORITY = BACKEND / "stage40_billing_production_environment_interlock_final_authority.json"
PROMOTION = BACKEND / "stage40_billing_production_environment_interlock_promotion_authority.json"
CANDIDATE = BACKEND / "operations" / "stage40_billing_production_environment_interlock_candidate.sql"
MIGRATION = BACKEND / "migrations" / "20260824003000_stage40_billing_production_environment_interlock.sql"
EXPECTED_BLOB = "9900408bec1b7d60f40c39f4e97e5e8c0c1c96cf"
FAILURE_CLASS = "BGF-STAGE40-BILLING-REMOTE-RECONCILIATION-367"


def fail(detail: str) -> None:
    raise SystemExit(f"STAGE40_BILLING_PRODUCTION_ENVIRONMENT_INTERLOCK_FINAL_RECONCILIATION=FAIL\nFAILURE_CLASS={FAILURE_CLASS}\nDETAIL={detail}")


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
    for key, val in expected.items():
        if mapping.get(key) != val:
            fail(f"{label} drift: {key}; expected={val!r} actual={mapping.get(key)!r}")


def main() -> None:
    ledger = load(LEDGER)
    authority = load(AUTHORITY)
    promotion = load(PROMOTION)
    try:
        if state(ledger) != "final":
            fail("migration ledger is not exact Stage40 final frontier")
        if state(to_promotion(ledger)) != "promotion":
            fail("historical Stage40 promotion projection invalid")
    except ValueError as exc:
        fail(str(exc))

    require(ledger, {"schema_version":1,"project_ref":"mceukeondizkwlpfxzgf","baseline_main_sha":FINAL_BASELINE,"observed_at_utc":FINAL_OBSERVED,"source":"Supabase.list_migrations+Supabase.execute_sql"}, "final ledger")
    if remote_map(ledger).get(NAME) != REMOTE_VERSION:
        fail("Stage40 remote migration version drift")
    remote_only, repo_only = divergences(ledger)
    if len(remote_only) != 3 or repo_only:
        fail("final divergence frontier drift")
    if blob(CANDIDATE) != EXPECTED_BLOB or blob(MIGRATION) != EXPECTED_BLOB or CANDIDATE.read_bytes() != MIGRATION.read_bytes():
        fail("candidate/migration exact blob invariant failed")

    require(promotion, {"schema_version":1,"project_ref":"mceukeondizkwlpfxzgf","stage":"STAGE40_BILLING_PRODUCTION_ENVIRONMENT_INTERLOCK_PROMOTION","baseline_main_sha":"f3288d465cf6f3457ce2403b470a2546b5672d0f"}, "promotion authority")
    require(authority, {"schema_version":1,"project_ref":"mceukeondizkwlpfxzgf","stage":"STAGE40_BILLING_PRODUCTION_ENVIRONMENT_INTERLOCK_FINAL_RECONCILIATION","baseline_main_sha":FINAL_BASELINE,"current_state":"PRODUCTION_ENVIRONMENT_INTERLOCK_REMOTE_APPLIED_PROVIDER_STILL_PENDING_ZERO_EXTERNAL_EVIDENCE_BILLING_GATE_BLOCKED"}, "final authority")
    require(authority.get("repository_promotion", {}), {"pull_request":126,"head_sha":"63369595bac880d98c5c145cde45a13609c77214","merge_main_sha":FINAL_BASELINE,"migration_git_blob_sha":EXPECTED_BLOB,"candidate_git_blob_sha":EXPECTED_BLOB,"exact_candidate_blob_reused":True,"stage40_workflow_run":32676993407,"stage40_workflow_result":"SUCCESS","flutter_quality_gate_run":32676993377,"flutter_quality_gate_result":"SUCCESS","consumed_live_proofs_reexecuted":False}, "repository promotion")
    require(authority.get("remote_apply", {}), {"migration_name":NAME,"remote_version":REMOTE_VERSION,"applied_via":"Supabase.apply_migration","apply_count":1,"reapply_allowed":False,"execute_sql_used_for_dml_or_ddl":False,"provider_activation_performed":False,"provider_called":False,"external_evidence_attested":False,"customer_data_used":False}, "remote apply")
    receipt = authority.get("fresh_post_apply_remote_receipt", {})
    require(receipt, {"observed_at_utc":"2026-08-24T00:37:12.870108+00:00","external_evidence_rows":0,"auth_users":0,"organizations":0,"activation_external_evidence_interlock":True,"activation_production_interlock":True,"readiness_production_interlock":True,"tracking_core_ready":True,"pricing_experiment_ready":True,"billing_provider_credentials_ready":False,"manual_evidence_ready":0,"manual_evidence_total":6,"mandatory_gate_total":9,"ready_mandatory_gate_total":2,"blocking_gate_total":7}, "post-apply receipt")
    require(receipt.get("selection", {}), {"scope":"BR_V1","provider_code":"asaas","state":"selected_pending_credentials","evidence_version":"2026-08-18-official-docs-v1","activated_at":None}, "selection")
    expected_exec = {"anon":False,"authenticated":False,"service_role":True}
    if receipt.get("activation_execute") != expected_exec or receipt.get("readiness_authority_execute") != expected_exec:
        fail("service-role-only function privilege boundary drift")
    require(authority.get("security_invariants", {}), {"sandbox_evidence_can_activate_br_v1":False,"br_v1_asaas_activation_requires_asaas_production":True,"activation_still_requires_external_credential_evidence":True,"billing_launch_readiness_requires_proof_complete":True,"billing_launch_readiness_requires_asaas_production":True,"activation_execute_service_role_only":True,"readiness_authority_execute_service_role_only":True,"activation_alone_can_promote_billing_launch_gate":False,"secret_values_stored_in_repository":False}, "security invariants")
    require(authority.get("gates", {}), {"stage40_hardening":"PASS_REMOTE_RECONCILED","billing_provider_credentials":"DENIED_AWAITING_REAL_ASAAS_PRODUCTION_OPERATOR_EVIDENCE","provider_activation":"DENIED","provider_call":"DENIED","controlled_launch":"DENIED","production_deployment":"DENIED","incident_response":"DENIED","paid_media":"DENIED","launch":"DENIED"}, "gates")

    serialized = json.dumps(authority, sort_keys=True).lower()
    for key in ('"api_key"','"access_token"','"password"','"webhook_token"','"credential_secret_value"'):
        if key in serialized:
            fail(f"secret-bearing key found: {key}")
    print("STAGE40_BILLING_PRODUCTION_ENVIRONMENT_INTERLOCK_FINAL_RECONCILIATION=PASS")
    print(f"FINAL_BASELINE_MAIN_SHA={FINAL_BASELINE}")
    print(f"STAGE40_REMOTE_VERSION={REMOTE_VERSION}")
    print("STAGE40_REPO_ONLY_COUNT=0")
    print("ASAAS_STATE=SELECTED_PENDING_CREDENTIALS")
    print("ASAAS_PRODUCTION_INTERLOCK=PASS")
    print("BILLING_GATE=DENIED_AWAITING_REAL_ASAAS_PRODUCTION_OPERATOR_EVIDENCE")


if __name__ == "__main__":
    main()
