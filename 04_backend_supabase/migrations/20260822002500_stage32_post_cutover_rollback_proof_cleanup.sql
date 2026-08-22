-- Stage 32: fail-closed cleanup after the sealed real post-cutover Edge-to-direct rollback proof.
--
-- Failure classes:
--   BGF-STAGE32-ROLLBACK-PROOF-REEXECUTION-242
--   BGF-STAGE32-POST-CUTOVER-ROLLBACK-CLEANUP-244
--
-- Authorized only after workflow run 32540031081 / job 96948118831 proved all five
-- routes through StudentAccessTransport.forAuthorizedRollbackProof at exact sealed
-- head cb734b3ef51fe607d7d4de2709d517625a9c8101. The production singleton remained
-- Edge-selected and automatic fallback remained disabled. This migration deletes only
-- the exact rollback synthetic fixture and exact proof residue. No bearer token,
-- network origin, network-origin digest, service-role credential, or real customer data
-- is embedded. Direct-RPC grants are verified intact before and after cleanup and are
-- intentionally NOT revoked here.
do $$
declare
  v_user constant uuid := '5f5166fe-e774-593b-b86d-ddb9d93e16ca';
  v_org constant uuid := 'b01e4654-8a8e-5634-9ee7-3635114b1346';
  v_student constant uuid := 'e17f6053-d6dc-543a-bce7-c06cdf432e46';
  v_plan constant uuid := '8409e7e1-b853-5aab-97dd-50cf8b0d40f2';
  v_exercise constant uuid := '28a281ea-8f9e-542b-85f7-9ccd7a7ef7ee';
  v_link constant uuid := 'e2252055-fed6-5d3f-9410-1cccbe7d20c9';
  v_session constant uuid := 'eab31a9f-2206-4175-aa16-a8254ada91c6';
  v_log constant uuid := '62d5a65e-60f8-4c0d-b23d-4f29937d51f4';
  v_feedback constant uuid := '5d7f47c0-f132-4fbc-8cf5-5ea000a8257e';
  v_proof_window constant timestamptz := timestamptz '2026-08-22 00:21:00+00';
  v_count integer;
  v_deleted integer;
