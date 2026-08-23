from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage36_controlled_launch_external_gate_assessment_authority.json"
PLACEHOLDERS = BACKEND / "external_gate_evidence_placeholders.json"
STAGE20 = BACKEND / "migrations" / "20260819062000_stage20_controlled_launch_admission.sql"
STAGE35 = BACKEND / "stage35_alert_external_delivery_cleanup_final_reconciliation_authority.json"
PROOF_TRIGGER = BACKEND / "stage35_alert_external_delivery_proof_trigger.json"

BASELINE = "5d38f307c6bd597acedbfcee371e8f365918f3f4"
OBSERVED = "2026-08-23T17:24:41.050833+00:00"
PROJECT_REF = "mceukeondizkwlpfxzgf"
PLACEHOLDER_BLOB = "07e6eb3330076f3e576ed2dd2a2e385f5fa3b2db"
STAGE20_BLOB = "e26dd18eff1f4dbf099ad721963b06d6362bc3b9"
STAGE35_BLOB = "f495f0c01bb16b049b5383f46db9868724b798e8"
FAILURE_CLASS = "BGF-STAGE36-LAUNCH-ASSESSMENT-319"

EXPECTED_MATRIX = [
    {
        "gate_code": "billing_provider_credentials",
        "category": "commercial",
        "authority_mode": "external_authorization",
        "mandatory": True,
        "effective_state": "blocked",
        "evidence_state": None,
        "has_evidence_ref": False,
        "has_evidence_digest": False,
        "assessment": "BLOCKED_NO_ACTIVE_ASAAS_EXTERNAL_AUTHORITY",
    },
    {
        "gate_code": "pricing_experiment",
        "category": "commercial",
        "authority_mode": "automatic",
        "mandatory": True,
        "effective_state": "ready",
        "evidence_state": None,
        "has_evidence_ref": False,
        "has_evidence_digest": False,
        "assessment": "AUTOMATIC_READINESS_PASS",
    },
    {
        "gate_code": "production_deployment",
        "category": "deployment",
        "authority_mode": "evidence_migration",
        "mandatory": True,
        "effective_state": "blocked",
        "evidence_state": "blocked",
        "has_evidence_ref": False,
        "has_evidence_digest": False,
        "assessment": "BLOCKED_NO_EXTERNAL_EVIDENCE",
    },
    {
        "gate_code": "legal_terms_of_use",
        "category": "legal",
        "authority_mode": "evidence_migration",
        "mandatory": True,
        "effective_state": "blocked",
        "evidence_state": "blocked",
        "has_evidence_ref": False,
        "has_evidence_digest": False,
        "assessment": "BLOCKED_NO_EXTERNAL_EVIDENCE",
    },
    {
        "gate_code": "data_subject_request_channel",
        "category": "privacy",
        "authority_mode": "evidence_migration",
        "mandatory": True,
        "effective_state": "blocked",
        "evidence_state": "blocked",
        "has_evidence_ref": False,
        "has_evidence_digest": False,
        "assessment": "BLOCKED_NO_EXTERNAL_EVIDENCE",
    },
    {
        "gate_code": "legal_privacy_notice",
        "category": "privacy",
        "authority_mode": "evidence_migration",
        "mandatory": True,
        "effective_state": "blocked",
        "evidence_state": "blocked",
        "has_evidence_ref": False,
        "has_evidence_digest": False,
        "assessment": "BLOCKED_NO_EXTERNAL_EVIDENCE",
    },
    {
        "gate_code": "legal_role_mapping",
        "category": "privacy",
        "authority_mode": "evidence_migration",
        "mandatory": True,
        "effective_state": "blocked",
        "evidence_state": "blocked",
        "has_evidence_ref": False,
        "has_evidence_digest": False,
        "assessment": "BLOCKED_NO_EXTERNAL_EVIDENCE",
    },
    {
        "gate_code": "incident_response",
        "category": "security",
        "authority_mode": "evidence_migration",
        "mandatory": True,
        "effective_state": "blocked",
        "evidence_state": "blocked",
        "has_evidence_ref": False,
        "has_evidence_digest": False,
        "assessment": "BLOCKED_NO_OPERATIONAL_EVIDENCE",
    },
    {
        "gate_code": "tracking_core",
        "category": "tracking",
        "authority_mode": "automatic",
        "mandatory": True,
        "effective_state": "ready",
        "evidence_state": None,
        "has_evidence_ref": False,
        "has_evidence_digest": False,
        "assessment": "AUTOMATIC_READINESS_PASS",
    },
]


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE36_CONTROLLED_LAUNCH_EXTERNAL_GATE_ASSESSMENT=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\nDETAIL={detail}"
    )


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to read {path.relative_to(ROOT)}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"expected JSON object: {path.relative_to(ROOT)}")
    return value


def blob(path: Path) -> str:
    try:
        data = path.read_bytes()
    except OSError as exc:
        fail(f"unable to hash {path.relative_to(ROOT)}: {type(exc).__name__}")
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def require(mapping: dict, expected: dict, label: str) -> None:
    if not isinstance(mapping, dict):
        fail(f"{label} must be an object")
    for key, value in expected.items():
        if mapping.get(key) != value:
            fail(f"{label} drift: {key}")


