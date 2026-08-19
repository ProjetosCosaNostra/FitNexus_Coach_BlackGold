-- BGF-SQL-THREE-VALUED-LEFT-JOIN-045
-- A LEFT JOIN with no action event returns NULL. `NOT (NULL AND ...)` is NULL,
-- not TRUE, so a plain WHERE predicate can accidentally hide every fresh action.
-- Coalesce the suppression predicates to FALSE so "no event" means "visible".

create or replace function public.get_coach_action_center(p_organization_id uuid)
returns jsonb
language plpgsql
stable
security invoker
set search_path = ''
as $$
declare
  v_actions jsonb := '[]'::jsonb;
  v_summary jsonb := '{}'::jsonb;
  v_completed_today integer := 0;
  v_snoozed integer := 0;
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
      max(ws.started_at) filter (where ws.status <> 'cancelled') as last_session_at
    from public.students s
    left join public.workout_sessions ws
      on ws.student_id = s.id
     and ws.organization_id = s.organization_id
    where s.organization_id = p_organization_id
    group by s.id
  ),
  signals as (
    select
      s.id as student_id,
      s.name,
      s.objective,
      s.level,
      s.status,
      s.adherence,
      coalesce(ss.sessions_30d, 0) as sessions_30d,
      coalesce(ss.completed_30d, 0) as completed_30d,
      ss.last_session_at,
      wf.id as feedback_id,
      wf.pain_score,
      wf.perceived_exertion,
      wf.energy_score,
      wf.pain_location,
      wf.submitted_at as feedback_submitted_at,
      tp.id as active_plan_id,
      tp.name as active_plan_name,
      al.id as active_access_id,
      dir.id as unresolved_decision_run_id,
      dir.created_at as unresolved_decision_created_at
    from public.students s
    left join session_stats ss on ss.student_id = s.id
    left join lateral (
      select f.*
      from public.workout_feedback f
      where f.student_id = s.id
        and f.organization_id = s.organization_id
      order by f.submitted_at desc
      limit 1
    ) wf on true
    left join lateral (
      select p.id, p.name
      from public.training_plans p
      where p.student_id = s.id
        and p.organization_id = s.organization_id
        and p.is_active
      order by p.updated_at desc
      limit 1
    ) tp on true
    left join lateral (
      select l.id
      from public.student_access_links l
      where l.student_id = s.id
        and l.organization_id = s.organization_id
        and l.is_active
        and (l.expires_at is null or l.expires_at > now())
      order by l.created_at desc
      limit 1
    ) al on true
    left join lateral (
      select r.id, r.created_at
      from public.decision_intelligence_runs r
      left join public.decision_intelligence_outcomes o on o.run_id = r.id
      where r.student_id = s.id
        and r.organization_id = s.organization_id
        and o.id is null
      order by r.created_at desc
      limit 1
    ) dir on true
    where s.organization_id = p_organization_id
  ),
  classified as (
    select
      sig.*,
      case
        when sig.feedback_id is not null and sig.pain_score >= 7 then 100
        when sig.feedback_id is not null and sig.perceived_exertion >= 9 and sig.energy_score <= 2 then 95
        when sig.last_session_at is not null and sig.last_session_at < now() - interval '14 days' then 90
        when sig.sessions_30d > 0 and sig.adherence < 40 then 88
        when sig.feedback_id is not null and sig.pain_score >= 4 then 82
        when sig.active_plan_id is null then 78
        when sig.active_access_id is null then 74
        when sig.sessions_30d = 0 then 70
        when sig.unresolved_decision_run_id is not null then 62
        when sig.last_session_at is not null and sig.last_session_at < now() - interval '7 days' then 58
        when sig.adherence < 70 then 55
        when sig.adherence >= 80 and sig.completed_30d >= 3 then 40
        else 20
      end as priority_score,
      case
        when sig.feedback_id is not null and sig.pain_score >= 7 then 'urgent'
        when sig.feedback_id is not null and sig.perceived_exertion >= 9 and sig.energy_score <= 2 then 'urgent'
        when sig.last_session_at is not null and sig.last_session_at < now() - interval '14 days' then 'urgent'
        when sig.sessions_30d > 0 and sig.adherence < 40 then 'urgent'
        when sig.feedback_id is not null and sig.pain_score >= 4 then 'attention'
        when sig.active_plan_id is null then 'setup'
        when sig.active_access_id is null then 'setup'
        when sig.sessions_30d = 0 then 'attention'
        when sig.unresolved_decision_run_id is not null then 'attention'
        when sig.last_session_at is not null and sig.last_session_at < now() - interval '7 days' then 'attention'
        when sig.adherence < 70 then 'attention'
        else 'monitor'
      end as priority_label,
      case
        when sig.feedback_id is not null and sig.pain_score >= 7 then 'feedback_priority_review'
        when sig.feedback_id is not null and sig.perceived_exertion >= 9 and sig.energy_score <= 2 then 'recovery_priority_review'
        when sig.last_session_at is not null and sig.last_session_at < now() - interval '14 days' then 'reengagement_contact'
        when sig.sessions_30d > 0 and sig.adherence < 40 then 'adherence_recovery'
        when sig.feedback_id is not null and sig.pain_score >= 4 then 'discomfort_review'
        when sig.active_plan_id is null then 'create_first_training'
        when sig.active_access_id is null then 'issue_student_access'
        when sig.sessions_30d = 0 then 'first_execution_followup'
        when sig.unresolved_decision_run_id is not null then 'review_decision_brief'
        when sig.last_session_at is not null and sig.last_session_at < now() - interval '7 days' then 'reengagement_check'
        when sig.adherence < 70 then 'adherence_check'
        when sig.adherence >= 80 and sig.completed_30d >= 3 then 'progression_review'
        else 'maintain_monitoring'
      end as action_type,
      case
        when sig.feedback_id is not null and sig.pain_score >= 7 then 'Revisar dor/desconforto agora'
        when sig.feedback_id is not null and sig.perceived_exertion >= 9 and sig.energy_score <= 2 then 'Revisar esforço e recuperação'
        when sig.last_session_at is not null and sig.last_session_at < now() - interval '14 days' then 'Recuperar contato com o aluno'
        when sig.sessions_30d > 0 and sig.adherence < 40 then 'Investigar queda de aderência'
        when sig.feedback_id is not null and sig.pain_score >= 4 then 'Validar desconforto antes de progredir'
        when sig.active_plan_id is null then 'Criar a primeira prescrição'
        when sig.active_access_id is null then 'Liberar acesso do aluno'
        when sig.sessions_30d = 0 then 'Acompanhar a primeira execução'
        when sig.unresolved_decision_run_id is not null then 'Resolver Decision Brief pendente'
        when sig.last_session_at is not null and sig.last_session_at < now() - interval '7 days' then 'Estimular retomada'
        when sig.adherence < 70 then 'Checar barreiras de execução'
        when sig.adherence >= 80 and sig.completed_30d >= 3 then 'Revisar progressão planejada'
        else 'Manter acompanhamento'
      end as action_title,
      case
        when sig.feedback_id is not null and sig.pain_score >= 7 then
          'O feedback mais recente registrou dor/desconforto alto. O FitNexus prioriza revisão humana e não altera a prescrição.'
        when sig.feedback_id is not null and sig.perceived_exertion >= 9 and sig.energy_score <= 2 then
          'Esforço muito alto combinado com energia baixa indica necessidade de revisar o contexto antes de qualquer progressão.'
        when sig.last_session_at is not null and sig.last_session_at < now() - interval '14 days' then
          'O aluno está há mais de 14 dias sem executar um treino registrado.'
        when sig.sessions_30d > 0 and sig.adherence < 40 then
          'A aderência está abaixo de 40%; a prioridade é entender barreiras antes de trocar exercícios.'
        when sig.feedback_id is not null and sig.pain_score >= 4 then
          'Existe desconforto moderado no feedback recente; progressão fica subordinada à revisão do professor.'
        when sig.active_plan_id is null then
          'O aluno ainda não possui uma prescrição ativa.'
        when sig.active_access_id is null then
          'Há prescrição, mas nenhum link/QR ativo para o aluno acessar o treino.'
        when sig.sessions_30d = 0 then
          'Ainda não existe execução registrada nos últimos 30 dias.'
        when sig.unresolved_decision_run_id is not null then
          'Existe um Decision Brief sem resultado humano registrado.'
        when sig.last_session_at is not null and sig.last_session_at < now() - interval '7 days' then
          'A última execução ocorreu há mais de 7 dias.'
        when sig.adherence < 70 then
          'A aderência está abaixo de 70% e merece acompanhamento antes de mudanças de prescrição.'
        when sig.adherence >= 80 and sig.completed_30d >= 3 then
          'Aderência alta e execuções concluídas tornam razoável revisar progressão no Decision Intelligence.'
        else
          'Os sinais atuais favorecem continuidade e acompanhamento normal.'
      end as action_reason,
      case
        when sig.feedback_id is not null and sig.pain_score >= 4 then 'feedback'
        when sig.active_plan_id is null then 'training'
        when sig.active_access_id is null then 'access'
        when sig.unresolved_decision_run_id is not null then 'intelligence'
        when sig.adherence >= 80 and sig.completed_30d >= 3 then 'intelligence'
        else 'progress'
      end as target,
      encode(
        extensions.digest(
          concat_ws(
            '|',
            sig.student_id::text,
            case
              when sig.feedback_id is not null and sig.pain_score >= 7 then 'feedback_priority_review'
              when sig.feedback_id is not null and sig.perceived_exertion >= 9 and sig.energy_score <= 2 then 'recovery_priority_review'
              when sig.last_session_at is not null and sig.last_session_at < now() - interval '14 days' then 'reengagement_contact'
              when sig.sessions_30d > 0 and sig.adherence < 40 then 'adherence_recovery'
              when sig.feedback_id is not null and sig.pain_score >= 4 then 'discomfort_review'
              when sig.active_plan_id is null then 'create_first_training'
              when sig.active_access_id is null then 'issue_student_access'
              when sig.sessions_30d = 0 then 'first_execution_followup'
              when sig.unresolved_decision_run_id is not null then 'review_decision_brief'
              when sig.last_session_at is not null and sig.last_session_at < now() - interval '7 days' then 'reengagement_check'
              when sig.adherence < 70 then 'adherence_check'
              when sig.adherence >= 80 and sig.completed_30d >= 3 then 'progression_review'
              else 'maintain_monitoring'
            end,
            coalesce(sig.feedback_id::text, ''),
            coalesce(sig.last_session_at::text, ''),
            sig.adherence::text,
            coalesce(sig.active_plan_id::text, ''),
            coalesce(sig.active_access_id::text, ''),
            coalesce(sig.unresolved_decision_run_id::text, '')
          ),
          'sha256'
        ),
        'hex'
      ) as action_fingerprint
    from signals sig
  ),
  visible as (
    select c.*
    from classified c
    left join lateral (
      select e.resolution, e.snooze_until, e.created_at
      from public.coach_action_events e
      where e.organization_id = p_organization_id
        and e.student_id = c.student_id
        and e.action_fingerprint = c.action_fingerprint
      order by e.created_at desc
      limit 1
    ) event on true
    where not coalesce(
      event.resolution = 'completed'
      and event.created_at >= now() - interval '24 hours',
      false
    )
    and not coalesce(
      event.resolution = 'snoozed'
      and event.snooze_until > now(),
      false
    )
  )
  select coalesce(
    jsonb_agg(
      jsonb_build_object(
        'student_id', v.student_id,
        'student_name', v.name,
        'objective', v.objective,
        'level', v.level,
        'student_status', v.status,
        'adherence', v.adherence,
        'sessions_30d', v.sessions_30d,
        'completed_30d', v.completed_30d,
        'last_session_at', v.last_session_at,
        'priority_score', v.priority_score,
        'priority_label', v.priority_label,
        'action_type', v.action_type,
        'action_title', v.action_title,
        'action_reason', v.action_reason,
        'target', v.target,
        'action_fingerprint', v.action_fingerprint,
        'evidence', jsonb_strip_nulls(jsonb_build_object(
          'pain_score', v.pain_score,
          'pain_location', v.pain_location,
          'perceived_exertion', v.perceived_exertion,
          'energy_score', v.energy_score,
          'feedback_submitted_at', v.feedback_submitted_at,
          'active_plan_id', v.active_plan_id,
          'active_plan_name', v.active_plan_name,
          'has_active_access', (v.active_access_id is not null),
          'unresolved_decision_run_id', v.unresolved_decision_run_id,
          'unresolved_decision_created_at', v.unresolved_decision_created_at
        )),
        'guardrails', jsonb_build_object(
          'auto_execute', false,
          'auto_contact_student', false,
          'auto_change_prescription', false,
          'human_action_required', true
        )
      ) order by v.priority_score desc, v.adherence asc, v.name asc
    ),
    '[]'::jsonb
  ) into v_actions
  from visible v;

  select count(*)::int
    into v_completed_today
  from public.coach_action_events e
  where e.organization_id = p_organization_id
    and e.resolution = 'completed'
    and e.created_at >= date_trunc('day', now());

  select count(*)::int
    into v_snoozed
  from public.coach_action_events e
  where e.organization_id = p_organization_id
    and e.resolution = 'snoozed'
    and e.snooze_until > now();

  select jsonb_build_object(
    'active_actions', count(*)::int,
    'urgent', count(*) filter (where item ->> 'priority_label' = 'urgent')::int,
    'attention', count(*) filter (where item ->> 'priority_label' = 'attention')::int,
    'setup', count(*) filter (where item ->> 'priority_label' = 'setup')::int,
    'monitor', count(*) filter (where item ->> 'priority_label' = 'monitor')::int,
    'completed_today', v_completed_today,
    'snoozed', v_snoozed
  ) into v_summary
  from jsonb_array_elements(v_actions) item;

  return jsonb_build_object(
    'summary', v_summary,
    'actions', v_actions,
    'principle', 'O FitNexus prioriza e explica; o professor decide e executa.',
    'generated_at', now()
  );
end;
$$;

revoke execute on function public.get_coach_action_center(uuid) from public, anon;
grant execute on function public.get_coach_action_center(uuid) to authenticated;
