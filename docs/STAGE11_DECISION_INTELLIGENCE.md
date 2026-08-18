# FitNexus Coach BlackGold — Stage 11 Decision Intelligence

## Purpose

Stage 11 introduces an explainable decision layer above Risk Radar, post-workout feedback, execution history, Smart Templates and Training Lineage.

The layer does **not** prescribe autonomously. Its contract is:

`signals → deterministic brief → confidence → optional professional candidate → diff → Decision Studio → human confirmation → Training Lineage`

## Deterministic fallback first

The first engine is `blackgold_deterministic_v1` and requires no external model. This keeps the SaaS functional when no AI provider is configured or available and avoids external inference cost during the initial product stage.

The output contract is intentionally provider-neutral so a future AI advisor can be added behind the same interface without gaining permission to mutate prescriptions.

## Signals used

The engine may consider:

- current adherence;
- sessions started and completed in the last 30 days;
- last execution time;
- latest perceived exertion, pain/discomfort and energy feedback;
- active training plan;
- available active Smart Templates matching the student's objective and level;
- current Training Lineage origin.

## Guardrails

The engine always returns `auto_apply=false` and `human_review_required=true`.

High pain/discomfort, very high exertion with low energy, recovery concerns, or adherence problems deliberately block an automatic training candidate. In those cases the recommendation is a human review, not a guessed prescription change.

A Smart Template candidate is only surfaced when the rule engine considers comparison appropriate and a professional template matches the student's objective and level. The candidate remains only a comparison source.

## Proposed diff

When a Smart Template candidate is available, Stage 11 calls the non-mutating `preview_training_plan_change` contract and returns:

- exercises added;
- exercises removed;
- prescriptions changed.

No training row is changed by generating a Decision Brief.

## Decision Studio handoff

A candidate can be opened in Decision Studio. The proposal is prefilled, but the professor must still:

1. review/edit the proposal;
2. generate a new preview;
3. inspect the diff;
4. keep a decision reason;
5. explicitly confirm.

If the draft changes after preview, the existing fingerprint interlock invalidates confirmation and requires another preview.

When a Decision Intelligence candidate is committed, its `run_id` is written into the Training Lineage trigger context so the final human decision can be traced back to the analysis that helped inform it.

## Evidence persistence

Every generated brief is stored in `decision_intelligence_runs` with tenant isolation, engine version, author and timestamp. The table is RLS-protected; anonymous direct access is denied.

## Safety boundary

Decision Intelligence is a coaching decision-support feature. It does not diagnose medical conditions and does not silently change a student's training prescription.
