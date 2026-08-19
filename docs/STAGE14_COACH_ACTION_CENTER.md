# FitNexus Coach BlackGold — Stage 14 Coach Action Center

## Purpose

Stage 14 turns the intelligence stack into a daily operating surface for the coach.

The professor no longer needs to inspect every student manually. The Coach Action Center produces exactly one explainable next-best action per student by crossing:

- workout execution in the last 30 days;
- adherence;
- latest post-workout feedback;
- pain/discomfort and recovery signals;
- active training-plan existence;
- active student link/QR existence;
- unresolved Decision Intelligence runs;
- progression-readiness signals.

The system prioritizes. The professor decides and executes.

## Priority contract

Actions are ordered by a deterministic score. Safety and interruption signals outrank setup, engagement, Decision Intelligence and normal progression.

Examples of high-priority conditions:

1. pain/discomfort >= 7/10;
2. perceived exertion >= 9/10 combined with energy <= 2/5;
3. more than 14 days without execution;
4. adherence below 40% after execution has started;
5. moderate pain/discomfort;
6. missing active prescription;
7. missing active student access;
8. first-execution follow-up;
9. unresolved Decision Brief;
10. normal progression review.

This is not a clinical diagnostic score. It is a workflow-priority score.

## Human authority

Every returned action carries guardrails:

- `auto_execute=false`;
- `auto_contact_student=false`;
- `auto_change_prescription=false`;
- `human_action_required=true`.

The Action Center never changes a training plan and never contacts a student by itself.

## Action fingerprint

Each next-best action receives a SHA-256 fingerprint derived from the student, action type and current evidence context.

The fingerprint changes when important context changes, such as feedback, last execution, adherence, active plan/access or unresolved Decision Brief.

This prevents a professor from accidentally resolving an action that was generated from stale evidence.

## Resolution ledger

`coach_action_events` is an RLS-protected evidence ledger.

The client cannot insert directly into it. A controlled RPC validates that the action is still current before appending one of two outcomes:

- `completed`: hides the exact action fingerprint for 24 hours;
- `snoozed`: hides the exact fingerprint until the requested future time, capped at seven days.

If the student's context changes, a new fingerprint is generated and the new action can surface immediately.

## Daily entry point

The authenticated professor workspace now opens on **Hoje**, the Coach Action Center. The previous operational dashboard remains available from a dedicated button.

This makes the product answer the daily question first:

> “Quem precisa de mim agora, por quê, e qual é a próxima ação?”

## Permanent prevention classes

- `BGF-ACTION-CENTER-FILE-MISSING-031`: mandatory Action Center artifacts cannot disappear silently.
- `BGF-ACTION-EVIDENCE-032`: daily action outcomes require immutable evidence.
- `BGF-ACTION-PRIORITY-CONTRACT-033`: ranking logic must remain versioned and deterministic.
- `BGF-ACTION-STALE-CONTEXT-034`: stale action fingerprints cannot be resolved.
- `BGF-ACTION-RECURRENCE-035`: completed actions use bounded 24-hour suppression instead of disappearing forever.
- `BGF-ACTION-SNOOZE-BOUNDARY-036`: snooze is bounded and cannot become indefinite hiding.
- `BGF-ACTION-NO-AUTO-PRESCRIPTION-037`: Action Center cannot mutate prescriptions automatically.
- `BGF-ACTION-NO-AUTO-CONTACT-038`: Action Center cannot contact students automatically.
- `BGF-ACTION-HUMAN-AUTHORITY-039`: human action remains mandatory.
- `BGF-ACTION-FLUTTER-BINDING-040`: Flutter must stay bound to controlled Action Center RPCs.
- `BGF-ACTION-WORKFLOW-041`: complete/snooze workflow remains regression-gated.
- `BGF-ACTION-DAILY-ENTRYPOINT-042`: the daily workspace must remain visible and first-class.
- `BGF-ACTION-LEDGER-WRITE-AUTHORITY-043`: clients cannot directly fabricate action evidence rows.
- `BGF-ACTION-RPC-AUTHORITY-044`: public Action Center commands stay authenticated-only.

## Construction gate

`verify_coach_action_center_contract.py` is executed by GitHub Actions before Flutter analysis/tests. It fails closed if the daily-action authority, stale-context protection, human guardrails, RPC authority or Flutter bindings drift.
