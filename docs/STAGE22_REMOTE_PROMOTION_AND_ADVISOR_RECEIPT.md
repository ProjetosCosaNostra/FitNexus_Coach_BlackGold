# Stage 22 — Remote Promotion + Advisor Receipt

## First remote promotion

Authoritative Supabase project: `mceukeondizkwlpfxzgf`

Repository merge admitted before DDL:

`8cbc37dcbf61f4cc4ace31e3c6b91e05c972a286`

Observed remote ledger row after application:

- `20260819145811 stage22_tenant_isolation_relational_interlock`

## Structural verification

Post-application catalog verification confirmed:

- `student_access_links_rotation_same_student_org_fk` is composite across `rotated_from_link_id, student_id, organization_id`;
- its delete action is partial `SET NULL` on `rotated_from_link_id` only;
- `workout_sessions_access_link_same_student_org_fk` is composite across `student_access_link_id, student_id, organization_id`;
- its delete action is partial `SET NULL` on `student_access_link_id` only;
- `student_access_links_rotation_not_self_chk` is active.

Read-only live probe after migration:

- `workout_access_link_cross_tenant_mismatches = 0`
- `rotation_lineage_cross_tenant_mismatches = 0`
- `anon_v2_workout_execute = true`
- `anon_legacy_workout_execute = false`
- `anon_student_access_links_select = false`
- `anon_workout_sessions_select = false`

## Security Advisor interpretation

The Security Advisor reports warnings for the intentionally exposed Stage 21 v2 `SECURITY DEFINER` possession-token RPCs and the authenticated token-issuance RPC. These warnings describe the deliberate API boundary: anonymous students authenticate possession with the bounded bearer token, while the functions enforce token validation, tenant binding, rate limits and command replay protection internally.

They are therefore retained as **reviewed intentional exposure**, not silently suppressed and not treated as authority to remove the student access surface. The adversarial CI guard continues to require v2-only anonymous exposure and legacy v1 denial.

## Performance Advisor finding

Immediately after the relational interlock was applied, the Performance Advisor identified two new composite foreign keys without covering indexes:

- `student_access_links_rotation_same_student_org_fk`
- `workout_sessions_access_link_same_student_org_fk`

This is actionable and has been converted into permanent failure class:

`BGF-TENANT-FK-INDEX-COVERAGE-158`

Follow-up migration, still repo-first at this receipt stage:

`stage22_tenant_isolation_fk_index_hardening`

It adds covering indexes matching both foreign-key column orders. The tenant-isolation CI guard now requires these indexes so the advisor finding cannot regress silently.

## Promotion discipline

The first Stage 22 migration is reconciled into the remote baseline in the same branch that declares the advisor-driven index follow-up as temporary `repo_only`. The index migration must pass CI and enter `main` before remote application, after which a final ledger reconciliation removes the temporary divergence.

No launch evidence gate, Asaas credential state, legal/privacy state, production deployment state or paid-media state is changed by this receipt.
