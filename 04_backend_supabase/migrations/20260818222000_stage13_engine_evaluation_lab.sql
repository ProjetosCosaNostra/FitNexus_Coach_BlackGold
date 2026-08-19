create table if not exists public.decision_engine_registry (
  engine_version text primary key,
  engine_role text not null check (engine_role in ('champion','challenger','retired')),
  lifecycle text not null check (lifecycle in ('active','lab_only','retired')),
  description text not null,
  ruleset jsonb not null default '{}'::jsonb check (jsonb_typeof(ruleset) = 'object'),
  created_at timestamptz not null default now()
);

create unique index if not exists decision_engine_single_active_champion_idx
  on public.decision_engine_registry ((1))
  where engine_role = 'champion' and lifecycle = 'active';

alter table public.decision_engine_registry enable row level security;
revoke all on public.decision_engine_registry from anon, authenticated;
grant select on public.decision_engine_registry to authenticated;

drop policy if exists decision_engine_registry_authenticated_read on public.decision_engine_registry;
create policy decision_engine_registry_authenticated_read
on public.decision_engine_registry
for select to authenticated
using ((select auth.uid()) is not null);

insert into public.decision_engine_registry (
  engine_version, engine_role, lifecycle, description, ruleset
) values
(
  'blackgold_deterministic_v1',
  'champion',
  'active',
  'Motor determinístico de produção do Decision Intelligence.',
  jsonb_build_object(
    'risk_policy', 'rule_engine_v1',
    'external_model_required', false,
    'auto_apply', false,
    'human_confirmation_required', true
  )
),
(
  'blackgold_deterministic_v1_1_shadow',
  'challenger',
  'lab_only',
  'Challenger conservador: exige evidência recente antes de sugerir progressão e recalibra confiança sem afetar produção.',
  jsonb_build_object(
    'risk_policy', 'rule_engine_v1_1_shadow',
    'external_model_required', false,
    'auto_apply', false,
    'shadow_only', true,
    'fresh_feedback_required_for_progression', true,
    'human_confirmation_required', true
  )
)
on conflict (engine_version) do update
set description = excluded.description,
    ruleset = excluded.ruleset;

create table if not exists public.decision_engine_evaluation_runs (
  id uuid primary key default extensions.gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  champion_version text not null references public.decision_engine_registry(engine_version) on delete restrict,
  challenger_version text not null references public.decision_engine_registry(engine_version) on delete restrict,
  status text not null check (status in (
    'running',
    'blocked_insufficient_evidence',
    'blocked_safety_regression',
    'blocked_no_alignment_uplift',
    'eligible_for_engineering_review',
    'failed'
  )),
  case_count integer not null default 0 check (case_count >= 0),
  resolved_count integer not null default 0 check (resolved_count >= 0),
  champion_alignment_rate numeric(6,2) not null default 0,
  challenger_alignment_rate numeric(6,2) not null default 0,
  alignment_uplift numeric(7,2) not null default 0,
  recommendation_changes integer not null default 0 check (recommendation_changes >= 0),
  risk_changes integer not null default 0 check (risk_changes >= 0),
  safety_downgrades integer not null default 0 check (safety_downgrades >= 0),
  unsafe_actionability_conflicts integer not null default 0 check (unsafe_actionability_conflicts >= 0),
  report jsonb not null default '{}'::jsonb check (jsonb_typeof(report) = 'object'),
  origin text not null check (origin in ('interactive','migration_bootstrap','scheduled')),
  requested_by uuid,
  created_at timestamptz not null default now(),
  completed_at timestamptz
);

create index if not exists decision_engine_evaluation_runs_org_created_idx
  on public.decision_engine_evaluation_runs(organization_id, created_at desc);
create index if not exists decision_engine_evaluation_runs_champion_fk_idx
  on public.decision_engine_evaluation_runs(champion_version);
create index if not exists decision_engine_evaluation_runs_challenger_fk_idx
  on public.decision_engine_evaluation_runs(challenger_version);

