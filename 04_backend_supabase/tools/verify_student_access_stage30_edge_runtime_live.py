from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
AUTHORITY = ROOT / "04_backend_supabase" / "student_access_client_runtime_smoke_authority.json"
ENDPOINT = "https://mceukeondizkwlpfxzgf.supabase.co/functions/v1/student-access-gateway"
PUBLISHABLE_KEY = "sb_publishable_aggqgASWuWfgBJAlrRKoeg_Gg2qnjHQ"
TOKEN_SEED = "fitnexus-stage30-edge-runtime-smoke-fixture-v1"
PENDING_STATE = "EDGE_RUNTIME_SMOKE_FIXTURE_REMOTE_LIVE_PROOF_PENDING"
PROVEN_STATE = "EDGE_RUNTIME_SMOKE_LIVE_VERIFIED_CLEANUP_PENDING"
SEALED_STATES = {PROVEN_STATE}
FIXTURE_VERSION = "20260821075532"
SEALED_WORKFLOW_RUN = 32461357789
FAILURE_CLASS = "BGF-STAGE30-RUNTIME-SMOKE-COMMAND-FLOW-206"
DATA_LEAK_CLASS = "BGF-STAGE30-RUNTIME-SMOKE-RESPONSE-DATA-LEAK-205"
REEXECUTION_CLASS = "BGF-STAGE30-RUNTIME-SMOKE-PROOF-REEXECUTION-204"

EXPECTED_STUDENT_ID = "81d3be6f-824e-59bc-8fa0-27acf046d6d3"
EXPECTED_PLAN_ID = "82b92191-a8e3-5bb2-8f5d-fec9a59a57bb"
EXPECTED_EXERCISE_ID = "fe116050-9061-5627-8e3a-dedd863d6447"
EXPECTED_LINK_ID = "53dfab53-5ff8-573a-ab2a-faaea24107db"
EXPECTED_STUDENT = "Stage30 Synthetic Student"
EXPECTED_PLAN = "Stage30 Synthetic Plan"
EXPECTED_EXERCISE = "Stage30 Synthetic Exercise"

FORBIDDEN_KEYS = {
    "token",
    "token_hash",
    "authorization",
    "apikey",
    "headers",
    "network_origin",
    "raw_network_origin",
    "origin_hash",
    "client_ip",
    "ip",
    "secret",
    "service_role",
    "cf-connecting-ip",
    "x-forwarded-for",
    "x-real-ip",
}


def fail(detail: str) -> None:
    raise SystemExit("STAGE30_EDGE_RUNTIME_LIVE_SMOKE=FAIL\n" + detail)


