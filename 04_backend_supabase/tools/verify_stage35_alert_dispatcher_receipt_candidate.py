from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage35_alert_dispatcher_receipt_candidate_authority.json"
CURRENT = BACKEND / "student_access_current_boundary_authority.json"
CONTRACT = BACKEND / "student_access_alert_delivery_contract.json"
CLEANUP = BACKEND / "stage33_post_revocation_proof_cleanup_authority.json"
LEDGER = BACKEND / "migration_ledger_authority.json"
SQL = BACKEND / "operations" / "stage35_alert_delivery_receipt_store_candidate.sql"
DISPATCHER = BACKEND / "functions" / "student-access-alert-dispatcher" / "index.ts"
GATEWAY = BACKEND / "functions" / "student-access-gateway" / "index.ts"
MIGRATIONS = BACKEND / "migrations"
OPERATIONS = BACKEND / "operations"

BASELINE = "15bbbab131df86cc38ab583d3180acbfa494249d"
SQL_BLOB = "465c6a76249847673a6e8d627c8a882d2331217a"
DISPATCHER_BLOB = "0aece761d707d8befb64a0fb89ce495fc50255a0"
FAILURE_CLASS = "BGF-STAGE35-ALERT-CANDIDATE-REMOTE-MUTATION-281"
PROOF_MARKER = "fitnexus-stage34-alert-delivery-proof-v1"


