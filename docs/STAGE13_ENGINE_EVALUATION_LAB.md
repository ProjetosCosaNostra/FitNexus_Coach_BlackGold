# FitNexus Coach BlackGold — Stage 13 Engine Evaluation Lab

## Purpose

Stage 13 introduces a controlled Champion–Challenger laboratory for Decision Intelligence.

The production engine stays frozen as the **Champion** while new deterministic versions can replay historical Decision Brief evidence in **shadow mode**.

Core contract:

`stored Decision Brief evidence → Champion replay → Challenger replay → divergence + human outcome alignment + safety gate → promotion packet → engineering review only`

No evaluation run can activate an engine.

## Version authority

`decision_engine_registry` is the version authority.

Initial entries:

- `blackgold_deterministic_v1` — `champion / active`;
- `blackgold_deterministic_v1_1_shadow` — `challenger / lab_only`.

The Stage 13 migration deliberately does not contain an update path that changes `engine_role` or `lifecycle`. Promotion must be a separate reviewed engineering change.

## Historical replay

`private.evaluate_decision_engine_snapshot(brief, engine_version)` evaluates only the immutable evidence captured inside an existing Decision Brief.

This prevents the challenger from accidentally using today's mutable student state when judging a historical decision.

The shadow challenger is deliberately more conservative before progression:

- same high-risk pain and recovery guardrails as the Champion;
- same adherence/absence safety hierarchy;
- progression is withheld when feedback is missing or older than 14 days;
- confidence is recalculated from historical evidence freshness;
- no candidate is applied and no live recommendation is changed.

The lab does not replay mutable Smart Template availability. It evaluates decision policy and actionability, not current catalog state.

## Evaluation evidence

Every evaluation produces:

- `decision_engine_evaluation_runs` — immutable run-level summary;
- `decision_engine_evaluation_cases` — per historical Decision Brief comparison;
- `decision_engine_promotion_packets` — promotion-gate evidence packet.

For each historical case the lab records:

- Champion output;
- Challenger output;
- recommendation divergence;
- risk divergence;
- risk downgrade flag;
- unsafe actionability conflict flag;
- human outcome when available;
- coarse decision-alignment result for Champion and Challenger.

## Decision alignment

Human outcomes from Stage 12 are interpreted only as behavioral evidence:

- `accepted` or `modified` → an actionable recommendation aligns with the professional action;
- `rejected` or `no_action` → a non-actionable recommendation aligns with the professional action.

This is **not** a measure of clinical efficacy, medical correctness, or training outcome quality.

## Promotion gate

A challenger can reach only `eligible_for_engineering_review` when all of the following are true:

- at least 20 historical cases;
- at least 12 resolved human outcomes;
- zero risk downgrades;
- zero unsafe actionability conflicts;
- Challenger decision-alignment rate is not below Champion alignment.

Possible states:

- `blocked_insufficient_evidence`;
- `blocked_safety_regression`;
- `blocked_no_alignment_uplift`;
- `eligible_for_engineering_review`.

Even `eligible_for_engineering_review` does not authorize activation.

The promotion packet always contains:

- `activation_authorized=false`;
- `auto_activation=false`;
- a next action requiring a separate reviewed change.

## New permanent failure classes

### BGF-ENGINE-VERSION-AUTHORITY-023

Engine identity cannot live only inside scattered SQL conditionals. A version registry is mandatory so Champion, Challenger and retired engines have explicit lifecycle authority.

### BGF-ENGINE-SHADOW-ISOLATION-024

A challenger under evaluation cannot influence production recommendations, prescriptions, Training Lineage or live Decision Brief generation. Replay must consume historical snapshots only.

### BGF-ENGINE-EVALUATION-EVIDENCE-025

An aggregate percentage without case-level evidence is insufficient for engine governance. Every evaluation stores the per-case Champion/Challenger comparison that produced the summary.

### BGF-ENGINE-PROMOTION-GATE-026

A challenger cannot become review-eligible without minimum sample volume, minimum resolved human outcomes and explicit safety checks.

### BGF-ENGINE-SAFETY-REGRESSION-027

A challenger that downgrades historical risk or becomes actionable where the Champion had medium/high risk is blocked regardless of alignment uplift.

### BGF-ENGINE-NO-SELF-PROMOTION-028

Evaluation and promotion are separate authorities. The laboratory can generate an evidence packet but cannot change engine role/lifecycle or activate a production version.

### BGF-ENGINE-EVALUATION-COMMAND-029

Evaluation execution and lab status are authenticated RPC contracts. Anonymous execution is denied; organization managers run evaluations and organization members may read status.

### BGF-ENGINE-LAB-FLUTTER-BINDING-030

The Flutter repository binds explicitly to the lab RPCs and to the named shadow version. Contract CI fails if the app loses those bindings.

## Construction intelligence

The existing Decision Intelligence CI contract guard now also fails if:

- the engine registry disappears;
- shadow-only challenger identity drifts;
- historical replay disappears;
- per-case evaluation evidence disappears;
- safety downgrade/conflict metrics disappear;
- minimum sample gates are weakened silently;
- auto-activation protection disappears;
- a migration tries to mutate engine role/lifecycle inside the evaluation pipeline;
- Flutter loses its Engine Lab RPC bindings.

This turns Stage 13 itself into a permanent prevention mechanism for future engine evolution.
