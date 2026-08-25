from __future__ import annotations

import argparse
from pathlib import Path

from stage56_billing_proof_promotion_contract import load_authority, render_candidate_sql, validate_authority

FAILURE_CLASS = "BGF-STAGE56-PROOF-COMPLETE-PROMOTION-BOUNDARY-GUARD-543"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a local Stage56 proof_complete SQL candidate from independently reviewed proof authority."
    )
    parser.add_argument("authority", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    try:
        authority = load_authority(args.authority)
        validate_authority(authority, require_migration=False)
    except ValueError as exc:
        raise SystemExit(
            "STAGE56_BILLING_PROOF_COMPLETE_CANDIDATE=FAIL\n"
            f"FAILURE_CLASS={FAILURE_CLASS}\nDETAIL={exc}"
        )

    if authority.get("promotion_state") != "REVIEWED_CANDIDATE_NO_MIGRATION":
        raise SystemExit(
            "STAGE56_BILLING_PROOF_COMPLETE_CANDIDATE=FAIL\n"
            f"FAILURE_CLASS={FAILURE_CLASS}\nDETAIL=builder accepts reviewed candidate state only"
        )

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_candidate_sql(authority), encoding="utf-8")

    print("STAGE56_BILLING_PROOF_COMPLETE_CANDIDATE=BUILT_LOCAL_ONLY")
    print("REMOTE_APPLY_AUTHORITY=false")
    print("PROVIDER_ACTIVATION_BY_TOOLING=false")
    print("PROVIDER_CALL_BY_TOOLING=false")
    print("REMOTE_MUTATION=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
