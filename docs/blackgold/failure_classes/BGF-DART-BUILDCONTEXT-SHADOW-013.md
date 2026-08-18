# BGF-DART-BUILDCONTEXT-SHADOW-013

## Symptom

Flutter static analysis failed because a local variable named `context` held `StudentFeedbackContext?` and shadowed the widget `BuildContext`. A later call to `ScaffoldMessenger.of(context)` therefore received the wrong type.

## Root cause

UI-layer local state reused the framework-reserved semantic name `context` for a domain object.

## Permanent prevention

- Flutter `analyze` remains a mandatory promotion gate.
- UI code must reserve `context` for `BuildContext` parameters/variables.
- Domain objects use semantic names such as `feedbackContext`, `authContext`, or `decisionContext`.
- A failed static-analysis run cannot be promoted; the exact analyzer evidence must be fixed and the complete quality gate rerun.

## Recovery proof

The Stage 8 branch was repaired by renaming the domain variable to `feedbackContext`. The subsequent Supabase identity guard, Flutter static analysis and widget/unit test gate all passed before PR #8 was promoted.
