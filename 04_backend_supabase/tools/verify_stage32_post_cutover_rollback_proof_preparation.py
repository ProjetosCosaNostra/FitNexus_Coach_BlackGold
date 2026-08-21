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

STATE = "POST_CUTOVER_ROLLBACK_FIXTURE_REPO_ONLY_PROOF_PREPARATION_EDGE_MODE"
CLEANUP_STATE = "POST_CUTOVER_EDGE_RUNTIME_PROOF_R1_VERIFIED_CLEANUP_COMPLETE_ROLLBACK_PROOF_PENDING_EDGE_MODE"
FIXTURE_NAME = "stage32_post_cutover_rollback_fixture"
FIXTURE_FAILURE = "BGF-STAGE32-POST-CUTOVER-ROLLBACK-FIXTURE-240"
SEAM_FAILURE = "BGF-STAGE32-ROLLBACK-PROOF-SEAM-BYPASS-241"
REEXEC_FAILURE = "BGF-STAGE32-ROLLBACK-PROOF-REEXECUTION-242"
MUTATION_FAILURE = "BGF-STAGE32-ROLLBACK-PRODUCTION-MUTATION-243"
BASELINE = "40e01bfd9060edafd8f6b834ef5636534b834005"
OBSERVED = "2026-08-21T23:47:57.870914Z"


