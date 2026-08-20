from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "cf_origin_spoof_sentinel_authority.json"
NETWORK_AUTHORITY = BACKEND / "student_access_network_origin_boundary.json"
EDGE = BACKEND / "functions" / "student-access-gateway" / "index.ts"
LIVE = BACKEND / "tools" / "verify_cf_origin_spoof_sentinel_live.py"

FAILURE_CLASSES = (
    "BGF-CF-ORIGIN-SPOOF-171",
    "BGF-EDGE-SENTINEL-DATA-LEAK-172",
    "BGF-CF-SPOOF-PROOF-OUTCOME-ASSUMPTION-173",
)
SENTINEL = "203.0.113.77"
DEPLOYMENT_ID = "2f85d9e1-39b3-46d7-a6c2-902eed7b4233"
BUNDLE_SHA256 = "6d67c45bdd23694bcfbe24503c84d1d0e7c540a43d7c54e104a376a7c2a18c5a"
SOURCE_MAIN_SHA = "0215cb417e0fafe659649d60a4d889b947d489cb"
FAILED_RUN_ID = 32338828582
SUCCESS_RUN_ID = 32338900002


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
    if not EDGE.is_file() or not LIVE.is_file():
        fail("required Edge or live-proof source is missing")
    edge = EDGE.read_text(encoding="utf-8")
    edge_lower = edge.lower()
    live = LIVE.read_text(encoding="utf-8")
    live_lower = live.lower()

    if authority.get("schema_version") != 2:
        fail("authority schema_version must remain 2")
    if authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("wrong Supabase project authority")
    if authority.get("failure_classes") != list(FAILURE_CLASSES):
        fail("failure classes drifted")
    if authority.get("state") != "SPOOF_RESISTANCE_VERIFIED_EDGE_BLOCK_403":
        fail("spoof-resistance authority is not in the verified state")
    if authority.get("source_main_sha") != SOURCE_MAIN_SHA:
        fail("source-main SHA drifted")

    runtime = authority.get("current_runtime", {})
    expected_runtime = {
        "edge_function_name": "student-access-gateway",
        "version": 2,
        "deployment_id": DEPLOYMENT_ID,
        "bundle_sha256": BUNDLE_SHA256,
        "status": "ACTIVE",
        "verify_jwt": False,
        "origin_candidate": "cf-connecting-ip",
        "origin_candidate_available": True,
        "origin_candidate_trusted_for_security": True,
        "spoof_resistance_verified": True,
    }
    for key, expected in expected_runtime.items():
        if runtime.get(key) != expected:
            fail(f"runtime authority drift for {key}: {runtime.get(key)!r}")

    contract = authority.get("sentinel_contract", {})
    expected_contract = {
        "sentinel": SENTINEL,
        "sentinel_standard": "RFC5737_TEST_NET_3",
        "response_field": "candidate_equals_known_client_spoof_sentinel",
        "response_is_boolean_only": True,
        "raw_runtime_origin_returned": False,
        "raw_runtime_origin_logged": False,
        "raw_runtime_origin_persisted": False,
        "student_rpc_forwarding_enabled": False,
        "launch_gate_authority": False,
    }
    for key, expected in expected_contract.items():
        if contract.get(key) != expected:
            fail(f"sentinel contract drift for {key}: {contract.get(key)!r}")

    receipt = authority.get("live_spoof_receipt", {})
    expected_receipt = {
        "workflow_run_id": SUCCESS_RUN_ID,
        "check_name": "Live CF origin spoof sentinel",
        "baseline_http_status": 200,
        "spoof_attempt_http_status": 403,
        "spoof_proof_outcome": "BLOCKED_AT_EDGE_403",
        "client_can_force_cf_connecting_ip": False,
        "raw_runtime_origin_returned": False,
        "raw_runtime_origin_persisted": False,
        "student_rpc_forwarding_observed": False,
        "launch_gate_authority_observed": False,
    }
    for key, expected in expected_receipt.items():
        if receipt.get(key) != expected:
            fail(f"{FAILURE_CLASSES[0]} live receipt drift for {key}: {receipt.get(key)!r}")

    failure_receipt = authority.get("live_spoof_failure_receipt", {})
    if failure_receipt.get("workflow_run_id") != FAILED_RUN_ID:
        fail(f"{FAILURE_CLASSES[2]} failure receipt run id drifted")
    if failure_receipt.get("failure_class") != FAILURE_CLASSES[2]:
        fail(f"{FAILURE_CLASSES[2]} failure receipt class drifted")
    if "403" not in str(failure_receipt.get("safe_finding", "")):
        fail(f"{FAILURE_CLASSES[2]} failure receipt lost the safe edge-block finding")
    corrective = str(failure_receipt.get("corrective_policy", "")).lower()
    if "403" not in corrective or "fail-closed" not in corrective:
        fail(f"{FAILURE_CLASSES[2]} corrective policy weakened")

    promotion = authority.get("promotion_rule", {})
    for key in (
        "trusted_if_platform_blocks_client_cf_connecting_ip_with_403",
        "trusted_if_function_executes_and_sentinel_equality_false",
        "client_forwarded_headers_are_never_authority",
        "no_student_cutover_in_this_stage",
    ):
        if promotion.get(key) is not True:
            fail(f"promotion rule weakened: {key}")
    for key in (
        "trusted_if_sentinel_equality_true",
        "trusted_if_live_probe_missing_or_ambiguous",
    ):
        if promotion.get(key) is not False:
            fail(f"fail-closed rule weakened: {key}")

    remaining = authority.get("remaining_boundaries", {})
    required_false = (
        "invalid_token_network_origin_rate_limit_implemented",
        "flutter_student_gateway_cutover_complete",
        "direct_anon_v2_rpc_execute_revoked",
        "alert_delivery_verified",
        "rollback_verified",
    )
    for key in required_false:
        if remaining.get(key) is not False:
            fail(f"source-trust proof self-promoted a remaining boundary: {key}")

    if any(value is not False for value in authority.get("launch_authority", {}).values()):
        fail("spoof proof gained launch authority")

    network_runtime = network.get("observed_runtime", {})
    if network.get("schema_version") != 4:
        fail("network-origin authority schema drifted")
    if network.get("current_state") != "ORIGIN_SOURCE_SPOOF_RESISTANCE_VERIFIED":
        fail("network-origin authority did not consume spoof proof")
    if network_runtime.get("runtime_origin_candidate_trusted_for_security") is not True:
        fail("network-origin authority did not promote the proven source")
    if network_runtime.get("spoof_resistance_receipt", {}).get("workflow_run_id") != SUCCESS_RUN_ID:
        fail("network-origin authority has a different spoof receipt")
    if network.get("current_client_boundary", {}).get("network_origin_rate_limit_for_invalid_token") is not False:
        fail("network-origin trust was confused with rate-limit implementation")

    required_edge = (
        f'const SPOOF_SENTINEL = "{SENTINEL}";',
        "candidate_equals_known_client_spoof_sentinel:",
        "cloudflareOrigin?.trim() === SPOOF_SENTINEL",
        'req.headers.get("cf-connecting-ip")',
        "raw_network_origin_returned: false",
        "student_rpc_forwarding_enabled: false",
        "launch_gate_authority: false",
    )
    missing_edge = [fragment for fragment in required_edge if fragment not in edge]
    if missing_edge:
        fail(f"sentinel Edge source contract incomplete: {missing_edge}")

    forbidden_edge = (
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
    present = [fragment for fragment in forbidden_edge if fragment in edge_lower]
    if present:
        fail(f"{FAILURE_CLASSES[1]} sentinel source gained forbidden behavior: {present}")

    required_live = (
        f'SENTINEL = "{SENTINEL}"',
        "allow_edge_block=True",
        "exc.code == 403",
        'outcome = "BLOCKED_AT_EDGE_403"',
        "CLIENT_CAN_FORCE_CF_CONNECTING_IP=false",
        "RAW_RUNTIME_ORIGIN_RETURNED=false",
    )
    missing_live = [fragment for fragment in required_live if fragment not in live]
    if missing_live:
        fail(f"{FAILURE_CLASSES[2]} live verifier contract incomplete: {missing_live}")
    forbidden_live = (
        "print(raw",
        "print(value",
        "print(response",
        "print(headers",
        "supabase_service_role_key",
    )
    unsafe_live = [fragment for fragment in forbidden_live if fragment in live_lower]
    if unsafe_live:
        fail(f"{FAILURE_CLASSES[1]} live verifier could disclose raw material: {unsafe_live}")

    if edge.count("SPOOF_SENTINEL") != 2:
        fail("spoof sentinel must exist only as declaration and comparison")
    if edge.count("candidate_equals_known_client_spoof_sentinel") != 1:
        fail("sentinel equality response field must be unique")

    print("CF_ORIGIN_SPOOF_SENTINEL_AUTHORITY_GUARD=PASS")
    print("RUNTIME_VERSION=2")
    print("SENTINEL=RFC5737_TEST_NET_3")
    print("SPOOF_PROOF_OUTCOME=BLOCKED_AT_EDGE_403")
    print("CLIENT_CAN_FORCE_CF_CONNECTING_IP=false")
    print("ORIGIN_CANDIDATE_SECURITY_TRUST=VERIFIED")
    print("INVALID_TOKEN_NETWORK_ORIGIN_RATE_LIMIT=NOT_IMPLEMENTED")
    print("STUDENT_GATEWAY_CUTOVER=DENIED")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
