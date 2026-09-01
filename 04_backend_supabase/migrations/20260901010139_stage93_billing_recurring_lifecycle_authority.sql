-- Remote promotion ledger version: 20260901010139
-- Migration name: stage93_billing_recurring_lifecycle_authority
-- Source candidate: operations/billing_recurring_lifecycle_authority_v1.sql

alter table public.organization_subscriptions
  add column if not exists billing_interval text;

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'organization_subscriptions_billing_interval_chk'
      and conrelid = 'public.organization_subscriptions'::regclass
  ) then
    alter table public.organization_subscriptions
      add constraint organization_subscriptions_billing_interval_chk
      check (billing_interval is null or billing_interval in ('month','year'));
  end if;
end;
$$;

create or replace function public.bind_billing_provider_subscription(
  p_provider_code text,
  p_provider_subscription_ref text,
  p_provider_customer_ref text,
  p_provider_event_id text,
  p_payload_sha256 text,
  p_provider_cycle text,
  p_next_due_date date default null
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_provider text;
  v_subscription_ref text;
  v_customer_ref text;
  v_event_id text;
  v_cycle text;
  v_interval text;
  v_candidate_count integer;
  v_organization_id uuid;
  v_current public.organization_subscriptions%rowtype;
  v_period_end timestamptz;
  v_result jsonb;
begin
  v_provider := nullif(btrim(coalesce(p_provider_code, '')), '');
  v_subscription_ref := nullif(btrim(coalesce(p_provider_subscription_ref, '')), '');
  v_customer_ref := nullif(btrim(coalesce(p_provider_customer_ref, '')), '');
  v_event_id := nullif(btrim(coalesce(p_provider_event_id, '')), '');
  v_cycle := upper(nullif(btrim(coalesce(p_provider_cycle, '')), ''));

  if v_provider is null or not exists (
    select 1 from public.billing_provider_registry p
    where p.provider_code = v_provider
  ) then
    raise exception using errcode = '22023', message = 'UNKNOWN_BILLING_PROVIDER';
  end if;
  if v_subscription_ref is null then
    raise exception using errcode = '22023', message = 'PROVIDER_SUBSCRIPTION_REF_REQUIRED';
  end if;
  if v_customer_ref is null then
    raise exception using errcode = '22023', message = 'PROVIDER_CUSTOMER_REF_REQUIRED';
  end if;
  if v_event_id is null then
    raise exception using errcode = '22023', message = 'PROVIDER_EVENT_ID_REQUIRED';
  end if;
  if p_payload_sha256 is null or p_payload_sha256 !~ '^[0-9a-f]{64}$' then
    raise exception using errcode = '22023', message = 'INVALID_PAYLOAD_SHA256';
  end if;

  v_interval := case v_cycle
    when 'MONTHLY' then 'month'
    when 'YEARLY' then 'year'
    else null
  end;
  if v_interval is null then
    raise exception using
      errcode = '22023',
      message = 'UNSUPPORTED_PROVIDER_BILLING_CYCLE',
      detail = coalesce(v_cycle, 'null');
  end if;

  select count(*)::int, min(s.organization_id)
  into v_candidate_count, v_organization_id
  from public.organization_subscriptions s
  where s.provider = v_provider
    and s.provider_customer_ref = v_customer_ref
    and (s.provider_subscription_ref is null or s.provider_subscription_ref = v_subscription_ref)
    and exists (
      select 1
      from public.billing_checkout_intents i
      where i.organization_id = s.organization_id
        and i.provider_code = v_provider
        and i.status = 'completed'
        and i.plan_code = s.plan_code
        and i.billing_interval = v_interval
    );

  if v_candidate_count = 0 then
    raise exception using errcode = 'P0002', message = 'SUBSCRIPTION_BINDING_CANDIDATE_NOT_FOUND';
  end if;
  if v_candidate_count <> 1 then
    raise exception using
      errcode = '40900',
      message = 'SUBSCRIPTION_BINDING_AMBIGUOUS',
      detail = format('candidate_count=%s', v_candidate_count);
  end if;

  select * into v_current
  from public.organization_subscriptions s
  where s.organization_id = v_organization_id
  for update;

  if v_current.provider_subscription_ref is not null
    and v_current.provider_subscription_ref <> v_subscription_ref
  then
    raise exception using errcode = '40900', message = 'PROVIDER_SUBSCRIPTION_REF_CONFLICT';
  end if;

  v_period_end := case
    when p_next_due_date is null then v_current.current_period_end
    when v_current.current_period_start is null then
      (p_next_due_date::timestamp at time zone 'UTC')
    when (p_next_due_date::timestamp at time zone 'UTC') > v_current.current_period_start then
      (p_next_due_date::timestamp at time zone 'UTC')
    else v_current.current_period_end
  end;

  v_result := public.apply_subscription_authority_event(
    v_current.organization_id,
    v_current.plan_code,
    v_current.status,
    'provider_webhook',
    v_provider || ':' || v_event_id,
    now(),
    v_current.current_period_start,
    v_period_end,
    v_current.cancel_at_period_end,
    v_provider,
    v_customer_ref,
    v_subscription_ref,
    p_payload_sha256
  );

  update public.organization_subscriptions
  set
    billing_interval = v_interval,
    updated_at = now()
  where organization_id = v_current.organization_id;

  return jsonb_build_object(
    'applied', coalesce((v_result ->> 'applied')::boolean, false),
    'idempotent_replay', coalesce((v_result ->> 'idempotent_replay')::boolean, false),
    'organization_id', v_current.organization_id,
    'plan_code', v_current.plan_code,
    'provider_code', v_provider,
    'provider_subscription_ref', v_subscription_ref,
    'billing_interval', v_interval,
    'current_period_end', v_period_end
  );
end;
$$;

revoke execute on function public.bind_billing_provider_subscription(text,text,text,text,text,text,date)
  from public, anon, authenticated;
grant execute on function public.bind_billing_provider_subscription(text,text,text,text,text,text,date)
  to service_role;

create or replace function public.apply_billing_subscription_lifecycle_event(
  p_provider_code text,
  p_provider_subscription_ref text,
  p_provider_event_id text,
  p_event_type text,
  p_payload_sha256 text,
  p_payment_due_date date default null,
  p_next_due_date date default null
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_provider text;
  v_subscription_ref text;
  v_event_id text;
  v_event_type text;
  v_current public.organization_subscriptions%rowtype;
  v_target_status text;
  v_period_start timestamptz;
  v_period_end timestamptz;
  v_current_start_date date;
  v_current_end_date date;
  v_result jsonb;
begin
  v_provider := nullif(btrim(coalesce(p_provider_code, '')), '');
  v_subscription_ref := nullif(btrim(coalesce(p_provider_subscription_ref, '')), '');
  v_event_id := nullif(btrim(coalesce(p_provider_event_id, '')), '');
  v_event_type := upper(nullif(btrim(coalesce(p_event_type, '')), ''));

  if v_provider is null or not exists (
    select 1 from public.billing_provider_registry p
    where p.provider_code = v_provider
  ) then
    raise exception using errcode = '22023', message = 'UNKNOWN_BILLING_PROVIDER';
  end if;
  if v_subscription_ref is null then
    raise exception using errcode = '22023', message = 'PROVIDER_SUBSCRIPTION_REF_REQUIRED';
  end if;
  if v_event_id is null then
    raise exception using errcode = '22023', message = 'PROVIDER_EVENT_ID_REQUIRED';
  end if;
  if p_payload_sha256 is null or p_payload_sha256 !~ '^[0-9a-f]{64}$' then
    raise exception using errcode = '22023', message = 'INVALID_PAYLOAD_SHA256';
  end if;

  if v_event_type not in (
    'SUBSCRIPTION_UPDATED',
    'SUBSCRIPTION_INACTIVATED',
    'SUBSCRIPTION_DELETED',
    'PAYMENT_CONFIRMED',
    'PAYMENT_RECEIVED',
    'PAYMENT_OVERDUE',
    'PAYMENT_REFUNDED',
    'PAYMENT_CHARGEBACK_REQUESTED',
    'PAYMENT_CREDIT_CARD_CAPTURE_REFUSED',
    'PAYMENT_REPROVED_BY_RISK_ANALYSIS'
  ) then
    return jsonb_build_object(
      'applied', false,
      'ignored', true,
      'reason', 'EVENT_NOT_STATEFUL_FOR_FITNEXUS',
      'provider_event_id', v_event_id,
      'event_type', v_event_type
    );
  end if;

  select * into v_current
  from public.organization_subscriptions s
  where s.provider = v_provider
    and s.provider_subscription_ref = v_subscription_ref
  for update;

  if v_current.organization_id is null then
    raise exception using errcode = 'P0002', message = 'PROVIDER_SUBSCRIPTION_NOT_BOUND';
  end if;

  if v_current.billing_interval not in ('month','year') then
    raise exception using errcode = '42501', message = 'BILLING_INTERVAL_NOT_BOUND';
  end if;

  v_current_start_date := case
    when v_current.current_period_start is null then null
    else (v_current.current_period_start at time zone 'UTC')::date
  end;
  v_current_end_date := case
    when v_current.current_period_end is null then null
    else (v_current.current_period_end at time zone 'UTC')::date
  end;

  if v_event_type = 'SUBSCRIPTION_UPDATED' then
    return jsonb_build_object(
      'applied', false,
      'ignored', true,
      'reason', 'SUBSCRIPTION_UPDATE_REQUIRES_NO_ACCESS_MUTATION',
      'organization_id', v_current.organization_id,
      'event_type', v_event_type,
      'next_due_date_observed', p_next_due_date
    );
  end if;

  if v_event_type in ('SUBSCRIPTION_INACTIVATED','SUBSCRIPTION_DELETED') then
    v_result := public.apply_subscription_authority_event(
      v_current.organization_id,
      v_current.plan_code,
      'canceled',
      'provider_webhook',
      v_provider || ':' || v_event_id,
      now(),
      v_current.current_period_start,
      v_current.current_period_end,
      true,
      v_provider,
      v_current.provider_customer_ref,
      v_subscription_ref,
      p_payload_sha256
    );

    return jsonb_build_object(
      'applied', coalesce((v_result ->> 'applied')::boolean, false),
      'idempotent_replay', coalesce((v_result ->> 'idempotent_replay')::boolean, false),
      'organization_id', v_current.organization_id,
      'event_type', v_event_type,
      'subscription_status', 'canceled'
    );
  end if;

  if p_payment_due_date is null then
    return jsonb_build_object(
      'applied', false,
      'ignored', true,
      'reason', 'PAYMENT_DUE_DATE_REQUIRED_FOR_SAFE_PERIOD_RECONCILIATION',
      'organization_id', v_current.organization_id,
      'event_type', v_event_type
    );
  end if;

  if v_current_start_date is not null and p_payment_due_date < v_current_start_date then
    return jsonb_build_object(
      'applied', false,
      'ignored', true,
      'reason', 'HISTORICAL_PAYMENT_EVENT_IGNORED',
      'organization_id', v_current.organization_id,
      'event_type', v_event_type,
      'payment_due_date', p_payment_due_date,
      'current_period_start', v_current_start_date
    );
  end if;

  if v_event_type in ('PAYMENT_CONFIRMED','PAYMENT_RECEIVED') then
    v_period_start := p_payment_due_date::timestamp at time zone 'UTC';
    v_period_end := case v_current.billing_interval
      when 'year' then v_period_start + interval '1 year'
      else v_period_start + interval '1 month'
    end;
    v_target_status := 'active';
  elsif v_event_type = 'PAYMENT_OVERDUE' then
    if p_payment_due_date > current_date then
      return jsonb_build_object(
        'applied', false,
        'ignored', true,
        'reason', 'FUTURE_PAYMENT_CANNOT_BE_OVERDUE',
        'organization_id', v_current.organization_id,
        'payment_due_date', p_payment_due_date
      );
    end if;
    v_period_start := v_current.current_period_start;
    v_period_end := v_current.current_period_end;
    v_target_status := 'past_due';
  elsif v_event_type in (
    'PAYMENT_CREDIT_CARD_CAPTURE_REFUSED',
    'PAYMENT_REPROVED_BY_RISK_ANALYSIS'
  ) then
    if p_payment_due_date > current_date then
      return jsonb_build_object(
        'applied', false,
        'ignored', true,
        'reason', 'PRE_DUE_PAYMENT_FAILURE_DOES_NOT_REVOKE_ACCESS',
        'organization_id', v_current.organization_id,
        'event_type', v_event_type,
        'payment_due_date', p_payment_due_date
      );
    end if;
    v_period_start := v_current.current_period_start;
    v_period_end := v_current.current_period_end;
    v_target_status := 'past_due';
  else
    if v_current_start_date is null
      or v_current_end_date is null
      or p_payment_due_date < v_current_start_date
      or p_payment_due_date >= v_current_end_date
    then
      return jsonb_build_object(
        'applied', false,
        'ignored', true,
        'reason', 'HISTORICAL_REVERSAL_DOES_NOT_REVOKE_CURRENT_PERIOD',
        'organization_id', v_current.organization_id,
        'event_type', v_event_type,
        'payment_due_date', p_payment_due_date
      );
    end if;
    v_period_start := v_current.current_period_start;
    v_period_end := v_current.current_period_end;
    v_target_status := 'past_due';
  end if;

  v_result := public.apply_subscription_authority_event(
    v_current.organization_id,
    v_current.plan_code,
    v_target_status,
    'provider_webhook',
    v_provider || ':' || v_event_id,
    now(),
    v_period_start,
    v_period_end,
    false,
    v_provider,
    v_current.provider_customer_ref,
    v_subscription_ref,
    p_payload_sha256
  );

  return jsonb_build_object(
    'applied', coalesce((v_result ->> 'applied')::boolean, false),
    'idempotent_replay', coalesce((v_result ->> 'idempotent_replay')::boolean, false),
    'organization_id', v_current.organization_id,
    'plan_code', v_current.plan_code,
    'event_type', v_event_type,
    'subscription_status', v_target_status,
    'billing_interval', v_current.billing_interval,
    'current_period_start', v_period_start,
    'current_period_end', v_period_end
  );
end;
$$;

revoke execute on function public.apply_billing_subscription_lifecycle_event(text,text,text,text,text,date,date)
  from public, anon, authenticated;
grant execute on function public.apply_billing_subscription_lifecycle_event(text,text,text,text,text,date,date)
  to service_role;
