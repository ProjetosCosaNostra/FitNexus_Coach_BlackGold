-- Stage 32: fail-closed cleanup after the sealed post-cutover production Edge R1 proof.
--
-- Failure classes:
--   BGF-STAGE32-POST-CUTOVER-PROOF-REEXECUTION-233
--   BGF-STAGE32-POST-CUTOVER-R1-CLEANUP-239
--
-- This cleanup is authorized only after workflow run 32532170382 / job 96926178484
-- proved all five routes through StudentAccessTransport.instance at the exact sealed
-- proof head. It deletes only the exact synthetic fixture and exact proof residue.
-- No raw bearer token, network origin, or network-origin digest is embedded here.
-- Security events are deleted explicitly before the access-link cascade because the
-- security-event link FK uses ON DELETE SET NULL rather than CASCADE.
do $$
declare
  v_user constant uuid := '728ea3d2-335f-5936-b78b-0289f9e732b8';
  v_org constant uuid := '51143353-1492-54a9-b5f8-1ad99cf4c6f3';
  v_student constant uuid := 'bdbe631a-4c44-53fc-a0da-38310bbdf90e';
  v_plan constant uuid := 'a1c29966-b4c1-59fc-bb9e-ac0b055ea577';
  v_exercise constant uuid := '585b0618-8141-513c-a37e-02cb5ccd93f1';
  v_link constant uuid := '378baa18-c8fc-5765-b01f-6fd3dd898f64';
  v_session constant uuid := '29721756-f091-4b33-9106-82a253e9f9c8';
  v_log constant uuid := '07df75e0-36f2-4ce3-b090-4d72261e0717';
  v_feedback constant uuid := '58972689-2208-4ee0-ab34-8ebe75c0f6cb';
  v_proof_window constant timestamptz := timestamptz '2026-08-21 22:15:00+00';
  v_count integer;
  v_deleted integer;
