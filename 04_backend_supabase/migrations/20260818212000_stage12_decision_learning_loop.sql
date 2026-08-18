create table if not exists public.decision_intelligence_outcomes (
  id uuid primary key default extensions.gen_random_uuid(),
  run_id uuid not null unique references public.decision_intelligence_runs(id) on delete restrict,
  organization_id uuid not null references public.organizations(id) on delete cascade,
  student_id uuid not null,
  outcome text not null check (outcome in ('accepted','modified','rejected','no_action')),
  committed_plan_id uuid,
  note text check (note is null or char_length(note) <= 500),
  decided_by uuid not null,
  decided_at timestamptz not null default now(),
  constraint decision_intelligence_outcomes_student_org_fk
    foreign key (student_id, organization_id)
    references public.students(id, organization_id)
    on delete cascade,
  constraint decision_intelligence_outcomes_plan_student_org_fk
    foreign key (committed_plan_id, student_id, organization_id)
    references public.training_plans(id, student_id, organization_id)
    on delete restrict
);

create index if not exists decision_intelligence_outcomes_org_student_decided_idx
  on public.decision_intelligence_outcomes(organization_id, student_id, decided_at desc);
create index if not exists decision_intelligence_outcomes_student_org_fk_idx
  on public.decision_intelligence_outcomes(student_id, organization_id);
create index if not exists decision_intelligence_outcomes_plan_student_org_fk_idx
  on public.decision_intelligence_outcomes(committed_plan_id, student_id, organization_id)
  where committed_plan_id is not null;

alter table public.decision_intelligence_outcomes enable row level security;
revoke all on public.decision_intelligence_outcomes from anon, authenticated;
grant select, insert on public.decision_intelligence_outcomes to authenticated;

drop policy if exists decision_intelligence_outcomes_select_org on public.decision_intelligence_outcomes;
create policy decision_intelligence_outcomes_select_org
on public.decision_intelligence_outcomes
for select to authenticated
using ((select private.is_org_member(organization_id)));

drop policy if exists decision_intelligence_outcomes_insert_manager on public.decision_intelligence_outcomes;
create policy decision_intelligence_outcomes_insert_manager
on public.decision_intelligence_outcomes
for insert to authenticated
with check (
  (select private.is_org_manager(organization_id))
  and decided_by = (select auth.uid())
);

create or replace function private.normalize_training_exercises(p_exercises jsonb)
returns jsonb
language sql
immutable
set search_path = ''
as $$
  select coalesce(
    jsonb_agg(
      jsonb_build_object(
        'name', btrim(coalesce(e.value ->> 'name', '')),
        'prescription', btrim(coalesce(e.value ->> 'prescription', ''))
      ) order by e.ordinality
    ),
    '[]'::jsonb
  )
  from jsonb_array_elements(coalesce(p_exercises, '[]'::jsonb)) with ordinality as e(value, ordinality);
$$;

revoke all on function private.normalize_training_exercises(jsonb) from public, anon, authenticated;
grant execute on function private.normalize_training_exercises(jsonb) to authenticated;

create or replace function public.create_training_plan_from_decision_intelligence(
  p_run_id uuid,
  p_name text,
  p_next_session text default null,
  p_notes text default null,
  p_exercises jsonb default '[]'::jsonb,
  p_decision_reason text default null
)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_run record;
  v_candidate jsonb;
  v_candidate_exercises jsonb;
  v_source_template uuid;
  v_outcome text;
  v_plan uuid;
  v_reason text;
