create table if not exists public.billing_provider_registry (
  provider_code text primary key check (provider_code ~ '^[a-z0-9_]{2,40}$'),
  display_name text not null check (char_length(btrim(display_name)) between 2 and 80),
  lifecycle text not null check (lifecycle in ('evaluated','selected','retired')),
  market_scope text not null,
  capabilities jsonb not null default '{}'::jsonb check (jsonb_typeof(capabilities) = 'object'),
  evidence_version text not null,
  evidence_checked_at timestamptz not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

insert into public.billing_provider_registry (
  provider_code,
  display_name,
  lifecycle,
  market_scope,
  capabilities,
  evidence_version,
  evidence_checked_at
)
values
  (
    'asaas',
    'Asaas',
    'selected',
    'BR_V1',
    jsonb_build_object(
      'hosted_checkout', true,
      'recurring_subscriptions', true,
      'credit_card_recurring', true,
      'pix', true,
      'pix_automatic', true,
      'sandbox', true,
      'webhooks', true,
      'webhook_at_least_once', true,
      'webhook_auth_token', true,
      'monthly_platform_fee_required', false
    ),
    '2026-08-18-official-docs-v1',
    '2026-08-18T23:50:00-03:00'::timestamptz
  ),
  (
    'stripe',
    'Stripe',
    'evaluated',
    'FUTURE_INTERNATIONAL_CANDIDATE',
    jsonb_build_object(
      'hosted_checkout', true,
      'recurring_subscriptions', true,
      'international_reach', true,
      'pix_brazil_invite_only', true,
      'billing_volume_fee', true
    ),
    '2026-08-18-official-docs-v1',
    '2026-08-18T23:50:00-03:00'::timestamptz
  ),
  (
    'mercado_pago',
    'Mercado Pago',
    'evaluated',
    'BR_ALTERNATIVE',
    jsonb_build_object(
      'hosted_checkout', true,
      'recurring_subscriptions', true,
      'pix', true,
      'boleto', true,
      'automatic_retry', true
    ),
    '2026-08-18-official-docs-v1',
    '2026-08-18T23:50:00-03:00'::timestamptz
  )
on conflict (provider_code) do update
set
  display_name = excluded.display_name,
  lifecycle = excluded.lifecycle,
  market_scope = excluded.market_scope,
  capabilities = excluded.capabilities,
  evidence_version = excluded.evidence_version,
  evidence_checked_at = excluded.evidence_checked_at,
  updated_at = now();

create table if not exists public.billing_provider_selections (
  scope text primary key check (char_length(btrim(scope)) between 2 and 80),
  provider_code text not null references public.billing_provider_registry(provider_code) on update restrict on delete restrict,
  state text not null check (state in ('selected_pending_credentials','active','suspended')),
  evidence_version text not null,
  selected_at timestamptz not null default now(),
  activated_at timestamptz,
  updated_at timestamptz not null default now(),
  check ((state <> 'active') or activated_at is not null)
);

insert into public.billing_provider_selections (
  scope,
  provider_code,
  state,
  evidence_version,
  selected_at
)
values (
  'BR_V1',
  'asaas',
  'selected_pending_credentials',
  '2026-08-18-official-docs-v1',
  now()
)
on conflict (scope) do update
set
  provider_code = excluded.provider_code,
  state = case
    when public.billing_provider_selections.state = 'active'
      and public.billing_provider_selections.provider_code = excluded.provider_code
      then public.billing_provider_selections.state
    else excluded.state
  end,
  evidence_version = excluded.evidence_version,
  selected_at = excluded.selected_at,
  updated_at = now();

create table if not exists public.subscription_plan_prices (
  id uuid primary key default extensions.gen_random_uuid(),
  plan_code text not null references public.subscription_plans(code) on update restrict on delete restrict,
  currency text not null check (currency ~ '^[A-Z]{3}$'),
  billing_interval text not null check (billing_interval in ('month','year')),
  amount_minor integer not null check (amount_minor > 0),
  lifecycle text not null default 'draft' check (lifecycle in ('draft','active','retired')),
  evidence_version text not null,
  effective_from timestamptz,
  effective_until timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (effective_until is null or effective_from is null or effective_until > effective_from)
);

create unique index if not exists subscription_plan_prices_one_active_idx
  on public.subscription_plan_prices(plan_code, currency, billing_interval)
  where lifecycle = 'active';

create table if not exists public.billing_checkout_intents (
  id uuid primary key default extensions.gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  plan_code text not null references public.subscription_plans(code) on update restrict on delete restrict,
  price_id uuid not null references public.subscription_plan_prices(id) on update restrict on delete restrict,
  provider_code text not null references public.billing_provider_registry(provider_code) on update restrict on delete restrict,
  currency text not null check (currency ~ '^[A-Z]{3}$'),
  amount_minor integer not null check (amount_minor > 0),
  billing_interval text not null check (billing_interval in ('month','year')),
  status text not null default 'provider_pending' check (status in ('provider_pending','redirect_ready','completed','expired','failed','canceled')),
  idempotency_key uuid not null unique,
  created_by uuid not null references auth.users(id) on delete restrict,
  provider_checkout_ref text,
  checkout_url text,
  expires_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (checkout_url is null or checkout_url ~ '^https://')
);

create unique index if not exists billing_checkout_intents_provider_ref_uidx
  on public.billing_checkout_intents(provider_code, provider_checkout_ref)
  where provider_checkout_ref is not null;

create index if not exists billing_checkout_intents_org_created_idx
  on public.billing_checkout_intents(organization_id, created_at desc);

create table if not exists public.billing_webhook_receipts (
  id uuid primary key default extensions.gen_random_uuid(),
  provider_code text not null references public.billing_provider_registry(provider_code) on update restrict on delete restrict,
  provider_event_id text not null,
  event_type text not null,
  payload_sha256 text not null check (payload_sha256 ~ '^[0-9a-f]{64}$'),
  auth_verified boolean not null check (auth_verified),
  processing_status text not null default 'received' check (processing_status in ('received','applied','ignored','failed')),
  organization_id uuid references public.organizations(id) on delete set null,
  provider_subscription_ref text,
  received_at timestamptz not null default now(),
  processed_at timestamptz,
  created_at timestamptz not null default now(),
  unique (provider_code, provider_event_id)
);

create index if not exists billing_webhook_receipts_org_received_idx
  on public.billing_webhook_receipts(organization_id, received_at desc)
  where organization_id is not null;

alter table public.billing_provider_registry enable row level security;
alter table public.billing_provider_selections enable row level security;
alter table public.subscription_plan_prices enable row level security;
alter table public.billing_checkout_intents enable row level security;
alter table public.billing_webhook_receipts enable row level security;

revoke all on public.billing_provider_registry from anon, authenticated;
revoke all on public.billing_provider_selections from anon, authenticated;
revoke all on public.subscription_plan_prices from anon, authenticated;
revoke all on public.billing_checkout_intents from anon, authenticated;
revoke all on public.billing_webhook_receipts from anon, authenticated;

grant select on public.billing_provider_registry to authenticated;
grant select on public.billing_provider_selections to authenticated;
grant select on public.subscription_plan_prices to authenticated;
grant select on public.billing_checkout_intents to authenticated;
grant select on public.billing_webhook_receipts to authenticated;

revoke all on public.billing_provider_registry from service_role;
revoke all on public.billing_provider_selections from service_role;
revoke all on public.subscription_plan_prices from service_role;
revoke all on public.billing_checkout_intents from service_role;
revoke all on public.billing_webhook_receipts from service_role;

grant select on public.billing_provider_registry to service_role;
grant select, update on public.billing_provider_selections to service_role;
grant select on public.subscription_plan_prices to service_role;
grant select, update on public.billing_checkout_intents to service_role;
grant select, insert, update on public.billing_webhook_receipts to service_role;

drop policy if exists billing_provider_registry_select_authenticated on public.billing_provider_registry;
create policy billing_provider_registry_select_authenticated
on public.billing_provider_registry
for select
to authenticated
using (true);

drop policy if exists billing_provider_selections_select_authenticated on public.billing_provider_selections;
create policy billing_provider_selections_select_authenticated
on public.billing_provider_selections
for select
to authenticated
using (true);

drop policy if exists subscription_plan_prices_select_active on public.subscription_plan_prices;
create policy subscription_plan_prices_select_active
on public.subscription_plan_prices
for select
to authenticated
using (lifecycle = 'active');

drop policy if exists billing_checkout_intents_select_member on public.billing_checkout_intents;
create policy billing_checkout_intents_select_member
on public.billing_checkout_intents
for select
to authenticated
using ((select private.is_org_member(organization_id)));

drop policy if exists billing_webhook_receipts_select_manager on public.billing_webhook_receipts;
create policy billing_webhook_receipts_select_manager
on public.billing_webhook_receipts
for select
to authenticated
using (organization_id is not null and (select private.is_org_billing_manager(organization_id)));

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
  v_active_price_count integer;
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

  select count(*)::int into v_active_price_count
  from public.subscription_plan_prices p
  where p.currency = 'BRL'
    and p.lifecycle = 'active'
    and (p.effective_from is null or p.effective_from <= now())
    and (p.effective_until is null or p.effective_until > now());

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
      'state', case when v_active_price_count > 0 then 'PROMOTED' else 'UNFROZEN' end,
      'active_price_count', v_active_price_count
    ),
    'credentials', jsonb_build_object(
      'state', case
        when v_selection.state = 'active' then 'EXTERNAL_AUTHORITY_CONFIGURED'
        else 'PENDING_EXTERNAL_CREDENTIAL_BOUNDARY'
      end,
      'secret_exposed_to_flutter', false
    ),
    'checkout', jsonb_build_object(
      'ready', v_selection.state = 'active' and v_active_price_count > 0,
      'server_amount_authority', true,
      'client_amount_allowed', false,
      'silent_provider_fallback', false
    ),
    'subscription_provider_bound', v_subscription.provider is not null,
    'generated_at', now()
  );
