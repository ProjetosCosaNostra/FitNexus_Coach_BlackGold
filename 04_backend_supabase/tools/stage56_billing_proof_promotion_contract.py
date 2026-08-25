from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

PROTOCOL = "STAGE56_V1"
PROJECT_REF = "mceukeondizkwlpfxzgf"
SCOPE = "BR_V1"
PROVIDER_CODE = "asaas"
EVIDENCE_VERSION = "2026-08-18-official-docs-v1"
SOURCE_STATE = "credentials_verified"
TARGET_STATE = "proof_complete"
PROVIDER_ENVIRONMENT_ID = "asaas-production"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
MIGRATION_NAME = re.compile(
    r"^(?P<version>\d{14})_billing_external_evidence_proof_complete_br_v1_asaas\.sql$"
)

EXPECTED_KEYS = {
    "schema_version",
    "protocol",
    "project_ref",
    "scope",
    "provider_code",
    "evidence_version",
    "source_state",
    "target_state",
    "provider_environment_id",
    "promotion_state",
    "independent_review_decision",
    "provider_account_owner_authorization_digest",
    "credential_activation_digest",
    "credentials_verified_at_utc",
    "provider_selection_activated_at_utc",
    "provider_activation_receipt_sha256",
    "webhook_auth_test_receipt_digest",
    "webhook_replay_receipt_digest",
    "checkout_end_to_end_receipt_digest",
    "synthetic_fixture_manifest_sha256",
    "synthetic_fixture_cleanup_receipt_sha256",
    "independent_review_receipt_sha256",
    "proof_bundle_digest",
    "reviewer_reference_digest",
    "reviewer_independence_attested",
    "source_artifacts_reviewed_out_of_band_attested",
    "synthetic_non_customer_fixture_attested",
    "customer_data_used",
    "raw_secret_copied_to_receipts",
    "real_financial_charge_completed",
    "paid_subscription_created",
    "provider_call_performed_by_tooling",
    "provider_activation_performed_by_tooling",
    "remote_apply_performed",
    "controlled_launch_promoted",
    "paid_media_promoted",
    "launch_promoted",
    "proof_completed_at_utc",
    "independent_review_completed_at_utc",
    "migration_filename",
}

REQUIRED_DIGESTS = {
    "provider_account_owner_authorization_digest",
    "credential_activation_digest",
    "provider_activation_receipt_sha256",
    "webhook_auth_test_receipt_digest",
    "webhook_replay_receipt_digest",
    "checkout_end_to_end_receipt_digest",
    "synthetic_fixture_manifest_sha256",
    "synthetic_fixture_cleanup_receipt_sha256",
    "independent_review_receipt_sha256",
    "proof_bundle_digest",
    "reviewer_reference_digest",
}

REQUIRED_TRUE = {
    "reviewer_independence_attested",
    "source_artifacts_reviewed_out_of_band_attested",
    "synthetic_non_customer_fixture_attested",
}

REQUIRED_FALSE = {
    "customer_data_used",
    "raw_secret_copied_to_receipts",
    "real_financial_charge_completed",
    "paid_subscription_created",
    "provider_call_performed_by_tooling",
    "provider_activation_performed_by_tooling",
    "controlled_launch_promoted",
    "paid_media_promoted",
    "launch_promoted",
}


def fail(detail: str) -> None:
    raise ValueError(detail)


