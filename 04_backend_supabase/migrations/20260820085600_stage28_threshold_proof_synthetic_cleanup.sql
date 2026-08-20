-- Stage 28 controlled threshold-proof cleanup.
-- Failure class: BGF-SYNTHETIC-SECURITY-PROOF-RESIDUE-186
--
-- The one-shot Edge threshold proof intentionally created two pseudonymous start_workout
-- rate buckets/signals while proving HTTP 429 at request 31. This migration removes only
-- those exact synthetic rows. It never stores or matches a raw network origin and fails
-- closed unless the expected evidence cardinality is exactly 2 buckets + 2 signals.

do $$
declare
  v_bucket_count integer;
  v_signal_count integer;
  v_remaining_buckets integer;
  v_remaining_signals integer;
begin
  select count(*) into v_bucket_count
  from private.student_access_network_rate_buckets
  where operation = 'start_workout'
    and request_count = 31
    and (
      (window_started_at = timestamptz '2026-08-20 08:53:00+00'
       and last_seen_at = timestamptz '2026-08-20 08:53:15.673219+00')
      or
      (window_started_at = timestamptz '2026-08-20 08:54:00+00'
       and last_seen_at = timestamptz '2026-08-20 08:54:14.980613+00')
    );

  select count(*) into v_signal_count
  from private.student_access_security_signals
  where signal_type = 'network_rate_limit_burst'
    and severity = 'high'
    and operation = 'start_workout'
    and event_count = 31
    and link_id is null
    and organization_id is null
    and student_id is null
    and (
      (window_started_at = timestamptz '2026-08-20 08:53:00+00'
       and last_seen_at = timestamptz '2026-08-20 08:53:15.673219+00')
      or
      (window_started_at = timestamptz '2026-08-20 08:54:00+00'
       and last_seen_at = timestamptz '2026-08-20 08:54:14.980613+00')
    );

  if v_bucket_count <> 2 or v_signal_count <> 2 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE28_SYNTHETIC_CLEANUP_SELECTOR_MISMATCH';
  end if;

  delete from private.student_access_security_signals
  where signal_type = 'network_rate_limit_burst'
    and severity = 'high'
    and operation = 'start_workout'
    and event_count = 31
    and link_id is null
    and organization_id is null
    and student_id is null
    and (
      (window_started_at = timestamptz '2026-08-20 08:53:00+00'
       and last_seen_at = timestamptz '2026-08-20 08:53:15.673219+00')
      or
      (window_started_at = timestamptz '2026-08-20 08:54:00+00'
       and last_seen_at = timestamptz '2026-08-20 08:54:14.980613+00')
    );

  delete from private.student_access_network_rate_buckets
  where operation = 'start_workout'
    and request_count = 31
    and (
      (window_started_at = timestamptz '2026-08-20 08:53:00+00'
       and last_seen_at = timestamptz '2026-08-20 08:53:15.673219+00')
      or
      (window_started_at = timestamptz '2026-08-20 08:54:00+00'
       and last_seen_at = timestamptz '2026-08-20 08:54:14.980613+00')
    );

  select count(*) into v_remaining_buckets
  from private.student_access_network_rate_buckets
  where operation = 'start_workout'
    and request_count = 31
    and window_started_at in (
      timestamptz '2026-08-20 08:53:00+00',
      timestamptz '2026-08-20 08:54:00+00'
    );

  select count(*) into v_remaining_signals
  from private.student_access_security_signals
  where signal_type = 'network_rate_limit_burst'
    and operation = 'start_workout'
    and event_count = 31
    and window_started_at in (
      timestamptz '2026-08-20 08:53:00+00',
      timestamptz '2026-08-20 08:54:00+00'
    );

  if v_remaining_buckets <> 0 or v_remaining_signals <> 0 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE28_SYNTHETIC_CLEANUP_INCOMPLETE';
  end if;
end;
$$;