end;
$$;

revoke execute on function public.get_billing_provider_readiness(uuid,text) from public, anon;
grant execute on function public.get_billing_provider_readiness(uuid,text) to authenticated;

create or replace function public.create_billing_checkout_intent(
  p_organization_id uuid,
  p_plan_code text,
  p_billing_interval text default 'month',
  p_idempotency_key uuid default extensions.gen_random_uuid()
)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_selection public.billing_provider_selections%rowtype;
  v_price public.subscription_plan_prices%rowtype;
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
    and (p.effective_from is null or p.effective_from <= now())
    and (p.effective_until is null or p.effective_until > now())
  limit 1;

  if v_price.id is null then
    raise exception using errcode = '42501', message = 'COMMERCIAL_PRICE_NOT_PROMOTED';
  end if;

  select * into v_intent
  from public.billing_checkout_intents i
  where i.idempotency_key = p_idempotency_key;

  if v_intent.id is not null then
    if v_intent.organization_id <> p_organization_id
      or v_intent.plan_code <> p_plan_code
      or v_intent.billing_interval <> p_billing_interval
    then
      raise exception using errcode = '40900', message = 'CHECKOUT_IDEMPOTENCY_KEY_CONFLICT';
    end if;

    return jsonb_build_object(
      'checkout_intent_id', v_intent.id,
      'idempotent_replay', true,
      'status', v_intent.status,
      'provider_code', v_intent.provider_code,
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
    created_by
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
    auth.uid()
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
    'checkout_url', null
  );
