from __future__ import annotations

import hashlib
import json
from pathlib import Path

from stage35_migration_frontier import (
    CLEANUP_NAME,
    CLEANUP_VERSION,
    FINAL_BASELINE,
    FINAL_OBSERVED,
    FIXTURE_NAME,
    FIXTURE_VERSION,
    RECEIPT_NAME,
    RECEIPT_VERSION,
    divergences,
    remote_map,
    state as frontier_state,
    to_cleanup_promotion,
    to_fixture,
    to_receipt,
    to_reconciled,
)

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
LEDGER = BACKEND / "migration_ledger_authority.json"
AUTHORITY = BACKEND / "stage35_alert_external_delivery_cleanup_final_reconciliation_authority.json"
CLEANUP_MIGRATION = BACKEND / "migrations" / "20260823161000_stage35_alert_delivery_controlled_proof_cleanup.sql"
CLEANUP_CANDIDATE = BACKEND / "operations" / "stage35_alert_delivery_controlled_proof_cleanup_candidate.sql"
RECEIPT_MIGRATION = BACKEND / "migrations" / "20260822075500_stage35_alert_delivery_receipt_store.sql"
FIXTURE_MIGRATION = BACKEND / "migrations" / "20260823091500_stage35_alert_delivery_controlled_proof_fixture.sql"
DISPATCHER = BACKEND / "functions" / "student-access-alert-dispatcher" / "index.ts"
PROOF_WORKFLOW = ROOT / ".github" / "workflows" / "stage35_alert_external_delivery_one_shot_proof.yml"
TRIGGER_FILE = BACKEND / "stage35_alert_external_delivery_proof_trigger.json"

RECEIPT_BLOB = "9f1a625cd316362874aefcfd9e33d64f9ecd173d"
FIXTURE_BLOB = "7d3631fc425903b013606b4a7731eaa273867a9b"
CLEANUP_CANDIDATE_BLOB = "ca8a824131120d912d0fe98687820c2b320e33f5"
CLEANUP_MIGRATION_BLOB = "a53354ed3a4983ebfe1017d4df622ed5dc6a97d0"
DISPATCHER_BLOB = "0aece761d707d8befb64a0fb89ce495fc50255a0"
PROOF_WORKFLOW_BLOB = "079a140e36a851eb0f787397929ffbe3351aba48"
BODY_MARKER = b"do $$"
FAILURE_CLASS = "BGF-STAGE35-ALERT-CLEANUP-REMOTE-RECONCILIATION-314"


