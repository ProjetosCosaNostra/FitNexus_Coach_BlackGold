from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage43_legal_role_mapping_external_evidence_preparation_authority.json"
UPSTREAM = BACKEND / "stage42_privacy_notice_external_evidence_preparation_authority.json"
PLACEHOLDERS = BACKEND / "external_gate_evidence_placeholders.json"
STAGE20 = BACKEND / "migrations" / "20260819062000_stage20_controlled_launch_admission.sql"
COLLECTOR = BACKEND / "tools" / "collect_stage43_legal_role_mapping_evidence.ps1"
REVIEWER = BACKEND / "tools" / "review_stage43_legal_role_mapping_evidence_receipt.py"

BASELINE = "4ca2b02b79851937209ee3482c5f52bc4323c375"
OBSERVED = "2026-08-24T07:42:27.979055+00:00"
UPSTREAM_BLOB = "3ee0558a54e1a05a3331797275c243a0c1078021"
PLACEHOLDER_BLOB = "07e6eb3330076f3e576ed2dd2a2e385f5fa3b2db"
STAGE20_BLOB = "e26dd18eff1f4dbf099ad721963b06d6362bc3b9"
FAILURE_CLASS = "BGF-STAGE43-LEGAL-ROLE-MAPPING-PREPARATION-GUARD-395"


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE43_LEGAL_ROLE_MAPPING_EXTERNAL_EVIDENCE_PREPARATION=FAIL\n"
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
            "stage": "STAGE43_LEGAL_ROLE_MAPPING_EXTERNAL_EVIDENCE_PREPARATION",
            "baseline_main_sha": BASELINE,
            "current_state": "PREPARED_REAL_PROCESSING_ROLE_AND_LEGAL_BASIS_REVIEW_EVIDENCE_REQUIRED_NO_ATTESTATION_NO_GATE_PROMOTION",
        },
        "authority",
    )
    require(
        upstream,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "stage": "STAGE42_PRIVACY_NOTICE_EXTERNAL_EVIDENCE_PREPARATION",
            "current_state": "PREPARED_REAL_PRIVACY_LEGAL_REVIEW_AND_STABLE_PUBLICATION_EVIDENCE_REQUIRED_NO_ATTESTATION_NO_GATE_PROMOTION",
        },
        "Stage42 upstream",
    )
    require(
        authority.get("fresh_remote_read_only_receipt", {}),
        {
            "source": "Supabase.execute_sql_read_only",
            "observed_at_utc": OBSERVED,
            "gate_code": "legal_role_mapping",
            "category": "privacy",
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

    role_mapping = placeholders.get("gates", {}).get("legal_role_mapping", {})
    expected_required = [
        "legal reviewer/reference",
        "approved processing-role matrix version",
        "purpose-to-role mapping",
        "purpose-to-legal-basis review",
        "sensitive-data treatment review",
        "processor/subprocessor map",
        "international-transfer mechanism map when applicable",
        "approved matrix sha256 digest",
    ]
    if role_mapping.get("authority_mode") != "evidence_migration" or role_mapping.get("required_evidence") != expected_required:
        fail("legal role mapping placeholder contract drift")
    if role_mapping.get("evidence_ref") is not None or role_mapping.get("evidence_digest") is not None:
        fail("legal role mapping placeholder contains live evidence")

    for fragment in (
        "('legal_role_mapping','privacy','evidence_migration',true",
        "Awaiting explicit evidence migration.",
        "'legal_review_evidence_is_migration_owned',true",
        "'paid_ads_auto_launch',false",
    ):
        if fragment not in stage20:
            fail(f"Stage20 legal role mapping boundary missing: {fragment}")

    required_collector = (
        "I_CONFIRM_ARTIFACTS_REDACTED_AND_NO_SECRETS",
        "APPLICABLE','NOT_APPLICABLE_REVIEWED",
        "Get-FileHash -LiteralPath $File.FullName -Algorithm SHA256",
        "approved_processing_role_matrix_digest",
        "purpose_to_role_mapping_digest",
        "purpose_to_legal_basis_review_digest",
        "sensitive_data_treatment_review_digest",
        "processor_subprocessor_map_digest",
        "international_transfer_mechanism_map_digest",
        "network_call_performed = $false",
        "supabase_mutation_performed = $false",
        "legal_or_privacy_review_self_attested = $false",
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
        "LEGAL_PRIVACY_REVIEW_VERIFIED_BY_SCRIPT=false",
        "PROCESSING_ROLE_MATRIX_LEGAL_SUFFICIENCY_VERIFIED_BY_SCRIPT=false",
        "LEGAL_BASIS_CONCLUSION_VERIFIED_BY_SCRIPT=false",
        "SENSITIVE_DATA_TREATMENT_CONCLUSION_VERIFIED_BY_SCRIPT=false",
        "TRANSFER_MECHANISM_LEGAL_CONCLUSION_VERIFIED_BY_SCRIPT=false",
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
            "legal_or_privacy_review_self_attestation_allowed": False,
            "raw_artifact_content_copied_to_receipt": False,
            "artifact_path_or_filename_copied_to_receipt": False,
            "personal_or_secret_material_allowed": False,
            "receipt_can_mark_gate_ready": False,
            "receipt_can_promote_controlled_launch": False,
        },
        "collector contract",
    )
    require(
        authority.get("gates", {}),
        {
            "stage43_preparation": "REPO_ONLY_PENDING_CI",
            "legal_role_mapping": "DENIED_AWAITING_REAL_PROCESSING_ROLE_AND_LEGAL_BASIS_REVIEW_EVIDENCE",
            "legal_privacy_notice": "DENIED_AWAITING_REAL_PRIVACY_LEGAL_REVIEW_AND_STABLE_PUBLICATION_EVIDENCE",
            "legal_terms_of_use": "DENIED_AWAITING_REAL_LEGAL_REVIEW_AND_STABLE_PUBLICATION_EVIDENCE",
            "billing_provider_credentials": "DENIED_AWAITING_REAL_ASAAS_PRODUCTION_OPERATOR_EVIDENCE",
            "controlled_launch": "DENIED",
            "production_deployment": "DENIED",
            "incident_response": "DENIED",
            "paid_media": "DENIED",
            "launch": "DENIED",
        },
        "gates",
    )

    if list((BACKEND / "migrations").glob("*stage43*.sql")):
        fail("Stage43 preparation must not create evidence migration")

    print("STAGE43_LEGAL_ROLE_MAPPING_EXTERNAL_EVIDENCE_PREPARATION=PASS")
    print("LEGAL_ROLE_MAPPING_GATE=BLOCKED")
    print("REMOTE_MUTATION=false")
    print("LEGAL_PRIVACY_SELF_ATTESTATION=false")
    print("INDEPENDENT_REAL_REVIEW_REQUIRED=true")


if __name__ == "__main__":
    main()
