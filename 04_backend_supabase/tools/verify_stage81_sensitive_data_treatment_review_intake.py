from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage81_sensitive_data_treatment_review_intake_authority.json"
REGISTRY = ROOT / "10_compliance" / "inventory" / "STAGE80_TECHNICAL_SENSITIVE_DATA_MINIMIZATION_REGISTRY.json"
OPEN_DECISIONS = ROOT / "10_compliance" / "drafts" / "COMPLIANCE_OPEN_DECISIONS.json"
QUESTIONNAIRE = ROOT / "10_compliance" / "review" / "STAGE81_SENSITIVE_DATA_TREATMENT_REVIEW_QUESTIONNAIRE.md"
TEMPLATE = ROOT / "10_compliance" / "review" / "STAGE81_SENSITIVE_DATA_REVIEW_INPUT_TEMPLATE.json"
COLLECTOR = BACKEND / "tools" / "collect_stage81_sensitive_data_review_candidate.py"
WORKFLOW = ROOT / ".github" / "workflows" / "stage81_sensitive_data_treatment_review_intake.yml"
FAILURE_CLASS = "BGF-STAGE81-SENSITIVE-DATA-REVIEW-INTAKE-GUARD-792"

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
REQUIRED_FIELDS = [
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
FORBIDDEN_IMPORT_ROOTS = {"os", "subprocess", "socket", "urllib", "http", "requests", "psycopg", "supabase"}
FORBIDDEN_WORKFLOW_TOKENS = (
    "git push", "apply_migration", "execute_sql", "supabase db", "curl ", "wget ",
    "deploy-pages", "actions/deploy-pages", "powershell", "gh api", "gh pr merge",
)


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE81_SENSITIVE_DATA_REVIEW_INTAKE_GUARD=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\n"
        f"DETAIL={detail}"
    )


def load(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to load {label}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"{label} must be a JSON object")
    return value


def read(path: Path, label: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"unable to read {label}: {type(exc).__name__}")


