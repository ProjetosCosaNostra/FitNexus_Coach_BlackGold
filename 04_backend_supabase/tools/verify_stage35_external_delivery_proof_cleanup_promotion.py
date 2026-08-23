from __future__ import annotations

import hashlib
import json
from pathlib import Path

from stage35_migration_frontier import state as frontier_state, to_cleanup_promotion

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage35_alert_external_delivery_proof_receipt_cleanup_promotion_authority.json"
LEDGER = BACKEND / "migration_ledger_authority.json"
CLEANUP_MIGRATION = BACKEND / "migrations" / "20260823161000_stage35_alert_delivery_controlled_proof_cleanup.sql"
CLEANUP_CANDIDATE = BACKEND / "operations" / "stage35_alert_delivery_controlled_proof_cleanup_candidate.sql"
RECEIPT_MIGRATION = BACKEND / "migrations" / "20260822075500_stage35_alert_delivery_receipt_store.sql"
FIXTURE_MIGRATION = BACKEND / "migrations" / "20260823091500_stage35_alert_delivery_controlled_proof_fixture.sql"
DISPATCHER = BACKEND / "functions" / "student-access-alert-dispatcher" / "index.ts"
PROOF_WORKFLOW = ROOT / ".github" / "workflows" / "stage35_alert_external_delivery_one_shot_proof.yml"
TRIGGER_FILE = BACKEND / "stage35_alert_external_delivery_proof_trigger.json"

BASELINE = "db522140cc2b21840b5b48727cb15a82ca22f975"
OBSERVED = "2026-08-23T16:06:48.978350Z"
CLEANUP_NAME = "stage35_alert_delivery_controlled_proof_cleanup"
CLEANUP_MIGRATION_BLOB = "a53354ed3a4983ebfe1017d4df622ed5dc6a97d0"
CLEANUP_CANDIDATE_BLOB = "ca8a824131120d912d0fe98687820c2b320e33f5"
RECEIPT_BLOB = "9f1a625cd316362874aefcfd9e33d64f9ecd173d"
FIXTURE_BLOB = "7d3631fc425903b013606b4a7731eaa273867a9b"
DISPATCHER_BLOB = "0aece761d707d8befb64a0fb89ce495fc50255a0"
PROOF_WORKFLOW_BLOB = "079a140e36a851eb0f787397929ffbe3351aba48"
FAILURE_CLASS = "BGF-STAGE35-ALERT-CLEANUP-PROMOTION-313"
BODY_MARKER = b"do $$"


