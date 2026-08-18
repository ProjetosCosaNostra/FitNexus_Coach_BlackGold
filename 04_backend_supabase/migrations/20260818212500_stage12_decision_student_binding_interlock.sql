create or replace function public.create_training_plan_from_decision_intelligence_v2(
  p_run_id uuid,
  p_student_id uuid,
  p_name text,
  p_next_session text default null,
  p_notes text default null,
  p_exercises jsonb default '[]'::jsonb,
  p_decision_reason text default null
)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_run_student uuid;
begin
  if auth.uid() is null then
    raise exception using errcode = '42501', message = 'AUTH_REQUIRED';
  end if;

  select r.student_id into v_run_student
  from public.decision_intelligence_runs r
  where r.id = p_run_id;

  if v_run_student is null then
    raise exception using errcode = 'P0002', message = 'DECISION_INTELLIGENCE_RUN_NOT_FOUND';
  end if;
  if p_student_id is null or p_student_id <> v_run_student then
    raise exception using errcode = '42501', message = 'DECISION_INTELLIGENCE_STUDENT_BINDING_MISMATCH';
  end if;

  return public.create_training_plan_from_decision_intelligence(
    p_run_id,
    p_name,
    p_next_session,
    p_notes,
    p_exercises,
    p_decision_reason
  );
end;
$$;

revoke execute on function public.create_training_plan_from_decision_intelligence_v2(uuid,uuid,text,text,text,jsonb,text) from public, anon;
grant execute on function public.create_training_plan_from_decision_intelligence_v2(uuid,uuid,text,text,text,jsonb,text) to authenticated;
