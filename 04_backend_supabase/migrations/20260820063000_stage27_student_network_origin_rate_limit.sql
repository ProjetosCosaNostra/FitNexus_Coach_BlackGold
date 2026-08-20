-- Stage 27: durable network-origin throttle for anonymous student access.
--
-- This boundary runs before possession-token validation in the Edge gateway. Raw network
-- origins are transient inputs only: PostgreSQL derives a keyed HMAC and persists only the
-- digest. Thresholds are database-owned so a caller cannot silently weaken the limiter.
--
-- Failure classes:
--   BGF-EDGE-INVALID-TOKEN-RATE-LIMIT-174
--   BGF-NETWORK-ORIGIN-RAW-PERSISTENCE-175
--   BGF-NETWORK-THROTTLE-CALLER-LIMIT-OVERRIDE-176
--   BGF-EDGE-SECRET-KEY-LEAK-177

create table if not exists private.student_access_network_origin_secret (
  singleton boolean primary key default true check (singleton),
  pepper bytea not null check (octet_length(pepper) = 32),
  created_at timestamptz not null default now()
);

insert into private.student_access_network_origin_secret (singleton, pepper)
values (true, extensions.gen_random_bytes(32))
on conflict (singleton) do nothing;

create table if not exists private.student_access_network_rate_buckets (
  origin_hash bytea not null check (octet_length(origin_hash) = 32),
  operation text not null check (operation in (
    'get_workout',
    'start_workout',
    'set_completion',
    'get_feedback_context',
    'submit_feedback'
  )),
  window_started_at timestamptz not null,
  request_count integer not null default 1 check (request_count >= 1),
  last_seen_at timestamptz not null default now(),
  primary key (origin_hash, operation, window_started_at)
);

create index if not exists student_access_network_rate_buckets_last_seen_idx
  on private.student_access_network_rate_buckets(last_seen_at);

revoke all on private.student_access_network_origin_secret
  from public, anon, authenticated, service_role;
revoke all on private.student_access_network_rate_buckets
  from public, anon, authenticated, service_role;

-- Stage 24 signal authority is extended with a dedicated network-origin burst signal.
-- The subject key is a truncated keyed digest, never the raw client/network address.
alter table private.student_access_security_signals
  drop constraint if exists student_access_security_signals_signal_type_check;
alter table private.student_access_security_signals
  add constraint student_access_security_signals_signal_type_check
  check (signal_type in (
    'rate_limit_burst',
    'command_replay_burst',
    'token_rotation_burst',
    'network_rate_limit_burst'
  ));

create or replace function private.student_access_network_rate_limit_v1(
  p_network_origin text,
  p_operation text
)
returns jsonb
language plpgsql
volatile
security definer
set search_path = ''
as $$
declare
  v_origin text;
  v_pepper bytea;
  v_origin_hash bytea;
  v_window timestamptz := date_trunc('minute', now());
  v_count integer := 0;
  v_limit integer;
  v_subject_key text;
begin
  v_limit := case p_operation
    when 'get_workout' then 120
    when 'start_workout' then 30
    when 'set_completion' then 120
    when 'get_feedback_context' then 90
    when 'submit_feedback' then 30
    else null
  end;

  if v_limit is null then
    return jsonb_build_object(
      'ok', false,
      'error', 'STUDENT_NETWORK_OPERATION_INVALID'
    );
  end if;

  if p_network_origin is null
     or char_length(btrim(p_network_origin)) < 3
     or char_length(btrim(p_network_origin)) > 64 then
    return jsonb_build_object(
      'ok', false,
      'error', 'STUDENT_NETWORK_ORIGIN_INVALID'
    );
  end if;

  begin
    v_origin := host(btrim(p_network_origin)::inet);
  exception
    when invalid_text_representation then
      return jsonb_build_object(
        'ok', false,
        'error', 'STUDENT_NETWORK_ORIGIN_INVALID'
      );
  end;

  select s.pepper
    into v_pepper
    from private.student_access_network_origin_secret s
   where s.singleton = true;

  if v_pepper is null or octet_length(v_pepper) <> 32 then
    raise exception using
      errcode = 'P0001',
      message = 'STUDENT_NETWORK_ORIGIN_SECRET_MISSING';
  end if;

  v_origin_hash := extensions.hmac(
    convert_to('fitnexus-student-origin-v1:' || v_origin, 'UTF8'),
    v_pepper,
    'sha256'
  );

  delete from private.student_access_network_rate_buckets
   where last_seen_at < now() - interval '2 days';

  insert into private.student_access_network_rate_buckets as b (
    origin_hash,
    operation,
    window_started_at,
    request_count,
    last_seen_at
  ) values (
    v_origin_hash,
    p_operation,
    v_window,
    1,
    now()
  )
  on conflict (origin_hash, operation, window_started_at)
  do update set
    request_count = b.request_count + 1,
    last_seen_at = now()
  returning request_count into v_count;

  if v_count > v_limit then
    v_subject_key := 'origin:' || substr(encode(v_origin_hash, 'hex'), 1, 32);

    insert into private.student_access_security_signals as s (
      signal_type,
      severity,
      subject_key,
      link_id,
      organization_id,
      student_id,
      operation,
      window_started_at,
      event_count,
      first_seen_at,
      last_seen_at
    ) values (
      'network_rate_limit_burst',
      'high',
      v_subject_key,
      null,
      null,
      null,
      p_operation,
      v_window,
      v_count,
      now(),
      now()
    )
    on conflict (signal_type, subject_key, operation, window_started_at)
    do update set
      severity = 'high',
      event_count = greatest(s.event_count, excluded.event_count),
      first_seen_at = least(s.first_seen_at, excluded.first_seen_at),
      last_seen_at = greatest(s.last_seen_at, excluded.last_seen_at),
      updated_at = now();

    return jsonb_build_object(
      'ok', false,
      'error', 'STUDENT_NETWORK_RATE_LIMITED',
      'request_count', v_count,
      'limit_per_minute', v_limit,
      'retry_after_seconds', greatest(1, 60 - extract(second from now())::integer)
    );
  end if;

  return jsonb_build_object(
    'ok', true,
    'request_count', v_count,
    'limit_per_minute', v_limit
  );
