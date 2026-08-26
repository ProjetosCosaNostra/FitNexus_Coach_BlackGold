from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage82r1_billing_policy_source_wording_reconciliation_authority.json"
STAGE82_AUTHORITY = BACKEND / "stage82_technical_billing_lifecycle_policy_inventory_authority.json"
REGISTRY = ROOT / "10_compliance" / "inventory" / "STAGE82_TECHNICAL_BILLING_LIFECYCLE_POLICY_SURFACE_REGISTRY.json"
OPEN_DECISIONS = ROOT / "10_compliance" / "drafts" / "COMPLIANCE_OPEN_DECISIONS.json"
STAGE61 = BACKEND / "stage61_billing_authorization_state_machine_authority.json"
STAGE62 = BACKEND / "stage62_stage61_final_reconciliation_authority.json"
MIGRATIONS = BACKEND / "migrations"
FAILURE_CLASS = "BGF-STAGE82R1-BILLING-POLICY-SOURCE-WORDING-RECONCILIATION-GUARD-802"
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
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


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE82R1_RECONCILED_BILLING_LIFECYCLE_INVENTORY=FAIL\n"
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
            text = raw.decode("utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            fail(f"migration corpus unreadable: {rel}: {type(exc).__name__}")
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(raw)
        digest.update(b"\0")
        texts.append(text.lower())
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
    if target.get("state") != "OPEN":
        fail("BILLING_CANCELLATION_REFUND_POLICY must remain OPEN")
    if target.get("applies_to") != ["legal_terms_of_use"]:
        fail("billing decision applies_to drift")
    if target.get("required") != CANONICAL_REQUIRED:
        fail("canonical billing policy requirement drift")
    if target.get("resolution_authority") != CANONICAL_RESOLUTION_AUTHORITY:
        fail("canonical billing policy resolution authority drift")
    return target


def validate_historical_stage82_snapshot() -> None:
    stage82 = load(STAGE82_AUTHORITY, "historical Stage82 authority")
    target = stage82.get("target_open_decision")
    if not isinstance(target, dict):
        fail("historical Stage82 target decision missing")
    if target.get("required") != HISTORICAL_REQUIRED:
        fail("historical Stage82 wording changed; reconciliation provenance invalid")
    if target.get("resolution_authority") != HISTORICAL_RESOLUTION_AUTHORITY:
        fail("historical Stage82 resolution wording changed; reconciliation provenance invalid")
    if target.get("state") != "OPEN" or target.get("stage82_can_close_decision") is not False:
        fail("historical Stage82 decision boundary drift")


def validate_registry(corpus: str) -> list[dict]:
    registry = load(REGISTRY, "Stage82 registry")
    if registry.get("status") != "TECHNICAL_BILLING_LIFECYCLE_SURFACE_REGISTRY_POLICY_UNRESOLVED_NOT_CUSTOMER_TERMS_NOT_EVIDENCE":
        fail("Stage82 registry status drift")
    boundaries = registry.get("global_boundaries")
    if not isinstance(boundaries, dict) or not boundaries or any(value is not False for value in boundaries.values()):
        fail("Stage82 registry boundaries must all remain false")
    surfaces = registry.get("technical_surfaces")
    if not isinstance(surfaces, list) or len(surfaces) != 10:
        fail("Stage82 registry surface count drift")
    if [x.get("surface_id") for x in surfaces if isinstance(x, dict)] != EXPECTED_SURFACE_IDS:
        fail("Stage82 registry surface identity/order drift")

    built: list[dict] = []
    for item in surfaces:
        if not isinstance(item, dict):
            fail("Stage82 registry surface must be an object")
        sid = item.get("surface_id")
        tables = item.get("source_tables")
        fields = item.get("field_markers")
        questions = item.get("policy_questions_for_real_review")
        if not isinstance(tables, list) or not tables:
            fail(f"missing source tables: {sid}")
        if not isinstance(fields, list) or not fields:
            fail(f"missing field markers: {sid}")
        if not isinstance(questions, list) or len(questions) < 3:
            fail(f"insufficient review questions: {sid}")
        if item.get("approved_policy_state") != "UNRESOLVED_BUSINESS_OWNER_PLUS_LEGAL_REVIEW":
            fail(f"technical surface unexpectedly approved: {sid}")
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
            "policy_questions_for_real_review": questions,
            "technical_source_markers_validated": True,
            "approved_policy_state": "UNRESOLVED_BUSINESS_OWNER_PLUS_LEGAL_REVIEW",
        })
    return built


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

    authority = load(AUTHORITY, "Stage82R1 authority")
    if authority.get("stage") != "STAGE82R1_BILLING_POLICY_SOURCE_WORDING_RECONCILIATION":
        fail("Stage82R1 authority stage drift")
    canonical = canonical_decision()
    validate_historical_stage82_snapshot()
    validate_billing_boundary()
    migration_count, migration_digest, corpus = migration_corpus()
    surfaces = validate_registry(corpus)

    output = {
        "schema_version": 1,
        "stage": "STAGE82R1_BILLING_POLICY_SOURCE_WORDING_RECONCILIATION",
        "output_kind": "NON_ATTESTING_RECONCILED_TECHNICAL_BILLING_LIFECYCLE_POLICY_INVENTORY",
        "state": "TECHNICAL_BILLING_LIFECYCLE_INVENTORY_RECONCILED_TO_CANONICAL_OPEN_DECISION_NOT_CUSTOMER_TERMS_EVIDENCE",
        "source_sha": source_sha,
        "canonical_target_open_decision": {
            "id": canonical.get("id"),
            "state": "OPEN",
            "applies_to": ["legal_terms_of_use"],
            "required": CANONICAL_REQUIRED,
            "resolution_authority": CANONICAL_RESOLUTION_AUTHORITY,
        },
        "historical_stage82_wording_reconciliation": {
            "failed_head_sha": "369b56d8c541a6981cb6e236b5690396cb1382e9",
            "failed_ci_run_id": 32982246549,
            "failed_detail": "global billing policy requirement drift",
            "historical_required": HISTORICAL_REQUIRED,
            "historical_resolution_authority": HISTORICAL_RESOLUTION_AUTHORITY,
            "canonical_required": CANONICAL_REQUIRED,
            "canonical_resolution_authority": CANONICAL_RESOLUTION_AUTHORITY,
            "historical_snapshot_mutated": False,
        },
        "source_bindings": {
            "stage82r1_authority_git_blob": git_blob_sha(AUTHORITY),
            "stage82_authority_git_blob": git_blob_sha(STAGE82_AUTHORITY),
            "stage82_registry_git_blob": git_blob_sha(REGISTRY),
            "stage82_registry_sha256": sha256_file(REGISTRY),
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
            "customer_policy_approved": False,
            "refund_rule_approved": False,
            "cancellation_rule_approved": False,
            "delinquency_rule_approved": False,
            "proration_rule_approved": False,
            "post_cancellation_access_rule_approved": False,
            "customer_communication_rule_approved": False,
            "terms_of_use_modified": False,
            "target_open_decision_closed": False,
            "real_billing_authority_present": False,
            "business_owner_review_completed": False,
            "legal_review_completed": False,
            "provider_call": False,
            "remote_mutation": False,
            "evidence_migration_created": False,
            "legal_terms_gate_ready": False,
            "controlled_launch_promoted": False,
            "paid_media_promoted": False,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("STAGE82R1_RECONCILED_BILLING_LIFECYCLE_INVENTORY=PASS")
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
