# FitNexus Coach BlackGold — Stage 19 Public Funnel Capture

## Purpose

Stage 19 closes the two public acquisition events that Stage 18 deliberately left pending:

- `landing_view`;
- `signup_started`.

The goal is **measurement readiness**, not ad launch. The FitNexus strategic contract requires conversion tracking and activation to be operational before meaningful paid media. Stage 19 therefore turns the tracking sub-gate green while keeping the overall ADS release gate explicitly blocked by separate commercial, legal and release conditions.

## Dedicated anonymous telemetry boundary

Anonymous capture does not reuse the application `private` schema.

Stage 19 creates a dedicated non-exposed schema:

`telemetry_private`

Only schema `USAGE` and execution of one narrow capture helper are granted to `anon`/`authenticated`. The raw acquisition table is not directly readable or writable by either role.

This prevents public-funnel requirements from broadening the authority surface of the application's existing private functions.

## Public event evidence

`telemetry_private.public_growth_events` stores only:

- `landing_view` or `signup_started`;
- a SHA-256 hash of a random client visitor key;
- a SHA-256 attribution-touch hash;
- a relative landing path without query string or fragment;
- bounded UTM source/medium/campaign/term/content;
- event day and timestamps.

It does **not** store:

- raw visitor key;
- email, name or phone;
- student or organization identity;
- health/pain/objective data;
- arbitrary payload/metadata;
- full query string;
- referrer URL;
- IP address.

## Capture authority

Public endpoint:

`public.capture_public_growth_event(...)`

is `SECURITY INVOKER`.

It delegates to:

`telemetry_private.capture_public_growth_event_authority(...)`

which is the dedicated non-exposed `SECURITY DEFINER` mutation boundary.

Both layers validate the event allowlist and path/visitor-key bounds. Direct INSERT/UPDATE/DELETE on the raw acquisition table remains denied to browser roles.

## Abuse damping — not a bot-proof claim

The server hashes the random visitor key and deduplicates by:

`event + visitor_hash + landing_path + attribution_touch_hash + event_day`

This prevents normal reloads/click repetition from inflating the same event indefinitely while preserving distinct campaign touches.

It is intentionally described as **abuse damping**, not bot prevention. A hostile client can generate new visitor keys. Reliable paid conversion decisions must therefore continue to rely on deeper server-authoritative milestones such as signup completion, activation and paid state, not raw landing views alone.

## Flutter capture

`PublicFunnelTelemetry` generates a persistent random visitor key using `Random.secure()` and stores it in `SharedPreferences`.

The browser sends that opaque key to the database only for hashing; the raw value is never stored in the server evidence table.

Capture is fail-open:

- telemetry errors are logged through `dart:developer`;
- landing rendering continues;
- signup navigation continues;
- auth/business writes do not depend on public telemetry success.

## Landing view

`ResponsiveLandingPage` is now stateful and emits `landing_view` from `initState()` without blocking rendering.

A persistent `Começar grátis` entry point routes to `/start`.

## Signup-start semantics

`/start` opens:

`AuthPreviewPage(initialRegisterMode: true)`

Entering registration mode emits `signup_started`. Switching manually from login to `Criar conta` also emits the event.

Daily server deduplication prevents repeated mode toggles from becoming unbounded event inflation for the same visitor/path/touch.

## Event catalog transition

Stage 18 registered `landing_view` and `signup_started` as:

`future_public_capture / pending`

Stage 19 promotes both to:

`public_capture / active`

The growth snapshot now reports:

- `tracking_core_gate = READY` when no public capture event remains pending;
- `ads_release_gate = BLOCKED_BY_SEPARATE_RELEASE_GATES`.

The second field is deliberate. Tracking readiness is necessary but not sufficient for paid-media release.

## Historical migration shadow prevention

Stage 19 exposed a weakness in the original static construction gate: scanning the concatenated migration history for a string can prove that a **historical** definition existed while missing that a newer migration superseded it.

The growth contract guard is now stage-aware. When the Stage 19 migration exists, it inspects that current authoritative transition instead of accepting the old Stage 18 `pending` strings as evidence of present state.

This is permanently registered as:

`BGF-CONTRACT-GATE-HISTORICAL-SHADOW-115`

Future gates that validate mutable database functions/state must inspect the latest authority file or otherwise resolve final migration order, not merely search all historical SQL.

