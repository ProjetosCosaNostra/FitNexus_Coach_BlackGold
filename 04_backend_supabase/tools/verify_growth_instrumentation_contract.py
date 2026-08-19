from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS = ROOT / "04_backend_supabase" / "migrations"
APP = ROOT / "03_app_flutter" / "fitnexus_app" / "lib"
PRIVATE_SNAPSHOT_HARDENING = (
    MIGRATIONS / "20260819055000_stage18_private_snapshot_authority_hardening.sql"
)


def fail(code: str, detail: str) -> None:
    print("GROWTH_INSTRUMENTATION_CONTRACT_GATE=FAIL")
    print(f"FAILURE_CLASS={code}")
    print(f"DETAIL={detail}")
    raise SystemExit(1)


def require(text: str, needle: str, code: str, detail: str) -> None:
    if needle not in text:
        fail(code, detail)


def forbid(text: str, needle: str, code: str, detail: str) -> None:
    if needle in text:
        fail(code, detail)


def main() -> int:
    migrations = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(MIGRATIONS.glob("*.sql"))
    ).lower()
    auth = (APP / "features" / "auth" / "auth_service.dart").read_text(encoding="utf-8")
    capture = (APP / "features" / "growth" / "growth_attribution_capture.dart").read_text(encoding="utf-8")

    if not PRIVATE_SNAPSHOT_HARDENING.exists():
        fail(
            "BGF-GROWTH-PRIVATE-BRIDGE-DIRECT-CALL-114",
            "private snapshot authority hardening migration disappeared",
        )
    snapshot_hardening = PRIVATE_SNAPSHOT_HARDENING.read_text(encoding="utf-8").lower()

    checks = [
        (migrations, "private.growth_event_catalog", "BGF-GROWTH-FUNNEL-AUTHORITY-100", "growth event catalog disappeared"),
        (migrations, "private.growth_events", "BGF-GROWTH-FUNNEL-AUTHORITY-100", "private growth event ledger disappeared"),
        (migrations, "private.growth_attribution", "BGF-GROWTH-ATTRIBUTION-FIRST-LAST-101", "first/last attribution authority disappeared"),
        (migrations, "private.growth_capture_failures", "BGF-GROWTH-TELEMETRY-CORE-BLOCK-113", "telemetry failure evidence disappeared"),
        (migrations, "('landing_view','acquisition','future_public_capture','pending'", "BGF-GROWTH-PUBLIC-CAPTURE-GAP-105", "landing_view must remain explicitly pending until public capture exists"),
        (migrations, "('signup_started','signup','future_public_capture','pending'", "BGF-GROWTH-PUBLIC-CAPTURE-GAP-105", "signup_started must remain explicitly pending until public capture exists"),
        (migrations, "'signup_completed'", "BGF-GROWTH-FUNNEL-AUTHORITY-100", "signup_completed server event disappeared"),
        (migrations, "'student_created'", "BGF-GROWTH-FUNNEL-AUTHORITY-100", "student_created server event disappeared"),
        (migrations, "'training_created_or_duplicated'", "BGF-GROWTH-FUNNEL-AUTHORITY-100", "training creation event disappeared"),
        (migrations, "'training_delivered'", "BGF-GROWTH-NORTH-STAR-SEMANTICS-103", "training delivery event disappeared"),
        (migrations, "'workout_logged'", "BGF-GROWTH-RETENTION-AUTHORITY-110", "workout completion event disappeared"),
        (migrations, "'trial_started'", "BGF-GROWTH-REVENUE-AUTHORITY-111", "trial event disappeared"),
        (migrations, "'checkout_started'", "BGF-GROWTH-REVENUE-AUTHORITY-111", "checkout event disappeared"),
        (migrations, "'paid'", "BGF-GROWTH-REVENUE-AUTHORITY-111", "paid transition event disappeared"),
        (migrations, "growth_events_entity_uidx", "BGF-GROWTH-TRIGGER-IDEMPOTENCY-107", "entity-level event deduplication disappeared"),
        (migrations, "growth_attribution_first_actor_user_id_idx", "BGF-GROWTH-FK-INDEX-112", "first-touch actor FK index disappeared"),
        (migrations, "growth_attribution_last_actor_user_id_idx", "BGF-GROWTH-FK-INDEX-112", "last-touch actor FK index disappeared"),
        (migrations, "coaches_with_at_least_one_training_delivery_in_last_7_days", "BGF-GROWTH-NORTH-STAR-SEMANTICS-103", "north-star operational definition drifted"),
        (migrations, "time_to_first_value_seconds", "BGF-GROWTH-TTFV-104", "time-to-first-value calculation disappeared"),
        (migrations, "blocked_tracking_incomplete", "BGF-GROWTH-PAID-MEDIA-PREMATURE-102", "paid-media gate no longer fails closed while public funnel capture is pending"),
        (migrations, "sensitive_health_payload_in_growth_events',false", "BGF-GROWTH-SENSITIVE-PAYLOAD-099", "growth snapshot lost explicit sensitive-health exclusion"),
        (migrations, "private.attach_growth_attribution_authority", "BGF-GROWTH-RPC-EXPOSED-DEFINER-106", "private attribution authority bridge disappeared"),
        (migrations, "private.get_growth_funnel_snapshot_authority", "BGF-GROWTH-RPC-EXPOSED-DEFINER-106", "private snapshot authority bridge disappeared"),
        (migrations, "public.attach_growth_attribution", "BGF-GROWTH-ATTRIBUTION-FIRST-LAST-101", "public attribution wrapper disappeared"),
        (migrations, "public.get_growth_funnel_snapshot", "BGF-GROWTH-FUNNEL-AUTHORITY-100", "public growth snapshot wrapper disappeared"),
        (migrations, "exception when others then", "BGF-GROWTH-TELEMETRY-CORE-BLOCK-113", "server telemetry lost its exception containment boundary"),
        (migrations, "error_fingerprint", "BGF-GROWTH-TELEMETRY-CORE-BLOCK-113", "telemetry failures lost non-payload diagnostic fingerprinting"),
        (capture, "utm_source", "BGF-GROWTH-ATTRIBUTION-FIRST-LAST-101", "UTM source capture disappeared"),
        (capture, "utm_medium", "BGF-GROWTH-ATTRIBUTION-FIRST-LAST-101", "UTM medium capture disappeared"),
        (capture, "utm_campaign", "BGF-GROWTH-ATTRIBUTION-FIRST-LAST-101", "UTM campaign capture disappeared"),
        (capture, "uri.path", "BGF-GROWTH-LANDING-PII-109", "relative landing-path capture disappeared"),
        (auth, "_attachGrowthAttributionIfPresent", "BGF-GROWTH-ATTRIBUTION-FAILOPEN-108", "organization bootstrap lost attribution attachment"),
        (auth, "Growth attribution capture failed without blocking core auth.", "BGF-GROWTH-ATTRIBUTION-FAILOPEN-108", "telemetry failure must remain observable and non-blocking"),
        (snapshot_hardening, "if auth.uid() is null", "BGF-GROWTH-PRIVATE-BRIDGE-DIRECT-CALL-114", "private snapshot authority must revalidate authentication internally"),
        (snapshot_hardening, "not private.is_org_member(p_organization_id)", "BGF-GROWTH-PRIVATE-BRIDGE-DIRECT-CALL-114", "private snapshot authority must revalidate tenant membership internally"),
        (snapshot_hardening, "security definer", "BGF-GROWTH-PRIVATE-BRIDGE-DIRECT-CALL-114", "private snapshot authority hardening lost its explicit definer boundary"),
    ]
    for text, needle, code, detail in checks:
        require(text, needle, code, detail)

    growth_table_match = re.search(
        r"create table if not exists private\.growth_events \((.*?)\);",
        migrations,
        flags=re.DOTALL,
    )
    if growth_table_match is None:
        fail("BGF-GROWTH-FUNNEL-AUTHORITY-100", "could not isolate growth_events table contract")
    growth_table = growth_table_match.group(1)
    for forbidden_column in ("metadata", "payload", "properties", "student_id", "email", "objective", "pain"):
        forbid(
            growth_table,
            forbidden_column,
            "BGF-GROWTH-SENSITIVE-PAYLOAD-099",
            f"growth event ledger must not carry arbitrary/sensitive field: {forbidden_column}",
        )

    failure_table_match = re.search(
        r"create table if not exists private\.growth_capture_failures \((.*?)\);",
        migrations,
        flags=re.DOTALL,
    )
    if failure_table_match is None:
        fail("BGF-GROWTH-TELEMETRY-CORE-BLOCK-113", "could not isolate growth_capture_failures contract")
    failure_table = failure_table_match.group(1)
    for forbidden_failure_column in ("error_message", "payload", "metadata", "email", "student_id"):
        forbid(
            failure_table,
            forbidden_failure_column,
            "BGF-GROWTH-SENSITIVE-PAYLOAD-099",
            f"growth failure evidence must not persist raw/sensitive field: {forbidden_failure_column}",
        )

    for forbidden_grant, code, detail in (
        ("grant insert on private.growth_events to authenticated", "BGF-GROWTH-CLIENT-EVENT-FABRICATION-098", "authenticated clients must not fabricate growth events"),
        ("grant update on private.growth_events to authenticated", "BGF-GROWTH-CLIENT-EVENT-FABRICATION-098", "authenticated clients must not rewrite growth events"),
        ("grant select on private.growth_events to authenticated", "BGF-GROWTH-SENSITIVE-PAYLOAD-099", "raw growth ledger must remain private"),
        ("grant select on private.growth_capture_failures to authenticated", "BGF-GROWTH-SENSITIVE-PAYLOAD-099", "failure fingerprints must remain internal"),
    ):
        forbid(migrations, forbidden_grant, code, detail)

    # Public wrappers remain invokers; private bridges own elevated authority and revalidate callers.
    for fn_name in ("attach_growth_attribution", "get_growth_funnel_snapshot"):
        pattern = rf"create or replace function public\.{fn_name}\(.*?security invoker"
        if re.search(pattern, migrations, flags=re.DOTALL) is None:
            fail("BGF-GROWTH-RPC-EXPOSED-DEFINER-106", f"public {fn_name} must remain SECURITY INVOKER")

    print("GROWTH_INSTRUMENTATION_CONTRACT_GATE=PASS")
    print("SERVER_FUNNEL_EVENTS=ACTIVE")
    print("PUBLIC_FUNNEL_CAPTURE=PENDING_EXPLICIT")
    print("PAID_MEDIA_GATE=BLOCKED_TRACKING_INCOMPLETE")
    print("GROWTH_EVENT_ARBITRARY_PAYLOAD=DENIED")
    print("DIRECT_CLIENT_EVENT_FABRICATION=DENIED")
    print("UTM_ATTRIBUTION=PRIVACY_MINIMIZED")
    print("NORTH_STAR=TRAINING_DELIVERY_7D")
    print("TTFV=SERVER_DERIVED")
    print("PUBLIC_WRAPPERS=SECURITY_INVOKER")
    print("SERVER_TELEMETRY=FAIL_OPEN_OBSERVABLE")
    print("GROWTH_FK_INDEX_COVERAGE=PASS")
    print("PRIVATE_BRIDGE_TENANT_REVALIDATION=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