alter table public.decision_engine_evaluation_runs enable row level security;
revoke all on public.decision_engine_evaluation_runs from anon, authenticated;
grant select on public.decision_engine_evaluation_runs to authenticated;

drop policy if exists decision_engine_evaluation_runs_select_org on public.decision_engine_evaluation_runs;
create policy decision_engine_evaluation_runs_select_org
on public.decision_engine_evaluation_runs
for select to authenticated
using ((select private.is_org_member(organization_id)));

create table if not exists public.decision_engine_evaluation_cases (
  id uuid primary key default extensions.gen_random_uuid(),
  evaluation_run_id uuid not null references public.decision_engine_evaluation_runs(id) on delete cascade,
  organization_id uuid not null references public.organizations(id) on delete cascade,
  source_run_id uuid not null references public.decision_intelligence_runs(id) on delete restrict,
  student_id uuid not null,
  human_outcome text check (human_outcome is null or human_outcome in ('accepted','modified','rejected','no_action')),
  champion_output jsonb not null check (jsonb_typeof(champion_output) = 'object'),
  challenger_output jsonb not null check (jsonb_typeof(challenger_output) = 'object'),
  recommendation_changed boolean not null,
  risk_changed boolean not null,
  risk_downgrade boolean not null,
  unsafe_actionability_conflict boolean not null,
  champion_aligned_with_human boolean,
  challenger_aligned_with_human boolean,
  created_at timestamptz not null default now(),
  constraint decision_engine_evaluation_cases_student_org_fk
    foreign key (student_id, organization_id)
    references public.students(id, organization_id)
    on delete cascade,
  constraint decision_engine_evaluation_cases_run_source_unique
    unique (evaluation_run_id, source_run_id)
);

create index if not exists decision_engine_evaluation_cases_run_idx
  on public.decision_engine_evaluation_cases(evaluation_run_id);
create index if not exists decision_engine_evaluation_cases_source_idx
  on public.decision_engine_evaluation_cases(source_run_id);
create index if not exists decision_engine_evaluation_cases_student_org_fk_idx
  on public.decision_engine_evaluation_cases(student_id, organization_id);
create index if not exists decision_engine_evaluation_cases_org_created_idx
  on public.decision_engine_evaluation_cases(organization_id, created_at desc);

alter table public.decision_engine_evaluation_cases enable row level security;
revoke all on public.decision_engine_evaluation_cases from anon, authenticated;
grant select on public.decision_engine_evaluation_cases to authenticated;

drop policy if exists decision_engine_evaluation_cases_select_org on public.decision_engine_evaluation_cases;
create policy decision_engine_evaluation_cases_select_org
on public.decision_engine_evaluation_cases
for select to authenticated
using ((select private.is_org_member(organization_id)));

create table if not exists public.decision_engine_promotion_packets (
  id uuid primary key default extensions.gen_random_uuid(),
  evaluation_run_id uuid not null unique references public.decision_engine_evaluation_runs(id) on delete cascade,
  organization_id uuid not null references public.organizations(id) on delete cascade,
  challenger_version text not null references public.decision_engine_registry(engine_version) on delete restrict,
  gate_status text not null check (gate_status in (
    'blocked_insufficient_evidence',
    'blocked_safety_regression',
    'blocked_no_alignment_uplift',
    'eligible_for_engineering_review'
  )),
  packet jsonb not null check (jsonb_typeof(packet) = 'object'),
  requested_by uuid,
  created_at timestamptz not null default now()
);

create index if not exists decision_engine_promotion_packets_org_created_idx
  on public.decision_engine_promotion_packets(organization_id, created_at desc);
create index if not exists decision_engine_promotion_packets_challenger_fk_idx
  on public.decision_engine_promotion_packets(challenger_version);

alter table public.decision_engine_promotion_packets enable row level security;
revoke all on public.decision_engine_promotion_packets from anon, authenticated;
grant select on public.decision_engine_promotion_packets to authenticated;

