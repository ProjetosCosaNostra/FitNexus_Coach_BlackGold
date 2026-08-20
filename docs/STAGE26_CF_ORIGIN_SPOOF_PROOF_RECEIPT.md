# Stage 26 — CF Origin Spoof Proof Receipt

## Scope

This receipt records only the runtime trust proof for the `cf-connecting-ip` network-origin candidate used by the future student access gateway boundary. It does not claim that invalid-token rate limiting, student gateway routing, Flutter cutover, direct RPC revocation, alert delivery, rollback readiness, incident response, production deployment, legal gates, billing credentials or paid media are complete.

## Repository source authority

The privacy-safe spoof sentinel source was merged to `main` at:

- source main SHA: `0215cb417e0fafe659649d60a4d889b947d489cb`
- Edge Function: `04_backend_supabase/functions/student-access-gateway/index.ts`
- sentinel: `203.0.113.77` (`RFC5737 TEST-NET-3`)
- response signal: `candidate_equals_known_client_spoof_sentinel`

The function never returns, logs or persists the raw runtime network origin. The sentinel is a documentation-only TEST-NET address, not a user address.

## Authoritative Edge runtime

Observed in Supabase project `mceukeondizkwlpfxzgf`:

- function: `student-access-gateway`
- deployment id: `2f85d9e1-39b3-46d7-a6c2-902eed7b4233`
- version: `2`
- status: `ACTIVE`
- `verify_jwt`: `false`
- bundle SHA-256: `6d67c45bdd23694bcfbe24503c84d1d0e7c540a43d7c54e104a376a7c2a18c5a`
- deployed/observed: `2026-08-20T06:01:01Z`

Version 2 remains an inert metadata/sentinel probe. It does not accept student commands and does not forward student RPCs.

## Candidate availability proof

Earlier live run `32337114801` proved that normal requests reach the function with `cf-connecting-ip` available as a plausible runtime candidate while raw network-origin data remains undisclosed. Client-supplied `x-forwarded-for` and `x-real-ip` remain untrusted diagnostic metadata regardless of whether an intermediary preserves, strips or normalizes them.

## First spoof verifier failure — prevention class

Live run `32338828582` deliberately sent the RFC5737 sentinel as a client-supplied `cf-connecting-ip` header. The request was rejected with HTTP `403` before the Edge Function executed.

The original verifier incorrectly treated every non-200 outcome as a test failure. The security boundary itself had not failed; the verifier had encoded the wrong success model. This became permanent failure class:

- `BGF-CF-SPOOF-PROOF-OUTCOME-ASSUMPTION-173`

Permanent corrective rule:

- HTTP `403` on the deliberate protected-header spoof attempt is accepted as a strong safe outcome;
- HTTP `200` is accepted only when the function reports sentinel equality `false`;
- HTTP `200` with sentinel equality `true` fails closed;
- missing or ambiguous evidence fails closed;
- a rejection body is never inspected or printed.

## Successful spoof-resistance proof

Corrected GitHub Actions run `32338900002` completed successfully. The live proof reported:

- baseline HTTP status: `200`
- runtime version expected: `2`
- network-origin candidate: `cf-connecting-ip`
- sentinel standard: `RFC5737_TEST_NET_3`
- spoof proof outcome: `BLOCKED_AT_EDGE_403`
- `CLIENT_CAN_FORCE_CF_CONNECTING_IP=false`
- raw runtime origin returned: `false`
- student RPC forwarding: `false`
- launch gate authority: `false`

The same run also passed all repository guards, Deno typecheck, Flutter static analysis, 31 tests and the release web build.

## Authority promoted by this receipt

The evidence supports exactly this promotion:

- `cf-connecting-ip` is an approved network-origin source for the tested authoritative Supabase Edge runtime path because a normal request receives the runtime candidate and a direct client attempt to force that protected header is rejected at the edge.

This is source trust, not a complete abuse-control implementation.

## Explicit non-promotions

The following remain blocked or not implemented:

- invalid-token rate limiting by network origin and route;
- full student command routing through the Edge gateway;
- Flutter cutover from the five direct v2 RPC calls;
- revocation of direct anon/authenticated execute on the student v2 RPCs;
- alert delivery verification;
- rollback verification;
- incident-response gate;
- production-deployment gate;
- billing credential gate;
- legal/privacy/terms/DSR gates;
- paid media.

The existing direct student RPC path and current privileges must remain intact until the complete gateway and Flutter cutover have passed their own live verification.
