create or replace function public.create_training_plan(
  p_student_id uuid,
  p_name text,
  p_next_session text default null,
  p_notes text default null,
  p_exercises jsonb default '[]'::jsonb
)
returns uuid
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_uid uuid := auth.uid();
  v_org uuid;
  v_plan uuid;
  v_name text := btrim(coalesce(p_name, ''));
  v_item jsonb;
  v_position integer := 0;
begin
  if v_uid is null then
    raise exception using errcode = '42501', message = 'AUTH_REQUIRED';
  end if;

  if char_length(v_name) < 2 or char_length(v_name) > 120 then
    raise exception using errcode = '22023', message = 'TRAINING_NAME_INVALID';
  end if;

  if jsonb_typeof(p_exercises) <> 'array' or jsonb_array_length(p_exercises) = 0 then
    raise exception using errcode = '22023', message = 'TRAINING_EXERCISES_REQUIRED';
  end if;

  select s.organization_id into v_org
  from public.students s
  where s.id = p_student_id;

  if v_org is null then
    raise exception using errcode = 'P0002', message = 'STUDENT_NOT_FOUND_OR_FORBIDDEN';
  end if;

  if not private.is_org_manager(v_org) then
    raise exception using errcode = '42501', message = 'ORG_MANAGER_REQUIRED';
  end if;

  insert into public.training_plans (
    organization_id, student_id, name, next_session, notes
  ) values (
    v_org,
    p_student_id,
    v_name,
    nullif(btrim(coalesce(p_next_session, '')), ''),
    nullif(btrim(coalesce(p_notes, '')), '')
  ) returning id into v_plan;

  for v_item in select value from jsonb_array_elements(p_exercises)
  loop
    if char_length(btrim(coalesce(v_item ->> 'name', ''))) < 2 then
      raise exception using errcode = '22023', message = 'EXERCISE_NAME_INVALID';
    end if;

    insert into public.training_exercises (
      organization_id, training_plan_id, position, name, prescription
    ) values (
      v_org,
      v_plan,
      v_position,
      btrim(v_item ->> 'name'),
      btrim(coalesce(v_item ->> 'prescription', ''))
    );

    v_position := v_position + 1;
  end loop;

  update public.students
     set last_workout = v_name,
         last_workout_date = current_date,
         next_session = nullif(btrim(coalesce(p_next_session, '')), ''),
         status = 'Treino criado'
   where id = p_student_id;

  return v_plan;
end;
$$;

revoke execute on function public.create_training_plan(uuid,text,text,text,jsonb) from public, anon;
grant execute on function public.create_training_plan(uuid,text,text,text,jsonb) to authenticated;
