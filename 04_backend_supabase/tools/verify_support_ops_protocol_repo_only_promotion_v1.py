#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUTHORITY = ROOT / "04_backend_supabase/operations/SUPPORT_OPS_PROTOCOL_REPO_ONLY_PROMOTION_V1.json"
READINESS = ROOT / "04_backend_supabase/operations/SUPPORT_OPS_PROTOCOL_PROMOTION_READINESS_V1.json"
CANDIDATE = ROOT / "04_backend_supabase/operations/candidates/SUPPORT_OPS_PROTOCOL_CANDIDATE.sql"
MIGRATION = ROOT / "04_backend_supabase/migrations/20260827190000_support_ops_protocol.sql"
LEDGER = ROOT / "04_backend_supabase/migration_ledger_authority.json"
OPEN_DECISIONS = ROOT / "10_compliance/drafts/COMPLIANCE_OPEN_DECISIONS.json"
WORKFLOW = ROOT / ".github/workflows/support_ops_protocol_repo_only_promotion_v1.yml"

EXPECTED_BLOB = "d9f4496ef4daee43afc5eb8a9f355e3659df97bb"
EXPECTED_LEDGER_BLOB = "6e2e8a815485d8975c08a2bb07a5583be772977f"
EXPECTED_READINESS_BLOB = "904c45669b92c1a00f7554752c35f1ddfe1bb784"
EXPECTED_BASE_MAIN = "04161a3c35528d3bc3298a8627d9f2411d6afb00"


def fail(message: str) -> None:
    raise SystemExit(f"SUPPORT_OPS_PROTOCOL_REPO_ONLY_PROMOTION_V1=FAIL\nDETAIL={message}")


def git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(f"blob {len(raw)}\0".encode("utf-8") + raw).hexdigest()


