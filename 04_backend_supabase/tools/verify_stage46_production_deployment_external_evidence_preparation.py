from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage46_production_deployment_external_evidence_preparation_authority.json"
UPSTREAM = BACKEND / "stage45_incident_response_external_evidence_preparation_authority.json"
PLACEHOLDERS = BACKEND / "external_gate_evidence_placeholders.json"
STAGE20 = BACKEND / "migrations" / "20260819062000_stage20_controlled_launch_admission.sql"
COLLECTOR = BACKEND / "tools" / "collect_stage46_production_deployment_evidence.ps1"
REVIEWER = BACKEND / "tools" / "review_stage46_production_deployment_evidence_receipt.py"

BASELINE = "c6cb7ef60b814fe5f8d43d49f656681b08d3b0d4"
OBSERVED = "2026-08-24T07:59:41.047277+00:00"
UPSTREAM_BLOB = "d5d32990e8ef7a3c4f13dc63e2088ea28e471f12"
PLACEHOLDER_BLOB = "07e6eb3330076f3e576ed2dd2a2e385f5fa3b2db"
STAGE20_BLOB = "e26dd18eff1f4dbf099ad721963b06d6362bc3b9"
FAILURE_CLASS = "BGF-STAGE46-PRODUCTION-DEPLOYMENT-PREPARATION-GUARD-432"


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE46_PRODUCTION_DEPLOYMENT_EXTERNAL_EVIDENCE_PREPARATION=FAIL\n"
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
            "stage": "STAGE46_PRODUCTION_DEPLOYMENT_EXTERNAL_EVIDENCE_PREPARATION",
            "baseline_main_sha": BASELINE,
            "current_state": "PREPARED_REAL_PRODUCTION_RELEASE_AND_OPERATIONS_EVIDENCE_REQUIRED_NO_DEPLOYMENT_NO_ATTESTATION_NO_GATE_PROMOTION",
        },
        "authority",
    )
    require(
        upstream,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "stage": "STAGE45_INCIDENT_RESPONSE_EXTERNAL_EVIDENCE_PREPARATION",
            "current_state": "PREPARED_REAL_INCIDENT_RESPONSE_GOVERNANCE_AND_CONTROLLED_TABLETOP_EVIDENCE_REQUIRED_NO_ATTESTATION_NO_GATE_PROMOTION",
        },
        "Stage45 upstream",
    )
    require(
        authority.get("fresh_remote_read_only_receipt", {}),
        {
            "source": "Supabase.execute_sql_read_only",
            "observed_at_utc": OBSERVED,
            "gate_code": "production_deployment",
            "category": "deployment",
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

    deployment = placeholders.get("gates", {}).get("production_deployment", {})
    expected_required = [
        "stable production domain",
        "TLS evidence",
        "environment configuration receipt without secrets",
        "release commit sha",
        "production smoke-test receipt",
        "rollback test receipt",
        "monitoring/alerting readiness receipt",
        "backup/restore readiness reference",
        "release evidence digest",
    ]
    if deployment.get("authority_mode") != "evidence_migration" or deployment.get("required_evidence") != expected_required:
        fail("production deployment placeholder contract drift")
    if deployment.get("evidence_ref") is not None or deployment.get("evidence_digest") is not None:
        fail("production deployment placeholder contains live evidence")

    for fragment in (
        "('production_deployment','deployment','evidence_migration',true",
        "Awaiting explicit evidence migration.",
        "'legal_review_evidence_is_migration_owned',true",
        "'paid_ads_auto_launch',false",
    ):
        if fragment not in stage20:
            fail(f"Stage20 production deployment boundary missing: {fragment}")

    required_collector = (
        "I_CONFIRM_ENVIRONMENT_RECEIPT_AND_ARTIFACTS_REDACTED_NO_SECRET_VALUES",
        "I_CONFIRM_MONITORING_ALERTING_EVIDENCE_IS_NOT_STAGE35_ALERT_PROOF_ALONE",
        "Get-FileHash -LiteralPath $File.FullName -Algorithm SHA256",
        "stable_production_domain",
        "tls_evidence_digest",
        "environment_configuration_receipt_digest",
        "release_commit_sha",
        "production_smoke_test_receipt_digest",
        "rollback_test_receipt_digest",
        "monitoring_alerting_readiness_receipt_digest",
        "backup_restore_readiness_reference_digest",
        "release_evidence_manifest_digest",
        "secret_values_collected = $false",
        "deployment_action_performed = $false",
        "network_call_performed = $false",
        "supabase_mutation_performed = $false",
        "operations_self_attested = $false",
        "stage35_alert_proof_alone_used_for_monitoring_alerting = $false",
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
        r"\bsupabase\s+functions\s+deploy\b",
        r"\bvercel\b",
        r"\bnetlify\b",
        r"\bapi_key\b",
        r"\baccess_token\b",
        r"\bpassword\b",
        r"\bservice_role_key\b",
    ):
        if re.search(pattern, collector, flags=re.IGNORECASE):
            fail(f"forbidden collector pattern: {pattern}")

    for fragment in (
        "PASS_STRUCTURAL_CANDIDATE_ONLY",
        "PRODUCTION_DOMAIN_LIVE_VERIFIED_BY_SCRIPT=false",
        "TLS_LIVE_VERIFIED_BY_SCRIPT=false",
        "ENVIRONMENT_SECRET_ABSENCE_IN_SOURCE_ARTIFACT_VERIFIED_BY_SCRIPT=false",
        "RELEASE_SHA_DEPLOYMENT_BINDING_VERIFIED_BY_SCRIPT=false",
        "PRODUCTION_SMOKE_OPERATIONALLY_VERIFIED_BY_SCRIPT=false",
        "ROLLBACK_OPERATIONALLY_VERIFIED_BY_SCRIPT=false",
        "MONITORING_ALERTING_COMPLETENESS_VERIFIED_BY_SCRIPT=false",
        "BACKUP_RESTORE_OPERATIONALLY_VERIFIED_BY_SCRIPT=false",
        "STAGE35_ALERT_PROOF_ALONE_SUFFICIENT=false",
        "DEPLOYMENT_ACTION_PERFORMED=false",
        "GATE_READY=false",
    ):
        if fragment not in reviewer:
            fail(f"reviewer fail-closed fragment missing: {fragment}")

    require(
        authority.get("collector_contract", {}),
        {
            "network_calls_allowed": False,
            "supabase_mutation_allowed": False,
            "deployment_action_allowed": False,
            "evidence_migration_creation_allowed": False,
            "operations_self_attestation_allowed": False,
            "raw_artifact_content_copied_to_receipt": False,
            "artifact_path_or_filename_copied_to_receipt": False,
            "secret_values_allowed": False,
            "stage35_alert_proof_alone_can_satisfy_monitoring_alerting": False,
            "receipt_can_mark_gate_ready": False,
            "receipt_can_promote_controlled_launch": False,
        },
        "collector contract",
    )
    require(
        authority.get("gates", {}),
        {
            "stage46_preparation": "REPO_ONLY_PENDING_CI",
            "production_deployment": "DENIED_AWAITING_REAL_PRODUCTION_RELEASE_AND_OPERATIONS_EVIDENCE",
            "incident_response": "DENIED_AWAITING_REAL_GOVERNANCE_AND_CONTROLLED_TABLETOP_EVIDENCE",
            "data_subject_request_channel": "DENIED_AWAITING_REAL_OPERATIONAL_AND_CONTROLLED_SYNTHETIC_EVIDENCE",
            "legal_role_mapping": "DENIED_AWAITING_REAL_PROCESSING_ROLE_AND_LEGAL_BASIS_REVIEW_EVIDENCE",
            "legal_privacy_notice": "DENIED_AWAITING_REAL_PRIVACY_LEGAL_REVIEW_AND_STABLE_PUBLICATION_EVIDENCE",
            "legal_terms_of_use": "DENIED_AWAITING_REAL_LEGAL_REVIEW_AND_STABLE_PUBLICATION_EVIDENCE",
            "billing_provider_credentials": "DENIED_AWAITING_REAL_ASAAS_PRODUCTION_OPERATOR_EVIDENCE",
            "controlled_launch": "DENIED",
            "paid_media": "DENIED",
            "launch": "DENIED",
        },
        "gates",
    )

    if list((BACKEND / "migrations").glob("*stage46*.sql")):
        fail("Stage46 preparation must not create evidence migration")

    print("STAGE46_PRODUCTION_DEPLOYMENT_EXTERNAL_EVIDENCE_PREPARATION=PASS")
    print("PRODUCTION_DEPLOYMENT_GATE=BLOCKED")
    print("REMOTE_MUTATION=false")
    print("DEPLOYMENT_ACTION=false")
    print("SECRET_VALUES_COLLECTED=false")
    print("STAGE35_ALERT_PROOF_ALONE_SUFFICIENT=false")
    print("SELF_ATTESTATION=false")
    print("INDEPENDENT_REAL_REVIEW_REQUIRED=true")


if __name__ == "__main__":
    main()
