from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage82_technical_billing_lifecycle_policy_inventory_authority.json"
REGISTRY = ROOT / "10_compliance" / "inventory" / "STAGE82_TECHNICAL_BILLING_LIFECYCLE_POLICY_SURFACE_REGISTRY.json"
OPEN_DECISIONS = ROOT / "10_compliance" / "drafts" / "COMPLIANCE_OPEN_DECISIONS.json"
STAGE61 = BACKEND / "stage61_billing_authorization_state_machine_authority.json"
STAGE62 = BACKEND / "stage62_stage61_final_reconciliation_authority.json"
MIGRATIONS = BACKEND / "migrations"
FAILURE_CLASS = "BGF-STAGE82-TECHNICAL-BILLING-LIFECYCLE-INVENTORY-GUARD-801"
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
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
        "STAGE82_TECHNICAL_BILLING_LIFECYCLE_POLICY_INVENTORY=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\nDETAIL={detail}"
    )


def load_json(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to load {label}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"{label} must be a JSON object")
    return value


def sha256_file(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        fail(f"unable to hash {path.relative_to(ROOT)}: {type(exc).__name__}")


def git_blob_sha(path: Path) -> str:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        fail(f"unable to read {path.relative_to(ROOT)}: {type(exc).__name__}")
    return hashlib.sha1(f"blob {len(raw)}\0".encode("utf-8") + raw).hexdigest()


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
        texts.append(text)
    return len(paths), digest.hexdigest(), "\n".join(texts).lower()


def validate_authority() -> dict:
    a = load_json(AUTHORITY, "Stage82 authority")
    if a.get("schema_version") != 1 or a.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("Stage82 authority identity drift")
    if a.get("stage") != "STAGE82_TECHNICAL_BILLING_LIFECYCLE_POLICY_INVENTORY":
        fail("Stage82 authority stage drift")
    if a.get("baseline_main_sha") != "d88060f9e3787a9e34937385b1f69370ba5379fb":
        fail("Stage82 baseline main SHA drift")
    target = a.get("target_open_decision")
    if not isinstance(target, dict):
        fail("Stage82 target decision missing")
    if target.get("id") != "BILLING_CANCELLATION_REFUND_POLICY" or target.get("state") != "OPEN":
        fail("BILLING_CANCELLATION_REFUND_POLICY must remain OPEN")
    if target.get("affected_gates") != ["legal_terms_of_use"]:
        fail("Stage82 affected gate set/order drift")
    if target.get("required") != "Approved customer-facing subscription, cancellation, delinquency and refund policy.":
        fail("Stage82 target requirement drift")
    if target.get("resolution_authority") != "business owner plus legal review":
        fail("Stage82 resolution authority drift")
    if target.get("stage82_can_close_decision") is not False:
        fail("Stage82 cannot close billing policy decision")

    remote = a.get("fresh_remote_read_only_receipt")
    if not isinstance(remote, dict):
        fail("Stage82 remote receipt missing")
    if [remote.get("auth_users"), remote.get("organizations"), remote.get("students")] != [0, 0, 0]:
        fail("Stage82 customer baseline drift")
    if [remote.get("organization_subscriptions"), remote.get("checkout_intents"), remote.get("webhook_receipts")] != [0, 0, 0]:
        fail("Stage82 billing row baseline drift")
    if remote.get("asaas_state") != "selected_pending_credentials" or remote.get("asaas_activated_at") is not None:
        fail("Stage82 Asaas baseline drift")
    if remote.get("remote_mutation_performed") is not False:
        fail("Stage82 remote receipt must remain read-only")

    sep = a.get("billing_authority_separation")
    if not isinstance(sep, dict):
        fail("Stage82 billing authority separation missing")
    if sep.get("current_billing_structural_state") != "AWAITING_REAL_OPERATOR_CREDENTIAL_EVIDENCE":
        fail("Stage82 billing structural state drift")
    if sep.get("provider_code") != "asaas" or sep.get("provider_active") is not False:
        fail("Stage82 provider state drift")
    for key, value in sep.items():
        if key.startswith("stage82_can_") and value is not False:
            fail(f"Stage82 authority separation must keep {key}=false")

    contract = a.get("inventory_contract")
    if not isinstance(contract, dict):
        fail("Stage82 inventory contract missing")
    if contract.get("expected_surface_count") != 10:
        fail("Stage82 expected surface count drift")
    for key in (
        "technical_source_binding_required", "migration_corpus_digest_required", "registry_digest_required",
        "stage61_and_stage62_binding_required", "technical_statuses_and_lifecycle_markers_may_be_reported",
        "unresolved_business_legal_questions_may_be_reported",
    ):
        if contract.get(key) is not True:
            fail(f"Stage82 contract must keep {key}=true")
    for key, value in contract.items():
        if key in {"expected_surface_count", "registry", "builder", "guard", "workflow"}:
            continue
        if key.endswith("_required") or key.endswith("_reported"):
            continue
        if key in {"technical_statuses_and_lifecycle_markers_may_be_reported", "unresolved_business_legal_questions_may_be_reported"}:
            continue
        if isinstance(value, bool) and value is not False:
            fail(f"Stage82 policy/remote boundary must keep {key}=false")
    return a


def validate_upstream(authority: dict) -> dict:
    pins = authority.get("upstream_authority")
    if not isinstance(pins, dict):
        fail("Stage82 upstream pins missing")
    expected = {
        OPEN_DECISIONS: "215d527c1cb79d7b72697f03f1f84887e3a72d95",
        STAGE61: "3225b3c5d03fc45c57a4f043411d03b092e31c13",
        STAGE62: "4c9c99ecb2f3f016287e9d5c7de1888e6e2c846f",
        REGISTRY: "8df44e092680c5dba82d602efa23872124daedd0",
    }
    for path, expected_blob in expected.items():
        if git_blob_sha(path) != expected_blob:
            fail(f"Stage82 upstream Git blob drift: {path.relative_to(ROOT)}")

    decisions = load_json(OPEN_DECISIONS, "open decisions")
    unresolved = decisions.get("unresolved")
    target = next((x for x in unresolved if isinstance(x, dict) and x.get("id") == "BILLING_CANCELLATION_REFUND_POLICY"), None) if isinstance(unresolved, list) else None
    if not isinstance(target, dict) or target.get("state") != "OPEN":
        fail("BILLING_CANCELLATION_REFUND_POLICY missing or closed")
    if target.get("applies_to") != ["legal_terms_of_use"]:
        fail("billing policy decision applies_to drift")
    if target.get("resolution_authority") != "business owner plus legal review":
        fail("billing policy decision resolution authority drift")

    s61 = load_json(STAGE61, "Stage61 authority")
    if s61.get("stage") != "STAGE61_BILLING_AUTHORIZATION_STATE_MACHINE":
        fail("Stage61 authority stage drift")
    sm = s61.get("state_machine")
    if not isinstance(sm, dict) or sm.get("current_structural_state") != "AWAITING_REAL_OPERATOR_CREDENTIAL_EVIDENCE":
        fail("Stage61 structural state drift")
    if sm.get("state_evaluator_output_is_provider_call_authority") is not False or sm.get("state_evaluator_output_is_launch_authority") is not False:
        fail("Stage61 provider/launch authority boundary drift")

    s62 = load_json(STAGE62, "Stage62 final reconciliation")
    if s62.get("stage") != "STAGE62_STAGE61_FINAL_RECONCILIATION":
        fail("Stage62 stage drift")
    if s62.get("final_state") != "STAGE61_MERGED_GREEN_REMOTE_UNCHANGED_FIRST_EXTERNAL_BOUNDARY_STILL_OPERATOR_CREDENTIAL_EVIDENCE":
        fail("Stage62 final billing boundary drift")
    governance = s62.get("governance")
    if not isinstance(governance, dict) or governance.get("provider_call") != "DENIED" or governance.get("billing_provider_credentials") != "DENIED":
        fail("Stage62 provider/billing gate boundary drift")
    return target


def validate_registry(corpus: str) -> list[dict]:
    registry = load_json(REGISTRY, "Stage82 registry")
    if registry.get("schema_version") != 1:
        fail("Stage82 registry schema drift")
    if registry.get("status") != "TECHNICAL_BILLING_LIFECYCLE_SURFACE_REGISTRY_POLICY_UNRESOLVED_NOT_CUSTOMER_TERMS_NOT_EVIDENCE":
        fail("Stage82 registry status drift")
    if registry.get("resolution_authority") != "business owner plus legal review":
        fail("Stage82 registry resolution authority drift")
    boundaries = registry.get("global_boundaries")
    if not isinstance(boundaries, dict) or not boundaries:
        fail("Stage82 global boundaries missing")
    for key, value in boundaries.items():
        if value is not False:
            fail(f"Stage82 registry boundary must remain false: {key}")

    surfaces = registry.get("technical_surfaces")
    if not isinstance(surfaces, list) or len(surfaces) != 10:
        fail("Stage82 technical surface count drift")
    ids = [x.get("surface_id") for x in surfaces if isinstance(x, dict)]
    if ids != EXPECTED_SURFACE_IDS:
        fail("Stage82 technical surface identity/order drift")

    built: list[dict] = []
    for item in surfaces:
        if not isinstance(item, dict):
            fail("Stage82 technical surface must be object")
        sid = item.get("surface_id")
        tables = item.get("source_tables")
        fields = item.get("field_markers")
        questions = item.get("policy_questions_for_real_review")
        observation = item.get("technical_observation")
        if not isinstance(tables, list) or not tables:
            fail(f"Stage82 source tables missing: {sid}")
        if not isinstance(fields, list) or not fields:
            fail(f"Stage82 field markers missing: {sid}")
        if not isinstance(questions, list) or len(questions) < 3:
            fail(f"Stage82 policy questions insufficient: {sid}")
        if not isinstance(observation, str) or len(observation.strip()) < 20:
            fail(f"Stage82 technical observation missing: {sid}")
        if item.get("approved_policy_state") != "UNRESOLVED_BUSINESS_OWNER_PLUS_LEGAL_REVIEW":
            fail(f"Stage82 surface policy unexpectedly resolved: {sid}")
        for table in tables:
            if not isinstance(table, str) or table.split(".")[-1].lower() not in corpus:
                fail(f"Stage82 migration corpus missing source table: {sid}:{table}")
        for field in fields:
            if not isinstance(field, str) or field.lower() not in corpus:
                fail(f"Stage82 migration corpus missing field marker: {sid}:{field}")
        built.append({
            "surface_id": sid,
            "source_tables": tables,
            "field_markers": fields,
            "technical_observation": observation,
            "policy_questions_for_real_review": questions,
            "technical_source_markers_validated": True,
            "approved_policy_state": "UNRESOLVED_BUSINESS_OWNER_PLUS_LEGAL_REVIEW",
        })

    unresolved = registry.get("cross_surface_unresolved_policy_decisions")
    if not isinstance(unresolved, list) or len(unresolved) < 10:
        fail("Stage82 cross-surface unresolved decisions missing")
    return built


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    source_sha = args.source_sha.strip().lower()
    if SHA40_RE.fullmatch(source_sha) is None:
        fail("source-sha must be exact lowercase 40-character Git SHA")

    authority = validate_authority()
    target = validate_upstream(authority)
    migration_count, migration_digest, corpus = migration_corpus()
    surfaces = validate_registry(corpus)

    registry = load_json(REGISTRY, "Stage82 registry")
    output = {
        "schema_version": 1,
        "stage": "STAGE82_TECHNICAL_BILLING_LIFECYCLE_POLICY_INVENTORY",
        "output_kind": "NON_ATTESTING_TECHNICAL_BILLING_LIFECYCLE_POLICY_SURFACE_INVENTORY",
        "state": "TECHNICAL_BILLING_LIFECYCLE_SURFACES_INVENTORIED_POLICY_DECISIONS_UNRESOLVED_NOT_CUSTOMER_TERMS_EVIDENCE",
        "source_sha": source_sha,
        "target_open_decision": {
            "id": target.get("id"),
            "state": "OPEN",
            "resolution_authority": "business owner plus legal review",
        },
        "source_bindings": {
            "stage82_registry_git_blob": git_blob_sha(REGISTRY),
            "stage82_registry_sha256": sha256_file(REGISTRY),
            "open_decisions_git_blob": git_blob_sha(OPEN_DECISIONS),
            "open_decisions_sha256": sha256_file(OPEN_DECISIONS),
            "stage61_authority_git_blob": git_blob_sha(STAGE61),
            "stage61_authority_sha256": sha256_file(STAGE61),
            "stage62_reconciliation_git_blob": git_blob_sha(STAGE62),
            "stage62_reconciliation_sha256": sha256_file(STAGE62),
            "migration_file_count": migration_count,
            "migration_corpus_sha256": migration_digest,
        },
        "surface_count": 10,
        "technical_surfaces": surfaces,
        "cross_surface_unresolved_policy_decisions": registry.get("cross_surface_unresolved_policy_decisions"),
        "current_billing_structural_state": "AWAITING_REAL_OPERATOR_CREDENTIAL_EVIDENCE",
        "asaas_state": "selected_pending_credentials",
        "customer_policy_approved": False,
        "business_owner_review_performed": False,
        "legal_review_performed": False,
        "refund_rule_approved": False,
        "cancellation_rule_approved": False,
        "delinquency_rule_approved": False,
        "proration_rule_approved": False,
        "access_entitlement_rule_approved": False,
        "provider_refund_capability_proven": False,
        "terms_of_use_modified": False,
        "target_open_decision_closed": False,
        "legal_terms_of_use_gate_ready": False,
        "evidence_ref_created": False,
        "evidence_digest_promoted": False,
        "evidence_migration_created": False,
        "network_call_performed": False,
        "provider_call_performed": False,
        "supabase_mutation_performed": False,
        "deployment_performed": False,
        "controlled_launch_promoted": False,
        "paid_media_promoted": False,
        "next_action": "REAL_BUSINESS_OWNER_PLUS_LEGAL_REVIEW_REQUIRED_BEFORE_CUSTOMER_FACING_BILLING_CANCELLATION_DELINQUENCY_OR_REFUND_POLICY_EXISTS",
    }

    dest = args.output.expanduser().resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(output, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print("STAGE82_TECHNICAL_BILLING_LIFECYCLE_POLICY_INVENTORY=PASS")
    print("SURFACE_COUNT=10")
    print("CUSTOMER_POLICY_APPROVED=false")
    print("TARGET_DECISION_CLOSED=false")
    print("LEGAL_TERMS_GATE_READY=false")
    print("PROVIDER_CALL=false")
    print("REMOTE_MUTATION=false")


if __name__ == "__main__":
    main()
