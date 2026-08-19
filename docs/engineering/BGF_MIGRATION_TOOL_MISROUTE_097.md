# BGF-MIGRATION-TOOL-MISROUTE-097

## Failure class

`BGF-MIGRATION-TOOL-MISROUTE-097` — read-only health/advisor work must never be routed through the schema migration mutation endpoint.

## Incident

During Stage 17 advisor reconciliation, three `select 1;` no-op calls were accidentally sent through `apply_migration` while the intended operation was read-only inspection.

Remote migration-ledger entries created:

- `stage17_pricing_guard_indexes_marker`
- `stage17_pricing_advisor_reconciliation`
- `stage17_pricing_advisor_guard`

Each entry executed only `select 1;`.

Classification:

- schema mutation: **NO**;
- data mutation: **NO**;
- authority mutation: **NO**;
- migration-ledger noise: **YES**.

The entries are retained as historical evidence rather than hidden or rewritten.

## Root cause

Tool routing did not distinguish strongly enough between:

- DDL/schema mutation, which belongs to `apply_migration`; and
- advisor/health/read operations, which belong to `get_advisors`, `execute_sql` read queries, or purpose-specific read tools.

A syntactically harmless no-op still becomes permanent ledger noise when executed through a migration endpoint.

## Permanent prevention

Construction controllers must classify every Supabase operation before invocation:

| Intent | Allowed path |
| --- | --- |
| DDL/schema change | `apply_migration` |
| Data/schema read | `execute_sql` read-only query |
| Security/performance lints | `get_advisors` |
| Migration inventory | `list_migrations` |

Additional invariant:

- reject `apply_migration` payloads whose normalized SQL is only `select`, `show`, `explain`, or another read/no-op statement;
- migration names containing `advisor`, `health`, `inspect`, `check`, `marker`, or `reconciliation` require a DDL mutation proof before execution;
- no-op ledger entries must be reported explicitly, never disguised as meaningful migrations.

## Regression expectation

A future BlackGold migration dispatcher should fail closed with:

`MIGRATION_MUTATION_PROOF_REQUIRED`

when a migration request has no schema/data mutation intent.

## Stage 17 status

The three accidental entries have no schema or data effect. All real Stage 17 DDL remains represented by the authoritative repository migrations, including pricing authority, FK hardening and the private checkout authority bridge.
