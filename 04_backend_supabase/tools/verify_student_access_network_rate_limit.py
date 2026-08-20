from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
APP = ROOT / "03_app_flutter" / "fitnexus_app" / "lib"
MIGRATION = BACKEND / "migrations" / "20260820063000_stage27_student_network_origin_rate_limit.sql"
VERIFY_MIGRATION = BACKEND / "migrations" / "20260820065900_stage27_network_rate_limit_verification_interlock.sql"
AUTHORITY = BACKEND / "student_access_network_rate_limit_authority.json"
NETWORK_AUTHORITY = BACKEND / "student_access_network_origin_boundary.json"
LEDGER = BACKEND / "migration_ledger_authority.json"
EXTERNAL_GATES = BACKEND / "external_gate_evidence_placeholders.json"

FAILURE_CLASSES = [
    "BGF-EDGE-INVALID-TOKEN-RATE-LIMIT-174",
    "BGF-NETWORK-ORIGIN-RAW-PERSISTENCE-175",
    "BGF-NETWORK-THROTTLE-CALLER-LIMIT-OVERRIDE-176",
    "BGF-EDGE-SECRET-KEY-LEAK-177",
]
VERIFY_FAILURE_CLASS = "BGF-NETWORK-RATE-LIMIT-REMOTE-VERIFICATION-179"
THRESHOLDS = {
    "get_workout": 120,
    "start_workout": 30,
    "set_completion": 120,
    "get_feedback_context": 90,
    "submit_feedback": 30,
}
DIRECT_V2_RPCS = (
    "get_student_workout_v2",
    "start_student_workout_v2",
    "set_student_exercise_completion_v2",
    "get_student_feedback_context_v2",
    "submit_student_workout_feedback_v2",
)
PENDING_STATE = "DATABASE_APPLIED_VERIFICATION_INTERLOCK_REPO_ONLY"
VERIFIED_STATE = "DATABASE_RATE_LIMIT_APPLIED_VERIFIED_EDGE_INTEGRATION_PENDING"


def fail(message: str) -> None:
    raise SystemExit("STUDENT_ACCESS_NETWORK_RATE_LIMIT_GUARD=FAIL\n" + message)


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


def require(source: str, fragments: tuple[str, ...], failure_class: str) -> None:
    lower = source.lower()
    missing = [fragment for fragment in fragments if fragment.lower() not in lower]
    if missing:
        fail(f"{failure_class} missing invariants: {missing}")


