-- Stage 38: close the gap between internal billing-provider activation and
-- the external evidence required by the controlled-launch authority.
--
-- This migration does not activate a provider and does not attest any external
-- evidence. It creates a migration-owned evidence boundary, requires credential
-- evidence before provider activation, and requires proof-complete evidence
-- before billing_provider_credentials may satisfy controlled-launch readiness.

create table if not exists private.billing_provider_external_evidence (
  scope text not null references public.billing_provider_selections(scope) on update restrict on delete restrict,
  provider_code text not null references public.billing_provider_registry(provider_code) on update restrict on delete restrict,
  evidence_version text not null,
  state text not null check (state in ('credentials_verified','proof_complete')),
  provider_account_owner_authorization_digest text not null
    check (provider_account_owner_authorization_digest ~ '^[0-9a-f]{64}$'),
  credential_activation_digest text not null
    check (credential_activation_digest ~ '^[0-9a-f]{64}$'),
  provider_environment_id text not null
    check (char_length(btrim(provider_environment_id)) between 2 and 128),
  webhook_auth_test_receipt_digest text
    check (webhook_auth_test_receipt_digest is null or webhook_auth_test_receipt_digest ~ '^[0-9a-f]{64}$'),
  webhook_replay_receipt_digest text
    check (webhook_replay_receipt_digest is null or webhook_replay_receipt_digest ~ '^[0-9a-f]{64}$'),
  checkout_end_to_end_receipt_digest text
    check (checkout_end_to_end_receipt_digest is null or checkout_end_to_end_receipt_digest ~ '^[0-9a-f]{64}$'),
  credentials_verified_at timestamptz not null,
  proof_completed_at timestamptz,
  attested_at timestamptz not null default now(),
  note text,
  primary key (scope, provider_code, evidence_version),
  check (
    state <> 'proof_complete'
    or (
      webhook_auth_test_receipt_digest is not null
      and webhook_replay_receipt_digest is not null
      and checkout_end_to_end_receipt_digest is not null
      and proof_completed_at is not null
    )
  )
);

comment on table private.billing_provider_external_evidence is
  'Migration-owned non-secret evidence authority for billing provider activation and launch readiness. Runtime roles receive no DML authority.';

revoke all on private.billing_provider_external_evidence from public, anon, authenticated, service_role;

-- BGF-STAGE37-BILLING-EVIDENCE-BINDING-GAP-320:
-- activation is no longer admitted from an internal evidence-version string alone.
create or replace function public.activate_billing_provider_selection(
  p_scope text,
  p_provider_code text,
  p_evidence_version text
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_selection public.billing_provider_selections%rowtype;
  v_external_evidence private.billing_provider_external_evidence%rowtype;
  v_evidence text;
begin
  select * into v_selection
  from public.billing_provider_selections s
  where s.scope = p_scope
  for update;

  if v_selection.scope is null then
    raise exception using errcode = 'P0002', message = 'BILLING_PROVIDER_NOT_SELECTED';
  end if;
  if v_selection.provider_code <> p_provider_code then
    raise exception using errcode = '42501', message = 'SILENT_PROVIDER_FALLBACK_FORBIDDEN';
  end if;

  v_evidence := nullif(btrim(coalesce(p_evidence_version, '')), '');
  if v_evidence is null or v_evidence <> v_selection.evidence_version then
    raise exception using errcode = '42501', message = 'BILLING_PROVIDER_EVIDENCE_VERSION_MISMATCH';
  end if;

  select * into v_external_evidence
  from private.billing_provider_external_evidence e
  where e.scope = v_selection.scope
    and e.provider_code = v_selection.provider_code
    and e.evidence_version = v_selection.evidence_version;

  if v_external_evidence.scope is null
    or v_external_evidence.state not in ('credentials_verified','proof_complete')
    or v_external_evidence.credentials_verified_at is null
  then
    raise exception using errcode = '42501', message = 'BILLING_PROVIDER_EXTERNAL_CREDENTIAL_EVIDENCE_REQUIRED';
  end if;

  update public.billing_provider_selections
  set
    state = 'active',
    activated_at = coalesce(activated_at, now()),
    updated_at = now()
  where scope = v_selection.scope;

  return jsonb_build_object(
    'scope', v_selection.scope,
    'provider_code', v_selection.provider_code,
    'state', 'active',
    'evidence_version', v_selection.evidence_version,
    'external_credential_evidence_bound', true,
    'activated', true
  );
end;
$$;

revoke execute on function public.activate_billing_provider_selection(text,text,text) from public, anon, authenticated;
grant execute on function public.activate_billing_provider_selection(text,text,text) to service_role;

-- Controlled-launch billing readiness now needs proof-complete migration-owned
-- external evidence in addition to provider activation. This prevents activation
-- from promoting the billing gate before webhook and checkout proof are sealed.
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
    select 1
    from public.billing_provider_selections s
    join private.billing_provider_external_evidence e
      on e.scope=s.scope
     and e.provider_code=s.provider_code
     and e.evidence_version=s.evidence_version
    where s.scope='BR_V1'
      and s.provider_code='asaas'
      and s.state='active'
      and s.activated_at is not null
      and e.state='proof_complete'
      and e.provider_account_owner_authorization_digest ~ '^[0-9a-f]{64}$'
      and e.credential_activation_digest ~ '^[0-9a-f]{64}$'
      and char_length(btrim(e.provider_environment_id)) between 2 and 128
      and e.webhook_auth_test_receipt_digest ~ '^[0-9a-f]{64}$'
      and e.webhook_replay_receipt_digest ~ '^[0-9a-f]{64}$'
      and e.checkout_end_to_end_receipt_digest ~ '^[0-9a-f]{64}$'
      and e.credentials_verified_at is not null
      and e.proof_completed_at is not null
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
      'external_billing_launch_evidence_required',true,
      'legal_review_evidence_is_migration_owned',true,
      'paid_ads_auto_launch',false
    ),
    'generated_at',now()
  );
end;
$$;

revoke execute on function private.get_controlled_launch_readiness_authority() from public,anon,authenticated;
grant execute on function private.get_controlled_launch_readiness_authority() to service_role;
