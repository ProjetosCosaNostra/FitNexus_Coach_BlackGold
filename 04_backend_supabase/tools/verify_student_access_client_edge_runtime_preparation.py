from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
APP_ROOT = ROOT / "03_app_flutter" / "fitnexus_app"
STUDENT_LIB = APP_ROOT / "lib" / "features" / "student"

AUTHORITY = BACKEND / "student_access_client_edge_runtime_proof_authority.json"
CUTOVER = BACKEND / "student_access_client_cutover_authority.json"
ROLLBACK = BACKEND / "student_access_runtime_rollback_authority.json"
SMOKE = BACKEND / "student_access_client_runtime_smoke_authority.json"
LEDGER = BACKEND / "migration_ledger_authority.json"
FIXTURE_SQL = BACKEND / "migrations" / "20260821104600_stage31_client_edge_runtime_fixture.sql"
TRANSPORT = STUDENT_LIB / "student_access_transport.dart"
CONTRACT = STUDENT_LIB / "student_access_transport_contract.dart"

FAILURE_CLASSES = [
    "BGF-STAGE31-CLIENT-EDGE-RUNTIME-FIXTURE-216",
    "BGF-STAGE31-VERIFICATION-SEAM-PRODUCTION-LEAK-217",
    "BGF-STAGE31-CLIENT-EDGE-RUNTIME-PROOF-PREMATURE-218",
    "BGF-STAGE31-CLIENT-EDGE-RUNTIME-PROOF-REEXECUTION-219",
]
STATE = "CLIENT_EDGE_RUNTIME_PROOF_FIXTURE_REPO_ONLY_DIRECT_MODE"
FIXTURE_NAME = "stage31_client_edge_runtime_fixture"
BASELINE = "40042c82a658dd991b6b025ec619fa064898fc52"
SEED = "fitnexus-stage31-client-edge-runtime-proof-v1"
ROUTES = [
    "get_workout",
    "start_workout",
    "set_completion",
    "get_feedback_context",
    "submit_feedback",
]
EXPECTED_IDS = {
    "user_id": "e06ec62d-e9b7-54a8-8fb9-d47828499939",
    "organization_id": "cd4688ec-cc08-5c2d-ad8c-0149242d809e",
    "student_id": "bbdf3d96-0569-51d4-aadc-251ed0abc24e",
    "plan_id": "b54064b9-f6a8-539e-b4a2-976d99141844",
    "exercise_id": "51871b03-c901-5a8f-b659-40f63e1f22e4",
    "link_id": "4ad0ced0-fc32-50cb-8287-fb4f971942a5",
}


def fail(message: str) -> None:
    raise SystemExit("STUDENT_ACCESS_CLIENT_EDGE_RUNTIME_PREPARATION_GUARD=FAIL\n" + message)


def text(path: Path) -> str:
    if not path.is_file():
        fail(f"missing source: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def data(path: Path) -> dict:
    try:
        value = json.loads(text(path))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path.relative_to(ROOT)}: {exc}")
    if not isinstance(value, dict):
        fail(f"expected JSON object: {path.relative_to(ROOT)}")
    return value


def require(mapping: dict, expected: dict, label: str) -> None:
    for key, value in expected.items():
        if mapping.get(key) != value:
            fail(f"{label} drift: {key}")


