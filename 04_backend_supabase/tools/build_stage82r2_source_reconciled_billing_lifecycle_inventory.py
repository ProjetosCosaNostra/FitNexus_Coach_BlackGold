from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage82r2_billing_lifecycle_source_reconciliation_authority.json"
REGISTRY = ROOT / "10_compliance" / "inventory" / "STAGE82R2_TECHNICAL_BILLING_LIFECYCLE_POLICY_SURFACE_REGISTRY.json"
OPEN_DECISIONS = ROOT / "10_compliance" / "drafts" / "COMPLIANCE_OPEN_DECISIONS.json"
STAGE61 = BACKEND / "stage61_billing_authorization_state_machine_authority.json"
STAGE62 = BACKEND / "stage62_stage61_final_reconciliation_authority.json"
MIGRATIONS = BACKEND / "migrations"
FAILURE_CLASS = "BGF-STAGE82R2-BILLING-LIFECYCLE-SOURCE-RECONCILIATION-GUARD-819"
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
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
FORBIDDEN_HISTORICAL_MARKERS = {
    "canceled_at", "delinquent_since", "previous_state", "new_state", "external_charge_ref",
    "processing_error", "matched_organization_id", "matched_subscription_id", "effective_to",
    "percentage_bps", "fixed_fee_minor", "tax_bps", "source_ref", "lifecycle_state", "deactivated_at",
}


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE82R2_SOURCE_RECONCILED_BILLING_LIFECYCLE_INVENTORY=FAIL\n"
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


def migration_corpus() -> tuple[int, str, str]:
    paths = sorted(MIGRATIONS.glob("*.sql"), key=lambda p: p.name)
    if not paths:
        fail("migration corpus is empty")
    digest = hashlib.sha256()
    texts: list[str] = []
    for path in paths:
        rel = path.relative_to(ROOT).as_posix()
        try:
            raw = path.read_bytes()
            text = raw.decode("utf-8").lower()
        except (OSError, UnicodeDecodeError) as exc:
            fail(f"migration corpus unreadable: {rel}: {type(exc).__name__}")
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(raw)
        digest.update(b"\0")
        texts.append(text)
    return len(paths), digest.hexdigest(), "\n".join(texts)


def canonical_decision() -> dict:
    decisions = load(OPEN_DECISIONS, "open decisions")
    unresolved = decisions.get("unresolved")
    target = next(
        (x for x in unresolved if isinstance(x, dict) and x.get("id") == "BILLING_CANCELLATION_REFUND_POLICY"),
        None,
    ) if isinstance(unresolved, list) else None
    if not isinstance(target, dict):
        fail("BILLING_CANCELLATION_REFUND_POLICY missing")
    if target.get("state") != "OPEN" or target.get("applies_to") != ["legal_terms_of_use"]:
        fail("canonical billing decision state/scope drift")
    if target.get("required") != CANONICAL_REQUIRED:
        fail("canonical billing requirement drift")
    if target.get("resolution_authority") != CANONICAL_RESOLUTION_AUTHORITY:
        fail("canonical billing resolution authority drift")
    return target


def validate_registry(corpus: str) -> tuple[list[dict], dict]:
    registry = load(REGISTRY, "Stage82R2 registry")
    if registry.get("status") != "TECHNICAL_BILLING_LIFECYCLE_SURFACE_REGISTRY_R2_SOURCE_RECONCILED_POLICY_UNRESOLVED_NOT_CUSTOMER_TERMS_NOT_EVIDENCE":
        fail("Stage82R2 registry status drift")
    if registry.get("resolution_authority") != CANONICAL_RESOLUTION_AUTHORITY:
        fail("Stage82R2 registry resolution authority drift")
    canonical = registry.get("canonical_open_decision", {})
    if canonical.get("required") != CANONICAL_REQUIRED or canonical.get("resolution_authority") != CANONICAL_RESOLUTION_AUTHORITY:
        fail("Stage82R2 registry canonical decision drift")
    if canonical.get("state") != "OPEN" or canonical.get("applies_to") != ["legal_terms_of_use"]:
        fail("Stage82R2 registry canonical decision state/scope drift")

    reconciliation = registry.get("source_reconciliation")
    if not isinstance(reconciliation, dict):
        fail("Stage82R2 source reconciliation missing")
    removed = reconciliation.get("historical_false_or_unproven_markers_removed")
    if not isinstance(removed, list) or not FORBIDDEN_HISTORICAL_MARKERS.issubset(set(removed)):
        fail("Stage82R2 historical false-marker removal set incomplete")

    boundaries = registry.get("global_boundaries")
    if not isinstance(boundaries, dict) or not boundaries or any(value is not False for value in boundaries.values()):
        fail("Stage82R2 global boundaries must all remain false")

    surfaces = registry.get("technical_surfaces")
    if not isinstance(surfaces, list) or len(surfaces) != 10:
        fail("Stage82R2 technical surface count drift")
    if [x.get("surface_id") for x in surfaces if isinstance(x, dict)] != EXPECTED_SURFACE_IDS:
        fail("Stage82R2 technical surface identity/order drift")

    built: list[dict] = []
    for item in surfaces:
        if not isinstance(item, dict):
            fail("Stage82R2 technical surface must be object")
        sid = item.get("surface_id")
        tables = item.get("source_tables")
        fields = item.get("field_markers")
        questions = item.get("policy_questions_for_future_real_review")
        if not isinstance(tables, list) or not tables:
            fail(f"source tables missing: {sid}")
        if not isinstance(fields, list) or not fields:
            fail(f"field markers missing: {sid}")
        if FORBIDDEN_HISTORICAL_MARKERS.intersection(fields):
            fail(f"historical false marker leaked into reconciled surface: {sid}")
        if not isinstance(questions, list) or len(questions) < 3:
            fail(f"future real review questions missing: {sid}")
        if item.get("approved_policy_state") != "UNRESOLVED_AFTER_REAL_BILLING_AUTHORITY_BUSINESS_PLUS_LEGAL_REVIEW":
            fail(f"Stage82R2 surface policy unexpectedly resolved: {sid}")
        for table in tables:
            if not isinstance(table, str) or table.split(".")[-1].lower() not in corpus:
                fail(f"migration corpus missing source table: {sid}:{table}")
        for field in fields:
            if not isinstance(field, str) or field.lower() not in corpus:
                fail(f"migration corpus missing field marker: {sid}:{field}")
        built.append({
            "surface_id": sid,
            "source_tables": tables,
            "field_markers": fields,
            "technical_observation": item.get("technical_observation"),
            "policy_questions_for_future_real_review": questions,
            "technical_source_markers_validated": True,
            "approved_policy_state": "UNRESOLVED_AFTER_REAL_BILLING_AUTHORITY_BUSINESS_PLUS_LEGAL_REVIEW",
        })
    return built, reconciliation