def fail(message: str) -> None:
    raise SystemExit(
        "STAGE35_ALERT_DISPATCHER_RECEIPT_CANDIDATE_GUARD=FAIL\n"
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


def main() -> None:
    authority = load(AUTHORITY)
    current = load(CURRENT)
    contract = load(CONTRACT)
    cleanup = load(CLEANUP)
    ledger = load(LEDGER)
    sql = raw(SQL).decode("utf-8")
    dispatcher = raw(DISPATCHER).decode("utf-8")
    gateway = raw(GATEWAY).decode("utf-8")

    require(current, {
        "schema_version": 1,
        "baseline_main_sha": "c0ae8148fcb32f3190be3380d8989144a54fd1e7",
        "current_state": "POST_REVOCATION_EDGE_BOUNDARY_VERIFIED_SOURCE_METADATA_RECONCILIATION_PENDING_ALERT_DELIVERY_UNVERIFIED",
    }, "current boundary authority")
    require(contract, {
        "schema_version": 1,
        "baseline_main_sha": "c0ae8148fcb32f3190be3380d8989144a54fd1e7",
        "current_state": "ALERT_DELIVERY_CONTRACT_PREPARED_RUNTIME_NOT_IMPLEMENTED",
    }, "alert contract")
    require(cleanup, {
        "current_state": "POST_REVOCATION_EDGE_PROOF_VERIFIED_CLEANUP_REMOTE_COMPLETE",
    }, "Stage33 cleanup authority")
    require(cleanup.get("post_cleanup_receipt", {}), {
        "auth_users": 0,
        "organizations": 0,
        "students": 0,
        "security_events": 0,
        "security_signals": 0,
        "global_network_buckets": 13,
        "global_growth_events": 6,
        "anon_execute_count": 0,
        "authenticated_execute_count": 0,
        "service_role_execute_count": 5,
        "issue_student_access_token_v2_authenticated_execute": True,
        "security_posture_after_cleanup": "quiet",
    }, "Stage33 post-cleanup truth")

    remote = {
        row.get("name"): row.get("version")
        for row in ledger.get("remote_migrations", []) if isinstance(row, dict)
    }
    if remote.get("stage33_direct_rpc_revocation_and_post_revocation_fixture") != "20260822032456":
        fail("Stage33 revocation remote receipt drifted")
    if remote.get("stage33_post_revocation_proof_cleanup") != "20260822061133":
        fail("Stage33 cleanup remote receipt drifted")
    if any(
        isinstance(row, dict) and row.get("direction") == "repo_only"
        for row in ledger.get("declared_divergences", [])
    ):
        fail("candidate must not create repository migration divergence")

    require(authority, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE35_ALERT_DISPATCHER_RECEIPT_CANDIDATE",
        "baseline_main_sha": BASELINE,
        "current_state": "ALERT_DISPATCHER_AND_RECEIPT_CANDIDATE_STAGED_NO_REMOTE_MUTATION",
    }, "Stage35 authority")
    if set(authority.get("failure_classes", [])) != {
        "BGF-STAGE35-ALERT-CLAIM-DUPLICATE-275",
        "BGF-STAGE35-ALERT-UNKNOWN-DELIVERY-RETRY-276",
        "BGF-STAGE35-ALERT-RECEIPT-SCOPE-277",
        "BGF-STAGE35-ALERT-PROOF-CUSTOMER-CROSSOVER-278",
        "BGF-STAGE35-ALERT-DISPATCH-AUTH-BYPASS-279",
        "BGF-STAGE35-ALERT-PROVIDER-RECEIPT-SELF-ATTESTATION-280",
        FAILURE_CLASS,
    }:
        fail("Stage35 failure-class set drifted")

    require(authority.get("prerequisites", {}), {
        "required_current_boundary_state": "POST_REVOCATION_EDGE_BOUNDARY_VERIFIED_SOURCE_METADATA_RECONCILIATION_PENDING_ALERT_DELIVERY_UNVERIFIED",
        "required_alert_contract_state": "ALERT_DELIVERY_CONTRACT_PREPARED_RUNTIME_NOT_IMPLEMENTED",
        "preparation_pr": 98,
        "preparation_head_sha": "4d5d89dfa15ed12b94900ea54e323546e0d37e5c",
        "preparation_merge_main_sha": BASELINE,
        "preparation_quality_gate_run": 32560302863,
        "preparation_quality_gate_job": 97000751486,
        "preparation_dedicated_run": 32560302802,
        "preparation_dedicated_job": 97000751326,
        "preparation_result": "PASS",
    }, "Stage35 prerequisites")
    require(authority.get("fresh_live_receipt", {}), {
        "source": "Supabase.execute_sql+Supabase.list_edge_functions",
        "observed_at_utc": "2026-08-22T07:44:50.934525Z",
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
        "deployed_edge_function_count": 1,
        "student_access_alert_dispatcher_deployed": False,
    }, "fresh live receipt")
    deployed = authority.get("fresh_live_receipt", {}).get("deployed_edge_functions", [])
    if deployed != [{
        "slug": "student-access-gateway",
        "version": 3,
        "status": "ACTIVE",
        "verify_jwt": False,
        "bundle_sha256": "b57892b3f399b76f8127c9a39d3d8c021ffe639aa7bf92c7fa9a459d35721b82",
    }]:
        fail("fresh deployed Edge inventory drifted")

    if git_blob_sha(SQL) != SQL_BLOB:
        fail("receipt-store candidate Git blob drifted")
    if git_blob_sha(DISPATCHER) != DISPATCHER_BLOB:
        fail("dispatcher candidate Git blob drifted")
    require(authority.get("receipt_store_candidate", {}), {
        "git_blob_sha": SQL_BLOB,
        "operations_only": True,
        "migration_file_present": False,
        "remote_applied": False,
        "remote_version": None,
        "table": "private.student_access_alert_delivery_receipts",
        "public_claim_bridge": "public.claim_student_access_alert_delivery_v1(text,text)",
        "public_record_bridge": "public.record_student_access_alert_delivery_v1(uuid,text,bigint,text)",
        "public_bridges_security_invoker": True,
        "public_bridges_service_role_only": True,
        "private_functions_security_definer": True,
        "receipt_table_direct_service_role_access": False,
        "max_attempts": 3,
        "claim_lease_minutes": 2,
        "expired_pending_becomes_unknown": True,
        "unknown_automatic_retry": False,
        "delivered_automatic_retry": False,
        "failed_bounded_retry": True,
        "controlled_proof_marker": PROOF_MARKER,
        "controlled_proof_requires_network_rate_limit_burst_high": True,
        "normal_dispatch_excludes_proof_subjects": True,
    }, "receipt-store candidate authority")
    require(authority.get("dispatcher_candidate", {}), {
        "git_blob_sha": DISPATCHER_BLOB,
        "edge_function_name": "student-access-alert-dispatcher",
        "repository_source_present": True,
        "remote_deployed": False,
        "deployment_count": 0,
        "method": "POST",
        "custom_dispatch_header": "x-fitnexus-alert-dispatch-token",
        "dispatch_secret_env": "STUDENT_ACCESS_ALERT_DISPATCH_TOKEN",
        "telegram_token_env": "STUDENT_ACCESS_ALERT_TELEGRAM_BOT_TOKEN",
        "telegram_chat_env": "STUDENT_ACCESS_ALERT_TELEGRAM_CHAT_ID",
        "provider": "telegram_bot_api",
        "provider_endpoint": "sendMessage",
        "provider_call_inline_with_student_gateway": False,
        "service_side_only": True,
        "claims_via_service_role_bridge": True,
        "records_via_service_role_bridge": True,
        "destination_id_persisted": False,
        "destination_fingerprint_sha256_only": True,
        "raw_token_sent": False,
        "raw_network_origin_sent": False,
        "network_origin_digest_sent": False,
        "subject_key_sent": False,
        "customer_identifiers_sent": False,
        "provider_credentials_logged": False,
        "success_requires_http_200": True,
        "success_requires_provider_ok_true": True,
        "success_requires_positive_message_id": True,
        "success_requires_destination_match": True,
        "provider_network_error_is_unknown": True,
        "provider_success_receipt_invalid_is_unknown": True,
        "provider_rejection_is_failed": True,
        "receipt_persistence_failure_after_provider_success_is_not_reported_as_success": True,
    }, "dispatcher candidate authority")

    lower_sql = sql.lower()
    required_sql = (
        "this file is not a migration and must not be executed from operations/",
        "private.student_access_alert_delivery_receipts",
        "status in ('pending','delivered','failed','unknown')",
        "attempt_number between 1 and 3",
        "claim_lease_expired_delivery_unknown",
        "r.status in ('delivered','pending','unknown')",
        "r.status = 'failed'",
        "r.attempt_number < 3",
        "s.subject_key not like 'proof:%'",
        "s.subject_key = 'proof:' || p_controlled_proof_marker",
        "security invoker",
        "grant execute on function public.claim_student_access_alert_delivery_v1(text,text)",
        "grant execute on function public.record_student_access_alert_delivery_v1(uuid,text,bigint,text)",
    )
    for fragment in required_sql:
        if fragment not in lower_sql:
            fail(f"receipt-store invariant missing: {fragment}")
    if "grant execute on function public.claim_student_access_alert_delivery_v1(text,text)\n  to anon" in lower_sql:
        fail("claim bridge exposed to anon")
    if "grant execute on function public.record_student_access_alert_delivery_v1(uuid,text,bigint,text)\n  to authenticated" in lower_sql:
        fail("record bridge exposed to authenticated")
    if "raw_network_origin" in lower_sql and "never persisted" not in lower_sql:
        fail("candidate SQL contains unexpected raw network-origin semantics")

    migration_names = {path.name for path in MIGRATIONS.glob("*.sql")}
    if any("stage35" in name or "alert_delivery_receipt" in name for name in migration_names):
        fail("Stage35 receipt-store migration materialized prematurely")
    operation_names = sorted(path.name for path in OPERATIONS.iterdir() if path.is_file())
    if operation_names != [
        "stage32_rearm_expired_fixture_r1.sql",
        "stage33_direct_rpc_regrant_recovery.sql",
        "stage33_direct_rpc_revocation_and_post_revocation_fixture_candidate.sql",
        "stage35_alert_delivery_receipt_store_candidate.sql",
    ]:
        fail(f"unexpected operations inventory: {operation_names}")

    required_dispatcher = (
        'const telegram_base_url = "https://api.telegram.org";',
        'const dispatch_header = "x-fitnexus-alert-dispatch-token";',
        'deno.env.get("student_access_alert_dispatch_token")',
        'deno.env.get("student_access_alert_telegram_bot_token")',
        'deno.env.get("student_access_alert_telegram_chat_id")',
        "fitnexus-alert-destination-v1:",
        "alert_provider_delivered_receipt_persistence_unconfirmed",
        '"unknown",\n      null,\n      "telegram_network_delivery_unknown"',
        '"unknown",\n      null,\n      "telegram_success_receipt_invalid"',
        'if (string(chat.id) !== telegramchatid)',
        'provider_message_id: messageid',
        'controlled_proof_marker: proofmarker ?? false',
    )
    lower_dispatcher = dispatcher.lower()
    for fragment in required_dispatcher:
        if fragment not in lower_dispatcher:
            fail(f"dispatcher invariant missing: {fragment}")
    if "console.log" in dispatcher or "console.error" in dispatcher or "console.warn" in dispatcher:
        fail("dispatcher must not log provider/security material")
    if "organization_id:" in lower_dispatcher or "student_id:" in lower_dispatcher or "link_id:" in lower_dispatcher:
        fail("dispatcher message surface contains customer identifiers")
    if "subject_key:" in lower_dispatcher or "raw_network_origin" in lower_dispatcher or "origin_hash" in lower_dispatcher:
        fail("dispatcher message surface contains forbidden network/subject material")
    if "student-access-alert-dispatcher" in gateway or "api.telegram.org" in gateway.lower():
        fail("alert provider call must not be added to student-access-gateway critical path")

    require(authority.get("remote_mutation_boundary", {}), {
        "database_ddl_applied": False,
        "database_dml_applied": False,
        "database_privileges_changed": False,
        "edge_function_deployed": False,
        "runtime_secrets_configured_by_this_stage": False,
        "synthetic_signal_created": False,
        "external_provider_called": False,
        "source_transport_metadata_changed": False,
        "direct_rpc_regrant_performed": False,
    }, "remote mutation boundary")
    require(authority.get("proof_boundary", {}), {
        "controlled_external_delivery_proof_completed": False,
        "external_provider_receipt_verified": False,
        "proof_workflow_present": False,
        "proof_candidate_head_sealed": False,
        "one_shot_proof_required": True,
        "real_customer_data_allowed": False,
        "proof_reexecution_after_success_allowed": False,
        "proof_cleanup_required": True,
    }, "proof boundary")
    require(authority.get("promotion_rules", {}), {
        "may_execute_operations_sql": False,
        "may_apply_receipt_store_remotely": False,
        "may_deploy_alert_dispatcher": False,
        "may_configure_runtime_secrets_in_repo": False,
        "may_create_controlled_signal": False,
        "may_call_external_provider": False,
        "may_advance_source_transport_metadata": False,
        "may_reexecute_consumed_stage31_32_33_proofs": False,
        "may_promote_incident_response_gate": False,
        "may_promote_production_deployment_gate": False,
        "may_enable_paid_ads": False,
    }, "promotion rules")

    print("STAGE35_ALERT_DISPATCHER_RECEIPT_CANDIDATE_GUARD=PASS")
    print(f"BASELINE_MAIN_SHA={BASELINE}")
    print(f"RECEIPT_STORE_CANDIDATE_BLOB={SQL_BLOB}")
    print(f"DISPATCHER_CANDIDATE_BLOB={DISPATCHER_BLOB}")
    print("RECEIPT_STORE_STATE=operations_only")
    print("ALERT_DISPATCHER_REMOTE_DEPLOYED=false")
    print("EXTERNAL_PROVIDER_CALLED=false")
    print("UNKNOWN_DELIVERY_AUTOMATIC_RETRY=false")
    print("CONTROLLED_ALERT_PROOF_COMPLETED=false")
    print("SOURCE_TRANSPORT_METADATA_CHANGED=false")
    print("INCIDENT_RESPONSE_GATE=DENIED")
    print("PRODUCTION_DEPLOYMENT_GATE=DENIED")
    print("PAID_MEDIA_GATE=DENIED")


if __name__ == "__main__":
    main()
