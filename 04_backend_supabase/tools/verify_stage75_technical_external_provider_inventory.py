from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage75_technical_external_provider_inventory_authority.json"
REGISTRY = ROOT / "10_compliance" / "inventory" / "STAGE75_TECHNICAL_EXTERNAL_SERVICE_SOURCE_REGISTRY.json"
DECISIONS = ROOT / "10_compliance" / "drafts" / "COMPLIANCE_OPEN_DECISIONS.json"
MATRIX = ROOT / "10_compliance" / "drafts" / "PROCESSING_ROLE_MATRIX_CANDIDATE.md"
BUILDER = BACKEND / "tools" / "build_stage75_technical_external_provider_inventory.py"
WORKFLOW = ROOT / ".github" / "workflows" / "stage75_technical_external_provider_inventory.yml"
FAILURE_CLASS = "BGF-STAGE75-TECHNICAL-PROVIDER-INVENTORY-GUARD-725"

EXPECTED_IDS = [
    "supabase",
    "telegram_bot_api",
    "asaas",
    "cloudflare_edge_signal",
    "github_repository_ci_pages",
]
EXPECTED_RELATIONSHIPS = {
    "supabase": "CONFIRMED_ACTIVE_DIRECT_TECHNICAL_SERVICE",
    "telegram_bot_api": "CONFIRMED_ACTIVE_EXTERNAL_ALERT_DELIVERY_SERVICE",
    "asaas": "SELECTED_PRODUCTION_BILLING_PROVIDER_NOT_ACTIVATED",
    "cloudflare_edge_signal": "INDIRECT_INFRASTRUCTURE_SIGNAL_OBSERVED_CONTRACTUAL_RELATIONSHIP_UNVERIFIED",
    "github_repository_ci_pages": "CONFIRMED_REPOSITORY_CI_SERVICE_STALE_PUBLIC_PAGES_SURFACE_NOT_CURRENT_PRODUCTION_AUTHORITY",
}
EXPECTED_SOURCE_PINS = {
    "flutter_pubspec": "644e57059c75964066645f8b9b0223f70a0a07c5",
    "student_access_edge_gateway": "e5a97eb416194110062fdd1ddcaeb307af7e8d0f",
    "student_access_production_edge_selection": "7f21a980d3cd3846a2500995a1ae57edc428d61a",
    "cf_origin_spoof_sentinel": "5aadef86b6061a1e7bf2fc8755c3218b0d49d51c",
    "student_access_alert_delivery_contract": "7dde0dbd4788c66df1ca82a5ae29996a4dd4dc3e",
    "stage35_alert_delivery_reconciliation": "f495f0c01bb16b049b5383f46db9868724b798e8",
    "stage39_billing_credential_preparation": "404a320c43ba1e1f7092f11686d9ce990a602329",
    "stage62_billing_final_reconciliation": "4c9c99ecb2f3f016287e9d5c7de1888e6e2c846f",
    "stage66_release_candidate": "8f3be15da1027d9a5bed6e7d1f43cefebcf6a9eb",
}
UNKNOWN_FIELDS = {
    "provider_legal_entity",
    "contract_or_dpa_reference",
    "processing_regions",
    "retention_terms",
    "international_transfer_mechanism",
    "subprocessor_chain",
    "legal_relationship_classification",
}
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
        "STAGE75_TECHNICAL_EXTERNAL_PROVIDER_INVENTORY_GUARD=FAIL\n"
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
        fail("Stage75 authority identity drift")
    if authority.get("stage") != "STAGE75_TECHNICAL_EXTERNAL_PROVIDER_INVENTORY_CANDIDATE":
        fail("Stage75 authority stage drift")
    if authority.get("baseline_main_sha") != "2a9fab9e102b5f750e22891f4527f8df375d937a":
        fail("Stage75 baseline main SHA drift")

    upstream = authority.get("upstream_authority")
    if not isinstance(upstream, dict):
        fail("Stage75 upstream authority missing")
    if upstream.get("stage74_independent_review_intake_blob") != "ac75422c37b74642e342fb516527463c4c7cd10e":
        fail("Stage74 authority blob pin drift")
    if upstream.get("stage67_open_decisions_blob") != "215d527c1cb79d7b72697f03f1f84887e3a72d95":
        fail("Stage67 open-decisions blob pin drift")
    if upstream.get("processing_role_matrix_candidate_blob") != "7ddaa7bef68f489478f5db3fb31beb79abadf026":
        fail("processing role matrix blob pin drift")

    pins = authority.get("technical_source_pins")
    if not isinstance(pins, dict) or set(pins) != set(EXPECTED_SOURCE_PINS):
        fail("Stage75 technical source pin set drift")
    for key, expected_blob in EXPECTED_SOURCE_PINS.items():
        item = pins.get(key)
        if not isinstance(item, dict) or item.get("blob") != expected_blob:
            fail(f"Stage75 technical source blob pin drift: {key}")
        path = item.get("path")
        if not isinstance(path, str) or not path:
            fail(f"Stage75 technical source path missing: {key}")
        if not (ROOT / path).is_file():
            fail(f"Stage75 pinned technical source missing from checkout: {key}")

    target = authority.get("target_open_decision")
    if not isinstance(target, dict):
        fail("Stage75 target decision missing")
    if target.get("id") != "SUBPROCESSOR_AND_TRANSFER_MAP" or target.get("state") != "OPEN":
        fail("Stage75 target decision identity/state drift")
    if set(target.get("affected_gates", [])) != {"legal_privacy_notice", "legal_role_mapping"}:
        fail("Stage75 target decision affected gates drift")
    if target.get("resolution_authority") != "provider evidence plus legal/privacy review":
        fail("Stage75 target resolution authority drift")

    contract = authority.get("inventory_contract")
    if not isinstance(contract, dict):
        fail("Stage75 inventory contract missing")
    if contract.get("service_count") != 5 or contract.get("expected_service_ids") != EXPECTED_IDS:
        fail("Stage75 expected service inventory drift")
    true_fields = (
        "source_claims_must_be_bound_to_repository_artifacts",
    )
    for key in true_fields:
        if contract.get(key) is not True:
            fail(f"Stage75 contract must keep {key}=true")
    false_fields = (
        "technical_relationship_labels_are_legal_classifications",
        "direct_subprocessor_designation_allowed",
        "provider_contract_evidence_present",
        "provider_region_evidence_present",
        "provider_retention_evidence_present",
        "international_transfer_mechanism_evidence_present",
        "provider_legal_entity_evidence_present",
        "subprocessor_chain_evidence_present",
        "cloudflare_direct_contract_may_be_inferred",
        "github_pages_may_be_treated_as_current_production_release",
        "asaas_may_be_treated_as_activated",
        "telegram_controlled_proof_may_be_generalized_to_customer_data_processing",
        "inventory_is_provider_evidence",
        "inventory_is_legal_review",
        "inventory_can_close_target_decision",
        "inventory_can_mark_gate_ready",
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
    for key in false_fields:
        if contract.get(key) is not False:
            fail(f"Stage75 contract must keep {key}=false")

    remote = authority.get("fresh_remote_read_only_receipt")
    if not isinstance(remote, dict):
        fail("Stage75 fresh remote receipt missing")
    if remote.get("auth_users") != 0 or remote.get("organizations") != 0 or remote.get("students") != 0:
        fail("Stage75 remote customer baseline drift")
    if remote.get("asaas_state") != "selected_pending_credentials" or remote.get("asaas_activated_at") is not None:
        fail("Stage75 remote Asaas baseline drift")
    if remote.get("remote_mutation_performed") is not False:
        fail("Stage75 remote receipt must preserve no mutation")

    gates = authority.get("gates")
    if not isinstance(gates, dict):
        fail("Stage75 gate map missing")
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
            fail(f"Stage75 external gate must remain denied: {gate}")
    for gate in ("controlled_launch", "paid_media", "launch"):
        if gates.get(gate) != "DENIED":
            fail(f"Stage75 {gate} must remain DENIED")
    return authority


def verify_target_decision() -> None:
    decisions = load(DECISIONS)
    if decisions.get("status") != "DRAFT_UNREVIEWED_NOT_EVIDENCE":
        fail("Stage67 decision registry status drift")
    unresolved = decisions.get("unresolved")
    if not isinstance(unresolved, list):
        fail("Stage67 unresolved decision array missing")
    target = next((item for item in unresolved if isinstance(item, dict) and item.get("id") == "SUBPROCESSOR_AND_TRANSFER_MAP"), None)
    if not isinstance(target, dict) or target.get("state") != "OPEN":
        fail("SUBPROCESSOR_AND_TRANSFER_MAP must remain OPEN")
    if set(target.get("applies_to", [])) != {"legal_privacy_notice", "legal_role_mapping"}:
        fail("SUBPROCESSOR_AND_TRANSFER_MAP affected gates drift")
    if target.get("resolution_authority") != "provider evidence plus legal/privacy review":
        fail("SUBPROCESSOR_AND_TRANSFER_MAP resolution authority drift")


def verify_matrix_boundary() -> None:
    try:
        text = MATRIX.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"processing role matrix unreadable: {type(exc).__name__}")
    for marker in (
        "DRAFT_UNREVIEWED_NOT_LEGAL_EVIDENCE",
        "HIPÓTESE, NÃO CONCLUSÃO JURÍDICA",
        "Nenhuma linha abaixo congela controlador, operador, base legal, transferência internacional ou retenção.",
        "Aprovar inventário real de subprocessadores, regiões e transferências internacionais.",
    ):
        if marker not in text:
            fail(f"processing role matrix boundary drift: {marker}")


