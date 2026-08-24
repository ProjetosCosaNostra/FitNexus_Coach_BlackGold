from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage40_billing_production_environment_interlock_candidate_authority.json"
STAGE39 = BACKEND / "stage39_billing_credential_authority_external_evidence_preparation.json"
STAGE38 = BACKEND / "stage38_billing_evidence_bound_activation_final_authority.json"
CANDIDATE = BACKEND / "operations" / "stage40_billing_production_environment_interlock_candidate.sql"
REVIEWER = BACKEND / "tools" / "review_stage39_billing_credential_evidence_receipt.py"
MIGRATIONS = BACKEND / "migrations"

BASELINE_MAIN = "f1de13ea29265326f00fd51a29b7f710b0a892ac"
OBSERVED_AT = "2026-08-24T00:16:15.565213+00:00"
STAGE38_REMOTE_VERSION = "20260823175158"
FAILURE_CLASS = "BGF-STAGE40-BILLING-PRODUCTION-ENVIRONMENT-CANDIDATE-GUARD-362"


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE40_BILLING_PRODUCTION_ENVIRONMENT_INTERLOCK_CANDIDATE=FAIL\n"
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


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"unable to read {path.relative_to(ROOT)}: {type(exc).__name__}")


def require(mapping: dict, expected: dict, label: str) -> None:
    if not isinstance(mapping, dict):
        fail(f"{label} must be object")
    for key, expected_value in expected.items():
        if mapping.get(key) != expected_value:
            fail(
                f"{label} drift: {key}; expected={expected_value!r} actual={mapping.get(key)!r}"
            )


