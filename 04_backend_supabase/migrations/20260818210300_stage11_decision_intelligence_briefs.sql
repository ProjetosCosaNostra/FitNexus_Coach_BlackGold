create table if not exists public.decision_intelligence_runs (
  id uuid primary key default extensions.gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  student_id uuid not null,
  engine_version text not null,
  brief jsonb not null,
  created_by uuid not null,
  created_at timestamptz not null default now(),
  constraint decision_intelligence_runs_student_org_fk
    foreign key (student_id, organization_id)
    references public.students(id, organization_id)
    on delete cascade
);

create index if not exists decision_intelligence_runs_org_student_created_idx
  on public.decision_intelligence_runs(organization_id, student_id, created_at desc);

create index if not exists decision_intelligence_runs_student_org_fk_idx
  on public.decision_intelligence_runs(student_id, organization_id);

alter table public.decision_intelligence_runs enable row level security;

revoke all on public.decision_intelligence_runs from anon, authenticated;
grant select, insert on public.decision_intelligence_runs to authenticated;

drop policy if exists decision_intelligence_runs_select_org on public.decision_intelligence_runs;
create policy decision_intelligence_runs_select_org
on public.decision_intelligence_runs
for select to authenticated
using ((select private.is_org_member(organization_id)));

drop policy if exists decision_intelligence_runs_insert_manager on public.decision_intelligence_runs;
create policy decision_intelligence_runs_insert_manager
on public.decision_intelligence_runs
for insert to authenticated
with check (
  (select private.is_org_manager(organization_id))
  and created_by = auth.uid()
);

create or replace function public.generate_decision_intelligence_brief(p_student_id uuid)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_student record;
  v_plan record;
  v_latest_feedback record;
  v_latest_lineage record;
  v_template record;
  v_plan_exercises jsonb := '[]'::jsonb;
  v_template_exercises jsonb := '[]'::jsonb;
  v_preview jsonb := null;
  v_sessions_30d integer := 0;
  v_completed_30d integer := 0;
  v_last_session_at timestamptz := null;
  v_feedback_age_days integer := null;
  v_risk_level text := 'low';
  v_recommendation_type text := 'maintain_and_monitor';
  v_recommendation_title text := 'Manter e acompanhar';
  v_recommendation_reason text := 'Os sinais atuais não indicam necessidade de alterar a prescrição automaticamente.';
  v_confidence integer := 35;
  v_candidate_allowed boolean := false;
  v_candidate_block_reason text := null;
  v_evidence jsonb := '[]'::jsonb;
  v_candidate jsonb := null;
  v_brief jsonb;
  v_run_id uuid;
  v_engine_version constant text := 'blackgold_deterministic_v1';
