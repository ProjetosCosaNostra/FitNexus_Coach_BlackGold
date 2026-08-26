# FitNexus Coach BlackGold — Stage81 Sensitive Data Treatment Review Questionnaire

**STATUS:** REVIEW PREPARATION ONLY — NOT LEGAL ADVICE, NOT AN APPROVED POLICY, NOT GATE EVIDENCE.

This questionnaire is bound to the current Stage80 technical sensitive-data registry through the Stage80R1 reconciliation addendum. It exists so **real independent legal and privacy reviewers** can determine the treatment rules that engineering is not authorized to invent.

## Mandatory rule

**DO NOT PREPOPULATE OR RECOMMEND A LEGAL CLASSIFICATION, LEGAL BASIS, CONSENT RULE, RETENTION PERIOD, INCIDENT-NOTIFICATION OUTCOME, EXTERNAL-AI AUTHORIZATION OR MARKETING AUTHORIZATION.**

The reviewer must provide the conclusion and supporting reference. A technical flag such as `potentially_sensitive_source_flag=true`, RLS, private schema, zero direct grants, or zero current customer rows is not a legal conclusion.

## Upstream technical surfaces to review

Exactly these nine Stage80 surfaces must be reviewed:

1. `student_profile_objective_and_context`
2. `training_prescription_notes_and_lineage`
3. `workout_feedback_pain_energy_and_notes`
4. `decision_intelligence_context_and_outcomes`
5. `coach_action_notes`
6. `student_access_security_identifiers_and_alerts`
7. `growth_attribution_and_marketing_boundary`
8. `support_and_dsr_free_form_ingress`
9. `incident_response_sensitive_data_handling`

The registry identifies concrete technical risks such as `pain_score`, `pain_location`, free-form notes/context, inheritance of student context into Decision Intelligence, security telemetry boundaries, growth/advertising ingress, support/DSR free-form submissions, and incident-investigation access. It does **not** classify them legally.

## Required participant roles

A real review session must include both:

- `legal_review`
- `privacy_review`

Each participant needs a real traceable review reference and a separate review artifact. A placeholder name, synthetic identity, or `test_fixture=true` is invalid.

## Questions required for every surface

For each of the nine surfaces, reviewers must record all of the following without relying on engineering to supply the legal answer:

1. **Final legal classification** — how the actual data/flow should be classified under the applicable reviewed framework, including conditional cases.
2. **Purpose and necessity** — which processing purposes are permitted, necessary and proportionate, and which are not.
3. **Minimization rule** — what may be collected/stored/transmitted and what must be excluded, structured, shortened, separated, redacted or prohibited.
4. **Free-form content rule** — treatment of notes, objectives, context, support/DSR messages or other fields that can inherit sensitive information.
5. **Access-control rule** — any legal/privacy requirements beyond current technical tenancy/RLS/private-schema controls.
6. **External AI rule** — whether any sensitive context may ever be sent to an external AI provider and under what independently reviewed prerequisites. Stage81 itself grants no authorization.
7. **Marketing/analytics rule** — whether any data from this surface may enter growth, analytics, conversion or advertising flows. Stage81 itself grants no authorization.
8. **Transparency rule** — disclosures/notices or user-facing explanations required for the reviewed treatment.
9. **Incident-handling rule** — treatment/minimization expectations during investigation and what facts trigger later authorized legal/privacy assessment. Do not pre-decide notification.
10. **Retention dependency** — reference the real retention decision/material applicable to this surface; Stage81 must not invent a period.
11. **Review-material reference** — traceable source for the reviewer’s conclusion.

## Cross-surface review questions

The real review must also resolve, or explicitly defer with a cited dependency:

- whether health, injury, pain, limitation, exertion, energy or free-form coaching context receives the same or different treatment by purpose;
- whether general-purpose fields should technically prohibit sensitive narrative when a narrower field is available;
- whether derived summaries/signals remain within the same treatment boundary;
- whether security telemetry must explicitly reject coaching/health narrative;
- whether growth/UTM/ad fields must remain a hard no-sensitive-data boundary;
- whether support and rights-request channels need warning/minimization language;
- how controller/processor conclusions affect each surface;
- how the approved retention matrix constrains each surface;
- how incident review handles potentially sensitive student data without unnecessary copying;
- what changes must be reflected later in the privacy notice, processing-role matrix, DSR runbook and incident runbook after canonical acceptance.

## Review output rule

A completed Stage81 input must stay **outside the repository**. The collector may only bind SHA-256 digests of reviewer references, review artifacts and per-surface decision material. It must not copy reviewer identities, file paths, legal conclusions or raw sensitive data into the repository/CI artifact.

A digest-only candidate means only:

`REAL_EXTERNAL_SENSITIVE_DATA_TREATMENT_REVIEW_MATERIAL_DIGESTS_BOUND_AWAITING_CANONICAL_INDEPENDENT_ACCEPTANCE_NOT_POLICY_EVIDENCE`

It does **not** mean:

- legal classification approved;
- processing/minimization policy approved;
- privacy notice approved;
- role mapping approved;
- incident procedure approved;
- external AI approved;
- sensitive-data marketing approved;
- `SENSITIVE_DATA_TREATMENT` closed;
- any launch gate ready.
