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
LEDGER = BACKEND / "migration_ledger_authority.json"
MIGRATION = BACKEND / "migrations" / "20260820180000_stage29_valid_student_route_fixture.sql"

FAILURE_CLASSES = (
    "BGF-VALID-STUDENT-ROUTE-UNPROVEN-187",
    "BGF-SYNTHETIC-VALID-ROUTE-FIXTURE-RESIDUE-188",
    "BGF-VALID-ROUTE-RESPONSE-DATA-LEAK-189",
)
GUARD_CONTRADICTION_CLASS = "BGF-GUARD-REQUIRED-FORBIDDEN-CONTRADICTION-190"
APPLY_COMPATIBILITY_CLASS = "BGF-MIGRATION-APPLY-SYNTHETIC-LITERAL-SCREENING-191"
TOKEN_SEED = "fitnexus-stage29-valid-route-fixture-v1"
FIXTURE_TOKEN = hashlib.sha256(TOKEN_SEED.encode("utf-8")).hexdigest()
FIXTURE_REMOTE_VERSION = "20260820192415"
STATE_REPO_ONLY = "VALID_ROUTE_SYNTHETIC_FIXTURE_REPO_ONLY"
STATE_REMOTE_PENDING = "VALID_ROUTE_SYNTHETIC_FIXTURE_REMOTE_LIVE_PROOF_PENDING"
FIXTURE_IDS = {
    "user_id": "2615749d-ffca-5319-84e0-b775578ceaf6",
    "organization_id": "13678787-eeae-5f6a-8828-190723a22594",
    "student_id": "659eafee-0508-5dfb-9fcb-d285d9e846db",
    "plan_id": "fd5762db-0a0c-54dc-81c9-2aeade199ee5",
    "exercise_id": "2ec1260b-88f2-5a2c-ba81-3433d2c147d5",
    "link_id": "f31a3c36-4ee1-5d64-b30d-f00fc98aea9b",
}
DIRECT_V2_RPCS = (
    "get_student_workout_v2",
    "start_student_workout_v2",
    "set_student_exercise_completion_v2",
    "get_student_feedback_context_v2",
    "submit_student_workout_feedback_v2",
)


def fail(message: str) -> None:
    raise SystemExit("STUDENT_ACCESS_VALID_ROUTE_FIXTURE_GUARD=FAIL\n" + message)


def read_text(path: Path) -> str:
    if not path.is_file():
        fail(f"missing source: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> dict:
    try:
        return json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path.relative_to(ROOT)}: {exc}")
    raise AssertionError("unreachable")


