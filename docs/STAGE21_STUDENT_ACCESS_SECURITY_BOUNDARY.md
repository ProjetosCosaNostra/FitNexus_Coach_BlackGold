# FitNexus Coach BlackGold — Stage 21 Student Access Security Boundary

## Purpose

Stage 21 hardens the public student experience without converting students into full authenticated accounts. The product keeps the low-friction possession-token UX, but the bearer link is no longer treated as an unlimited, immortal capability.

The boundary is deliberately server-authoritative and preserves the BlackGold rule: a repeated security weakness becomes a permanent prevention/detection/test mechanism instead of another manual reminder.

## Concrete weaknesses found

The Stage 5/8 student flow already had important strengths: raw tokens were never stored, tokens were SHA-256 matched, only one active link existed per student, expiry was supported by the resolver, tenant/student/session bindings were checked, direct table access was denied, and mutations were mediated by RPCs.

The remaining production-hardening gaps were:

1. newly issued links had no mandatory expiry and could remain valid indefinitely;
2. anonymous RPCs had no server-side traffic bound for a valid bearer;
3. mutable commands had no explicit command receipt/idempotency key;
4. successful abuse/replay events had no dedicated security ledger;
5. legacy v1 RPCs would remain a bypass if a v2 boundary were added without revoking their client grants;
6. `StudentExperiencePage` still accepted a token from the top-level URL query string even though the generated QR/link already used the fragment route;
7. the web shell did not carry an explicit `no-referrer` policy.

## Stage 21 controls

### 1. Finite bearer lifetime

`issue_student_access_token_v2` rotates the existing link through the already-authoritative issuance routine and then assigns a 30-day expiry.

Existing active links with `expires_at IS NULL` receive a 30-day migration window. No raw token is recovered or persisted.

Rotation lineage is recorded with:

- `revoked_at`;
- `revocation_reason`;
- `rotated_from_link_id`;
- `rotation_number`.

A 30-second issuance cooldown blocks accidental rapid rotations.

### 2. Successful-request rate boundary

`private.student_access_rate_buckets` counts successful authenticated-by-possession traffic per student link, operation and minute.

Current ceilings are deliberately generous enough for normal UI usage:

- workout snapshot: 90/minute;
- feedback context: 45/minute;
- start workout: 12/minute;
- exercise completion: 60/minute;
- feedback submission: 12/minute.

When the limit is exceeded, the v2 RPC returns `STUDENT_ACCESS_RATE_LIMITED` plus a retry hint and records the event in the security ledger.

Important limitation: PostgreSQL RPC transactions roll back their own state if a downstream function raises. Stage 21 therefore guarantees durable rate accounting for successful/replayed v2 traffic and explicit rate-limit responses. Invalid random-token brute force remains cryptographically impractical because the bearer is 256 random bits; a future edge boundary may add network/IP-level throttling when production infrastructure is selected.

### 3. Replay/idempotency receipts

Mutable v2 RPCs require a 128-bit lowercase hex `p_command_id` generated in Flutter with `Random.secure()`.

`private.student_access_command_receipts` is unique on:

`(link_id, operation, command_id)`

The first delivery executes the underlying authoritative mutation and stores its JSON response. A duplicate delivery returns the stored response instead of executing the same command again. Receipts are retained for 30 days and old receipts are opportunistically pruned per link.

This protects:

- workout start;
- exercise completion commands;
- workout feedback submission.

The existing business operations were already mostly idempotent by data model (one in-progress session; one exercise log per session/exercise; one feedback per session). Stage 21 adds an explicit transport/command identity on top of those semantic protections.

### 4. Abuse/replay observability

`private.student_access_security_events` records security-relevant successful boundary events without raw bearer material:

- `allowed` command;
- `rate_limited` request;
- `replay` receipt hit;
- token `rotated`.

Only service-role read access is granted for operational inspection. Anonymous/authenticated clients have no direct access to the private tables.

### 5. Legacy bypass closure

After the v2 boundary exists, client execute grants are revoked from the legacy possession-token RPCs:

- `issue_student_access_token`;
- `get_student_workout`;
- `start_student_workout`;
- `set_student_exercise_completion`;
- `get_student_feedback_context`;
- `submit_student_workout_feedback`.

The v2 SECURITY DEFINER wrappers can still call the old business functions internally as owner. This avoids duplicating mature domain logic while preventing clients from bypassing the new security controls.

### 6. URL leakage reduction

Generated student links already use the fragment form:

`#/student?token=<bearer>`

Stage 21 removes the fallback that read `Uri.base.queryParameters['token']`. Therefore the bearer is accepted from the fragment only (or a direct in-memory constructor argument used internally).

Fragments are not sent as part of normal HTTP request targets. The web shell also adds:

`<meta name="referrer" content="no-referrer">`

This is defense in depth and does not replace the server-side bearer controls.

## Permanent failure classes

- `BGF-STUDENT-ACCESS-UNBOUNDED-BEARER-147` — a possession token must not regain unlimited lifetime/rotation semantics.
- `BGF-STUDENT-ACCESS-REPLAY-148` — mutable anonymous student commands must retain secure command IDs and server receipts.
- `BGF-STUDENT-ACCESS-RATE-LIMIT-149` — successful possession-token traffic must remain rate-bounded and observable.
- `BGF-STUDENT-ACCESS-URL-LEAK-150` — student bearer tokens must not return to the top-level URL query string or normal referrer flow.
- `BGF-STUDENT-ACCESS-LEGACY-RPC-BYPASS-151` — client code and grants must not bypass the hardened v2 RPC boundary.
- `BGF-STUDENT-ACCESS-BOUNDARY-FILE-MISSING-152` — Stage 21 authority/guard artifacts cannot disappear silently.

`verify_student_access_security_contract.py` enforces these invariants in every Flutter Quality Gate run.

## Migration authority

Stage 21 follows the Migration Ledger Reconciler two-phase workflow.

During repository-first promotion, `stage21_student_access_security_boundary` is explicitly declared `repo_only`. The SQL must pass CI and enter `main` before it is applied to the authoritative Supabase project. After remote application, the observed remote ledger version must be recorded and the temporary divergence removed.

No migration may be silently applied remote-first.

## What Stage 21 does not claim

Stage 21 does **not**:

- promote the product to production;
- satisfy `production_deployment`;
- activate Asaas credentials;
- approve legal/privacy drafts;
- launch ads;
- create IP/device fingerprinting;
- claim that database-level rate limits replace CDN/WAF/edge controls.

Those authorities remain independent under Stage 20 Controlled Launch Admission.
