from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage41_legal_terms_external_evidence_preparation_authority.json"
PLACEHOLDERS = BACKEND / "external_gate_evidence_placeholders.json"
STAGE20 = BACKEND / "migrations" / "20260819062000_stage20_controlled_launch_admission.sql"
STAGE40 = BACKEND / "stage40_billing_production_environment_interlock_final_authority.json"
COLLECTOR = BACKEND / "tools" / "collect_stage41_legal_terms_evidence.ps1"
REVIEWER = BACKEND / "tools" / "review_stage41_legal_terms_evidence_receipt.py"

BASELINE_MAIN = "d390dcfdc18abb19248314b1b7c131d91b0a4a72"
OBSERVED_AT = "2026-08-24T00:42:47.237278+00:00"
PLACEHOLDER_BLOB = "07e6eb3330076f3e576ed2dd2a2e385f5fa3b2db"
STAGE20_BLOB = "e26dd18eff1f4dbf099ad721963b06d6362bc3b9"
STAGE40_BLOB = "46ccb3ae5cc23d741e60a128713361a9ad7b68da"
FAILURE_CLASS = "BGF-STAGE41-LEGAL-TERMS-PREPARATION-GUARD-376"


def fail(detail: str) -> None:
    raise SystemExit(f"STAGE41_LEGAL_TERMS_EXTERNAL_EVIDENCE_PREPARATION=FAIL\nFAILURE_CLASS={FAILURE_CLASS}\nDETAIL={detail}")


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to load {path.relative_to(ROOT)}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"expected JSON object: {path.relative_to(ROOT)}")
    return value


def git_blob(path: Path) -> str:
    import hashlib
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def require(mapping: dict, expected: dict, label: str) -> None:
    if not isinstance(mapping, dict):
        fail(f"{label} must be object")
    for key, val in expected.items():
        if mapping.get(key) != val:
            fail(f"{label} drift: {key}")


