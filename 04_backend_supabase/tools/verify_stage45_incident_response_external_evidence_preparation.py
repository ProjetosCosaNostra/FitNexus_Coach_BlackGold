from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage45_incident_response_external_evidence_preparation_authority.json"
UPSTREAM = BACKEND / "stage44_data_subject_request_external_evidence_preparation_authority.json"
PLACEHOLDERS = BACKEND / "external_gate_evidence_placeholders.json"
STAGE20 = BACKEND / "migrations" / "20260819062000_stage20_controlled_launch_admission.sql"
COLLECTOR = BACKEND / "tools" / "collect_stage45_incident_response_evidence.ps1"
REVIEWER = BACKEND / "tools" / "review_stage45_incident_response_evidence_receipt.py"

BASELINE = "7b3fb946de8eb2f1356d795d2cc4031c95b7ec9a"
OBSERVED = "2026-08-24T07:53:52.531479+00:00"
UPSTREAM_BLOB = "53321a9af19ba3423fca44191bf000815eb617d5"
PLACEHOLDER_BLOB = "07e6eb3330076f3e576ed2dd2a2e385f5fa3b2db"
STAGE20_BLOB = "e26dd18eff1f4dbf099ad721963b06d6362bc3b9"
FAILURE_CLASS = "BGF-STAGE45-INCIDENT-RESPONSE-PREPARATION-GUARD-419"


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE45_INCIDENT_RESPONSE_EXTERNAL_EVIDENCE_PREPARATION=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\n"
        f"DETAIL={detail}"
    )


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to load {path.relative_to(ROOT)}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"expected object: {path.relative_to(ROOT)}")
    return value


