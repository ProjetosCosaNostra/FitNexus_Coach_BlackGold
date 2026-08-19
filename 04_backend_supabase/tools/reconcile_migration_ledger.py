from __future__ import annotations

import argparse
from pathlib import Path

from migration_ledger_lib import (
    ReconcileError,
    load_json,
    normalize_remote_payload,
    parse_repo_migrations,
    reconcile,
    verify_authority_contract,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_AUTHORITY = ROOT / "04_backend_supabase" / "migration_ledger_authority.json"
DEFAULT_IDENTITY = ROOT / "04_backend_supabase" / "project_identity.json"
DEFAULT_MIGRATIONS = ROOT / "04_backend_supabase" / "migrations"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fail-closed reconciliation of the authoritative Supabase migration ledger "
            "against repository migrations."
        )
    )
    parser.add_argument(
        "--remote-json",
        type=Path,
        required=True,
        help=(
            "JSON exported from Supabase list_migrations. Accepts direct "
            "{migrations:[...]} or connector wrapper {text:'...'}."
        ),
    )
    parser.add_argument("--authority", type=Path, default=DEFAULT_AUTHORITY)
    parser.add_argument("--identity", type=Path, default=DEFAULT_IDENTITY)
    parser.add_argument("--migrations-dir", type=Path, default=DEFAULT_MIGRATIONS)
    return parser.parse_args()


def fail(message: str) -> None:
    raise SystemExit(f"MIGRATION_LEDGER_RECONCILER=FAIL\n{message}")


def main() -> None:
    args = parse_args()
    try:
        authority = load_json(args.authority)
        identity = load_json(args.identity)
        repo = parse_repo_migrations(args.migrations_dir)
        verify_authority_contract(authority, identity, repo)
        remote_payload = load_json(args.remote_json)
        actual_remote = normalize_remote_payload(remote_payload)
        result = reconcile(authority, repo, actual_remote)
    except ReconcileError as exc:
        fail(str(exc))

    print("MIGRATION_LEDGER_RECONCILER=PASS")
    print(f"PROJECT_REF={result['project_ref']}")
    print(f"REPO_MIGRATIONS={result['repo_count']}")
    print(f"REMOTE_MIGRATIONS={result['remote_count']}")
    print(
        "REPO_ONLY_DECLARED="
        + (",".join(result["repo_only_declared"]) if result["repo_only_declared"] else "NONE")
    )
    print(
        "REMOTE_ONLY_DECLARED="
        + (
            ",".join(result["remote_only_declared"])
            if result["remote_only_declared"]
            else "NONE"
        )
    )


if __name__ == "__main__":
    main()
