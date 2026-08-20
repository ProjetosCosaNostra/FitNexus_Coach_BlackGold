-- Stage 27: remote verification interlock for the durable network-origin limiter.
--
-- This migration intentionally performs a controlled write-path exercise inside the
-- migration transaction, validates the 120/min get_workout threshold, and removes all
-- synthetic bucket/signal evidence before commit. Any failed assertion aborts the entire
-- migration transaction and leaves no synthetic residue.
--
-- Failure class:
--   BGF-NETWORK-RATE-LIMIT-REMOTE-VERIFICATION-179

do $$
declare
  v_test_origin constant text := '203.0.113.55'; -- RFC 5737 TEST-NET-3 only
  v_operation constant text := 'get_workout';
  v_result jsonb;
  v_pepper bytea;
  v_origin_hash bytea;
  v_subject_key text;
  v_i integer;
  v_bucket_before integer;
  v_signal_before integer;
  v_bucket_after integer;
  v_signal_after integer;
begin
  select s.pepper
    into v_pepper
    from private.student_access_network_origin_secret s
   where s.singleton = true;

  if v_pepper is null or octet_length(v_pepper) <> 32 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE27_VERIFY_SECRET_MISSING';
  end if;

  v_origin_hash := extensions.hmac(
    convert_to('fitnexus-student-origin-v1:' || host(v_test_origin::inet), 'UTF8'),
    v_pepper,
    'sha256'
  );
  v_subject_key := 'origin:' || substr(encode(v_origin_hash, 'hex'), 1, 32);

  select count(*)::integer
    into v_bucket_before
    from private.student_access_network_rate_buckets b
   where b.origin_hash = v_origin_hash
     and b.operation = v_operation;

  select count(*)::integer
    into v_signal_before
    from private.student_access_security_signals s
   where s.signal_type = 'network_rate_limit_burst'
     and s.subject_key = v_subject_key
     and s.operation = v_operation;

  if v_bucket_before <> 0 or v_signal_before <> 0 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE27_VERIFY_SYNTHETIC_RESIDUE_PREEXISTS';
  end if;

  for v_i in 1..121 loop
    v_result := private.student_access_network_rate_limit_v1(v_test_origin, v_operation);

    if v_i <= 120 then
      if coalesce((v_result ->> 'ok')::boolean, false) is not true then
        raise exception using
          errcode = 'P0001',
          message = 'STAGE27_VERIFY_EARLY_RATE_LIMIT';
      end if;

      if (v_result ->> 'request_count')::integer <> v_i then
        raise exception using
          errcode = 'P0001',
          message = 'STAGE27_VERIFY_REQUEST_COUNT_DRIFT';
      end if;
    else
      if v_result ->> 'error' <> 'STUDENT_NETWORK_RATE_LIMITED' then
        raise exception using
          errcode = 'P0001',
          message = 'STAGE27_VERIFY_RATE_LIMIT_NOT_REACHED';
      end if;

      if (v_result ->> 'request_count')::integer <> 121
         or (v_result ->> 'limit_per_minute')::integer <> 120 then
        raise exception using
          errcode = 'P0001',
          message = 'STAGE27_VERIFY_RATE_LIMIT_RECEIPT_DRIFT';
      end if;
    end if;
  end loop;

  delete from private.student_access_security_signals s
   where s.signal_type = 'network_rate_limit_burst'
     and s.subject_key = v_subject_key
     and s.operation = v_operation;

  delete from private.student_access_network_rate_buckets b
   where b.origin_hash = v_origin_hash
     and b.operation = v_operation;

  select count(*)::integer
    into v_bucket_after
    from private.student_access_network_rate_buckets b
   where b.origin_hash = v_origin_hash
     and b.operation = v_operation;

  select count(*)::integer
    into v_signal_after
    from private.student_access_security_signals s
   where s.signal_type = 'network_rate_limit_burst'
     and s.subject_key = v_subject_key
     and s.operation = v_operation;

  if v_bucket_after <> 0 or v_signal_after <> 0 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE27_VERIFY_SYNTHETIC_CLEANUP_FAILED';
  end if;
end
$$;