def load_authority(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"proof promotion authority unreadable: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail("proof promotion authority must be a JSON object")
    return value


def parse_timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        fail(f"{field} must be a non-empty ISO-8601 timestamp")
    candidate = value.strip()
    try:
        parsed = datetime.fromisoformat(candidate[:-1] + "+00:00" if candidate.endswith("Z") else candidate)
    except ValueError:
        fail(f"{field} must be valid ISO-8601")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        fail(f"{field} must be timezone-aware")
    return parsed


def validate_authority(authority: dict[str, Any], *, require_migration: bool) -> None:
    if set(authority) != EXPECTED_KEYS:
        missing = sorted(EXPECTED_KEYS - set(authority))
        extra = sorted(set(authority) - EXPECTED_KEYS)
        fail(f"proof promotion authority key set drift; missing={missing}; extra={extra}")
    exact = {
        "schema_version": 1,
        "protocol": PROTOCOL,
        "project_ref": PROJECT_REF,
        "scope": SCOPE,
        "provider_code": PROVIDER_CODE,
        "evidence_version": EVIDENCE_VERSION,
        "source_state": SOURCE_STATE,
        "target_state": TARGET_STATE,
        "provider_environment_id": PROVIDER_ENVIRONMENT_ID,
        "independent_review_decision": "APPROVED_FOR_PROOF_COMPLETE_MIGRATION_DRAFT",
    }
    for key, expected in exact.items():
        if authority.get(key) != expected:
            fail(f"proof promotion authority drift: {key}")

    state = authority.get("promotion_state")
    allowed_states = {
        "REVIEWED_CANDIDATE_NO_MIGRATION",
        "VERSIONED_MIGRATION_PRESENT_REPO_ONLY",
        "REMOTE_APPLIED_RECONCILED",
    }
    if state not in allowed_states:
        fail("promotion_state is invalid")
    if require_migration and state == "REVIEWED_CANDIDATE_NO_MIGRATION":
        fail("promotion authority does not attest a versioned migration")

    for field in REQUIRED_DIGESTS:
        if not HEX64.fullmatch(str(authority.get(field, ""))):
            fail(f"invalid SHA-256 digest: {field}")

    proof_digests = [
        authority["provider_activation_receipt_sha256"],
        authority["webhook_auth_test_receipt_digest"],
        authority["webhook_replay_receipt_digest"],
        authority["checkout_end_to_end_receipt_digest"],
        authority["synthetic_fixture_manifest_sha256"],
        authority["synthetic_fixture_cleanup_receipt_sha256"],
        authority["independent_review_receipt_sha256"],
        authority["proof_bundle_digest"],
        authority["reviewer_reference_digest"],
    ]
    if len(set(proof_digests)) != len(proof_digests):
        fail("proof/review/fixture digests must identify distinct artifacts")

    for field in REQUIRED_TRUE:
        if authority.get(field) is not True:
            fail(f"required proof attestation missing: {field}")
    for field in REQUIRED_FALSE:
        if authority.get(field) is not False:
            fail(f"forbidden proof authority drift: {field}")

    credentials_at = parse_timestamp(authority.get("credentials_verified_at_utc"), "credentials_verified_at_utc")
    activated_at = parse_timestamp(authority.get("provider_selection_activated_at_utc"), "provider_selection_activated_at_utc")
    proof_at = parse_timestamp(authority.get("proof_completed_at_utc"), "proof_completed_at_utc")
    review_at = parse_timestamp(authority.get("independent_review_completed_at_utc"), "independent_review_completed_at_utc")
    if activated_at < credentials_at:
        fail("provider selection activation cannot precede credentials verification")
    if proof_at < activated_at:
        fail("proof_complete evidence cannot precede provider selection activation")
    if review_at < proof_at:
        fail("independent review cannot complete before proof bundle completion")

    migration_filename = authority.get("migration_filename")
    if state == "REVIEWED_CANDIDATE_NO_MIGRATION":
        if migration_filename not in {None, ""}:
            fail("reviewed candidate must not claim a migration filename")
    else:
        if not isinstance(migration_filename, str) or MIGRATION_NAME.fullmatch(migration_filename) is None:
            fail("migration_filename does not match Stage56 proof-complete naming contract")

    remote_apply = authority.get("remote_apply_performed")
    if state == "REMOTE_APPLIED_RECONCILED":
        if remote_apply is not True:
            fail("remote reconciled state requires remote_apply_performed=true")
    elif remote_apply is not False:
        fail("repo-only states require remote_apply_performed=false")


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def render_executable_sql(authority: dict[str, Any]) -> str:
    validate_authority(authority, require_migration=False)
    note = (
        "Stage56 proof_complete; proof_bundle_sha256="
        f"{authority['proof_bundle_digest']}; independent_review_sha256="
        f"{authority['independent_review_receipt_sha256']}"
    )
    return f"""do $$
declare
  v_updated integer := 0;
begin
  update private.billing_provider_external_evidence e
  set
    state = {sql_literal(TARGET_STATE)},
    webhook_auth_test_receipt_digest = {sql_literal(str(authority['webhook_auth_test_receipt_digest']))},
    webhook_replay_receipt_digest = {sql_literal(str(authority['webhook_replay_receipt_digest']))},
    checkout_end_to_end_receipt_digest = {sql_literal(str(authority['checkout_end_to_end_receipt_digest']))},
    proof_completed_at = {sql_literal(str(authority['proof_completed_at_utc']))}::timestamptz,
    attested_at = {sql_literal(str(authority['independent_review_completed_at_utc']))}::timestamptz,
    note = {sql_literal(note)}
  from public.billing_provider_selections s
  where e.scope = {sql_literal(SCOPE)}
    and e.provider_code = {sql_literal(PROVIDER_CODE)}
    and e.evidence_version = {sql_literal(EVIDENCE_VERSION)}
    and e.state = {sql_literal(SOURCE_STATE)}
    and e.provider_environment_id = {sql_literal(PROVIDER_ENVIRONMENT_ID)}
    and e.provider_account_owner_authorization_digest = {sql_literal(str(authority['provider_account_owner_authorization_digest']))}
    and e.credential_activation_digest = {sql_literal(str(authority['credential_activation_digest']))}
    and e.credentials_verified_at = {sql_literal(str(authority['credentials_verified_at_utc']))}::timestamptz
    and e.webhook_auth_test_receipt_digest is null
    and e.webhook_replay_receipt_digest is null
    and e.checkout_end_to_end_receipt_digest is null
    and e.proof_completed_at is null
    and s.scope = e.scope
    and s.provider_code = e.provider_code
    and s.evidence_version = e.evidence_version
    and s.state = 'active'
    and s.activated_at = {sql_literal(str(authority['provider_selection_activated_at_utc']))}::timestamptz;

  get diagnostics v_updated = row_count;
  if v_updated <> 1 then
    raise exception 'STAGE56_PROOF_COMPLETE_PROMOTION_PRECONDITION_FAILED';
  end if;
end
$$;
"""


def render_candidate_sql(authority: dict[str, Any]) -> str:
    validate_authority(authority, require_migration=False)
    metadata = [
        "-- STAGE56 OPERATIONS CANDIDATE ONLY — DO NOT APPLY DIRECTLY",
        f"-- BILLING_PROOF_PROMOTION_PROTOCOL={PROTOCOL}",
        f"-- SCOPE={SCOPE}",
        f"-- PROVIDER_CODE={PROVIDER_CODE}",
        f"-- EVIDENCE_VERSION={EVIDENCE_VERSION}",
        f"-- TARGET_STATE={TARGET_STATE}",
        f"-- PROVIDER_ENVIRONMENT_ID={PROVIDER_ENVIRONMENT_ID}",
        f"-- WEBHOOK_AUTH_RECEIPT_SHA256={authority['webhook_auth_test_receipt_digest']}",
        f"-- WEBHOOK_REPLAY_RECEIPT_SHA256={authority['webhook_replay_receipt_digest']}",
        f"-- CHECKOUT_E2E_RECEIPT_SHA256={authority['checkout_end_to_end_receipt_digest']}",
        f"-- INDEPENDENT_REVIEW_RECEIPT_SHA256={authority['independent_review_receipt_sha256']}",
        "-- CANDIDATE_IS_REMOTE_APPLY_AUTHORITY=false",
        "-- PROVIDER_ACTIVATION_PERFORMED_BY_TOOLING=false",
        "-- PROVIDER_CALL_PERFORMED_BY_TOOLING=false",
        "",
    ]
    return "\n".join(metadata) + render_executable_sql(authority)


def normalize_executable_sql(sql: str) -> str:
    lines: list[str] = []
    for raw in sql.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("--"):
            continue
        lines.append(" ".join(stripped.split()))
    return "\n".join(lines)
