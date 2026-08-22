from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
APP = ROOT / "03_app_flutter" / "fitnexus_app"
AUTHORITY = BACKEND / "stage35_alert_delivery_receipt_store_migration_promotion_authority.json"
CANDIDATE_AUTHORITY = BACKEND / "stage35_alert_dispatcher_receipt_candidate_authority.json"
CURRENT = BACKEND / "student_access_current_boundary_authority.json"
ALERT_CONTRACT = BACKEND / "student_access_alert_delivery_contract.json"
LEDGER = BACKEND / "migration_ledger_authority.json"
MIGRATION = BACKEND / "migrations" / "20260822075500_stage35_alert_delivery_receipt_store.sql"
CANDIDATE = BACKEND / "operations" / "stage35_alert_delivery_receipt_store_candidate.sql"
DISPATCHER = BACKEND / "functions" / "student-access-alert-dispatcher" / "index.ts"
TRANSPORT = APP / "lib" / "features" / "student" / "student_access_transport_contract.dart"
PROOF_WORKFLOW = ROOT / ".github" / "workflows" / "stage35_alert_external_delivery_live_proof.yml"

BASELINE = "6aad66c159c82c634af8ec58f0ec742267484b70"
OBSERVED = "2026-08-22T07:54:12.776139Z"
MIGRATION_NAME = "stage35_alert_delivery_receipt_store"
MIGRATION_BLOB = "9f1a625cd316362874aefcfd9e33d64f9ecd173d"
CANDIDATE_BLOB = "465c6a76249847673a6e8d627c8a882d2331217a"
DISPATCHER_BLOB = "0aece761d707d8befb64a0fb89ce495fc50255a0"
FAILURE_CLASS = "BGF-STAGE35-ALERT-RECEIPT-MIGRATION-PROMOTION-282"
BODY_MARKER = b"create table if not exists private.student_access_alert_delivery_receipts"


