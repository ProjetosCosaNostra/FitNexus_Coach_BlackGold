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
THRESHOLD_GAP_CLASS = "BGF-EDGE-LIVE-THRESHOLD-PROOF-GAP-185"
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
VERIFIED_STATE = "DATABASE_RATE_LIMIT_APPLIED_VERIFIED_EDGE_PATH_LIVE_THRESHOLD_PROOF_PENDING"


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

    if authority.get("schema_version") != 2 or authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("Stage 27/28 authority identity drifted")
    if authority.get("failure_classes") != FAILURE_CLASSES:
        fail("Stage 27 failure-class authority drifted")
    if authority.get("verification_failure_class") != VERIFY_FAILURE_CLASS:
        fail("Stage 27 verification failure class drifted")
    if authority.get("runtime_threshold_proof_failure_class") != THRESHOLD_GAP_CLASS:
        fail("runtime threshold proof gap class drifted")
    if authority.get("current_state") != VERIFIED_STATE:
        fail("Stage 27/28 runtime state drifted")

    migration_auth = authority.get("migration", {})
    if migration_auth.get("migration_name") != "stage27_student_network_origin_rate_limit":
        fail("Stage 27 migration name drifted")
    if migration_auth.get("remote_applied") is not True or migration_auth.get("remote_version") != "20260820065403":
        fail("Stage 27 remote migration receipt is missing")

    verify_auth = authority.get("verification_migration", {})
    if verify_auth.get("remote_applied") is not True or verify_auth.get("remote_version") != "20260820070524":
        fail("verification migration receipt missing")
    expected_verify = {
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
            fail(f"verification authority drift for {key}")

    trusted = authority.get("trusted_origin_authority", {})
    expected_trusted = {
        "source": "cf-connecting-ip",
        "source_state": "ORIGIN_SOURCE_SPOOF_RESISTANCE_VERIFIED",
        "edge_function_version": 3,
        "edge_function_bundle_sha256": "b57892b3f399b76f8127c9a39d3d8c021ffe639aa7bf92c7fa9a459d35721b82",
        "spoof_proof_workflow_run_id": 32349938290,
        "spoof_proof_outcome": "BLOCKED_AT_EDGE_403",
        "client_can_force_source": False,
    }
    if trusted != expected_trusted:
        fail(f"{FAILURE_CLASSES[0]} trusted-origin authority drifted")

    observed = network.get("observed_runtime", {})
    if network.get("current_state") != "ORIGIN_SOURCE_SPOOF_RESISTANCE_VERIFIED":
        fail("origin trust state drifted")
    if observed.get("edge_function_version") != 3:
        fail("network authority is not anchored to runtime v3")
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
            fail(f"database contract drift for {key}")

    require(
        migration,
        (
            "create table if not exists private.student_access_network_origin_secret",
            "extensions.gen_random_bytes(32)",
            "create table if not exists private.student_access_network_rate_buckets",
            "extensions.hmac(",
            "create or replace function public.check_student_access_network_rate_limit_v1(",
            "security invoker",
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

    require(
        verification,
        (
            VERIFY_FAILURE_CLASS,
            "203.0.113.55",
            "for v_i in 1..121 loop",
            "STUDENT_NETWORK_RATE_LIMITED",
            "delete from private.student_access_security_signals",
            "delete from private.student_access_network_rate_buckets",
            "STAGE27_VERIFY_SYNTHETIC_CLEANUP_FAILED",
        ),
        VERIFY_FAILURE_CLASS,
    )

    remote_names = {item.get("name") for item in ledger.get("remote_migrations", [])}
    for name in (
        "stage27_student_network_origin_rate_limit",
        "stage27_network_rate_limit_verification_interlock",
    ):
        if name not in remote_names:
            fail(f"migration ledger missing {name}")

    runtime = authority.get("runtime_boundary", {})
    if runtime.get("edge_gateway_uses_network_rate_limit") is not True:
        fail("live Edge limiter path was lost")
    if runtime.get("network_origin_rate_limit_path_verified_live") is not True:
        fail("pre-token limiter path proof missing")
    if runtime.get("live_path_proof_workflow_run_id") != 32349938290:
        fail("live path proof workflow receipt drifted")
    if runtime.get("live_path_proof_http_status") != 400 or runtime.get("live_path_proof_terminal_error") != "STUDENT_GATEWAY_PAYLOAD_INVALID":
        fail("live pre-token path terminal boundary drifted")
    if runtime.get("invalid_token_network_origin_rate_limit_threshold_verified_live") is not False:
        fail(f"{THRESHOLD_GAP_CLASS} threshold-exceeded runtime proof was self-attested")
    for key in (
        "flutter_uses_edge_gateway",
        "direct_anon_v2_rpc_execute_revoked",
        "edge_alert_delivery_verified",
        "rollback_verified",
    ):
        if runtime.get(key) is not False:
            fail(f"runtime state self-promoted: {key}")
    if runtime.get("direct_v2_rpc_path_active") is not True:
        fail("direct v2 RPC path removed before Flutter cutover")

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

    if any(value is not False for value in authority.get("launch_authority", {}).values()):
        fail("Stage 27/28 gained launch authority")

    print("STUDENT_ACCESS_NETWORK_RATE_LIMIT_GUARD=PASS")
    print("CURRENT_STATE=DATABASE_RATE_LIMIT_APPLIED_VERIFIED_EDGE_PATH_LIVE_THRESHOLD_PROOF_PENDING")
    print("REMOTE_STAGE27_VERSION=20260820065403")
    print("EDGE_RATE_LIMIT_PATH_LIVE=VERIFIED_PRE_TOKEN")
    print("EDGE_THRESHOLD_429_PROOF=PENDING")
    print("DIRECT_V2_RPC_PATHS=5")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
