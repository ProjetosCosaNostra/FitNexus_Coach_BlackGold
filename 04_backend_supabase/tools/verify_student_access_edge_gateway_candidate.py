from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
APP = ROOT / "03_app_flutter" / "fitnexus_app" / "lib"

AUTHORITY = BACKEND / "student_access_edge_gateway_authority.json"
RATE_AUTHORITY = BACKEND / "student_access_network_rate_limit_authority.json"
NETWORK_AUTHORITY = BACKEND / "student_access_network_origin_boundary.json"
LEDGER = BACKEND / "migration_ledger_authority.json"
EDGE = BACKEND / "functions" / "student-access-gateway" / "index.ts"

FAILURE_CLASSES = (
    "BGF-EDGE-RATE-LIMIT-ORDER-BYPASS-180",
    "BGF-EDGE-SECRET-MATERIAL-EXPOSURE-181",
    "BGF-EDGE-RAW-TOKEN-LOGGING-182",
    "BGF-EDGE-ACTION-RPC-MAPPING-DRIFT-183",
    "BGF-EDGE-CANDIDATE-DEPLOYMENT-SELF-ATTESTATION-184",
    "BGF-EDGE-LIVE-THRESHOLD-PROOF-GAP-185",
    "BGF-SYNTHETIC-SECURITY-PROOF-RESIDUE-186",
)

ROUTES = {
    "get_workout": "get_student_workout_v2",
    "start_workout": "start_student_workout_v2",
    "set_completion": "set_student_exercise_completion_v2",
    "get_feedback_context": "get_student_feedback_context_v2",
    "submit_feedback": "submit_student_workout_feedback_v2",
}


