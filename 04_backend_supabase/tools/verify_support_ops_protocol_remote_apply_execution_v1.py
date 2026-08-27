#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RECEIPT = ROOT / "04_backend_supabase/operations/SUPPORT_OPS_PROTOCOL_REMOTE_APPLY_EXECUTION_V1.json"
LEDGER = ROOT / "04_backend_supabase/migration_ledger_authority.json"
MIGRATION = ROOT / "04_backend_supabase/migrations/20260827190000_support_ops_protocol.sql"
GATE = ROOT / "04_backend_supabase/operations/SUPPORT_OPS_PROTOCOL_REMOTE_APPLY_GATE_V1.json"

EXPECTED_PROJECT_REF = "mceukeondizkwlpfxzgf"
EXPECTED_MIGRATION_BLOB = "d9f4496ef4daee43afc5eb8a9f355e3659df97bb"
EXPECTED_LEDGER_BLOB = "6a856462a1b988da6c37edd44f09d257074add72"
EXPECTED_REMOTE_VERSION = "20260827230306"
EXPECTED_GATE_MERGE = "31866ba974c13ec78455a8be35ad665376a9a9c8"


def fail(message: str) -> None:
    raise SystemExit(f"SUPPORT_OPS_PROTOCOL_REMOTE_APPLY_EXECUTION_V1=FAIL\nDETAIL={message}")


def git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(f"blob {len(raw)}\0".encode("utf-8") + raw).hexdigest()


