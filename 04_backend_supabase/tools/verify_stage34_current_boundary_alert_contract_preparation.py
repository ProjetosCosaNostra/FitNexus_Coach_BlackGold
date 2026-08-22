from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
APP = ROOT / "03_app_flutter" / "fitnexus_app"
CURRENT = BACKEND / "student_access_current_boundary_authority.json"
ALERT = BACKEND / "student_access_alert_delivery_contract.json"
ASSESSMENT = BACKEND / "stage34_post_revocation_boundary_assessment_authority.json"
CLEANUP = BACKEND / "stage33_post_revocation_proof_cleanup_authority.json"
LEDGER = BACKEND / "migration_ledger_authority.json"
EXPOSURE = BACKEND / "security_definer_exposure_authority.json"
CLIENT = BACKEND / "student_access_client_cutover_authority.json"
SELECTION = BACKEND / "student_access_production_edge_selection_authority.json"
NETWORK = BACKEND / "student_access_network_origin_boundary.json"
ABUSE = BACKEND / "student_access_abuse_authority.json"
CONTRACT = APP / "lib" / "features" / "student" / "student_access_transport_contract.dart"
OPERATIONS = BACKEND / "operations"
ALERT_FUNCTION_DIR = BACKEND / "functions" / "student-access-alert-dispatcher"

BASELINE = "c0ae8148fcb32f3190be3380d8989144a54fd1e7"
REVOCATION_VERSION = "20260822032456"
CLEANUP_VERSION = "20260822061133"
FAILURE_CLASS = "BGF-STAGE34-CURRENT-BOUNDARY-SELF-ATTESTATION-268"


