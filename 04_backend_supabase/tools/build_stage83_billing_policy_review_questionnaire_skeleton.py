from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage83_billing_policy_review_questionnaire_skeleton_authority.json"
QUESTIONNAIRE = ROOT / "10_compliance" / "review" / "STAGE83_BILLING_POLICY_REVIEW_QUESTIONNAIRE_SKELETON.md"
OPEN_DECISIONS = ROOT / "10_compliance" / "drafts" / "COMPLIANCE_OPEN_DECISIONS.json"
STAGE61 = BACKEND / "stage61_billing_authorization_state_machine_authority.json"
STAGE62 = BACKEND / "stage62_stage61_final_reconciliation_authority.json"
STAGE82R2_AUTHORITY = BACKEND / "stage82r2_billing_lifecycle_source_reconciliation_authority.json"
STAGE82R2_REGISTRY = ROOT / "10_compliance" / "inventory" / "STAGE82R2_TECHNICAL_BILLING_LIFECYCLE_POLICY_SURFACE_REGISTRY.json"
FAILURE_CLASS = "BGF-STAGE83-BILLING-POLICY-QUESTIONNAIRE-SKELETON-GUARD-828"
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
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
EXPECTED_SECTION_IDS = [
    "trial_policy",
    "renewal_policy",
    "customer_initiated_cancellation",
    "service_initiated_or_exceptional_cancellation",
    "refund_withdrawal_policy",
    "delinquency_retry_suspension_and_recovery",
    "reactivation",
    "access_and_entitlement_consequences",
    "price_fees_taxes_and_proration",
    "customer_communications_and_receipts",
    "provider_mechanics_dependency",
    "data_retention_and_account_lifecycle_dependency",
    "terms_acceptance_and_versioning_dependency",
]
SECTION_HEADINGS = [
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
QUESTION_COUNTS = [6, 5, 7, 5, 8, 7, 5, 6, 6, 8, 6, 5, 4]


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE83_BILLING_POLICY_QUESTIONNAIRE_SKELETON=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\nDETAIL={detail}"
    )


def load(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to load {label}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"{label} must be a JSON object")
    return value


def git_blob_sha(path: Path) -> str:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        fail(f"unable to read {path.relative_to(ROOT)}: {type(exc).__name__}")
    return hashlib.sha1(f"blob {len(raw)}\0".encode("utf-8") + raw).hexdigest()


