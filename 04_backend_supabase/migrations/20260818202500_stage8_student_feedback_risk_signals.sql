create unique index if not exists workout_sessions_id_student_org_uq
  on public.workout_sessions(id, student_id, organization_id);

create table if not exists public.workout_feedback (
  id uuid primary key default extensions.gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  student_id uuid not null,
  session_id uuid not null unique,
  perceived_exertion smallint not null check (perceived_exertion between 1 and 10),
  pain_score smallint not null check (pain_score between 0 and 10),
  energy_score smallint not null check (energy_score between 1 and 5),
  pain_location text check (pain_location is null or char_length(pain_location) <= 120),
  note text check (note is null or char_length(note) <= 500),
  submitted_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint workout_feedback_session_student_org_fk
    foreign key (session_id, student_id, organization_id)
    references public.workout_sessions(id, student_id, organization_id)
    on delete cascade
);

create index if not exists workout_feedback_org_student_submitted_idx
  on public.workout_feedback(organization_id, student_id, submitted_at desc);

create index if not exists workout_feedback_session_student_org_fk_idx
  on public.workout_feedback(session_id, student_id, organization_id);

alter table public.workout_feedback enable row level security;

revoke all on public.workout_feedback from anon, authenticated;
grant select on public.workout_feedback to authenticated;

drop trigger if exists workout_feedback_set_updated_at on public.workout_feedback;
create trigger workout_feedback_set_updated_at
before update on public.workout_feedback
for each row execute function private.set_updated_at();

drop policy if exists workout_feedback_select_org on public.workout_feedback;
create policy workout_feedback_select_org
on public.workout_feedback
for select
to authenticated
using ((select private.is_org_member(organization_id)));

create or replace function public.get_student_feedback_context(p_token text)
returns jsonb
language plpgsql
stable
security definer
set search_path = ''
as $$
declare
  v_access record;
  v_session record;
  v_feedback record;
begin
  select * into v_access from private.resolve_student_access(p_token);
  if not found then
    raise exception using errcode = '42501', message = 'STUDENT_ACCESS_INVALID';
  end if;

  select ws.*, p.name as plan_name
    into v_session
    from public.workout_sessions ws
    join public.training_plans p
      on p.id = ws.training_plan_id
     and p.organization_id = ws.organization_id
   where ws.student_id = v_access.student_id
     and ws.organization_id = v_access.organization_id
     and ws.status = 'completed'
   order by ws.completed_at desc nulls last, ws.started_at desc
   limit 1;

  if v_session.id is null then
    return jsonb_build_object('eligible', false, 'reason', 'NO_COMPLETED_SESSION', 'submitted', false);
  end if;

  select wf.* into v_feedback
    from public.workout_feedback wf
   where wf.session_id = v_session.id;

  return jsonb_build_object(
    'eligible', true,
    'session_id', v_session.id,
    'plan_name', v_session.plan_name,
    'completed_at', v_session.completed_at,
    'submitted', v_feedback.id is not null,
    'feedback', case when v_feedback.id is null then null else jsonb_build_object(
      'perceived_exertion', v_feedback.perceived_exertion,
      'pain_score', v_feedback.pain_score,
      'energy_score', v_feedback.energy_score,
      'pain_location', v_feedback.pain_location,
      'note', v_feedback.note,
      'submitted_at', v_feedback.submitted_at
    ) end
  );
end;
$$;

revoke all on function public.get_student_feedback_context(text) from public;
grant execute on function public.get_student_feedback_context(text) to anon, authenticated;

