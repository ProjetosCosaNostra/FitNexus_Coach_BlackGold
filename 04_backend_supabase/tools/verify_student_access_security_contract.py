from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
STUDENT = ROOT / "03_app_flutter" / "fitnexus_app" / "lib" / "features" / "student"
MIGRATION = BACKEND / "migrations" / "20260819103700_stage21_student_access_security_boundary.sql"
WORKOUT_REPOSITORY = STUDENT / "student_workout_repository.dart"
FEEDBACK_REPOSITORY = STUDENT / "student_feedback_repository.dart"
TRANSPORT_CONTRACT = STUDENT / "student_access_transport_contract.dart"
TRANSPORT_RUNTIME = STUDENT / "student_access_transport.dart"
CUTOVER_AUTHORITY = BACKEND / "student_access_client_cutover_authority.json"
COMMAND_ID = STUDENT / "student_access_command_id.dart"
EXPERIENCE = STUDENT / "student_experience_page.dart"
PROFESSOR_REPOSITORY = ROOT / "03_app_flutter" / "fitnexus_app" / "lib" / "features" / "professor" / "professor_data_repository.dart"
WEB_INDEX = ROOT / "03_app_flutter" / "fitnexus_app" / "web" / "index.html"

CALLSITE_MODEL_FAILURE = "BGF-GUARD-RPC-CALLSITE-COLOCATION-200"
ROUTES = {
    "get_workout": "get_student_workout_v2",
    "start_workout": "start_student_workout_v2",
    "set_completion": "set_student_exercise_completion_v2",
    "get_feedback_context": "get_student_feedback_context_v2",
    "submit_feedback": "submit_student_workout_feedback_v2",
}


def fail(code: str, detail: str) -> None:
    raise SystemExit(
        "STUDENT_ACCESS_SECURITY_CONTRACT_GUARD=FAIL\n"
        f"FAILURE_CLASS={code}\n"
        f"DETAIL={detail}"
    )


def require(text: str, needle: str, code: str, detail: str) -> None:
    if needle not in text:
        fail(code, detail)


def forbid(text: str, needle: str, code: str, detail: str) -> None:
    if needle in text:
        fail(code, detail)


def read(path: Path) -> str:
    if not path.exists():
        fail("BGF-STUDENT-ACCESS-BOUNDARY-FILE-MISSING-152", f"missing required file: {path}")
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> dict:
    try:
        value = json.loads(read(path))
    except json.JSONDecodeError as exc:
        fail("BGF-STUDENT-ACCESS-BOUNDARY-FILE-MISSING-152", f"invalid authority JSON: {exc}")
    if not isinstance(value, dict):
        fail("BGF-STUDENT-ACCESS-BOUNDARY-FILE-MISSING-152", "cutover authority must be an object")
    return value


