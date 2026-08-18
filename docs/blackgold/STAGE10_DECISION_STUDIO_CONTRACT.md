# Stage 10 — Decision Studio Contract

## Goal

Turn Training Lineage into a controlled decision workflow instead of a passive history screen.

## New prescription flow

1. Professor selects a student and drafts the new prescription.
2. `preview_training_plan_change` compares the draft against the active plan without writing anything.
3. The UI shows added, removed and changed exercises.
4. The professor records the reason for the change.
5. Confirmation is accepted only while the form still matches the preview fingerprint.
6. `create_training_plan_v2` commits the new version and immutable lineage record.

If the draft changes after preview, confirmation fails closed and a new preview is required.

## Controlled restore

An old version is never reactivated in place. `restore_training_plan_version` copies it into a brand-new active plan, keeps the previously active plan as predecessor, records decision type `restoration`, preserves source-template lineage when available, and stores a human-confirmed restore context.

This makes rollback auditable rather than destructive.

## Human authority

Risk Radar, feedback and future AI can explain or suggest. Only an authenticated organization manager can confirm a prescription or restoration. The application never silently mutates the active prescription.
