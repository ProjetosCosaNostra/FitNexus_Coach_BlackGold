# Stage 9 — Training Lineage & Explainable Decision Contract

## Product rule

A new prescription never erases the reasoning context of the previous one. Every training plan created after this stage receives an immutable lineage record that identifies its predecessor, origin and decision reason.

## Decision chain

Each plan records:

- student and organization;
- predecessor plan when one exists;
- Smart Template origin when one exists;
- decision type;
- decision reason;
- trigger context;
- author and timestamp.

The plan history is append-only from the product perspective. Old plans remain available as historical evidence and only one plan remains active for the student.

## Diff contract

`preview_training_plan_change` compares a proposed exercise set with the active prescription without mutating the database. It reports added, removed and prescription-changed exercises.

`get_student_training_lineage` returns the committed chain plus the same kind of diff between each plan and its predecessor.

The intended product flow is therefore:

**signal → preview/diff → professor decision → commit → immutable lineage**.

## Human-in-the-loop rule

Risk Radar, student feedback and future AI modules may provide trigger context or suggestions. They do not silently replace the active prescription. A new plan is committed only through an explicit professor-authorized training command.

## Security rule

- lineage is tenant-isolated by RLS;
- anonymous access is denied;
- authenticated members may read only their organization;
- only organization managers can create lineage rows through training commands;
- lineage update/delete is not granted to the application role.