def main() -> None:
    authority = data(AUTHORITY)
    cutover = data(CUTOVER)
    rollback = data(ROLLBACK)
    smoke = data(SMOKE)
    ledger = data(LEDGER)
    fixture_sql = text(FIXTURE_SQL)
    transport = text(TRANSPORT)
    contract = text(CONTRACT)

    require(
        authority,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "current_state": STATE,
            "baseline_main_sha": BASELINE,
            "failure_classes": FAILURE_CLASSES,
        },
        "Stage 31 authority",
    )

    prerequisites = authority.get("prerequisites", {})
    require(
        prerequisites,
        {
            "cutover_required_state": "CLIENT_RUNTIME_ROLLBACK_VERIFIED_DIRECT_MODE",
            "runtime_smoke_required_state": "EDGE_RUNTIME_SMOKE_LIVE_VERIFIED_CLEANUP_COMPLETE",
            "rollback_required_state": "RUNTIME_ROLLBACK_PROOF_RECONCILED_DIRECT_MODE",
            "edge_runtime_version": 3,
            "stage30_five_route_server_smoke_verified": True,
            "stage30_synthetic_cleanup_complete": True,
            "isolated_rollback_resolver_proof_verified": True,
        },
        "Stage 31 prerequisites",
    )
    if cutover.get("current_state") != prerequisites["cutover_required_state"]:
        fail("cutover authority did not reach the reconciled direct-mode prerequisite")
    if rollback.get("current_state") != prerequisites["rollback_required_state"]:
        fail("rollback proof authority is not reconciled")
    if smoke.get("current_state") != prerequisites["runtime_smoke_required_state"]:
        fail("Stage 30 five-route smoke cleanup prerequisite regressed")

    smoke_runtime = smoke.get("runtime_proof", {})
    if smoke_runtime.get("all_five_routes_verified") is not True or smoke_runtime.get("cleanup_completed") is not True:
        fail("Stage 30 five-route runtime proof/cleanup receipt missing")
    for key in (
        "synthetic_business_rows_remaining",
        "synthetic_security_rows_remaining",
        "synthetic_network_proof_rows_remaining",
    ):
        if smoke_runtime.get(key) != 0:
            fail(f"Stage 30 synthetic residue returned: {key}")

    precondition = authority.get("database_precondition_receipt", {})
    if precondition.get("source") != "Supabase.execute_sql" or precondition.get("observed_at_utc") != "2026-08-21T10:45:41Z":
        fail("Stage 31 empty-domain receipt identity drifted")
    for key in (
        "auth_users",
        "profiles",
        "organizations",
        "students",
        "training_plans",
        "training_exercises",
        "access_links",
        "workout_sessions",
        "workout_logs",
        "workout_feedback",
    ):
        if precondition.get(key) != 0:
            fail(f"Stage 31 precondition receipt is not empty: {key}")
    if precondition.get("customer_domain_empty") is not True:
        fail("Stage 31 empty-domain receipt did not seal the empty customer domain")

    fixture = authority.get("fixture", {})
    require(
        fixture,
        {
            "repository_file": "04_backend_supabase/migrations/20260821104600_stage31_client_edge_runtime_fixture.sql",
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
        "Stage 31 fixture authority",
    )
    for key, expected in EXPECTED_IDS.items():
        if fixture.get(key) != expected:
            fail(f"Stage 31 fixture identifier drift: {key}")

    remote = {
        row.get("name"): row.get("version")
        for row in ledger.get("remote_migrations", [])
        if isinstance(row, dict)
    }
    if remote.get("stage30_edge_runtime_smoke_cleanup") != "20260821083507":
        fail("Stage 30 cleanup remote migration receipt missing")
    if FIXTURE_NAME in remote:
        fail(f"{FAILURE_CLASSES[2]} Stage 31 fixture self-attested as remotely applied")
    repo_only = {
        row.get("name")
        for row in ledger.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    }
    if repo_only != {FIXTURE_NAME}:
        fail(f"unexpected Stage 31 repo_only divergence set: {sorted(repo_only)}")
    row = next(
        row
        for row in ledger.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    )
    if row.get("related_failure_class") != FAILURE_CLASSES[0] or row.get("owner") != "BlackGold Forge":
        fail("Stage 31 repo_only divergence authority drifted")
    if ledger.get("baseline_main_sha") != BASELINE or ledger.get("observed_at_utc") != "2026-08-21T10:44:35Z":
        fail("Stage 31 migration ledger observation/baseline drifted")

    required_fixture_fragments = (
        FAILURE_CLASSES[0],
        "STAGE31_CLIENT_EDGE_RUNTIME_FIXTURE_REQUIRES_EMPTY_CUSTOMER_DOMAIN",
        "STAGE31_CLIENT_EDGE_RUNTIME_FIXTURE_POSTCONDITION_FAILED",
        SEED,
        "extensions.digest(v_token, 'sha256')",
        "now() + interval '2 hours'",
        "Stage31 Synthetic Organization",
        "Stage31 Synthetic Student",
        "Stage31 Synthetic Plan",
        "Stage31 Synthetic Exercise",
    )
    for fragment in required_fixture_fragments:
        if fragment not in fixture_sql:
            fail(f"Stage 31 fixture migration drift: {fragment}")
    if re.findall(r"(?<![0-9a-fA-F])[0-9a-fA-F]{64}(?![0-9a-fA-F])", fixture_sql):
        fail("Stage 31 fixture contains a bearer-looking 64-hex literal")
    fixture_lower = fixture_sql.lower()
    for forbidden in ("origin_hash", "cf-connecting-ip", "x-forwarded-for", "x-real-ip"):
        if forbidden in fixture_lower:
            fail(f"Stage 31 fixture contains forbidden network-origin material: {forbidden}")

    production = authority.get("production_boundary", {})
    require(
        production,
        {
            "active_transport": "directRpc",
            "resolved_transport": "directRpc",
            "edge_gateway_selected": False,
            "flutter_uses_edge_gateway_in_production": False,
            "direct_v2_rpc_path_active": True,
            "direct_anon_v2_rpc_execute_revoked": False,
            "explicit_rollback_requested": False,
            "explicit_rollback_authorized": False,
            "automatic_edge_to_direct_fallback": False,
            "client_cutover_verified": False,
            "behavioral_transport_change": False,
        },
        "Stage 31 production boundary",
    )
    cutover_transport = cutover.get("transport_contract", {})
    for key, expected in {
        "active_mode": "directRpc",
        "resolved_mode": "directRpc",
        "edge_gateway_selected": False,
        "automatic_edge_to_direct_fallback": False,
        "explicit_rollback_requested": False,
        "explicit_rollback_authorized": False,
        "direct_rpc_execute_revoked": False,
        "client_cutover_verified": False,
    }.items():
        if cutover_transport.get(key) != expected:
            fail(f"cutover production boundary drifted during Stage 31 preparation: {key}")

    seam = authority.get("client_verification_seam", {})
    require(
        seam,
        {
            "factory": "StudentAccessTransport.forVerification",
            "annotation": "visibleForTesting",
            "injected_client_type": "SupabaseClient",
            "explicit_configured_mode_supported": True,
            "verification_mode_for_live_proof": "edgeGateway",
            "explicit_rollback_requested_in_verification": False,
            "explicit_rollback_authorized_in_verification": False,
            "production_singleton_unchanged": True,
            "production_repositories_may_reference_factory": False,
            "automatic_edge_to_direct_fallback": False,
        },
        "Stage 31 verification seam",
    )

    for fragment in (
        "static final StudentAccessTransport instance = StudentAccessTransport._();",
        "@visibleForTesting",
        "factory StudentAccessTransport.forVerification({",
        "required SupabaseClient client",
        "required StudentAccessTransportMode configuredMode",
        "clientOverride: client",
        "configuredModeOverride: configuredMode",
        "explicitRollbackRequestedOverride: false",
        "explicitRollbackAuthorizedOverride: false",
        "_clientOverride ?? Supabase.instance.client",
        "resolveStudentAccessTransportMode(",
        "return _client.rpc(directRpc, params: directParams);",
        "return _invokeEdge(action: action, payload: edgePayload);",
        "_client.functions.invoke(",
    ):
        if fragment not in transport:
            fail(f"Stage 31 verification seam source drift: {fragment}")
    for fragment in (
        "static const StudentAccessTransportMode activeMode =",
        "StudentAccessTransportMode.directRpc;",
        "static const bool edgeGatewaySelected = false;",
        "static const bool automaticEdgeToDirectFallback = false;",
        "static const bool explicitRollbackRequested = false;",
        "static const bool explicitRollbackAuthorized = false;",
        "static const bool directRpcExecuteRevoked = false;",
        "static const bool rollbackVerified = false;",
        "static const bool clientCutoverVerified = false;",
    ):
        if fragment not in contract:
            fail(f"production transport contract drift during Stage 31 preparation: {fragment}")

    verification_usage = []
    for path in (APP_ROOT / "lib").rglob("*.dart"):
        if path == TRANSPORT:
            continue
        source = path.read_text(encoding="utf-8")
        if "StudentAccessTransport.forVerification" in source or ".forVerification(" in source:
            verification_usage.append(str(path.relative_to(ROOT)))
    if verification_usage:
        fail(f"{FAILURE_CLASSES[1]} verification-only transport leaked into production lib: {verification_usage}")

    expected_live = authority.get("expected_live_proof", {})
    if expected_live.get("route_sequence") != ROUTES or expected_live.get("route_count") != 5:
        fail("Stage 31 five-route client proof sequence drifted")
    for key in (
        "must_use_flutter_student_access_transport",
        "must_use_verification_factory",
        "must_use_edge_gateway_mode",
        "direct_rpc_call_from_proof_forbidden",
        "raw_token_return_forbidden",
        "raw_network_origin_return_forbidden",
        "real_customer_data_forbidden",
        "real_customer_mutation_forbidden",
        "workflow_must_be_one_shot",
        "workflow_must_be_sealed_to_exact_pr_and_head_before_first_execution",
    ):
        if expected_live.get(key) is not True:
            fail(f"Stage 31 live-proof invariant missing: {key}")

    runtime = authority.get("runtime_proof", {})
    if runtime.get("workflow_run_id") is not None or runtime.get("result") is not None:
        fail(f"{FAILURE_CLASSES[2]} live client proof receipt appeared before fixture apply")
    for key in (
        "flutter_transport_edge_path_verified",
        "get_workout_verified",
        "start_workout_verified",
        "set_completion_verified",
        "get_feedback_context_verified",
        "submit_feedback_verified",
        "all_five_routes_verified",
        "raw_token_returned",
        "raw_network_origin_returned",
        "real_customer_data_used",
        "real_customer_data_mutated",
        "proof_reexecution_allowed",
        "cleanup_completed",
    ):
        if runtime.get(key) is not False:
            fail(f"{FAILURE_CLASSES[2]} Stage 31 runtime proof self-attested: {key}")

    promotion = authority.get("promotion_rules", {})
    for key in (
        "may_apply_fixture_before_ci_and_merge",
        "may_execute_live_client_proof_before_fixture_remote_apply",
        "may_change_production_active_mode_during_preparation_or_proof",
        "may_select_edge_gateway_during_preparation_or_proof",
        "may_enable_automatic_edge_to_direct_fallback",
        "may_revoke_direct_rpc_execute_during_preparation_or_proof",
        "may_use_real_customer_data",
        "may_promote_launch_gates",
    ):
        if promotion.get(key) is not False:
            fail(f"Stage 31 gained prohibited promotion authority: {key}")
    for key in (
        "cleanup_required_before_any_edge_selection",
        "post_cutover_rollback_proof_still_required_before_direct_rpc_revocation",
    ):
        if promotion.get(key) is not True:
            fail(f"Stage 31 missing promotion interlock: {key}")

    next_stage = authority.get("next_stage", {})
    require(
        next_stage,
        {
            "name": "APPLY_STAGE31_CLIENT_EDGE_RUNTIME_FIXTURE",
            "allowed_now": True,
            "requires_ci_and_merge_first": True,
            "requires_exact_merged_sql": True,
            "requires_fresh_migration_ledger_check_immediately_before_apply": True,
            "may_select_edge_gateway_now": False,
            "may_revoke_direct_rpc_execute_now": False,
        },
        "Stage 31 next stage",
    )
    if any(value is not False for value in authority.get("launch_authority", {}).values()):
        fail("Stage 31 preparation gained launch authority")

    print("STUDENT_ACCESS_CLIENT_EDGE_RUNTIME_PREPARATION_GUARD=PASS")
    print(f"CURRENT_STATE={STATE}")
    print("PRODUCTION_ACTIVE_TRANSPORT=directRpc")
    print("VERIFICATION_EDGE_MODE=COMPILED_TEST_ONLY")
    print("PRODUCTION_VERIFICATION_FACTORY_USAGE=0")
    print("STAGE31_FIXTURE_LEDGER=REPO_ONLY")
    print("CUSTOMER_DOMAIN_PRECONDITION=EMPTY")
    print("LIVE_CLIENT_EDGE_PROOF=NOT_EXECUTED")
    print("EDGE_SELECTION=false")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")
    print("NEXT=APPLY_STAGE31_CLIENT_EDGE_RUNTIME_FIXTURE")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
