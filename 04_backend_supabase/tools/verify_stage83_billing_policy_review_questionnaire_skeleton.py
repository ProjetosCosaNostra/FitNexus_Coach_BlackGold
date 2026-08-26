from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage83_billing_policy_review_questionnaire_skeleton_authority.json"
QUESTIONNAIRE = ROOT / "10_compliance" / "review" / "STAGE83_BILLING_POLICY_REVIEW_QUESTIONNAIRE_SKELETON.md"
BUILDER = BACKEND / "tools" / "build_stage83_billing_policy_review_questionnaire_skeleton.py"
OPEN_DECISIONS = ROOT / "10_compliance" / "drafts" / "COMPLIANCE_OPEN_DECISIONS.json"
STAGE61 = BACKEND / "stage61_billing_authorization_state_machine_authority.json"
STAGE62 = BACKEND / "stage62_stage61_final_reconciliation_authority.json"
STAGE82R2_AUTHORITY = BACKEND / "stage82r2_billing_lifecycle_source_reconciliation_authority.json"
STAGE82R2_REGISTRY = ROOT / "10_compliance" / "inventory" / "STAGE82R2_TECHNICAL_BILLING_LIFECYCLE_POLICY_SURFACE_REGISTRY.json"
STAGE82R2_GUARD = BACKEND / "tools" / "verify_stage82r2_billing_lifecycle_source_reconciliation.py"
WORKFLOW = ROOT / ".github" / "workflows" / "stage83_billing_policy_review_questionnaire_skeleton.yml"
FAILURE_CLASS = "BGF-STAGE83-BILLING-POLICY-QUESTIONNAIRE-SKELETON-GUARD-828"
CANONICAL_REQUIRED = "Approved trial, renewal, cancellation, refund/withdrawal, delinquency and reactivation policy."
CANONICAL_RESOLUTION = "business plus legal review after real billing authority"
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
EXPECTED_SECTION_HEADINGS = [
    "## Section A — Trial policy",
    "## Section B — Renewal policy",
    "## Section C — Customer-initiated cancellation",
    "## Section D — Service-initiated or exceptional cancellation",
    "## Section E — Refund / withdrawal policy",
    "## Section F — Delinquency, retry, suspension and recovery",
    "## Section G — Reactivation",
    "## Section H — Access and entitlement consequences",
    "## Section I — Price, fees, taxes and proration",
    "## Section J — Customer communications and receipts",
    "## Section K — Provider mechanics dependency",
    "## Section L — Data, retention and account lifecycle dependency",
    "## Section M — Terms acceptance and versioning dependency",
]
EXPECTED_QUESTION_COUNTS = [6, 5, 7, 5, 8, 7, 5, 6, 6, 8, 6, 5, 4]
FORBIDDEN_IMPORT_ROOTS = {"os", "subprocess", "socket", "urllib", "http", "requests", "psycopg", "supabase"}
FORBIDDEN_WORKFLOW_TOKENS = (
    "git push", "apply_migration", "execute_sql", "supabase db", "curl ", "wget ",
    "deploy-pages", "actions/deploy-pages", "powershell",
)


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE83_BILLING_POLICY_QUESTIONNAIRE_SKELETON_GUARD=FAIL\n"
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
        AUTHORITY: "ab273d380b85a032b83b45679f420fd49a38f6ac",
        QUESTIONNAIRE: "1644ebd8d55bf16146c74decacb674aa4cc6cf4a",
        BUILDER: "24e302fa7f4e8595a1c1dd8afe32515d29ef83e5",
        OPEN_DECISIONS: "215d527c1cb79d7b72697f03f1f84887e3a72d95",
        STAGE61: "3225b3c5d03fc45c57a4f043411d03b092e31c13",
        STAGE62: "4c9c99ecb2f3f016287e9d5c7de1888e6e2c846f",
        STAGE82R2_AUTHORITY: "71c7073e06901b83e0cb1555d2423eb67273abc9",
        STAGE82R2_REGISTRY: "8e67cbd375c33a0dbe7bea98bbcb7e05fdba5576",
        STAGE82R2_GUARD: "bed314e352cbcb1320867032e035109cc95027a8",
    }
    for path, expected_blob in expected.items():
        if git_blob_sha(path) != expected_blob:
            fail(f"sealed input drift: {path.relative_to(ROOT)}")


