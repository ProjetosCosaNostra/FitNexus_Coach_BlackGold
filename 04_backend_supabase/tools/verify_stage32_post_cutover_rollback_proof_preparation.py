from __future__ import annotations

# Historical name retained because this guard is wired into the permanent Quality Gate.
# The authoritative Stage32 rollback lifecycle has advanced beyond proof preparation to
# the consumed successful proof + repo-only cleanup frontier. Delegate to the current
# fail-closed lifecycle guard rather than preserving stale pre-proof semantics.
from verify_stage32_post_cutover_rollback_proof_cleanup import main


if __name__ == "__main__":
    main()
