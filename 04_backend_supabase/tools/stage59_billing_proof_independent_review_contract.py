from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

CONTRACT = "STAGE59_V1"
PROJECT_REF = "mceukeondizkwlpfxzgf"
SCOPE = "BR_V1"
PROVIDER_CODE = "asaas"
EVIDENCE_VERSION = "2026-08-18-official-docs-v1"
PROVIDER_ENVIRONMENT_ID = "asaas-production"
HEX64 = re.compile(r"^[0-9a-f]{64}$")

DIGEST_FIELDS = (
    "provider_activation_receipt_sha256",
    "webhook_auth_test_receipt_digest",
    "webhook_replay_receipt_digest",
    "checkout_end_to_end_receipt_digest",
    "synthetic_fixture_manifest_sha256",
    "synthetic_fixture_cleanup_receipt_sha256",
)

EXPECTED_KEYS = {
    "schema_version",
    "contract",
    "project_ref",
    "scope",
    "provider_code",
    "evidence_version",
    "provider_environment_id",
    "decision",
    "stage58_aggregate_sha256",
    "proof_bundle_digest",
    "stage56_candidate_digest_mapping",
    "reviewed_source_artifact_set_digest",
    "reviewer_reference_digest",
    "review_notes_digest",
    "reviewer_independence_attested",
    "source_artifacts_reviewed_out_of_band_attested",
    "synthetic_non_customer_fixture_attested",
    "cleanup_zero_residue_attested",
    "customer_data_used",
    "raw_secret_copied_to_review_receipt",
    "provider_call_performed_by_review_tooling",
    "provider_activation_performed_by_review_tooling",
    "supabase_mutation_performed_by_review_tooling",
    "provider_account_owner_authorization_digest",
    "credential_activation_digest",
    "credentials_verified_at_utc",
    "provider_selection_activated_at_utc",
    "proof_completed_at_utc",
    "independent_review_completed_at_utc",
}


def fail(detail: str) -> None:
    raise ValueError(detail)


def load_receipt(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"independent review receipt unreadable: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail("independent review receipt must be a JSON object")
    return value


def require_digest(value: Any, field: str) -> None:
    if not isinstance(value, str) or HEX64.fullmatch(value) is None:
        fail(f"{field} must be a lowercase SHA-256 digest")


def parse_timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        fail(f"{field} must be a non-empty timezone-aware timestamp")
    candidate = value.strip()
    try:
        parsed = datetime.fromisoformat(candidate[:-1] + "+00:00" if candidate.endswith("Z") else candidate)
    except ValueError:
        fail(f"{field} is not valid ISO-8601")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        fail(f"{field} must be timezone-aware")
    return parsed


def validate_review_receipt(receipt: dict[str, Any], *, require_approved: bool) -> None:
    if set(receipt) != EXPECTED_KEYS:
        missing = sorted(EXPECTED_KEYS - set(receipt))
        extra = sorted(set(receipt) - EXPECTED_KEYS)
        fail(f"independent review receipt key set drift; missing={missing}; extra={extra}")

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
            fail(f"independent review authority drift: {key}")

    decision = receipt.get("decision")
    if decision not in {"APPROVED_FOR_STAGE56_PROOF_PROMOTION_DRAFT", "REJECTED"}:
        fail("invalid independent review decision")
    if require_approved and decision != "APPROVED_FOR_STAGE56_PROOF_PROMOTION_DRAFT":
        fail("independent review did not approve Stage56 candidate drafting")

    for field in (
        "stage58_aggregate_sha256",
        "proof_bundle_digest",
        "reviewed_source_artifact_set_digest",
        "reviewer_reference_digest",
        "review_notes_digest",
        "provider_account_owner_authorization_digest",
        "credential_activation_digest",
    ):
        require_digest(receipt.get(field), field)

    mapping = receipt.get("stage56_candidate_digest_mapping")
    if not isinstance(mapping, dict) or set(mapping) != set(DIGEST_FIELDS):
        fail("Stage56 candidate digest mapping must contain exactly six proof receipt digests")
    for field in DIGEST_FIELDS:
        require_digest(mapping.get(field), field)
    if len(set(mapping.values())) != len(DIGEST_FIELDS):
        fail("six proof receipt digests must identify distinct receipts")

    for field in (
        "reviewer_independence_attested",
        "source_artifacts_reviewed_out_of_band_attested",
        "synthetic_non_customer_fixture_attested",
    ):
        if receipt.get(field) is not True:
            fail(f"required independent review attestation missing: {field}")

    if require_approved and receipt.get("cleanup_zero_residue_attested") is not True:
        fail("approved review requires independently attested zero synthetic residue")
    if not isinstance(receipt.get("cleanup_zero_residue_attested"), bool):
        fail("cleanup_zero_residue_attested must be boolean")

    for field in (
        "customer_data_used",
        "raw_secret_copied_to_review_receipt",
        "provider_call_performed_by_review_tooling",
        "provider_activation_performed_by_review_tooling",
        "supabase_mutation_performed_by_review_tooling",
    ):
        if receipt.get(field) is not False:
            fail(f"independent review tooling side-effect/privacy boundary drift: {field}")

    credentials_at = parse_timestamp(receipt.get("credentials_verified_at_utc"), "credentials_verified_at_utc")
    activated_at = parse_timestamp(receipt.get("provider_selection_activated_at_utc"), "provider_selection_activated_at_utc")
    proof_at = parse_timestamp(receipt.get("proof_completed_at_utc"), "proof_completed_at_utc")
    review_at = parse_timestamp(receipt.get("independent_review_completed_at_utc"), "independent_review_completed_at_utc")
    if activated_at < credentials_at:
        fail("provider activation cannot precede credentials verification")
    if proof_at < activated_at:
        fail("controlled proof cannot complete before provider activation")
    if review_at < proof_at:
        fail("independent review cannot complete before controlled proof completion")
