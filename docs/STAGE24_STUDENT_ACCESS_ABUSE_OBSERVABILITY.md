# Stage 24 — Student Access Abuse Observability

## Objective

Convert the Stage 21 possession-token security telemetry into a permanent, versioned, server-derived abuse-signal boundary without fabricating incident-response evidence and without adding raw-token, IP-address or arbitrary request-payload storage.

Stage 24 is operational observability. It is **not** an incident tabletop, production monitoring delivery receipt, legal review, production deployment receipt or launch authority.

## Preflight authority

Before creating Stage 24 repository DDL, the authoritative Supabase migration ledger was re-read and matched the repository baseline through:

- `20260819145811 stage22_tenant_isolation_relational_interlock`
- `20260819150440 stage22_tenant_isolation_fk_index_hardening`

Only the three known Stage 17 remote-only no-op exceptions remain declared historical divergences.

A read-only live query of `private.student_access_security_events` returned:

- `events_15m = 0`
- `events_60m = 0`
- `events_24h = 0`
- `rate_limited_60m = 0`
- `replay_60m = 0`
- `rotated_24h = 0`
- `distinct_links_24h = 0`

Therefore Stage 24 does **not** claim any observed attack, replay incident, rate-limit incident or completed operational incident response. No synthetic production events are inserted merely to manufacture evidence.

## Failure classes

### `BGF-STUDENT-ACCESS-ABUSE-BLIND-SPOT-160`

Raw security events existed, but there was no permanent derived signal contract for bursts that should demand operator attention.

Prevention:

- private derived signal table;
- deterministic trigger over the Stage 21 event stream;
- service-side posture view;
- read-only live probe;
- CI guard.

### `BGF-STUDENT-ACCESS-ABUSE-THRESHOLD-DRIFT-161`

Risk: SQL thresholds can silently diverge from operational documentation and expected behavior.

Prevention:

- `04_backend_supabase/student_access_abuse_authority.json` is the versioned threshold authority;
- CI asserts exact threshold/window/severity values against the migration contract.

### `BGF-INCIDENT-GATE-SELF-ATTESTATION-162`

Risk: internal telemetry could be incorrectly presented as completion of the external `incident_response` gate.

Prevention:

- authority explicitly denies launch-gate promotion;
- CI asserts that `incident_response` and `production_deployment` remain placeholder-only with null evidence references/digests;
- Stage 24 introduces no evidence migration.

## Signal authority

The authority defines exactly three derived signals.

| Signal | Source | Subject | Rolling window | Threshold | Severity |
| --- | --- | --- | ---: | ---: | --- |
| `rate_limit_burst` | `rate_limited` | link + operation | 5 min | 10 | high |
| `command_replay_burst` | `replay` | link + operation | 10 min | 3 | high |
| `token_rotation_burst` | `rotated` | organization + student | 30 min | 4 | medium |

Signals use fixed time buckets only for deduplication. Threshold evaluation itself uses a rolling window, reducing simple bucket-boundary evasion.

## Database design

Migration:

`04_backend_supabase/migrations/20260819192100_stage24_student_access_abuse_observability.sql`

It creates:

- `private.student_access_security_signals`;
- indexes covering recent-signal lookups, organization triage, the signal table FK, rate/replay rolling-window queries and rotation-subject rolling-window queries;
- `private.detect_student_access_abuse_signal_v1()`;
- `student_access_security_abuse_signal_v1` AFTER INSERT trigger;
- `private.student_access_security_posture_v1` security-invoker view.

The signal table is deduplicated by:

`signal_type + subject_key + operation + window_started_at`

The trigger only observes Stage 21 outcomes:

- `rate_limited`
- `replay`
- `rotated`

It does not block, rewrite or auto-revoke a token. Existing Stage 21 enforcement remains the authority for request rate limiting, replay receipts and token rotation.

## Posture semantics

The service-side posture view uses a 60-minute window:

- `quiet`: no recent derived signal;
- `observe`: at least one medium signal and no high/critical signal;
- `investigate`: at least one high/critical signal.

This posture is deliberately descriptive. It does not acknowledge an incident, close an incident, notify the ANPD, contact a data subject or mutate launch readiness.

## Privacy boundary

Stage 24 stores no:

- raw possession token;
- IP address;
- arbitrary request payload.

`subject_key` is an internal UUID-derived pseudonymous key used only for deduplication.

## Known network-origin blind spot

Invalid-token brute force cannot be attributed reliably inside PostgreSQL because a rejected token has no stable `link_id`, while trustworthy network-origin/IP attribution belongs to the HTTP/edge/deployment layer.

That remains an explicit future production boundary. Stage 24 must not invent an IP address or hash arbitrary invalid bearer tokens into an unbounded database table merely to make observability look complete.

Before `production_deployment` evidence can be promoted, deploy-layer or edge-layer network-origin abuse control and real alert-delivery evidence are still required.

## CI

`04_backend_supabase/tools/verify_student_access_abuse_observability.py` fails closed if:

- the authority manifest changes unexpectedly;
- threshold/window/severity values drift;
- the Stage 21 event source disappears;
- the signal table/trigger/posture view contract disappears;
- anon/authenticated access to the private signal boundary is introduced;
- a public RPC is introduced by Stage 24;
- raw-token/IP storage markers are added to the Stage 24 migration;
- the incident-response or production-deployment placeholders are promoted without real evidence.

The guard is wired into `.github/workflows/flutter_quality_gate.yml` before Flutter setup.

## Live probe

Read-only operational probe:

`04_backend_supabase/tools/student_access_abuse_live_probe.sql`

It reports the derived posture, recent signal counts, recent source-event counts and effective table privileges. It does not mutate production state.

## Migration ledger rule

`stage24_student_access_abuse_observability` is declared `repo_only` until:

1. repository CI passes;
2. the PR is merged to `main`;
3. only then the migration may be applied to the authoritative Supabase project;
4. the remote ledger and live structure are re-read;
5. a second reconciliation removes the temporary divergence.

No DDL is authorized before steps 1–2 complete.
