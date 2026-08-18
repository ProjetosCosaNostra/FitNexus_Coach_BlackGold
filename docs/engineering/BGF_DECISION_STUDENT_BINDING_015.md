# BGF-DECISION-STUDENT-BINDING-015

## Failure class

A Decision Intelligence run is permanently bound to the student whose evidence generated it. If a client lets a professor switch students after opening an intelligence candidate, a preview could be calculated against one student while the commit authority still belongs to the original run/student.

## Permanent prevention

Intelligence-assisted commits use `create_training_plan_from_decision_intelligence_v2`.

The RPC receives both `run_id` and the student selected by the Decision Studio and fails closed with `DECISION_INTELLIGENCE_STUDENT_BINDING_MISMATCH` unless the two authorities match.

The older atomic command remains internally safe because it always commits to the run's own student, but the V2 binding interlock additionally prevents a misleading cross-student preview/commit workflow from the application layer.

## Regression contract

Any Flutter path carrying `decisionIntelligenceRunId` must call the V2 atomic command and pass the selected `studentId`. A mismatch must be rejected by PostgreSQL before any training-plan mutation or outcome record is created.
