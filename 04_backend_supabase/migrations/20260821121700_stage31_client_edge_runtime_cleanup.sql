-- Stage 31: fail-closed cleanup after the sealed Flutter client -> Edge live proof.
--
-- Failure classes:
--   BGF-STAGE31-CLIENT-EDGE-RUNTIME-FIXTURE-216
--   BGF-STAGE31-CLIENT-EDGE-RUNTIME-PROOF-REEXECUTION-219
--   BGF-STAGE31-CLIENT-EDGE-RUNTIME-CLEANUP-225
--
-- This cleanup is allowed only while the authoritative customer domain is still exactly
-- the Stage 31 synthetic fixture and the observed live-proof mutations match the sealed
-- receipt. The network-origin selector uses only operation/time/count semantics; no raw
-- network origin or origin digest is embedded in repository source.
do $$
declare
  v_user constant uuid := 'e06ec62d-e9b7-54a8-8fb9-d47828499939';
  v_org constant uuid := 'cd4688ec-cc08-5c2d-ad8c-0149242d809e';
  v_student constant uuid := 'bbdf3d96-0569-51d4-aadc-251ed0abc24e';
  v_plan constant uuid := 'b54064b9-f6a8-539e-b4a2-976d99141844';
  v_exercise constant uuid := '51871b03-c901-5a8f-b659-40f63e1f22e4';
  v_link constant uuid := '4ad0ced0-fc32-50cb-8287-fb4f971942a5';
  v_session constant uuid := 'b7555999-5d2c-4ee5-8ccd-faad53d77939';
  v_log constant uuid := '22b55e28-f217-4da0-aff3-d5dbaf937b89';
  v_feedback constant uuid := '20bb7e8c-9a1b-4f45-af41-6cf009142dea';
  v_proof_window constant timestamptz := timestamptz '2026-08-21 12:11:00+00';
  v_count integer;
  v_deleted integer;
