from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
APP = ROOT / "03_app_flutter" / "fitnexus_app"
AUTHORITY = BACKEND / "stage35_alert_dispatcher_deployment_proof_seal_authority.json"
PROMOTION_AUTHORITY = BACKEND / "stage35_alert_delivery_receipt_store_migration_promotion_authority.json"
LEDGER = BACKEND / "migration_ledger_authority.json"
MIGRATION = BACKEND / "migrations" / "20260822075500_stage35_alert_delivery_receipt_store.sql"
DISPATCHER = BACKEND / "functions" / "student-access-alert-dispatcher" / "index.ts"
FIXTURE = BACKEND / "operations" / "stage35_alert_delivery_controlled_proof_fixture_candidate.sql"
CLEANUP = BACKEND / "operations" / "stage35_alert_delivery_controlled_proof_cleanup_candidate.sql"
PROOF_WORKFLOW = ROOT / ".github" / "workflows" / "stage35_alert_external_delivery_live_proof.yml"
TRANSPORT = APP / "lib" / "features" / "student" / "student_access_transport_contract.dart"

BASELINE = "af2d0ce99ccb91db857c595f2f6d05de4894a59f"
MIGRATION_BLOB = "9f1a625cd316362874aefcfd9e33d64f9ecd173d"
DISPATCHER_BLOB = "0aece761d707d8befb64a0fb89ce495fc50255a0"
FIXTURE_BLOB = "745fd77814fa40909069e00de6b41c7292e8df7b"
CLEANUP_BLOB = "ca8a824131120d912d0fe98687820c2b320e33f5"
PROOF_WORKFLOW_BLOB = "079a140e36a851eb0f787397929ffbe3351aba48"
MIGRATION_NAME = "stage35_alert_delivery_receipt_store"
PROOF_MARKER = "fitnexus-stage34-alert-delivery-proof-v1"
FAILURE_CLASS = "BGF-STAGE35-ALERT-DISPATCHER-PREMATURE-DEPLOYMENT-283"


def fail(message: str) -> None:
    raise SystemExit(
        "STAGE35_ALERT_DISPATCHER_DEPLOYMENT_PROOF_SEAL_GUARD=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\nDETAIL={message}"
    )


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to read {path.relative_to(ROOT)}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"expected JSON object: {path.relative_to(ROOT)}")
    return value


