#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUTH = ROOT / "04_backend_supabase/operations/SUPPORT_OPS_SERVICE_ROLE_IDEMPOTENCY_REMOTE_EXECUTION_GATE_V1.json"
PROMO = ROOT / "04_backend_supabase/operations/SUPPORT_OPS_SERVICE_ROLE_IDEMPOTENCY_REPO_ONLY_PROMOTION_V1.json"
MIG = ROOT / "04_backend_supabase/migrations/20260828094000_support_ops_service_role_idempotency_proof.sql"
LEDGER = ROOT / "04_backend_supabase/migration_ledger_authority.json"


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(msg)


a = json.loads(AUTH.read_text(encoding="utf-8"))
ledger = json.loads(LEDGER.read_text(encoding="utf-8"))

require(a["schema_version"] == 1, "schema_version")
require(a["kind"] == "SUPPORT_OPS_SERVICE_ROLE_IDEMPOTENCY_REMOTE_EXECUTION_GATE", "kind")
require(a["project_ref"] == "mceukeondizkwlpfxzgf", "project_ref")
require(a["base_main_sha"] == "ef8e62e5d80fd478f34d5776bb238fff63c46645", "base_main_sha")
require(git_blob_sha(PROMO) == "f4906148b2ba84dfefdb2cbd0d48548384095801", "promotion blob drift")
require(git_blob_sha(MIG) == "0e3add60d6d6046ef36da6f7be2d9a6512941778", "migration blob drift")
require(git_blob_sha(LEDGER) == "34540d90dc2618d04eb95ba8166e7eaeb84f64e6", "ledger blob drift")

m = a["migration"]
require(m["name"] == "support_ops_service_role_idempotency_proof", "migration name")
require(m["repository_promoted"] is True, "repository not promoted")
require(m["remote_applied"] is False and m["remote_apply_count"] == 0, "premature remote apply")

pre = a["fresh_remote_preflight"]
require(pre["query_was_read_only"] is True, "preflight not read-only")
require(pre["execution_user"] == "supabase_read_only_user", "unexpected preflight user")
require(pre["proof_migration_present"] is False, "proof migration already remote")
require(pre["synthetic_request_rows"] == 0 and pre["synthetic_event_rows"] == 0, "synthetic residue")
require(pre["service_role_ingest_execute"] is True and pre["service_role_record_execute"] is True, "service role privilege missing")
require(pre["anon_ingest_execute"] is False and pre["authenticated_ingest_execute"] is False, "public privilege drift")
require(pre["remote_mutation_performed"] is False, "preflight mutated remote")

g = a["gate_state"]
require(g["gate_prepared"] is True, "gate not prepared")
require(g["remote_proof_execution_authorized"] is False, "execution prematurely authorized")
require(g["remote_proof_execution_count"] == 0, "execution count nonzero")
require(g["required_execution_method"] == "Supabase.apply_migration", "wrong execution method")
require(g["ad_hoc_execute_sql_allowed"] is False, "ad hoc SQL allowed")
require(g["exact_migration_blob_required"] is True, "exact blob not required")
require(g["support_ops_primary_migration_must_not_be_reexecuted"] is True, "primary reexecution not denied")
require(g["post_apply_migration_readback_required"] is True, "post-apply readback missing")
require(g["synthetic_cleanup_readback_required"] is True, "cleanup readback missing")
require(g["post_apply_ledger_reconciliation_required"] is True, "ledger reconciliation missing")
require(g["explicit_user_authorization_required_after_green_merge"] is True, "explicit authorization missing")

repo_only = [d for d in ledger["declared_divergences"] if d.get("direction") == "repo_only" and d.get("name") == m["name"]]
require(len(repo_only) == 1, "repo_only divergence missing/duplicate")
remote_names = [x["name"] for x in ledger["remote_migrations"]]
require("support_ops_protocol" in remote_names, "primary remote migration missing")
require(m["name"] not in remote_names, "proof migration incorrectly claimed remote")

b = a["boundaries"]
require(all(v is False for v in b.values()), "side-effect boundary drift")
require(a["commercial_progress"] == {"credit_percent_points": 0, "management_estimate_percent": 74}, "commercial credit drift")
require(a["state"] == "REMOTE_PROOF_GATE_PREPARED_EXECUTION_NOT_AUTHORIZED", "state")
print("SUPPORT_OPS_SERVICE_ROLE_IDEMPOTENCY_REMOTE_EXECUTION_GATE_V1=PASS")