def verify_registry() -> None:
    registry = load(REGISTRY)
    if registry.get("schema_version") != 1:
        fail("Stage75 registry schema drift")
    if registry.get("status") != "TECHNICAL_SOURCE_REGISTRY_NOT_LEGAL_PROVIDER_MAP_NOT_EVIDENCE":
        fail("Stage75 registry status drift")
    services = registry.get("services")
    if not isinstance(services, list) or len(services) != 5:
        fail("Stage75 registry service count drift")
    ids = [item.get("service_id") for item in services if isinstance(item, dict)]
    if ids != EXPECTED_IDS or len(ids) != 5:
        fail("Stage75 registry service order/set drift")

    for item in services:
        service_id = str(item.get("service_id", ""))
        if item.get("relationship_status") != EXPECTED_RELATIONSHIPS[service_id]:
            fail(f"Stage75 registry relationship drift: {service_id}")
        if not isinstance(item.get("source_artifacts"), list) or not item["source_artifacts"]:
            fail(f"Stage75 source artifacts missing: {service_id}")
        if not isinstance(item.get("source_claim_markers"), list) or not item["source_claim_markers"]:
            fail(f"Stage75 source markers missing: {service_id}")
        for key in UNKNOWN_FIELDS:
            value = str(item.get(key, ""))
            if not (value.startswith("UNKNOWN_") or value.startswith("UNRESOLVED_")):
                fail(f"Stage75 registry unresolved field improperly resolved: {service_id}.{key}")

    by_id = {item["service_id"]: item for item in services}
    if by_id["supabase"].get("customer_data_processing_possible_from_repo_design") is not True:
        fail("Supabase customer-data design possibility must remain explicit")
    if by_id["supabase"].get("current_customer_rows_observed") != 0:
        fail("Supabase current customer rows observation drift")

    telegram = by_id["telegram_bot_api"]
    if telegram.get("controlled_proof_used_real_customer_data") is not False:
        fail("Telegram controlled proof must remain non-customer")
    if telegram.get("payload_direct_student_identifiers_forbidden_by_contract") is not True:
        fail("Telegram direct student identifier minimization boundary drift")

    asaas = by_id["asaas"]
    for key in ("production_credentials_verified", "provider_activation_observed", "real_checkout_proof_completed"):
        if asaas.get(key) is not False:
            fail(f"Asaas premature activation/proof claim: {key}")

    cloudflare = by_id["cloudflare_edge_signal"]
    if cloudflare.get("direct_contract_with_fitnexus_proven") is not False or cloudflare.get("direct_provider_selection_by_fitnexus_proven") is not False:
        fail("Cloudflare direct relationship must remain unproven")
    if cloudflare.get("must_not_be_called_confirmed_subprocessor_from_repo_evidence") is not True:
        fail("Cloudflare legal caveat missing")

    github = by_id["github_repository_ci_pages"]
    if github.get("current_pages_surface_is_production_deployment_evidence") is not False:
        fail("GitHub Pages stale surface must not become production evidence")
    if github.get("customer_data_processing_by_pages_or_ci_attested") is not False:
        fail("GitHub customer-data processing must not be invented")

    boundaries = registry.get("hard_boundaries")
    if not isinstance(boundaries, dict):
        fail("Stage75 registry hard boundaries missing")
    for key, value in boundaries.items():
        if value is not False:
            fail(f"Stage75 registry hard boundary must remain false: {key}")