def fail(message: str) -> None:
    raise SystemExit(
        "STAGE35_EXTERNAL_DELIVERY_PROOF_CLEANUP_PROMOTION_GUARD=FAIL\n"
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


def raw(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        fail(f"unable to read {path.relative_to(ROOT)}: {type(exc).__name__}")


def blob(path: Path) -> str:
    data = raw(path)
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def body(data: bytes, label: str) -> bytes:
    index = data.find(BODY_MARKER)
    if index < 0:
        fail(f"{label} executable body missing")
    return data[index:]


def require(mapping: dict, expected: dict, label: str) -> None:
    if not isinstance(mapping, dict):
        fail(f"{label} must be object")
    for key, value in expected.items():
        if mapping.get(key) != value:
            fail(f"{label} drift: {key}")


def main() -> None:
    authority = load(AUTHORITY)
    current_ledger = load(LEDGER)
    try:
        current_frontier = frontier_state(current_ledger)
        ledger = to_cleanup_promotion(current_ledger)
    except ValueError as exc:
        fail(f"Stage35 cleanup-promotion projection failed: {exc}")

    require(authority, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE35_ALERT_EXTERNAL_DELIVERY_PROOF_RECEIPT_AND_CLEANUP_PROMOTION",
        "baseline_main_sha": BASELINE,
        "current_state": "EXTERNAL_DELIVERY_PROOF_IMMUTABLE_PASS_CLEANUP_MIGRATION_REPO_ONLY_REMOTE_APPLY_PENDING",
    }, "authority")

    if set(authority.get("failure_classes", [])) != {
        "BGF-STAGE35-ALERT-PROOF-CLEANUP-286",
        "BGF-STAGE35-ALERT-PROOF-RECEIPT-AMBIGUITY-287",
        "BGF-STAGE35-ALERT-PROOF-CLEANUP-CROSSOVER-288",
        "BGF-STAGE35-ALERT-PROOF-WORKFLOW-REPLAY-290",
        "BGF-STAGE35-ALERT-EXTERNAL-PROOF-IMMUTABLE-312",
        FAILURE_CLASS,
    }:
        fail("failure-class set drifted")

    require(authority.get("immutable_external_delivery_proof", {}), {
        "pull_request": 117,
        "pull_request_closed_unmerged": True,
        "pull_request_reopen_allowed": False,
        "base_seal_main_sha": BASELINE,
        "head_sha": "731b0626a5b87d03fc598d5632e60df73b2a22c7",
        "workflow_run_id": 32650555123,
        "workflow_job_id": 97221340290,
        "workflow_run_attempt": 1,
        "workflow_result": "SUCCESS",
        "trigger_diff_exact_one_file": True,
        "proof_marker": "fitnexus-stage34-alert-delivery-proof-v1",
        "provider": "telegram_bot_api",
        "provider_http_200_and_ok_true": True,
        "provider_message_id_positive": True,
        "provider_message_id_value_recorded_in_repo": False,
        "provider_destination_match_verified_by_deployed_source": True,
        "durable_receipt_recorded_before_success": True,
        "second_dispatch_result": "NO_ELIGIBLE_SIGNAL",
        "second_dispatch_provider_replay": False,
        "real_customer_data_used": False,
        "raw_provider_or_runtime_secrets_printed": False,
        "proof_reexecution_allowed": False,
    }, "immutable external proof")

    post = authority.get("fresh_post_proof_remote_receipt", {})
    require(post, {
        "source": "Supabase.execute_sql",
        "observed_at_utc": OBSERVED,
        "auth_users": 0,
        "organizations": 0,
        "students": 0,
        "security_events": 0,
        "security_signals": 1,
        "alert_delivery_receipts": 1,
        "network_buckets": 13,
        "growth_events": 6,
        "exact_controlled_proof_signals": 1,
        "exact_controlled_proof_receipts": 1,
        "direct_target_rpc_anon_execute_count": 0,
        "direct_target_rpc_authenticated_execute_count": 0,
        "direct_target_rpc_service_role_execute_count": 5,
        "issue_student_access_token_v2_authenticated_execute": True,
    }, "fresh post-proof remote receipt")
    require(post.get("receipt", {}), {
        "signal_id": 4,
        "provider": "telegram_bot_api",
        "destination_fingerprint_present": True,
        "destination_fingerprint_length": 64,
        "destination_fingerprint_value_recorded_in_repo": False,
        "status": "delivered",
        "attempt_number": 1,
        "claim_token_present": True,
        "claim_token_value_recorded_in_repo": False,
        "lease_expires_at_is_null": True,
        "provider_message_id_positive": True,
        "provider_message_id_value_recorded_in_repo": False,
        "controlled_proof_marker": "fitnexus-stage34-alert-delivery-proof-v1",
        "last_error_code_is_null": True,
        "delivered_at": "2026-08-23T16:04:59.845212Z",
    }, "durable receipt")

    require(ledger, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "baseline_main_sha": BASELINE,
        "observed_at_utc": OBSERVED,
        "source": "Supabase.list_migrations+Supabase.execute_sql+Supabase.list_edge_functions",
    }, "migration ledger")
    divergences = [row for row in ledger.get("declared_divergences", []) if isinstance(row, dict)]
    remote_only = [row for row in divergences if row.get("direction") == "remote_only"]
    repo_only = [row for row in divergences if row.get("direction") == "repo_only"]
    if len(remote_only) != 3:
        fail("historical Stage17 remote-only divergence count drifted")
    if len(repo_only) != 1 or repo_only[0].get("name") != CLEANUP_NAME:
        fail("cleanup migration must be the unique repo-only divergence")
    if repo_only[0].get("related_failure_class") != "BGF-STAGE35-ALERT-PROOF-CLEANUP-286":
        fail("cleanup repo-only failure-class binding drifted")

    remote = {
        row.get("name"): row.get("version")
        for row in ledger.get("remote_migrations", []) if isinstance(row, dict)
    }
    if remote.get("stage35_alert_delivery_receipt_store") != "20260823092354":
        fail("receipt-store remote version drifted")
    if remote.get("stage35_alert_delivery_controlled_proof_fixture") != "20260823145908":
        fail("controlled-fixture remote version drifted")
    if CLEANUP_NAME in remote:
        fail("cleanup migration unexpectedly remote in projected promotion frontier")

    if blob(CLEANUP_MIGRATION) != CLEANUP_MIGRATION_BLOB:
        fail("cleanup migration blob drifted")
    if blob(CLEANUP_CANDIDATE) != CLEANUP_CANDIDATE_BLOB:
        fail("cleanup candidate blob drifted")
    if body(raw(CLEANUP_MIGRATION), "cleanup migration") != body(raw(CLEANUP_CANDIDATE), "cleanup candidate"):
        fail("cleanup migration executable body is not byte-identical to candidate")
    cleanup_header = raw(CLEANUP_MIGRATION).split(BODY_MARKER, 1)[0].decode("utf-8", errors="replace").lower()
    for fragment in ("repository-only", "remote application is forbidden"):
        if fragment not in cleanup_header:
            fail(f"cleanup safety header missing: {fragment}")

    if blob(RECEIPT_MIGRATION) != RECEIPT_BLOB:
        fail("receipt-store migration blob drifted")
    if blob(FIXTURE_MIGRATION) != FIXTURE_BLOB:
        fail("controlled-fixture migration blob drifted")
    if blob(DISPATCHER) != DISPATCHER_BLOB:
        fail("dispatcher source blob drifted")
    if blob(PROOF_WORKFLOW) != PROOF_WORKFLOW_BLOB:
        fail("one-shot proof workflow blob drifted")
    if TRIGGER_FILE.exists():
        fail("one-shot trigger must not be mergeable into main")

    stage35_migrations = sorted(path.name for path in (BACKEND / "migrations").glob("*stage35*.sql"))
    if stage35_migrations != [
        "20260822075500_stage35_alert_delivery_receipt_store.sql",
        "20260823091500_stage35_alert_delivery_controlled_proof_fixture.sql",
        "20260823161000_stage35_alert_delivery_controlled_proof_cleanup.sql",
    ]:
        fail(f"unexpected Stage35 migration inventory: {stage35_migrations}")

    require(authority.get("cleanup_promotion", {}), {
        "migration_name": CLEANUP_NAME,
        "migration_file": "04_backend_supabase/migrations/20260823161000_stage35_alert_delivery_controlled_proof_cleanup.sql",
        "migration_git_blob_sha": CLEANUP_MIGRATION_BLOB,
        "source_candidate_file": "04_backend_supabase/operations/stage35_alert_delivery_controlled_proof_cleanup_candidate.sql",
        "source_candidate_git_blob_sha": CLEANUP_CANDIDATE_BLOB,
        "executable_body_byte_identical": True,
        "migration_ledger_state": "repo_only",
        "remote_applied": False,
        "remote_version": None,
        "apply_count": 0,
        "remote_apply_allowed_after_this_pr_alone": False,
        "operations_candidate_direct_execution_allowed": False,
        "execute_sql_dml_or_ddl_allowed": False,
    }, "cleanup promotion")
    require(authority.get("cleanup_contract", {}), {
        "requires_exact_one_synthetic_signal": True,
        "requires_exact_one_delivered_telegram_receipt": True,
        "requires_customer_domain_empty": True,
        "requires_security_events_zero": True,
        "requires_network_baseline": 13,
        "requires_growth_baseline": 6,
        "requires_direct_rpc_grants": "0/0/5",
        "requires_issue_token_authenticated_execute": True,
        "deletes_only_exact_synthetic_signal": True,
        "receipt_removed_by_foreign_key_cascade": True,
        "postcondition_security_signals": 0,
        "postcondition_alert_delivery_receipts": 0,
        "postcondition_network_baseline": 13,
        "postcondition_growth_baseline": 6,
    }, "cleanup contract")
    require(authority.get("sequence_boundary", {}), {
        "may_rerun_successful_external_proof": False,
        "may_reopen_pr117": False,
        "may_merge_trigger_pr117": False,
        "may_apply_cleanup_before_green_merge": False,
        "may_execute_operations_sql_directly": False,
        "may_use_execute_sql_for_dml_or_ddl": False,
    }, "sequence boundary")
    require(authority.get("gates", {}), {
        "incident_response": "DENIED",
        "production_deployment": "DENIED",
        "paid_media": "DENIED",
        "launch": "DENIED",
        "external_delivery_proof": "PASS_IMMUTABLE",
        "cleanup_remote_apply": "PENDING_GREEN_MERGE",
    }, "historical gates")

    serialized = json.dumps(authority, sort_keys=True).lower()
    for forbidden in (
        "sbp_",
        "telegram_bot_token\": \"",
        "telegram_chat_id\": \"",
        "x-fitnexus-alert-dispatch-token\": \"",
        "destination_fingerprint\": \"",
        "provider_message_id\": ",
        "claim_token\": \"",
    ):
        if forbidden in serialized:
            fail("authority appears to contain forbidden secret/provider identifier material")

    print("STAGE35_EXTERNAL_DELIVERY_PROOF_CLEANUP_PROMOTION_GUARD=PASS")
    print(f"HISTORICAL_BASELINE_MAIN_SHA={BASELINE}")
    print(f"CURRENT_STAGE35_FRONTIER={current_frontier}")
    print("EXTERNAL_DELIVERY_PROOF=PASS_IMMUTABLE")
    print("PROOF_RUN=32650555123")
    print("PROOF_JOB=97221340290")
    print("PROOF_HEAD=731b0626a5b87d03fc598d5632e60df73b2a22c7")
    print("DURABLE_DELIVERED_RECEIPT=VERIFIED")
    print("SECOND_DISPATCH_PROVIDER_REPLAY=false")
    print(f"CLEANUP_MIGRATION_BLOB={CLEANUP_MIGRATION_BLOB}")
    print(f"CLEANUP_CANDIDATE_BLOB={CLEANUP_CANDIDATE_BLOB}")
    print("CLEANUP_EXECUTABLE_BODY_BYTE_IDENTICAL=true")
    print("HISTORICAL_CLEANUP_LEDGER_STATE=repo_only")
    print("PROOF_REEXECUTION_ALLOWED=false")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