def fail(message: str) -> None:
    raise SystemExit(
        "STAGE34_CURRENT_BOUNDARY_ALERT_CONTRACT_PREPARATION_GUARD=FAIL\n"
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


def require(mapping: dict, expected: dict, label: str) -> None:
    if not isinstance(mapping, dict):
        fail(f"{label} must be an object")
    for key, expected_value in expected.items():
        if mapping.get(key) != expected_value:
            fail(f"{label} drift: {key}")


def main() -> None:
    current = load(CURRENT)
    alert = load(ALERT)
    assessment = load(ASSESSMENT)
    cleanup = load(CLEANUP)
    ledger = load(LEDGER)
    exposure = load(EXPOSURE)
    client = load(CLIENT)
    selection = load(SELECTION)
    network = load(NETWORK)
    abuse = load(ABUSE)
    contract = CONTRACT.read_text(encoding="utf-8")

    require(assessment, {
        "schema_version": 1,
        "current_state": "ASSESSMENT_COMPLETE_FAIL_CLOSED_ALERT_DELIVERY_AND_SOURCE_AUTHORITY_RECONCILIATION_REQUIRED",
        "baseline_main_sha": "8bffaabfa72103257fec80f997dc6b2fa6a86f48",
    }, "Stage34 assessment")
    require(assessment.get("next_stage", {}), {
        "name": "PREPARE_STAGE34_CURRENT_BOUNDARY_AUTHORITY_AND_ALERT_DELIVERY_CONTRACT",
        "allowed_now": True,
        "repository_only": True,
        "requires_historical_guard_projection_for_source_metadata": True,
        "requires_external_alert_delivery_contract_before_runtime_proof": True,
        "requires_no_real_customer_data": True,
        "requires_no_proof_replay": True,
        "requires_no_remote_privilege_mutation": True,
        "may_promote_launch_gates": False,
    }, "Stage34 assessment next-stage authorization")

    require(cleanup, {
        "current_state": "POST_REVOCATION_EDGE_PROOF_VERIFIED_CLEANUP_REMOTE_COMPLETE",
        "baseline_main_sha": "e30aa197fe5d19b9e385a8720944c6c9c10d34ee",
    }, "Stage33 cleanup authority")
    require(cleanup.get("cleanup", {}), {
        "migration_ledger_state": "remote_reconciled",
        "remote_applied": True,
        "remote_version": CLEANUP_VERSION,
        "apply_count": 1,
        "cleanup_completed": True,
        "reapply_allowed": False,
    }, "Stage33 cleanup receipt")
    require(cleanup.get("post_cleanup_receipt", {}), {
        "auth_users": 0,
        "organizations": 0,
        "students": 0,
        "security_events": 0,
        "security_signals": 0,
        "global_growth_events": 6,
        "global_network_buckets": 13,
        "proof_network_buckets": 0,
        "anon_execute_count": 0,
        "authenticated_execute_count": 0,
        "service_role_execute_count": 5,
        "issue_student_access_token_v2_authenticated_execute": True,
        "security_posture_after_cleanup": "quiet",
        "direct_student_route_security_definer_warnings": 0,
    }, "Stage33 live post-cleanup truth")

    remote = {
        row.get("name"): row.get("version")
        for row in ledger.get("remote_migrations", []) if isinstance(row, dict)
    }
    if remote.get("stage33_direct_rpc_revocation_and_post_revocation_fixture") != REVOCATION_VERSION:
        fail("Stage33 revocation remote version missing")
    if remote.get("stage33_post_revocation_proof_cleanup") != CLEANUP_VERSION:
        fail("Stage33 cleanup remote version missing")
    if any(
        isinstance(row, dict) and row.get("direction") == "repo_only"
        for row in ledger.get("declared_divergences", [])
    ):
        fail("preparation must not create a migration divergence")

    require(exposure, {
        "schema_version": 2,
        "current_state": "STAGE33_REVOCATION_REMOTE_RECONCILED_POST_REVOCATION",
    }, "SECURITY DEFINER authority")
    require(exposure.get("stage33_transition", {}), {
        "remote_applied": True,
        "remote_version": REVOCATION_VERSION,
        "repository_target_anon_exposures": 0,
        "repository_target_authenticated_exposures": 1,
        "service_role_preserved_for_edge_backend": True,
        "issue_student_access_token_v2_preserved": True,
        "post_revocation_live_anon_execute_count": 0,
        "post_revocation_live_authenticated_execute_count": 0,
        "post_revocation_live_service_role_execute_count": 5,
        "post_revocation_student_route_advisor_warnings": 0,
    }, "Stage33 exposure transition")

    # Stage32 files remain immutable historical snapshots in this preparation.
    require(client, {
        "schema_version": 2,
        "current_state": "CLIENT_EDGE_SELECTED_POST_CUTOVER_PROOF_PENDING",
    }, "historical client cutover snapshot")
    require(selection, {
        "schema_version": 1,
        "current_state": "PRODUCTION_EDGE_SELECTION_CANDIDATE_EDGE_MODE_POST_CUTOVER_PROOF_PENDING",
    }, "historical production selection snapshot")
    require(network, {
        "schema_version": 5,
        "current_state": "ORIGIN_SOURCE_SPOOF_RESISTANCE_AND_EDGE_THRESHOLD_VERIFIED",
    }, "historical network authority")
    require(network.get("current_client_boundary", {}), {
        "anonymous_v2_rpc_execute_required_by_current_client": True,
        "valid_student_route_verified_live": False,
        "edge_alert_delivery_verified": False,
    }, "historical network client fields")
    if network.get("target_cutover_invariants", {}).get("alert_delivery_requires_real_runtime_receipt") is not True:
        fail("network authority lost external alert receipt requirement")
    if abuse.get("launch_authority", {}).get("can_promote_incident_response_gate") is not False:
        fail("abuse authority unexpectedly promoted incident response")

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
        if fragment not in contract:
            fail(f"preparation must not advance transport source metadata: {fragment}")

    require(current, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE34_CURRENT_STUDENT_ACCESS_BOUNDARY",
        "baseline_main_sha": BASELINE,
        "current_state": "POST_REVOCATION_EDGE_BOUNDARY_VERIFIED_SOURCE_METADATA_RECONCILIATION_PENDING_ALERT_DELIVERY_UNVERIFIED",
    }, "current student-access authority")
    if set(current.get("failure_classes", [])) != {
        FAILURE_CLASS,
        "BGF-STAGE34-SOURCE-METADATA-PREMATURE-PROMOTION-269",
        "BGF-STAGE34-ALERT-DELIVERY-RECEIPT-AMBIGUITY-270",
        "BGF-STAGE34-ALERT-SECRET-LEAK-271",
        "BGF-STAGE34-ALERT-PAYLOAD-PRIVACY-272",
        "BGF-STAGE34-ALERT-DELIVERY-REPLAY-273",
    }:
        fail("current authority failure-class set drifted")
    require(current.get("verified_remote_truth", {}), {
        "revocation_remote_version": REVOCATION_VERSION,
        "cleanup_remote_version": CLEANUP_VERSION,
        "target_student_rpc_count": 5,
        "anon_execute_count": 0,
        "authenticated_execute_count": 0,
        "service_role_execute_count": 5,
        "issue_student_access_token_v2_authenticated_execute": True,
        "synthetic_customer_runtime_residue": 0,
        "global_historical_network_buckets": 13,
        "global_historical_growth_events": 6,
        "security_posture": "quiet",
        "direct_student_route_security_definer_warnings": 0,
    }, "current remote truth")
    require(current.get("verified_runtime_truth", {}), {
        "active_transport": "edgeGateway",
        "resolved_transport": "edgeGateway",
        "production_singleton": "StudentAccessTransport.instance",
        "edge_function_name": "student-access-gateway",
        "edge_runtime_version": 3,
        "route_count": 5,
        "all_five_routes_share_single_transport": True,
        "automatic_edge_to_direct_fallback": False,
        "post_cutover_edge_runtime_proof_verified": True,
        "post_cutover_rollback_proof_verified_before_revocation": True,
        "post_revocation_edge_runtime_proof_verified": True,
        "direct_http_rpc_denial_verified_after_revocation": True,
        "direct_http_rpc_denial_status": 401,
        "direct_http_synthetic_data_returned": False,
    }, "current runtime truth")
    require(current.get("source_metadata_reconciliation", {}), {
        "active_edge_transport_is_correct": True,
        "automatic_fallback_disabled_is_correct": True,
        "source_direct_rpc_execute_revoked_flag": False,
        "verified_direct_rpc_execute_revoked_truth": True,
        "source_rollback_verified_flag": False,
        "verified_post_cutover_rollback_truth": True,
        "source_client_cutover_verified_flag": False,
        "verified_client_cutover_truth": True,
        "metadata_flags_stale": True,
        "metadata_flag_advance_allowed_in_this_preparation": False,
        "direct_rpc_runtime_branch_removal_allowed": False,
        "direct_route_map_removal_allowed": False,
        "emergency_regrant_recovery_removal_allowed": False,
        "requires_historical_guard_projection_before_flag_advance": True,
    }, "source metadata boundary")
    require(current.get("alert_delivery_boundary", {}), {
        "external_delivery_required": True,
        "runtime_implementation_present": False,
        "runtime_deployed": False,
        "controlled_signal_runtime_proof_completed": False,
        "external_delivery_receipt_verified": False,
        "synthetic_database_signal_only_is_sufficient": False,
        "self_attestation_allowed": False,
        "real_customer_data_required": False,
        "raw_token_allowed": False,
        "raw_network_origin_allowed": False,
        "network_origin_digest_allowed": False,
        "credential_material_allowed": False,
    }, "current alert boundary")

    require(alert, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE34_STUDENT_ACCESS_ALERT_DELIVERY_CONTRACT",
        "baseline_main_sha": BASELINE,
        "current_state": "ALERT_DELIVERY_CONTRACT_PREPARED_RUNTIME_NOT_IMPLEMENTED",
    }, "alert contract")
    require(alert.get("provider_contract", {}), {
        "provider": "telegram_bot_api",
        "delivery_method": "HTTPS_POST_sendMessage",
        "base_url": "https://api.telegram.org",
        "endpoint_template": "/bot<secret-token>/sendMessage",
        "destination_is_runtime_secret": True,
        "public_marketing_channel_is_not_assumed": True,
        "secrets_must_not_exist_in_repository": True,
        "secrets_must_not_be_logged": True,
        "chat_id_must_not_be_hardcoded": True,
    }, "provider contract")
    required_secrets = alert.get("provider_contract", {}).get("required_runtime_secrets", [])
    if required_secrets != [
        "STUDENT_ACCESS_ALERT_TELEGRAM_BOT_TOKEN",
        "STUDENT_ACCESS_ALERT_TELEGRAM_CHAT_ID",
    ]:
        fail("alert runtime secret contract drifted")

    forbidden = set(alert.get("payload_contract", {}).get("forbidden_fields", []))
    for required_forbidden in (
        "raw_possession_token",
        "service_role_key",
        "supabase_secret_key",
        "telegram_bot_token",
        "raw_network_origin",
        "network_origin_digest",
        "subject_key",
        "arbitrary_request_payload",
        "student_name",
        "email",
        "phone",
    ):
        if required_forbidden not in forbidden:
            fail(f"alert privacy forbidden-field missing: {required_forbidden}")
    require(alert.get("provider_success_receipt", {}), {
        "http_status": 200,
        "response_json_ok": True,
        "requires_positive_message_id": True,
        "requires_result_chat_id_matches_configured_destination": True,
        "raw_provider_response_persistence_allowed": False,
        "http_2xx_without_provider_ok_true_is_success": False,
        "local_log_line_is_external_delivery_receipt": False,
        "database_dispatch_row_without_provider_receipt_is_external_delivery_receipt": False,
    }, "provider receipt contract")
    require(alert.get("runtime_candidate_boundary", {}), {
        "expected_edge_function_name": "student-access-alert-dispatcher",
        "implementation_present_in_this_stage": False,
        "deployment_allowed_in_this_stage": False,
        "client_invocation_allowed": False,
        "anon_invocation_allowed": False,
        "authenticated_client_invocation_allowed": False,
        "scheduled_or_service_side_invocation_only": True,
        "student_access_gateway_inline_provider_call_allowed": False,
    }, "alert runtime candidate boundary")
    require(alert.get("controlled_signal_proof_contract", {}), {
        "required": True,
        "real_customer_data_allowed": False,
        "synthetic_signal_required": True,
        "synthetic_signal_must_be_uniquely_identifiable": True,
        "allowed_signal_type": "network_rate_limit_burst",
        "allowed_severity": "high",
        "proof_marker": "fitnexus-stage34-alert-delivery-proof-v1",
        "external_provider_success_receipt_required": True,
        "provider_message_id_required": True,
        "destination_match_required": True,
        "provider_secret_printing_forbidden": True,
        "raw_network_origin_generation_or_logging_required": False,
        "proof_must_cleanup_synthetic_signal_and_delivery_receipt": True,
        "one_shot_proof_required": True,
        "proof_reexecution_after_success_allowed": False,
    }, "controlled alert proof contract")
    require(alert.get("incident_response_boundary", {}), {
        "contract_is_runtime_evidence": False,
        "implementation_is_runtime_evidence": False,
        "deployment_without_controlled_delivery_receipt_is_runtime_evidence": False,
        "successful_controlled_external_delivery_receipt_required": True,
        "incident_response_gate_may_promote_after_this_contract_alone": False,
        "production_deployment_gate_may_promote_after_this_contract_alone": False,
        "paid_media_gate_may_promote_after_this_contract_alone": False,
    }, "incident response boundary")

    if ALERT_FUNCTION_DIR.exists():
        fail("alert dispatcher implementation appeared during contract-only preparation")
    operation_names = sorted(path.name for path in OPERATIONS.iterdir() if path.is_file())
    if operation_names != [
        "stage32_rearm_expired_fixture_r1.sql",
        "stage33_direct_rpc_regrant_recovery.sql",
        "stage33_direct_rpc_revocation_and_post_revocation_fixture_candidate.sql",
    ]:
        fail(f"operations inventory changed during contract-only preparation: {operation_names}")

    # Never allow literal secret values or provider bot URL material in the contract files.
    combined = CURRENT.read_text(encoding="utf-8") + ALERT.read_text(encoding="utf-8")
    if "api.telegram.org/bot" in combined:
        fail("contract must not materialize a bot-token-bearing URL")
    if "sb_secret_" in combined or "service_role_key=" in combined.lower():
        fail("credential-like material found in Stage34 contract source")

    require(current.get("promotion_rules", {}), {
        "may_reexecute_consumed_proofs": False,
        "may_reapply_stage33_revocation": False,
        "may_reapply_stage33_cleanup": False,
        "may_regrant_direct_rpc_execute_as_normal_flow": False,
        "may_advance_source_metadata_flags_without_historical_projection": False,
        "may_claim_alert_delivery_without_external_provider_receipt": False,
        "may_promote_incident_response_gate": False,
        "may_promote_production_deployment_gate": False,
        "may_enable_paid_ads": False,
    }, "current promotion rules")

    print("STAGE34_CURRENT_BOUNDARY_ALERT_CONTRACT_PREPARATION_GUARD=PASS")
    print(f"BASELINE_MAIN_SHA={BASELINE}")
    print("CURRENT_ACTIVE_TRANSPORT=edgeGateway")
    print("DIRECT_ANON_EXECUTE=0")
    print("DIRECT_AUTHENTICATED_EXECUTE=0")
    print("EDGE_SERVICE_ROLE_EXECUTE=5")
    print("SOURCE_METADATA_RECONCILIATION=PENDING")
    print("ALERT_PROVIDER_CONTRACT=telegram_bot_api")
    print("ALERT_RUNTIME_IMPLEMENTATION_PRESENT=false")
    print("EXTERNAL_ALERT_DELIVERY_RECEIPT=UNVERIFIED")
    print("PROOF_REEXECUTION_ALLOWED=false")
    print("INCIDENT_RESPONSE_GATE=DENIED")
    print("PRODUCTION_DEPLOYMENT_GATE=DENIED")
    print("PAID_MEDIA_GATE=DENIED")


if __name__ == "__main__":
    main()
