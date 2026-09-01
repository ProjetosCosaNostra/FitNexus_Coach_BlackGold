-- Candidate authority for Google Play subscription verification.
-- Publication-critical Android monetization path.
-- No remote migration is performed by this file alone.

create table if not exists public.google_play_purchase_receipts (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  user_id uuid not null,
  product_id text not null,
  purchase_token_sha256 text not null unique,
  purchase_id text,
  subscription_state text not null,
  start_time timestamptz,
  expiry_time timestamptz,
  auto_renewing boolean not null default false,
  raw_response_sha256 text not null,
  last_verified_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint google_play_purchase_receipts_token_hash_chk
    check (purchase_token_sha256 ~ '^[0-9a-f]{64}$'),
  constraint google_play_purchase_receipts_response_hash_chk
    check (raw_response_sha256 ~ '^[0-9a-f]{64}$'),
  constraint google_play_purchase_receipts_product_chk
    check (product_id in ('fitnexus_solo','fitnexus_pro','fitnexus_studio'))
);

alter table public.google_play_purchase_receipts enable row level security;
revoke all on table public.google_play_purchase_receipts from public, anon, authenticated;
grant select, insert, update on table public.google_play_purchase_receipts to service_role;

create index if not exists google_play_purchase_receipts_org_idx
  on public.google_play_purchase_receipts(organization_id, last_verified_at desc);
create index if not exists google_play_purchase_receipts_user_idx
  on public.google_play_purchase_receipts(user_id, last_verified_at desc);

create or replace function public.apply_google_play_subscription_verification(
  p_organization_id uuid,
  p_user_id uuid,
  p_product_id text,
  p_purchase_token_sha256 text,
  p_purchase_id text,
  p_subscription_state text,
  p_start_time timestamptz,
  p_expiry_time timestamptz,
  p_auto_renewing boolean,
  p_raw_response_sha256 text
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_plan_code text;
  v_status text;
  v_active boolean;
  v_result jsonb;
begin
  if p_organization_id is null or p_user_id is null then
    raise exception using errcode = '22023', message = 'GOOGLE_PLAY_ORGANIZATION_AND_USER_REQUIRED';
  end if;

  if not exists (
    select 1
    from public.organization_members m
    where m.organization_id = p_organization_id
      and m.user_id = p_user_id
  ) then
    raise exception using errcode = '42501', message = 'GOOGLE_PLAY_ORGANIZATION_MEMBERSHIP_REQUIRED';
  end if;

  v_plan_code := case p_product_id
    when 'fitnexus_solo' then 'solo'
    when 'fitnexus_pro' then 'pro'
    when 'fitnexus_studio' then 'studio'
    else null
  end;
  if v_plan_code is null then
    raise exception using errcode = '22023', message = 'GOOGLE_PLAY_PRODUCT_NOT_ALLOWED';
  end if;

  if p_purchase_token_sha256 is null or p_purchase_token_sha256 !~ '^[0-9a-f]{64}$' then
    raise exception using errcode = '22023', message = 'GOOGLE_PLAY_PURCHASE_TOKEN_HASH_INVALID';
  end if;
  if p_raw_response_sha256 is null or p_raw_response_sha256 !~ '^[0-9a-f]{64}$' then
    raise exception using errcode = '22023', message = 'GOOGLE_PLAY_RESPONSE_HASH_INVALID';
  end if;

  v_active := p_expiry_time is not null
    and p_expiry_time > now()
    and p_subscription_state in (
      'SUBSCRIPTION_STATE_ACTIVE',
      'SUBSCRIPTION_STATE_IN_GRACE_PERIOD',
      'SUBSCRIPTION_STATE_CANCELED'
    );

  v_status := case
    when v_active and p_subscription_state = 'SUBSCRIPTION_STATE_IN_GRACE_PERIOD' then 'grace'
    when v_active then 'active'
    when p_subscription_state = 'SUBSCRIPTION_STATE_ON_HOLD' then 'past_due'
    when p_subscription_state = 'SUBSCRIPTION_STATE_EXPIRED' then 'expired'
    else 'canceled'
  end;

  insert into public.google_play_purchase_receipts (
    organization_id,
    user_id,
    product_id,
    purchase_token_sha256,
    purchase_id,
    subscription_state,
    start_time,
    expiry_time,
    auto_renewing,
    raw_response_sha256,
    last_verified_at,
    updated_at
  ) values (
    p_organization_id,
    p_user_id,
    p_product_id,
    p_purchase_token_sha256,
    nullif(btrim(coalesce(p_purchase_id, '')), ''),
    p_subscription_state,
    p_start_time,
    p_expiry_time,
    coalesce(p_auto_renewing, false),
    p_raw_response_sha256,
    now(),
    now()
  )
  on conflict (purchase_token_sha256) do update set
    organization_id = excluded.organization_id,
    user_id = excluded.user_id,
    product_id = excluded.product_id,
    purchase_id = excluded.purchase_id,
    subscription_state = excluded.subscription_state,
    start_time = excluded.start_time,
    expiry_time = excluded.expiry_time,
    auto_renewing = excluded.auto_renewing,
    raw_response_sha256 = excluded.raw_response_sha256,
    last_verified_at = now(),
    updated_at = now();

  v_result := public.apply_subscription_authority_event(
    p_organization_id,
    v_plan_code,
    v_status,
    'provider_webhook',
    'google_play:' || p_purchase_token_sha256,
    now(),
    p_start_time,
    p_expiry_time,
    not coalesce(p_auto_renewing, false),
    'google_play',
    p_user_id::text,
    p_purchase_token_sha256,
    p_raw_response_sha256
  );

  return jsonb_build_object(
    'ok', true,
    'organization_id', p_organization_id,
    'plan_code', v_plan_code,
    'subscription_state', p_subscription_state,
    'entitlement_active', v_active,
    'status', v_status,
    'expiry_time', p_expiry_time,
    'authority', v_result
  );
end;
$$;

revoke execute on function public.apply_google_play_subscription_verification(
  uuid,uuid,text,text,text,text,timestamptz,timestamptz,boolean,text
) from public, anon, authenticated;
grant execute on function public.apply_google_play_subscription_verification(
  uuid,uuid,text,text,text,text,timestamptz,timestamptz,boolean,text
) to service_role;
