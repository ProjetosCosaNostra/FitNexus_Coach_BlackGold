from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage82r1_billing_policy_source_wording_reconciliation_authority.json"
STAGE82_AUTHORITY = BACKEND / "stage82_technical_billing_lifecycle_policy_inventory_authority.json"
STAGE82_REGISTRY = ROOT / "10_compliance" / "inventory" / "STAGE82_TECHNICAL_BILLING_LIFECYCLE_POLICY_SURFACE_REGISTRY.json"
STAGE82_BUILDER = BACKEND / "tools" / "build_stage82_technical_billing_lifecycle_policy_inventory.py"
STAGE82_GUARD = BACKEND / "tools" / "verify_stage82_technical_billing_lifecycle_policy_inventory.py"
BUILDER = BACKEND / "tools" / "build_stage82r1_reconciled_billing_lifecycle_inventory.py"
OPEN_DECISIONS = ROOT / "10_compliance" / "drafts" / "COMPLIANCE_OPEN_DECISIONS.json"
STAGE61 = BACKEND / "stage61_billing_authorization_state_machine_authority.json"
STAGE62 = BACKEND / "stage62_stage61_final_reconciliation_authority.json"
WORKFLOW = ROOT / ".github" / "workflows" / "stage82_technical_billing_lifecycle_policy_inventory.yml"
FAILURE_CLASS = "BGF-STAGE82R1-BILLING-POLICY-SOURCE-WORDING-RECONCILIATION-GUARD-810"
CANONICAL_REQUIRED = "Approved trial, renewal, cancellation, refund/withdrawal, delinquency and reactivation policy."
CANONICAL_RESOLUTION_AUTHORITY = "business plus legal review after real billing authority"
HISTORICAL_REQUIRED = "Approved customer-facing subscription, cancellation, delinquency and refund policy."
HISTORICAL_RESOLUTION_AUTHORITY = "business owner plus legal review"
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
        "STAGE82R1_BILLING_POLICY_SOURCE_WORDING_RECONCILIATION_GUARD=FAIL\n"
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
        AUTHORITY: "151ac54887f05ca8dcedabbadb454fed073f37f7",
        OPEN_DECISIONS: "215d527c1cb79d7b72697f03f1f84887e3a72d95",
        STAGE61: "3225b3c5d03fc45c57a4f043411d03b092e31c13",
        STAGE62: "4c9c99ecb2f3f016287e9d5c7de1888e6e2c846f",
        STAGE82_AUTHORITY: "d87c603f3c476981803cdcca455d924d0b77235f",
        STAGE82_REGISTRY: "8df44e092680c5dba82d602efa23872124daedd0",
        STAGE82_BUILDER: "a8f1ccbe3e6c5dc99bd6d6cfa29b1400a8605c71",
        STAGE82_GUARD: "45867fd02122ee8620ce21628aeeb76604b20ceb",
        BUILDER: "db70b9678de3fddc6f825f066ad18b78e846ea1a",
    }
    for path, expected_blob in expected.items():
        if git_blob_sha(path) != expected_blob:
            fail(f"sealed input drift: {path.relative_to(ROOT)}")


