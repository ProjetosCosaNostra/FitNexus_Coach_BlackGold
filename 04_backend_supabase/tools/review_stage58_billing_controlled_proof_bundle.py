from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from stage58_billing_controlled_proof_receipt_contract import (
    CONTRACT,
    RECEIPT_TYPES,
    load_receipt,
    validate_receipt,
)

FAILURE_CLASS = "BGF-STAGE58-CONTROLLED-PROOF-INTAKE-GUARD-562"
MAX_RECEIPT_BYTES = 1024 * 1024

STAGE56_DIGEST_FIELD = {
    "PROVIDER_SELECTION_ACTIVATION": "provider_activation_receipt_sha256",
    "WEBHOOK_AUTH": "webhook_auth_test_receipt_digest",
    "WEBHOOK_REPLAY": "webhook_replay_receipt_digest",
    "CHECKOUT_END_TO_END": "checkout_end_to_end_receipt_digest",
    "SYNTHETIC_FIXTURE_MANIFEST": "synthetic_fixture_manifest_sha256",
    "SYNTHETIC_FIXTURE_CLEANUP": "synthetic_fixture_cleanup_receipt_sha256",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(128 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_bundle_digest(mapping: dict[str, str]) -> str:
    payload = json.dumps(mapping, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def authority_flags() -> dict[str, bool]:
    return {
        "independent_review_passed": False,
        "proof_complete_authorized": False,
        "proof_complete_migration_created": False,
        "remote_apply_authorized": False,
        "provider_activation_authorized": False,
        "provider_call_authorized": False,
        "provider_call_performed_by_stage58_tooling": False,
        "provider_activation_performed_by_stage58_tooling": False,
        "supabase_mutation_performed_by_stage58_tooling": False,
        "network_call_performed_by_stage58_tooling": False,
        "controlled_launch_promoted": False,
        "paid_media_promoted": False,
        "launch_promoted": False,
        "raw_receipt_body_copied_to_bundle": False,
        "receipt_path_or_filename_copied_to_bundle": False,
    }


def identify_candidate(path: Path) -> tuple[str | None, dict[str, Any] | None]:
    try:
        if path.stat().st_size > MAX_RECEIPT_BYTES:
            return None, None
        receipt = load_receipt(path)
    except (OSError, ValueError):
        return None, None
    receipt_type = receipt.get("receipt_type")
    if receipt.get("contract") != CONTRACT or receipt_type not in RECEIPT_TYPES:
        return None, receipt
    return str(receipt_type), receipt


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Review a local Stage58 billing controlled-proof receipt bundle without attesting proof truth."
    )
    parser.add_argument("--bundle-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=("inventory", "complete"), default="inventory")
    args = parser.parse_args()

    bundle_dir = args.bundle_dir.resolve()
    output = args.output.resolve()
    if not bundle_dir.is_dir():
        raise SystemExit(
            "STAGE58_BILLING_CONTROLLED_PROOF_BUNDLE=FAIL\n"
            f"FAILURE_CLASS={FAILURE_CLASS}\nDETAIL=bundle directory missing"
        )

    grouped: dict[str, list[tuple[Path, dict[str, Any]]]] = {receipt_type: [] for receipt_type in RECEIPT_TYPES}
    unknown_or_unreadable = 0
    for path in sorted(bundle_dir.glob("*.json")):
        try:
            if path.resolve() == output:
                continue
        except OSError:
            unknown_or_unreadable += 1
            continue
        receipt_type, receipt = identify_candidate(path)
        if receipt_type is None or receipt is None:
            unknown_or_unreadable += 1
            continue
        grouped[receipt_type].append((path, receipt))

    entries: list[dict[str, Any]] = []
    digest_mapping: dict[str, str] = {}
    valid_count = 0
    missing_count = 0
    duplicate_count = 0
    invalid_count = unknown_or_unreadable

    for receipt_type in RECEIPT_TYPES:
        candidates = grouped[receipt_type]
        entry: dict[str, Any] = {
            "receipt_type": receipt_type,
            "stage56_digest_field": STAGE56_DIGEST_FIELD[receipt_type],
            "status": "MISSING",
            "receipt_sha256": None,
            "independent_review_required": True,
            "proof_complete_authority": False,
        }
        if not candidates:
            missing_count += 1
        elif len(candidates) > 1:
            entry["status"] = "DUPLICATE"
            entry["receipt_sha256"] = sorted(sha256_file(path) for path, _ in candidates)
            duplicate_count += 1
            invalid_count += 1
        else:
            path, receipt = candidates[0]
            digest = sha256_file(path)
            entry["receipt_sha256"] = digest
            try:
                validate_receipt(receipt)
            except ValueError:
                entry["status"] = "INVALID_STRUCTURE"
                invalid_count += 1
            else:
                entry["status"] = "STRUCTURALLY_VALID_FOR_INDEPENDENT_REVIEW_ONLY"
                digest_mapping[STAGE56_DIGEST_FIELD[receipt_type]] = digest
                valid_count += 1
        entries.append(entry)

    if invalid_count:
        overall = "INVALID_RECEIPT_PRESENT"
    elif missing_count:
        overall = "INCOMPLETE_MISSING_RECEIPTS"
    else:
        overall = "STRUCTURALLY_COMPLETE_AWAITING_INDEPENDENT_REVIEW"

    complete_mapping = len(digest_mapping) == len(RECEIPT_TYPES)
    aggregate = {
        "schema_version": 1,
        "stage": "STAGE58_BILLING_CONTROLLED_PROOF_INTAKE_PREPARATION",
        "contract": CONTRACT,
        "mode": args.mode,
        "overall_state": overall,
        "expected_receipt_count": len(RECEIPT_TYPES),
        "valid_structural_receipt_count": valid_count,
        "missing_receipt_count": missing_count,
        "duplicate_receipt_type_count": duplicate_count,
        "unknown_or_unreadable_receipt_count": unknown_or_unreadable,
        "invalid_receipt_count": invalid_count,
        "entries": entries,
        "stage56_candidate_digest_mapping": digest_mapping if complete_mapping else None,
        "proof_bundle_digest": canonical_bundle_digest(digest_mapping) if complete_mapping else None,
        "authority_flags": authority_flags(),
        "next_action": "INDEPENDENT_SOURCE_ARTIFACT_REVIEW_REQUIRED_BEFORE_ANY_STAGE56_PROOF_PROMOTION_AUTHORITY",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(aggregate, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"STAGE58_BILLING_CONTROLLED_PROOF_BUNDLE_STATE={overall}")
    print(f"VALID_STRUCTURAL_RECEIPTS={valid_count}")
    print(f"MISSING={missing_count}")
    print(f"INVALID={invalid_count}")
    print("INDEPENDENT_REVIEW_PASSED=false")
    print("PROOF_COMPLETE_AUTHORIZED=false")
    print("PROVIDER_CALL_BY_STAGE58_TOOLING=false")
    print("REMOTE_MUTATION=false")

    if invalid_count:
        return 2
    if args.mode == "complete" and missing_count:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
