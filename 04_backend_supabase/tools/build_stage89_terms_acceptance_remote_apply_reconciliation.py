from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage89_terms_acceptance_remote_apply_reconciliation_authority.json"
MIGRATION = BACKEND / "migrations" / "20260826180000_stage85_terms_acceptance_registry_ledger.sql"
LEDGER = BACKEND / "migration_ledger_authority.json"
EXPOSURE = BACKEND / "security_definer_exposure_authority.json"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
FAILURE = "BGF-STAGE89-REMOTE-APPLY-RECONCILIATION-GUARD-885"
TARGET = "stage85_terms_acceptance_registry_ledger"
REMOTE_VERSION = "20260826184218"


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE89_TERMS_ACCEPTANCE_REMOTE_APPLY_RECONCILIATION=FAIL\n"
        f"FAILURE_CLASS={FAILURE}\nDETAIL={detail}"
    )


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"load failed {path.relative_to(ROOT)}:{type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"expected object {path.relative_to(ROOT)}")
    return value


def blob(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    source_sha = args.source_sha.strip().lower()
    if SHA40.fullmatch(source_sha) is None:
        fail("invalid source sha")

    authority = load(AUTHORITY)
    ledger = load(LEDGER)
    exposure = load(EXPOSURE)
    if blob(AUTHORITY) != "70fcae1902568c070b2a82a52eca338c8e8da6bd":
        fail("Stage89 authority blob drift")
    reconciliation = authority.get("repository_reconciliation", {})
    if reconciliation.get("migration_ledger_blob") != blob(LEDGER):
        fail("migration ledger blob drift")
    if reconciliation.get("security_definer_authority_blob") != blob(EXPOSURE):
        fail("SECURITY DEFINER authority blob drift")
    if authority.get("sealed_execution_inputs", {}).get("migration_blob") != blob(MIGRATION):
        fail("migration blob drift")

    repo_only = [
        row for row in ledger.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    ]
    if repo_only:
        fail("Stage89 reconciled ledger retained repo-only divergence")
    target_rows = [
        row for row in ledger.get("remote_migrations", [])
        if isinstance(row, dict) and row.get("name") == TARGET
    ]
    if len(target_rows) != 1 or target_rows[0].get("version") != REMOTE_VERSION:
        fail("Stage89 target remote receipt drift")

    apply_receipt = authority.get("one_shot_remote_apply_receipt", {})
    post = authority.get("immediate_post_apply_receipt", {})
    privilege = authority.get("fresh_privilege_reconciliation_receipt", {})
    if apply_receipt.get("apply_attempt_count") != 1 or apply_receipt.get("blind_retry_count") != 0:
        fail("one-shot apply receipt drift")
    if post.get("terms_registry_rows") != 0 or post.get("acceptance_ledger_rows") != 0:
        fail("zero-row postcondition drift")
    if privilege.get("student_direct_route_anon_execute_count") != 0 or privilege.get("student_direct_route_authenticated_execute_count") != 0:
        fail("student direct-route privilege regression")

    packet = {
        "schema_version": 1,
        "stage": "STAGE89_TERMS_ACCEPTANCE_REMOTE_APPLY_RECONCILIATION",
        "output_kind": "REPOSITORY_PACKET_OF_CAPTURED_ONE_SHOT_REMOTE_APPLY_RECONCILIATION_RECEIPTS",
        "source_sha": source_sha,
        "live_remote_requery_performed_by_builder": False,
        "migration": {
            "name": TARGET,
            "git_blob_sha": blob(MIGRATION),
            "sha256": sha256(MIGRATION),
            "remote_applied_exactly_once": True,
            "remote_version": REMOTE_VERSION,
        },
        "captured_pre_apply_receipt": authority.get("fresh_post_stage88_merge_pre_apply_receipt"),
        "captured_apply_receipt": apply_receipt,
        "captured_post_apply_receipt": post,
        "captured_privilege_reconciliation_receipt": privilege,
        "repository_reconciliation": {
            "migration_ledger_git_blob_sha": blob(LEDGER),
            "security_definer_authority_git_blob_sha": blob(EXPOSURE),
            "repo_only_target_divergence_present": False,
            "remote_terms_security_definer_exposure_count": 3,
        },
        "legal_boundary": {
            "terms_acceptance_versioning": "OPEN",
            "terms_candidate_approved": False,
            "terms_candidate_published": False,
            "terms_registry_rows": 0,
            "acceptance_ledger_rows": 0,
            "legal_terms_gate_ready": False,
            "controlled_launch_promoted": False,
            "paid_media_promoted": False,
        },
        "next_after_green": authority.get("next_after_green"),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("STAGE89_TERMS_ACCEPTANCE_REMOTE_APPLY_RECONCILIATION=PASS")
    print("REMOTE_MIGRATION_APPLIED_EXACTLY_ONCE=true")
    print(f"REMOTE_VERSION={REMOTE_VERSION}")
    print("TERMS_REGISTRY_ROWS=0")
    print("ACCEPTANCE_LEDGER_ROWS=0")
    print("LEGAL_TERMS_GATE_READY=false")


if __name__ == "__main__":
    main()
