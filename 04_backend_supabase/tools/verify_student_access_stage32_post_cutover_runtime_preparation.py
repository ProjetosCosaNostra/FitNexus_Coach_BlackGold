from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
APP = ROOT / "03_app_flutter" / "fitnexus_app"
STUDENT = APP / "lib" / "features" / "student"

AUTHORITY = BACKEND / "student_access_stage32_post_cutover_runtime_proof_authority.json"
SELECTION = BACKEND / "student_access_production_edge_selection_authority.json"
CUTOVER = BACKEND / "student_access_client_cutover_authority.json"
STAGE31 = BACKEND / "student_access_client_edge_runtime_proof_authority.json"
LEDGER = BACKEND / "migration_ledger_authority.json"
FIXTURE_SQL = BACKEND / "migrations" / "20260821170400_stage32_post_cutover_edge_runtime_fixture.sql"
CONTRACT = STUDENT / "student_access_transport_contract.dart"
TRANSPORT = STUDENT / "student_access_transport.dart"
WORKOUT = STUDENT / "student_workout_repository.dart"
FEEDBACK = STUDENT / "student_feedback_repository.dart"
LIVE_TEST = APP / "test" / "student_access_stage32_post_cutover_live_edge_proof_test.dart"

STATE = "POST_CUTOVER_EDGE_RUNTIME_PROOF_FIXTURE_REPO_ONLY_EDGE_MODE"
BASELINE = "8c6bb194cbe6550c91d26dda17bd645f037a5a25"
SELECTION_STATE = "PRODUCTION_EDGE_SELECTION_CANDIDATE_EDGE_MODE_POST_CUTOVER_PROOF_PENDING"
CUTOVER_STATE = "CLIENT_EDGE_SELECTED_POST_CUTOVER_PROOF_PENDING"
STAGE31_STATE = "CLIENT_EDGE_RUNTIME_PROOF_LIVE_VERIFIED_CLEANUP_COMPLETE_DIRECT_MODE"
FIXTURE_NAME = "stage32_post_cutover_edge_runtime_fixture"
FIXTURE_FILE = "04_backend_supabase/migrations/20260821170400_stage32_post_cutover_edge_runtime_fixture.sql"
SEED = "fitnexus-stage32-post-cutover-edge-runtime-proof-v1"
FAILURE_CLASSES = [
    "BGF-STAGE32-POST-CUTOVER-RUNTIME-FIXTURE-231",
    "BGF-STAGE32-POST-CUTOVER-PROOF-PREMATURE-232",
    "BGF-STAGE32-POST-CUTOVER-PROOF-REEXECUTION-233",
    "BGF-STAGE32-PRODUCTION-SINGLETON-BYPASS-234",
]
ROUTES = [
    "get_workout",
    "start_workout",
    "set_completion",
    "get_feedback_context",
    "submit_feedback",
]
RPC_MAP = {
    "get_workout": "get_student_workout_v2",
    "start_workout": "start_student_workout_v2",
    "set_completion": "set_student_exercise_completion_v2",
    "get_feedback_context": "get_student_feedback_context_v2",
    "submit_feedback": "submit_student_workout_feedback_v2",
}
EXPECTED_IDS = {
    "user_id": "728ea3d2-335f-5936-b78b-0289f9e732b8",
    "organization_id": "51143353-1492-54a9-b5f8-1ad99cf4c6f3",
    "student_id": "bdbe631a-4c44-53fc-a0da-38310bbdf90e",
    "plan_id": "a1c29966-b4c1-59fc-bb9e-ac0b055ea577",
    "exercise_id": "585b0618-8141-513c-a37e-02cb5ccd93f1",
    "link_id": "378baa18-c8fc-5765-b01f-6fd3dd898f64",
}


