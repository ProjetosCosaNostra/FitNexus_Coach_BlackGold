# FitNexus Coach BlackGold — Stage83 Billing Policy Review Questionnaire Skeleton

**STATUS:** STRUCTURE ONLY — DO NOT COMPLETE, SIGN, APPROVE OR TREAT AS REVIEW MATERIAL BEFORE REAL BILLING AUTHORITY EXISTS.

This document prepares the questions that a future real business-owner plus legal review must answer for `BILLING_CANCELLATION_REFUND_POLICY`. It is deliberately **unanswered** and cannot be used as customer terms, legal advice, billing-provider evidence, gate evidence or approval.

## Mandatory precondition

**REAL BILLING AUTHORITY MUST EXIST BEFORE ANY REAL BUSINESS-OWNER OR LEGAL POLICY REVIEW IS COLLECTED.**

Current upstream billing state remains `AWAITING_REAL_OPERATOR_CREDENTIAL_EVIDENCE`. Asaas is selected but not activated. Until real operator credential evidence is accepted through the existing canonical billing evidence path:

- do not fill answers into this questionnaire;
- do not obtain signatures/approvals against this questionnaire;
- do not claim provider cancellation/refund behavior;
- do not decide customer refund/withdrawal eligibility;
- do not decide cancellation effective time;
- do not decide delinquency grace/retry/suspension/reactivation rules;
- do not modify Terms of Use from this skeleton;
- do not close `BILLING_CANCELLATION_REFUND_POLICY`;
- do not promote `legal_terms_of_use`, billing credentials, controlled launch, paid media or launch.

## Canonical open decision

- **Decision:** `BILLING_CANCELLATION_REFUND_POLICY`
- **State:** `OPEN`
- **Affected gate:** `legal_terms_of_use`
- **Required outcome, when the external prerequisite actually exists:** `Approved trial, renewal, cancellation, refund/withdrawal, delinquency and reactivation policy.`
- **Resolution authority:** `business plus legal review after real billing authority`

The wording above is copied from the canonical unresolved-decision registry and must not be paraphrased into a different authority boundary.

## Technical surfaces that future review must consider

The future review must consider all 10 source-reconciled Stage82R2 surfaces without treating database fields as customer policy:

1. `trial_lifecycle`
2. `paid_period_and_entitlement_boundary`
3. `cancel_at_period_end_intent`
4. `delinquency_and_recovery`
5. `terminal_subscription_cancellation`
6. `checkout_intent_lifecycle`
7. `webhook_reconciliation_and_payment_events`
8. `subscription_authority_audit_trail`
9. `plan_price_and_fee_assumption_boundaries`
10. `provider_selection_and_external_billing_boundary`

A technical status, timestamp, flag, provider reference, webhook receipt or audit event never answers the commercial/legal question by itself.

## Future participant roles — not yet collectible

Only after real billing authority exists, the actual review will require traceable real participants for at least:

- `business_owner_review`
- `legal_review`

Stage83 does not identify, assign or simulate those people. It does not accept placeholder identities as real participants.

## Section A — Trial policy

Future real reviewers must decide, with source/reference material:

1. When a trial starts and what event/timestamp is customer-visible.
2. Whether and how a customer may cancel during trial.
3. Whether cancellation during trial ends access immediately or later.
4. What notice is required before conversion, expiration or any charge.
5. What happens when real billing authority/provider processing is unavailable.
6. Whether any withdrawal/refund concept can apply to a trial and under which reviewed basis.

**Stage83 answer:** intentionally blank — no rule selected.

## Section B — Renewal policy

Future real reviewers must decide:

1. What constitutes renewal for each billing interval.
2. What advance disclosure/notice is required.
3. How price/version changes apply to existing customers.
4. What happens when renewal payment fails or remains unconfirmed.
5. Which real provider event is authoritative before subscription state changes.

**Stage83 answer:** intentionally blank — no rule selected.

## Section C — Customer-initiated cancellation

Future real reviewers must decide:

1. Which customer action constitutes a cancellation request.
2. Whether `cancel_at_period_end` is used and under what approved rule.
3. The effective cancellation time/date shown to the customer.
4. Whether a scheduled cancellation may be reversed.
5. What access continues after cancellation and until when.
6. What confirmation/receipt is required.
7. What operational evidence must accompany the state transition.

**Stage83 answer:** intentionally blank — no rule selected.

## Section D — Service-initiated or exceptional cancellation

Future real reviewers must decide:

1. Which causes may allow service-initiated cancellation.
2. Which notice, cure opportunity or escalation applies, if any.
3. How cancellation interacts with delinquency, abuse/security, legal requirements or provider failure.
4. What happens to paid access, outstanding amounts and data/account access.
5. Which business/legal/provider approval is needed for exceptional paths.

**Stage83 answer:** intentionally blank — no rule selected.

## Section E — Refund / withdrawal policy

Future real reviewers must decide only after real billing authority and real provider mechanics are known:

1. Which circumstances create refund or withdrawal eligibility.
2. Which time window, if any, applies and how it is measured.
3. Whether outcomes may be full, partial, prorated or unavailable.
4. How duplicate, disputed, failed or reversed charges are handled.
5. How taxes and real provider fees are treated.
6. Which provider receipt proves an actual financial reversal.
7. What happens when approved customer policy requires an outcome the provider cannot automate.
8. What customer confirmation and timing disclosure are required.

