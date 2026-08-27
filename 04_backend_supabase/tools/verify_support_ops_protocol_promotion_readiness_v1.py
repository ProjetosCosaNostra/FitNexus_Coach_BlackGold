#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUTHORITY = ROOT / "04_backend_supabase/operations/SUPPORT_OPS_PROTOCOL_PROMOTION_READINESS_V1.json"
CANDIDATE = ROOT / "04_backend_supabase/operations/candidates/SUPPORT_OPS_PROTOCOL_CANDIDATE.sql"
LEDGER = ROOT / "04_backend_supabase/migration_ledger_authority.json"
OPEN_DECISIONS = ROOT / "10_compliance/drafts/COMPLIANCE_OPEN_DECISIONS.json"


def fail(message: str) -> None:
    raise SystemExit(f"SUPPORT_OPS_PROTOCOL_PROMOTION_READINESS_V1=FAIL\nDETAIL={message}")


def git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(f"blob {len(raw)}\0".encode("utf-8") + raw).hexdigest()


def main() -> int:
    authority = json.loads(AUTHORITY.read_text(encoding="utf-8"))
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    decisions = json.loads(OPEN_DECISIONS.read_text(encoding="utf-8"))
    candidate_raw = CANDIDATE.read_bytes()
    candidate = candidate_raw.decode("utf-8")

    if authority.get("schema_version") != 1:
        fail("authority schema drift")
    if authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("project_ref drift")
    if authority.get("baseline_main_sha") != "0cbdecabc180c939132dcc839417f0d746ea336d":
        fail("baseline main drift")

    candidate_meta = authority.get("candidate", {})
    if candidate_meta.get("git_blob_sha") != git_blob_sha(candidate_raw):
        fail("candidate blob drift")
    if candidate_meta.get("git_blob_sha") != "d9f4496ef4daee43afc5eb8a9f355e3659df97bb":
        fail("candidate exact blob pin drift")
    if candidate_meta.get("target_migration_name") != "support_ops_protocol":
        fail("target migration name drift")
    if candidate_meta.get("exact_candidate_bytes_required") is not True:
        fail("exact candidate bytes must remain required")

    required_sql = (
        "create table if not exists public.support_requests",
        "create table if not exists public.support_request_events",
        "support_ingest_email_v1",
        "support_record_event_v1",
        "enable row level security",
        "to service_role",
    )
    low = candidate.lower()
    for marker in required_sql:
        if marker.lower() not in low:
            fail(f"candidate SQL marker missing: {marker}")

    receipt = authority.get("remote_read_only_receipt", {})
    if receipt.get("query_was_read_only") is not True or receipt.get("remote_mutation_performed") is not False:
        fail("remote receipt mutation boundary drift")
    for key in (
        "support_requests_table_exists",
        "support_request_events_table_exists",
        "support_ingest_email_v1_exists",
        "support_record_event_v1_exists",
    ):
        if receipt.get(key) is not False:
            fail(f"remote absence receipt drift: {key}")

    boundary = authority.get("promotion_boundary", {})
    forbidden_true = (
        "repo_only_promotion_performed",
        "migration_ledger_repo_only_declaration_present",
        "remote_supabase_apply_allowed",
        "gmail_mutation_allowed",
        "automatic_outbound_email_allowed",
        "terms_publication_allowed",
        "billing_activation_allowed",
        "production_deployment_allowed",
    )
    for key in forbidden_true:
        if boundary.get(key) is not False:
            fail(f"boundary must remain false: {key}")
    if boundary.get("remote_apply_count") != 0:
        fail("remote apply count must remain zero")

    repo_only = {
        row.get("name")
        for row in ledger.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    }
    if "support_ops_protocol" in repo_only:
        fail("repo-only promotion already declared; readiness authority stale")

    open_map = {item.get("id"): item.get("state") for item in decisions.get("unresolved", []) if isinstance(item, dict)}
    if open_map.get("DSR_STABLE_PUBLIC_ROUTE") != "OPEN":
        fail("DSR_STABLE_PUBLIC_ROUTE must remain OPEN")
    if open_map.get("DSR_CONTROLLED_TESTS") != "OPEN":
        fail("DSR_CONTROLLED_TESTS must remain OPEN")

    progress = authority.get("commercial_progress", {})
    if progress.get("credit_percent_points") != 0 or progress.get("management_estimate_percent") != 74:
        fail("commercial progress boundary drift")

    print("SUPPORT_OPS_PROTOCOL_PROMOTION_READINESS_V1=PASS")
    print("REMOTE_ABSENCE_CONFIRMED=true")
    print("REPO_ONLY_PROMOTION_PERFORMED=false")
    print("REMOTE_APPLY_ALLOWED=false")
    print("REMOTE_APPLY_COUNT=0")
    print("COMMERCIAL_PROGRESS_CREDIT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
