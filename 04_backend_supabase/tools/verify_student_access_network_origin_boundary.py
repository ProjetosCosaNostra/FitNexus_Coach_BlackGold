from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
APP = ROOT / "03_app_flutter" / "fitnexus_app" / "lib"
MIGRATIONS = BACKEND / "migrations"

AUTHORITY = BACKEND / "student_access_network_origin_boundary.json"
SPOOF_AUTHORITY = BACKEND / "cf_origin_spoof_sentinel_authority.json"
GATEWAY_AUTHORITY = BACKEND / "student_access_edge_gateway_authority.json"
STAGE21 = MIGRATIONS / "20260819103700_stage21_student_access_security_boundary.sql"
EDGE = BACKEND / "functions" / "student-access-gateway" / "index.ts"
LIVE_PROBE = BACKEND / "tools" / "verify_student_access_edge_probe_live.py"
SPOOF_LIVE_PROBE = BACKEND / "tools" / "verify_cf_origin_spoof_sentinel_live.py"

FAILURE_CLASSES = (
    "BGF-NETWORK-ORIGIN-ABUSE-BYPASS-163",
    "BGF-EDGE-ORIGIN-TRUST-164",
    "BGF-STUDENT-ACCESS-PARTIAL-EDGE-CUTOVER-165",
    "BGF-ALERT-DELIVERY-SELF-ATTESTATION-166",
    "BGF-EDGE-RUNTIME-ORIGIN-ASSUMPTION-167",
    "BGF-EDGE-PROBE-DATA-LEAK-168",
    "BGF-EDGE-PROBE-PREMATURE-CUTOVER-169",
    "BGF-EDGE-HEADER-PRESENCE-ASSUMPTION-170",
    "BGF-CF-ORIGIN-SPOOF-171",
    "BGF-EDGE-SENTINEL-DATA-LEAK-172",
    "BGF-CF-SPOOF-PROOF-OUTCOME-ASSUMPTION-173",
)

DIRECT_V2_RPCS = (
    "get_student_workout_v2",
    "start_student_workout_v2",
    "set_student_exercise_completion_v2",
    "get_student_feedback_context_v2",
    "submit_student_workout_feedback_v2",
)