drop policy if exists decision_engine_promotion_packets_select_org on public.decision_engine_promotion_packets;
create policy decision_engine_promotion_packets_select_org
on public.decision_engine_promotion_packets
for select to authenticated
using ((select private.is_org_member(organization_id)));

create or replace function private.decision_evidence_value(
  p_brief jsonb,
  p_type text
)
returns jsonb
language sql
immutable
set search_path = ''
as $$
  select item -> 'value'
  from jsonb_array_elements(coalesce(p_brief -> 'evidence', '[]'::jsonb)) item
  where item ->> 'type' = p_type
  limit 1;
$$;

revoke all on function private.decision_evidence_value(jsonb,text) from public, anon, authenticated;
grant execute on function private.decision_evidence_value(jsonb,text) to authenticated;

create or replace function private.decision_risk_rank(p_level text)
returns integer
language sql
immutable
set search_path = ''
as $$
  select case coalesce(p_level, 'new')
    when 'high' then 3
    when 'medium' then 2
    when 'low' then 1
    else 0
  end;
$$;

revoke all on function private.decision_risk_rank(text) from public, anon, authenticated;
grant execute on function private.decision_risk_rank(text) to authenticated;

create or replace function private.evaluate_decision_engine_snapshot(
  p_brief jsonb,
  p_engine_version text
)
returns jsonb
language plpgsql
immutable
set search_path = ''
as $$
declare
  v_adherence integer := coalesce((p_brief #>> '{student,adherence}')::integer, 0);
  v_sessions_30d integer := coalesce((private.decision_evidence_value(p_brief, 'sessions_30d') #>> '{}')::integer, 0);
  v_completed_30d integer := coalesce((private.decision_evidence_value(p_brief, 'completed_30d') #>> '{}')::integer, 0);
  v_feedback jsonb := private.decision_evidence_value(p_brief, 'latest_feedback');
  v_active_plan jsonb := private.decision_evidence_value(p_brief, 'active_plan');
  v_last_session_raw text := private.decision_evidence_value(p_brief, 'last_session_at') #>> '{}';
  v_generated_raw text := p_brief ->> 'generated_at';
  v_feedback_age integer := null;
  v_pain integer := null;
  v_effort integer := null;
  v_energy integer := null;
  v_last_session_age integer := null;
  v_generated_at timestamptz := null;
  v_last_session_at timestamptz := null;
  v_risk text := 'low';
  v_recommendation text := 'maintain_and_monitor';
  v_confidence integer := 30;
  v_actionable boolean := false;
  v_candidate_available boolean := false;
  v_reason text := 'Os sinais atuais favorecem manutenção e acompanhamento.';
begin
  if p_engine_version = 'blackgold_deterministic_v1' then
    return jsonb_build_object(
      'engine_version', p_engine_version,
      'risk_level', coalesce(p_brief #>> '{risk,level}', 'new'),
      'recommendation_type', coalesce(p_brief #>> '{recommendation,type}', 'maintain_and_monitor'),
      'confidence_score', coalesce((p_brief #>> '{confidence,score}')::integer, 0),
      'actionable', p_brief -> 'candidate' is not null and jsonb_typeof(p_brief -> 'candidate') = 'object',
      'candidate_available', p_brief -> 'candidate' is not null and jsonb_typeof(p_brief -> 'candidate') = 'object',
      'shadow_only', false,
      'source', 'stored_champion_brief'
    );
  end if;

  if p_engine_version <> 'blackgold_deterministic_v1_1_shadow' then
    raise exception using errcode = '22023', message = 'DECISION_ENGINE_VERSION_NOT_IMPLEMENTED';
  end if;

  if v_feedback is not null and jsonb_typeof(v_feedback) = 'object' then
    v_feedback_age := nullif(v_feedback ->> 'age_days', '')::integer;
    v_pain := nullif(v_feedback ->> 'pain_score', '')::integer;
    v_effort := nullif(v_feedback ->> 'perceived_exertion', '')::integer;
    v_energy := nullif(v_feedback ->> 'energy_score', '')::integer;
  end if;

  if nullif(v_generated_raw, '') is not null then
    v_generated_at := v_generated_raw::timestamptz;
  end if;
  if nullif(v_last_session_raw, '') is not null then
    v_last_session_at := v_last_session_raw::timestamptz;
  end if;
  if v_generated_at is not null and v_last_session_at is not null then
    v_last_session_age := greatest(
      0,
      floor(extract(epoch from (v_generated_at - v_last_session_at)) / 86400)::integer
    );
  end if;

  if v_active_plan is not null and jsonb_typeof(v_active_plan) = 'object' then
    v_confidence := v_confidence + 15;
  end if;
  if v_sessions_30d >= 2 then
    v_confidence := v_confidence + 15;
  elsif v_sessions_30d = 1 then
    v_confidence := v_confidence + 8;
  end if;
  if v_feedback is not null and jsonb_typeof(v_feedback) = 'object' then
    if coalesce(v_feedback_age, 999) <= 7 then
      v_confidence := v_confidence + 20;
    elsif coalesce(v_feedback_age, 999) <= 14 then
      v_confidence := v_confidence + 10;
    end if;
  end if;
  v_confidence := v_confidence + 10;
  if v_completed_30d >= 3 then
    v_confidence := v_confidence + 5;
  end if;
  if v_last_session_age is not null and v_last_session_age <= 7 then
    v_confidence := v_confidence + 5;
  end if;

  if coalesce(v_pain, 0) >= 7 then
    v_risk := 'high';
    v_recommendation := 'priority_human_review';
    v_reason := 'Dor/desconforto alto exige revisão humana prioritária.';
  elsif coalesce(v_effort, 0) >= 9 and coalesce(v_energy, 5) <= 2 then
    v_risk := 'high';
    v_recommendation := 'recovery_review';
    v_reason := 'Esforço muito alto com energia baixa exige revisão de recuperação.';
  elsif (v_last_session_age is not null and v_last_session_age > 14) or v_adherence < 40 then
    v_risk := 'high';
    v_recommendation := 'engagement_recovery';
    v_reason := 'Baixa aderência ou ausência prolongada exige recuperação de continuidade.';
  elsif coalesce(v_pain, 0) >= 4 then
    v_risk := 'medium';
    v_recommendation := 'discomfort_review';
    v_reason := 'Desconforto moderado deve ser revisado antes de progressão.';
  elsif coalesce(v_effort, 0) >= 9 or coalesce(v_energy, 5) <= 2 then
    v_risk := 'medium';
    v_recommendation := 'recovery_check';
    v_reason := 'Esforço alto ou energia baixa pede validação de recuperação.';
  elsif (v_last_session_age is not null and v_last_session_age > 7) or v_adherence < 70 then
    v_risk := 'medium';
    v_recommendation := 'engagement_check';
    v_reason := 'Aderência intermediária ou pausa recente pede investigação de barreiras.';
  elsif v_active_plan is null or jsonb_typeof(v_active_plan) <> 'object' then
    v_risk := 'new';
    v_recommendation := 'initial_prescription_needed';
    v_reason := 'Não há treino ativo; a decisão profissional deve criar a prescrição inicial.';
    v_actionable := true;
  elsif v_adherence >= 80 and v_completed_30d >= 3 then
    if v_feedback is null
       or jsonb_typeof(v_feedback) <> 'object'
       or coalesce(v_feedback_age, 999) > 14 then
      v_risk := 'medium';
      v_recommendation := 'evidence_refresh_before_progression';
      v_reason := 'Aderência e execução permitem considerar progressão, mas o feedback está ausente ou antigo demais para liberar candidato sombra.';
      v_actionable := false;
    else
      v_risk := 'low';
      v_recommendation := 'progression_candidate';
      v_reason := 'Aderência, execuções e feedback recente sustentam comparação de uma alternativa profissional.';
      v_actionable := true;
    end if;
  else
    v_risk := 'low';
    v_recommendation := 'maintain_and_monitor';
    v_reason := 'Os sinais atuais favorecem manutenção e observação.';
  end if;

  v_confidence := least(90, greatest(0, v_confidence));
  v_candidate_available := v_actionable;

  return jsonb_build_object(
    'engine_version', p_engine_version,
    'risk_level', v_risk,
    'recommendation_type', v_recommendation,
    'confidence_score', v_confidence,
    'actionable', v_actionable,
    'candidate_available', v_candidate_available,
    'shadow_only', true,
    'reason', v_reason,
    'evidence_freshness', jsonb_build_object(
      'feedback_age_days', v_feedback_age,
      'last_session_age_days', v_last_session_age
    ),
    'guardrails', jsonb_build_object(
      'auto_apply', false,
      'production_influence', false,
      'human_confirmation_required', true
    )
  );
end;
$$;

revoke all on function private.evaluate_decision_engine_snapshot(jsonb,text) from public, anon, authenticated;
grant execute on function private.evaluate_decision_engine_snapshot(jsonb,text) to authenticated;

create or replace function private.run_decision_engine_evaluation_internal(
  p_organization_id uuid,
  p_challenger_version text,
  p_requested_by uuid,
  p_origin text
)
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_champion_version text;
  v_evaluation_id uuid;
  v_case_count integer := 0;
  v_resolved_count integer := 0;
  v_recommendation_changes integer := 0;
  v_risk_changes integer := 0;
  v_safety_downgrades integer := 0;
  v_unsafe_conflicts integer := 0;
  v_champion_aligned integer := 0;
  v_challenger_aligned integer := 0;
  v_champion_rate numeric(6,2) := 0;
  v_challenger_rate numeric(6,2) := 0;
  v_uplift numeric(7,2) := 0;
  v_status text := 'running';
  v_report jsonb := '{}'::jsonb;
  v_champion jsonb;
  v_challenger jsonb;
  v_human_outcome text;
  v_rec_changed boolean;
  v_risk_changed boolean;
  v_risk_downgrade boolean;
  v_unsafe_conflict boolean;
  v_champion_human boolean;
  v_challenger_human boolean;
  v_champion_actionable boolean;
  v_challenger_actionable boolean;
  v_packet jsonb;
  r record;
begin
  if p_origin not in ('interactive','migration_bootstrap','scheduled') then
    raise exception using errcode = '22023', message = 'ENGINE_EVALUATION_ORIGIN_INVALID';
  end if;

  select engine_version into v_champion_version
  from public.decision_engine_registry
  where engine_role = 'champion' and lifecycle = 'active'
  limit 1;

  if v_champion_version is null then
    raise exception using errcode = 'P0002', message = 'ACTIVE_CHAMPION_NOT_FOUND';
  end if;

  if not exists (
    select 1
    from public.decision_engine_registry
    where engine_version = p_challenger_version
      and engine_role = 'challenger'
      and lifecycle = 'lab_only'
  ) then
    raise exception using errcode = '22023', message = 'LAB_CHALLENGER_NOT_FOUND';
  end if;

  if not exists (
    select 1 from public.organizations o where o.id = p_organization_id
  ) then
    raise exception using errcode = 'P0002', message = 'ORGANIZATION_NOT_FOUND';
  end if;

  insert into public.decision_engine_evaluation_runs (
    organization_id,
    champion_version,
    challenger_version,
    status,
    origin,
    requested_by
  ) values (
    p_organization_id,
    v_champion_version,
    p_challenger_version,
    'running',
    p_origin,
    p_requested_by
  ) returning id into v_evaluation_id;

  for r in
    select dir.id as source_run_id,
           dir.student_id,
           dir.brief,
           dio.outcome as human_outcome
    from public.decision_intelligence_runs dir
    left join public.decision_intelligence_outcomes dio
      on dio.run_id = dir.id
    where dir.organization_id = p_organization_id
    order by dir.created_at desc
    limit 250
  loop
    v_champion := private.evaluate_decision_engine_snapshot(r.brief, v_champion_version);
    v_challenger := private.evaluate_decision_engine_snapshot(r.brief, p_challenger_version);
    v_human_outcome := r.human_outcome;

    v_rec_changed := coalesce(v_champion ->> 'recommendation_type', '')
      <> coalesce(v_challenger ->> 'recommendation_type', '');
    v_risk_changed := coalesce(v_champion ->> 'risk_level', '')
      <> coalesce(v_challenger ->> 'risk_level', '');
    v_risk_downgrade := private.decision_risk_rank(v_challenger ->> 'risk_level')
      < private.decision_risk_rank(v_champion ->> 'risk_level');

    v_champion_actionable := coalesce((v_champion ->> 'actionable')::boolean, false);
    v_challenger_actionable := coalesce((v_challenger ->> 'actionable')::boolean, false);
    v_unsafe_conflict := v_challenger_actionable
      and private.decision_risk_rank(v_champion ->> 'risk_level') >= 2;

    v_champion_human := null;
    v_challenger_human := null;
    if v_human_outcome is not null then
      if v_human_outcome in ('accepted','modified') then
        v_champion_human := v_champion_actionable;
        v_challenger_human := v_challenger_actionable;
      else
        v_champion_human := not v_champion_actionable;
        v_challenger_human := not v_challenger_actionable;
      end if;
    end if;

    insert into public.decision_engine_evaluation_cases (
      evaluation_run_id,
      organization_id,
      source_run_id,
      student_id,
      human_outcome,
      champion_output,
      challenger_output,
      recommendation_changed,
      risk_changed,
      risk_downgrade,
      unsafe_actionability_conflict,
      champion_aligned_with_human,
      challenger_aligned_with_human
    ) values (
      v_evaluation_id,
      p_organization_id,
      r.source_run_id,
      r.student_id,
      v_human_outcome,
      v_champion,
      v_challenger,
      v_rec_changed,
      v_risk_changed,
      v_risk_downgrade,
      v_unsafe_conflict,
      v_champion_human,
      v_challenger_human
    );
  end loop;

  select count(*)::integer,
         count(*) filter (where human_outcome is not null)::integer,
         count(*) filter (where recommendation_changed)::integer,
         count(*) filter (where risk_changed)::integer,
         count(*) filter (where risk_downgrade)::integer,
         count(*) filter (where unsafe_actionability_conflict)::integer,
         count(*) filter (where champion_aligned_with_human is true)::integer,
         count(*) filter (where challenger_aligned_with_human is true)::integer
  into v_case_count,
       v_resolved_count,
       v_recommendation_changes,
       v_risk_changes,
       v_safety_downgrades,
       v_unsafe_conflicts,
       v_champion_aligned,
       v_challenger_aligned
  from public.decision_engine_evaluation_cases
  where evaluation_run_id = v_evaluation_id;

  if v_resolved_count > 0 then
    v_champion_rate := round(100.0 * v_champion_aligned / v_resolved_count, 2);
    v_challenger_rate := round(100.0 * v_challenger_aligned / v_resolved_count, 2);
  end if;
  v_uplift := v_challenger_rate - v_champion_rate;

  v_status := case
    when v_case_count < 20 or v_resolved_count < 12
      then 'blocked_insufficient_evidence'
    when v_safety_downgrades > 0 or v_unsafe_conflicts > 0
      then 'blocked_safety_regression'
    when v_challenger_rate < v_champion_rate
      then 'blocked_no_alignment_uplift'
    else 'eligible_for_engineering_review'
  end;

  v_report := jsonb_build_object(
    'evaluation_run_id', v_evaluation_id,
    'mode', 'historical_shadow_replay',
    'champion_version', v_champion_version,
    'challenger_version', p_challenger_version,
    'sample', jsonb_build_object(
      'cases', v_case_count,
      'resolved', v_resolved_count,
      'minimum_cases_for_review', 20,
      'minimum_resolved_for_review', 12
    ),
    'decision_alignment', jsonb_build_object(
      'champion_rate', v_champion_rate,
      'challenger_rate', v_challenger_rate,
      'uplift', v_uplift,
      'meaning', 'Alinhamento com aceitar/modificar versus rejeitar/sem ação; não mede eficácia clínica.'
    ),
    'divergence', jsonb_build_object(
      'recommendation_changes', v_recommendation_changes,
      'risk_changes', v_risk_changes
    ),
    'safety', jsonb_build_object(
      'risk_downgrades', v_safety_downgrades,
      'unsafe_actionability_conflicts', v_unsafe_conflicts,
      'required_for_review', 'zero'
    ),
    'promotion_gate', jsonb_build_object(
      'status', v_status,
      'auto_activation', false,
      'human_engineering_review_required', true
    ),
    'limitations', jsonb_build_array(
      'Historical outcome alignment is not clinical efficacy.',
      'The shadow challenger cannot change live recommendations.',
      'Template availability is not replayed as a mutable production dependency.',
      'Promotion requires a separate versioned engineering change after review.'
    )
  );

  update public.decision_engine_evaluation_runs
  set status = v_status,
      case_count = v_case_count,
      resolved_count = v_resolved_count,
      champion_alignment_rate = v_champion_rate,
      challenger_alignment_rate = v_challenger_rate,
      alignment_uplift = v_uplift,
      recommendation_changes = v_recommendation_changes,
      risk_changes = v_risk_changes,
      safety_downgrades = v_safety_downgrades,
      unsafe_actionability_conflicts = v_unsafe_conflicts,
      report = v_report,
      completed_at = now()
  where id = v_evaluation_id;

  v_packet := jsonb_build_object(
    'evaluation_run_id', v_evaluation_id,
    'challenger_version', p_challenger_version,
    'gate_status', v_status,
    'evidence', v_report,
    'activation_authorized', false,
    'next_action', case
      when v_status = 'eligible_for_engineering_review'
        then 'Create a separate reviewed promotion change; do not activate automatically.'
      when v_status = 'blocked_insufficient_evidence'
        then 'Collect more resolved Decision Intelligence outcomes before reconsidering promotion.'
      when v_status = 'blocked_safety_regression'
        then 'Fix the challenger safety regression before any promotion discussion.'
      else 'Improve decision alignment without weakening safety.'
    end
  );

  insert into public.decision_engine_promotion_packets (
    evaluation_run_id,
    organization_id,
    challenger_version,
    gate_status,
    packet,
    requested_by
  ) values (
    v_evaluation_id,
    p_organization_id,
    p_challenger_version,
    v_status,
    v_packet,
    p_requested_by
  );

  return v_evaluation_id;
exception when others then
  if v_evaluation_id is not null then
    update public.decision_engine_evaluation_runs
    set status = 'failed',
        report = jsonb_build_object(
          'error_class', sqlstate,
          'error_message', sqlerrm,
          'auto_activation', false
        ),
        completed_at = now()
    where id = v_evaluation_id;
  end if;
  raise;
end;
$$;

revoke all on function private.run_decision_engine_evaluation_internal(uuid,text,uuid,text) from public, anon, authenticated;
grant execute on function private.run_decision_engine_evaluation_internal(uuid,text,uuid,text) to authenticated;

create or replace function public.run_decision_engine_evaluation(
  p_organization_id uuid,
  p_challenger_version text default 'blackgold_deterministic_v1_1_shadow'
)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_evaluation_id uuid;
  v_result jsonb;
begin
  if auth.uid() is null then
    raise exception using errcode = '42501', message = 'AUTH_REQUIRED';
  end if;
  if not private.is_org_manager(p_organization_id) then
    raise exception using errcode = '42501', message = 'ORG_MANAGER_REQUIRED';
  end if;

  v_evaluation_id := private.run_decision_engine_evaluation_internal(
    p_organization_id,
    p_challenger_version,
    auth.uid(),
    'interactive'
  );

  select jsonb_build_object(
    'evaluation_run_id', r.id,
    'status', r.status,
    'report', r.report,
    'completed_at', r.completed_at,
    'shadow_only', true,
    'auto_activation', false
  ) into v_result
  from public.decision_engine_evaluation_runs r
  where r.id = v_evaluation_id;

  return v_result;
end;
$$;

revoke execute on function public.run_decision_engine_evaluation(uuid,text) from public, anon;
grant execute on function public.run_decision_engine_evaluation(uuid,text) to authenticated;

create or replace function public.get_decision_engine_lab_status(p_organization_id uuid)
returns jsonb
language plpgsql
stable
security invoker
set search_path = ''
as $$
declare
  v_latest record;
  v_packet record;
  v_champion jsonb;
  v_challengers jsonb := '[]'::jsonb;
begin
  if auth.uid() is null then
    raise exception using errcode = '42501', message = 'AUTH_REQUIRED';
  end if;
  if not private.is_org_member(p_organization_id) then
    raise exception using errcode = '42501', message = 'ORG_MEMBER_REQUIRED';
  end if;

  select jsonb_build_object(
    'engine_version', engine_version,
    'role', engine_role,
    'lifecycle', lifecycle,
    'description', description,
    'ruleset', ruleset
  ) into v_champion
  from public.decision_engine_registry
  where engine_role = 'champion' and lifecycle = 'active'
  limit 1;

  select coalesce(
    jsonb_agg(
      jsonb_build_object(
        'engine_version', engine_version,
        'role', engine_role,
        'lifecycle', lifecycle,
        'description', description,
        'ruleset', ruleset
      ) order by engine_version
    ),
    '[]'::jsonb
  ) into v_challengers
  from public.decision_engine_registry
  where engine_role = 'challenger' and lifecycle = 'lab_only';

  select * into v_latest
  from public.decision_engine_evaluation_runs
  where organization_id = p_organization_id
  order by created_at desc
  limit 1;

  if v_latest.id is not null then
    select * into v_packet
    from public.decision_engine_promotion_packets
    where evaluation_run_id = v_latest.id;
  end if;

  return jsonb_build_object(
    'champion', v_champion,
    'challengers', v_challengers,
    'latest_evaluation', case when v_latest.id is null then null else jsonb_build_object(
      'evaluation_run_id', v_latest.id,
      'challenger_version', v_latest.challenger_version,
      'status', v_latest.status,
      'case_count', v_latest.case_count,
      'resolved_count', v_latest.resolved_count,
      'champion_alignment_rate', v_latest.champion_alignment_rate,
      'challenger_alignment_rate', v_latest.challenger_alignment_rate,
      'alignment_uplift', v_latest.alignment_uplift,
      'recommendation_changes', v_latest.recommendation_changes,
      'risk_changes', v_latest.risk_changes,
      'safety_downgrades', v_latest.safety_downgrades,
      'unsafe_actionability_conflicts', v_latest.unsafe_actionability_conflicts,
      'report', v_latest.report,
      'created_at', v_latest.created_at,
      'completed_at', v_latest.completed_at
    ) end,
    'promotion_packet', case when v_packet.id is null then null else jsonb_build_object(
      'gate_status', v_packet.gate_status,
      'packet', v_packet.packet,
      'created_at', v_packet.created_at
    ) end,
    'shadow_only', true,
    'production_engine_unchanged', true,
    'auto_activation', false,
    'generated_at', now()
  );
end;
$$;

revoke execute on function public.get_decision_engine_lab_status(uuid) from public, anon;
grant execute on function public.get_decision_engine_lab_status(uuid) to authenticated;

do $$
declare
  v_org uuid;
begin
  for v_org in
    select distinct organization_id
    from public.decision_intelligence_runs
  loop
    perform private.run_decision_engine_evaluation_internal(
      v_org,
      'blackgold_deterministic_v1_1_shadow',
      null,
      'migration_bootstrap'
    );
  end loop;
end;
$$;