def fail(message: str) -> None:
    raise SystemExit(
        "STUDENT_ACCESS_STAGE32_POST_CUTOVER_RUNTIME_PREPARATION_GUARD=FAIL\n"
        + message
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
    selection = load(SELECTION)
    cutover = load(CUTOVER)
    stage31 = load(STAGE31)
    ledger = load(LEDGER)
    fixture_sql = text(FIXTURE_SQL)
    contract = text(CONTRACT)
    transport = text(TRANSPORT)
    workout = text(WORKOUT)
    feedback = text(FEEDBACK)
    live_test = text(LIVE_TEST)

    require(
        authority,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "stage": "STAGE32_POST_CUTOVER_EDGE_RUNTIME_PROOF",
            "current_state": STATE,
            "baseline_main_sha": BASELINE,
            "failure_classes": FAILURE_CLASSES,
        },
        "Stage 32 post-cutover authority",
    )

    prerequisites = authority.get("prerequisites", {})
    require(
        prerequisites,
        {
            "selection_authority_file": "04_backend_supabase/student_access_production_edge_selection_authority.json",
            "selection_required_state": SELECTION_STATE,
            "cutover_authority_file": "04_backend_supabase/student_access_client_cutover_authority.json",
            "cutover_required_state": CUTOVER_STATE,
            "stage31_authority_file": "04_backend_supabase/student_access_client_edge_runtime_proof_authority.json",
            "stage31_required_state": STAGE31_STATE,
            "stage31_cleanup_complete": True,
            "stage31_proof_reexecution_allowed": False,
            "edge_runtime_version": 3,
            "production_active_transport": "edgeGateway",
            "production_edge_gateway_selected": True,
            "automatic_edge_to_direct_fallback": False,
            "direct_rpc_grants_required_intact": True,
            "post_cutover_live_proof_required": True,
            "post_cutover_rollback_proof_required_after_live_proof": True,
        },
        "Stage 32 prerequisites",
    )

    if selection.get("current_state") != SELECTION_STATE:
        fail("production Edge selection authority is not at the post-cutover proof frontier")
    if cutover.get("current_state") != CUTOVER_STATE:
        fail("client cutover authority is not Edge-selected")
    if stage31.get("current_state") != STAGE31_STATE:
        fail("sealed Stage 31 proof/cleanup prerequisite disappeared")
    stage31_runtime = stage31.get("runtime_proof", {})
    require(
        stage31_runtime,
        {
            "result": "PASS",
            "all_five_routes_verified": True,
            "proof_reexecution_allowed": False,
            "cleanup_completed": True,
            "synthetic_business_rows_remaining": 0,
            "synthetic_security_rows_remaining": 0,
            "synthetic_network_proof_rows_remaining": 0,
        },
        "Stage 31 sealed proof receipt",
    )

    production = authority.get("production_boundary", {})
    require(
        production,
        {
            "active_transport": "edgeGateway",
            "resolved_transport": "edgeGateway",
            "edge_gateway_selected": True,
            "flutter_uses_edge_gateway_in_production": True,
            "production_singleton": "StudentAccessTransport.instance",
            "direct_v2_rpc_path_active_for_controlled_rollback": True,
            "direct_anon_v2_rpc_execute_revoked": False,
            "explicit_rollback_requested": False,
            "explicit_rollback_authorized": False,
            "automatic_edge_to_direct_fallback": False,
            "client_cutover_verified": False,
            "post_cutover_rollback_verified": False,
        },
        "post-cutover production boundary",
    )

    cutover_transport = cutover.get("transport_contract", {})
    require(
        cutover_transport,
        {
            "active_mode": "edgeGateway",
            "resolved_mode": "edgeGateway",
            "edge_gateway_selected": True,
            "automatic_edge_to_direct_fallback": False,
            "explicit_rollback_requested": False,
            "explicit_rollback_authorized": False,
            "direct_rpc_execute_revoked": False,
            "rollback_verified": False,
            "client_cutover_verified": False,
            "exact_route_count": 5,
            "edge_path_active_in_repository_source": True,
            "behavioral_transport_change": True,
        },
        "cutover transport",
    )
    inventory = cutover.get("current_client_inventory", {})
    require(
        inventory,
        {
            "transport_mode": "edge_gateway",
            "flutter_uses_edge_gateway": True,
            "direct_v2_rpc_path_active": True,
            "direct_anon_v2_rpc_execute_revoked": False,
            "repositories_call_supabase_rpc_directly": False,
            "repositories_call_single_transport": True,
        },
        "cutover client inventory",
    )

    pre = authority.get("database_precondition_receipt", {})
    require(
        pre,
        {
            "source": "Supabase.execute_sql",
            "observed_at_utc": "2026-08-21T17:07:13.992654Z",
            "auth_users": 0,
            "profiles": 0,
            "organizations": 0,
            "organization_members": 0,
            "organization_subscriptions": 0,
            "students": 0,
            "training_plans": 0,
            "training_exercises": 0,
            "access_links": 0,
            "workout_sessions": 0,
            "workout_logs": 0,
            "workout_feedback": 0,
            "command_receipts": 0,
            "security_events": 0,
            "security_signals": 0,
            "customer_domain_empty": True,
        },
        "fresh empty-domain receipt",
    )

    grants = authority.get("direct_rpc_grant_receipt", {})
    for rpc in RPC_MAP.values():
        if grants.get(rpc) is not True:
            fail(f"BGF-STAGE32-DIRECT-RPC-REVOCATION-PREMATURE-229 direct RPC grant missing: {rpc}")
    require(
        grants,
        {
            "source": "Supabase.execute_sql",
            "observed_after_selection_merge": True,
            "all_five_anon_execute_intact": True,
            "all_five_authenticated_execute_intact": True,
            "grants_changed_during_preparation": False,
        },
        "direct RPC grant receipt",
    )

    fixture = authority.get("fixture", {})
    require(
        fixture,
        {
            "repository_file": FIXTURE_FILE,
            "migration_name": FIXTURE_NAME,
            "migration_ledger_state": "repo_only",
            "remote_applied": False,
            "remote_version": None,
            "requires_empty_customer_domain": True,
            "synthetic_only": True,
            "token_seed": SEED,
            "raw_token_is_public_synthetic_test_material": True,
            "database_stores_token_hash_only": True,
            "repository_contains_bearer_literal": False,
            "raw_network_origin_embedded": False,
            "network_origin_digest_embedded": False,
            "expiry_hours": 2,
            "cleanup_required_after_proof": True,
        },
        "Stage 32 fixture",
    )
    for key, expected in EXPECTED_IDS.items():
        if fixture.get(key) != expected:
            fail(f"Stage 32 fixture identifier drift: {key}")

    remote = {
        row.get("name"): row.get("version")
        for row in ledger.get("remote_migrations", [])
        if isinstance(row, dict)
    }
    if remote.get("stage31_client_edge_runtime_cleanup") != "20260821161224":
        fail("sealed Stage 31 cleanup remote receipt disappeared")
    if FIXTURE_NAME in remote:
        fail(f"{FAILURE_CLASSES[1]} Stage 32 fixture self-attested as remotely applied")
    repo_only = [
        row
        for row in ledger.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    ]
    if len(repo_only) != 1 or repo_only[0].get("name") != FIXTURE_NAME:
        fail("Stage 32 fixture must be the unique repo_only migration divergence")
    if repo_only[0].get("related_failure_class") != FAILURE_CLASSES[0]:
        fail("Stage 32 repo_only divergence failure-class authority drifted")

    required_fixture = (
        FAILURE_CLASSES[0],
        "STAGE32_POST_CUTOVER_FIXTURE_REQUIRES_EMPTY_CUSTOMER_DOMAIN",
        "STAGE32_SYNTHETIC_TRIAL_INITIALIZATION_FAILED",
        "STAGE32_SYNTHETIC_TOKEN_RESOLUTION_FAILED",
        "STAGE32_POST_CUTOVER_FIXTURE_POSTCONDITION_FAILED",
        SEED,
        "extensions.digest(v_token, 'sha256')",
        "now() + interval '2 hours'",
        "Stage32 Synthetic Organization",
        "Stage32 Synthetic Student",
        "Stage32 Synthetic Plan",
        "Stage32 Synthetic Exercise",
    )
    for fragment in required_fixture:
        if fragment not in fixture_sql:
            fail(f"Stage 32 fixture SQL drift: {fragment}")
    if re.findall(r"(?<![0-9a-fA-F])[0-9a-fA-F]{64}(?![0-9a-fA-F])", fixture_sql):
        fail("Stage 32 fixture contains a bearer-looking 64-hex literal")
    fixture_lower = fixture_sql.lower()
    for forbidden in ("origin_hash", "cf-connecting-ip", "x-forwarded-for", "x-real-ip"):
        if forbidden in fixture_lower:
            fail(f"Stage 32 fixture contains forbidden network-origin material: {forbidden}")

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
            fail(f"production Edge contract drifted: {fragment}")
    for action, rpc in RPC_MAP.items():
        if contract.count(f"'{action}': '{rpc}'") != 1:
            fail(f"five-route rollback map drifted: {action}")

    repositories = workout + "\n" + feedback
    if repositories.count("StudentAccessTransport.instance.invoke(") != 5:
        fail("all five repositories must remain on the single production transport")
    if ".rpc(" in repositories or ".functions.invoke(" in repositories:
        fail("repository bypassed the single production transport")
    for action in ROUTES:
        if repositories.count(f"action: '{action}'") != 1:
            fail(f"repository route drifted: {action}")

    for fragment in (
        "return _client.rpc(directRpc, params: directParams);",
        "return _invokeEdge(action: action, payload: edgePayload);",
        "_client.functions.invoke(",
        "StudentAccessTransportContract.edgeFunctionName",
        "normalizeStudentEdgeFunctionException(",
    ):
        if fragment not in transport:
            fail(f"single transport runtime drifted: {fragment}")

    expected = authority.get("expected_live_proof", {})
    if expected.get("route_sequence") != ROUTES or expected.get("route_count") != 5:
        fail("Stage 32 live proof route sequence drifted")
    for key in (
        "must_use_flutter_student_access_transport",
        "must_use_production_singleton",
        "verification_factory_forbidden",
        "must_observe_production_edge_gateway_mode",
        "direct_rpc_call_from_proof_forbidden",
        "raw_token_return_forbidden",
        "raw_network_origin_return_forbidden",
        "real_customer_data_forbidden",
        "real_customer_mutation_forbidden",
        "direct_rpc_grant_change_forbidden",
        "workflow_must_be_one_shot",
        "workflow_must_be_sealed_to_exact_pr_and_head_before_first_execution",
        "cleanup_required_after_proof",
    ):
        if expected.get(key) is not True:
            fail(f"Stage 32 live-proof invariant missing: {key}")

    required_test = (
        "STAGE32_POST_CUTOVER_LIVE_PROOF_ENABLED",
        "StudentAccessTransportMode.edgeGateway",
        "StudentAccessTransportContract.edgeGatewaySelected, isTrue",
        "StudentAccessTransportContract.automaticEdgeToDirectFallback",
        "StudentAccessTransportContract.directRpcExecuteRevoked, isFalse",
        "StudentAccessTransportContract.rollbackVerified, isFalse",
        "StudentAccessTransportContract.clientCutoverVerified, isFalse",
        "await Supabase.initialize(",
        "final transport = StudentAccessTransport.instance;",
        "32000000000000000000000000000001",
        "32000000000000000000000000000002",
        "32000000000000000000000000000003",
    )
    for fragment in required_test:
        if fragment not in live_test:
            fail(f"Stage 32 focused live proof source drifted: {fragment}")
    if "StudentAccessTransport.forVerification" in live_test or ".forVerification(" in live_test:
        fail(f"{FAILURE_CLASSES[3]} post-cutover proof must use the production singleton")
    if ".rpc(" in live_test or ".functions.invoke(" in live_test:
        fail(f"{FAILURE_CLASSES[3]} post-cutover proof bypassed StudentAccessTransport.instance")
    for action in ROUTES:
        if live_test.count(f"action: '{action}'") != 1:
            fail(f"Stage 32 focused proof route drifted: {action}")

    proof = authority.get("runtime_proof", {})
    if proof.get("workflow_run_id") is not None or proof.get("workflow_job_id") is not None or proof.get("result") is not None:
        fail(f"{FAILURE_CLASSES[1]} runtime proof receipt appeared before fixture apply")
    for key in (
        "production_singleton_verified",
        "production_edge_mode_verified",
        "get_workout_verified",
        "start_workout_verified",
        "set_completion_verified",
        "get_feedback_context_verified",
        "submit_feedback_verified",
        "all_five_routes_verified",
        "synthetic_fixture_mutated_as_expected",
        "raw_token_returned",
        "raw_network_origin_returned",
        "real_customer_data_used",
        "real_customer_data_mutated",
        "direct_rpc_grants_changed",
        "proof_reexecution_allowed",
        "cleanup_completed",
    ):
        if proof.get(key) is not False:
            fail(f"{FAILURE_CLASSES[1]} runtime proof self-attested during preparation: {key}")

    rules = authority.get("promotion_rules", {})
    for key in (
        "may_apply_fixture_before_ci_and_merge",
        "may_execute_live_proof_before_fixture_remote_apply",
        "may_reexecute_stage31_live_proof",
        "may_reexecute_stage32_post_cutover_live_proof",
        "may_use_verification_factory_for_post_cutover_proof",
        "may_switch_production_back_to_direct_during_live_proof",
        "may_enable_automatic_edge_to_direct_fallback",
        "may_revoke_direct_rpc_execute_before_post_cutover_live_and_rollback_proofs",
        "may_use_real_customer_data",
        "may_promote_launch_gates",
    ):
        if rules.get(key) is not False:
            fail(f"Stage 32 preparation gained prohibited promotion authority: {key}")
    if rules.get("cleanup_required_before_post_cutover_rollback_proof") is not True:
        fail("Stage 32 cleanup-before-rollback interlock disappeared")

    require(
        authority.get("next_stage", {}),
        {
            "name": "APPLY_STAGE32_POST_CUTOVER_EDGE_RUNTIME_FIXTURE",
            "allowed_now": True,
            "requires_ci_and_merge_first": True,
            "requires_exact_merged_sql": True,
            "requires_fresh_empty_customer_domain_check_immediately_before_apply": True,
            "requires_fresh_migration_ledger_check_immediately_before_apply": True,
            "requires_direct_rpc_grants_intact": True,
            "may_execute_live_proof_now": False,
            "may_revoke_direct_rpc_execute_now": False,
        },
        "Stage 32 next stage",
    )
    if any(value is not False for value in authority.get("launch_authority", {}).values()):
        fail("Stage 32 post-cutover preparation gained launch authority")

    print("STUDENT_ACCESS_STAGE32_POST_CUTOVER_RUNTIME_PREPARATION_GUARD=PASS")
    print(f"CURRENT_STATE={STATE}")
    print(f"BASELINE_MAIN_SHA={BASELINE}")
    print("PRODUCTION_ACTIVE_TRANSPORT=edgeGateway")
    print("PRODUCTION_SINGLETON=StudentAccessTransport.instance")
    print("ATOMIC_ROUTE_COUNT=5")
    print("STAGE31_PROOF_REEXECUTION_ALLOWED=false")
    print("STAGE32_FIXTURE_LEDGER=REPO_ONLY")
    print("CUSTOMER_DOMAIN_PRECONDITION=EMPTY")
    print("DIRECT_RPC_GRANTS=INTACT")
    print("LIVE_POST_CUTOVER_PROOF=NOT_EXECUTED")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")
    print("NEXT=APPLY_STAGE32_POST_CUTOVER_EDGE_RUNTIME_FIXTURE_AFTER_CI_AND_MERGE")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
