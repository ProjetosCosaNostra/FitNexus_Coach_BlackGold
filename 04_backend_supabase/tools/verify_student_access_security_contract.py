from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "04_backend_supabase" / "migrations" / "20260819103700_stage21_student_access_security_boundary.sql"
WORKOUT_REPOSITORY = ROOT / "03_app_flutter" / "fitnexus_app" / "lib" / "features" / "student" / "student_workout_repository.dart"
FEEDBACK_REPOSITORY = ROOT / "03_app_flutter" / "fitnexus_app" / "lib" / "features" / "student" / "student_feedback_repository.dart"
COMMAND_ID = ROOT / "03_app_flutter" / "fitnexus_app" / "lib" / "features" / "student" / "student_access_command_id.dart"
EXPERIENCE = ROOT / "03_app_flutter" / "fitnexus_app" / "lib" / "features" / "student" / "student_experience_page.dart"
PROFESSOR_REPOSITORY = ROOT / "03_app_flutter" / "fitnexus_app" / "lib" / "features" / "professor" / "professor_data_repository.dart"
WEB_INDEX = ROOT / "03_app_flutter" / "fitnexus_app" / "web" / "index.html"


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


def main() -> None:
    sql = read(MIGRATION).lower()
    workout = read(WORKOUT_REPOSITORY)
    feedback = read(FEEDBACK_REPOSITORY)
    command_id = read(COMMAND_ID)
    experience = read(EXPERIENCE)
    professor = read(PROFESSOR_REPOSITORY)
    web_index = read(WEB_INDEX).lower()

    # Finite bearer lifetime + explicit rotation/revocation lineage.
    for needle in (
        "expires_at = now() + interval '30 days'",
        "revoked_at timestamptz",
        "revocation_reason text",
        "rotated_from_link_id uuid",
        "rotation_number integer not null default 1",
        "issue_student_access_token_v2",
        "student_access_rotation_cooldown",
    ):
        require(
            sql,
            needle,
            "BGF-STUDENT-ACCESS-UNBOUNDED-BEARER-147",
            f"finite lifetime/rotation invariant disappeared: {needle}",
        )

    # Successful anonymous traffic is rate bounded and leaves operational telemetry.
    for needle in (
        "private.student_access_rate_buckets",
        "student_access_rate_limited",
        "private.student_access_security_events",
        "'rate_limited'",
        "p_limit_per_minute",
    ):
        require(
            sql,
            needle,
            "BGF-STUDENT-ACCESS-RATE-LIMIT-149",
            f"rate-limit/abuse-monitoring invariant disappeared: {needle}",
        )

    # Mutable possession-token commands carry a 128-bit random command id and
    # server-side receipt, so duplicate delivery cannot apply the same command twice.
    for needle in (
        "private.student_access_command_receipts",
        "command_id ~ '^[0-9a-f]{32}$'",
        "student_access_command_begin_v2",
        "student_access_command_finish_v2",
        "'replay'",
    ):
        require(
            sql,
            needle,
            "BGF-STUDENT-ACCESS-REPLAY-148",
            f"replay/idempotency invariant disappeared: {needle}",
        )

    require(
        command_id,
        "Random.secure()",
        "BGF-STUDENT-ACCESS-REPLAY-148",
        "client command ids must use a cryptographically secure RNG",
    )
    require(
        command_id,
        "index < 16",
        "BGF-STUDENT-ACCESS-REPLAY-148",
        "client command ids must retain 16 random bytes / 128 bits",
    )

    # Client code must use only the hardened v2 boundary.
    for needle in (
        "'get_student_workout_v2'",
        "'start_student_workout_v2'",
        "'set_student_exercise_completion_v2'",
        "'p_command_id'",
    ):
        require(
            workout,
            needle,
            "BGF-STUDENT-ACCESS-LEGACY-RPC-BYPASS-151",
            f"workout client bypassed the v2 boundary: {needle}",
        )

    for needle in (
        "'get_student_feedback_context_v2'",
        "'submit_student_workout_feedback_v2'",
        "'p_command_id'",
    ):
        require(
            feedback,
            needle,
            "BGF-STUDENT-ACCESS-LEGACY-RPC-BYPASS-151",
            f"feedback client bypassed the v2 boundary: {needle}",
        )

    require(
        professor,
        "'issue_student_access_token_v2'",
        "BGF-STUDENT-ACCESS-LEGACY-RPC-BYPASS-151",
        "professor token issuance must use the bounded v2 rotation boundary",
    )

    for legacy_grant in (
        "revoke execute on function public.issue_student_access_token(uuid) from authenticated",
        "revoke execute on function public.get_student_workout(text) from anon, authenticated",
        "revoke execute on function public.start_student_workout(text) from anon, authenticated",
        "revoke execute on function public.set_student_exercise_completion(text,uuid,uuid,boolean) from anon, authenticated",
        "revoke execute on function public.get_student_feedback_context(text) from anon, authenticated",
        "revoke execute on function public.submit_student_workout_feedback(text,uuid,integer,integer,integer,text,text) from anon, authenticated",
    ):
        require(
            sql,
            legacy_grant,
            "BGF-STUDENT-ACCESS-LEGACY-RPC-BYPASS-151",
            f"legacy RPC remained client-callable: {legacy_grant}",
        )

    # Bearer tokens may be in the fragment route, never in the top-level query string.
    forbid(
        experience,
        "Uri.base.queryParameters['token']",
        "BGF-STUDENT-ACCESS-URL-LEAK-150",
        "student bearer token must not be read from the top-level URL query string",
    )
    require(
        experience,
        "Uri.base.fragment",
        "BGF-STUDENT-ACCESS-URL-LEAK-150",
        "student bearer token must remain fragment-scoped",
    )
    require(
        web_index,
        '<meta name="referrer" content="no-referrer">',
        "BGF-STUDENT-ACCESS-URL-LEAK-150",
        "web shell must keep an explicit no-referrer policy",
    )

    print("STUDENT_ACCESS_SECURITY_CONTRACT_GUARD=PASS")
    print("FINITE_TOKEN_LIFETIME=PASS")
    print("RATE_LIMIT_BOUNDARY=PASS")
    print("COMMAND_REPLAY_DEFENSE=PASS")
    print("LEGACY_RPC_BYPASS=DENIED")
    print("TOKEN_QUERY_LEAK=DENIED")


if __name__ == "__main__":
    main()
