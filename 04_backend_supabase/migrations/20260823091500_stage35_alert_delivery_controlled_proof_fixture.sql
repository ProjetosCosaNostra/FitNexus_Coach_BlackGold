-- Stage 35 controlled external-delivery proof fixture repository promotion.
-- REPOSITORY-ONLY. REMOTE APPLICATION IS FORBIDDEN UNTIL THIS PROMOTION MERGES
-- GREEN AND THE SEPARATE RECEIPT-STORE APPLY / DISPATCHER DEPLOYMENT SEQUENCE IS AUTHORIZED.
-- Executable body below is byte-identical to the reviewed operations candidate.
--
-- Stage 35 controlled external-delivery proof fixture candidate.
--
-- REPOSITORY-ONLY OPERATIONS CANDIDATE. DO NOT EXECUTE FROM operations/.
-- Promotion to migrations/ requires the Stage35 deployment/proof seal to merge first.
-- The fixture is synthetic, contains no customer identity, raw possession token, raw network
-- origin, origin digest, provider credential, destination ID, or provider response.
--
-- Failure classes:
--   BGF-STAGE35-ALERT-PROOF-CUSTOMER-CROSSOVER-278
--   BGF-STAGE35-ALERT-CONTROLLED-FIXTURE-PREMATURE-284
--   BGF-STAGE35-ALERT-CONTROLLED-FIXTURE-DRIFT-285
do $$
declare
  v_now timestamptz := clock_timestamp();
  v_marker constant text := 'fitnexus-stage34-alert-delivery-proof-v1';
  v_subject constant text := 'proof:fitnexus-stage34-alert-delivery-proof-v1';
begin
  if to_regclass('private.student_access_alert_delivery_receipts') is null then
    raise exception using errcode = 'P0001', message = 'STAGE35_ALERT_RECEIPT_STORE_NOT_PRESENT';
  end if;

  if (select count(*) from auth.users) <> 0
     or (select count(*) from public.organizations) <> 0
     or (select count(*) from public.students) <> 0 then
    raise exception using errcode = 'P0001', message = 'STAGE35_ALERT_PROOF_CUSTOMER_DOMAIN_NOT_EMPTY';
  end if;

  if (select count(*) from private.student_access_security_events) <> 0
     or (select count(*) from private.student_access_security_signals) <> 0 then
    raise exception using errcode = 'P0001', message = 'STAGE35_ALERT_PROOF_SECURITY_DOMAIN_NOT_EMPTY';
  end if;

  if (select count(*) from private.student_access_network_rate_buckets) <> 13
     or (select count(*) from private.growth_events) <> 6 then
    raise exception using errcode = 'P0001', message = 'STAGE35_ALERT_PROOF_HISTORICAL_BASELINE_DRIFT';
  end if;

  if exists (
    select 1
      from private.student_access_alert_delivery_receipts r
     where r.controlled_proof_marker = v_marker
  ) then
    raise exception using errcode = 'P0001', message = 'STAGE35_ALERT_PROOF_RECEIPT_ALREADY_EXISTS';
  end if;

  if exists (
    select 1
      from private.student_access_security_signals s
     where s.subject_key = v_subject
  ) then
    raise exception using errcode = 'P0001', message = 'STAGE35_ALERT_PROOF_SIGNAL_ALREADY_EXISTS';
  end if;

  if (
    select count(*)
      from pg_proc p
      join pg_namespace n on n.oid = p.pronamespace
     where n.nspname = 'public'
       and p.proname in (
         'get_student_workout_v2',
         'start_student_workout_v2',
         'set_student_exercise_completion_v2',
         'get_student_feedback_context_v2',
         'submit_student_workout_feedback_v2'
       )
       and has_function_privilege('anon', p.oid, 'EXECUTE')
  ) <> 0 then
    raise exception using errcode = 'P0001', message = 'STAGE35_ALERT_PROOF_ANON_DIRECT_EXECUTE_CHANGED';
  end if;

  if (
    select count(*)
      from pg_proc p
      join pg_namespace n on n.oid = p.pronamespace
     where n.nspname = 'public'
       and p.proname in (
         'get_student_workout_v2',
         'start_student_workout_v2',
         'set_student_exercise_completion_v2',
         'get_student_feedback_context_v2',
         'submit_student_workout_feedback_v2'
       )
       and has_function_privilege('authenticated', p.oid, 'EXECUTE')
  ) <> 0 then
    raise exception using errcode = 'P0001', message = 'STAGE35_ALERT_PROOF_AUTH_DIRECT_EXECUTE_CHANGED';
  end if;

  if (
    select count(*)
      from pg_proc p
      join pg_namespace n on n.oid = p.pronamespace
     where n.nspname = 'public'
       and p.proname in (
         'get_student_workout_v2',
         'start_student_workout_v2',
         'set_student_exercise_completion_v2',
         'get_student_feedback_context_v2',
         'submit_student_workout_feedback_v2'
       )
       and has_function_privilege('service_role', p.oid, 'EXECUTE')
  ) <> 5 then
    raise exception using errcode = 'P0001', message = 'STAGE35_ALERT_PROOF_SERVICE_ROLE_BOUNDARY_CHANGED';
  end if;

  if not has_function_privilege(
    'authenticated',
    'public.issue_student_access_token_v2(uuid)',
    'EXECUTE'
  ) then
    raise exception using errcode = 'P0001', message = 'STAGE35_ALERT_PROOF_ISSUE_TOKEN_AUTHORITY_CHANGED';
  end if;

  insert into private.student_access_security_signals (
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
    last_seen_at,
    created_at,
    updated_at
  ) values (
    'network_rate_limit_burst',
    'high',
    v_subject,
    null,
    null,
    null,
    'get_workout',
    date_trunc('minute', v_now),
    1,
    v_now,
    v_now,
    v_now,
    v_now
  );

  if (select count(*) from private.student_access_security_signals) <> 1
     or (
       select count(*)
         from private.student_access_security_signals s
        where s.signal_type = 'network_rate_limit_burst'
          and s.severity = 'high'
          and s.subject_key = v_subject
          and s.operation = 'get_workout'
          and s.event_count = 1
          and s.link_id is null
          and s.organization_id is null
          and s.student_id is null
     ) <> 1 then
    raise exception using errcode = 'P0001', message = 'STAGE35_ALERT_PROOF_SIGNAL_POSTCONDITION_FAILED';
  end if;

  if (select count(*) from private.student_access_alert_delivery_receipts) <> 0 then
    raise exception using errcode = 'P0001', message = 'STAGE35_ALERT_PROOF_RECEIPT_PREMATURELY_MATERIALIZED';
  end if;
end;
$$;
