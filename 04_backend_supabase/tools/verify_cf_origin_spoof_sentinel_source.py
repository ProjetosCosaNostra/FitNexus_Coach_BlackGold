from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "cf_origin_spoof_sentinel_authority.json"
NETWORK_AUTHORITY = BACKEND / "student_access_network_origin_boundary.json"
GATEWAY_AUTHORITY = BACKEND / "student_access_edge_gateway_authority.json"
EDGE = BACKEND / "functions" / "student-access-gateway" / "index.ts"
LIVE = BACKEND / "tools" / "verify_cf_origin_spoof_sentinel_live.py"

FAILURE_CLASSES = (
    "BGF-CF-ORIGIN-SPOOF-171",
    "BGF-EDGE-SENTINEL-DATA-LEAK-172",
    "BGF-CF-SPOOF-PROOF-OUTCOME-ASSUMPTION-173",
)
SENTINEL = "203.0.113.77"


def fail(message: str) -> None:
    raise SystemExit("CF_ORIGIN_SPOOF_SENTINEL_AUTHORITY_GUARD=FAIL\n" + message)


def read_json(path: Path) -> dict:
    if not path.is_file():
        fail(f"missing authority: {path.relative_to(ROOT)}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path.relative_to(ROOT)}: {exc}")
    raise AssertionError("unreachable")


