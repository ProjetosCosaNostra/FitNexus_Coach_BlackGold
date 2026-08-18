create table if not exists public.training_templates (
  id uuid primary key default extensions.gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  name text not null check (char_length(btrim(name)) between 2 and 120),
  objective text not null default 'Geral',
  level text not null default 'Iniciante',
  notes text,
  created_by uuid,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (id, organization_id)
);

create table if not exists public.training_template_exercises (
  id uuid primary key default extensions.gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  template_id uuid not null,
  position integer not null check (position >= 0),
  name text not null check (char_length(btrim(name)) between 2 and 160),
  prescription text not null default '',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint training_template_exercises_template_same_org_fk
    foreign key (template_id, organization_id)
    references public.training_templates(id, organization_id)
    on delete cascade,
  unique (template_id, position)
);

create index if not exists training_templates_org_updated_idx
  on public.training_templates(organization_id, updated_at desc);

create index if not exists training_template_exercises_org_fk_idx
  on public.training_template_exercises(organization_id);

create index if not exists training_template_exercises_template_org_fk_idx
  on public.training_template_exercises(template_id, organization_id);

alter table public.training_templates enable row level security;
alter table public.training_template_exercises enable row level security;

revoke all on public.training_templates from anon;
revoke all on public.training_template_exercises from anon;
revoke all on public.training_templates from authenticated;
revoke all on public.training_template_exercises from authenticated;

grant select, insert, update, delete on public.training_templates to authenticated;
grant select, insert, update, delete on public.training_template_exercises to authenticated;

drop trigger if exists training_templates_set_updated_at on public.training_templates;
create trigger training_templates_set_updated_at
before update on public.training_templates
for each row execute function private.set_updated_at();

drop trigger if exists training_template_exercises_set_updated_at on public.training_template_exercises;
create trigger training_template_exercises_set_updated_at
before update on public.training_template_exercises
for each row execute function private.set_updated_at();

drop policy if exists training_templates_select_org on public.training_templates;
create policy training_templates_select_org
on public.training_templates
for select to authenticated
using ((select private.is_org_member(organization_id)));

drop policy if exists training_templates_insert_manager on public.training_templates;
create policy training_templates_insert_manager
on public.training_templates
for insert to authenticated
with check ((select private.is_org_manager(organization_id)));

drop policy if exists training_templates_update_manager on public.training_templates;
create policy training_templates_update_manager
on public.training_templates
for update to authenticated
using ((select private.is_org_manager(organization_id)))
with check ((select private.is_org_manager(organization_id)));

drop policy if exists training_templates_delete_manager on public.training_templates;
create policy training_templates_delete_manager
on public.training_templates
for delete to authenticated
using ((select private.is_org_manager(organization_id)));

drop policy if exists training_template_exercises_select_org on public.training_template_exercises;
create policy training_template_exercises_select_org
on public.training_template_exercises
for select to authenticated
using ((select private.is_org_member(organization_id)));

drop policy if exists training_template_exercises_insert_manager on public.training_template_exercises;
create policy training_template_exercises_insert_manager
on public.training_template_exercises
for insert to authenticated
with check ((select private.is_org_manager(organization_id)));

drop policy if exists training_template_exercises_update_manager on public.training_template_exercises;
create policy training_template_exercises_update_manager
on public.training_template_exercises
for update to authenticated
using ((select private.is_org_manager(organization_id)))
with check ((select private.is_org_manager(organization_id)));

drop policy if exists training_template_exercises_delete_manager on public.training_template_exercises;
create policy training_template_exercises_delete_manager
on public.training_template_exercises
for delete to authenticated
using ((select private.is_org_manager(organization_id)));

create or replace function public.create_training_template(
  p_organization_id uuid,
  p_name text,
  p_objective text default 'Geral',
  p_level text default 'Iniciante',
  p_notes text default null,
  p_exercises jsonb default '[]'::jsonb
)
returns uuid
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_template uuid;
  v_item jsonb;
  v_position integer := 0;
  v_name text := btrim(coalesce(p_name, ''));
