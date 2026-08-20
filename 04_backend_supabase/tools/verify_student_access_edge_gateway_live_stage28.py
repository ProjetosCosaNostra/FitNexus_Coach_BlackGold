from __future__ import annotations

import json
import urllib.error
import urllib.request

ENDPOINT = "https://mceukeondizkwlpfxzgf.supabase.co/functions/v1/student-access-gateway"
PUBLISHABLE_KEY = "sb_publishable_aggqgASWuWfgBJAlrRKoeg_Gg2qnjHQ"
EXPECTED_MODE = "stage28_gateway_candidate_repository_source"


def fail(message: str) -> None:
    raise SystemExit("STUDENT_ACCESS_EDGE_GATEWAY_STAGE28_LIVE=FAIL\n" + message)


def request_json(method: str, payload: dict | None = None) -> tuple[int, dict]:
    headers = {
        "apikey": PUBLISHABLE_KEY,
        "user-agent": "FitNexus-Stage28-Gateway-Live/1.0",
        "accept": "application/json",
    }
    data = None
    if payload is not None:
        headers["content-type"] = "application/json"
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")

    req = urllib.request.Request(ENDPOINT, headers=headers, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            status = response.status
            raw = response.read(16384)
    except urllib.error.HTTPError as exc:
        status = exc.code
        raw = exc.read(16384)
    except urllib.error.URLError as exc:
        fail(f"edge endpoint unreachable: {type(exc.reason).__name__}")

    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        fail(f"HTTP {status} response is not valid UTF-8 JSON")

    if not isinstance(value, dict):
        fail(f"HTTP {status} response JSON must be an object")
    return status, value


def reject_raw_keys(value: dict, label: str) -> None:
    forbidden = {
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
    present = sorted(forbidden.intersection(value))
    if present:
        fail(f"{label} exposed forbidden raw-data keys: {present}")


def main() -> None:
    status, health = request_json("GET")
    if status != 200:
        fail(f"health probe HTTP status {status}, expected 200")

    expected_health = {
        "ok": True,
        "mode": EXPECTED_MODE,
        "network_origin_source_candidate": "cf-connecting-ip",
        "network_origin_candidate_available": True,
        "raw_network_origin_returned": False,
        "request_body_read": False,
        "network_origin_rate_limit_enabled": True,
        "student_rpc_forwarding_enabled": True,
        "launch_gate_authority": False,
    }
    mismatches = {
        key: health.get(key)
        for key, expected in expected_health.items()
        if health.get(key) != expected
    }
    if mismatches:
        fail(f"health contract mismatch: {sorted(mismatches)}")
    reject_raw_keys(health, "health")

    # Deliberately omit the possession token. Stage 28 executes the durable network-origin
    # limiter first. Reaching STUDENT_GATEWAY_PAYLOAD_INVALID therefore proves the live
    # limiter call succeeded before token/payload validation, without using a real token.
    status, invalid = request_json("POST", {"action": "start_workout"})
    if status != 400:
        fail(f"pre-token limiter proof HTTP status {status}, expected 400")
    if invalid.get("ok") is not False or invalid.get("error") != "STUDENT_GATEWAY_PAYLOAD_INVALID":
        fail("pre-token limiter proof did not reach the expected post-limiter validation boundary")
    reject_raw_keys(invalid, "pre-token limiter proof")

    print("STUDENT_ACCESS_EDGE_GATEWAY_STAGE28_LIVE=PASS")
    print("EDGE_RUNTIME_MODE=stage28_gateway_candidate_repository_source")
    print("NETWORK_ORIGIN_SOURCE=cf-connecting-ip")
    print("NETWORK_ORIGIN_RATE_LIMIT_LIVE_PATH=VERIFIED_PRE_TOKEN")
    print("STUDENT_RPC_FORWARDING_RUNTIME_ENABLED=true")
    print("REAL_STUDENT_TOKEN_USED=false")
    print("REAL_STUDENT_DATA_MUTATED=false")
    print("RAW_NETWORK_ORIGIN_RETURNED=false")
    print("LAUNCH_GATE_AUTHORITY=false")


if __name__ == "__main__":
    main()