begin
  if auth.uid() is null then
    raise exception using errcode = '42501', message = 'AUTH_REQUIRED';
  end if;

  select s.* into v_student
  from public.students s
  where s.id = p_student_id;

  if v_student.id is null then
    raise exception using errcode = 'P0002', message = 'STUDENT_NOT_FOUND';
  end if;

  if not private.is_org_manager(v_student.organization_id) then
    raise exception using errcode = '42501', message = 'ORG_MANAGER_REQUIRED';
  end if;

  select p.* into v_plan
  from public.training_plans p
  where p.student_id = v_student.id
    and p.organization_id = v_student.organization_id
    and p.is_active
  order by p.updated_at desc
  limit 1;

  if v_plan.id is not null then
    select coalesce(
      jsonb_agg(
        jsonb_build_object(
          'name', e.name,
          'prescription', e.prescription,
          'position', e.position
        ) order by e.position
      ),
      '[]'::jsonb
    ) into v_plan_exercises
    from public.training_exercises e
    where e.training_plan_id = v_plan.id
      and e.organization_id = v_student.organization_id;

    v_confidence := v_confidence + 20;
  end if;

  select
    count(ws.id) filter (
      where ws.started_at >= now() - interval '30 days'
        and ws.status <> 'cancelled'
    )::int,
    count(ws.id) filter (
      where ws.started_at >= now() - interval '30 days'
        and ws.status = 'completed'
    )::int,
    max(ws.started_at) filter (where ws.status <> 'cancelled')
  into v_sessions_30d, v_completed_30d, v_last_session_at
  from public.workout_sessions ws
  where ws.student_id = v_student.id
    and ws.organization_id = v_student.organization_id;

  if v_sessions_30d >= 2 then
    v_confidence := v_confidence + 15;
  elsif v_sessions_30d = 1 then
    v_confidence := v_confidence + 8;
  end if;

  select wf.* into v_latest_feedback
  from public.workout_feedback wf
  where wf.student_id = v_student.id
    and wf.organization_id = v_student.organization_id
  order by wf.submitted_at desc
  limit 1;

  if v_latest_feedback.id is not null then
    v_feedback_age_days := greatest(0, floor(extract(epoch from (now() - v_latest_feedback.submitted_at)) / 86400)::int);
    if v_feedback_age_days <= 7 then
      v_confidence := v_confidence + 20;
    elsif v_feedback_age_days <= 14 then
      v_confidence := v_confidence + 12;
    else
      v_confidence := v_confidence + 5;
    end if;
  end if;

  v_confidence := v_confidence + 10;

  if v_latest_feedback.id is not null and v_latest_feedback.pain_score >= 7 then
    v_risk_level := 'high';
    v_recommendation_type := 'priority_human_review';
    v_recommendation_title := 'Revisão prioritária antes de progredir';
    v_recommendation_reason := 'O último feedback registrou dor ou desconforto alto. O FitNexus bloqueia sugestão automática de nova prescrição e prioriza revisão humana.';
    v_candidate_block_reason := 'HIGH_PAIN_REQUIRES_HUMAN_REVIEW';
  elsif v_latest_feedback.id is not null
      and v_latest_feedback.perceived_exertion >= 9
      and v_latest_feedback.energy_score <= 2 then
    v_risk_level := 'high';
    v_recommendation_type := 'recovery_review';
    v_recommendation_title := 'Revisar carga percebida e recuperação';
    v_recommendation_reason := 'Esforço muito alto combinado com baixa energia pede revisão do professor antes de qualquer progressão.';
    v_candidate_block_reason := 'RECOVERY_SIGNAL_REQUIRES_HUMAN_REVIEW';
  elsif (v_last_session_at is not null and v_last_session_at < now() - interval '14 days')
      or v_student.adherence < 40 then
    v_risk_level := 'high';
    v_recommendation_type := 'engagement_recovery';
    v_recommendation_title := 'Recuperar aderência antes de trocar o treino';
    v_recommendation_reason := 'Baixa aderência ou longa ausência pode ser problema de execução, não necessariamente de prescrição. O motor evita trocar o treino sem contexto humano.';
    v_candidate_block_reason := 'ENGAGEMENT_SIGNAL_REQUIRES_CONTEXT';
  elsif v_latest_feedback.id is not null and v_latest_feedback.pain_score >= 4 then
    v_risk_level := 'medium';
    v_recommendation_type := 'discomfort_review';
    v_recommendation_title := 'Revisar desconforto antes de progredir';
    v_recommendation_reason := 'Há desconforto moderado no feedback recente. O motor mantém a prescrição intacta até revisão do professor.';
    v_candidate_block_reason := 'MODERATE_PAIN_REQUIRES_REVIEW';
  elsif v_latest_feedback.id is not null
      and (v_latest_feedback.perceived_exertion >= 9 or v_latest_feedback.energy_score <= 2) then
    v_risk_level := 'medium';
    v_recommendation_type := 'recovery_check';
    v_recommendation_title := 'Validar recuperação antes da progressão';
    v_recommendation_reason := 'O feedback sugere esforço alto ou energia baixa. O professor deve validar o contexto antes de editar a prescrição.';
    v_candidate_block_reason := 'RECOVERY_CHECK_REQUIRED';
  elsif (v_last_session_at is not null and v_last_session_at < now() - interval '7 days')
      or v_student.adherence < 70 then
    v_risk_level := 'medium';
    v_recommendation_type := 'engagement_check';
    v_recommendation_title := 'Checar aderência e barreiras';
    v_recommendation_reason := 'O principal sinal é aderência intermediária ou pausa recente; a próxima ação recomendada é entender barreiras antes de mudar exercícios.';
    v_candidate_block_reason := 'ENGAGEMENT_CHECK_REQUIRED';
  elsif v_plan.id is null then
    v_risk_level := 'new';
    v_recommendation_type := 'initial_prescription_needed';
    v_recommendation_title := 'Criar primeira prescrição';
    v_recommendation_reason := 'O aluno ainda não possui treino ativo. O professor deve criar a prescrição inicial.';
    v_candidate_allowed := true;
  elsif v_student.adherence >= 80 and v_completed_30d >= 3 then
    v_risk_level := 'low';
    v_recommendation_type := 'progression_candidate';
    v_recommendation_title := 'Elegível para revisar progressão';
    v_recommendation_reason := 'Aderência alta, execuções concluídas e ausência de sinais de alerta tornam razoável comparar uma alternativa profissional antes de decidir.';
    v_candidate_allowed := true;
  else
    v_risk_level := 'low';
    v_recommendation_type := 'maintain_and_monitor';
    v_recommendation_title := 'Manter e acompanhar';
    v_recommendation_reason := 'Os sinais atuais favorecem continuidade e observação. Nenhuma troca de prescrição é sugerida.';
    v_candidate_block_reason := 'NO_CHANGE_SIGNAL';
  end if;

  select l.* into v_latest_lineage
  from public.training_plan_lineage l
  where l.student_id = v_student.id
    and l.organization_id = v_student.organization_id
    and l.plan_id = v_plan.id
  order by l.created_at desc
  limit 1;

  if v_candidate_allowed then
    select t.* into v_template
    from public.training_templates t
    where t.organization_id = v_student.organization_id
      and t.is_active
      and lower(btrim(t.objective)) = lower(btrim(coalesce(v_student.objective, 'Geral')))
      and lower(btrim(t.level)) = lower(btrim(coalesce(v_student.level, 'Iniciante')))
      and (v_latest_lineage.source_template_id is null or t.id <> v_latest_lineage.source_template_id)
    order by t.updated_at desc, t.created_at desc
    limit 1;

    if v_template.id is not null then
      select coalesce(
        jsonb_agg(
          jsonb_build_object(
            'name', e.name,
            'prescription', e.prescription
          ) order by e.position
        ),
        '[]'::jsonb
      ) into v_template_exercises
      from public.training_template_exercises e
      where e.template_id = v_template.id
        and e.organization_id = v_student.organization_id;

      if jsonb_array_length(v_template_exercises) > 0 then
        if v_plan.id is not null then
          v_preview := public.preview_training_plan_change(v_student.id, v_template_exercises);
        else
          v_preview := jsonb_build_object(
            'has_previous_plan', false,
            'active_plan_id', null,
            'active_plan_name', null,
            'added', v_template_exercises,
            'removed', '[]'::jsonb,
            'changed', '[]'::jsonb
          );
        end if;
        v_confidence := v_confidence + 10;
        v_candidate := jsonb_build_object(
          'candidate_type', 'smart_template',
          'template_id', v_template.id,
          'template_name', v_template.name,
          'objective', v_template.objective,
          'level', v_template.level,
          'proposed_exercises', v_template_exercises,
          'proposed_diff', v_preview,
          'auto_apply', false,
          'requires_professor_preview', true,
          'requires_professor_confirmation', true
        );
      else
        v_candidate_block_reason := 'MATCHING_TEMPLATE_EMPTY';
      end if;
    else
      v_candidate_block_reason := coalesce(v_candidate_block_reason, 'NO_MATCHING_PROFESSIONAL_TEMPLATE');
    end if;
  end if;

  v_confidence := least(95, greatest(0, v_confidence));

  v_evidence := jsonb_build_array(
    jsonb_build_object(
      'type', 'adherence',
      'label', 'Aderência atual',
      'value', v_student.adherence,
      'unit', '%'
    ),
    jsonb_build_object(
      'type', 'sessions_30d',
      'label', 'Sessões nos últimos 30 dias',
      'value', v_sessions_30d
    ),
    jsonb_build_object(
      'type', 'completed_30d',
      'label', 'Sessões concluídas nos últimos 30 dias',
      'value', v_completed_30d
    ),
    jsonb_build_object(
      'type', 'last_session_at',
      'label', 'Última execução',
      'value', v_last_session_at
    ),
    jsonb_build_object(
      'type', 'latest_feedback',
      'label', 'Último feedback',
      'value', case when v_latest_feedback.id is null then null else jsonb_build_object(
        'pain_score', v_latest_feedback.pain_score,
        'perceived_exertion', v_latest_feedback.perceived_exertion,
        'energy_score', v_latest_feedback.energy_score,
        'submitted_at', v_latest_feedback.submitted_at,
        'age_days', v_feedback_age_days
      ) end
    ),
    jsonb_build_object(
      'type', 'active_plan',
      'label', 'Treino ativo',
      'value', case when v_plan.id is null then null else jsonb_build_object(
        'plan_id', v_plan.id,
        'plan_name', v_plan.name,
        'exercise_count', jsonb_array_length(v_plan_exercises)
      ) end
    )
  );

  v_brief := jsonb_build_object(
    'engine', jsonb_build_object(
      'version', v_engine_version,
      'mode', 'deterministic_fallback',
      'external_model_required', false
    ),
    'student', jsonb_build_object(
      'student_id', v_student.id,
      'name', v_student.name,
      'objective', v_student.objective,
      'level', v_student.level,
      'adherence', v_student.adherence
    ),
    'risk', jsonb_build_object(
      'level', v_risk_level,
      'source', 'rule_engine_v1'
    ),
    'confidence', jsonb_build_object(
      'score', v_confidence,
      'label', case
        when v_confidence >= 80 then 'high'
        when v_confidence >= 60 then 'medium'
        else 'low'
      end,
      'meaning', 'Confiança na recomendação de próxima ação, não autorização para alterar prescrição.'
    ),
    'recommendation', jsonb_build_object(
      'type', v_recommendation_type,
      'title', v_recommendation_title,
      'reason', v_recommendation_reason
    ),
    'evidence', v_evidence,
    'candidate', v_candidate,
    'candidate_block_reason', v_candidate_block_reason,
    'guardrails', jsonb_build_object(
      'auto_apply', false,
      'silent_prescription_change', false,
      'human_review_required', true,
      'decision_studio_required_for_commit', true,
      'medical_diagnosis', false
    ),
    'generated_at', now()
  );

  insert into public.decision_intelligence_runs (
    organization_id,
    student_id,
    engine_version,
    brief,
    created_by
  ) values (
    v_student.organization_id,
    v_student.id,
    v_engine_version,
    v_brief,
    auth.uid()
  ) returning id into v_run_id;

  return v_brief || jsonb_build_object('run_id', v_run_id);
