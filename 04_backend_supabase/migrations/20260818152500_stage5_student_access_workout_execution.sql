-- Stage 5: secure student links, workout sessions, exercise completion and history.

with ranked as (
  select id,
         row_number() over (
           partition by student_id
           order by updated_at desc, created_at desc, id desc
         ) as rn
  from public.training_plans
  where is_active
)
update public.training_plans p
   set is_active = false
  from ranked r
 where p.id = r.id
   and r.rn > 1;

create unique index if not exists training_plans_one_active_student_idx
  on public.training_plans(student_id)
  where is_active;

create unique index if not exists training_plans_id_student_org_uq
  on public.training_plans(id, student_id, organization_id);

create unique index if not exists training_exercises_id_plan_org_uq
  on public.training_exercises(id, training_plan_id, organization_id);

create table if not exists public.student_access_links (
  id uuid primary key default extensions.gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  student_id uuid not null,
  token_hash bytea not null unique,
  is_active boolean not null default true,
  expires_at timestamptz,
  last_used_at timestamptz,
  created_by uuid,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint student_access_links_student_same_org_fk
    foreign key (student_id, organization_id)
    references public.students(id, organization_id)
    on delete cascade
);

create unique index if not exists student_access_links_one_active_student_idx
  on public.student_access_links(student_id)
  where is_active;

create index if not exists student_access_links_org_student_idx
  on public.student_access_links(organization_id, student_id);

create table if not exists public.workout_sessions (
  id uuid primary key default extensions.gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  student_id uuid not null,
  training_plan_id uuid not null,
  student_access_link_id uuid references public.student_access_links(id) on delete set null,
  status text not null default 'in_progress'
    check (status in ('in_progress', 'completed', 'cancelled')),
  started_at timestamptz not null default now(),
  completed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (id, training_plan_id, organization_id),
  constraint workout_sessions_plan_student_same_org_fk
    foreign key (training_plan_id, student_id, organization_id)
    references public.training_plans(id, student_id, organization_id)
    on delete cascade
);

create unique index if not exists workout_sessions_one_in_progress_idx
  on public.workout_sessions(student_id, training_plan_id)
  where status = 'in_progress';

create index if not exists workout_sessions_student_started_idx
  on public.workout_sessions(student_id, started_at desc);

create table if not exists public.workout_exercise_logs (
  id uuid primary key default extensions.gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  session_id uuid not null,
  training_plan_id uuid not null,
  exercise_id uuid not null,
  completed boolean not null default false,
  completed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (session_id, exercise_id),
  constraint workout_exercise_logs_session_same_plan_org_fk
    foreign key (session_id, training_plan_id, organization_id)
    references public.workout_sessions(id, training_plan_id, organization_id)
    on delete cascade,
  constraint workout_exercise_logs_exercise_same_plan_org_fk
    foreign key (exercise_id, training_plan_id, organization_id)
    references public.training_exercises(id, training_plan_id, organization_id)
    on delete cascade
);

create index if not exists workout_exercise_logs_session_idx
  on public.workout_exercise_logs(session_id);

alter table public.student_access_links enable row level security;
alter table public.workout_sessions enable row level security;
alter table public.workout_exercise_logs enable row level security;

revoke all on public.student_access_links from anon, authenticated;
revoke all on public.workout_sessions from anon, authenticated;
revoke all on public.workout_exercise_logs from anon, authenticated;

grant select on public.workout_sessions to authenticated;
grant select on public.workout_exercise_logs to authenticated;

drop trigger if exists student_access_links_set_updated_at on public.student_access_links;
create trigger student_access_links_set_updated_at
before update on public.student_access_links
for each row execute function private.set_updated_at();

drop trigger if exists workout_sessions_set_updated_at on public.workout_sessions;
create trigger workout_sessions_set_updated_at
before update on public.workout_sessions
for each row execute function private.set_updated_at();

