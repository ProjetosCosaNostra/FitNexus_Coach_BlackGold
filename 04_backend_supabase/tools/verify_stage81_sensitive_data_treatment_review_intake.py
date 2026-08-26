from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage81_sensitive_data_treatment_review_intake_authority.json"
ADDENDUM = BACKEND / "stage80r1_registry_pin_reconciliation_authority.json"
REGISTRY = ROOT / "10_compliance" / "inventory" / "STAGE80_TECHNICAL_SENSITIVE_DATA_MINIMIZATION_REGISTRY.json"
OPEN_DECISIONS = ROOT / "10_compliance" / "drafts" / "COMPLIANCE_OPEN_DECISIONS.json"
QUESTIONNAIRE = ROOT / "10_compliance" / "review" / "STAGE81_SENSITIVE_DATA_TREATMENT_REVIEW_QUESTIONNAIRE.md"
TEMPLATE = ROOT / "10_compliance" / "review" / "STAGE81_SENSITIVE_DATA_TREATMENT_REVIEW_INPUT_TEMPLATE.json"
COLLECTOR = BACKEND / "tools" / "collect_stage81_sensitive_data_treatment_review_candidate.py"
WORKFLOW = ROOT / ".github" / "workflows" / "stage81_sensitive_data_treatment_review_intake.yml"
FAILURE_CLASS = "BGF-STAGE81-SENSITIVE-DATA-TREATMENT-REVIEW-INTAKE-GUARD-791"
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
EXPECTED_ROLES = ["legal_review", "privacy_review"]
FORBIDDEN_IMPORT_ROOTS = {"os", "subprocess", "socket", "urllib", "http", "requests", "psycopg", "supabase"}
FORBIDDEN_WORKFLOW_TOKENS = (
    "git push", "apply_migration", "execute_sql", "supabase db", "curl ", "wget ",
    "deploy-pages", "actions/deploy-pages", "powershell",
)


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE81_SENSITIVE_DATA_TREATMENT_REVIEW_INTAKE=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\nDETAIL={detail}"
    )


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to load {path.relative_to(ROOT)}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"expected JSON object: {path.relative_to(ROOT)}")
    return value


