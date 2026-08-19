from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS = ROOT / "04_backend_supabase" / "migrations"
APP = ROOT / "03_app_flutter" / "fitnexus_app" / "lib"

STAGE5 = MIGRATIONS / "20260818152500_stage5_student_access_workout_execution.sql"
DIRECT_DENY = MIGRATIONS / "20260818203000_stage8_student_access_direct_deny_policy.sql"
STAGE21 = MIGRATIONS / "20260819103700_stage21_student_access_security_boundary.sql"
STAGE22 = MIGRATIONS / "20260819114500_stage22_tenant_isolation_relational_interlock.sql"

FAILURE_CLASSES = (
    "BGF-TENANT-RELATIONSHIP-DECOUPLING-154",
    "BGF-TENANT-ANON-RPC-DOWNGRADE-155",
    "BGF-TENANT-DIRECT-TABLE-BYPASS-156",
    "BGF-TENANT-CLIENT-RPC-DOWNGRADE-157",
)


def fail(message: str) -> None:
    raise SystemExit("TENANT_ISOLATION_CONTRACT_GUARD=FAIL\n" + message)


def read(path: Path) -> str:
    if not path.is_file():
        fail(f"missing required contract source: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def require(text: str, fragments: list[str], label: str) -> None:
    missing = [fragment for fragment in fragments if fragment not in text]
    if missing:
        fail(f"{label} missing required invariants: {missing}")


def main() -> None:
    stage5 = read(STAGE5).lower()
    stage22 = read(STAGE22).lower()
    stage21 = read(STAGE21).lower()
    direct_deny = read(DIRECT_DENY).lower()
    all_sql = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in sorted(MIGRATIONS.glob("*.sql"))
    )

    require(
        stage22,
        [
            "bgf-tenant-relationship-decoupling-154",
            "student_access_links_id_student_org_uq",
            "foreign key (rotated_from_link_id, student_id, organization_id)",
            "references public.student_access_links(id, student_id, organization_id)",
            "on delete set null (rotated_from_link_id)",
            "student_access_links_rotation_not_self_chk",
            "check (rotated_from_link_id is null or rotated_from_link_id <> id)",
            "foreign key (student_access_link_id, student_id, organization_id)",
            "on delete set null (student_access_link_id)",
            "drop constraint if exists workout_sessions_student_access_link_id_fkey",
            "drop constraint if exists student_access_links_rotated_from_link_id_fkey",
        ],
        FAILURE_CLASSES[0],
    )

    legacy_rpcs = [
        "get_student_workout(text)",
        "start_student_workout(text)",
        "set_student_exercise_completion(text,uuid,uuid,boolean)",
        "get_student_feedback_context(text)",
        "submit_student_workout_feedback(text,uuid,integer,integer,integer,text,text)",
    ]
    for signature in legacy_rpcs:
        expected = (
            f"revoke all on function public.{signature} from public, anon, authenticated;"
        )
        if expected not in stage21:
            fail(f"{FAILURE_CLASSES[1]} legacy anonymous RPC not fail-closed: {signature}")

    v2_rpcs = [
        "get_student_workout_v2(text)",
        "start_student_workout_v2(text,text)",
        "set_student_exercise_completion_v2(text,uuid,uuid,boolean,text)",
        "get_student_feedback_context_v2(text)",
        "submit_student_workout_feedback_v2(text,uuid,integer,integer,integer,text,text,text)",
    ]
    for signature in v2_rpcs:
        expected = f"grant execute on function public.{signature} to anon, authenticated;"
        if expected not in stage21:
            fail(f"{FAILURE_CLASSES[1]} expected v2 anonymous boundary missing: {signature}")

    require(
        stage5,
        [
            "revoke all on public.student_access_links from anon, authenticated",
            "revoke all on public.workout_sessions from anon, authenticated",
            "revoke all on public.workout_exercise_logs from anon, authenticated",
        ],
        FAILURE_CLASSES[2],
    )
    require(
        direct_deny,
        [
            "create policy student_access_links_deny_direct",
            "for all",
            "to anon, authenticated",
            "using (false)",
            "with check (false)",
        ],
        FAILURE_CLASSES[2],
    )

    forbidden_direct_anon_grants = [
        "grant select on public.student_access_links to anon",
        "grant insert on public.student_access_links to anon",
        "grant update on public.student_access_links to anon",
        "grant delete on public.student_access_links to anon",
        "grant select on public.workout_sessions to anon",
        "grant insert on public.workout_sessions to anon",
        "grant update on public.workout_sessions to anon",
        "grant delete on public.workout_sessions to anon",
        "grant select on public.workout_exercise_logs to anon",
        "grant insert on public.workout_exercise_logs to anon",
        "grant update on public.workout_exercise_logs to anon",
        "grant delete on public.workout_exercise_logs to anon",
        "grant select on public.workout_feedback to anon",
        "grant insert on public.workout_feedback to anon",
        "grant update on public.workout_feedback to anon",
        "grant delete on public.workout_feedback to anon",
    ]
    forbidden = [marker for marker in forbidden_direct_anon_grants if marker in all_sql]
    if forbidden:
        fail(f"{FAILURE_CLASSES[2]} direct anon grants found: {forbidden}")

    legacy_call_markers = [
        ".rpc('get_student_workout'",
        '.rpc("get_student_workout"',
        ".rpc('start_student_workout'",
        '.rpc("start_student_workout"',
        ".rpc('set_student_exercise_completion'",
        '.rpc("set_student_exercise_completion"',
        ".rpc('get_student_feedback_context'",
        '.rpc("get_student_feedback_context"',
        ".rpc('submit_student_workout_feedback'",
        '.rpc("submit_student_workout_feedback"',
        ".rpc('issue_student_access_token'",
        '.rpc("issue_student_access_token"',
    ]

    offenders: list[str] = []
    for path in APP.rglob("*.dart"):
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in legacy_call_markers):
            offenders.append(path.relative_to(ROOT).as_posix())
    if offenders:
        fail(
            f"{FAILURE_CLASSES[3]} Flutter client references legacy RPCs: "
            + ", ".join(sorted(offenders))
        )

    experience = read(
        APP / "features" / "student" / "student_experience_page.dart"
    )
    if "Uri.base.queryParameters['token']" in experience or 'Uri.base.queryParameters["token"]' in experience:
        fail(f"{FAILURE_CLASSES[3]} bearer token returned to top-level query parameters")

    print("TENANT_ISOLATION_CONTRACT_GUARD=PASS")
    print("RELATIONAL_BINDING=STUDENT_ACCESS_LINK+STUDENT+ORGANIZATION")
    print("ROTATION_LINEAGE=SAME_STUDENT_SAME_ORGANIZATION")
    print("ANON_STUDENT_RPCS=V2_ONLY")
    print("DIRECT_STUDENT_TABLE_BYPASS=DENIED")
    print("CLIENT_LEGACY_RPC_CALLS=0")


if __name__ == "__main__":
    main()
