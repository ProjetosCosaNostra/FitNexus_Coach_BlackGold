# Stage 25 — Student Network-Origin Abuse Cutover Contract

## Objective

Turn the remaining invalid-token/network-origin abuse blind spot into an explicit fail-closed cutover contract without pretending that an edge gateway is already deployed or that alert delivery has been tested.

Stage 24 protects and observes requests after a possession token resolves to a stable `link_id`. That is intentionally insufficient for random invalid-token brute force: rejected tokens do not provide a durable link identity, and PostgreSQL is not the trustworthy owner of network-origin metadata.

Stage 25 therefore records exactly what remains unprotected and prevents a future half-cutover from being mistaken for security readiness.

## Live preflight

The authoritative Supabase runtime was queried before this contract was created:

- `Supabase.list_edge_functions` returned `[]`;
- observed Edge Function count: `0`;
- `student-access-gateway` is not deployed.

The current Flutter student repositories were also read from `main` and still call five anonymous v2 RPCs directly:

1. `get_student_workout_v2`
2. `start_student_workout_v2`
3. `set_student_exercise_completion_v2`
4. `get_student_feedback_context_v2`
5. `submit_student_workout_feedback_v2`

Therefore the authoritative Stage 25 state is:

`NOT_ENFORCED_DIRECT_RPC_PATH_ACTIVE`

This is not a defect hidden by documentation; it is now a versioned blocking state.

## Failure classes

### `BGF-NETWORK-ORIGIN-ABUSE-BYPASS-163`

A database-only rate limit cannot bound random invalid-token attempts by trustworthy network origin because failed token resolution does not yield a stable possession-link identity.

Prevention contract:

- future edge gateway owns network-origin throttling;
- PostgreSQL continues to own valid-token/link-based throttling;
- the two layers are complementary, not substitutes.

### `BGF-EDGE-ORIGIN-TRUST-164`

A future gateway must not trust an origin/IP value simply because the client supplied a forwarding header.

Prevention contract:

- network origin must come only from metadata supplied by the trusted deployed runtime;
- client-controlled forwarded headers are not authority;
- the exact runtime metadata must be verified in the deployed environment before promotion.

Stage 25 deliberately does not guess a provider-specific header and does not fabricate a trusted-IP recipe before runtime verification.

### `BGF-STUDENT-ACCESS-PARTIAL-EDGE-CUTOVER-165`

A dangerous intermediate state would be any of the following:

- Flutter partly moved to an edge gateway while some student actions still call v2 RPCs directly;
- anon execute revoked before the gateway and client cutover are verified, breaking student access;
- gateway deployed while direct anonymous RPC bypass remains and is incorrectly called protected;
- client keeps a direct-RPC fallback after edge cutover.

The Stage 25 CI guard treats the current architecture as one atomic state. Any partial change fails until the authority and cutover implementation advance together.

### `BGF-ALERT-DELIVERY-SELF-ATTESTATION-166`

Stage 24 can derive `observe`/`investigate`, but that does not prove that a human receives an alert.

Prevention contract:

- alert delivery requires a real runtime receipt;
- no repository manifest can self-promote `incident_response`;
- no quiet posture can be interpreted as monitoring/alerting readiness.

## Current direct boundary

Current Flutter files use Supabase RPC directly. That means the database sees the request only after the HTTP/API layer has accepted and routed it.

The Stage 21 v2 RPCs remain anonymous by design in the current architecture. This is required for possession-token student access and remains protected by:

- finite token lifetime;
- hashed bearer storage;
- link-based rate limiting;
- replay receipts;
- tenant isolation;
- direct-table denial;
- Stage 23 SECURITY DEFINER exposure authority;
- Stage 24 derived abuse signals.

But direct anonymous RPC access remains a bypass around any future edge-only network-origin throttle until a verified cutover revokes it.

## Target cutover invariants

A future `student-access-gateway` is only allowed to become authoritative when all of the following are true together:

- one gateway owns every student possession-token operation;
- trusted runtime metadata, not client headers, owns network origin;
- invalid-token attempts are bounded by network origin + route;
- valid-token Stage 21 database rate limits remain active as defense in depth;
- raw possession tokens are never logged;
- arbitrary request payloads are never copied into security telemetry;
- Flutter student traffic has no direct-RPC fallback;
- anonymous execute on the five v2 RPCs is revoked only after gateway cutover verification;
- alert delivery has a controlled runtime receipt;
- rollback has a controlled runtime receipt;
- any privilege-changing DDL follows the Migration Ledger Reconciler repo-first workflow.

## Why no Edge Function is deployed in this Stage

Deploying a dormant gateway while the client continues to bypass it would not close the vulnerability. Revoking direct RPC access before a verified gateway/client cutover could break the student product. Doing both without a runtime test would turn a security improvement into an uncontrolled production change.

Accordingly, Stage 25 stops at the exact external/runtime boundary instead of manufacturing a green status.

## CI contract

`04_backend_supabase/tools/verify_student_access_network_origin_boundary.py` asserts:

- observed authority state is still `NOT_ENFORCED_DIRECT_RPC_PATH_ACTIVE`;
- runtime snapshot records zero Edge Functions and no deployed gateway;
- all five direct v2 RPC client paths still exist in the current state;
- all five current anon v2 grants still exist in the current state;
- Stage 24 keeps its network-origin blind spot explicit;
- a gateway implementation cannot silently appear while the authority still claims the old state;
- incident-response and production-deployment evidence placeholders stay unpromoted;
- alert delivery, network-origin throttling and deployment readiness remain explicitly unverified.

This guard is a transition interlock. A future real cutover must intentionally replace its current-state assertions rather than bypass them.

## External boundary reached

The next real security advancement requires runtime work, not another database fiction:

1. implement the gateway;
2. deploy it to the authoritative Supabase project;
3. verify trustworthy network-origin metadata there;
4. perform controlled invalid-token throttling tests;
5. cut Flutter over atomically;
6. repo-first revoke direct anonymous RPC execute;
7. test alert delivery and rollback;
8. reconcile all runtime/DDL evidence.

Until that happens, `incident_response`, `production_deployment`, legal gates, billing activation and paid media remain independent and blocked.
