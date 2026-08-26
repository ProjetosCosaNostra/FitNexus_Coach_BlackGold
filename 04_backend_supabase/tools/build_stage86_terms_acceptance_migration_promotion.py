from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage86_terms_acceptance_migration_promotion_authority.json"
MIGRATION = BACKEND / "migrations" / "20260826180000_stage85_terms_acceptance_registry_ledger.sql"
SOURCE = BACKEND / "operations" / "stage85_terms_acceptance_registry_ledger_candidate.sql"
LEDGER = BACKEND / "migration_ledger_authority.json"
OPEN_DECISIONS = ROOT / "10_compliance" / "drafts" / "COMPLIANCE_OPEN_DECISIONS.json"
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
FAILURE_CLASS = "BGF-STAGE86-TERMS-ACCEPTANCE-MIGRATION-PROMOTION-GUARD-858"
CANONICAL_REQUIRED = "Production mechanism binding user acceptance to immutable terms version/digest."
CANONICAL_RESOLUTION = "product implementation plus independent review"


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE86_TERMS_ACCEPTANCE_MIGRATION_PROMOTION=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\nDETAIL={detail}"
    )


def load_json(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to load {label}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"{label} must be a JSON object")
    return value


def git_blob_sha(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(f"blob {len(raw)}\0".encode("utf-8") + raw).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_from_standalone_do(path: Path) -> bytes:
    raw = path.read_bytes()
    lines = raw.splitlines(keepends=True)
    offset = 0
    for line in lines:
        try:
            text = line.decode("utf-8").strip()
        except UnicodeDecodeError:
            fail(f"non-UTF8 SQL: {path.relative_to(ROOT)}")
        if text == "do $$":
            return raw[offset:]
        offset += len(line)
    fail(f"standalone do $$ marker missing: {path.relative_to(ROOT)}")
    raise AssertionError("unreachable")


def canonical_decision() -> dict:
    decisions = load_json(OPEN_DECISIONS, "open decisions")
    unresolved = decisions.get("unresolved")
    target = next(
        (row for row in unresolved if isinstance(row, dict) and row.get("id") == "TERMS_ACCEPTANCE_VERSIONING"),
        None,
    ) if isinstance(unresolved, list) else None
    if not isinstance(target, dict):
        fail("TERMS_ACCEPTANCE_VERSIONING missing")
    if target.get("state") != "OPEN" or target.get("applies_to") != ["legal_terms_of_use"]:
        fail("canonical target state/scope drift")
    if target.get("required") != CANONICAL_REQUIRED or target.get("resolution_authority") != CANONICAL_RESOLUTION:
        fail("canonical target wording drift")
    return target


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    source_sha = args.source_sha.strip().lower()
    if SHA40_RE.fullmatch(source_sha) is None:
        fail("source-sha must be exact lowercase 40-character Git SHA")

    authority = load_json(AUTHORITY, "Stage86 authority")
    ledger = load_json(LEDGER, "migration ledger authority")
    canonical = canonical_decision()

    if authority.get("stage") != "STAGE86_TERMS_ACCEPTANCE_MIGRATION_PROMOTION":
        fail("Stage86 authority identity drift")
    migration = authority.get("migration", {})
    if migration.get("repository_blob_sha") != git_blob_sha(MIGRATION):
        fail("migration blob drift")
    if migration.get("source_candidate_blob_sha") != git_blob_sha(SOURCE):
        fail("source candidate blob drift")
    if migration.get("migration_ledger_blob_after_promotion") != git_blob_sha(LEDGER):
        fail("migration ledger blob drift")
    if extract_from_standalone_do(MIGRATION) != extract_from_standalone_do(SOURCE):
        fail("migration executable body differs from reviewed Stage85 candidate")

    repo_only = [
        row for row in ledger.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    ]
    if [row.get("name") for row in repo_only] != ["stage85_terms_acceptance_registry_ledger"]:
        fail("Stage86 repo-only migration ledger declaration drift")

    output = {
        "schema_version": 1,
        "stage": "STAGE86_TERMS_ACCEPTANCE_MIGRATION_PROMOTION",
        "output_kind": "NON_ATTESTING_REPOSITORY_ONLY_MIGRATION_PROMOTION_PACKET",
        "state": "EXACT_MIGRATION_PROMOTED_REPO_ONLY_REMOTE_UNAPPLIED_NO_TERMS_DATA_NO_ACCEPTANCE_DATA_NO_GATE_PROMOTION",
        "source_sha": source_sha,
        "canonical_target_open_decision": {
            "id": canonical["id"],
            "state": canonical["state"],
            "applies_to": canonical["applies_to"],
            "required": canonical["required"],
            "resolution_authority": canonical["resolution_authority"],
        },
        "migration": {
            "name": migration["name"],
            "path": str(MIGRATION.relative_to(ROOT)).replace("\\", "/"),
            "git_blob_sha": git_blob_sha(MIGRATION),
            "sha256": sha256_file(MIGRATION),
            "byte_count": len(MIGRATION.read_bytes()),
            "source_candidate_git_blob_sha": git_blob_sha(SOURCE),
            "executable_body_byte_identical": True,
            "migration_ledger_state": "repo_only",
            "remote_applied": False,
            "apply_count": 0,
        },
        "migration_ledger": {
            "git_blob_sha": git_blob_sha(LEDGER),
            "baseline_main_sha": ledger.get("baseline_main_sha"),
            "repo_only_divergence": "stage85_terms_acceptance_registry_ledger",
            "remote_history_row_count": len(ledger.get("remote_migrations", [])),
        },
        "hard_boundaries": {
            "terms_candidate_approved": False,
            "terms_candidate_published": False,
            "terms_registry_row_created": False,
            "real_acceptance_collected": False,
            "remote_migration_applied": False,
            "supabase_mutation": False,
            "target_decision_closed": False,
            "legal_terms_gate_ready": False,
            "deployment": False,
            "controlled_launch_promoted": False,
            "paid_media_promoted": False,
        },
        "next_after_green": authority["next_after_green"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("STAGE86_TERMS_ACCEPTANCE_MIGRATION_PROMOTION=PASS")
    print("MIGRATION_LEDGER_STATE=repo_only")
    print("EXECUTABLE_BODY_BYTE_IDENTICAL=true")
    print("REMOTE_MIGRATION_APPLIED=false")
    print("SUPABASE_MUTATION=false")
    print("TERMS_REGISTRY_ROW_CREATED=false")
    print("REAL_ACCEPTANCE_COLLECTED=false")
    print("TARGET_DECISION_CLOSED=false")
    print("LEGAL_TERMS_GATE_READY=false")


if __name__ == "__main__":
    main()
