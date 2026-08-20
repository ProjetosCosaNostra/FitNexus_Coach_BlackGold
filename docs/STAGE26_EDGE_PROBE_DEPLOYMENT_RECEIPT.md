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

## Live runtime check

State at this receipt revision: **PENDING**.

The repository now contains `verify_student_access_edge_probe_live.py`, and CI will call the deployed public endpoint from a real external runner. It must prove, without printing or persisting the raw network origin, that:

- HTTP response is 200;
- mode remains `origin_probe_not_student_gateway_cutover`;
- candidate source remains `cf-connecting-ip`;
- candidate presence is true in the deployed runtime;
- raw network origin is not returned;
- request body is not read;
- no student RPC forwarding is active;
- launch authority remains false;
- client-supplied `x-forwarded-for` and `x-real-ip` are observed only as **untrusted presence**.

A successful result establishes only **runtime candidate availability**. It does **not** yet establish that a client cannot spoof `cf-connecting-ip`. A separate sentinel-based live test is required before that header can become trusted security authority.

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
