from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
APP = ROOT / "03_app_flutter" / "fitnexus_app" / "lib"

AUTHORITY = BACKEND / "student_access_edge_gateway_authority.json"
RATE_AUTHORITY = BACKEND / "student_access_network_rate_limit_authority.json"
NETWORK_AUTHORITY = BACKEND / "student_access_network_origin_boundary.json"
EDGE = BACKEND / "functions" / "student-access-gateway" / "index.ts"

FAILURE_CLASSES = (
    "BGF-EDGE-RATE-LIMIT-ORDER-BYPASS-180",
    "BGF-EDGE-SECRET-MATERIAL-EXPOSURE-181",
    "BGF-EDGE-RAW-TOKEN-LOGGING-182",
    "BGF-EDGE-ACTION-RPC-MAPPING-DRIFT-183",
    "BGF-EDGE-CANDIDATE-DEPLOYMENT-SELF-ATTESTATION-184",
    "BGF-EDGE-LIVE-THRESHOLD-PROOF-GAP-185",
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
    edge = read_text(EDGE)
    lower = edge.lower()

    if authority.get("schema_version") != 2:
        fail("authority schema_version must be 2 after live deployment proof")
    if authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("wrong Supabase project")
    if authority.get("failure_classes") != list(FAILURE_CLASSES):
        fail("failure class authority drifted")
    if authority.get("current_state") != "EDGE_GATEWAY_V3_DEPLOYED_PRETOKEN_LIMITER_PATH_VERIFIED_THRESHOLD_PROOF_PENDING":
        fail("Stage 28 runtime state drifted")

    dependency = authority.get("stage27_dependency", {})
    if rate.get("current_state") not in dependency.get("accepted_states", []):
        fail(f"{FAILURE_CLASSES[0]} Stage 27 dependency state is not accepted")
    if rate.get("migration", {}).get("remote_version") != dependency.get("durable_migration_remote_version"):
        fail("Stage 27 durable migration version drifted")
    if rate.get("verification_migration", {}).get("remote_version") != dependency.get("verification_migration_remote_version"):
        fail("Stage 27 verification migration version drifted")
    if network.get("observed_runtime", {}).get("runtime_origin_candidate_trusted_for_security") is not True:
        fail("trusted cf-connecting-ip authority disappeared")

    candidate = authority.get("candidate_contract", {})
    required_candidate = {
        "verify_jwt": False,
        "trusted_network_origin_header": "cf-connecting-ip",
        "max_body_bytes": 16384,
        "rate_limit_bridge": "check_student_access_network_rate_limit_v1",
        "rate_limit_before_student_rpc": True,
        "rate_limit_before_token_validation": True,
        "secret_key_source_preferred": "SUPABASE_SECRET_KEYS.default",
        "legacy_secret_fallback": "SUPABASE_SERVICE_ROLE_KEY",
        "new_secret_key_uses_apikey_header_only": True,
        "legacy_service_role_uses_authorization_bearer": True,
        "raw_network_origin_returned": False,
        "raw_network_origin_logged": False,
        "raw_possession_token_logged": False,
        "raw_request_body_logged": False,
        "upstream_error_body_echoed": False,
        "launch_gate_authority": False,
    }
    for key, expected in required_candidate.items():
        if candidate.get(key) != expected:
            fail(f"candidate contract drift for {key}: {candidate.get(key)!r}")
    if candidate.get("allowed_methods") != ["GET", "POST", "OPTIONS"]:
        fail("gateway method contract drifted")
    if authority.get("route_rpc_map") != ROUTES:
        fail(f"{FAILURE_CLASSES[3]} route-to-RPC map drifted")

    observed = authority.get("observed_deployed_runtime", {})
    expected_runtime = {
        "version": 3,
        "deployment_id": "2f85d9e1-39b3-46d7-a6c2-902eed7b4233",
        "bundle_sha256": "b57892b3f399b76f8127c9a39d3d8c021ffe639aa7bf92c7fa9a459d35721b82",
        "status": "ACTIVE",
        "verify_jwt": False,
        "mode": "stage28_gateway_candidate_repository_source",
        "candidate_source_deployed": True,
        "deployment_main_sha": "dfb0c3a81031ae3a13605be9c9fe969940f9878a",
        "student_rpc_forwarding_enabled_observed": True,
        "network_origin_rate_limit_enabled_observed": True,
    }
    for key, expected in expected_runtime.items():
        if observed.get(key) != expected:
            fail(f"{FAILURE_CLASSES[4]} deployed runtime receipt drift for {key}")

    runtime = authority.get("runtime_verification", {})
    for key in (
        "candidate_deployed",
        "health_probe_verified",
        "network_origin_rate_limit_path_verified_live",
        "student_rpc_forwarding_enabled_observed",
    ):
        if runtime.get(key) is not True:
            fail(f"missing live runtime proof: {key}")
    if runtime.get("live_proof_workflow_run_id") != 32349938290:
        fail("live proof workflow receipt drifted")
    if runtime.get("live_proof_result") != "PASS":
        fail("live proof did not pass")
    if runtime.get("pre_token_limiter_proof_http_status") != 400:
        fail("pre-token limiter proof status drifted")
    if runtime.get("pre_token_limiter_proof_error") != "STUDENT_GATEWAY_PAYLOAD_INVALID":
        fail("pre-token limiter terminal boundary drifted")
    if runtime.get("spoof_attempt_http_status") != 403 or runtime.get("spoof_proof_outcome") != "BLOCKED_AT_EDGE_403":
        fail("runtime v3 spoof proof drifted")
    if runtime.get("real_student_token_used") is not False or runtime.get("real_student_data_mutated") is not False:
        fail("live proof unexpectedly used real student material")

    # BGF-EDGE-LIVE-THRESHOLD-PROOF-GAP-185: a successful allowed limiter call is not
    # equivalent to observing the actual 429 threshold-exceeded path.
    if runtime.get("invalid_token_network_origin_rate_limit_threshold_verified_live") is not False:
        fail(f"{FAILURE_CLASSES[5]} threshold proof was self-attested")
    if runtime.get("student_rpc_forwarding_with_valid_token_verified_live") is not False:
        fail("valid-token forwarding was self-attested")
    if runtime.get("edge_alert_delivery_verified") is not False or runtime.get("rollback_verified") is not False:
        fail("alert/rollback proof was self-attested")

    client = authority.get("client_boundary", {})
    if client.get("flutter_uses_edge_gateway") is not False:
        fail("Flutter cutover self-attested")
    if client.get("direct_v2_rpc_path_active") is not True:
        fail("direct RPC fallback removed before client cutover")
    if client.get("direct_anon_v2_rpc_execute_revoked") is not False:
        fail("direct RPC privileges revoked before cutover")

    required_source = (
        'const SPOOF_SENTINEL = "203.0.113.77";',
        'const MAX_BODY_BYTES = 16_384;',
        'const RATE_LIMIT_RPC = "check_student_access_network_rate_limit_v1";',
        'req.headers.get("cf-connecting-ip")',
        'Deno.env.get("SUPABASE_SECRET_KEYS")',
        'Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")',
        'secretKey.startsWith("sb_secret_")',
        'access-control-allow-methods": "GET, POST, OPTIONS"',
        'if (req.method === "POST")',
        'raw_network_origin_returned: false',
        'network_origin_rate_limit_enabled: true',
        'student_rpc_forwarding_enabled: true',
        'launch_gate_authority: false',
    )
    missing = [fragment for fragment in required_source if fragment not in edge]
    if missing:
        fail(f"gateway source incomplete: {missing}")

    for route, rpc in ROUTES.items():
        if f'{route}: "{rpc}"' not in edge:
            fail(f"{FAILURE_CLASSES[3]} missing mapping {route}->{rpc}")

    limiter_call = edge.find("const rateLimit = await callRpc")
    param_build = edge.find("const rpcParams = buildRpcParams")
    student_call = edge.find("const studentRpc = await callRpc")
    if min(limiter_call, param_build, student_call) < 0 or not (limiter_call < param_build < student_call):
        fail(f"{FAILURE_CLASSES[0]} limiter order drifted")
    if "p_network_origin: cloudflareOrigin!.trim()" not in edge or "p_operation: payload.action" not in edge:
        fail(f"{FAILURE_CLASSES[0]} limiter binding drifted")

    forbidden = (
        "console.log",
        "console.error",
        "console.warn",
        "console.info",
        "service_role_key=",
        "authorization: req.headers.get",
    )
    present = [fragment for fragment in forbidden if fragment.lower() in lower]
    if present:
        fail(f"{FAILURE_CLASSES[1]} unsafe source pattern present: {present}")

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
    print("CURRENT_STATE=EDGE_GATEWAY_V3_DEPLOYED_PRETOKEN_LIMITER_PATH_VERIFIED_THRESHOLD_PROOF_PENDING")
    print("EDGE_RUNTIME_VERSION=3")
    print("RATE_LIMIT_ORDER=BEFORE_TOKEN_VALIDATION_AND_STUDENT_RPC")
    print("LIVE_PRETOKEN_LIMITER_PATH=VERIFIED")
    print("LIVE_THRESHOLD_429_PROOF=PENDING")
    print("FLUTTER_CUTOVER=false")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