end;
$$;

revoke execute on function public.create_billing_checkout_intent(uuid,text,text,uuid) from public, anon;
grant execute on function public.create_billing_checkout_intent(uuid,text,text,uuid) to authenticated;

create or replace function public.attach_billing_provider_checkout(
  p_checkout_intent_id uuid,
  p_provider_checkout_ref text,
  p_checkout_url text,
  p_expires_at timestamptz default null
)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_intent public.billing_checkout_intents%rowtype;
  v_ref text;
  v_url text;
begin
  v_ref := nullif(btrim(coalesce(p_provider_checkout_ref, '')), '');
  v_url := nullif(btrim(coalesce(p_checkout_url, '')), '');

  if v_ref is null then
    raise exception using errcode = '22023', message = 'PROVIDER_CHECKOUT_REF_REQUIRED';
  end if;
  if v_url is null or v_url !~ '^https://' then
    raise exception using errcode = '22023', message = 'HTTPS_CHECKOUT_URL_REQUIRED';
  end if;

  select * into v_intent
  from public.billing_checkout_intents i
  where i.id = p_checkout_intent_id
  for update;

  if v_intent.id is null then
    raise exception using errcode = 'P0002', message = 'CHECKOUT_INTENT_NOT_FOUND';
  end if;
  if v_intent.status not in ('provider_pending','redirect_ready') then
    raise exception using errcode = '40900', message = 'CHECKOUT_INTENT_NOT_ATTACHABLE';
  end if;

  update public.billing_checkout_intents
  set
    provider_checkout_ref = v_ref,
    checkout_url = v_url,
    status = 'redirect_ready',
    expires_at = p_expires_at,
    updated_at = now()
  where id = v_intent.id;

  return jsonb_build_object(
    'checkout_intent_id', v_intent.id,
    'provider_code', v_intent.provider_code,
    'status', 'redirect_ready',
    'checkout_url', v_url
  );
