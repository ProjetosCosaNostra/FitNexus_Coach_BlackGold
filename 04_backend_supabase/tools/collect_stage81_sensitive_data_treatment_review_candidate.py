from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STAGE80R1_AUTHORITY = ROOT / "04_backend_supabase" / "stage80r1_registry_pin_reconciliation_authority.json"
STAGE80_REGISTRY = ROOT / "10_compliance" / "inventory" / "STAGE80_TECHNICAL_SENSITIVE_DATA_MINIMIZATION_REGISTRY.json"
FAILURE_CLASS = "BGF-STAGE81-SENSITIVE-DATA-TREATMENT-REVIEW-INTAKE-GUARD-791"
STAGE80R1_AUTHORITY_GIT_BLOB = "3f05971fae97c0491ba8c532d0577383f2b630c6"
STAGE80_REGISTRY_GIT_BLOB = "2aacf6d36834f6542e0cc9ef1f9be360fc61019d"
PLACEHOLDER_RE = re.compile(
    r"<[^>]+>|placeholder|replace[_ -]?with|tbd|to[_ -]?be[_ -]?defined|example|dummy|fixture",
    re.IGNORECASE,
)
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", re.IGNORECASE),
    re.compile(
        r"\b(?:password|passwd|api[_-]?key|access[_-]?token|service[_-]?role[_-]?key|client[_-]?secret|webhook[_-]?token|secret[_-]?value)\s*[:=]\s*[^\s,}\]]+",
        re.IGNORECASE,
    ),
)
EXPECTED_PARTICIPANT_ROLES = ["legal_review", "privacy_review"]
EXPECTED_SURFACE_IDS = [
    "student_profile_objective_and_context",
    "training_prescription_notes_and_lineage",
    "workout_feedback_pain_energy_and_notes",
    "decision_intelligence_context_and_outcomes",
    "coach_action_notes",
    "student_access_security_identifiers_and_alerts",
    "growth_attribution_and_marketing_boundary",
    "support_and_dsr_free_form_ingress",
    "incident_response_sensitive_data_handling",
]
REVIEW_FIELDS = [
    "final_legal_classification",
    "purpose_and_necessity",
    "minimization_rule",
    "free_form_content_rule",
    "access_control_rule",
    "external_ai_rule",
    "marketing_analytics_rule",
    "transparency_rule",
    "incident_handling_rule",
    "retention_dependency_reference",
    "review_material_reference",
]


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE81_SENSITIVE_DATA_REVIEW_CANDIDATE=FAIL\n"
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


def git_blob_sha(path: Path) -> str:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        fail(f"unable to read {path.name}: {type(exc).__name__}")
    return hashlib.sha1(f"blob {len(raw)}\0".encode("utf-8") + raw).hexdigest()


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
    raw = real_text(value, "reviewed_at")
    try:
        parsed = datetime.fromisoformat(raw[:-1] + "+00:00" if raw.endswith("Z") else raw)
    except ValueError:
        fail("reviewed_at is not valid ISO-8601")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        fail("reviewed_at must be timezone-aware")
    utc = parsed.astimezone(timezone.utc)
    if utc > datetime.now(timezone.utc):
        fail("reviewed_at cannot be in the future")
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


