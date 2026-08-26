from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage82r2_billing_lifecycle_source_reconciliation_authority.json"
REGISTRY = ROOT / "10_compliance" / "inventory" / "STAGE82R2_TECHNICAL_BILLING_LIFECYCLE_POLICY_SURFACE_REGISTRY.json"
BUILDER = BACKEND / "tools" / "build_stage82r2_source_reconciled_billing_lifecycle_inventory.py"
OPEN_DECISIONS = ROOT / "10_compliance" / "drafts" / "COMPLIANCE_OPEN_DECISIONS.json"
STAGE61 = BACKEND / "stage61_billing_authorization_state_machine_authority.json"
STAGE62 = BACKEND / "stage62_stage61_final_reconciliation_authority.json"
STAGE82_AUTHORITY = BACKEND / "stage82_technical_billing_lifecycle_policy_inventory_authority.json"
STAGE82_REGISTRY = ROOT / "10_compliance" / "inventory" / "STAGE82_TECHNICAL_BILLING_LIFECYCLE_POLICY_SURFACE_REGISTRY.json"
STAGE82R1_AUTHORITY = BACKEND / "stage82r1_billing_policy_source_wording_reconciliation_authority.json"
STAGE82R1_BUILDER = BACKEND / "tools" / "build_stage82r1_reconciled_billing_lifecycle_inventory.py"
STAGE82R1_GUARD = BACKEND / "tools" / "verify_stage82r1_billing_policy_source_wording_reconciliation.py"
WORKFLOW = ROOT / ".github" / "workflows" / "stage82_technical_billing_lifecycle_policy_inventory.yml"
FAILURE_CLASS = "BGF-STAGE82R2-BILLING-LIFECYCLE-SOURCE-RECONCILIATION-GUARD-819"
CANONICAL_REQUIRED = "Approved trial, renewal, cancellation, refund/withdrawal, delinquency and reactivation policy."
CANONICAL_RESOLUTION_AUTHORITY = "business plus legal review after real billing authority"
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
FORBIDDEN_MARKERS = {
    "canceled_at", "delinquent_since", "previous_state", "new_state", "external_charge_ref",
    "processing_error", "matched_organization_id", "matched_subscription_id", "effective_to",
    "percentage_bps", "fixed_fee_minor", "tax_bps", "source_ref", "lifecycle_state", "deactivated_at",
}
FORBIDDEN_IMPORT_ROOTS = {"os", "subprocess", "socket", "urllib", "http", "requests", "psycopg", "supabase"}
FORBIDDEN_WORKFLOW_TOKENS = (
    "git push", "apply_migration", "execute_sql", "supabase db", "curl ", "wget ",
    "deploy-pages", "actions/deploy-pages", "powershell",
)


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE82R2_BILLING_LIFECYCLE_SOURCE_RECONCILIATION_GUARD=FAIL\n"
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


def verify_pins() -> None:
    expected = {
        AUTHORITY: "71c7073e06901b83e0cb1555d2423eb67273abc9",
        REGISTRY: "8e67cbd375c33a0dbe7bea98bbcb7e05fdba5576",
        BUILDER: "03aa20c17b15fff8ed56efbc70815e56ab19285f",
        OPEN_DECISIONS: "215d527c1cb79d7b72697f03f1f84887e3a72d95",
        STAGE61: "3225b3c5d03fc45c57a4f043411d03b092e31c13",
        STAGE62: "4c9c99ecb2f3f016287e9d5c7de1888e6e2c846f",
        STAGE82_AUTHORITY: "d87c603f3c476981803cdcca455d924d0b77235f",
        STAGE82_REGISTRY: "8df44e092680c5dba82d602efa23872124daedd0",
        STAGE82R1_AUTHORITY: "151ac54887f05ca8dcedabbadb454fed073f37f7",
        STAGE82R1_BUILDER: "db70b9678de3fddc6f825f066ad18b78e846ea1a",
        STAGE82R1_GUARD: "51b3813558a5663b3a68654547a22e25b4fe1f67",
    }
    for path, expected_blob in expected.items():
        if git_blob_sha(path) != expected_blob:
            fail(f"sealed input drift: {path.relative_to(ROOT)}")


