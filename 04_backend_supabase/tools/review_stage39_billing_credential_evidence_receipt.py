from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EXPECTED_KEYS = {
    "schema_version",
    "stage",
    "result",
    "project_ref",
    "scope",
    "provider_code",
    "evidence_version",
    "provider_environment_id",
    "provider_base_url",
    "real_financial_impact_expected",
    "secret_boundary_ref",
    "provider_account_owner_authorization_digest",
    "credential_activation_digest",
    "provider_account_owner_authorization_confirmed",
    "credential_artifact_secret_value_absent_or_redacted_confirmed",
    "collected_at_utc",
    "raw_secret_value_collected",
    "raw_artifact_content_copied_to_receipt",
    "artifact_path_or_filename_copied_to_receipt",
    "provider_called",
    "provider_activation_performed",
    "supabase_mutation_performed",
    "customer_data_used",
    "credentials_verified_state_attested",
    "billing_gate_promoted",
    "launch_gate_promoted",
    "next_action",
}

HEX64 = re.compile(r"^[0-9a-f]{64}$")
SECRET_BOUNDARY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/ -]{2,127}$")
FORBIDDEN_SECRET_KEYS = {
    "api_key",
    "access_token",
    "password",
    "webhook_token",
    "credential_secret_value",
    "secret",
    "token",
}
FAILURE_CLASS = "BGF-STAGE40-BILLING-RECEIPT-REVIEW-361"


def fail(detail: str, marker: str = "STAGE39_BILLING_CREDENTIAL_EVIDENCE_RECEIPT_REVIEW=FAIL") -> None:
    raise SystemExit(f"{marker}\nFAILURE_CLASS={FAILURE_CLASS}\nDETAIL={detail}")


def load_receipt(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8-sig")
        value = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"receipt unreadable or invalid JSON: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail("receipt must be a JSON object")
    return value


def walk_keys(value: Any) -> list[str]:
    result: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            result.append(str(key).lower())
            result.extend(walk_keys(child))
    elif isinstance(value, list):
        for child in value:
            result.extend(walk_keys(child))
    return result


def require_exact(receipt: dict[str, Any], key: str, expected: Any) -> None:
    if receipt.get(key) != expected:
        fail(f"receipt field drift: {key}; expected={expected!r} actual={receipt.get(key)!r}")


def validate_timestamp(value: Any) -> None:
    if not isinstance(value, str) or not value.strip():
        fail("collected_at_utc must be a non-empty timestamp")
    candidate = value.strip()
    try:
        parsed = datetime.fromisoformat(candidate[:-1] + "+00:00" if candidate.endswith("Z") else candidate)
    except ValueError:
        fail("collected_at_utc is not valid ISO-8601")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        fail("collected_at_utc must be timezone-aware")
    if parsed.astimezone(timezone.utc) > datetime.now(timezone.utc):
        fail("collected_at_utc cannot be in the future")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Review a Stage39 digest-only receipt for BR_V1 production credential-evidence eligibility."
    )
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()

    receipt = load_receipt(args.receipt)

    if set(receipt) != EXPECTED_KEYS:
        missing = sorted(EXPECTED_KEYS - set(receipt))
        extra = sorted(set(receipt) - EXPECTED_KEYS)
        fail(f"receipt key set drifted; missing={missing}; extra={extra}")

    for key in walk_keys(receipt):
        if key in FORBIDDEN_SECRET_KEYS:
            fail(f"secret-bearing key is forbidden in digest-only receipt: {key}")

    require_exact(receipt, "schema_version", 1)
    require_exact(receipt, "stage", "STAGE39_BILLING_CREDENTIAL_AUTHORITY_EXTERNAL_EVIDENCE")
    require_exact(receipt, "result", "DIGEST_ONLY_EVIDENCE_INTAKE_CANDIDATE")
    require_exact(receipt, "project_ref", "mceukeondizkwlpfxzgf")
    require_exact(receipt, "scope", "BR_V1")
    require_exact(receipt, "provider_code", "asaas")
    require_exact(receipt, "evidence_version", "2026-08-18-official-docs-v1")

    environment = receipt.get("provider_environment_id")
    if environment == "asaas-sandbox":
        fail(
            "sandbox evidence is valid only for non-production integration testing and cannot authorize BR_V1 production activation",
            marker="STAGE39_RECEIPT_ENVIRONMENT_NOT_ELIGIBLE_FOR_BR_V1_PRODUCTION_ACTIVATION",
        )
    require_exact(receipt, "provider_environment_id", "asaas-production")
    require_exact(receipt, "provider_base_url", "https://api.asaas.com/v3")
    require_exact(receipt, "real_financial_impact_expected", True)

    boundary = receipt.get("secret_boundary_ref")
    if not isinstance(boundary, str) or SECRET_BOUNDARY.fullmatch(boundary) is None:
        fail("secret_boundary_ref is missing or invalid")

    for digest_key in (
        "provider_account_owner_authorization_digest",
        "credential_activation_digest",
    ):
        digest = receipt.get(digest_key)
        if not isinstance(digest, str) or HEX64.fullmatch(digest) is None:
            fail(f"{digest_key} must be a lowercase SHA-256 digest")

    require_exact(receipt, "provider_account_owner_authorization_confirmed", True)
    require_exact(receipt, "credential_artifact_secret_value_absent_or_redacted_confirmed", True)
    validate_timestamp(receipt.get("collected_at_utc"))

    for false_field in (
        "raw_secret_value_collected",
        "raw_artifact_content_copied_to_receipt",
        "artifact_path_or_filename_copied_to_receipt",
        "provider_called",
        "provider_activation_performed",
        "supabase_mutation_performed",
        "customer_data_used",
        "credentials_verified_state_attested",
        "billing_gate_promoted",
        "launch_gate_promoted",
    ):
        require_exact(receipt, false_field, False)

    require_exact(
        receipt,
        "next_action",
        "INDEPENDENT_REVIEW_REQUIRED_BEFORE_ANY_EVIDENCE_MIGRATION",
    )

    print("STAGE39_BILLING_CREDENTIAL_EVIDENCE_RECEIPT_REVIEW=PASS")
    print("SCOPE=BR_V1")
    print("PROVIDER=asaas")
    print("PROVIDER_ENVIRONMENT_ID=asaas-production")
    print("DIGEST_SHAPE=PASS")
    print("SECRET_VALUE_COLLECTION=false")
    print("PROVIDER_CALLED=false")
    print("PROVIDER_ACTIVATION_PERFORMED=false")
    print("SUPABASE_MUTATION_PERFORMED=false")
    print("CREDENTIALS_VERIFIED_STATE_ATTESTED=false")
    print("BILLING_GATE_PROMOTED=false")
    print("NEXT_ACTION=INDEPENDENT_EVIDENCE_MIGRATION_REVIEW_ONLY")


if __name__ == "__main__":
    main()