def validate_billing_boundary() -> None:
    s61 = load(STAGE61, "Stage61 authority")
    if s61.get("state_machine", {}).get("current_structural_state") != "AWAITING_REAL_OPERATOR_CREDENTIAL_EVIDENCE":
        fail("Stage61 billing structural state drift")
    s62 = load(STAGE62, "Stage62 reconciliation")
    if s62.get("final_state") != "STAGE61_MERGED_GREEN_REMOTE_UNCHANGED_FIRST_EXTERNAL_BOUNDARY_STILL_OPERATOR_CREDENTIAL_EVIDENCE":
        fail("Stage62 billing boundary drift")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    source_sha = args.source_sha.strip().lower()
    if SHA40_RE.fullmatch(source_sha) is None:
        fail("source-sha must be exact lowercase 40-character Git SHA")

    authority = load(AUTHORITY, "Stage82R2 authority")
    if authority.get("stage") != "STAGE82R2_BILLING_LIFECYCLE_SOURCE_RECONCILIATION":
        fail("Stage82R2 authority stage drift")
    decision = canonical_decision()
    validate_billing_boundary()
    migration_count, migration_digest, corpus = migration_corpus()
    surfaces, reconciliation = validate_registry(corpus)

    output = {
        "schema_version": 1,
        "stage": "STAGE82R2_BILLING_LIFECYCLE_SOURCE_RECONCILIATION",
        "output_kind": "NON_ATTESTING_SOURCE_RECONCILED_TECHNICAL_BILLING_LIFECYCLE_POLICY_INVENTORY",
        "state": "SOURCE_MARKERS_RECONCILED_TO_AUTHORITATIVE_SCHEMA_POLICY_DECISIONS_UNRESOLVED_NOT_CUSTOMER_TERMS_EVIDENCE",
        "source_sha": source_sha,
        "canonical_target_open_decision": {
            "id": decision.get("id"),
            "state": "OPEN",
            "applies_to": ["legal_terms_of_use"],
            "required": CANONICAL_REQUIRED,
            "resolution_authority": CANONICAL_RESOLUTION_AUTHORITY,
        },
        "failed_head_chain": [
            {
                "head_sha": "369b56d8c541a6981cb6e236b5690396cb1382e9",
                "workflow_run_id": 32982246549,
                "detail": "global billing policy requirement drift",
                "preserved": True,
            },
            {
                "head_sha": "7762a4e833cc5df860c2c94a73ccc0e14ed86ed8",
                "workflow_run_id": 32982854740,
                "detail": "migration corpus missing field marker: cancel_at_period_end_intent:canceled_at",
                "preserved": True,
            },
        ],
        "source_reconciliation": reconciliation,
        "source_bindings": {
            "stage82r2_authority_git_blob": git_blob_sha(AUTHORITY),
            "stage82r2_registry_git_blob": git_blob_sha(REGISTRY),
            "stage82r2_registry_sha256": sha256_file(REGISTRY),
            "open_decisions_git_blob": git_blob_sha(OPEN_DECISIONS),
            "open_decisions_sha256": sha256_file(OPEN_DECISIONS),
            "stage61_authority_git_blob": git_blob_sha(STAGE61),
            "stage62_reconciliation_git_blob": git_blob_sha(STAGE62),
            "migration_file_count": migration_count,
            "migration_corpus_sha256": migration_digest,
        },
        "surface_count": 10,
        "technical_surfaces": surfaces,
        "current_billing_structural_state": "AWAITING_REAL_OPERATOR_CREDENTIAL_EVIDENCE",
        "provider_code": "asaas",
        "provider_active": False,
        "policy_boundaries": {
            "real_billing_authority_present": False,
            "customer_policy_approved": False,
            "refund_rule_approved": False,
            "cancellation_rule_approved": False,
            "delinquency_rule_approved": False,
            "reactivation_rule_approved": False,
            "proration_rule_approved": False,
            "post_cancellation_access_rule_approved": False,
            "customer_communication_rule_approved": False,
            "terms_of_use_modified": False,
            "target_open_decision_closed": False,
            "business_owner_review_completed": False,
            "legal_review_completed": False,
            "provider_call": False,
            "remote_mutation": False,
            "deployment": False,
            "evidence_migration_created": False,
            "legal_terms_gate_ready": False,
            "controlled_launch_promoted": False,
            "paid_media_promoted": False,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("STAGE82R2_SOURCE_RECONCILED_BILLING_LIFECYCLE_INVENTORY=PASS")
    print("FAILED_HEAD_COUNT=2")
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
