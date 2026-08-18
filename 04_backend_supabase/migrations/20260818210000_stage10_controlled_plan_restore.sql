alter table public.training_plan_lineage
  drop constraint if exists training_plan_lineage_decision_type_check;

alter table public.training_plan_lineage
  add constraint training_plan_lineage_decision_type_check
  check (decision_type in (
    'initial_prescription',
    'manual_revision',
    'template_assignment',
    'legacy_import',
    'restoration'
  ));

create or replace function public.restore_training_plan_version(
  p_plan_id uuid,
  p_decision_reason text default null
)
returns uuid
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_uid uuid := auth.uid();
  v_target record;
  v_current_active uuid;
  v_source_template uuid;
  v_reason text;
  v_new_plan uuid;
  v_exercise record;
begin
  if v_uid is null then
    raise exception using errcode = '42501', message = 'AUTH_REQUIRED';
  end if;

  select p.* into v_target
  from public.training_plans p
  where p.id = p_plan_id;

  if v_target.id is null then
    raise exception using errcode = 'P0002', message = 'TRAINING_PLAN_NOT_FOUND';
  end if;

  if not private.is_org_manager(v_target.organization_id) then
    raise exception using errcode = '42501', message = 'ORG_MANAGER_REQUIRED';
  end if;

  select p.id into v_current_active
  from public.training_plans p
  where p.student_id = v_target.student_id
    and p.organization_id = v_target.organization_id
    and p.is_active
  order by p.updated_at desc, p.created_at desc
  limit 1;

  if v_current_active = v_target.id then
    raise exception using errcode = '22023', message = 'PLAN_ALREADY_ACTIVE';
  end if;

  if not exists (
    select 1 from public.training_exercises e
    where e.training_plan_id = v_target.id
      and e.organization_id = v_target.organization_id
  ) then
    raise exception using errcode = '22023', message = 'RESTORE_SOURCE_HAS_NO_EXERCISES';
  end if;

  select l.source_template_id into v_source_template
  from public.training_plan_lineage l
  where l.plan_id = v_target.id
    and l.organization_id = v_target.organization_id;

  v_reason := nullif(btrim(coalesce(p_decision_reason, '')), '');
  if v_reason is null then
    v_reason := 'Restauração controlada da versão "' || v_target.name || '"';
  end if;
  if char_length(v_reason) > 500 then
    raise exception using errcode = '22023', message = 'DECISION_REASON_TOO_LONG';
  end if;

  update public.training_plans
     set is_active = false
   where student_id = v_target.student_id
     and organization_id = v_target.organization_id
     and is_active;

  insert into public.training_plans (
    organization_id,
    student_id,
    name,
    next_session,
    notes,
    is_active
  ) values (
    v_target.organization_id,
    v_target.student_id,
    v_target.name,
    v_target.next_session,
    v_target.notes,
    true
  ) returning id into v_new_plan;

  for v_exercise in
    select e.*
    from public.training_exercises e
    where e.training_plan_id = v_target.id
      and e.organization_id = v_target.organization_id
    order by e.position
  loop
    insert into public.training_exercises (
      organization_id,
      training_plan_id,
      position,
      name,
      prescription
    ) values (
      v_target.organization_id,
      v_new_plan,
      v_exercise.position,
      v_exercise.name,
      v_exercise.prescription
    );
  end loop;

  insert into public.training_plan_lineage (
    organization_id,
    student_id,
    plan_id,
    predecessor_plan_id,
    source_template_id,
    decision_type,
    decision_reason,
    trigger_context,
    created_by
  ) values (
    v_target.organization_id,
    v_target.student_id,
    v_new_plan,
    v_current_active,
    v_source_template,
    'restoration',
    v_reason,
    jsonb_build_object(
      'source', 'training_lineage_restore',
      'restored_plan_id', v_target.id,
      'human_confirmed', true
    ),
    v_uid
  );

  update public.students
     set last_workout = v_target.name,
         last_workout_date = current_date,
         next_session = v_target.next_session,
         status = 'Treino restaurado'
   where id = v_target.student_id
     and organization_id = v_target.organization_id;

  return v_new_plan;
end;
$$;

revoke execute on function public.restore_training_plan_version(uuid,text) from public, anon;
grant execute on function public.restore_training_plan_version(uuid,text) to authenticated;
