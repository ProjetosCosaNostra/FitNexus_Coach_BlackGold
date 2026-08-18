-- Stage 6 performance hardening: cover tenant-bound foreign keys used by
-- progress analytics and workout execution. These indexes are intentionally
-- additive; existing single-column indexes remain until production usage data
-- can prove they are redundant.

create index if not exists student_access_links_student_org_fk_idx
  on public.student_access_links(student_id, organization_id);

create index if not exists training_exercises_org_fk_idx
  on public.training_exercises(organization_id);

create index if not exists training_exercises_plan_org_fk_idx
  on public.training_exercises(training_plan_id, organization_id);

create index if not exists training_plans_student_org_fk_idx
  on public.training_plans(student_id, organization_id);

create index if not exists workout_exercise_logs_exercise_plan_org_fk_idx
  on public.workout_exercise_logs(exercise_id, training_plan_id, organization_id);

create index if not exists workout_exercise_logs_org_fk_idx
  on public.workout_exercise_logs(organization_id);

create index if not exists workout_exercise_logs_session_plan_org_fk_idx
  on public.workout_exercise_logs(session_id, training_plan_id, organization_id);

create index if not exists workout_sessions_org_fk_idx
  on public.workout_sessions(organization_id);

create index if not exists workout_sessions_plan_student_org_fk_idx
  on public.workout_sessions(training_plan_id, student_id, organization_id);

create index if not exists workout_sessions_access_link_fk_idx
  on public.workout_sessions(student_access_link_id);