def verify_authority() -> None:
    a = load(AUTHORITY)
    if a.get("schema_version") != 1 or a.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("Stage82R2 authority identity drift")
    if a.get("stage") != "STAGE82R2_BILLING_LIFECYCLE_SOURCE_RECONCILIATION":
        fail("Stage82R2 stage drift")
    if a.get("baseline_main_sha") != "d88060f9e3787a9e34937385b1f69370ba5379fb":
        fail("Stage82R2 baseline main SHA drift")

    chain = a.get("failed_head_chain")
    if not isinstance(chain, list) or len(chain) != 2:
        fail("Stage82R2 must preserve exactly two failed heads")
    expected = [
        ("369b56d8c541a6981cb6e236b5690396cb1382e9", 32982246549, "global billing policy requirement drift"),
        ("7762a4e833cc5df860c2c94a73ccc0e14ed86ed8", 32982854740, "migration corpus missing field marker: cancel_at_period_end_intent:canceled_at"),
    ]
    for row, (sha, run_id, detail) in zip(chain, expected):
        if row.get("head_sha") != sha or row.get("workflow_run_id") != run_id or row.get("detail") != detail:
            fail("failed-head provenance drift")
        if row.get("conclusion") != "failure" or row.get("preserved") is not True or row.get("rerun") is not False:
            fail("failed-head preservation contract drift")

    remote = a.get("fresh_remote_schema_read_only_receipt", {})
    expected_remote = {
        "has_cancel_at_period_end": True,
        "has_canceled_at": False,
        "has_delinquent_since": False,
        "has_from_status": True,
        "has_previous_state": False,
        "has_provider_checkout_ref": True,
        "has_external_charge_ref": False,
        "has_webhook_organization_id": True,
        "has_matched_organization_id": False,
        "has_effective_until": True,
        "has_effective_to": False,
        "has_variable_bps": True,
        "has_percentage_bps": False,
        "has_provider_lifecycle": True,
        "has_provider_lifecycle_state": False,
        "remote_mutation_performed": False,
    }
    if remote.get("observed_at_utc") != "2026-08-26T14:53:30.123086+00:00":
        fail("remote schema receipt timestamp drift")
    for key, value in expected_remote.items():
        if remote.get(key) is not value:
            fail(f"remote schema receipt drift: {key}")

    target = a.get("canonical_target_open_decision", {})
    if target.get("id") != "BILLING_CANCELLATION_REFUND_POLICY" or target.get("state") != "OPEN":
        fail("canonical target decision identity/state drift")
    if target.get("affected_gates") != ["legal_terms_of_use"]:
        fail("canonical target affected-gate drift")
    if target.get("required") != CANONICAL_REQUIRED or target.get("resolution_authority") != CANONICAL_RESOLUTION_AUTHORITY:
        fail("canonical target wording drift")
    if target.get("stage82r2_can_close_decision") is not False:
        fail("Stage82R2 cannot close target decision")

    contract = a.get("source_reconciliation_contract", {})
    for key in (
        "migration_marker_validation_required",
        "canonical_open_decision_exact_match_required",
        "both_failed_heads_must_remain_preserved",
        "historical_stage82_and_r1_files_must_remain_unmodified",
        "deterministic_double_build_required",
    ):
        if contract.get(key) is not True:
            fail(f"Stage82R2 contract must keep {key}=true")
    for key, value in contract.items():
        if isinstance(value, bool) and key not in {
            "migration_marker_validation_required",
            "canonical_open_decision_exact_match_required",
            "both_failed_heads_must_remain_preserved",
            "historical_stage82_and_r1_files_must_remain_unmodified",
            "deterministic_double_build_required",
        } and value is not False:
            fail(f"Stage82R2 prohibited boundary must keep {key}=false")

    billing = a.get("billing_authority_boundary", {})
    if billing.get("current_structural_state") != "AWAITING_REAL_OPERATOR_CREDENTIAL_EVIDENCE":
        fail("Stage82R2 billing structural state drift")
    if billing.get("provider_code") != "asaas" or billing.get("provider_active") is not False:
        fail("Stage82R2 provider state drift")
    if billing.get("real_billing_authority_present") is not False:
        fail("real billing authority must remain absent")
    if billing.get("real_business_owner_policy_review_may_be_collected_now") is not False:
        fail("business-owner policy review collection is premature")
    if billing.get("real_legal_policy_review_may_be_collected_now") is not False:
        fail("legal policy review collection is premature")
    if billing.get("unanswered_questionnaire_structure_may_be_prepared") is not True:
        fail("safe unanswered-questionnaire boundary drift")