def fail(message: str, failure_class: str = FIXTURE_FAILURE) -> None:
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
        fail("R1 Edge proof cleanup is not at the required remote-complete frontier")
    cleanup = cleanup_authority.get("cleanup", {})
    require(
        cleanup,
        {
            "migration_ledger_state": "remote_reconciled",
            "remote_applied": True,
            "remote_version": "20260821222724",
            "cleanup_completed": True,
        },
        "R1 Edge proof cleanup",
    )

    failure_ids = set(authority.get("failure_classes", []))
    expected_failures = {FIXTURE_FAILURE, SEAM_FAILURE, REEXEC_FAILURE, MUTATION_FAILURE}
    if expected_failures - failure_ids:
        fail("rollback prevention class set is incomplete")

    require(
        authority.get("database_precondition_receipt", {}),
        {
            "source": "Supabase.execute_sql",
            "observed_at_utc": OBSERVED,
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
            "global_growth_events": 4,
            "growth_attribution": 0,
            "global_network_buckets": 13,
            "customer_domain_empty": True,
            "rpc_count": 5,
            "all_five_anon_execute_intact": True,
            "all_five_authenticated_execute_intact": True,
        },
        "database precondition receipt",
    )

    fixture_auth = authority.get("fixture", {})
    require(
        fixture_auth,
        {
            "repository_file": "04_backend_supabase/migrations/20260821235000_stage32_post_cutover_rollback_fixture.sql",
            "migration_name": FIXTURE_NAME,
            "migration_ledger_state": "repo_only",
            "remote_applied": False,
            "remote_version": None,
            "synthetic_only": True,
            "requires_empty_customer_domain": True,
            "requires_five_direct_rpc_grants_intact": True,
            "token_seed": "fitnexus-stage32-post-cutover-rollback-proof-v1",
            "raw_token_is_public_synthetic_test_material": True,
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

    repo_only = [
        row for row in ledger.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    ]
    if len(repo_only) != 1:
        fail("rollback fixture must be the unique repo_only migration")
    if repo_only[0].get("name") != FIXTURE_NAME or repo_only[0].get("related_failure_class") != FIXTURE_FAILURE:
        fail("rollback fixture repo_only divergence drifted")
    remote = {
        row.get("name"): row.get("version")
        for row in ledger.get("remote_migrations", []) if isinstance(row, dict)
    }
    if remote.get("stage32_post_cutover_live_proof_r1_cleanup") != "20260821222724":
        fail("R1 cleanup remote migration receipt disappeared")
    if FIXTURE_NAME in remote:
        fail("rollback fixture self-attested as remotely applied")
    if ledger.get("baseline_main_sha") != BASELINE or ledger.get("observed_at_utc") != OBSERVED:
        fail("rollback fixture ledger baseline/observation drifted")

    for fragment in (
        FIXTURE_FAILURE,
        "STAGE32_POST_CUTOVER_ROLLBACK_FIXTURE_REQUIRES_EMPTY_CUSTOMER_DOMAIN",
        "STAGE32_POST_CUTOVER_ROLLBACK_DIRECT_GRANTS_NOT_INTACT",
        "STAGE32_POST_CUTOVER_ROLLBACK_TOKEN_RESOLUTION_FAILED",
        "STAGE32_POST_CUTOVER_ROLLBACK_FIXTURE_POSTCONDITION_FAILED",
        "fitnexus-stage32-post-cutover-rollback-proof-v1",
        "now() + interval '4 hours'",
        "5f5166fe-e774-593b-b86d-ddb9d93e16ca",
        "b01e4654-8a8e-5634-9ee7-3635114b1346",
        "e17f6053-d6dc-543a-bce7-c06cdf432e46",
        "8409e7e1-b853-5aab-97dd-50cf8b0d40f2",
        "28a281ea-8f9e-542b-85f7-9ccd7a7ef7ee",
        "e2252055-fed6-5d3f-9410-1cccbe7d20c9",
    ):
        if fragment not in fixture:
            fail(f"rollback fixture SQL drift: {fragment}")
    fixture_lower = fixture.lower()
    if "origin_hash" in fixture_lower or "network_origin" in fixture_lower:
        fail("rollback fixture embeds a network-origin selector")
    if "delete from" in fixture_lower or "update " in fixture_lower:
        fail("rollback fixture preparation may not clean or mutate existing customer rows")

    for fragment in (
        "factory StudentAccessTransport.forAuthorizedRollbackProof",
        "configuredModeOverride: StudentAccessTransportMode.edgeGateway",
        "explicitRollbackRequestedOverride: true",
        "explicitRollbackAuthorizedOverride: true",
        "@visibleForTesting",
    ):
        if fragment not in transport:
            fail(f"authorized rollback proof seam drift: {fragment}", SEAM_FAILURE)

    # The proof-only factory is forbidden from every production Dart file except its
    # declaration in the transport boundary itself.
    for path in (APP / "lib").rglob("*.dart"):
        if path == TRANSPORT:
            continue
        if "forAuthorizedRollbackProof" in path.read_text(encoding="utf-8"):
            fail(
                f"production source references rollback proof seam: {path.relative_to(ROOT)}",
                SEAM_FAILURE,
            )

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
            fail(f"production transport contract drift: {fragment}", MUTATION_FAILURE)

    proof_surface = authority.get("rollback_proof_surface", {})
    require(
        proof_surface,
        {
            "proof_factory": "StudentAccessTransport.forAuthorizedRollbackProof",
            "proof_factory_visible_for_testing": True,
            "proof_factory_configured_mode": "edgeGateway",
            "proof_factory_explicit_rollback_requested": True,
            "proof_factory_explicit_rollback_authorized": True,
            "production_repositories_may_use_proof_factory": False,
            "direct_rpc_calls_from_focused_test_forbidden": True,
            "edge_function_calls_from_focused_test_forbidden": True,
            "all_calls_must_use_transport_invoke": True,
            "edge_payload_intentionally_empty": True,
            "route_count": 5,
        },
        "rollback proof surface",
    )
    if proof_surface.get("route_sequence") != [
        "get_workout", "start_workout", "set_completion", "get_feedback_context", "submit_feedback"
    ]:
        fail("rollback route sequence drifted", SEAM_FAILURE)
    if proof_surface.get("command_ids") != [
        "33000000000000000000000000000001",
        "33000000000000000000000000000002",
        "33000000000000000000000000000003",
    ]:
        fail("rollback command IDs drifted", SEAM_FAILURE)

    for fragment in (
        "STAGE32_POST_CUTOVER_ROLLBACK_PROOF_ENABLED",
        "StudentAccessTransport.forAuthorizedRollbackProof",
        "const emptyEdgePayload = <String, dynamic>{};",
        "resolveStudentAccessTransportMode(",
        "explicitRollbackRequested: true",
        "explicitRollbackAuthorized: true",
        "33000000000000000000000000000001",
        "33000000000000000000000000000002",
        "33000000000000000000000000000003",
        "SharedPreferences.setMockInitialValues(<String, Object>{});",
        "HttpOverrides.global = null;",
    ):
        if fragment not in test:
            fail(f"focused rollback proof test drift: {fragment}", SEAM_FAILURE)
    if ".rpc(" in test or ".functions.invoke(" in test:
        fail("focused rollback proof bypasses StudentAccessTransport", SEAM_FAILURE)
    if "StudentAccessTransport.instance.invoke" in test:
        fail("rollback proof incorrectly uses production singleton as rollback object", SEAM_FAILURE)

    runtime = authority.get("runtime_proof", {})
    require(
        runtime,
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
        "rollback runtime proof",
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

    rules = authority.get("promotion_rules", {})
    for key in (
        "may_apply_fixture_before_ci_and_merge",
        "may_execute_rollback_proof_before_fixture_remote_apply",
        "may_use_production_singleton_as_rollback_object",
        "may_mutate_production_rollback_constants_during_proof",
        "may_enable_automatic_edge_to_direct_fallback",
        "may_call_rpc_directly_from_focused_test",
        "may_call_edge_directly_from_focused_test",
        "may_use_real_customer_data",
        "may_reexecute_stage32_edge_live_proof",
        "may_revoke_direct_rpc_execute_before_rollback_proof_cleanup",
        "may_promote_launch_gates",
    ):
        if rules.get(key) is not False:
            fail(f"rollback authority gained prohibited permission: {key}")

    print("STAGE32_POST_CUTOVER_ROLLBACK_PROOF_PREPARATION_GUARD=PASS")
    print(f"CURRENT_STATE={STATE}")
    print(f"FIXTURE_MIGRATION={FIXTURE_NAME}")
    print("FIXTURE_LEDGER=REPO_ONLY")
    print("FIXTURE_REMOTE_APPLIED=false")
    print("PRODUCTION_ACTIVE_TRANSPORT=edgeGateway")
    print("PRODUCTION_SINGLETON=StudentAccessTransport.instance")
    print("AUTHORIZED_ROLLBACK_PROOF_SEAM=true")
    print("ROLLBACK_PROOF_EXECUTED=false")
    print("DIRECT_RPC_GRANTS=INTACT")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
