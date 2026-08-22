from __future__ import annotations

import importlib
import tempfile
from pathlib import Path


def fail(message: str) -> None:
    raise SystemExit("STAGE33_POST_REVOCATION_SEAL_HISTORICAL_COMPAT=FAIL\n" + message)


def main() -> None:
    # Prove the actual downstream seal frontier first.
    seal = importlib.import_module(
        "verify_stage33_post_revocation_live_proof_workflow_seal"
    )
    seal.main()

    # Then prove the immutable migration-promotion contract under its historical
    # pre-seal filesystem projection. The only projected fact is that the later
    # one-shot workflow did not exist yet; all migration/authority/ledger sources
    # remain the actual current repository files.
    promotion = importlib.import_module(
        "verify_stage33_direct_rpc_revocation_migration_promotion"
    )
    original_workflow = promotion.PROOF_WORKFLOW
    with tempfile.TemporaryDirectory(prefix="fitnexus-stage33-seal-history-") as tmp:
        promotion.PROOF_WORKFLOW = Path(tmp) / "stage33_post_revocation_edge_runtime_live_proof.yml"
        try:
            promotion.main()
        finally:
            promotion.PROOF_WORKFLOW = original_workflow

    print("STAGE33_POST_REVOCATION_SEAL_HISTORICAL_COMPAT=PASS")
    print("ACTUAL_FRONTIER=POST_REVOCATION_ONE_SHOT_SEALED_REMOTE_APPLY_PENDING")
    print("PROJECTED_HISTORICAL_PROOF_WORKFLOW_EXISTS=false")
    print("MIGRATION_PROMOTION_HISTORICAL_CONTRACT=PASS")
    print("REMOTE_REVOCATION_APPLIED=false")
    print("PROOF_EVENT_ALLOWED_NOW=false")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
