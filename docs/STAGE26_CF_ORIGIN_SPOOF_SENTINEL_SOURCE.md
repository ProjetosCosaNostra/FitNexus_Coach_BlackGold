# Stage 26 — cf-connecting-ip Spoof Sentinel Source

## Purpose

The deployed Stage 26 probe proved that `cf-connecting-ip` is present as a plausible network-origin candidate in the authoritative Supabase Edge runtime. Presence alone is not enough to trust it for abuse controls.

This phase prepares a privacy-safe live spoof-resistance experiment **repo-first**. It does not yet change the deployed runtime.

## Failure classes

- `BGF-CF-ORIGIN-SPOOF-171` — a client can force the candidate to a client-chosen value, or trust is promoted without a negative sentinel equality result.
- `BGF-EDGE-SENTINEL-DATA-LEAK-172` — spoof testing returns, logs or persists the raw runtime network origin.

## Sentinel contract

The next Edge source uses RFC 5737 TEST-NET-3 value `203.0.113.77` only as a known comparison sentinel.

The function never returns the actual runtime origin. It returns one boolean only:

`candidate_equals_known_client_spoof_sentinel`

The future live verifier will send `cf-connecting-ip: 203.0.113.77` from an external runner.

Interpretation after exact-main deployment:

- `false`: the runtime candidate did not equal the client sentinel. This is the required condition before `cf-connecting-ip` can be promoted to trusted network-origin input.
- `true`: fail closed. The candidate is client-spoofable and cannot be used as network-origin security authority.
- missing/ambiguous: fail closed.

## Current runtime remains v1

While this source PR is under review/CI, the deployed function remains:

- version `1`;
- deployment id `2f85d9e1-39b3-46d7-a6c2-902eed7b4233`;
- bundle SHA-256 `a67cfccbab1f89377afab63cf6100e6fff7baa2f9ff67ba3b58203198f079de9`;
- candidate observed but `origin_candidate_trusted_for_security=false`;
- spoof resistance not verified.

CI still probes deployed v1 for the already-proven candidate-availability contract. The new sentinel source is separately typechecked and structurally guarded. It will not be deployed until this source PR is green and merged to `main`.

## No cutover

This phase does not:

- implement network-origin throttling;
- forward student operations through Edge;
- change Flutter callsites;
- revoke anon access to the five v2 RPCs;
- test alert delivery;
- claim rollback readiness;
- promote incident-response, production-deployment, billing, legal/privacy or paid-media gates.