def verify_authority() -> None:
    a = load(AUTHORITY)
    if a.get("schema_version") != 1 or a.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("Stage82R1 authority identity drift")
    if a.get("stage") != "STAGE82R1_BILLING_POLICY_SOURCE_WORDING_RECONCILIATION":
        fail("Stage82R1 stage drift")
    if a.get("baseline_main_sha") != "d88060f9e3787a9e34937385b1f69370ba5379fb":
        fail("Stage82R1 baseline main SHA drift")

    failed = a.get("failed_head_evidence", {})
    if failed.get("head_sha") != "369b56d8c541a6981cb6e236b5690396cb1382e9":
        fail("failed head SHA drift")
    if failed.get("workflow_run_id") != 32982246549 or failed.get("conclusion") != "failure":
        fail("failed CI provenance drift")
    if failed.get("detail") != "global billing policy requirement drift":
        fail("failed CI detail drift")
    if failed.get("rerun_failed_head") is not False or failed.get("failed_head_preserved") is not True:
        fail("failed-head preservation boundary drift")

    rec = a.get("wording_reconciliation", {})
    if rec.get("decision_id") != "BILLING_CANCELLATION_REFUND_POLICY" or rec.get("state") != "OPEN":
        fail("reconciled decision identity/state drift")
    if rec.get("affected_gates") != ["legal_terms_of_use"]:
        fail("reconciled affected-gate drift")
    if rec.get("historical_stage82_required") != HISTORICAL_REQUIRED:
        fail("historical requirement marker drift")
    if rec.get("canonical_required") != CANONICAL_REQUIRED:
        fail("canonical requirement marker drift")
    if rec.get("historical_stage82_resolution_authority") != HISTORICAL_RESOLUTION_AUTHORITY:
        fail("historical resolution marker drift")
    if rec.get("canonical_resolution_authority") != CANONICAL_RESOLUTION_AUTHORITY:
        fail("canonical resolution authority marker drift")
    if rec.get("reconciliation_kind") != "SOURCE_WORDING_CORRECTION_ONLY":
        fail("reconciliation kind drift")
    for key in ("historical_stage82_files_mutated", "business_or_legal_conclusion_changed", "policy_selected", "decision_closed"):
        if rec.get(key) is not False:
            fail(f"reconciliation boundary must keep {key}=false")

    billing = a.get("billing_authority_boundary", {})
    if billing.get("current_structural_state") != "AWAITING_REAL_OPERATOR_CREDENTIAL_EVIDENCE":
        fail("billing structural state drift")
    if billing.get("provider_code") != "asaas" or billing.get("provider_active") is not False:
        fail("provider activation boundary drift")
    if billing.get("real_billing_authority_present") is not False:
        fail("real billing authority must not be inferred")
    if billing.get("real_business_owner_policy_review_may_be_collected_now") is not False:
        fail("business-owner review cannot be collected before real billing authority")
    if billing.get("real_legal_policy_review_may_be_collected_now") is not False:
        fail("legal review cannot be collected before real billing authority")
    if billing.get("questionnaire_structure_may_be_prepared_without_answers") is not True:
        fail("safe questionnaire-structure boundary drift")
    for key in ("provider_call_allowed", "checkout_allowed", "refund_allowed", "cancellation_allowed", "subscription_mutation_allowed"):
        if billing.get(key) is not False:
            fail(f"billing execution boundary must keep {key}=false")

    contract = a.get("reconciliation_contract", {})
    for key in (
        "canonical_open_decision_exact_match_required",
        "historical_failed_head_must_remain_unmodified",
        "migration_source_markers_must_still_validate",
        "deterministic_double_build_required",
    ):
        if contract.get(key) is not True:
            fail(f"Stage82R1 contract must keep {key}=true")
    for key, value in contract.items():
        if isinstance(value, bool) and key not in {
            "canonical_open_decision_exact_match_required",
            "historical_failed_head_must_remain_unmodified",
            "migration_source_markers_must_still_validate",
            "deterministic_double_build_required",
        } and value is not False:
            fail(f"Stage82R1 prohibited boundary must keep {key}=false")


