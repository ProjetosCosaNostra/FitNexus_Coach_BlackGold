from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage79_retention_decision_review_intake_authority.json"
STAGE78 = BACKEND / "stage78_technical_retention_surface_inventory_authority.json"
REGISTRY = ROOT / "10_compliance" / "inventory" / "STAGE78_TECHNICAL_DATA_RETENTION_SURFACE_REGISTRY.json"
OPEN_DECISIONS = ROOT / "10_compliance" / "drafts" / "COMPLIANCE_OPEN_DECISIONS.json"
QUESTIONNAIRE = ROOT / "10_compliance" / "review" / "STAGE79_RETENTION_DECISION_QUESTIONNAIRE.md"
TEMPLATE = ROOT / "10_compliance" / "review" / "STAGE79_RETENTION_REVIEW_INPUT_TEMPLATE.json"
COLLECTOR = BACKEND / "tools" / "collect_stage79_retention_review_candidate.py"
WORKFLOW = ROOT / ".github" / "workflows" / "stage79_retention_decision_review_intake.yml"
FAILURE_CLASS = "BGF-STAGE79-RETENTION-REVIEW-INTAKE-GUARD-765"

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
FORBIDDEN_IMPORT_ROOTS = {
    "os",
    "subprocess",
    "socket",
    "urllib",
    "http",
    "requests",
    "psycopg",
    "supabase",
}
FORBIDDEN_WORKFLOW_TOKENS = (
    "git push",
    "apply_migration",
    "execute_sql",
    "supabase db",
    "curl ",
    "wget ",
    "deploy-pages",
    "actions/deploy-pages",
    "powershell",
)


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE79_RETENTION_REVIEW_INTAKE_GUARD=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\n"
        f"DETAIL={detail}"
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
    authority = load(AUTHORITY)
    if authority.get("schema_version") != 1 or authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("Stage79 authority identity drift")
    if authority.get("stage") != "STAGE79_RETENTION_DECISION_REVIEW_INTAKE_BOUNDARY":
        fail("Stage79 authority stage drift")
    if authority.get("baseline_main_sha") != "7f06f31b7005a07a1b527bed34839b2d93226fc6":
        fail("Stage79 baseline main SHA drift")
    if authority.get("current_state") != "RETENTION_REVIEW_QUESTIONNAIRE_AND_EXTERNAL_DIGEST_ONLY_INTAKE_PREPARED_NO_RETENTION_POLICY_APPROVAL_NO_GATE_PROMOTION":
        fail("Stage79 current state drift")

    upstream = authority.get("upstream_authority")
    if not isinstance(upstream, dict):
        fail("Stage79 upstream authority missing")
    expected_pins = {
        "stage78_retention_surface_inventory_blob": "fccb9879da90a3e0cb4a8cc7d8ef16010ffe89fe",
        "stage78_registry_blob": "9a5c8c549a26f04146298c8c1b52b2fb64a414ec",
        "open_decisions_blob": "215d527c1cb79d7b72697f03f1f84887e3a72d95",
    }
    for key, expected in expected_pins.items():
        if upstream.get(key) != expected:
            fail(f"Stage79 upstream pin drift: {key}")

    remote = authority.get("fresh_remote_read_only_receipt")
    if not isinstance(remote, dict):
        fail("Stage79 remote receipt missing")
    if remote.get("auth_users") != 0 or remote.get("organizations") != 0 or remote.get("students") != 0:
        fail("Stage79 remote customer baseline drift")
    if remote.get("asaas_state") != "selected_pending_credentials" or remote.get("asaas_activated_at") is not None:
        fail("Stage79 Asaas baseline drift")
    if remote.get("remote_mutation_performed") is not False:
        fail("Stage79 remote receipt must preserve no mutation")

    target = authority.get("target_open_decision")
    if not isinstance(target, dict):
        fail("Stage79 target decision missing")
    if target.get("id") != "RETENTION_MATRIX" or target.get("state") != "OPEN":
        fail("Stage79 target must remain RETENTION_MATRIX OPEN")
    if target.get("affected_gates") != ["legal_privacy_notice", "data_subject_request_channel", "incident_response"]:
        fail("Stage79 target gate set/order drift")
    if target.get("required") != "Approved category-by-category retention, backup expiration and legal-hold rules.":
        fail("Stage79 target requirement drift")
    if target.get("resolution_authority") != "legal/privacy/operations review":
        fail("Stage79 target resolution authority drift")
    if target.get("stage79_can_close_decision") is not False:
        fail("Stage79 must not close RETENTION_MATRIX")

    contract = authority.get("review_intake_contract")
    if not isinstance(contract, dict):
        fail("Stage79 review intake contract missing")
    if contract.get("expected_review_surface_count") != 12:
        fail("Stage79 expected review surface count drift")
    if contract.get("expected_participant_roles") != EXPECTED_PARTICIPANT_ROLES:
        fail("Stage79 participant role contract drift")
    for key in (
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
    ):
        if contract.get(key) is not True:
            fail(f"Stage79 contract must keep {key}=true")
    for key in (
        "collector_copies_reviewer_identity",
        "collector_copies_review_artifact_paths",
        "collector_copies_review_decision_text",
        "collector_verifies_legal_correctness",
        "collector_approves_retention_policy",
        "collector_updates_candidate_documents",
        "collector_closes_retention_matrix",
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
    ):
        if contract.get(key) is not False:
            fail(f"Stage79 contract must keep {key}=false")

    if authority.get("allowed_candidate_state") != "REAL_EXTERNAL_RETENTION_REVIEW_MATERIAL_DIGESTS_BOUND_AWAITING_CANONICAL_INDEPENDENT_ACCEPTANCE_NOT_POLICY_EVIDENCE":
        fail("Stage79 allowed candidate state drift")

    gates = authority.get("gates")
    if not isinstance(gates, dict):
        fail("Stage79 gate map missing")
    for gate in (
        "billing_provider_credentials",
        "legal_terms_of_use",
        "legal_privacy_notice",
        "legal_role_mapping",
        "data_subject_request_channel",
        "incident_response",
        "production_deployment",
    ):
        value = gates.get(gate)
        if not isinstance(value, str) or not value.startswith("DENIED_"):
            fail(f"Stage79 external gate must remain denied: {gate}")
    for gate in ("controlled_launch", "paid_media", "launch"):
        if gates.get(gate) != "DENIED":
            fail(f"Stage79 {gate} must remain DENIED")


