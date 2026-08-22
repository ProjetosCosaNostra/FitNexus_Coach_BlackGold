from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
APP = ROOT / "03_app_flutter" / "fitnexus_app"
AUTHORITY = BACKEND / "stage32_post_cutover_rollback_proof_authority.json"
CLEANUP_AUTHORITY = BACKEND / "stage32_post_cutover_live_proof_r1_cleanup_authority.json"
LEDGER = BACKEND / "migration_ledger_authority.json"
FIXTURE = BACKEND / "migrations" / "20260821235000_stage32_post_cutover_rollback_fixture.sql"
TRANSPORT = APP / "lib" / "features" / "student" / "student_access_transport.dart"
CONTRACT = APP / "lib" / "features" / "student" / "student_access_transport_contract.dart"
TEST = APP / "test" / "student_access_stage32_post_cutover_live_rollback_proof_test.dart"

STATE = "POST_CUTOVER_ROLLBACK_FIXTURE_REMOTE_LIVE_PROOF_PENDING_EDGE_MODE"
CLEANUP_STATE = "POST_CUTOVER_EDGE_RUNTIME_PROOF_R1_VERIFIED_CLEANUP_COMPLETE_ROLLBACK_PROOF_PENDING_EDGE_MODE"
FIXTURE_NAME = "stage32_post_cutover_rollback_fixture"
FIXTURE_VERSION = "20260821235550"
FIXTURE_FILE_SHA = "ead2d358f017b5c5704fe525c942af4b2da5f758"
FAIL_FIXTURE = "BGF-STAGE32-POST-CUTOVER-ROLLBACK-FIXTURE-240"
FAIL_SEAM = "BGF-STAGE32-ROLLBACK-PROOF-SEAM-BYPASS-241"
FAIL_REEXEC = "BGF-STAGE32-ROLLBACK-PROOF-REEXECUTION-242"
FAIL_MUTATION = "BGF-STAGE32-ROLLBACK-PRODUCTION-MUTATION-243"
BASELINE = "4e686d526779cce4236b6e1b4fba42c4ba6ef3c7"
OBSERVED = "2026-08-21T23:56:22.809328Z"


def fail(message: str, failure_class: str = FAIL_FIXTURE) -> None:
    raise SystemExit(
        "STAGE32_POST_CUTOVER_ROLLBACK_PROOF_PREPARATION_GUARD=FAIL\n"
        f"FAILURE_CLASS={failure_class}\nDETAIL={message}"
    )


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to read {path.relative_to(ROOT)}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"expected JSON object: {path.relative_to(ROOT)}")
    return value


def text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"unable to read {path.relative_to(ROOT)}: {type(exc).__name__}")
    raise AssertionError("unreachable")


def require(mapping: dict, expected: dict, label: str) -> None:
    for key, value in expected.items():
        if mapping.get(key) != value:
            fail(f"{label} drift: {key}")


