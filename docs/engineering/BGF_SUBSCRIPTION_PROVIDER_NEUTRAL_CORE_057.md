# BGF-SUBSCRIPTION-PROVIDER-COUPLING-057

## Failure class

Commercial state must not be modeled as a payment-provider schema.

If provider-specific customer IDs, price IDs, webhook semantics or checkout states become the business-domain authority, changing providers forces rewrites across tenant, student, training and product logic.

## Permanent prevention

FitNexus keeps a provider-neutral commercial core:

- `subscription_plans` owns capacity/features;
- `organization_subscriptions` owns effective SaaS lifecycle;
- `subscription_authority_events` owns transition evidence;
- `apply_subscription_authority_event(...)` is the narrow provider adapter boundary;
- pricing is explicitly `UNFROZEN` until a provider/pricing decision is separately promoted.

Provider adapters may supply identifiers and state transitions, but they do not become the source of truth for product entitlements.

## Authority boundary

Normal authenticated clients cannot apply subscription authority events or mutate subscription state directly. Provider transitions require `service_role`, idempotent external event references and append-only evidence.