def main() -> None:
    authority = read_json(AUTHORITY)
    network = read_json(NETWORK_AUTHORITY)
    gateway = read_json(GATEWAY_AUTHORITY)
    if not EDGE.is_file() or not LIVE.is_file():
        fail("required Edge/live source missing")
    edge = EDGE.read_text(encoding="utf-8")
    lower = edge.lower()
    live = LIVE.read_text(encoding="utf-8")

    if authority.get("schema_version") != 2:
        fail("spoof authority schema_version drifted")
    if authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("wrong Supabase project")
    if authority.get("failure_classes") != list(FAILURE_CLASSES):
        fail("failure classes drifted")
    if authority.get("state") != "SPOOF_RESISTANCE_VERIFIED_EDGE_BLOCK_403":
        fail("spoof authority is no longer verified")
    if authority.get("source_main_sha") != "dfb0c3a81031ae3a13605be9c9fe969940f9878a":
        fail("runtime v3 source-main authority drifted")

    runtime = authority.get("current_runtime", {})
    expected = {
        "edge_function_name": "student-access-gateway",
        "version": 3,
        "deployment_id": "2f85d9e1-39b3-46d7-a6c2-902eed7b4233",
        "bundle_sha256": "b57892b3f399b76f8127c9a39d3d8c021ffe639aa7bf92c7fa9a459d35721b82",
        "status": "ACTIVE",
        "verify_jwt": False,
        "deployed_source_main_sha": "dfb0c3a81031ae3a13605be9c9fe969940f9878a",
        "origin_candidate": "cf-connecting-ip",
        "origin_candidate_available": True,
        "origin_candidate_trusted_for_security": True,
        "spoof_resistance_verified": True,
    }
    for key, value in expected.items():
        if runtime.get(key) != value:
            fail(f"observed runtime drift for {key}")

    contract = authority.get("sentinel_contract", {})
    expected_contract = {
        "sentinel": SENTINEL,
        "sentinel_standard": "RFC5737_TEST_NET_3",
        "response_field": "candidate_equals_known_client_spoof_sentinel",
        "response_is_boolean_only": True,
        "raw_runtime_origin_returned": False,
        "raw_runtime_origin_logged": False,
        "raw_runtime_origin_persisted": False,
        "student_rpc_forwarding_enabled": True,
        "network_origin_rate_limit_enabled": True,
        "launch_gate_authority": False,
    }
    for key, expected_value in expected_contract.items():
        if contract.get(key) != expected_value:
            fail(f"sentinel contract drift for {key}")

    receipt = authority.get("live_spoof_receipt", {})
    if receipt.get("workflow_run_id") != 32349938290:
        fail("live runtime v3 spoof receipt run drifted")
    if receipt.get("baseline_http_status") != 200 or receipt.get("spoof_attempt_http_status") != 403:
        fail("runtime v3 spoof HTTP evidence drifted")
    if receipt.get("spoof_proof_outcome") != "BLOCKED_AT_EDGE_403":
        fail("runtime v3 spoof proof outcome drifted")
    if receipt.get("client_can_force_cf_connecting_ip") is not False:
        fail(f"{FAILURE_CLASSES[0]} client can force cf-connecting-ip")
    if receipt.get("raw_runtime_origin_returned") is not False:
        fail(f"{FAILURE_CLASSES[1]} raw runtime origin was exposed")
    if receipt.get("student_rpc_forwarding_enabled_observed") is not True:
        fail("runtime v3 forwarding capability not observed")
    if receipt.get("network_origin_rate_limit_enabled_observed") is not True:
        fail("runtime v3 network limiter capability not observed")

    prior = authority.get("prior_v2_live_spoof_receipt", {})
    if prior.get("workflow_run_id") != 32338900002 or prior.get("spoof_attempt_http_status") != 403:
        fail("historical v2 spoof receipt was lost")

    network_runtime = network.get("observed_runtime", {})
    if network_runtime.get("edge_function_version") != 3:
        fail("network authority is not anchored to runtime v3")
    if network_runtime.get("runtime_origin_candidate_trusted_for_security") is not True:
        fail("network origin authority lost spoof-resistant trust")
    if network_runtime.get("spoof_resistance_receipt", {}).get("workflow_run_id") != 32349938290:
        fail("network authority spoof receipt differs")

    if gateway.get("current_state") != "EDGE_GATEWAY_V3_DEPLOYED_PRETOKEN_LIMITER_PATH_VERIFIED_THRESHOLD_PROOF_PENDING":
        fail("Stage 28 gateway authority state drifted")
    gv = gateway.get("runtime_verification", {})
    if gv.get("live_proof_workflow_run_id") != 32349938290:
        fail("gateway and spoof authorities disagree on live proof")
    if gv.get("spoof_proof_outcome") != "BLOCKED_AT_EDGE_403":
        fail("gateway authority lost spoof outcome")

    required_edge = (
        f'const SPOOF_SENTINEL = "{SENTINEL}";',
        "candidate_equals_known_client_spoof_sentinel:",
        "cloudflareOrigin?.trim() === SPOOF_SENTINEL",
        'req.headers.get("cf-connecting-ip")',
        "raw_network_origin_returned: false",
        "network_origin_rate_limit_enabled: true",
        "student_rpc_forwarding_enabled: true",
        "launch_gate_authority: false",
    )
    missing = [fragment for fragment in required_edge if fragment not in edge]
    if missing:
        fail(f"spoof-resistant source contract incomplete: {missing}")

    if edge.count("SPOOF_SENTINEL") != 2:
        fail("spoof sentinel must remain declaration + comparison only")
    if edge.count("candidate_equals_known_client_spoof_sentinel") != 1:
        fail("sentinel equality response field must remain unique")
    if any(fragment in lower for fragment in ("console.log", "console.error", "console.warn", "console.info")):
        fail(f"{FAILURE_CLASSES[1]} Edge source can log sensitive material")

    required_live = (
        f'SENTINEL = "{SENTINEL}"',
        "allow_edge_block=True",
        "exc.code == 403",
        'outcome = "BLOCKED_AT_EDGE_403"',
        "CLIENT_CAN_FORCE_CF_CONNECTING_IP=false",
        "RAW_RUNTIME_ORIGIN_RETURNED=false",
        "RUNTIME_VERSION_EXPECTED=3",
        "STUDENT_RPC_FORWARDING_ENABLED=true",
    )
    missing_live = [fragment for fragment in required_live if fragment not in live]
    if missing_live:
        fail(f"{FAILURE_CLASSES[2]} live spoof verifier drifted: {missing_live}")

    remaining = authority.get("remaining_boundaries", {})
    if remaining.get("network_origin_rate_limit_path_live_verified") is not True:
        fail("live limiter-path proof disappeared")
    for key in (
        "invalid_token_network_origin_rate_limit_threshold_verified",
        "flutter_student_gateway_cutover_complete",
        "direct_anon_v2_rpc_execute_revoked",
        "alert_delivery_verified",
        "rollback_verified",
    ):
        if remaining.get(key) is not False:
            fail(f"remaining boundary self-promoted: {key}")

    if any(value is not False for value in authority.get("launch_authority", {}).values()):
        fail("spoof proof gained launch authority")

    print("CF_ORIGIN_SPOOF_SENTINEL_AUTHORITY_GUARD=PASS")
    print("OBSERVED_RUNTIME_VERSION=3")
    print("SPOOF_PROOF_OUTCOME=BLOCKED_AT_EDGE_403")
    print("CLIENT_CAN_FORCE_CF_CONNECTING_IP=false")
    print("EDGE_RATE_LIMIT_PATH_LIVE=VERIFIED")
    print("EDGE_THRESHOLD_429_PROOF=PENDING")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