def blob(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def require(mapping: dict, expected: dict, label: str) -> None:
    if not isinstance(mapping, dict):
        fail(f"{label} must be object")
    for key, value in expected.items():
        if mapping.get(key) != value:
            fail(f"{label} drift: {key}")


def main() -> None:
    authority = load(AUTHORITY)
    upstream = load(UPSTREAM)
    placeholders = load(PLACEHOLDERS)
    stage20 = STAGE20.read_text(encoding="utf-8")
    collector = COLLECTOR.read_text(encoding="utf-8")
    reviewer = REVIEWER.read_text(encoding="utf-8")

    if blob(UPSTREAM) != UPSTREAM_BLOB or blob(PLACEHOLDERS) != PLACEHOLDER_BLOB or blob(STAGE20) != STAGE20_BLOB:
        fail("pinned upstream blob drift")

    require(
        authority,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "stage": "STAGE45_INCIDENT_RESPONSE_EXTERNAL_EVIDENCE_PREPARATION",
            "baseline_main_sha": BASELINE,
            "current_state": "PREPARED_REAL_INCIDENT_RESPONSE_GOVERNANCE_AND_CONTROLLED_TABLETOP_EVIDENCE_REQUIRED_NO_ATTESTATION_NO_GATE_PROMOTION",
        },
        "authority",
    )
    require(
        upstream,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "stage": "STAGE44_DATA_SUBJECT_REQUEST_EXTERNAL_EVIDENCE_PREPARATION",
            "current_state": "PREPARED_REAL_DATA_SUBJECT_REQUEST_CHANNEL_AND_CONTROLLED_OPERATIONAL_EVIDENCE_REQUIRED_NO_ATTESTATION_NO_GATE_PROMOTION",
        },
        "Stage44 upstream",
    )
    require(
        authority.get("fresh_remote_read_only_receipt", {}),
        {
            "source": "Supabase.execute_sql_read_only",
            "observed_at_utc": OBSERVED,
            "gate_code": "incident_response",
            "category": "security",
            "authority_mode": "evidence_migration",
            "mandatory": True,
            "state": "blocked",
            "evidence_ref": None,
            "evidence_digest": None,
            "ready_evidence_migration_count": 0,
            "remote_mutation_performed": False,
        },
        "remote receipt",
    )

    incident = placeholders.get("gates", {}).get("incident_response", {})
    expected_required = [
        "incident commander/privacy owner/technical owner assignment",
        "risk classification matrix",
        "operator-to-controller handoff procedure",
        "ANPD/data-subject communication decision procedure",
        "incident registry retention control",
        "cross-tenant exposure tabletop receipt",
        "credential compromise tabletop receipt",
        "potentially sensitive student-data tabletop receipt",
        "final drill/postmortem digest",
    ]
    if incident.get("authority_mode") != "evidence_migration" or incident.get("required_evidence") != expected_required:
        fail("incident response placeholder contract drift")
    if incident.get("evidence_ref") is not None or incident.get("evidence_digest") is not None:
        fail("incident response placeholder contains live evidence")

    for fragment in (
        "('incident_response','security','evidence_migration',true",
        "Awaiting explicit evidence migration.",
        "'legal_review_evidence_is_migration_owned',true",
        "'paid_ads_auto_launch',false",
    ):
        if fragment not in stage20:
            fail(f"Stage20 incident response boundary missing: {fragment}")

    required_collector = (
        "I_CONFIRM_TABLETOPS_USE_SYNTHETIC_OR_NON_CUSTOMER_FIXTURES",
        "I_CONFIRM_ARTIFACTS_REDACTED_AND_NO_SECRETS",
        "Get-FileHash -LiteralPath $File.FullName -Algorithm SHA256",
        "incident_commander_privacy_owner_technical_owner_assignment_digest",
        "risk_classification_matrix_digest",
        "operator_to_controller_handoff_procedure_digest",
        "anpd_data_subject_communication_decision_procedure_digest",
        "incident_registry_retention_control_digest",
        "cross_tenant_exposure_tabletop_receipt_digest",
        "credential_compromise_tabletop_receipt_digest",
        "potentially_sensitive_student_data_tabletop_receipt_digest",
        "final_drill_postmortem_digest",
        "real_customer_data_used_in_tabletops = $false",
        "live_incident_required = $false",
        "network_call_performed = $false",
        "supabase_mutation_performed = $false",
        "operational_or_legal_self_attested = $false",
        "gate_ready_attested = $false",
        "INDEPENDENT_REVIEW_REQUIRED_BEFORE_ANY_EVIDENCE_MIGRATION",
    )
    for fragment in required_collector:
        if fragment not in collector:
            fail(f"collector fragment missing: {fragment}")

    for pattern in (
        r"\bInvoke-WebRequest\b",
        r"\bInvoke-RestMethod\b",
        r"\bcurl(?:\.exe)?\b",
        r"\bwget(?:\.exe)?\b",
        r"\bapply_migration\b",
        r"\bexecute_sql\b",
        r"\bcontrolled_launch_gate_evidence\b",
        r"\bapi_key\b",
        r"\baccess_token\b",
        r"\bpassword\b",
    ):
        if re.search(pattern, collector, flags=re.IGNORECASE):
            fail(f"forbidden collector pattern: {pattern}")

    for fragment in (
        "PASS_STRUCTURAL_CANDIDATE_ONLY",
        "INCIDENT_OWNERSHIP_OPERATIONALLY_VERIFIED_BY_SCRIPT=false",
        "RISK_CLASSIFICATION_LEGAL_SUFFICIENCY_VERIFIED_BY_SCRIPT=false",
        "ANPD_DATA_SUBJECT_NOTIFICATION_CONCLUSION_VERIFIED_BY_SCRIPT=false",
        "TABLETOP_OPERATIONAL_SUFFICIENCY_VERIFIED_BY_SCRIPT=false",
        "POSTMORTEM_REMEDIATION_COMPLETENESS_VERIFIED_BY_SCRIPT=false",
        "REAL_CUSTOMER_DATA_USED=false",
        "LIVE_INCIDENT_REQUIRED=false",
        "GATE_READY=false",
    ):
        if fragment not in reviewer:
            fail(f"reviewer fail-closed fragment missing: {fragment}")

    require(
        authority.get("collector_contract", {}),
        {
            "network_calls_allowed": False,
            "supabase_mutation_allowed": False,
            "evidence_migration_creation_allowed": False,
            "operational_or_legal_self_attestation_allowed": False,
            "raw_artifact_content_copied_to_receipt": False,
            "artifact_path_or_filename_copied_to_receipt": False,
            "personal_or_secret_material_allowed": False,
            "real_customer_data_allowed_in_tabletop_receipts": False,
            "live_incident_required_for_preparation": False,
            "receipt_can_mark_gate_ready": False,
            "receipt_can_promote_controlled_launch": False,
        },
        "collector contract",
    )
    require(
        authority.get("gates", {}),
        {
            "stage45_preparation": "REPO_ONLY_PENDING_CI",
            "incident_response": "DENIED_AWAITING_REAL_GOVERNANCE_AND_CONTROLLED_TABLETOP_EVIDENCE",
            "data_subject_request_channel": "DENIED_AWAITING_REAL_OPERATIONAL_AND_CONTROLLED_SYNTHETIC_EVIDENCE",
            "legal_role_mapping": "DENIED_AWAITING_REAL_PROCESSING_ROLE_AND_LEGAL_BASIS_REVIEW_EVIDENCE",
            "legal_privacy_notice": "DENIED_AWAITING_REAL_PRIVACY_LEGAL_REVIEW_AND_STABLE_PUBLICATION_EVIDENCE",
            "legal_terms_of_use": "DENIED_AWAITING_REAL_LEGAL_REVIEW_AND_STABLE_PUBLICATION_EVIDENCE",
            "billing_provider_credentials": "DENIED_AWAITING_REAL_ASAAS_PRODUCTION_OPERATOR_EVIDENCE",
            "controlled_launch": "DENIED",
            "production_deployment": "DENIED",
            "paid_media": "DENIED",
            "launch": "DENIED",
        },
        "gates",
    )

    if list((BACKEND / "migrations").glob("*stage45*.sql")):
        fail("Stage45 preparation must not create evidence migration")

    print("STAGE45_INCIDENT_RESPONSE_EXTERNAL_EVIDENCE_PREPARATION=PASS")
    print("INCIDENT_RESPONSE_GATE=BLOCKED")
    print("REMOTE_MUTATION=false")
    print("REAL_CUSTOMER_DATA_USED=false")
    print("LIVE_INCIDENT_REQUIRED=false")
    print("SELF_ATTESTATION=false")
    print("INDEPENDENT_REAL_REVIEW_REQUIRED=true")


if __name__ == "__main__":
    main()