drop trigger if exists workout_exercise_logs_set_updated_at on public.workout_exercise_logs;
create trigger workout_exercise_logs_set_updated_at
before update on public.workout_exercise_logs
for each row execute function private.set_updated_at();

drop policy if exists workout_sessions_select_org on public.workout_sessions;
create policy workout_sessions_select_org on public.workout_sessions
for select to authenticated
using ((select private.is_org_member(organization_id)));

drop policy if exists workout_exercise_logs_select_org on public.workout_exercise_logs;
create policy workout_exercise_logs_select_org on public.workout_exercise_logs
for select to authenticated
using ((select private.is_org_member(organization_id)));

create or replace function private.resolve_student_access(p_token text)
returns table(link_id uuid, organization_id uuid, student_id uuid)
language plpgsql
stable
security definer
set search_path = ''
as $$
begin
  if p_token is null or p_token !~ '^[0-9a-fA-F]{64}$' then
    return;
  end if;

  return query
  select l.id, l.organization_id, l.student_id
    from public.student_access_links l
   where l.token_hash = extensions.digest(p_token, 'sha256')
     and l.is_active
     and (l.expires_at is null or l.expires_at > now())
   limit 1;
end;
$$;

revoke all on function private.resolve_student_access(text) from public, anon, authenticated;

create or replace function public.issue_student_access_token(p_student_id uuid)
returns text
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_org uuid;
  v_token text;
begin
  if auth.uid() is null then
    raise exception using errcode = '42501', message = 'AUTH_REQUIRED';
  end if;

  select s.organization_id into v_org
    from public.students s
   where s.id = p_student_id;

  if v_org is null then
    raise exception using errcode = 'P0002', message = 'STUDENT_NOT_FOUND';
  end if;

  if not private.is_org_manager(v_org) then
    raise exception using errcode = '42501', message = 'ORG_MANAGER_REQUIRED';
  end if;

  update public.student_access_links
     set is_active = false
   where student_id = p_student_id
     and is_active;

  v_token := encode(extensions.gen_random_bytes(32), 'hex');

  insert into public.student_access_links (
    organization_id,
    student_id,
    token_hash,
    created_by
  ) values (
    v_org,
    p_student_id,
    extensions.digest(v_token, 'sha256'),
    auth.uid()
  );

  return v_token;
end;
$$;

revoke all on function public.issue_student_access_token(uuid) from public, anon;
grant execute on function public.issue_student_access_token(uuid) to authenticated;

create or replace function public.get_student_workout(p_token text)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_access record;
  v_student record;
  v_plan record;
  v_session record;
  v_exercises jsonb := '[]'::jsonb;
  v_history jsonb := '[]'::jsonb;
