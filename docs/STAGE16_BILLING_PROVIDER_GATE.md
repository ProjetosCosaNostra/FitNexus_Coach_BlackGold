# FitNexus Coach BlackGold — Stage 16 Billing Provider Gate

## Purpose

Stage 16 selects the Brazil V1 billing adapter without pretending that selection equals a live payment account.

The commercial domain remains provider-neutral. A payment provider is now an external adapter behind explicit gates for:

1. provider evidence and selection;
2. external credentials;
3. promoted FitNexus price authority;
4. checkout intent idempotency;
5. authenticated webhook evidence;
6. subscription authority transitions.

No gate is allowed to silently infer another.

## Brazil V1 provider decision

`Asaas` is selected for `BR_V1` with evidence version `2026-08-18-official-docs-v1`.

The selection is based on official provider documentation reviewed for the current Stage 16 decision. The evidence set supports:

- recurring subscription APIs;
- recurring credit-card billing;
- Pix;
- Pix Automático for recurring collection;
- hosted recurring checkout;
- sandbox environment;
- webhook delivery with at-least-once semantics;
- webhook authentication token support.

`Stripe` is retained as a future international candidate. Its current Brazil materials support global billing strength, but the evaluated Pix availability is less convenient for the Brazil-first V1 path.

`Mercado Pago` is retained as a Brazil alternative with recurring subscription, Pix/boleto and retry capabilities.

This registry is an architectural evidence record, not a stored secret and not a guarantee that an external provider account is already active.

## Provider state machine

The Brazil V1 provider selection starts as:

`selected_pending_credentials`

It can become `active` only through `activate_billing_provider_selection(...)`, a service-role-only command that requires:

- the same already-selected provider;
- the exact promoted evidence version;
- an explicit external credential verification performed by the provider adapter.

A provider mismatch fails with `SILENT_PROVIDER_FALLBACK_FORBIDDEN`.

## Pricing remains independent

`subscription_plan_prices` is separate from `subscription_plans`.

The Stage 16 migration intentionally seeds **zero active prices**. The FitNexus price is therefore still `UNFROZEN`.

`create_billing_checkout_intent(...)` fails closed with `COMMERCIAL_PRICE_NOT_PROMOTED` until an active server-authoritative price exists.

The client never submits the amount. A checkout intent copies currency and amount from the promoted database price.

## Credential boundary

Provider credentials are not stored in Flutter, GitHub source, public database rows or entitlement snapshots.

Until the external authority is verified, the readiness snapshot returns:

- provider selected;
- credentials pending;
- price unfrozen;
- checkout not ready;
- `secret_exposed_to_flutter=false`.

This is a deliberate hard boundary. Architecture completion does not manufacture an external account or API key.

## Checkout intent authority

`billing_checkout_intents` is an RLS-protected ledger.

Normal authenticated clients cannot INSERT directly. Billing managers request a checkout intent through the controlled RPC, which validates:

- organization billing authority;
- selected provider active;
- billing interval;
- promoted price;
- server-owned amount;
- idempotency key.

The external provider adapter attaches the provider checkout reference and HTTPS redirect only through a service-role-only command.

## Webhook authority

`billing_webhook_receipts` stores minimal payment-event evidence:

- provider;
- provider event id;
- event type;
- SHA-256 of the payload;
- authentication verification result;
- processing status;
- optional organization/subscription reference.

A receipt is admitted only after webhook authentication was verified. `(provider_code, provider_event_id)` is unique, so at-least-once delivery cannot duplicate the event receipt.

The provider adapter later maps validated external events into Stage 15 `apply_subscription_authority_event(...)`, preserving the provider-neutral subscription domain.

## Service authority: command-only mutation

Stage 16 originally gave the provider runtime narrow direct UPDATE/INSERT table grants. Construction review identified that even narrow direct table mutation was broader than necessary.

The hardening migration now gives the service runtime SELECT-only access to Stage 16 billing tables. All mutations are performed by explicit service-role-only commands:

- `activate_billing_provider_selection(...)`;
- `attach_billing_provider_checkout(...)`;
- `record_billing_webhook_receipt(...)`;
- `mark_billing_webhook_receipt(...)`.

This makes the intended mutation vocabulary auditable and prevents arbitrary table writes by the provider worker.

## Readiness snapshot

`get_billing_provider_readiness(...)` is authenticated-only and reports:

- provider selection;
- evidence version;
- provider capabilities;
- credential state;
- promoted-price count;
- checkout readiness;
- whether the subscription is already bound to an external provider.

It also returns the permanent checkout guardrails:

- `server_amount_authority=true`;
- `client_amount_allowed=false`;
- `silent_provider_fallback=false`;
- `secret_exposed_to_flutter=false`.

The professor Plan workspace displays these states without showing a fake checkout button while the gates are red.

## Performance gate

Supabase Performance Advisor identified four Stage 16 unindexed foreign keys immediately after the first migration. They were repaired before promotion:

- `billing_checkout_intents.created_by`;
- `billing_checkout_intents.plan_code`;
- `billing_checkout_intents.price_id`;
- `billing_provider_selections.provider_code`.

A repeated advisor run confirmed no remaining Stage 16 unindexed-FK finding.

## Permanent prevention classes

- `BGF-BILLING-PROVIDER-EVIDENCE-070`: provider selection must carry a dated evidence version instead of relying on memory.
- `BGF-BILLING-PRICE-AUTHORITY-071`: checkout amount must come from a separately promoted server price; client amount is forbidden.
- `BGF-BILLING-CREDENTIAL-BOUNDARY-072`: selected provider is not active until external credentials are verified.
- `BGF-BILLING-WEBHOOK-AUTH-073`: provider events are inadmissible before webhook authentication verification.
- `BGF-BILLING-WEBHOOK-IDEMPOTENCY-074`: provider event ids are deduplicated because webhook delivery may repeat.
- `BGF-BILLING-CHECKOUT-IDEMPOTENCY-075`: checkout intent retries require an idempotency key and reject conflicting reuse.
- `BGF-BILLING-NO-SILENT-FALLBACK-076`: provider adapters cannot silently replace the selected provider.
- `BGF-BILLING-CHECKOUT-URL-AUTHORITY-077`: provider redirect is service-attached and must be HTTPS.
- `BGF-BILLING-SECRET-EXPOSURE-078`: provider secret material must never be returned to Flutter.
- `BGF-BILLING-SERVICE-DIRECT-MUTATION-079`: provider workers receive read-only table access; mutations use explicit service commands.
- `BGF-BILLING-FK-INDEX-080`: new billing foreign keys require advisor-cleared covering indexes before promotion.
- `BGF-BILLING-FLUTTER-READINESS-081`: product UI reads server readiness and cannot represent blocked checkout as live.

## Promotion boundary

Stage 16 can be promoted while checkout remains blocked. That is the correct state until two independent future gates are completed:

1. one-time external Asaas credential/webhook authority verification;
2. deliberate FitNexus pricing promotion.

Neither is inferred or fabricated by this stage.
