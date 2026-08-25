from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

PROTOCOL = "STAGE61_V1"
PROJECT_REF = "mceukeondizkwlpfxzgf"

ORDERED_CLAIMS = (
    "operator_credentials_evidence_supplied",
    "credentials_independent_review_passed",
    "credentials_reviewed_candidate_exists",
    "credentials_migration_draft_exists",
    "credentials_remote_apply_authorized",
    "credentials_remote_applied_confirmed",
    "provider_activation_authorized",
    "provider_active_confirmed",
    "controlled_proof_execution_authorized",
    "stage58_receipts_structurally_complete",
    "synthetic_cleanup_zero_residue_confirmed",
    "stage59_independent_review_passed",
    "stage56_reviewed_candidate_exists",
    "proof_complete_migration_draft_exists",
    "proof_complete_remote_apply_authorized",
    "proof_complete_remote_confirmed",
)

STATES = (
    "AWAITING_REAL_OPERATOR_CREDENTIAL_EVIDENCE",
    "AWAITING_INDEPENDENT_CREDENTIAL_REVIEW",
    "AWAITING_CREDENTIAL_REVIEWED_CANDIDATE",
    "AWAITING_CREDENTIAL_MIGRATION_DRAFT",
    "AWAITING_CREDENTIAL_REMOTE_APPLY_AUTHORIZATION",
    "AWAITING_CREDENTIAL_REMOTE_APPLY_CONFIRMATION",
    "AWAITING_PROVIDER_ACTIVATION_AUTHORIZATION",
    "AWAITING_PROVIDER_ACTIVE_CONFIRMATION",
    "AWAITING_CONTROLLED_PROOF_EXECUTION_AUTHORIZATION",
    "AWAITING_STAGE58_CONTROLLED_PROOF_RECEIPTS",
    "AWAITING_SYNTHETIC_CLEANUP_ZERO_RESIDUE",
    "AWAITING_STAGE59_INDEPENDENT_PROOF_REVIEW",
    "AWAITING_STAGE56_REVIEWED_PROOF_CANDIDATE",
    "AWAITING_PROOF_COMPLETE_MIGRATION_DRAFT",
    "AWAITING_PROOF_COMPLETE_REMOTE_APPLY_AUTHORIZATION",
    "AWAITING_PROOF_COMPLETE_REMOTE_CONFIRMATION",
    "PROOF_COMPLETE_REMOTE_CONFIRMED_BILLING_GATE_REASSESSMENT_REQUIRED",
)

FAILURE_CLASS = "BGF-STAGE61-AUTHORIZATION-STATE-MACHINE-GUARD-594"


def load_input(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"input unreadable: {type(exc).__name__}")
    if not isinstance(value, dict):
        raise ValueError("input must be a JSON object")
    if set(value) != {"schema_version", "protocol", "claims"}:
        raise ValueError("input top-level key set drift")
    if value.get("schema_version") != 1 or value.get("protocol") != PROTOCOL:
        raise ValueError("input protocol/schema drift")
    claims = value.get("claims")
    if not isinstance(claims, dict) or set(claims) != set(ORDERED_CLAIMS):
        raise ValueError("claims must contain the exact Stage61 claim set")
    for claim in ORDERED_CLAIMS:
        if type(claims[claim]) is not bool:
            raise ValueError(f"claim must be boolean: {claim}")
    return value


def evaluate(claims: dict[str, bool]) -> dict[str, Any]:
    first_false: int | None = None
    out_of_order: list[str] = []
    for index, claim in enumerate(ORDERED_CLAIMS):
        value = claims[claim]
        if not value and first_false is None:
            first_false = index
        elif value and first_false is not None:
            out_of_order.append(claim)

    if out_of_order:
        return {
            "schema_version": 1,
            "protocol": PROTOCOL,
            "project_ref": PROJECT_REF,
            "evaluation_state": "INVALID_OUT_OF_ORDER_CLAIM",
            "structural_state_index": None,
            "structural_state": None,
            "next_required_claim": ORDERED_CLAIMS[first_false] if first_false is not None else None,
            "out_of_order_claims": out_of_order,
            "truth_verified": False,
            "structural_only": True,
            "authority_flags": authority_flags(),
        }

    state_index = len(ORDERED_CLAIMS) if first_false is None else first_false
    next_required = None if first_false is None else ORDERED_CLAIMS[first_false]
    return {
        "schema_version": 1,
        "protocol": PROTOCOL,
        "project_ref": PROJECT_REF,
        "evaluation_state": "STRUCTURALLY_ORDERED_NOT_TRUTH_VERIFIED",
        "structural_state_index": state_index,
        "structural_state": STATES[state_index],
        "next_required_claim": next_required,
        "out_of_order_claims": [],
        "truth_verified": False,
        "structural_only": True,
        "authority_flags": authority_flags(),
    }


def authority_flags() -> dict[str, bool]:
    return {
        "provider_call_authorized": False,
        "provider_activation_authorized": False,
        "supabase_mutation_authorized": False,
        "migration_creation_authorized": False,
        "migration_apply_authorized": False,
        "controlled_proof_authorized": False,
        "independent_review_verified_by_tool": False,
        "proof_complete_authorized": False,
        "billing_gate_promoted": False,
        "controlled_launch_authorized": False,
        "paid_media_authorized": False,
        "launch_authorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate ordering of Stage61 billing authorization claims. "
            "This is structural-only and never validates truth or grants authority."
        )
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=("inventory", "strict"), default="inventory")
    args = parser.parse_args()

    try:
        payload = load_input(args.input.resolve())
        result = evaluate(payload["claims"])
    except ValueError as exc:
        raise SystemExit(
            "STAGE61_AUTHORIZATION_STATE_MACHINE=FAIL\n"
            f"FAILURE_CLASS={FAILURE_CLASS}\nDETAIL={exc}"
        )

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"STAGE61_EVALUATION_STATE={result['evaluation_state']}")
    print(f"STRUCTURAL_STATE={result['structural_state']}")
    print(f"NEXT_REQUIRED_CLAIM={result['next_required_claim']}")
    print("TRUTH_VERIFIED=false")
    print("REMOTE_AUTHORITY=false")

    if args.mode == "strict" and result["evaluation_state"] != "STRUCTURALLY_ORDERED_NOT_TRUTH_VERIFIED":
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