begin
  if auth.uid() is null then
    raise exception using errcode = '42501', message = 'AUTH_REQUIRED';
  end if;

  if not private.is_org_manager(p_organization_id) then
    raise exception using errcode = '42501', message = 'ORG_MANAGER_REQUIRED';
  end if;

  if char_length(v_name) < 2 or char_length(v_name) > 120 then
    raise exception using errcode = '22023', message = 'TEMPLATE_NAME_INVALID';
  end if;

  if jsonb_typeof(p_exercises) <> 'array' or jsonb_array_length(p_exercises) = 0 then
    raise exception using errcode = '22023', message = 'TEMPLATE_EXERCISES_REQUIRED';
  end if;

  insert into public.training_templates (
    organization_id,
    name,
    objective,
    level,
    notes,
    created_by
  ) values (
    p_organization_id,
    v_name,
    coalesce(nullif(btrim(coalesce(p_objective, '')), ''), 'Geral'),
    coalesce(nullif(btrim(coalesce(p_level, '')), ''), 'Iniciante'),
    nullif(btrim(coalesce(p_notes, '')), ''),
    auth.uid()
  )
  returning id into v_template;

  for v_item in select value from jsonb_array_elements(p_exercises)
  loop
    if char_length(btrim(coalesce(v_item ->> 'name', ''))) < 2 then
      raise exception using errcode = '22023', message = 'TEMPLATE_EXERCISE_NAME_INVALID';
    end if;

    insert into public.training_template_exercises (
      organization_id,
      template_id,
      position,
      name,
      prescription
    ) values (
      p_organization_id,
      v_template,
      v_position,
      btrim(v_item ->> 'name'),
      btrim(coalesce(v_item ->> 'prescription', ''))
    );

    v_position := v_position + 1;
  end loop;

  return v_template;
end;
$$;

revoke execute on function public.create_training_template(uuid,text,text,text,text,jsonb) from public, anon;
grant execute on function public.create_training_template(uuid,text,text,text,text,jsonb) to authenticated;

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
  where t.id = p_template_id
    and t.is_active;

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
    jsonb_agg(
      jsonb_build_object(
        'name', e.name,
        'prescription', e.prescription
      ) order by e.position
    ),
    '[]'::jsonb
  )
  into v_exercises
  from public.training_template_exercises e
  where e.template_id = v_template.id
    and e.organization_id = v_template.organization_id;

  if jsonb_array_length(v_exercises) = 0 then
    raise exception using errcode = '22023', message = 'TEMPLATE_HAS_NO_EXERCISES';
  end if;

  select public.create_training_plan(
    p_student_id,
    v_template.name,
    p_next_session,
    v_template.notes,
    v_exercises
  )
  into v_plan;

  return v_plan;
end;
$$;

revoke execute on function public.assign_training_template(uuid,uuid,text) from public, anon;
grant execute on function public.assign_training_template(uuid,uuid,text) to authenticated;

create or replace function public.create_training_template_from_plan(
  p_plan_id uuid,
  p_name text default null
)
returns uuid
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_plan record;
  v_student record;
  v_exercises jsonb := '[]'::jsonb;
  v_template_name text;
  v_template uuid;
begin
  if auth.uid() is null then
    raise exception using errcode = '42501', message = 'AUTH_REQUIRED';
  end if;

  select p.* into v_plan
  from public.training_plans p
  where p.id = p_plan_id;

  if v_plan.id is null then
    raise exception using errcode = 'P0002', message = 'TRAINING_PLAN_NOT_FOUND';
  end if;

  if not private.is_org_manager(v_plan.organization_id) then
    raise exception using errcode = '42501', message = 'ORG_MANAGER_REQUIRED';
  end if;

  select s.* into v_student
  from public.students s
  where s.id = v_plan.student_id
    and s.organization_id = v_plan.organization_id;

  select coalesce(
    jsonb_agg(
      jsonb_build_object(
        'name', e.name,
        'prescription', e.prescription
      ) order by e.position
    ),
    '[]'::jsonb
  )
  into v_exercises
  from public.training_exercises e
  where e.training_plan_id = v_plan.id
    and e.organization_id = v_plan.organization_id;

  v_template_name := coalesce(
    nullif(btrim(coalesce(p_name, '')), ''),
    v_plan.name
  );

  select public.create_training_template(
    v_plan.organization_id,
    v_template_name,
    coalesce(v_student.objective, 'Geral'),
    coalesce(v_student.level, 'Iniciante'),
    v_plan.notes,
    v_exercises
  )
  into v_template;

  return v_template;
end;
$$;

revoke execute on function public.create_training_template_from_plan(uuid,text) from public, anon;
grant execute on function public.create_training_template_from_plan(uuid,text) to authenticated;
