from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage82_technical_billing_lifecycle_policy_inventory_authority.json"
REGISTRY = ROOT / "10_compliance" / "inventory" / "STAGE82_TECHNICAL_BILLING_LIFECYCLE_POLICY_SURFACE_REGISTRY.json"
OPEN_DECISIONS = ROOT / "10_compliance" / "drafts" / "COMPLIANCE_OPEN_DECISIONS.json"
STAGE61 = BACKEND / "stage61_billing_authorization_state_machine_authority.json"
STAGE62 = BACKEND / "stage62_stage61_final_reconciliation_authority.json"
BUILDER = BACKEND / "tools" / "build_stage82_technical_billing_lifecycle_policy_inventory.py"
WORKFLOW = ROOT / ".github" / "workflows" / "stage82_technical_billing_lifecycle_policy_inventory.yml"
FAILURE_CLASS = "BGF-STAGE82-TECHNICAL-BILLING-LIFECYCLE-INVENTORY-GUARD-801"
EXPECTED_SURFACE_IDS = [
    "trial_lifecycle",
    "paid_period_and_entitlement_boundary",
    "cancel_at_period_end_intent",
    "delinquency_and_recovery",
    "terminal_subscription_cancellation",
    "checkout_intent_lifecycle",
    "webhook_reconciliation_and_payment_events",
    "subscription_authority_audit_trail",
    "plan_price_and_fee_assumption_boundaries",
    "provider_selection_and_external_billing_boundary",
]
FORBIDDEN_IMPORT_ROOTS = {"os", "subprocess", "socket", "urllib", "http", "requests", "psycopg", "supabase"}
FORBIDDEN_WORKFLOW_TOKENS = (
    "git push", "apply_migration", "execute_sql", "supabase db", "curl ", "wget ",
    "deploy-pages", "actions/deploy-pages", "powershell",
)


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE82_TECHNICAL_BILLING_LIFECYCLE_POLICY_INVENTORY_GUARD=FAIL\n"
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


def git_blob_sha(path: Path) -> str:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        fail(f"unable to read {path.relative_to(ROOT)}: {type(exc).__name__}")
    return hashlib.sha1(f"blob {len(raw)}\0".encode("utf-8") + raw).hexdigest()