def main() -> None:
    authority = load(AUTHORITY)
    placeholders = load(PLACEHOLDERS)
    stage35 = load(STAGE35)

    require(authority, {
        "schema_version": 1,
        "project_ref": PROJECT_REF,
        "stage": "STAGE36_CONTROLLED_LAUNCH_EXTERNAL_GATE_ASSESSMENT",
        "baseline_main_sha": BASELINE,
        "current_state": "ASSESSMENT_ONLY_TWO_AUTOMATIC_READY_SEVEN_EXTERNAL_OR_EVIDENCE_GATES_BLOCKED_NO_PROMOTION",
    }, "Stage36 authority")

    if set(authority.get("failure_classes", [])) != {
        "BGF-STAGE36-LAUNCH-GATE-CODE-315",
        "BGF-STAGE36-LAUNCH-EVIDENCE-SELF-ATTESTATION-316",
        "BGF-STAGE36-STAGE35-CROSS-PROMOTION-317",
        "BGF-STAGE36-BILLING-AUTHORITY-318",
    }:
        fail("Stage36 failure-class set drifted")

    require(authority.get("repo_authority", {}), {
        "stage20_migration_file": "04_backend_supabase/migrations/20260819062000_stage20_controlled_launch_admission.sql",
        "stage20_migration_git_blob_sha": STAGE20_BLOB,
        "stage20_remote_name": "stage20_controlled_launch_admission",
        "stage20_remote_version": "20260819085840",
        "external_evidence_placeholder_file": "04_backend_supabase/external_gate_evidence_placeholders.json",
        "external_evidence_placeholder_git_blob_sha": PLACEHOLDER_BLOB,
        "stage35_final_authority_file": "04_backend_supabase/stage35_alert_external_delivery_cleanup_final_reconciliation_authority.json",
        "stage35_final_authority_git_blob_sha": STAGE35_BLOB,
    }, "repository authority")

    if blob(PLACEHOLDERS) != PLACEHOLDER_BLOB:
        fail("external evidence placeholder blob drifted")
    if blob(STAGE20) != STAGE20_BLOB:
        fail("Stage20 controlled-launch migration blob drifted")
    if blob(STAGE35) != STAGE35_BLOB:
        fail("Stage35 final authority blob drifted")

    require(placeholders, {
        "schema_version": 1,
        "project_ref": PROJECT_REF,
        "template_state": "PLACEHOLDER_ONLY_NOT_ATTESTATION",
    }, "external evidence placeholders")
    rules = placeholders.get("rules", {})
    require(rules, {
        "this_file_can_mark_gate_ready": False,
        "this_file_can_hold_evidence_ref": False,
        "this_file_can_hold_evidence_digest": False,
        "promotion_authority": "dedicated_versioned_evidence_migration_after_real_external_review_or_operational_test",
    }, "placeholder rules")
    expected_external = {
        "billing_provider_credentials",
        "legal_privacy_notice",
        "legal_terms_of_use",
        "legal_role_mapping",
        "data_subject_request_channel",
        "incident_response",
        "production_deployment",
    }
    if set(placeholders.get("gates", {})) != expected_external:
        fail("external placeholder gate set drifted")
    for code, gate in placeholders.get("gates", {}).items():
        if not isinstance(gate, dict):
            fail(f"placeholder gate is not object: {code}")
        if gate.get("placeholder_only") is not True or gate.get("evidence_ref") is not None or gate.get("evidence_digest") is not None:
            fail(f"placeholder became attesting: {code}")
        if "state" in gate or "ready" in gate:
            fail(f"placeholder carries live readiness state: {code}")

    stage20_text = STAGE20.read_text(encoding="utf-8").lower()
    expected_codes = {row["gate_code"] for row in EXPECTED_MATRIX}
    for code in expected_codes:
        if f"('{code}'" not in stage20_text:
            fail(f"Stage20 mandatory gate disappeared: {code}")
    for fragment in (
        "authority_mode in ('automatic','evidence_migration','external_authorization')",
        "state = 'blocked' or (evidence_ref is not null and evidence_digest is not null)",
        "'paid_ads_auto_launch',false",
        "revoke execute on function public.get_controlled_launch_readiness() from public,anon,authenticated",
        "grant execute on function public.get_controlled_launch_readiness() to service_role",
    ):
        if fragment not in stage20_text:
            fail(f"Stage20 launch boundary drifted: {fragment}")

    remote = authority.get("fresh_remote_assessment", {})
    require(remote, {
        "source": "Supabase.execute_sql_read_only",
        "observed_at_utc": OBSERVED,
        "pricing_decisions": 1,
        "active_plan_prices": 6,
        "pricing_experiment_ready": True,
        "tracking_core_rows": 2,
        "active_asaas": 0,
        "mandatory_gate_count": 9,
        "effective_ready_gate_count": 2,
        "effective_blocking_gate_count": 7,
        "evidence_migration_gate_count": 6,
        "external_authorization_gate_count": 1,
        "remote_mutation_performed": False,
        "provider_called": False,
        "customer_data_used": False,
    }, "fresh remote assessment")

    matrix = authority.get("mandatory_gate_matrix")
    if matrix != EXPECTED_MATRIX:
        fail("mandatory gate matrix does not match fresh authoritative assessment")
    if len(matrix) != 9 or len({row.get("gate_code") for row in matrix}) != 9:
        fail("mandatory gate matrix cardinality drifted")
    ready = [row for row in matrix if row.get("effective_state") == "ready"]
    blocked = [row for row in matrix if row.get("effective_state") == "blocked"]
    if {row.get("gate_code") for row in ready} != {"tracking_core", "pricing_experiment"}:
        fail("only tracking_core and pricing_experiment may be ready in this assessment")
    if len(blocked) != 7:
        fail("seven gates must remain blocking")
    if any(row.get("has_evidence_ref") or row.get("has_evidence_digest") for row in blocked):
        fail("blocking gate unexpectedly carries evidence reference/digest")

    require(authority.get("authority_boundaries", {}), {
        "automatic_readiness_is_gate_promotion": False,
        "stage35_alert_proof_is_production_deployment_evidence_by_itself": False,
        "stage35_alert_proof_is_incident_response_evidence_by_itself": False,
        "placeholder_file_can_attest_external_evidence": False,
        "runtime_self_attestation_allowed": False,
        "stage36_evidence_migration_allowed": False,
        "stage36_remote_mutation_allowed": False,
        "stage36_provider_call_allowed": False,
        "stage36_customer_data_allowed": False,
        "paid_ads_auto_launch_allowed": False,
    }, "authority boundaries")

    require(stage35.get("gates", {}), {
        "external_delivery_proof": "PASS_IMMUTABLE",
        "synthetic_cleanup": "PASS_ZERO_RESIDUE",
        "incident_response": "DENIED",
        "production_deployment": "DENIED",
        "paid_media": "DENIED",
        "launch": "DENIED",
    }, "Stage35 immutable gate boundary")
    require(authority.get("stage35_immutable_boundary", {}), {
        "external_delivery_proof": "PASS_IMMUTABLE",
        "synthetic_cleanup": "PASS_ZERO_RESIDUE",
        "proof_reexecution_allowed": False,
        "pr117_reopen_allowed": False,
        "stage35_remote_reapply_allowed": False,
    }, "Stage35 immutable boundary receipt")

    require(authority.get("gates", {}), {
        "controlled_launch": "DENIED_7_OF_9_MANDATORY_GATES_BLOCKING",
        "billing_provider_credentials": "DENIED",
        "incident_response": "DENIED",
        "production_deployment": "DENIED",
        "paid_media": "DENIED",
        "launch": "DENIED",
    }, "Stage36 gates")

    next_sequence = authority.get("next_evidence_sequence")
    if not isinstance(next_sequence, list) or [row.get("gate_code") for row in next_sequence if isinstance(row, dict)] != [
        "billing_provider_credentials",
        "legal_terms_of_use",
        "legal_privacy_notice",
        "legal_role_mapping",
        "data_subject_request_channel",
        "incident_response",
        "production_deployment",
    ]:
        fail("next evidence sequence drifted")

    stage36_migrations = sorted(path.name for path in (BACKEND / "migrations").glob("*stage36*.sql"))
    if stage36_migrations:
        fail(f"assessment must not introduce Stage36 migration: {stage36_migrations}")
    if PROOF_TRIGGER.exists():
        fail("consumed Stage35 one-shot proof trigger entered mergeable history")

    serialized = json.dumps(authority, sort_keys=True).lower()
    for forbidden in (
        "sbp_",
        "telegram_bot_token\": \"",
        "telegram_chat_id\": \"",
        "x-fitnexus-alert-dispatch-token\": \"",
        "provider_message_id\":",
        "claim_token\": \"",
    ):
        if forbidden in serialized:
            fail("Stage36 authority appears to contain secret/provider identifier material")

    print("STAGE36_CONTROLLED_LAUNCH_EXTERNAL_GATE_ASSESSMENT=PASS")
    print(f"BASELINE_MAIN_SHA={BASELINE}")
    print(f"OBSERVED_AT_UTC={OBSERVED}")
    print("MANDATORY_GATES=9")
    print("EFFECTIVE_READY_GATES=2")
    print("EFFECTIVE_BLOCKING_GATES=7")
    print("AUTOMATIC_READY=tracking_core,pricing_experiment")
    print("ACTIVE_ASAAS=0")
    print("EXTERNAL_EVIDENCE_REFS=0")
    print("STAGE36_REMOTE_MUTATION=false")
    print("STAGE35_PROOF_REEXECUTION_ALLOWED=false")
    print("CONTROLLED_LAUNCH=DENIED")
    print("PAID_MEDIA=DENIED")


if __name__ == "__main__":
    main()