def verify_stage78_and_open_decision() -> None:
    stage78 = load(STAGE78)
    if stage78.get("stage") != "STAGE78_TECHNICAL_RETENTION_SURFACE_INVENTORY":
        fail("Stage78 authority stage drift")
    target = stage78.get("target_open_decision")
    if not isinstance(target, dict) or target.get("id") != "RETENTION_MATRIX" or target.get("state") != "OPEN":
        fail("Stage78 RETENTION_MATRIX must remain OPEN")
    if target.get("resolution_authority") != "legal/privacy/operations review":
        fail("Stage78 retention resolution authority drift")

    registry = load(REGISTRY)
    if registry.get("status") != "TECHNICAL_DATA_RETENTION_SURFACE_REGISTRY_NOT_APPROVED_RETENTION_POLICY_NOT_EVIDENCE":
        fail("Stage78 registry status drift")
    categories = registry.get("categories")
    surfaces = registry.get("non_table_surfaces")
    if not isinstance(categories, list) or not isinstance(surfaces, list):
        fail("Stage78 registry surfaces missing")
    ids = [item.get("category_id") for item in categories if isinstance(item, dict)] + [
        item.get("surface_id") for item in surfaces if isinstance(item, dict)
    ]
    if ids != EXPECTED_SURFACE_IDS:
        fail("Stage78 registry surface set/order drift")
    for item in categories:
        if item.get("explicit_retention_period_in_registry") is not None:
            fail("Stage78 registry unexpectedly contains a retention period")

    decisions = load(OPEN_DECISIONS)
    unresolved = decisions.get("unresolved")
    if not isinstance(unresolved, list):
        fail("open decisions registry missing unresolved list")
    open_target = next((item for item in unresolved if isinstance(item, dict) and item.get("id") == "RETENTION_MATRIX"), None)
    if not isinstance(open_target, dict) or open_target.get("state") != "OPEN":
        fail("global RETENTION_MATRIX must remain OPEN")
    if open_target.get("resolution_authority") != "legal/privacy/operations review":
        fail("global RETENTION_MATRIX resolution authority drift")


