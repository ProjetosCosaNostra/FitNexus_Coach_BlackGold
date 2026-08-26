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
SURFACE_IDS = [
    "trial_lifecycle", "paid_period_and_entitlement_boundary", "cancel_at_period_end_intent",
    "delinquency_and_recovery", "terminal_subscription_cancellation", "checkout_intent_lifecycle",
    "webhook_reconciliation_and_payment_events", "subscription_authority_audit_trail",
    "plan_price_and_fee_assumption_boundaries", "provider_selection_and_external_billing_boundary",
]
SECTION_IDS = [
    "trial_policy", "renewal_policy", "customer_initiated_cancellation",
    "service_initiated_or_exceptional_cancellation", "refund_withdrawal_policy",
    "delinquency_retry_suspension_and_recovery", "reactivation",
    "access_and_entitlement_consequences", "price_fees_taxes_and_proration",
    "customer_communications_and_receipts", "provider_mechanics_dependency",
    "data_retention_and_account_lifecycle_dependency", "terms_acceptance_and_versioning_dependency",
]
HEADINGS = [
    "## Section A — Trial policy", "## Section B — Renewal policy",
    "## Section C — Customer-initiated cancellation",
    "## Section D — Service-initiated or exceptional cancellation",
    "## Section E — Refund / withdrawal policy",
    "## Section F — Delinquency, retry, suspension and recovery", "## Section G — Reactivation",
    "## Section H — Access and entitlement consequences",
    "## Section I — Price, fees, taxes and proration",
    "## Section J — Customer communications and receipts", "## Section K — Provider mechanics dependency",
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


def blob(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_upstream() -> dict:
    decisions = load(OPEN_DECISIONS, "open decisions")
    unresolved = decisions.get("unresolved")
    target = next((r for r in unresolved if isinstance(r, dict) and r.get("id") == "BILLING_CANCELLATION_REFUND_POLICY"), None) if isinstance(unresolved, list) else None
    if not isinstance(target, dict):
        fail("canonical billing policy decision missing")
    if target.get("state") != "OPEN" or target.get("applies_to") != ["legal_terms_of_use"]:
        fail("canonical billing decision state/scope drift")
    if target.get("required") != CANONICAL_REQUIRED or target.get("resolution_authority") != CANONICAL_RESOLUTION:
        fail("canonical billing decision wording drift")

    s61 = load(STAGE61, "Stage61 authority")
    if s61.get("state_machine", {}).get("current_structural_state") != "AWAITING_REAL_OPERATOR_CREDENTIAL_EVIDENCE":
        fail("real billing authority precondition changed")
    s62 = load(STAGE62, "Stage62 reconciliation")
    if s62.get("final_state") != "STAGE61_MERGED_GREEN_REMOTE_UNCHANGED_FIRST_EXTERNAL_BOUNDARY_STILL_OPERATOR_CREDENTIAL_EVIDENCE":
        fail("Stage62 billing boundary drift")

    r2 = load(STAGE82R2_AUTHORITY, "Stage82R2 authority")
    billing = r2.get("billing_authority_boundary", {})
    expected_false = (
        "real_billing_authority_present", "real_business_owner_policy_review_may_be_collected_now",
        "real_legal_policy_review_may_be_collected_now",
    )
    for key in expected_false:
        if billing.get(key) is not False:
            fail(f"Stage83 skeleton precondition changed: {key}")
    if billing.get("unanswered_questionnaire_structure_may_be_prepared") is not True:
        fail("Stage82R2 no longer authorizes unanswered skeleton preparation")

    registry = load(STAGE82R2_REGISTRY, "Stage82R2 registry")
    surfaces = registry.get("technical_surfaces")
    if not isinstance(surfaces, list) or [r.get("surface_id") for r in surfaces if isinstance(r, dict)] != SURFACE_IDS:
        fail("Stage82R2 surface identity/order drift")
    if any(r.get("approved_policy_state") != "UNRESOLVED_AFTER_REAL_BILLING_AUTHORITY_BUSINESS_PLUS_LEGAL_REVIEW" for r in surfaces):
        fail("Stage82R2 contains an unexpectedly approved policy surface")
    return target


def validate_questionnaire() -> list[dict]:
    text = QUESTIONNAIRE.read_text(encoding="utf-8")
    markers = (
        "STRUCTURE ONLY — DO NOT COMPLETE, SIGN, APPROVE OR TREAT AS REVIEW MATERIAL BEFORE REAL BILLING AUTHORITY EXISTS",
        "REAL BILLING AUTHORITY MUST EXIST BEFORE ANY REAL BUSINESS-OWNER OR LEGAL POLICY REVIEW IS COLLECTED",
        CANONICAL_REQUIRED, CANONICAL_RESOLUTION,
        "REAL_BILLING_AUTHORITY_PRESENT=false", "REAL_REVIEW_COLLECTION_ALLOWED=false",
        "CUSTOMER_POLICY_APPROVED=false", "TERMS_OF_USE_MODIFIED=false",
        "TARGET_DECISION_CLOSED=false", "LEGAL_TERMS_GATE_READY=false",
        "PROVIDER_CALL=false", "REMOTE_MUTATION=false", "CONTROLLED_LAUNCH=DENIED", "PAID_MEDIA=DENIED",
    )
    for marker in markers:
        if marker not in text:
            fail(f"questionnaire missing boundary marker: {marker}")
    for sid in SURFACE_IDS:
        if f"`{sid}`" not in text:
            fail(f"questionnaire missing Stage82R2 surface: {sid}")

    sections: list[dict] = []
    for i, (sid, heading, expected) in enumerate(zip(SECTION_IDS, HEADINGS, QUESTION_COUNTS)):
        start = text.find(heading)
        if start < 0:
            fail(f"questionnaire section missing: {heading}")
        end = text.find(HEADINGS[i + 1], start + len(heading)) if i + 1 < len(HEADINGS) else text.find("## Future review completion criteria", start)
        if end < 0:
            fail(f"questionnaire section boundary missing: {heading}")
        body = text[start:end]
        actual = len(re.findall(r"(?m)^\d+\. ", body))
        if actual != expected:
            fail(f"question count drift for {sid}: expected {expected}, got {actual}")
        if "**Stage83 answer:** intentionally blank" not in body:
            fail(f"section is not explicitly unanswered: {sid}")
        sections.append({"section_id": sid, "question_count": actual, "answers_present": False, "review_collection_allowed": False})
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
    target = validate_upstream()
    sections = validate_questionnaire()

    output = {
        "schema_version": 1,
        "stage": "STAGE83_BILLING_POLICY_REVIEW_QUESTIONNAIRE_SKELETON",
        "output_kind": "NON_ATTESTING_UNANSWERED_BILLING_POLICY_REVIEW_QUESTIONNAIRE_SKELETON",
        "state": "QUESTIONNAIRE_STRUCTURE_PREPARED_REAL_REVIEW_COLLECTION_BLOCKED_UNTIL_REAL_BILLING_AUTHORITY_NOT_POLICY_NOT_TERMS_NOT_EVIDENCE",
        "source_sha": source_sha,
        "canonical_target_open_decision": {
            "id": target["id"], "state": "OPEN", "applies_to": ["legal_terms_of_use"],
            "required": CANONICAL_REQUIRED, "resolution_authority": CANONICAL_RESOLUTION,
        },
        "source_bindings": {
            "stage83_authority_git_blob": blob(AUTHORITY), "stage83_questionnaire_git_blob": blob(QUESTIONNAIRE),
            "stage83_questionnaire_sha256": sha256(QUESTIONNAIRE), "open_decisions_git_blob": blob(OPEN_DECISIONS),
            "stage61_authority_git_blob": blob(STAGE61), "stage62_reconciliation_git_blob": blob(STAGE62),
            "stage82r2_authority_git_blob": blob(STAGE82R2_AUTHORITY), "stage82r2_registry_git_blob": blob(STAGE82R2_REGISTRY),
        },
        "surface_count": 10, "section_count": len(sections),
        "total_question_count": sum(r["question_count"] for r in sections), "sections": sections,
        "review_roles_reserved_for_future_real_review": ["business_owner_review", "legal_review"],
        "hard_boundaries": {
            "real_billing_authority_present": False, "real_review_collection_allowed": False,
            "review_answers_present": False, "business_owner_review_completed": False, "legal_review_completed": False,
            "customer_policy_approved": False, "refund_or_withdrawal_rule_approved": False,
            "cancellation_rule_approved": False, "delinquency_rule_approved": False, "reactivation_rule_approved": False,
            "proration_rule_approved": False, "terms_of_use_modified": False, "target_open_decision_closed": False,
            "provider_call": False, "remote_mutation": False, "deployment": False, "evidence_ref_created": False,
            "evidence_digest_promoted": False, "evidence_migration_created": False, "legal_terms_gate_ready": False,
            "controlled_launch_promoted": False, "paid_media_promoted": False,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("STAGE83_BILLING_POLICY_QUESTIONNAIRE_SKELETON=PASS")
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
