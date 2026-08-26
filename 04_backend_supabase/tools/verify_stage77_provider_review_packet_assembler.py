from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage77_provider_review_packet_assembler_authority.json"
STAGE76 = BACKEND / "stage76_provider_evidence_acquisition_boundary_authority.json"
OPEN_DECISIONS = ROOT / "10_compliance" / "drafts" / "COMPLIANCE_OPEN_DECISIONS.json"
TEMPLATE = ROOT / "10_compliance" / "review" / "STAGE77_STAGE76_DIGEST_CANDIDATE_SET_TEMPLATE.json"
BUILDER = BACKEND / "tools" / "build_stage77_provider_review_packet.py"
WORKFLOW = ROOT / ".github" / "workflows" / "stage77_provider_review_packet_assembler.yml"
FAILURE_CLASS = "BGF-STAGE77-PROVIDER-REVIEW-PACKET-ASSEMBLER-GUARD-745"

EXPECTED_IDS = [
    "supabase",
    "telegram_bot_api",
    "asaas",
    "cloudflare_edge_signal",
    "github_repository_ci_pages",
]
EXPECTED_ARTIFACT_KEYS = [
    "relationship_scope_resolution",
    "provider_legal_entity_source",
    "contract_dpa_or_data_terms_source",
    "processing_purpose_and_data_categories_source",
    "processing_or_hosting_regions_source",
    "retention_and_deletion_terms_source",
    "subprocessor_chain_source",
    "international_transfer_mechanism_source",
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
        "STAGE77_PROVIDER_REVIEW_PACKET_ASSEMBLER_GUARD=FAIL\n"
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
        fail("Stage77 authority identity drift")
    if authority.get("stage") != "STAGE77_PROVIDER_REVIEW_PACKET_ASSEMBLER_BOUNDARY":
        fail("Stage77 authority stage drift")
    if authority.get("baseline_main_sha") != "c83fa7ae55876ada43b12d06985e87b7da44d8af":
        fail("Stage77 baseline main SHA drift")

    upstream = authority.get("upstream_authority")
    if not isinstance(upstream, dict):
        fail("Stage77 upstream authority missing")
    if upstream.get("stage76_provider_evidence_acquisition_blob") != "c07c2fca4894a2f6076ed86bb6587c3a878d93ec":
        fail("Stage76 authority blob pin drift")
    if upstream.get("open_decisions_blob") != "215d527c1cb79d7b72697f03f1f84887e3a72d95":
        fail("open-decisions blob pin drift")

    target = authority.get("target_open_decision")
    if not isinstance(target, dict):
        fail("Stage77 target decision missing")
    if target.get("id") != "SUBPROCESSOR_AND_TRANSFER_MAP" or target.get("state") != "OPEN":
        fail("Stage77 target decision must remain OPEN")
    if target.get("resolution_authority") != "provider evidence plus legal/privacy review":
        fail("Stage77 target resolution authority drift")
    if target.get("stage77_can_close_decision") is not False:
        fail("Stage77 may not close target decision")

    contract = authority.get("assembler_contract")
    if not isinstance(contract, dict):
        fail("Stage77 assembler contract missing")
    if contract.get("allowed_service_ids") != EXPECTED_IDS:
        fail("Stage77 allowed service IDs drift")
    if contract.get("required_stage76_output_kind") != "DIGEST_ONLY_PROVIDER_PRIVACY_EVIDENCE_INTAKE_CANDIDATE":
        fail("Stage77 required Stage76 output kind drift")
    if contract.get("required_stage76_candidate_state") != "REAL_EXTERNAL_SOURCE_ARTIFACT_DIGESTS_BOUND_AWAITING_INDEPENDENT_LEGAL_PRIVACY_REVIEW_NOT_GATE_EVIDENCE":
        fail("Stage77 required Stage76 candidate state drift")

    for key in (
        "real_stage76_digest_candidates_required",
        "candidate_set_completed_copy_must_remain_outside_repo",
        "committed_placeholder_candidate_set_must_fail",
        "test_fixture_candidate_set_must_fail",
        "candidate_entries_sorted_by_service_id",
        "packet_is_deterministic_for_same_source_and_candidates",
        "packet_can_include_stage76_digest_metadata",
        "independent_legal_privacy_review_required_after_packet",
    ):
        if contract.get(key) is not True:
            fail(f"Stage77 contract must keep {key}=true")

    for key in (
        "candidate_paths_copied_to_packet",
        "raw_provider_artifacts_copied_to_packet",
        "secret_values_copied_to_packet",
        "duplicate_service_candidates_allowed",
        "packet_extracts_or_attests_provider_facts",
        "packet_performs_legal_privacy_review",
        "packet_determines_legal_subprocessor_status",
        "packet_determines_transfer_legality",
        "packet_determines_contract_sufficiency",
        "packet_determines_retention_sufficiency",
        "all_five_services_present_can_close_decision",
        "partial_provider_set_can_close_decision",
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
            fail(f"Stage77 contract must keep {key}=false")

    remote = authority.get("fresh_remote_read_only_receipt")
    if not isinstance(remote, dict):
        fail("Stage77 fresh remote receipt missing")
    if remote.get("auth_users") != 0 or remote.get("organizations") != 0 or remote.get("students") != 0:
        fail("Stage77 remote customer baseline drift")
    if remote.get("asaas_state") != "selected_pending_credentials" or remote.get("asaas_activated_at") is not None:
        fail("Stage77 Asaas baseline drift")
    if remote.get("remote_mutation_performed") is not False:
        fail("Stage77 remote receipt must preserve no mutation")

    gates = authority.get("gates")
    if not isinstance(gates, dict):
        fail("Stage77 gate map missing")
    for gate in (
        "billing_provider_credentials",
        "legal_terms_of_use",
        "legal_privacy_notice",
        "legal_role_mapping",
        "data_subject_request_channel",
        "incident_response",
        "production_deployment",
    ):
        state = gates.get(gate)
        if not isinstance(state, str) or not state.startswith("DENIED_"):
            fail(f"Stage77 external gate must remain denied: {gate}")
    for gate in ("controlled_launch", "paid_media", "launch"):
        if gates.get(gate) != "DENIED":
            fail(f"Stage77 {gate} must remain DENIED")


def verify_upstream() -> None:
    stage76 = load(STAGE76)
    if stage76.get("stage") != "STAGE76_PROVIDER_EVIDENCE_ACQUISITION_BOUNDARY":
        fail("Stage76 authority stage drift")
    contract = stage76.get("acquisition_contract")
    if not isinstance(contract, dict) or contract.get("allowed_service_ids") != EXPECTED_IDS:
        fail("Stage76 allowed service IDs drift")
    if contract.get("required_artifact_keys") != EXPECTED_ARTIFACT_KEYS:
        fail("Stage76 required artifact keys drift")
    if contract.get("collector_output_is_digest_only") is not True:
        fail("Stage76 digest-only boundary drift")
    if contract.get("target_open_decision_remains_open_after_collection") is not True:
        fail("Stage76 target decision boundary drift")

    decisions = load(OPEN_DECISIONS)
    unresolved = decisions.get("unresolved")
    if not isinstance(unresolved, list):
        fail("open decisions registry missing unresolved list")
    target = next((x for x in unresolved if isinstance(x, dict) and x.get("id") == "SUBPROCESSOR_AND_TRANSFER_MAP"), None)
    if not isinstance(target, dict) or target.get("state") != "OPEN":
        fail("SUBPROCESSOR_AND_TRANSFER_MAP must remain OPEN")


def verify_template() -> None:
    template = load(TEMPLATE)
    if template.get("schema_version") != 1 or template.get("manifest_kind") != "STAGE77_REAL_STAGE76_DIGEST_CANDIDATE_SET":
        fail("Stage77 template identity drift")
    if template.get("status") != "PLACEHOLDER_TEMPLATE_NOT_REAL_STAGE76_CANDIDATE_SET":
        fail("Stage77 committed template status drift")
    if template.get("test_fixture") is not True or template.get("contains_placeholders") is not True:
        fail("Stage77 committed template must remain an invalid fixture")
    paths = template.get("candidate_paths")
    if not isinstance(paths, list) or len(paths) != 1 or "<" not in str(paths[0]):
        fail("Stage77 template must preserve placeholder candidate path")
    boundary = template.get("scope_boundary")
    if not isinstance(boundary, dict):
        fail("Stage77 template scope boundary missing")
    for key, value in boundary.items():
        if value is not False:
            fail(f"Stage77 template scope boundary must remain false: {key}")


def verify_builder() -> None:
    try:
        source = BUILDER.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (OSError, SyntaxError) as exc:
        fail(f"Stage77 builder unreadable or invalid Python: {type(exc).__name__}")
    for node in ast.walk(tree):
        roots: list[str] = []
        if isinstance(node, ast.Import):
            roots.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.append(node.module.split(".")[0])
        for root in roots:
            if root in FORBIDDEN_IMPORT_ROOTS:
                fail(f"Stage77 builder imports forbidden network/remote module: {root}")

    for marker in (
        "NON_ATTESTING_MULTI_PROVIDER_STAGE76_DIGEST_REVIEW_PACKET",
        "REAL_STAGE76_DIGEST_CANDIDATES_ASSEMBLED_AWAITING_INDEPENDENT_LEGAL_PRIVACY_REVIEW_NOT_GATE_EVIDENCE",
        "entries.sort(key=lambda item: item[\"service_id\"])",
        "provider_facts_extracted_or_attested\": False",
        "independent_legal_privacy_review_performed\": False",
        "target_open_decision_closed\": False",
        "legal_gate_ready_attested\": False",
        "REAL_INDEPENDENT_LEGAL_PRIVACY_REVIEW_REQUIRED_BEFORE_SUBPROCESSOR_AND_TRANSFER_MAP_DECISION",
        "PROVIDER_FACTS_ATTESTED=false",
        "LEGAL_REVIEW_PERFORMED=false",
        "TARGET_DECISION_CLOSED=false",
        "REMOTE_MUTATION=false",
    ):
        if marker not in source:
            fail(f"Stage77 builder missing required boundary marker: {marker}")


def verify_workflow() -> None:
    try:
        text = WORKFLOW.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"Stage77 workflow unreadable: {type(exc).__name__}")
    lowered = text.lower()
    for token in FORBIDDEN_WORKFLOW_TOKENS:
        if token in lowered:
            fail(f"Stage77 workflow contains forbidden action/token: {token}")
    for marker in (
        "permissions:\n  contents: read",
        "Checkout exact head",
        "Verify Stage77 provider review packet assembler contract",
        "Prove committed placeholder Stage76 candidate set is refused",
        "PLACEHOLDER_STAGE76_CANDIDATE_SET_REFUSED=PASS",
        "PROVIDER_FACTS_ATTESTED=false",
        "LEGAL_REVIEW_PERFORMED=false",
        "TARGET_DECISION_CLOSED=false",
        "GATE_PROMOTION=false",
        "CONTROLLED_LAUNCH=DENIED",
        "REMOTE_MUTATION=false",
    ):
        if marker not in text:
            fail(f"Stage77 workflow missing required marker: {marker}")


def verify_no_stage77_migration() -> None:
    matches: list[Path] = []
    for root in (BACKEND / "migrations", BACKEND / "supabase" / "migrations"):
        if root.exists():
            matches.extend(root.glob("*stage77*"))
    if matches:
        fail("Stage77 must not create a Supabase migration")


def main() -> None:
    verify_authority()
    verify_upstream()
    verify_template()
    verify_builder()
    verify_workflow()
    verify_no_stage77_migration()

    print("STAGE77_PROVIDER_REVIEW_PACKET_ASSEMBLER_GUARD=PASS")
    print("SERVICE_COUNT=5")
    print("REAL_STAGE76_CANDIDATES_REQUIRED=true")
    print("PROVIDER_FACTS_ATTESTED=false")
    print("LEGAL_REVIEW_PERFORMED=false")
    print("TARGET_DECISION_CLOSED=false")
    print("GATE_PROMOTION=false")
    print("REMOTE_MUTATION=false")


if __name__ == "__main__":
    main()