create or replace function public.submit_student_workout_feedback(
  p_token text,
  p_session_id uuid,
  p_perceived_exertion integer,
  p_pain_score integer,
  p_energy_score integer,
  p_pain_location text default null,
  p_note text default null
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_access record;
  v_session record;
  v_feedback_id uuid;
  v_pain_location text := nullif(btrim(coalesce(p_pain_location, '')), '');
  v_note text := nullif(btrim(coalesce(p_note, '')), '');
begin
  if p_perceived_exertion is null or p_perceived_exertion not between 1 and 10 then
    raise exception using errcode = '22023', message = 'PERCEIVED_EXERTION_INVALID';
  end if;
  if p_pain_score is null or p_pain_score not between 0 and 10 then
    raise exception using errcode = '22023', message = 'PAIN_SCORE_INVALID';
  end if;
  if p_energy_score is null or p_energy_score not between 1 and 5 then
    raise exception using errcode = '22023', message = 'ENERGY_SCORE_INVALID';
  end if;
  if v_pain_location is not null and char_length(v_pain_location) > 120 then
    raise exception using errcode = '22023', message = 'PAIN_LOCATION_TOO_LONG';
  end if;
  if v_note is not null and char_length(v_note) > 500 then
    raise exception using errcode = '22023', message = 'FEEDBACK_NOTE_TOO_LONG';
  end if;

  select * into v_access from private.resolve_student_access(p_token);
  if not found then
    raise exception using errcode = '42501', message = 'STUDENT_ACCESS_INVALID';
  end if;

  select ws.* into v_session
    from public.workout_sessions ws
   where ws.id = p_session_id
     and ws.student_id = v_access.student_id
     and ws.organization_id = v_access.organization_id
     and ws.status = 'completed';

  if v_session.id is null then
    raise exception using errcode = 'P0002', message = 'COMPLETED_SESSION_NOT_FOUND';
  end if;

  insert into public.workout_feedback (
    organization_id, student_id, session_id, perceived_exertion, pain_score,
    energy_score, pain_location, note
  ) values (
    v_access.organization_id, v_access.student_id, v_session.id,
    p_perceived_exertion, p_pain_score, p_energy_score, v_pain_location, v_note
  )
  on conflict (session_id)
  do update set
    perceived_exertion = excluded.perceived_exertion,
    pain_score = excluded.pain_score,
    energy_score = excluded.energy_score,
    pain_location = excluded.pain_location,
    note = excluded.note,
    submitted_at = now()
  returning id into v_feedback_id;

  update public.student_access_links set last_used_at = now() where id = v_access.link_id;

  return jsonb_build_object(
    'feedback_id', v_feedback_id,
    'session_id', v_session.id,
    'submitted', true,
    'risk_signal', case
      when p_pain_score >= 7 then 'high'
      when p_pain_score >= 4 then 'medium'
      when p_perceived_exertion >= 9 and p_energy_score <= 2 then 'high'
      when p_perceived_exertion >= 9 or p_energy_score <= 2 then 'medium'
      else 'low'
    end
  );
end;
$$;

revoke all on function public.submit_student_workout_feedback(text,uuid,integer,integer,integer,text,text) from public;
grant execute on function public.submit_student_workout_feedback(text,uuid,integer,integer,integer,text,text) to anon, authenticated;

create or replace function public.get_professor_progress_dashboard_v2(p_organization_id uuid)
returns jsonb
language plpgsql
stable
security invoker
set search_path = ''
as $$
declare
  v_base jsonb;
  v_students jsonb := '[]'::jsonb;
  v_summary jsonb := '{}'::jsonb;
  v_high integer := 0;
  v_medium integer := 0;
  v_feedback_7d integer := 0;
  v_pain_alerts_7d integer := 0;
begin
  v_base := public.get_professor_progress_dashboard(p_organization_id);

  with enriched as (
    select e.ordinality,
      case
        when lf.pain_score >= 7 then e.value || jsonb_build_object(
          'risk_level', 'high',
          'risk_reason', 'Dor relatada em ' || lf.pain_score || '/10 no último feedback',
          'next_best_action', 'Entrar em contato antes da próxima sessão e revisar desconforto e prescrição',
          'latest_feedback', lf.feedback)
        when e.value ->> 'risk_level' = 'high' then e.value || jsonb_build_object('latest_feedback', lf.feedback)
        when lf.perceived_exertion >= 9 and lf.energy_score <= 2 then e.value || jsonb_build_object(
          'risk_level', 'high',
          'risk_reason', 'Esforço muito alto com baixa energia no último feedback',
          'next_best_action', 'Revisar intensidade e recuperação percebida antes da próxima sessão',
          'latest_feedback', lf.feedback)
        when lf.pain_score >= 4 then e.value || jsonb_build_object(
          'risk_level', 'medium',
          'risk_reason', 'Desconforto relatado em ' || lf.pain_score || '/10 no último feedback',
          'next_best_action', 'Revisar o desconforto relatado antes de progredir o treino',
          'latest_feedback', lf.feedback)
        when e.value ->> 'risk_level' = 'medium' then e.value || jsonb_build_object('latest_feedback', lf.feedback)
        when lf.perceived_exertion >= 9 then e.value || jsonb_build_object(
          'risk_level', 'medium',
          'risk_reason', 'Esforço percebido muito alto no último feedback',
          'next_best_action', 'Validar a intensidade percebida antes de progredir o treino',
          'latest_feedback', lf.feedback)
        when lf.energy_score <= 2 then e.value || jsonb_build_object(
          'risk_level', 'medium',
          'risk_reason', 'Baixa energia relatada no último feedback',
          'next_best_action', 'Checar recuperação e ajustar a próxima sessão se necessário',
          'latest_feedback', lf.feedback)
        else e.value || jsonb_build_object('latest_feedback', lf.feedback)
      end as item
    from jsonb_array_elements(v_base -> 'students') with ordinality as e(value, ordinality)
    left join lateral (
      select wf.pain_score, wf.perceived_exertion, wf.energy_score,
        jsonb_build_object(
          'session_id', wf.session_id,
          'perceived_exertion', wf.perceived_exertion,
          'pain_score', wf.pain_score,
          'energy_score', wf.energy_score,
          'pain_location', wf.pain_location,
          'note', wf.note,
          'submitted_at', wf.submitted_at) as feedback
      from public.workout_feedback wf
      where wf.organization_id = p_organization_id
        and wf.student_id = (e.value ->> 'student_id')::uuid
      order by wf.submitted_at desc
      limit 1
    ) lf on true
  )
  select coalesce(jsonb_agg(item order by ordinality), '[]'::jsonb)
    into v_students from enriched;

  select count(*) filter (where value ->> 'risk_level' = 'high')::int,
         count(*) filter (where value ->> 'risk_level' = 'medium')::int
    into v_high, v_medium
    from jsonb_array_elements(v_students);

  select count(*) filter (where submitted_at >= now() - interval '7 days')::int,
         count(*) filter (where submitted_at >= now() - interval '7 days' and pain_score >= 7)::int
    into v_feedback_7d, v_pain_alerts_7d
    from public.workout_feedback
    where organization_id = p_organization_id;

  v_summary := (v_base -> 'summary') || jsonb_build_object(
    'high_risk', v_high,
    'medium_risk', v_medium,
    'feedback_7d', v_feedback_7d,
    'pain_alerts_7d', v_pain_alerts_7d);

  return jsonb_set(jsonb_set(v_base, '{students}', v_students, true), '{summary}', v_summary, true);
end;
$$;

revoke execute on function public.get_professor_progress_dashboard_v2(uuid) from public, anon;
grant execute on function public.get_professor_progress_dashboard_v2(uuid) to authenticated;