begin
  if auth.uid() is null then
    raise exception using errcode = '42501', message = 'AUTH_REQUIRED';
  end if;

  select r.* into v_run
  from public.decision_intelligence_runs r
  where r.id = p_run_id;

  if v_run.id is null then
    raise exception using errcode = 'P0002', message = 'DECISION_INTELLIGENCE_RUN_NOT_FOUND';
  end if;
  if not private.is_org_manager(v_run.organization_id) then
    raise exception using errcode = '42501', message = 'ORG_MANAGER_REQUIRED';
  end if;
  if exists (select 1 from public.decision_intelligence_outcomes o where o.run_id = v_run.id) then
    raise exception using errcode = '23505', message = 'DECISION_INTELLIGENCE_RUN_ALREADY_RESOLVED';
  end if;
  if jsonb_typeof(p_exercises) <> 'array' or jsonb_array_length(p_exercises) = 0 then
    raise exception using errcode = '22023', message = 'TRAINING_EXERCISES_REQUIRED';
  end if;

  v_candidate := v_run.brief -> 'candidate';
  if v_candidate is null or jsonb_typeof(v_candidate) <> 'object' then
    raise exception using errcode = '22023', message = 'DECISION_INTELLIGENCE_CANDIDATE_NOT_AVAILABLE';
  end if;

  v_candidate_exercises := v_candidate -> 'proposed_exercises';
  if v_candidate_exercises is null
     or jsonb_typeof(v_candidate_exercises) <> 'array'
     or jsonb_array_length(v_candidate_exercises) = 0 then
    raise exception using errcode = '22023', message = 'DECISION_INTELLIGENCE_CANDIDATE_INVALID';
  end if;

  begin
    v_source_template := nullif(v_candidate ->> 'template_id', '')::uuid;
  exception when invalid_text_representation then
    raise exception using errcode = '22023', message = 'DECISION_INTELLIGENCE_TEMPLATE_ID_INVALID';
  end;

  if v_source_template is null or not exists (
    select 1 from public.training_templates t
    where t.id = v_source_template
      and t.organization_id = v_run.organization_id
      and t.is_active
  ) then
    raise exception using errcode = '42501', message = 'DECISION_INTELLIGENCE_TEMPLATE_NOT_AVAILABLE';
  end if;

  v_outcome := case
    when private.normalize_training_exercises(p_exercises)
       = private.normalize_training_exercises(v_candidate_exercises)
      then 'accepted'
    else 'modified'
  end;

  v_reason := nullif(btrim(coalesce(p_decision_reason, '')), '');
  if v_reason is null then
    raise exception using errcode = '22023', message = 'DECISION_REASON_REQUIRED';
  end if;

  select public.create_training_plan_v2(
    v_run.student_id,
    p_name,
    p_next_session,
    p_notes,
    p_exercises,
    v_reason,
    v_source_template,
    jsonb_build_object(
      'source', 'decision_intelligence',
      'decision_intelligence_run_id', v_run.id,
      'decision_intelligence_outcome', v_outcome,
      'source_template_id', v_source_template,
      'human_confirmed', true
    )
  ) into v_plan;

  insert into public.decision_intelligence_outcomes (
    run_id, organization_id, student_id, outcome, committed_plan_id,
    note, decided_by
  ) values (
    v_run.id, v_run.organization_id, v_run.student_id, v_outcome, v_plan,
    case
      when v_outcome = 'accepted' then 'Candidato aceito após preview e confirmação humana'
      else 'Candidato modificado pelo professor antes do commit'
    end,
    auth.uid()
  );

  return jsonb_build_object(
    'run_id', v_run.id,
    'plan_id', v_plan,
    'outcome', v_outcome,
    'source_template_id', v_source_template,
    'atomic', true,
    'human_confirmed', true
  );
end;
$$;

revoke execute on function public.create_training_plan_from_decision_intelligence(uuid,text,text,text,jsonb,text) from public, anon;
grant execute on function public.create_training_plan_from_decision_intelligence(uuid,text,text,text,jsonb,text) to authenticated;

create or replace function public.record_decision_intelligence_outcome(
  p_run_id uuid,
  p_outcome text,
  p_note text default null
)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_run record;
  v_note text := nullif(btrim(coalesce(p_note, '')), '');
begin
  if auth.uid() is null then
    raise exception using errcode = '42501', message = 'AUTH_REQUIRED';
  end if;
  if p_outcome not in ('rejected','no_action') then
    raise exception using errcode = '22023', message = 'NON_COMMIT_OUTCOME_INVALID';
  end if;
  if v_note is not null and char_length(v_note) > 500 then
    raise exception using errcode = '22023', message = 'OUTCOME_NOTE_TOO_LONG';
  end if;

  select r.* into v_run
  from public.decision_intelligence_runs r
  where r.id = p_run_id;

  if v_run.id is null then
    raise exception using errcode = 'P0002', message = 'DECISION_INTELLIGENCE_RUN_NOT_FOUND';
  end if;
  if not private.is_org_manager(v_run.organization_id) then
    raise exception using errcode = '42501', message = 'ORG_MANAGER_REQUIRED';
  end if;
  if exists (select 1 from public.decision_intelligence_outcomes o where o.run_id = v_run.id) then
    raise exception using errcode = '23505', message = 'DECISION_INTELLIGENCE_RUN_ALREADY_RESOLVED';
  end if;

  insert into public.decision_intelligence_outcomes (
    run_id, organization_id, student_id, outcome, committed_plan_id,
    note, decided_by
  ) values (
    v_run.id, v_run.organization_id, v_run.student_id, p_outcome, null,
    v_note, auth.uid()
  );

  return jsonb_build_object(
    'run_id', v_run.id,
    'outcome', p_outcome,
    'committed_plan_id', null,
    'recorded', true
  );
end;
$$;

revoke execute on function public.record_decision_intelligence_outcome(uuid,text,text) from public, anon;
grant execute on function public.record_decision_intelligence_outcome(uuid,text,text) to authenticated;

create or replace function public.get_decision_intelligence_calibration(p_organization_id uuid)
returns jsonb
language plpgsql
stable
security invoker
set search_path = ''
as $$
declare
  v_summary jsonb;
  v_by_recommendation jsonb := '[]'::jsonb;
  v_by_confidence jsonb := '[]'::jsonb;
  v_by_risk jsonb := '[]'::jsonb;
