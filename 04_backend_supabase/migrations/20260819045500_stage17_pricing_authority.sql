create table if not exists public.pricing_decisions (
  decision_version text primary key check (char_length(btrim(decision_version)) between 8 and 120),
  scope text not null check (char_length(btrim(scope)) between 2 and 80),
  currency text not null check (currency ~ '^[A-Z]{3}$'),
  mode text not null check (mode in ('experiment','frozen','retired')),
  annual_strategy text not null,
  price_payload jsonb not null check (jsonb_typeof(price_payload) = 'array'),
  evidence_version text not null,
  evidence_checked_at timestamptz not null,
  evidence_summary jsonb not null default '{}'::jsonb check (jsonb_typeof(evidence_summary) = 'object'),
  effective_from timestamptz not null default now(),
  effective_until timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (effective_until is null or effective_until > effective_from)
);

create unique index if not exists pricing_decisions_one_current_scope_currency_idx
  on public.pricing_decisions(scope, currency)
  where mode in ('experiment','frozen');

create table if not exists public.billing_fee_assumptions (
  provider_code text not null references public.billing_provider_registry(provider_code) on update restrict on delete restrict,
  fee_code text not null,
  assumption_version text not null,
  currency text not null check (currency ~ '^[A-Z]{3}$'),
  variable_bps integer not null default 0 check (variable_bps between 0 and 10000),
  fixed_amount_minor integer not null default 0 check (fixed_amount_minor >= 0),
  contractual boolean not null default false,
  evidence_version text not null,
  evidence_checked_at timestamptz not null,
  notes text,
  created_at timestamptz not null default now(),
  primary key (provider_code, fee_code, assumption_version)
);

alter table public.pricing_decisions enable row level security;
alter table public.billing_fee_assumptions enable row level security;

revoke all on public.pricing_decisions from public, anon, authenticated, service_role;
revoke all on public.billing_fee_assumptions from public, anon, authenticated, service_role;
grant select on public.pricing_decisions to authenticated;
grant select on public.pricing_decisions to service_role;
grant select on public.billing_fee_assumptions to service_role;

drop policy if exists pricing_decisions_select_current_authenticated on public.pricing_decisions;
create policy pricing_decisions_select_current_authenticated
on public.pricing_decisions
for select
to authenticated
using (mode in ('experiment','frozen'));

insert into public.billing_fee_assumptions (
  provider_code,
  fee_code,
  assumption_version,
  currency,
  variable_bps,
  fixed_amount_minor,
  contractual,
  evidence_version,
  evidence_checked_at,
  notes
)
values
  (
    'asaas',
    'credit_card_standard_starting',
    'ASAAS_PUBLIC_FEE_20260819_V1',
    'BRL',
    299,
    49,
    false,
    '2026-08-19-official-public-pricing-v1',
    '2026-08-19T04:48:00-03:00'::timestamptz,
    'Public starting rate used only for planning. Account-specific contracted fees remain authoritative.'
  ),
  (
    'asaas',
    'pix_invoice_standard',
    'ASAAS_PUBLIC_FEE_20260819_V1',
    'BRL',
    0,
    199,
    false,
    '2026-08-19-official-public-pricing-v1',
    '2026-08-19T04:48:00-03:00'::timestamptz,
    'Public invoice Pix receipt rate used only for planning. Account-specific contracted fees remain authoritative.'
  )
on conflict (provider_code, fee_code, assumption_version) do nothing;

alter table public.subscription_plan_prices
  add column if not exists pricing_decision_version text references public.pricing_decisions(decision_version) on update restrict on delete restrict;

create unique index if not exists subscription_plan_prices_decision_combo_uidx
  on public.subscription_plan_prices(pricing_decision_version, plan_code, currency, billing_interval);

alter table public.billing_checkout_intents
  add column if not exists pricing_decision_version text references public.pricing_decisions(decision_version) on update restrict on delete restrict;

