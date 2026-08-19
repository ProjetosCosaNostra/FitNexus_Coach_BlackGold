from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS = ROOT / "04_backend_supabase" / "migrations"
PROFESSOR = ROOT / "03_app_flutter" / "fitnexus_app" / "lib" / "features" / "professor"


def fail(code: str, detail: str) -> None:
    print("SUBSCRIPTION_ENTITLEMENT_CONTRACT_GATE=FAIL")
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
        PROFESSOR / "professor_subscription_repository.dart",
        "BGF-SUBSCRIPTION-FILE-MISSING-046",
    )
    page = read(
        PROFESSOR / "professor_subscription_page.dart",
        "BGF-SUBSCRIPTION-FILE-MISSING-046",
    )
    shell = read(
        PROFESSOR / "authenticated_professor_page.dart",
        "BGF-SUBSCRIPTION-FILE-MISSING-046",
    )

    checks = [
        (migrations, "subscription_plans", "BGF-SUBSCRIPTION-PLAN-AUTHORITY-047", "provider-neutral plan catalog disappeared"),
        (migrations, "organization_subscriptions", "BGF-SUBSCRIPTION-STATE-AUTHORITY-048", "organization subscription authority disappeared"),
        (migrations, "subscription_authority_events", "BGF-SUBSCRIPTION-EVENT-EVIDENCE-049", "immutable subscription authority event ledger disappeared"),
        (migrations, "'trial','BlackGold Trial','active',10,1,14", "BGF-SUBSCRIPTION-TRIAL-BOOTSTRAP-050", "14-day trial bootstrap contract drifted"),
        (migrations, "aa_on_organization_subscription_created", "BGF-SUBSCRIPTION-TRIAL-BOOTSTRAP-050", "automatic trial initialization trigger disappeared"),
        (migrations, "students_subscription_limit_gate", "BGF-SUBSCRIPTION-STUDENT-LIMIT-051", "server-side student capacity gate disappeared"),
        (migrations, "organization_members_subscription_limit_gate", "BGF-SUBSCRIPTION-MEMBER-LIMIT-052", "server-side team capacity gate disappeared"),
        (migrations, "training_plans_subscription_write_gate", "BGF-SUBSCRIPTION-WRITE-GATE-053", "training-plan commercial write gate disappeared"),
        (migrations, "decision_intelligence_subscription_gate", "BGF-SUBSCRIPTION-FEATURE-GATE-054", "Decision Intelligence entitlement gate disappeared"),
        (migrations, "get_subscription_entitlement_snapshot", "BGF-SUBSCRIPTION-SNAPSHOT-055", "subscription/usage snapshot RPC disappeared"),
        (migrations, "'state', 'UNFROZEN'", "BGF-SUBSCRIPTION-PRICE-AUTHORITY-056", "pricing must stay explicitly unfrozen until a provider/pricing decision is promoted"),
        (migrations, "'provider_neutral_core', true", "BGF-SUBSCRIPTION-PROVIDER-COUPLING-057", "provider-neutral entitlement guardrail disappeared"),
        (migrations, "apply_subscription_authority_event", "BGF-SUBSCRIPTION-PROVIDER-EVENT-058", "controlled provider authority event command disappeared"),
        (migrations, "idempotent_replay", "BGF-SUBSCRIPTION-EVENT-IDEMPOTENCY-059", "provider event replay protection disappeared"),
        (repository, "get_subscription_entitlement_snapshot", "BGF-SUBSCRIPTION-FLUTTER-BINDING-060", "Flutter subscription snapshot RPC binding disappeared"),
        (page, "Plano & assinatura", "BGF-SUBSCRIPTION-WORKSPACE-061", "professor subscription workspace disappeared"),
        (shell, "ProfessorSubscriptionPage()", "BGF-SUBSCRIPTION-ENTRYPOINT-062", "subscription workspace entrypoint disappeared"),
    ]

    for text, needle, code, detail in checks:
        require(text, needle, code, detail)

    for table in (
        "public.subscription_plans",
        "public.organization_subscriptions",
        "public.subscription_authority_events",
    ):
        require(
            migrations,
            f"alter table {table} enable row level security;",
            "BGF-SUBSCRIPTION-RLS-063",
            f"RLS missing for {table}",
        )

    require(
        migrations,
        "revoke all on public.organization_subscriptions from anon, authenticated;",
        "BGF-SUBSCRIPTION-CLIENT-MUTATION-064",
        "subscription state must start from deny-all client privileges",
    )
    require(
        migrations,
        "grant select on public.organization_subscriptions to authenticated;",
        "BGF-SUBSCRIPTION-CLIENT-MUTATION-064",
        "authenticated members lost read access to their subscription state",
    )
    forbid(
        migrations,
        "grant update on public.organization_subscriptions to authenticated",
        "BGF-SUBSCRIPTION-CLIENT-MUTATION-064",
        "Flutter clients must never update subscription authority directly",
    )
    forbid(
        migrations,
        "grant insert on public.subscription_authority_events to authenticated",
        "BGF-SUBSCRIPTION-EVENT-EVIDENCE-049",
        "clients must never fabricate provider/subscription authority events",
    )

    apply_signature = (
        "public.apply_subscription_authority_event(uuid,text,text,text,text,"
        "timestamptz,timestamptz,timestamptz,boolean,text,text,text,text)"
    )
    require(
        migrations,
        f"revoke execute on function {apply_signature} from public, anon, authenticated;",
        "BGF-SUBSCRIPTION-PROVIDER-AUTHORITY-065",
        "subscription authority event RPC must be denied to normal clients",
    )
    require(
        migrations,
        f"grant execute on function {apply_signature} to service_role;",
        "BGF-SUBSCRIPTION-PROVIDER-AUTHORITY-065",
        "provider adapter authority must be isolated to service_role",
    )

    # BGF-SUBSCRIPTION-SERVICE-LEAST-PRIVILEGE-067:
    # the provider adapter may read the catalog, update subscription state and
    # append authority evidence. It must not rewrite plans or historical events.
    require(
        migrations,
        "revoke all on public.subscription_plans from service_role;",
        "BGF-SUBSCRIPTION-SERVICE-LEAST-PRIVILEGE-067",
        "service role plan authority must be reset before narrow grants",
    )
    require(
        migrations,
        "grant select on public.subscription_plans to service_role;",
        "BGF-SUBSCRIPTION-SERVICE-LEAST-PRIVILEGE-067",
        "provider adapter needs catalog read but not catalog mutation",
    )
    require(
        migrations,
        "grant select, update on public.organization_subscriptions to service_role;",
        "BGF-SUBSCRIPTION-SERVICE-LEAST-PRIVILEGE-067",
        "provider adapter lost controlled subscription state transition authority",
    )
    require(
        migrations,
        "grant select, insert on public.subscription_authority_events to service_role;",
        "BGF-SUBSCRIPTION-SERVICE-LEAST-PRIVILEGE-067",
        "provider adapter must append but not rewrite subscription evidence",
    )

    require(
        migrations,
        "revoke execute on function public.get_subscription_entitlement_snapshot(uuid) from public, anon;",
        "BGF-SUBSCRIPTION-RPC-AUTHORITY-066",
        "anonymous entitlement snapshot access must remain denied",
    )
    require(
        migrations,
        "grant execute on function public.get_subscription_entitlement_snapshot(uuid) to authenticated;",
        "BGF-SUBSCRIPTION-RPC-AUTHORITY-066",
        "authenticated entitlement snapshot access disappeared",
    )

    print("SUBSCRIPTION_ENTITLEMENT_CONTRACT_GATE=PASS")
    print("PLAN_AUTHORITY=PASS")
    print("TRIAL_BOOTSTRAP=PASS")
    print("STUDENT_LIMIT_GATE=PASS")
    print("MEMBER_LIMIT_GATE=PASS")
    print("TRAINING_WRITE_GATE=PASS")
    print("DECISION_INTELLIGENCE_GATE=PASS")
    print("PROVIDER_NEUTRAL_CORE=PASS")
    print("PROVIDER_EVENT_IDEMPOTENCY=PASS")
    print("SERVICE_ROLE_LEAST_PRIVILEGE=PASS")
    print("DIRECT_CLIENT_MUTATION=DENIED")
    print("FLUTTER_BINDING=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