def verify_authority() -> None:
    a = load(AUTHORITY)
    if a.get("schema_version") != 1 or a.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("Stage81 authority identity drift")
    if a.get("stage") != "STAGE81_SENSITIVE_DATA_TREATMENT_REVIEW_INTAKE_BOUNDARY":
        fail("Stage81 authority stage drift")
    if a.get("baseline_main_sha") != "a6f7b3efe64ac6995c3c2e0d53fc89aeda3bf91d":
        fail("Stage81 baseline main SHA drift")
    if a.get("current_state") != "SENSITIVE_DATA_TREATMENT_REVIEW_QUESTIONNAIRE_AND_EXTERNAL_DIGEST_ONLY_INTAKE_PREPARED_NO_LEGAL_CLASSIFICATION_OR_POLICY_APPROVAL_NO_GATE_PROMOTION":
        fail("Stage81 current state drift")

    pins = a.get("upstream_authority", {})
    expected_pins = {
        "stage80r1_registry_pin_reconciliation_blob": "3f05971fae97c0491ba8c532d0577383f2b630c6",
        "historical_stage80_authority_blob": "9461cf96aaa44f1b422f78a137fe338ef51eae87",
        "current_stage80_registry_blob": "2aacf6d36834f6542e0cc9ef1f9be360fc61019d",
        "open_decisions_blob": "215d527c1cb79d7b72697f03f1f84887e3a72d95",
    }
    for key, value in expected_pins.items():
        if pins.get(key) != value:
            fail(f"Stage81 upstream pin drift: {key}")

    remote = a.get("fresh_remote_read_only_receipt", {})
    if [remote.get("auth_users"), remote.get("organizations"), remote.get("students")] != [0, 0, 0]:
        fail("Stage81 remote customer baseline drift")
    if remote.get("asaas_state") != "selected_pending_credentials" or remote.get("asaas_activated_at") is not None:
        fail("Stage81 Asaas baseline drift")
    if remote.get("remote_mutation_performed") is not False:
        fail("Stage81 remote mutation boundary drift")

    target = a.get("target_open_decision", {})
    if target.get("id") != "SENSITIVE_DATA_TREATMENT" or target.get("state") != "OPEN":
        fail("SENSITIVE_DATA_TREATMENT must remain OPEN")
    if target.get("affected_gates") != ["legal_role_mapping", "legal_privacy_notice", "incident_response"]:
        fail("Stage81 affected gate set/order drift")
    if target.get("resolution_authority") != "independent legal/privacy review":
        fail("Stage81 resolution authority drift")
    if target.get("stage81_can_close_decision") is not False:
        fail("Stage81 cannot close SENSITIVE_DATA_TREATMENT")

    contract = a.get("review_intake_contract", {})
    if contract.get("expected_review_surface_count") != 9:
        fail("Stage81 review surface count drift")
    if contract.get("expected_participant_roles") != EXPECTED_ROLES:
        fail("Stage81 participant role order drift")
    true_keys = (
        "completed_input_must_remain_outside_repo",
        "committed_placeholder_input_must_fail",
        "test_fixture_input_must_fail",
        "real_traceable_review_session_reference_required",
        "real_review_artifact_per_participant_required",
        "all_review_surfaces_must_be_complete",
        "artifact_secret_values_must_be_absent_or_redacted",
        "collector_output_is_digest_only",
        "collector_may_hash_reviewer_references",
        "collector_may_hash_review_artifacts",
        "collector_may_hash_surface_decisions",
        "canonical_independent_acceptance_required_after_collection",
    )
    for key in true_keys:
        if contract.get(key) is not True:
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
        if contract.get(key) is not False:
            fail(f"Stage81 contract must keep {key}=false")
    if a.get("allowed_candidate_state") != "REAL_EXTERNAL_SENSITIVE_DATA_TREATMENT_REVIEW_MATERIAL_DIGESTS_BOUND_AWAITING_CANONICAL_INDEPENDENT_ACCEPTANCE_NOT_POLICY_EVIDENCE":
        fail("Stage81 allowed candidate state drift")

    gates = a.get("gates", {})
    for gate in ("billing_provider_credentials", "legal_terms_of_use", "legal_privacy_notice", "legal_role_mapping", "data_subject_request_channel", "incident_response", "production_deployment"):
        if not str(gates.get(gate, "")).startswith("DENIED_"):
            fail(f"Stage81 external gate must remain denied: {gate}")
    for gate in ("controlled_launch", "paid_media", "launch"):
        if gates.get(gate) != "DENIED":
            fail(f"Stage81 {gate} must remain DENIED")


