from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS = ROOT / "04_backend_supabase" / "migrations"
PROFESSOR = ROOT / "03_app_flutter" / "fitnexus_app" / "lib" / "features" / "professor"


def fail(code: str, detail: str) -> None:
    print("COACH_ACTION_CENTER_CONTRACT_GATE=FAIL")
    print(f"FAILURE_CLASS={code}")
    print(f"DETAIL={detail}")
    raise SystemExit(1)


def require(text: str, needle: str, code: str, detail: str) -> None:
    if needle not in text:
        fail(code, detail)


def forbid(text: str, needle: str, code: str, detail: str) -> None:
    if needle in text:
        fail(code, detail)


def read(path: Path, code: str) -> str:
    if not path.exists():
        fail(code, f"required file missing: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def main() -> int:
    migrations = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(MIGRATIONS.glob("*.sql"))
    )
    repository = read(
        PROFESSOR / "professor_coach_action_repository.dart",
        "BGF-ACTION-CENTER-FILE-MISSING-031",
    )
    page = read(
        PROFESSOR / "professor_coach_action_center_page.dart",
        "BGF-ACTION-CENTER-FILE-MISSING-031",
    )
    shell = read(
        PROFESSOR / "authenticated_professor_page.dart",
        "BGF-ACTION-CENTER-FILE-MISSING-031",
    )

    checks = [
        (
            migrations,
            "coach_action_events",
            "BGF-ACTION-EVIDENCE-032",
            "immutable action resolution ledger disappeared",
        ),
        (
            migrations,
            "get_coach_action_center",
            "BGF-ACTION-PRIORITY-CONTRACT-033",
            "Coach Action Center ranking RPC disappeared",
        ),
        (
            migrations,
            "record_coach_action_event",
            "BGF-ACTION-EVIDENCE-032",
            "controlled action resolution command disappeared",
        ),
        (
            migrations,
            "STALE_ACTION_CONTEXT",
            "BGF-ACTION-STALE-CONTEXT-034",
            "stale action fingerprint interlock disappeared",
        ),
        (
            migrations,
            "event.created_at >= now() - interval '24 hours'",
            "BGF-ACTION-RECURRENCE-035",
            "24-hour completion suppression contract drifted",
        ),
        (
            migrations,
            "p_snooze_until > now() + interval '7 days'",
            "BGF-ACTION-SNOOZE-BOUNDARY-036",
            "bounded snooze contract disappeared",
        ),
        (
            migrations,
            "'auto_change_prescription', false",
            "BGF-ACTION-NO-AUTO-PRESCRIPTION-037",
            "no-auto-prescription guardrail disappeared",
        ),
        (
            migrations,
            "'auto_contact_student', false",
            "BGF-ACTION-NO-AUTO-CONTACT-038",
            "no-auto-contact guardrail disappeared",
        ),
        (
            migrations,
            "'human_action_required', true",
            "BGF-ACTION-HUMAN-AUTHORITY-039",
            "human authority contract disappeared",
        ),
        (
            migrations,
            "where not coalesce(",
            "BGF-SQL-THREE-VALUED-LEFT-JOIN-045",
            "LEFT JOIN suppression must coalesce NULL to FALSE so fresh actions stay visible",
        ),
        (
            repository,
            "get_coach_action_center",
            "BGF-ACTION-FLUTTER-BINDING-040",
            "Flutter ranking RPC binding disappeared",
        ),
        (
            repository,
            "record_coach_action_event",
            "BGF-ACTION-FLUTTER-BINDING-040",
            "Flutter resolution RPC binding disappeared",
        ),
        (
            page,
            "Concluir por hoje",
            "BGF-ACTION-WORKFLOW-041",
            "daily completion workflow disappeared",
        ),
        (
            page,
            "Lembrar amanhã",
            "BGF-ACTION-WORKFLOW-041",
            "daily snooze workflow disappeared",
        ),
        (
            shell,
            "ProfessorCoachActionCenterPage()",
            "BGF-ACTION-DAILY-ENTRYPOINT-042",
            "Action Center stopped being the professor daily entrypoint",
        ),
    ]

    for text, needle, code, detail in checks:
        require(text, needle, code, detail)

    require(
        migrations,
        "revoke all on public.coach_action_events from anon, authenticated;",
        "BGF-ACTION-LEDGER-WRITE-AUTHORITY-043",
        "action ledger must deny direct client mutation",
    )
    require(
        migrations,
        "grant select on public.coach_action_events to authenticated;",
        "BGF-ACTION-LEDGER-WRITE-AUTHORITY-043",
        "authenticated users lost read access to their RLS-protected action evidence",
    )
    forbid(
        migrations,
        "grant insert on public.coach_action_events to authenticated",
        "BGF-ACTION-LEDGER-WRITE-AUTHORITY-043",
        "direct authenticated INSERT into the action evidence ledger is forbidden",
    )

    for signature in (
        "public.get_coach_action_center(uuid)",
        "public.record_coach_action_event(uuid,uuid,text,text,text,timestamptz)",
    ):
        require(
            migrations,
            f"revoke execute on function {signature} from public, anon;",
            "BGF-ACTION-RPC-AUTHORITY-044",
            f"anonymous execute revoke missing for {signature}",
        )
        require(
            migrations,
            f"grant execute on function {signature} to authenticated;",
            "BGF-ACTION-RPC-AUTHORITY-044",
            f"authenticated execute grant missing for {signature}",
        )

    print("COACH_ACTION_CENTER_CONTRACT_GATE=PASS")
    print("PRIORITY_CONTRACT=PASS")
    print("STALE_CONTEXT_INTERLOCK=PASS")
    print("NULL_VISIBILITY_SEMANTICS=PASS")
    print("ACTION_LEDGER_AUTHORITY=PASS")
    print("NO_AUTO_PRESCRIPTION=PASS")
    print("NO_AUTO_CONTACT=PASS")
    print("HUMAN_AUTHORITY=PASS")
    print("DAILY_ENTRYPOINT=PASS")
    print("FLUTTER_BINDING=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