def verify_builder_source() -> None:
    try:
        source = BUILDER.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (OSError, SyntaxError) as exc:
        fail(f"Stage75 builder unreadable or invalid Python: {type(exc).__name__}")
    for node in ast.walk(tree):
        roots: list[str] = []
        if isinstance(node, ast.Import):
            roots.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.append(node.module.split(".")[0])
        for root in roots:
            if root in FORBIDDEN_IMPORT_ROOTS:
                fail(f"Stage75 builder imports forbidden network/remote module: {root}")
    for marker in (
        "NON_ATTESTING_SOURCE_DERIVED_TECHNICAL_EXTERNAL_SERVICE_INVENTORY",
        "TECHNICAL_SERVICE_RELATIONSHIPS_OBSERVED_LEGAL_PROVIDER_MAP_UNRESOLVED",
        "OBTAIN_REAL_PROVIDER_TERMS_REGION_RETENTION_TRANSFER_EVIDENCE_THEN_INDEPENDENT_LEGAL_PRIVACY_REVIEW",
        "confirmed_subprocessor\": False",
        "CONFIRMED_LEGAL_SUBPROCESSORS=0",
        "TARGET_DECISION_CLOSED=false",
        "LEGAL_GATE_READY=false",
    ):
        if marker not in source:
            fail(f"Stage75 builder missing required marker: {marker}")