def verify_authority() -> None:
    a = load(AUTHORITY)
    if a.get("schema_version") != 1 or a.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("Stage83 authority identity drift")
    if a.get("stage") != "STAGE83_BILLING_POLICY_REVIEW_QUESTIONNAIRE_SKELETON":
        fail("Stage83 authority stage drift")
    if a.get("baseline_main_sha") != "ef2afb0a94b602008f0d91f427f928b538016ccf":
        fail("Stage83 baseline main SHA drift")

    upstream = a.get("upstream_stage82r2_green", {})
    if upstream.get("green_head_sha") != "8aa22571a561186b6841a2ef789a98f28bf8e182":
        fail("Stage82R2 GREEN head drift")
    if upstream.get("merged_main_sha") != "ef2afb0a94b602008f0d91f427f928b538016ccf":
        fail("Stage82R2 merge SHA drift")
    if upstream.get("dedicated_ci_run_id") != 32983553292 or upstream.get("dedicated_ci_conclusion") != "success":
        fail("Stage82R2 dedicated CI provenance drift")
    if upstream.get("flutter_quality_gate_run_id") != 32983553265 or upstream.get("flutter_quality_gate_conclusion") != "success":
        fail("Stage82R2 Flutter GREEN provenance drift")
    if upstream.get("artifact_id") != 9612439348:
        fail("Stage82R2 artifact id drift")
    if upstream.get("artifact_digest") != "sha256:314127a66d364b2e533fdebc8480b27ac9b295a208d568626af5050532ee9616":
        fail("Stage82R2 artifact digest drift")
    if upstream.get("artifact_is_policy_or_gate_evidence") is not False:
        fail("Stage82R2 artifact cannot become policy/gate evidence")

    remote = a.get("fresh_postmerge_remote_read_only_receipt", {})
    if remote.get("observed_at_utc") != "2026-08-26T15:02:30.519632+00:00":
        fail("Stage83 remote receipt timestamp drift")
    if [remote.get("auth_users"), remote.get("organizations"), remote.get("students")] != [0, 0, 0]:
        fail("Stage83 remote customer baseline drift")
    if [remote.get("organization_subscriptions"), remote.get("checkout_intents"), remote.get("webhook_receipts")] != [0, 0, 0]:
        fail("Stage83 remote billing baseline drift")
    if remote.get("asaas_state") != "selected_pending_credentials" or remote.get("asaas_activated_at") is not None:
        fail("Stage83 Asaas state drift")
    if remote.get("remote_mutation_performed") is not False:
        fail("Stage83 remote receipt must remain read-only")

    target = a.get("canonical_target_open_decision", {})
    if target.get("id") != "BILLING_CANCELLATION_REFUND_POLICY" or target.get("state") != "OPEN":
        fail("Stage83 target decision identity/state drift")
    if target.get("affected_gates") != ["legal_terms_of_use"]:
        fail("Stage83 target decision gate drift")
    if target.get("required") != CANONICAL_REQUIRED or target.get("resolution_authority") != CANONICAL_RESOLUTION:
        fail("Stage83 canonical target wording drift")
    if target.get("stage83_can_close_decision") is not False:
        fail("Stage83 cannot close target decision")

    pre = a.get("precondition_state", {})
    if pre.get("current_billing_structural_state") != "AWAITING_REAL_OPERATOR_CREDENTIAL_EVIDENCE":
        fail("Stage83 billing precondition drift")
    if pre.get("provider_code") != "asaas" or pre.get("provider_active") is not False:
        fail("Stage83 provider precondition drift")
    for key in (
        "real_billing_authority_present",
        "real_business_owner_policy_review_collection_allowed",
        "real_legal_policy_review_collection_allowed",
        "questionnaire_answers_allowed",
        "review_signatures_or_approvals_allowed",
    ):
        if pre.get(key) is not False:
            fail(f"Stage83 precondition must keep {key}=false")
    if pre.get("unanswered_questionnaire_structure_allowed") is not True:
        fail("Stage83 unanswered questionnaire preparation boundary drift")

    contract = a.get("questionnaire_contract", {})
    if contract.get("expected_surface_count") != 10 or contract.get("expected_section_count") != 13 or contract.get("expected_total_question_count") != 78:
        fail("Stage83 questionnaire counts drift")
    allowed_true = {
        "canonical_open_decision_exact_match_required",
        "stage82r2_surface_binding_required",
        "real_billing_authority_absence_required_for_stage83_state",
        "all_sections_must_remain_explicitly_unanswered",
        "deterministic_double_build_required",
    }
    for key in allowed_true:
        if contract.get(key) is not True:
            fail(f"Stage83 contract must keep {key}=true")
    for key, value in contract.items():
        if isinstance(value, bool) and key not in allowed_true and value is not False:
            fail(f"Stage83 prohibited contract boundary must keep {key}=false")


