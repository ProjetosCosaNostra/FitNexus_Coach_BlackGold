from __future__ import annotations

from pathlib import Path

from migration_ledger_lib import (
    ReconcileError,
    load_json,
    parse_repo_migrations,
    verify_authority_contract,
)


ROOT = Path(__file__).resolve().parents[2]
AUTHORITY_PATH = ROOT / "04_backend_supabase" / "migration_ledger_authority.json"
IDENTITY_PATH = ROOT / "04_backend_supabase" / "project_identity.json"
MIGRATIONS_DIR = ROOT / "04_backend_supabase" / "migrations"


def fail(message: str) -> None:
    raise SystemExit(f"MIGRATION_LEDGER_CONTRACT_GUARD=FAIL\n{message}")


def main() -> None:
    try:
        authority = load_json(AUTHORITY_PATH)
        identity = load_json(IDENTITY_PATH)
        repo = parse_repo_migrations(MIGRATIONS_DIR)
        result = verify_authority_contract(authority, identity, repo)
    except ReconcileError as exc:
        fail(str(exc))

    print("MIGRATION_LEDGER_CONTRACT_GUARD=PASS")
    print(f"PROJECT_REF={result['project_ref']}")
    print(f"REPO_MIGRATIONS={result['repo_count']}")
    print(f"REMOTE_BASELINE_MIGRATIONS={result['baseline_remote_count']}")
    print(f"BASELINE_MAIN_SHA={result['baseline_main_sha']}")
    print("COMPARISON_KEY=migration_name")
    print("REMOTE_VERSION_EQUALS_REPO_TIMESTAMP=NOT_REQUIRED")


if __name__ == "__main__":
    main()