def verify_workflow() -> None:
    try:
        text = WORKFLOW.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"Stage75 workflow unreadable: {type(exc).__name__}")
    lowered = text.lower()
    for token in FORBIDDEN_WORKFLOW_TOKENS:
        if token in lowered:
            fail(f"Stage75 workflow contains forbidden action/token: {token}")
    for marker in (
        "permissions:\n  contents: read",
        "Checkout exact head",
        "Verify Stage75 provider inventory contract",
        "Build deterministic technical inventory twice",
        "cmp",
        "Upload non-attesting technical provider inventory",
        "retention-days: 7",
        "LEGAL_SUBPROCESSOR_CLASSIFICATION=false",
        "PROVIDER_CONTRACT_EVIDENCE=false",
        "TARGET_DECISION_CLOSED=false",
        "GATE_PROMOTION=false",
        "CONTROLLED_LAUNCH=DENIED",
        "REMOTE_MUTATION=false",
    ):
        if marker not in text:
            fail(f"Stage75 workflow missing required marker: {marker}")


def verify_no_stage75_migration() -> None:
    matches = []
    for root in (BACKEND / "migrations", BACKEND / "supabase" / "migrations"):
        if root.exists():
            matches.extend(root.glob("*stage75*"))
    if matches:
        fail("Stage75 must not create a Supabase migration")


def main() -> None:
    verify_authority()
    verify_target_decision()
    verify_matrix_boundary()
    verify_registry()
    verify_builder_source()
    verify_workflow()
    verify_no_stage75_migration()

    print("STAGE75_TECHNICAL_EXTERNAL_PROVIDER_INVENTORY_GUARD=PASS")
    print("SERVICE_COUNT=5")
    print("TARGET_DECISION=SUBPROCESSOR_AND_TRANSFER_MAP")
    print("LEGAL_SUBPROCESSOR_CLASSIFICATION=false")
    print("PROVIDER_CONTRACT_EVIDENCE=false")
    print("TARGET_DECISION_CLOSED=false")
    print("GATE_PROMOTION=false")
    print("REMOTE_MUTATION=false")


if __name__ == "__main__":
    main()
