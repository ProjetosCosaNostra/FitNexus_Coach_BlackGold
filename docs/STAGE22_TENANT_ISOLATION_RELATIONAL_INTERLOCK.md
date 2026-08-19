# Stage 22 — Tenant Isolation Relational Interlock

## Objective

Turn tenant isolation on the anonymous student execution path into a database-enforced relational invariant, not only a property of current RPC implementation code.

Stage 21 hardened possession-token lifetime, replay, rate limiting, issuance authority and client handling. Stage 22 addresses the remaining structural assumption: a privileged or future code path could theoretically write a `workout_sessions.student_access_link_id` or `student_access_links.rotated_from_link_id` that points at another student or organization because those relationships were still single-column foreign keys.

## Failure classes

- `BGF-TENANT-RELATIONSHIP-DECOUPLING-154`: tenant identity is checked procedurally but not enforced across every relational edge.
- `BGF-TENANT-ANON-RPC-DOWNGRADE-155`: a legacy anonymous RPC regains EXECUTE and bypasses the v2 boundary.
- `BGF-TENANT-DIRECT-TABLE-BYPASS-156`: direct anonymous access to the possession-token table is restored.
- `BGF-TENANT-CLIENT-RPC-DOWNGRADE-157`: Flutter silently returns to legacy student RPCs or top-level bearer query parameters.

## Live preflight evidence

Before creating the migration, the authoritative Supabase project was inspected read-only.

Observed state:

- `workout_access_link_cross_tenant_mismatches = 0`
- `rotation_lineage_cross_tenant_mismatches = 0`
- anonymous direct table privileges on `student_access_links`, `workout_sessions`, `workout_exercise_logs` and `workout_feedback` are absent
- the only anonymous student workout/feedback entrypoints are the Stage 21 v2 security-definer RPCs
- legacy student v1 RPCs are not executable by `anon`
- existing RLS policies on professor-visible student/training/session/feedback data are organization-scoped

This means Stage 22 hardens a currently clean state rather than attempting to normalize known cross-tenant corruption.

## Relational interlocks

Migration `stage22_tenant_isolation_relational_interlock` adds a stable unique key on:

`student_access_links(id, student_id, organization_id)`

It then replaces the remaining single-column lineage relationships with composite tenant-bound relationships:

1. `workout_sessions(student_access_link_id, student_id, organization_id)` → `student_access_links(id, student_id, organization_id)`
2. `student_access_links(rotated_from_link_id, student_id, organization_id)` → `student_access_links(id, student_id, organization_id)`

The optional link columns retain `SET NULL` deletion semantics without nulling the mandatory student or organization columns. Rotation also receives a no-self-reference check.

## CI adversarial guard

`verify_tenant_isolation_contract.py` fails closed when any of these regressions appears:

- Stage 22 composite foreign keys/index/check disappear;
- legacy v1 student RPCs stop being explicitly revoked;
- expected v2 anonymous RPC grants disappear;
- direct-deny protection on `student_access_links` disappears;
- Flutter calls any legacy student RPC;
- Flutter accepts the possession token again from the top-level URL query string.

`tenant_isolation_live_probe.sql` is the repeatable read-only catalog/data probe for post-migration and future security checks.

## Promotion rule

This Stage follows the permanent Migration Ledger Reconciler workflow:

1. live ledger reconciled before DDL;
2. migration committed repo-first and declared `repo_only`;
3. CI must pass and PR must merge to `main`;
4. only then apply the already-versioned migration to the authoritative Supabase project;
5. run live probe and constraint verification;
6. update the authority manifest with the remote version and remove temporary `repo_only`;
7. reconcile and merge the receipt.

No Asaas, legal/privacy gate, production deployment or paid acquisition state is promoted by Stage 22.
