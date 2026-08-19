# Stage 21 — Remote Promotion Receipt

## Repository-first authority

Stage 21 entered `main` first through PR #24 after the complete Flutter Quality Gate passed.

Repository promotion SHA:

`416144b3a5e90e4f48bc754a0a0969b9b31fc38b`

Only after that merge were the already-versioned migrations applied to the authoritative Supabase project `mceukeondizkwlpfxzgf`.

## Observed remote migration ledger

Supabase assigned the following remote ledger versions:

- `20260819135747` — `stage21_student_access_security_boundary`
- `20260819135808` — `stage21_student_access_issuance_authority_hardening`

The repository filename timestamps intentionally remain independent evidence. Reconciliation authority is the stable migration name, as required by `BGF-REMOTE-REPO-MIGRATION-DIVERGENCE-142`.

## Post-apply structural verification

Read-only verification against the authoritative project confirmed:

- all four new `student_access_links` hardening columns exist;
- `private.student_access_rate_buckets` exists;
- `private.student_access_command_receipts` exists;
- `private.student_access_security_events` exists;
- active student links with `expires_at IS NULL`: **0**;
- `anon` can execute `get_student_workout_v2(text)`: **true**;
- `anon` can execute legacy `get_student_workout(text)`: **false**;
- `authenticated` can execute `issue_student_access_token_v2(uuid)`: **true**;
- `authenticated` can execute legacy `issue_student_access_token(uuid)`: **false**.

This verifies the intended v2 admission path and legacy bypass closure without creating test students, issuing a real bearer, or mutating customer/student workout data.

## Ledger reconciliation

The temporary Stage 21 `repo_only` declarations are removed in the reconciliation change. The two observed remote versions are added to `migration_ledger_authority.json`.

The three historical Stage 17 no-op `remote_only` exceptions remain preserved exactly as historical evidence.

## Authority boundaries unchanged

This receipt proves Stage 21 technical promotion only. It does not promote:

- `billing_provider_credentials`;
- legal/privacy gates;
- DSR operational evidence;
- incident-response evidence;
- `production_deployment`;
- paid advertising.

Controlled launch therefore remains independently fail-closed under Stage 20.
