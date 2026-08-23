from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage39_billing_credential_authority_external_evidence_preparation.json"
UPSTREAM = BACKEND / "stage38_billing_evidence_bound_activation_final_authority.json"
COLLECTOR = BACKEND / "tools" / "collect_stage39_billing_credential_evidence.ps1"

BASELINE_MAIN = "472126a513e1bf20a75d63a1bfcfeb608ffc5566"
STAGE38_REMOTE_VERSION = "20260823175158"
OBSERVED_AT = "2026-08-23T18:59:33.884123+00:00"
FAILURE_CLASS = "BGF-STAGE39-BILLING-PREPARATION-356"


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE39_BILLING_CREDENTIAL_AUTHORITY_PREPARATION=FAIL\n"
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
        fail(f"{label} must be an object")
    for key, value in expected.items():
        if mapping.get(key) != value:
            fail(f"{label} drift: {key}")


def main() -> None:
    authority = load(AUTHORITY)
    upstream = load(UPSTREAM)
    try:
        collector = COLLECTOR.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"unable to read collector: {type(exc).__name__}")

    require(
        authority,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "stage": "STAGE39_BILLING_CREDENTIAL_AUTHORITY_EXTERNAL_EVIDENCE_PREPARATION",
            "baseline_main_sha": BASELINE_MAIN,
            "current_state": "PREPARED_OPERATOR_EVIDENCE_REQUIRED_NO_PROVIDER_CALL_NO_ACTIVATION_NO_GATE_PROMOTION",
        },
        "Stage39 authority",
    )

    expected_failure_classes = {
        "BGF-STAGE39-BILLING-OWNER-AUTHORIZATION-MISSING-349",
        "BGF-STAGE39-BILLING-SECRET-MATERIAL-CROSSOVER-350",
        "BGF-STAGE39-BILLING-ENVIRONMENT-IDENTITY-AMBIGUOUS-351",
        "BGF-STAGE39-BILLING-EVIDENCE-DIGEST-WITHOUT-ARTIFACT-352",
        "BGF-STAGE39-BILLING-PREMATURE-PROVIDER-CALL-353",
        "BGF-STAGE39-BILLING-PREMATURE-ACTIVATION-354",
        "BGF-STAGE39-BILLING-RECEIPT-SELF-ATTESTATION-355",
    }
    if set(authority.get("failure_classes", [])) != expected_failure_classes:
        fail("Stage39 failure-class set drifted")

    require(
        upstream,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "stage": "STAGE38_BILLING_EVIDENCE_BOUND_ACTIVATION_FINAL_RECONCILIATION",
            "current_state": "HARDENING_REMOTE_APPLIED_ZERO_EXTERNAL_EVIDENCE_PROVIDER_STILL_PENDING_BILLING_GATE_BLOCKED",
        },
        "Stage38 upstream authority",
    )
    require(
        upstream.get("next_stage", {}),
        {
            "name": "STAGE39_BILLING_CREDENTIAL_AUTHORITY_EXTERNAL_EVIDENCE",
            "provider_activation_allowed_now": False,
            "provider_call_allowed_now": False,
            "billing_gate_promotion_allowed_now": False,
        },
        "Stage38 next-stage boundary",
    )
    require(
        authority.get("upstream_authority", {}),
        {
            "stage38_hardening_state": "PASS_REMOTE_RECONCILED",
            "stage38_remote_version": STAGE38_REMOTE_VERSION,
            "stage38_may_reapply": False,
            "provider_activation_requires_external_credential_evidence": True,
            "billing_launch_readiness_requires_proof_complete": True,
        },
        "Stage39 upstream binding",
    )

    require(
        authority.get("fresh_remote_read_only_receipt", {}),
        {
            "observed_at_utc": OBSERVED_AT,
            "stage38_remote_version": STAGE38_REMOTE_VERSION,
            "external_evidence_rows": 0,
            "checkout_intents": 0,
            "webhook_receipts": 0,
            "auth_users": 0,
            "organizations": 0,
            "billing_launch_predicate_ready": False,
            "remote_mutation_performed": False,
            "provider_called": False,
            "customer_data_used": False,
        },
        "fresh remote receipt",
    )
    require(
        authority["fresh_remote_read_only_receipt"].get("selection", {}),
        {
            "scope": "BR_V1",
            "provider_code": "asaas",
            "state": "selected_pending_credentials",
            "evidence_version": "2026-08-18-official-docs-v1",
            "activated_at": None,
        },
        "billing provider selection",
    )

    docs = authority.get("official_provider_documentation_review", {})
    require(
        docs,
        {
            "reviewed_at_utc_date": "2026-08-23",
            "authentication_url": "https://docs.asaas.com/docs/authentication",
            "api_keys_url": "https://docs.asaas.com/docs/chaves-de-api",
            "sandbox_url": "https://docs.asaas.com/docs/sandbox",
            "webhook_idempotency_url": "https://docs.asaas.com/docs/como-implementar-idempotencia-em-webhooks",
        },
        "provider documentation review",
    )
    require(
        docs.get("facts_used_by_preparation", {}),
        {
            "api_key_generated_in_web_integrations_by_admin_user": True,
            "api_key_should_be_stored_in_secret_manager": True,
            "sandbox_and_production_use_independent_accounts_and_keys": True,
            "sandbox_base_url": "https://api-sandbox.asaas.com/v3",
            "production_base_url": "https://api.asaas.com/v3",
            "initial_integration_testing_should_use_sandbox": True,
            "webhook_delivery_semantics_at_least_once": True,
            "webhook_duplicate_handling_requires_idempotency": True,
        },
        "provider documentation facts",
    )

    evidence = authority.get("required_stage39_operator_evidence", {})
    expected_evidence_keys = {
        "provider_account_owner_authorization_artifact",
        "credential_activation_artifact",
        "provider_environment_id",
        "secret_boundary_ref",
        "operator_redaction_confirmation",
    }
    if set(evidence) != expected_evidence_keys:
        fail("operator evidence shape drifted")
    if evidence["provider_environment_id"].get("allowed_values") != ["asaas-sandbox", "asaas-production"]:
        fail("provider environment values drifted")
    if evidence["secret_boundary_ref"].get("secret_value_allowed") is not False:
        fail("secret boundary must forbid secret values")

    require(
        authority.get("collector_contract", {}),
        {
            "script": "04_backend_supabase/tools/collect_stage39_billing_credential_evidence.ps1",
            "output_kind": "DIGEST_ONLY_EVIDENCE_INTAKE_CANDIDATE",
            "network_calls_allowed": False,
            "provider_calls_allowed": False,
            "provider_activation_allowed": False,
            "supabase_mutation_allowed": False,
            "secret_parameter_allowed": False,
            "raw_artifact_content_copied_to_receipt": False,
            "artifact_path_or_filename_copied_to_receipt": False,
            "receipt_can_attest_credentials_verified": False,
            "receipt_can_promote_billing_gate": False,
        },
        "collector contract",
    )

    required_collector_fragments = (
        "ValidateSet('asaas-sandbox', 'asaas-production')",
        "I_AUTHORIZE_FITNEXUS_ASAAS_INTEGRATION",
        "SECRET_VALUE_ABSENT_OR_REDACTED",
        "Get-FileHash -LiteralPath $ownerArtifact.FullName -Algorithm SHA256",
        "Get-FileHash -LiteralPath $credentialArtifact.FullName -Algorithm SHA256",
        "raw_secret_value_collected = $false",
        "raw_artifact_content_copied_to_receipt = $false",
        "artifact_path_or_filename_copied_to_receipt = $false",
        "provider_called = $false",
        "provider_activation_performed = $false",
        "supabase_mutation_performed = $false",
        "credentials_verified_state_attested = $false",
        "billing_gate_promoted = $false",
        "INDEPENDENT_REVIEW_REQUIRED_BEFORE_ANY_EVIDENCE_MIGRATION",
    )
    for fragment in required_collector_fragments:
        if fragment not in collector:
            fail(f"collector contract fragment missing: {fragment}")

    forbidden_collector_patterns = (
        r"\bInvoke-WebRequest\b",
        r"\bInvoke-RestMethod\b",
        r"\bStart-BitsTransfer\b",
        r"\bSystem\.Net\.Http\.HttpClient\b",
        r"\bcurl(?:\.exe)?\b",
        r"\bwget(?:\.exe)?\b",
        r"\baccess_token\b",
        r"\$ApiKey\b",
        r"\$AccessToken\b",
        r"\$SecretValue\b",
        r"\$WebhookToken\b",
        r"\bactivate_billing_provider_selection\b",
        r"\bapply_migration\b",
        r"\bexecute_sql\b",
    )
    for pattern in forbidden_collector_patterns:
        if re.search(pattern, collector, flags=re.IGNORECASE):
            fail(f"collector contains forbidden network/secret/mutation pattern: {pattern}")

    gates = authority.get("gates", {})
    require(
        gates,
        {
            "stage39_preparation": "REPO_ONLY_PENDING_CI",
            "billing_provider_credentials": "DENIED_AWAITING_REAL_OPERATOR_EVIDENCE",
            "provider_activation": "DENIED",
            "provider_call": "DENIED",
            "controlled_launch": "DENIED",
            "production_deployment": "DENIED",
            "incident_response": "DENIED",
            "paid_media": "DENIED",
            "launch": "DENIED",
        },
        "Stage39 gates",
    )

    serialized = json.dumps(authority, sort_keys=True).lower()
    for secret_key in ('"api_key"', '"access_token"', '"password"', '"webhook_token"', '"secret_value"'):
        if secret_key in serialized:
            fail(f"authority contains secret-bearing key: {secret_key}")

    print("STAGE39_BILLING_CREDENTIAL_AUTHORITY_PREPARATION=PASS")
    print(f"BASELINE_MAIN_SHA={BASELINE_MAIN}")
    print(f"STAGE38_REMOTE_VERSION={STAGE38_REMOTE_VERSION}")
    print("REMOTE_MUTATION=false")
    print("PROVIDER_CALL=false")
    print("PROVIDER_ACTIVATION=false")
    print("SECRET_VALUE_COLLECTION=false")
    print("DIGEST_ONLY_EVIDENCE_COLLECTOR=PASS")
    print("BILLING_PROVIDER_CREDENTIALS_GATE=DENIED_AWAITING_REAL_OPERATOR_EVIDENCE")
    print("CONTROLLED_LAUNCH_GATE=DENIED")


if __name__ == "__main__":
    main()
