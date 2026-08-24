from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

FAILURE_CLASS = "BGF-STAGE43-LEGAL-ROLE-MAPPING-RECEIPT-STRUCTURAL-REVIEW-394"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE43_LEGAL_ROLE_MAPPING_RECEIPT_REVIEW=FAIL\n"
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
        "stage": "STAGE43_LEGAL_ROLE_MAPPING_EXTERNAL_EVIDENCE_PREPARATION",
        "output_kind": "DIGEST_ONLY_LEGAL_ROLE_MAPPING_EVIDENCE_INTAKE_CANDIDATE",
        "gate_code": "legal_role_mapping",
        "candidate_state": "AWAITING_INDEPENDENT_REVIEW_NOT_ATTESTATION",
        "redaction_confirmation": "CONFIRMED",
        "raw_artifact_content_copied_to_receipt": False,
        "artifact_path_or_filename_copied_to_receipt": False,
        "personal_or_secret_material_collected": False,
        "network_call_performed": False,
        "supabase_mutation_performed": False,
        "evidence_migration_created": False,
        "legal_or_privacy_review_self_attested": False,
        "gate_ready_attested": False,
        "controlled_launch_promoted": False,
        "next_action": "INDEPENDENT_REVIEW_REQUIRED_BEFORE_ANY_EVIDENCE_MIGRATION",
    }
    for key, value in expected.items():
        if receipt.get(key) != value:
            fail(f"receipt invariant drift: {key}")

    for key in (
        "legal_privacy_role_review_artifact_digest",
        "approved_processing_role_matrix_digest",
        "purpose_to_role_mapping_digest",
        "purpose_to_legal_basis_review_digest",
        "sensitive_data_treatment_review_digest",
        "processor_subprocessor_map_digest",
        "international_transfer_mechanism_map_digest",
    ):
        if not SHA256_RE.fullmatch(str(receipt.get(key, ""))):
            fail(f"invalid SHA-256 digest: {key}")

    reviewer = str(receipt.get("legal_reviewer_reference", "")).strip()
    version = str(receipt.get("approved_processing_role_matrix_version", "")).strip()
    if not reviewer or len(reviewer) > 240:
        fail("legal/privacy reviewer reference missing or malformed")
    if not version or len(version) > 120:
        fail("approved processing-role matrix version missing or malformed")
    if receipt.get("international_transfer_applicability") not in {"APPLICABLE", "NOT_APPLICABLE_REVIEWED"}:
        fail("international-transfer applicability is not explicitly reviewed")

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
    ):
        if forbidden in serialized:
            fail(f"secret/personal-bearing key present: {forbidden}")

    print("STAGE43_LEGAL_ROLE_MAPPING_RECEIPT_REVIEW=PASS_STRUCTURAL_CANDIDATE_ONLY")
    print("LEGAL_PRIVACY_REVIEW_VERIFIED_BY_SCRIPT=false")
    print("PROCESSING_ROLE_MATRIX_LEGAL_SUFFICIENCY_VERIFIED_BY_SCRIPT=false")
    print("LEGAL_BASIS_CONCLUSION_VERIFIED_BY_SCRIPT=false")
    print("SENSITIVE_DATA_TREATMENT_CONCLUSION_VERIFIED_BY_SCRIPT=false")
    print("TRANSFER_MECHANISM_LEGAL_CONCLUSION_VERIFIED_BY_SCRIPT=false")
    print("GATE_READY=false")
    print("INDEPENDENT_SOURCE_ARTIFACT_REVIEW_REQUIRED=true")


if __name__ == "__main__":
    main()