create or replace function public.promote_subscription_pricing(
  p_decision_version text,
  p_scope text,
  p_currency text,
  p_mode text,
  p_annual_strategy text,
  p_prices jsonb,
  p_evidence_version text,
  p_evidence_checked_at timestamptz,
  p_evidence_summary jsonb default '{}'::jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_existing public.pricing_decisions%rowtype;
  v_item jsonb;
  v_plan text;
  v_interval text;
  v_amount integer;
  v_combo_count integer := 0;
  v_valid_combo_count integer;
  v_annual_ok_count integer;
  v_price_count integer;
begin
  if p_decision_version is null or char_length(btrim(p_decision_version)) < 8 then
    raise exception using errcode = '22023', message = 'PRICING_DECISION_VERSION_REQUIRED';
  end if;
  if p_scope is null or p_currency !~ '^[A-Z]{3}$' then
    raise exception using errcode = '22023', message = 'INVALID_PRICING_SCOPE_OR_CURRENCY';
  end if;
  if p_mode not in ('experiment','frozen') then
    raise exception using errcode = '22023', message = 'INVALID_PRICING_MODE';
  end if;
  if p_annual_strategy <> 'TEN_MONTHS_FOR_TWELVE' then
    raise exception using errcode = '22023', message = 'UNSUPPORTED_ANNUAL_PRICING_STRATEGY';
  end if;
  if jsonb_typeof(p_prices) <> 'array' or jsonb_array_length(p_prices) <> 6 then
    raise exception using errcode = '22023', message = 'PRICING_SET_MUST_HAVE_SIX_OFFERS';
  end if;
  if jsonb_typeof(coalesce(p_evidence_summary, '{}'::jsonb)) <> 'object' then
    raise exception using errcode = '22023', message = 'INVALID_PRICING_EVIDENCE_SUMMARY';
  end if;

  for v_item in select value from jsonb_array_elements(p_prices)
  loop
    v_plan := v_item ->> 'plan_code';
    v_interval := v_item ->> 'billing_interval';
    begin
      v_amount := (v_item ->> 'amount_minor')::integer;
    exception when others then
      raise exception using errcode = '22023', message = 'INVALID_PRICING_AMOUNT';
    end;

    if v_plan not in ('solo','pro','studio')
      or v_interval not in ('month','year')
      or v_amount <= 0
    then
      raise exception using errcode = '22023', message = 'INVALID_PRICING_OFFER';
    end if;
    v_combo_count := v_combo_count + 1;
  end loop;

  select count(*)::int into v_valid_combo_count
  from (
    select distinct
      value ->> 'plan_code' as plan_code,
      value ->> 'billing_interval' as billing_interval
    from jsonb_array_elements(p_prices)
  ) q;

  if v_combo_count <> 6 or v_valid_combo_count <> 6 then
    raise exception using errcode = '22023', message = 'PRICING_SET_DUPLICATE_OR_MISSING_COMBO';
  end if;

  select count(*)::int into v_annual_ok_count
  from (
    select
      value ->> 'plan_code' as plan_code,
      max((value ->> 'amount_minor')::integer) filter (where value ->> 'billing_interval' = 'month') as monthly_minor,
      max((value ->> 'amount_minor')::integer) filter (where value ->> 'billing_interval' = 'year') as annual_minor
    from jsonb_array_elements(p_prices)
    group by value ->> 'plan_code'
  ) p
  where p.monthly_minor is not null
    and p.annual_minor = p.monthly_minor * 10;

  if v_annual_ok_count <> 3 then
    raise exception using errcode = '22023', message = 'ANNUAL_PRICE_MUST_EQUAL_TEN_MONTHS';
  end if;

  select * into v_existing
  from public.pricing_decisions d
  where d.decision_version = p_decision_version;

  if v_existing.decision_version is not null then
    if v_existing.scope <> p_scope
      or v_existing.currency <> p_currency
      or v_existing.mode <> p_mode
      or v_existing.annual_strategy <> p_annual_strategy
      or v_existing.price_payload <> p_prices
      or v_existing.evidence_version <> p_evidence_version
    then
      raise exception using errcode = '40900', message = 'PRICING_DECISION_VERSION_CONFLICT';
    end if;

    select count(*)::int into v_price_count
    from public.subscription_plan_prices p
    where p.pricing_decision_version = p_decision_version
      and p.lifecycle = 'active';

    return jsonb_build_object(
      'decision_version', p_decision_version,
      'idempotent_replay', true,
      'active_price_count', v_price_count
    );
  end if;

  update public.pricing_decisions
  set
    mode = 'retired',
    effective_until = now(),
    updated_at = now()
  where scope = p_scope
    and currency = p_currency
    and mode in ('experiment','frozen');

  update public.subscription_plan_prices
  set
    lifecycle = 'retired',
    effective_until = now(),
    updated_at = now()
  where currency = p_currency
    and lifecycle = 'active';

  insert into public.pricing_decisions (
    decision_version,
    scope,
    currency,
    mode,
    annual_strategy,
    price_payload,
    evidence_version,
    evidence_checked_at,
    evidence_summary,
    effective_from
  )
  values (
    p_decision_version,
    p_scope,
    p_currency,
    p_mode,
    p_annual_strategy,
    p_prices,
    p_evidence_version,
    p_evidence_checked_at,
    coalesce(p_evidence_summary, '{}'::jsonb),
    now()
  );

  for v_item in select value from jsonb_array_elements(p_prices)
  loop
    insert into public.subscription_plan_prices (
      plan_code,
      currency,
      billing_interval,
      amount_minor,
      lifecycle,
      evidence_version,
      effective_from,
      pricing_decision_version
    )
    values (
      v_item ->> 'plan_code',
      p_currency,
      v_item ->> 'billing_interval',
      (v_item ->> 'amount_minor')::integer,
      'active',
      p_evidence_version,
      now(),
      p_decision_version
    )
    on conflict (pricing_decision_version, plan_code, currency, billing_interval)
    do update set
      amount_minor = excluded.amount_minor,
      lifecycle = 'active',
      evidence_version = excluded.evidence_version,
      effective_from = now(),
      effective_until = null,
      updated_at = now();
  end loop;

  select count(*)::int into v_price_count
  from public.subscription_plan_prices p
  where p.pricing_decision_version = p_decision_version
    and p.lifecycle = 'active';

  if v_price_count <> 6 then
    raise exception using errcode = 'P0001', message = 'PRICING_PARTIAL_PROMOTION_BLOCKED';
  end if;

  return jsonb_build_object(
    'decision_version', p_decision_version,
    'idempotent_replay', false,
    'mode', p_mode,
    'active_price_count', v_price_count
  );
end;
$$;

revoke execute on function public.promote_subscription_pricing(text,text,text,text,text,jsonb,text,timestamptz,jsonb) from public, anon, authenticated;
grant execute on function public.promote_subscription_pricing(text,text,text,text,text,jsonb,text,timestamptz,jsonb) to service_role;

select public.promote_subscription_pricing(
  'BR_V1_PRICING_EXPERIMENT_001',
  'BR_V1',
  'BRL',
  'experiment',
  'TEN_MONTHS_FOR_TWELVE',
  jsonb_build_array(
    jsonb_build_object('plan_code','solo','billing_interval','month','amount_minor',3990),
    jsonb_build_object('plan_code','solo','billing_interval','year','amount_minor',39900),
    jsonb_build_object('plan_code','pro','billing_interval','month','amount_minor',7990),
    jsonb_build_object('plan_code','pro','billing_interval','year','amount_minor',79900),
    jsonb_build_object('plan_code','studio','billing_interval','month','amount_minor',17990),
    jsonb_build_object('plan_code','studio','billing_interval','year','amount_minor',179900)
  ),
  '2026-08-19-pricing-evidence-v1',
  '2026-08-19T04:48:00-03:00'::timestamptz,
  jsonb_build_object(
    'source_contract', 'FitNexus monetization adendum: hypothesis ranges remain a commercial gate',
    'range_position', 'upper_bound_validation',
    'market_research_checked_at', '2026-08-19T04:48:00-03:00',
    'provider_fee_assumptions_contractual', false,
    'annual_strategy', 'approximately ten monthly payments for twelve months'
  )
);

alter table public.billing_checkout_intents
  alter column pricing_decision_version set not null;

create or replace function public.create_billing_checkout_intent(
  p_organization_id uuid,
  p_plan_code text,
  p_billing_interval text default 'month',
  p_idempotency_key uuid default extensions.gen_random_uuid()
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_selection public.billing_provider_selections%rowtype;
  v_price public.subscription_plan_prices%rowtype;
  v_decision public.pricing_decisions%rowtype;
  v_intent public.billing_checkout_intents%rowtype;
begin
  if auth.uid() is null then
    raise exception using errcode = '42501', message = 'AUTH_REQUIRED';
  end if;
  if p_organization_id is null or not private.is_org_billing_manager(p_organization_id) then
    raise exception using errcode = '42501', message = 'ORG_BILLING_MANAGER_REQUIRED';
  end if;
  if p_billing_interval not in ('month','year') then
    raise exception using errcode = '22023', message = 'INVALID_BILLING_INTERVAL';
  end if;

  select * into v_selection
  from public.billing_provider_selections s
  where s.scope = 'BR_V1';

  if v_selection.scope is null then
    raise exception using errcode = 'P0002', message = 'BILLING_PROVIDER_NOT_SELECTED';
  end if;
  if v_selection.state <> 'active' then
    raise exception using errcode = '42501', message = 'BILLING_PROVIDER_CREDENTIALS_NOT_READY';
  end if;

  select * into v_price
  from public.subscription_plan_prices p
  where p.plan_code = p_plan_code
    and p.currency = 'BRL'
    and p.billing_interval = p_billing_interval
    and p.lifecycle = 'active'
    and p.pricing_decision_version is not null
    and (p.effective_from is null or p.effective_from <= now())
    and (p.effective_until is null or p.effective_until > now())
  limit 1;

  if v_price.id is null then
    raise exception using errcode = '42501', message = 'COMMERCIAL_PRICE_NOT_PROMOTED';
  end if;

  select * into v_decision
  from public.pricing_decisions d
  where d.decision_version = v_price.pricing_decision_version
    and d.mode in ('experiment','frozen')
    and d.scope = 'BR_V1'
    and d.currency = 'BRL';

  if v_decision.decision_version is null then
    raise exception using errcode = '42501', message = 'PRICING_DECISION_NOT_CURRENT';
  end if;

  select * into v_intent
  from public.billing_checkout_intents i
  where i.idempotency_key = p_idempotency_key;

  if v_intent.id is not null then
    if v_intent.organization_id <> p_organization_id
      or v_intent.plan_code <> p_plan_code
      or v_intent.billing_interval <> p_billing_interval
      or v_intent.pricing_decision_version <> v_price.pricing_decision_version
    then
      raise exception using errcode = '40900', message = 'CHECKOUT_IDEMPOTENCY_KEY_CONFLICT';
    end if;

    return jsonb_build_object(
      'checkout_intent_id', v_intent.id,
      'idempotent_replay', true,
      'status', v_intent.status,
      'provider_code', v_intent.provider_code,
      'pricing_decision_version', v_intent.pricing_decision_version,
      'checkout_url', v_intent.checkout_url
    );
  end if;

  insert into public.billing_checkout_intents (
    organization_id,
    plan_code,
    price_id,
    provider_code,
    currency,
    amount_minor,
    billing_interval,
    idempotency_key,
    created_by,
    pricing_decision_version
  )
  values (
    p_organization_id,
    p_plan_code,
    v_price.id,
    v_selection.provider_code,
    v_price.currency,
    v_price.amount_minor,
    v_price.billing_interval,
    p_idempotency_key,
    auth.uid(),
    v_price.pricing_decision_version
  )
  returning * into v_intent;

  return jsonb_build_object(
    'checkout_intent_id', v_intent.id,
    'idempotent_replay', false,
    'status', v_intent.status,
    'provider_code', v_intent.provider_code,
    'plan_code', v_intent.plan_code,
    'currency', v_intent.currency,
    'amount_minor', v_intent.amount_minor,
    'billing_interval', v_intent.billing_interval,
    'pricing_decision_version', v_intent.pricing_decision_version,
    'checkout_url', null
  );
end;
$$;

revoke execute on function public.create_billing_checkout_intent(uuid,text,text,uuid) from public, anon;
grant execute on function public.create_billing_checkout_intent(uuid,text,text,uuid) to authenticated;
grant execute on function public.create_billing_checkout_intent(uuid,text,text,uuid) to service_role;

create or replace function public.get_pricing_catalog(
  p_currency text default 'BRL'
)
returns jsonb
language sql
stable
security invoker
set search_path = ''
as $$
  with current_decision as (
    select d.*
    from public.pricing_decisions d
    where d.currency = p_currency
      and d.mode in ('experiment','frozen')
    order by d.effective_from desc
    limit 1
  ), offers as (
    select
      sp.code,
      sp.display_name,
      sp.student_limit,
      sp.member_limit,
      max(spp.amount_minor) filter (where spp.billing_interval = 'month') as monthly_minor,
      max(spp.amount_minor) filter (where spp.billing_interval = 'year') as annual_minor,
      max(spp.pricing_decision_version) as pricing_decision_version
    from public.subscription_plans sp
    join public.subscription_plan_prices spp on spp.plan_code = sp.code
    join current_decision d on d.decision_version = spp.pricing_decision_version
    where sp.lifecycle = 'active'
      and sp.code in ('solo','pro','studio')
      and spp.lifecycle = 'active'
      and spp.currency = p_currency
      and (spp.effective_from is null or spp.effective_from <= now())
      and (spp.effective_until is null or spp.effective_until > now())
    group by sp.code, sp.display_name, sp.student_limit, sp.member_limit, sp.sort_order
    order by sp.sort_order
  )
  select jsonb_build_object(
    'currency', p_currency,
    'decision_version', d.decision_version,
    'mode', upper(d.mode),
    'annual_strategy', d.annual_strategy,
    'offers', coalesce(
      jsonb_agg(
        jsonb_build_object(
          'plan_code', o.code,
          'display_name', o.display_name,
          'student_limit', o.student_limit,
          'member_limit', o.member_limit,
          'monthly_amount_minor', o.monthly_minor,
          'annual_amount_minor', o.annual_minor,
          'annual_savings_minor', (o.monthly_minor * 12) - o.annual_minor,
          'annual_monthly_equivalent_minor', round(o.annual_minor / 12.0)::int,
          'pricing_decision_version', o.pricing_decision_version
        )
        order by o.student_limit
      ),
      '[]'::jsonb
    ),
    'generated_at', now()
  )
  from current_decision d
  left join offers o on true
  group by d.decision_version, d.mode, d.annual_strategy;
$$;

revoke execute on function public.get_pricing_catalog(text) from public, anon;
grant execute on function public.get_pricing_catalog(text) to authenticated;

create or replace function public.get_billing_provider_readiness(
  p_organization_id uuid,
  p_scope text default 'BR_V1'
)
returns jsonb
language plpgsql
stable
security invoker
set search_path = ''
as $$
declare
  v_selection public.billing_provider_selections%rowtype;
  v_provider public.billing_provider_registry%rowtype;
  v_decision public.pricing_decisions%rowtype;
  v_active_price_count integer := 0;
  v_pricing_complete boolean := false;
  v_subscription public.organization_subscriptions%rowtype;
begin
  if auth.uid() is null then
    raise exception using errcode = '42501', message = 'AUTH_REQUIRED';
  end if;
  if p_organization_id is null or not private.is_org_member(p_organization_id) then
    raise exception using errcode = '42501', message = 'ORG_MEMBER_REQUIRED';
  end if;

  select * into v_selection
  from public.billing_provider_selections s
  where s.scope = p_scope;

  if v_selection.scope is null then
    raise exception using errcode = 'P0002', message = 'BILLING_PROVIDER_NOT_SELECTED';
  end if;

  select * into v_provider
  from public.billing_provider_registry p
  where p.provider_code = v_selection.provider_code;

  select * into v_decision
  from public.pricing_decisions d
  where d.scope = p_scope
    and d.currency = 'BRL'
    and d.mode in ('experiment','frozen')
  order by d.effective_from desc
  limit 1;

  if v_decision.decision_version is not null then
    select count(*)::int into v_active_price_count
    from public.subscription_plan_prices p
    where p.currency = 'BRL'
      and p.lifecycle = 'active'
      and p.pricing_decision_version = v_decision.decision_version
      and p.plan_code in ('solo','pro','studio')
      and p.billing_interval in ('month','year')
      and (p.effective_from is null or p.effective_from <= now())
      and (p.effective_until is null or p.effective_until > now());
  end if;

  v_pricing_complete := v_decision.decision_version is not null and v_active_price_count = 6;

  select * into v_subscription
  from public.organization_subscriptions s
  where s.organization_id = p_organization_id;

  return jsonb_build_object(
    'organization_id', p_organization_id,
    'scope', p_scope,
    'provider', jsonb_build_object(
      'code', v_provider.provider_code,
      'display_name', v_provider.display_name,
      'selection_state', v_selection.state,
      'capabilities', v_provider.capabilities,
      'evidence_version', v_selection.evidence_version
    ),
    'pricing', jsonb_build_object(
      'state', case when v_pricing_complete then 'PROMOTED' else 'UNFROZEN' end,
      'mode', case when v_decision.decision_version is null then 'NONE' else upper(v_decision.mode) end,
      'decision_version', v_decision.decision_version,
      'annual_strategy', v_decision.annual_strategy,
      'active_price_count', v_active_price_count,
      'expected_price_count', 6,
      'complete', v_pricing_complete
    ),
    'credentials', jsonb_build_object(
      'state', case
        when v_selection.state = 'active' then 'EXTERNAL_AUTHORITY_CONFIGURED'
        else 'PENDING_EXTERNAL_CREDENTIAL_BOUNDARY'
      end,
      'secret_exposed_to_flutter', false
    ),
    'checkout', jsonb_build_object(
      'ready', v_selection.state = 'active' and v_pricing_complete,
      'server_amount_authority', true,
      'client_amount_allowed', false,
      'silent_provider_fallback', false,
      'pricing_decision_bound', v_pricing_complete
    ),
    'subscription_provider_bound', v_subscription.provider is not null,
    'generated_at', now()
  );
end;
$$;

revoke execute on function public.get_billing_provider_readiness(uuid,text) from public, anon;
grant execute on function public.get_billing_provider_readiness(uuid,text) to authenticated;
