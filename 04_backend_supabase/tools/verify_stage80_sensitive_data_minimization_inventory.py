from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage80_sensitive_data_minimization_inventory_authority.json"
REGISTRY = ROOT / "10_compliance" / "inventory" / "STAGE80_TECHNICAL_SENSITIVE_DATA_MINIMIZATION_REGISTRY.json"
OPEN_DECISIONS = ROOT / "10_compliance" / "drafts" / "COMPLIANCE_OPEN_DECISIONS.json"
ROLE_MATRIX = ROOT / "10_compliance" / "drafts" / "PROCESSING_ROLE_MATRIX_CANDIDATE.md"
PRIVACY = ROOT / "10_compliance" / "drafts" / "PRIVACY_NOTICE_CANDIDATE_PTBR.md"
INCIDENT = ROOT / "10_compliance" / "drafts" / "INCIDENT_RESPONSE_RUNBOOK_CANDIDATE.md"
BUILDER = BACKEND / "tools" / "build_stage80_sensitive_data_minimization_inventory.py"
WORKFLOW = ROOT / ".github" / "workflows" / "stage80_sensitive_data_minimization_inventory.yml"
FAILURE_CLASS = "BGF-STAGE80-SENSITIVE-DATA-MINIMIZATION-GUARD-775"
TABLE_IDS = [
    "student_profile_objective_and_context",
    "training_prescription_notes_and_lineage",
    "workout_feedback_pain_energy_and_notes",
    "decision_intelligence_context_and_outcomes",
    "coach_action_notes",
    "student_access_security_identifiers_and_alerts",
    "growth_attribution_and_marketing_boundary",
]
NON_TABLE_IDS = ["support_and_dsr_free_form_ingress", "incident_response_sensitive_data_handling"]
FORBIDDEN_IMPORT_ROOTS = {"os", "subprocess", "socket", "urllib", "http", "requests", "psycopg", "supabase"}
FORBIDDEN_WORKFLOW_TOKENS = (
    "git push", "apply_migration", "execute_sql", "supabase db", "curl ", "wget ",
    "deploy-pages", "actions/deploy-pages", "powershell",
)


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE80_SENSITIVE_DATA_MINIMIZATION_GUARD=FAIL\n"
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


