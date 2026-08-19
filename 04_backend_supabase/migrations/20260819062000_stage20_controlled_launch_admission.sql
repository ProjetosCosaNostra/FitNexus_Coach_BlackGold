create table if not exists private.controlled_launch_gate_catalog (
  gate_code text primary key check (gate_code ~ '^[a-z0-9_]{3,80}$'),
  category text not null check (category in ('tracking','commercial','legal','privacy','security','deployment')),
  authority_mode text not null check (authority_mode in ('automatic','evidence_migration','external_authorization')),
  mandatory boolean not null default true,
  description text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists private.controlled_launch_gate_evidence (
  gate_code text primary key references private.controlled_launch_gate_catalog(gate_code) on update restrict on delete restrict,
  state text not null check (state in ('blocked','ready')),
  evidence_ref text,
  evidence_digest text,
  note text,
  attested_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (state = 'blocked' or (evidence_ref is not null and evidence_digest is not null))
);

insert into private.controlled_launch_gate_catalog (gate_code,category,authority_mode,mandatory,description)
values
  ('tracking_core','tracking','automatic',true,'Public acquisition plus authenticated activation and revenue tracking is complete.'),
  ('pricing_experiment','commercial','automatic',true,'A complete versioned BRL pricing decision is current.'),
  ('billing_provider_credentials','commercial','external_authorization',true,'The selected billing provider has externally authorized credentials and active authority.'),
  ('legal_privacy_notice','privacy','evidence_migration',true,'A production privacy notice completed legal review and is published at a stable public route.'),
  ('legal_terms_of_use','legal','evidence_migration',true,'Production Terms of Use completed legal review and are published at a stable public route.'),
  ('legal_role_mapping','privacy','evidence_migration',true,'Controller and operator responsibilities for FitNexus, coach and student processing are reviewed and documented.'),
  ('data_subject_request_channel','privacy','evidence_migration',true,'A tested operational channel exists for LGPD data-subject requests.'),
  ('incident_response','security','evidence_migration',true,'Personal-data incident response ownership, evidence retention and notification decision flow are tested.'),
  ('production_deployment','deployment','evidence_migration',true,'Stable production domain, TLS, rollback evidence and release receipt are attested.')
on conflict (gate_code) do update set
  category=excluded.category,
  authority_mode=excluded.authority_mode,
  mandatory=excluded.mandatory,
  description=excluded.description,
  updated_at=now();

insert into private.controlled_launch_gate_evidence (gate_code,state,note)
select c.gate_code,'blocked','Awaiting explicit evidence migration.'
from private.controlled_launch_gate_catalog c
where c.authority_mode='evidence_migration'
on conflict (gate_code) do nothing;

revoke all on private.controlled_launch_gate_catalog from public,anon,authenticated,service_role;
revoke all on private.controlled_launch_gate_evidence from public,anon,authenticated,service_role;
grant select on private.controlled_launch_gate_catalog to service_role;
grant select on private.controlled_launch_gate_evidence to service_role;

create or replace function private.get_controlled_launch_readiness_authority()
returns jsonb
language plpgsql
stable
security definer
set search_path=''
as $$
declare
  v_tracking boolean:=false;
  v_pricing boolean:=false;
  v_billing boolean:=false;
  v_manual_ready integer:=0;
  v_manual_total integer:=0;
  v_mandatory integer:=0;
  v_ready integer:=0;
  v_gates jsonb;
begin
  select count(*)=2 into v_tracking
  from private.growth_event_catalog c
  where c.event_name in ('landing_view','signup_started')
    and c.capture_authority='public_capture'
    and c.capture_status='active';

  select exists(
    select 1 from public.pricing_decisions d
    where d.scope='BR_V1' and d.currency='BRL' and d.mode in ('experiment','frozen')
      and (select count(*) from public.subscription_plan_prices p
           where p.pricing_decision_version=d.decision_version
             and p.lifecycle='active' and p.currency='BRL'
             and p.plan_code in ('solo','pro','studio')
             and p.billing_interval in ('month','year'))=6
  ) into v_pricing;

  select exists(
    select 1 from public.billing_provider_selections s
    where s.scope='BR_V1' and s.provider_code='asaas'
      and s.state='active' and s.activated_at is not null
  ) into v_billing;

  select count(*) filter(where e.state='ready')::int,count(*)::int
    into v_manual_ready,v_manual_total
  from private.controlled_launch_gate_catalog c
  left join private.controlled_launch_gate_evidence e using(gate_code)
  where c.mandatory and c.authority_mode='evidence_migration';

  select count(*)::int into v_mandatory
  from private.controlled_launch_gate_catalog c where c.mandatory;

  v_ready := (case when v_tracking then 1 else 0 end)
           + (case when v_pricing then 1 else 0 end)
           + (case when v_billing then 1 else 0 end)
           + v_manual_ready;

  with s as (
    select c.gate_code,c.category,c.authority_mode,c.mandatory,c.description,
      case c.gate_code
        when 'tracking_core' then case when v_tracking then 'ready' else 'blocked' end
        when 'pricing_experiment' then case when v_pricing then 'ready' else 'blocked' end
        when 'billing_provider_credentials' then case when v_billing then 'ready' else 'blocked' end
        else coalesce(e.state,'blocked')
      end as state,
      e.evidence_ref,e.evidence_digest,e.attested_at
    from private.controlled_launch_gate_catalog c
    left join private.controlled_launch_gate_evidence e using(gate_code)
  )
  select jsonb_agg(jsonb_build_object(
    'gate_code',s.gate_code,'category',s.category,'authority_mode',s.authority_mode,
    'mandatory',s.mandatory,'state',s.state,'evidence_ref',s.evidence_ref,
    'evidence_digest',s.evidence_digest,'attested_at',s.attested_at,'description',s.description
  ) order by s.category,s.gate_code) into v_gates from s;

  return jsonb_build_object(
    'release_state',case when v_ready=v_mandatory then 'READY_FOR_CONTROLLED_LAUNCH' else 'BLOCKED' end,
    'ads_release_state',case when v_ready=v_mandatory then 'READY_FOR_CONTROLLED_ADMISSION' else 'BLOCKED' end,
    'ready_mandatory_gates',v_ready,
    'mandatory_gates',v_mandatory,
    'blocking_gate_count',greatest(v_mandatory-v_ready,0),
    'automatic',jsonb_build_object('tracking_core',v_tracking,'pricing_experiment',v_pricing,'billing_provider_credentials',v_billing),
    'gates',coalesce(v_gates,'[]'::jsonb),
    'guardrails',jsonb_build_object(
      'tracking_readiness_is_not_launch_authority',true,
      'pricing_readiness_is_not_checkout_authority',true,
      'external_billing_authorization_required',true,
      'legal_review_evidence_is_migration_owned',true,
      'paid_ads_auto_launch',false
    ),
    'generated_at',now()
  );
end;
$$;

revoke execute on function private.get_controlled_launch_readiness_authority() from public,anon,authenticated;
grant execute on function private.get_controlled_launch_readiness_authority() to service_role;

create or replace function public.get_controlled_launch_readiness()
returns jsonb
language sql
stable
security invoker
set search_path=''
as $$ select private.get_controlled_launch_readiness_authority(); $$;

revoke execute on function public.get_controlled_launch_readiness() from public,anon,authenticated;
grant execute on function public.get_controlled_launch_readiness() to service_role;