def verify_authority() -> None:
    a = load(AUTHORITY)
    if a.get("schema_version") != 1 or a.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("Stage82 authority identity drift")
    if a.get("stage") != "STAGE82_TECHNICAL_BILLING_LIFECYCLE_POLICY_INVENTORY":
        fail("Stage82 stage drift")
    if a.get("baseline_main_sha") != "d88060f9e3787a9e34937385b1f69370ba5379fb":
        fail("Stage82 baseline main SHA drift")
    if a.get("current_state") != "TECHNICAL_BILLING_LIFECYCLE_SURFACES_INVENTORIED_POLICY_DECISIONS_UNRESOLVED_NOT_CUSTOMER_TERMS_EVIDENCE_NO_GATE_PROMOTION":
        fail("Stage82 current state drift")

    pins = a.get("upstream_authority", {})
    expected = {
        "open_decisions_blob": "215d527c1cb79d7b72697f03f1f84887e3a72d95",
        "stage61_billing_authorization_state_machine_blob": "3225b3c5d03fc45c57a4f043411d03b092e31c13",
        "stage62_stage61_final_reconciliation_blob": "4c9c99ecb2f3f016287e9d5c7de1888e6e2c846f",
        "stage82_registry_blob": "8df44e092680c5dba82d602efa23872124daedd0",
    }
    for key, value in expected.items():
        if pins.get(key) != value:
            fail(f"Stage82 upstream pin drift: {key}")

    remote = a.get("fresh_remote_read_only_receipt", {})
    if [remote.get("auth_users"), remote.get("organizations"), remote.get("students")] != [0, 0, 0]:
        fail("Stage82 remote customer baseline drift")
    if [remote.get("organization_subscriptions"), remote.get("checkout_intents"), remote.get("webhook_receipts")] != [0, 0, 0]:
        fail("Stage82 remote billing baseline drift")
    if remote.get("asaas_state") != "selected_pending_credentials" or remote.get("asaas_activated_at") is not None:
        fail("Stage82 Asaas baseline drift")
    if remote.get("remote_mutation_performed") is not False:
        fail("Stage82 remote mutation boundary drift")

    target = a.get("target_open_decision", {})
    if target.get("id") != "BILLING_CANCELLATION_REFUND_POLICY" or target.get("state") != "OPEN":
        fail("billing cancellation/refund decision must remain OPEN")
    if target.get("affected_gates") != ["legal_terms_of_use"]:
        fail("Stage82 affected gate drift")
    if target.get("resolution_authority") != "business owner plus legal review":
        fail("Stage82 resolution authority drift")
    if target.get("stage82_can_close_decision") is not False:
        fail("Stage82 cannot close billing policy decision")

    separation = a.get("billing_authority_separation", {})
    if separation.get("current_billing_structural_state") != "AWAITING_REAL_OPERATOR_CREDENTIAL_EVIDENCE":
        fail("Stage82 billing structural state drift")
    if separation.get("provider_code") != "asaas" or separation.get("provider_active") is not False:
        fail("Stage82 provider activation state drift")
    for key, value in separation.items():
        if key.startswith("stage82_can_") and value is not False:
            fail(f"Stage82 authority boundary must keep {key}=false")

    contract = a.get("inventory_contract", {})
    if contract.get("expected_surface_count") != 10:
        fail("Stage82 expected surface count drift")
    for key in (
        "technical_source_binding_required", "migration_corpus_digest_required", "registry_digest_required",
        "stage61_and_stage62_binding_required", "technical_statuses_and_lifecycle_markers_may_be_reported",
        "unresolved_business_legal_questions_may_be_reported",
    ):
        if contract.get(key) is not True:
            fail(f"Stage82 contract must keep {key}=true")
    forbidden_true = (
        "database_status_enum_is_customer_policy", "technical_cancel_flag_is_approved_cancellation_rule",
        "billing_period_boundary_is_approved_entitlement_rule", "delinquency_marker_is_approved_grace_period_rule",
        "checkout_status_is_refund_evidence", "webhook_receipt_is_customer_terms",
        "provider_selection_is_provider_refund_capability_evidence", "refund_eligibility_may_be_selected",
        "refund_window_or_duration_may_be_selected", "proration_rule_may_be_selected",
        "cancellation_effective_time_may_be_selected", "delinquency_grace_period_may_be_selected",
        "access_after_cancellation_may_be_selected", "tax_or_provider_fee_refund_treatment_may_be_selected",
        "customer_communication_rule_may_be_approved", "terms_of_use_may_be_modified",
        "target_open_decision_can_be_closed", "inventory_is_business_owner_approval", "inventory_is_legal_review",
        "inventory_is_customer_terms_evidence", "network_calls_allowed", "provider_calls_allowed",
        "supabase_mutation_allowed", "deployment_action_allowed", "evidence_ref_creation_allowed",
        "evidence_digest_promotion_allowed", "evidence_migration_creation_allowed", "gate_promotion_allowed",
        "controlled_launch_promotion_allowed", "paid_media_promotion_allowed",
    )
    for key in forbidden_true:
        if contract.get(key) is not False:
            fail(f"Stage82 contract must keep {key}=false")


def verify_pins_and_registry() -> None:
    expected_blobs = {
        OPEN_DECISIONS: "215d527c1cb79d7b72697f03f1f84887e3a72d95",
        STAGE61: "3225b3c5d03fc45c57a4f043411d03b092e31c13",
        STAGE62: "4c9c99ecb2f3f016287e9d5c7de1888e6e2c846f",
        REGISTRY: "8df44e092680c5dba82d602efa23872124daedd0",
        BUILDER: "a8f1ccbe3e6c5dc99bd6d6cfa29b1400a8605c71",
    }
    for path, expected in expected_blobs.items():
        if git_blob_sha(path) != expected:
            fail(f"Stage82 sealed input drift: {path.relative_to(ROOT)}")

    decisions = load(OPEN_DECISIONS)
    unresolved = decisions.get("unresolved")
    target = next((x for x in unresolved if isinstance(x, dict) and x.get("id") == "BILLING_CANCELLATION_REFUND_POLICY"), None) if isinstance(unresolved, list) else None
    if not isinstance(target, dict) or target.get("state") != "OPEN":
        fail("global billing cancellation/refund policy decision missing or closed")
    if target.get("required") != "Approved customer-facing subscription, cancellation, delinquency and refund policy.":
        fail("global billing policy requirement drift")
    if target.get("resolution_authority") != "business owner plus legal review":
        fail("global billing policy authority drift")

    s61 = load(STAGE61)
    if s61.get("state_machine", {}).get("current_structural_state") != "AWAITING_REAL_OPERATOR_CREDENTIAL_EVIDENCE":
        fail("Stage61 current billing structural state drift")
    s62 = load(STAGE62)
    if s62.get("final_state") != "STAGE61_MERGED_GREEN_REMOTE_UNCHANGED_FIRST_EXTERNAL_BOUNDARY_STILL_OPERATOR_CREDENTIAL_EVIDENCE":
        fail("Stage62 final billing boundary drift")

    registry = load(REGISTRY)
    if registry.get("status") != "TECHNICAL_BILLING_LIFECYCLE_SURFACE_REGISTRY_POLICY_UNRESOLVED_NOT_CUSTOMER_TERMS_NOT_EVIDENCE":
        fail("Stage82 registry status drift")
    if registry.get("resolution_authority") != "business owner plus legal review":
        fail("Stage82 registry resolution authority drift")
    boundaries = registry.get("global_boundaries", {})
    if not boundaries or any(value is not False for value in boundaries.values()):
        fail("Stage82 registry global boundaries must all remain false")
    surfaces = registry.get("technical_surfaces")
    if not isinstance(surfaces, list) or [x.get("surface_id") for x in surfaces if isinstance(x, dict)] != EXPECTED_SURFACE_IDS:
        fail("Stage82 registry surface identity/order drift")
    for item in surfaces:
        if item.get("approved_policy_state") != "UNRESOLVED_BUSINESS_OWNER_PLUS_LEGAL_REVIEW":
            fail(f"Stage82 registry policy unexpectedly resolved: {item.get('surface_id')}")
        if not isinstance(item.get("policy_questions_for_real_review"), list) or len(item["policy_questions_for_real_review"]) < 3:
            fail(f"Stage82 review questions missing: {item.get('surface_id')}")