begin
  -- Any new real customer-domain row blocks cleanup transactionally.
  if (select count(*) from auth.users) <> 1
     or (select count(*) from public.profiles) <> 1
     or (select count(*) from public.organizations) <> 1
     or (select count(*) from public.organization_members) <> 1
     or (select count(*) from public.organization_subscriptions) <> 1
     or (select count(*) from public.subscription_authority_events) <> 1
     or (select count(*) from public.students) <> 1
     or (select count(*) from public.training_plans) <> 1
     or (select count(*) from public.training_exercises) <> 1
     or (select count(*) from public.student_access_links) <> 1
     or (select count(*) from public.workout_sessions) <> 1
     or (select count(*) from public.workout_exercise_logs) <> 1
     or (select count(*) from public.workout_feedback) <> 1 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE31_CLEANUP_CUSTOMER_DOMAIN_NO_LONGER_SYNTHETIC_ONLY';
  end if;

  if (select count(*) from auth.users where id = v_user) <> 1
     or (select count(*) from public.profiles where user_id = v_user) <> 1
     or (select count(*) from public.organizations where id = v_org and owner_user_id = v_user and name = 'Stage31 Synthetic Organization') <> 1
     or (select count(*) from public.organization_members where organization_id = v_org and user_id = v_user and role = 'owner') <> 1
     or (select count(*) from public.organization_subscriptions where organization_id = v_org and plan_code = 'trial' and status = 'trialing') <> 1
     or (select count(*) from public.subscription_authority_events where organization_id = v_org and event_type = 'trial_initialized') <> 1
     or (select count(*) from public.students where id = v_student and organization_id = v_org and name = 'Stage31 Synthetic Student' and status = 'Treino concluído' and adherence = 100 and last_workout = 'Stage31 Synthetic Plan') <> 1
     or (select count(*) from public.training_plans where id = v_plan and student_id = v_student and organization_id = v_org and name = 'Stage31 Synthetic Plan' and is_active) <> 1
     or (select count(*) from public.training_exercises where id = v_exercise and training_plan_id = v_plan and organization_id = v_org and name = 'Stage31 Synthetic Exercise') <> 1
     or (select count(*) from public.student_access_links where id = v_link and student_id = v_student and organization_id = v_org and is_active and rotation_number = 1 and revoked_at is null) <> 1 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE31_CLEANUP_FIXTURE_IDENTITY_MISMATCH';
  end if;

  if (select count(*) from public.workout_sessions where id = v_session and organization_id = v_org and student_id = v_student and training_plan_id = v_plan and student_access_link_id = v_link and status = 'completed' and completed_at is not null) <> 1
     or (select count(*) from public.workout_exercise_logs where id = v_log and organization_id = v_org and session_id = v_session and training_plan_id = v_plan and exercise_id = v_exercise and completed and completed_at is not null) <> 1
     or (select count(*) from public.workout_feedback where id = v_feedback and organization_id = v_org and student_id = v_student and session_id = v_session and perceived_exertion = 5 and pain_score = 0 and energy_score = 4 and pain_location is null and note is null) <> 1 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE31_CLEANUP_LIVE_PROOF_BUSINESS_RECEIPT_DRIFT';
  end if;

  if (select count(*) from private.student_access_command_receipts where link_id = v_link) <> 3
     or (select count(*) from private.student_access_command_receipts where link_id = v_link and operation = 'start_workout' and command_id = '31000000000000000000000000000001' and completed_at is not null) <> 1
     or (select count(*) from private.student_access_command_receipts where link_id = v_link and operation = 'set_completion' and command_id = '31000000000000000000000000000002' and completed_at is not null) <> 1
     or (select count(*) from private.student_access_command_receipts where link_id = v_link and operation = 'submit_feedback' and command_id = '31000000000000000000000000000003' and completed_at is not null) <> 1 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE31_CLEANUP_COMMAND_RECEIPT_DRIFT';
  end if;

  if (select count(*) from private.student_access_rate_buckets where link_id = v_link) <> 5
     or (select count(distinct operation) from private.student_access_rate_buckets where link_id = v_link and window_started_at = v_proof_window and request_count = 1 and operation in ('get_workout','start_workout','set_completion','get_feedback_context','submit_feedback')) <> 5 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE31_CLEANUP_LINK_RATE_BUCKET_DRIFT';
  end if;

  if (select count(*) from private.student_access_security_events where link_id = v_link or organization_id = v_org or student_id = v_student) <> 3
     or (select count(*) from private.student_access_security_events where link_id = v_link and outcome = 'allowed' and operation = 'start_workout' and command_id = '31000000000000000000000000000001') <> 1
     or (select count(*) from private.student_access_security_events where link_id = v_link and outcome = 'allowed' and operation = 'set_completion' and command_id = '31000000000000000000000000000002') <> 1
     or (select count(*) from private.student_access_security_events where link_id = v_link and outcome = 'allowed' and operation = 'submit_feedback' and command_id = '31000000000000000000000000000003') <> 1
     or (select count(*) from private.student_access_security_signals where link_id = v_link or organization_id = v_org or student_id = v_student) <> 0 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE31_CLEANUP_SECURITY_RECEIPT_DRIFT';
  end if;

  if (select count(*) from private.growth_events where organization_id = v_org) <> 5
     or (select count(*) from private.growth_events where organization_id = v_org and event_name = 'trial_started') <> 1
     or (select count(*) from private.growth_events where organization_id = v_org and event_name = 'student_created') <> 1
     or (select count(*) from private.growth_events where organization_id = v_org and event_name = 'training_created_or_duplicated') <> 1
     or (select count(*) from private.growth_events where organization_id = v_org and event_name = 'training_delivered') <> 1
     or (select count(*) from private.growth_events where organization_id = v_org and event_name = 'workout_logged') <> 1
     or (select count(*) from private.growth_attribution where organization_id = v_org) <> 0 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE31_CLEANUP_GROWTH_RECEIPT_DRIFT';
  end if;

  if (select count(*) from public.billing_checkout_intents where organization_id = v_org) <> 0
     or (select count(*) from public.billing_webhook_receipts where organization_id = v_org) <> 0
     or (select count(*) from public.coach_action_events where organization_id = v_org or student_id = v_student) <> 0
     or (select count(*) from public.decision_engine_evaluation_cases where organization_id = v_org or student_id = v_student) <> 0
     or (select count(*) from public.decision_engine_evaluation_runs where organization_id = v_org) <> 0
     or (select count(*) from public.decision_engine_promotion_packets where organization_id = v_org) <> 0
     or (select count(*) from public.decision_intelligence_runs where organization_id = v_org or student_id = v_student) <> 0
     or (select count(*) from public.decision_intelligence_outcomes where organization_id = v_org or student_id = v_student) <> 0
     or (select count(*) from public.training_plan_lineage where organization_id = v_org or student_id = v_student) <> 0
     or (select count(*) from public.training_templates where organization_id = v_org) <> 0
     or (select count(*) from public.training_template_exercises where organization_id = v_org) <> 0 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE31_CLEANUP_UNEXPECTED_SYNTHETIC_DOMAIN_MUTATION';
  end if;

  select count(*)::integer into v_count
    from private.student_access_network_rate_buckets
   where operation in ('get_workout','start_workout','set_completion','get_feedback_context','submit_feedback')
     and window_started_at = v_proof_window
     and request_count = 1
     and last_seen_at >= v_proof_window
     and last_seen_at < v_proof_window + interval '1 minute';
  if v_count <> 5 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE31_CLEANUP_NETWORK_BUCKET_SELECTOR_MISMATCH';
  end if;

  delete from private.student_access_network_rate_buckets
   where operation in ('get_workout','start_workout','set_completion','get_feedback_context','submit_feedback')
     and window_started_at = v_proof_window
     and request_count = 1
     and last_seen_at >= v_proof_window
     and last_seen_at < v_proof_window + interval '1 minute';
  get diagnostics v_deleted = row_count;
  if v_deleted <> 5 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE31_CLEANUP_NETWORK_BUCKET_DELETE_COUNT_MISMATCH';
  end if;

  -- Organization deletion cascades the synthetic student/workout/subscription/growth/link
  -- domain. It must happen before auth-user deletion because owner_user_id is restrictive.
  delete from public.organizations where id = v_org;
  get diagnostics v_deleted = row_count;
  if v_deleted <> 1 then
    raise exception using errcode = 'P0001', message = 'STAGE31_CLEANUP_ORGANIZATION_DELETE_FAILED';
  end if;

  delete from auth.users where id = v_user;
  get diagnostics v_deleted = row_count;
  if v_deleted <> 1 then
    raise exception using errcode = 'P0001', message = 'STAGE31_CLEANUP_AUTH_USER_DELETE_FAILED';
  end if;

  if (select count(*) from auth.users) <> 0
     or (select count(*) from public.profiles where user_id = v_user) <> 0
     or (select count(*) from public.organizations) <> 0
     or (select count(*) from public.organization_members where organization_id = v_org) <> 0
     or (select count(*) from public.organization_subscriptions where organization_id = v_org) <> 0
     or (select count(*) from public.subscription_authority_events where organization_id = v_org) <> 0
     or (select count(*) from public.students) <> 0
     or (select count(*) from public.training_plans) <> 0
     or (select count(*) from public.training_exercises) <> 0
     or (select count(*) from public.student_access_links) <> 0
     or (select count(*) from public.workout_sessions) <> 0
     or (select count(*) from public.workout_exercise_logs) <> 0
     or (select count(*) from public.workout_feedback) <> 0
     or (select count(*) from private.growth_events where organization_id = v_org) <> 0
     or (select count(*) from private.growth_attribution where organization_id = v_org) <> 0
     or (select count(*) from private.student_access_rate_buckets where link_id = v_link) <> 0
     or (select count(*) from private.student_access_command_receipts where link_id = v_link) <> 0
     or (select count(*) from private.student_access_security_events where link_id = v_link or organization_id = v_org or student_id = v_student) <> 0
     or (select count(*) from private.student_access_security_signals where link_id = v_link or organization_id = v_org or student_id = v_student) <> 0
     or (select count(*) from private.student_access_network_rate_buckets
          where operation in ('get_workout','start_workout','set_completion','get_feedback_context','submit_feedback')
            and window_started_at = v_proof_window
            and request_count = 1
            and last_seen_at >= v_proof_window
            and last_seen_at < v_proof_window + interval '1 minute') <> 0 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE31_CLEANUP_POSTCONDITION_FAILED';
  end if;
end;
$$;
