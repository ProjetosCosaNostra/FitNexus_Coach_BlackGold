# Stage 22 — Final Reconciliation Receipt

## Authoritative repository state before final ledger close

Stage 22 relational interlock merge:

`8cbc37dcbf61f4cc4ace31e3c6b91e05c972a286`

Stage 22 advisor/index hardening merge:

`9bcd1b74f9a1c0b429ad3567566357254762b4d6`

## Authoritative Supabase ledger

Observed after both repo-first remote applications:

- `20260819145811 stage22_tenant_isolation_relational_interlock`
- `20260819150440 stage22_tenant_isolation_fk_index_hardening`

The temporary Stage 22 `repo_only` declaration is therefore removed. The only declared migration divergences remaining are the three historical Stage 17 remote-only no-op rows already covered by `BGF-MIGRATION-TOOL-MISROUTE-097`.

## Final structural truth

Database catalog verification confirms:

- rotation lineage is constrained by `(rotated_from_link_id, student_id, organization_id)`;
- workout-session possession-link binding is constrained by `(student_access_link_id, student_id, organization_id)`;
- both partial-delete semantics null only the optional link identifier;
- self-rotation is rejected;
- both composite foreign keys now have covering indexes matching their column order.

## Final live isolation probe

- `workout_access_link_cross_tenant_mismatches = 0`
- `rotation_lineage_cross_tenant_mismatches = 0`
- anonymous v2 workout entrypoint remains executable as designed;
- anonymous legacy workout entrypoint remains non-executable;
- anonymous direct SELECT on `student_access_links` remains denied;
- anonymous direct SELECT on `workout_sessions` remains denied.

## Advisor closure

After the index migration, the Performance Advisor no longer reports `unindexed_foreign_keys` for either Stage 22 foreign key. Newly created indexes naturally appear as unused immediately after creation; this is not evidence that the required FK coverage should be removed.

Security Advisor warnings on the v2 `SECURITY DEFINER` possession-token surface remain an explicitly reviewed intentional boundary. They are protected by finite token lifetime, token hashing, rate buckets, command replay receipts, tenant-bound resolution, v2-only grants and direct-table denial.

## Failure classes permanently retained

- `BGF-TENANT-RELATIONSHIP-DECOUPLING-154`
- `BGF-TENANT-ANON-RPC-DOWNGRADE-155`
- `BGF-TENANT-DIRECT-TABLE-BYPASS-156`
- `BGF-TENANT-CLIENT-RPC-DOWNGRADE-157`
- `BGF-TENANT-FK-INDEX-COVERAGE-158`

## Launch boundary

Stage 22 changes no external admission evidence. Billing credentials, legal/privacy evidence, DSR operations, incident-response evidence and production deployment remain governed by their existing fail-closed launch gates.