begin
  if auth.uid() is null then
    raise exception using errcode = '42501', message = 'AUTH_REQUIRED';
  end if;
  if not private.is_org_member(p_organization_id) then
    raise exception using errcode = '42501', message = 'ORG_MEMBER_REQUIRED';
  end if;

  with base as (
    select r.id,
      r.brief -> 'recommendation' ->> 'type' as recommendation_type,
      r.brief -> 'confidence' ->> 'label' as confidence_label,
      r.brief -> 'risk' ->> 'level' as risk_level,
      o.outcome
    from public.decision_intelligence_runs r
    left join public.decision_intelligence_outcomes o on o.run_id = r.id
    where r.organization_id = p_organization_id
  )
  select jsonb_build_object(
    'total_runs', count(*)::int,
    'resolved_runs', count(*) filter (where outcome is not null)::int,
    'unresolved_runs', count(*) filter (where outcome is null)::int,
    'accepted', count(*) filter (where outcome = 'accepted')::int,
    'modified', count(*) filter (where outcome = 'modified')::int,
    'rejected', count(*) filter (where outcome = 'rejected')::int,
    'no_action', count(*) filter (where outcome = 'no_action')::int,
    'adoption_rate', case
      when count(*) filter (where outcome is not null) = 0 then 0
      else round(100.0 * count(*) filter (where outcome in ('accepted','modified')) /
        count(*) filter (where outcome is not null))::int
    end,
    'exact_acceptance_rate', case
      when count(*) filter (where outcome is not null) = 0 then 0
      else round(100.0 * count(*) filter (where outcome = 'accepted') /
        count(*) filter (where outcome is not null))::int
    end,
    'modification_rate', case
      when count(*) filter (where outcome is not null) = 0 then 0
      else round(100.0 * count(*) filter (where outcome = 'modified') /
        count(*) filter (where outcome is not null))::int
    end
  ) into v_summary
  from base;

  with base as (
    select coalesce(r.brief -> 'recommendation' ->> 'type', 'unknown') as key,
      o.outcome
    from public.decision_intelligence_runs r
    left join public.decision_intelligence_outcomes o on o.run_id = r.id
    where r.organization_id = p_organization_id
  ), grouped as (
    select key,
      count(*)::int as runs,
      count(*) filter (where outcome is not null)::int as resolved,
      count(*) filter (where outcome = 'accepted')::int as accepted,
      count(*) filter (where outcome = 'modified')::int as modified,
      count(*) filter (where outcome = 'rejected')::int as rejected,
      count(*) filter (where outcome = 'no_action')::int as no_action
    from base group by key
  )
  select coalesce(jsonb_agg(to_jsonb(grouped) order by runs desc, key), '[]'::jsonb)
  into v_by_recommendation from grouped;

  with base as (
    select coalesce(r.brief -> 'confidence' ->> 'label', 'unknown') as key,
      o.outcome
    from public.decision_intelligence_runs r
    left join public.decision_intelligence_outcomes o on o.run_id = r.id
    where r.organization_id = p_organization_id
  ), grouped as (
    select key,
      count(*)::int as runs,
      count(*) filter (where outcome is not null)::int as resolved,
      count(*) filter (where outcome = 'accepted')::int as accepted,
      count(*) filter (where outcome = 'modified')::int as modified,
      count(*) filter (where outcome = 'rejected')::int as rejected,
      count(*) filter (where outcome = 'no_action')::int as no_action
    from base group by key
  )
  select coalesce(jsonb_agg(to_jsonb(grouped) order by key), '[]'::jsonb)
  into v_by_confidence from grouped;

  with base as (
    select coalesce(r.brief -> 'risk' ->> 'level', 'unknown') as key,
      o.outcome
    from public.decision_intelligence_runs r
    left join public.decision_intelligence_outcomes o on o.run_id = r.id
    where r.organization_id = p_organization_id
  ), grouped as (
    select key,
      count(*)::int as runs,
      count(*) filter (where outcome is not null)::int as resolved,
      count(*) filter (where outcome = 'accepted')::int as accepted,
      count(*) filter (where outcome = 'modified')::int as modified,
      count(*) filter (where outcome = 'rejected')::int as rejected,
      count(*) filter (where outcome = 'no_action')::int as no_action
    from base group by key
  )
  select coalesce(jsonb_agg(to_jsonb(grouped) order by key), '[]'::jsonb)
  into v_by_risk from grouped;

  return jsonb_build_object(
    'summary', v_summary,
    'by_recommendation', v_by_recommendation,
    'by_confidence', v_by_confidence,
    'by_risk', v_by_risk,
    'interpretation', 'Calibração de uso e decisão humana; não mede eficácia clínica nem autoriza automação de prescrição.',
    'generated_at', now()
  );
end;
$$;

revoke execute on function public.get_decision_intelligence_calibration(uuid) from public, anon;
grant execute on function public.get_decision_intelligence_calibration(uuid) to authenticated;
