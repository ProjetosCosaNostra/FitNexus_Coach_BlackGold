from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage87_terms_acceptance_remote_apply_gate_preparation_authority.json"
CONTRACT = BACKEND / "operations" / "stage87_terms_acceptance_remote_apply_gate_contract.json"
MIGRATION = BACKEND / "migrations" / "20260826180000_stage85_terms_acceptance_registry_ledger.sql"
LEDGER = BACKEND / "migration_ledger_authority.json"
OPEN_DECISIONS = ROOT / "10_compliance" / "drafts" / "COMPLIANCE_OPEN_DECISIONS.json"
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
FAILURE_CLASS = "BGF-STAGE87-REMOTE-APPLY-GATE-PREPARATION-GUARD-869"


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE87_TERMS_ACCEPTANCE_REMOTE_APPLY_GATE_PREPARATION=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\nDETAIL={detail}"
    )


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to load {path.relative_to(ROOT)}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"expected JSON object: {path.relative_to(ROOT)}")
    return value


def git_blob_sha(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(f"blob {len(raw)}\0".encode("utf-8") + raw).hexdigest()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_target() -> dict:
    rows = load(OPEN_DECISIONS).get("unresolved")
    target = next(
        (row for row in rows if isinstance(row, dict) and row.get("id") == "TERMS_ACCEPTANCE_VERSIONING"),
        None,
    ) if isinstance(rows, list) else None
    if not isinstance(target, dict) or target.get("state") != "OPEN":
        fail("TERMS_ACCEPTANCE_VERSIONING is not OPEN")
    return target


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    source_sha = args.source_sha.strip().lower()
    if SHA40_RE.fullmatch(source_sha) is None:
        fail("source-sha must be exact lowercase 40-character Git SHA")

    authority = load(AUTHORITY)
    contract = load(CONTRACT)
    ledger = load(LEDGER)
    target = canonical_target()
    if authority.get("stage") != "STAGE87_TERMS_ACCEPTANCE_REMOTE_APPLY_GATE_PREPARATION":
        fail("Stage87 authority identity drift")
    if authority.get("sealed_inputs", {}).get("apply_gate_contract_blob") != git_blob_sha(CONTRACT):
        fail("Stage87 gate contract blob drift")
    if authority.get("sealed_inputs", {}).get("migration_blob") != git_blob_sha(MIGRATION):
        fail("Stage87 migration blob drift")
    if authority.get("sealed_inputs", {}).get("migration_ledger_blob") != git_blob_sha(LEDGER):
        fail("Stage87 migration ledger blob drift")
    if contract.get("execution_contract", {}).get("stage87_executes_remote_apply") is not False:
        fail("Stage87 contract unexpectedly executes remote apply")

    repo_only = [
        row for row in ledger.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    ]
    if len(repo_only) != 1 or repo_only[0].get("name") != "stage85_terms_acceptance_registry_ledger":
        fail("Stage87 requires exactly one target repo-only migration divergence")

    output = {
        "schema_version": 1,
        "stage": "STAGE87_TERMS_ACCEPTANCE_REMOTE_APPLY_GATE_PREPARATION",
        "output_kind": "NON_ATTESTING_REPO_ONLY_ONE_SHOT_REMOTE_APPLY_GATE_PREPARATION_PACKET",
        "source_sha": source_sha,
        "state": "GATE_PREPARED_NO_REMOTE_EXECUTION_NO_TERMS_DATA_NO_ACCEPTANCE_DATA_NO_GATE_PROMOTION",
        "canonical_target": {
            "id": target.get("id"),
            "state": target.get("state"),
            "applies_to": target.get("applies_to"),
        },
        "migration": {
            "name": "stage85_terms_acceptance_registry_ledger",
            "git_blob_sha": git_blob_sha(MIGRATION),
            "sha256": sha256(MIGRATION),
            "remote_applied": False,
            "apply_count": 0,
        },
        "apply_gate_contract": {
            "git_blob_sha": git_blob_sha(CONTRACT),
            "sha256": sha256(CONTRACT),
            "one_shot": True,
            "stage87_executes": False,
        },
        "fresh_remote_receipt": authority.get("fresh_post_merge_remote_precondition_receipt"),
        "hard_boundaries": {
            "remote_migration_applied": False,
            "supabase_mutation": False,
            "terms_registry_row_created": False,
            "real_acceptance_collected": False,
            "target_decision_closed": False,
            "legal_terms_gate_ready": False,
            "deployment": False,
            "controlled_launch_promoted": False,
            "paid_media_promoted": False,
        },
        "next_after_green": authority.get("next_after_green"),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("STAGE87_TERMS_ACCEPTANCE_REMOTE_APPLY_GATE_PREPARATION=PASS")
    print("ONE_SHOT_GATE_PREPARED=true")
    print("REMOTE_MIGRATION_APPLIED=false")
    print("SUPABASE_MUTATION=false")
    print("TERMS_REGISTRY_ROW_CREATED=false")
    print("REAL_ACCEPTANCE_COLLECTED=false")
    print("TARGET_DECISION_CLOSED=false")
    print("LEGAL_TERMS_GATE_READY=false")


if __name__ == "__main__":
    main()
