#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUTHORITY = ROOT / "04_backend_supabase/operations/SUPPORT_OPS_PROTOCOL_REMOTE_APPLY_GATE_V1.json"
REPO_ONLY_AUTHORITY = ROOT / "04_backend_supabase/operations/SUPPORT_OPS_PROTOCOL_REPO_ONLY_PROMOTION_V1.json"
MIGRATION = ROOT / "04_backend_supabase/migrations/20260827190000_support_ops_protocol.sql"
LEDGER = ROOT / "04_backend_supabase/migration_ledger_authority.json"
OPEN_DECISIONS = ROOT / "10_compliance/drafts/COMPLIANCE_OPEN_DECISIONS.json"

EXPECTED_BASE_MAIN = "0013ff91060ca9983605e9ac293a7de19f5aae69"
EXPECTED_REPO_ONLY_AUTHORITY_BLOB = "0f0fd4a41cfa62f9e86bbc640380c889432f9be1"
EXPECTED_MIGRATION_BLOB = "d9f4496ef4daee43afc5eb8a9f355e3659df97bb"
EXPECTED_LEDGER_BLOB = "6e2e8a815485d8975c08a2bb07a5583be772977f"


def fail(message: str) -> None:
    raise SystemExit(f"SUPPORT_OPS_PROTOCOL_REMOTE_APPLY_GATE_V1=FAIL\nDETAIL={message}")


def git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(f"blob {len(raw)}\0".encode("utf-8") + raw).hexdigest()


def main() -> int:
    authority = json.loads(AUTHORITY.read_text(encoding="utf-8"))
    repo_only_raw = REPO_ONLY_AUTHORITY.read_bytes()
    migration_raw = MIGRATION.read_bytes()
    ledger_raw = LEDGER.read_bytes()
    ledger = json.loads(ledger_raw.decode("utf-8"))
    decisions = json.loads(OPEN_DECISIONS.read_text(encoding="utf-8"))

    if authority.get("schema_version") != 1:
        fail("authority schema drift")
    if authority.get("kind") != "SUPPORT_OPS_PROTOCOL_REMOTE_APPLY_GATE":
        fail("authority kind drift")
    if authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("project_ref drift")
    if authority.get("base_main_sha") != EXPECTED_BASE_MAIN:
        fail("base main SHA drift")

    if git_blob_sha(repo_only_raw) != EXPECTED_REPO_ONLY_AUTHORITY_BLOB:
        fail("repo-only authority blob drift")
    if authority.get("repo_only_promotion_authority", {}).get("git_blob_sha") != EXPECTED_REPO_ONLY_AUTHORITY_BLOB:
        fail("repo-only authority pin drift")

    if git_blob_sha(migration_raw) != EXPECTED_MIGRATION_BLOB:
        fail("migration blob drift")
    migration = authority.get("migration", {})
    if migration.get("name") != "support_ops_protocol":
        fail("migration name drift")
    if migration.get("path") != "04_backend_supabase/migrations/20260827190000_support_ops_protocol.sql":
        fail("migration path drift")
    if migration.get("git_blob_sha") != EXPECTED_MIGRATION_BLOB:
        fail("migration pin drift")
    if migration.get("repository_promoted") is not True or migration.get("remote_applied") is not False:
        fail("migration repo/remote state drift")

    if git_blob_sha(ledger_raw) != EXPECTED_LEDGER_BLOB:
        fail("migration ledger blob drift")
    if authority.get("migration_ledger", {}).get("git_blob_sha") != EXPECTED_LEDGER_BLOB:
        fail("migration ledger pin drift")

    divergences = [row for row in ledger.get("declared_divergences", []) if isinstance(row, dict)]
    repo_only = [row for row in divergences if row.get("direction") == "repo_only" and row.get("name") == "support_ops_protocol"]
    if len(repo_only) != 1:
        fail("support_ops_protocol repo_only declaration must exist exactly once")

    remote_names = {row.get("name") for row in ledger.get("remote_migrations", []) if isinstance(row, dict)}
    if "support_ops_protocol" in remote_names:
        fail("repository ledger already claims support_ops_protocol remote")

    preflight = authority.get("fresh_remote_preflight", {})
    if preflight.get("query_was_read_only") is not True or preflight.get("remote_mutation_performed") is not False:
        fail("fresh preflight mutation boundary drift")
    for key in (
        "support_ops_protocol_migration_exists",
        "support_requests_table_exists",
        "support_request_events_table_exists",
        "support_ingest_email_v1_exists",
        "support_record_event_v1_exists",
    ):
        if preflight.get(key) is not False:
            fail(f"fresh remote absence proof drift: {key}")

    gate = authority.get("gate_state", {})
    if gate.get("gate_prepared") is not True:
        fail("gate must be prepared")
    if gate.get("remote_apply_authorized") is not False:
        fail("remote apply must remain unauthorized in gate-preparation PR")
    if gate.get("remote_apply_count") != 0:
        fail("remote apply count must remain zero")
    if gate.get("required_apply_method") != "Supabase.apply_migration":
        fail("required apply method drift")
    if gate.get("ad_hoc_execute_sql_allowed") is not False:
        fail("ad hoc execute_sql must remain denied")
    for key in (
        "requires_exact_migration_blob",
        "requires_post_apply_readback",
        "requires_post_apply_ledger_reconciliation",
        "requires_synthetic_idempotency_test_after_apply",
    ):
        if gate.get(key) is not True:
            fail(f"required gate control missing: {key}")

    boundaries = authority.get("boundaries", {})
    for key in (
        "gmail_mutation_allowed",
        "automatic_outbound_email_allowed",
        "terms_publication_allowed",
        "billing_activation_allowed",
        "production_deployment_allowed",
        "dsr_gate_closure_allowed",
    ):
        if boundaries.get(key) is not False:
            fail(f"forbidden boundary must remain false: {key}")

    progress = authority.get("commercial_progress", {})
    if progress.get("credit_percent_points") != 0 or progress.get("management_estimate_percent") != 74:
        fail("commercial progress boundary drift")

    open_map = {item.get("id"): item.get("state") for item in decisions.get("unresolved", []) if isinstance(item, dict)}
    if open_map.get("DSR_STABLE_PUBLIC_ROUTE") != "OPEN":
        fail("DSR_STABLE_PUBLIC_ROUTE must remain OPEN")
    if open_map.get("DSR_CONTROLLED_TESTS") != "OPEN":
        fail("DSR_CONTROLLED_TESTS must remain OPEN")

    print("SUPPORT_OPS_PROTOCOL_REMOTE_APPLY_GATE_V1=PASS")
    print("FRESH_REMOTE_ABSENCE_CONFIRMED=true")
    print("REPO_ONLY_MIGRATION_BLOB=" + EXPECTED_MIGRATION_BLOB)
    print("REMOTE_APPLY_AUTHORIZED=false")
    print("REMOTE_APPLY_COUNT=0")
    print("REQUIRED_APPLY_METHOD=Supabase.apply_migration")
    print("AD_HOC_EXECUTE_SQL_ALLOWED=false")
    print("COMMERCIAL_PROGRESS_CREDIT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
