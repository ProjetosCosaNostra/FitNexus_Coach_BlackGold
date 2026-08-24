from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse

FAILURE_CLASS = "BGF-STAGE46-PRODUCTION-DEPLOYMENT-RECEIPT-STRUCTURAL-REVIEW-431"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE46_PRODUCTION_DEPLOYMENT_RECEIPT_REVIEW=FAIL\n"
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
        "stage": "STAGE46_PRODUCTION_DEPLOYMENT_EXTERNAL_EVIDENCE_PREPARATION",
        "output_kind": "DIGEST_ONLY_PRODUCTION_DEPLOYMENT_EVIDENCE_INTAKE_CANDIDATE",
        "gate_code": "production_deployment",
        "candidate_state": "AWAITING_INDEPENDENT_REVIEW_NOT_ATTESTATION",
        "secret_redaction_confirmation": "CONFIRMED",
        "monitoring_alerting_not_stage35_only_confirmation": "CONFIRMED",
        "raw_artifact_content_copied_to_receipt": False,
        "artifact_path_or_filename_copied_to_receipt": False,
        "secret_values_collected": False,
        "network_call_performed": False,
        "deployment_action_performed": False,
        "supabase_mutation_performed": False,
        "evidence_migration_created": False,
        "operations_self_attested": False,
        "stage35_alert_proof_alone_used_for_monitoring_alerting": False,
        "gate_ready_attested": False,
        "controlled_launch_promoted": False,
        "next_action": "INDEPENDENT_REVIEW_REQUIRED_BEFORE_ANY_EVIDENCE_MIGRATION",
    }
    for key, value in expected.items():
        if receipt.get(key) != value:
            fail(f"receipt invariant drift: {key}")

    for key in (
        "tls_evidence_digest",
        "environment_configuration_receipt_digest",
        "production_smoke_test_receipt_digest",
        "rollback_test_receipt_digest",
        "monitoring_alerting_readiness_receipt_digest",
        "backup_restore_readiness_reference_digest",
        "release_evidence_manifest_digest",
    ):
        if not SHA256_RE.fullmatch(str(receipt.get(key, ""))):
            fail(f"invalid SHA-256 digest: {key}")
    if not GIT_SHA_RE.fullmatch(str(receipt.get("release_commit_sha", ""))):
        fail("release commit SHA is not lowercase 40-character git SHA-1 hex")

    domain = str(receipt.get("stable_production_domain", "")).strip()
    parsed = urlparse(domain)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not host:
        fail("stable production domain must be absolute HTTPS")
    if host in {"localhost", "127.0.0.1", "::1", "example.com", "www.example.com"}:
        fail("stable production domain is placeholder/local")
    if re.search(r"(^|\.)(test|staging|preview|dev)(\.|$)", host):
        fail("stable production domain appears non-production")
    if re.search(r"example|placeholder|localhost|preview", domain, re.IGNORECASE):
        fail("stable production domain contains placeholder marker")

    serialized = json.dumps(receipt, sort_keys=True).lower()
    for forbidden in (
        '"api_key"',
        '"access_token"',
        '"password"',
        '"webhook_token"',
        '"secret_value"',
        '"service_role_key"',
        '"private_key"',
    ):
        if forbidden in serialized:
            fail(f"secret-bearing key present: {forbidden}")

    print("STAGE46_PRODUCTION_DEPLOYMENT_RECEIPT_REVIEW=PASS_STRUCTURAL_CANDIDATE_ONLY")
    print("PRODUCTION_DOMAIN_LIVE_VERIFIED_BY_SCRIPT=false")
    print("TLS_LIVE_VERIFIED_BY_SCRIPT=false")
    print("ENVIRONMENT_SECRET_ABSENCE_IN_SOURCE_ARTIFACT_VERIFIED_BY_SCRIPT=false")
    print("RELEASE_SHA_DEPLOYMENT_BINDING_VERIFIED_BY_SCRIPT=false")
    print("PRODUCTION_SMOKE_OPERATIONALLY_VERIFIED_BY_SCRIPT=false")
    print("ROLLBACK_OPERATIONALLY_VERIFIED_BY_SCRIPT=false")
    print("MONITORING_ALERTING_COMPLETENESS_VERIFIED_BY_SCRIPT=false")
    print("BACKUP_RESTORE_OPERATIONALLY_VERIFIED_BY_SCRIPT=false")
    print("STAGE35_ALERT_PROOF_ALONE_SUFFICIENT=false")
    print("DEPLOYMENT_ACTION_PERFORMED=false")
    print("GATE_READY=false")
    print("INDEPENDENT_SOURCE_ARTIFACT_REVIEW_REQUIRED=true")


if __name__ == "__main__":
    main()
