from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from review_stage58_billing_controlled_proof_bundle import canonical_bundle_digest
from stage59_billing_proof_independent_review_contract import (
    DIGEST_FIELDS,
    load_receipt,
    validate_review_receipt,
)
from stage56_billing_proof_promotion_contract import validate_authority as validate_stage56_authority

FAILURE_CLASS = "BGF-STAGE59-INDEPENDENT-REVIEW-PREPARATION-GUARD-576"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(128 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_stage58_aggregate(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Stage58 aggregate unreadable: {type(exc).__name__}")
    if not isinstance(value, dict):
        raise ValueError("Stage58 aggregate must be a JSON object")
    if value.get("schema_version") != 1:
        raise ValueError("Stage58 aggregate schema drift")
    if value.get("stage") != "STAGE58_BILLING_CONTROLLED_PROOF_INTAKE_PREPARATION":
        raise ValueError("Stage58 aggregate stage drift")
    if value.get("contract") != "STAGE58_V1":
        raise ValueError("Stage58 aggregate contract drift")
    if value.get("overall_state") != "STRUCTURALLY_COMPLETE_AWAITING_INDEPENDENT_REVIEW":
        raise ValueError("Stage58 aggregate is not structurally complete")
    if value.get("expected_receipt_count") != 6 or value.get("valid_structural_receipt_count") != 6:
        raise ValueError("Stage58 aggregate receipt count drift")
    if any(value.get(key) != 0 for key in (
        "missing_receipt_count",
        "duplicate_receipt_type_count",
        "unknown_or_unreadable_receipt_count",
        "invalid_receipt_count",
    )):
        raise ValueError("Stage58 aggregate contains incomplete or invalid receipt state")
    flags = value.get("authority_flags")
    if not isinstance(flags, dict) or not flags or any(flag is not False for flag in flags.values()):
        raise ValueError("Stage58 aggregate attempted authority promotion")
    mapping = value.get("stage56_candidate_digest_mapping")
    if not isinstance(mapping, dict) or set(mapping) != set(DIGEST_FIELDS):
        raise ValueError("Stage58 aggregate Stage56 digest mapping drift")
    for field in DIGEST_FIELDS:
        digest = mapping.get(field)
        if not isinstance(digest, str) or len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
            raise ValueError(f"Stage58 aggregate invalid digest: {field}")
    if len(set(mapping.values())) != len(DIGEST_FIELDS):
        raise ValueError("Stage58 aggregate proof receipt digests collide")
    expected_bundle = canonical_bundle_digest(mapping)
    if value.get("proof_bundle_digest") != expected_bundle:
        raise ValueError("Stage58 aggregate proof_bundle_digest drift")
    return value


def build_candidate(aggregate: dict[str, Any], review: dict[str, Any], review_sha256: str) -> dict[str, Any]:
    mapping = aggregate["stage56_candidate_digest_mapping"]
    return {
        "schema_version": 1,
        "protocol": "STAGE56_V1",
        "project_ref": "mceukeondizkwlpfxzgf",
        "scope": "BR_V1",
        "provider_code": "asaas",
        "evidence_version": "2026-08-18-official-docs-v1",
        "source_state": "credentials_verified",
        "target_state": "proof_complete",
        "provider_environment_id": "asaas-production",
        "promotion_state": "REVIEWED_CANDIDATE_NO_MIGRATION",
        "independent_review_decision": "APPROVED_FOR_PROOF_COMPLETE_MIGRATION_DRAFT",
        "provider_account_owner_authorization_digest": review["provider_account_owner_authorization_digest"],
        "credential_activation_digest": review["credential_activation_digest"],
        "credentials_verified_at_utc": review["credentials_verified_at_utc"],
        "provider_selection_activated_at_utc": review["provider_selection_activated_at_utc"],
        "provider_activation_receipt_sha256": mapping["provider_activation_receipt_sha256"],
        "webhook_auth_test_receipt_digest": mapping["webhook_auth_test_receipt_digest"],
        "webhook_replay_receipt_digest": mapping["webhook_replay_receipt_digest"],
        "checkout_end_to_end_receipt_digest": mapping["checkout_end_to_end_receipt_digest"],
        "synthetic_fixture_manifest_sha256": mapping["synthetic_fixture_manifest_sha256"],
        "synthetic_fixture_cleanup_receipt_sha256": mapping["synthetic_fixture_cleanup_receipt_sha256"],
        "independent_review_receipt_sha256": review_sha256,
        "proof_bundle_digest": aggregate["proof_bundle_digest"],
        "reviewer_reference_digest": review["reviewer_reference_digest"],
        "reviewer_independence_attested": True,
        "source_artifacts_reviewed_out_of_band_attested": True,
        "synthetic_non_customer_fixture_attested": True,
        "customer_data_used": False,
        "raw_secret_copied_to_receipts": False,
        "real_financial_charge_completed": False,
        "paid_subscription_created": False,
        "provider_call_performed_by_tooling": False,
        "provider_activation_performed_by_tooling": False,
        "remote_apply_performed": False,
        "controlled_launch_promoted": False,
        "paid_media_promoted": False,
        "launch_promoted": False,
        "proof_completed_at_utc": review["proof_completed_at_utc"],
        "independent_review_completed_at_utc": review["independent_review_completed_at_utc"],
        "migration_filename": None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a Stage56 REVIEWED_CANDIDATE_NO_MIGRATION authority from a complete Stage58 bundle and real Stage59 independent-review receipt."
    )
    parser.add_argument("--stage58-aggregate", type=Path, required=True)
    parser.add_argument("--independent-review-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        aggregate_path = args.stage58_aggregate.resolve()
        review_path = args.independent_review_receipt.resolve()
        aggregate = load_stage58_aggregate(aggregate_path)
        review = load_receipt(review_path)
        validate_review_receipt(review, require_approved=True)

        aggregate_sha = sha256_file(aggregate_path)
        review_sha = sha256_file(review_path)
        if review["stage58_aggregate_sha256"] != aggregate_sha:
            raise ValueError("independent review receipt is not bound to the supplied Stage58 aggregate bytes")
        if review["proof_bundle_digest"] != aggregate["proof_bundle_digest"]:
            raise ValueError("independent review proof_bundle_digest does not match Stage58 aggregate")
        if review["stage56_candidate_digest_mapping"] != aggregate["stage56_candidate_digest_mapping"]:
            raise ValueError("independent review Stage56 digest mapping does not match Stage58 aggregate")

        candidate = build_candidate(aggregate, review, review_sha)
        validate_stage56_authority(candidate, require_migration=False)
    except ValueError as exc:
        raise SystemExit(
            "STAGE59_STAGE56_PROOF_PROMOTION_AUTHORITY=FAIL\n"
            f"FAILURE_CLASS={FAILURE_CLASS}\nDETAIL={exc}"
        )

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("STAGE59_STAGE56_PROOF_PROMOTION_AUTHORITY=BUILT_REVIEWED_CANDIDATE_NO_MIGRATION")
    print("MIGRATION_CREATED=false")
    print("REMOTE_APPLY_AUTHORITY=false")
    print("PROOF_COMPLETE_AUTHORITY=false")
    print("PROVIDER_CALL_BY_TOOLING=false")
    print("PROVIDER_ACTIVATION_BY_TOOLING=false")
    print("REMOTE_MUTATION=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
