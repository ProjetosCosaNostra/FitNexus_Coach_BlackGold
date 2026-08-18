create table if not exists public.training_plan_lineage (
  id uuid primary key default extensions.gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  student_id uuid not null,
  plan_id uuid not null unique,
  predecessor_plan_id uuid,
  source_template_id uuid,
  decision_type text not null check (decision_type in ('initial_prescription','manual_revision','template_assignment','legacy_import')),
  decision_reason text not null check (char_length(btrim(decision_reason)) between 2 and 500),
  trigger_context jsonb not null default '{}'::jsonb check (jsonb_typeof(trigger_context) = 'object'),
  created_by uuid,
  created_at timestamptz not null default now(),
  constraint training_plan_lineage_plan_same_student_org_fk
    foreign key (plan_id, student_id, organization_id)
    references public.training_plans(id, student_id, organization_id)
    on delete cascade,
  constraint training_plan_lineage_predecessor_same_student_org_fk
    foreign key (predecessor_plan_id, student_id, organization_id)
    references public.training_plans(id, student_id, organization_id)
    on delete restrict,
  constraint training_plan_lineage_source_template_same_org_fk
    foreign key (source_template_id, organization_id)
    references public.training_templates(id, organization_id)
    on delete restrict
);

create index if not exists training_plan_lineage_org_student_created_idx
  on public.training_plan_lineage(organization_id, student_id, created_at desc);
create index if not exists training_plan_lineage_predecessor_idx
  on public.training_plan_lineage(predecessor_plan_id) where predecessor_plan_id is not null;
create index if not exists training_plan_lineage_source_template_idx
  on public.training_plan_lineage(source_template_id) where source_template_id is not null;

alter table public.training_plan_lineage enable row level security;
revoke all on public.training_plan_lineage from anon, authenticated;
grant select, insert on public.training_plan_lineage to authenticated;

drop policy if exists training_plan_lineage_select_org on public.training_plan_lineage;
create policy training_plan_lineage_select_org
on public.training_plan_lineage
for select to authenticated
using ((select private.is_org_member(organization_id)));

drop policy if exists training_plan_lineage_insert_manager on public.training_plan_lineage;
create policy training_plan_lineage_insert_manager
on public.training_plan_lineage
for insert to authenticated
with check ((select private.is_org_manager(organization_id)));

with ordered as (
  select p.id, p.organization_id, p.student_id, p.created_at,
    lag(p.id) over (
      partition by p.organization_id, p.student_id
      order by p.created_at, p.id
    ) as predecessor_plan_id
  from public.training_plans p
)
insert into public.training_plan_lineage (
  organization_id, student_id, plan_id, predecessor_plan_id,
  source_template_id, decision_type, decision_reason, trigger_context,
  created_by, created_at
)
select o.organization_id, o.student_id, o.id, o.predecessor_plan_id, null,
  case when o.predecessor_plan_id is null then 'initial_prescription' else 'legacy_import' end,
  case when o.predecessor_plan_id is null
    then 'Prescrição inicial registrada antes do Training Lineage'
    else 'Histórico importado automaticamente para o Training Lineage'
  end,
  jsonb_build_object('backfilled', true), null, o.created_at
from ordered o
on conflict (plan_id) do nothing;