## Exact-identifier static privacy checks

Before CI promotion, the first Stage 19 privacy guard was found to test forbidden column names through raw substring search. That would incorrectly treat the legitimate `event_name` column as a forbidden `name` column.

The guard was repaired before promotion: it now extracts declared SQL identifiers and compares forbidden names by exact identifier equality.

This is permanently registered as:

`BGF-CONTRACT-GATE-SUBSTRING-COLLISION-129`

Static privacy/security gates must never use unconstrained substring matching when one identifier can legally contain another identifier's text.

## Remote authority attestation

The authoritative Supabase project confirms:

- application schema `private`: anonymous `USAGE = false`;
- dedicated schema `telemetry_private`: anonymous `USAGE = true`;
- public capture wrapper: anonymous/authenticated `EXECUTE = true`, service-role direct public-wrapper execution intentionally false;
- public capture wrapper: `SECURITY INVOKER`;
- dedicated telemetry authority helper: `SECURITY DEFINER`;
- anonymous raw acquisition-table `SELECT = false`, `INSERT = false`;
- authenticated raw acquisition-table `SELECT = false`, `INSERT = false`;
- `landing_view` and `signup_started`: `public_capture / active`;
- no public-funnel rows were fabricated for validation;
- database remains without fabricated organizations/students.

The latest Security Advisor shows no new Stage 19 exposed public-definer warning; remaining warnings are the older possession-token student RPC boundary. The latest Performance Advisor shows no unindexed-foreign-key Stage 19 finding; only unused-index INFO notices appear on the empty/low-traffic database.

## Permanent prevention classes

- `BGF-CONTRACT-GATE-HISTORICAL-SHADOW-115`: historical migration text cannot satisfy a gate for current authority after a later migration supersedes it.
- `BGF-PUBLIC-FUNNEL-FILE-MISSING-116`: public-funnel migration/client/route artifacts cannot disappear silently.
- `BGF-PUBLIC-FUNNEL-DEDICATED-SCHEMA-117`: anonymous capture uses a dedicated non-exposed telemetry schema and must not broaden the application `private` schema to anon.
- `BGF-PUBLIC-FUNNEL-ROW-AUTHORITY-118`: browser roles cannot directly read/write the raw public-growth table.
- `BGF-PUBLIC-FUNNEL-PII-BOUNDARY-119`: anonymous acquisition evidence stores only hashed visitor identity, relative path and bounded UTM fields.
- `BGF-PUBLIC-FUNNEL-ABUSE-DAMPING-120`: normal duplicate public events are bounded by visitor/path/touch/day idempotency.
- `BGF-PUBLIC-FUNNEL-RPC-AUTHORITY-121`: public capture remains an invoker wrapper around a dedicated non-exposed definer authority.
- `BGF-PUBLIC-FUNNEL-CAPTURE-GATE-122`: public event catalog state becomes active only when real backend and Flutter capture artifacts coexist.
- `BGF-PUBLIC-FUNNEL-ADS-SEPARATION-123`: tracking readiness cannot silently open the overall ADS release gate.
- `BGF-PUBLIC-FUNNEL-FLUTTER-BINDING-124`: landing/signup events remain bound to the public capture RPC.
- `BGF-PUBLIC-FUNNEL-VISITOR-STABILITY-125`: anonymous visitor identity uses persistent cryptographically random opaque keys rather than user PII.
- `BGF-PUBLIC-FUNNEL-FAILOPEN-126`: public telemetry failures are observable but cannot block landing, navigation or signup.
- `BGF-PUBLIC-FUNNEL-LANDING-ENTRY-127`: the public landing route continues to emit `landing_view`.
- `BGF-PUBLIC-FUNNEL-SIGNUP-ENTRY-128`: an explicit online signup route opens registration mode and emits `signup_started`.
- `BGF-CONTRACT-GATE-SUBSTRING-COLLISION-129`: static contract gates compare parsed identifiers exactly rather than accepting unsafe substring matches.

## Current release posture

After Stage 19, the **tracking core** has a real path for public acquisition plus authenticated activation/revenue milestones.

This still does not authorize ad spend. Separate gates remain, including the external Asaas credential/checkout boundary and the wider release/legal readiness contract. No paid campaign is created or activated by this stage.
