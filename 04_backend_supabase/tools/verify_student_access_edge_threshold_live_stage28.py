from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

ENDPOINT = "https://mceukeondizkwlpfxzgf.supabase.co/functions/v1/student-access-gateway"
PUBLISHABLE_KEY = "sb_publishable_aggqgASWuWfgBJAlrRKoeg_Gg2qnjHQ"
ACTION = "start_workout"
LIMIT = 30
EXPECTED_ALLOWED_BOUNDARY = "STUDENT_GATEWAY_PAYLOAD_INVALID"
EXPECTED_RATE_LIMIT = "STUDENT_NETWORK_RATE_LIMITED"


def fail(message: str) -> None:
    raise SystemExit("STAGE28_EDGE_THRESHOLD_LIVE_PROOF=FAIL\n" + message)


def post_without_token() -> tuple[int, dict]:
    payload = json.dumps({"action": ACTION}, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        ENDPOINT,
        method="POST",
        data=payload,
        headers={
            "apikey": PUBLISHABLE_KEY,
            "content-type": "application/json",
            "accept": "application/json",
            "user-agent": "FitNexus-Stage28-Threshold-Proof/1.0",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=25) as response:
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
        fail(f"HTTP {status} response must be a JSON object")
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
    # Start in a fresh database minute window. This makes the proof exact: requests 1..30
    # must reach the post-limiter payload-validation boundary and request 31 must be the
    # first threshold-exceeded response. If shared-origin traffic interferes, fail closed.
    now = datetime.now(timezone.utc)
    wait_seconds = 62 - now.second - (now.microsecond / 1_000_000)
    if wait_seconds > 0:
        time.sleep(wait_seconds)

    for attempt in range(1, LIMIT + 2):
        status, body = post_without_token()
        reject_raw_keys(body, f"attempt {attempt}")

        if attempt <= LIMIT:
            if status != 400:
                fail(f"attempt {attempt} HTTP {status}, expected 400 before threshold")
            if body.get("ok") is not False or body.get("error") != EXPECTED_ALLOWED_BOUNDARY:
                fail(f"attempt {attempt} did not reach the expected post-limiter boundary")
            continue

        if status != 429:
            fail(f"attempt {attempt} HTTP {status}, expected 429 at threshold+1")
        if body.get("ok") is not False or body.get("error") != EXPECTED_RATE_LIMIT:
            fail("threshold+1 response did not return STUDENT_NETWORK_RATE_LIMITED")
        retry_after = body.get("retry_after_seconds")
        if not isinstance(retry_after, int) or retry_after < 1 or retry_after > 60:
            fail("threshold+1 retry_after_seconds is outside 1..60")

    print("STAGE28_EDGE_THRESHOLD_LIVE_PROOF=PASS")
    print("EDGE_RUNTIME_EXPECTED_VERSION=3")
    print("ACTION=start_workout")
    print("CONFIGURED_LIMIT=30")
    print("ALLOWED_CALLS_OBSERVED=30")
    print("RATE_LIMITED_CALL_NUMBER=31")
    print("RATE_LIMIT_HTTP_STATUS=429")
    print("RATE_LIMIT_ERROR=STUDENT_NETWORK_RATE_LIMITED")
    print("REAL_STUDENT_TOKEN_USED=false")
    print("REAL_STUDENT_DATA_MUTATED=false")
    print("RAW_NETWORK_ORIGIN_RETURNED=false")
    print("SYNTHETIC_PSEUDONYMOUS_BUCKET_AND_SIGNAL_CLEANUP_REQUIRED=true")
    print("LAUNCH_GATE_AUTHORITY=false")


if __name__ == "__main__":
    main()