def fail(message: str) -> None:
    raise SystemExit("STUDENT_ACCESS_EDGE_GATEWAY_CANDIDATE_GUARD=FAIL\n" + message)


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
    rate = read_json(RATE_AUTHORITY)
    network = read_json(NETWORK_AUTHORITY)
    ledger = read_json(LEDGER)
    edge = read_text(EDGE)
    lower = edge.lower()

    if authority.get("schema_version") != 3:
        fail("authority schema_version must be 3 after exact threshold proof and cleanup")
    if authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("wrong Supabase project")
    if authority.get("failure_classes") != list(FAILURE_CLASSES):
        fail("failure-class authority drifted")
    if authority.get("current_state") != "EDGE_GATEWAY_V3_THRESHOLD_429_VERIFIED_SYNTHETIC_CLEANUP_COMPLETE_VALID_ROUTE_PROOF_PENDING":
        fail("Stage 28 final runtime state drifted")

    dependency = authority.get("stage27_dependency", {})
    if rate.get("current_state") not in dependency.get("accepted_states", []):
        fail("final Stage 27/28 rate-limit authority state is not accepted")
    if rate.get("migration", {}).get("remote_version") != "20260820065403":
        fail("Stage 27 durable migration version drifted")
    if rate.get("verification_migration", {}).get("remote_version") != "20260820070524":
        fail("Stage 27 verification migration version drifted")

    observed = authority.get("observed_deployed_runtime", {})
    expected_runtime = {
        "version": 3,
        "deployment_id": "2f85d9e1-39b3-46d7-a6c2-902eed7b4233",
        "bundle_sha256": "b57892b3f399b76f8127c9a39d3d8c021ffe639aa7bf92c7fa9a459d35721b82",
        "status": "ACTIVE",
        "verify_jwt": False,
        "candidate_source_deployed": True,
        "deployment_main_sha": "dfb0c3a81031ae3a13605be9c9fe969940f9878a",
        "student_rpc_forwarding_enabled_observed": True,
        "network_origin_rate_limit_enabled_observed": True,
    }
    for key, expected in expected_runtime.items():
        if observed.get(key) != expected:
            fail(f"deployed runtime receipt drift for {key}")

    if network.get("observed_runtime", {}).get("edge_function_version") != 3:
        fail("trusted-origin authority is not anchored to Edge runtime v3")
    if network.get("observed_runtime", {}).get("runtime_origin_candidate_trusted_for_security") is not True:
        fail("trusted cf-connecting-ip authority disappeared")

    runtime = authority.get("runtime_verification", {})
    required_true = (
        "candidate_deployed",
        "health_probe_verified",
        "network_origin_rate_limit_path_verified_live",
        "invalid_token_network_origin_rate_limit_threshold_verified_live",
        "student_rpc_forwarding_enabled_observed",
    )
    for key in required_true:
        if runtime.get(key) is not True:
            fail(f"missing Stage 28 runtime proof: {key}")
    if runtime.get("threshold_live_proof_workflow_run_id") != 32351032979:
        fail("threshold workflow receipt drifted")
    if runtime.get("threshold_operation") != "start_workout":
        fail("threshold operation drifted")
    if runtime.get("threshold_limit_per_minute") != 30:
        fail("threshold limit drifted")
    if runtime.get("allowed_calls_observed") != 30 or runtime.get("rate_limited_call_number") != 31:
        fail("exact threshold call counts drifted")
    if runtime.get("rate_limit_http_status") != 429 or runtime.get("rate_limit_error") != "STUDENT_NETWORK_RATE_LIMITED":
        fail(f"{FAILURE_CLASSES[5]} exact live HTTP 429 proof disappeared")
    if runtime.get("real_student_token_used") is not False or runtime.get("real_student_data_mutated") is not False:
        fail("threshold proof unexpectedly used real student material")
    if runtime.get("student_rpc_forwarding_with_valid_token_verified_live") is not False:
        fail("valid-token route proof was self-attested")
    if runtime.get("edge_alert_delivery_verified") is not False or runtime.get("rollback_verified") is not False:
        fail("alert/rollback proof was self-attested")

    cleanup = authority.get("synthetic_cleanup_receipt", {})
    expected_cleanup = {
        "failure_class": FAILURE_CLASSES[6],
        "migration_name": "stage28_threshold_proof_synthetic_cleanup",
        "remote_version": "20260820173521",
        "remote_applied": True,
        "expected_buckets_removed": 2,
        "expected_signals_removed": 2,
        "proof_buckets_remaining": 0,
        "proof_signals_remaining": 0,
        "anonymous_network_rate_limit_signals_remaining": 0,
        "raw_network_origin_stored_in_repository": False,
        "migration_ledger_state": "remote_reconciled",
    }
    for key, expected in expected_cleanup.items():
        if cleanup.get(key) != expected:
            fail(f"{FAILURE_CLASSES[6]} cleanup receipt drift for {key}")

    remote = {row.get("name"): row.get("version") for row in ledger.get("remote_migrations", [])}
    if remote.get("stage28_threshold_proof_synthetic_cleanup") != "20260820173521":
        fail("Stage 28 cleanup migration is not remotely reconciled")
    if any(
        row.get("direction") == "repo_only" and row.get("name") == "stage28_threshold_proof_synthetic_cleanup"
        for row in ledger.get("declared_divergences", [])
    ):
        fail("stale Stage 28 cleanup repo_only declaration remains")

    candidate = authority.get("candidate_contract", {})
    for key, expected in {
        "trusted_network_origin_header": "cf-connecting-ip",
        "rate_limit_before_student_rpc": True,
        "rate_limit_before_token_validation": True,
        "raw_network_origin_returned": False,
        "raw_network_origin_logged": False,
        "raw_possession_token_logged": False,
        "raw_request_body_logged": False,
        "upstream_error_body_echoed": False,
        "launch_gate_authority": False,
    }.items():
        if candidate.get(key) != expected:
            fail(f"gateway candidate contract drift for {key}")
    if authority.get("route_rpc_map") != ROUTES:
        fail(f"{FAILURE_CLASSES[3]} route-to-RPC map drifted")

    required_source = (
        'const RATE_LIMIT_RPC = "check_student_access_network_rate_limit_v1";',
        'req.headers.get("cf-connecting-ip")',
        'Deno.env.get("SUPABASE_SECRET_KEYS")',
        'if (req.method === "POST")',
        'raw_network_origin_returned: false',
        'network_origin_rate_limit_enabled: true',
        'student_rpc_forwarding_enabled: true',
    )
    missing_source = [fragment for fragment in required_source if fragment not in edge]
    if missing_source:
        fail(f"gateway source incomplete: {missing_source}")
    limiter_call = edge.find("const rateLimit = await callRpc")
    param_build = edge.find("const rpcParams = buildRpcParams")
    student_call = edge.find("const studentRpc = await callRpc")
    if min(limiter_call, param_build, student_call) < 0 or not (limiter_call < param_build < student_call):
        fail(f"{FAILURE_CLASSES[0]} limiter order drifted")
    if any(fragment in lower for fragment in ("console.log", "console.error", "console.warn", "console.info")):
        fail(f"{FAILURE_CLASSES[1]} Edge source can log sensitive material")

    client = authority.get("client_boundary", {})
    if client.get("flutter_uses_edge_gateway") is not False:
        fail("Flutter cutover self-attested")
    if client.get("direct_v2_rpc_path_active") is not True:
        fail("direct RPC fallback removed before valid-route proof/cutover")
    if client.get("direct_anon_v2_rpc_execute_revoked") is not False:
        fail("direct RPC privileges revoked before cutover")

    direct_calls = {rpc: 0 for rpc in ROUTES.values()}
    for path in APP.rglob("*.dart"):
        source = path.read_text(encoding="utf-8")
        for rpc in direct_calls:
            if f"'{rpc}'" in source:
                direct_calls[rpc] += 1
    missing_direct = [rpc for rpc, count in direct_calls.items() if count == 0]
    if missing_direct:
        fail(f"partial Flutter cutover detected: {missing_direct}")

    if any(value is not False for value in authority.get("launch_authority", {}).values()):
        fail("Stage 28 gained launch authority")

    print("STUDENT_ACCESS_EDGE_GATEWAY_CANDIDATE_GUARD=PASS")
    print("CURRENT_STATE=EDGE_GATEWAY_V3_THRESHOLD_429_VERIFIED_SYNTHETIC_CLEANUP_COMPLETE_VALID_ROUTE_PROOF_PENDING")
    print("EDGE_RUNTIME_VERSION=3")
    print("LIVE_PRETOKEN_LIMITER_PATH=VERIFIED")
    print("LIVE_THRESHOLD_429_PROOF=VERIFIED")
    print("SYNTHETIC_PROOF_RESIDUE=ZERO")
    print("VALID_STUDENT_ROUTE_PROOF=PENDING")
    print("FLUTTER_CUTOVER=false")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