def main() -> int:
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    ledger_raw = LEDGER.read_bytes()
    ledger = json.loads(ledger_raw.decode("utf-8"))
    migration_raw = MIGRATION.read_bytes()
    gate = json.loads(GATE.read_text(encoding="utf-8"))

    if receipt.get("schema_version") != 1:
        fail("receipt schema drift")
    if receipt.get("project_ref") != EXPECTED_PROJECT_REF:
        fail("project_ref drift")
    source_gate = receipt.get("source_gate", {})
    if source_gate.get("pr") != 193 or source_gate.get("merge_sha") != EXPECTED_GATE_MERGE:
        fail("source gate authority drift")
    if gate.get("project_ref") != EXPECTED_PROJECT_REF:
        fail("merged gate project_ref drift")

    authorization = receipt.get("authorization", {})
    if authorization.get("explicit_user_authorization") is not True:
        fail("explicit authorization evidence missing")
    if authorization.get("authorization_text") != "AUTORIZAR APLICAÇÃO REMOTA SUPPORT OPS":
        fail("authorization text drift")

    remote_apply = receipt.get("remote_apply", {})
    if remote_apply.get("method") != "Supabase.apply_migration":
        fail("remote apply method drift")
    if remote_apply.get("success") is not True or remote_apply.get("apply_count") != 1:
        fail("remote apply success/count drift")
    if remote_apply.get("migration_name") != "support_ops_protocol":
        fail("migration name drift")
    if remote_apply.get("observed_remote_version") != EXPECTED_REMOTE_VERSION:
        fail("remote migration version drift")

    if git_blob_sha(migration_raw) != EXPECTED_MIGRATION_BLOB:
        fail("migration blob drift")
    if source_gate.get("migration_git_blob_sha") != EXPECTED_MIGRATION_BLOB:
        fail("receipt migration blob pin drift")

    readback = receipt.get("post_apply_readback", {})
    required_true = (
        "migration_present",
        "support_requests_table_exists",
        "support_request_events_table_exists",
        "support_ingest_email_v1_exists",
        "support_record_event_v1_exists",
        "support_requests_rls_enabled",
        "support_request_events_rls_enabled",
        "ingest_security_definer",
        "record_security_definer",
        "service_role_ingest_execute",
        "service_role_record_execute",
    )
    for key in required_true:
        if readback.get(key) is not True:
            fail(f"post-apply readback must be true: {key}")
    required_false = (
        "anon_ingest_execute",
        "authenticated_ingest_execute",
        "public_ingest_execute",
        "anon_record_execute",
        "authenticated_record_execute",
        "public_record_execute",
        "anon_support_requests_select",
        "authenticated_support_requests_select",
        "anon_support_request_events_select",
        "authenticated_support_request_events_select",
    )
    for key in required_false:
        if readback.get(key) is not False:
            fail(f"least-privilege readback must be false: {key}")
    if readback.get("support_requests_count_after_apply") != 0 or readback.get("support_request_events_count_after_apply") != 0:
        fail("post-apply tables were not empty before synthetic proof attempt")

    if git_blob_sha(ledger_raw) != EXPECTED_LEDGER_BLOB:
        fail("canonical migration ledger blob drift")
    divergences = [row for row in ledger.get("declared_divergences", []) if isinstance(row, dict)]
    if any(row.get("direction") == "repo_only" and row.get("name") == "support_ops_protocol" for row in divergences):
        fail("support_ops_protocol must no longer be declared repo_only")
    remote_rows = [row for row in ledger.get("remote_migrations", []) if isinstance(row, dict) and row.get("name") == "support_ops_protocol"]
    if remote_rows != [{"version": EXPECTED_REMOTE_VERSION, "name": "support_ops_protocol"}]:
        fail("canonical ledger remote row drift")

    reconciliation = receipt.get("migration_ledger_reconciliation", {})
    if reconciliation.get("completed") is not True:
        fail("ledger reconciliation must be complete")
    if reconciliation.get("ledger_git_blob_sha_after_reconciliation") != EXPECTED_LEDGER_BLOB:
        fail("ledger receipt blob pin drift")

    synthetic = receipt.get("synthetic_idempotency_test", {})
    if synthetic.get("required") is not True or synthetic.get("attempted") is not True:
        fail("synthetic test requirement/attempt evidence missing")
    if synthetic.get("completed") is not False:
        fail("synthetic test must remain explicitly OPEN until a service-role proof exists")
    if synthetic.get("state") != "BLOCKED_BY_READ_ONLY_SQL_EXECUTION_CONTEXT":
        fail("synthetic blocker classification drift")
    evidence = synthetic.get("evidence", {})
    if evidence.get("execute_sql_current_user") != "supabase_read_only_user":
        fail("read-only execution context evidence drift")

    incident = receipt.get("operator_incident", {})
    if incident.get("class") != "BGF-DIRECT-MAIN-ACCIDENTAL-NOOP-WRITE-CLEANED-143":
        fail("operator incident class missing")
    if incident.get("final_tree_content_impact") != "NONE":
        fail("operator incident cleanup not sealed")

    boundaries = receipt.get("boundaries", {})
    for key in (
        "gmail_mutation_performed",
        "automatic_outbound_email_performed",
        "terms_publication_performed",
        "billing_activation_performed",
        "production_deployment_performed",
        "dsr_gate_closed",
    ):
        if boundaries.get(key) is not False:
            fail(f"forbidden boundary crossed: {key}")

    progress = receipt.get("commercial_progress", {})
    if progress.get("credit_percent_points") != 0 or progress.get("management_estimate_percent") != 74:
        fail("commercial progress boundary drift")
    if receipt.get("state") != "REMOTE_APPLY_GREEN_POST_READBACK_GREEN_LEDGER_GREEN_SYNTHETIC_IDEMPOTENCY_OPEN":
        fail("execution state drift")

    print("SUPPORT_OPS_PROTOCOL_REMOTE_APPLY_EXECUTION_V1=PASS")
    print("REMOTE_APPLY_SUCCESS=true")
    print("REMOTE_APPLY_COUNT=1")
    print("REMOTE_VERSION=" + EXPECTED_REMOTE_VERSION)
    print("POST_APPLY_READBACK=GREEN")
    print("MIGRATION_LEDGER_RECONCILIATION=GREEN")
    print("RLS_GRANTS_PROOF=GREEN")
    print("SYNTHETIC_IDEMPOTENCY=OPEN")
    print("SYNTHETIC_BLOCKER=READ_ONLY_SQL_EXECUTION_CONTEXT")
    print("COMMERCIAL_PROGRESS_CREDIT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