def validate_upstream() -> tuple[str, str]:
    if git_blob_sha(STAGE80R1_AUTHORITY) != STAGE80R1_AUTHORITY_GIT_BLOB:
        fail("Stage80R1 authority bytes drifted from canonical Git blob")
    if git_blob_sha(STAGE80_REGISTRY) != STAGE80_REGISTRY_GIT_BLOB:
        fail("current Stage80 registry bytes drifted from canonical Git blob")
    addendum = load_json(STAGE80R1_AUTHORITY, "Stage80R1 reconciliation authority")
    if addendum.get("stage") != "STAGE80R1_REGISTRY_PIN_RECONCILIATION":
        fail("Stage80R1 authority stage drift")
    if addendum.get("current_stage80_registry", {}).get("blob") != STAGE80_REGISTRY_GIT_BLOB:
        fail("Stage80R1 addendum no longer binds current Stage80 registry")
    registry = load_json(STAGE80_REGISTRY, "Stage80 registry")
    if registry.get("status") != "TECHNICAL_SENSITIVE_DATA_MINIMIZATION_REGISTRY_NOT_FINAL_LEGAL_CLASSIFICATION_NOT_POLICY_NOT_EVIDENCE":
        fail("Stage80 registry status drift")
    observed = [
        item.get("surface_id") for item in registry.get("table_backed_surfaces", []) if isinstance(item, dict)
    ] + [
        item.get("surface_id") for item in registry.get("non_table_surfaces", []) if isinstance(item, dict)
    ]
    if observed != EXPECTED_SURFACE_IDS:
        fail("Stage80 registry surface identity/order drift")
    return sha256_file(STAGE80R1_AUTHORITY), sha256_file(STAGE80_REGISTRY)


def validate_participants(value: object) -> list[dict]:
    if not isinstance(value, list) or len(value) != 2:
        fail("participants must contain exactly legal_review and privacy_review")
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
        if item.get("artifact_secret_values_absent_or_redacted") is not True:
            fail(f"{role} must confirm artifact secret absence/redaction")
        if item.get("acknowledged_real_review") is not True:
            fail(f"{role} must acknowledge real independent review")
        artifact_path = Path(artifact_raw).expanduser().resolve()
        artifact_digest = validate_artifact(artifact_path, f"{role}.review_artifact")
        output.append({
            "role": role,
            "reviewer_reference_sha256": sha256_bytes(reviewer_ref.encode("utf-8")),
            "review_artifact_sha256": artifact_digest,
        })
    return output


