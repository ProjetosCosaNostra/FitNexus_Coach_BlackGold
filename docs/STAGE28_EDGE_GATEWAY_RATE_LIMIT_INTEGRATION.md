# Stage 28 — Edge Gateway Rate-Limit Integration

## Objective

Integrate the remotely verified Stage 27 network-origin rate limiter into the repository source for `student-access-gateway` so every valid student action is throttled by trusted network origin **before** possession-token validation or a student v2 RPC is executed.

This stage is repository-first. The authoritative deployed Edge runtime remains version 2 until this candidate passes CI and is merged. Repository implementation is not runtime proof.

## Failure classes

- `BGF-EDGE-RATE-LIMIT-ORDER-BYPASS-180` — no student route may validate or forward a possession token before the durable network-origin limiter executes.
- `BGF-EDGE-SECRET-MATERIAL-EXPOSURE-181` — backend secret/service-role credentials must come only from Edge environment variables and may never be returned, logged or committed.
- `BGF-EDGE-RAW-TOKEN-LOGGING-182` — raw possession tokens and raw request payloads must never be logged or echoed as diagnostics.
- `BGF-EDGE-ACTION-RPC-MAPPING-DRIFT-183` — each public gateway action has one fixed student v2 RPC and one fixed Stage 27 limiter operation.
- `BGF-EDGE-CANDIDATE-DEPLOYMENT-SELF-ATTESTATION-184` — repository source, CI success or merge cannot be recorded as runtime deployment/proof.

## Implemented repository candidate

The candidate supports `GET`, `POST` and `OPTIONS`.

`GET` remains a safe origin/sentinel metadata surface. It returns booleans only and never returns the raw `cf-connecting-ip` value.

`POST` accepts one of five actions:

| Gateway action | Student v2 RPC |
| --- | --- |
| `get_workout` | `get_student_workout_v2` |
| `start_workout` | `start_student_workout_v2` |
| `set_completion` | `set_student_exercise_completion_v2` |
| `get_feedback_context` | `get_student_feedback_context_v2` |
| `submit_feedback` | `submit_student_workout_feedback_v2` |

For every valid action the candidate:

1. requires a plausible platform-provided `cf-connecting-ip` value;
2. limits the request body to 16 KiB;
3. resolves a backend credential only from Edge environment variables;
4. calls `check_student_access_network_rate_limit_v1` with the transient trusted origin + action;
5. returns HTTP 429 only when the Stage 27 limiter returns `STUDENT_NETWORK_RATE_LIMITED`;
6. only after the limiter succeeds, validates/builds the possession-token RPC parameters;
7. forwards to the mapped v2 student RPC;
8. does not log token, raw origin, request body, backend secret or upstream error body.

## Backend credential strategy

The candidate follows current Supabase key guidance:

- prefer `SUPABASE_SECRET_KEYS` and the `default` `sb_secret_...` key;
- send a new secret key on the `apikey` header only;
- retain `SUPABASE_SERVICE_ROLE_KEY` only as a legacy fallback;
- when the legacy JWT-based service-role key is used, send `apikey` plus `Authorization: Bearer ...`;
- `verify_jwt` remains false for the Edge function because the student boundary is possession-token based and backend authorization is handled by the function itself.

No key material is stored in repository source.

## Stage 27 dependency

Stage 28 depends on both remotely reconciled Stage 27 migrations:

- `stage27_student_network_origin_rate_limit` — remote version `20260820065403`;
- `stage27_network_rate_limit_verification_interlock` — remote version `20260820070524`.

The Stage 27 proof established 120 permitted `get_workout` requests followed by request 121 returning `STUDENT_NETWORK_RATE_LIMITED`, with zero synthetic bucket/signal residue after commit.

## Explicit non-promotions

At repository-candidate state:

- the deployed Edge runtime is still version 2;
- live invalid-token network-origin throttling is not yet proven over HTTP;
- Flutter still calls the five v2 RPCs directly;
- direct anonymous/authenticated execute grants remain intact;
- client direct-RPC fallback is not removed;
- alert delivery is not verified;
- rollback is not verified;
- incident-response or production-deployment gates are not promoted;
- paid media remains blocked.

## Next controlled promotion

After full CI and merge, deploy the exact merged `student-access-gateway` source to the authoritative Supabase project, record the new runtime identity/version/bundle, then run controlled live HTTP proofs for health, route forwarding and invalid/random-token rate limiting. Flutter cutover remains forbidden until those runtime proofs pass.