def verify_questionnaire() -> None:
    try:
        text = QUESTIONNAIRE.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"Stage79 questionnaire unreadable: {type(exc).__name__}")
    for marker in (
        "REVIEW_INTAKE_QUESTIONNAIRE_NOT_POLICY_NOT_LEGAL_EVIDENCE",
        "DO NOT PREPOPULATE OR RECOMMEND A DURATION.",
        "RETENTION_MATRIX` continua OPEN",
        "REAL_EXTERNAL_RETENTION_REVIEW_MATERIAL_DIGESTS_BOUND_AWAITING_CANONICAL_INDEPENDENT_ACCEPTANCE_NOT_POLICY_EVIDENCE",
        "legal/privacy/operations",
        "backup_restore_and_expiration",
        "scheduled_cleanup_or_purge",
    ):
        if marker not in text:
            fail(f"Stage79 questionnaire missing boundary marker: {marker}")
    for surface_id in EXPECTED_SURFACE_IDS:
        if surface_id not in text:
            fail(f"Stage79 questionnaire missing surface: {surface_id}")


def verify_template() -> None:
    template = load(TEMPLATE)
    if template.get("schema_version") != 1 or template.get("input_kind") != "REAL_RETENTION_DECISION_REVIEW_INPUT":
        fail("Stage79 template identity drift")
    if template.get("status") != "PLACEHOLDER_TEMPLATE_NOT_REAL_RETENTION_REVIEW":
        fail("Stage79 template status drift")
    if template.get("test_fixture") is not True or template.get("contains_placeholders") is not True:
        fail("Stage79 committed template must remain invalid placeholder fixture")
    if template.get("stage78_registry_git_blob") != "9a5c8c549a26f04146298c8c1b52b2fb64a414ec":
        fail("Stage79 template Stage78 registry blob drift")

    participants = template.get("participants")
    if not isinstance(participants, list) or [item.get("role") for item in participants if isinstance(item, dict)] != EXPECTED_PARTICIPANT_ROLES:
        fail("Stage79 template participant roles/order drift")
    for item in participants:
        if not isinstance(item, dict):
            fail("Stage79 template participant must be object")
        if "<" not in str(item.get("reviewer_reference", "")) or "<" not in str(item.get("review_artifact_path", "")):
            fail(f"Stage79 template participant must remain placeholder: {item.get('role')}")

    review_surfaces = template.get("review_surfaces")
    if not isinstance(review_surfaces, list) or len(review_surfaces) != 12:
        fail("Stage79 template review surface count drift")
    if [item.get("surface_id") for item in review_surfaces if isinstance(item, dict)] != EXPECTED_SURFACE_IDS:
        fail("Stage79 template review surface identity/order drift")
    for item in review_surfaces:
        if not isinstance(item, dict):
            fail("Stage79 template surface must be object")
        if item.get("review_complete_for_surface") is not False:
            fail(f"Stage79 template surface must remain incomplete: {item.get('surface_id')}")
        for field in REVIEW_FIELDS:
            if "<" not in str(item.get(field, "")):
                fail(f"Stage79 template field must remain placeholder: {item.get('surface_id')}:{field}")

    if template.get("artifact_secret_values_absent_or_redacted_confirmed") is not False:
        fail("Stage79 committed template must not attest secret redaction")
    boundary = template.get("scope_boundary")
    if not isinstance(boundary, dict) or list(boundary) != SCOPE_KEYS:
        fail("Stage79 template scope boundary keys drift")
    for key in SCOPE_KEYS:
        if boundary.get(key) is not False:
            fail(f"Stage79 template scope boundary must remain false: {key}")


