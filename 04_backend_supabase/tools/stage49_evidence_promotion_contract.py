from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

PROTOCOL = "STAGE49_V1"
PROJECT_REF = "mceukeondizkwlpfxzgf"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
MIGRATION_NAME = re.compile(
    r"^(?P<version>\d{14})_external_evidence_promotion_(?P<gate>[a-z0-9_]+)\.sql$"
)
ELIGIBLE_GATES = {
    "legal_privacy_notice",
    "legal_terms_of_use",
    "legal_role_mapping",
    "data_subject_request_channel",
    "incident_response",
    "production_deployment",
}

REQUIRED_BOOLEAN_TRUE = {
    "reviewer_independence_attested",
    "source_artifacts_reviewed_out_of_band_attested",
}
REQUIRED_BOOLEAN_FALSE = {
    "script_verifies_reviewer_independence",
    "synthetic_test_fixture",
    "stage47_aggregate_used_as_external_review_authority",
    "stage48_regression_used_as_external_review_authority",
    "stage35_alert_proof_alone_used_for_production_deployment",
    "gate_ready_attested_by_tool",
    "controlled_launch_promoted",
    "paid_media_promoted",
    "launch_promoted",
}
REQUIRED_DIGESTS = {
    "source_receipt_sha256",
    "independent_review_receipt_sha256",
    "source_artifact_review_digest",
    "review_bundle_digest",
    "reviewer_reference_digest",
}


def fail(detail: str) -> None:
    raise ValueError(detail)


def load_authority(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"promotion authority unreadable: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail("promotion authority must be a JSON object")
    return value


def validate_timestamp(value: Any, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        fail(f"{field} must be a non-empty ISO-8601 timestamp")
    candidate = value.strip()
    try:
        parsed = datetime.fromisoformat(candidate[:-1] + "+00:00" if candidate.endswith("Z") else candidate)
    except ValueError:
        fail(f"{field} must be valid ISO-8601")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        fail(f"{field} must be timezone-aware")


def validate_authority(authority: dict[str, Any], *, require_migration: bool) -> None:
    if authority.get("schema_version") != 1:
        fail("schema_version must be 1")
    if authority.get("protocol") != PROTOCOL:
        fail("promotion protocol drift")
    if authority.get("project_ref") != PROJECT_REF:
        fail("project_ref drift")

    gate = authority.get("gate_code")
    if gate not in ELIGIBLE_GATES:
        fail("gate_code is not eligible for evidence_migration promotion")

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

    for field in REQUIRED_BOOLEAN_TRUE:
        if authority.get(field) is not True:
            fail(f"required independent-review attestation missing: {field}")
    for field in REQUIRED_BOOLEAN_FALSE:
        if authority.get(field) is not False:
            fail(f"forbidden promotion authority drift: {field}")

    validate_timestamp(authority.get("independent_review_completed_at_utc"), "independent_review_completed_at_utc")

    expected_ref = (
        f"stage49://external-evidence/{gate}/"
        f"{authority['independent_review_receipt_sha256']}"
    )
    if authority.get("evidence_ref") != expected_ref:
        fail("evidence_ref is not canonically bound to gate and independent review receipt")
    if authority.get("evidence_digest") != authority.get("review_bundle_digest"):
        fail("evidence_digest must equal review_bundle_digest")

    migration_filename = authority.get("migration_filename")
    if state == "REVIEWED_CANDIDATE_NO_MIGRATION":
        if migration_filename not in {None, ""}:
            fail("reviewed candidate must not claim a migration filename")
    else:
        if not isinstance(migration_filename, str):
            fail("migration_filename is required")
        match = MIGRATION_NAME.fullmatch(migration_filename)
        if match is None:
            fail("migration_filename does not match Stage49 naming contract")
        if match.group("gate") != gate:
            fail("migration_filename gate does not match authority gate")

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
    gate = str(authority["gate_code"])
    evidence_ref = str(authority["evidence_ref"])
    evidence_digest = str(authority["evidence_digest"])
    note = (
        "Stage49 independent external review bound to canonical source receipt and "
        "independent-review receipt; versioned promotion authority required."
    )
    return f"""do $$
declare
  v_updated integer := 0;
begin
  update private.controlled_launch_gate_evidence
  set state = 'ready',
      evidence_ref = {sql_literal(evidence_ref)},
      evidence_digest = {sql_literal(evidence_digest)},
      note = {sql_literal(note)},
      attested_at = now(),
      updated_at = now()
  where gate_code = {sql_literal(gate)}
    and state = 'blocked'
    and evidence_ref is null
    and evidence_digest is null;

  get diagnostics v_updated = row_count;
  if v_updated <> 1 then
    raise exception 'STAGE49_EVIDENCE_PROMOTION_PRECONDITION_FAILED:%', {sql_literal(gate)};
  end if;
end
$$;
"""


def render_candidate_sql(authority: dict[str, Any]) -> str:
    validate_authority(authority, require_migration=False)
    metadata = [
        "-- STAGE49 OPERATIONS CANDIDATE ONLY — DO NOT APPLY DIRECTLY",
        f"-- EXTERNAL_EVIDENCE_PROMOTION_PROTOCOL={PROTOCOL}",
        f"-- GATE_CODE={authority['gate_code']}",
        f"-- SOURCE_RECEIPT_SHA256={authority['source_receipt_sha256']}",
        f"-- INDEPENDENT_REVIEW_RECEIPT_SHA256={authority['independent_review_receipt_sha256']}",
        f"-- SOURCE_ARTIFACT_REVIEW_DIGEST={authority['source_artifact_review_digest']}",
        f"-- REVIEW_BUNDLE_DIGEST={authority['review_bundle_digest']}",
        f"-- REVIEWER_REFERENCE_DIGEST={authority['reviewer_reference_digest']}",
        "-- CANDIDATE_IS_REMOTE_APPLY_AUTHORITY=false",
        "-- GATE_READY_AT_CANDIDATE_GENERATION=false",
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
