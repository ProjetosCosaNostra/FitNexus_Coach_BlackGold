from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.request

ENDPOINT = "https://mceukeondizkwlpfxzgf.supabase.co/functions/v1/student-access-gateway"
PUBLISHABLE_KEY = "sb_publishable_aggqgASWuWfgBJAlrRKoeg_Gg2qnjHQ"
TOKEN_SEED = "fitnexus-stage29-valid-route-fixture-v1"
EXPECTED_STUDENT_ID = "659eafee-0508-5dfb-9fcb-d285d9e846db"
EXPECTED_PLAN_ID = "fd5762db-0a0c-54dc-81c9-2aeade199ee5"
EXPECTED_EXERCISE_ID = "2ec1260b-88f2-5a2c-ba81-3433d2c147d5"
FAILURE_CLASS = "BGF-VALID-STUDENT-ROUTE-UNPROVEN-187"
DATA_LEAK_CLASS = "BGF-VALID-ROUTE-RESPONSE-DATA-LEAK-189"


def fail(message: str) -> None:
    raise SystemExit("STUDENT_ACCESS_VALID_ROUTE_LIVE=FAIL\n" + message)


def walk_keys(value: object) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            keys.add(str(key).lower())
            keys.update(walk_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.update(walk_keys(child))
    return keys


def main() -> None:
    token = hashlib.sha256(TOKEN_SEED.encode("utf-8")).hexdigest()
    payload = json.dumps(
        {"action": "get_workout", "token": token},
        separators=(",", ":"),
    ).encode("utf-8")
    request = urllib.request.Request(
        ENDPOINT,
        data=payload,
        method="POST",
        headers={
            "apikey": PUBLISHABLE_KEY,
            "content-type": "application/json",
            "accept": "application/json",
            "user-agent": "FitNexus-Stage29-Valid-Route-Proof/1.0",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            status = response.status
            raw = response.read(32768)
    except urllib.error.HTTPError as exc:
        fail(f"{FAILURE_CLASS} unexpected HTTP status: {exc.code}")
    except urllib.error.URLError as exc:
        fail(f"{FAILURE_CLASS} edge endpoint unreachable: {type(exc.reason).__name__}")

    if status != 200:
        fail(f"{FAILURE_CLASS} expected HTTP 200, observed {status}")

    try:
        decoded = raw.decode("utf-8")
        value = json.loads(decoded)
    except (UnicodeDecodeError, json.JSONDecodeError):
        fail(f"{FAILURE_CLASS} response is not valid UTF-8 JSON")

    if token in decoded:
        fail(f"{DATA_LEAK_CLASS} raw synthetic bearer was returned")
    if not isinstance(value, dict):
        fail(f"{FAILURE_CLASS} response JSON must be an object")

    forbidden_keys = {
        "token",
        "authorization",
        "apikey",
        "headers",
        "network_origin",
        "raw_network_origin",
        "client_ip",
        "ip",
        "secret",
        "service_role",
        "cf-connecting-ip",
        "x-forwarded-for",
        "x-real-ip",
    }
    present = sorted(forbidden_keys.intersection(walk_keys(value)))
    if present:
        fail(f"{DATA_LEAK_CLASS} forbidden response keys present: {present}")

    student = value.get("student")
    plan = value.get("plan")
    exercises = value.get("exercises")
    history = value.get("history")
    session = value.get("session")

    if not isinstance(student, dict):
        fail(f"{FAILURE_CLASS} student object missing")
    expected_student = {
        "id": EXPECTED_STUDENT_ID,
        "name": "Stage29 Synthetic Student",
        "objective": "Valid Edge Route Proof",
        "level": "Iniciante",
        "adherence": 0,
        "status": "Ativo",
    }
    mismatched_student = [
        key for key, expected in expected_student.items() if student.get(key) != expected
    ]
    if mismatched_student:
        fail(f"{FAILURE_CLASS} student fixture mismatch: {mismatched_student}")

    if not isinstance(plan, dict):
        fail(f"{FAILURE_CLASS} active plan object missing")
    expected_plan = {
        "id": EXPECTED_PLAN_ID,
        "name": "Stage29 Synthetic Plan",
        "notes": "Controlled live GET proof; no real student data.",
        "next_session": "Synthetic proof only",
    }
    mismatched_plan = [
        key for key, expected in expected_plan.items() if plan.get(key) != expected
    ]
    if mismatched_plan:
        fail(f"{FAILURE_CLASS} plan fixture mismatch: {mismatched_plan}")

    if session is not None:
        fail(f"{FAILURE_CLASS} synthetic fixture unexpectedly has a workout session")
    if history != []:
        fail(f"{FAILURE_CLASS} synthetic fixture history must be empty")
    if not isinstance(exercises, list) or len(exercises) != 1:
        fail(f"{FAILURE_CLASS} expected exactly one synthetic exercise")

    exercise = exercises[0]
    if not isinstance(exercise, dict):
        fail(f"{FAILURE_CLASS} exercise payload is not an object")
    expected_exercise = {
        "id": EXPECTED_EXERCISE_ID,
        "position": 0,
        "name": "Stage29 Synthetic Exercise",
        "prescription": "1 x 1 controlled proof",
        "completed": False,
        "completed_at": None,
    }
    mismatched_exercise = [
        key for key, expected in expected_exercise.items() if exercise.get(key) != expected
    ]
    if mismatched_exercise:
        fail(f"{FAILURE_CLASS} exercise fixture mismatch: {mismatched_exercise}")

    print("STUDENT_ACCESS_VALID_ROUTE_LIVE=PASS")
    print("EDGE_RUNTIME_EXPECTED_VERSION=3")
    print("HTTP_STATUS=200")
    print("ACTION=get_workout")
    print("VALID_SYNTHETIC_POSSESSION_TOKEN=ACCEPTED")
    print("STUDENT_RPC_FORWARDING_WITH_VALID_TOKEN=VERIFIED")
    print("RESPONSE_MATCHES_SYNTHETIC_FIXTURE=true")
    print("RAW_SYNTHETIC_TOKEN_RETURNED=false")
    print("RAW_NETWORK_ORIGIN_RETURNED=false")
    print("REAL_STUDENT_DATA_USED=false")
    print("REAL_STUDENT_DATA_MUTATED=false")
    print("FIXTURE_CLEANUP=REQUIRED")
    print("FLUTTER_CUTOVER=false")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