def verify_upstream_and_questionnaire() -> None:
    decisions = load(OPEN_DECISIONS)
    unresolved = decisions.get("unresolved")
    target = next(
        (row for row in unresolved if isinstance(row, dict) and row.get("id") == "BILLING_CANCELLATION_REFUND_POLICY"),
        None,
    ) if isinstance(unresolved, list) else None
    if not isinstance(target, dict):
        fail("canonical billing policy decision missing")
    if target.get("state") != "OPEN" or target.get("applies_to") != ["legal_terms_of_use"]:
        fail("canonical billing policy decision state/scope drift")
    if target.get("required") != CANONICAL_REQUIRED or target.get("resolution_authority") != CANONICAL_RESOLUTION:
        fail("canonical billing policy source wording drift")

    s61 = load(STAGE61)
    if s61.get("state_machine", {}).get("current_structural_state") != "AWAITING_REAL_OPERATOR_CREDENTIAL_EVIDENCE":
        fail("Stage61 billing authority precondition drift")
    s62 = load(STAGE62)
    if s62.get("final_state") != "STAGE61_MERGED_GREEN_REMOTE_UNCHANGED_FIRST_EXTERNAL_BOUNDARY_STILL_OPERATOR_CREDENTIAL_EVIDENCE":
        fail("Stage62 billing authority precondition drift")

    r2 = load(STAGE82R2_AUTHORITY)
    billing = r2.get("billing_authority_boundary", {})
    if billing.get("real_billing_authority_present") is not False:
        fail("Stage82R2 now indicates real billing authority; Stage83 skeleton state must be revisited")
    if billing.get("real_business_owner_policy_review_may_be_collected_now") is not False:
        fail("Stage82R2 now allows business review; Stage83 skeleton-only state must be revisited")
    if billing.get("real_legal_policy_review_may_be_collected_now") is not False:
        fail("Stage82R2 now allows legal review; Stage83 skeleton-only state must be revisited")

    registry = load(STAGE82R2_REGISTRY)
    surfaces = registry.get("technical_surfaces")
    if not isinstance(surfaces, list) or [row.get("surface_id") for row in surfaces if isinstance(row, dict)] != EXPECTED_SURFACE_IDS:
        fail("Stage82R2 surface identity/order drift")
    for row in surfaces:
        if row.get("approved_policy_state") != "UNRESOLVED_AFTER_REAL_BILLING_AUTHORITY_BUSINESS_PLUS_LEGAL_REVIEW":
            fail(f"Stage82R2 surface unexpectedly approved: {row.get('surface_id')}")

    try:
        text = QUESTIONNAIRE.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"unable to read Stage83 questionnaire: {type(exc).__name__}")
    required_markers = (
        "STRUCTURE ONLY — DO NOT COMPLETE, SIGN, APPROVE OR TREAT AS REVIEW MATERIAL BEFORE REAL BILLING AUTHORITY EXISTS",
        "REAL BILLING AUTHORITY MUST EXIST BEFORE ANY REAL BUSINESS-OWNER OR LEGAL POLICY REVIEW IS COLLECTED",
        CANONICAL_REQUIRED,
        CANONICAL_RESOLUTION,
        "REAL_BILLING_AUTHORITY_PRESENT=false",
        "REAL_REVIEW_COLLECTION_ALLOWED=false",
        "CUSTOMER_POLICY_APPROVED=false",
        "TERMS_OF_USE_MODIFIED=false",
        "TARGET_DECISION_CLOSED=false",
        "LEGAL_TERMS_GATE_READY=false",
        "PROVIDER_CALL=false",
        "REMOTE_MUTATION=false",
        "CONTROLLED_LAUNCH=DENIED",
        "PAID_MEDIA=DENIED",
    )
    for marker in required_markers:
        if marker not in text:
            fail(f"Stage83 questionnaire boundary marker missing: {marker}")
    for surface_id in EXPECTED_SURFACE_IDS:
        if f"`{surface_id}`" not in text:
            fail(f"Stage83 questionnaire missing upstream surface: {surface_id}")

    for index, (heading, expected_count) in enumerate(zip(EXPECTED_SECTION_HEADINGS, EXPECTED_QUESTION_COUNTS)):
        start = text.find(heading)
        if start < 0:
            fail(f"Stage83 section missing: {heading}")
        end = text.find(EXPECTED_SECTION_HEADINGS[index + 1], start + len(heading)) if index + 1 < len(EXPECTED_SECTION_HEADINGS) else text.find("## Future review completion criteria", start)
        if end < 0:
            fail(f"Stage83 section boundary missing: {heading}")
        body = text[start:end]
        if len(re.findall(r"(?m)^\d+\. ", body)) != expected_count:
            fail(f"Stage83 question count drift: {heading}")
        if "**Stage83 answer:** intentionally blank" not in body:
            fail(f"Stage83 section is not explicitly unanswered: {heading}")


