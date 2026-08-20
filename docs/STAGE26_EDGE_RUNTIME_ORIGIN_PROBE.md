# Stage 26 — Edge Runtime Origin Probe

## Purpose

Stage 25 made the remaining possession-token blind spot explicit: PostgreSQL can rate-limit a resolved student link, but a spray of random invalid tokens has no stable link identity at the database boundary. Network-origin enforcement therefore needs an edge boundary.

Stage 26 does **not** assume that an arbitrary forwarded header is trustworthy. It first proves what the authoritative Supabase Edge runtime actually supplies.

## Failure classes

- `BGF-EDGE-RUNTIME-ORIGIN-ASSUMPTION-167` — code treats an undocumented/unverified origin field as authoritative.
- `BGF-EDGE-PROBE-DATA-LEAK-168` — a diagnostic probe returns or logs raw network origin, bearer tokens or arbitrary request payloads.
- `BGF-EDGE-PROBE-PREMATURE-CUTOVER-169` — deploying a probe is mistaken for a student gateway cutover or launch-readiness evidence.

The Stage 25 classes `163–166` remain active.

## Repository state

`04_backend_supabase/functions/student-access-gateway/index.ts` is currently an inert origin probe.

It:

- accepts `GET` only for the probe;
- returns only booleans about header **presence**;
- checks `cf-connecting-ip` only as a **candidate**;
- reports `x-forwarded-for` and `x-real-ip` only as present/untrusted booleans;
- does not read a request body;
- does not import/use service-role credentials;
- does not call any student RPC;
- does not log anything;
- returns `STUDENT_GATEWAY_NOT_CUTOVER` for non-probe traffic;
- has no launch-gate authority.

This allows an empirical runtime check without touching the student path.

## Why `cf-connecting-ip` is only a candidate

Current Supabase documentation states that Edge Functions sit behind a global edge gateway and that API logging receives Cloudflare request metadata, including `cf-connecting-ip`. That is enough to justify an empirical probe, **not** enough to claim that the function can safely trust the field until the deployed runtime is tested.

A client-supplied `x-forwarded-for` or `x-real-ip` is never considered authoritative by this contract.

## Repo-first promotion sequence

1. Commit the inert probe and permanent guard.
2. Pass Python guards, Deno typecheck, Flutter analysis/tests and release build.
3. Merge the probe to `main`.
4. Deploy the exact `main` probe to project `mceukeondizkwlpfxzgf` with custom possession-token auth semantics (`verify_jwt=false`).
5. Run a live GET health/probe request.
6. Record only booleans; do not persist the raw IP.
7. Attempt a controlled spoof of client forwarding headers and verify they cannot become the authority candidate.
8. Only then design the durable invalid-token network bucket and full gateway.

## Explicitly not completed by this stage

- no invalid-token IP/network throttle;
- no student RPC forwarding through Edge;
- no Flutter cutover;
- no revocation of direct anon v2 RPC execute;
- no alert-delivery receipt;
- no rollback receipt;
- no incident-response gate promotion;
- no production-deployment gate promotion.

## CI interlock

The permanent network-origin guard fails if the probe:

- starts reading request bodies;
- accesses a service-role key;
- calls a student RPC;
- logs request data;
- returns a raw network origin by contract;
- removes any current direct Flutter RPC before a full cutover stage;
- removes anon v2 grants before a full cutover stage;
- self-attests runtime deployment or launch readiness.

The workflow also typechecks the Edge Function with Deno before Flutter build/test stages.
