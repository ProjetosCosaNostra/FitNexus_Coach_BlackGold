from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

PROTOCOL = "STAGE54_V1"
PROJECT_REF = "mceukeondizkwlpfxzgf"
SCOPE = "BR_V1"
PROVIDER_CODE = "asaas"
EVIDENCE_VERSION = "2026-08-18-official-docs-v1"
EVIDENCE_STATE = "credentials_verified"
PROVIDER_ENVIRONMENT_ID = "asaas-production"
SOURCE_STAGE = "STAGE39_BILLING_CREDENTIAL_AUTHORITY_EXTERNAL_EVIDENCE"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
MIGRATION_NAME = re.compile(
    r"^(?P<version>\d{14})_billing_external_evidence_credentials_verified_br_v1_asaas\.sql$"
)

EXPECTED_KEYS = {
    "schema_version",
    "protocol",
    "project_ref",
    "scope",
    "provider_code",
    "evidence_version",
    "evidence_state",
    "provider_environment_id",
    "source_receipt_stage",
    "promotion_state",
    "independent_review_decision",
    "source_receipt_sha256",
    "independent_review_receipt_sha256",
    "source_artifact_review_digest",
    "review_bundle_digest",
    "reviewer_reference_digest",
    "provider_account_owner_authorization_digest",
    "credential_activation_digest",
    "secret_boundary_ref_digest",
    "reviewer_independence_attested",
    "source_artifacts_reviewed_out_of_band_attested",
    "operator_redaction_confirmed",
    "credential_artifact_contains_secret_value",
    "script_verifies_reviewer_independence",
    "synthetic_test_fixture",
    "stage47_aggregate_used_as_external_review_authority",
    "stage48_regression_used_as_external_review_authority",
    "stage49_protocol_used_as_billing_authorization",
    "provider_activation_performed",
    "provider_call_performed",
    "gate_ready_attested_by_tool",
    "remote_apply_performed",
    "controlled_launch_promoted",
    "paid_media_promoted",
    "launch_promoted",
    "credentials_verified_at_utc",
    "independent_review_completed_at_utc",
    "evidence_ref",
    "evidence_digest",
    "migration_filename",
}

REQUIRED_DIGESTS = {
    "source_receipt_sha256",
    "independent_review_receipt_sha256",
    "source_artifact_review_digest",
    "review_bundle_digest",
    "reviewer_reference_digest",
    "provider_account_owner_authorization_digest",
    "credential_activation_digest",
    "secret_boundary_ref_digest",
}

REQUIRED_TRUE = {
    "reviewer_independence_attested",
    "source_artifacts_reviewed_out_of_band_attested",
    "operator_redaction_confirmed",
}

