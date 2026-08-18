# FitNexus Coach BlackGold — Stage 12 Decision Learning Loop

## Purpose

Stage 12 closes the human-in-the-loop cycle introduced by Decision Intelligence.

The system no longer records only what it suggested. It records what the professional actually decided:

`Decision Brief → preview/diff → professional decision → accepted | modified | rejected | no_action → calibration evidence`

This is a learning loop about **human use of recommendations**, not autonomous retraining and not clinical validation.

## Outcome authority

`decision_intelligence_outcomes` stores one immutable outcome per Decision Intelligence run:

- `accepted`: the final exercise/prescription sequence matches the stored candidate exactly;
- `modified`: the professor changed the candidate before confirming;
- `rejected`: a candidate was consciously discarded;
- `no_action`: the professor consciously kept the current prescription without a new plan.

A run can be resolved only once.

## Atomic commit contract

`create_training_plan_from_decision_intelligence(...)` prevents a split-brain state where a new training plan could be committed while its Decision Intelligence outcome failed to record.

For an intelligence-assisted prescription, plan creation and outcome insertion now happen in the same PostgreSQL transaction. If either side fails, neither side persists.

The RPC does not trust the Flutter client to declare whether the candidate was accepted or modified. It loads the original candidate stored in the Decision Brief, normalizes both exercise arrays server-side, and classifies the outcome itself.

The Smart Template source is also derived from the stored Decision Brief rather than trusted from the client payload.

## Training Lineage provenance

A human-confirmed intelligence-assisted plan writes the following context into immutable Training Lineage:

- `source=decision_intelligence`;
- `decision_intelligence_run_id`;
- server-classified `decision_intelligence_outcome`;
- `source_template_id`;
- `human_confirmed=true`.

This preserves the chain from evidence to recommendation to final professional action.

## Calibration

`get_decision_intelligence_calibration(...)` aggregates:

- total and unresolved briefs;
- accepted candidates;
- modified candidates;
- rejected candidates;
- no-action decisions;
- adoption rate (`accepted + modified` among resolved runs);
- exact acceptance rate;
- modification rate;
- breakdowns by recommendation type, confidence label and risk level.

The UI labels this explicitly as **Calibração Humana**.

These metrics do not mean the engine was clinically correct. They measure how professionals interacted with its recommendations.

## Guardrail against unsafe self-learning

Stage 12 does **not** rewrite thresholds, templates, exercises, prescriptions or risk rules based on outcome percentages.

Outcome evidence may support future evaluation or controlled experiments, but any change to the decision engine remains a versioned engineering change that must pass review, tests and promotion gates.

## BGF-DECISION-AUDIT-SPLITBRAIN-014

Permanent prevention class introduced in Stage 12:

**Failure mode:** committing a training plan and recording the recommendation outcome through separate calls can leave the system with a real prescription change but no corresponding decision evidence if the second write fails.

**Prevention:** intelligence-assisted commits must use the atomic database command `create_training_plan_from_decision_intelligence` so the prescription and its outcome share one transaction.

**Regression contract:** Flutter must route any commit carrying a Decision Intelligence run id through the atomic RPC; ordinary professor-authored prescriptions continue through the standard lineage-aware command.
