from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
APP = ROOT / "03_app_flutter" / "fitnexus_app"
AUTHORITY = BACKEND / "stage34_post_revocation_boundary_assessment_authority.json"
CLEANUP_AUTHORITY = BACKEND / "stage33_post_revocation_proof_cleanup_authority.json"
LEDGER = BACKEND / "migration_ledger_authority.json"
EXPOSURE = BACKEND / "security_definer_exposure_authority.json"
CLIENT = BACKEND / "student_access_client_cutover_authority.json"
SELECTION = BACKEND / "student_access_production_edge_selection_authority.json"
NETWORK = BACKEND / "student_access_network_origin_boundary.json"
ABUSE = BACKEND / "student_access_abuse_authority.json"
CONTRACT = APP / "lib" / "features" / "student" / "student_access_transport_contract.dart"
OPERATIONS = BACKEND / "operations"

FAILURE_CLASS = "BGF-STAGE34-POST-REVOCATION-AUTHORITY-DRIFT-264"
BASELINE = "8bffaabfa72103257fec80f997dc6b2fa6a86f48"
REVOCATION_VERSION = "20260822032456"
CLEANUP_VERSION = "20260822061133"


def fail(message: str) -> None:
    raise SystemExit(
        "STAGE34_POST_REVOCATION_BOUNDARY_ASSESSMENT_GUARD=FAIL\n"
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
    authority = load(AUTHORITY)
    cleanup = load(CLEANUP_AUTHORITY)
    ledger = load(LEDGER)
    exposure = load(EXPOSURE)
    client = load(CLIENT)
    selection = load(SELECTION)
    network = load(NETWORK)
    abuse = load(ABUSE)
    contract = CONTRACT.read_text(encoding="utf-8")

    require(authority, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE34_POST_REVOCATION_BOUNDARY_RECONCILIATION_ASSESSMENT",
        "baseline_main_sha": BASELINE,
        "observed_at_utc": "2026-08-22T06:12:09.300352Z",
        "current_state": "ASSESSMENT_COMPLETE_FAIL_CLOSED_ALERT_DELIVERY_AND_SOURCE_AUTHORITY_RECONCILIATION_REQUIRED",
    }, "Stage34 authority")
    if set(authority.get("failure_classes", [])) != {
        FAILURE_CLASS,
        "BGF-STAGE34-LIVE-SOURCE-REVOCATION-MISMATCH-265",
        "BGF-STAGE34-ALERT-DELIVERY-EVIDENCE-GAP-266",
        "BGF-STAGE34-HISTORICAL-AUTHORITY-AS-CURRENT-267",
    }:
        fail("Stage34 failure-class set drifted")

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
        "workout_sessions": 0,
        "command_receipts": 0,
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
    }, "Stage33 post-cleanup live truth")

    if ledger.get("baseline_main_sha") != "e30aa197fe5d19b9e385a8720944c6c9c10d34ee":
        fail("ledger baseline is not Stage33 cleanup merge")
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
        fail("post-cleanup ledger retained repo-only divergence")

    require(exposure, {
        "schema_version": 2,
        "current_state": "STAGE33_REVOCATION_REMOTE_RECONCILED_POST_REVOCATION",
    }, "SECURITY DEFINER exposure authority")
    require(exposure.get("stage33_transition", {}), {
        "remote_applied": True,
        "remote_version": REVOCATION_VERSION,
        "repository_target_anon_exposures": 0,
        "repository_target_authenticated_exposures": 1,
        "service_role_preserved_for_edge_backend": True,
        "issue_student_access_token_v2_preserved": True,
    }, "SECURITY DEFINER Stage33 transition")

    require(client, {
        "schema_version": 2,
        "current_state": "CLIENT_EDGE_SELECTED_POST_CUTOVER_PROOF_PENDING",
    }, "historical client cutover snapshot")
    require(client.get("current_client_inventory", {}), {
        "transport_mode": "edge_gateway",
        "flutter_uses_edge_gateway": True,
        "direct_v2_rpc_path_active": True,
        "direct_anon_v2_rpc_execute_revoked": False,
    }, "historical client inventory")
    require(client.get("required_before_direct_rpc_revocation", {}), {
        "flutter_edge_gateway_active": True,
        "five_routes_verified_via_edge": False,
        "automatic_direct_fallback_absent": True,
        "post_cutover_rollback_path_verified": False,
        "post_cutover_observation_window_passed": False,
        "security_advisor_rechecked": False,
    }, "historical client revocation gate")

    require(selection, {
        "schema_version": 1,
        "current_state": "PRODUCTION_EDGE_SELECTION_CANDIDATE_EDGE_MODE_POST_CUTOVER_PROOF_PENDING",
    }, "historical production selection snapshot")
    require(selection.get("selection_candidate", {}), {
        "active_transport": "edgeGateway",
        "edge_gateway_selected": True,
        "automatic_edge_to_direct_fallback": False,
        "direct_rpc_execute_revoked": False,
        "client_cutover_verified": False,
        "post_cutover_live_proof_completed": False,
        "post_cutover_rollback_proof_completed": False,
        "production_runtime_claimed_verified": False,
    }, "historical selection candidate")

    require(network, {
        "schema_version": 5,
        "current_state": "ORIGIN_SOURCE_SPOOF_RESISTANCE_AND_EDGE_THRESHOLD_VERIFIED",
    }, "network-origin historical authority")
    require(network.get("current_client_boundary", {}), {
        "anonymous_v2_rpc_execute_required_by_current_client": True,
        "network_origin_rate_limit_path_verified_live": True,
        "network_origin_rate_limit_for_invalid_token": True,
        "valid_student_route_verified_live": False,
        "edge_alert_delivery_verified": False,
    }, "stale network client boundary")
    if network.get("target_cutover_invariants", {}).get("alert_delivery_requires_real_runtime_receipt") is not True:
        fail("network authority lost real-runtime alert-delivery requirement")
    if "alert delivery tested against controlled signal" not in network.get("promotion_preconditions", []):
        fail("network authority lost controlled-signal alert-delivery precondition")

    if abuse.get("purpose") != (
        "Versioned authority for server-derived abuse signals on the student possession-token boundary. "
        "This authority is operational observability only and is not incident-response evidence or launch authority."
    ):
        fail("abuse authority incident-response boundary drifted")
    future_control = abuse.get("known_external_boundary", {}).get("required_future_control", "")
    if "alert delivery" not in future_control or "production deployment evidence" not in future_control:
        fail("abuse authority lost external alert-delivery requirement")

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
            fail(f"transport source metadata drift: {fragment}")

    operation_names = sorted(path.name for path in OPERATIONS.iterdir() if path.is_file())
    if operation_names != [
        "stage32_rearm_expired_fixture_r1.sql",
        "stage33_direct_rpc_regrant_recovery.sql",
        "stage33_direct_rpc_revocation_and_post_revocation_fixture_candidate.sql",
    ]:
        fail(f"operations inventory drifted: {operation_names}")
    if any("alert" in name.lower() for name in operation_names):
        fail("assessment expected no authoritative alert-delivery operation artifact yet")

    require(authority.get("verified_live_truth", {}), {
        "stage33_cleanup_state": "POST_REVOCATION_EDGE_PROOF_VERIFIED_CLEANUP_REMOTE_COMPLETE",
        "stage33_revocation_remote_version": REVOCATION_VERSION,
        "stage33_cleanup_remote_version": CLEANUP_VERSION,
        "synthetic_customer_runtime_residue": 0,
        "global_historical_network_buckets": 13,
        "global_historical_growth_events": 6,
        "security_posture": "quiet",
        "target_student_rpc_count": 5,
        "anon_execute_count": 0,
        "authenticated_execute_count": 0,
        "service_role_execute_count": 5,
        "issue_student_access_token_v2_authenticated_execute": True,
        "direct_student_route_security_definer_warnings": 0,
        "production_edge_transport_verified": True,
        "production_edge_route_count_verified": 5,
        "post_cutover_direct_rollback_proof_verified_before_revocation": True,
        "automatic_edge_to_direct_fallback": False,
        "launch_gate_promotion": False,
    }, "Stage34 verified live truth")

    require(authority.get("source_reconciliation_boundary", {}), {
        "live_remote_direct_rpc_revoked": True,
        "source_direct_rpc_execute_revoked_flag": False,
        "live_post_cutover_rollback_verified": True,
        "source_rollback_verified_flag": False,
        "live_client_cutover_verified": True,
        "source_client_cutover_verified_flag": False,
        "source_metadata_reconciliation_required": True,
        "source_metadata_mutation_allowed_in_assessment": False,
        "direct_rpc_runtime_branch_removal_authorized": False,
        "automatic_direct_rpc_regrant_authorized": False,
        "historical_guard_projection_required_before_source_flag_advance": True,
    }, "source reconciliation boundary")

    require(authority.get("alert_delivery_gap", {}), {
        "failure_class": "BGF-STAGE34-ALERT-DELIVERY-EVIDENCE-GAP-266",
        "current_verified_receipt": None,
        "self_attestation_allowed": False,
        "synthetic_database_signal_without_external_delivery_receipt_is_sufficient": False,
        "incident_response_gate_blocked": True,
        "production_deployment_gate_blocked": True,
        "paid_ads_blocked": True,
    }, "alert delivery gap")

    require(authority.get("promotion_rules", {}), {
        "may_mutate_remote_privileges": False,
        "may_regrant_direct_rpc_execute": False,
        "may_reexecute_consumed_proofs": False,
        "may_self_attest_alert_delivery": False,
        "may_promote_incident_response_gate": False,
        "may_promote_production_deployment_gate": False,
        "may_enable_paid_ads": False,
    }, "promotion rules")

    print("STAGE34_POST_REVOCATION_BOUNDARY_ASSESSMENT_GUARD=PASS")
    print(f"BASELINE_MAIN_SHA={BASELINE}")
    print("LIVE_DIRECT_ANON_EXECUTE=0")
    print("LIVE_DIRECT_AUTHENTICATED_EXECUTE=0")
    print("LIVE_EDGE_SERVICE_ROLE_EXECUTE=5")
    print("SOURCE_DIRECT_RPC_EXECUTE_REVOKED_FLAG=false")
    print("SOURCE_ROLLBACK_VERIFIED_FLAG=false")
    print("SOURCE_CLIENT_CUTOVER_VERIFIED_FLAG=false")
    print("HISTORICAL_STAGE32_AUTHORITIES_STALE=true")
    print("ALERT_DELIVERY_RUNTIME_RECEIPT=MISSING")
    print("INCIDENT_RESPONSE_GATE=DENIED")
    print("PRODUCTION_DEPLOYMENT_GATE=DENIED")
    print("PAID_MEDIA_GATE=DENIED")


if __name__ == "__main__":
    main()