def fail(message: str) -> None:
    raise SystemExit(
        "STAGE35_ALERT_RECEIPT_STORE_MIGRATION_PROMOTION_GUARD=FAIL\n"
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


def git_blob_sha(path: Path) -> str:
    data = raw(path)
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def require(mapping: dict, expected: dict, label: str) -> None:
    if not isinstance(mapping, dict):
        fail(f"{label} must be an object")
    for key, expected_value in expected.items():
        if mapping.get(key) != expected_value:
            fail(f"{label} drift: {key}")


def executable_body(data: bytes, label: str) -> bytes:
    index = data.find(BODY_MARKER)
    if index < 0:
        fail(f"{label} executable body marker missing")
    return data[index:]


def main() -> None:
    authority = load(AUTHORITY)
    candidate_authority = load(CANDIDATE_AUTHORITY)
    current = load(CURRENT)
    alert_contract = load(ALERT_CONTRACT)
    ledger = load(LEDGER)
    migration = raw(MIGRATION)
    candidate = raw(CANDIDATE)
    dispatcher = raw(DISPATCHER)
    transport = raw(TRANSPORT).decode("utf-8")

    require(candidate_authority, {
        "schema_version": 1,
        "baseline_main_sha": "15bbbab131df86cc38ab583d3180acbfa494249d",
        "current_state": "ALERT_DISPATCHER_AND_RECEIPT_CANDIDATE_STAGED_NO_REMOTE_MUTATION",
    }, "Stage35 candidate authority")
    require(candidate_authority.get("next_stage", {}), {
        "name": "PROMOTE_EXACT_STAGE35_RECEIPT_STORE_TO_REPO_MIGRATION_AND_PREPARE_DEPLOYMENT_SEAL",
        "allowed_now": False,
        "requires_candidate_full_ci_green": True,
        "requires_candidate_merge_to_main": True,
        "requires_exact_sql_candidate_blob": CANDIDATE_BLOB,
        "requires_exact_dispatcher_blob": DISPATCHER_BLOB,
        "requires_no_remote_mutation_before_promotion": True,
        "requires_no_launch_gate_promotion": True,
    }, "candidate next-stage contract")
    require(current, {
        "current_state": "POST_REVOCATION_EDGE_BOUNDARY_VERIFIED_SOURCE_METADATA_RECONCILIATION_PENDING_ALERT_DELIVERY_UNVERIFIED",
    }, "current boundary authority")
    require(alert_contract, {
        "current_state": "ALERT_DELIVERY_CONTRACT_PREPARED_RUNTIME_NOT_IMPLEMENTED",
    }, "alert contract")

    require(authority, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE35_ALERT_DELIVERY_RECEIPT_STORE_MIGRATION_PROMOTION",
        "baseline_main_sha": BASELINE,
        "current_state": "RECEIPT_STORE_MIGRATION_REPO_ONLY_DISPATCHER_DEPLOYMENT_SEAL_PENDING",
    }, "promotion authority")
    if set(authority.get("failure_classes", [])) != {
        "BGF-STAGE35-ALERT-CLAIM-DUPLICATE-275",
        "BGF-STAGE35-ALERT-UNKNOWN-DELIVERY-RETRY-276",
        "BGF-STAGE35-ALERT-RECEIPT-SCOPE-277",
        "BGF-STAGE35-ALERT-PROOF-CUSTOMER-CROSSOVER-278",
        "BGF-STAGE35-ALERT-DISPATCH-AUTH-BYPASS-279",
        "BGF-STAGE35-ALERT-PROVIDER-RECEIPT-SELF-ATTESTATION-280",
        "BGF-STAGE35-ALERT-CANDIDATE-REMOTE-MUTATION-281",
        FAILURE_CLASS,
        "BGF-STAGE35-ALERT-DISPATCHER-PREMATURE-DEPLOYMENT-283",
    }:
        fail("promotion authority failure-class set drifted")

    require(authority.get("candidate_receipt", {}), {
        "candidate_pr": 99,
        "candidate_head_sha": "fd5c3edef2cb865102686640b4b2ed3313464c23",
        "candidate_merge_main_sha": BASELINE,
        "quality_gate_run": 32560729198,
        "quality_gate_job": 97001758640,
        "stage35_run": 32560729211,
        "stage35_job": 97001758534,
        "stage34_assessment_lifecycle_run": 32560729197,
        "stage34_current_boundary_lifecycle_run": 32560729195,
        "result": "PASS",
    }, "candidate receipt")
    require(authority.get("fresh_pre_promotion_receipt", {}), {
        "source": "Supabase.execute_sql+Supabase.list_migrations+Supabase.list_edge_functions",
        "observed_at_utc": OBSERVED,
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
    }, "fresh pre-promotion receipt")
    deployed = authority["fresh_pre_promotion_receipt"].get("deployed_edge_functions", [])
    if deployed != [{
        "slug": "student-access-gateway",
        "version": 3,
        "status": "ACTIVE",
        "verify_jwt": False,
        "bundle_sha256": "b57892b3f399b76f8127c9a39d3d8c021ffe639aa7bf92c7fa9a459d35721b82",
    }]:
        fail("pre-promotion Edge inventory drifted")

    if git_blob_sha(MIGRATION) != MIGRATION_BLOB:
        fail("Stage35 migration Git blob drifted")
    if git_blob_sha(CANDIDATE) != CANDIDATE_BLOB:
        fail("Stage35 source candidate Git blob drifted")
    if git_blob_sha(DISPATCHER) != DISPATCHER_BLOB:
        fail("Stage35 dispatcher Git blob drifted")
    if executable_body(migration, "migration") != executable_body(candidate, "candidate"):
        fail("promoted migration executable body is not byte-identical to reviewed candidate")

    require(authority.get("migration_promotion", {}), {
        "migration_name": MIGRATION_NAME,
        "migration_file": "04_backend_supabase/migrations/20260822075500_stage35_alert_delivery_receipt_store.sql",
        "migration_git_blob_sha": MIGRATION_BLOB,
        "source_candidate_file": "04_backend_supabase/operations/stage35_alert_delivery_receipt_store_candidate.sql",
        "source_candidate_git_blob_sha": CANDIDATE_BLOB,
        "executable_body_byte_identical": True,
        "migration_ledger_state": "repo_only",
        "remote_applied": False,
        "remote_version": None,
        "apply_count": 0,
        "remote_apply_allowed_after_this_pr_alone": False,
        "service_role_only_public_bridges": True,
        "public_bridges_security_invoker": True,
        "private_receipt_table_direct_service_role_access": False,
        "unknown_delivery_automatic_retry": False,
        "max_attempts": 3,
    }, "migration promotion")

    if ledger.get("baseline_main_sha") != BASELINE:
        fail("migration ledger baseline drifted")
    if ledger.get("observed_at_utc") != OBSERVED:
        fail("migration ledger observation drifted")
    remote = {
        row.get("name"): row.get("version")
        for row in ledger.get("remote_migrations", []) if isinstance(row, dict)
    }
    if remote.get("stage33_direct_rpc_revocation_and_post_revocation_fixture") != "20260822032456":
        fail("Stage33 revocation remote receipt drifted")
    if remote.get("stage33_post_revocation_proof_cleanup") != "20260822061133":
        fail("Stage33 cleanup remote receipt drifted")
    if MIGRATION_NAME in remote:
        fail("Stage35 receipt-store migration unexpectedly remote")
    repo_only = [
        row for row in ledger.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    ]
    if len(repo_only) != 1 or repo_only[0].get("name") != MIGRATION_NAME:
        fail("Stage35 receipt store must be unique repo-only divergence")
    if repo_only[0].get("related_failure_class") != "BGF-STAGE35-ALERT-CANDIDATE-REMOTE-MUTATION-281":
        fail("Stage35 repo-only failure-class binding drifted")

    migration_names = [path.name for path in (BACKEND / "migrations").glob("*.sql") if "stage35" in path.name]
    if migration_names != ["20260822075500_stage35_alert_delivery_receipt_store.sql"]:
        fail(f"unexpected Stage35 migration inventory: {migration_names}")
    if PROOF_WORKFLOW.exists():
        fail("controlled external delivery proof workflow materialized before deployment seal")

    lower_dispatcher = dispatcher.decode("utf-8").lower()
    for fragment in (
        'deno.env.get("student_access_alert_dispatch_token")',
        'deno.env.get("student_access_alert_telegram_bot_token")',
        'deno.env.get("student_access_alert_telegram_chat_id")',
        'const dispatch_header = "x-fitnexus-alert-dispatch-token";',
        "alert_provider_delivered_receipt_persistence_unconfirmed",
        "telegram_network_delivery_unknown",
        "telegram_destination_mismatch",
    ):
        if fragment not in lower_dispatcher:
            fail(f"dispatcher security invariant missing: {fragment}")
    if "console.log" in lower_dispatcher or "console.error" in lower_dispatcher:
        fail("dispatcher logging appeared")

    for fragment in (
        "StudentAccessTransportMode.edgeGateway;",
        "static const bool edgeGatewaySelected = true;",
        "static const bool automaticEdgeToDirectFallback = false;",
        "static const bool explicitRollbackRequested = false;",
        "static const bool explicitRollbackAuthorized = false;",
        "static const bool directRpcExecuteRevoked = false;",
        "static const bool rollbackVerified = false;",
        "static const bool clientCutoverVerified = false;",
    ):
        if fragment not in transport:
            fail(f"promotion must not change production transport/source metadata: {fragment}")

    require(authority.get("dispatcher_seal_boundary", {}), {
        "dispatcher_git_blob_sha": DISPATCHER_BLOB,
        "remote_deployed": False,
        "deployment_count": 0,
        "runtime_secrets_configured_by_this_stage": False,
        "verify_jwt_deployment_decision": "custom_dispatch_secret_required_before_verify_jwt_false",
        "custom_dispatch_auth_present_in_source": True,
        "deployment_seal_authority_present": False,
        "controlled_proof_fixture_present": False,
        "one_shot_proof_workflow_present": False,
        "external_provider_receipt_verified": False,
        "external_provider_called": False,
    }, "dispatcher seal boundary")
    require(authority.get("repository_boundary", {}), {
        "migration_ledger_unique_repo_only_name": MIGRATION_NAME,
        "stage33_remote_migrations_unchanged": True,
        "stage33_direct_rpc_revocation_unchanged": True,
        "stage33_cleanup_unchanged": True,
        "production_student_transport_unchanged": True,
        "source_transport_metadata_unchanged": True,
        "automatic_edge_to_direct_fallback": False,
        "direct_rpc_regrant_performed": False,
        "consumed_proof_replayed": False,
    }, "repository boundary")
    require(authority.get("promotion_rules", {}), {
        "may_execute_operations_candidate": False,
        "may_apply_stage35_receipt_store_remotely": False,
        "may_deploy_alert_dispatcher": False,
        "may_configure_provider_or_dispatch_secrets_in_repository": False,
        "may_create_controlled_alert_signal": False,
        "may_call_telegram_provider": False,
        "may_reexecute_consumed_stage31_32_33_proofs": False,
        "may_advance_source_transport_metadata": False,
        "may_promote_incident_response_gate": False,
        "may_promote_production_deployment_gate": False,
        "may_enable_paid_ads": False,
    }, "promotion rules")

    print("STAGE35_ALERT_RECEIPT_STORE_MIGRATION_PROMOTION_GUARD=PASS")
    print(f"BASELINE_MAIN_SHA={BASELINE}")
    print(f"MIGRATION_BLOB={MIGRATION_BLOB}")
    print(f"SOURCE_CANDIDATE_BLOB={CANDIDATE_BLOB}")
    print(f"DISPATCHER_BLOB={DISPATCHER_BLOB}")
    print("EXECUTABLE_BODY_BYTE_IDENTICAL=true")
    print("MIGRATION_LEDGER_STATE=repo_only")
    print("RECEIPT_STORE_REMOTE_APPLIED=false")
    print("ALERT_DISPATCHER_REMOTE_DEPLOYED=false")
    print("EXTERNAL_PROVIDER_CALLED=false")
    print("CONTROLLED_EXTERNAL_DELIVERY_PROOF=false")
    print("SOURCE_TRANSPORT_METADATA_CHANGED=false")
    print("INCIDENT_RESPONSE_GATE=DENIED")
    print("PRODUCTION_DEPLOYMENT_GATE=DENIED")
    print("PAID_MEDIA_GATE=DENIED")


if __name__ == "__main__":
    main()
