-- Stage 35 controlled external-delivery proof cleanup candidate.
--
-- REPOSITORY-ONLY OPERATIONS CANDIDATE. DO NOT EXECUTE FROM operations/.
-- Promote only after one successful sealed external-delivery proof and a fresh read-only
-- receipt proving exactly one synthetic signal + one delivered provider receipt.
--
-- Failure classes:
--   BGF-STAGE35-ALERT-PROOF-CLEANUP-286
--   BGF-STAGE35-ALERT-PROOF-RECEIPT-AMBIGUITY-287
--   BGF-STAGE35-ALERT-PROOF-CLEANUP-CROSSOVER-288

do $$
declare
  v_marker constant text := 'fitnexus-stage34-alert-delivery-proof-v1';
  v_subject constant text := 'proof:fitnexus-stage34-alert-delivery-proof-v1';
  v_signal_id bigint;
begin
  if to_regclass('private.student_access_alert_delivery_receipts') is null then
    raise exception using errcode = 'P0001', message = 'STAGE35_ALERT_CLEANUP_RECEIPT_STORE_MISSING';
  end if;

  if (select count(*) from auth.users) <> 0
     or (select count(*) from public.organizations) <> 0
     or (select count(*) from public.students) <> 0 then
    raise exception using errcode = 'P0001', message = 'STAGE35_ALERT_CLEANUP_CUSTOMER_DOMAIN_NOT_EMPTY';
  end if;

  if (select count(*) from private.student_access_security_events) <> 0
     or (select count(*) from private.student_access_security_signals) <> 1 then
    raise exception using errcode = 'P0001', message = 'STAGE35_ALERT_CLEANUP_SECURITY_DOMAIN_DRIFT';
  end if;

  select s.id
    into v_signal_id
    from private.student_access_security_signals s
   where s.signal_type = 'network_rate_limit_burst'
     and s.severity = 'high'
     and s.subject_key = v_subject
     and s.operation = 'get_workout'
     and s.event_count = 1
     and s.link_id is null
     and s.organization_id is null
     and s.student_id is null;

  if v_signal_id is null then
    raise exception using errcode = 'P0001', message = 'STAGE35_ALERT_CLEANUP_EXACT_PROOF_SIGNAL_MISSING';
  end if;

  if (select count(*) from private.student_access_alert_delivery_receipts) <> 1
     or (
       select count(*)
         from private.student_access_alert_delivery_receipts r
        where r.signal_id = v_signal_id
          and r.provider = 'telegram_bot_api'
          and r.destination_fingerprint ~ '^[0-9a-f]{64}$'
          and r.status = 'delivered'
          and r.attempt_number = 1
          and r.provider_message_id is not null
          and r.provider_message_id > 0
          and r.controlled_proof_marker = v_marker
          and r.last_error_code is null
          and r.delivered_at is not null
          and r.lease_expires_at is null
     ) <> 1 then
    raise exception using errcode = 'P0001', message = 'STAGE35_ALERT_CLEANUP_EXTERNAL_DELIVERY_RECEIPT_NOT_EXACT';
  end if;

  if (select count(*) from private.student_access_network_rate_buckets) <> 13
     or (select count(*) from private.growth_events) <> 6 then
    raise exception using errcode = 'P0001', message = 'STAGE35_ALERT_CLEANUP_HISTORICAL_BASELINE_DRIFT';
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
    raise exception using errcode = 'P0001', message = 'STAGE35_ALERT_CLEANUP_ANON_DIRECT_EXECUTE_CHANGED';
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
    raise exception using errcode = 'P0001', message = 'STAGE35_ALERT_CLEANUP_AUTH_DIRECT_EXECUTE_CHANGED';
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
    raise exception using errcode = 'P0001', message = 'STAGE35_ALERT_CLEANUP_SERVICE_ROLE_BOUNDARY_CHANGED';
  end if;

  if not has_function_privilege(
    'authenticated',
    'public.issue_student_access_token_v2(uuid)',
    'EXECUTE'
  ) then
    raise exception using errcode = 'P0001', message = 'STAGE35_ALERT_CLEANUP_ISSUE_TOKEN_AUTHORITY_CHANGED';
  end if;

  delete from private.student_access_security_signals s
   where s.id = v_signal_id
     and s.subject_key = v_subject;

  if (select count(*) from private.student_access_security_signals) <> 0
     or (select count(*) from private.student_access_alert_delivery_receipts) <> 0 then
    raise exception using errcode = 'P0001', message = 'STAGE35_ALERT_CLEANUP_SYNTHETIC_RESIDUE_REMAINS';
  end if;

  if (select count(*) from private.student_access_network_rate_buckets) <> 13
     or (select count(*) from private.growth_events) <> 6 then
    raise exception using errcode = 'P0001', message = 'STAGE35_ALERT_CLEANUP_POSTCONDITION_BASELINE_CHANGED';
  end if;
end;
$$;
