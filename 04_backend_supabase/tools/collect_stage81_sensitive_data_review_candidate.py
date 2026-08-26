from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUTHORITY = ROOT / "04_backend_supabase" / "stage81_sensitive_data_treatment_review_intake_authority.json"
REGISTRY = ROOT / "10_compliance" / "inventory" / "STAGE80_TECHNICAL_SENSITIVE_DATA_MINIMIZATION_REGISTRY.json"
OPEN_DECISIONS = ROOT / "10_compliance" / "drafts" / "COMPLIANCE_OPEN_DECISIONS.json"

PROJECT_REF = "mceukeondizkwlpfxzgf"
STAGE = "STAGE81_SENSITIVE_DATA_TREATMENT_EXTERNAL_REVIEW"
EXPECTED_ROLES = ["legal_review", "privacy_review"]
EXPECTED_SURFACES = [
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
REQUIRED_SURFACE_FIELDS = [
    "legal_classification_review",
    "processing_purpose_review",
    "minimization_rule_review",
    "legal_basis_or_consent_review",
    "disclosure_recipient_review",
    "external_ai_review",
    "marketing_review",
    "controller_processor_dependency_ref",
    "retention_dependency_ref",
    "incident_dependency_ref",
    "review_material_ref",
]
PLACEHOLDER_MARKERS = (
    "replace_with",
    "pending_real_review",
    "placeholder",
    "example_only",
    "test_fixture",
    "todo",
)
SECRET_MARKERS = (
    b"-----begin private key-----",
    b"-----begin rsa private key-----",
    b"sk_live_",
    b"access_token=",
    b"api_key=",
    b"password=",
    b"authorization: bearer ",
)
CANDIDATE_STATE = "REAL_EXTERNAL_SENSITIVE_DATA_REVIEW_MATERIAL_DIGESTS_BOUND_AWAITING_CANONICAL_INDEPENDENT_ACCEPTANCE_NOT_POLICY_EVIDENCE"
FAILURE_CLASS = "BGF-STAGE81-SENSITIVE-DATA-REVIEW-INTAKE-GUARD-792"


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE81_SENSITIVE_DATA_REVIEW_COLLECTOR=FAIL\n"
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


def canonical_sha256(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def file_sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        fail(f"unable to hash external review artifact: {type(exc).__name__}")


def non_placeholder(value: object, label: str) -> str:
    if not isinstance(value, str) or len(value.strip()) < 4:
        fail(f"{label} must be a non-empty real review value")
    text = value.strip()
    low = text.lower()
    if any(marker in low for marker in PLACEHOLDER_MARKERS):
        fail(f"{label} contains placeholder/test material")
    return text


def outside_repo(path: Path, label: str) -> Path:
    try:
        resolved = path.expanduser().resolve(strict=True)
    except OSError as exc:
        fail(f"{label} does not resolve to an existing file: {type(exc).__name__}")
    if not resolved.is_file():
        fail(f"{label} must resolve to a file")
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError:
        return resolved
    fail(f"{label} must remain outside the repository")


def scan_secret_markers(path: Path, label: str) -> None:
    try:
        raw = path.read_bytes().lower()
    except OSError as exc:
        fail(f"unable to inspect {label}: {type(exc).__name__}")
    for marker in SECRET_MARKERS:
        if marker in raw:
            fail(f"{label} contains a secret-like marker and must be redacted")


def parse_reviewed_at(value: object) -> str:
    text = non_placeholder(value, "reviewed_at")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        fail("reviewed_at must be valid ISO-8601")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        fail("reviewed_at must be timezone-aware")
    return text


def validate_upstream() -> dict:
    authority = load_json(AUTHORITY, "Stage81 authority")
    registry = load_json(REGISTRY, "Stage80 registry")
    decisions = load_json(OPEN_DECISIONS, "open decisions")

    if authority.get("project_ref") != PROJECT_REF or authority.get("stage") != "STAGE81_SENSITIVE_DATA_TREATMENT_REVIEW_INTAKE_BOUNDARY":
        fail("Stage81 authority identity drift")
    if registry.get("status") != "TECHNICAL_SENSITIVE_DATA_MINIMIZATION_REGISTRY_NOT_FINAL_LEGAL_CLASSIFICATION_NOT_POLICY_NOT_EVIDENCE":
        fail("Stage80 registry status drift")

    registry_surfaces = [
        item.get("surface_id")
        for group in (registry.get("table_backed_surfaces"), registry.get("non_table_surfaces"))
        if isinstance(group, list)
        for item in group
        if isinstance(item, dict)
    ]
    if registry_surfaces != EXPECTED_SURFACES:
        fail("Stage80 registry surface identity/order drift")

    unresolved = decisions.get("unresolved")
    if not isinstance(unresolved, list):
        fail("open decisions unresolved list missing")
    target = next((x for x in unresolved if isinstance(x, dict) and x.get("id") == "SENSITIVE_DATA_TREATMENT"), None)
    if not isinstance(target, dict) or target.get("state") != "OPEN":
        fail("SENSITIVE_DATA_TREATMENT must remain OPEN")
    if target.get("resolution_authority") != "independent legal/privacy review":
        fail("SENSITIVE_DATA_TREATMENT resolution authority drift")
    return authority


def validate_input(input_path: Path, authority: dict) -> tuple[dict, list[dict], list[dict], dict]:
    try:
        resolved_input = input_path.expanduser().resolve(strict=True)
    except OSError as exc:
        fail(f"input path unavailable: {type(exc).__name__}")
    try:
        resolved_input.relative_to(ROOT.resolve())
    except ValueError:
        pass
    else:
        fail("completed Stage81 review input must remain outside the repository")

    data = load_json(resolved_input, "Stage81 external review input")
    if data.get("schema_version") != 1 or data.get("stage") != STAGE or data.get("project_ref") != PROJECT_REF:
        fail("Stage81 external review input identity drift")
    if data.get("test_fixture") is not False:
        fail("test_fixture must be explicitly false for real review material")

    binding = data.get("source_binding")
    if not isinstance(binding, dict):
        fail("source_binding missing")
    expected_binding = {
        "stage80r1_authority_blob": "3f05971fae97c0491ba8c532d0577383f2b630c6",
        "stage80_registry_blob": "2aacf6d36834f6542e0cc9ef1f9be360fc61019d",
        "stage81_baseline_main_sha": "a6f7b3efe64ac6995c3c2e0d53fc89aeda3bf91d",
    }
    if binding != expected_binding:
        fail("Stage81 source binding drift")

    session_ref = non_placeholder(data.get("review_session_reference"), "review_session_reference")
    reviewed_at = parse_reviewed_at(data.get("reviewed_at"))

    participants = data.get("participants")
    if not isinstance(participants, list) or len(participants) != len(EXPECTED_ROLES):
        fail("Stage81 requires exactly legal_review and privacy_review participants")
    if [x.get("role") for x in participants if isinstance(x, dict)] != EXPECTED_ROLES:
        fail("Stage81 participant role identity/order drift")

    participant_bindings: list[dict] = []
    for participant in participants:
        role = participant.get("role")
        if participant.get("acknowledged_assignment") is not True:
            fail(f"participant assignment not acknowledged: {role}")
        reviewer_ref = non_placeholder(participant.get("reviewer_reference"), f"{role}.reviewer_reference")
        artifact_text = non_placeholder(participant.get("review_artifact_path"), f"{role}.review_artifact_path")
        artifact = outside_repo(Path(artifact_text), f"{role}.review_artifact_path")
        scan_secret_markers(artifact, f"{role}.review_artifact")
        participant_bindings.append({
            "role": role,
            "reviewer_reference_sha256": hashlib.sha256(reviewer_ref.encode("utf-8")).hexdigest(),
            "review_artifact_sha256": file_sha256(artifact),
        })

    surface_reviews = data.get("surface_reviews")
    if not isinstance(surface_reviews, list) or len(surface_reviews) != len(EXPECTED_SURFACES):
        fail("Stage81 surface review count drift")
    if [x.get("surface_id") for x in surface_reviews if isinstance(x, dict)] != EXPECTED_SURFACES:
        fail("Stage81 surface review identity/order drift")

    surface_bindings: list[dict] = []
    for review in surface_reviews:
        sid = review.get("surface_id")
        if review.get("review_status") != "COMPLETED_REAL_REVIEW":
            fail(f"surface review must be completed by real reviewers: {sid}")
        alignment = review.get("review_alignment_state")
        if alignment not in ("CONSENSUS_RECORDED", "UNRESOLVED_DIFFERENCE_RECORDED"):
            fail(f"surface review alignment state invalid: {sid}")
        decision_payload: dict[str, str] = {"surface_id": sid, "review_alignment_state": alignment}
        for field in REQUIRED_SURFACE_FIELDS:
            decision_payload[field] = non_placeholder(review.get(field), f"{sid}.{field}")
        surface_bindings.append({
            "surface_id": sid,
            "surface_review_material_sha256": canonical_sha256(decision_payload),
            "decision_text_copied": False,
        })

    global_review = data.get("global_review_conclusion")
    if not isinstance(global_review, dict):
        fail("global_review_conclusion missing")
    completion = global_review.get("review_completion_state")
    if completion not in ("COMPLETED_WITH_CONCLUSIONS", "COMPLETED_WITH_UNRESOLVED_ITEMS"):
        fail("global review completion state invalid")
    unresolved_ref = non_placeholder(global_review.get("unresolved_items_ref"), "global_review_conclusion.unresolved_items_ref")
    material_ref = non_placeholder(global_review.get("global_review_material_ref"), "global_review_conclusion.global_review_material_ref")
    global_binding = {
        "global_review_conclusion_sha256": canonical_sha256({
            "review_completion_state": completion,
            "unresolved_items_ref": unresolved_ref,
            "global_review_material_ref": material_ref,
        })
    }

    metadata = {
        "review_session_reference_sha256": hashlib.sha256(session_ref.encode("utf-8")).hexdigest(),
        "reviewed_at": reviewed_at,
    }
    return metadata, participant_bindings, surface_bindings, global_binding


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    authority = validate_upstream()
    metadata, participants, surfaces, global_binding = validate_input(args.input, authority)

    output = {
        "schema_version": 1,
        "kind": "NON_ATTESTING_DIGEST_ONLY_SENSITIVE_DATA_TREATMENT_REVIEW_CANDIDATE",
        "state": CANDIDATE_STATE,
        "project_ref": PROJECT_REF,
        "source_binding": {
            "stage80r1_authority_blob": "3f05971fae97c0491ba8c532d0577383f2b630c6",
            "stage80_registry_blob": "2aacf6d36834f6542e0cc9ef1f9be360fc61019d",
            "stage81_baseline_main_sha": "a6f7b3efe64ac6995c3c2e0d53fc89aeda3bf91d",
        },
        **metadata,
        "participant_bindings": participants,
        "surface_review_bindings": surfaces,
        **global_binding,
        "reviewer_identity_copied": False,
        "review_artifact_path_copied": False,
        "review_decision_text_copied": False,
        "legal_correctness_verified": False,
        "final_sensitive_data_classification_approved": False,
        "sensitive_data_processing_policy_approved": False,
        "external_ai_sensitive_data_use_authorized": False,
        "marketing_sensitive_data_use_authorized": False,
        "legal_basis_or_consent_selected_by_collector": False,
        "retention_rule_selected_by_collector": False,
        "controller_processor_role_selected_by_collector": False,
        "incident_notification_obligation_selected_by_collector": False,
        "target_open_decision_closed": False,
        "canonical_independent_acceptance_required": True,
        "evidence_ref_created": False,
        "evidence_digest_promoted": False,
        "evidence_migration_created": False,
        "gate_promotion": False,
        "controlled_launch": False,
        "paid_media": False,
        "remote_mutation": False,
    }

    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except OSError as exc:
        fail(f"unable to write output: {type(exc).__name__}")

    print("STAGE81_SENSITIVE_DATA_REVIEW_COLLECTOR=PASS")
    print(f"STATE={CANDIDATE_STATE}")
    print("PARTICIPANT_COUNT=2")
    print("SURFACE_REVIEW_COUNT=9")
    print("FINAL_SENSITIVE_DATA_CLASSIFICATION_APPROVED=false")
    print("SENSITIVE_DATA_PROCESSING_POLICY_APPROVED=false")
    print("TARGET_DECISION_CLOSED=false")
    print("GATE_PROMOTION=false")
    print("REMOTE_MUTATION=false")


if __name__ == "__main__":
    main()
