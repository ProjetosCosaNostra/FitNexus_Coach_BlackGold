# BlackGold Forge — Stage 16 Billing Prevention Classes

## BGF-BILLING-PROVIDER-EVIDENCE-070
Provider choice is unstable external knowledge. Selection must record an evidence version and checked timestamp. Runtime activation must match the selected provider and evidence version.

## BGF-BILLING-PRICE-AUTHORITY-071
A checkout client must never submit its own payable amount. Currency/amount are copied only from one promoted `subscription_plan_prices` row. Missing price fails with `COMMERCIAL_PRICE_NOT_PROMOTED`.

## BGF-BILLING-CREDENTIAL-BOUNDARY-072
Architecture cannot manufacture an external provider account/API key. Provider state remains `selected_pending_credentials` until explicit service-side verification activates it.

## BGF-BILLING-WEBHOOK-AUTH-073
Webhook evidence must not enter the receipt ledger unless provider-specific authentication was verified first. Failure is `WEBHOOK_AUTH_NOT_VERIFIED`.

## BGF-BILLING-WEBHOOK-IDEMPOTENCY-074
Webhook delivery may repeat. `(provider_code, provider_event_id)` is unique and duplicate receipt attempts are represented as idempotent replay instead of duplicate state transitions.

## BGF-BILLING-CHECKOUT-IDEMPOTENCY-075
Checkout intent creation uses a unique idempotency key. Reuse with the same commercial request returns the existing intent; conflicting reuse fails with `CHECKOUT_IDEMPOTENCY_KEY_CONFLICT`.

## BGF-BILLING-NO-SILENT-FALLBACK-076
The external adapter cannot silently switch Asaas to another evaluated provider. Activation of any provider other than the selected provider fails with `SILENT_PROVIDER_FALLBACK_FORBIDDEN`.

## BGF-BILLING-CHECKOUT-URL-AUTHORITY-077
Checkout redirects are attached by the service adapter, never accepted from Flutter as authority, and must use HTTPS.

## BGF-BILLING-SECRET-EXPOSURE-078
Provider credentials/API keys/webhook tokens never enter Flutter models, public tables or checkout readiness output. The public contract explicitly reports `secret_exposed_to_flutter=false`.

## BGF-BILLING-SERVICE-DIRECT-MUTATION-079
Even service-role table grants are broader than needed. Stage 16 billing tables are read-only to the provider worker; all state changes are admitted through narrow service-only commands with validation.

## BGF-BILLING-FK-INDEX-080
Every new billing-domain foreign key must be checked by Supabase Performance Advisor. All Stage 16 unindexed-FK findings must be repaired before promotion and their index names become CI contract evidence.

## BGF-BILLING-FLUTTER-READINESS-081
The UI must consume `get_billing_provider_readiness(...)`. A selected provider with missing credentials or no promoted price must display a blocked checkout, never a false "buy" state.