def sha256_file(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        fail(f"unable to hash {path.relative_to(ROOT)}: {type(exc).__name__}")


def canonical_decision() -> dict:
    decisions = load(OPEN_DECISIONS, "open decisions")
    unresolved = decisions.get("unresolved")
    target = next(
        (row for row in unresolved if isinstance(row, dict) and row.get("id") == "BILLING_CANCELLATION_REFUND_POLICY"),
        None,
    ) if isinstance(unresolved, list) else None
    if not isinstance(target, dict):
        fail("BILLING_CANCELLATION_REFUND_POLICY missing")
    if target.get("state") != "OPEN" or target.get("applies_to") != ["legal_terms_of_use"]:
        fail("canonical billing policy decision state/scope drift")
    if target.get("required") != CANONICAL_REQUIRED:
        fail("canonical billing policy requirement drift")
    if target.get("resolution_authority") != CANONICAL_RESOLUTION:
        fail("canonical billing policy resolution authority drift")
    return target


def validate_upstream() -> None:
    s61 = load(STAGE61, "Stage61 authority")
    if s61.get("state_machine", {}).get("current_structural_state") != "AWAITING_REAL_OPERATOR_CREDENTIAL_EVIDENCE":
        fail("Stage61 structural state no longer blocks real billing policy review")
    s62 = load(STAGE62, "Stage62 reconciliation")
    if s62.get("final_state") != "STAGE61_MERGED_GREEN_REMOTE_UNCHANGED_FIRST_EXTERNAL_BOUNDARY_STILL_OPERATOR_CREDENTIAL_EVIDENCE":
        fail("Stage62 billing boundary drift")

    r2 = load(STAGE82R2_AUTHORITY, "Stage82R2 authority")
    if r2.get("stage") != "STAGE82R2_BILLING_LIFECYCLE_SOURCE_RECONCILIATION":
        fail("Stage82R2 authority stage drift")
    billing = r2.get("billing_authority_boundary", {})
    if billing.get("real_billing_authority_present") is not False:
        fail("Stage83 cannot remain a skeleton if real billing authority is present")
    if billing.get("real_business_owner_policy_review_may_be_collected_now") is not False:
        fail("Stage83 real business review collection unexpectedly allowed")
    if billing.get("real_legal_policy_review_may_be_collected_now") is not False:
        fail("Stage83 real legal review collection unexpectedly allowed")
    if billing.get("unanswered_questionnaire_structure_may_be_prepared") is not True:
        fail("Stage82R2 does not authorize unanswered questionnaire preparation")

    registry = load(STAGE82R2_REGISTRY, "Stage82R2 registry")
    if registry.get("resolution_authority") != CANONICAL_RESOLUTION:
        fail("Stage82R2 registry resolution authority drift")
    surfaces = registry.get("technical_surfaces")
    if not isinstance(surfaces, list) or [row.get("surface_id") for row in surfaces if isinstance(row, dict)] != EXPECTED_SURFACE_IDS:
        fail("Stage82R2 registry surface identity/order drift")
    for row in surfaces:
        if row.get("approved_policy_state") != "UNRESOLVED_AFTER_REAL_BILLING_AUTHORITY_BUSINESS_PLUS_LEGAL_REVIEW":
            fail(f"Stage82R2 surface unexpectedly resolved: {row.get('surface_id')}")


def validate_questionnaire() -> list[dict]:
    try:
        text = QUESTIONNAIRE.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"unable to read questionnaire: {type(exc).__name__}")

    mandatory_markers = (
        "STRUCTURE ONLY — DO NOT COMPLETE, SIGN, APPROVE OR TREAT AS REVIEW MATERIAL BEFORE REAL BILLING AUTHORITY EXISTS",
        "REAL BILLING AUTHORITY MUST EXIST BEFORE ANY REAL BUSINESS-OWNER OR LEGAL POLICY REVIEW IS COLLECTED",
        "Approved trial, renewal, cancellation, refund/withdrawal, delinquency and reactivation policy.",
        "business plus legal review after real billing authority",
        "Stage83 answer: intentionally blank",
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
    for marker in mandatory_markers:
        if marker not in text:
            fail(f"questionnaire missing mandatory boundary marker: {marker}")

    for surface_id in EXPECTED_SURFACE_IDS:
        if f"`{surface_id}`" not in text:
            fail(f"questionnaire missing Stage82R2 surface: {surface_id}")

    sections: list[dict] = []
    for index, (section_id, heading, expected_questions) in enumerate(zip(EXPECTED_SECTION_IDS, SECTION_HEADINGS, QUESTION_COUNTS)):
        start = text.find(heading)
        if start < 0:
            fail(f"questionnaire missing section heading: {heading}")
        end = text.find(SECTION_HEADINGS[index + 1], start + len(heading)) if index + 1 < len(SECTION_HEADINGS) else text.find("## Future review completion criteria", start)
        if end < 0:
            fail(f"unable to determine questionnaire section boundary: {heading}")
        body = text[start:end]
        actual_questions = len(re.findall(r"(?m)^\d+\. ", body))
        if actual_questions != expected_questions:
            fail(f"question count drift for {section_id}: expected {expected_questions}, got {actual_questions}")
        if "**Stage83 answer:** intentionally blank" not in body:
            fail(f"section lacks explicit blank-answer boundary: {section_id}")
        sections.append({
            "section_id": section_id,
            "question_count": actual_questions,
            "answers_present": False,
            "review_collection_allowed": False,
        })
    return sections


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    source_sha = args.source_sha.strip().lower()
    if SHA40_RE.fullmatch(source_sha) is None:
        fail("source-sha must be exact lowercase 40-character Git SHA")

    authority = load(AUTHORITY, "Stage83 authority")
    if authority.get("stage") != "STAGE83_BILLING_POLICY_REVIEW_QUESTIONNAIRE_SKELETON":
        fail("Stage83 authority stage drift")
    canonical = canonical_decision()
    validate_upstream()
    sections = validate_questionnaire()

    output = {
        "schema_version": 1,
        "stage": "STAGE83_BILLING_POLICY_REVIEW_QUESTIONNAIRE_SKELETON",
        "output_kind": "NON_ATTESTING_UNANSWERED_BILLING_POLICY_REVIEW_QUESTIONNAIRE_SKELETON",
        "state": "QUESTIONNAIRE_STRUCTURE_PREPARED_REAL_REVIEW_COLLECTION_BLOCKED_UNTIL_REAL_BILLING_AUTHORITY_NOT_POLICY_NOT_TERMS_NOT_EVIDENCE",
        "source_sha": source_sha,
        "canonical_target_open_decision": {
            "id": canonical.get("id"),
            "state": "OPEN",
            "applies_to": ["legal_terms_of_use"],
            "required": CANONICAL_REQUIRED,
            "resolution_authority": CANONICAL_RESOLUTION,
        },
        "source_bindings": {
            "stage83_authority_git_blob": git_blob_sha(AUTHORITY),
            "stage83_questionnaire_git_blob": git_blob_sha(QUESTIONNAIRE),
            "stage83_questionnaire_sha256": sha256_file(QUESTIONNAIRE),
            "open_decisions_git_blob": git_blob_sha(OPEN_DECISIONS),
            "stage61_authority_git_blob": git_blob_sha(STAGE61),
            "stage62_reconciliation_git_blob": git_blob_sha(STAGE62),
            "stage82r2_authority_git_blob": git_blob_sha(STAGE82R2_AUTHORITY),
            "stage82r2_registry_git_blob": git_blob_sha(STAGE82R2_REGISTRY),
        },
        "surface_count": 10,
        "section_count": len(sections),
        "total_question_count": sum(row["question_count"] for row in sections),
        "sections": sections,
        "review_roles_reserved_for_future_real_review": ["business_owner_review", "legal_review"],
        "hard_boundaries": {
            "real_billing_authority_present": False,
            "real_review_collection_allowed": False,
            "review_answers_present": False,
            "business_owner_review_completed": False,
            "legal_review_completed": False,
            "customer_policy_approved": False,
            "refund_or_withdrawal_rule_approved": False,
            "cancellation_rule_approved": False,
            "delinquency_rule_approved": False,
            "reactivation_rule_approved": False,
            "proration_rule_approved": False,
            "terms_of_use_modified": False,
            "target_open_decision_closed": False,
            "provider_call": False,
            "remote_mutation": False,
            "deployment": False,
            "evidence_ref_created": False,
            "evidence_digest_promoted": False,
            "evidence_migration_created": False,
            "legal_terms_gate_ready": False,
            "controlled_launch_promoted": False,
            "paid_media_promoted": False,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("STAGE83_BILLING_POLICY_QUESTIONNAIRE_SKELETON=PASS")
    print("SURFACE_COUNT=10")
    print(f"SECTION_COUNT={len(sections)}")
    print(f"TOTAL_QUESTION_COUNT={sum(row['question_count'] for row in sections)}")
    print("REAL_BILLING_AUTHORITY_PRESENT=false")
    print("REAL_REVIEW_COLLECTION_ALLOWED=false")
    print("CUSTOMER_POLICY_APPROVED=false")
    print("TARGET_DECISION_CLOSED=false")
    print("LEGAL_TERMS_GATE_READY=false")
    print("PROVIDER_CALL=false")
    print("REMOTE_MUTATION=false")


if __name__ == "__main__":
    main()