def validate_surfaces(value: object) -> list[dict]:
    if not isinstance(value, list) or len(value) != 9:
        fail("surface_reviews must contain exactly nine Stage80 surfaces")
    ids = [item.get("surface_id") for item in value if isinstance(item, dict)]
    if ids != EXPECTED_SURFACE_IDS:
        fail("surface review identity/order drift")
    output: list[dict] = []
    for item in value:
        if not isinstance(item, dict):
            fail("surface review entry must be an object")
        surface_id = item["surface_id"]
        decision: dict[str, str] = {}
        for key in REVIEW_FIELDS:
            decision[key] = real_text(item.get(key), f"{surface_id}.{key}")
        output.append({
            "surface_id": surface_id,
            "review_decision_sha256": canonical_sha256(decision),
        })
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review-input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    addendum_sha256, registry_sha256 = validate_upstream()
    input_path = args.review_input.expanduser().resolve()
    value = load_json(input_path, "real sensitive data treatment review input")

    if value.get("schema_version") != 1:
        fail("review input schema_version must be 1")
    if value.get("stage") != "STAGE81_SENSITIVE_DATA_TREATMENT_REVIEW_EXTERNAL_INPUT":
        fail("review input stage drift")
    if value.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("review input project_ref drift")
    if value.get("test_fixture") is not False:
        fail("review input is a test fixture; real external review is required")
    status = real_text(value.get("status"), "status")
    if status == "PLACEHOLDER_TEMPLATE_NOT_REAL_REVIEW_MATERIAL_MUST_FAIL_COLLECTOR":
        fail("review input is the committed placeholder template")

    binding = value.get("upstream_binding")
    if not isinstance(binding, dict):
        fail("upstream_binding is required")
    if binding.get("stage80r1_registry_pin_reconciliation_blob") != STAGE80R1_AUTHORITY_GIT_BLOB:
        fail("Stage80R1 addendum Git blob binding drift")
    if binding.get("current_stage80_registry_blob") != STAGE80_REGISTRY_GIT_BLOB:
        fail("current Stage80 registry Git blob binding drift")

    review_reference = real_text(value.get("review_session_reference"), "review_session_reference")
    reviewed_at_utc = validate_timestamp(value.get("reviewed_at"))
    participants = validate_participants(value.get("participants"))
    surfaces = validate_surfaces(value.get("surface_reviews"))
    cross_surface_ref = real_text(value.get("cross_surface_review_reference"), "cross_surface_review_reference")

    if value.get("all_surface_reviews_complete") is not True:
        fail("all_surface_reviews_complete must be true for real intake")
    if value.get("legal_and_privacy_review_complete") is not True:
        fail("legal_and_privacy_review_complete must be true for real intake")
    if value.get("canonical_independent_acceptance_performed") is not False:
        fail("canonical independent acceptance must remain a later step")
    if value.get("sensitive_data_treatment_decision_closed") is not False:
        fail("SENSITIVE_DATA_TREATMENT cannot be closed by Stage81 intake")
    if value.get("gate_promotion_performed") is not False:
        fail("Stage81 intake cannot promote any gate")

    candidate = {
        "schema_version": 1,
        "stage": "STAGE81_SENSITIVE_DATA_TREATMENT_REVIEW_INTAKE_BOUNDARY",
        "output_kind": "DIGEST_ONLY_SENSITIVE_DATA_TREATMENT_REVIEW_MATERIAL_CANDIDATE",
        "candidate_state": "REAL_EXTERNAL_SENSITIVE_DATA_TREATMENT_REVIEW_MATERIAL_DIGESTS_BOUND_AWAITING_CANONICAL_INDEPENDENT_ACCEPTANCE_NOT_POLICY_EVIDENCE",
        "stage80r1_authority_git_blob": STAGE80R1_AUTHORITY_GIT_BLOB,
        "stage80r1_authority_sha256": addendum_sha256,
        "stage80_registry_git_blob": STAGE80_REGISTRY_GIT_BLOB,
        "stage80_registry_sha256": registry_sha256,
        "review_input_sha256": sha256_file(input_path),
        "review_session_reference_sha256": sha256_bytes(review_reference.encode("utf-8")),
        "cross_surface_review_reference_sha256": sha256_bytes(cross_surface_ref.encode("utf-8")),
        "reviewed_at_utc": reviewed_at_utc,
        "participant_count": 2,
        "participants": participants,
        "surface_count": 9,
        "surface_reviews": surfaces,
        "reviewer_identity_copied": False,
        "review_artifact_paths_copied": False,
        "review_artifact_contents_copied": False,
        "review_decision_text_copied": False,
        "secret_values_copied": False,
        "external_review_material_collected": True,
        "canonical_independent_acceptance_performed": False,
        "legal_correctness_verified_by_collector": False,
        "final_sensitive_data_classification_approved": False,
        "sensitive_data_processing_policy_approved": False,
        "external_ai_sensitive_data_use_authorized": False,
        "marketing_sensitive_data_use_authorized": False,
        "candidate_documents_modified": False,
        "target_open_decision_closed": False,
        "legal_role_mapping_gate_ready": False,
        "legal_privacy_notice_gate_ready": False,
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
        "next_action": "CANONICAL_INDEPENDENT_ACCEPTANCE_REQUIRED_BEFORE_DRAFT_POLICY_OR_DOCUMENT_UPDATE_OR_SENSITIVE_DATA_TREATMENT_CLOSURE",
    }

    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(candidate, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

    print("STAGE81_SENSITIVE_DATA_REVIEW_CANDIDATE=PASS_DIGEST_ONLY")
    print("PARTICIPANT_COUNT=2")
    print("SURFACE_COUNT=9")
    print("FINAL_LEGAL_CLASSIFICATION_APPROVED=false")
    print("SENSITIVE_DATA_POLICY_APPROVED=false")
    print("TARGET_DECISION_CLOSED=false")
    print("GATE_PROMOTION=false")
    print("REMOTE_MUTATION=false")


if __name__ == "__main__":
    main()