def verify_registry_and_canonical_decision() -> None:
    decisions = load(OPEN_DECISIONS)
    unresolved = decisions.get("unresolved")
    target = next(
        (x for x in unresolved if isinstance(x, dict) and x.get("id") == "BILLING_CANCELLATION_REFUND_POLICY"),
        None,
    ) if isinstance(unresolved, list) else None
    if not isinstance(target, dict):
        fail("canonical billing decision missing")
    if target.get("state") != "OPEN" or target.get("applies_to") != ["legal_terms_of_use"]:
        fail("canonical billing decision state/scope drift")
    if target.get("required") != CANONICAL_REQUIRED or target.get("resolution_authority") != CANONICAL_RESOLUTION_AUTHORITY:
        fail("canonical billing decision wording drift")

    registry = load(REGISTRY)
    if registry.get("status") != "TECHNICAL_BILLING_LIFECYCLE_SURFACE_REGISTRY_R2_SOURCE_RECONCILED_POLICY_UNRESOLVED_NOT_CUSTOMER_TERMS_NOT_EVIDENCE":
        fail("Stage82R2 registry status drift")
    if registry.get("resolution_authority") != CANONICAL_RESOLUTION_AUTHORITY:
        fail("Stage82R2 registry resolution authority drift")
    rec = registry.get("source_reconciliation", {})
    removed = rec.get("historical_false_or_unproven_markers_removed")
    if not isinstance(removed, list) or not FORBIDDEN_MARKERS.issubset(set(removed)):
        fail("Stage82R2 removed-marker set incomplete")
    boundaries = registry.get("global_boundaries")
    if not isinstance(boundaries, dict) or not boundaries or any(value is not False for value in boundaries.values()):
        fail("Stage82R2 global boundaries drift")
    surfaces = registry.get("technical_surfaces")
    if not isinstance(surfaces, list) or len(surfaces) != 10:
        fail("Stage82R2 surface count drift")
    if [x.get("surface_id") for x in surfaces if isinstance(x, dict)] != EXPECTED_SURFACE_IDS:
        fail("Stage82R2 surface identity/order drift")
    for item in surfaces:
        fields = item.get("field_markers")
        if not isinstance(fields, list) or not fields:
            fail(f"Stage82R2 field markers missing: {item.get('surface_id')}")
        leaked = FORBIDDEN_MARKERS.intersection(fields)
        if leaked:
            fail(f"historical false marker leaked into R2 registry: {item.get('surface_id')}:{sorted(leaked)}")
        if item.get("approved_policy_state") != "UNRESOLVED_AFTER_REAL_BILLING_AUTHORITY_BUSINESS_PLUS_LEGAL_REVIEW":
            fail(f"Stage82R2 surface policy unexpectedly resolved: {item.get('surface_id')}")

    s61 = load(STAGE61)
    if s61.get("state_machine", {}).get("current_structural_state") != "AWAITING_REAL_OPERATOR_CREDENTIAL_EVIDENCE":
        fail("Stage61 billing state drift")
    s62 = load(STAGE62)
    if s62.get("final_state") != "STAGE61_MERGED_GREEN_REMOTE_UNCHANGED_FIRST_EXTERNAL_BOUNDARY_STILL_OPERATOR_CREDENTIAL_EVIDENCE":
        fail("Stage62 billing boundary drift")


