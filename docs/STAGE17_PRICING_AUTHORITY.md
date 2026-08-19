# FitNexus Coach BlackGold — Stage 17 Pricing Authority

## Purpose

Stage 17 closes the first **pricing experiment gate** without pretending that the commercial hypothesis is permanently frozen.

The project continuity adendum explicitly classified pricing as a gate. Its validation ranges were:

- Solo / Essencial: R$ 29,90–39,90 per month;
- Pro: R$ 59,90–79,90 per month;
- Studio: R$ 119,90–179,90 per month;
- annual: approximately ten monthly payments for twelve months, subject to unit economics.

Stage 17 promotes the **upper-bound validation experiment** so willingness-to-pay can be measured without changing the product domain later.

## BR V1 experiment prices

Decision version: `BR_V1_PRICING_EXPERIMENT_001`

| Plan | Capacity | Monthly | Annual | Annual strategy |
| --- | ---: | ---: | ---: | --- |
| Coach Solo | 30 students / 1 member | R$ 39,90 | R$ 399,00 | 10 months paid / 12 months |
| Coach Pro | 100 students / 3 members | R$ 79,90 | R$ 799,00 | 10 months paid / 12 months |
| Studio | 300 students / 10 members | R$ 179,90 | R$ 1.799,00 | 10 months paid / 12 months |

These values are **promoted experiment prices**, not a claim that pricing is permanently frozen. Any future change requires a new `decision_version`; the same version cannot be replayed with different values.

## Why these values

The decision uses three evidence layers:

1. **FitNexus source contract** — the project adendum provided hypothesis ranges and required pricing to remain a commercial gate until validated.
2. **Current market anchors checked on 2026-08-19** — public competitor offers showed coach software around R$ 49 for ~10 students, R$ 79–99 around 25–50 students, and R$ 149–199 around 100 students, with some lower and higher outliers. The FitNexus experiment deliberately stays inside its original hypothesis ranges instead of copying a competitor.
3. **Current provider public-cost evidence** — Asaas publicly states that recurring billing itself has no platform monthly fee and that transaction costs depend on payment method. The public starting credit-card rate observed was 2.99% + R$ 0.49 per received charge; public Pix-invoice receipt pricing observed was R$ 1.99. These are planning assumptions only, not account-specific contracted rates.

### Public market anchors used as non-authoritative evidence

- Nexur public plans: R$ 49,90 up to 25 students; R$ 79,90 up to 50; R$ 149,90 up to 100; R$ 249,90 up to 250.
- Welltrainer public plans: R$ 47 up to 10; R$ 97 up to 50; R$ 197 unlimited, with temporary pioneer discounts shown separately.
- Trainer Connect public plans: R$ 49 up to 10; R$ 99 up to 30; R$ 199 up to 100; R$ 349 unlimited.
- PersonalGO PRO public help: R$ 79,90 monthly for trainers.

Market anchors are evidence snapshots, not dependencies. A competitor changing price must never silently change FitNexus pricing.

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

These figures do **not** include taxes, hosting, support, AI, storage, chargebacks, discounts, refunds or future contracted provider pricing. They therefore cannot be used as a final gross-margin statement.

## Atomic price-set promotion

`promote_subscription_pricing(...)` is the only service-role promotion command introduced for price-set changes.

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

Every new `billing_checkout_intents` row now stores `pricing_decision_version`.

This creates the chain:

`pricing decision -> promoted price -> checkout intent -> provider checkout -> webhook -> subscription authority`

A paid conversion can therefore be attributed to the exact pricing experiment that produced it.

## Latent Stage 16 defect found and repaired

During Stage 17 privilege-closure review, `create_billing_checkout_intent(...)` was found to be `SECURITY INVOKER` while authenticated clients had no direct INSERT privilege on `billing_checkout_intents`.

That meant the RPC had execute permission but its underlying mutation path was dead.

Stage 17 repairs this by making the RPC `SECURITY DEFINER` while preserving its explicit internal controls:

- `auth.uid()` required;
- organization billing-manager authority required;
- provider must be active;
- amount/currency/interval come from the active server price;
- current pricing decision must match;
- idempotency conflict checks remain;
- direct client table mutation remains denied.

This failure class is permanently registered as `BGF-BILLING-RPC-PRIVILEGE-DEADPATH-082`.

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

Flutter now has typed models for this contract. It does not calculate or invent server prices.

## Permanent prevention classes

- `BGF-BILLING-RPC-PRIVILEGE-DEADPATH-082`: executable RPC cannot depend on table privileges the caller does not possess unless the command deliberately closes that authority path.
- `BGF-PRICING-UNVERSIONED-083`: no promoted price exists without pricing decision identity.
- `BGF-PRICING-DECISION-DRIFT-084`: price changes require a new decision version.
- `BGF-PRICING-ANNUAL-STRATEGY-085`: annual strategy is explicit and regression-gated.
- `BGF-PRICING-PARTIAL-PROMOTION-086`: incomplete price sets cannot be promoted.
- `BGF-PRICING-IDEMPOTENCY-087`: a decision version cannot be reused for different price content.
- `BGF-PRICING-FEE-EVIDENCE-088`: public provider fees are evidence, never silently treated as contracted account rates.
- `BGF-PRICING-CHECKOUT-BINDING-089`: each checkout must preserve pricing-decision lineage.
- `BGF-PRICING-CATALOG-090`: clients consume one authoritative pricing catalog.
- `BGF-PRICING-COMPLETE-SET-091`: billing readiness requires the complete six-offer set.
- `BGF-PRICING-FLUTTER-BINDING-092`: Flutter pricing models remain bound to server authority.
- `BGF-PRICING-CLIENT-MUTATION-093`: normal clients cannot write pricing authority.
- `BGF-PRICING-PROMOTION-AUTHORITY-094`: pricing promotion remains service-authority-only.

## Remaining commercial boundary

The price gate is now promoted as an experiment. Checkout still remains blocked because the external Asaas credential/account boundary has not been activated.

That separation is intentional: price validation and provider credential authorization are independent authorities.