def main() -> None:
    authority = load(AUTHORITY)
    cleanup_authority = load(CLEANUP_AUTHORITY)
    ledger = load(LEDGER)
    fixture = text(FIXTURE)
    transport = text(TRANSPORT)
    contract = text(CONTRACT)
    test = text(TEST)

    require(
        authority,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "stage": "STAGE32_POST_CUTOVER_ROLLBACK_PROOF",
            "baseline_main_sha": BASELINE,
            "current_state": STATE,
        },
        "rollback authority",
    )
    if cleanup_authority.get("current_state") != CLEANUP_STATE:
        fail("R1 Edge proof cleanup is not remote-complete")
    require(
        cleanup_authority.get("cleanup", {}),
        {
            "migration_ledger_state": "remote_reconciled",
            "remote_applied": True,
            "remote_version": "20260821222724",
            "cleanup_completed": True,
        },
        "R1 Edge cleanup",
    )

    if set(authority.get("failure_classes", [])) != {
        FAIL_FIXTURE, FAIL_SEAM, FAIL_REEXEC, FAIL_MUTATION
    }:
        fail("rollback failure class set drifted")

    require(
        authority.get("pre_apply_receipt", {}),
        {
            "source": "Supabase.execute_sql+Supabase.list_migrations",
            "observed_at_utc": "2026-08-21T23:55:20.31244Z",
            "source_main_sha": BASELINE,
            "remote_fixture_present_before_apply": False,
            "auth_users": 0,
            "profiles": 0,
            "organizations": 0,
            "organization_members": 0,
            "organization_subscriptions": 0,
            "subscription_authority_events": 0,
            "students": 0,
            "training_plans": 0,
            "training_exercises": 0,
            "access_links": 0,
            "workout_sessions": 0,
            "workout_logs": 0,
            "workout_feedback": 0,
            "command_receipts": 0,
            "link_rate_buckets": 0,
            "security_events": 0,
            "security_signals": 0,
            "customer_domain_empty": True,
            "rpc_count": 5,
            "all_five_anon_execute_intact": True,
            "all_five_authenticated_execute_intact": True,
        },
        "pre-apply receipt",
    )

    fixture_auth = authority.get("fixture", {})
    require(
        fixture_auth,
        {
            "repository_file": "04_backend_supabase/migrations/20260821235000_stage32_post_cutover_rollback_fixture.sql",
            "repository_file_sha": FIXTURE_FILE_SHA,
            "migration_name": FIXTURE_NAME,
            "migration_ledger_state": "remote_reconciled",
            "remote_applied": True,
            "remote_version": FIXTURE_VERSION,
            "synthetic_only": True,
            "requires_empty_customer_domain": True,
            "requires_five_direct_rpc_grants_intact": True,
            "token_seed": "fitnexus-stage32-post-cutover-rollback-proof-v1",
            "database_stores_token_hash_only": True,
            "repository_contains_bearer_literal": False,
            "raw_network_origin_embedded": False,
            "network_origin_digest_embedded": False,
            "expiry_hours": 4,
            "user_id": "5f5166fe-e774-593b-b86d-ddb9d93e16ca",
            "organization_id": "b01e4654-8a8e-5634-9ee7-3635114b1346",
            "student_id": "e17f6053-d6dc-543a-bce7-c06cdf432e46",
            "plan_id": "8409e7e1-b853-5aab-97dd-50cf8b0d40f2",
            "exercise_id": "28a281ea-8f9e-542b-85f7-9ccd7a7ef7ee",
            "link_id": "e2252055-fed6-5d3f-9410-1cccbe7d20c9",
            "cleanup_required_after_proof": True,
        },
        "rollback fixture authority",
    )

    receipt = authority.get("remote_apply_receipt", {})
    require(
        receipt,
        {
            "source": "Supabase.apply_migration",
            "source_main_sha": BASELINE,
            "source_file": "04_backend_supabase/migrations/20260821235000_stage32_post_cutover_rollback_fixture.sql",
            "source_file_sha": FIXTURE_FILE_SHA,
            "migration_name": FIXTURE_NAME,
            "remote_version": FIXTURE_VERSION,
            "pre_apply_observed_at_utc": "2026-08-21T23:55:20.31244Z",
            "apply_result": "SUCCESS",
            "post_apply_observed_at_utc": OBSERVED,
            "auth_users": 1,
            "profiles": 1,
            "organizations": 1,
            "organization_members": 1,
            "organization_subscriptions": 1,
            "subscription_authority_events": 1,
            "students": 1,
            "training_plans": 1,
            "training_exercises": 1,
            "access_links": 1,
            "workout_sessions": 0,
            "workout_logs": 0,
            "workout_feedback": 0,
            "expected_user": 1,
            "expected_profile": 1,
            "expected_org": 1,
            "expected_member": 1,
            "expected_subscription": 1,
            "expected_student": 1,
            "expected_plan": 1,
            "expected_exercise": 1,
            "expected_active_link": 1,
            "fixture_command_receipts": 0,
            "fixture_rate_buckets": 0,
            "fixture_security_events": 0,
            "fixture_security_signals": 0,
            "fixture_growth_events": 4,
            "fixture_growth_attribution": 0,
            "global_network_buckets": 13,
            "rpc_count": 5,
            "all_five_anon_execute_intact": True,
            "all_five_authenticated_execute_intact": True,
            "direct_rpc_grants_changed": False,
            "real_customer_data_used": False,
        },
        "remote apply receipt",
    )
    ttl = receipt.get("ttl_minutes_remaining_at_receipt")
    if not isinstance(ttl, (int, float)) or ttl < 230:
        fail("rollback fixture remote receipt TTL is unexpectedly short")

    repo_only = [
        row for row in ledger.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    ]
    if repo_only:
        fail("rollback fixture remains repo_only after remote apply")
    remote = {
        row.get("name"): row.get("version")
        for row in ledger.get("remote_migrations", []) if isinstance(row, dict)
    }
    if remote.get("stage32_post_cutover_live_proof_r1_cleanup") != "20260821222724":
        fail("R1 cleanup remote receipt disappeared")
    if remote.get(FIXTURE_NAME) != FIXTURE_VERSION:
        fail("rollback fixture remote migration receipt drifted")
    if ledger.get("baseline_main_sha") != BASELINE or ledger.get("observed_at_utc") != OBSERVED:
        fail("rollback fixture remote ledger baseline/observation drifted")

    for fragment in (
        FAIL_FIXTURE,
        "STAGE32_POST_CUTOVER_ROLLBACK_FIXTURE_REQUIRES_EMPTY_CUSTOMER_DOMAIN",
        "STAGE32_POST_CUTOVER_ROLLBACK_DIRECT_GRANTS_NOT_INTACT",
        "STAGE32_POST_CUTOVER_ROLLBACK_TOKEN_RESOLUTION_FAILED",
        "STAGE32_POST_CUTOVER_ROLLBACK_FIXTURE_POSTCONDITION_FAILED",
        "fitnexus-stage32-post-cutover-rollback-proof-v1",
        "now() + interval '4 hours'",
    ):
        if fragment not in fixture:
            fail(f"rollback fixture SQL drift: {fragment}")
    lower_fixture = fixture.lower()
    if "origin_hash" in lower_fixture or "network_origin" in lower_fixture:
        fail("rollback fixture embeds network-origin material")
    if "delete from" in lower_fixture or "update " in lower_fixture:
        fail("rollback fixture contains forbidden cleanup/update DML")

    for fragment in (
        "factory StudentAccessTransport.forAuthorizedRollbackProof",
        "configuredModeOverride: StudentAccessTransportMode.edgeGateway",
        "explicitRollbackRequestedOverride: true",
        "explicitRollbackAuthorizedOverride: true",
        "@visibleForTesting",
    ):
        if fragment not in transport:
            fail(f"rollback proof seam drift: {fragment}", FAIL_SEAM)
    for path in (APP / "lib").rglob("*.dart"):
        if path == TRANSPORT:
            continue
        if "forAuthorizedRollbackProof" in path.read_text(encoding="utf-8"):
            fail(f"production source references proof-only rollback seam: {path.relative_to(ROOT)}", FAIL_SEAM)

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
            fail(f"production transport contract drift: {fragment}", FAIL_MUTATION)

    for fragment in (
        "STAGE32_POST_CUTOVER_ROLLBACK_PROOF_ENABLED",
        "StudentAccessTransport.forAuthorizedRollbackProof",
        "const emptyEdgePayload = <String, dynamic>{};",
        "explicitRollbackRequested: true",
        "explicitRollbackAuthorized: true",
        "33000000000000000000000000000001",
        "33000000000000000000000000000002",
        "33000000000000000000000000000003",
        "SharedPreferences.setMockInitialValues(<String, Object>{});",
        "HttpOverrides.global = null;",
    ):
        if fragment not in test:
            fail(f"focused rollback test drift: {fragment}", FAIL_SEAM)
    if ".rpc(" in test or ".functions.invoke(" in test:
        fail("focused rollback test bypasses transport seam", FAIL_SEAM)

    require(
        authority.get("runtime_proof", {}),
        {
            "workflow_run_id": None,
            "workflow_job_id": None,
            "result": None,
            "proof_head_sha": None,
            "authorized_rollback_object_verified": False,
            "direct_rpc_branch_verified": False,
            "get_workout_verified": False,
            "start_workout_verified": False,
            "set_completion_verified": False,
            "get_feedback_context_verified": False,
            "submit_feedback_verified": False,
            "all_five_routes_verified": False,
            "production_edge_mode_preserved": False,
            "automatic_fallback_remained_false": False,
            "direct_rpc_grants_changed": False,
            "real_customer_data_used": False,
            "cleanup_completed": False,
            "proof_reexecution_allowed": False,
        },
        "runtime proof",
    )
    require(
        authority.get("production_boundary", {}),
        {
            "active_transport": "edgeGateway",
            "resolved_transport": "edgeGateway",
            "production_singleton": "StudentAccessTransport.instance",
            "edge_gateway_selected": True,
            "automatic_edge_to_direct_fallback": False,
            "explicit_rollback_requested": False,
            "explicit_rollback_authorized": False,
            "direct_rpc_execute_revoked": False,
            "post_cutover_live_proof_verified": True,
            "post_cutover_cleanup_verified": True,
            "post_cutover_rollback_verified": False,
            "production_transport_change_allowed_during_proof": False,
            "launch_gate_promotion": False,
        },
        "production boundary",
    )

    next_stage = authority.get("next_stage", {})
    require(
        next_stage,
        {
            "name": "PREPARE_SEALED_POST_CUTOVER_ROLLBACK_LIVE_PROOF_CANDIDATE",
            "allowed_now": True,
            "requires_fixture_remote_reconciled": True,
            "requires_fresh_fixture_ttl_check_immediately_before_event_delivery": True,
            "requires_fresh_direct_rpc_grant_check_immediately_before_event_delivery": True,
            "requires_zero_runtime_mutation_residue_before_event_delivery": True,
            "requires_new_exact_proof_head": True,
            "requires_new_one_shot_workflow_seal": True,
            "requires_new_trigger_head": True,
            "may_execute_live_rollback_proof_before_workflow_seal": False,
            "may_reapply_fixture": False,
            "may_revoke_direct_rpc_execute_now": False,
            "may_promote_launch_gates": False,
        },
        "next stage",
    )

    print("STAGE32_POST_CUTOVER_ROLLBACK_PROOF_PREPARATION_GUARD=PASS")
    print(f"CURRENT_STATE={STATE}")
    print(f"FIXTURE_REMOTE_VERSION={FIXTURE_VERSION}")
    print("FIXTURE_REMOTE_APPLIED=true")
    print("ROLLBACK_PROOF_EXECUTED=false")
    print("PRODUCTION_ACTIVE_TRANSPORT=edgeGateway")
    print("AUTHORIZED_ROLLBACK_PROOF_SEAM=true")
    print("DIRECT_RPC_GRANTS=INTACT")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
