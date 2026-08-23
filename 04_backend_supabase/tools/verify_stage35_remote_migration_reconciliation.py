from __future__ import annotations

import hashlib
import json
from pathlib import Path

from stage35_migration_frontier import state as frontier_state, to_reconciled

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
LEDGER = BACKEND / "migration_ledger_authority.json"
AUTHORITY = BACKEND / "stage35_alert_remote_migration_reconciliation_authority.json"
RECEIPT_MIGRATION = BACKEND / "migrations" / "20260822075500_stage35_alert_delivery_receipt_store.sql"
FIXTURE_MIGRATION = BACKEND / "migrations" / "20260823091500_stage35_alert_delivery_controlled_proof_fixture.sql"
DISPATCHER = BACKEND / "functions" / "student-access-alert-dispatcher" / "index.ts"

BASELINE = "a23dd9d892189b92a633634caf750606504e83ee"
OBSERVED = "2026-08-23T15:56:57.947085Z"
RECEIPT_NAME = "stage35_alert_delivery_receipt_store"
FIXTURE_NAME = "stage35_alert_delivery_controlled_proof_fixture"
RECEIPT_VERSION = "20260823092354"
FIXTURE_VERSION = "20260823145908"
RECEIPT_BLOB = "9f1a625cd316362874aefcfd9e33d64f9ecd173d"
FIXTURE_BLOB = "7d3631fc425903b013606b4a7731eaa273867a9b"
DISPATCHER_BLOB = "0aece761d707d8befb64a0fb89ce495fc50255a0"
FAILURE_CLASS = "BGF-STAGE35-ALERT-REMOTE-LEDGER-RECONCILIATION-311"


def fail(message: str) -> None:
    raise SystemExit(
        "STAGE35_REMOTE_MIGRATION_RECONCILIATION_GUARD=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\nDETAIL={message}"
    )


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to read {path.relative_to(ROOT)}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"expected object: {path.relative_to(ROOT)}")
    return value


def git_blob(path: Path) -> str:
    try:
        data = path.read_bytes()
    except OSError as exc:
        fail(f"unable to read {path.relative_to(ROOT)}: {type(exc).__name__}")
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def require(mapping: dict, expected: dict, label: str) -> None:
    if not isinstance(mapping, dict):
        fail(f"{label} must be object")
    for key, value in expected.items():
        if mapping.get(key) != value:
            fail(f"{label} drift: {key}")