begin
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
    raise exception using errcode = 'P0001', message = 'STAGE32_R1_CLEANUP_CUSTOMER_DOMAIN_NO_LONGER_EXACT_SYNTHETIC_PROOF';
  end if;

  if (select count(*) from auth.users where id = v_user) <> 1
     or (select count(*) from public.profiles where user_id = v_user) <> 1
     or (select count(*) from public.organizations where id = v_org and owner_user_id = v_user and name = 'Stage32 Synthetic Organization') <> 1
     or (select count(*) from public.organization_members where organization_id = v_org and user_id = v_user and role = 'owner') <> 1
     or (select count(*) from public.organization_subscriptions where organization_id = v_org and plan_code = 'trial' and status = 'trialing') <> 1
     or (select count(*) from public.subscription_authority_events where organization_id = v_org and event_type = 'trial_initialized') <> 1
     or (select count(*) from public.students where id = v_student and organization_id = v_org and name = 'Stage32 Synthetic Student' and status = 'Treino concluído' and adherence = 100 and last_workout = 'Stage32 Synthetic Plan') <> 1
     or (select count(*) from public.training_plans where id = v_plan and student_id = v_student and organization_id = v_org and name = 'Stage32 Synthetic Plan' and is_active) <> 1
     or (select count(*) from public.training_exercises where id = v_exercise and training_plan_id = v_plan and organization_id = v_org and name = 'Stage32 Synthetic Exercise') <> 1
     or (select count(*) from public.student_access_links where id = v_link and student_id = v_student and organization_id = v_org and is_active and rotation_number = 1 and revoked_at is null) <> 1 then
    raise exception using errcode = 'P0001', message = 'STAGE32_R1_CLEANUP_FIXTURE_IDENTITY_MISMATCH';
  end if;

  if (select count(*) from public.workout_sessions where id = v_session and organization_id = v_org and student_id = v_student and training_plan_id = v_plan and student_access_link_id = v_link and status = 'completed' and started_at = timestamptz '2026-08-21 22:15:38.584185+00' and completed_at = timestamptz '2026-08-21 22:15:39.693767+00') <> 1
     or (select count(*) from public.workout_exercise_logs where id = v_log and organization_id = v_org and session_id = v_session and training_plan_id = v_plan and exercise_id = v_exercise and completed and completed_at = timestamptz '2026-08-21 22:15:39.693767+00') <> 1
     or (select count(*) from public.workout_feedback where id = v_feedback and organization_id = v_org and student_id = v_student and session_id = v_session and perceived_exertion = 5 and pain_score = 0 and energy_score = 4 and pain_location is null and note is null and submitted_at = timestamptz '2026-08-21 22:15:41.585474+00') <> 1 then
    raise exception using errcode = 'P0001', message = 'STAGE32_R1_CLEANUP_LIVE_PROOF_BUSINESS_RECEIPT_DRIFT';
  end if;

  if (select count(*) from private.student_access_command_receipts where link_id = v_link) <> 3
     or (select count(*) from private.student_access_command_receipts where link_id = v_link and operation = 'start_workout' and command_id = '32000000000000000000000000000001' and completed_at = timestamptz '2026-08-21 22:15:38.584185+00') <> 1
     or (select count(*) from private.student_access_command_receipts where link_id = v_link and operation = 'set_completion' and command_id = '32000000000000000000000000000002' and completed_at = timestamptz '2026-08-21 22:15:39.693767+00') <> 1
     or (select count(*) from private.student_access_command_receipts where link_id = v_link and operation = 'submit_feedback' and command_id = '32000000000000000000000000000003' and completed_at = timestamptz '2026-08-21 22:15:41.585474+00') <> 1 then
    raise exception using errcode = 'P0001', message = 'STAGE32_R1_CLEANUP_COMMAND_RECEIPT_DRIFT';
  end if;

  if (select count(*) from private.student_access_rate_buckets where link_id = v_link) <> 5
     or (select count(distinct operation) from private.student_access_rate_buckets where link_id = v_link and window_started_at = v_proof_window and request_count = 1 and operation in ('get_workout','start_workout','set_completion','get_feedback_context','submit_feedback')) <> 5 then
    raise exception using errcode = 'P0001', message = 'STAGE32_R1_CLEANUP_LINK_RATE_BUCKET_DRIFT';
  end if;

  if (select count(*) from private.student_access_security_events where link_id = v_link or organization_id = v_org or student_id = v_student) <> 3
     or (select count(*) from private.student_access_security_events where link_id = v_link and outcome = 'allowed' and operation = 'start_workout' and command_id = '32000000000000000000000000000001' and occurred_at = timestamptz '2026-08-21 22:15:38.584185+00') <> 1
     or (select count(*) from private.student_access_security_events where link_id = v_link and outcome = 'allowed' and operation = 'set_completion' and command_id = '32000000000000000000000000000002' and occurred_at = timestamptz '2026-08-21 22:15:39.693767+00') <> 1
     or (select count(*) from private.student_access_security_events where link_id = v_link and outcome = 'allowed' and operation = 'submit_feedback' and command_id = '32000000000000000000000000000003' and occurred_at = timestamptz '2026-08-21 22:15:41.585474+00') <> 1
     or (select count(*) from private.student_access_security_signals where link_id = v_link or organization_id = v_org or student_id = v_student) <> 0 then
    raise exception using errcode = 'P0001', message = 'STAGE32_R1_CLEANUP_SECURITY_RECEIPT_DRIFT';
  end if;

  if (select count(*) from private.growth_events where organization_id = v_org) <> 5
     or (select count(*) from private.growth_events where organization_id = v_org and event_name = 'trial_started') <> 1
     or (select count(*) from private.growth_events where organization_id = v_org and event_name = 'student_created') <> 1
     or (select count(*) from private.growth_events where organization_id = v_org and event_name = 'training_created_or_duplicated') <> 1
     or (select count(*) from private.growth_events where organization_id = v_org and event_name = 'training_delivered') <> 1
     or (select count(*) from private.growth_events where organization_id = v_org and event_name = 'workout_logged' and occurred_at = timestamptz '2026-08-21 22:15:39.693767+00') <> 1
     or (select count(*) from private.growth_attribution where organization_id = v_org) <> 0 then
    raise exception using errcode = 'P0001', message = 'STAGE32_R1_CLEANUP_GROWTH_RECEIPT_DRIFT';
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
    raise exception using errcode = 'P0001', message = 'STAGE32_R1_CLEANUP_UNEXPECTED_SYNTHETIC_DOMAIN_MUTATION';
  end if;

  select count(*)::integer into v_count
    from private.student_access_network_rate_buckets
   where operation in ('get_workout','start_workout','set_completion','get_feedback_context','submit_feedback')
     and window_started_at = v_proof_window
     and request_count = 1
     and last_seen_at >= v_proof_window
     and last_seen_at < v_proof_window + interval '1 minute';
  if v_count <> 5 then
    raise exception using errcode = 'P0001', message = 'STAGE32_R1_CLEANUP_NETWORK_BUCKET_SELECTOR_MISMATCH';
  end if;

  delete from private.student_access_network_rate_buckets
   where operation in ('get_workout','start_workout','set_completion','get_feedback_context','submit_feedback')
     and window_started_at = v_proof_window
     and request_count = 1
     and last_seen_at >= v_proof_window
     and last_seen_at < v_proof_window + interval '1 minute';
  get diagnostics v_deleted = row_count;
  if v_deleted <> 5 then
    raise exception using errcode = 'P0001', message = 'STAGE32_R1_CLEANUP_NETWORK_BUCKET_DELETE_COUNT_MISMATCH';
  end if;

  delete from private.student_access_security_events
   where link_id = v_link or organization_id = v_org or student_id = v_student;
  get diagnostics v_deleted = row_count;
  if v_deleted <> 3 then
    raise exception using errcode = 'P0001', message = 'STAGE32_R1_CLEANUP_SECURITY_EVENT_DELETE_COUNT_MISMATCH';
  end if;

  delete from private.student_access_security_signals
   where link_id = v_link or organization_id = v_org or student_id = v_student;
  get diagnostics v_deleted = row_count;
  if v_deleted <> 0 then
    raise exception using errcode = 'P0001', message = 'STAGE32_R1_CLEANUP_UNEXPECTED_SECURITY_SIGNAL_DELETE';
  end if;

  delete from public.organizations where id = v_org;
  get diagnostics v_deleted = row_count;
  if v_deleted <> 1 then
    raise exception using errcode = 'P0001', message = 'STAGE32_R1_CLEANUP_ORGANIZATION_DELETE_FAILED';
  end if;

  delete from auth.users where id = v_user;
  get diagnostics v_deleted = row_count;
  if v_deleted <> 1 then
    raise exception using errcode = 'P0001', message = 'STAGE32_R1_CLEANUP_AUTH_USER_DELETE_FAILED';
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
    raise exception using errcode = 'P0001', message = 'STAGE32_R1_CLEANUP_POSTCONDITION_FAILED';
  end if;
end;
$$;