**Stage83 answer:** intentionally blank — no eligibility, period or formula selected.

## Section F — Delinquency, retry, suspension and recovery

Future real reviewers must decide:

1. Which real provider-confirmed event enters delinquency.
2. Whether a grace period exists and, if so, its reviewed duration/basis.
3. Retry cadence and stopping conditions.
4. Access changes during delinquency or suspension.
5. Customer notice cadence/content.
6. When delinquency may transition to cancellation.
7. How successful recovery restores state/access.

**Stage83 answer:** intentionally blank — no grace/retry/suspension rule selected.

## Section G — Reactivation

Future real reviewers must decide:

1. Which canceled, delinquent or inactive states may be reactivated.
2. Whether reactivation requires a new checkout, payment confirmation or plan selection.
3. How old balances, prior periods and new billing periods are treated.
4. Which customer disclosures/consents are required.
5. Which provider and internal authority events prove reactivation.

**Stage83 answer:** intentionally blank — no reactivation rule selected.

## Section H — Access and entitlement consequences

Future real reviewers must decide:

1. Access behavior after scheduled cancellation.
2. Access behavior after terminal cancellation.
3. Access behavior during delinquency/suspension.
4. Access behavior after refund/withdrawal.
5. Access behavior during provider reconciliation uncertainty.
6. Whether read-only/export/access-to-records obligations survive subscription state changes.

**Stage83 answer:** intentionally blank — no entitlement rule selected.

## Section I — Price, fees, taxes and proration

Future real reviewers must decide using real current commercial/provider evidence:

1. Which price/version controls each event.
2. Whether proration exists and in which situations.
3. How real provider fees affect calculations or disclosures.
4. How tax treatment is determined by the appropriate authority/source.
5. How rounding/currency rules are disclosed where relevant.
6. How price changes affect renewal/cancellation/refund rights.

**Stage83 answer:** intentionally blank — no fee/tax/proration rule selected.

## Section J — Customer communications and receipts

Future real reviewers must decide:

1. Required messages for trial conversion/expiration.
2. Renewal notices.
3. Cancellation request and effective-cancellation confirmation.
4. Delinquency/retry/suspension/recovery notices.
5. Refund/withdrawal request and financial-reversal confirmation.
6. Duplicate/disputed charge handling communications.
7. Reactivation confirmation.
8. Minimum information that must be included without exposing secrets or unnecessary personal data.

**Stage83 answer:** intentionally blank — no communication rule selected.

## Section K — Provider mechanics dependency

This section cannot be answered from provider selection metadata. After real Asaas production authority exists, reviewers must bind policy to verified provider facts such as:

1. Actual cancellation operations available in the authorized environment.
2. Actual refund/reversal operations available in the authorized environment.
3. Authoritative payment/refund/cancellation webhook or API receipts.
4. Timing, settlement or irreversibility constraints that affect policy execution.
5. Real provider fee behavior relevant to reversals.
6. Failure/escalation paths when provider mechanics do not match approved customer policy.

**Stage83 answer:** intentionally blank — provider behavior is not inferred.

## Section L — Data, retention and account lifecycle dependency

Future real reviewers must reference—not reinvent—the approved privacy/retention/DSR conclusions for:

1. Billing/subscription audit retention.
2. Provider-reference and receipt retention.
3. Account/data behavior after cancellation or withdrawal.
4. Legal-hold or dispute exceptions, when actually approved.
5. DSR access/export/deletion interactions with subscription state.

**Stage83 answer:** intentionally blank — no retention/deletion rule selected.

## Section M — Terms acceptance and versioning dependency

Future approved billing policy must eventually map to the separately unresolved `TERMS_ACCEPTANCE_VERSIONING` decision. Reviewers must determine:

1. Which immutable Terms version contains the approved billing policy.
2. How acceptance is bound to user/account and version/digest.
3. How material changes are communicated and accepted when required.
4. How evidence of acceptance is retained and retrieved.

**Stage83 answer:** intentionally blank — Terms are not modified and acceptance mechanism is not approved here.

## Future review completion criteria — informational only

When real billing authority exists, a later stage may define a fail-closed external review intake. That future intake must require real traceable business and legal review references, exact canonical source bindings, explicit answers to every required policy dimension, and independent acceptance before any Terms candidate or gate evidence can be promoted.

Stage83 itself produces none of those artifacts.

## Stage83 hard result

`UNANSWERED_BILLING_POLICY_REVIEW_QUESTIONNAIRE_SKELETON_PREPARED_COLLECTION_BLOCKED_UNTIL_REAL_BILLING_AUTHORITY_NOT_POLICY_NOT_TERMS_NOT_EVIDENCE`

- `REAL_BILLING_AUTHORITY_PRESENT=false`
- `REAL_REVIEW_COLLECTION_ALLOWED=false`
- `CUSTOMER_POLICY_APPROVED=false`
- `TERMS_OF_USE_MODIFIED=false`
- `TARGET_DECISION_CLOSED=false`
- `LEGAL_TERMS_GATE_READY=false`
- `PROVIDER_CALL=false`
- `REMOTE_MUTATION=false`
- `CONTROLLED_LAUNCH=DENIED`
- `PAID_MEDIA=DENIED`