begin
  select * into v_access from private.resolve_student_access(p_token);
  if not found then
    raise exception using errcode = '42501', message = 'STUDENT_ACCESS_INVALID';
  end if;

  select s.* into v_student
    from public.students s
   where s.id = v_access.student_id
     and s.organization_id = v_access.organization_id;

  select p.* into v_plan
    from public.training_plans p
   where p.student_id = v_access.student_id
     and p.organization_id = v_access.organization_id
     and p.is_active
   order by p.updated_at desc
   limit 1;

  if v_plan.id is not null then
    select ws.* into v_session
      from public.workout_sessions ws
     where ws.student_id = v_access.student_id
       and ws.organization_id = v_access.organization_id
       and ws.training_plan_id = v_plan.id
       and ws.status <> 'cancelled'
     order by case when ws.status = 'in_progress' then 0 else 1 end,
              ws.started_at desc
     limit 1;

    select coalesce(
             jsonb_agg(
               jsonb_build_object(
                 'id', e.id,
                 'position', e.position,
                 'name', e.name,
                 'prescription', e.prescription,
                 'completed', coalesce(l.completed, false),
                 'completed_at', l.completed_at
               ) order by e.position
             ),
             '[]'::jsonb
           )
      into v_exercises
      from public.training_exercises e
      left join public.workout_exercise_logs l
        on v_session.id is not null
       and l.session_id = v_session.id
       and l.exercise_id = e.id
     where e.training_plan_id = v_plan.id
       and e.organization_id = v_access.organization_id;
  end if;

  select coalesce(jsonb_agg(h.item order by h.started_at desc), '[]'::jsonb)
    into v_history
    from (
      select ws.started_at,
             jsonb_build_object(
               'id', ws.id,
               'plan_name', p.name,
               'status', ws.status,
               'started_at', ws.started_at,
               'completed_at', ws.completed_at,
               'completed_exercises', (
                 select count(*)::int
                   from public.workout_exercise_logs wl
                  where wl.session_id = ws.id
                    and wl.completed
               ),
               'total_exercises', (
                 select count(*)::int
                   from public.training_exercises te
                  where te.training_plan_id = ws.training_plan_id
               )
             ) as item
        from public.workout_sessions ws
        join public.training_plans p on p.id = ws.training_plan_id
       where ws.student_id = v_access.student_id
         and ws.organization_id = v_access.organization_id
         and ws.status <> 'cancelled'
       order by ws.started_at desc
       limit 10
    ) h;

  return jsonb_build_object(
    'student', jsonb_build_object(
      'id', v_student.id,
      'name', v_student.name,
      'objective', v_student.objective,
      'level', v_student.level,
      'adherence', v_student.adherence,
      'status', v_student.status
    ),
    'plan', case when v_plan.id is null then null else jsonb_build_object(
      'id', v_plan.id,
      'name', v_plan.name,
      'notes', v_plan.notes,
      'next_session', v_plan.next_session
    ) end,
    'session', case when v_session.id is null then null else jsonb_build_object(
      'id', v_session.id,
      'status', v_session.status,
      'started_at', v_session.started_at,
      'completed_at', v_session.completed_at
    ) end,
    'exercises', v_exercises,
    'history', v_history
  );
end;
$$;

revoke all on function public.get_student_workout(text) from public;
grant execute on function public.get_student_workout(text) to anon, authenticated;

create or replace function public.start_student_workout(p_token text)
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_access record;
  v_plan uuid;
  v_session uuid;
begin
  select * into v_access from private.resolve_student_access(p_token);
  if not found then
    raise exception using errcode = '42501', message = 'STUDENT_ACCESS_INVALID';
  end if;

  select p.id into v_plan
    from public.training_plans p
   where p.student_id = v_access.student_id
     and p.organization_id = v_access.organization_id
     and p.is_active
   order by p.updated_at desc
   limit 1;

  if v_plan is null then
    raise exception using errcode = 'P0002', message = 'ACTIVE_TRAINING_NOT_FOUND';
  end if;

  insert into public.workout_sessions (
    organization_id,
    student_id,
    training_plan_id,
    student_access_link_id
  ) values (
    v_access.organization_id,
    v_access.student_id,
    v_plan,
    v_access.link_id
  )
  on conflict (student_id, training_plan_id) where status = 'in_progress'
  do update set student_access_link_id = excluded.student_access_link_id
  returning id into v_session;

  update public.student_access_links
     set last_used_at = now()
   where id = v_access.link_id;

  update public.students
     set status = 'Em treino'
   where id = v_access.student_id
     and organization_id = v_access.organization_id;

  return v_session;
end;
$$;

revoke all on function public.start_student_workout(text) from public;
grant execute on function public.start_student_workout(text) to anon, authenticated;