def load_authority() -> dict[str, Any]:
    try:
        value = json.loads(AUTHORITY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"authority unavailable: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail("authority must be a JSON object")
    return value


def command_id(label: str) -> str:
    return hashlib.sha256(
        f"fitnexus-stage30-{label}-command-v1".encode("utf-8")
    ).hexdigest()[:32]


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


def assert_safe_response(value: object, raw_text: str, raw_token: str, action: str) -> None:
    if raw_token in raw_text:
        fail(f"{DATA_LEAK_CLASS} raw synthetic bearer returned by {action}")
    present = sorted(FORBIDDEN_KEYS.intersection(walk_keys(value)))
    if present:
        fail(f"{DATA_LEAK_CLASS} forbidden response keys from {action}: {present}")


def request_json(*, method: str, payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any], str]:
    data = None
    if payload is not None:
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        ENDPOINT,
        data=data,
        method=method,
        headers={
            "apikey": PUBLISHABLE_KEY,
            "content-type": "application/json",
            "accept": "application/json",
            "user-agent": "FitNexus-Stage30-FiveRoute-Smoke/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            status = response.status
            raw = response.read(65536)
    except urllib.error.HTTPError as exc:
        fail(f"{FAILURE_CLASS} unexpected HTTP status {exc.code}")
    except urllib.error.URLError as exc:
        fail(f"{FAILURE_CLASS} Edge endpoint unreachable: {type(exc.reason).__name__}")

    try:
        text = raw.decode("utf-8")
        value = json.loads(text)
    except (UnicodeDecodeError, json.JSONDecodeError):
        fail(f"{FAILURE_CLASS} Edge response is not valid UTF-8 JSON")
    if not isinstance(value, dict):
        fail(f"{FAILURE_CLASS} Edge response must be a JSON object")
    return status, value, text


def post_action(action: str, raw_token: str, fields: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"action": action, "token": raw_token}
    if fields:
        payload.update(fields)
    status, value, raw_text = request_json(method="POST", payload=payload)
    assert_safe_response(value, raw_text, raw_token, action)
    if status != 200:
        fail(f"{FAILURE_CLASS} {action} expected HTTP 200, observed {status}")
    if value.get("error") is not None or value.get("ok") is False:
        fail(f"{FAILURE_CLASS} {action} returned a bounded error instead of success")
    return value


def require_uuid(value: object, label: str) -> str:
    if not isinstance(value, str):
        fail(f"{FAILURE_CLASS} {label} missing")
    try:
        parsed = uuid.UUID(value)
    except ValueError:
        fail(f"{FAILURE_CLASS} {label} is not a UUID")
    return str(parsed)


def sealed_skip(authority: dict[str, Any]) -> bool:
    state = authority.get("current_state")
    if state not in SEALED_STATES:
        return False
    if authority.get("proof_reexecution_failure_class") != REEXECUTION_CLASS:
        fail("sealed smoke lost reexecution failure-class authority")
    runtime = authority.get("runtime_proof", {})
    receipt = authority.get("live_proof_receipt", {})
    if runtime.get("proof_workflow_run_id") != SEALED_WORKFLOW_RUN or runtime.get("proof_result") != "PASS":
        fail("sealed smoke runtime receipt drifted")
    for key in (
        "get_workout_verified",
        "start_workout_verified",
        "set_completion_verified",
        "get_feedback_context_verified",
        "submit_feedback_verified",
        "all_five_routes_verified",
        "completed_session_verified",
        "feedback_submitted_verified",
    ):
        if runtime.get(key) is not True:
            fail(f"sealed smoke proof missing: {key}")
    if runtime.get("proof_reexecution_allowed") is not False:
        fail(f"{REEXECUTION_CLASS} sealed smoke permits reexecution")
    if receipt.get("workflow_run_id") != SEALED_WORKFLOW_RUN or receipt.get("result") != "PASS":
        fail("sealed smoke proof receipt missing")
    if receipt.get("routes_verified") != 5 or receipt.get("proof_reexecution_allowed") is not False:
        fail("sealed smoke route/reexecution receipt drifted")

    print("STAGE30_EDGE_RUNTIME_LIVE_SMOKE=PASS")
    print("LIVE_SMOKE_MODE=SEALED_SKIP_REEXECUTION")
    print(f"SEALED_WORKFLOW_RUN_ID={SEALED_WORKFLOW_RUN}")
    print(f"REEXECUTION_PREVENTION={REEXECUTION_CLASS}")
    print(f"SEALED_AUTHORITY_STATE={state}")
    print("NETWORK_CALL_EXECUTED=false")
    print("ROUTES_VERIFIED=5")
    print("COMPLETED_SESSION_VERIFIED=true")
    print("FEEDBACK_SUBMITTED_VERIFIED=true")
    print("RAW_SYNTHETIC_TOKEN_RETURNED=false")
    print("RAW_NETWORK_ORIGIN_RETURNED=false")
    print("FLUTTER_ACTIVE_TRANSPORT=directRpc")
    print("EDGE_SELECTION=false")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")
    print("FIXTURE_CLEANUP=REQUIRED")
    print("LAUNCH_GATE_PROMOTION=DENIED")
    return True


def main() -> None:
    authority = load_authority()
    if authority.get("schema_version") != 1 or authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("smoke authority identity drifted")
    if sealed_skip(authority):
        return
    if authority.get("current_state") != PENDING_STATE:
        fail(f"{REEXECUTION_CLASS} unsupported smoke state: {authority.get('current_state')}")

    fixture = authority.get("fixture", {})
    runtime = authority.get("runtime_proof", {})
    cutover = authority.get("client_cutover_authority", {})
    if fixture.get("remote_applied") is not True or fixture.get("remote_version") != FIXTURE_VERSION:
        fail("smoke fixture remote receipt missing")
    if fixture.get("migration_ledger_state") != "remote_reconciled":
        fail("smoke fixture ledger is not reconciled")
    if runtime.get("fixture_deployed") is not True:
        fail("smoke fixture is not marked deployed")
    for key in (
        "get_workout_verified",
        "start_workout_verified",
        "set_completion_verified",
        "get_feedback_context_verified",
        "submit_feedback_verified",
        "all_five_routes_verified",
        "completed_session_verified",
        "feedback_submitted_verified",
        "cleanup_completed",
    ):
        if runtime.get(key) is not False:
            fail(f"{REEXECUTION_CLASS} proof authority already advanced: {key}")
    if runtime.get("proof_workflow_run_id") is not None or runtime.get("proof_result") is not None:
        fail(f"{REEXECUTION_CLASS} proof receipt already exists")
    if cutover.get("active_transport") != "directRpc":
        fail("Flutter active transport changed before smoke")
    for key in ("edge_gateway_selected", "rollback_verified", "direct_rpc_execute_revoked"):
        if cutover.get(key) is not False:
            fail(f"premature cutover authority: {key}")

    raw_token = hashlib.sha256(TOKEN_SEED.encode("utf-8")).hexdigest()

    health_status, health, health_text = request_json(method="GET")
    assert_safe_response(health, health_text, raw_token, "health")
    if health_status != 200:
        fail(f"{FAILURE_CLASS} gateway health expected HTTP 200, observed {health_status}")
    for key in ("ok", "network_origin_rate_limit_enabled", "student_rpc_forwarding_enabled"):
        if health.get(key) is not True:
            fail(f"{FAILURE_CLASS} gateway health invariant missing: {key}")
    if health.get("raw_network_origin_returned") is not False:
        fail(f"{DATA_LEAK_CLASS} gateway health claims raw network-origin return")
    if health.get("launch_gate_authority") is not False:
        fail("gateway unexpectedly gained launch authority")

    workout = post_action("get_workout", raw_token)
    student = workout.get("student")
    plan = workout.get("plan")
    exercises = workout.get("exercises")
    if not isinstance(student, dict) or student.get("id") != EXPECTED_STUDENT_ID or student.get("name") != EXPECTED_STUDENT:
        fail(f"{FAILURE_CLASS} get_workout synthetic student mismatch")
    if not isinstance(plan, dict) or plan.get("id") != EXPECTED_PLAN_ID or plan.get("name") != EXPECTED_PLAN:
        fail(f"{FAILURE_CLASS} get_workout synthetic plan mismatch")
    if workout.get("session") is not None or workout.get("history") != []:
        fail(f"{FAILURE_CLASS} initial synthetic workout is not pristine")
    if not isinstance(exercises, list) or len(exercises) != 1:
        fail(f"{FAILURE_CLASS} get_workout expected exactly one exercise")
    exercise = exercises[0]
    if not isinstance(exercise, dict):
        fail(f"{FAILURE_CLASS} get_workout exercise payload invalid")
    if exercise.get("id") != EXPECTED_EXERCISE_ID or exercise.get("name") != EXPECTED_EXERCISE:
        fail(f"{FAILURE_CLASS} get_workout synthetic exercise mismatch")
    if exercise.get("completed") is not False or exercise.get("completed_at") is not None:
        fail(f"{FAILURE_CLASS} synthetic exercise unexpectedly completed before command")

    started = post_action(
        "start_workout",
        raw_token,
        {"command_id": command_id("start-workout")},
    )
    session_id = require_uuid(started.get("session_id"), "start_workout.session_id")
    if started.get("replayed") is not False:
        fail(f"{FAILURE_CLASS} first start_workout unexpectedly replayed")

    completion = post_action(
        "set_completion",
        raw_token,
        {
            "session_id": session_id,
            "exercise_id": EXPECTED_EXERCISE_ID,
            "completed": True,
            "command_id": command_id("set-completion"),
        },
    )
    if completion.get("session_id") != session_id:
        fail(f"{FAILURE_CLASS} set_completion session mismatch")
    for key, expected in {
        "status": "completed",
        "completed_exercises": 1,
        "total_exercises": 1,
        "adherence": 100,
    }.items():
        if completion.get(key) != expected:
            fail(f"{FAILURE_CLASS} set_completion mismatch: {key}")

    feedback_context = post_action("get_feedback_context", raw_token)
    if feedback_context.get("eligible") is not True:
        fail(f"{FAILURE_CLASS} completed session is not feedback-eligible")
    if feedback_context.get("session_id") != session_id:
        fail(f"{FAILURE_CLASS} feedback context session mismatch")
    if feedback_context.get("plan_name") != EXPECTED_PLAN:
        fail(f"{FAILURE_CLASS} feedback context plan mismatch")
    if feedback_context.get("submitted") is not False or feedback_context.get("feedback") is not None:
        fail(f"{FAILURE_CLASS} feedback context is not pristine before submit")
    if not isinstance(feedback_context.get("completed_at"), str):
        fail(f"{FAILURE_CLASS} completed_at missing from feedback context")

    submitted = post_action(
        "submit_feedback",
        raw_token,
        {
            "session_id": session_id,
            "perceived_exertion": 5,
            "pain_score": 0,
            "energy_score": 4,
            "pain_location": None,
            "note": None,
            "command_id": command_id("submit-feedback"),
        },
    )
    require_uuid(submitted.get("feedback_id"), "submit_feedback.feedback_id")
    if submitted.get("session_id") != session_id:
        fail(f"{FAILURE_CLASS} submit_feedback session mismatch")
    if submitted.get("submitted") is not True or submitted.get("risk_signal") != "low":
        fail(f"{FAILURE_CLASS} submit_feedback safe synthetic result mismatch")

    print("STAGE30_EDGE_RUNTIME_LIVE_SMOKE=PASS")
    print("LIVE_SMOKE_MODE=EXECUTED_ONCE")
    print("EDGE_RUNTIME_EXPECTED_VERSION=3")
    print("GATEWAY_HEALTH=PASS")
    print("ROUTE_1_GET_WORKOUT=PASS")
    print("ROUTE_2_START_WORKOUT=PASS")
    print("ROUTE_3_SET_COMPLETION=PASS")
    print("ROUTE_4_GET_FEEDBACK_CONTEXT=PASS")
    print("ROUTE_5_SUBMIT_FEEDBACK=PASS")
    print("ROUTES_VERIFIED=5")
    print("COMPLETED_SESSION_VERIFIED=true")
    print("FEEDBACK_SUBMITTED_VERIFIED=true")
    print("FEEDBACK_RISK_SIGNAL=low")
    print("RAW_SYNTHETIC_TOKEN_RETURNED=false")
    print("RAW_NETWORK_ORIGIN_RETURNED=false")
    print("REAL_STUDENT_DATA_USED=false")
    print("REAL_STUDENT_DATA_MUTATED=false")
    print("FLUTTER_ACTIVE_TRANSPORT=directRpc")
    print("EDGE_SELECTION=false")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")
    print("FIXTURE_CLEANUP=REQUIRED")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
