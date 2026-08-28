#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUTH_PATH = ROOT / "04_backend_supabase/operations/SUPPORT_OPS_SERVICE_ROLE_IDEMPOTENCY_REPO_ONLY_PROMOTION_V1.json"
CANDIDATE_PATH = ROOT / "04_backend_supabase/operations/candidates/SUPPORT_OPS_SERVICE_ROLE_IDEMPOTENCY_PROOF_CANDIDATE.sql"
MIGRATION_PATH = ROOT / "04_backend_supabase/migrations/20260828094000_support_ops_service_role_idempotency_proof.sql"
LEDGER_PATH = ROOT / "04_backend_supabase/migration_ledger_authority.json"
SOURCE_AUTH_PATH = ROOT / "04_backend_supabase/operations/SUPPORT_OPS_SERVICE_ROLE_IDEMPOTENCY_CANDIDATE_V1.json"
WORKFLOW_PATH = ROOT / ".github/workflows/support_ops_service_role_idempotency_repo_only_promotion_v1.yml"

EXPECTED_BASE = "8bd9a93d79a7d66d3100d348cab6a858820bea37"
EXPECTED_SOURCE_AUTH_BLOB = "7bd272578d459790d35b327d951bb7c52b1a4398"
EXPECTED_PROOF_BLOB = "0e3add60d6d6046ef36da6f7be2d9a6512941778"
EXPECTED_LEDGER_BLOB = "34540d90dc2618d04eb95ba8166e7eaeb84f64e6"
PROOF_NAME = "support_ops_service_role_idempotency_proof"
STAGE17_REMOTE_ONLY = {
    "stage17_pricing_guard_indexes_marker",
    "stage17_pricing_advisor_reconciliation",
    "stage17_pricing_advisor_guard",
}


def fail(msg: str) -> None:
    raise SystemExit(f"FAIL: {msg}")


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def require(cond: bool, msg: str) -> None:
    if not cond:
        fail(msg)


