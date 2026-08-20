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
DEPLOYMENT_ID = "2f85d9e1-39b3-46d7-a6c2-902eed7b4233"
BUNDLE_SHA256 = "6d67c45bdd23694bcfbe24503c84d1d0e7c540a43d7c54e104a376a7c2a18c5a"
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

    runtime = authority.get("current_runtime", {})
    expected = {
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
    for key, value in expected.items():
        if runtime.get(key) != value:
            fail(f"observed runtime drift for {key}")

    receipt = authority.get("live_spoof_receipt", {})
    if receipt.get("workflow_run_id") != SUCCESS_RUN_ID:
        fail("live spoof receipt run drifted")
    if receipt.get("spoof_attempt_http_status") != 403:
        fail("client spoof attempt is no longer evidenced as edge-blocked")
    if receipt.get("client_can_force_cf_connecting_ip") is not False:
        fail(f"{FAILURE_CLASSES[0]} client can force cf-connecting-ip")
    if receipt.get("raw_runtime_origin_returned") is not False:
        fail(f"{FAILURE_CLASSES[1]} raw runtime origin was exposed")

    network_runtime = network.get("observed_runtime", {})
    if network_runtime.get("runtime_origin_candidate_trusted_for_security") is not True:
        fail("network origin authority lost spoof-resistant trust")
    if network_runtime.get("spoof_resistance_receipt", {}).get("workflow_run_id") != SUCCESS_RUN_ID:
        fail("network authority spoof receipt differs")

    if gateway.get("current_state") != "REPOSITORY_GATEWAY_RATE_LIMIT_IMPLEMENTED_NOT_DEPLOYED":
        fail("Stage 28 candidate authority missing or self-promoted")
    if gateway.get("runtime_verification", {}).get("candidate_deployed") is not False:
        fail("repository candidate was confused with deployed runtime")

    required_edge = (
        f'const SPOOF_SENTINEL = "{SENTINEL}";',
        "candidate_equals_known_client_spoof_sentinel:",
        "cloudflareOrigin?.trim() === SPOOF_SENTINEL",
        'req.headers.get("cf-connecting-ip")',
        "raw_network_origin_returned: false",
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
    )
    missing_live = [fragment for fragment in required_live if fragment not in live]
    if missing_live:
        fail(f"{FAILURE_CLASSES[2]} live spoof verifier drifted: {missing_live}")

    if any(value is not False for value in authority.get("launch_authority", {}).values()):
        fail("spoof proof gained launch authority")

    print("CF_ORIGIN_SPOOF_SENTINEL_AUTHORITY_GUARD=PASS")
    print("OBSERVED_RUNTIME_VERSION=2")
    print("SPOOF_PROOF_OUTCOME=BLOCKED_AT_EDGE_403")
    print("CLIENT_CAN_FORCE_CF_CONNECTING_IP=false")
    print("REPOSITORY_GATEWAY_CANDIDATE=IMPLEMENTED_NOT_DEPLOYED")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
