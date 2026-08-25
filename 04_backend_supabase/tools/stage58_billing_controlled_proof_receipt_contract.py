from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

CONTRACT = "STAGE58_V1"
PROJECT_REF = "mceukeondizkwlpfxzgf"
SCOPE = "BR_V1"
PROVIDER_CODE = "asaas"
EVIDENCE_VERSION = "2026-08-18-official-docs-v1"
PROVIDER_ENVIRONMENT_ID = "asaas-production"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")

RECEIPT_TYPES = (
    "SYNTHETIC_FIXTURE_MANIFEST",
    "PROVIDER_SELECTION_ACTIVATION",
    "WEBHOOK_AUTH",
    "WEBHOOK_REPLAY",
    "CHECKOUT_END_TO_END",
    "SYNTHETIC_FIXTURE_CLEANUP",
)

RESULT_BY_TYPE = {
    "SYNTHETIC_FIXTURE_MANIFEST": "SYNTHETIC_FIXTURE_MANIFEST_CAPTURED",
    "PROVIDER_SELECTION_ACTIVATION": "PROVIDER_SELECTION_ACTIVATION_PASS",
    "WEBHOOK_AUTH": "WEBHOOK_AUTH_CONTROLLED_PROOF_PASS",
    "WEBHOOK_REPLAY": "WEBHOOK_REPLAY_CONTROLLED_PROOF_PASS",
    "CHECKOUT_END_TO_END": "CHECKOUT_END_TO_END_CONTROLLED_PROOF_PASS",
    "SYNTHETIC_FIXTURE_CLEANUP": "SYNTHETIC_FIXTURE_CLEANUP_PASS",
}

COMMON_KEYS = {
    "schema_version",
    "contract",
    "receipt_type",
    "project_ref",
    "scope",
    "provider_code",
    "evidence_version",
    "provider_environment_id",
    "result",
    "source_commit_sha",
    "execution_authorization_ref_digest",
    "credentials_evidence_ref_digest",
    "synthetic_fixture_id_digest",
    "source_artifact_digest",
    "collected_at_utc",
    "customer_data_used",
    "raw_secret_copied_to_receipt",
    "real_financial_charge_completed",
    "paid_subscription_created",
    "controlled_launch_promoted",
    "provider_call_performed",
    "provider_activation_performed",
    "supabase_mutation_performed",
    "outcome",
}

EXPECTED_OUTCOME_KEYS = {
    "SYNTHETIC_FIXTURE_MANIFEST": {
        "synthetic_only_attested",
        "cleanup_required",
        "fixture_manifest_digest",
        "fixture_raw_identifiers_copied",
    },
    "PROVIDER_SELECTION_ACTIVATION": {
        "selection_before_state",
        "selection_after_state",
        "activation_function_definition_sha256",
        "activation_receipt_digest",
        "credential_evidence_bound",
    },
    "WEBHOOK_AUTH": {
        "valid_auth_accepted",
        "invalid_auth_rejected",
        "missing_auth_rejected",
        "record_function_definition_sha256",
        "raw_webhook_secret_copied",
    },
    "WEBHOOK_REPLAY": {
        "first_receipt_durable",
        "replay_idempotent",
        "duplicate_durable_receipt_created",
        "duplicate_subscription_transition_applied",
        "record_function_definition_sha256",
        "mark_function_definition_sha256",
    },
    "CHECKOUT_END_TO_END": {
        "idempotent_replay",
        "conflicting_reuse_rejected",
        "server_amount_authority",
        "silent_provider_fallback",
        "https_checkout_url",
        "provider_ref_durable",
        "create_function_definition_sha256",
        "attach_function_definition_sha256",
    },
    "SYNTHETIC_FIXTURE_CLEANUP": {
        "cleanup_complete",
        "fixture_scoped_residual_count",
        "customer_rows_touched",
        "cleanup_receipt_digest",
    },
}