end;
$$;

revoke all on function private.student_access_network_rate_limit_v1(text,text)
  from public, anon, authenticated;
grant execute on function private.student_access_network_rate_limit_v1(text,text)
  to service_role;

-- PostgREST exposes the public schema. Keep the HTTP-facing bridge SECURITY INVOKER and
-- service-role-only; the private SECURITY DEFINER function owns the minimum required writes.
create or replace function public.check_student_access_network_rate_limit_v1(
  p_network_origin text,
  p_operation text
)
returns jsonb
language sql
volatile
security invoker
set search_path = ''
as $$
  select private.student_access_network_rate_limit_v1(p_network_origin, p_operation)
$$;

revoke all on function public.check_student_access_network_rate_limit_v1(text,text)
  from public, anon, authenticated;
grant execute on function public.check_student_access_network_rate_limit_v1(text,text)
  to service_role;

create or replace view private.student_access_security_posture_v1
with (security_invoker = true)
as
select
  now() as evaluated_at,
  case
    when exists (
      select 1
        from private.student_access_security_signals s
       where s.last_seen_at >= now() - interval '60 minutes'
         and s.severity in ('high','critical')
    ) then 'investigate'
    when exists (
      select 1
        from private.student_access_security_signals s
       where s.last_seen_at >= now() - interval '60 minutes'
         and s.severity = 'medium'
    ) then 'observe'
    else 'quiet'
  end as posture,
  (
    select count(*)::integer
      from private.student_access_security_signals s
     where s.last_seen_at >= now() - interval '60 minutes'
  ) as signals_60m,
  (
    select count(*)::integer
      from private.student_access_security_signals s
     where s.signal_type = 'rate_limit_burst'
       and s.last_seen_at >= now() - interval '60 minutes'
  ) as rate_limit_burst_signals_60m,
  (
    select count(*)::integer
      from private.student_access_security_signals s
     where s.signal_type = 'network_rate_limit_burst'
       and s.last_seen_at >= now() - interval '60 minutes'
  ) as network_rate_limit_burst_signals_60m,
  (
    select count(*)::integer
      from private.student_access_security_signals s
     where s.signal_type = 'command_replay_burst'
       and s.last_seen_at >= now() - interval '60 minutes'
  ) as command_replay_burst_signals_60m,
  (
    select count(*)::integer
      from private.student_access_security_signals s
     where s.signal_type = 'token_rotation_burst'
       and s.last_seen_at >= now() - interval '60 minutes'
  ) as token_rotation_burst_signals_60m,
  (
    select count(*)::integer
      from private.student_access_security_events e
     where e.occurred_at >= now() - interval '15 minutes'
  ) as security_events_15m,
  (
    select count(*)::integer
      from private.student_access_security_events e
     where e.outcome = 'rate_limited'
       and e.occurred_at >= now() - interval '15 minutes'
  ) as rate_limited_events_15m,
  (
    select count(*)::integer
      from private.student_access_security_events e
     where e.outcome = 'replay'
       and e.occurred_at >= now() - interval '15 minutes'
  ) as replay_events_15m;

revoke all on private.student_access_security_posture_v1 from public, anon, authenticated;
grant select on private.student_access_security_posture_v1 to service_role;

comment on table private.student_access_network_origin_secret is
  'Runtime-generated HMAC pepper for network-origin pseudonymization. Never exposed to clients or stored in repository source.';
comment on table private.student_access_network_rate_buckets is
  'Durable student gateway network-origin rate buckets keyed only by HMAC digest; raw network origins are never persisted.';
comment on function public.check_student_access_network_rate_limit_v1(text,text) is
  'Service-role-only SECURITY INVOKER bridge for the Edge student gateway network-origin throttle.';
