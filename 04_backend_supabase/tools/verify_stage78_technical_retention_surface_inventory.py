from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage78_technical_retention_surface_inventory_authority.json"
REGISTRY = ROOT / "10_compliance" / "inventory" / "STAGE78_TECHNICAL_DATA_RETENTION_SURFACE_REGISTRY.json"
OPEN_DECISIONS = ROOT / "10_compliance" / "drafts" / "COMPLIANCE_OPEN_DECISIONS.json"
PRIVACY = ROOT / "10_compliance" / "drafts" / "PRIVACY_NOTICE_CANDIDATE_PTBR.md"
DSR = ROOT / "10_compliance" / "drafts" / "DATA_SUBJECT_REQUEST_RUNBOOK_CANDIDATE.md"
BUILDER = BACKEND / "tools" / "build_stage78_technical_retention_surface_inventory.py"
WORKFLOW = ROOT / ".github" / "workflows" / "stage78_technical_retention_surface_inventory.yml"
FAILURE_CLASS = "BGF-STAGE78-TECHNICAL-RETENTION-SURFACE-GUARD-755"

EXPECTED_CATEGORY_IDS = [
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
]
EXPECTED_NON_TABLE_IDS = ["backup_restore_and_expiration", "scheduled_cleanup_or_purge"]
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
        "STAGE78_TECHNICAL_RETENTION_SURFACE_GUARD=FAIL\n"
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
        fail("Stage78 authority identity drift")
    if authority.get("stage") != "STAGE78_TECHNICAL_RETENTION_SURFACE_INVENTORY":
        fail("Stage78 authority stage drift")
    if authority.get("baseline_main_sha") != "c92da46e17e7a8614545c62f6921f22ff661a10c":
        fail("Stage78 baseline main SHA drift")
    if authority.get("current_state") != "SOURCE_DERIVED_DATA_RETENTION_SURFACES_AND_LIFECYCLE_MARKERS_INVENTORIED_NO_RETENTION_PERIODS_APPROVED_NO_GATE_PROMOTION":
        fail("Stage78 current_state drift")

    upstream = authority.get("upstream_authority")
    if not isinstance(upstream, dict):
        fail("Stage78 upstream authority missing")
    expected_pins = {
        "stage77_provider_review_packet_blob": "12053a4ffbe60919511ca7f119671a291e418f48",
        "open_decisions_blob": "215d527c1cb79d7b72697f03f1f84887e3a72d95",
        "privacy_notice_candidate_blob": "1e5afdba4735469d734490883be8f7e011ac8159",
        "dsr_runbook_candidate_blob": "a4a9ee94d29dc17c9a76db2f8ede629d7c207ab8",
    }
    for key, expected in expected_pins.items():
        if upstream.get(key) != expected:
            fail(f"Stage78 upstream pin drift: {key}")

    target = authority.get("target_open_decision")
    if not isinstance(target, dict):
        fail("Stage78 target decision missing")
    if target.get("id") != "RETENTION_MATRIX" or target.get("state") != "OPEN":
        fail("RETENTION_MATRIX must remain OPEN")
    if target.get("affected_gates") != ["legal_privacy_notice", "data_subject_request_channel", "incident_response"]:
        fail("RETENTION_MATRIX affected gates drift")
    if target.get("resolution_authority") != "legal/privacy/operations review":
        fail("RETENTION_MATRIX resolution authority drift")

    remote = authority.get("fresh_remote_read_only_receipt")
    if not isinstance(remote, dict):
        fail("Stage78 remote read-only receipt missing")
    if remote.get("auth_users") != 0 or remote.get("organizations") != 0 or remote.get("students") != 0:
        fail("Stage78 remote customer baseline drift")
    if remote.get("asaas_state") != "selected_pending_credentials" or remote.get("asaas_activated_at") is not None:
        fail("Stage78 Asaas baseline drift")
    if remote.get("public_private_table_count") != 45:
        fail("Stage78 observed table count drift")
    if remote.get("cleanup_like_named_routines_observed") != 0:
        fail("Stage78 cleanup-like routine observation drift")
    if remote.get("storage_bucket_count") != 0 or remote.get("pg_cron_installed") is not False:
        fail("Stage78 storage/cron observation drift")
    if remote.get("remote_mutation_performed") is not False:
        fail("Stage78 remote receipt must preserve read-only state")
    interpretation = remote.get("interpretation_boundaries")
    if not isinstance(interpretation, dict) or not interpretation:
        fail("Stage78 remote interpretation boundaries missing")
    for key, value in interpretation.items():
        if value is not False:
            fail(f"Stage78 remote interpretation boundary must remain false: {key}")

    contract = authority.get("inventory_contract")
    if not isinstance(contract, dict):
        fail("Stage78 inventory contract missing")
    if contract.get("expected_category_count") != 10 or contract.get("expected_non_table_surface_count") != 2:
        fail("Stage78 inventory count contract drift")
    for key in (
        "technical_source_binding_required",
        "migration_corpus_digest_required",
        "registry_digest_required",
        "candidate_document_digests_required",
        "technical_lifecycle_markers_may_be_reported",
    ):
        if contract.get(key) is not True:
            fail(f"Stage78 contract must keep {key}=true")
    for key in (
        "technical_lifecycle_marker_is_retention_policy",
        "retention_periods_may_be_selected",
        "backup_expiration_may_be_selected",
        "legal_hold_rules_may_be_selected",
        "cancellation_or_delinquency_retention_may_be_selected",
        "anonymization_or_deletion_obligations_may_be_approved",
        "legal_basis_may_be_selected",
        "sensitivity_flags_are_final_legal_classification",
        "target_open_decision_can_be_closed",
        "inventory_is_legal_review",
        "inventory_is_operational_deletion_test",
        "inventory_is_dsr_evidence",
        "inventory_is_incident_response_evidence",
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
            fail(f"Stage78 contract must keep {key}=false")

    gates = authority.get("gates")
    if not isinstance(gates, dict):
        fail("Stage78 gate map missing")
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
            fail(f"Stage78 external gate must remain denied: {gate}")
    for gate in ("controlled_launch", "paid_media", "launch"):
        if gates.get(gate) != "DENIED":
            fail(f"Stage78 {gate} must remain DENIED")


def verify_registry() -> None:
    registry = load(REGISTRY)
    if registry.get("schema_version") != 1:
        fail("Stage78 registry schema drift")
    if registry.get("status") != "TECHNICAL_DATA_RETENTION_SURFACE_REGISTRY_NOT_APPROVED_RETENTION_POLICY_NOT_EVIDENCE":
        fail("Stage78 registry status drift")
    boundary = registry.get("policy_boundary")
    if not isinstance(boundary, dict) or not boundary:
        fail("Stage78 registry policy boundary missing")
    for key, value in boundary.items():
        if value is not False:
            fail(f"Stage78 registry boundary must remain false: {key}")

    categories = registry.get("categories")
    if not isinstance(categories, list) or len(categories) != 10:
        fail("Stage78 registry category count drift")
    ids = [item.get("category_id") for item in categories if isinstance(item, dict)]
    if ids != EXPECTED_CATEGORY_IDS:
        fail("Stage78 registry category identity/order drift")
    for item in categories:
        if item.get("explicit_retention_period_in_registry") is not None:
            fail(f"Stage78 registry invented retention period: {item.get('category_id')}")
        state = item.get("retention_policy_state")
        if not isinstance(state, str) or not state.startswith("UNRESOLVED_REQUIRES_"):
            fail(f"Stage78 registry category unexpectedly resolved: {item.get('category_id')}")
        if not isinstance(item.get("source_tables"), list) or not item.get("source_tables"):
            fail(f"Stage78 registry category missing source tables: {item.get('category_id')}")
        if not isinstance(item.get("observed_lifecycle_markers"), list) or not item.get("observed_lifecycle_markers"):
            fail(f"Stage78 registry category missing lifecycle markers: {item.get('category_id')}")

    surfaces = registry.get("non_table_surfaces")
    if not isinstance(surfaces, list) or len(surfaces) != 2:
        fail("Stage78 non-table surface count drift")
    if [item.get("surface_id") for item in surfaces if isinstance(item, dict)] != EXPECTED_NON_TABLE_IDS:
        fail("Stage78 non-table surface identity/order drift")
    for item in surfaces:
        state = item.get("retention_policy_state")
        if not isinstance(state, str) or not state.startswith("UNRESOLVED_REQUIRES_"):
            fail(f"Stage78 non-table surface unexpectedly resolved: {item.get('surface_id')}")


def verify_open_decision_and_docs() -> None:
    decisions = load(OPEN_DECISIONS)
    unresolved = decisions.get("unresolved")
    if not isinstance(unresolved, list):
        fail("open decisions list missing")
    target = next((x for x in unresolved if isinstance(x, dict) and x.get("id") == "RETENTION_MATRIX"), None)
    if not isinstance(target, dict) or target.get("state") != "OPEN":
        fail("RETENTION_MATRIX must remain OPEN")
    if target.get("required") != "Approved category-by-category retention, backup expiration and legal-hold rules.":
        fail("RETENTION_MATRIX requirement drift")

    try:
        privacy = PRIVACY.read_text(encoding="utf-8")
        dsr = DSR.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"candidate compliance document unreadable: {type(exc).__name__}")
    for marker in (
        "DRAFT_UNREVIEWED_NOT_PUBLISHED_NOT_LEGAL_EVIDENCE",
        "## 8. Retenção e eliminação",
        "Nenhum prazo deve ser inventado neste candidato.",
    ):
        if marker not in privacy:
            fail(f"privacy retention boundary missing: {marker}")
    for marker in (
        "DRAFT_UNREVIEWED_NOT_OPERATIONAL_EVIDENCE",
        "## 9. Eliminação, anonimização, bloqueio e retention hold — teste exigido",
        "Nenhum prazo ou obrigação é congelado por este candidato.",
    ):
        if marker not in dsr:
            fail(f"DSR retention boundary missing: {marker}")