def main() -> None:
    authority = data(AUTHORITY)
    network = data(NETWORK_AUTHORITY)
    ledger = data(LEDGER)
    external = data(EXTERNAL_GATES)
    migration = text(MIGRATION)
    verification = text(VERIFY_MIGRATION)
    lower = migration.lower()

    if authority.get("schema_version") != 1 or authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("Stage 27 authority identity drifted")
    if authority.get("failure_classes") != FAILURE_CLASSES:
        fail("Stage 27 failure-class authority drifted")
    if authority.get("verification_failure_class") != VERIFY_FAILURE_CLASS:
        fail("Stage 27 verification failure class drifted")

    state = authority.get("current_state")
    if state not in (PENDING_STATE, VERIFIED_STATE):
        fail(f"unsupported Stage 27 authority state: {state!r}")

    migration_auth = authority.get("migration", {})
    if migration_auth.get("repository_file") != "04_backend_supabase/migrations/20260820063000_stage27_student_network_origin_rate_limit.sql":
        fail("Stage 27 migration path drifted")
    if migration_auth.get("migration_name") != "stage27_student_network_origin_rate_limit":
        fail("Stage 27 migration name drifted")
    if migration_auth.get("remote_applied") is not True or migration_auth.get("remote_version") != "20260820065403":
        fail("Stage 27 remote migration receipt is missing")

    verify_auth = authority.get("verification_migration", {})
    expected_verify = {
        "repository_file": "04_backend_supabase/migrations/20260820065900_stage27_network_rate_limit_verification_interlock.sql",
        "migration_name": "stage27_network_rate_limit_verification_interlock",
        "test_origin": "RFC5737_TEST_NET_ONLY",
        "test_operation": "get_workout",
        "test_calls": 121,
        "expected_allowed_calls": 120,
        "expected_rate_limited_calls": 1,
        "synthetic_bucket_cleanup_required": True,
        "synthetic_signal_cleanup_required": True,
    }
    for key, expected in expected_verify.items():
        if verify_auth.get(key) != expected:
            fail(f"verification authority drift for {key}: {verify_auth.get(key)!r}")
    if state == PENDING_STATE and verify_auth.get("remote_applied") is not False:
        fail("verification migration self-promoted before remote apply")
    if state == VERIFIED_STATE and verify_auth.get("remote_applied") is not True:
        fail("verified state is missing remote verification receipt")

    trusted = authority.get("trusted_origin_authority", {})
    if trusted != {
        "source": "cf-connecting-ip",
        "source_state": "ORIGIN_SOURCE_SPOOF_RESISTANCE_VERIFIED",
        "edge_function_version": 2,
        "spoof_proof_workflow_run_id": 32338900002,
        "spoof_proof_outcome": "BLOCKED_AT_EDGE_403",
        "client_can_force_source": False,
    }:
        fail(f"{FAILURE_CLASSES[0]} trusted-origin authority drifted")

    observed = network.get("observed_runtime", {})
    if network.get("current_state") != "ORIGIN_SOURCE_SPOOF_RESISTANCE_VERIFIED":
        fail("Stage 26 origin trust was not preserved")
    if observed.get("runtime_origin_candidate") != "cf-connecting-ip" or observed.get("runtime_origin_candidate_trusted_for_security") is not True:
        fail("trusted network-origin source drifted")

    if authority.get("route_thresholds_per_minute") != THRESHOLDS:
        fail(f"{FAILURE_CLASSES[2]} threshold authority drifted")

    db = authority.get("database_contract", {})
    expected_db = {
        "private_function": "private.student_access_network_rate_limit_v1(text,text)",
        "public_bridge": "public.check_student_access_network_rate_limit_v1(text,text)",
        "public_bridge_security_mode": "SECURITY_INVOKER",
        "public_bridge_execute_role": "service_role",
        "caller_can_supply_limit": False,
        "raw_network_origin_persisted": False,
        "origin_digest_persisted": True,
        "origin_digest_algorithm": "HMAC-SHA256",
        "pepper_generated_at_remote_migration_apply": True,
        "pepper_length_bytes": 32,
        "pepper_stored_in_repository": False,
        "pepper_direct_service_role_access": False,
        "bucket_retention_days": 2,
        "rate_limit_error": "STUDENT_NETWORK_RATE_LIMITED",
        "signal_type": "network_rate_limit_burst",
        "signal_severity": "high",
        "posture_view_replace_policy": "preserve_existing_columns_in_order_append_new_columns_only",
        "posture_view_stage27_appended_column": "network_rate_limit_burst_signals_60m",
    }
    for key, expected in expected_db.items():
        if db.get(key) != expected:
            fail(f"database contract drift for {key}: {db.get(key)!r}")

    require(
        migration,
        (
            "create table if not exists private.student_access_network_origin_secret",
            "extensions.gen_random_bytes(32)",
            "create table if not exists private.student_access_network_rate_buckets",
            "origin_hash bytea not null",
            "extensions.hmac(",
            "convert_to('fitnexus-student-origin-v1:' || v_origin, 'UTF8')",
            "create or replace function private.student_access_network_rate_limit_v1(",
            "create or replace function public.check_student_access_network_rate_limit_v1(",
            "security invoker",
            "grant execute on function public.check_student_access_network_rate_limit_v1(text,text)",
            "to service_role",
            "network_rate_limit_burst",
            "STUDENT_NETWORK_RATE_LIMITED",
        ),
        FAILURE_CLASSES[0],
    )
    if "p_limit" in lower or "limit_per_minute integer" in lower:
        fail(f"{FAILURE_CLASSES[2]} caller-supplied threshold appeared")
    for operation, threshold in THRESHOLDS.items():
        if f"when '{operation}' then {threshold}" not in lower:
            fail(f"{FAILURE_CLASSES[2]} missing DB threshold for {operation}")

    bucket_start = lower.index("create table if not exists private.student_access_network_rate_buckets")
    bucket_end = lower.index(");", bucket_start) + 2
    bucket_ddl = lower[bucket_start:bucket_end]
    for forbidden in ("client_ip", "ip_address", "network_origin text", "origin text"):
        if forbidden in bucket_ddl:
            fail(f"{FAILURE_CLASSES[1]} raw origin persistence appeared: {forbidden}")
    for secret_fragment in ("sb_secret_", "service_role_key=", "supabase_service_role_key"):
        if secret_fragment in lower:
            fail(f"{FAILURE_CLASSES[3]} secret material appeared in migration source")

    require(
        verification,
        (
            VERIFY_FAILURE_CLASS,
            "203.0.113.55",
            "for v_i in 1..121 loop",
            "STUDENT_NETWORK_RATE_LIMITED",
            "request_count')::integer <> 121",
            "limit_per_minute')::integer <> 120",
            "delete from private.student_access_security_signals",
            "delete from private.student_access_network_rate_buckets",
            "STAGE27_VERIFY_SYNTHETIC_CLEANUP_FAILED",
        ),
        VERIFY_FAILURE_CLASS,
    )

    divergences = ledger.get("declared_divergences", [])
    repo_only_names = {
        item.get("name") for item in divergences if item.get("direction") == "repo_only"
    }
    remote_names = {item.get("name") for item in ledger.get("remote_migrations", [])}
    if state == PENDING_STATE:
        if "stage27_network_rate_limit_verification_interlock" not in repo_only_names:
            fail("verification migration is not declared repo_only")
    else:
        if "stage27_student_network_origin_rate_limit" not in remote_names:
            fail("verified state missing Stage 27 remote migration in ledger")
        if "stage27_network_rate_limit_verification_interlock" not in remote_names:
            fail("verified state missing verification migration in ledger")
        if "stage27_student_network_origin_rate_limit" in repo_only_names or "stage27_network_rate_limit_verification_interlock" in repo_only_names:
            fail("verified state still contains Stage 27 repo_only divergence")

    runtime = authority.get("runtime_boundary", {})
    for key in (
        "edge_gateway_uses_network_rate_limit",
        "invalid_token_network_origin_rate_limit_verified_live",
        "flutter_uses_edge_gateway",
        "direct_anon_v2_rpc_execute_revoked",
        "edge_alert_delivery_verified",
        "rollback_verified",
    ):
        if runtime.get(key) is not False:
            fail(f"Stage 27 database work self-promoted runtime state: {key}")
    if runtime.get("direct_v2_rpc_path_active") is not True:
        fail("direct v2 RPC path removed before gateway cutover")

    direct = {rpc: False for rpc in DIRECT_V2_RPCS}
    for path in APP.rglob("*.dart"):
        source = path.read_text(encoding="utf-8")
        for rpc in DIRECT_V2_RPCS:
            if rpc in source and ".rpc" in source:
                direct[rpc] = True
    missing = [rpc for rpc, present in direct.items() if not present]
    if missing:
        fail(f"partial Flutter cutover detected: {missing}")

    gates = external.get("gates", {})
    for gate_name in ("incident_response", "production_deployment"):
        gate = gates.get(gate_name, {})
        if gate.get("placeholder_only") is not True or gate.get("evidence_ref") is not None or gate.get("evidence_digest") is not None:
            fail(f"{gate_name} was promoted without dedicated evidence")

    for key, value in authority.get("launch_authority", {}).items():
        if value is not False:
            fail(f"Stage 27 gained launch authority: {key}")

    print("STUDENT_ACCESS_NETWORK_RATE_LIMIT_GUARD=PASS")
    print(f"CURRENT_STATE={state}")
    print("REMOTE_STAGE27_VERSION=20260820065403")
    print("VERIFICATION_INTERLOCK=REPO_ONLY" if state == PENDING_STATE else "VERIFICATION_INTERLOCK=REMOTE_VERIFIED")
    print("RAW_NETWORK_ORIGIN_PERSISTENCE=DENIED")
    print("CALLER_LIMIT_OVERRIDE=DENIED")
    print("PUBLIC_BRIDGE=SECURITY_INVOKER_SERVICE_ROLE_ONLY")
    print("DIRECT_V2_RPC_PATHS=5")
    print("EDGE_RATE_LIMIT_INTEGRATION=NOT_DEPLOYED")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
