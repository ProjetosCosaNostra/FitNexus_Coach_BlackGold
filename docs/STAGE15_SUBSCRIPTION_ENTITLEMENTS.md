# FitNexus Coach BlackGold — Stage 15 Subscription & Entitlement Core

## Purpose

Stage 15 turns the product into a commercially enforceable SaaS without coupling the domain to any payment processor.

The system now has four independent authorities:

1. **Plan catalog** — defines capacity and feature entitlements.
2. **Organization subscription state** — defines trial/active/grace/past-due/canceled/expired lifecycle.
3. **Usage** — derives real student/team consumption from authoritative tenant data.
4. **Provider event authority** — accepts future billing-provider state transitions through an idempotent service-role-only command.

The commercial core works before any payment processor is selected. Provider choice can therefore change without rewriting student, training, intelligence or tenant tables.

## Trial bootstrap

Every new organization receives a server-created `BlackGold Trial` automatically:

- 14 days;
- 10 student records;
- 1 organization member;
- current core product features enabled.

The trial is created by a database trigger, not by Flutter. The client cannot give itself a longer trial.

## Plan catalog

Stage 15 introduces capacity tiers without freezing price:

- `trial` — 10 students / 1 team member;
- `solo` — 30 students / 1 team member;
- `pro` — 100 students / 3 team members;
- `studio` — 300 students / 10 team members.

Pricing remains explicitly `UNFROZEN`. A future checkout/provider stage may attach commercial prices without changing entitlement semantics.

## Effective subscription state

The database derives an effective state instead of trusting a stored string forever.

For example, a row may still say `trialing`, but once `trial_ends_at <= now()` the entitlement snapshot reports `expired` and write gates fail closed.

Write-enabled states are currently:

- `trialing` while the trial is still valid;
- `active` while the current period is valid;
- `grace` while its period remains valid.

`past_due`, `canceled`, `expired`, missing or invalid authority are not write-enabled.

## Server-side limits

Commercial limits are not UI decorations.

Database triggers enforce:

- student capacity before `students` INSERT;
- organization-member capacity before `organization_members` INSERT;
- subscription write authority before new training plans;
- Decision Intelligence entitlement before new Decision Brief evidence is created.

This means bypassing the Flutter UI does not bypass the commercial contract.

## Read preservation

Stage 15 intentionally distinguishes **new commercial writes** from data preservation.

An expired or blocked subscription does not delete student, training, feedback, lineage or decision evidence. The system blocks protected new operations while preserving existing tenant data.

## Provider-neutral authority adapter

`apply_subscription_authority_event(...)` is the future billing adapter boundary.

It is:

- callable only by `service_role`;
- denied to `anon` and normal authenticated users;
- provider-neutral;
- idempotent through an external event reference;
- auditable through `subscription_authority_events`;
- versioned through `authority_version`.

The function stores only provider identifiers and an optional SHA-256 payload fingerprint. It does not require raw webhook bodies to be stored in the tenant domain.

The provider runtime follows least privilege:

- plan catalog: SELECT only;
- organization subscription state: SELECT + UPDATE;
- authority-event ledger: SELECT + INSERT only.

It cannot rewrite plan definitions or UPDATE/DELETE historical authority events.

## Entitlement snapshot

`get_subscription_entitlement_snapshot(organization_id)` returns one server-authoritative object containing:

- plan code/name;
- stored and effective subscription state;
- write-enabled state;
- trial time remaining;
- real student/team usage;
- remaining capacity;
- feature flags;
- provider-bound state;
- commercial guardrails.

The professor Plan workspace reads this RPC. It does not calculate entitlement locally.

## Client mutation boundary

Authenticated clients can read their RLS-protected subscription state but cannot:

- INSERT or UPDATE `organization_subscriptions`;
- fabricate `subscription_authority_events`;
- invoke provider authority transitions;
- expand their own capacity;
- extend their own trial.

## Performance hardening

The Stage 15 migrations include covering indexes for every new plan-code foreign key detected by the Supabase advisor. This prevents the commercial domain from introducing known unindexed-FK debt at promotion time.

## Permanent prevention classes

- `BGF-SUBSCRIPTION-FILE-MISSING-046`: required commercial-core artifacts cannot silently disappear.
- `BGF-SUBSCRIPTION-PLAN-AUTHORITY-047`: plan/capacity must have a single database authority.
- `BGF-SUBSCRIPTION-STATE-AUTHORITY-048`: organization lifecycle cannot be inferred from UI state.
- `BGF-SUBSCRIPTION-EVENT-EVIDENCE-049`: commercial state transitions require evidence.
- `BGF-SUBSCRIPTION-TRIAL-BOOTSTRAP-050`: trial initialization is server-owned and deterministic.
- `BGF-SUBSCRIPTION-STUDENT-LIMIT-051`: student capacity is server enforced.
- `BGF-SUBSCRIPTION-MEMBER-LIMIT-052`: team capacity is server enforced.
- `BGF-SUBSCRIPTION-WRITE-GATE-053`: commercial write state gates new prescriptions.
- `BGF-SUBSCRIPTION-FEATURE-GATE-054`: Decision Intelligence cannot bypass entitlement.
- `BGF-SUBSCRIPTION-SNAPSHOT-055`: UI must consume one authoritative entitlement snapshot.
- `BGF-SUBSCRIPTION-PRICE-AUTHORITY-056`: pricing remains explicitly unfrozen until promoted deliberately.
- `BGF-SUBSCRIPTION-PROVIDER-COUPLING-057`: payment provider cannot become the domain model.
- `BGF-SUBSCRIPTION-PROVIDER-EVENT-058`: external billing transitions enter through one controlled authority command.
- `BGF-SUBSCRIPTION-EVENT-IDEMPOTENCY-059`: duplicate webhooks/events cannot replay commercial mutations.
- `BGF-SUBSCRIPTION-FLUTTER-BINDING-060`: Flutter remains bound to the server snapshot.
- `BGF-SUBSCRIPTION-WORKSPACE-061`: plan/capacity status remains visible to the professor.
- `BGF-SUBSCRIPTION-ENTRYPOINT-062`: the professor shell retains access to the Plan workspace.
- `BGF-SUBSCRIPTION-RLS-063`: all commercial authority tables remain RLS protected.
- `BGF-SUBSCRIPTION-CLIENT-MUTATION-064`: normal clients cannot mutate subscription authority.
- `BGF-SUBSCRIPTION-PROVIDER-AUTHORITY-065`: provider events require service-role authority.
- `BGF-SUBSCRIPTION-RPC-AUTHORITY-066`: entitlement snapshots remain authenticated-only.
- `BGF-SUBSCRIPTION-SERVICE-LEAST-PRIVILEGE-067`: billing service authority must receive only the table privileges required by the adapter contract.
- `BGF-SUBSCRIPTION-FK-INDEX-068`: every new commercial-domain foreign key must have covering index evidence before promotion.

## Construction gate

`verify_subscription_entitlements_contract.py` runs in GitHub Actions before Flutter analysis and tests. It fails closed if capacity gates, trial authority, provider-neutrality, service-role isolation, foreign-key coverage, direct-client mutation denial or Flutter bindings drift.
