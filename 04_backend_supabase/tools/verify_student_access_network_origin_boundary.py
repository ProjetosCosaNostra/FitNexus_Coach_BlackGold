from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
APP = ROOT / "03_app_flutter" / "fitnexus_app" / "lib"
MIGRATIONS = BACKEND / "migrations"

AUTHORITY = BACKEND / "student_access_network_origin_boundary.json"
SPOOF_AUTHORITY = BACKEND / "cf_origin_spoof_sentinel_authority.json"
STAGE21 = MIGRATIONS / "20260819103700_stage21_student_access_security_boundary.sql"
ABUSE_AUTHORITY = BACKEND / "student_access_abuse_authority.json"
EXTERNAL_GATES = BACKEND / "external_gate_evidence_placeholders.json"
GATEWAY_ENTRYPOINT = BACKEND / "functions" / "student-access-gateway" / "index.ts"
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
CANDIDATE_RUN_ID = 32337114801
SPOOF_FAILURE_RUN_ID = 32338828582
SPOOF_SUCCESS_RUN_ID = 32338900002


def fail(message: str) -> None:
    raise SystemExit("STUDENT_ACCESS_NETWORK_ORIGIN_BOUNDARY_GUARD=FAIL\n" + message)


def read_text(path: Path) -> str:
    if not path.is_file():
        fail(f"missing required source: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> dict:
    try:
        return json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path.relative_to(ROOT)}: {exc}")
    raise AssertionError("unreachable")


def require(text: str, fragments: tuple[str, ...], failure_class: str) -> None:
    missing = [fragment for fragment in fragments if fragment.lower() not in text.lower()]
    if missing:
        fail(f"{failure_class} missing invariants: {missing}")


