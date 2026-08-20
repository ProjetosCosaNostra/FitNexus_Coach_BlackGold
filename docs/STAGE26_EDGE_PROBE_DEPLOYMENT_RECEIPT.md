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

## Successful corrected live runtime check

GitHub Actions run `32337114801` completed successfully, including every existing guard, the Stage 26 guard, Deno typecheck, the live Edge probe, Flutter analysis, 31 tests and the release web build.

The live step reported only privacy-safe state:

- `EDGE_HTTP_STATUS=200`
- `NETWORK_ORIGIN_CANDIDATE=cf-connecting-ip`
- `NETWORK_ORIGIN_CANDIDATE_AVAILABLE=true`
- `X_FORWARDED_FOR_CLIENT_HEADER_PRESERVED=true`
- `X_REAL_IP_CLIENT_HEADER_PRESERVED=false`
- `CLIENT_FORWARDED_HEADERS=UNTRUSTED_REGARDLESS_OF_NORMALIZATION`
- `RAW_NETWORK_ORIGIN_RETURNED=false`
- `STUDENT_RPC_FORWARDING=false`
- `LAUNCH_GATE_AUTHORITY=false`

This establishes that the deployed Supabase Edge runtime exposes a plausible `cf-connecting-ip` candidate to this function. The authority therefore advances to:

`ORIGIN_PROBE_RUNTIME_CANDIDATE_OBSERVED`

It does **not** make `cf-connecting-ip` trusted security authority yet. A client-spoof sentinel test remains mandatory, and the authority explicitly records `runtime_origin_candidate_trusted_for_security=false` and `cf_connecting_ip_spoof_resistance_verified=false`.

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
