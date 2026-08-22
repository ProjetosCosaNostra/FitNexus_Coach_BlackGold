-- Stage 35: privacy-minimized external alert delivery receipt store and service bridge.
--
-- Repository promotion only. Remote application is forbidden until a later deployment/proof
-- seal authorizes the exact migration and dispatcher lifecycle. No Stage33 privilege,
-- transport, proof or cleanup boundary is changed here.
--
-- Failure classes:
--   BGF-STAGE35-ALERT-CLAIM-DUPLICATE-275
--   BGF-STAGE35-ALERT-UNKNOWN-DELIVERY-RETRY-276
--   BGF-STAGE35-ALERT-RECEIPT-SCOPE-277
--   BGF-STAGE35-ALERT-PROOF-CUSTOMER-CROSSOVER-278

create table if not exists private.student_access_alert_delivery_receipts (
  signal_id bigint not null
    references private.student_access_security_signals(id) on delete cascade,
  provider text not null check (provider = 'telegram_bot_api'),
  destination_fingerprint text not null
    check (destination_fingerprint ~ '^[0-9a-f]{64}$'),
  status text not null check (status in ('pending','delivered','failed','unknown')),
  attempt_number integer not null check (attempt_number between 1 and 3),
  claim_token uuid not null,
  lease_expires_at timestamptz,
  provider_message_id bigint check (provider_message_id is null or provider_message_id > 0),
  controlled_proof_marker text,
  last_error_code text,
  delivered_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (signal_id, provider, destination_fingerprint),
  check (
    controlled_proof_marker is null
    or controlled_proof_marker = 'fitnexus-stage34-alert-delivery-proof-v1'
  ),
  check (
    (status = 'delivered' and provider_message_id is not null and delivered_at is not null and lease_expires_at is null)
    or (status <> 'delivered' and provider_message_id is null and delivered_at is null)
  ),
  check (
    (status = 'pending' and lease_expires_at is not null)
    or (status <> 'pending' and lease_expires_at is null)
  )
);

create unique index if not exists student_access_alert_delivery_claim_token_uidx
  on private.student_access_alert_delivery_receipts(claim_token);
create index if not exists student_access_alert_delivery_status_idx
  on private.student_access_alert_delivery_receipts(status, updated_at);

revoke all on private.student_access_alert_delivery_receipts
  from public, anon, authenticated, service_role;

create or replace function private.claim_student_access_alert_delivery_v1(
  p_destination_fingerprint text,
  p_controlled_proof_marker text default null
)
returns jsonb
language plpgsql
volatile
security definer
set search_path = ''
as $$
declare
  v_signal private.student_access_security_signals%rowtype;
  v_claim_token uuid;
  v_attempt integer;
  v_updated integer;
begin
  if p_destination_fingerprint is null
     or p_destination_fingerprint !~ '^[0-9a-f]{64}$' then
    raise exception using errcode = '22023', message = 'ALERT_DESTINATION_FINGERPRINT_INVALID';
  end if;

  if p_controlled_proof_marker is not null
     and p_controlled_proof_marker <> 'fitnexus-stage34-alert-delivery-proof-v1' then
    raise exception using errcode = '22023', message = 'ALERT_CONTROLLED_PROOF_MARKER_INVALID';
  end if;

  -- A lost dispatcher after claiming is delivery-ambiguous. Expired pending claims become
  -- terminal UNKNOWN and are never automatically reclaimed, preventing blind duplicate sends.
  update private.student_access_alert_delivery_receipts
     set status = 'unknown',
         lease_expires_at = null,
         last_error_code = 'CLAIM_LEASE_EXPIRED_DELIVERY_UNKNOWN',
         updated_at = now()
   where status = 'pending'
     and lease_expires_at < now();

  for v_signal in
    select s.*
      from private.student_access_security_signals s
     where s.severity in ('high','critical')
       and (
         (p_controlled_proof_marker is null and s.subject_key not like 'proof:%')
         or (
           p_controlled_proof_marker is not null
           and s.signal_type = 'network_rate_limit_burst'
           and s.severity = 'high'
           and s.subject_key = 'proof:' || p_controlled_proof_marker
         )
       )
       and not exists (
         select 1
           from private.student_access_alert_delivery_receipts r
          where r.signal_id = s.id
            and r.provider = 'telegram_bot_api'
            and r.destination_fingerprint = p_destination_fingerprint
            and r.status in ('delivered','pending','unknown')
       )
     order by s.last_seen_at asc, s.id asc
  loop
    v_claim_token := extensions.gen_random_uuid();

    insert into private.student_access_alert_delivery_receipts as r (
      signal_id,
      provider,
      destination_fingerprint,
      status,
      attempt_number,
      claim_token,
      lease_expires_at,
      provider_message_id,
      controlled_proof_marker,
      last_error_code,
      delivered_at,
      created_at,
      updated_at
    ) values (
      v_signal.id,
      'telegram_bot_api',
      p_destination_fingerprint,
      'pending',
      1,
      v_claim_token,
      now() + interval '2 minutes',
      null,
      p_controlled_proof_marker,
      null,
      null,
      now(),
      now()
    )
    on conflict (signal_id, provider, destination_fingerprint)
    do update set
      status = 'pending',
      attempt_number = r.attempt_number + 1,
      claim_token = excluded.claim_token,
      lease_expires_at = excluded.lease_expires_at,
      controlled_proof_marker = excluded.controlled_proof_marker,
      last_error_code = null,
      updated_at = now()
    where r.status = 'failed'
      and r.attempt_number < 3;

    get diagnostics v_updated = row_count;
    if v_updated = 1 then
      select r.attempt_number
        into v_attempt
        from private.student_access_alert_delivery_receipts r
       where r.signal_id = v_signal.id
         and r.provider = 'telegram_bot_api'
         and r.destination_fingerprint = p_destination_fingerprint
         and r.claim_token = v_claim_token
         and r.status = 'pending';

      if v_attempt is not null then
        return jsonb_build_object(
          'ok', true,
          'claimed', true,
          'claim_token', v_claim_token,
          'attempt_number', v_attempt,
          'signal_id', v_signal.id,
          'signal_type', v_signal.signal_type,
          'severity', v_signal.severity,
          'operation', v_signal.operation,
          'event_count', v_signal.event_count,
          'window_started_at', v_signal.window_started_at,
          'first_seen_at', v_signal.first_seen_at,
          'last_seen_at', v_signal.last_seen_at,
          'controlled_proof_marker', p_controlled_proof_marker
        );
      end if;
    end if;
  end loop;

  return jsonb_build_object('ok', true, 'claimed', false);