def main() -> None:
    sql = read(MIGRATION).lower()
    workout = read(WORKOUT_REPOSITORY)
    feedback = read(FEEDBACK_REPOSITORY)
    command_id = read(COMMAND_ID)
    experience = read(EXPERIENCE)
    professor = read(PROFESSOR_REPOSITORY)
    web_index = read(WEB_INDEX).lower()
    cutover = read_json(CUTOVER_AUTHORITY) if CUTOVER_AUTHORITY.exists() else None

    for needle in (
        "expires_at = now() + interval '30 days'",
        "revoked_at timestamptz",
        "revocation_reason text",
        "rotated_from_link_id uuid",
        "rotation_number integer not null default 1",
        "issue_student_access_token_v2",
        "student_access_rotation_cooldown",
    ):
        require(sql, needle, "BGF-STUDENT-ACCESS-UNBOUNDED-BEARER-147", f"finite lifetime/rotation invariant disappeared: {needle}")

    for needle in (
        "private.student_access_rate_buckets",
        "student_access_rate_limited",
        "private.student_access_security_events",
        "'rate_limited'",
        "p_limit_per_minute",
    ):
        require(sql, needle, "BGF-STUDENT-ACCESS-RATE-LIMIT-149", f"rate-limit/abuse-monitoring invariant disappeared: {needle}")

    for needle in (
        "private.student_access_command_receipts",
        "command_id ~ '^[0-9a-f]{32}$'",
        "student_access_command_begin_v2",
        "student_access_command_finish_v2",
        "'replay'",
    ):
        require(sql, needle, "BGF-STUDENT-ACCESS-REPLAY-148", f"replay/idempotency invariant disappeared: {needle}")

    require(command_id, "Random.secure()", "BGF-STUDENT-ACCESS-REPLAY-148", "client command ids must use a cryptographically secure RNG")
    require(command_id, "index < 16", "BGF-STUDENT-ACCESS-REPLAY-148", "client command ids must retain 16 random bytes / 128 bits")

    if cutover is None:
        for needle in (
            "'get_student_workout_v2'",
            "'start_student_workout_v2'",
            "'set_student_exercise_completion_v2'",
            "'p_command_id'",
        ):
            require(workout, needle, "BGF-STUDENT-ACCESS-LEGACY-RPC-BYPASS-151", f"workout client bypassed the v2 boundary: {needle}")
        for needle in (
            "'get_student_feedback_context_v2'",
            "'submit_student_workout_feedback_v2'",
            "'p_command_id'",
        ):
            require(feedback, needle, "BGF-STUDENT-ACCESS-LEGACY-RPC-BYPASS-151", f"feedback client bypassed the v2 boundary: {needle}")
    else:
        guard_classes = cutover.get("guard_failure_classes", [])
        legacy_guard_class = cutover.get("guard_callsite_model_failure_class")
        if CALLSITE_MODEL_FAILURE not in guard_classes and legacy_guard_class != CALLSITE_MODEL_FAILURE:
            fail(CALLSITE_MODEL_FAILURE, "centralized call-site guard prevention authority missing")
        state = cutover.get("current_state")
        if state == "CLIENT_EDGE_CUTOVER_PREPARATION_DIRECT_PATH_ACTIVE":
            for needle in (
                "'get_student_workout_v2'",
                "'start_student_workout_v2'",
                "'set_student_exercise_completion_v2'",
                "'p_command_id'",
            ):
                require(workout, needle, "BGF-STUDENT-ACCESS-LEGACY-RPC-BYPASS-151", f"workout v2 boundary missing: {needle}")
            for needle in (
                "'get_student_feedback_context_v2'",
                "'submit_student_workout_feedback_v2'",
                "'p_command_id'",
            ):
                require(feedback, needle, "BGF-STUDENT-ACCESS-LEGACY-RPC-BYPASS-151", f"feedback v2 boundary missing: {needle}")
        elif state in (
            "CLIENT_SINGLE_TRANSPORT_SOURCE_INTEGRATED_DIRECT_MODE",
            "CLIENT_EDGE_ERROR_CONTRACT_ROLLBACK_HARNESS_READY_DIRECT_MODE",
            "CLIENT_RUNTIME_ROLLBACK_VERIFIED_DIRECT_MODE",
        ):
            contract = read(TRANSPORT_CONTRACT)
            runtime = read(TRANSPORT_RUNTIME)
            inventory = cutover.get("current_client_inventory", {})
            if inventory.get("repositories_call_supabase_rpc_directly") is not False:
                fail(CALLSITE_MODEL_FAILURE, "centralized transport authority says repositories still call RPC directly")
            if inventory.get("repositories_call_single_transport") is not True:
                fail(CALLSITE_MODEL_FAILURE, "single-transport repository authority missing")
            for action, rpc in ROUTES.items():
                require(contract, f"'{action}': '{rpc}'", "BGF-STUDENT-ACCESS-LEGACY-RPC-BYPASS-151", f"central transport lost hardened v2 route: {action}->{rpc}")
            require(runtime, "return _client.rpc(directRpc, params: directParams);", "BGF-STUDENT-ACCESS-LEGACY-RPC-BYPASS-151", "active direct mode no longer resolves the centralized v2 RPC map")
            require(workout, "action: 'get_workout'", CALLSITE_MODEL_FAILURE, "workout get route no longer enters centralized transport")
            require(workout, "action: 'start_workout'", CALLSITE_MODEL_FAILURE, "workout start route no longer enters centralized transport")
            require(workout, "action: 'set_completion'", CALLSITE_MODEL_FAILURE, "workout completion route no longer enters centralized transport")
            require(feedback, "action: 'get_feedback_context'", CALLSITE_MODEL_FAILURE, "feedback context route no longer enters centralized transport")
            require(feedback, "action: 'submit_feedback'", CALLSITE_MODEL_FAILURE, "feedback submit route no longer enters centralized transport")
            require(workout, "'p_command_id': commandId", "BGF-STUDENT-ACCESS-REPLAY-148", "workout command id mapping disappeared")
            require(feedback, "'p_command_id': commandId", "BGF-STUDENT-ACCESS-REPLAY-148", "feedback command id mapping disappeared")
            forbid(workout, ".rpc(", CALLSITE_MODEL_FAILURE, "workout repository bypassed the centralized transport")
            forbid(feedback, ".rpc(", CALLSITE_MODEL_FAILURE, "feedback repository bypassed the centralized transport")
        else:
            fail(CALLSITE_MODEL_FAILURE, f"security guard has no client-callsite model for state: {state}")

    require(professor, "'issue_student_access_token_v2'", "BGF-STUDENT-ACCESS-LEGACY-RPC-BYPASS-151", "professor token issuance must use the bounded v2 rotation boundary")

    for legacy_grant in (
        "revoke execute on function public.issue_student_access_token(uuid) from authenticated",
        "revoke execute on function public.get_student_workout(text) from anon, authenticated",
        "revoke execute on function public.start_student_workout(text) from anon, authenticated",
        "revoke execute on function public.set_student_exercise_completion(text,uuid,uuid,boolean) from anon, authenticated",
        "revoke execute on function public.get_student_feedback_context(text) from anon, authenticated",
        "revoke execute on function public.submit_student_workout_feedback(text,uuid,integer,integer,integer,text,text) from anon, authenticated",
    ):
        require(sql, legacy_grant, "BGF-STUDENT-ACCESS-LEGACY-RPC-BYPASS-151", f"legacy RPC remained client-callable: {legacy_grant}")

    forbid(experience, "Uri.base.queryParameters['token']", "BGF-STUDENT-ACCESS-URL-LEAK-150", "student bearer token must not be read from the top-level URL query string")
    require(experience, "Uri.base.fragment", "BGF-STUDENT-ACCESS-URL-LEAK-150", "student bearer token must remain fragment-scoped")
    require(web_index, '<meta name="referrer" content="no-referrer">', "BGF-STUDENT-ACCESS-URL-LEAK-150", "web shell must keep an explicit no-referrer policy")

    print("STUDENT_ACCESS_SECURITY_CONTRACT_GUARD=PASS")
    print("FINITE_TOKEN_LIFETIME=PASS")
    print("RATE_LIMIT_BOUNDARY=PASS")
    print("COMMAND_REPLAY_DEFENSE=PASS")
    print("LEGACY_RPC_BYPASS=DENIED")
    print(f"CALLSITE_MODEL_PREVENTION={CALLSITE_MODEL_FAILURE}")
    print("TOKEN_QUERY_LEAK=DENIED")


if __name__ == "__main__":
    main()
