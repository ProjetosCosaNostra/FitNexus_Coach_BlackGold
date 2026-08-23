from __future__ import annotations

import hashlib
import json
from pathlib import Path

from stage38_billing_migration_frontier import (
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
AUTHORITY = BACKEND / "stage38_billing_evidence_bound_activation_final_authority.json"
PROMOTION = BACKEND / "stage38_billing_evidence_bound_activation_promotion_authority.json"
MIGRATION = BACKEND / "migrations" / "20260823174500_stage38_billing_evidence_bound_activation.sql"

EXPECTED_BLOB = "a09aa83eb6eb24739ad0a73b7c08db3185eb4f63"
FAILURE_CLASS = "BGF-STAGE38-BILLING-REMOTE-RECONCILIATION-348"


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE38_BILLING_EVIDENCE_BOUND_ACTIVATION_FINAL_RECONCILIATION=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\n"
        f"DETAIL={detail}"
    )


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to read {path.relative_to(ROOT)}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"expected object: {path.relative_to(ROOT)}")
    return value


def blob(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def require(mapping: dict, expected: dict, label: str) -> None:
    if not isinstance(mapping, dict):
        fail(f"{label} must be object")
    for key, expected_value in expected.items():
        if mapping.get(key) != expected_value:
            fail(f"{label} drift: {key}; expected={expected_value!r} actual={mapping.get(key)!r}")


def main() -> None:
    ledger = load(LEDGER)
    authority = load(AUTHORITY)
    promotion = load(PROMOTION)

    try:
        if state(ledger) != "final":
            fail("migration ledger is not exact Stage38 final frontier")
        promotion_projection = to_promotion(ledger)
        if state(promotion_projection) != "promotion":
            fail("historical promotion projection invalid")
    except ValueError as exc:
        fail(f"Stage38 frontier validation failed: {exc}")

    require(ledger, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "baseline_main_sha": FINAL_BASELINE,
        "observed_at_utc": FINAL_OBSERVED,
        "source": "Supabase.list_migrations+Supabase.execute_sql",
    }, "final ledger")
    remote = remote_map(ledger)
    if remote.get(NAME) != REMOTE_VERSION:
        fail("Stage38 remote migration version drifted")
    remote_only, repo_only = divergences(ledger)
    if len(remote_only) != 3:
        fail("historical Stage17 remote-only count must remain three")
    if repo_only:
        fail("final Stage38 ledger must have no repo-only divergence")

    if blob(MIGRATION) != EXPECTED_BLOB:
        fail("merged Stage38 migration blob drifted")

    require(promotion, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE38_BILLING_EVIDENCE_BOUND_ACTIVATION_PROMOTION",
        "baseline_main_sha": "5ba7caa8dde7d5154b8d20da11c18274e83f41a8",
        "current_state": "REPO_ONLY_HARDENING_CANDIDATE_NO_PROVIDER_ACTIVATION_NO_EXTERNAL_EVIDENCE_ATTESTED",
    }, "promotion authority")
    require(promotion.get("migration", {}), {
        "name": NAME,
        "git_blob_sha": EXPECTED_BLOB,
        "repo_only": True,
        "remote_apply_count": 0,
        "apply_allowed_before_green_merge": False,
        "apply_method_after_green_merge": "Supabase.apply_migration",
        "execute_sql_for_dml_or_ddl_allowed": False,
    }, "historical promotion migration")

    require(authority, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE38_BILLING_EVIDENCE_BOUND_ACTIVATION_FINAL_RECONCILIATION",
        "baseline_main_sha": FINAL_BASELINE,
        "current_state": "HARDENING_REMOTE_APPLIED_ZERO_EXTERNAL_EVIDENCE_PROVIDER_STILL_PENDING_BILLING_GATE_BLOCKED",
    }, "final authority")

    required_failure_classes = {
        "BGF-STAGE37-BILLING-PREMATURE-ACTIVATION-319",
        "BGF-STAGE37-BILLING-EVIDENCE-BINDING-GAP-320",
        "BGF-STAGE38-BILLING-RUNTIME-SELF-ATTESTATION-333",
        "BGF-STAGE38-BILLING-ACTIVATION-BEFORE-CREDENTIAL-EVIDENCE-334",
        "BGF-STAGE38-BILLING-LAUNCH-BEFORE-PROOF-COMPLETE-335",
        "BGF-STAGE38-BILLING-EVIDENCE-SECRET-LEAK-336",
        FAILURE_CLASS,
    }
    if set(authority.get("failure_classes", [])) != required_failure_classes:
        fail("final failure-class set drifted")

    require(authority.get("repository_promotion", {}), {
        "pull_request": 122,
        "head_sha": "be4c5d41ca52fc91eb6560624a57fa49fefcf73c",
        "merge_main_sha": FINAL_BASELINE,
        "migration_git_blob_sha": EXPECTED_BLOB,
        "stage38_workflow_run": 32656021412,
        "stage38_workflow_result": "SUCCESS",
        "flutter_quality_gate_run": 32656021453,
        "flutter_quality_gate_result": "SUCCESS",
        "postgres_compatibility_run": 32656021444,
        "postgres_compatibility_result": "SUCCESS",
        "historical_stage34_stage35_checks_green": True,
        "consumed_live_proofs_reexecuted": False,
    }, "repository promotion")

    require(authority.get("remote_apply", {}), {
        "migration_name": NAME,
        "remote_version": REMOTE_VERSION,
        "applied_via": "Supabase.apply_migration",
        "apply_count": 1,
        "reapply_allowed": False,
        "execute_sql_used_for_dml_or_ddl": False,
        "provider_activation_performed": False,
        "provider_called": False,
        "external_evidence_attested": False,
        "customer_data_used": False,
    }, "remote apply")

    receipt = authority.get("fresh_post_apply_remote_receipt", {})
    require(receipt, {
        "source": "Supabase.list_migrations+Supabase.execute_sql_read_only",
        "observed_at_utc": "2026-08-23T17:52:43.344298+00:00",
        "stage38_table_exists": True,
        "evidence_rows": 0,
        "checkout_intents": 0,
        "webhook_receipts": 0,
        "active_brl_prices": 6,
        "auth_users": 0,
        "organizations": 0,
        "billing_launch_predicate_ready": False,
        "activation_interlock_present": True,
        "readiness_proof_complete_interlock_present": True,
    }, "post-apply receipt")
    require(receipt.get("selection", {}), {
        "scope": "BR_V1",
        "provider_code": "asaas",
        "state": "selected_pending_credentials",
        "evidence_version": "2026-08-18-official-docs-v1",
        "activated_at": None,
    }, "post-apply provider selection")
    require(receipt.get("activation_execute", {}), {
        "anon": False,
        "authenticated": False,
        "service_role": True,
    }, "activation execute privileges")
    expected_table_privs = {"select": False, "insert": False, "update": False, "delete": False}
    for role in ("anon", "authenticated", "service_role"):
        if receipt.get("external_evidence_table_privileges", {}).get(role) != expected_table_privs:
            fail(f"external evidence table privileges drifted for {role}")

    require(authority.get("migration_reconciliation", {}), {
        "ledger_baseline_main_sha": FINAL_BASELINE,
        "ledger_observed_at_utc": FINAL_OBSERVED,
        "stage38_remote_version": REMOTE_VERSION,
        "stage38_repo_only_count": 0,
        "historical_stage17_remote_only_count": 3,
        "stage35_history_preserved": True,
        "remote_mutation_performed_by_reconciliation_pr": False,
    }, "migration reconciliation")

    require(authority.get("security_invariants", {}), {
        "runtime_can_self_attest_external_evidence": False,
        "service_role_can_directly_dml_external_evidence": False,
        "provider_activation_requires_external_credential_evidence": True,
        "billing_launch_readiness_requires_proof_complete": True,
        "activation_alone_can_promote_billing_launch_gate": False,
        "secret_values_stored_in_repository": False,
    }, "security invariants")

    require(authority.get("sequence_boundary", {}), {
        "may_reapply_stage38": False,
        "may_activate_asaas_without_real_credential_evidence": False,
        "may_insert_credentials_verified_without_real_evidence": False,
        "may_call_provider_before_credential_authority": False,
        "may_promote_billing_gate_without_proof_complete": False,
        "may_use_customer_data_for_controlled_proof": False,
        "may_use_execute_sql_for_dml_or_ddl": False,
        "stage35_proof_reexecution_allowed": False,
    }, "sequence boundary")

    require(authority.get("gates", {}), {
        "stage38_hardening": "PASS_REMOTE_RECONCILED",
        "billing_provider_credentials": "DENIED_AWAITING_REAL_EXTERNAL_CREDENTIAL_EVIDENCE",
        "controlled_launch": "DENIED",
        "production_deployment": "DENIED",
        "incident_response": "DENIED",
        "paid_media": "DENIED",
        "launch": "DENIED",
    }, "gates")

    require(authority.get("next_stage", {}), {
        "name": "STAGE39_BILLING_CREDENTIAL_AUTHORITY_EXTERNAL_EVIDENCE",
        "provider_activation_allowed_now": False,
        "provider_call_allowed_now": False,
        "billing_gate_promotion_allowed_now": False,
    }, "next stage")

    serialized = json.dumps(authority, sort_keys=True).lower()
    for forbidden in ('"api_key"', '"access_token"', '"password"', '"webhook_token"', '"credential_secret_value"'):
        if forbidden in serialized:
            fail(f"secret-bearing key found: {forbidden}")

    print("STAGE38_BILLING_EVIDENCE_BOUND_ACTIVATION_FINAL_RECONCILIATION=PASS")
    print(f"FINAL_BASELINE_MAIN_SHA={FINAL_BASELINE}")
    print(f"STAGE38_REMOTE_VERSION={REMOTE_VERSION}")
    print("STAGE38_REPO_ONLY_COUNT=0")
    print("EXTERNAL_EVIDENCE_ROWS=0")
    print("ASAAS_STATE=SELECTED_PENDING_CREDENTIALS")
    print("ACTIVATION_REQUIRES_EXTERNAL_CREDENTIAL_EVIDENCE=PASS")
    print("BILLING_LAUNCH_REQUIRES_PROOF_COMPLETE=PASS")
    print("BILLING_GATE=DENIED")
    print("PROVIDER_ACTIVATION_ALLOWED=false")
    print("PROVIDER_CALL_ALLOWED=false")
    print("NEXT_STAGE=STAGE39_BILLING_CREDENTIAL_AUTHORITY_EXTERNAL_EVIDENCE")


if __name__ == "__main__":
    main()
