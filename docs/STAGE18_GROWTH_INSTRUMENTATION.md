# FitNexus Coach BlackGold — Stage 18 Growth Instrumentation

## Purpose

Stage 18 turns acquisition, activation, retention and revenue measurement into a first-party system before meaningful paid media is allowed.

The FitNexus strategic source contract requires the funnel to measure acquisition, signup, first student, first training, delivery, retention and revenue, and explicitly warns against investing in paid traffic before conversion tracking and activation are operational.

Stage 18 therefore does **not** turn on ads. It builds the measurement authority and leaves missing public-funnel capture visible as a blocking gate.

## First-party event authority

Growth telemetry lives in the non-exposed `private` schema:

- `private.growth_event_catalog` — versionable semantic registry;
- `private.growth_events` — append-only operational event evidence;
- `private.growth_attribution` — first-touch and last-touch campaign attribution;
- `private.growth_capture_failures` — telemetry failure fingerprints without user payloads.

Normal authenticated clients have no direct SELECT/INSERT/UPDATE privileges on the raw growth ledger.

### Active server-authoritative events

| Event | Funnel stage | Authority |
| --- | --- | --- |
| `signup_completed` | Signup | `auth.users` INSERT trigger |
| `coach_profile_completed` | Onboarding | profile display-name completion trigger |
| `student_created` | Activation | `students` INSERT trigger |
| `training_created_or_duplicated` | Activation | `training_plans` INSERT trigger |
| `training_delivered` | Activation | active `student_access_links` INSERT trigger |
| `workout_logged` | Retention | workout session completed-state trigger |
| `trial_started` | Revenue | trial subscription INSERT trigger |
| `checkout_started` | Revenue | checkout intent INSERT trigger |
| `paid` | Revenue | subscription transition to `active` |

The ledger does not copy student name, email, objective, exercise content, pain, feedback or arbitrary metadata/property bags.

## Server telemetry cannot block the product

Database telemetry is downstream evidence, not business authority. An analytics failure must never roll back signup, student creation, training creation, delivery, workout completion or billing state.

`private.append_growth_event(...)` therefore runs the telemetry write inside an internal exception boundary. If capture fails:

1. the original domain/auth write continues;
2. a minimal record is attempted in `private.growth_capture_failures`;
3. only event name, source table/entity id, SQLSTATE and an MD5 diagnostic fingerprint of the database error are retained;
4. if even failure-evidence insertion fails, that secondary failure is swallowed rather than propagating into the product transaction.

No raw error text or user payload is stored in the failure ledger. This closes `BGF-GROWTH-TELEMETRY-CORE-BLOCK-113`.

## Explicitly incomplete public acquisition capture

Two source-contract events remain intentionally pending:

- `landing_view`;
- `signup_started`.

They are registered in the catalog as `future_public_capture / pending` instead of being faked from unrelated backend activity.

Until the future public landing/signup surface captures those events with abuse and privacy controls, the growth snapshot reports:

`paid_media_gate = BLOCKED_TRACKING_INCOMPLETE`

This prevents the system from declaring Google Ads or another paid channel ready merely because authenticated activation events exist.

## Attribution

Flutter now reads only explicit UTM keys from `Uri.base`:

- `utm_source`;
- `utm_medium`;
- `utm_campaign`;
- `utm_term`;
- `utm_content`.

It sends only those bounded values plus a **relative landing path** after the authenticated organization exists.

The capture intentionally does not copy the full query string, email, student data, health context or arbitrary URL parameters.

Attribution attachment uses the same authority pattern established in billing:

- public RPC `attach_growth_attribution(...)` = `SECURITY INVOKER`;
- private `attach_growth_attribution_authority(...)` = `SECURITY DEFINER`;
- organization membership is checked before attachment;
- first touch is preserved;
- later valid touches update only last-touch fields.

Flutter-side telemetry failure is also fail-open for core authentication/organization bootstrap: the error is logged through `dart:developer`, while sign-in and tenant preparation continue.

## Server-derived funnel snapshot

`get_growth_funnel_snapshot(organization_id, days)` returns an authenticated, tenant-scoped measurement snapshot without exposing the raw ledger.

It includes:

- signup completion;
- coach profile completion;
- first student;
- first training;
- first delivery;
- trial start;
- checkout start;
- paid conversion;
- training delivery count;
- workout completion count;
- first/last attribution summary;
- time-to-first-value;
- North Star state;
- explicit instrumentation gaps.

