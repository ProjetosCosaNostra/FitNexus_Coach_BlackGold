# Stage 23 — SECURITY DEFINER Exposure Authority

## Objective

Turn Supabase Security Advisor warnings about externally executable `SECURITY DEFINER` functions into a versioned, fail-closed exposure authority instead of leaving them as informal exceptions.

## Failure class

`BGF-SECURITY-DEFINER-EXPOSURE-DRIFT-159`

## Live authority baseline

A live catalog audit of the authoritative Supabase project found exactly six externally executable `public` `SECURITY DEFINER` functions:

1. `get_student_feedback_context_v2(text)` — anon + authenticated
2. `get_student_workout_v2(text)` — anon + authenticated
3. `issue_student_access_token_v2(uuid)` — authenticated only
4. `set_student_exercise_completion_v2(text,uuid,uuid,boolean,text)` — anon + authenticated
5. `start_student_workout_v2(text,text)` — anon + authenticated
6. `submit_student_workout_feedback_v2(text,uuid,integer,integer,integer,text,text,text)` — anon + authenticated

No other public `SECURITY DEFINER` function is approved for `anon` or `authenticated` execution.

## Why these warnings remain intentional

Five functions are the Stage 21 student possession-token v2 boundary. Anonymous access is the product contract for a student who owns a bounded private link; server-side functions enforce token hashing/validation, expiration, tenant binding, per-operation rate limits and replay-safe command receipts.

`issue_student_access_token_v2` is not anonymous. It is authenticated-only and verifies organization-manager authority before rotation-state access or token mutation.

The authority therefore does not suppress the Supabase warnings. It records why the six exposures are approved and fails closed if the repository exposure surface changes.

## Static replay guard

`verify_security_definer_exposure_authority.py` replays repository migration history for public functions and function EXECUTE grants/revokes. It models PostgreSQL's default EXECUTE-to-PUBLIC behavior for newly created functions and computes the final effective `anon`/`authenticated` exposure of every public `SECURITY DEFINER` function.

CI fails if:

- a new public `SECURITY DEFINER` function becomes externally executable without allowlisting;
- one of the approved six disappears;
- anon/authenticated roles drift from the reviewed baseline;
- a function retains default PUBLIC EXECUTE unexpectedly;
- the authority manifest no longer matches the authoritative project identity.

## Authority file

`04_backend_supabase/security_definer_exposure_authority.json`

The manifest is intentionally separate from the migration ledger. This Stage changes no DDL and therefore requires no Supabase migration.

## Operational invariant

Any future change that intentionally adds an externally executable `SECURITY DEFINER` function must be reviewed as a security-boundary change, update the authority manifest with reason/boundary/roles, and pass CI. A code-only grant is not sufficient authority.

Stage 23 does not promote billing, legal/privacy, incident-response, deployment or paid-media launch gates.