def fail(message: str) -> None:
    raise SystemExit("STUDENT_ACCESS_NETWORK_ORIGIN_BOUNDARY_GUARD=FAIL\n" + message)


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
    spoof = read_json(SPOOF_AUTHORITY)
    gateway = read_json(GATEWAY_AUTHORITY)
    edge = read_text(EDGE)
    lower = edge.lower()
    stage21 = read_text(STAGE21).lower()
    live = read_text(LIVE_PROBE)
    spoof_live = read_text(SPOOF_LIVE_PROBE)

    if authority.get("schema_version") != 5:
        fail("network-origin authority schema_version must be 5")
    if authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("wrong Supabase project")
    if authority.get("failure_classes") != list(FAILURE_CLASSES):
        fail("failure-class authority drifted")
    if authority.get("current_state") != "ORIGIN_SOURCE_SPOOF_RESISTANCE_AND_EDGE_THRESHOLD_VERIFIED":
        fail("network-origin final Stage 28 state drifted")

    runtime = authority.get("observed_runtime", {})
    expected_runtime = {
        "edge_function_name": "student-access-gateway",
        "edge_function_deployed": True,
        "observed_edge_function_count": 1,
        "edge_function_version": 3,
        "edge_function_status": "ACTIVE",
        "verify_jwt": False,
        "deployment_id": "2f85d9e1-39b3-46d7-a6c2-902eed7b4233",
        "deployment_bundle_sha256": "b57892b3f399b76f8127c9a39d3d8c021ffe639aa7bf92c7fa9a459d35721b82",
        "runtime_mode": "stage28_gateway_candidate_repository_source",
        "runtime_origin_candidate_verified": True,
        "runtime_origin_candidate": "cf-connecting-ip",
        "runtime_origin_candidate_trusted_for_security": True,
    }
    for key, expected in expected_runtime.items():
        if runtime.get(key) != expected:
            fail(f"{FAILURE_CLASSES[4]} observed runtime drift for {key}")

    spoof_receipt = runtime.get("spoof_resistance_receipt", {})
    if spoof_receipt.get("workflow_run_id") != 32349938290:
        fail("runtime v3 spoof receipt drifted")
    if spoof_receipt.get("spoof_attempt_http_status") != 403 or spoof_receipt.get("spoof_proof_outcome") != "BLOCKED_AT_EDGE_403":
        fail("runtime v3 spoof outcome drifted")
    if spoof_receipt.get("client_can_force_cf_connecting_ip") is not False:
        fail(f"{FAILURE_CLASSES[8]} client can force trusted origin")

    live_receipt = runtime.get("stage28_gateway_live_receipt", {})
    if live_receipt.get("pre_token_workflow_run_id") != 32349938290:
        fail("pre-token live proof receipt drifted")
    if live_receipt.get("network_origin_rate_limit_path_verified_live") is not True:
        fail(f"{FAILURE_CLASSES[0]} pre-token limiter path proof missing")
    if live_receipt.get("threshold_workflow_run_id") != 32351032979:
        fail("threshold workflow receipt drifted")
    if live_receipt.get("threshold_exceeded_http_429_verified_live") is not True:
        fail("live threshold HTTP 429 proof missing")
    if live_receipt.get("threshold_operation") != "start_workout" or live_receipt.get("threshold_limit_per_minute") != 30:
        fail("threshold route/limit drifted")
    if live_receipt.get("allowed_calls_observed") != 30 or live_receipt.get("rate_limited_call_number") != 31:
        fail("threshold exact call counts drifted")
    if live_receipt.get("rate_limit_http_status") != 429 or live_receipt.get("rate_limit_error") != "STUDENT_NETWORK_RATE_LIMITED":
        fail("threshold terminal outcome drifted")
    if live_receipt.get("real_student_token_used") is not False or live_receipt.get("real_student_data_mutated") is not False:
        fail("threshold proof unexpectedly used real student material")

    cleanup = runtime.get("synthetic_cleanup_receipt", {})
    if cleanup.get("remote_version") != "20260820173521":
        fail("Stage 28 cleanup remote version drifted")
    if cleanup.get("proof_buckets_remaining") != 0 or cleanup.get("proof_signals_remaining") != 0:
        fail("Stage 28 proof residue remains")
    if cleanup.get("anonymous_network_rate_limit_signals_remaining") != 0:
        fail("anonymous network-rate-limit signal residue remains")

    if spoof.get("state") != "SPOOF_RESISTANCE_VERIFIED_EDGE_BLOCK_403":
        fail("spoof authority is no longer verified")
    spoof_runtime = spoof.get("current_runtime", {})
    if spoof_runtime.get("version") != 3 or spoof_runtime.get("bundle_sha256") != expected_runtime["deployment_bundle_sha256"]:
        fail("spoof authority is not anchored to runtime v3")

    if gateway.get("current_state") != "EDGE_GATEWAY_V3_THRESHOLD_429_VERIFIED_SYNTHETIC_CLEANUP_COMPLETE_VALID_ROUTE_PROOF_PENDING":
        fail("Stage 28 gateway authority state drifted")
    gv = gateway.get("runtime_verification", {})
    if gv.get("candidate_deployed") is not True or gv.get("network_origin_rate_limit_path_verified_live") is not True:
        fail("gateway live deployment evidence missing")
    if gv.get("invalid_token_network_origin_rate_limit_threshold_verified_live") is not True:
        fail("gateway threshold proof missing")
    if gv.get("student_rpc_forwarding_with_valid_token_verified_live") is not False:
        fail("valid-token forwarding was self-attested")

    current = authority.get("current_client_boundary", {})
    if current.get("direct_v2_rpc_calls") != list(DIRECT_V2_RPCS):
        fail(f"{FAILURE_CLASSES[2]} direct-RPC inventory drifted")
    if current.get("anonymous_v2_rpc_execute_required_by_current_client") is not True:
        fail(f"{FAILURE_CLASSES[2]} direct RPC authority revoked before Flutter cutover")
    if current.get("network_origin_rate_limit_path_verified_live") is not True:
        fail("current client boundary lost live limiter path proof")
    if current.get("network_origin_rate_limit_for_invalid_token") is not True:
        fail("verified invalid-token threshold enforcement disappeared")
    if current.get("valid_student_route_verified_live") is not False:
        fail("valid student route proof self-attested")
    if current.get("edge_alert_delivery_verified") is not False:
        fail(f"{FAILURE_CLASSES[3]} alert delivery was self-attested")

    direct_calls = {rpc: 0 for rpc in DIRECT_V2_RPCS}
    for path in APP.rglob("*.dart"):
        source = path.read_text(encoding="utf-8")
        for rpc in direct_calls:
            if f"'{rpc}'" in source:
                direct_calls[rpc] += 1
    missing = [rpc for rpc, count in direct_calls.items() if count == 0]
    if missing:
        fail(f"{FAILURE_CLASSES[2]} partial Flutter cutover detected: {missing}")

    grants = (
        "grant execute on function public.get_student_workout_v2(text) to anon, authenticated;",
        "grant execute on function public.start_student_workout_v2(text,text) to anon, authenticated;",
        "grant execute on function public.set_student_exercise_completion_v2(text,uuid,uuid,boolean,text) to anon, authenticated;",
        "grant execute on function public.get_student_feedback_context_v2(text) to anon, authenticated;",
        "grant execute on function public.submit_student_workout_feedback_v2(text,uuid,integer,integer,integer,text,text,text) to anon, authenticated;",
    )
    absent = [grant for grant in grants if grant not in stage21]
    if absent:
        fail(f"{FAILURE_CLASSES[2]} privilege cutover occurred before Flutter cutover")

    required_source = (
        'const SPOOF_SENTINEL = "203.0.113.77";',
        'const RATE_LIMIT_RPC = "check_student_access_network_rate_limit_v1";',
        'req.headers.get("cf-connecting-ip")',
        "candidate_equals_known_client_spoof_sentinel:",
        "raw_network_origin_returned: false",
        "network_origin_rate_limit_enabled: true",
        "student_rpc_forwarding_enabled: true",
        "launch_gate_authority: false",
    )
    missing_source = [fragment for fragment in required_source if fragment not in edge]
    if missing_source:
        fail(f"trusted-origin source invariants missing: {missing_source}")
    if any(fragment in lower for fragment in ("console.log", "console.error", "console.warn", "console.info")):
        fail(f"{FAILURE_CLASSES[9]} Edge source can log sensitive request material")

    if 'EXPECTED_MODE = "stage28_gateway_candidate_repository_source"' not in live:
        fail("live origin probe is not anchored to runtime v3")
    if "UNTRUSTED_REGARDLESS_OF_NORMALIZATION" not in live:
        fail("client-forwarded-header distrust invariant disappeared")
    if 'SENTINEL = "203.0.113.77"' not in spoof_live or "RUNTIME_VERSION_EXPECTED=3" not in spoof_live:
        fail("live spoof verifier is not anchored to runtime v3")

    if any(value is not False for value in authority.get("launch_authority", {}).values()):
        fail("network-origin authority gained launch authority")

    print("STUDENT_ACCESS_NETWORK_ORIGIN_BOUNDARY_GUARD=PASS")
    print("OBSERVED_RUNTIME_VERSION=3")
    print("NETWORK_ORIGIN_SECURITY_TRUST=VERIFIED")
    print("SPOOF_PROOF_OUTCOME=BLOCKED_AT_EDGE_403")
    print("LIVE_PRETOKEN_LIMITER_PATH=VERIFIED")
    print("LIVE_THRESHOLD_429_PROOF=VERIFIED")
    print("SYNTHETIC_PROOF_RESIDUE=ZERO")
    print("VALID_STUDENT_ROUTE_PROOF=PENDING")
    print("DIRECT_V2_RPC_PATHS=5")
    print("FLUTTER_GATEWAY_CUTOVER=NOT_STARTED")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