def verify_builder() -> None:
    try:
        source = BUILDER.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (OSError, SyntaxError) as exc:
        fail(f"Stage78 builder unreadable or invalid Python: {type(exc).__name__}")
    for node in ast.walk(tree):
        roots: list[str] = []
        if isinstance(node, ast.Import):
            roots.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.append(node.module.split(".")[0])
        for root in roots:
            if root in FORBIDDEN_IMPORT_ROOTS:
                fail(f"Stage78 builder imports forbidden network/remote module: {root}")

    for marker in (
        "NON_ATTESTING_TECHNICAL_RETENTION_SURFACE_INVENTORY",
        "TECHNICAL_SURFACES_BOUND_RETENTION_PERIODS_AND_LEGAL_HOLD_BACKUP_PURGE_RULES_UNRESOLVED_NOT_GATE_EVIDENCE",
        "retention_periods_defined_count\": 0",
        "technical_lifecycle_markers_are_retention_policy\": False",
        "zero_customer_rows_resolves_retention\": False",
        "zero_cleanup_named_routines_proves_no_deletion_paths\": False",
        "zero_storage_buckets_proves_no_backup_or_provider_retention\": False",
        "sensitivity_source_flags_are_final_legal_classification\": False",
        "target_open_decision_closed\": False",
        "REAL_LEGAL_PRIVACY_OPERATIONS_REVIEW_REQUIRED_TO_SELECT_CATEGORY_RETENTION_BACKUP_PURGE_LEGAL_HOLD_AND_DELETION_RULES",
        "RETENTION_PERIODS_DEFINED=0",
        "TARGET_DECISION_CLOSED=false",
        "REMOTE_MUTATION=false",
    ):
        if marker not in source:
            fail(f"Stage78 builder missing boundary marker: {marker}")