end;
$$;

revoke execute on function public.generate_decision_intelligence_brief(uuid) from public, anon;
grant execute on function public.generate_decision_intelligence_brief(uuid) to authenticated;

create or replace function public.get_decision_intelligence_history(
  p_student_id uuid,
  p_limit integer default 10
)
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

  select s.organization_id into v_org
  from public.students s
  where s.id = p_student_id;

  if v_org is null then
    raise exception using errcode = 'P0002', message = 'STUDENT_NOT_FOUND';
  end if;

  if not private.is_org_member(v_org) then
    raise exception using errcode = '42501', message = 'ORG_MEMBER_REQUIRED';
  end if;

  select coalesce(
    jsonb_agg(
      jsonb_build_object(
        'run_id', r.id,
        'engine_version', r.engine_version,
        'brief', r.brief,
        'created_at', r.created_at
      ) order by r.created_at desc
    ),
    '[]'::jsonb
  ) into v_items
  from (
    select *
    from public.decision_intelligence_runs
    where organization_id = v_org
      and student_id = p_student_id
    order by created_at desc
    limit least(greatest(coalesce(p_limit, 10), 1), 50)
  ) r;

  return jsonb_build_object(
    'student_id', p_student_id,
    'items', v_items,
    'generated_at', now()
  );
end;
$$;

revoke execute on function public.get_decision_intelligence_history(uuid,integer) from public, anon;
grant execute on function public.get_decision_intelligence_history(uuid,integer) to authenticated;
