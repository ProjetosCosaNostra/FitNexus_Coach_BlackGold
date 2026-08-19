# FitNexus Coach BlackGold — Stage 17 Pricing Authority

## Purpose

Stage 17 closes the first **pricing experiment gate** without pretending that the commercial hypothesis is permanently frozen.

The project continuity adendum explicitly classified pricing as a gate. Its validation ranges were:

- Solo / Essencial: R$ 29,90–39,90 per month;
- Pro: R$ 59,90–79,90 per month;
- Studio: R$ 119,90–179,90 per month;
- annual: approximately ten monthly payments for twelve months, subject to unit economics.

Stage 17 promotes the **upper-bound validation experiment** so willingness-to-pay can be measured while preserving a versioned path for later price changes.

## BR V1 experiment prices

Decision version: `BR_V1_PRICING_EXPERIMENT_001`

| Plan | Capacity | Monthly | Annual | Annual strategy |
| --- | ---: | ---: | ---: | --- |
| Coach Solo | 30 students / 1 member | R$ 39,90 | R$ 399,00 | 10 months paid / 12 months |
| Coach Pro | 100 students / 3 members | R$ 79,90 | R$ 799,00 | 10 months paid / 12 months |
| Studio | 300 students / 10 members | R$ 179,90 | R$ 1.799,00 | 10 months paid / 12 months |

These values are **promoted experiment prices**, not a permanent price freeze. Any future change requires a new `decision_version`; the same version cannot be replayed with different values.

## Evidence model

The decision uses three evidence layers:

1. **FitNexus source contract** — the project adendum provided hypothesis ranges and required pricing to remain a commercial gate until validated.
2. **Market evidence snapshot** — current public competitor offers were checked as non-authoritative anchors. They inform the experiment but never mutate FitNexus pricing automatically.
3. **Provider cost evidence** — current public Asaas rates are stored only as planning assumptions. `contractual = false` is mandatory so a public rate can never masquerade as the account-specific commercial contract.

Market anchors and provider rates are evidence snapshots, not runtime dependencies. Any future evidence refresh requires a deliberate pricing decision, not silent drift.

## Unit-economics evidence boundary

`billing_fee_assumptions` stores versioned, non-contractual planning assumptions.

Current snapshot:

- Asaas card public starting assumption: 299 bps + R$ 0,49;
- Asaas Pix-invoice public assumption: R$ 1,99;
- `contractual = false` is mandatory.

At the current monthly experiment prices, the approximate amount remaining after only those public payment-processing assumptions is:

| Plan | Card public-starting assumption | Pix-invoice public assumption |
| --- | ---: | ---: |
| Solo R$ 39,90 | ~R$ 38,22 | R$ 37,91 |
| Pro R$ 79,90 | ~R$ 77,02 | R$ 77,91 |
| Studio R$ 179,90 | ~R$ 174,03 | R$ 177,91 |

These figures do **not** include taxes, hosting, support, AI, storage, chargebacks, discounts, refunds or future contracted provider pricing. They are therefore not final gross-margin claims.

## Atomic price-set promotion

`promote_subscription_pricing(...)` is the service-authority promotion command for price-set changes.

It fails closed when:

- the decision version is missing;
- the price set does not contain exactly six offers;
- a plan/interval pair is missing or duplicated;
- a price is non-positive;
- the annual strategy is not `TEN_MONTHS_FOR_TWELVE`;
- annual price is not exactly ten monthly payments;
- an existing decision version is replayed with different content;
- promotion ends with fewer than six active prices.

A new price decision retires the previous current decision and its active prices transactionally.

## Checkout lineage

Every new `billing_checkout_intents` row stores `pricing_decision_version`.

The commercial evidence chain is therefore:

`pricing decision -> promoted price -> checkout intent -> provider checkout -> webhook -> subscription authority`

A paid conversion can be attributed to the exact pricing experiment that produced it.

## Stage 16 privilege dead-path found and permanently repaired

During Stage 17 privilege-closure review, `create_billing_checkout_intent(...)` was found to be `SECURITY INVOKER` while authenticated clients intentionally had no direct INSERT privilege on `billing_checkout_intents`.

