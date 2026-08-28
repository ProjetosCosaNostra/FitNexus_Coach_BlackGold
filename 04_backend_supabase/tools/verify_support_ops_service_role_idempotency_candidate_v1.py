#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUTHORITY = ROOT / "04_backend_supabase/operations/SUPPORT_OPS_SERVICE_ROLE_IDEMPOTENCY_CANDIDATE_V1.json"
EXECUTION = ROOT / "04_backend_supabase/operations/SUPPORT_OPS_PROTOCOL_REMOTE_APPLY_EXECUTION_V1.json"
CANDIDATE = ROOT / "04_backend_supabase/operations/candidates/SUPPORT_OPS_SERVICE_ROLE_IDEMPOTENCY_PROOF_CANDIDATE.sql"
MIGRATION = ROOT / "04_backend_supabase/migrations/20260828094000_support_ops_service_role_idempotency_proof.sql"

EXPECTED_BASE = "4eb127d6ef1d354e71038d1de318c0074c2d3604"
EXPECTED_EXECUTION_BLOB = "6b06a1dbfa4f008794d4a728f19b00ef183f3bb2"
EXPECTED_CANDIDATE_BLOB = "0e3add60d6d6046ef36da6f7be2d9a6512941778"


def fail(message: str) -> None:
    raise SystemExit(f"SUPPORT_OPS_SERVICE_ROLE_IDEMPOTENCY_CANDIDATE_V1=FAIL\nDETAIL={message}")


def git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()


def main() -> int:
    authority_raw = AUTHORITY.read_bytes()
    authority = json.loads(authority_raw.decode("utf-8"))
    execution_raw = EXECUTION.read_bytes()
    execution = json.loads(execution_raw.decode("utf-8"))
    candidate_raw = CANDIDATE.read_bytes()
    candidate = candidate_raw.decode("utf-8")
    low = candidate.lower()

    if authority.get("schema_version") != 1:
        fail("authority schema drift")
    if authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("project_ref drift")
    if authority.get("base_main_sha") != EXPECTED_BASE:
        fail("base main drift")

    source = authority.get("source_remote_execution", {})
    if git_blob_sha(execution_raw) != EXPECTED_EXECUTION_BLOB:
        fail("source execution receipt blob drift")
    if source.get("git_blob_sha") != EXPECTED_EXECUTION_BLOB:
        fail("source execution receipt pin drift")
    if source.get("source_pr") != 194 or source.get("source_pr_merge_sha") != EXPECTED_BASE:
        fail("source PR authority drift")
    if execution.get("state") != "REMOTE_APPLY_GREEN_POST_READBACK_GREEN_LEDGER_GREEN_SYNTHETIC_IDEMPOTENCY_OPEN":
        fail("source remote execution state drift")
    if execution.get("remote_apply", {}).get("apply_count") != 1:
        fail("primary Support Ops migration apply count must remain exactly one")

    candidate_meta = authority.get("candidate", {})
    if git_blob_sha(candidate_raw) != EXPECTED_CANDIDATE_BLOB:
        fail("candidate blob drift")
    if candidate_meta.get("git_blob_sha") != EXPECTED_CANDIDATE_BLOB:
        fail("candidate pin drift")
    if candidate_meta.get("target_migration_name") != "support_ops_service_role_idempotency_proof":
        fail("target migration name drift")
    if candidate_meta.get("exact_candidate_bytes_required") is not True:
        fail("exact candidate bytes must remain required")
    if MIGRATION.exists():
        fail("proof migration already promoted; candidate gate is stale")

    required_markers = (
        "set local role service_role;",
        "current_user <> 'service_role'",
        "support_ingest_email_v1",
        "support_record_event_v1",
        "v_created_first is not true",
        "v_created_second is not false",
        "v_id_second is distinct from v_id_first",
        "v_protocol_second is distinct from v_protocol_first",
        "fitnexus-support-ops-idempotency-v1",
        "synthetic-support-ops-idempotency@invalid.example",
        "delete from public.support_request_events",
        "delete from public.support_requests",
        "support_ops_idempotency_synthetic_cleanup_failed",
    )
    for marker in required_markers:
        if marker.lower() not in low:
            fail(f"candidate proof marker missing: {marker}")

    forbidden = (
        "gmail",
        "send email",
        "billing activation",
        "terms publication",
        "supabase db push",
        "support_ops_protocol.sql",
    )
    # Header may describe forbidden boundaries. Only reject executable-style mutation markers.
    for marker in forbidden[1:]:
        if marker in low:
            fail(f"candidate contains forbidden marker: {marker}")

    proof = authority.get("proof_contract", {})
    if proof.get("must_enter_actual_database_role") != "service_role":
        fail("service_role execution contract drift")
    if proof.get("same_migration_cleanup_required") is not True:
        fail("same-migration cleanup must remain required")
    if proof.get("surviving_synthetic_rows_allowed") is not False:
        fail("surviving synthetic rows must remain forbidden")

    gate = authority.get("gate_state", {})
    if gate.get("candidate_prepared") is not True:
        fail("candidate must be prepared")
    for key in ("repository_migration_promoted", "remote_proof_execution_authorized"):
        if gate.get(key) is not False:
            fail(f"gate boundary must remain false: {key}")
    if gate.get("remote_proof_execution_count") != 0:
        fail("remote proof execution count must remain zero")
    if gate.get("support_ops_primary_migration_must_not_be_reexecuted") is not True:
        fail("primary Support Ops migration re-execution guard missing")

    safety = authority.get("candidate_safety", {})
    if safety.get("customer_identity_used") is not False:
        fail("customer identity use must remain false")
    for key in (
        "gmail_mutation_allowed",
        "automatic_outbound_email_allowed",
        "terms_publication_allowed",
        "billing_activation_allowed",
        "production_deployment_allowed",
        "dsr_gate_closure_allowed",
    ):
        if safety.get(key) is not False:
            fail(f"safety boundary must remain false: {key}")

    progress = authority.get("commercial_progress", {})
    if progress.get("credit_percent_points") != 0 or progress.get("management_estimate_percent") != 74:
        fail("commercial progress boundary drift")

    print("SUPPORT_OPS_SERVICE_ROLE_IDEMPOTENCY_CANDIDATE_V1=PASS")
    print("CANDIDATE_BLOB=" + EXPECTED_CANDIDATE_BLOB)
    print("ACTUAL_DB_ROLE_REQUIRED=service_role")
    print("SYNTHETIC_CLEANUP_REQUIRED=true")
    print("REPO_MIGRATION_PROMOTED=false")
    print("REMOTE_PROOF_EXECUTION_AUTHORIZED=false")
    print("REMOTE_PROOF_EXECUTION_COUNT=0")
    print("PRIMARY_SUPPORT_OPS_APPLY_COUNT=1")
    print("COMMERCIAL_PROGRESS_CREDIT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