def verify_builder() -> None:
    try:
        source = BUILDER.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (OSError, SyntaxError) as exc:
        fail(f"Stage82 builder unreadable or invalid Python: {type(exc).__name__}")
    for node in ast.walk(tree):
        roots: list[str] = []
        if isinstance(node, ast.Import):
            roots.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.append(node.module.split(".")[0])
        for root in roots:
            if root in FORBIDDEN_IMPORT_ROOTS:
                fail(f"Stage82 builder imports forbidden remote module: {root}")
    for marker in (
        "TECHNICAL_BILLING_LIFECYCLE_SURFACES_INVENTORIED_POLICY_DECISIONS_UNRESOLVED_NOT_CUSTOMER_TERMS_EVIDENCE",
        "AWAITING_REAL_OPERATOR_CREDENTIAL_EVIDENCE",
        "CUSTOMER_POLICY_APPROVED=false",
        "TARGET_DECISION_CLOSED=false",
        "LEGAL_TERMS_GATE_READY=false",
        "PROVIDER_CALL=false",
        "REMOTE_MUTATION=false",
        "customer_policy_approved\": False",
        "refund_rule_approved\": False",
        "cancellation_rule_approved\": False",
        "delinquency_rule_approved\": False",
        "terms_of_use_modified\": False",
        "target_open_decision_closed\": False",
    ):
        if marker not in source:
            fail(f"Stage82 builder missing boundary marker: {marker}")


def verify_workflow() -> None:
    try:
        text = WORKFLOW.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"Stage82 workflow unreadable: {type(exc).__name__}")
    low = text.lower()
    for token in FORBIDDEN_WORKFLOW_TOKENS:
        if token in low:
            fail(f"Stage82 workflow contains forbidden token: {token}")
    for marker in (
        "permissions:\n  contents: read",
        "Checkout exact head",
        "Verify Stage82 technical billing lifecycle policy inventory contract",
        "Build deterministic Stage82 inventory twice",
        "cmp /tmp/stage82_inventory_a.json /tmp/stage82_inventory_b.json",
        "Upload non-attesting Stage82 billing lifecycle inventory",
        "CUSTOMER_POLICY_APPROVED=false",
        "REFUND_RULE_APPROVED=false",
        "CANCELLATION_RULE_APPROVED=false",
        "TARGET_DECISION_CLOSED=false",
        "LEGAL_TERMS_GATE_READY=false",
        "PROVIDER_CALL=false",
        "GATE_PROMOTION=false",
        "CONTROLLED_LAUNCH=DENIED",
        "REMOTE_MUTATION=false",
    ):
        if marker not in text:
            fail(f"Stage82 workflow missing marker: {marker}")


def verify_no_stage82_migration() -> None:
    found: list[Path] = []
    for root in (BACKEND / "migrations", BACKEND / "supabase" / "migrations"):
        if root.exists():
            found.extend(root.glob("*stage82*"))
    if found:
        fail("Stage82 must not create a Supabase migration")


def main() -> None:
    verify_authority()
    verify_pins_and_registry()
    verify_builder()
    verify_workflow()
    verify_no_stage82_migration()
    print("STAGE82_TECHNICAL_BILLING_LIFECYCLE_POLICY_INVENTORY_GUARD=PASS")
    print("SURFACE_COUNT=10")
    print("CUSTOMER_POLICY_APPROVED=false")
    print("TARGET_DECISION_CLOSED=false")
    print("LEGAL_TERMS_GATE_READY=false")
    print("PROVIDER_CALL=false")
    print("REMOTE_MUTATION=false")


if __name__ == "__main__":
    main()
