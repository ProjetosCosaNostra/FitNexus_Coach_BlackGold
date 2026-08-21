from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
APP = ROOT / "03_app_flutter" / "fitnexus_app" / "lib"
AUTHORITY = BACKEND / "student_access_valid_route_authority.json"
GATEWAY_AUTHORITY = BACKEND / "student_access_edge_gateway_authority.json"
SMOKE_AUTHORITY = BACKEND / "student_access_client_runtime_smoke_authority.json"
LEDGER = BACKEND / "migration_ledger_authority.json"
FIXTURE_SQL = BACKEND / "migrations" / "20260820180000_stage29_valid_student_route_fixture.sql"
CLEANUP_SQL = BACKEND / "migrations" / "20260820194000_stage29_valid_route_fixture_cleanup.sql"
LIVE = BACKEND / "tools" / "verify_student_access_valid_route_live.py"

FAILURE_CLASSES = [
    "BGF-VALID-STUDENT-ROUTE-UNPROVEN-187",
    "BGF-SYNTHETIC-VALID-ROUTE-FIXTURE-RESIDUE-188",
    "BGF-VALID-ROUTE-RESPONSE-DATA-LEAK-189",
]
APPLY_CLASS = "BGF-MIGRATION-APPLY-SYNTHETIC-LITERAL-SCREENING-191"
REEXEC_CLASS = "BGF-LIVE-PROOF-REEXECUTION-192"
CLEANUP_CLASS = "BGF-STAGE29-CLEANUP-SCOPE-DRIFT-193"
TOKEN_SEED = "fitnexus-stage29-valid-route-fixture-v1"
DERIVED_TOKEN = hashlib.sha256(TOKEN_SEED.encode("utf-8")).hexdigest()
FIXTURE_VERSION = "20260820192415"
SEALED_RUN = 32409055932
CLEANUP_NAME = "stage29_valid_route_fixture_cleanup"
STAGE30_SMOKE_NAME = "stage30_edge_runtime_smoke_fixture"
STAGE30_SMOKE_STATE = "EDGE_RUNTIME_SMOKE_FIXTURE_REPO_ONLY"

STATE_REPO = "VALID_ROUTE_SYNTHETIC_FIXTURE_REPO_ONLY"
STATE_REMOTE = "VALID_ROUTE_SYNTHETIC_FIXTURE_REMOTE_LIVE_PROOF_PENDING"
STATE_PROVEN = "VALID_ROUTE_LIVE_VERIFIED_CLEANUP_PENDING"
STATE_CLEANUP_REPO = "VALID_ROUTE_LIVE_VERIFIED_CLEANUP_REPO_ONLY"
STATE_CLEAN = "VALID_ROUTE_LIVE_VERIFIED_CLEANUP_COMPLETE"
ALLOWED_STATES = {STATE_REPO, STATE_REMOTE, STATE_PROVEN, STATE_CLEANUP_REPO, STATE_CLEAN}

FIXTURE_IDS = {
    "user_id": "2615749d-ffca-5319-84e0-b775578ceaf6",
    "organization_id": "13678787-eeae-5f6a-8828-190723a22594",
    "student_id": "659eafee-0508-5dfb-9fcb-d285d9e846db",
    "plan_id": "fd5762db-0a0c-54dc-81c9-2aeade199ee5",
    "exercise_id": "2ec1260b-88f2-5a2c-ba81-3433d2c147d5",
    "link_id": "f31a3c36-4ee1-5d64-b30d-f00fc98aea9b",
}
DIRECT_RPCS = (
    "get_student_workout_v2",
    "start_student_workout_v2",
    "set_student_exercise_completion_v2",
    "get_student_feedback_context_v2",
    "submit_student_workout_feedback_v2",
)


def fail(msg: str) -> None:
    raise SystemExit("STUDENT_ACCESS_VALID_ROUTE_FIXTURE_GUARD=FAIL\n" + msg)


def text(path: Path) -> str:
    if not path.is_file():
        fail(f"missing source: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def data(path: Path) -> dict:
    try:
        return json.loads(text(path))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path.relative_to(ROOT)}: {exc}")
    raise AssertionError("unreachable")


