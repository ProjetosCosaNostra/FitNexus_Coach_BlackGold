-- Candidate authority for promotion after PR validation.
-- No remote migration is performed by this file alone.
--
-- BGF-BILLING-CHECKOUT-WEBHOOK-AUTHORITY-V1
-- Provider webhooks may only mutate checkout/subscription state through this
-- narrow service-role-only command. Browser callbacks never call this path.

create or replace function public.apply_billing_checkout_webhook_event(
  p_provider_code text,
  p_provider_checkout_ref text,
  p_provider_event_id text,
  p_event_type text,
  p_payload_sha256 text,
  p_effective_at timestamptz default now(),
  p_provider_customer_ref text default null
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_intent public.billing_checkout_intents%rowtype;
  v_provider text;
  v_checkout_ref text;
  v_event_id text;
  v_event_type text;
  v_effective_at timestamptz;
  v_period_end timestamptz;
  v_target_status text;
  v_subscription_result jsonb;
begin
  v_provider := nullif(btrim(coalesce(p_provider_code, '')), '');
  v_checkout_ref := nullif(btrim(coalesce(p_provider_checkout_ref, '')), '');
  v_event_id := nullif(btrim(coalesce(p_provider_event_id, '')), '');
  v_event_type := nullif(btrim(coalesce(p_event_type, '')), '');
  v_effective_at := coalesce(p_effective_at, now());

  if v_provider is null or not exists (
    select 1
    from public.billing_provider_registry p
    where p.provider_code = v_provider
  ) then
    raise exception using errcode = '22023', message = 'UNKNOWN_BILLING_PROVIDER';
  end if;
  if v_checkout_ref is null then
    raise exception using errcode = '22023', message = 'PROVIDER_CHECKOUT_REF_REQUIRED';
  end if;
  if v_event_id is null then
    raise exception using errcode = '22023', message = 'PROVIDER_EVENT_ID_REQUIRED';
  end if;
  if v_event_type not in (
    'CHECKOUT_CREATED',
    'CHECKOUT_PAID',
    'CHECKOUT_CANCELED',
    'CHECKOUT_EXPIRED'
  ) then
    raise exception using errcode = '22023', message = 'UNSUPPORTED_CHECKOUT_EVENT';
  end if;
  if p_payload_sha256 is null or p_payload_sha256 !~ '^[0-9a-f]{64}$' then
    raise exception using errcode = '22023', message = 'INVALID_PAYLOAD_SHA256';
  end if;

  select * into v_intent
  from public.billing_checkout_intents i
  where i.provider_code = v_provider
    and i.provider_checkout_ref = v_checkout_ref
  for update;

  if v_intent.id is null then
    raise exception using errcode = 'P0002', message = 'CHECKOUT_INTENT_NOT_FOUND';
  end if;

  if v_event_type = 'CHECKOUT_CREATED' then
    return jsonb_build_object(
      'applied', false,
      'ignored', true,
      'reason', 'CHECKOUT_CREATED_ALREADY_BOUND_BY_INITIATION',
      'checkout_intent_id', v_intent.id,
      'organization_id', v_intent.organization_id,
      'plan_code', v_intent.plan_code,
      'billing_interval', v_intent.billing_interval,
      'checkout_status', v_intent.status
    );
  end if;

  if v_event_type = 'CHECKOUT_PAID' then
    if v_intent.status in ('canceled','expired','failed') then
      raise exception using
        errcode = '40900',
        message = 'CHECKOUT_TERMINAL_CONFLICT',
        detail = format('current_status=%s event_type=%s', v_intent.status, v_event_type);
    end if;

    v_target_status := 'completed';
    v_period_end := case v_intent.billing_interval
      when 'year' then v_effective_at + interval '1 year'
      else v_effective_at + interval '1 month'
    end;

    update public.billing_checkout_intents
    set
      status = v_target_status,
      updated_at = now()
    where id = v_intent.id;

    v_subscription_result := public.apply_subscription_authority_event(
      v_intent.organization_id,
      v_intent.plan_code,
      'active',
      'provider_webhook',
      v_provider || ':' || v_event_id,
      v_effective_at,
      v_effective_at,
      v_period_end,
      false,
      v_provider,
      nullif(btrim(coalesce(p_provider_customer_ref, '')), ''),
      null,
      p_payload_sha256
    );

    return jsonb_build_object(
      'applied', true,
      'ignored', false,
      'checkout_intent_id', v_intent.id,
      'organization_id', v_intent.organization_id,
      'plan_code', v_intent.plan_code,
      'billing_interval', v_intent.billing_interval,
      'checkout_status', v_target_status,
      'subscription', v_subscription_result
    );
  end if;

  v_target_status := case v_event_type
    when 'CHECKOUT_CANCELED' then 'canceled'
    when 'CHECKOUT_EXPIRED' then 'expired'
    else null
  end;

  if v_intent.status = 'completed' then
    return jsonb_build_object(
      'applied', false,
      'ignored', true,
      'reason', 'PAID_CHECKOUT_NOT_DOWNGRADED_BY_LATE_TERMINAL_EVENT',
      'checkout_intent_id', v_intent.id,
      'organization_id', v_intent.organization_id,
      'plan_code', v_intent.plan_code,
      'billing_interval', v_intent.billing_interval,
      'checkout_status', v_intent.status
    );
  end if;

  update public.billing_checkout_intents
  set
    status = v_target_status,
    updated_at = now()
  where id = v_intent.id
    and status in ('provider_pending','redirect_ready', v_target_status);

  return jsonb_build_object(
    'applied', true,
    'ignored', false,
    'checkout_intent_id', v_intent.id,
    'organization_id', v_intent.organization_id,
    'plan_code', v_intent.plan_code,
    'billing_interval', v_intent.billing_interval,
    'checkout_status', v_target_status
  );
end;
$$;

revoke execute on function public.apply_billing_checkout_webhook_event(text,text,text,text,text,timestamptz,text)
  from public, anon, authenticated;
grant execute on function public.apply_billing_checkout_webhook_event(text,text,text,text,text,timestamptz,text)
  to service_role;