def main() -> None:
    authority = load(AUTHORITY)
    stage39 = load(STAGE39)
    stage38 = load(STAGE38)
    candidate = read(CANDIDATE)
    reviewer = read(REVIEWER)

    require(
        authority,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "stage": "STAGE40_BILLING_PRODUCTION_ENVIRONMENT_INTERLOCK_CANDIDATE",
            "baseline_main_sha": BASELINE_MAIN,
            "current_state": "REPO_ONLY_CANDIDATE_SANDBOX_CANNOT_PROMOTE_BR_V1_PRODUCTION_BINDING_NOT_YET_REMOTE",
        },
        "Stage40 authority",
    )

    if set(authority.get("failure_classes", [])) != {
        "BGF-STAGE40-BILLING-SANDBOX-EVIDENCE-CROSS-ENV-ACTIVATION-357",
        "BGF-STAGE40-BILLING-LAUNCH-ENVIRONMENT-MISMATCH-358",
        "BGF-STAGE40-BILLING-ENVIRONMENT-IDENTITY-DOWNGRADE-359",
        "BGF-STAGE40-BILLING-CANDIDATE-DIRECT-APPLY-360",
    }:
        fail("Stage40 authority failure-class set drifted")

    require(
        authority.get("upstream_authority", {}),
        {
            "stage38_remote_version": STAGE38_REMOTE_VERSION,
            "stage38_may_reapply": False,
            "stage39_operator_evidence_receipt_present_in_repository": False,
            "provider_activation_requires_external_credential_evidence": True,
            "billing_launch_readiness_requires_proof_complete": True,
        },
        "upstream authority",
    )

    require(
        stage38,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "stage": "STAGE38_BILLING_EVIDENCE_BOUND_ACTIVATION_FINAL_RECONCILIATION",
            "current_state": "HARDENING_REMOTE_APPLIED_ZERO_EXTERNAL_EVIDENCE_PROVIDER_STILL_PENDING_BILLING_GATE_BLOCKED",
        },
        "Stage38 final authority",
    )
    require(
        stage39,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "stage": "STAGE39_BILLING_CREDENTIAL_AUTHORITY_EXTERNAL_EVIDENCE_PREPARATION",
            "current_state": "PREPARED_OPERATOR_EVIDENCE_REQUIRED_NO_PROVIDER_CALL_NO_ACTIVATION_NO_GATE_PROMOTION",
        },
        "Stage39 preparation authority",
    )

    docs_facts = stage39.get("official_provider_documentation_review", {}).get(
        "facts_used_by_preparation", {}
    )
    require(
        docs_facts,
        {
            "sandbox_and_production_use_independent_accounts_and_keys": True,
            "sandbox_base_url": "https://api-sandbox.asaas.com/v3",
            "production_base_url": "https://api.asaas.com/v3",
            "initial_integration_testing_should_use_sandbox": True,
        },
        "Stage39 provider environment facts",
    )

    remote = authority.get("fresh_remote_read_only_receipt", {})
    require(
        remote,
        {
            "source": "Supabase.execute_sql_read_only",
            "observed_at_utc": OBSERVED_AT,
            "external_evidence_rows": 0,
            "checkout_intents": 0,
            "webhook_receipts": 0,
            "auth_users": 0,
            "organizations": 0,
            "billing_launch_predicate_ready": False,
            "activation_function_contains_external_evidence_interlock": True,
            "activation_function_contains_production_environment_interlock": False,
            "remote_mutation_performed": False,
            "provider_called": False,
            "customer_data_used": False,
        },
        "fresh remote receipt",
    )
    require(
        remote.get("selection", {}),
        {
            "scope": "BR_V1",
            "provider_code": "asaas",
            "state": "selected_pending_credentials",
            "evidence_version": "2026-08-18-official-docs-v1",
            "activated_at": None,
        },
        "provider selection",
    )

    stage40_migrations = [path.name for path in MIGRATIONS.glob("*stage40*.sql")]
    if stage40_migrations:
        fail(f"Stage40 candidate PR must not add migrations: {stage40_migrations}")

    required_candidate_fragments = (
        "BILLING_PROVIDER_EXTERNAL_CREDENTIAL_EVIDENCE_REQUIRED",
        "v_external_evidence.state not in ('credentials_verified','proof_complete')",
        "v_external_evidence.credentials_verified_at is null",
        "v_selection.scope = 'BR_V1'",
        "v_selection.provider_code = 'asaas'",
        "v_external_evidence.provider_environment_id <> 'asaas-production'",
        "BILLING_PROVIDER_PRODUCTION_ENVIRONMENT_EVIDENCE_REQUIRED",
        "e.state='proof_complete'",
        "e.provider_environment_id='asaas-production'",
        "production_billing_environment_required",
        "revoke execute on function public.activate_billing_provider_selection(text,text,text) from public, anon, authenticated;",
        "grant execute on function public.activate_billing_provider_selection(text,text,text) to service_role;",
        "revoke execute on function private.get_controlled_launch_readiness_authority() from public,anon,authenticated;",
        "grant execute on function private.get_controlled_launch_readiness_authority() to service_role;",
    )
    for fragment in required_candidate_fragments:
        if fragment not in candidate:
            fail(f"candidate contract fragment missing: {fragment}")

    forbidden_candidate_patterns = (
        r"insert\s+into\s+private\.billing_provider_external_evidence",
        r"update\s+private\.billing_provider_external_evidence",
        r"delete\s+from\s+private\.billing_provider_external_evidence",
        r"https://api-sandbox\.asaas\.com",
        r"https://api\.asaas\.com",
        r"\bnet\.http\b",
        r"\bcurl\b",
    )
    for pattern in forbidden_candidate_patterns:
        if re.search(pattern, candidate, flags=re.IGNORECASE):
            fail(f"candidate contains forbidden mutation/provider-call pattern: {pattern}")

    require(
        authority.get("candidate", {}),
        {
            "file": "04_backend_supabase/operations/stage40_billing_production_environment_interlock_candidate.sql",
            "location_class": "OPERATIONS_CANDIDATE_NOT_MIGRATION",
            "remote_apply_allowed": False,
            "direct_apply_allowed": False,
            "promotion_requires_separate_versioned_migration_pr": True,
        },
        "candidate authority",
    )
    require(
        authority.get("candidate", {}).get("activation_change", {}),
        {
            "scope": "BR_V1",
            "provider_code": "asaas",
            "required_provider_environment_id": "asaas-production",
            "failure_message": "BILLING_PROVIDER_PRODUCTION_ENVIRONMENT_EVIDENCE_REQUIRED",
            "preserves_external_credential_evidence_interlock": True,
        },
        "activation change",
    )
    require(
        authority.get("candidate", {}).get("controlled_launch_change", {}),
        {
            "required_provider_environment_id": "asaas-production",
            "preserves_proof_complete_requirement": True,
            "adds_guardrail": "production_billing_environment_required",
        },
        "controlled-launch change",
    )

    require(
        authority.get("receipt_review_contract", {}),
        {
            "reviewer": "04_backend_supabase/tools/review_stage39_billing_credential_evidence_receipt.py",
            "review_only": True,
            "provider_call_allowed": False,
            "supabase_mutation_allowed": False,
            "migration_generation_allowed": False,
            "evidence_attestation_allowed": False,
            "billing_gate_promotion_allowed": False,
            "br_v1_eligible_environment": "asaas-production",
            "sandbox_failure": "STAGE39_RECEIPT_ENVIRONMENT_NOT_ELIGIBLE_FOR_BR_V1_PRODUCTION_ACTIVATION",
        },
        "receipt review contract",
    )

    required_reviewer_fragments = (
        'require_exact(receipt, "scope", "BR_V1")',
        'require_exact(receipt, "provider_code", "asaas")',
        'if environment == "asaas-sandbox":',
        'marker="STAGE39_RECEIPT_ENVIRONMENT_NOT_ELIGIBLE_FOR_BR_V1_PRODUCTION_ACTIVATION"',
        'require_exact(receipt, "provider_environment_id", "asaas-production")',
        'require_exact(receipt, "provider_base_url", "https://api.asaas.com/v3")',
        'require_exact(receipt, "real_financial_impact_expected", True)',
        '"provider_called",',
        '"provider_activation_performed",',
        '"supabase_mutation_performed",',
        '"credentials_verified_state_attested",',
        '"billing_gate_promoted",',
        '"launch_gate_promoted",',
        '"INDEPENDENT_REVIEW_REQUIRED_BEFORE_ANY_EVIDENCE_MIGRATION"',
    )
    for fragment in required_reviewer_fragments:
        if fragment not in reviewer:
            fail(f"receipt reviewer contract fragment missing: {fragment}")

    forbidden_reviewer_patterns = (
        r"\brequests\.",
        r"\burllib\.",
        r"\bhttpx\.",
        r"\bsubprocess\.",
        r"\bapply_migration\b",
        r"\bexecute_sql\b",
        r"\bactivate_billing_provider_selection\b",
    )
    for pattern in forbidden_reviewer_patterns:
        if re.search(pattern, reviewer, flags=re.IGNORECASE):
            fail(f"receipt reviewer contains forbidden network/mutation pattern: {pattern}")

    boundaries = authority.get("boundaries", {})
    require(
        boundaries,
        {
            "repo_only": True,
            "migration_added": False,
            "supabase_mutation_performed": False,
            "provider_call_performed": False,
            "provider_activation_performed": False,
            "external_evidence_attested": False,
            "customer_data_used": False,
            "credential_secret_recorded": False,
            "billing_gate_promoted": False,
            "launch_gate_promoted": False,
            "production_deployment_allowed": False,
            "incident_response_promotion_allowed": False,
            "paid_media_allowed": False,
            "stage35_proof_reexecution_allowed": False,
        },
        "Stage40 boundaries",
    )

    require(
        authority.get("gates", {}),
        {
            "stage40_candidate": "REPO_ONLY_PENDING_CI",
            "stage40_remote_apply": "DENIED",
            "billing_provider_credentials": "DENIED_AWAITING_REAL_ASAAS_PRODUCTION_OPERATOR_EVIDENCE",
            "provider_activation": "DENIED",
            "provider_call": "DENIED",
            "controlled_launch": "DENIED",
            "production_deployment": "DENIED",
            "incident_response": "DENIED",
            "paid_media": "DENIED",
            "launch": "DENIED",
        },
        "Stage40 gates",
    )

    serialized = json.dumps(authority, sort_keys=True).lower()
    for forbidden in ('"api_key"', '"access_token"', '"password"', '"webhook_token"', '"credential_secret_value"'):
        if forbidden in serialized:
            fail(f"secret-bearing key found in authority: {forbidden}")

    print("STAGE40_BILLING_PRODUCTION_ENVIRONMENT_INTERLOCK_CANDIDATE=PASS")
    print(f"BASELINE_MAIN_SHA={BASELINE_MAIN}")
    print("STAGE40_MIGRATION_ADDED=false")
    print("REMOTE_MUTATION=false")
    print("PROVIDER_CALL=false")
    print("PROVIDER_ACTIVATION=false")
    print("BR_V1_ASAAS_REQUIRED_ENVIRONMENT=asaas-production")
    print("SANDBOX_CAN_UNLOCK_BR_V1=false")
    print("BILLING_GATE=DENIED")
    print("NEXT_ACTION=SEPARATE_VERSIONED_MIGRATION_PROMOTION_PR_AFTER_GREEN_CANDIDATE_MERGE")


if __name__ == "__main__":
    main()