create or replace function public.create_training_plan_v2(
  p_student_id uuid,
  p_name text,
  p_next_session text default null,
  p_notes text default null,
  p_exercises jsonb default '[]'::jsonb,
  p_decision_reason text default null,
  p_source_template_id uuid default null,
  p_trigger_context jsonb default '{}'::jsonb
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
  v_previous_plan uuid;
  v_name text := btrim(coalesce(p_name, ''));
  v_reason text;
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
  if p_trigger_context is null or jsonb_typeof(p_trigger_context) <> 'object' then
    raise exception using errcode = '22023', message = 'TRIGGER_CONTEXT_INVALID';
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

  if p_source_template_id is not null and not exists (
    select 1 from public.training_templates t
    where t.id = p_source_template_id
      and t.organization_id = v_org
      and t.is_active
  ) then
    raise exception using errcode = '42501', message = 'SOURCE_TEMPLATE_NOT_FOUND_OR_FORBIDDEN';
  end if;

  select p.id into v_previous_plan
  from public.training_plans p
  where p.student_id = p_student_id
    and p.organization_id = v_org
    and p.is_active
  order by p.updated_at desc, p.created_at desc
  limit 1;

  v_reason := nullif(btrim(coalesce(p_decision_reason, '')), '');
  if v_reason is null then
    v_reason := case
      when p_source_template_id is not null then 'Nova prescrição criada a partir de um Smart Template'
      when v_previous_plan is null then 'Prescrição inicial criada pelo professor'
      else 'Nova revisão de treino criada pelo professor'
    end;
  end if;
  if char_length(v_reason) > 500 then
    raise exception using errcode = '22023', message = 'DECISION_REASON_TOO_LONG';
  end if;

  update public.training_plans
     set is_active = false
   where student_id = p_student_id
     and organization_id = v_org
     and is_active;

  insert into public.training_plans (
    organization_id, student_id, name, next_session, notes
  ) values (
    v_org, p_student_id, v_name,
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
      v_org, v_plan, v_position,
      btrim(v_item ->> 'name'),
      btrim(coalesce(v_item ->> 'prescription', ''))
    );
    v_position := v_position + 1;
  end loop;

  insert into public.training_plan_lineage (
    organization_id, student_id, plan_id, predecessor_plan_id,
    source_template_id, decision_type, decision_reason, trigger_context,
    created_by
  ) values (
    v_org, p_student_id, v_plan, v_previous_plan, p_source_template_id,
    case
      when p_source_template_id is not null then 'template_assignment'
      when v_previous_plan is null then 'initial_prescription'
      else 'manual_revision'
    end,
    v_reason, p_trigger_context, v_uid
  );

  update public.students
     set last_workout = v_name,
         last_workout_date = current_date,
         next_session = nullif(btrim(coalesce(p_next_session, '')), ''),
         status = 'Treino criado'
   where id = p_student_id
     and organization_id = v_org;

  return v_plan;
end;
$$;

revoke execute on function public.create_training_plan_v2(uuid,text,text,text,jsonb,text,uuid,jsonb) from public, anon;
grant execute on function public.create_training_plan_v2(uuid,text,text,text,jsonb,text,uuid,jsonb) to authenticated;

create or replace function public.create_training_plan(
  p_student_id uuid,
  p_name text,
  p_next_session text default null,
  p_notes text default null,
  p_exercises jsonb default '[]'::jsonb
)
returns uuid
language sql
security invoker
set search_path = ''
as $$
  select public.create_training_plan_v2(
    p_student_id, p_name, p_next_session, p_notes, p_exercises,
    null, null, '{}'::jsonb
  );
$$;

revoke execute on function public.create_training_plan(uuid,text,text,text,jsonb) from public, anon;
grant execute on function public.create_training_plan(uuid,text,text,text,jsonb) to authenticated;

create or replace function public.assign_training_template(
  p_template_id uuid,
  p_student_id uuid,
  p_next_session text default null
)
returns uuid
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_template record;
  v_student_org uuid;
  v_exercises jsonb := '[]'::jsonb;
  v_plan uuid;
begin
  if auth.uid() is null then
    raise exception using errcode = '42501', message = 'AUTH_REQUIRED';
  end if;

  select t.* into v_template
  from public.training_templates t
  where t.id = p_template_id and t.is_active;
  if v_template.id is null then
    raise exception using errcode = 'P0002', message = 'TEMPLATE_NOT_FOUND';
  end if;

  select s.organization_id into v_student_org
  from public.students s
  where s.id = p_student_id;
  if v_student_org is null then
    raise exception using errcode = 'P0002', message = 'STUDENT_NOT_FOUND';
  end if;
  if v_student_org <> v_template.organization_id then
    raise exception using errcode = '42501', message = 'TEMPLATE_STUDENT_TENANT_MISMATCH';
  end if;
  if not private.is_org_manager(v_template.organization_id) then
    raise exception using errcode = '42501', message = 'ORG_MANAGER_REQUIRED';
  end if;

  select coalesce(
    jsonb_agg(jsonb_build_object('name', e.name, 'prescription', e.prescription) order by e.position),
    '[]'::jsonb
  ) into v_exercises
  from public.training_template_exercises e
  where e.template_id = v_template.id
    and e.organization_id = v_template.organization_id;
  if jsonb_array_length(v_exercises) = 0 then
    raise exception using errcode = '22023', message = 'TEMPLATE_HAS_NO_EXERCISES';
  end if;

  select public.create_training_plan_v2(
    p_student_id, v_template.name, p_next_session, v_template.notes, v_exercises,
    'Prescrição criada a partir do Smart Template "' || v_template.name || '"',
    v_template.id,
    jsonb_build_object('source', 'smart_template')
  ) into v_plan;

  return v_plan;
end;
$$;

revoke execute on function public.assign_training_template(uuid,uuid,text) from public, anon;
grant execute on function public.assign_training_template(uuid,uuid,text) to authenticated;

create or replace function public.preview_training_plan_change(
  p_student_id uuid,
  p_exercises jsonb
)
returns jsonb
language plpgsql
stable
security invoker
set search_path = ''
as $$
declare
  v_org uuid;
  v_active_plan uuid;
  v_active_name text;
  v_added jsonb := '[]'::jsonb;
  v_removed jsonb := '[]'::jsonb;
  v_changed jsonb := '[]'::jsonb;
begin
  if auth.uid() is null then
    raise exception using errcode = '42501', message = 'AUTH_REQUIRED';
  end if;
  if p_exercises is null or jsonb_typeof(p_exercises) <> 'array' then
    raise exception using errcode = '22023', message = 'TRAINING_EXERCISES_INVALID';
  end if;

  select s.organization_id into v_org
  from public.students s
  where s.id = p_student_id;
  if v_org is null or not private.is_org_manager(v_org) then
    raise exception using errcode = '42501', message = 'ORG_MANAGER_REQUIRED';
  end if;

  select p.id, p.name into v_active_plan, v_active_name
  from public.training_plans p
  where p.student_id = p_student_id
    and p.organization_id = v_org
    and p.is_active
  order by p.updated_at desc
  limit 1;

  with proposed as (
    select lower(btrim(value ->> 'name')) as key,
           btrim(value ->> 'name') as name,
           btrim(coalesce(value ->> 'prescription', '')) as prescription
    from jsonb_array_elements(p_exercises)
  ), current_exercises as (
    select lower(btrim(e.name)) as key, e.name, e.prescription
    from public.training_exercises e
    where e.training_plan_id = v_active_plan
      and e.organization_id = v_org
  )
  select
    coalesce((
      select jsonb_agg(jsonb_build_object('name', p.name, 'prescription', p.prescription) order by p.name)
      from proposed p left join current_exercises c on c.key = p.key
      where c.key is null
    ), '[]'::jsonb),
    coalesce((
      select jsonb_agg(jsonb_build_object('name', c.name, 'prescription', c.prescription) order by c.name)
      from current_exercises c left join proposed p on p.key = c.key
      where p.key is null
    ), '[]'::jsonb),
    coalesce((
      select jsonb_agg(jsonb_build_object('name', p.name, 'before', c.prescription, 'after', p.prescription) order by p.name)
      from proposed p join current_exercises c on c.key = p.key
      where coalesce(c.prescription, '') <> coalesce(p.prescription, '')
    ), '[]'::jsonb)
  into v_added, v_removed, v_changed;

  return jsonb_build_object(
    'active_plan_id', v_active_plan,
    'active_plan_name', v_active_name,
    'has_previous_plan', v_active_plan is not null,
    'added', v_added,
    'removed', v_removed,
    'changed', v_changed,
    'added_count', jsonb_array_length(v_added),
    'removed_count', jsonb_array_length(v_removed),
    'changed_count', jsonb_array_length(v_changed)
  );
end;
$$;

revoke execute on function public.preview_training_plan_change(uuid,jsonb) from public, anon;
grant execute on function public.preview_training_plan_change(uuid,jsonb) to authenticated;

create or replace function public.get_student_training_lineage(p_student_id uuid)
returns jsonb
language plpgsql
stable
security invoker
set search_path = ''
as $$
declare
  v_org uuid;
  v_items jsonb := '[]'::jsonb;
begin
  if auth.uid() is null then
    raise exception using errcode = '42501', message = 'AUTH_REQUIRED';
  end if;
  select s.organization_id into v_org from public.students s where s.id = p_student_id;
  if v_org is null or not private.is_org_member(v_org) then
    raise exception using errcode = '42501', message = 'ORG_MEMBER_REQUIRED';
  end if;

  select coalesce(jsonb_agg(x.item order by x.created_at desc), '[]'::jsonb)
  into v_items
  from (
    select l.created_at,
      jsonb_build_object(
        'lineage_id', l.id,
        'plan_id', p.id,
        'plan_name', p.name,
        'is_active', p.is_active,
        'created_at', p.created_at,
        'predecessor_plan_id', l.predecessor_plan_id,
        'predecessor_plan_name', pp.name,
        'source_template_id', l.source_template_id,
        'source_template_name', t.name,
        'decision_type', l.decision_type,
        'decision_reason', l.decision_reason,
        'trigger_context', l.trigger_context,
        'exercise_count', (
          select count(*)::int from public.training_exercises e
          where e.training_plan_id = p.id and e.organization_id = p.organization_id
        ),
        'diff', case when l.predecessor_plan_id is null then jsonb_build_object(
          'added', '[]'::jsonb, 'removed', '[]'::jsonb, 'changed', '[]'::jsonb,
          'added_count', 0, 'removed_count', 0, 'changed_count', 0
        ) else (
          with current_exercises as (
            select lower(btrim(e.name)) as key, e.name, e.prescription
            from public.training_exercises e
            where e.training_plan_id = p.id and e.organization_id = p.organization_id
          ), previous_exercises as (
            select lower(btrim(e.name)) as key, e.name, e.prescription
            from public.training_exercises e
            where e.training_plan_id = l.predecessor_plan_id and e.organization_id = p.organization_id
          ), added as (
            select coalesce(jsonb_agg(jsonb_build_object('name', c.name, 'prescription', c.prescription) order by c.name), '[]'::jsonb) as value
            from current_exercises c left join previous_exercises q on q.key = c.key where q.key is null
          ), removed as (
            select coalesce(jsonb_agg(jsonb_build_object('name', q.name, 'prescription', q.prescription) order by q.name), '[]'::jsonb) as value
            from previous_exercises q left join current_exercises c on c.key = q.key where c.key is null
          ), changed as (
            select coalesce(jsonb_agg(jsonb_build_object('name', c.name, 'before', q.prescription, 'after', c.prescription) order by c.name), '[]'::jsonb) as value
            from current_exercises c join previous_exercises q on q.key = c.key
            where coalesce(c.prescription, '') <> coalesce(q.prescription, '')
          )
          select jsonb_build_object(
            'added', a.value, 'removed', r.value, 'changed', c.value,
            'added_count', jsonb_array_length(a.value),
            'removed_count', jsonb_array_length(r.value),
            'changed_count', jsonb_array_length(c.value)
          ) from added a cross join removed r cross join changed c
        ) end
      ) as item
    from public.training_plan_lineage l
    join public.training_plans p
      on p.id = l.plan_id and p.student_id = l.student_id and p.organization_id = l.organization_id
    left join public.training_plans pp
      on pp.id = l.predecessor_plan_id and pp.organization_id = l.organization_id
    left join public.training_templates t
      on t.id = l.source_template_id and t.organization_id = l.organization_id
    where l.student_id = p_student_id and l.organization_id = v_org
  ) x;

  return jsonb_build_object('student_id', p_student_id, 'items', v_items, 'generated_at', now());
end;
$$;

revoke execute on function public.get_student_training_lineage(uuid) from public, anon;
grant execute on function public.get_student_training_lineage(uuid) to authenticated;
