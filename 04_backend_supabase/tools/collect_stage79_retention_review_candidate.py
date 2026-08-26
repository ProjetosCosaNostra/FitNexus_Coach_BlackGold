from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "10_compliance" / "inventory" / "STAGE78_TECHNICAL_DATA_RETENTION_SURFACE_REGISTRY.json"
FAILURE_CLASS = "BGF-STAGE79-RETENTION-REVIEW-INTAKE-GUARD-765"
STAGE78_REGISTRY_GIT_BLOB = "9a5c8c549a26f04146298c8c1b52b2fb64a414ec"
PLACEHOLDER_RE = re.compile(r"<[^>]+>|placeholder|tbd|to[_ -]?be[_ -]?defined|example", re.IGNORECASE)
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", re.IGNORECASE),
    re.compile(r"\b(?:password|passwd|api[_-]?key|access[_-]?token|service[_-]?role[_-]?key|client[_-]?secret|webhook[_-]?token|secret[_-]?value)\s*[:=]\s*[^\s,}\]]+", re.IGNORECASE),
)
EXPECTED_PARTICIPANT_ROLES = ["legal_review", "privacy_review", "operations_review"]
EXPECTED_SURFACE_IDS = [
    "account_and_tenancy",
    "student_identity_and_coaching_profile",
    "training_prescription_templates_and_lineage",
    "workout_execution_history",
    "potentially_sensitive_workout_feedback",
    "decision_intelligence_and_coach_action_history",
    "student_access_security_and_abuse_telemetry",
    "growth_attribution_and_funnel_telemetry",
    "billing_subscription_and_webhook_history",
    "governance_and_gate_evidence_metadata",
    "backup_restore_and_expiration",
    "scheduled_cleanup_or_purge",
]
REVIEW_FIELDS = [
    "reviewed_retention_criterion",
    "purpose_or_authority_reference",
    "cancellation_effect",
    "delinquency_effect",
    "backup_purge_or_expiration_rule",
    "legal_hold_rule",
    "end_of_retention_action",
    "security_audit_exception_or_none",
    "review_material_reference",
]
SCOPE_KEYS = [
    "input_is_approved_retention_policy",
    "input_is_legal_gate_evidence",
    "collector_can_copy_reviewer_identity_or_paths",
    "collector_can_close_retention_matrix",
    "collector_can_modify_privacy_or_dsr_documents",
    "collector_can_create_evidence_ref_or_digest",
    "collector_can_create_evidence_migration",
    "collector_can_mutate_supabase",
    "collector_can_deploy",
    "collector_can_promote_controlled_launch_or_paid_media",
]


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE79_RETENTION_REVIEW_CANDIDATE=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\n"
        f"DETAIL={detail}"
    )


def load_json(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to load {label}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"{label} must be a JSON object")
    return value


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    try:
        return sha256_bytes(path.read_bytes())
    except OSError as exc:
        fail(f"unable to hash {path.name}: {type(exc).__name__}")