def raw(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        fail(f"unable to read {path.relative_to(ROOT)}: {type(exc).__name__}")
    raise AssertionError("unreachable")


def text(path: Path) -> str:
    return raw(path).decode("utf-8")


def git_blob_sha(path: Path) -> str:
    data = raw(path)
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def require(mapping: dict, expected: dict, label: str) -> None:
    if not isinstance(mapping, dict):
        fail(f"{label} must be an object")
    for key, expected_value in expected.items():
        if mapping.get(key) != expected_value:
            fail(f"{label} drift: {key}")


def prove_historical_promotion_frontier() -> None:
    """Run the immutable Stage35 promotion guard with the later proof workflow hidden.

    The promotion guard intentionally rejected a proof workflow before a deployment seal.
    Once this seal exists, that absence is a historical filesystem fact. We project only
    the workflow path while leaving the actual migration/ledger/dispatcher authority intact.
    """
    module = importlib.import_module("verify_stage35_alert_receipt_store_migration_promotion")
    original = module.PROOF_WORKFLOW
    hidden = ROOT / ".stage35_historical_absent_external_delivery_workflow"
    if hidden.exists():
        fail("historical projection sentinel unexpectedly exists")
    try:
        module.PROOF_WORKFLOW = hidden
        module.main()
    finally:
        module.PROOF_WORKFLOW = original


def main() -> None:
    prove_historical_promotion_frontier()

    authority = load(AUTHORITY)
    promotion = load(PROMOTION_AUTHORITY)
    ledger = load(LEDGER)
    fixture = text(FIXTURE)
    cleanup = text(CLEANUP)
    workflow = text(PROOF_WORKFLOW)
    dispatcher = text(DISPATCHER)
    transport = text(TRANSPORT)

    require(authority, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE35_ALERT_DISPATCHER_DEPLOYMENT_AND_EXTERNAL_DELIVERY_PROOF_SEAL",
        "baseline_main_sha": BASELINE,
        "current_state": "DEPLOYMENT_AND_EXTERNAL_DELIVERY_PROOF_SEAL_STAGED_NO_REMOTE_MUTATION",
    }, "seal authority")

    if set(authority.get("failure_classes", [])) != {
        "BGF-STAGE35-ALERT-CLAIM-DUPLICATE-275",
        "BGF-STAGE35-ALERT-UNKNOWN-DELIVERY-RETRY-276",
        "BGF-STAGE35-ALERT-RECEIPT-SCOPE-277",
        "BGF-STAGE35-ALERT-PROOF-CUSTOMER-CROSSOVER-278",
        "BGF-STAGE35-ALERT-DISPATCH-AUTH-BYPASS-279",
        "BGF-STAGE35-ALERT-PROVIDER-RECEIPT-SELF-ATTESTATION-280",
        "BGF-STAGE35-ALERT-CANDIDATE-REMOTE-MUTATION-281",
        "BGF-STAGE35-ALERT-RECEIPT-MIGRATION-PROMOTION-282",
        FAILURE_CLASS,
        "BGF-STAGE35-ALERT-CONTROLLED-FIXTURE-PREMATURE-284",
        "BGF-STAGE35-ALERT-CONTROLLED-FIXTURE-DRIFT-285",
        "BGF-STAGE35-ALERT-PROOF-CLEANUP-286",
        "BGF-STAGE35-ALERT-PROOF-RECEIPT-AMBIGUITY-287",
        "BGF-STAGE35-ALERT-PROOF-CLEANUP-CROSSOVER-288",
        "BGF-STAGE35-ALERT-RUNTIME-SECRET-ASSUMPTION-289",
        "BGF-STAGE35-ALERT-PROOF-WORKFLOW-REPLAY-290",
    }:
        fail("seal authority failure-class set drifted")

    require(authority.get("migration_promotion_receipt", {}), {
        "promotion_pr": 100,
        "promotion_head_sha": "7f89fc2d174bcc62a251978af4ce6c4305e3f8a2",
        "promotion_merge_main_sha": BASELINE,
        "quality_gate_run": 32561172722,
        "quality_gate_job": 97002809029,
        "quality_gate_result": "PASS",
        "promotion_workflow_run": 32561172710,
        "promotion_workflow_job": 97002808959,
        "promotion_workflow_result": "PASS",
        "postgres_compatibility_run": 32561172806,
        "postgres_compatibility_job": 97002809165,
        "postgres_compatibility_result": "PASS",
        "consumed_stage31_32_33_proofs_reexecuted": False,
    }, "migration promotion receipt")

    receipt = authority.get("fresh_post_promotion_remote_receipt", {})
    require(receipt, {
        "source": "Supabase.execute_sql+Supabase.list_migrations+Supabase.list_edge_functions",
        "observed_at_utc": "2026-08-22T18:13:31.319947Z",
        "auth_users": 0,
        "organizations": 0,
        "students": 0,
        "security_events": 0,
        "security_signals": 0,
        "network_buckets": 13,
        "growth_events": 6,
        "anon_execute_count": 0,
        "authenticated_execute_count": 0,
        "service_role_execute_count": 5,
        "issue_student_access_token_v2_authenticated_execute": True,
        "security_posture": "quiet",
        "alert_receipt_table_exists": False,
        "alert_claim_bridge_exists": False,
        "alert_record_bridge_exists": False,
        "remote_stage35_receipt_store_migration_present": False,
        "deployed_edge_function_count": 1,
        "student_access_alert_dispatcher_deployed": False,
    }, "fresh post-promotion remote receipt")
    if receipt.get("deployed_edge_functions") != [{
        "slug": "student-access-gateway",
        "version": 3,
        "status": "ACTIVE",
        "verify_jwt": False,
        "bundle_sha256": "b57892b3f399b76f8127c9a39d3d8c021ffe639aa7bf92c7fa9a459d35721b82",
    }]:
        fail("fresh Edge inventory drifted")

    require(promotion, {
        "current_state": "RECEIPT_STORE_MIGRATION_REPO_ONLY_DISPATCHER_DEPLOYMENT_SEAL_PENDING",
        "baseline_main_sha": "6aad66c159c82c634af8ec58f0ec742267484b70",
    }, "promotion authority historical frontier")

    expected_blobs = {
        MIGRATION: MIGRATION_BLOB,
        DISPATCHER: DISPATCHER_BLOB,
        FIXTURE: FIXTURE_BLOB,
        CLEANUP: CLEANUP_BLOB,
        PROOF_WORKFLOW: PROOF_WORKFLOW_BLOB,
    }
    for path, expected in expected_blobs.items():
        actual = git_blob_sha(path)
        if actual != expected:
            fail(f"Git blob drift: {path.relative_to(ROOT)} => {actual}")

    require(authority.get("sealed_artifacts", {}), {
        "receipt_store_migration_git_blob_sha": MIGRATION_BLOB,
        "dispatcher_git_blob_sha": DISPATCHER_BLOB,
        "controlled_fixture_candidate_git_blob_sha": FIXTURE_BLOB,
        "cleanup_candidate_git_blob_sha": CLEANUP_BLOB,
        "one_shot_proof_workflow_git_blob_sha": PROOF_WORKFLOW_BLOB,
        "proof_marker": PROOF_MARKER,
        "proof_trigger_branch": "blackgold/stage35-alert-external-delivery-proof-trigger",
        "proof_trigger_file": "04_backend_supabase/stage35_alert_external_delivery_proof_trigger.json",
    }, "sealed artifacts")

    lower_fixture = fixture.lower()
    for fragment in (
        "repository-only operations candidate",
        "to_regclass('private.student_access_alert_delivery_receipts') is null",
        "stage35_alert_proof_customer_domain_not_empty",
        "stage35_alert_proof_security_domain_not_empty",
        "student_access_network_rate_buckets) <> 13",
        "growth_events) <> 6",
        "'network_rate_limit_burst'",
        "'high'",
        "'proof:fitnexus-stage34-alert-delivery-proof-v1'",
        "'get_workout'",
        "stage35_alert_proof_signal_postcondition_failed",
        "stage35_alert_proof_receipt_prematurely_materialized",
    ):
        if fragment not in lower_fixture:
            fail(f"fixture invariant missing: {fragment}")
    for forbidden in (
        "grant execute on function",
        "revoke execute on function",
        "telegram_bot_token",
        "telegram_chat_id",
        "origin_hash",
        "p_network_origin",
    ):
        if forbidden in lower_fixture:
            fail(f"fixture forbidden material appeared: {forbidden}")
    if "insert into private.student_access_security_signals" not in lower_fixture:
        fail("fixture does not insert the bounded synthetic signal")

    lower_cleanup = cleanup.lower()
    for fragment in (
        "repository-only operations candidate",
        "status = 'delivered'",
        "attempt_number = 1",
        "provider_message_id > 0",
        "controlled_proof_marker = v_marker",
        "destination_fingerprint ~ '^[0-9a-f]{64}$'",
        "delete from private.student_access_security_signals",
        "stage35_alert_cleanup_synthetic_residue_remains",
        "student_access_network_rate_buckets) <> 13",
        "growth_events) <> 6",
    ):
        if fragment not in lower_cleanup:
            fail(f"cleanup invariant missing: {fragment}")
    if "delete from private.student_access_alert_delivery_receipts" in lower_cleanup:
        fail("cleanup must rely on exact signal FK cascade for proof receipt deletion")
    if "grant execute on function" in lower_cleanup or "revoke execute on function" in lower_cleanup:
        fail("cleanup must not change student RPC privileges")

    lower_workflow = workflow.lower()
    for fragment in (
        "types:\n      - opened",
        "blackgold/stage35-alert-external-delivery-proof-trigger",
        "github.run_attempt == 1",
        "stage35_alert_external_delivery_proof_trigger.json",
        "student_access_alert_dispatch_token",
        "fitnexus-stage34-alert-delivery-proof-v1",
        "student-access-alert-dispatcher",
        "'provider': 'telegram_bot_api'",
        "'attempt_number': 1",
        "provider_message_id",
        "no_eligible_signal",
        "proof_reexecution_allowed=false",
    ):
        if fragment not in lower_workflow:
            fail(f"proof workflow invariant missing: {fragment}")
    for forbidden in (
        "workflow_dispatch:",
        "schedule:",
        "synchronize",
        "reopened",
    ):
        if forbidden in lower_workflow:
            fail(f"proof workflow replay surface appeared: {forbidden}")
    if lower_workflow.count("status, first = call()") != 1 or lower_workflow.count("status, second = call()") != 1:
        fail("proof workflow must execute exactly first delivery + one no-replay call")

    lower_dispatcher = dispatcher.lower()
    for fragment in (
        'deno.env.get("student_access_alert_dispatch_token")',
        'deno.env.get("student_access_alert_telegram_bot_token")',
        'deno.env.get("student_access_alert_telegram_chat_id")',
        "telegram_destination_mismatch",
        "alert_provider_delivered_receipt_persistence_unconfirmed",
    ):
        if fragment not in lower_dispatcher:
            fail(f"dispatcher runtime secret/provider invariant missing: {fragment}")
    if "console.log" in lower_dispatcher or "console.error" in lower_dispatcher:
        fail("dispatcher logging appeared")

    if ledger.get("baseline_main_sha") != "6aad66c159c82c634af8ec58f0ec742267484b70":
        fail("migration ledger must remain on the merged promotion observation until remote apply")
    remote = {
        row.get("name"): row.get("version")
        for row in ledger.get("remote_migrations", []) if isinstance(row, dict)
    }
    if MIGRATION_NAME in remote:
        fail("receipt-store migration unexpectedly remote before seal merge")
    repo_only = [
        row for row in ledger.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    ]
    if len(repo_only) != 1 or repo_only[0].get("name") != MIGRATION_NAME:
        fail("seal preparation must preserve receipt-store as unique repo-only migration")

    runtime = authority.get("runtime_secret_boundary", {})
    require(runtime, {
        "required_supabase_runtime_secrets": [
            "STUDENT_ACCESS_ALERT_DISPATCH_TOKEN",
            "STUDENT_ACCESS_ALERT_TELEGRAM_BOT_TOKEN",
            "STUDENT_ACCESS_ALERT_TELEGRAM_CHAT_ID",
        ],
        "required_github_proof_secret": "STUDENT_ACCESS_ALERT_DISPATCH_TOKEN",
        "secret_values_in_repository": False,
        "secret_values_in_database": False,
        "secret_values_in_proof_logs": False,
        "runtime_secret_presence_attested_by_this_stage": False,
        "provider_destination_presence_attested_by_this_stage": False,
        "deployment_allowed_without_runtime_secret_evidence": False,
        "fixture_remote_apply_allowed_without_runtime_secret_evidence": False,
        "proof_trigger_allowed_without_runtime_secret_evidence": False,
    }, "runtime secret boundary")

    require(authority.get("remote_mutation_boundary", {}), {
        "receipt_store_remote_applied": False,
        "controlled_fixture_remote_applied": False,
        "alert_dispatcher_remote_deployed": False,
        "provider_called": False,
        "external_delivery_receipt_verified": False,
        "operations_candidates_executed": False,
        "direct_rpc_regrant_performed": False,
        "automatic_edge_to_direct_fallback": False,
        "source_transport_metadata_advanced": False,
    }, "remote mutation boundary")

    for fragment in (
        "StudentAccessTransportMode.edgeGateway;",
        "static const bool edgeGatewaySelected = true;",
        "static const bool automaticEdgeToDirectFallback = false;",
        "static const bool explicitRollbackRequested = false;",
        "static const bool explicitRollbackAuthorized = false;",
        "static const bool directRpcExecuteRevoked = false;",
    ):
        if fragment not in transport:
            fail(f"seal must not change production transport metadata: {fragment}")

    require(authority.get("seal_rules", {}), {
        "may_apply_receipt_store_before_seal_merge": False,
        "may_promote_or_apply_fixture_before_seal_merge": False,
        "may_deploy_dispatcher_before_seal_merge": False,
        "may_open_proof_trigger_pr_before_seal_merge": False,
        "may_trigger_external_provider_before_seal_merge": False,
        "may_execute_operations_sql_directly": False,
        "may_use_execute_sql_for_dml": False,
        "may_store_runtime_secrets_in_repository": False,
        "may_reexecute_consumed_stage31_32_33_proofs": False,
        "may_regrant_direct_rpc_execute": False,
        "may_enable_automatic_direct_fallback": False,
        "may_advance_source_transport_metadata": False,
        "may_promote_incident_response_gate": False,
        "may_promote_production_deployment_gate": False,
        "may_enable_paid_ads": False,
    }, "seal rules")

    print("STAGE35_ALERT_DISPATCHER_DEPLOYMENT_PROOF_SEAL_GUARD=PASS")
    print(f"BASELINE_MAIN_SHA={BASELINE}")
    print(f"RECEIPT_STORE_MIGRATION_BLOB={MIGRATION_BLOB}")
    print(f"DISPATCHER_BLOB={DISPATCHER_BLOB}")
    print(f"CONTROLLED_FIXTURE_CANDIDATE_BLOB={FIXTURE_BLOB}")
    print(f"CLEANUP_CANDIDATE_BLOB={CLEANUP_BLOB}")
    print(f"ONE_SHOT_PROOF_WORKFLOW_BLOB={PROOF_WORKFLOW_BLOB}")
    print("REMOTE_MUTATION=false")
    print("RUNTIME_SECRET_PRESENCE_ATTESTED=false")
    print("CONTROLLED_EXTERNAL_DELIVERY_PROOF=false")
    print("PROOF_REEXECUTION_ALLOWED=false")
    print("INCIDENT_RESPONSE_GATE=DENIED")
    print("PRODUCTION_DEPLOYMENT_GATE=DENIED")
    print("PAID_MEDIA_GATE=DENIED")


if __name__ == "__main__":
    main()
