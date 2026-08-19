# BGF-SUBSCRIPTION-SERVICE-LEAST-PRIVILEGE-067

## Failure class

A billing/provider adapter that receives broad `service_role` table grants can accidentally or maliciously rewrite plan definitions, delete subscription state, or alter historical authority evidence beyond the minimum required to synchronize provider state.

## Permanent prevention

The Stage 15 hardening migration resets service-role privileges and grants only:

- `subscription_plans`: SELECT;
- `organization_subscriptions`: SELECT + UPDATE;
- `subscription_authority_events`: SELECT + INSERT.

The provider adapter can therefore read capacity policy, transition the current subscription state and append evidence, but cannot mutate plan definitions or UPDATE/DELETE historical authority events.

## Regression contract

`verify_subscription_entitlements_contract.py` fails if the narrow grants disappear. Remote privilege attestation is required before promotion.