FUNCTION_HASHES = {
    "activate": "d1ce2db8809c6b4fa66a7018b54baa05725ee97b14508080a5f52f0894400e7c",
    "create_checkout": "341a9fee068212dae3212b953615674b9a018f8254516ec50baee4816152c80d",
    "attach_checkout": "30a45ec42e2e50570fb75609f4e4fd2be67619e8b9d12edbda71c5b25a72d88c",
    "record_webhook": "2a609c89e954c8bc334219e52e1f197bca00228bccdbaf1ce4115e4a34374e44",
    "mark_webhook": "07fad48fd549366cf95aa206fdb3e83f98cab3e0b3038a42703b6259dfbf2e9f",
}


def fail(detail: str) -> None:
    raise ValueError(detail)


def load_receipt(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"receipt unreadable: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail("receipt must be a JSON object")
    return value


def parse_timestamp(value: Any) -> None:
    if not isinstance(value, str) or not value.strip():
        fail("collected_at_utc must be a non-empty timezone-aware timestamp")
    candidate = value.strip()
    try:
        parsed = datetime.fromisoformat(candidate[:-1] + "+00:00" if candidate.endswith("Z") else candidate)
    except ValueError:
        fail("collected_at_utc is not valid ISO-8601")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        fail("collected_at_utc must be timezone-aware")


def require_digest(value: Any, field: str) -> None:
    if not isinstance(value, str) or HEX64.fullmatch(value) is None:
        fail(f"{field} must be a lowercase SHA-256 digest")


def validate_receipt(receipt: dict[str, Any]) -> None:
    if set(receipt) != COMMON_KEYS:
        missing = sorted(COMMON_KEYS - set(receipt))
        extra = sorted(set(receipt) - COMMON_KEYS)
        fail(f"receipt key set drift; missing={missing}; extra={extra}")

    exact = {
        "schema_version": 1,
        "contract": CONTRACT,
        "project_ref": PROJECT_REF,
        "scope": SCOPE,
        "provider_code": PROVIDER_CODE,
        "evidence_version": EVIDENCE_VERSION,
        "provider_environment_id": PROVIDER_ENVIRONMENT_ID,
    }
    for key, expected in exact.items():
        if receipt.get(key) != expected:
            fail(f"receipt authority drift: {key}")

    receipt_type = receipt.get("receipt_type")
    if receipt_type not in RECEIPT_TYPES:
        fail("unknown receipt_type")
    if receipt.get("result") != RESULT_BY_TYPE[receipt_type]:
        fail("receipt result does not match receipt_type")
    if not isinstance(receipt.get("source_commit_sha"), str) or HEX40.fullmatch(receipt["source_commit_sha"]) is None:
        fail("source_commit_sha must be lowercase 40-hex")
    for field in (
        "execution_authorization_ref_digest",
        "credentials_evidence_ref_digest",
        "synthetic_fixture_id_digest",
        "source_artifact_digest",
    ):
        require_digest(receipt.get(field), field)
    if len({receipt[k] for k in (
        "execution_authorization_ref_digest",
        "credentials_evidence_ref_digest",
        "synthetic_fixture_id_digest",
        "source_artifact_digest",
    )}) != 4:
        fail("common receipt digests must identify distinct artifacts")
    parse_timestamp(receipt.get("collected_at_utc"))

    for field in (
        "customer_data_used",
        "raw_secret_copied_to_receipt",
        "real_financial_charge_completed",
        "paid_subscription_created",
        "controlled_launch_promoted",
    ):
        if receipt.get(field) is not False:
            fail(f"forbidden proof property enabled: {field}")

    outcome = receipt.get("outcome")
    if not isinstance(outcome, dict) or set(outcome) != EXPECTED_OUTCOME_KEYS[receipt_type]:
        fail("outcome key set drift")

    if receipt_type == "SYNTHETIC_FIXTURE_MANIFEST":
        if receipt.get("provider_call_performed") is not False or receipt.get("provider_activation_performed") is not False:
            fail("fixture manifest cannot perform provider call/activation")
        if outcome["synthetic_only_attested"] is not True or outcome["cleanup_required"] is not True:
            fail("fixture manifest synthetic/cleanup attestations missing")
        if outcome["fixture_raw_identifiers_copied"] is not False:
            fail("raw fixture identifiers are forbidden")
        require_digest(outcome["fixture_manifest_digest"], "fixture_manifest_digest")

    elif receipt_type == "PROVIDER_SELECTION_ACTIVATION":
        if receipt.get("provider_call_performed") is not False:
            fail("provider selection activation receipt must not imply external provider call")
        if receipt.get("provider_activation_performed") is not True or receipt.get("supabase_mutation_performed") is not True:
            fail("provider selection activation receipt must represent the local activation mutation")
        if outcome["selection_before_state"] != "selected_pending_credentials" or outcome["selection_after_state"] != "active":
            fail("provider selection activation state transition drift")
        if outcome["activation_function_definition_sha256"] != FUNCTION_HASHES["activate"]:
            fail("activation function authority hash drift")
        if outcome["credential_evidence_bound"] is not True:
            fail("provider activation receipt lacks credential-evidence binding")
        require_digest(outcome["activation_receipt_digest"], "activation_receipt_digest")

    elif receipt_type == "WEBHOOK_AUTH":
        if receipt.get("provider_activation_performed") is not False:
            fail("webhook auth proof cannot activate provider")
        if outcome["valid_auth_accepted"] is not True or outcome["invalid_auth_rejected"] is not True or outcome["missing_auth_rejected"] is not True:
            fail("webhook auth positive/negative controls are incomplete")
        if outcome["record_function_definition_sha256"] != FUNCTION_HASHES["record_webhook"]:
            fail("record webhook function authority hash drift")
        if outcome["raw_webhook_secret_copied"] is not False:
            fail("webhook secret copied to receipt")

    elif receipt_type == "WEBHOOK_REPLAY":
        if receipt.get("provider_activation_performed") is not False:
            fail("webhook replay proof cannot activate provider")
        if outcome["first_receipt_durable"] is not True or outcome["replay_idempotent"] is not True:
            fail("webhook replay durable/idempotent proof missing")
        if outcome["duplicate_durable_receipt_created"] is not False or outcome["duplicate_subscription_transition_applied"] is not False:
            fail("webhook replay created duplicate side effect")
        if outcome["record_function_definition_sha256"] != FUNCTION_HASHES["record_webhook"]:
            fail("record webhook function authority hash drift")
        if outcome["mark_function_definition_sha256"] != FUNCTION_HASHES["mark_webhook"]:
            fail("mark webhook function authority hash drift")

    elif receipt_type == "CHECKOUT_END_TO_END":
        if receipt.get("provider_activation_performed") is not False:
            fail("checkout proof cannot activate provider")
        if outcome["idempotent_replay"] is not True or outcome["conflicting_reuse_rejected"] is not True:
            fail("checkout idempotency proof incomplete")
        if outcome["server_amount_authority"] is not True or outcome["silent_provider_fallback"] is not False:
            fail("checkout price/provider authority drift")
        if outcome["https_checkout_url"] is not True or outcome["provider_ref_durable"] is not True:
            fail("checkout provider binding proof incomplete")
        if outcome["create_function_definition_sha256"] != FUNCTION_HASHES["create_checkout"]:
            fail("create checkout function authority hash drift")
        if outcome["attach_function_definition_sha256"] != FUNCTION_HASHES["attach_checkout"]:
            fail("attach checkout function authority hash drift")

    elif receipt_type == "SYNTHETIC_FIXTURE_CLEANUP":
        if receipt.get("provider_call_performed") is not False or receipt.get("provider_activation_performed") is not False:
            fail("cleanup receipt cannot perform provider call/activation")
        if outcome["cleanup_complete"] is not True or outcome["fixture_scoped_residual_count"] != 0:
            fail("fixture cleanup did not reach zero residue")
        if outcome["customer_rows_touched"] is not False:
            fail("fixture cleanup touched customer rows")
        require_digest(outcome["cleanup_receipt_digest"], "cleanup_receipt_digest")
