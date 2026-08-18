# Stage 8 — Student Feedback → Coach Decision Contract

## Product rule

The FitNexus student may report post-workout perceived exertion, pain/discomfort, energy and an optional note after a completed workout session.

These responses are coaching signals. They may change Risk Radar priority and the suggested Next Best Action, but they never mutate a training prescription automatically.

## Security rule

- Student feedback is accepted only through a high-entropy possession-token RPC.
- The RPC resolves the token privately, verifies the completed session belongs to that student and organization, validates ranges and upserts one feedback per session.
- Anonymous direct table access remains denied.
- Professors read feedback only inside their organization through authenticated RLS / SECURITY INVOKER RPCs.

## Explainable signal rules

High priority:
- pain >= 7/10; or
- perceived exertion >= 9/10 together with energy <= 2/5.

Attention:
- pain 4–6/10; or
- perceived exertion >= 9/10; or
- energy <= 2/5.

Otherwise the existing execution/adherence Risk Radar remains authoritative.

The rule is deliberately deterministic and explainable. AI may later suggest alternatives, but it cannot silently change the prescription.
