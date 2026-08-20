# Stage 27 — Student Network-Origin Rate Limit

## Objective

Close the remaining invalid/random possession-token brute-force blind spot at the Edge boundary without persisting a raw client/network address and without weakening the existing token/link rate limits.

Stage 26 established the prerequisite source authority: in the authoritative Supabase Edge runtime, normal requests expose `cf-connecting-ip` as the network-origin candidate and a deliberate client attempt to force that protected header was rejected at the edge with HTTP 403. Stage 27 uses that source only after the proof recorded by workflow run `32338900002`.

## Failure classes

- `BGF-EDGE-INVALID-TOKEN-RATE-LIMIT-174` — invalid/random token attempts must be throttled before token validation can be abused as an unbounded public path.
- `BGF-NETWORK-ORIGIN-RAW-PERSISTENCE-175` — raw IP/network-origin values must not become durable database telemetry.
- `BGF-NETWORK-THROTTLE-CALLER-LIMIT-OVERRIDE-176` — a caller must not be able to supply or weaken its own rate-limit threshold.
- `BGF-EDGE-SECRET-KEY-LEAK-177` — elevated backend key material and the network-origin pseudonymization pepper must never enter source, client code or public responses.
- `BGF-POSTGRES-VIEW-COLUMN-ORDER-178` — `CREATE OR REPLACE VIEW` must preserve every existing output-column name and ordinal position; new columns are append-only unless a deliberate drop/recreate migration is separately reviewed.

## Repository migration

`04_backend_supabase/migrations/20260820063000_stage27_student_network_origin_rate_limit.sql`

The migration is intentionally repository-first. Until CI, merge and remote application complete, the authority state remains `REPO_ONLY_DDL_NOT_APPLIED` and the migration ledger declares `stage27_student_network_origin_rate_limit` as `repo_only`.

## Durable privacy boundary

The database creates a single 32-byte random pepper during remote migration application. The pepper is never stored in Git and direct access to the secret table is revoked even from `service_role`.

For each request the trusted Edge runtime will eventually pass the transient normalized network-origin string to the service-only bridge. PostgreSQL converts it to `inet`, canonicalizes it, and computes:

`HMAC-SHA256(pepper, "fitnexus-student-origin-v1:" + normalized_origin)`

Only the 32-byte digest is stored in rate buckets. There is no persistent raw-IP/network-origin column.

## Database-owned thresholds

The caller supplies only operation + transient origin. Limits are selected inside the private function:

| Operation | Requests/minute |
| --- | ---: |
| `get_workout` | 120 |
| `start_workout` | 30 |
| `set_completion` | 120 |
| `get_feedback_context` | 90 |
| `submit_feedback` | 30 |

The thresholds are deliberately above the existing valid-link Stage 21 limits. Stage 27 is a coarse network-origin abuse damper before token validation; the stricter per-link/token protections remain authoritative after a possession token resolves successfully.

## Database interface

Private writer/authority:

`private.student_access_network_rate_limit_v1(text,text)`

Public PostgREST bridge:

`public.check_student_access_network_rate_limit_v1(text,text)`

The public bridge is `SECURITY INVOKER`, is executable only by `service_role`, and delegates to the minimum-purpose private `SECURITY DEFINER` function. `anon` and `authenticated` receive no execute privilege on this bridge.

## Observability

When a network-origin route exceeds its minute threshold, the limiter returns `STUDENT_NETWORK_RATE_LIMITED` and upserts a high-severity `network_rate_limit_burst` into the existing Stage 24 signal table.

The signal subject is a truncated keyed digest such as `origin:<digest-prefix>`, never the raw client/network address. The Stage 24 posture view is extended with `network_rate_limit_burst_signals_60m`; a high signal keeps the existing `investigate` posture semantics.

## View replacement compatibility incident and permanent prevention

The first remote Stage 27 application attempt was rejected transactionally because the proposed `CREATE OR REPLACE VIEW private.student_access_security_posture_v1` inserted the new Stage 27 output column before existing Stage 24 output columns. PostgreSQL does not permit an existing view column to be silently renamed/reordered through `CREATE OR REPLACE VIEW`. The migration did not enter the remote migration ledger, so no partial Stage 27 schema was accepted as authority.

The repair preserves the nine existing Stage 24 columns in their live ordinal order and appends `network_rate_limit_burst_signals_60m` as the tenth column. This rule is now machine-enforced by `04_backend_supabase/tools/verify_postgres_view_replace_compatibility.py` and the dedicated `Postgres View Replace Compatibility` CI workflow. Future migrations that reorder/rename an existing output column while using `CREATE OR REPLACE VIEW` fail before merge.

## Mandatory promotion sequence

1. Repository migration, authority and guards pass CI.
2. Merge to `main`.
3. Apply exact merged migration to project `mceukeondizkwlpfxzgf`.
4. Verify schema, privileges and absence of raw-origin columns.
5. Run a controlled transactional rate-limit probe and roll it back.
6. Run Supabase security and performance advisors.
7. Reconcile the remote migration ledger so Stage 27 is no longer `repo_only`.
8. Only then integrate the Edge gateway so the limiter executes before possession-token validation.

## Explicit non-promotions

This repository DDL does not yet mean:

- Edge gateway rate limiting is active;
- invalid-token abuse protection has passed a live HTTP test;
- student commands route through Edge;
- Flutter has been cut over;
- direct v2 student RPC execute privileges can be revoked;
- alert delivery is verified;
- rollback is verified;
- incident response or production deployment gates are satisfied;
- legal, privacy, terms, DSR, billing credentials or paid media are ready.

The five direct Flutter v2 RPC paths remain intact until the later gateway and client cutover is fully verified.
