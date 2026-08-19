from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "04_backend_supabase" / "migrations" / "20260819060000_stage19_public_funnel_capture.sql"
APP = ROOT / "03_app_flutter" / "fitnexus_app" / "lib"
TELEMETRY = APP / "features" / "growth" / "public_funnel_telemetry.dart"
LANDING = APP / "features" / "landing" / "responsive_landing_page.dart"
AUTH = APP / "features" / "auth" / "auth_preview_page.dart"
ROUTES = APP / "app" / "fitnexus_app.dart"


def fail(code: str, detail: str) -> None:
    print("PUBLIC_FUNNEL_CAPTURE_CONTRACT_GATE=FAIL")
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
        fail(code, f"required artifact missing: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def declared_columns(create_table_body: str) -> set[str]:
    """Extract declared identifiers without treating substrings as columns.

    This deliberately prevents `name` from matching a legitimate column such as
    `event_name`. Historical substring gates created false positives and are not
    acceptable for privacy contracts.
    """
    columns: set[str] = set()
    for line in create_table_body.splitlines():
        candidate = line.strip().rstrip(",")
        if not candidate or candidate.startswith(("check ", "constraint ", "primary ", "unique ", "foreign ")):
            continue
        match = re.match(r"^([a-z_][a-z0-9_]*)\s+", candidate)
        if match is not None:
            columns.add(match.group(1))
    return columns


def main() -> int:
    migration = read(MIGRATION, "BGF-PUBLIC-FUNNEL-FILE-MISSING-116").lower()
    telemetry = read(TELEMETRY, "BGF-PUBLIC-FUNNEL-FILE-MISSING-116")
    landing = read(LANDING, "BGF-PUBLIC-FUNNEL-FILE-MISSING-116")
    auth = read(AUTH, "BGF-PUBLIC-FUNNEL-FILE-MISSING-116")
    routes = read(ROUTES, "BGF-PUBLIC-FUNNEL-FILE-MISSING-116")

    checks = [
        (migration, "create schema if not exists telemetry_private", "BGF-PUBLIC-FUNNEL-DEDICATED-SCHEMA-117", "dedicated anonymous telemetry authority schema disappeared"),
        (migration, "grant usage on schema telemetry_private to anon, authenticated, service_role", "BGF-PUBLIC-FUNNEL-DEDICATED-SCHEMA-117", "anonymous capture schema usage contract drifted"),
        (migration, "telemetry_private.public_growth_events", "BGF-PUBLIC-FUNNEL-ROW-AUTHORITY-118", "public funnel evidence table disappeared"),
        (migration, "visitor_key_hash", "BGF-PUBLIC-FUNNEL-PII-BOUNDARY-119", "visitor hash boundary disappeared"),
        (migration, "extensions.digest(v_visitor_key, 'sha256')", "BGF-PUBLIC-FUNNEL-PII-BOUNDARY-119", "raw visitor key is no longer server-hashed"),
        (migration, "public_growth_events_dedupe_uidx", "BGF-PUBLIC-FUNNEL-ABUSE-DAMPING-120", "daily visitor/path/touch deduplication disappeared"),
        (migration, "event_day", "BGF-PUBLIC-FUNNEL-ABUSE-DAMPING-120", "capture deduplication lost its bounded day bucket"),
        (migration, "position('?' in landing_path) = 0", "BGF-PUBLIC-FUNNEL-PII-BOUNDARY-119", "landing table must reject query strings"),
        (migration, "position('#' in landing_path) = 0", "BGF-PUBLIC-FUNNEL-PII-BOUNDARY-119", "landing table must reject fragments"),
        (migration, "telemetry_private.capture_public_growth_event_authority", "BGF-PUBLIC-FUNNEL-RPC-AUTHORITY-121", "private public-capture authority disappeared"),
        (migration, "public.capture_public_growth_event", "BGF-PUBLIC-FUNNEL-RPC-AUTHORITY-121", "public capture wrapper disappeared"),
        (migration, "security invoker", "BGF-PUBLIC-FUNNEL-RPC-AUTHORITY-121", "public capture wrapper lost invoker semantics"),
        (migration, "security definer", "BGF-PUBLIC-FUNNEL-RPC-AUTHORITY-121", "dedicated private mutation authority lost definer semantics"),
        (migration, "grant execute on function public.capture_public_growth_event", "BGF-PUBLIC-FUNNEL-RPC-AUTHORITY-121", "anonymous public capture execute grant disappeared"),
        (migration, "to anon, authenticated", "BGF-PUBLIC-FUNNEL-RPC-AUTHORITY-121", "public capture must remain available before login"),
        (migration, "capture_authority = 'public_capture'", "BGF-PUBLIC-FUNNEL-CAPTURE-GATE-122", "event catalog was not promoted to real public capture authority"),
        (migration, "capture_status = 'active'", "BGF-PUBLIC-FUNNEL-CAPTURE-GATE-122", "public acquisition events are not active"),
        (migration, "'tracking_core_gate'", "BGF-PUBLIC-FUNNEL-CAPTURE-GATE-122", "tracking-core readiness signal disappeared"),
        (migration, "'ads_release_gate', 'blocked_by_separate_release_gates'", "BGF-PUBLIC-FUNNEL-ADS-SEPARATION-123", "tracking completion must not silently open ads release"),
        (telemetry, "captureLandingView", "BGF-PUBLIC-FUNNEL-FLUTTER-BINDING-124", "landing capture binding disappeared"),
        (telemetry, "captureSignupStarted", "BGF-PUBLIC-FUNNEL-FLUTTER-BINDING-124", "signup-start capture binding disappeared"),
        (telemetry, "SharedPreferences", "BGF-PUBLIC-FUNNEL-VISITOR-STABILITY-125", "anonymous visitor key lost bounded persistence"),
        (telemetry, "math.Random.secure()", "BGF-PUBLIC-FUNNEL-VISITOR-STABILITY-125", "visitor key generation lost cryptographic randomness"),
        (telemetry, "Public funnel telemetry failed without blocking navigation or signup.", "BGF-PUBLIC-FUNNEL-FAILOPEN-126", "public telemetry must remain observable and fail-open"),
        (landing, "captureLandingView", "BGF-PUBLIC-FUNNEL-LANDING-ENTRY-127", "landing route no longer emits landing_view"),
        (landing, "public-signup-entry", "BGF-PUBLIC-FUNNEL-SIGNUP-ENTRY-128", "explicit online signup CTA disappeared"),
        (landing, "pushNamed('/start')", "BGF-PUBLIC-FUNNEL-SIGNUP-ENTRY-128", "public signup CTA no longer enters the tracked signup route"),
        (auth, "initialRegisterMode", "BGF-PUBLIC-FUNNEL-SIGNUP-ENTRY-128", "explicit signup route no longer opens registration mode"),
        (auth, "captureSignupStarted", "BGF-PUBLIC-FUNNEL-SIGNUP-ENTRY-128", "registration mode lost signup_started capture"),
        (routes, "'/start': (_) => const AuthPreviewPage(initialRegisterMode: true)", "BGF-PUBLIC-FUNNEL-SIGNUP-ENTRY-128", "tracked public signup route disappeared"),
    ]
    for text, needle, code, detail in checks:
        require(text, needle, code, detail)

    table_match = re.search(
        r"create table if not exists telemetry_private\.public_growth_events \((.*?)\);",
        migration,
        flags=re.DOTALL,
    )
    if table_match is None:
        fail("BGF-PUBLIC-FUNNEL-ROW-AUTHORITY-118", "could not isolate public growth event table")

    columns = declared_columns(table_match.group(1))
    forbidden_columns = {
        "email",
        "name",
        "phone",
        "student_id",
        "organization_id",
        "payload",
        "metadata",
        "query_string",
        "referrer_url",
        "ip_address",
    }
    violations = sorted(columns.intersection(forbidden_columns))
    if violations:
        fail(
            "BGF-PUBLIC-FUNNEL-PII-BOUNDARY-119",
            f"anonymous acquisition table contains forbidden columns: {', '.join(violations)}",
        )

    for forbidden_grant, detail in (
        ("grant select on telemetry_private.public_growth_events to anon", "anon must not read raw public-growth evidence"),
        ("grant insert on telemetry_private.public_growth_events to anon", "anon must not bypass the capture RPC"),
        ("grant update on telemetry_private.public_growth_events to anon", "anon must not rewrite public-growth evidence"),
        ("grant delete on telemetry_private.public_growth_events to anon", "anon must not delete public-growth evidence"),
        ("grant select on telemetry_private.public_growth_events to authenticated", "authenticated clients must not read raw public-growth evidence"),
        ("grant insert on telemetry_private.public_growth_events to authenticated", "authenticated clients must not bypass the capture RPC"),
    ):
        forbid(migration, forbidden_grant, "BGF-PUBLIC-FUNNEL-ROW-AUTHORITY-118", detail)

    forbid(
        migration,
        "grant usage on schema private to anon",
        "BGF-PUBLIC-FUNNEL-DEDICATED-SCHEMA-117",
        "anonymous public capture must use telemetry_private rather than exposing the application private schema",
    )

    wrapper_match = re.search(
        r"create or replace function public\.capture_public_growth_event\(.*?\$\$;",
        migration,
        flags=re.DOTALL,
    )
    if wrapper_match is None or "security invoker" not in wrapper_match.group(0):
        fail("BGF-PUBLIC-FUNNEL-RPC-AUTHORITY-121", "public capture RPC must remain SECURITY INVOKER")

    helper_match = re.search(
        r"create or replace function telemetry_private\.capture_public_growth_event_authority\(.*?\$\$;",
        migration,
        flags=re.DOTALL,
    )
    if helper_match is None or "security definer" not in helper_match.group(0):
        fail("BGF-PUBLIC-FUNNEL-RPC-AUTHORITY-121", "dedicated capture authority must remain a non-public SECURITY DEFINER")

    print("PUBLIC_FUNNEL_CAPTURE_CONTRACT_GATE=PASS")
    print("LANDING_VIEW=ACTIVE_PUBLIC_CAPTURE")
    print("SIGNUP_STARTED=ACTIVE_PUBLIC_CAPTURE")
    print("RAW_VISITOR_KEY_STORED=NO")
    print("ARBITRARY_QUERY_PAYLOAD_STORED=NO")
    print("PUBLIC_ROW_DIRECT_MUTATION=DENIED")
    print("ABUSE_DAMPING=VISITOR_PATH_TOUCH_DAY_DEDUPE")
    print("PUBLIC_CAPTURE_WRAPPER=SECURITY_INVOKER")
    print("CAPTURE_AUTHORITY_SCHEMA=TELEMETRY_PRIVATE")
    print("PUBLIC_TELEMETRY=FAIL_OPEN")
    print("TRACKING_CORE=READY")
    print("ADS_RELEASE_GATE=SEPARATE_BLOCKED")
    print("PII_COLUMN_CHECK=EXACT_IDENTIFIER_MATCH")
    return 0


if __name__ == "__main__":
    sys.exit(main())
