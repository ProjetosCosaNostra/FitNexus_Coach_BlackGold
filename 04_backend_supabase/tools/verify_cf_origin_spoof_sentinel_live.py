from __future__ import annotations

import json
import urllib.error
import urllib.request

ENDPOINT = "https://mceukeondizkwlpfxzgf.supabase.co/functions/v1/student-access-gateway"
PUBLISHABLE_KEY = "sb_publishable_aggqgASWuWfgBJAlrRKoeg_Gg2qnjHQ"
SENTINEL = "203.0.113.77"
EXPECTED_MODE = "origin_probe_not_student_gateway_cutover"
EXPECTED_CANDIDATE = "cf-connecting-ip"


def fail(message: str) -> None:
    raise SystemExit("CF_ORIGIN_SPOOF_SENTINEL_LIVE=FAIL\n" + message)


def fetch(extra_headers: dict[str, str] | None = None) -> dict:
    headers = {
        "apikey": PUBLISHABLE_KEY,
        "user-agent": "FitNexus-Stage26-CF-Origin-Spoof-Sentinel/1.0",
        "accept": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)

    request = urllib.request.Request(ENDPOINT, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            status = response.status
            raw = response.read(16384)
    except urllib.error.HTTPError as exc:
        fail(f"unexpected HTTP status: {exc.code}")
    except urllib.error.URLError as exc:
        fail(f"edge endpoint unreachable: {type(exc.reason).__name__}")

    if status != 200:
        fail(f"unexpected HTTP status: {status}")

    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        fail("response is not valid UTF-8 JSON")

    if not isinstance(value, dict):
        fail("response JSON must be an object")
    return value


def require_safe_contract(value: dict, label: str) -> bool:
    expected = {
        "ok": True,
        "mode": EXPECTED_MODE,
        "network_origin_source_candidate": EXPECTED_CANDIDATE,
        "network_origin_candidate_available": True,
        "raw_network_origin_returned": False,
        "request_body_read": False,
        "student_rpc_forwarding_enabled": False,
        "launch_gate_authority": False,
    }
    mismatches = sorted(
        key for key, wanted in expected.items() if value.get(key) != wanted
    )
    if mismatches:
        fail(f"{label} safe contract mismatch: {mismatches}")

    forbidden_keys = {
        "ip",
        "client_ip",
        "network_origin",
        "raw_ip",
        "token",
        "authorization",
        "request_body",
        "headers",
    }
    present = sorted(forbidden_keys.intersection(value))
    if present:
        fail(f"{label} response contains forbidden raw-data keys: {present}")

    equality = value.get("candidate_equals_known_client_spoof_sentinel")
    if not isinstance(equality, bool):
        fail(f"{label} sentinel equality field must be boolean")
    return equality


def main() -> None:
    baseline = fetch()
    baseline_equal = require_safe_contract(baseline, "baseline")
    if baseline_equal:
        fail("baseline unexpectedly equals the TEST-NET spoof sentinel")

    spoof_attempt = fetch({"cf-connecting-ip": SENTINEL})
    spoof_equal = require_safe_contract(spoof_attempt, "cf-connecting-ip spoof attempt")

    if spoof_equal:
        fail(
            "BGF-CF-ORIGIN-SPOOF-171 client-supplied cf-connecting-ip reached the runtime candidate unchanged"
        )

    print("CF_ORIGIN_SPOOF_SENTINEL_LIVE=PASS")
    print("EDGE_HTTP_STATUS=200")
    print("RUNTIME_VERSION_EXPECTED=2")
    print("NETWORK_ORIGIN_CANDIDATE=cf-connecting-ip")
    print("SENTINEL_STANDARD=RFC5737_TEST_NET_3")
    print("CLIENT_SUPPLIED_CF_CONNECTING_IP_EQUALITY=false")
    print("RAW_RUNTIME_ORIGIN_RETURNED=false")
    print("STUDENT_RPC_FORWARDING=false")
    print("LAUNCH_GATE_AUTHORITY=false")


if __name__ == "__main__":
    main()