def verify_authority() -> None:
    a = load(AUTHORITY, "Stage81 authority")
    if a.get("schema_version") != 1 or a.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("Stage81 authority identity drift")
    if a.get("stage") != "STAGE81_SENSITIVE_DATA_TREATMENT_REVIEW_INTAKE_BOUNDARY":
        fail("Stage81 authority stage drift")
    if a.get("baseline_main_sha") != "a6f7b3efe64ac6995c3c2e0d53fc89aeda3bf91d":
        fail("Stage81 baseline main SHA drift")
    if a.get("current_state") != "SENSITIVE_DATA_LEGAL_PRIVACY_REVIEW_QUESTIONNAIRE_AND_EXTERNAL_DIGEST_ONLY_INTAKE_PREPARED_NO_LEGAL_CLASSIFICATION_OR_POLICY_APPROVAL_NO_GATE_PROMOTION":
        fail("Stage81 current state drift")

    up = a.get("upstream_authority", {})
    expected_pins = {
        "stage80r1_reconciliation_blob": "3f05971fae97c0491ba8c532d0577383f2b630c6",
        "stage80_registry_blob": "2aacf6d36834f6542e0cc9ef1f9be360fc61019d",
        "open_decisions_blob": "215d527c1cb79d7b72697f03f1f84887e3a72d95",
        "stage80_green_head_sha": "c29183359eaf21ea421af09c23a7804ad23ab55b",
        "stage80_green_artifact_digest": "sha256:f504b98221d3b8c01527523e9f9c793037c984d007aebc74178c7d03fee3a95d",
    }
    for key, value in expected_pins.items():
        if up.get(key) != value:
            fail(f"Stage81 upstream pin drift: {key}")

    remote = a.get("fresh_remote_read_only_receipt", {})
    if [remote.get("auth_users"), remote.get("organizations"), remote.get("students")] != [0, 0, 0]:
        fail("Stage81 remote customer baseline drift")
    if remote.get("asaas_state") != "selected_pending_credentials" or remote.get("asaas_activated_at") is not None:
        fail("Stage81 Asaas baseline drift")
    if remote.get("remote_mutation_performed") is not False:
        fail("Stage81 remote receipt must preserve no mutation")

    target = a.get("target_open_decision", {})
    if target.get("id") != "SENSITIVE_DATA_TREATMENT" or target.get("state") != "OPEN":
        fail("Stage81 target decision must remain OPEN")
    if target.get("affected_gates") != ["legal_role_mapping", "legal_privacy_notice", "incident_response"]:
        fail("Stage81 affected gate set/order drift")
    if target.get("resolution_authority") != "independent legal/privacy review":
        fail("Stage81 target resolution authority drift")
    if target.get("stage81_can_close_decision") is not False:
        fail("Stage81 cannot close SENSITIVE_DATA_TREATMENT")

    c = a.get("review_intake_contract", {})
    if c.get("expected_review_surface_count") != 9 or c.get("expected_participant_roles") != EXPECTED_ROLES:
        fail("Stage81 review cardinality/role drift")
    true_keys = (
        "completed_input_must_remain_outside_repo",
        "committed_placeholder_input_must_fail",
        "test_fixture_input_must_fail",
        "real_traceable_review_session_reference_required",
        "real_review_artifact_per_participant_required",
        "all_review_surfaces_must_be_complete",
        "review_material_secret_values_must_be_absent_or_redacted",
        "collector_output_is_digest_only",
        "collector_may_hash_reviewer_references",
        "collector_may_hash_review_artifacts",
        "collector_may_hash_surface_decisions",
        "canonical_independent_acceptance_required_after_collection",
    )
    for key in true_keys:
        if c.get(key) is not True:
            fail(f"Stage81 contract must keep {key}=true")
    false_keys = (
        "collector_copies_reviewer_identity",
        "collector_copies_review_artifact_paths",
        "collector_copies_review_decision_text",
        "collector_verifies_legal_correctness",
        "collector_approves_sensitive_data_classification",
        "collector_approves_sensitive_data_processing_policy",
        "collector_authorizes_external_ai_sensitive_data_use",
        "collector_authorizes_marketing_sensitive_data_use",
        "collector_selects_legal_basis_or_consent",
        "collector_selects_retention_rule",
        "collector_selects_controller_processor_role",
        "collector_selects_incident_notification_obligation",
        "collector_updates_candidate_documents",
        "collector_closes_sensitive_data_treatment",
        "collector_marks_any_gate_ready",
        "network_calls_allowed",
        "provider_calls_allowed",
        "supabase_mutation_allowed",
        "deployment_action_allowed",
        "evidence_ref_creation_allowed",
        "evidence_digest_promotion_allowed",
        "evidence_migration_creation_allowed",
        "gate_promotion_allowed",
        "controlled_launch_promotion_allowed",
        "paid_media_promotion_allowed",
    )
    for key in false_keys:
        if c.get(key) is not False:
            fail(f"Stage81 contract must keep {key}=false")
    if a.get("required_surface_review_fields") != REQUIRED_FIELDS:
        fail("Stage81 required review fields drift")
    if a.get("allowed_candidate_state") != "REAL_EXTERNAL_SENSITIVE_DATA_REVIEW_MATERIAL_DIGESTS_BOUND_AWAITING_CANONICAL_INDEPENDENT_ACCEPTANCE_NOT_POLICY_EVIDENCE":
        fail("Stage81 allowed candidate state drift")

    gates = a.get("gates", {})
    for gate in ("billing_provider_credentials", "legal_terms_of_use", "legal_privacy_notice", "legal_role_mapping", "data_subject_request_channel", "incident_response", "production_deployment"):
        if not str(gates.get(gate, "")).startswith("DENIED_"):
            fail(f"Stage81 external gate must remain denied: {gate}")
    for gate in ("controlled_launch", "paid_media", "launch"):
        if gates.get(gate) != "DENIED":
            fail(f"Stage81 {gate} must remain DENIED")