def main() -> None:
    authority = load(AUTHORITY)
    placeholders = load(PLACEHOLDERS)
    stage40 = load(STAGE40)
    stage20 = STAGE20.read_text(encoding="utf-8")
    collector = COLLECTOR.read_text(encoding="utf-8")
    reviewer = REVIEWER.read_text(encoding="utf-8")

    if git_blob(PLACEHOLDERS) != PLACEHOLDER_BLOB or git_blob(STAGE20) != STAGE20_BLOB or git_blob(STAGE40) != STAGE40_BLOB:
        fail("pinned upstream source blob drift")

    require(authority, {"schema_version":1,"project_ref":"mceukeondizkwlpfxzgf","stage":"STAGE41_LEGAL_TERMS_EXTERNAL_EVIDENCE_PREPARATION","baseline_main_sha":BASELINE_MAIN,"current_state":"PREPARED_REAL_LEGAL_REVIEW_AND_STABLE_PUBLICATION_EVIDENCE_REQUIRED_NO_ATTESTATION_NO_GATE_PROMOTION"}, "authority")
    expected_classes = {
        "BGF-STAGE41-LEGAL-TERMS-SELF-ATTESTATION-368",
        "BGF-STAGE41-LEGAL-TERMS-UNSTABLE-PUBLICATION-REFERENCE-369",
        "BGF-STAGE41-LEGAL-TERMS-DIGEST-WITHOUT-ARTIFACT-370",
        "BGF-STAGE41-LEGAL-TERMS-BILLING-POLICY-REFERENCE-OMISSION-371",
        "BGF-STAGE41-LEGAL-TERMS-ACCEPTANCE-VERSIONING-EVIDENCE-OMISSION-372",
        "BGF-STAGE41-LEGAL-TERMS-PREMATURE-EVIDENCE-MIGRATION-373",
        "BGF-STAGE41-LEGAL-TERMS-RECEIPT-PERSONAL-OR-SECRET-MATERIAL-CROSSOVER-374",
    }
    if set(authority.get("failure_classes", [])) != expected_classes:
        fail("failure-class set drift")

    require(stage40, {"schema_version":1,"project_ref":"mceukeondizkwlpfxzgf","stage":"STAGE40_BILLING_PRODUCTION_ENVIRONMENT_INTERLOCK_FINAL_RECONCILIATION","current_state":"PRODUCTION_ENVIRONMENT_INTERLOCK_REMOTE_APPLIED_PROVIDER_STILL_PENDING_ZERO_EXTERNAL_EVIDENCE_BILLING_GATE_BLOCKED"}, "Stage40 upstream")
    require(stage40.get("gates", {}), {"stage40_hardening":"PASS_REMOTE_RECONCILED","controlled_launch":"DENIED","launch":"DENIED"}, "Stage40 gates")

    require(authority.get("fresh_remote_read_only_receipt", {}), {"source":"Supabase.execute_sql_read_only","observed_at_utc":OBSERVED_AT,"gate_code":"legal_terms_of_use","category":"legal","authority_mode":"evidence_migration","mandatory":True,"state":"blocked","evidence_ref":None,"evidence_digest":None,"ready_evidence_migration_count":0,"remote_mutation_performed":False}, "remote receipt")

    if placeholders.get("template_state") != "PLACEHOLDER_ONLY_NOT_ATTESTATION" or placeholders.get("rules", {}).get("this_file_can_mark_gate_ready") is not False:
        fail("external evidence placeholder became attestation authority")
    terms_placeholder = placeholders.get("gates", {}).get("legal_terms_of_use", {})
    required_terms = [
        "legal reviewer/reference",
        "approved terms version",
        "stable published terms URL",
        "approved document sha256 digest",
        "effective date",
        "billing/cancellation/refund policy reference",
        "contract acceptance/versioning evidence",
    ]
    if terms_placeholder.get("authority_mode") != "evidence_migration" or terms_placeholder.get("required_evidence") != required_terms:
        fail("legal terms placeholder evidence contract drift")
    if terms_placeholder.get("evidence_ref") is not None or terms_placeholder.get("evidence_digest") is not None:
        fail("placeholder contains live legal terms evidence")

    for fragment in (
        "('legal_terms_of_use','legal','evidence_migration',true",
        "Awaiting explicit evidence migration.",
        "grant select on private.controlled_launch_gate_evidence to service_role",
        "'legal_review_evidence_is_migration_owned',true",
        "'paid_ads_auto_launch',false",
    ):
        if fragment not in stage20:
            fail(f"Stage20 legal terms boundary missing: {fragment}")

    required_collector = (
        "I_CONFIRM_ARTIFACTS_REDACTED_AND_NO_SECRETS",
        "Get-FileHash -LiteralPath $File.FullName -Algorithm SHA256",
        "stable_published_terms_url",
        "billing_cancellation_refund_policy_digest",
        "contract_acceptance_versioning_digest",
        "raw_artifact_content_copied_to_receipt = $false",
        "artifact_path_or_filename_copied_to_receipt = $false",
        "network_call_performed = $false",
        "supabase_mutation_performed = $false",
        "legal_review_self_attested = $false",
        "gate_ready_attested = $false",
        "INDEPENDENT_REVIEW_REQUIRED_BEFORE_ANY_EVIDENCE_MIGRATION",
    )
    for fragment in required_collector:
        if fragment not in collector:
            fail(f"collector contract fragment missing: {fragment}")

    for pattern in (
        r"\bInvoke-WebRequest\b", r"\bInvoke-RestMethod\b", r"\bcurl(?:\.exe)?\b", r"\bwget(?:\.exe)?\b",
        r"\bapply_migration\b", r"\bexecute_sql\b", r"\bcontrolled_launch_gate_evidence\b", r"\bapi_key\b", r"\baccess_token\b", r"\bpassword\b",
    ):
        if re.search(pattern, collector, flags=re.IGNORECASE):
            fail(f"collector contains forbidden network/mutation/secret pattern: {pattern}")

    for fragment in (
        "PASS_STRUCTURAL_CANDIDATE_ONLY",
        "LEGAL_REVIEW_VERIFIED_BY_SCRIPT=false",
        "PUBLISHED_CONTENT_LEGAL_SUFFICIENCY_VERIFIED_BY_SCRIPT=false",
        "GATE_READY=false",
        "INDEPENDENT_SOURCE_ARTIFACT_REVIEW_REQUIRED=true",
    ):
        if fragment not in reviewer:
            fail(f"reviewer fail-closed fragment missing: {fragment}")

    require(authority.get("collector_contract", {}), {"network_calls_allowed":False,"supabase_mutation_allowed":False,"evidence_migration_creation_allowed":False,"legal_review_self_attestation_allowed":False,"raw_artifact_content_copied_to_receipt":False,"artifact_path_or_filename_copied_to_receipt":False,"personal_or_secret_material_allowed":False,"receipt_can_mark_gate_ready":False,"receipt_can_promote_controlled_launch":False}, "collector authority")
    require(authority.get("gates", {}), {"stage41_preparation":"REPO_ONLY_PENDING_CI","legal_terms_of_use":"DENIED_AWAITING_REAL_LEGAL_REVIEW_AND_STABLE_PUBLICATION_EVIDENCE","billing_provider_credentials":"DENIED_AWAITING_REAL_ASAAS_PRODUCTION_OPERATOR_EVIDENCE","controlled_launch":"DENIED","production_deployment":"DENIED","incident_response":"DENIED","paid_media":"DENIED","launch":"DENIED"}, "gates")

    if list((BACKEND / "migrations").glob("*stage41*.sql")):
        fail("Stage41 preparation must not create an evidence migration")
    serialized = json.dumps(authority, sort_keys=True).lower()
    for key in ('"api_key"','"access_token"','"password"','"webhook_token"','"secret_value"'):
        if key in serialized:
            fail(f"secret-bearing key found: {key}")

    print("STAGE41_LEGAL_TERMS_EXTERNAL_EVIDENCE_PREPARATION=PASS")
    print(f"BASELINE_MAIN_SHA={BASELINE_MAIN}")
    print("LEGAL_TERMS_GATE=BLOCKED")
    print("REMOTE_MUTATION=false")
    print("LEGAL_SELF_ATTESTATION=false")
    print("EVIDENCE_MIGRATION_CREATED=false")
    print("INDEPENDENT_REAL_LEGAL_REVIEW_REQUIRED=true")


if __name__ == "__main__":
    main()
