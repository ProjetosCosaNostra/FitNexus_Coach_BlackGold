from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage76_provider_evidence_acquisition_boundary_authority.json"
STAGE75 = BACKEND / "stage75_technical_external_provider_inventory_authority.json"
REGISTRY = ROOT / "10_compliance" / "inventory" / "STAGE75_TECHNICAL_EXTERNAL_SERVICE_SOURCE_REGISTRY.json"
TEMPLATE = ROOT / "10_compliance" / "inventory" / "STAGE76_PROVIDER_EVIDENCE_INPUT_TEMPLATE.json"
COLLECTOR = BACKEND / "tools" / "collect_stage76_provider_evidence_candidate.py"
WORKFLOW = ROOT / ".github" / "workflows" / "stage76_provider_evidence_acquisition_boundary.yml"
FAILURE_CLASS = "BGF-STAGE76-PROVIDER-EVIDENCE-ACQUISITION-GUARD-735"

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
        "STAGE76_PROVIDER_EVIDENCE_ACQUISITION_GUARD=FAIL\n"
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


def verify_authority() -> dict:
    authority = load(AUTHORITY)
    if authority.get("schema_version") != 1 or authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("Stage76 authority identity drift")
    if authority.get("stage") != "STAGE76_PROVIDER_EVIDENCE_ACQUISITION_BOUNDARY":
        fail("Stage76 authority stage drift")
    if authority.get("baseline_main_sha") != "a0e22bc72954325e439d049c2f350bc77994a9b7":
        fail("Stage76 baseline main SHA drift")

    upstream = authority.get("upstream_authority")
    if not isinstance(upstream, dict):
        fail("Stage76 upstream authority missing")
    if upstream.get("stage75_provider_inventory_blob") != "8a4d0e6ce6a67360d432e401f34653916aeaf58d":
        fail("Stage75 authority blob pin drift")

    contract = authority.get("acquisition_contract")
    if not isinstance(contract, dict):
        fail("Stage76 acquisition contract missing")
    if contract.get("allowed_service_ids") != EXPECTED_IDS:
        fail("Stage76 allowed service IDs drift")
    if contract.get("required_artifact_keys") != EXPECTED_ARTIFACT_KEYS:
        fail("Stage76 required artifact keys drift")

    for key in (
        "real_external_artifacts_required",
        "each_artifact_must_be_nonempty_utf8",
        "secret_like_markers_rejected",
        "completed_input_must_remain_outside_repo",
        "committed_placeholder_input_must_fail",
        "test_fixture_input_must_fail",
        "collector_output_is_digest_only",
        "independent_legal_privacy_review_required_after_collection",
        "target_open_decision_remains_open_after_collection",
    ):
        if contract.get(key) is not True:
            fail(f"Stage76 contract must keep {key}=true")

    for key in (
        "collector_extracts_or_asserts_provider_facts",
        "collector_determines_legal_subprocessor_status",
        "collector_determines_transfer_legality",
        "collector_determines_contract_sufficiency",
        "collector_determines_retention_sufficiency",
        "collector_can_activate_asaas",
        "collector_accepts_billing_credentials_or_secrets",
        "collector_can_prove_cloudflare_direct_contract",
        "collector_can_make_github_production_authority",
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
            fail(f"Stage76 contract must keep {key}=false")

    separation = authority.get("scope_separation")
    if not isinstance(separation, dict) or separation.get("provider_web_research_inside_ci") is not False:
        fail("Stage76 provider research/CI scope boundary drift")
    for marker in ("Stage39/58/59/61/62", "Stage46/66/70/71"):
        if marker not in json.dumps(separation, sort_keys=True):
            fail(f"Stage76 upstream scope separation missing: {marker}")

    remote = authority.get("fresh_remote_read_only_receipt")
    if not isinstance(remote, dict):
        fail("Stage76 fresh remote receipt missing")
    if remote.get("auth_users") != 0 or remote.get("organizations") != 0 or remote.get("students") != 0:
        fail("Stage76 remote customer baseline drift")
    if remote.get("asaas_state") != "selected_pending_credentials" or remote.get("asaas_activated_at") is not None:
        fail("Stage76 remote Asaas baseline drift")
    if remote.get("remote_mutation_performed") is not False:
        fail("Stage76 remote receipt must preserve no mutation")

    gates = authority.get("gates")
    if not isinstance(gates, dict):
        fail("Stage76 gate map missing")
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
            fail(f"Stage76 external gate must remain denied: {gate}")
    for gate in ("controlled_launch", "paid_media", "launch"):
        if gates.get(gate) != "DENIED":
            fail(f"Stage76 {gate} must remain DENIED")
    return authority


def verify_stage75_inputs() -> None:
    stage75 = load(STAGE75)
    if stage75.get("stage") != "STAGE75_TECHNICAL_EXTERNAL_PROVIDER_INVENTORY_CANDIDATE":
        fail("Stage75 authority stage drift")
    target = stage75.get("target_open_decision", {})
    if target.get("id") != "SUBPROCESSOR_AND_TRANSFER_MAP" or target.get("state") != "OPEN":
        fail("Stage75 target decision must remain OPEN")
    if target.get("resolution_authority") != "provider evidence plus legal/privacy review":
        fail("Stage75 target decision resolution authority drift")

    registry = load(REGISTRY)
    if registry.get("status") != "TECHNICAL_SOURCE_REGISTRY_NOT_LEGAL_PROVIDER_MAP_NOT_EVIDENCE":
        fail("Stage75 registry status drift")
    services = registry.get("services")
    if not isinstance(services, list) or [item.get("service_id") for item in services if isinstance(item, dict)] != EXPECTED_IDS:
        fail("Stage75 registry service set/order drift")
    for item in services:
        if item.get("legal_relationship_classification", "").startswith(("UNKNOWN_", "UNRESOLVED_")) is False:
            fail(f"Stage75 legal relationship unexpectedly resolved: {item.get('service_id')}")


def verify_template() -> None:
    template = load(TEMPLATE)
    if template.get("schema_version") != 1:
        fail("Stage76 template schema drift")
    if template.get("input_kind") != "REAL_PROVIDER_PRIVACY_EVIDENCE_INPUT":
        fail("Stage76 template input kind drift")
    if template.get("status") != "PLACEHOLDER_TEMPLATE_NOT_REAL_PROVIDER_EVIDENCE":
        fail("Stage76 template status drift")
    if template.get("test_fixture") is not True or template.get("contains_placeholders") is not True:
        fail("committed Stage76 template must remain invalid placeholder fixture")
    if template.get("collector_acknowledges_stage75_relationship_status_only") is not False:
        fail("committed template must not acknowledge a real collection")
    if template.get("artifact_secret_values_absent_or_redacted_confirmed") is not False:
        fail("committed template must not attest artifact redaction")
    artifacts = template.get("artifacts")
    if not isinstance(artifacts, dict) or list(artifacts) != EXPECTED_ARTIFACT_KEYS:
        fail("Stage76 template artifact key order/set drift")
    boundary = template.get("scope_boundary")
    if not isinstance(boundary, dict):
        fail("Stage76 template scope boundary missing")
    for key, value in boundary.items():
        if value is not False:
            fail(f"Stage76 template scope boundary must remain false: {key}")


def verify_collector() -> None:
    try:
        source = COLLECTOR.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (OSError, SyntaxError) as exc:
        fail(f"Stage76 collector unreadable or invalid Python: {type(exc).__name__}")
    for node in ast.walk(tree):
        roots: list[str] = []
        if isinstance(node, ast.Import):
            roots.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.append(node.module.split(".")[0])
        for root in roots:
            if root in FORBIDDEN_IMPORT_ROOTS:
                fail(f"Stage76 collector imports forbidden network/remote module: {root}")
    for marker in (
        "DIGEST_ONLY_PROVIDER_PRIVACY_EVIDENCE_INTAKE_CANDIDATE",
        "REAL_EXTERNAL_SOURCE_ARTIFACT_DIGESTS_BOUND_AWAITING_INDEPENDENT_LEGAL_PRIVACY_REVIEW_NOT_GATE_EVIDENCE",
        "provider_facts_extracted_or_attested\": False",
        "legal_relationship_classified\": False",
        "billing_credential_evidence\": False",
        "target_open_decision_closed\": False",
        "INDEPENDENT_LEGAL_PRIVACY_REVIEW_OF_REAL_SOURCE_ARTIFACTS_REQUIRED_BEFORE_PROVIDER_MAP_DECISION",
        "PROVIDER_FACTS_ATTESTED=false",
        "LEGAL_RELATIONSHIP_CLASSIFIED=false",
        "TARGET_DECISION_CLOSED=false",
        "REMOTE_MUTATION=false",
    ):
        if marker not in source:
            fail(f"Stage76 collector missing required boundary marker: {marker}")


def verify_workflow() -> None:
    try:
        text = WORKFLOW.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"Stage76 workflow unreadable: {type(exc).__name__}")
    lowered = text.lower()
    for token in FORBIDDEN_WORKFLOW_TOKENS:
        if token in lowered:
            fail(f"Stage76 workflow contains forbidden action/token: {token}")
    for marker in (
        "permissions:\n  contents: read",
        "Checkout exact head",
        "Verify Stage76 provider evidence acquisition contract",
        "Prove committed placeholder provider evidence input is refused",
        "PLACEHOLDER_PROVIDER_EVIDENCE_INPUT_REFUSED=PASS",
        "PROVIDER_FACTS_ATTESTED=false",
        "LEGAL_RELATIONSHIP_CLASSIFIED=false",
        "TARGET_DECISION_CLOSED=false",
        "GATE_PROMOTION=false",
        "CONTROLLED_LAUNCH=DENIED",
        "REMOTE_MUTATION=false",
    ):
        if marker not in text:
            fail(f"Stage76 workflow missing required marker: {marker}")


def verify_no_stage76_migration() -> None:
    matches = []
    for root in (BACKEND / "migrations", BACKEND / "supabase" / "migrations"):
        if root.exists():
            matches.extend(root.glob("*stage76*"))
    if matches:
        fail("Stage76 must not create a Supabase migration")


def main() -> None:
    verify_authority()
    verify_stage75_inputs()
    verify_template()
    verify_collector()
    verify_workflow()
    verify_no_stage76_migration()

    print("STAGE76_PROVIDER_EVIDENCE_ACQUISITION_GUARD=PASS")
    print("SERVICE_COUNT=5")
    print("REQUIRED_ARTIFACTS_PER_SERVICE=8")
    print("PROVIDER_FACTS_ATTESTED=false")
    print("LEGAL_RELATIONSHIP_CLASSIFIED=false")
    print("TARGET_DECISION_CLOSED=false")
    print("GATE_PROMOTION=false")
    print("REMOTE_MUTATION=false")


if __name__ == "__main__":
    main()