create or replace function public.set_student_exercise_completion(
  p_token text,
  p_session_id uuid,
  p_exercise_id uuid,
  p_completed boolean
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_access record;
  v_session record;
  v_plan_name text;
  v_total integer := 0;
  v_done integer := 0;
  v_adherence integer := 0;
begin
  select * into v_access from private.resolve_student_access(p_token);
  if not found then
    raise exception using errcode = '42501', message = 'STUDENT_ACCESS_INVALID';
  end if;

  select ws.* into v_session
    from public.workout_sessions ws
   where ws.id = p_session_id
     and ws.student_id = v_access.student_id
     and ws.organization_id = v_access.organization_id
     and ws.status in ('in_progress', 'completed');

  if v_session.id is null then
    raise exception using errcode = 'P0002', message = 'WORKOUT_SESSION_NOT_FOUND';
  end if;

  if not exists (
    select 1
      from public.training_exercises e
     where e.id = p_exercise_id
       and e.training_plan_id = v_session.training_plan_id
       and e.organization_id = v_access.organization_id
  ) then
    raise exception using errcode = 'P0002', message = 'EXERCISE_NOT_FOUND';
  end if;

  insert into public.workout_exercise_logs (
    organization_id,
    session_id,
    training_plan_id,
    exercise_id,
    completed,
    completed_at
  ) values (
    v_access.organization_id,
    v_session.id,
    v_session.training_plan_id,
    p_exercise_id,
    p_completed,
    case when p_completed then now() else null end
  )
  on conflict (session_id, exercise_id)
  do update set
    completed = excluded.completed,
    completed_at = excluded.completed_at;

  select count(*)::int into v_total
    from public.training_exercises e
   where e.training_plan_id = v_session.training_plan_id
     and e.organization_id = v_access.organization_id;

  select count(*)::int into v_done
    from public.workout_exercise_logs l
   where l.session_id = v_session.id
     and l.completed;

  if v_total > 0 and v_done = v_total then
    update public.workout_sessions
       set status = 'completed',
           completed_at = coalesce(completed_at, now())
     where id = v_session.id;

    select p.name into v_plan_name
      from public.training_plans p
     where p.id = v_session.training_plan_id;

    update public.students
       set last_workout = v_plan_name,
           last_workout_date = current_date,
           status = 'Treino concluído'
     where id = v_access.student_id
       and organization_id = v_access.organization_id;
  else
    update public.workout_sessions
       set status = 'in_progress',
           completed_at = null
     where id = v_session.id;

    update public.students
       set status = 'Em treino'
     where id = v_access.student_id
       and organization_id = v_access.organization_id;
  end if;

  select coalesce(round(avg(x.percent_complete)), 0)::int
    into v_adherence
    from (
      select case
               when totals.total_count = 0 then 0::numeric
               else (100.0 * totals.done_count / totals.total_count)
             end as percent_complete
        from (
          select ws.id,
                 (
                   select count(*)::numeric
                     from public.training_exercises e
                    where e.training_plan_id = ws.training_plan_id
                 ) as total_count,
                 (
                   select count(*)::numeric
                     from public.workout_exercise_logs l
                    where l.session_id = ws.id
                      and l.completed
                 ) as done_count
            from public.workout_sessions ws
           where ws.student_id = v_access.student_id
             and ws.organization_id = v_access.organization_id
             and ws.status <> 'cancelled'
           order by ws.started_at desc
           limit 10
        ) totals
    ) x;

  update public.students
     set adherence = greatest(0, least(100, v_adherence))
   where id = v_access.student_id
     and organization_id = v_access.organization_id;

  update public.student_access_links
     set last_used_at = now()
   where id = v_access.link_id;

  return jsonb_build_object(
    'session_id', v_session.id,
    'status', case when v_total > 0 and v_done = v_total then 'completed' else 'in_progress' end,
    'completed_exercises', v_done,
    'total_exercises', v_total,
    'adherence', v_adherence
  );
end;
$$;

revoke all on function public.set_student_exercise_completion(text,uuid,uuid,boolean) from public;
grant execute on function public.set_student_exercise_completion(text,uuid,uuid,boolean) to anon, authenticated;

-- Preserve one active plan per student from now on.
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

  update public.training_plans
     set is_active = false
   where student_id = p_student_id
     and organization_id = v_org
     and is_active;

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