def verify_registry_and_open_decision() -> None:
    r = load(REGISTRY, "Stage80 registry")
    if r.get("status") != "TECHNICAL_SENSITIVE_DATA_MINIMIZATION_REGISTRY_NOT_FINAL_LEGAL_CLASSIFICATION_NOT_POLICY_NOT_EVIDENCE":
        fail("Stage80 registry status drift")
    for key, value in r.get("global_boundaries", {}).items():
        if value is not False:
            fail(f"Stage80 registry boundary unexpectedly true: {key}")
    surface_ids = [
        item.get("surface_id")
        for group in (r.get("table_backed_surfaces"), r.get("non_table_surfaces"))
        if isinstance(group, list)
        for item in group
        if isinstance(item, dict)
    ]
    if surface_ids != EXPECTED_SURFACES:
        fail("Stage80 registry surface identity/order drift")
    for group in (r.get("table_backed_surfaces"), r.get("non_table_surfaces")):
        if not isinstance(group, list):
            fail("Stage80 registry surface group missing")
        for item in group:
            if item.get("approved_policy_state") != "UNRESOLVED":
                fail(f"Stage80 surface unexpectedly approved: {item.get('surface_id')}")

    d = load(OPEN_DECISIONS, "open decisions")
    unresolved = d.get("unresolved")
    if not isinstance(unresolved, list):
        fail("open decisions unresolved list missing")
    target = next((x for x in unresolved if isinstance(x, dict) and x.get("id") == "SENSITIVE_DATA_TREATMENT"), None)
    if not isinstance(target, dict) or target.get("state") != "OPEN":
        fail("global SENSITIVE_DATA_TREATMENT must remain OPEN")
    if target.get("applies_to") != ["legal_role_mapping", "legal_privacy_notice", "incident_response"]:
        fail("SENSITIVE_DATA_TREATMENT applies_to drift")
    if target.get("required") != "Approved treatment/minimization rules for health, injury, pain or other potentially sensitive student information.":
        fail("SENSITIVE_DATA_TREATMENT requirement drift")
    if target.get("resolution_authority") != "independent legal/privacy review":
        fail("SENSITIVE_DATA_TREATMENT resolution authority drift")


def verify_questionnaire() -> None:
    text = read(QUESTIONNAIRE, "Stage81 questionnaire")
    low = text.lower()
    markers = (
        "DO NOT PREPOPULATE OR RECOMMEND A LEGAL CLASSIFICATION.",
        "legal_review",
        "privacy_review",
        "canonical independent acceptance",
        "não deve ser preenchido por CI, automação, engenharia ou IA em nome dos revisores",
        "não autoriza uso",
        "SENSITIVE_DATA_TREATMENT",
    )
    for marker in markers:
        if marker.lower() not in low:
            fail(f"Stage81 questionnaire missing boundary marker: {marker}")
    for sid in EXPECTED_SURFACES:
        if sid not in text:
            fail(f"Stage81 questionnaire missing surface: {sid}")
    for field in REQUIRED_FIELDS:
        if field not in text:
            fail(f"Stage81 questionnaire missing required review field: {field}")


def verify_template() -> None:
    t = load(TEMPLATE, "Stage81 review input template")
    if t.get("schema_version") != 1 or t.get("stage") != "STAGE81_SENSITIVE_DATA_TREATMENT_EXTERNAL_REVIEW" or t.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("Stage81 template identity drift")
    if t.get("test_fixture") is not True:
        fail("committed Stage81 template must remain test_fixture=true")
    if t.get("source_binding") != {
        "stage80r1_authority_blob": "3f05971fae97c0491ba8c532d0577383f2b630c6",
        "stage80_registry_blob": "2aacf6d36834f6542e0cc9ef1f9be360fc61019d",
        "stage81_baseline_main_sha": "a6f7b3efe64ac6995c3c2e0d53fc89aeda3bf91d",
    }:
        fail("Stage81 template source binding drift")
    participants = t.get("participants")
    if not isinstance(participants, list) or [x.get("role") for x in participants if isinstance(x, dict)] != EXPECTED_ROLES:
        fail("Stage81 template participant role drift")
    if any(x.get("acknowledged_assignment") is not False for x in participants):
        fail("committed Stage81 template participant acknowledgment must remain false")
    surfaces = t.get("surface_reviews")
    if not isinstance(surfaces, list) or [x.get("surface_id") for x in surfaces if isinstance(x, dict)] != EXPECTED_SURFACES:
        fail("Stage81 template surface identity/order drift")
    for item in surfaces:
        if item.get("review_status") != "PENDING_REAL_REVIEW" or item.get("review_alignment_state") != "PENDING_REAL_REVIEW":
            fail(f"committed Stage81 template must remain pending: {item.get('surface_id')}")
        for field in REQUIRED_FIELDS:
            value = str(item.get(field, ""))
            if "REPLACE_WITH_REAL_" not in value:
                fail(f"committed Stage81 template must remain placeholder for {item.get('surface_id')}:{field}")