The exposed RPC had execute permission, but its intended INSERT path would be dead once provider credentials became active.

An intermediate repair changed the public RPC to `SECURITY DEFINER`. The Supabase Security Advisor correctly surfaced that public exposed definer as a new warning, so that intermediate form was not accepted as the final architecture.

The final authority pattern is:

- `public.create_billing_checkout_intent(...)` — exposed **SECURITY INVOKER** wrapper;
- `private.create_billing_checkout_intent_authority(...)` — non-public **SECURITY DEFINER** mutation bridge;
- direct authenticated INSERT on `billing_checkout_intents` remains denied;
- both layers validate authenticated billing-manager authority;
- provider must be active;
- amount/currency/interval come from the promoted server price;
- the current pricing decision must match;
- idempotency conflict checks remain;
- the private authority bridge is outside the public PostgREST RPC surface.

This permanently closes `BGF-BILLING-RPC-PRIVILEGE-DEADPATH-082` without leaving a new public-definer warning. The intermediate advisor finding became an additional prevention class, `BGF-BILLING-RPC-EXPOSED-DEFINER-095`.

## Pricing catalog

`get_pricing_catalog('BRL')` provides one server-authoritative authenticated catalog containing:

- pricing decision version;
- experiment/frozen mode;
- annual strategy;
- plan capacities;
- monthly price;
- annual price;
- annual savings;
- annual monthly equivalent.

Flutter has typed models for this contract. It does not calculate or invent server prices.

## RLS and advisor closure

Stage 17 enables RLS on both pricing authority tables. `pricing_decisions` exposes only current experiment/frozen decisions to authenticated clients. `billing_fee_assumptions` remains internal; an explicit service-role read policy prevents an ambiguous `RLS enabled, no policy` state.

Foreign-key indexes were added for pricing-decision lineage and provider fee assumptions. The performance advisor no longer reports Stage 17 unindexed foreign keys. Unused-index INFO notices are expected while the project contains little/no production traffic.

## Permanent prevention classes

- `BGF-BILLING-RPC-PRIVILEGE-DEADPATH-082`: executable mutation RPC cannot depend on table privileges the caller intentionally does not possess.
- `BGF-PRICING-UNVERSIONED-083`: no promoted price exists without pricing decision identity.
- `BGF-PRICING-DECISION-DRIFT-084`: price changes require a new decision version.
- `BGF-PRICING-ANNUAL-STRATEGY-085`: annual strategy is explicit and regression-gated.
- `BGF-PRICING-PARTIAL-PROMOTION-086`: incomplete price sets cannot be promoted.
- `BGF-PRICING-IDEMPOTENCY-087`: a decision version cannot be reused for different price content.
- `BGF-PRICING-FEE-EVIDENCE-088`: public provider fees are evidence, never silently treated as contracted account rates.
- `BGF-PRICING-CHECKOUT-BINDING-089`: each checkout preserves pricing-decision lineage.
- `BGF-PRICING-CATALOG-090`: clients consume one authoritative pricing catalog.
- `BGF-PRICING-COMPLETE-SET-091`: billing readiness requires the complete six-offer set.
- `BGF-PRICING-FLUTTER-BINDING-092`: Flutter pricing models remain bound to server authority.
- `BGF-PRICING-CLIENT-MUTATION-093`: normal clients cannot write pricing authority.
- `BGF-PRICING-PROMOTION-AUTHORITY-094`: pricing promotion remains service-authority-only.
- `BGF-BILLING-RPC-EXPOSED-DEFINER-095`: a public RPC must not be promoted to SECURITY DEFINER when a private definer bridge can close the authority path.
- `BGF-PRICING-FEE-RLS-096`: internal fee-evidence tables must have explicit RLS policy semantics, even when not exposed to normal clients.

## Remaining commercial boundary

The pricing gate is now promoted as a versioned experiment. Checkout remains blocked because the external Asaas credential/account boundary has not been activated.

That separation is intentional: pricing validation and provider credential authorization are independent authorities.
