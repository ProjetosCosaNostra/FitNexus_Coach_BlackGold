create or replace function private.is_org_manager(target_org uuid)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select 1
    from public.organization_members m
    where m.organization_id = target_org
      and m.user_id = (select auth.uid())
      and m.role in ('owner','admin')
  );
$$;

revoke all on function private.is_org_manager(uuid) from public, anon;
grant execute on function private.is_org_manager(uuid) to authenticated;

create table if not exists public.students (
  id uuid primary key default extensions.gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  name text not null check (char_length(btrim(name)) between 2 and 120),
  email text,
  objective text not null default 'Geral',
  level text not null default 'Iniciante',
  last_workout text,
  last_workout_date date,
  adherence smallint not null default 0 check (adherence between 0 and 100),
  next_session text,
  status text not null default 'Ativo',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (id, organization_id)
);

create table if not exists public.training_plans (
  id uuid primary key default extensions.gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  student_id uuid not null,
  name text not null check (char_length(btrim(name)) between 2 and 120),
  next_session text,
  notes text,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (id, organization_id),
  constraint training_plans_student_same_org_fk
    foreign key (student_id, organization_id)
    references public.students(id, organization_id)
    on delete cascade
);

create table if not exists public.training_exercises (
  id uuid primary key default extensions.gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  training_plan_id uuid not null,
  position integer not null check (position >= 0),
  name text not null check (char_length(btrim(name)) between 2 and 160),
  prescription text not null default '',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint training_exercises_plan_same_org_fk
    foreign key (training_plan_id, organization_id)
    references public.training_plans(id, organization_id)
    on delete cascade,
  unique (training_plan_id, position)
);

create index if not exists students_organization_id_idx on public.students(organization_id);
create index if not exists students_org_updated_idx on public.students(organization_id, updated_at desc);
create index if not exists training_plans_organization_id_idx on public.training_plans(organization_id);
create index if not exists training_plans_student_id_idx on public.training_plans(student_id);
create index if not exists training_exercises_plan_id_idx on public.training_exercises(training_plan_id);

alter table public.students enable row level security;
alter table public.training_plans enable row level security;
alter table public.training_exercises enable row level security;

revoke all on public.students from anon;
revoke all on public.training_plans from anon;
revoke all on public.training_exercises from anon;
revoke all on public.students from authenticated;
revoke all on public.training_plans from authenticated;
revoke all on public.training_exercises from authenticated;

grant select, insert, update, delete on public.students to authenticated;
grant select, insert, update, delete on public.training_plans to authenticated;
grant select, insert, update, delete on public.training_exercises to authenticated;

drop trigger if exists students_set_updated_at on public.students;
create trigger students_set_updated_at before update on public.students
for each row execute function private.set_updated_at();

drop trigger if exists training_plans_set_updated_at on public.training_plans;
create trigger training_plans_set_updated_at before update on public.training_plans
for each row execute function private.set_updated_at();

drop trigger if exists training_exercises_set_updated_at on public.training_exercises;
create trigger training_exercises_set_updated_at before update on public.training_exercises
for each row execute function private.set_updated_at();

drop policy if exists students_select_org on public.students;
create policy students_select_org on public.students for select to authenticated
using ((select private.is_org_member(organization_id)));

drop policy if exists students_insert_manager on public.students;
create policy students_insert_manager on public.students for insert to authenticated
with check ((select private.is_org_manager(organization_id)));

drop policy if exists students_update_manager on public.students;
create policy students_update_manager on public.students for update to authenticated
using ((select private.is_org_manager(organization_id)))
with check ((select private.is_org_manager(organization_id)));

drop policy if exists students_delete_manager on public.students;
create policy students_delete_manager on public.students for delete to authenticated
using ((select private.is_org_manager(organization_id)));

drop policy if exists training_plans_select_org on public.training_plans;
create policy training_plans_select_org on public.training_plans for select to authenticated
using ((select private.is_org_member(organization_id)));

drop policy if exists training_plans_insert_manager on public.training_plans;
create policy training_plans_insert_manager on public.training_plans for insert to authenticated
with check ((select private.is_org_manager(organization_id)));

drop policy if exists training_plans_update_manager on public.training_plans;
create policy training_plans_update_manager on public.training_plans for update to authenticated
using ((select private.is_org_manager(organization_id)))
with check ((select private.is_org_manager(organization_id)));

drop policy if exists training_plans_delete_manager on public.training_plans;
create policy training_plans_delete_manager on public.training_plans for delete to authenticated
using ((select private.is_org_manager(organization_id)));

drop policy if exists training_exercises_select_org on public.training_exercises;
create policy training_exercises_select_org on public.training_exercises for select to authenticated
using ((select private.is_org_member(organization_id)));

drop policy if exists training_exercises_insert_manager on public.training_exercises;
create policy training_exercises_insert_manager on public.training_exercises for insert to authenticated
with check ((select private.is_org_manager(organization_id)));

drop policy if exists training_exercises_update_manager on public.training_exercises;
create policy training_exercises_update_manager on public.training_exercises for update to authenticated
using ((select private.is_org_manager(organization_id)))
with check ((select private.is_org_manager(organization_id)));

drop policy if exists training_exercises_delete_manager on public.training_exercises;
create policy training_exercises_delete_manager on public.training_exercises for delete to authenticated
using ((select private.is_org_manager(organization_id)));
