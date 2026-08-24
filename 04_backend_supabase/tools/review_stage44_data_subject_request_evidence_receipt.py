from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse

FAILURE_CLASS = "BGF-STAGE44-DSR-RECEIPT-STRUCTURAL-REVIEW-406"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE44_DATA_SUBJECT_REQUEST_RECEIPT_REVIEW=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\n"
        f"DETAIL={detail}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()
    try:
        receipt = json.loads(args.receipt.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"receipt unreadable: {type(exc).__name__}")
    if not isinstance(receipt, dict):
        fail("receipt must be a JSON object")

    expected = {
        "schema_version": 1,
        "stage": "STAGE44_DATA_SUBJECT_REQUEST_EXTERNAL_EVIDENCE_PREPARATION",
        "output_kind": "DIGEST_ONLY_DATA_SUBJECT_REQUEST_EVIDENCE_INTAKE_CANDIDATE",
        "gate_code": "data_subject_request_channel",
        "candidate_state": "AWAITING_INDEPENDENT_REVIEW_NOT_ATTESTATION",
        "synthetic_or_non_customer_fixture_confirmation": "CONFIRMED",
        "redaction_confirmation": "CONFIRMED",
        "raw_artifact_content_copied_to_receipt": False,
        "artifact_path_or_filename_copied_to_receipt": False,
        "personal_or_secret_material_collected": False,
        "real_customer_data_used_in_test_receipts": False,
        "network_call_performed": False,
        "supabase_mutation_performed": False,
        "evidence_migration_created": False,
        "operational_or_legal_self_attested": False,
        "gate_ready_attested": False,
        "controlled_launch_promoted": False,
        "next_action": "INDEPENDENT_REVIEW_REQUIRED_BEFORE_ANY_EVIDENCE_MIGRATION",
    }
    for key, value in expected.items():
        if receipt.get(key) != value:
            fail(f"receipt invariant drift: {key}")

    for key in (
        "owner_and_backup_owner_assignment_digest",
        "identity_verification_procedure_digest",
        "tenant_scoped_access_export_test_receipt_digest",
        "correction_workflow_test_receipt_digest",
        "deletion_anonymization_blocking_retention_hold_test_receipt_digest",
        "controller_operator_handoff_procedure_digest",
        "reviewed_response_time_policy_digest",
        "tabletop_request_receipt_digest",
    ):
        if not SHA256_RE.fullmatch(str(receipt.get(key, ""))):
            fail(f"invalid SHA-256 digest: {key}")

    route = str(receipt.get("stable_published_titular_contact_route", "")).strip()
    parsed = urlparse(route)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not host:
        fail("published data-subject request route must be absolute HTTPS")
    if host in {"localhost", "127.0.0.1", "::1", "example.com", "www.example.com"}:
        fail("published data-subject request route is placeholder/local")
    if re.search(r"(^|\.)(test|staging|preview|dev)(\.|$)", host):
        fail("published data-subject request route appears non-production")
    if re.search(r"example|placeholder|localhost|preview", route, re.IGNORECASE):
        fail("published data-subject request route contains placeholder marker")

    serialized = json.dumps(receipt, sort_keys=True).lower()
    for forbidden in (
        '"api_key"',
        '"access_token"',
        '"password"',
        '"webhook_token"',
        '"secret_value"',
        '"cpf"',
        '"student_name"',
        '"customer_email"',
        '"customer_name"',
    ):
        if forbidden in serialized:
            fail(f"secret/personal-bearing key present: {forbidden}")

    print("STAGE44_DATA_SUBJECT_REQUEST_RECEIPT_REVIEW=PASS_STRUCTURAL_CANDIDATE_ONLY")
    print("PUBLISHED_CHANNEL_OPERATIONALLY_VERIFIED_BY_SCRIPT=false")
    print("IDENTITY_VERIFICATION_LEGAL_SUFFICIENCY_VERIFIED_BY_SCRIPT=false")
    print("TENANT_SCOPED_ACCESS_EXPORT_VERIFIED_BY_SCRIPT=false")
    print("DELETION_RETENTION_HOLD_LEGAL_CONCLUSION_VERIFIED_BY_SCRIPT=false")
    print("RESPONSE_TIME_POLICY_LEGAL_CONCLUSION_VERIFIED_BY_SCRIPT=false")
    print("TABLETOP_OPERATIONAL_SUFFICIENCY_VERIFIED_BY_SCRIPT=false")
    print("REAL_CUSTOMER_DATA_USED=false")
    print("GATE_READY=false")
    print("INDEPENDENT_SOURCE_ARTIFACT_REVIEW_REQUIRED=true")


if __name__ == "__main__":
    main()
