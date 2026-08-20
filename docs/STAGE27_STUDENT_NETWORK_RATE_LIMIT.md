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
- `BGF-NETWORK-RATE-LIMIT-REMOTE-VERIFICATION-179` — remote write-path proof must be executed by a controlled versioned migration when the connected SQL inspection role is read-only; inability of the inspection connector to assume `service_role` must never be treated as proof or silently bypassed.

## Durable migration — applied

Repository source:

`04_backend_supabase/migrations/20260820063000_stage27_student_network_origin_rate_limit.sql`

Remote authority:

- project: `mceukeondizkwlpfxzgf`;
- migration: `stage27_student_network_origin_rate_limit`;
- remote version: `20260820065403`;
- exact repaired source was merged through PR #38 before application.

The durable Stage 27 migration is now applied. Live schema inspection confirmed one 32-byte pepper row, zero initial rate buckets, no persistent raw-origin column, the expected SECURITY DEFINER private limiter, the SECURITY INVOKER public bridge, and the repaired posture view with the new network counter appended as column 10.

## Durable privacy boundary

The database creates a single 32-byte random pepper during remote migration application. The pepper is never stored in Git and direct table access is revoked even from `service_role`.

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

## Database interface and verified privileges

Private writer/authority:

`private.student_access_network_rate_limit_v1(text,text)`

Public PostgREST bridge:

`public.check_student_access_network_rate_limit_v1(text,text)`

Live inspection confirmed:

- private limiter is `SECURITY DEFINER`;
- public bridge is `SECURITY INVOKER`;
- `service_role` can execute the private limiter and public bridge;
- `anon` and `authenticated` cannot execute either Stage 27 function;
- `service_role` cannot directly select the pepper or rate-bucket tables.

## Observability

When a network-origin route exceeds its minute threshold, the limiter returns `STUDENT_NETWORK_RATE_LIMITED` and upserts a high-severity `network_rate_limit_burst` into the existing Stage 24 signal table.

The signal subject is a truncated keyed digest such as `origin:<digest-prefix>`, never the raw client/network address. The Stage 24 posture view is extended with `network_rate_limit_burst_signals_60m`; a high signal keeps the existing `investigate` posture semantics.

## View replacement compatibility incident and permanent prevention

The first remote Stage 27 application attempt was rejected transactionally because the proposed `CREATE OR REPLACE VIEW private.student_access_security_posture_v1` inserted the new Stage 27 output column before existing Stage 24 output columns. PostgreSQL did not accept the migration and no Stage 27 ledger row was created by that failed attempt.

The repair preserves the nine existing Stage 24 columns in their live ordinal order and appends `network_rate_limit_burst_signals_60m` as the tenth column. This rule is machine-enforced by `04_backend_supabase/tools/verify_postgres_view_replace_compatibility.py` and the dedicated `Postgres View Replace Compatibility` CI workflow.

## Remote verification interlock

The connected SQL inspection endpoint currently executes as `supabase_read_only_user`. It cannot `SET ROLE service_role` and cannot invoke the service-role-only bridge, so it cannot safely perform the required 121-call write probe.

That limitation is not bypassed. The controlled proof is versioned as:

`04_backend_supabase/migrations/20260820065900_stage27_network_rate_limit_verification_interlock.sql`

The verification migration:

1. uses only RFC 5737 TEST-NET origin `203.0.113.55`;
2. derives the same HMAC identity as production logic;
3. requires no pre-existing synthetic bucket or network signal for that identity;
4. calls the private limiter 121 times for `get_workout`;
5. requires calls 1–120 to pass with exact request counts;
6. requires call 121 to return `STUDENT_NETWORK_RATE_LIMITED`, request count 121 and limit 120;
7. deletes the synthetic bucket and signal before commit;
8. rechecks zero synthetic residue;
9. aborts the migration transaction on any mismatch.

Until that verification migration passes remotely and the final ledger is reconciled, authority remains `DATABASE_APPLIED_VERIFICATION_INTERLOCK_REPO_ONLY`.

## Advisors after durable DDL

Security Advisor produced no new Stage 27 actionable finding. Existing warnings for the intentional public student v2 SECURITY DEFINER RPCs remain expected until full Edge cutover and are not authority to revoke those RPCs prematurely.

Performance Advisor produced no new Stage 27 actionable finding. The new cleanup index `student_access_network_rate_buckets_last_seen_idx` is initially reported as unused INFO; immediate unused-index telemetry is not removal authority.

## Remaining promotion sequence

1. Verification migration + updated authority/ledger pass CI.
2. Merge verification interlock to `main`.
3. Reconfirm remote ledger has durable Stage 27 but not verification interlock.
4. Apply exact merged verification migration.
5. Confirm its remote ledger version and zero synthetic bucket/signal residue.
6. Re-run security and performance advisors.
7. Final ledger reconciliation: both Stage 27 migrations remote, only the three historical Stage 17 remote-only exceptions remain.
8. Only then begin actual Edge gateway rate-limit integration.

## Explicit non-promotions

Database Stage 27 being applied does not yet mean:

- Edge gateway rate limiting is active;
- invalid-token abuse protection has passed a live HTTP gateway test;
- student commands route through Edge;
- Flutter has been cut over;
- direct v2 student RPC execute privileges can be revoked;
- alert delivery is verified;
- rollback is verified;
- incident response or production deployment gates are satisfied;
- legal, privacy, terms, DSR, billing credentials or paid media are ready.

The five direct Flutter v2 RPC paths remain intact until the later gateway and client cutover is fully verified.