def verify_upstream_and_decision() -> None:
    addendum = load(ADDENDUM)
    if addendum.get("stage") != "STAGE80R1_REGISTRY_PIN_RECONCILIATION":
        fail("Stage80R1 upstream authority stage drift")
    if addendum.get("current_stage80_registry", {}).get("blob") != "2aacf6d36834f6542e0cc9ef1f9be360fc61019d":
        fail("Stage80R1 current registry pin drift")
    if addendum.get("target_open_decision", {}).get("state") != "OPEN":
        fail("Stage80R1 target decision unexpectedly closed")

    registry = load(REGISTRY)
    if registry.get("status") != "TECHNICAL_SENSITIVE_DATA_MINIMIZATION_REGISTRY_NOT_FINAL_LEGAL_CLASSIFICATION_NOT_POLICY_NOT_EVIDENCE":
        fail("Stage80 registry status drift")
    ids = [x.get("surface_id") for x in registry.get("table_backed_surfaces", []) if isinstance(x, dict)] + [
        x.get("surface_id") for x in registry.get("non_table_surfaces", []) if isinstance(x, dict)
    ]
    if ids != EXPECTED_SURFACE_IDS:
        fail("Stage80 registry surface identity/order drift")
    for item in registry.get("table_backed_surfaces", []):
        if item.get("approved_policy_state") != "UNRESOLVED":
            fail(f"Stage80 surface unexpectedly approved: {item.get('surface_id')}")
    for item in registry.get("non_table_surfaces", []):
        if item.get("approved_policy_state") != "UNRESOLVED":
            fail(f"Stage80 non-table surface unexpectedly approved: {item.get('surface_id')}")

    decisions = load(OPEN_DECISIONS)
    unresolved = decisions.get("unresolved")
    target = next((x for x in unresolved if isinstance(x, dict) and x.get("id") == "SENSITIVE_DATA_TREATMENT"), None) if isinstance(unresolved, list) else None
    if not isinstance(target, dict) or target.get("state") != "OPEN":
        fail("global SENSITIVE_DATA_TREATMENT must remain OPEN")
    if target.get("required") != "Approved treatment/minimization rules for health, injury, pain or other potentially sensitive student information.":
        fail("global SENSITIVE_DATA_TREATMENT requirement drift")
    if target.get("resolution_authority") != "independent legal/privacy review":
        fail("global SENSITIVE_DATA_TREATMENT authority drift")


def verify_questionnaire_and_template() -> None:
    try:
        q = QUESTIONNAIRE.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"Stage81 questionnaire unreadable: {type(exc).__name__}")
    qlow = q.lower()
    for marker in (
        "review preparation only",
        "do not prepopulate or recommend a legal classification",
        "legal_review",
        "privacy_review",
        "exactly these nine stage80 surfaces",
        "real_external_sensitive_data_treatment_review_material_digests_bound_awaiting_canonical_independent_acceptance_not_policy_evidence",
        "does not mean",
        "external ai approved",
        "sensitive-data marketing approved",
    ):
        if marker not in qlow:
            fail(f"Stage81 questionnaire missing boundary marker: {marker}")
    for surface_id in EXPECTED_SURFACE_IDS:
        if surface_id not in q:
            fail(f"Stage81 questionnaire missing surface: {surface_id}")

    t = load(TEMPLATE)
    if t.get("schema_version") != 1 or t.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("Stage81 template identity drift")
    if t.get("stage") != "STAGE81_SENSITIVE_DATA_TREATMENT_REVIEW_EXTERNAL_INPUT":
        fail("Stage81 template stage drift")
    if t.get("test_fixture") is not True:
        fail("committed Stage81 template must remain an invalid test fixture")
    if t.get("status") != "PLACEHOLDER_TEMPLATE_NOT_REAL_REVIEW_MATERIAL_MUST_FAIL_COLLECTOR":
        fail("Stage81 template placeholder status drift")
    if t.get("upstream_binding") != {
        "stage80r1_registry_pin_reconciliation_blob": "3f05971fae97c0491ba8c532d0577383f2b630c6",
        "current_stage80_registry_blob": "2aacf6d36834f6542e0cc9ef1f9be360fc61019d",
    }:
        fail("Stage81 template upstream binding drift")
    participants = t.get("participants")
    if not isinstance(participants, list) or [x.get("role") for x in participants if isinstance(x, dict)] != EXPECTED_ROLES:
        fail("Stage81 template participant roles drift")
    for item in participants:
        if item.get("acknowledged_real_review") is not False or item.get("artifact_secret_values_absent_or_redacted") is not False:
            fail("committed Stage81 participant placeholders must remain false")
    surfaces = t.get("surface_reviews")
    if not isinstance(surfaces, list) or [x.get("surface_id") for x in surfaces if isinstance(x, dict)] != EXPECTED_SURFACE_IDS:
        fail("Stage81 template surface identity/order drift")
    if t.get("all_surface_reviews_complete") is not False or t.get("legal_and_privacy_review_complete") is not False:
        fail("committed Stage81 template completion flags must remain false")
    if t.get("canonical_independent_acceptance_performed") is not False or t.get("sensitive_data_treatment_decision_closed") is not False or t.get("gate_promotion_performed") is not False:
        fail("Stage81 template must not pre-accept, close or promote")