def verify_canonical_and_historical_sources() -> None:
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
    if target.get("required") != CANONICAL_REQUIRED:
        fail("canonical billing requirement drift")
    if target.get("resolution_authority") != CANONICAL_RESOLUTION_AUTHORITY:
        fail("canonical billing resolution authority drift")

    historical = load(STAGE82_AUTHORITY)
    htarget = historical.get("target_open_decision", {})
    if htarget.get("required") != HISTORICAL_REQUIRED:
        fail("historical Stage82 requirement no longer matches failed head")
    if htarget.get("resolution_authority") != HISTORICAL_RESOLUTION_AUTHORITY:
        fail("historical Stage82 resolution no longer matches failed head")
    if htarget.get("state") != "OPEN" or htarget.get("stage82_can_close_decision") is not False:
        fail("historical Stage82 decision boundary drift")

    registry = load(STAGE82_REGISTRY)
    surfaces = registry.get("technical_surfaces")
    if not isinstance(surfaces, list) or len(surfaces) != 10:
        fail("Stage82 registry surface count drift")
    if [x.get("surface_id") for x in surfaces if isinstance(x, dict)] != EXPECTED_SURFACE_IDS:
        fail("Stage82 registry surface identity/order drift")
    boundaries = registry.get("global_boundaries")
    if not isinstance(boundaries, dict) or not boundaries or any(value is not False for value in boundaries.values()):
        fail("Stage82 registry technical/policy boundaries drift")

    s61 = load(STAGE61)
    if s61.get("state_machine", {}).get("current_structural_state") != "AWAITING_REAL_OPERATOR_CREDENTIAL_EVIDENCE":
        fail("Stage61 structural billing state drift")
    s62 = load(STAGE62)
    if s62.get("final_state") != "STAGE61_MERGED_GREEN_REMOTE_UNCHANGED_FIRST_EXTERNAL_BOUNDARY_STILL_OPERATOR_CREDENTIAL_EVIDENCE":
        fail("Stage62 billing reconciliation drift")


def verify_builder() -> None:
    try:
        source = BUILDER.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (OSError, SyntaxError) as exc:
        fail(f"Stage82R1 builder unreadable or invalid Python: {type(exc).__name__}")
    for node in ast.walk(tree):
        roots: list[str] = []
        if isinstance(node, ast.Import):
            roots.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.append(node.module.split(".")[0])
        for root in roots:
            if root in FORBIDDEN_IMPORT_ROOTS:
                fail(f"Stage82R1 builder imports forbidden module: {root}")
    for marker in (
        CANONICAL_REQUIRED,
        CANONICAL_RESOLUTION_AUTHORITY,
        HISTORICAL_REQUIRED,
        HISTORICAL_RESOLUTION_AUTHORITY,
        "failed_head_sha\": \"369b56d8c541a6981cb6e236b5690396cb1382e9\"",
        "failed_ci_run_id\": 32982246549",
        "real_billing_authority_present\": False",
        "customer_policy_approved\": False",
        "target_open_decision_closed\": False",
        "legal_terms_gate_ready\": False",
        "provider_call\": False",
        "remote_mutation\": False",
    ):
        if marker not in source:
            fail(f"Stage82R1 builder missing boundary marker: {marker}")


def verify_workflow() -> None:
    try:
        text = WORKFLOW.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"Stage82 workflow unreadable: {type(exc).__name__}")
    low = text.lower()
    for token in FORBIDDEN_WORKFLOW_TOKENS:
        if token in low:
            fail(f"Stage82R1 workflow contains forbidden token: {token}")
    for marker in (
        "permissions:\n  contents: read",
        "Checkout exact head",
        "Verify Stage82R1 billing policy source wording reconciliation",
        "Build deterministic Stage82R1 reconciled inventory twice",
        "cmp /tmp/stage82r1_inventory_a.json /tmp/stage82r1_inventory_b.json",
        "Upload non-attesting Stage82R1 reconciled billing lifecycle inventory",
        "FAILED_STAGE82_HEAD_PRESERVED=true",
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
            fail(f"Stage82R1 workflow missing marker: {marker}")


def verify_no_migration() -> None:
    found: list[Path] = []
    for root in (BACKEND / "migrations", BACKEND / "supabase" / "migrations"):
        if root.exists():
            found.extend(root.glob("*stage82r1*"))
    if found:
        fail("Stage82R1 must not create a Supabase migration")


def main() -> None:
    verify_pins()
    verify_authority()
    verify_canonical_and_historical_sources()
    verify_builder()
    verify_workflow()
    verify_no_migration()
    print("STAGE82R1_BILLING_POLICY_SOURCE_WORDING_RECONCILIATION_GUARD=PASS")
    print("FAILED_STAGE82_HEAD_PRESERVED=true")
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
