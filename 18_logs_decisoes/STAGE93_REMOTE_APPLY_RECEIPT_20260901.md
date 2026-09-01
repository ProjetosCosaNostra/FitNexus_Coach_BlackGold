# Stage93 — Billing recurring lifecycle remote apply receipt

Observed: 2026-09-01
Project: FitNexus Coach BlackGold
Supabase project ref: `mceukeondizkwlpfxzgf`

## Remote promotion

Migration applied successfully:

- version: `20260901010139`
- name: `stage93_billing_recurring_lifecycle_authority`

Verified remote authorities:

- `public.bind_billing_provider_subscription(...)`
  - `SECURITY DEFINER`: true
  - `anon EXECUTE`: false
  - `authenticated EXECUTE`: false
  - `service_role EXECUTE`: true
- `public.apply_billing_subscription_lifecycle_event(...)`
  - `SECURITY DEFINER`: true
  - `anon EXECUTE`: false
  - `authenticated EXECUTE`: false
  - `service_role EXECUTE`: true
- `public.organization_subscriptions.billing_interval`: present

Edge runtime after promotion:

- `billing-webhook`: deployed as version 2
- JWT verification remains disabled intentionally because the endpoint uses dedicated provider webhook-token authentication inside the function.

## Scope boundary

No production charge was created. No Asaas production credential was activated. This receipt only reconciles the already-completed database/runtime promotion.