end;
$$;

revoke execute on function public.attach_billing_provider_checkout(uuid,text,text,timestamptz) from public, anon, authenticated;
grant execute on function public.attach_billing_provider_checkout(uuid,text,text,timestamptz) to service_role;

create or replace function public.record_billing_webhook_receipt(
  p_provider_code text,
  p_provider_event_id text,
  p_event_type text,
  p_payload_sha256 text,
  p_auth_verified boolean,
  p_organization_id uuid default null,
  p_provider_subscription_ref text default null
)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_receipt_id uuid;
  v_event_id text;
  v_event_type text;
begin
  v_event_id := nullif(btrim(coalesce(p_provider_event_id, '')), '');
  v_event_type := nullif(btrim(coalesce(p_event_type, '')), '');

  if not coalesce(p_auth_verified, false) then
    raise exception using errcode = '42501', message = 'WEBHOOK_AUTH_NOT_VERIFIED';
  end if;
  if v_event_id is null then
    raise exception using errcode = '22023', message = 'PROVIDER_EVENT_ID_REQUIRED';
  end if;
  if v_event_type is null then
    raise exception using errcode = '22023', message = 'PROVIDER_EVENT_TYPE_REQUIRED';
  end if;
  if p_payload_sha256 is null or p_payload_sha256 !~ '^[0-9a-f]{64}$' then
    raise exception using errcode = '22023', message = 'INVALID_PAYLOAD_SHA256';
  end if;
  if not exists (
    select 1 from public.billing_provider_registry p
    where p.provider_code = p_provider_code
  ) then
    raise exception using errcode = '22023', message = 'UNKNOWN_BILLING_PROVIDER';
  end if;

  insert into public.billing_webhook_receipts (
    provider_code,
    provider_event_id,
    event_type,
    payload_sha256,
    auth_verified,
    organization_id,
    provider_subscription_ref
  )
  values (
    p_provider_code,
    v_event_id,
    v_event_type,
    p_payload_sha256,
    true,
    p_organization_id,
    nullif(btrim(coalesce(p_provider_subscription_ref, '')), '')
  )
  on conflict (provider_code, provider_event_id) do nothing
  returning id into v_receipt_id;

  return jsonb_build_object(
    'receipt_id', v_receipt_id,
    'idempotent_replay', v_receipt_id is null,
    'provider_code', p_provider_code,
    'provider_event_id', v_event_id
  );
end;
$$;

revoke execute on function public.record_billing_webhook_receipt(text,text,text,text,boolean,uuid,text) from public, anon, authenticated;
grant execute on function public.record_billing_webhook_receipt(text,text,text,text,boolean,uuid,text) to service_role;

drop trigger if exists billing_provider_registry_set_updated_at on public.billing_provider_registry;
create trigger billing_provider_registry_set_updated_at
before update on public.billing_provider_registry
for each row execute function private.set_updated_at();

drop trigger if exists billing_provider_selections_set_updated_at on public.billing_provider_selections;
create trigger billing_provider_selections_set_updated_at
before update on public.billing_provider_selections
for each row execute function private.set_updated_at();

drop trigger if exists subscription_plan_prices_set_updated_at on public.subscription_plan_prices;
create trigger subscription_plan_prices_set_updated_at
before update on public.subscription_plan_prices
for each row execute function private.set_updated_at();

drop trigger if exists billing_checkout_intents_set_updated_at on public.billing_checkout_intents;
create trigger billing_checkout_intents_set_updated_at
before update on public.billing_checkout_intents
for each row execute function private.set_updated_at();