def verify_collector() -> None:
    try:
        source = COLLECTOR.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (OSError, SyntaxError) as exc:
        fail(f"Stage81 collector unreadable or invalid Python: {type(exc).__name__}")
    for node in ast.walk(tree):
        roots: list[str] = []
        if isinstance(node, ast.Import):
            roots.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.append(node.module.split(".")[0])
        for root in roots:
            if root in FORBIDDEN_IMPORT_ROOTS:
                fail(f"Stage81 collector imports forbidden remote module: {root}")
    for marker in (
        "REAL_EXTERNAL_SENSITIVE_DATA_TREATMENT_REVIEW_MATERIAL_DIGESTS_BOUND_AWAITING_CANONICAL_INDEPENDENT_ACCEPTANCE_NOT_POLICY_EVIDENCE",
        "reviewer_identity_copied\": False",
        "review_artifact_paths_copied\": False",
        "review_decision_text_copied\": False",
        "final_sensitive_data_classification_approved\": False",
        "sensitive_data_processing_policy_approved\": False",
        "external_ai_sensitive_data_use_authorized\": False",
        "marketing_sensitive_data_use_authorized\": False",
        "target_open_decision_closed\": False",
        "canonical_independent_acceptance_required\": True",
        "STAGE81_SENSITIVE_DATA_REVIEW_CANDIDATE=PASS_DIGEST_ONLY",
        "FINAL_LEGAL_CLASSIFICATION_APPROVED=false",
        "SENSITIVE_DATA_POLICY_APPROVED=false",
        "TARGET_DECISION_CLOSED=false",
        "REMOTE_MUTATION=false",
    ):
        if marker not in source:
            fail(f"Stage81 collector missing boundary marker: {marker}")


def verify_workflow() -> None:
    try:
        text = WORKFLOW.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"Stage81 workflow unreadable: {type(exc).__name__}")
    low = text.lower()
    for token in FORBIDDEN_WORKFLOW_TOKENS:
        if token in low:
            fail(f"Stage81 workflow contains forbidden token: {token}")
    for marker in (
        "permissions:\n  contents: read",
        "Checkout exact head",
        "Verify Stage81 sensitive data treatment review intake contract",
        "Prove committed placeholder sensitive data review input is refused",
        "STAGE81_SENSITIVE_DATA_REVIEW_CANDIDATE=FAIL",
        "Upload non-attesting Stage81 review intake boundary",
        "FINAL_LEGAL_CLASSIFICATION_APPROVED=false",
        "SENSITIVE_DATA_POLICY_APPROVED=false",
        "TARGET_DECISION_CLOSED=false",
        "GATE_PROMOTION=false",
        "CONTROLLED_LAUNCH=DENIED",
        "REMOTE_MUTATION=false",
    ):
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
    verify_upstream_and_decision()
    verify_questionnaire_and_template()
    verify_collector()
    verify_workflow()
    verify_no_stage81_migration()
    print("STAGE81_SENSITIVE_DATA_TREATMENT_REVIEW_INTAKE=PASS")
    print("PARTICIPANT_ROLE_COUNT=2")
    print("REVIEW_SURFACE_COUNT=9")
    print("PLACEHOLDER_INPUT_MUST_FAIL=true")
    print("FINAL_LEGAL_CLASSIFICATION_APPROVED=false")
    print("SENSITIVE_DATA_POLICY_APPROVED=false")
    print("TARGET_DECISION_CLOSED=false")
    print("REMOTE_MUTATION=false")


if __name__ == "__main__":
    main()