begin
  -- Full customer/runtime domain must still be exactly the single rollback fixture.
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
    raise exception using errcode = 'P0001', message = 'STAGE32_ROLLBACK_CLEANUP_CUSTOMER_DOMAIN_NO_LONGER_EXACT_SYNTHETIC_PROOF';
  end if;

  -- Fixture identity and final business state are exact.
  if (select count(*) from auth.users where id = v_user) <> 1
     or (select count(*) from public.profiles where user_id = v_user) <> 1
     or (select count(*) from public.organizations where id = v_org and owner_user_id = v_user and name = 'Stage32 Rollback Synthetic Organization') <> 1
     or (select count(*) from public.organization_members where organization_id = v_org and user_id = v_user and role = 'owner') <> 1
     or (select count(*) from public.organization_subscriptions where organization_id = v_org and plan_code = 'trial' and status = 'trialing') <> 1
     or (select count(*) from public.subscription_authority_events where organization_id = v_org and event_type = 'trial_initialized') <> 1
     or (select count(*) from public.students where id = v_student and organization_id = v_org and name = 'Stage32 Rollback Synthetic Student' and status = 'Treino concluído' and adherence = 100 and last_workout = 'Stage32 Rollback Synthetic Plan') <> 1
     or (select count(*) from public.training_plans where id = v_plan and student_id = v_student and organization_id = v_org and name = 'Stage32 Rollback Synthetic Plan' and is_active) <> 1
     or (select count(*) from public.training_exercises where id = v_exercise and training_plan_id = v_plan and organization_id = v_org and name = 'Stage32 Rollback Synthetic Exercise') <> 1
     or (select count(*) from public.student_access_links where id = v_link and student_id = v_student and organization_id = v_org and is_active and rotation_number = 1 and revoked_at is null) <> 1 then
    raise exception using errcode = 'P0001', message = 'STAGE32_ROLLBACK_CLEANUP_FIXTURE_IDENTITY_MISMATCH';
  end if;

  -- Exact business receipts from the sealed rollback proof.
  if (select count(*) from public.workout_sessions where id = v_session and organization_id = v_org and student_id = v_student and training_plan_id = v_plan and student_access_link_id = v_link and status = 'completed' and started_at = timestamptz '2026-08-22 00:21:17.923258+00' and completed_at = timestamptz '2026-08-22 00:21:18.353143+00') <> 1
     or (select count(*) from public.workout_exercise_logs where id = v_log and organization_id = v_org and session_id = v_session and training_plan_id = v_plan and exercise_id = v_exercise and completed and completed_at = timestamptz '2026-08-22 00:21:18.353143+00') <> 1
     or (select count(*) from public.workout_feedback where id = v_feedback and organization_id = v_org and student_id = v_student and session_id = v_session and perceived_exertion = 5 and pain_score = 0 and energy_score = 4 and pain_location is null and note is null and submitted_at = timestamptz '2026-08-22 00:21:18.9307+00') <> 1 then
    raise exception using errcode = 'P0001', message = 'STAGE32_ROLLBACK_CLEANUP_LIVE_PROOF_BUSINESS_RECEIPT_DRIFT';
  end if;

  -- Exactly the three mutating command receipts created by the proof.
  if (select count(*) from private.student_access_command_receipts where link_id = v_link) <> 3
     or (select count(*) from private.student_access_command_receipts where link_id = v_link and operation = 'start_workout' and command_id = '33000000000000000000000000000001' and completed_at = timestamptz '2026-08-22 00:21:17.923258+00') <> 1
     or (select count(*) from private.student_access_command_receipts where link_id = v_link and operation = 'set_completion' and command_id = '33000000000000000000000000000002' and completed_at = timestamptz '2026-08-22 00:21:18.353143+00') <> 1
     or (select count(*) from private.student_access_command_receipts where link_id = v_link and operation = 'submit_feedback' and command_id = '33000000000000000000000000000003' and completed_at = timestamptz '2026-08-22 00:21:18.9307+00') <> 1 then
    raise exception using errcode = 'P0001', message = 'STAGE32_ROLLBACK_CLEANUP_COMMAND_RECEIPT_DRIFT';
  end if;

  -- Direct RPC path still passes the link-scoped limiter: one bucket per route.
  if (select count(*) from private.student_access_rate_buckets where link_id = v_link) <> 5
     or (select count(distinct operation) from private.student_access_rate_buckets where link_id = v_link and window_started_at = v_proof_window and request_count = 1 and operation in ('get_workout','start_workout','set_completion','get_feedback_context','submit_feedback')) <> 5 then
    raise exception using errcode = 'P0001', message = 'STAGE32_ROLLBACK_CLEANUP_LINK_RATE_BUCKET_DRIFT';
  end if;

  -- Mutating routes emitted exactly three allowed security events and no signal.
  if (select count(*) from private.student_access_security_events where link_id = v_link or organization_id = v_org or student_id = v_student) <> 3
     or (select count(*) from private.student_access_security_events where link_id = v_link and outcome = 'allowed' and operation = 'start_workout' and command_id = '33000000000000000000000000000001' and occurred_at = timestamptz '2026-08-22 00:21:17.923258+00') <> 1
     or (select count(*) from private.student_access_security_events where link_id = v_link and outcome = 'allowed' and operation = 'set_completion' and command_id = '33000000000000000000000000000002' and occurred_at = timestamptz '2026-08-22 00:21:18.353143+00') <> 1
     or (select count(*) from private.student_access_security_events where link_id = v_link and outcome = 'allowed' and operation = 'submit_feedback' and command_id = '33000000000000000000000000000003' and occurred_at = timestamptz '2026-08-22 00:21:18.9307+00') <> 1
     or (select count(*) from private.student_access_security_signals where link_id = v_link or organization_id = v_org or student_id = v_student) <> 0 then
    raise exception using errcode = 'P0001', message = 'STAGE32_ROLLBACK_CLEANUP_SECURITY_RECEIPT_DRIFT';
  end if;

  -- Four fixture setup growth events plus the proof workout_logged event, nothing else.
  if (select count(*) from private.growth_events where organization_id = v_org) <> 5
     or (select count(*) from private.growth_events where organization_id = v_org and event_name = 'trial_started') <> 1
     or (select count(*) from private.growth_events where organization_id = v_org and event_name = 'student_created') <> 1
     or (select count(*) from private.growth_events where organization_id = v_org and event_name = 'training_created_or_duplicated') <> 1
     or (select count(*) from private.growth_events where organization_id = v_org and event_name = 'training_delivered') <> 1
     or (select count(*) from private.growth_events where organization_id = v_org and event_name = 'workout_logged' and occurred_at = timestamptz '2026-08-22 00:21:18.353143+00') <> 1
     or (select count(*) from private.growth_attribution where organization_id = v_org) <> 0 then
    raise exception using errcode = 'P0001', message = 'STAGE32_ROLLBACK_CLEANUP_GROWTH_RECEIPT_DRIFT';
  end if;

  -- No unrelated synthetic-domain mutation is permitted.
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
    raise exception using errcode = 'P0001', message = 'STAGE32_ROLLBACK_CLEANUP_UNEXPECTED_SYNTHETIC_DOMAIN_MUTATION';
  end if;

  -- Real rollback traversed retained direct RPC, not Edge, so it MUST NOT have created
  -- any network-origin buckets in its proof minute. Existing historical global buckets
  -- are deliberately left untouched.
  select count(*)::integer into v_count
    from private.student_access_network_rate_buckets
   where operation in ('get_workout','start_workout','set_completion','get_feedback_context','submit_feedback')
     and window_started_at = v_proof_window
     and request_count = 1
     and last_seen_at >= v_proof_window
     and last_seen_at < v_proof_window + interval '1 minute';
  if v_count <> 0 then
    raise exception using errcode = 'P0001', message = 'STAGE32_ROLLBACK_CLEANUP_DIRECT_PATH_NETWORK_BUCKET_UNEXPECTED';
  end if;

  -- Five retained direct-v2 functions must remain executable for anon/auth throughout
  -- cleanup; revocation is a separate future gate.
  select count(*)::integer into v_count
    from pg_proc p
    join pg_namespace n on n.oid = p.pronamespace
   where n.nspname = 'public'
     and p.proname in (
       'get_student_feedback_context_v2',
       'get_student_workout_v2',
       'set_student_exercise_completion_v2',
       'start_student_workout_v2',
       'submit_student_workout_feedback_v2'
     )
     and has_function_privilege('anon', p.oid, 'EXECUTE')
     and has_function_privilege('authenticated', p.oid, 'EXECUTE');
  if v_count <> 5 then
    raise exception using errcode = 'P0001', message = 'STAGE32_ROLLBACK_CLEANUP_DIRECT_GRANTS_NOT_INTACT';
  end if;

  -- Security event link FK uses ON DELETE SET NULL, so remove exact events explicitly
  -- before the organization/access-link cascade.
  delete from private.student_access_security_events
   where link_id = v_link or organization_id = v_org or student_id = v_student;
  get diagnostics v_deleted = row_count;
  if v_deleted <> 3 then
    raise exception using errcode = 'P0001', message = 'STAGE32_ROLLBACK_CLEANUP_SECURITY_EVENT_DELETE_COUNT_MISMATCH';
  end if;

  delete from private.student_access_security_signals
   where link_id = v_link or organization_id = v_org or student_id = v_student;
  get diagnostics v_deleted = row_count;
  if v_deleted <> 0 then
    raise exception using errcode = 'P0001', message = 'STAGE32_ROLLBACK_CLEANUP_UNEXPECTED_SECURITY_SIGNAL_DELETE';
  end if;

  delete from public.organizations where id = v_org;
  get diagnostics v_deleted = row_count;
  if v_deleted <> 1 then
    raise exception using errcode = 'P0001', message = 'STAGE32_ROLLBACK_CLEANUP_ORGANIZATION_DELETE_FAILED';
  end if;

  delete from auth.users where id = v_user;
  get diagnostics v_deleted = row_count;
  if v_deleted <> 1 then
    raise exception using errcode = 'P0001', message = 'STAGE32_ROLLBACK_CLEANUP_AUTH_USER_DELETE_FAILED';
  end if;

  -- Zero exact synthetic residue; unrelated historical network buckets remain untouched.
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
    raise exception using errcode = 'P0001', message = 'STAGE32_ROLLBACK_CLEANUP_POSTCONDITION_FAILED';
  end if;

  select count(*)::integer into v_count
    from pg_proc p
    join pg_namespace n on n.oid = p.pronamespace
   where n.nspname = 'public'
     and p.proname in (
       'get_student_feedback_context_v2',
       'get_student_workout_v2',
       'set_student_exercise_completion_v2',
       'start_student_workout_v2',
       'submit_student_workout_feedback_v2'
     )
     and has_function_privilege('anon', p.oid, 'EXECUTE')
     and has_function_privilege('authenticated', p.oid, 'EXECUTE');
  if v_count <> 5 then
    raise exception using errcode = 'P0001', message = 'STAGE32_ROLLBACK_CLEANUP_POSTCONDITION_DIRECT_GRANTS_CHANGED';
  end if;
end;
$$;