end;
$$;

create or replace function private.record_student_access_alert_delivery_v1(
  p_claim_token uuid,
  p_outcome text,
  p_provider_message_id bigint default null,
  p_error_code text default null
)
returns jsonb
language plpgsql
volatile
security definer
set search_path = ''
as $$
declare
  v_receipt private.student_access_alert_delivery_receipts%rowtype;
begin
  if p_claim_token is null then
    raise exception using errcode = '22023', message = 'ALERT_CLAIM_TOKEN_REQUIRED';
  end if;
  if p_outcome not in ('delivered','failed','unknown') then
    raise exception using errcode = '22023', message = 'ALERT_DELIVERY_OUTCOME_INVALID';
  end if;
  if p_outcome = 'delivered' and (p_provider_message_id is null or p_provider_message_id <= 0) then
    raise exception using errcode = '22023', message = 'ALERT_PROVIDER_MESSAGE_ID_REQUIRED';
  end if;
  if p_outcome <> 'delivered' and p_provider_message_id is not null then
    raise exception using errcode = '22023', message = 'ALERT_PROVIDER_MESSAGE_ID_FORBIDDEN_FOR_NONDELIVERY';
  end if;
  if p_outcome <> 'delivered'
     and (p_error_code is null or p_error_code !~ '^[A-Z0-9_]{3,96}$') then
    raise exception using errcode = '22023', message = 'ALERT_ERROR_CODE_INVALID';
  end if;

  select r.*
    into v_receipt
    from private.student_access_alert_delivery_receipts r
   where r.claim_token = p_claim_token
     and r.status = 'pending'
   for update;

  if not found then
    raise exception using errcode = 'P0001', message = 'ALERT_ACTIVE_CLAIM_NOT_FOUND';
  end if;

  update private.student_access_alert_delivery_receipts r
     set status = p_outcome,
         lease_expires_at = null,
         provider_message_id = case when p_outcome = 'delivered' then p_provider_message_id else null end,
         last_error_code = case when p_outcome = 'delivered' then null else p_error_code end,
         delivered_at = case when p_outcome = 'delivered' then now() else null end,
         updated_at = now()
   where r.claim_token = p_claim_token;

  return jsonb_build_object(
    'ok', true,
    'signal_id', v_receipt.signal_id,
    'outcome', p_outcome,
    'attempt_number', v_receipt.attempt_number,
    'controlled_proof_marker', v_receipt.controlled_proof_marker
  );
end;
$$;

revoke all on function private.claim_student_access_alert_delivery_v1(text,text)
  from public, anon, authenticated;
revoke all on function private.record_student_access_alert_delivery_v1(uuid,text,bigint,text)
  from public, anon, authenticated;
grant execute on function private.claim_student_access_alert_delivery_v1(text,text)
  to service_role;
grant execute on function private.record_student_access_alert_delivery_v1(uuid,text,bigint,text)
  to service_role;

-- HTTP-facing bridges remain SECURITY INVOKER and service-role-only. The private
-- SECURITY DEFINER functions own the minimum table access and never expose subject_key,
-- organization_id, student_id, link_id, raw token or raw network-origin material.
create or replace function public.claim_student_access_alert_delivery_v1(
  p_destination_fingerprint text,
  p_controlled_proof_marker text default null
)
returns jsonb
language sql
volatile
security invoker
set search_path = ''
as $$
  select private.claim_student_access_alert_delivery_v1(
    p_destination_fingerprint,
    p_controlled_proof_marker
  )
$$;

create or replace function public.record_student_access_alert_delivery_v1(
  p_claim_token uuid,
  p_outcome text,
  p_provider_message_id bigint default null,
  p_error_code text default null
)
returns jsonb
language sql
volatile
security invoker
set search_path = ''
as $$
  select private.record_student_access_alert_delivery_v1(
    p_claim_token,
    p_outcome,
    p_provider_message_id,
    p_error_code
  )
$$;

revoke all on function public.claim_student_access_alert_delivery_v1(text,text)
  from public, anon, authenticated;
revoke all on function public.record_student_access_alert_delivery_v1(uuid,text,bigint,text)
  from public, anon, authenticated;
grant execute on function public.claim_student_access_alert_delivery_v1(text,text)
  to service_role;
grant execute on function public.record_student_access_alert_delivery_v1(uuid,text,bigint,text)
  to service_role;

comment on table private.student_access_alert_delivery_receipts is
  'Privacy-minimized external alert delivery receipts. Provider secrets, destination IDs, raw provider responses, raw tokens and raw network origins are never persisted.';