def main() -> None:
    current_ledger = load(LEDGER)
    try:
        current_frontier = frontier_state(current_ledger)
        ledger = to_reconciled(current_ledger)
    except ValueError as exc:
        fail(f"Stage35 frontier projection failed: {exc}")
    authority = load(AUTHORITY)

    require(ledger, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "baseline_main_sha": BASELINE,
        "observed_at_utc": OBSERVED,
        "source": "Supabase.list_migrations+Supabase.execute_sql+Supabase.list_edge_functions",
    }, "historical reconciled ledger")

    divergences = [row for row in ledger.get("declared_divergences", []) if isinstance(row, dict)]
    remote_only = [row for row in divergences if row.get("direction") == "remote_only"]
    repo_only = [row for row in divergences if row.get("direction") == "repo_only"]
    if len(remote_only) != 3 or repo_only:
        fail("historical reconciliation divergence projection drifted")

    remote = {
        row.get("name"): row.get("version")
        for row in ledger.get("remote_migrations", [])
        if isinstance(row, dict)
    }
    if remote.get(RECEIPT_NAME) != RECEIPT_VERSION:
        fail("receipt-store remote version missing or drifted")
    if remote.get(FIXTURE_NAME) != FIXTURE_VERSION:
        fail("controlled-fixture remote version missing or drifted")
    if remote.get("stage33_direct_rpc_revocation_and_post_revocation_fixture") != "20260822032456":
        fail("Stage33 revocation history drifted")
    if remote.get("stage33_post_revocation_proof_cleanup") != "20260822061133":
        fail("Stage33 cleanup history drifted")

    if git_blob(RECEIPT_MIGRATION) != RECEIPT_BLOB:
        fail("receipt-store migration blob drifted")
    if git_blob(FIXTURE_MIGRATION) != FIXTURE_BLOB:
        fail("controlled-fixture migration blob drifted")
    if git_blob(DISPATCHER) != DISPATCHER_BLOB:
        fail("dispatcher source blob drifted")

    require(authority, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE35_ALERT_REMOTE_MIGRATION_RECONCILIATION",
        "baseline_main_sha": BASELINE,
        "current_state": "RECEIPT_STORE_AND_CONTROLLED_FIXTURE_REMOTE_APPLY_RECONCILED_EXTERNAL_DELIVERY_PROOF_UNCONSUMED",
    }, "historical reconciliation authority")

    receipt = authority.get("remote_migration_receipt", {})
    require(receipt, {
        "source": "Supabase.list_migrations+Supabase.execute_sql+Supabase.list_edge_functions",
        "observed_at_utc": OBSERVED,
    }, "remote migration receipt")
    require(receipt.get("receipt_store", {}), {
        "name": RECEIPT_NAME,
        "repository_git_blob_sha": RECEIPT_BLOB,
        "remote_version": RECEIPT_VERSION,
        "applied_once": True,
        "reapply_allowed": False,
    }, "receipt-store receipt")
    require(receipt.get("controlled_fixture", {}), {
        "name": FIXTURE_NAME,
        "repository_git_blob_sha": FIXTURE_BLOB,
        "candidate_executable_body_git_blob_sha": "745fd77814fa40909069e00de6b41c7292e8df7b",
        "remote_version": FIXTURE_VERSION,
        "applied_once": True,
        "reapply_allowed": False,
    }, "controlled-fixture receipt")

    require(authority.get("fresh_remote_receipt", {}), {
        "auth_users": 0,
        "organizations": 0,
        "students": 0,
        "security_events": 0,
        "security_signals": 1,
        "alert_delivery_receipts": 0,
        "network_buckets": 13,
        "growth_events": 6,
        "exact_controlled_proof_signals": 1,
        "controlled_proof_receipts": 0,
        "direct_target_rpc_anon_execute_count": 0,
        "direct_target_rpc_authenticated_execute_count": 0,
        "direct_target_rpc_service_role_execute_count": 5,
        "issue_student_access_token_v2_authenticated_execute": True,
    }, "historical fresh remote receipt")

    require(authority.get("repository_reconciliation", {}), {
        "receipt_store_moved_from_repo_only_to_remote_migrations": True,
        "controlled_fixture_moved_from_repo_only_to_remote_migrations": True,
        "historical_stage17_remote_only_count_preserved": 3,
        "historical_stage33_remote_versions_preserved": True,
        "remote_mutation_performed_by_this_repository_reconciliation": False,
        "execute_sql_used_for_dml_or_ddl": False,
        "proof_reexecution_performed": False,
        "provider_called_by_this_reconciliation": False,
    }, "repository reconciliation")

    history = authority.get("immutable_external_proof_history", {})
    require(history, {
        "failed_trigger_pr": 112,
        "failed_workflow_run_id": 32647288419,
        "failed_workflow_job_id": 97213360238,
        "failed_pr_closed_unmerged": True,
        "failed_head_may_reexecute": False,
        "provider_free_parity_pr": 114,
        "provider_free_parity_workflow_run_id": 32648015715,
        "provider_free_parity_workflow_job_id": 97215180531,
        "provider_free_pr_closed_unmerged": True,
        "telegram_provider_delivery_consumed": False,
        "durable_provider_receipt_exists": False,
        "controlled_signal_still_unclaimed": True,
    }, "historical proof boundary")

    require(authority.get("gates", {}), {
        "incident_response": "DENIED",
        "production_deployment": "DENIED",
        "paid_media": "DENIED",
        "launch": "DENIED",
        "external_delivery_proof": "NOT_YET_CONSUMED",
    }, "historical gates")

    serialized = json.dumps(authority, sort_keys=True).lower()
    for forbidden in ("sbp_", "telegram_bot_token\": \"", "telegram_chat_id\": \"", "x-fitnexus-alert-dispatch-token\": \""):
        if forbidden in serialized:
            fail("authority appears to contain a secret value")

    print("STAGE35_REMOTE_MIGRATION_RECONCILIATION_GUARD=PASS")
    print(f"HISTORICAL_BASELINE_MAIN_SHA={BASELINE}")
    print(f"HISTORICAL_OBSERVED_AT_UTC={OBSERVED}")
    print(f"CURRENT_STAGE35_FRONTIER={current_frontier}")
    print(f"RECEIPT_STORE_REMOTE_VERSION={RECEIPT_VERSION}")
    print(f"CONTROLLED_FIXTURE_REMOTE_VERSION={FIXTURE_VERSION}")
    print("HISTORICAL_REPO_ONLY_STAGE35_COUNT=0")
    print("PROOF_REEXECUTION_ALLOWED=false")
    print("REMOTE_MUTATION_BY_THIS_GUARD=false")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