def lower(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").lower()
    except OSError as exc:
        fail(f"unable to read {path.relative_to(ROOT)}: {type(exc).__name__}")


def verify_authority() -> None:
    a = load(AUTHORITY)
    if a.get("schema_version") != 1 or a.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("Stage80 authority identity drift")
    if a.get("stage") != "STAGE80_TECHNICAL_SENSITIVE_DATA_MINIMIZATION_INVENTORY":
        fail("Stage80 authority stage drift")
    if a.get("baseline_main_sha") != "1f9de92a9add0bc6762f153fd9ad2d40ac23fc71":
        fail("Stage80 baseline SHA drift")
    if a.get("current_state") != "SOURCE_DERIVED_SENSITIVE_DATA_EXPOSURE_AND_MINIMIZATION_SURFACES_INVENTORIED_NO_FINAL_LEGAL_CLASSIFICATION_NO_POLICY_OR_GATE_PROMOTION":
        fail("Stage80 current state drift")
    pins = a.get("upstream_authority", {})
    expected = {
        "stage79_retention_review_intake_blob": "1fd19a3747961f9ca4b4fb3950e6ade805779114",
        "stage78_retention_registry_blob": "9a5c8c549a26f04146298c8c1b52b2fb64a414ec",
        "open_decisions_blob": "215d527c1cb79d7b72697f03f1f84887e3a72d95",
        "processing_role_matrix_blob": "7ddaa7bef68f489478f5db3fb31beb79abadf026",
        "privacy_notice_candidate_blob": "1e5afdba4735469d734490883be8f7e011ac8159",
        "incident_runbook_candidate_blob": "e18ac0bec1c3d49cb9387e27f315d03c24efdf7d",
    }
    for key, value in expected.items():
        if pins.get(key) != value:
            fail(f"Stage80 upstream pin drift: {key}")
    if a.get("stage80_registry", {}).get("blob") != "b72c073e5b4079ef78dd3de94a5d3123dc7e4488":
        fail("Stage80 registry blob pin drift")
    target = a.get("target_open_decision", {})
    if target.get("id") != "SENSITIVE_DATA_TREATMENT" or target.get("state") != "OPEN":
        fail("SENSITIVE_DATA_TREATMENT must remain OPEN")
    if target.get("affected_gates") != ["legal_role_mapping", "legal_privacy_notice", "incident_response"]:
        fail("Stage80 affected gates drift")
    if target.get("resolution_authority") != "independent legal/privacy review":
        fail("Stage80 resolution authority drift")
    remote = a.get("fresh_remote_read_only_receipt", {})
    if [remote.get("auth_users"), remote.get("organizations"), remote.get("students")] != [0, 0, 0]:
        fail("Stage80 remote customer baseline drift")
    if remote.get("asaas_state") != "selected_pending_credentials" or remote.get("asaas_activated_at") is not None:
        fail("Stage80 Asaas baseline drift")
    if [remote.get("reviewed_public_table_count"), remote.get("reviewed_public_rls_enabled_count"), remote.get("reviewed_private_table_count"), remote.get("anon_authenticated_direct_table_grant_count")] != [8, 8, 6, 0]:
        fail("Stage80 bounded access-control observation drift")
    if remote.get("remote_mutation_performed") is not False:
        fail("Stage80 remote receipt must preserve no mutation")
    for key, value in remote.get("interpretation_boundaries", {}).items():
        if value is not False:
            fail(f"Stage80 remote interpretation boundary must remain false: {key}")
    c = a.get("inventory_contract", {})
    if c.get("expected_table_backed_surface_count") != 7 or c.get("expected_non_table_surface_count") != 2:
        fail("Stage80 surface cardinality drift")
    true_keys = (
        "technical_source_binding_required", "draft_document_boundary_binding_required",
        "migration_corpus_digest_required", "registry_digest_required",
        "technical_minimization_requirements_may_be_reported", "potentially_sensitive_source_flags_may_be_reported",
    )
    for key in true_keys:
        if c.get(key) is not True:
            fail(f"Stage80 contract must keep {key}=true")
    false_keys = (
        "potentially_sensitive_source_flags_are_final_legal_classification",
        "technical_minimization_requirements_are_approved_legal_policy", "legal_basis_may_be_selected",
        "consent_requirement_may_be_selected", "necessity_or_proportionality_may_be_legally_approved",
        "retention_period_may_be_selected", "incident_notification_decision_may_be_selected",
        "controller_processor_role_may_be_selected", "external_ai_sensitive_data_use_may_be_authorized",
        "marketing_sensitive_data_use_may_be_authorized", "target_open_decision_can_be_closed",
        "inventory_is_legal_review", "inventory_is_incident_evidence", "network_calls_allowed",
        "provider_calls_allowed", "supabase_mutation_allowed", "deployment_action_allowed",
        "evidence_ref_creation_allowed", "evidence_digest_promotion_allowed", "evidence_migration_creation_allowed",
        "gate_promotion_allowed", "controlled_launch_promotion_allowed", "paid_media_promotion_allowed",
    )
    for key in false_keys:
        if c.get(key) is not False:
            fail(f"Stage80 contract must keep {key}=false")
    gates = a.get("gates", {})
    for gate in ("billing_provider_credentials", "legal_terms_of_use", "legal_privacy_notice", "legal_role_mapping", "data_subject_request_channel", "incident_response", "production_deployment"):
        if not str(gates.get(gate, "")).startswith("DENIED_"):
            fail(f"Stage80 external gate must remain denied: {gate}")
    for gate in ("controlled_launch", "paid_media", "launch"):
        if gates.get(gate) != "DENIED":
            fail(f"Stage80 {gate} must remain DENIED")


def verify_registry_and_decision() -> None:
    r = load(REGISTRY)
    if r.get("status") != "TECHNICAL_SENSITIVE_DATA_MINIMIZATION_REGISTRY_NOT_FINAL_LEGAL_CLASSIFICATION_NOT_POLICY_NOT_EVIDENCE":
        fail("Stage80 registry status drift")
    for key, value in r.get("global_boundaries", {}).items():
        if value is not False:
            fail(f"Stage80 registry boundary must remain false: {key}")
    tables = r.get("table_backed_surfaces")
    non_tables = r.get("non_table_surfaces")
    if not isinstance(tables, list) or [x.get("surface_id") for x in tables if isinstance(x, dict)] != TABLE_IDS:
        fail("Stage80 table surface identity/order drift")
    if not isinstance(non_tables, list) or [x.get("surface_id") for x in non_tables if isinstance(x, dict)] != NON_TABLE_IDS:
        fail("Stage80 non-table surface identity/order drift")
    for item in tables:
        if item.get("approved_policy_state") != "UNRESOLVED" or not str(item.get("final_legal_classification", "")).startswith("UNRESOLVED_REQUIRES_"):
            fail(f"Stage80 surface unexpectedly resolved: {item.get('surface_id')}")
        if not item.get("technical_minimization_requirements_for_review"):
            fail(f"Stage80 surface minimization requirements missing: {item.get('surface_id')}")
    for item in non_tables:
        if item.get("approved_policy_state") != "UNRESOLVED":
            fail(f"Stage80 non-table surface unexpectedly resolved: {item.get('surface_id')}")
    context = r.get("observed_access_control_context", {})
    if [context.get("reviewed_public_table_count"), context.get("reviewed_public_rls_enabled_count"), context.get("reviewed_private_table_count"), context.get("anon_authenticated_direct_table_grant_count")] != [8, 8, 6, 0]:
        fail("Stage80 registry access-control observation drift")
    d = load(OPEN_DECISIONS)
    unresolved = d.get("unresolved")
    if not isinstance(unresolved, list):
        fail("open decisions list missing")
    target = next((x for x in unresolved if isinstance(x, dict) and x.get("id") == "SENSITIVE_DATA_TREATMENT"), None)
    if not isinstance(target, dict) or target.get("state") != "OPEN":
        fail("global SENSITIVE_DATA_TREATMENT must remain OPEN")
    if target.get("required") != "Approved treatment/minimization rules for health, injury, pain or other potentially sensitive student information.":
        fail("SENSITIVE_DATA_TREATMENT requirement drift")
    if target.get("resolution_authority") != "independent legal/privacy review":
        fail("SENSITIVE_DATA_TREATMENT authority drift")


def verify_drafts_case_insensitive() -> None:
    role = lower(ROLE_MATRIX)
    privacy = lower(PRIVACY)
    incident = lower(INCIDENT)
    for marker in ("draft_unreviewed_not_legal_evidence", "hipótese, não conclusão jurídica", "dados sensíveis não entram em utms/advertising payloads"):
        if marker not in role:
            fail(f"role matrix sensitive-data boundary missing: {marker}")
    for marker in ("draft_unreviewed_not_published_not_legal_evidence", "saúde, lesão, dor, limitações", "dados sensíveis não devem ser enviados em utms, payloads de advertising, logs desnecessários ou recibos de engenharia", "dados de saúde/sensíveis não devem ser reutilizados para segmentação publicitária"):
        if marker not in privacy:
            fail(f"privacy sensitive-data boundary missing: {marker}")
    for marker in ("draft_unreviewed_not_operational_evidence", "proteger tenants e dados potencialmente sensíveis", "potentially sensitive student data", "somente dados sintéticos/non-customer"):
        if marker not in incident:
            fail(f"incident sensitive-data boundary missing: {marker}")


def verify_builder() -> None:
    try:
        source = BUILDER.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (OSError, SyntaxError) as exc:
        fail(f"Stage80 builder unreadable or invalid Python: {type(exc).__name__}")
    for node in ast.walk(tree):
        roots: list[str] = []
        if isinstance(node, ast.Import):
            roots.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.append(node.module.split(".")[0])
        for root in roots:
            if root in FORBIDDEN_IMPORT_ROOTS:
                fail(f"Stage80 builder imports forbidden remote module: {root}")
    for marker in (
        "NON_ATTESTING_TECHNICAL_SENSITIVE_DATA_MINIMIZATION_INVENTORY",
        "SOURCE_SURFACES_AND_TECHNICAL_MINIMIZATION_REQUIREMENTS_BOUND_FINAL_LEGAL_CLASSIFICATION_AND_POLICY_UNRESOLVED_NOT_GATE_EVIDENCE",
        "potentially_sensitive_source_flags_are_final_legal_classification\": False",
        "technical_minimization_requirements_are_approved_legal_policy\": False",
        "external_ai_sensitive_data_use_authorized\": False",
        "marketing_sensitive_data_use_authorized\": False",
        "incident_notification_decision_made\": False",
        "target_open_decision_closed\": False",
        "REAL_INDEPENDENT_LEGAL_PRIVACY_REVIEW_REQUIRED_TO_APPROVE_SENSITIVE_DATA_CLASSIFICATION_PURPOSE_MINIMIZATION_AND_PROCESSING_RULES",
        "FINAL_LEGAL_CLASSIFICATION_APPROVED=false", "SENSITIVE_DATA_POLICY_APPROVED=false",
        "TARGET_DECISION_CLOSED=false", "REMOTE_MUTATION=false",
    ):
        if marker not in source:
            fail(f"Stage80 builder missing boundary marker: {marker}")


def verify_workflow() -> None:
    try:
        text = WORKFLOW.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"Stage80 workflow unreadable: {type(exc).__name__}")
    low = text.lower()
    for token in FORBIDDEN_WORKFLOW_TOKENS:
        if token in low:
            fail(f"Stage80 workflow contains forbidden action/token: {token}")
    for marker in (
        "permissions:\n  contents: read", "Checkout exact head",
        "Verify Stage80 sensitive data minimization contract",
        "Build deterministic sensitive data minimization inventory twice",
        "cmp /tmp/stage80_sensitive_a.json /tmp/stage80_sensitive_b.json",
        "Upload non-attesting sensitive data inventory", "FINAL_LEGAL_CLASSIFICATION_APPROVED=false",
        "SENSITIVE_DATA_POLICY_APPROVED=false", "TARGET_DECISION_CLOSED=false", "GATE_PROMOTION=false",
        "CONTROLLED_LAUNCH=DENIED", "REMOTE_MUTATION=false",
    ):
        if marker not in text:
            fail(f"Stage80 workflow missing marker: {marker}")


def verify_no_stage80_migration() -> None:
    found: list[Path] = []
    for root in (BACKEND / "migrations", BACKEND / "supabase" / "migrations"):
        if root.exists():
            found.extend(root.glob("*stage80*"))
    if found:
        fail("Stage80 must not create a Supabase migration")


def main() -> None:
    verify_authority()
    verify_registry_and_decision()
    verify_drafts_case_insensitive()
    verify_builder()
    verify_workflow()
    verify_no_stage80_migration()
    print("STAGE80_SENSITIVE_DATA_MINIMIZATION_GUARD=PASS")
    print("TABLE_BACKED_SURFACE_COUNT=7")
    print("NON_TABLE_SURFACE_COUNT=2")
    print("FINAL_LEGAL_CLASSIFICATION_APPROVED=false")
    print("SENSITIVE_DATA_POLICY_APPROVED=false")
    print("TARGET_DECISION_CLOSED=false")
    print("GATE_PROMOTION=false")
    print("REMOTE_MUTATION=false")


if __name__ == "__main__":
    main()