REQUIRED_FALSE = {
    "credential_artifact_contains_secret_value",
    "script_verifies_reviewer_independence",
    "synthetic_test_fixture",
    "stage47_aggregate_used_as_external_review_authority",
    "stage48_regression_used_as_external_review_authority",
    "stage49_protocol_used_as_billing_authorization",
    "provider_activation_performed",
    "provider_call_performed",
    "gate_ready_attested_by_tool",
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
        fail(f"billing promotion authority unreadable: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail("billing promotion authority must be a JSON object")
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
        fail(f"billing promotion authority key set drift; missing={missing}; extra={extra}")
    if authority.get("schema_version") != 1:
        fail("schema_version must be 1")
    if authority.get("protocol") != PROTOCOL:
        fail("promotion protocol drift")
    if authority.get("project_ref") != PROJECT_REF:
        fail("project_ref drift")
    if authority.get("scope") != SCOPE:
        fail("Stage54 V1 is bound to BR_V1")
    if authority.get("provider_code") != PROVIDER_CODE:
        fail("Stage54 V1 is bound to Asaas")
    if authority.get("evidence_version") != EVIDENCE_VERSION:
        fail("evidence_version is not the selected Stage39 authority version")
    if authority.get("evidence_state") != EVIDENCE_STATE:
        fail("Stage54 V1 only authorizes credentials_verified evidence")
    if authority.get("provider_environment_id") != PROVIDER_ENVIRONMENT_ID:
        fail("BR_V1 credentials evidence must be bound to asaas-production")
    if authority.get("source_receipt_stage") != SOURCE_STAGE:
        fail("source receipt stage is not canonical Stage39")
    if authority.get("independent_review_decision") != "APPROVED_FOR_CREDENTIAL_EVIDENCE_MIGRATION_DRAFT":
        fail("independent review decision does not authorize credential evidence migration drafting")

    state = authority.get("promotion_state")
    allowed_states = {
        "REVIEWED_CANDIDATE_NO_MIGRATION",
        "VERSIONED_MIGRATION_PRESENT_REPO_ONLY",
        "REMOTE_APPLIED_RECONCILED",
    }
    if state not in allowed_states:
        fail("promotion_state is invalid")
    if require_migration and state not in {
        "VERSIONED_MIGRATION_PRESENT_REPO_ONLY",
        "REMOTE_APPLIED_RECONCILED",
    }:
        fail("promotion authority does not attest a versioned migration")

    for field in REQUIRED_DIGESTS:
        if not HEX64.fullmatch(str(authority.get(field, ""))):
            fail(f"invalid SHA-256 digest: {field}")
    if authority["source_receipt_sha256"] == authority["independent_review_receipt_sha256"]:
        fail("source receipt and independent review receipt must be distinct artifacts")
    if authority["provider_account_owner_authorization_digest"] == authority["credential_activation_digest"]:
        fail("owner authorization and credential activation must be distinct artifacts")

    for field in REQUIRED_TRUE:
        if authority.get(field) is not True:
            fail(f"required external-review attestation missing: {field}")
    for field in REQUIRED_FALSE:
        if authority.get(field) is not False:
            fail(f"forbidden billing promotion authority drift: {field}")

    credentials_verified_at = parse_timestamp(authority.get("credentials_verified_at_utc"), "credentials_verified_at_utc")
    review_completed_at = parse_timestamp(authority.get("independent_review_completed_at_utc"), "independent_review_completed_at_utc")
    if review_completed_at < credentials_verified_at:
        fail("independent review cannot complete before credentials verification evidence time")

    expected_ref = (
        f"stage54://billing-credentials/{SCOPE}/{PROVIDER_CODE}/"
        f"{authority['independent_review_receipt_sha256']}"
    )
    if authority.get("evidence_ref") != expected_ref:
        fail("evidence_ref is not canonically bound to scope/provider/review receipt")
    if authority.get("evidence_digest") != authority.get("review_bundle_digest"):
        fail("evidence_digest must equal review_bundle_digest")

    migration_filename = authority.get("migration_filename")
    if state == "REVIEWED_CANDIDATE_NO_MIGRATION":
        if migration_filename not in {None, ""}:
            fail("reviewed candidate must not claim a migration filename")
    else:
        if not isinstance(migration_filename, str) or MIGRATION_NAME.fullmatch(migration_filename) is None:
            fail("migration_filename does not match Stage54 credentials migration naming contract")

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
        "Stage54 external credential evidence; review_bundle_sha256="
        f"{authority['review_bundle_digest']}; independent_review_sha256="
        f"{authority['independent_review_receipt_sha256']}"
    )
    return f"""do $$
declare
  v_inserted integer := 0;
begin
  insert into private.billing_provider_external_evidence (
    scope,
    provider_code,
    evidence_version,
    state,
    provider_account_owner_authorization_digest,
    credential_activation_digest,
    provider_environment_id,
    webhook_auth_test_receipt_digest,
    webhook_replay_receipt_digest,
    checkout_end_to_end_receipt_digest,
    credentials_verified_at,
    proof_completed_at,
    attested_at,
    note
  )
  select
    {sql_literal(SCOPE)},
    {sql_literal(PROVIDER_CODE)},
    {sql_literal(EVIDENCE_VERSION)},
    {sql_literal(EVIDENCE_STATE)},
    {sql_literal(str(authority['provider_account_owner_authorization_digest']))},
    {sql_literal(str(authority['credential_activation_digest']))},
    {sql_literal(PROVIDER_ENVIRONMENT_ID)},
    null,
    null,
    null,
    {sql_literal(str(authority['credentials_verified_at_utc']))}::timestamptz,
    null,
    {sql_literal(str(authority['independent_review_completed_at_utc']))}::timestamptz,
    {sql_literal(note)}
  from public.billing_provider_selections s
  where s.scope = {sql_literal(SCOPE)}
    and s.provider_code = {sql_literal(PROVIDER_CODE)}
    and s.evidence_version = {sql_literal(EVIDENCE_VERSION)}
    and s.state = 'selected_pending_credentials'
    and s.activated_at is null
    and not exists (
      select 1
      from private.billing_provider_external_evidence e
      where e.scope = s.scope
        and e.provider_code = s.provider_code
        and e.evidence_version = s.evidence_version
    );

  get diagnostics v_inserted = row_count;
  if v_inserted <> 1 then
    raise exception 'STAGE54_CREDENTIAL_EVIDENCE_PROMOTION_PRECONDITION_FAILED';
  end if;
end
$$;
"""


def render_candidate_sql(authority: dict[str, Any]) -> str:
    validate_authority(authority, require_migration=False)
    metadata = [
        "-- STAGE54 OPERATIONS CANDIDATE ONLY — DO NOT APPLY DIRECTLY",
        f"-- BILLING_EVIDENCE_PROMOTION_PROTOCOL={PROTOCOL}",
        f"-- SCOPE={SCOPE}",
        f"-- PROVIDER_CODE={PROVIDER_CODE}",
        f"-- EVIDENCE_VERSION={EVIDENCE_VERSION}",
        f"-- EVIDENCE_STATE={EVIDENCE_STATE}",
        f"-- PROVIDER_ENVIRONMENT_ID={PROVIDER_ENVIRONMENT_ID}",
        f"-- SOURCE_RECEIPT_SHA256={authority['source_receipt_sha256']}",
        f"-- INDEPENDENT_REVIEW_RECEIPT_SHA256={authority['independent_review_receipt_sha256']}",
        f"-- REVIEW_BUNDLE_DIGEST={authority['review_bundle_digest']}",
        "-- CANDIDATE_IS_REMOTE_APPLY_AUTHORITY=false",
        "-- PROVIDER_ACTIVATION_PERFORMED=false",
        "-- PROVIDER_CALL_PERFORMED=false",
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