The public RPC remains `SECURITY INVOKER` and delegates privileged reads to a private definer bridge.

## North Star operational definition

The strategic candidate North Star was coaches who delivered at least one training to an active student in the week.

Stage 18 materializes the current operational proxy as:

`coaches_with_at_least_one_training_delivery_in_last_7_days`

A `training_delivered` event currently means an **active student access link was issued**. It proves delivery authorization, not that the student opened or executed the workout. Student execution remains separately evidenced by workout session completion.

This semantic distinction is deliberate and documented so later product evolution cannot silently redefine the North Star.

## Time to first value

For the current funnel, TTFV is derived server-side as:

`first training_delivered - signup_completed`

The calculation is returned as `time_to_first_value_seconds` when both timestamps exist in the selected window.

## Retention gap remains explicit

`workout_logged` now supplies real usage evidence, but D7 return cannot yet be measured reliably because there is no authoritative session/activity event for a returning coach.

The snapshot therefore reports:

`return_d7_measurement = PENDING_SESSION_ACTIVITY_EVENT`

Stage 18 refuses to manufacture D7 from unrelated writes.

## Advisor closure

The Supabase Security Advisor reports no new Stage 18 public SECURITY DEFINER exposure. Public growth RPCs are invoker wrappers; elevated authority stays in `private` functions.

The first performance pass found two unindexed foreign keys on first/last attribution actors. They were immediately repaired with:

- `growth_attribution_first_actor_user_id_idx`;
- `growth_attribution_last_actor_user_id_idx`.

A second advisor pass reports no Stage 18 unindexed foreign-key finding. Remaining notices are unused-index INFOs expected on the currently empty/low-traffic database.

## Permanent prevention classes

- `BGF-GROWTH-CLIENT-EVENT-FABRICATION-098`: normal clients cannot INSERT/UPDATE the authoritative growth event ledger.
- `BGF-GROWTH-SENSITIVE-PAYLOAD-099`: growth telemetry cannot become a generic metadata/payload store for student or health data.
- `BGF-GROWTH-FUNNEL-AUTHORITY-100`: activation milestones have one server-side event authority.
- `BGF-GROWTH-ATTRIBUTION-FIRST-LAST-101`: first-touch attribution is preserved while later touches update only last-touch state.
- `BGF-GROWTH-PAID-MEDIA-PREMATURE-102`: paid-media readiness fails closed while mandatory funnel capture remains incomplete.
- `BGF-GROWTH-NORTH-STAR-SEMANTICS-103`: the North Star definition and its operational proxy cannot drift silently.
- `BGF-GROWTH-TTFV-104`: time-to-first-value is derived from authoritative timestamps, not UI timers.
- `BGF-GROWTH-PUBLIC-CAPTURE-GAP-105`: unavailable public events are marked pending, never fabricated from backend substitutes.
- `BGF-GROWTH-RPC-EXPOSED-DEFINER-106`: public growth RPCs remain SECURITY INVOKER wrappers around private authority bridges.
- `BGF-GROWTH-TRIGGER-IDEMPOTENCY-107`: entity-backed server events are deduplicated by event/source entity identity.
- `BGF-GROWTH-ATTRIBUTION-FAILOPEN-108`: Flutter attribution failure must be observable but cannot break authentication or tenant bootstrap.
- `BGF-GROWTH-LANDING-PII-109`: attribution capture stores bounded UTM fields and relative path only, never arbitrary query payloads.
- `BGF-GROWTH-RETENTION-AUTHORITY-110`: completed workout sessions, not UI impressions, provide retention usage evidence.
- `BGF-GROWTH-REVENUE-AUTHORITY-111`: trial, checkout and paid milestones originate from subscription/billing authority.
- `BGF-GROWTH-FK-INDEX-112`: growth foreign keys receive covering indexes before promotion.
- `BGF-GROWTH-TELEMETRY-CORE-BLOCK-113`: server telemetry exceptions are contained and fingerprinted; analytics cannot roll back core product writes.

## Current release posture

Stage 18 makes the authenticated funnel measurable and privacy-minimized, but **does not open the ADS gate**.

Before paid media becomes eligible, the project still needs a real public acquisition/signup surface that can capture `landing_view` and `signup_started` end-to-end, plus the separate checkout/provider credential boundary already tracked by billing.