def canonical_sha256(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256_bytes(raw)


def real_text(value: object, label: str, minimum: int = 3) -> str:
    if not isinstance(value, str):
        fail(f"{label} must be text")
    text = value.strip()
    if len(text) < minimum or PLACEHOLDER_RE.search(text):
        fail(f"{label} must be real non-placeholder review material")
    return text


def validate_timestamp(value: object) -> str:
    raw = real_text(value, "reviewed_at_utc")
    try:
        parsed = datetime.fromisoformat(raw[:-1] + "+00:00" if raw.endswith("Z") else raw)
    except ValueError:
        fail("reviewed_at_utc is not valid ISO-8601")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        fail("reviewed_at_utc must be timezone-aware")
    utc = parsed.astimezone(timezone.utc)
    if utc > datetime.now(timezone.utc):
        fail("reviewed_at_utc cannot be in the future")
    return utc.isoformat()


def validate_artifact(path: Path, label: str) -> str:
    if not path.is_file() or path.stat().st_size <= 0:
        fail(f"{label} must be a real non-empty file")
    if path.stat().st_size > 8 * 1024 * 1024:
        fail(f"{label} exceeds 8 MiB intake boundary")
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        fail(f"{label} must be UTF-8 text for secret-marker inspection")
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            fail(f"{label} contains a secret-like marker; redact before intake")
    return sha256_file(path)


def validate_registry() -> str:
    registry = load_json(REGISTRY, "Stage78 retention registry")
    if registry.get("schema_version") != 1:
        fail("Stage78 registry schema drift")
    if registry.get("status") != "TECHNICAL_DATA_RETENTION_SURFACE_REGISTRY_NOT_APPROVED_RETENTION_POLICY_NOT_EVIDENCE":
        fail("Stage78 registry status drift")
    categories = registry.get("categories")
    non_table = registry.get("non_table_surfaces")
    if not isinstance(categories, list) or not isinstance(non_table, list):
        fail("Stage78 registry surface lists missing")
    observed = [item.get("category_id") for item in categories if isinstance(item, dict)] + [
        item.get("surface_id") for item in non_table if isinstance(item, dict)
    ]
    if observed != EXPECTED_SURFACE_IDS:
        fail("Stage78 registry surface identity/order drift")
    for item in categories:
        if item.get("explicit_retention_period_in_registry") is not None:
            fail("Stage78 registry unexpectedly contains an approved retention period")
    return sha256_file(REGISTRY)


def validate_participants(value: object) -> list[dict]:
    if not isinstance(value, list) or len(value) != len(EXPECTED_PARTICIPANT_ROLES):
        fail("participants must contain exactly legal, privacy and operations review")
    roles = [item.get("role") for item in value if isinstance(item, dict)]
    if roles != EXPECTED_PARTICIPANT_ROLES:
        fail("participant role set/order drift")

    output: list[dict] = []
    for item in value:
        if not isinstance(item, dict):
            fail("participant entry must be an object")
        role = item["role"]
        reviewer_ref = real_text(item.get("reviewer_reference"), f"{role}.reviewer_reference")
        artifact_raw = real_text(item.get("review_artifact_path"), f"{role}.review_artifact_path")
        artifact_path = Path(artifact_raw).expanduser().resolve()
        artifact_digest = validate_artifact(artifact_path, f"{role}.review_artifact")
        output.append({
            "role": role,
            "reviewer_reference_sha256": sha256_bytes(reviewer_ref.encode("utf-8")),
            "review_artifact_sha256": artifact_digest,
        })
    return output


def validate_surfaces(value: object) -> list[dict]:
    if not isinstance(value, list) or len(value) != len(EXPECTED_SURFACE_IDS):
        fail("review_surfaces must contain exactly twelve Stage78 surfaces")
    ids = [item.get("surface_id") for item in value if isinstance(item, dict)]
    if ids != EXPECTED_SURFACE_IDS:
        fail("review surface identity/order drift")

    output: list[dict] = []
    for item in value:
        if not isinstance(item, dict):
            fail("review surface entry must be an object")
        surface_id = item["surface_id"]
        decision: dict[str, str] = {}
        for key in REVIEW_FIELDS:
            decision[key] = real_text(item.get(key), f"{surface_id}.{key}")
        if item.get("review_complete_for_surface") is not True:
            fail(f"review surface is incomplete: {surface_id}")
        output.append({
            "surface_id": surface_id,
            "review_decision_sha256": canonical_sha256(decision),
            "review_complete_declaration_received": True,
        })
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review-input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    registry_sha256 = validate_registry()
    input_path = args.review_input.expanduser().resolve()
    value = load_json(input_path, "real retention decision review input")

    if value.get("schema_version") != 1:
        fail("review input schema_version must be 1")
    if value.get("input_kind") != "REAL_RETENTION_DECISION_REVIEW_INPUT":
        fail("review input_kind drift")
    status = str(value.get("status", "")).strip()
    if not status or status == "PLACEHOLDER_TEMPLATE_NOT_REAL_RETENTION_REVIEW" or PLACEHOLDER_RE.search(status):
        fail("retention review input is still placeholder-like")
    if value.get("test_fixture") is not False:
        fail("retention review input is a test fixture; real external review is required")
    if value.get("contains_placeholders") is not False:
        fail("retention review input declares placeholders")
    if value.get("stage78_registry_git_blob") != STAGE78_REGISTRY_GIT_BLOB:
        fail("Stage78 registry Git blob binding drift")

    review_reference = real_text(value.get("review_session_reference"), "review_session_reference")
    reviewed_at_utc = validate_timestamp(value.get("reviewed_at_utc"))
    if value.get("artifact_secret_values_absent_or_redacted_confirmed") is not True:
        fail("review artifact secret absence/redaction confirmation is required")

    participants = validate_participants(value.get("participants"))
    surfaces = validate_surfaces(value.get("review_surfaces"))

    boundary = value.get("scope_boundary")
    if not isinstance(boundary, dict) or list(boundary) != SCOPE_KEYS:
        fail("review input scope_boundary keys drift")
    for key in SCOPE_KEYS:
        if boundary.get(key) is not False:
            fail(f"review input scope boundary must remain false: {key}")

    candidate = {
        "schema_version": 1,
        "stage": "STAGE79_RETENTION_DECISION_REVIEW_INTAKE_BOUNDARY",
        "output_kind": "DIGEST_ONLY_RETENTION_REVIEW_MATERIAL_CANDIDATE",
        "candidate_state": "REAL_EXTERNAL_RETENTION_REVIEW_MATERIAL_DIGESTS_BOUND_AWAITING_CANONICAL_INDEPENDENT_ACCEPTANCE_NOT_POLICY_EVIDENCE",
        "stage78_registry_git_blob": STAGE78_REGISTRY_GIT_BLOB,
        "stage78_registry_sha256": registry_sha256,
        "review_input_sha256": sha256_file(input_path),
        "review_session_reference_sha256": sha256_bytes(review_reference.encode("utf-8")),
        "reviewed_at_utc": reviewed_at_utc,
        "participant_count": len(participants),
        "participants": participants,
        "surface_count": len(surfaces),
        "review_surfaces": surfaces,
        "reviewer_identity_copied": False,
        "review_artifact_paths_copied": False,
        "review_artifact_contents_copied": False,
        "review_decision_text_copied": False,
        "secret_values_copied": False,
        "external_review_material_collected": True,
        "canonical_independent_acceptance_performed": False,
        "legal_correctness_verified_by_collector": False,
        "retention_policy_approved": False,
        "backup_expiration_policy_approved": False,
        "legal_hold_policy_approved": False,
        "candidate_documents_modified": False,
        "target_open_decision_closed": False,
        "legal_privacy_notice_gate_ready": False,
        "data_subject_request_channel_gate_ready": False,
        "incident_response_gate_ready": False,
        "evidence_ref_created": False,
        "evidence_digest_promoted": False,
        "evidence_migration_created": False,
        "network_call_performed": False,
        "provider_call_performed": False,
        "supabase_mutation_performed": False,
        "deployment_performed": False,
        "controlled_launch_promoted": False,
        "paid_media_promoted": False,
        "canonical_independent_acceptance_required": True,
        "next_action": "CANONICAL_INDEPENDENT_ACCEPTANCE_REQUIRED_BEFORE_RETENTION_POLICY_DRAFT_UPDATE_OR_RETENTION_MATRIX_CLOSURE",
    }

    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(candidate, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

    print("STAGE79_RETENTION_REVIEW_CANDIDATE=PASS_DIGEST_ONLY")
    print("PARTICIPANT_COUNT=3")
    print("SURFACE_COUNT=12")
    print("RETENTION_POLICY_APPROVED=false")
    print("TARGET_DECISION_CLOSED=false")
    print("GATE_PROMOTION=false")
    print("REMOTE_MUTATION=false")


if __name__ == "__main__":
    main()
