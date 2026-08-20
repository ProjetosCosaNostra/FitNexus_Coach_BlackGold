# Stage 26 — Edge Probe Deployment Receipt

## Repository authority

Probe source merged to `main` at:

- `ca6d754527c95f840fb0becb68736aab1c10de69`
- function: `04_backend_supabase/functions/student-access-gateway/index.ts`

The merged probe passed all repository guards, Deno typecheck, Flutter static analysis, tests and release web build before deployment.

## Authoritative Supabase deployment

Observed through the connected Supabase project authority for `mceukeondizkwlpfxzgf`:

- function: `student-access-gateway`
- deployment id: `2f85d9e1-39b3-46d7-a6c2-902eed7b4233`
- version: `1`
- status: `ACTIVE`
- `verify_jwt`: `false`
- bundle SHA-256: `a67cfccbab1f89377afab63cf6100e6fff7baa2f9ff67ba3b58203198f079de9`
- deployed/observed: `2026-08-20T05:42:29Z`
- post-deploy edge-function count: `1`

`verify_jwt=false` is intentional for this possession-token boundary. Version 1 is an inert metadata probe: it does not accept student commands, does not call student RPCs and does not expose student data.

## First live runtime attempt — useful failed assertion

GitHub Actions run `32336914881` reached the deployed Edge Function and proved all common safety checks before failing on one overly strict diagnostic assumption.

Observed safely from the runner:

- HTTP/common probe contract passed;
- `cf-connecting-ip` candidate availability passed;
- no raw network origin was returned by the probe contract;
- no student RPC forwarding was active;
- launch authority remained false;
- client-supplied TEST-NET `x-forwarded-for` reached the function as **untrusted presence**;
- client-supplied TEST-NET `x-real-ip` was stripped or absent before the function.

The failure was the verifier expecting `x-real-ip` to survive the intermediary. That expectation was incorrect and is now permanently classified as:

`BGF-EDGE-HEADER-PRESENCE-ASSUMPTION-170`

Permanent correction: client-supplied forwarded-header **presence is diagnostic only**. An edge intermediary may strip, normalize or preserve such a header. None of these outcomes can make it security authority, and correctness must not depend on the header surviving transit.

No raw IP/header value was printed or persisted by the verifier or receipt.

## Corrected live runtime check

State at this receipt revision: **PENDING RERUN**.

The corrected verifier still requires:

- HTTP 200;
- mode `origin_probe_not_student_gateway_cutover`;
- candidate source `cf-connecting-ip`;
- candidate availability true;
- raw network origin not returned;
- request body not read;
- no student RPC forwarding;
- launch authority false;
- TEST-NET `x-forwarded-for` observed as untrusted diagnostic presence.

For `x-real-ip`, it now requires a boolean observation but does not require preservation. This models real intermediary normalization instead of inventing a transport guarantee.

A successful rerun establishes only **runtime candidate availability**. It does **not** yet establish that a client cannot spoof `cf-connecting-ip`. A separate sentinel-based live test is required before that header can become trusted security authority.

## Explicit non-promotions

This receipt does not claim or promote:

- invalid-token network-origin throttling;
- spoof resistance of `cf-connecting-ip`;
- Flutter cutover;
- revocation of direct anon v2 RPC access;
- alert delivery;
- rollback readiness;
- incident-response gate;
- production-deployment gate;
- billing-provider readiness;
- legal/privacy gates;
- paid media.
