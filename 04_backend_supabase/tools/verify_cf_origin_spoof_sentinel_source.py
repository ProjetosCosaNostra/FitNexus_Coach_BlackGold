from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "cf_origin_spoof_sentinel_authority.json"
NETWORK_AUTHORITY = BACKEND / "student_access_network_origin_boundary.json"
EDGE = BACKEND / "functions" / "student-access-gateway" / "index.ts"

FAILURE_CLASSES = (
    "BGF-CF-ORIGIN-SPOOF-171",
    "BGF-EDGE-SENTINEL-DATA-LEAK-172",
)
SENTINEL = "203.0.113.77"
EXPECTED_STATE = "SPOOF_SENTINEL_SOURCE_READY_V1_RUNTIME"


def fail(message: str) -> None:
    raise SystemExit("CF_ORIGIN_SPOOF_SENTINEL_SOURCE_GUARD=FAIL\n" + message)


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
    if not EDGE.is_file():
        fail("student-access-gateway source missing")
    edge = EDGE.read_text(encoding="utf-8")
    lower = edge.lower()

    if authority.get("schema_version") != 1:
        fail("authority schema_version must remain 1")
    if authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("wrong Supabase project authority")
    if authority.get("failure_classes") != list(FAILURE_CLASSES):
        fail("failure classes drifted")
    if authority.get("state") != EXPECTED_STATE:
        fail(f"source stage may not self-promote runtime state: {authority.get('state')!r}")

    current = authority.get("current_runtime", {})
    expected_current = {
        "edge_function_name": "student-access-gateway",
        "version": 1,
        "deployment_id": "2f85d9e1-39b3-46d7-a6c2-902eed7b4233",
        "bundle_sha256": "a67cfccbab1f89377afab63cf6100e6fff7baa2f9ff67ba3b58203198f079de9",
        "status": "ACTIVE",
        "origin_candidate": "cf-connecting-ip",
        "origin_candidate_available": True,
        "origin_candidate_trusted_for_security": False,
        "spoof_resistance_verified": False,
    }
    for key, expected in expected_current.items():
        if current.get(key) != expected:
            fail(f"runtime v1 authority drift for {key}: {current.get(key)!r}")

    network_runtime = network.get("observed_runtime", {})
    if network.get("current_state") != "ORIGIN_PROBE_RUNTIME_CANDIDATE_OBSERVED":
        fail("network-origin authority must remain candidate-observed before spoof proof")
    if network_runtime.get("runtime_origin_candidate") != "cf-connecting-ip":
        fail("network-origin candidate drifted")
    if network_runtime.get("runtime_origin_candidate_trusted_for_security") is not False:
        fail("network-origin candidate was trusted before spoof proof")
    receipt = network_runtime.get("live_probe_receipt", {})
    if receipt.get("cf_connecting_ip_spoof_resistance_verified") is not False:
        fail("network authority already claims spoof proof")

    nxt = authority.get("next_source", {})
    expected_next = {
        "expected_edge_function_version_after_deploy": 2,
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
    for key, expected in expected_next.items():
        if nxt.get(key) != expected:
            fail(f"next-source authority drift for {key}: {nxt.get(key)!r}")

    if authority.get("live_spoof_receipt") is not None:
        fail("source-only stage contains fabricated live spoof receipt")

    promotion = authority.get("promotion_rule", {})
    required_true = (
        "deploy_only_after_source_ci_green_and_merge_to_main",
        "trusted_only_if_deployed_v2_live_probe_returns_sentinel_equality_false",
        "client_forwarded_headers_are_never_authority",
        "no_student_cutover_in_this_stage",
    )
    for key in required_true:
        if promotion.get(key) is not True:
            fail(f"promotion interlock weakened: {key}")
    for key in (
        "trusted_if_sentinel_equality_true",
        "trusted_if_live_probe_missing_or_ambiguous",
    ):
        if promotion.get(key) is not False:
            fail(f"fail-closed spoof rule weakened: {key}")

    launch = authority.get("launch_authority", {})
    if any(value is not False for value in launch.values()):
        fail("spoof-source stage gained launch authority")

    required_source = (
        f'const SPOOF_SENTINEL = "{SENTINEL}";',
        "candidate_equals_known_client_spoof_sentinel:",
        "cloudflareOrigin?.trim() === SPOOF_SENTINEL",
        'req.headers.get("cf-connecting-ip")',
        "raw_network_origin_returned: false",
        "student_rpc_forwarding_enabled: false",
        "launch_gate_authority: false",
    )
    missing = [fragment for fragment in required_source if fragment not in edge]
    if missing:
        fail(f"sentinel source contract incomplete: {missing}")

    forbidden = (
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
    present = [fragment for fragment in forbidden if fragment in lower]
    if present:
        fail(f"sentinel probe leaked into forbidden behavior: {present}")

    if edge.count("SPOOF_SENTINEL") != 2:
        fail("spoof sentinel must exist only as declaration and comparison")
    if edge.count("candidate_equals_known_client_spoof_sentinel") != 1:
        fail("sentinel equality response field must be unique")

    print("CF_ORIGIN_SPOOF_SENTINEL_SOURCE_GUARD=PASS")
    print("CURRENT_RUNTIME_VERSION=1")
    print("NEXT_SOURCE_VERSION=2")
    print("SENTINEL=RFC5737_TEST_NET_3")
    print("RAW_RUNTIME_ORIGIN_RETURN=DENIED")
    print("SPOOF_RESISTANCE=NOT_YET_VERIFIED")
    print("ORIGIN_CANDIDATE_SECURITY_TRUST=DENIED")
    print("STUDENT_GATEWAY_CUTOVER=DENIED")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