def verify_workflow() -> None:
    try:
        text = WORKFLOW.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"Stage78 workflow unreadable: {type(exc).__name__}")
    lowered = text.lower()
    for token in FORBIDDEN_WORKFLOW_TOKENS:
        if token in lowered:
            fail(f"Stage78 workflow contains forbidden action/token: {token}")
    for marker in (
        "permissions:\n  contents: read",
        "Checkout exact head",
        "Verify Stage78 technical retention surface contract",
        "Build deterministic retention surface inventory twice",
        "cmp /tmp/stage78_retention_a.json /tmp/stage78_retention_b.json",
        "Upload non-attesting retention surface inventory",
        "RETENTION_PERIODS_DEFINED=0",
        "LEGAL_HOLD_RULES_APPROVED=false",
        "BACKUP_EXPIRATION_APPROVED=false",
        "TARGET_DECISION_CLOSED=false",
        "GATE_PROMOTION=false",
        "CONTROLLED_LAUNCH=DENIED",
        "REMOTE_MUTATION=false",
    ):
        if marker not in text:
            fail(f"Stage78 workflow missing required marker: {marker}")


def verify_no_stage78_migration() -> None:
    matches: list[Path] = []
    for root in (BACKEND / "migrations", BACKEND / "supabase" / "migrations"):
        if root.exists():
            matches.extend(root.glob("*stage78*"))
    if matches:
        fail("Stage78 must not create a Supabase migration")


def main() -> None:
    verify_authority()
    verify_registry()
    verify_open_decision_and_docs()
    verify_builder()
    verify_workflow()
    verify_no_stage78_migration()

    print("STAGE78_TECHNICAL_RETENTION_SURFACE_GUARD=PASS")
    print("CATEGORY_COUNT=10")
    print("NON_TABLE_SURFACE_COUNT=2")
    print("RETENTION_PERIODS_DEFINED=0")
    print("LEGAL_HOLD_RULES_APPROVED=false")
    print("BACKUP_EXPIRATION_APPROVED=false")
    print("TARGET_DECISION_CLOSED=false")
    print("GATE_PROMOTION=false")
    print("REMOTE_MUTATION=false")


if __name__ == "__main__":
    main()