def main() -> None:
    authority = read_json(AUTHORITY)
    gateway = read_json(GATEWAY_AUTHORITY)
    ledger = read_json(LEDGER)
    migration = read_text(MIGRATION)
    lower = migration.lower()

    if authority.get("schema_version") != 1 or authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("Stage 29 authority identity drifted")
    if authority.get("failure_classes") != list(FAILURE_CLASSES):
        fail("Stage 29 failure classes drifted")
    if authority.get("apply_compatibility_failure_class") != APPLY_COMPATIBILITY_CLASS:
        fail("Stage 29 apply-compatibility failure class drifted")

    state = authority.get("current_state")
    if state not in {STATE_REPO_ONLY, STATE_REMOTE_PENDING}:
        fail(f"unsupported Stage 29 fixture state: {state}")

    fixture = authority.get("fixture_migration", {})
    common_fixture = {
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
    for key, expected in common_fixture.items():
        if fixture.get(key) != expected:
            fail(f"fixture authority drift for {key}")

    if state == STATE_REPO_ONLY:
        if fixture.get("remote_applied") is not False or fixture.get("migration_ledger_state") != "repo_only":
            fail("repository-only fixture state self-promoted")
        if fixture.get("remote_version") is not None:
            fail("repository-only fixture unexpectedly has a remote version")
    else:
        if fixture.get("remote_applied") is not True:
            fail("remote fixture state lost remote_applied receipt")
        if fixture.get("remote_version") != FIXTURE_REMOTE_VERSION:
            fail("remote fixture version drifted")
        if fixture.get("migration_ledger_state") != "remote_reconciled":
            fail("remote fixture is not reconciled in authority")

    if authority.get("fixture_identifiers") != FIXTURE_IDS:
        fail("synthetic fixture identifiers drifted")
    authority_text = json.dumps(authority, sort_keys=True)
    if FIXTURE_TOKEN in authority_text:
        fail(f"{FAILURE_CLASSES[2]} derived synthetic bearer token must not be duplicated into authority JSON")

    expected_live = authority.get("expected_live_contract", {})
    for key, expected in {
        "edge_runtime_version": 3,
        "method": "POST",
        "action": "get_workout",
        "expected_http_status": 200,
        "expected_student_name": "Stage29 Synthetic Student",
        "expected_plan_name": "Stage29 Synthetic Plan",
        "expected_exercise_name": "Stage29 Synthetic Exercise",
        "expected_exercise_count": 1,
        "expected_history_count": 0,
        "expected_session": None,
        "raw_token_returned": False,
        "raw_network_origin_returned": False,
        "real_student_data_used": False,
        "real_student_data_mutated": False,
    }.items():
        if expected_live.get(key) != expected:
            fail(f"expected live contract drift for {key}")

    runtime = authority.get("runtime_verification", {})
    if state == STATE_REPO_ONLY:
        expected_runtime = {
            "fixture_deployed": False,
            "valid_token_edge_route_verified_live": False,
            "student_rpc_forwarding_with_valid_token_verified_live": False,
            "response_matches_synthetic_fixture": False,
            "cleanup_completed": False,
            "synthetic_business_rows_remaining": None,
            "edge_alert_delivery_verified": False,
            "rollback_verified": False,
        }
    else:
        expected_runtime = {
            "fixture_deployed": True,
            "valid_token_edge_route_verified_live": False,
            "student_rpc_forwarding_with_valid_token_verified_live": False,
            "response_matches_synthetic_fixture": False,
            "cleanup_completed": False,
            "synthetic_business_rows_remaining": 14,
            "edge_alert_delivery_verified": False,
            "rollback_verified": False,
        }
    for key, expected in expected_runtime.items():
        if runtime.get(key) != expected:
            fail(f"runtime verification drift for {key}")

    if state == STATE_REMOTE_PENDING:
        receipt = authority.get("fixture_apply_receipt", {})
        expected_counts = {
            "auth_users": 1,
            "profiles": 1,
            "organizations": 1,
            "organization_members": 1,
            "organization_subscriptions": 1,
            "subscription_authority_events": 1,
            "students": 1,
            "training_plans": 1,
            "training_exercises": 1,
            "student_access_links": 1,
            "growth_events": 4,
            "growth_attribution": 0,
            "fixture_derived_rows_observed": 14,
            "active_link_verified": True,
            "trial_initialized_verified": True,
            "owner_membership_verified": True,
        }
        for key, expected in expected_counts.items():
            if receipt.get(key) != expected:
                fail(f"remote fixture apply receipt drift for {key}")

    if gateway.get("current_state") != "EDGE_GATEWAY_V3_THRESHOLD_429_VERIFIED_SYNTHETIC_CLEANUP_COMPLETE_VALID_ROUTE_PROOF_PENDING":
        fail("Stage 28 prerequisite state drifted")
    gv = gateway.get("runtime_verification", {})
    if gv.get("candidate_deployed") is not True:
        fail("Edge v3 deployment prerequisite missing")
    if gv.get("invalid_token_network_origin_rate_limit_threshold_verified_live") is not True:
        fail("Stage 28 exact threshold prerequisite missing")
    if gv.get("student_rpc_forwarding_with_valid_token_verified_live") is not False:
        fail("valid-route proof was already self-attested")

    repo_only = {
        row.get("name")
        for row in ledger.get("declared_divergences", [])
        if row.get("direction") == "repo_only"
    }
    remote = {row.get("name"): row.get("version") for row in ledger.get("remote_migrations", [])}
    if state == STATE_REPO_ONLY:
        if repo_only != {"stage29_valid_student_route_fixture"}:
            fail(f"unexpected repo_only migration set: {sorted(repo_only)}")
        if "stage29_valid_student_route_fixture" in remote:
            fail("fixture appears remote while authority says repo_only")
    else:
        if repo_only:
            fail(f"unexpected repo_only divergence after fixture apply: {sorted(repo_only)}")
        if remote.get("stage29_valid_student_route_fixture") != FIXTURE_REMOTE_VERSION:
            fail("migration ledger missing Stage 29 remote fixture receipt")

    required_source = (
        "BGF-VALID-STUDENT-ROUTE-UNPROVEN-187",
        "BGF-SYNTHETIC-VALID-ROUTE-FIXTURE-RESIDUE-188",
        "BGF-VALID-ROUTE-RESPONSE-DATA-LEAK-189",
        APPLY_COMPATIBILITY_CLASS,
        "STAGE29_VALID_ROUTE_FIXTURE_REQUIRES_EMPTY_CUSTOMER_DOMAIN",
        "STAGE29_SYNTHETIC_TRIAL_INITIALIZATION_FAILED",
        "STAGE29_SYNTHETIC_TOKEN_RESOLUTION_FAILED",
        "STAGE29_SYNTHETIC_FIXTURE_POSTCONDITION_FAILED",
        "insert into auth.users",
        "insert into public.organizations",
        "insert into public.students",
        "insert into public.training_plans",
        "insert into public.training_exercises",
        "insert into public.student_access_links",
        "extensions.digest(convert_to('fitnexus-stage29-valid-route-fixture-v1', 'UTF8'), 'sha256')",
        "extensions.digest(v_token, 'sha256')",
        "from private.resolve_student_access(v_token)",
        "now() + interval '2 hours'",
        *FIXTURE_IDS.values(),
    )
    missing = [fragment for fragment in required_source if fragment not in migration]
    if missing:
        fail(f"synthetic fixture migration incomplete: {missing}")

    forbidden_authority_prose = (
        '"requires_empty_customer_domain"',
        '"raw_token_is_public_synthetic_test_material"',
        '"database_stores_token_hash_only"',
        '"cleanup_migration_required"',
        '"valid_token_edge_route_verified_live"',
    )
    contradictory = [
        forbidden
        for forbidden in forbidden_authority_prose
        if any(forbidden.lower() in required.lower() or required.lower() in forbidden.lower() for required in required_source)
    ]
    if contradictory:
        fail(f"{GUARD_CONTRADICTION_CLASS} guard required/forbidden predicate overlap: {contradictory}")
    leaked = [fragment for fragment in forbidden_authority_prose if fragment in migration]
    if leaked:
        fail(f"authority JSON prose leaked into migration unexpectedly: {leaked}")

    if "email," in lower or "encrypted_password" in lower:
        fail("synthetic auth fixture must not create a routable email/password credential")
    if FIXTURE_TOKEN in migration:
        fail(f"{APPLY_COMPATIBILITY_CLASS} derived bearer was materialized as a repository literal")
    if re.search(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])", lower):
        fail(f"{APPLY_COMPATIBILITY_CLASS} bearer-looking 64-hex literal found in fixture migration")
    if migration.count(TOKEN_SEED) != 1:
        fail("synthetic public token seed must appear exactly once in the fixture migration")
    for identifier in FIXTURE_IDS.values():
        if migration.count(identifier) != 1:
            fail(f"synthetic identifier should be declared once: {identifier}")

    client = authority.get("client_boundary", {})
    if client.get("flutter_uses_edge_gateway") is not False:
        fail("Flutter cutover self-attested")
    if client.get("direct_v2_rpc_path_active") is not True:
        fail("direct RPC fallback removed before valid route proof")
    if client.get("direct_anon_v2_rpc_execute_revoked") is not False:
        fail("direct RPC grants revoked before valid route proof")

    direct_calls = {rpc: 0 for rpc in DIRECT_V2_RPCS}
    for path in APP.rglob("*.dart"):
        source = path.read_text(encoding="utf-8")
        for rpc in direct_calls:
            if f"'{rpc}'" in source:
                direct_calls[rpc] += 1
    missing_direct = [rpc for rpc, count in direct_calls.items() if count == 0]
    if missing_direct:
        fail(f"partial Flutter cutover detected: {missing_direct}")

    if any(value is not False for value in authority.get("launch_authority", {}).values()):
        fail("Stage 29 fixture gained launch authority")

    print("STUDENT_ACCESS_VALID_ROUTE_FIXTURE_GUARD=PASS")
    print(f"GUARD_CONTRADICTION_PREVENTION={GUARD_CONTRADICTION_CLASS}")
    print(f"APPLY_COMPATIBILITY_PREVENTION={APPLY_COMPATIBILITY_CLASS}")
    print(f"CURRENT_STATE={state}")
    print("FIXTURE_KIND=SYNTHETIC_ONLY")
    print("SYNTHETIC_TOKEN_SOURCE=PUBLIC_SEED_DERIVED")
    print("REPOSITORY_BEARER_LITERAL=false")
    print("DATABASE_TOKEN_STORAGE=SHA256_ONLY")
    print(f"FIXTURE_REMOTE_APPLIED={str(fixture.get('remote_applied')).lower()}")
    print("LIVE_VALID_ROUTE_PROOF=PENDING")
    print("CLEANUP_MIGRATION=REQUIRED_AFTER_PROOF")
    print("FLUTTER_CUTOVER=false")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