def main() -> None:
    auth = json.loads(AUTH_PATH.read_text(encoding="utf-8"))
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    source_auth_bytes = SOURCE_AUTH_PATH.read_bytes()
    candidate = CANDIDATE_PATH.read_bytes()
    migration = MIGRATION_PATH.read_bytes()

    require(auth.get("schema_version") == 1, "authority schema_version")
    require(auth.get("kind") == "SUPPORT_OPS_SERVICE_ROLE_IDEMPOTENCY_REPO_ONLY_PROMOTION", "authority kind")
    require(auth.get("project_ref") == "mceukeondizkwlpfxzgf", "project ref")
    require(auth.get("base_main_sha") == EXPECTED_BASE, "base main sha")

    src = auth["source_candidate_authority"]
    require(src["git_blob_sha"] == EXPECTED_SOURCE_AUTH_BLOB, "source authority pinned blob")
    require(git_blob_sha(source_auth_bytes) == EXPECTED_SOURCE_AUTH_BLOB, "source authority actual blob")
    require(src["source_pr"] == 195, "source PR")
    require(src["source_pr_merge_sha"] == EXPECTED_BASE, "source merge sha")

    promotion = auth["promotion"]
    require(candidate == migration, "candidate and migration bytes differ")
    require(git_blob_sha(candidate) == EXPECTED_PROOF_BLOB, "candidate blob drift")
    require(git_blob_sha(migration) == EXPECTED_PROOF_BLOB, "migration blob drift")
    require(promotion["candidate_git_blob_sha"] == EXPECTED_PROOF_BLOB, "candidate authority blob")
    require(promotion["migration_git_blob_sha"] == EXPECTED_PROOF_BLOB, "migration authority blob")
    require(promotion["migration_name"] == PROOF_NAME, "migration name")
    require(promotion["byte_identical_to_candidate"] is True, "byte identity authority")
    require(promotion["repository_promoted"] is True, "repository promoted")
    require(promotion["remote_applied"] is False, "remote apply must remain false")
    require(promotion["remote_apply_count"] == 0, "remote apply count must be zero")

    sql = candidate.decode("utf-8")
    required_sql = [
        "set local role service_role;",
        "current_user <> 'service_role'",
        "SUPPORT_OPS_IDEMPOTENCY_FIRST_INGEST_NOT_CREATED",
        "SUPPORT_OPS_IDEMPOTENCY_SECOND_INGEST_CREATED_DUPLICATE",
        "SUPPORT_OPS_IDEMPOTENCY_SECOND_INGEST_IDENTITY_DRIFT",
        "support_record_event_v1",
        "delete from public.support_request_events",
        "delete from public.support_requests",
        "SUPPORT_OPS_IDEMPOTENCY_SYNTHETIC_CLEANUP_FAILED",
        "synthetic-support-ops-idempotency@invalid.example",
    ]
    for marker in required_sql:
        require(marker in sql, f"proof SQL marker missing: {marker}")

    ledger_blob = git_blob_sha(LEDGER_PATH.read_bytes())
    require(ledger_blob == EXPECTED_LEDGER_BLOB, "ledger blob drift")
    require(auth["migration_ledger"]["git_blob_sha_after_promotion"] == EXPECTED_LEDGER_BLOB, "authority ledger blob")

    divergences = ledger.get("declared_divergences", [])
    proof_repo_only = [d for d in divergences if d.get("direction") == "repo_only" and d.get("name") == PROOF_NAME]
    require(len(proof_repo_only) == 1, "proof repo_only divergence must exist exactly once")
    remote_only_names = {d.get("name") for d in divergences if d.get("direction") == "remote_only"}
    require(STAGE17_REMOTE_ONLY <= remote_only_names, "historical Stage17 remote_only declarations lost")

    remote_names = [m.get("name") for m in ledger.get("remote_migrations", [])]
    require(remote_names.count("support_ops_protocol") == 1, "primary support_ops_protocol remote row must remain exactly once")
    require(PROOF_NAME not in remote_names, "proof migration must not be claimed remote before execution")

    boundaries = auth["proof_boundaries"]
    require(boundaries["remote_proof_execution_authorized"] is False, "remote proof authorization must remain false")
    require(boundaries["remote_proof_execution_count"] == 0, "remote proof execution count")
    require(boundaries["support_ops_primary_migration_must_not_be_reexecuted"] is True, "primary migration replay guard")
    for key in (
        "gmail_mutation_allowed",
        "automatic_outbound_email_allowed",
        "terms_publication_allowed",
        "billing_activation_allowed",
        "production_deployment_allowed",
        "dsr_gate_closure_allowed",
    ):
        require(boundaries[key] is False, f"boundary must remain false: {key}")

    commercial = auth["commercial_progress"]
    require(commercial["credit_percent_points"] == 0, "commercial credit must be zero")
    require(commercial["management_estimate_percent"] == 74, "commercial management estimate must remain 74")

    next_gate = auth["next_gate"]
    require(next_gate["requires_separate_remote_execution_gate"] is True, "separate remote gate required")
    require(next_gate["requires_fresh_read_only_preflight"] is True, "fresh read-only preflight required")
    require(next_gate["requires_explicit_remote_execution_authorization"] is True, "explicit authorization required")
    require(next_gate["remote_execution_method"] == "Supabase.apply_migration", "remote method")
    require(next_gate["ad_hoc_execute_sql_allowed"] is False, "ad hoc execute_sql must remain denied")
    require(next_gate["synthetic_cleanup_must_be_proven"] is True, "synthetic cleanup proof required")

    workflow = WORKFLOW_PATH.read_text(encoding="utf-8").lower()
    for forbidden in ("supabase db push", "supabase migration up", "apply_migration", "execute_sql"):
        require(forbidden not in workflow, f"workflow contains forbidden mutation marker: {forbidden}")

    print("PASS: Support Ops service-role idempotency repo-only promotion authority is internally consistent")


if __name__ == "__main__":
    main()