def verify_builder() -> None:
    try:
        source = BUILDER.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (OSError, SyntaxError) as exc:
        fail(f"Stage82R2 builder unreadable or invalid Python: {type(exc).__name__}")
    for node in ast.walk(tree):
        roots: list[str] = []
        if isinstance(node, ast.Import):
            roots.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.append(node.module.split(".")[0])
        for root in roots:
            if root in FORBIDDEN_IMPORT_ROOTS:
                fail(f"Stage82R2 builder imports forbidden module: {root}")
    for marker in (
        CANONICAL_REQUIRED,
        CANONICAL_RESOLUTION_AUTHORITY,
        "369b56d8c541a6981cb6e236b5690396cb1382e9",
        "7762a4e833cc5df860c2c94a73ccc0e14ed86ed8",
        "migration corpus missing field marker: cancel_at_period_end_intent:canceled_at",
        "UNRESOLVED_AFTER_REAL_BILLING_AUTHORITY_BUSINESS_PLUS_LEGAL_REVIEW",
        "real_billing_authority_present\": False",
        "customer_policy_approved\": False",
        "target_open_decision_closed\": False",
        "legal_terms_gate_ready\": False",
        "provider_call\": False",
        "remote_mutation\": False",
    ):
        if marker not in source:
            fail(f"Stage82R2 builder missing marker: {marker}")


def verify_workflow() -> None:
    try:
        text = WORKFLOW.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"Stage82 workflow unreadable: {type(exc).__name__}")
    low = text.lower()
    for token in FORBIDDEN_WORKFLOW_TOKENS:
        if token in low:
            fail(f"Stage82R2 workflow contains forbidden token: {token}")
    for marker in (
        "permissions:\n  contents: read",
        "Checkout exact head",
        "Verify Stage82R2 billing lifecycle source reconciliation",
        "Build deterministic Stage82R2 source-reconciled inventory twice",
        "cmp /tmp/stage82r2_inventory_a.json /tmp/stage82r2_inventory_b.json",
        "Upload non-attesting Stage82R2 source-reconciled billing lifecycle inventory",
        "FAILED_STAGE82_HEAD_COUNT=2",
        "CANONICAL_DECISION_STATE=OPEN",
        "REAL_BILLING_AUTHORITY_PRESENT=false",
        "CUSTOMER_POLICY_APPROVED=false",
        "TARGET_DECISION_CLOSED=false",
        "LEGAL_TERMS_GATE_READY=false",
        "PROVIDER_CALL=false",
        "GATE_PROMOTION=false",
        "CONTROLLED_LAUNCH=DENIED",
        "REMOTE_MUTATION=false",
    ):
        if marker not in text:
            fail(f"Stage82R2 workflow missing marker: {marker}")


def verify_no_migration() -> None:
    found: list[Path] = []
    for root in (BACKEND / "migrations", BACKEND / "supabase" / "migrations"):
        if root.exists():
            found.extend(root.glob("*stage82r2*"))
    if found:
        fail("Stage82R2 must not create a Supabase migration")


def main() -> None:
    verify_pins()
    verify_authority()
    verify_registry_and_canonical_decision()
    verify_builder()
    verify_workflow()
    verify_no_migration()
    print("STAGE82R2_BILLING_LIFECYCLE_SOURCE_RECONCILIATION_GUARD=PASS")
    print("FAILED_STAGE82_HEAD_COUNT=2")
    print("SURFACE_COUNT=10")
    print("CANONICAL_DECISION_STATE=OPEN")
    print("REAL_BILLING_AUTHORITY_PRESENT=false")
    print("CUSTOMER_POLICY_APPROVED=false")
    print("TARGET_DECISION_CLOSED=false")
    print("LEGAL_TERMS_GATE_READY=false")
    print("PROVIDER_CALL=false")
    print("REMOTE_MUTATION=false")


if __name__ == "__main__":
    main()
