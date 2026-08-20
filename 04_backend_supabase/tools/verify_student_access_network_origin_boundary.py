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

DEPLOYMENT_ID = "2f85d9e1-39b3-46d7-a6c2-902eed7b4233"
DEPLOYMENT_BUNDLE_SHA256 = "6d67c45bdd23694bcfbe24503c84d1d0e7c540a43d7c54e104a376a7c2a18c5a"
SOURCE_MAIN_SHA = "0215cb417e0fafe659649d60a4d889b947d489cb"
SPOOF_SUCCESS_RUN_ID = 32338900002


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
    gateway_authority = read_json(GATEWAY_AUTHORITY)
    edge = read_text(EDGE)
    edge_lower = edge.lower()
    stage21 = read_text(STAGE21).lower()
    live = read_text(LIVE_PROBE)
    spoof_live = read_text(SPOOF_LIVE_PROBE)

    if authority.get("schema_version") != 4:
        fail("Stage 26 authority schema_version must remain 4 until runtime promotion")
    if authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("wrong Supabase project")
    if authority.get("failure_classes") != list(FAILURE_CLASSES):
        fail("failure-class authority drifted")
    if authority.get("current_state") != "ORIGIN_SOURCE_SPOOF_RESISTANCE_VERIFIED":
        fail("deployed runtime authority self-promoted")
    if authority.get("baseline_main_sha") != SOURCE_MAIN_SHA:
        fail("Stage 26 baseline authority drifted")

    runtime = authority.get("observed_runtime", {})
    expected_runtime = {
        "edge_function_name": "student-access-gateway",
        "edge_function_deployed": True,
        "observed_edge_function_count": 1,
        "edge_function_version": 2,
        "edge_function_status": "ACTIVE",
        "verify_jwt": False,
        "deployment_id": DEPLOYMENT_ID,
        "deployment_bundle_sha256": DEPLOYMENT_BUNDLE_SHA256,
        "runtime_origin_candidate_verified": True,
        "runtime_origin_candidate": "cf-connecting-ip",
        "runtime_origin_candidate_trusted_for_security": True,
    }
    for key, expected in expected_runtime.items():
        if runtime.get(key) != expected:
            fail(f"{FAILURE_CLASSES[4]} observed runtime drift for {key}")

    receipt = runtime.get("spoof_resistance_receipt", {})
    if receipt.get("workflow_run_id") != SPOOF_SUCCESS_RUN_ID:
        fail("spoof proof receipt drifted")
    if receipt.get("spoof_proof_outcome") != "BLOCKED_AT_EDGE_403":
        fail("spoof proof outcome drifted")
    if receipt.get("client_can_force_cf_connecting_ip") is not False:
        fail(f"{FAILURE_CLASSES[8]} client can force trusted origin")

    if spoof.get("state") != "SPOOF_RESISTANCE_VERIFIED_EDGE_BLOCK_403":
        fail("spoof authority is no longer verified")
    if spoof.get("current_runtime", {}).get("version") != 2:
        fail("observed spoof runtime version drifted before deployment promotion")

    # Stage 28 may implement a repository candidate while the authoritative deployed runtime
    # remains v2. Source capability is therefore checked separately from deployed evidence.
    if gateway_authority.get("current_state") != "REPOSITORY_GATEWAY_RATE_LIMIT_IMPLEMENTED_NOT_DEPLOYED":
        fail("Stage 28 repository candidate authority is missing or self-promoted")
    if gateway_authority.get("observed_deployed_runtime", {}).get("version") != 2:
        fail("Stage 28 candidate lost the observed v2 runtime anchor")
    if gateway_authority.get("runtime_verification", {}).get("candidate_deployed") is not False:
        fail(f"{FAILURE_CLASSES[6]} repository source was confused with runtime deployment")

    current = authority.get("current_client_boundary", {})
    if current.get("direct_v2_rpc_calls") != list(DIRECT_V2_RPCS):
        fail(f"{FAILURE_CLASSES[2]} direct-RPC inventory drifted")
    if current.get("anonymous_v2_rpc_execute_required_by_current_client") is not True:
        fail(f"{FAILURE_CLASSES[2]} direct RPC authority revoked before Flutter cutover")
    if current.get("network_origin_rate_limit_for_invalid_token") is not False:
        fail(f"{FAILURE_CLASSES[0]} live invalid-token throttle was self-attested")
    if current.get("edge_alert_delivery_verified") is not False:
        fail(f"{FAILURE_CLASSES[3]} alert delivery was self-attested")

    direct_calls = {rpc: 0 for rpc in DIRECT_V2_RPCS}
    for path in APP.rglob("*.dart"):
        text = path.read_text(encoding="utf-8")
        for rpc in direct_calls:
            if f"'{rpc}'" in text:
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
    absent_grants = [grant for grant in grants if grant not in stage21]
    if absent_grants:
        fail(f"{FAILURE_CLASSES[2]} privilege cutover occurred before Flutter cutover")

    required_source = (
        'const SPOOF_SENTINEL = "203.0.113.77";',
        'req.headers.get("cf-connecting-ip")',
        "candidate_equals_known_client_spoof_sentinel:",
        "cloudflareOrigin?.trim() === SPOOF_SENTINEL",
        "raw_network_origin_returned: false",
        "launch_gate_authority: false",
    )
    missing_source = [fragment for fragment in required_source if fragment not in edge]
    if missing_source:
        fail(f"trusted-origin source invariants missing: {missing_source}")
    if any(fragment in edge_lower for fragment in ("console.log", "console.error", "console.warn", "console.info")):
        fail(f"{FAILURE_CLASSES[9]} Edge source can log sensitive request material")

    if "EXPECTED_MODE = \"origin_probe_not_student_gateway_cutover\"" not in live:
        fail("live Stage 26 probe no longer anchors the deployed v2 runtime")
    if "UNTRUSTED_REGARDLESS_OF_NORMALIZATION" not in live:
        fail("client-forwarded-header distrust invariant disappeared")
    if 'SENTINEL = "203.0.113.77"' not in spoof_live or "BLOCKED_AT_EDGE_403" not in spoof_live:
        fail("live spoof proof source drifted")

    if any(value is not False for value in authority.get("launch_authority", {}).values()):
        fail("network-origin authority gained launch authority")

    print("STUDENT_ACCESS_NETWORK_ORIGIN_BOUNDARY_GUARD=PASS")
    print("OBSERVED_RUNTIME_VERSION=2")
    print("NETWORK_ORIGIN_SECURITY_TRUST=VERIFIED")
    print("SPOOF_PROOF_OUTCOME=BLOCKED_AT_EDGE_403")
    print("REPOSITORY_GATEWAY_CANDIDATE=IMPLEMENTED_NOT_DEPLOYED")
    print("DIRECT_V2_RPC_PATHS=5")
    print("FLUTTER_GATEWAY_CUTOVER=NOT_STARTED")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
