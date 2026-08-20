from __future__ import annotations

import json
import urllib.error
import urllib.request

ENDPOINT = "https://mceukeondizkwlpfxzgf.supabase.co/functions/v1/student-access-gateway"
PUBLISHABLE_KEY = "sb_publishable_aggqgASWuWfgBJAlrRKoeg_Gg2qnjHQ"
EXPECTED_MODE = "stage28_gateway_candidate_repository_source"
EXPECTED_CANDIDATE = "cf-connecting-ip"


def fail(message: str) -> None:
    raise SystemExit("STUDENT_ACCESS_EDGE_PROBE_LIVE=FAIL\n" + message)


def fetch(extra_headers: dict[str, str] | None = None) -> dict:
    headers = {
        "apikey": PUBLISHABLE_KEY,
        "user-agent": "FitNexus-Stage28-Origin-Probe/2.0",
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


def require_common(value: dict, label: str) -> None:
    checks = {
        "ok": True,
        "mode": EXPECTED_MODE,
        "network_origin_source_candidate": EXPECTED_CANDIDATE,
        "network_origin_candidate_available": True,
        "raw_network_origin_returned": False,
        "request_body_read": False,
        "network_origin_rate_limit_enabled": True,
        "student_rpc_forwarding_enabled": True,
        "launch_gate_authority": False,
    }
    mismatches = {
        key: value.get(key)
        for key, expected in checks.items()
        if value.get(key) != expected
    }
    if mismatches:
        fail(f"{label} safe contract mismatch: {sorted(mismatches)}")

    forbidden_keys = {
        "ip",
        "client_ip",
        "network_origin",
        "raw_ip",
        "token",
        "authorization",
        "request_body",
        "headers",
        "secret",
        "service_role",
    }
    present = sorted(forbidden_keys.intersection(value))
    if present:
        fail(f"{label} response contains forbidden raw-data keys: {present}")


def require_boolean(value: dict, key: str, label: str) -> bool:
    observed = value.get(key)
    if not isinstance(observed, bool):
        fail(f"{label} field {key} must be boolean")
    return observed


def main() -> None:
    baseline = fetch()
    require_common(baseline, "baseline")

    forwarded = fetch(
        {
            "x-forwarded-for": "203.0.113.10",
            "x-real-ip": "203.0.113.11",
        }
    )
    require_common(forwarded, "forwarded-header probe")

    xff_present = require_boolean(
        forwarded,
        "x_forwarded_for_present_but_untrusted",
        "forwarded-header probe",
    )
    xreal_present = require_boolean(
        forwarded,
        "x_real_ip_present_but_untrusted",
        "forwarded-header probe",
    )

    # Client-supplied forwarding headers remain diagnostic only. Intermediaries may strip
    # or normalize them; neither may become network-origin authority.
    if not xff_present:
        fail("x-forwarded-for TEST-NET probe was unexpectedly absent")

    print("STUDENT_ACCESS_EDGE_PROBE_LIVE=PASS")
    print("EDGE_HTTP_STATUS=200")
    print("EDGE_RUNTIME_EXPECTED_VERSION=3")
    print("EDGE_RUNTIME_MODE=stage28_gateway_candidate_repository_source")
    print("NETWORK_ORIGIN_CANDIDATE=cf-connecting-ip")
    print("NETWORK_ORIGIN_CANDIDATE_AVAILABLE=true")
    print("X_FORWARDED_FOR_CLIENT_HEADER_PRESERVED=true")
    print(f"X_REAL_IP_CLIENT_HEADER_PRESERVED={str(xreal_present).lower()}")
    print("CLIENT_FORWARDED_HEADERS=UNTRUSTED_REGARDLESS_OF_NORMALIZATION")
    print("RAW_NETWORK_ORIGIN_RETURNED=false")
    print("NETWORK_ORIGIN_RATE_LIMIT_ENABLED=true")
    print("STUDENT_RPC_FORWARDING_ENABLED=true")
    print("LAUNCH_GATE_AUTHORITY=false")


if __name__ == "__main__":
    main()
