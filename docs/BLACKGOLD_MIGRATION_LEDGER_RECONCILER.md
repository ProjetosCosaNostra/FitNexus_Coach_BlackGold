# BlackGold Migration Ledger Reconciler

Failure class: `BGF-REMOTE-REPO-MIGRATION-DIVERGENCE-142`

## Problem

Stage 20 exposed a source-of-truth split: `stage20_controlled_launch_admission` was already applied to the authoritative Supabase project while its repository commits were still outside `main`.

That state is now treated as a permanent failure class. A successful remote DDL call is not sufficient evidence that the repository is synchronized.

## Authority

- Supabase project: `mceukeondizkwlpfxzgf`
- Repository: `ProjetosCosaNostra/FitNexus_Coach_BlackGold`
- Versioned baseline: `04_backend_supabase/migration_ledger_authority.json`
- Repository migration source: `04_backend_supabase/migrations/*.sql`
- Project identity source: `04_backend_supabase/project_identity.json`

## Critical comparison rule

Reconcile by **migration name**, not by timestamp alone.

The repository filename timestamp and the remote migration ledger version may differ when a migration is applied through tooling that records a fresh remote ledger version. Example already observed:

- repository: `20260819062000_stage20_controlled_launch_admission.sql`
- remote ledger: `20260819085840 / stage20_controlled_launch_admission`

This is not drift because the stable migration name matches. The remote version is preserved separately as application evidence.

## Fail-closed conditions

The reconciler fails when any of these are undeclared:

1. remote migration name missing from the repository (`remote_only`);
2. repository migration name missing from remote (`repo_only`);
3. duplicate migration names;
4. a known remote migration name changes remote ledger version unexpectedly;
5. baseline project identity differs from the authoritative project manifest;
6. a declared divergence remains after the divergence no longer exists.

Any temporary or historical divergence must be explicit in `declared_divergences` with direction, migration name, reason and owner.

The current baseline intentionally declares three historical `remote_only` no-op ledger rows from the Stage 17 migration-tool misroute incident (`BGF-MIGRATION-TOOL-MISROUTE-097`). They remain visible as evidence and are not fabricated into repository SQL files.

## Permanent workflow

Before **every** future remote DDL mutation:

1. Read `project_identity.json` and verify project ref/name/region.
2. Read live Supabase `list_migrations`.
3. Export the result to JSON and run `reconcile_migration_ledger.py`.
4. If the result is not `PASS`, do not apply new DDL.
5. Create the new migration in a branch.
6. Prefer repository-first promotion: declare a temporary `repo_only` divergence, pass CI and merge the migration to `main`.
7. Apply the already-versioned migration remotely.
8. Read live `list_migrations` again.
9. Update `migration_ledger_authority.json` with the observed remote version and remove the temporary declaration.
10. Run the reconciler again; only exact/declared authority may continue.

This two-phase pattern prefers `repo ahead of remote` over `remote ahead of main`, because remote schema must never silently outrun repository authority.

## Commands

Contract-only CI check:

```text
python 04_backend_supabase/tools/verify_migration_ledger_contract.py
python 04_backend_supabase/tools/test_migration_ledger_reconciler.py
```

Live reconciliation after exporting `Supabase.list_migrations` to `remote_migrations.json`:

```text
python 04_backend_supabase/tools/reconcile_migration_ledger.py --remote-json remote_migrations.json
```

## BlackGold invariant

A future operator may still use Supabase tooling, but no new DDL is admitted unless repository authority and the live remote ledger have first been reconciled. Repeated drift is no longer a manual reminder; it is a named failure class with a parser, regression tests and a fail-closed gate.
