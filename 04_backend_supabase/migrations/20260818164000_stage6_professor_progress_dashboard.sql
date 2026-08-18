create or replace function public.get_professor_progress_dashboard(
  p_organization_id uuid
)
returns jsonb
language plpgsql
stable
security invoker
set search_path = ''
as $$
declare
  v_students jsonb := '[]'::jsonb;
  v_recent jsonb := '[]'::jsonb;
  v_summary jsonb := '{}'::jsonb;
begin
  if auth.uid() is null then
    raise exception using errcode = '42501', message = 'AUTH_REQUIRED';
  end if;

  if p_organization_id is null or not private.is_org_member(p_organization_id) then
    raise exception using errcode = '42501', message = 'ORG_MEMBER_REQUIRED';
  end if;

  with session_stats as (
    select
      s.id as student_id,
      count(ws.id) filter (
        where ws.started_at >= now() - interval '30 days'
          and ws.status <> 'cancelled'
      )::int as sessions_30d,
      count(ws.id) filter (
        where ws.started_at >= now() - interval '30 days'
          and ws.status = 'completed'
      )::int as completed_30d,
      max(ws.started_at) filter (where ws.status <> 'cancelled') as last_session_at,
      max(ws.completed_at) filter (where ws.status = 'completed') as last_completed_at
    from public.students s
    left join public.workout_sessions ws
      on ws.student_id = s.id
     and ws.organization_id = s.organization_id
    where s.organization_id = p_organization_id
    group by s.id
  ),
  student_progress as (
    select
      s.id,
      s.name,
      s.objective,
      s.level,
      s.status,
      s.adherence,
      coalesce(ss.sessions_30d, 0) as sessions_30d,
      coalesce(ss.completed_30d, 0) as completed_30d,
      ss.last_session_at,
      ss.last_completed_at,
      case
        when coalesce(ss.sessions_30d, 0) = 0 then 'new'
        when ss.last_session_at < now() - interval '14 days' then 'high'
        when s.adherence < 40 then 'high'
        when ss.last_session_at < now() - interval '7 days' then 'medium'
        when s.adherence < 70 then 'medium'
        else 'low'
      end as risk_level,
      case
        when coalesce(ss.sessions_30d, 0) = 0 then 'Sem execução registrada nos últimos 30 dias'
        when ss.last_session_at < now() - interval '14 days' then 'Sem execução há mais de 14 dias'
        when s.adherence < 40 then 'Aderência abaixo de 40%'
        when ss.last_session_at < now() - interval '7 days' then 'Sem execução há mais de 7 dias'
        when s.adherence < 70 then 'Aderência abaixo de 70%'
        else 'Ritmo de execução saudável'
      end as risk_reason,
      case
        when coalesce(ss.sessions_30d, 0) = 0 then 'Gerar acesso e acompanhar o primeiro treino'
        when ss.last_session_at < now() - interval '14 days' then 'Entrar em contato e revisar o plano de adesão'
        when s.adherence < 40 then 'Revisar treino e barreiras de execução com o aluno'
        when ss.last_session_at < now() - interval '7 days' then 'Confirmar a próxima sessão e estimular retomada'
        when s.adherence < 70 then 'Acompanhar a próxima execução e ajustar se necessário'
        else 'Manter acompanhamento e progressão planejada'
      end as next_best_action
    from public.students s
    left join session_stats ss on ss.student_id = s.id
    where s.organization_id = p_organization_id
  )
  select coalesce(
    jsonb_agg(
      jsonb_build_object(
        'student_id', sp.id,
        'name', sp.name,
        'objective', sp.objective,
        'level', sp.level,
        'status', sp.status,
        'adherence', sp.adherence,
        'sessions_30d', sp.sessions_30d,
        'completed_30d', sp.completed_30d,
        'completion_rate_30d', case
          when sp.sessions_30d = 0 then 0
          else round(100.0 * sp.completed_30d / sp.sessions_30d)::int
        end,
        'last_session_at', sp.last_session_at,
        'last_completed_at', sp.last_completed_at,
        'risk_level', sp.risk_level,
        'risk_reason', sp.risk_reason,
        'next_best_action', sp.next_best_action
      )
      order by
        case sp.risk_level
          when 'high' then 0
          when 'medium' then 1
          when 'new' then 2
          else 3
        end,
        sp.adherence asc,
        sp.name asc
    ),
    '[]'::jsonb
  )
  into v_students
  from student_progress sp;

  select coalesce(
    jsonb_agg(r.item order by r.started_at desc),
    '[]'::jsonb
  )
  into v_recent
  from (
    select
      ws.started_at,
      jsonb_build_object(
        'session_id', ws.id,
        'student_id', ws.student_id,
        'student_name', s.name,
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
        ),
        'completion_percent', case
          when (
            select count(*)
            from public.training_exercises te
            where te.training_plan_id = ws.training_plan_id
          ) = 0 then 0
          else round(
            100.0 * (
              select count(*)
              from public.workout_exercise_logs wl
              where wl.session_id = ws.id
                and wl.completed
            ) / (
              select count(*)
              from public.training_exercises te
              where te.training_plan_id = ws.training_plan_id
            )
          )::int
        end
      ) as item
    from public.workout_sessions ws
    join public.students s
      on s.id = ws.student_id
     and s.organization_id = ws.organization_id
    join public.training_plans p
      on p.id = ws.training_plan_id
     and p.organization_id = ws.organization_id
    where ws.organization_id = p_organization_id
      and ws.status <> 'cancelled'
    order by ws.started_at desc
    limit 12
  ) r;

  with risk_counts as (
    select
      count(*) filter (
        where coalesce(ss.sessions_30d, 0) > 0
          and (
            ss.last_session_at < now() - interval '14 days'
            or s.adherence < 40
          )
      )::int as high_risk,
      count(*) filter (
        where coalesce(ss.sessions_30d, 0) > 0
          and not (
            ss.last_session_at < now() - interval '14 days'
            or s.adherence < 40
          )
          and (
            ss.last_session_at < now() - interval '7 days'
            or s.adherence < 70
          )
      )::int as medium_risk,
      count(*) filter (where coalesce(ss.sessions_30d, 0) = 0)::int as new_students
    from public.students s
    left join (
      select
        st.id as student_id,
        count(ws.id) filter (
          where ws.started_at >= now() - interval '30 days'
            and ws.status <> 'cancelled'
        )::int as sessions_30d,
        max(ws.started_at) filter (where ws.status <> 'cancelled') as last_session_at
      from public.students st
      left join public.workout_sessions ws
        on ws.student_id = st.id
       and ws.organization_id = st.organization_id
      where st.organization_id = p_organization_id
      group by st.id
    ) ss on ss.student_id = s.id
    where s.organization_id = p_organization_id
  ),
  session_summary as (
    select
      count(*) filter (
        where started_at >= now() - interval '7 days'
          and status <> 'cancelled'
      )::int as sessions_7d,
      count(*) filter (
        where started_at >= now() - interval '7 days'
          and status = 'completed'
      )::int as completed_7d
    from public.workout_sessions
    where organization_id = p_organization_id
  )
  select jsonb_build_object(
    'students', (
      select count(*)::int
      from public.students
      where organization_id = p_organization_id
    ),
    'active_plans', (
      select count(*)::int
      from public.training_plans
      where organization_id = p_organization_id
        and is_active
    ),
    'average_adherence', coalesce((
      select round(avg(adherence))::int
      from public.students
      where organization_id = p_organization_id
    ), 0),
    'sessions_7d', ss.sessions_7d,
    'completed_7d', ss.completed_7d,
    'completion_rate_7d', case
      when ss.sessions_7d = 0 then 0
      else round(100.0 * ss.completed_7d / ss.sessions_7d)::int
    end,
    'high_risk', rc.high_risk,
    'medium_risk', rc.medium_risk,
    'new_students', rc.new_students
  )
  into v_summary
  from risk_counts rc
  cross join session_summary ss;

  return jsonb_build_object(
    'summary', v_summary,
    'students', v_students,
    'recent_sessions', v_recent,
    'generated_at', now()
  );
end;
$$;

revoke execute on function public.get_professor_progress_dashboard(uuid) from public, anon;
grant execute on function public.get_professor_progress_dashboard(uuid) to authenticated;
