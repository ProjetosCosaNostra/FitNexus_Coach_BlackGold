from __future__ import annotations

import argparse
from pathlib import Path

from stage49_evidence_promotion_contract import (
    load_authority,
    render_candidate_sql,
    validate_authority,
)

FAILURE_CLASS = "BGF-STAGE49-CANDIDATE-DIRECT-APPLY-459"


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE49_EVIDENCE_PROMOTION_CANDIDATE=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\n"
        f"DETAIL={detail}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Build a local operations candidate from a real independently reviewed Stage49 promotion authority. "
            "This tool never creates a migration and never performs a remote mutation."
        )
    )
    parser.add_argument("--authority", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    try:
        authority = load_authority(args.authority)
        validate_authority(authority, require_migration=False)
    except ValueError as exc:
        fail(str(exc))

    if authority.get("promotion_state") != "REVIEWED_CANDIDATE_NO_MIGRATION":
        fail("candidate builder requires promotion_state=REVIEWED_CANDIDATE_NO_MIGRATION")

    output = args.output.resolve()
    repo_root = Path(__file__).resolve().parents[2]
    operations_root = (repo_root / "04_backend_supabase/operations").resolve()
    try:
        output.relative_to(operations_root)
    except ValueError:
        fail("output must be inside 04_backend_supabase/operations")

    if output.suffix.lower() != ".sql":
        fail("output must be a .sql operations candidate")
    if output.name.startswith(tuple(str(i) for i in range(10))):
        fail("operations candidate must not masquerade as a versioned migration")

    sql = render_candidate_sql(authority)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(sql, encoding="utf-8")

    print("STAGE49_EVIDENCE_PROMOTION_CANDIDATE=PASS_LOCAL_ONLY")
    print(f"GATE_CODE={authority['gate_code']}")
    print("INDEPENDENT_REVIEW_VERIFIED_BY_TOOL=false")
    print("SOURCE_ARTIFACT_CONTENT_VERIFIED_BY_TOOL=false")
    print("VERSIONED_MIGRATION_CREATED=false")
    print("REMOTE_APPLY_PERFORMED=false")
    print("GATE_READY=false")
    print("CONTROLLED_LAUNCH=false")


if __name__ == "__main__":
    main()
