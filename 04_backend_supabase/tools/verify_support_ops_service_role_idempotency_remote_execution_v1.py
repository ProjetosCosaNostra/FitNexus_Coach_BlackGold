#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RECEIPT = ROOT / "04_backend_supabase/operations/SUPPORT_OPS_SERVICE_ROLE_IDEMPOTENCY_REMOTE_EXECUTION_V1.json"
GATE = ROOT / "04_backend_supabase/operations/SUPPORT_OPS_SERVICE_ROLE_IDEMPOTENCY_REMOTE_EXECUTION_GATE_V1.json"
MIG = ROOT / "04_backend_supabase/migrations/20260828094000_support_ops_service_role_idempotency_proof.sql"
LEDGER = ROOT / "04_backend_supabase/migration_ledger_authority.json"


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(msg)

r = json.loads(RECEIPT.read_text(encoding="utf-8"))
ledger = json.loads(LEDGER.read_text(encoding="utf-8"))

require(r["schema_version"] == 1, "schema_version")
require(r["kind"] == "SUPPORT_OPS_SERVICE_ROLE_IDEMPOTENCY_REMOTE_EXECUTION", "kind")
require(r["project_ref"] == "mceukeondizkwlpfxzgf", "project_ref")
require(r["source_gate"]["pr"] == 197, "source PR")
require(r["source_gate"]["merge_sha"] == "8321ab01760f243012f0173f6031dd2cd530fc3e", "source merge")
require(git_blob_sha(GATE) == "8fc9821046c9880e55042a5eb3d8bc8b94e82a37", "gate blob drift")
require(git_blob_sha(MIG) == "0e3add60d6d6046ef36da6f7be2d9a6512941778", "migration blob drift")
require(git_blob_sha(LEDGER) == "23d419616878d3092583b688590bfaca78e07b28", "ledger blob drift")

a = r["authorization"]
require(a["explicit_user_authorization"] is True, "authorization")
require(a["authorization_text"] == "AUTORIZAR EXECUÇÃO REMOTA TESTE SINTÉTICO SUPPORT OPS", "authorization text")

m = r["migration"]
require(m["name"] == "support_ops_service_role_idempotency_proof", "migration name")
require(m["execution_method"] == "Supabase.apply_migration", "execution method")
require(m["remote_apply_success"] is True and m["remote_apply_count"] == 1, "apply result")
require(m["observed_remote_version"] == "20260828115427", "remote version")

p = r["proof_result"]
require(p["sequential_idempotency"] == "GREEN", "sequential idempotency")
for key in [
    "first_ingest_created_new_required_and_passed",
    "second_ingest_created_new_false_required_and_passed",
    "same_request_id_required_and_passed",
    "same_protocol_number_required_and_passed",
    "received_event_cardinality_one_required_and_passed",
    "status_transition_received_to_triaged_required_and_passed",
    "migration_transaction_completed",
]:
    require(p[key] is True, key)
require(p["concurrency_idempotency"] == "NOT_PROVEN", "concurrency state")
require(p["concurrency_claim_allowed"] is False, "concurrency claim")

post = r["post_apply_readback"]
require(post["migration_present"] is True, "migration readback")
require(post["synthetic_request_rows"] == 0 and post["synthetic_event_rows"] == 0, "synthetic residue")
require(post["synthetic_cleanup"] == "GREEN", "cleanup")
require(post["execute_sql_current_user"] == "supabase_read_only_user", "readback user")
require(post["service_role_ingest_execute"] is True and post["service_role_record_execute"] is True, "service role grants")
for key in ["anon_ingest_execute","authenticated_ingest_execute","public_ingest_execute","anon_record_execute","authenticated_record_execute","public_record_execute"]:
    require(post[key] is False, key)
require(post["least_privilege_boundary"] == "GREEN", "least privilege")

rec = r["migration_ledger_reconciliation"]
require(rec["completed"] is True, "ledger reconciliation")
require(rec["repo_only_declaration_removed"] is True, "repo-only removal")
require(rec["remote_migration_record_added"] is True, "remote row add")
require(rec["remote_version"] == "20260828115427", "ledger remote version")
require(rec["historical_stage17_remote_only_divergences_preserved"] == 3, "stage17 divergences")

repo_only = [d for d in ledger["declared_divergences"] if d.get("direction") == "repo_only" and d.get("name") == m["name"]]
require(len(repo_only) == 0, "proof repo_only divergence remains")
remote = [x for x in ledger["remote_migrations"] if x.get("name") == m["name"]]
require(remote == [{"version":"20260828115427","name":"support_ops_service_role_idempotency_proof"}], "proof remote row mismatch")
require(len([d for d in ledger["declared_divergences"] if d.get("direction") == "remote_only" and d.get("name","").startswith("stage17_")]) == 3, "historical divergences drift")

b = r["boundaries"]
require(all(v is False for v in b.values()), "boundary drift")
require(r["commercial_progress"] == {"credit_percent_points":0,"management_estimate_percent":74}, "commercial drift")
require(r["state"] == "SEQUENTIAL_IDEMPOTENCY_GREEN_CLEANUP_GREEN_LEDGER_GREEN_CONCURRENCY_NOT_PROVEN", "state")

print("SUPPORT_OPS_SERVICE_ROLE_IDEMPOTENCY_REMOTE_EXECUTION_V1=PASS")
print("REMOTE_APPLY_COUNT=1")
print("REMOTE_VERSION=20260828115427")
print("SEQUENTIAL_IDEMPOTENCY=GREEN")
print("SYNTHETIC_CLEANUP=GREEN")
print("LEAST_PRIVILEGE=GREEN")
print("MIGRATION_LEDGER_RECONCILIATION=GREEN")
print("CONCURRENCY_IDEMPOTENCY=NOT_PROVEN")
print("COMMERCIAL_PROGRESS_CREDIT=0")
