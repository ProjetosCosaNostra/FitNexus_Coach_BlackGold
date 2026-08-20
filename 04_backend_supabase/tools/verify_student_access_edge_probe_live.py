from __future__ import annotations

import json
import urllib.error
import urllib.request

ENDPOINT = "https://mceukeondizkwlpfxzgf.supabase.co/functions/v1/student-access-gateway"
PUBLISHABLE_KEY = "sb_publishable_aggqgASWuWfgBJAlrRKoeg_Gg2qnjHQ"
EXPECTED_MODE = "origin_probe_not_student_gateway_cutover"
EXPECTED_CANDIDATE = "cf-connecting-ip"


def fail(message: str) -> None:
    raise SystemExit("STUDENT_ACCESS_EDGE_PROBE_LIVE=FAIL\n" + message)


def fetch(extra_headers: dict[str, str] | None = None) -> dict:
    headers = {
        "apikey": PUBLISHABLE_KEY,
        "user-agent": "FitNexus-Stage26-Origin-Probe/1.0",
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
        "student_rpc_forwarding_enabled": False,
        "launch_gate_authority": False,
    }
    mismatches = {
        key: value.get(key)
        for key, expected in checks.items()
        if value.get(key) != expected
    }
    if mismatches:
        fail(f"{label} safe contract mismatch: {sorted(mismatches)}")

    # Fail closed if the probe unexpectedly starts returning fields that could contain
    # the raw network origin or request/bearer material.
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

    if forwarded.get("x_forwarded_for_present_but_untrusted") is not True:
        fail("x-forwarded-for probe was not observed as untrusted presence")
    if forwarded.get("x_real_ip_present_but_untrusted") is not True:
        fail("x-real-ip probe was not observed as untrusted presence")

    print("STUDENT_ACCESS_EDGE_PROBE_LIVE=PASS")
    print("EDGE_HTTP_STATUS=200")
    print("NETWORK_ORIGIN_CANDIDATE=cf-connecting-ip")
    print("NETWORK_ORIGIN_CANDIDATE_AVAILABLE=true")
    print("CLIENT_FORWARDED_HEADERS=OBSERVED_BUT_UNTRUSTED")
    print("RAW_NETWORK_ORIGIN_RETURNED=false")
    print("STUDENT_RPC_FORWARDING=false")
    print("LAUNCH_GATE_AUTHORITY=false")


if __name__ == "__main__":
    main()