def verify_collector() -> None:
    try:
        source = COLLECTOR.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (OSError, SyntaxError) as exc:
        fail(f"Stage79 collector unreadable or invalid Python: {type(exc).__name__}")
    for node in ast.walk(tree):
        roots: list[str] = []
        if isinstance(node, ast.Import):
            roots.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.append(node.module.split(".")[0])
        for root in roots:
            if root in FORBIDDEN_IMPORT_ROOTS:
                fail(f"Stage79 collector imports forbidden network/remote module: {root}")
    for marker in (
        "DIGEST_ONLY_RETENTION_REVIEW_MATERIAL_CANDIDATE",
        "REAL_EXTERNAL_RETENTION_REVIEW_MATERIAL_DIGESTS_BOUND_AWAITING_CANONICAL_INDEPENDENT_ACCEPTANCE_NOT_POLICY_EVIDENCE",
        "reviewer_identity_copied\": False",
        "review_artifact_paths_copied\": False",
        "review_decision_text_copied\": False",
        "canonical_independent_acceptance_performed\": False",
        "retention_policy_approved\": False",
        "target_open_decision_closed\": False",
        "CANONICAL_INDEPENDENT_ACCEPTANCE_REQUIRED_BEFORE_RETENTION_POLICY_DRAFT_UPDATE_OR_RETENTION_MATRIX_CLOSURE",
        "STAGE79_RETENTION_REVIEW_CANDIDATE=PASS_DIGEST_ONLY",
        "RETENTION_POLICY_APPROVED=false",
        "TARGET_DECISION_CLOSED=false",
        "REMOTE_MUTATION=false",
    ):
        if marker not in source:
            fail(f"Stage79 collector missing required boundary marker: {marker}")


def verify_workflow() -> None:
    try:
        text = WORKFLOW.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"Stage79 workflow unreadable: {type(exc).__name__}")
    lowered = text.lower()
    for token in FORBIDDEN_WORKFLOW_TOKENS:
        if token in lowered:
            fail(f"Stage79 workflow contains forbidden action/token: {token}")
    for marker in (
        "permissions:\n  contents: read",
        "Checkout exact head",
        "Verify Stage79 retention decision review intake contract",
        "Prove committed placeholder retention review input is refused",
        "PLACEHOLDER_RETENTION_REVIEW_INPUT_REFUSED=PASS",
        "RETENTION_POLICY_APPROVED=false",
        "TARGET_DECISION_CLOSED=false",
        "GATE_PROMOTION=false",
        "CONTROLLED_LAUNCH=DENIED",
        "REMOTE_MUTATION=false",
    ):
        if marker not in text:
            fail(f"Stage79 workflow missing required marker: {marker}")


def verify_no_stage79_migration() -> None:
    matches: list[Path] = []
    for root in (BACKEND / "migrations", BACKEND / "supabase" / "migrations"):
        if root.exists():
            matches.extend(root.glob("*stage79*"))
    if matches:
        fail("Stage79 must not create a Supabase migration")


def main() -> None:
    verify_authority()
    verify_stage78_and_open_decision()
    verify_questionnaire()
    verify_template()
    verify_collector()
    verify_workflow()
    verify_no_stage79_migration()

    print("STAGE79_RETENTION_REVIEW_INTAKE_GUARD=PASS")
    print("PARTICIPANT_ROLE_COUNT=3")
    print("REVIEW_SURFACE_COUNT=12")
    print("RETENTION_POLICY_APPROVED=false")
    print("TARGET_DECISION_CLOSED=false")
    print("GATE_PROMOTION=false")
    print("REMOTE_MUTATION=false")


if __name__ == "__main__":
    main()