def main() -> None:
    authority = read_json(AUTHORITY)
    spoof = read_json(SPOOF_AUTHORITY)
    stage21 = read_text(STAGE21).lower()
    abuse = read_json(ABUSE_AUTHORITY)
    external = read_json(EXTERNAL_GATES)
    gateway = read_text(GATEWAY_ENTRYPOINT)
    gateway_lower = gateway.lower()
    live_probe = read_text(LIVE_PROBE)
    live_probe_lower = live_probe.lower()
    spoof_live = read_text(SPOOF_LIVE_PROBE)
    spoof_live_lower = spoof_live.lower()

    if authority.get("schema_version") != 4:
        fail("Stage 26 network-origin authority schema_version must remain 4")
    if authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("wrong Supabase project authority")
    if authority.get("failure_classes") != list(FAILURE_CLASSES):
        fail("failure-class authority drifted")
    if authority.get("current_state") != "ORIGIN_SOURCE_SPOOF_RESISTANCE_VERIFIED":
        fail("verified network-origin state drifted")
    if authority.get("baseline_main_sha") != SOURCE_MAIN_SHA:
        fail("source-main authority drifted")

    runtime = authority.get("observed_runtime", {})
    exact_runtime = {
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
        "probe_repository_entrypoint_present": True,
    }
    for key, expected in exact_runtime.items():
        if runtime.get(key) != expected:
            fail(f"{FAILURE_CLASSES[4]} runtime drift for {key}: {runtime.get(key)!r}")

    source = str(runtime.get("source", ""))
    for marker in ("Supabase.deploy_edge_function", "Supabase.list_edge_functions", "GitHub Actions"):
        if marker not in source:
            fail(f"runtime evidence source missing {marker}")

    candidate_receipt = runtime.get("live_probe_receipt", {})
    if candidate_receipt.get("workflow_run_id") != CANDIDATE_RUN_ID:
        fail("candidate-availability receipt drifted")
    if candidate_receipt.get("baseline_candidate_available") is not True:
        fail("candidate availability is no longer evidenced")
    if candidate_receipt.get("raw_network_origin_observed") is not False:
        fail(f"{FAILURE_CLASSES[5]} candidate probe exposed raw origin")

    header_failure = runtime.get("live_probe_failure_receipt", {})
    if header_failure.get("failure_class") != "BGF-EDGE-HEADER-PRESENCE-ASSUMPTION-170":
        fail("forwarded-header normalization failure class was lost")

    spoof_receipt = runtime.get("spoof_resistance_receipt", {})
    expected_spoof = {
        "workflow_run_id": SPOOF_SUCCESS_RUN_ID,
        "check_name": "Live CF origin spoof sentinel",
        "sentinel_standard": "RFC5737_TEST_NET_3",
        "spoof_attempt_http_status": 403,
        "spoof_proof_outcome": "BLOCKED_AT_EDGE_403",
        "client_can_force_cf_connecting_ip": False,
        "raw_network_origin_observed": False,
        "raw_network_origin_persisted": False,
        "student_rpc_forwarding_observed": False,
        "launch_gate_authority_observed": False,
    }
    for key, expected in expected_spoof.items():
        if spoof_receipt.get(key) != expected:
            fail(f"{FAILURE_CLASSES[8]} spoof receipt drift for {key}: {spoof_receipt.get(key)!r}")

    verifier_failure = runtime.get("spoof_verifier_failure_receipt", {})
    if verifier_failure.get("workflow_run_id") != SPOOF_FAILURE_RUN_ID:
        fail(f"{FAILURE_CLASSES[10]} verifier failure receipt run drifted")
    if verifier_failure.get("failure_class") != FAILURE_CLASSES[10]:
        fail(f"{FAILURE_CLASSES[10]} verifier failure class drifted")
    if "403" not in str(verifier_failure.get("safe_finding", "")):
        fail(f"{FAILURE_CLASSES[10]} verifier failure finding lost edge-block evidence")

    if spoof.get("schema_version") != 2:
        fail("spoof authority schema_version must remain 2")
    if spoof.get("state") != "SPOOF_RESISTANCE_VERIFIED_EDGE_BLOCK_403":
        fail(f"{FAILURE_CLASSES[8]} spoof authority is not verified")
    spoof_runtime = spoof.get("current_runtime", {})
    for key, expected in {
        "version": 2,
        "deployment_id": DEPLOYMENT_ID,
        "bundle_sha256": DEPLOYMENT_BUNDLE_SHA256,
        "origin_candidate": "cf-connecting-ip",
        "origin_candidate_available": True,
        "origin_candidate_trusted_for_security": True,
        "spoof_resistance_verified": True,
    }.items():
        if spoof_runtime.get(key) != expected:
            fail(f"{FAILURE_CLASSES[8]} spoof runtime authority drift for {key}")
    if spoof.get("live_spoof_receipt", {}).get("workflow_run_id") != SPOOF_SUCCESS_RUN_ID:
        fail(f"{FAILURE_CLASSES[8]} spoof authority lost live receipt")

    probe = authority.get("probe_contract", {})
    expected_probe = {
        "mode": "origin_probe_not_student_gateway_cutover",
        "allowed_method": "GET",
        "candidate_header": "cf-connecting-ip",
        "returns_raw_ip": False,
        "logs_raw_ip": False,
        "reads_request_body": False,
        "forwards_student_rpc": False,
        "accepts_client_forwarded_header_as_authority": False,
        "launch_gate_authority": False,
    }
    for key, expected in expected_probe.items():
        if probe.get(key) != expected:
            fail(f"probe contract drift for {key}: {probe.get(key)!r}")

    current = authority.get("current_client_boundary", {})
    if current.get("direct_v2_rpc_calls") != list(DIRECT_V2_RPCS):
        fail(f"{FAILURE_CLASSES[2]} direct-RPC inventory drifted")
    if current.get("anonymous_v2_rpc_execute_required_by_current_client") is not True:
        fail(f"{FAILURE_CLASSES[2]} direct privilege was revoked before client cutover")
    if current.get("network_origin_rate_limit_for_invalid_token") is not False:
        fail(f"{FAILURE_CLASSES[0]} invalid-token throttle was self-attested")
    if current.get("edge_alert_delivery_verified") is not False:
        fail(f"{FAILURE_CLASSES[3]} alert delivery was self-attested")

    target = authority.get("target_cutover_invariants", {})
    required_true = (
        "single_student_gateway",
        "network_origin_must_come_from_trusted_runtime_metadata",
        "client_supplied_forwarded_headers_must_not_be_trusted",
        "client_forwarded_header_presence_must_not_be_required",
        "invalid_token_attempts_rate_limited_by_network_origin_and_route",
        "valid_token_database_rate_limits_remain_active",
        "raw_possession_token_logging_forbidden",
        "arbitrary_request_payload_logging_forbidden",
        "direct_anon_v2_rpc_execute_revoked_after_verified_cutover",
        "client_direct_rpc_fallback_forbidden_after_verified_cutover",
        "alert_delivery_requires_real_runtime_receipt",
        "rollback_requires_real_runtime_receipt",
    )
    missing_targets = [key for key in required_true if target.get(key) is not True]
    if missing_targets:
        fail(f"target cutover invariants weakened: {missing_targets}")

    blind_spot = abuse.get("known_external_boundary", {}).get("blind_spot", "").lower()
    if "invalid-token" not in blind_spot or "client ip" not in blind_spot:
        fail(f"{FAILURE_CLASSES[0]} Stage 24 blind spot disappeared before throttle implementation")

    direct_calls: dict[str, list[str]] = {rpc: [] for rpc in DIRECT_V2_RPCS}
    for path in APP.rglob("*.dart"):
        text = path.read_text(encoding="utf-8")
        for rpc in DIRECT_V2_RPCS:
            if f".rpc(\n      '{rpc}'" in text or f".rpc('{rpc}'" in text:
                direct_calls[rpc].append(path.relative_to(ROOT).as_posix())
    missing_calls = [rpc for rpc, paths in direct_calls.items() if not paths]
    if missing_calls:
        fail(f"{FAILURE_CLASSES[2]} partial Flutter cutover detected: {missing_calls}")

    expected_grants = (
        "grant execute on function public.get_student_workout_v2(text) to anon, authenticated;",
        "grant execute on function public.start_student_workout_v2(text,text) to anon, authenticated;",
        "grant execute on function public.set_student_exercise_completion_v2(text,uuid,uuid,boolean,text) to anon, authenticated;",
        "grant execute on function public.get_student_feedback_context_v2(text) to anon, authenticated;",
        "grant execute on function public.submit_student_workout_feedback_v2(text,uuid,integer,integer,integer,text,text,text) to anon, authenticated;",
    )
    missing_grants = [grant for grant in expected_grants if grant not in stage21]
    if missing_grants:
        fail(f"{FAILURE_CLASSES[2]} privilege cutover occurred before Flutter gateway cutover")

    require(
        gateway,
        (
            'const SPOOF_SENTINEL = "203.0.113.77";',
            'req.headers.get("cf-connecting-ip")',
            "candidate_equals_known_client_spoof_sentinel:",
            "cloudflareOrigin?.trim() === SPOOF_SENTINEL",
            "raw_network_origin_returned: false",
            "request_body_read: false",
            "student_rpc_forwarding_enabled: false",
            "launch_gate_authority: false",
        ),
        FAILURE_CLASSES[8],
    )
    forbidden_gateway = (
        "console.log",
        "console.error",
        "req.json(",
        "req.text(",
        "supabase_service_role_key",
        "/rest/v1/rpc/",
        "get_student_workout_v2",
        "start_student_workout_v2",
        "set_student_exercise_completion_v2",
        "get_student_feedback_context_v2",
        "submit_student_workout_feedback_v2",
    )
    leaked = [fragment for fragment in forbidden_gateway if fragment in gateway_lower]
    if leaked:
        fail(f"{FAILURE_CLASSES[9]} gateway probe gained forbidden behavior: {leaked}")

    require(
        live_probe,
        (
            "https://mceukeondizkwlpfxzgf.supabase.co/functions/v1/student-access-gateway",
            'EXPECTED_CANDIDATE = "cf-connecting-ip"',
            '"network_origin_candidate_available": True',
            "UNTRUSTED_REGARDLESS_OF_NORMALIZATION",
        ),
        FAILURE_CLASSES[4],
    )
    require(
        spoof_live,
        (
            'SENTINEL = "203.0.113.77"',
            'allow_edge_block=True',
            "exc.code == 403",
            'outcome = "BLOCKED_AT_EDGE_403"',
            'CLIENT_CAN_FORCE_CF_CONNECTING_IP=false',
            'RAW_RUNTIME_ORIGIN_RETURNED=false',
        ),
        FAILURE_CLASSES[10],
    )
    forbidden_live = (
        "print(raw",
        "print(value",
        "print(response",
        "print(headers",
        "supabase_service_role_key",
    )
    unsafe_live = [fragment for fragment in forbidden_live if fragment in live_probe_lower or fragment in spoof_live_lower]
    if unsafe_live:
        fail(f"{FAILURE_CLASSES[9]} live probes could disclose raw request/response material: {unsafe_live}")

    gates = external.get("gates", {})
    for gate_name in ("incident_response", "production_deployment"):
        gate = gates.get(gate_name, {})
        if gate.get("placeholder_only") is not True:
            fail(f"{FAILURE_CLASSES[3]} {gate_name} was promoted without dedicated evidence")
        if gate.get("evidence_ref") is not None or gate.get("evidence_digest") is not None:
            fail(f"{FAILURE_CLASSES[3]} {gate_name} contains fabricated evidence")

    launch = authority.get("launch_authority", {})
    if any(value is not False for value in launch.values()):
        fail(f"{FAILURE_CLASSES[3]} network-origin proof gained launch authority")
    if any(value is not False for value in spoof.get("launch_authority", {}).values()):
        fail(f"{FAILURE_CLASSES[3]} spoof proof gained launch authority")

    preconditions = authority.get("promotion_preconditions")
    if not isinstance(preconditions, list) or len(preconditions) < 10:
        fail(f"{FAILURE_CLASSES[2]} remaining cutover preconditions are incomplete")

    print("STUDENT_ACCESS_NETWORK_ORIGIN_BOUNDARY_GUARD=PASS")
    print("CURRENT_EDGE_STATE=ORIGIN_SOURCE_SPOOF_RESISTANCE_VERIFIED")
    print("OBSERVED_EDGE_FUNCTION_COUNT=1")
    print("EDGE_FUNCTION_VERSION=2")
    print("NETWORK_ORIGIN_CANDIDATE=cf-connecting-ip")
    print("NETWORK_ORIGIN_SECURITY_TRUST=VERIFIED")
    print("SPOOF_PROOF_OUTCOME=BLOCKED_AT_EDGE_403")
    print("DIRECT_V2_RPC_PATHS=5")
    print("INVALID_TOKEN_NETWORK_ORIGIN_RATE_LIMIT=NOT_IMPLEMENTED")
    print("FLUTTER_GATEWAY_CUTOVER=NOT_STARTED")
    print("INCIDENT_RESPONSE_GATE_PROMOTION=DENIED")
    print("PRODUCTION_DEPLOYMENT_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