def verify_collector() -> None:
    source = read(COLLECTOR, "Stage81 collector")
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        fail(f"Stage81 collector invalid Python: {type(exc).__name__}")
    for node in ast.walk(tree):
        roots: list[str] = []
        if isinstance(node, ast.Import):
            roots.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.append(node.module.split(".")[0])
        for root in roots:
            if root in FORBIDDEN_IMPORT_ROOTS:
                fail(f"Stage81 collector imports forbidden remote module: {root}")
    markers = (
        "REAL_EXTERNAL_SENSITIVE_DATA_REVIEW_MATERIAL_DIGESTS_BOUND_AWAITING_CANONICAL_INDEPENDENT_ACCEPTANCE_NOT_POLICY_EVIDENCE",
        "completed Stage81 review input must remain outside the repository",
        "test_fixture must be explicitly false",
        '"reviewer_identity_copied": False',
        '"review_artifact_path_copied": False',
        '"review_decision_text_copied": False',
        '"final_sensitive_data_classification_approved": False',
        '"sensitive_data_processing_policy_approved": False',
        '"external_ai_sensitive_data_use_authorized": False',
        '"marketing_sensitive_data_use_authorized": False',
        '"target_open_decision_closed": False',
        '"evidence_migration_created": False',
        '"gate_promotion": False',
        '"remote_mutation": False',
    )
    for marker in markers:
        if marker not in source:
            fail(f"Stage81 collector missing boundary marker: {marker}")


def verify_workflow() -> None:
    text = read(WORKFLOW, "Stage81 workflow")
    low = text.lower()
    for token in FORBIDDEN_WORKFLOW_TOKENS:
        if token in low:
            fail(f"Stage81 workflow contains forbidden action/token: {token}")
    markers = (
        "permissions:\n  contents: read",
        "Checkout exact head",
        "Verify Stage81 sensitive data review intake contract",
        "Prove committed placeholder sensitive-data review input is refused",
        "Upload non-attesting Stage81 review intake boundary",
        "FINAL_SENSITIVE_DATA_CLASSIFICATION_APPROVED=false",
        "SENSITIVE_DATA_PROCESSING_POLICY_APPROVED=false",
        "TARGET_DECISION_CLOSED=false",
        "GATE_PROMOTION=false",
        "CONTROLLED_LAUNCH=DENIED",
        "REMOTE_MUTATION=false",
    )
    for marker in markers:
        if marker not in text:
            fail(f"Stage81 workflow missing marker: {marker}")


def verify_no_stage81_migration() -> None:
    found: list[Path] = []
    for root in (BACKEND / "migrations", BACKEND / "supabase" / "migrations"):
        if root.exists():
            found.extend(root.glob("*stage81*"))
    if found:
        fail("Stage81 must not create a Supabase migration")


def main() -> None:
    verify_authority()
    verify_registry_and_open_decision()
    verify_questionnaire()
    verify_template()
    verify_collector()
    verify_workflow()
    verify_no_stage81_migration()
    print("STAGE81_SENSITIVE_DATA_REVIEW_INTAKE_GUARD=PASS")
    print("EXPECTED_PARTICIPANT_COUNT=2")
    print("EXPECTED_SURFACE_REVIEW_COUNT=9")
    print("FINAL_SENSITIVE_DATA_CLASSIFICATION_APPROVED=false")
    print("SENSITIVE_DATA_PROCESSING_POLICY_APPROVED=false")
    print("TARGET_DECISION_CLOSED=false")
    print("GATE_PROMOTION=false")
    print("REMOTE_MUTATION=false")


if __name__ == "__main__":
    main()