def verify_builder() -> None:
    try:
        source = BUILDER.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (OSError, SyntaxError) as exc:
        fail(f"Stage83 builder unreadable or invalid Python: {type(exc).__name__}")
    for node in ast.walk(tree):
        roots: list[str] = []
        if isinstance(node, ast.Import):
            roots.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.append(node.module.split(".")[0])
        for root in roots:
            if root in FORBIDDEN_IMPORT_ROOTS:
                fail(f"Stage83 builder imports forbidden module: {root}")
    for marker in (
        "NON_ATTESTING_UNANSWERED_BILLING_POLICY_REVIEW_QUESTIONNAIRE_SKELETON",
        "QUESTIONNAIRE_STRUCTURE_PREPARED_REAL_REVIEW_COLLECTION_BLOCKED_UNTIL_REAL_BILLING_AUTHORITY_NOT_POLICY_NOT_TERMS_NOT_EVIDENCE",
        "real_billing_authority_present\": False",
        "real_review_collection_allowed\": False",
        "review_answers_present\": False",
        "customer_policy_approved\": False",
        "terms_of_use_modified\": False",
        "target_open_decision_closed\": False",
        "legal_terms_gate_ready\": False",
        "provider_call\": False",
        "remote_mutation\": False",
    ):
        if marker not in source:
            fail(f"Stage83 builder boundary marker missing: {marker}")


def verify_workflow() -> None:
    try:
        text = WORKFLOW.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"Stage83 workflow unreadable: {type(exc).__name__}")
    low = text.lower()
    for token in FORBIDDEN_WORKFLOW_TOKENS:
        if token in low:
            fail(f"Stage83 workflow contains forbidden token: {token}")
    for marker in (
        "permissions:\n  contents: read",
        "Checkout exact head",
        "Verify Stage83 billing policy questionnaire skeleton contract",
        "Build deterministic Stage83 questionnaire skeleton packet twice",
        "cmp /tmp/stage83_skeleton_a.json /tmp/stage83_skeleton_b.json",
        "Upload non-attesting Stage83 questionnaire skeleton packet",
        "REAL_BILLING_AUTHORITY_PRESENT=false",
        "REAL_REVIEW_COLLECTION_ALLOWED=false",
        "CUSTOMER_POLICY_APPROVED=false",
        "TERMS_OF_USE_MODIFIED=false",
        "TARGET_DECISION_CLOSED=false",
        "LEGAL_TERMS_GATE_READY=false",
        "PROVIDER_CALL=false",
        "GATE_PROMOTION=false",
        "CONTROLLED_LAUNCH=DENIED",
        "PAID_MEDIA=DENIED",
        "REMOTE_MUTATION=false",
    ):
        if marker not in text:
            fail(f"Stage83 workflow marker missing: {marker}")


def verify_no_stage83_collection_or_migration() -> None:
    forbidden_paths = [
        ROOT / "10_compliance" / "review" / "STAGE83_BILLING_POLICY_REVIEW_INPUT_TEMPLATE.json",
        BACKEND / "tools" / "collect_stage83_billing_policy_review_candidate.py",
    ]
    for path in forbidden_paths:
        if path.exists():
            fail(f"Stage83 must not create real-review collection surface before billing authority: {path.relative_to(ROOT)}")
    found: list[Path] = []
    for root in (BACKEND / "migrations", BACKEND / "supabase" / "migrations"):
        if root.exists():
            found.extend(root.glob("*stage83*"))
    if found:
        fail("Stage83 must not create a Supabase migration")


def main() -> None:
    verify_pins()
    verify_authority()
    verify_upstream_and_questionnaire()
    verify_builder()
    verify_workflow()
    verify_no_stage83_collection_or_migration()
    print("STAGE83_BILLING_POLICY_QUESTIONNAIRE_SKELETON_GUARD=PASS")
    print("SURFACE_COUNT=10")
    print("SECTION_COUNT=13")
    print("TOTAL_QUESTION_COUNT=78")
    print("REAL_BILLING_AUTHORITY_PRESENT=false")
    print("REAL_REVIEW_COLLECTION_ALLOWED=false")
    print("CUSTOMER_POLICY_APPROVED=false")
    print("TARGET_DECISION_CLOSED=false")
    print("LEGAL_TERMS_GATE_READY=false")
    print("PROVIDER_CALL=false")
    print("REMOTE_MUTATION=false")


if __name__ == "__main__":
    main()
