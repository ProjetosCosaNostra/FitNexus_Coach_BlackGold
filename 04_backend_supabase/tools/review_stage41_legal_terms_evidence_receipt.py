from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse

FAILURE_CLASS = "BGF-STAGE41-LEGAL-TERMS-RECEIPT-STRUCTURAL-REVIEW-375"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE41_LEGAL_TERMS_RECEIPT_REVIEW=FAIL\n"
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
        "stage": "STAGE41_LEGAL_TERMS_EXTERNAL_EVIDENCE_PREPARATION",
        "output_kind": "DIGEST_ONLY_LEGAL_TERMS_EVIDENCE_INTAKE_CANDIDATE",
        "gate_code": "legal_terms_of_use",
        "candidate_state": "AWAITING_INDEPENDENT_REVIEW_NOT_ATTESTATION",
        "redaction_confirmation": "CONFIRMED",
        "raw_artifact_content_copied_to_receipt": False,
        "artifact_path_or_filename_copied_to_receipt": False,
        "personal_or_secret_material_collected": False,
        "network_call_performed": False,
        "supabase_mutation_performed": False,
        "evidence_migration_created": False,
        "legal_review_self_attested": False,
        "gate_ready_attested": False,
        "controlled_launch_promoted": False,
        "next_action": "INDEPENDENT_REVIEW_REQUIRED_BEFORE_ANY_EVIDENCE_MIGRATION",
    }
    for key, value in expected.items():
        if receipt.get(key) != value:
            fail(f"receipt invariant drift: {key}")

    for key in (
        "legal_review_artifact_digest",
        "approved_document_sha256_digest",
        "billing_cancellation_refund_policy_digest",
        "contract_acceptance_versioning_digest",
    ):
        if not SHA256_RE.fullmatch(str(receipt.get(key, ""))):
            fail(f"invalid SHA-256 digest: {key}")

    reviewer = str(receipt.get("legal_reviewer_reference", "")).strip()
    version = str(receipt.get("approved_terms_version", "")).strip()
    effective = str(receipt.get("effective_date", "")).strip()
    if not reviewer or len(reviewer) > 240:
        fail("legal reviewer/reference missing or malformed")
    if not version or len(version) > 120:
        fail("approved terms version missing or malformed")
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", effective) is None:
        fail("effective date must be YYYY-MM-DD")

    url = str(receipt.get("stable_published_terms_url", "")).strip()
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not host:
        fail("published terms URL must be absolute HTTPS")
    forbidden_hosts = {"localhost", "127.0.0.1", "::1", "example.com", "www.example.com"}
    if host in forbidden_hosts or re.search(r"(^|\.)(test|staging|preview|dev)(\.|$)", host):
        fail("published terms URL is not production-stable")
    if re.search(r"example|placeholder|localhost|preview", url, re.IGNORECASE):
        fail("published terms URL contains placeholder marker")

    serialized = json.dumps(receipt, sort_keys=True).lower()
    for forbidden in ('"api_key"', '"access_token"', '"password"', '"webhook_token"', '"secret_value"'):
        if forbidden in serialized:
            fail(f"secret-bearing key present: {forbidden}")

    print("STAGE41_LEGAL_TERMS_RECEIPT_REVIEW=PASS_STRUCTURAL_CANDIDATE_ONLY")
    print("LEGAL_REVIEW_VERIFIED_BY_SCRIPT=false")
    print("PUBLISHED_CONTENT_LEGAL_SUFFICIENCY_VERIFIED_BY_SCRIPT=false")
    print("GATE_READY=false")
    print("INDEPENDENT_SOURCE_ARTIFACT_REVIEW_REQUIRED=true")


if __name__ == "__main__":
    main()
