from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
APP = ROOT / "03_app_flutter" / "fitnexus_app" / "lib"
MIGRATION = BACKEND / "migrations" / "20260820063000_stage27_student_network_origin_rate_limit.sql"
VERIFY_MIGRATION = BACKEND / "migrations" / "20260820065900_stage27_network_rate_limit_verification_interlock.sql"
CLEANUP_MIGRATION = BACKEND / "migrations" / "20260820085600_stage28_threshold_proof_synthetic_cleanup.sql"
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
CLEANUP_FAILURE_CLASS = "BGF-SYNTHETIC-SECURITY-PROOF-RESIDUE-186"
FINAL_STATE = "DATABASE_AND_EDGE_THRESHOLD_VERIFIED_SYNTHETIC_CLEANUP_COMPLETE"
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


def main() -> None:
    authority = data(AUTHORITY)
    network = data(NETWORK_AUTHORITY)
    ledger = data(LEDGER)
    external = data(EXTERNAL_GATES)
    migration = text(MIGRATION).lower()
    verification = text(VERIFY_MIGRATION)
    cleanup_source = text(CLEANUP_MIGRATION)

    if authority.get("schema_version") != 3 or authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("Stage 27/28 authority identity drifted")
    if authority.get("failure_classes") != FAILURE_CLASSES:
        fail("Stage 27 failure classes drifted")
    if authority.get("verification_failure_class") != VERIFY_FAILURE_CLASS:
        fail("Stage 27 verification failure class drifted")
    if authority.get("runtime_threshold_proof_failure_class") != THRESHOLD_GAP_CLASS:
        fail("runtime threshold proof failure class drifted")
    if authority.get("synthetic_cleanup_failure_class") != CLEANUP_FAILURE_CLASS:
        fail("synthetic cleanup failure class drifted")
    if authority.get("current_state") != FINAL_STATE:
        fail("Stage 27/28 final rate-limit state drifted")

    if authority.get("migration", {}).get("remote_version") != "20260820065403":
        fail("Stage 27 durable migration receipt missing")
    if authority.get("verification_migration", {}).get("remote_version") != "20260820070524":
        fail("Stage 27 verification migration receipt missing")

    if network.get("observed_runtime", {}).get("edge_function_version") != 3:
        fail("trusted-origin authority not anchored to Edge v3")
    if network.get("observed_runtime", {}).get("runtime_origin_candidate_trusted_for_security") is not True:
        fail("trusted cf-connecting-ip authority disappeared")

    if authority.get("route_thresholds_per_minute") != THRESHOLDS:
        fail(f"{FAILURE_CLASSES[2]} threshold authority drifted")
    for operation, threshold in THRESHOLDS.items():
        if f"when '{operation}' then {threshold}" not in migration:
            fail(f"{FAILURE_CLASSES[2]} DB threshold missing for {operation}")
    if "p_limit" in migration or "limit_per_minute integer" in migration:
        fail(f"{FAILURE_CLASSES[2]} caller-supplied threshold appeared")

    db = authority.get("database_contract", {})
    required_db = {
        "public_bridge_security_mode": "SECURITY_INVOKER",
        "public_bridge_execute_role": "service_role",
        "caller_can_supply_limit": False,
        "raw_network_origin_persisted": False,
        "origin_digest_algorithm": "HMAC-SHA256",
        "pepper_stored_in_repository": False,
        "rate_limit_error": "STUDENT_NETWORK_RATE_LIMITED",
        "signal_type": "network_rate_limit_burst",
    }
    for key, expected in required_db.items():
        if db.get(key) != expected:
            fail(f"database contract drift for {key}")

    for fragment in (
        VERIFY_FAILURE_CLASS,
        "203.0.113.55",
        "for v_i in 1..121 loop",
        "STUDENT_NETWORK_RATE_LIMITED",
        "delete from private.student_access_security_signals",
        "delete from private.student_access_network_rate_buckets",
    ):
        if fragment not in verification:
            fail(f"Stage 27 verification interlock drifted: {fragment}")

    for fragment in (
        CLEANUP_FAILURE_CLASS,
        "STAGE28_SYNTHETIC_CLEANUP_SELECTOR_MISMATCH",
        "STAGE28_SYNTHETIC_CLEANUP_INCOMPLETE",
        "2026-08-20 08:53:00+00",
        "2026-08-20 08:54:00+00",
    ):
        if fragment not in cleanup_source:
            fail(f"{CLEANUP_FAILURE_CLASS} cleanup migration drifted: {fragment}")
    if "acc4dced" in cleanup_source.lower() or "cdbdc87f" in cleanup_source.lower():
        fail(f"{CLEANUP_FAILURE_CLASS} pseudonymous origin digest leaked into repository source")

    runtime = authority.get("runtime_boundary", {})
    for key in (
        "edge_gateway_uses_network_rate_limit",
        "network_origin_rate_limit_path_verified_live",
        "invalid_token_network_origin_rate_limit_threshold_verified_live",
    ):
        if runtime.get(key) is not True:
            fail(f"missing live rate-limit proof: {key}")
    if runtime.get("threshold_proof_workflow_run_id") != 32351032979:
        fail("threshold proof workflow receipt drifted")
    if runtime.get("threshold_operation") != "start_workout" or runtime.get("threshold_limit_per_minute") != 30:
        fail("threshold proof route/limit drifted")
    if runtime.get("allowed_calls_observed") != 30 or runtime.get("rate_limited_call_number") != 31:
        fail("threshold proof exact call counts drifted")
    if runtime.get("rate_limit_http_status") != 429 or runtime.get("rate_limit_error") != "STUDENT_NETWORK_RATE_LIMITED":
        fail(f"{THRESHOLD_GAP_CLASS} live HTTP 429 proof disappeared")

    cleanup = authority.get("synthetic_cleanup_receipt", {})
    expected_cleanup = {
        "migration_name": "stage28_threshold_proof_synthetic_cleanup",
        "remote_version": "20260820173521",
        "remote_applied": True,
        "expected_buckets_removed": 2,
        "expected_signals_removed": 2,
        "proof_buckets_remaining": 0,
        "proof_signals_remaining": 0,
        "anonymous_network_rate_limit_signals_remaining": 0,
        "migration_ledger_state": "remote_reconciled",
    }
    for key, expected in expected_cleanup.items():
        if cleanup.get(key) != expected:
            fail(f"{CLEANUP_FAILURE_CLASS} cleanup receipt drift for {key}")

    remote = {item.get("name"): item.get("version") for item in ledger.get("remote_migrations", [])}
    for name, version in {
        "stage27_student_network_origin_rate_limit": "20260820065403",
        "stage27_network_rate_limit_verification_interlock": "20260820070524",
        "stage28_threshold_proof_synthetic_cleanup": "20260820173521",
    }.items():
        if remote.get(name) != version:
            fail(f"migration ledger missing reconciled {name}")
    if any(row.get("direction") == "repo_only" for row in ledger.get("declared_divergences", [])):
        fail("unexpected repo_only divergence remains after Stage 28 reconciliation")

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

    if authority.get("proof_semantics", {}).get("valid_student_route_verified") is not False:
        fail("valid student route proof self-attested")
    if any(value is not False for value in authority.get("launch_authority", {}).values()):
        fail("Stage 27/28 gained launch authority")

    print("STUDENT_ACCESS_NETWORK_RATE_LIMIT_GUARD=PASS")
    print(f"CURRENT_STATE={FINAL_STATE}")
    print("REMOTE_STAGE27_VERSION=20260820065403")
    print("EDGE_RATE_LIMIT_PATH_LIVE=VERIFIED_PRE_TOKEN")
    print("EDGE_THRESHOLD_429_PROOF=VERIFIED")
    print("SYNTHETIC_PROOF_RESIDUE=ZERO")
    print("VALID_STUDENT_ROUTE_PROOF=PENDING")
    print("DIRECT_V2_RPC_PATHS=5")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