def main() -> int:
    authority_raw = AUTHORITY.read_bytes()
    authority = json.loads(authority_raw.decode("utf-8"))
    readiness_raw = READINESS.read_bytes()
    readiness = json.loads(readiness_raw.decode("utf-8"))
    candidate_raw = CANDIDATE.read_bytes()
    migration_raw = MIGRATION.read_bytes()
    ledger_raw = LEDGER.read_bytes()
    ledger = json.loads(ledger_raw.decode("utf-8"))
    decisions = json.loads(OPEN_DECISIONS.read_text(encoding="utf-8"))
    workflow = WORKFLOW.read_text(encoding="utf-8")

    if authority.get("schema_version") != 1:
        fail("authority schema drift")
    if authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("project_ref drift")
    if authority.get("base_main_sha") != EXPECTED_BASE_MAIN:
        fail("base main SHA drift")

    if git_blob_sha(readiness_raw) != EXPECTED_READINESS_BLOB:
        fail("readiness authority blob drift")
    if authority.get("readiness_authority", {}).get("git_blob_sha") != EXPECTED_READINESS_BLOB:
        fail("readiness authority pin drift")
    if readiness.get("candidate", {}).get("git_blob_sha") != EXPECTED_BLOB:
        fail("readiness candidate pin drift")

    if candidate_raw != migration_raw:
        fail("candidate and migration bytes differ")
    if git_blob_sha(candidate_raw) != EXPECTED_BLOB:
        fail("candidate blob drift")
    if git_blob_sha(migration_raw) != EXPECTED_BLOB:
        fail("migration blob drift")

    migration_meta = authority.get("migration", {})
    if migration_meta.get("name") != "support_ops_protocol":
        fail("migration name drift")
    if migration_meta.get("path") != "04_backend_supabase/migrations/20260827190000_support_ops_protocol.sql":
        fail("migration path drift")
    if migration_meta.get("git_blob_sha") != EXPECTED_BLOB:
        fail("migration authority blob pin drift")
    if migration_meta.get("byte_identical_to_candidate") is not True:
        fail("byte identity declaration missing")
    if migration_meta.get("repository_promoted") is not True or migration_meta.get("remote_applied") is not False:
        fail("repository/remote promotion boundary drift")

    if git_blob_sha(ledger_raw) != EXPECTED_LEDGER_BLOB:
        fail("migration ledger blob drift")
    if authority.get("migration_ledger", {}).get("git_blob_sha_after_declaration") != EXPECTED_LEDGER_BLOB:
        fail("migration ledger pin drift")

    divergences = [row for row in ledger.get("declared_divergences", []) if isinstance(row, dict)]
    repo_only = [row for row in divergences if row.get("direction") == "repo_only" and row.get("name") == "support_ops_protocol"]
    if len(repo_only) != 1:
        fail("support_ops_protocol repo_only declaration must exist exactly once")

    required_remote_only = {
        "stage17_pricing_guard_indexes_marker",
        "stage17_pricing_advisor_reconciliation",
        "stage17_pricing_advisor_guard",
    }
    actual_remote_only = {row.get("name") for row in divergences if row.get("direction") == "remote_only"}
    if not required_remote_only.issubset(actual_remote_only):
        fail("historical Stage17 remote_only declarations were not preserved")

    remote_names = {row.get("name") for row in ledger.get("remote_migrations", []) if isinstance(row, dict)}
    if "support_ops_protocol" in remote_names:
        fail("ledger claims support_ops_protocol is already remote")

    receipt = authority.get("remote_read_only_receipt", {})
    if receipt.get("query_was_read_only") is not True or receipt.get("remote_mutation_performed") is not False:
        fail("remote absence receipt boundary drift")
    for key in (
        "support_requests_table_exists",
        "support_request_events_table_exists",
        "support_ingest_email_v1_exists",
        "support_record_event_v1_exists",
    ):
        if receipt.get(key) is not False:
            fail(f"remote absence receipt drift: {key}")

    boundary = authority.get("boundaries", {})
    if boundary.get("repo_only_promotion_performed") is not True:
        fail("repo-only promotion must be true")
    for key in (
        "remote_supabase_apply_allowed",
        "gmail_mutation_allowed",
        "automatic_outbound_email_allowed",
        "terms_publication_allowed",
        "billing_activation_allowed",
        "production_deployment_allowed",
        "dsr_gate_closure_allowed",
    ):
        if boundary.get(key) is not False:
            fail(f"forbidden boundary must remain false: {key}")
    if boundary.get("remote_apply_count") != 0:
        fail("remote apply count must remain zero")

    progress = authority.get("commercial_progress", {})
    if progress.get("credit_percent_points") != 0 or progress.get("management_estimate_percent") != 74:
        fail("commercial progress boundary drift")

    next_gate = authority.get("next_gate", {})
    if next_gate.get("requires_separate_pr_and_authority") is not True:
        fail("separate remote apply gate must remain required")
    if next_gate.get("requires_fresh_read_only_preflight") is not True:
        fail("fresh remote preflight must remain required")
    if next_gate.get("ad_hoc_execute_sql_allowed") is not False:
        fail("ad hoc execute_sql must remain denied")

    open_map = {item.get("id"): item.get("state") for item in decisions.get("unresolved", []) if isinstance(item, dict)}
    if open_map.get("DSR_STABLE_PUBLIC_ROUTE") != "OPEN":
        fail("DSR_STABLE_PUBLIC_ROUTE must remain OPEN")
    if open_map.get("DSR_CONTROLLED_TESTS") != "OPEN":
        fail("DSR_CONTROLLED_TESTS must remain OPEN")

    workflow_low = workflow.lower()
    for forbidden in ("supabase db push", "supabase migration up", "execute_sql", "apply_migration", "gmail"):
        if forbidden in workflow_low:
            fail(f"workflow contains forbidden side-effect marker: {forbidden}")

    print("SUPPORT_OPS_PROTOCOL_REPO_ONLY_PROMOTION_V1=PASS")
    print("CANDIDATE_MIGRATION_BYTE_IDENTICAL=true")
    print("MIGRATION_BLOB=" + EXPECTED_BLOB)
    print("LEDGER_REPO_ONLY_DECLARED=true")
    print("REMOTE_SUPABASE_APPLY_ALLOWED=false")
    print("REMOTE_APPLY_COUNT=0")
    print("GMAIL_MUTATION=false")
    print("DSR_STABLE_PUBLIC_ROUTE=OPEN")
    print("COMMERCIAL_PROGRESS_CREDIT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