def fail(message: str) -> None:
    raise SystemExit(
        "STAGE35_ALERT_EXTERNAL_DELIVERY_CLEANUP_FINAL_RECONCILIATION=FAIL\n"
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


def blob(path: Path) -> str:
    try:
        data = path.read_bytes()
    except OSError as exc:
        fail(f"unable to read {path.relative_to(ROOT)}: {type(exc).__name__}")
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def require(mapping: dict, expected: dict, label: str) -> None:
    if not isinstance(mapping, dict):
        fail(f"{label} must be object")
    for key, expected_value in expected.items():
        if mapping.get(key) != expected_value:
            fail(f"{label} drift: {key}")


def executable_body(path: Path) -> bytes:
    data = path.read_bytes()
    index = data.find(BODY_MARKER)
    if index < 0:
        fail(f"executable body marker missing: {path.relative_to(ROOT)}")
    return data[index:]


def main() -> None:
    ledger = load(LEDGER)
    authority = load(AUTHORITY)

    try:
        if frontier_state(ledger) != "final":
            fail("migration ledger is not final Stage35 frontier")
        cleanup_projection = to_cleanup_promotion(ledger)
        reconciled_projection = to_reconciled(ledger)
        fixture_projection = to_fixture(ledger)
        receipt_projection = to_receipt(ledger)
    except ValueError as exc:
        fail(f"frontier projection failed: {exc}")

    require(ledger, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "baseline_main_sha": FINAL_BASELINE,
        "observed_at_utc": FINAL_OBSERVED,
        "source": "Supabase.list_migrations+Supabase.execute_sql+Supabase.list_edge_functions",
    }, "final ledger")

    remote_only, repo_only = divergences(ledger)
    if len(remote_only) != 3:
        fail("historical Stage17 remote-only count drifted")
    if repo_only:
        fail("final Stage35 ledger must not contain repo-only divergence")
    remote = remote_map(ledger)
    if remote.get(RECEIPT_NAME) != RECEIPT_VERSION:
        fail("receipt-store remote version drifted")
    if remote.get(FIXTURE_NAME) != FIXTURE_VERSION:
        fail("controlled-fixture remote version drifted")
    if remote.get(CLEANUP_NAME) != CLEANUP_VERSION:
        fail("controlled-cleanup remote version drifted")
    if remote.get("stage33_direct_rpc_revocation_and_post_revocation_fixture") != "20260822032456":
        fail("Stage33 revocation history drifted")
    if remote.get("stage33_post_revocation_proof_cleanup") != "20260822061133":
        fail("Stage33 cleanup history drifted")

    if blob(RECEIPT_MIGRATION) != RECEIPT_BLOB:
        fail("receipt-store migration blob drifted")
    if blob(FIXTURE_MIGRATION) != FIXTURE_BLOB:
        fail("controlled-fixture migration blob drifted")
    if blob(CLEANUP_CANDIDATE) != CLEANUP_CANDIDATE_BLOB:
        fail("cleanup candidate blob drifted")
    if blob(CLEANUP_MIGRATION) != CLEANUP_MIGRATION_BLOB:
        fail("cleanup migration blob drifted")
    if executable_body(CLEANUP_CANDIDATE) != executable_body(CLEANUP_MIGRATION):
        fail("cleanup migration executable body is not byte-identical to reviewed candidate")
    if blob(DISPATCHER) != DISPATCHER_BLOB:
        fail("dispatcher source blob drifted")
    if blob(PROOF_WORKFLOW) != PROOF_WORKFLOW_BLOB:
        fail("sealed external proof workflow blob drifted")
    if TRIGGER_FILE.exists():
        fail("one-shot trigger must not exist in mergeable repository history")

    stage35_migrations = sorted(path.name for path in (BACKEND / "migrations").glob("*stage35*.sql"))
    if stage35_migrations != [
        "20260822075500_stage35_alert_delivery_receipt_store.sql",
        "20260823091500_stage35_alert_delivery_controlled_proof_fixture.sql",
        "20260823161000_stage35_alert_delivery_controlled_proof_cleanup.sql",
    ]:
        fail(f"unexpected Stage35 migration inventory: {stage35_migrations}")

    require(authority, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE35_ALERT_EXTERNAL_DELIVERY_CLEANUP_FINAL_RECONCILIATION",
        "baseline_main_sha": FINAL_BASELINE,
        "current_state": "EXTERNAL_DELIVERY_PROOF_SEALED_CLEANUP_REMOTE_APPLIED_ZERO_SYNTHETIC_RESIDUE_FINAL_RECONCILIATION",
    }, "final reconciliation authority")

    required_failure_classes = {
        "BGF-STAGE35-ALERT-PROOF-CLEANUP-286",
        "BGF-STAGE35-ALERT-PROOF-RECEIPT-AMBIGUITY-287",
        "BGF-STAGE35-ALERT-PROOF-CLEANUP-CROSSOVER-288",
        "BGF-STAGE35-ALERT-PROOF-WORKFLOW-REPLAY-290",
        "BGF-STAGE35-ALERT-EXTERNAL-PROOF-IMMUTABLE-312",
        "BGF-STAGE35-ALERT-CLEANUP-PROMOTION-313",
        FAILURE_CLASS,
    }
    if set(authority.get("failure_classes", [])) != required_failure_classes:
        fail("final failure-class set drifted")

    require(authority.get("immutable_external_delivery_proof", {}), {
        "pull_request": 117,
        "pull_request_closed_unmerged": True,
        "pull_request_reopen_allowed": False,
        "base_seal_main_sha": "db522140cc2b21840b5b48727cb15a82ca22f975",
        "head_sha": "731b0626a5b87d03fc598d5632e60df73b2a22c7",
        "workflow_run_id": 32650555123,
        "workflow_job_id": 97221340290,
        "workflow_run_attempt": 1,
        "workflow_result": "SUCCESS",
        "provider": "telegram_bot_api",
        "provider_http_200_and_ok_true": True,
        "provider_message_id_positive": True,
        "provider_message_id_value_recorded_in_repo": False,
        "provider_destination_match": True,
        "durable_receipt_recorded_before_success": True,
        "second_dispatch_result": "NO_ELIGIBLE_SIGNAL",
        "second_dispatch_provider_replay": False,
        "real_customer_data_used": False,
        "raw_provider_or_runtime_secrets_printed": False,
        "proof_reexecution_allowed": False,
    }, "immutable external proof")

    require(authority.get("cleanup_promotion_receipt", {}), {
        "pull_request": 118,
        "base_sha": "db522140cc2b21840b5b48727cb15a82ca22f975",
        "head_sha": "21d14c2c173b87abba946a9c5fdad38f55cb46d0",
        "merge_main_sha": FINAL_BASELINE,
        "quality_gate_run": 32650979151,
        "quality_gate_result": "SUCCESS",
        "cleanup_promotion_run": 32650979147,
        "cleanup_promotion_result": "SUCCESS",
        "immutable_stage31_32_33_proofs_reexecuted": False,
        "migration_git_blob_sha": CLEANUP_MIGRATION_BLOB,
        "source_candidate_git_blob_sha": CLEANUP_CANDIDATE_BLOB,
        "executable_body_byte_identical": True,
    }, "cleanup promotion receipt")

    require(authority.get("cleanup_remote_apply", {}), {
        "name": CLEANUP_NAME,
        "remote_version": CLEANUP_VERSION,
        "applied_via": "Supabase.apply_migration",
        "apply_count": 1,
        "reapply_allowed": False,
        "execute_sql_used_for_dml_or_ddl": False,
    }, "cleanup remote apply")

    require(authority.get("fresh_post_cleanup_remote_receipt", {}), {
        "source": "Supabase.list_migrations+Supabase.execute_sql+Supabase.list_edge_functions",
        "observed_at_utc": FINAL_OBSERVED,
        "auth_users": 0,
        "organizations": 0,
        "students": 0,
        "security_events": 0,
        "security_signals": 0,
        "alert_delivery_receipts": 0,
        "network_buckets": 13,
        "growth_events": 6,
        "exact_controlled_proof_signals": 0,
        "controlled_proof_receipts": 0,
        "direct_target_rpc_anon_execute_count": 0,
        "direct_target_rpc_authenticated_execute_count": 0,
        "direct_target_rpc_service_role_execute_count": 5,
        "issue_student_access_token_v2_authenticated_execute": True,
    }, "fresh post-cleanup receipt")

    require(authority.get("migration_reconciliation", {}), {
        "receipt_store_remote_version": RECEIPT_VERSION,
        "controlled_fixture_remote_version": FIXTURE_VERSION,
        "controlled_cleanup_remote_version": CLEANUP_VERSION,
        "stage35_repo_only_count": 0,
        "historical_stage17_remote_only_count": 3,
        "stage33_history_preserved": True,
        "remote_mutation_performed_by_this_repository_reconciliation": False,
    }, "migration reconciliation")

    require(authority.get("sequence_boundary", {}), {
        "may_rerun_successful_external_proof": False,
        "may_reopen_pr117": False,
        "may_merge_pr117_trigger": False,
        "may_reapply_receipt_store": False,
        "may_reapply_controlled_fixture": False,
        "may_reapply_cleanup": False,
        "may_execute_operations_sql_directly": False,
        "may_use_execute_sql_for_dml_or_ddl": False,
        "synthetic_cleanup_complete": True,
        "final_stage35_remote_migration_reconciliation_complete_after_green_merge": True,
    }, "sequence boundary")

    require(authority.get("gates", {}), {
        "external_delivery_proof": "PASS_IMMUTABLE",
        "synthetic_cleanup": "PASS_ZERO_RESIDUE",
        "incident_response": "DENIED",
        "production_deployment": "DENIED",
        "paid_media": "DENIED",
        "launch": "DENIED",
    }, "gates")

    if frontier_state(cleanup_projection) != "cleanup_promotion":
        fail("cleanup-promotion projection invalid")
    if frontier_state(reconciled_projection) != "reconciled":
        fail("reconciled projection invalid")
    if frontier_state(fixture_projection) != "fixture":
        fail("fixture projection invalid")
    if frontier_state(receipt_projection) != "receipt":
        fail("receipt projection invalid")

    serialized = json.dumps(authority, sort_keys=True).lower()
    for forbidden in ("sbp_", "telegram_bot_token\": \"", "telegram_chat_id\": \"", "x-fitnexus-alert-dispatch-token\": \""):
        if forbidden in serialized:
            fail("final authority appears to contain a secret value")

    print("STAGE35_ALERT_EXTERNAL_DELIVERY_CLEANUP_FINAL_RECONCILIATION=PASS")
    print(f"FINAL_BASELINE_MAIN_SHA={FINAL_BASELINE}")
    print(f"FINAL_OBSERVED_AT_UTC={FINAL_OBSERVED}")
    print(f"RECEIPT_STORE_REMOTE_VERSION={RECEIPT_VERSION}")
    print(f"CONTROLLED_FIXTURE_REMOTE_VERSION={FIXTURE_VERSION}")
    print(f"CONTROLLED_CLEANUP_REMOTE_VERSION={CLEANUP_VERSION}")
    print("STAGE35_REPO_ONLY_COUNT=0")
    print("SYNTHETIC_SECURITY_SIGNALS=0")
    print("SYNTHETIC_DELIVERY_RECEIPTS=0")
    print("HISTORICAL_FRONTIER_PROJECTIONS=PASS")
    print("PROOF_REEXECUTION_ALLOWED=false")
    print("REMOTE_MUTATION_BY_THIS_RECONCILIATION=false")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
