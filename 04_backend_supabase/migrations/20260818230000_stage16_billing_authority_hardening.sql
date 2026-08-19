create index if not exists billing_checkout_intents_created_by_idx
  on public.billing_checkout_intents(created_by);

create index if not exists billing_checkout_intents_plan_code_idx
  on public.billing_checkout_intents(plan_code);

create index if not exists billing_checkout_intents_price_id_idx
  on public.billing_checkout_intents(price_id);

create index if not exists billing_provider_selections_provider_code_idx
  on public.billing_provider_selections(provider_code);

-- BGF-BILLING-SERVICE-DIRECT-MUTATION-079:
-- external provider workers receive read-only table access. Mutations are
-- admitted only through narrow, service-role-only SECURITY DEFINER commands.
revoke all on public.billing_provider_registry from service_role;
revoke all on public.billing_provider_selections from service_role;
revoke all on public.subscription_plan_prices from service_role;
revoke all on public.billing_checkout_intents from service_role;
revoke all on public.billing_webhook_receipts from service_role;

grant select on public.billing_provider_registry to service_role;
grant select on public.billing_provider_selections to service_role;
grant select on public.subscription_plan_prices to service_role;
grant select on public.billing_checkout_intents to service_role;
grant select on public.billing_webhook_receipts to service_role;

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
    'activated', true
  );
end;
$$;

revoke execute on function public.activate_billing_provider_selection(text,text,text) from public, anon, authenticated;
grant execute on function public.activate_billing_provider_selection(text,text,text) to service_role;

create or replace function public.attach_billing_provider_checkout(
  p_checkout_intent_id uuid,
  p_provider_checkout_ref text,
  p_checkout_url text,
  p_expires_at timestamptz default null
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_intent public.billing_checkout_intents%rowtype;
  v_selection public.billing_provider_selections%rowtype;
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

  select * into v_selection
  from public.billing_provider_selections s
  where s.scope = 'BR_V1';

  if v_selection.state <> 'active' or v_selection.provider_code <> v_intent.provider_code then
    raise exception using errcode = '42501', message = 'BILLING_PROVIDER_AUTHORITY_NOT_ACTIVE';
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
security definer
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
    select 1
    from public.billing_provider_registry p
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

create or replace function public.mark_billing_webhook_receipt(
  p_provider_code text,
  p_provider_event_id text,
  p_processing_status text,
  p_organization_id uuid default null,
  p_provider_subscription_ref text default null
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_receipt public.billing_webhook_receipts%rowtype;
begin
  if p_processing_status not in ('applied','ignored','failed') then
    raise exception using errcode = '22023', message = 'INVALID_WEBHOOK_PROCESSING_STATUS';
  end if;

  select * into v_receipt
  from public.billing_webhook_receipts r
  where r.provider_code = p_provider_code
    and r.provider_event_id = p_provider_event_id
  for update;

  if v_receipt.id is null then
    raise exception using errcode = 'P0002', message = 'WEBHOOK_RECEIPT_NOT_FOUND';
  end if;
  if not v_receipt.auth_verified then
    raise exception using errcode = '42501', message = 'WEBHOOK_AUTH_NOT_VERIFIED';
  end if;

  update public.billing_webhook_receipts
  set
    processing_status = p_processing_status,
    organization_id = coalesce(p_organization_id, organization_id),
    provider_subscription_ref = coalesce(
      nullif(btrim(coalesce(p_provider_subscription_ref, '')), ''),
      provider_subscription_ref
    ),
    processed_at = now()
  where id = v_receipt.id;

  return jsonb_build_object(
    'receipt_id', v_receipt.id,
    'provider_code', v_receipt.provider_code,
    'provider_event_id', v_receipt.provider_event_id,
    'processing_status', p_processing_status
  );
end;
$$;

revoke execute on function public.mark_billing_webhook_receipt(text,text,text,uuid,text) from public, anon, authenticated;
grant execute on function public.mark_billing_webhook_receipt(text,text,text,uuid,text) to service_role;