def stage30_smoke_repo_only_is_authorized(smoke: dict | None) -> bool:
    if smoke is None:
        return False
    if smoke.get("schema_version") != 1 or smoke.get("project_ref") != "mceukeondizkwlpfxzgf":
        return False
    if smoke.get("current_state") != STAGE30_SMOKE_STATE:
        return False
    fixture = smoke.get("fixture", {})
    proof = smoke.get("runtime_proof", {})
    client = smoke.get("client_cutover_authority", {})
    return (
        fixture.get("migration_name") == STAGE30_SMOKE_NAME
        and fixture.get("migration_ledger_state") == "repo_only"
        and fixture.get("remote_applied") is False
        and proof.get("fixture_deployed") is False
        and proof.get("all_five_routes_verified") is False
        and proof.get("cleanup_completed") is False
        and client.get("active_transport") == "directRpc"
        and client.get("edge_gateway_selected") is False
        and client.get("direct_rpc_execute_revoked") is False
    )


def main() -> None:
    authority = data(AUTHORITY)
    gateway = data(GATEWAY_AUTHORITY)
    smoke = data(SMOKE_AUTHORITY) if SMOKE_AUTHORITY.is_file() else None
    ledger = data(LEDGER)
    fixture_sql = text(FIXTURE_SQL)
    cleanup_sql = text(CLEANUP_SQL) if CLEANUP_SQL.is_file() else ""
    live = text(LIVE)

    if authority.get("schema_version") != 1 or authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("Stage 29 authority identity drifted")
    if authority.get("failure_classes") != FAILURE_CLASSES:
        fail("Stage 29 primary failure classes drifted")
    if authority.get("apply_compatibility_failure_class") != APPLY_CLASS:
        fail("apply compatibility prevention disappeared")

    state = authority.get("current_state")
    if state not in ALLOWED_STATES:
        fail(f"unsupported Stage 29 state: {state}")

    fixture = authority.get("fixture_migration", {})
    expected_fixture = {
        "repository_file": "04_backend_supabase/migrations/20260820180000_stage29_valid_student_route_fixture.sql",
        "migration_name": "stage29_valid_student_route_fixture",
        "requires_empty_customer_domain": True,
        "synthetic_auth_user": True,
        "synthetic_organization": True,
        "synthetic_student": True,
        "synthetic_training_plan": True,
        "synthetic_exercise": True,
        "synthetic_access_link": True,
        "raw_token_is_public_synthetic_test_material": True,
        "synthetic_token_derivation": "SHA256_UTF8_PUBLIC_SEED",
        "synthetic_token_seed": TOKEN_SEED,
        "repository_contains_bearer_literal": False,
        "database_stores_token_hash_only": True,
        "fixture_expiry_hours": 2,
        "cleanup_migration_required": True,
    }
    for key, expected in expected_fixture.items():
        if fixture.get(key) != expected:
            fail(f"fixture authority drift for {key}")

    if state == STATE_REPO:
        if fixture.get("remote_applied") is not False or fixture.get("migration_ledger_state") != "repo_only":
            fail("repository fixture self-promoted")
    else:
        if fixture.get("remote_applied") is not True or fixture.get("remote_version") != FIXTURE_VERSION:
            fail("remote fixture receipt missing")
        if fixture.get("migration_ledger_state") != "remote_reconciled":
            fail("fixture ledger state not reconciled")

    if authority.get("fixture_identifiers") != FIXTURE_IDS:
        fail("fixture identifiers drifted")
    if DERIVED_TOKEN in json.dumps(authority, sort_keys=True) or DERIVED_TOKEN in fixture_sql:
        fail(f"{APPLY_CLASS} derived bearer literal leaked")
    if re.search(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])", fixture_sql.lower()):
        fail(f"{APPLY_CLASS} bearer-looking literal appeared in fixture SQL")
    for fragment in (
        TOKEN_SEED,
        "STAGE29_VALID_ROUTE_FIXTURE_REQUIRES_EMPTY_CUSTOMER_DOMAIN",
        "extensions.digest(v_token, 'sha256')",
        "from private.resolve_student_access(v_token)",
    ):
        if fragment not in fixture_sql:
            fail(f"fixture SQL drift: {fragment}")

    proof_required = state in {STATE_PROVEN, STATE_CLEANUP_REPO, STATE_CLEAN}
    runtime = authority.get("runtime_verification", {})
    for key in (
        "valid_token_edge_route_verified_live",
        "student_rpc_forwarding_with_valid_token_verified_live",
        "response_matches_synthetic_fixture",
    ):
        if runtime.get(key) is not proof_required:
            fail(f"runtime proof drift: {key}")
    if runtime.get("fixture_deployed") is not (state != STATE_REPO):
        fail("fixture deployment state drifted")
    cleanup_complete = state == STATE_CLEAN
    if runtime.get("cleanup_completed") is not cleanup_complete:
        fail("cleanup completion state drifted")
    expected_remaining = 0 if cleanup_complete else (None if state == STATE_REPO else 14)
    if runtime.get("synthetic_business_rows_remaining") != expected_remaining:
        fail("synthetic residue count authority drifted")
    if runtime.get("edge_alert_delivery_verified") is not False or runtime.get("rollback_verified") is not False:
        fail("unrelated runtime authority self-promoted")

    if proof_required:
        if authority.get("proof_reexecution_failure_class") != REEXEC_CLASS:
            fail("proof reexecution prevention class missing")
        receipt = authority.get("live_proof_receipt", {})
        required_receipt = {
            "workflow_run_id": SEALED_RUN,
            "result": "PASS",
            "http_status": 200,
            "action": "get_workout",
            "student_rpc_forwarding_with_valid_token_verified": True,
            "response_matches_synthetic_fixture": True,
            "raw_synthetic_token_returned": False,
            "raw_network_origin_returned": False,
            "real_student_data_used": False,
            "real_student_data_mutated": False,
            "proof_reexecution_allowed": False,
        }
        for key, expected in required_receipt.items():
            if receipt.get(key) != expected:
                fail(f"sealed live proof receipt drift: {key}")
        for fragment in (REEXEC_CLASS, "SEALED_SKIP_REEXECUTION", "NETWORK_CALL_EXECUTED=false", f"EXPECTED_SEALED_RUN = {SEALED_RUN}"):
            if fragment not in live:
                fail(f"{REEXEC_CLASS} verifier seal drift: {fragment}")

    remote = {row.get("name"): row.get("version") for row in ledger.get("remote_migrations", [])}
    repo_only = {row.get("name") for row in ledger.get("declared_divergences", []) if row.get("direction") == "repo_only"}
    if state == STATE_REPO:
        if repo_only != {"stage29_valid_student_route_fixture"} or "stage29_valid_student_route_fixture" in remote:
            fail("fixture repo_only ledger mismatch")
    else:
        if remote.get("stage29_valid_student_route_fixture") != FIXTURE_VERSION:
            fail("fixture remote ledger receipt missing")
        expected_repo_only = {CLEANUP_NAME} if state == STATE_CLEANUP_REPO else set()
        if state == STATE_CLEAN and repo_only == {STAGE30_SMOKE_NAME}:
            if not stage30_smoke_repo_only_is_authorized(smoke):
                fail("Stage 30 repo_only divergence is not backed by a fail-closed smoke authority")
            expected_repo_only = {STAGE30_SMOKE_NAME}
        if repo_only != expected_repo_only:
            fail(f"unexpected repo_only set for {state}: {sorted(repo_only)}")

    if state in {STATE_CLEANUP_REPO, STATE_CLEAN}:
        if authority.get("cleanup_scope_failure_class") != CLEANUP_CLASS:
            fail("cleanup scope failure class missing")
        cleanup = authority.get("cleanup_migration", {})
        expected_cleanup = {
            "repository_file": "04_backend_supabase/migrations/20260820194000_stage29_valid_route_fixture_cleanup.sql",
            "migration_name": CLEANUP_NAME,
            "customer_domain_must_remain_synthetic_only": True,
            "expected_total_auth_users_before_cleanup": 1,
            "expected_total_organizations_before_cleanup": 1,
            "expected_total_students_before_cleanup": 1,
            "expected_total_training_plans_before_cleanup": 1,
            "expected_total_training_exercises_before_cleanup": 1,
            "expected_total_access_links_before_cleanup": 1,
            "expected_workout_sessions_before_cleanup": 0,
            "expected_workout_logs_before_cleanup": 0,
            "expected_workout_feedback_before_cleanup": 0,
            "expected_growth_events_for_fixture_org": 4,
            "expected_link_rate_bucket_rows": 1,
            "expected_link_rate_bucket_request_count": 2,
            "expected_network_proof_bucket_rows": 2,
            "network_proof_selector_operation": "get_workout",
            "network_proof_selector_window_utc": "2026-08-20T19:30:00Z",
            "network_proof_selector_request_count": 1,
            "origin_hash_embedded_in_repository": False,
            "raw_network_origin_embedded_in_repository": False,
            "organization_deleted_before_auth_user": True,
            "transactional_postcondition_required": True,
        }
        for key, expected in expected_cleanup.items():
            if cleanup.get(key) != expected:
                fail(f"cleanup authority drift for {key}")
        if state == STATE_CLEANUP_REPO:
            if cleanup.get("remote_applied") is not False or cleanup.get("migration_ledger_state") != "repo_only":
                fail("cleanup repository state self-promoted")
        else:
            if cleanup.get("remote_applied") is not True or cleanup.get("migration_ledger_state") != "remote_reconciled":
                fail("cleanup remote receipt missing")
            remote_version = cleanup.get("remote_version")
            if not isinstance(remote_version, str) or remote.get(CLEANUP_NAME) != remote_version:
                fail("cleanup remote version/ledger mismatch")
        for fragment in (
            CLEANUP_CLASS,
            "STAGE29_CLEANUP_CUSTOMER_DOMAIN_NO_LONGER_SYNTHETIC_ONLY",
            "STAGE29_CLEANUP_NETWORK_BUCKET_SELECTOR_MISMATCH",
            "STAGE29_CLEANUP_POSTCONDITION_FAILED",
            "2026-08-20 19:30:00+00",
            "delete from public.organizations where id = v_org",
            "delete from auth.users where id = v_user",
        ):
            if fragment not in cleanup_sql:
                fail(f"cleanup SQL drift: {fragment}")
        if "origin_hash" in cleanup_sql.lower() or DERIVED_TOKEN in cleanup_sql:
            fail(f"{CLEANUP_CLASS} cleanup source leaked pseudonymous origin/token material")

    gv = gateway.get("runtime_verification", {})
    if gv.get("candidate_deployed") is not True or gv.get("invalid_token_network_origin_rate_limit_threshold_verified_live") is not True:
        fail("Edge v3 prerequisite proof missing")

    direct = {rpc: False for rpc in DIRECT_RPCS}
    for path in APP.rglob("*.dart"):
        source = path.read_text(encoding="utf-8")
        for rpc in DIRECT_RPCS:
            if f"'{rpc}'" in source:
                direct[rpc] = True
    missing = [rpc for rpc, present in direct.items() if not present]
    if missing:
        fail(f"Flutter direct fallback changed before cutover: {missing}")

    client = authority.get("client_boundary", {})
    if client.get("flutter_uses_edge_gateway") is not False or client.get("direct_v2_rpc_path_active") is not True:
        fail("Flutter cutover self-attested")
    if client.get("direct_anon_v2_rpc_execute_revoked") is not False or client.get("client_direct_rpc_fallback_removed") is not False:
        fail("direct RPC path revoked/removed prematurely")
    if any(value is not False for value in authority.get("launch_authority", {}).values()):
        fail("Stage 29 gained launch authority")

    print("STUDENT_ACCESS_VALID_ROUTE_FIXTURE_GUARD=PASS")
    print(f"CURRENT_STATE={state}")
    print("LIVE_VALID_ROUTE_PROOF=VERIFIED" if proof_required else "LIVE_VALID_ROUTE_PROOF=PENDING")
    print("PROOF_REEXECUTION=SEALED" if proof_required else "PROOF_REEXECUTION=NOT_YET_SEALED")
    print(f"CLEANUP_REPO_ONLY={str(state == STATE_CLEANUP_REPO).lower()}")
    print(f"CLEANUP_COMPLETE={str(cleanup_complete).lower()}")
    print("FLUTTER_CUTOVER=false")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
