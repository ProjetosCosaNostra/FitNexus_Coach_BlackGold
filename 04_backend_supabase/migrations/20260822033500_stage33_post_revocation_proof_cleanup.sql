-- Stage 33: fail-closed cleanup after the sealed post-revocation production Edge proof.
--
-- Failure classes:
--   BGF-STAGE33-REVOCATION-PROOF-REEXECUTION-255
--   BGF-STAGE33-POST-REVOCATION-PROOF-CLEANUP-262
--   BGF-STAGE33-POST-REVOCATION-NETWORK-RESIDUE-263
--
-- Authorized only after workflow run 32548995700 / job 96972506797 completed
-- successfully at exact frozen proof head b8123abb7f0dda364f49d9f7342e5887c7da6553.
-- The proof first established direct anonymous RPC denial with HTTP 401, then proved all
-- five student routes through StudentAccessTransport.instance with production Edge still
-- selected and automatic Edge-to-direct fallback disabled. This cleanup deletes only the
-- exact Stage33 synthetic customer/runtime proof residue and the exact five network-origin
-- rate buckets created during the sealed proof minute. No raw bearer, raw network origin,
-- network-origin digest, production credential, or real customer data is embedded.
-- Direct anon/auth execution MUST remain revoked; service_role and authenticated token
-- issuance MUST remain intact before and after cleanup.
do $$
declare
  v_user constant uuid := 'c91c6cec-618b-58fc-99fc-948ab08895c4';
  v_org constant uuid := '3e4d79f5-9565-5ac9-b5e0-32ea4937d85b';
  v_student constant uuid := '87b426f7-73f0-53ec-880b-a75767415dbf';
  v_plan constant uuid := '059af7ff-3b6b-5e41-ac46-e4e73e4b5107';
  v_exercise constant uuid := '5f1b2d42-20f7-5701-9484-f1dcb9e1dcc2';
  v_link constant uuid := 'e412e8d8-7b09-5b09-bd06-dd9ea8fb6af1';
  v_session constant uuid := 'f70ef095-d693-48f7-a0e6-aeff55c4f7a9';
  v_log constant uuid := '799bfc07-e7be-48ea-a35f-afe37acc5016';
  v_feedback constant uuid := '479328d6-77ce-4fe2-a19a-232993fe1f04';
  v_proof_window constant timestamptz := timestamptz '2026-08-22 03:27:00+00';
  v_count integer;
  v_deleted integer;
begin
  -- Full customer/runtime domain must still be exactly the single Stage33 fixture.
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
    raise exception using errcode = 'P0001',
      message = 'STAGE33_CLEANUP_CUSTOMER_DOMAIN_NO_LONGER_EXACT_SYNTHETIC_PROOF';
  end if;

  -- Fixture identity and final business state are exact.
  if (select count(*) from auth.users where id = v_user) <> 1
     or (select count(*) from public.profiles where user_id = v_user) <> 1
     or (select count(*) from public.organizations where id = v_org and owner_user_id = v_user and name = 'Stage33 Post-Revocation Synthetic Organization') <> 1
     or (select count(*) from public.organization_members where organization_id = v_org and user_id = v_user and role = 'owner') <> 1
     or (select count(*) from public.organization_subscriptions where organization_id = v_org and plan_code = 'trial' and status = 'trialing') <> 1
     or (select count(*) from public.subscription_authority_events where organization_id = v_org and event_type = 'trial_initialized' and created_at = timestamptz '2026-08-22 03:24:56.584383+00') <> 1
     or (select count(*) from public.students where id = v_student and organization_id = v_org and name = 'Stage33 Post-Revocation Synthetic Student' and status = 'Treino concluído' and adherence = 100 and last_workout = 'Stage33 Post-Revocation Synthetic Plan' and last_workout_date = date '2026-08-22') <> 1
     or (select count(*) from public.training_plans where id = v_plan and student_id = v_student and organization_id = v_org and name = 'Stage33 Post-Revocation Synthetic Plan' and is_active) <> 1
     or (select count(*) from public.training_exercises where id = v_exercise and training_plan_id = v_plan and organization_id = v_org and name = 'Stage33 Post-Revocation Synthetic Exercise') <> 1
     or (select count(*) from public.student_access_links where id = v_link and student_id = v_student and organization_id = v_org and is_active and rotation_number = 1 and revoked_at is null and expires_at = timestamptz '2026-08-22 07:24:56.584383+00') <> 1 then
    raise exception using errcode = 'P0001', message = 'STAGE33_CLEANUP_FIXTURE_IDENTITY_MISMATCH';
  end if;

  -- Exact business receipts from the sealed five-route Edge proof.
  if (select count(*) from public.workout_sessions where id = v_session and organization_id = v_org and student_id = v_student and training_plan_id = v_plan and student_access_link_id = v_link and status = 'completed' and started_at = timestamptz '2026-08-22 03:27:38.146771+00' and completed_at = timestamptz '2026-08-22 03:27:39.113229+00') <> 1
     or (select count(*) from public.workout_exercise_logs where id = v_log and organization_id = v_org and session_id = v_session and training_plan_id = v_plan and exercise_id = v_exercise and completed and completed_at = timestamptz '2026-08-22 03:27:39.113229+00') <> 1
     or (select count(*) from public.workout_feedback where id = v_feedback and organization_id = v_org and student_id = v_student and session_id = v_session and perceived_exertion = 5 and pain_score = 0 and energy_score = 4 and pain_location is null and note is null and submitted_at = timestamptz '2026-08-22 03:27:40.411434+00') <> 1 then
    raise exception using errcode = 'P0001', message = 'STAGE33_CLEANUP_LIVE_PROOF_BUSINESS_RECEIPT_DRIFT';
  end if;

  -- Exactly the three mutating command receipts created by the proof.
  if (select count(*) from private.student_access_command_receipts where link_id = v_link) <> 3
     or (select count(*) from private.student_access_command_receipts where link_id = v_link and operation = 'start_workout' and command_id = '34000000000000000000000000000001' and completed_at = timestamptz '2026-08-22 03:27:38.146771+00') <> 1
     or (select count(*) from private.student_access_command_receipts where link_id = v_link and operation = 'set_completion' and command_id = '34000000000000000000000000000002' and completed_at = timestamptz '2026-08-22 03:27:39.113229+00') <> 1
     or (select count(*) from private.student_access_command_receipts where link_id = v_link and operation = 'submit_feedback' and command_id = '34000000000000000000000000000003' and completed_at = timestamptz '2026-08-22 03:27:40.411434+00') <> 1 then
    raise exception using errcode = 'P0001', message = 'STAGE33_CLEANUP_COMMAND_RECEIPT_DRIFT';
  end if;

  -- Link-scoped possession-token limiter: one exact bucket per route in the proof minute.
  if (select count(*) from private.student_access_rate_buckets where link_id = v_link) <> 5
     or (select count(distinct operation) from private.student_access_rate_buckets where link_id = v_link and window_started_at = v_proof_window and request_count = 1 and operation in ('get_workout','start_workout','set_completion','get_feedback_context','submit_feedback')) <> 5 then
    raise exception using errcode = 'P0001', message = 'STAGE33_CLEANUP_LINK_RATE_BUCKET_DRIFT';
  end if;

  -- Mutating routes emitted exactly three allowed security events and no derived signal.
  if (select count(*) from private.student_access_security_events where link_id = v_link or organization_id = v_org or student_id = v_student) <> 3
     or (select count(*) from private.student_access_security_events where link_id = v_link and outcome = 'allowed' and operation = 'start_workout' and command_id = '34000000000000000000000000000001' and occurred_at = timestamptz '2026-08-22 03:27:38.146771+00') <> 1
     or (select count(*) from private.student_access_security_events where link_id = v_link and outcome = 'allowed' and operation = 'set_completion' and command_id = '34000000000000000000000000000002' and occurred_at = timestamptz '2026-08-22 03:27:39.113229+00') <> 1
     or (select count(*) from private.student_access_security_events where link_id = v_link and outcome = 'allowed' and operation = 'submit_feedback' and command_id = '34000000000000000000000000000003' and occurred_at = timestamptz '2026-08-22 03:27:40.411434+00') <> 1
     or (select count(*) from private.student_access_security_signals where link_id = v_link or organization_id = v_org or student_id = v_student) <> 0 then
    raise exception using errcode = 'P0001', message = 'STAGE33_CLEANUP_SECURITY_RECEIPT_DRIFT';
  end if;

  -- Four fixture setup growth events plus the proof workout_logged event, nothing else.
  if (select count(*) from private.growth_events where organization_id = v_org) <> 5
     or (select count(*) from private.growth_events where organization_id = v_org and event_name = 'trial_started' and occurred_at = timestamptz '2026-08-22 03:24:56.584383+00') <> 1
     or (select count(*) from private.growth_events where organization_id = v_org and event_name = 'student_created' and occurred_at = timestamptz '2026-08-22 03:24:56.584383+00') <> 1
     or (select count(*) from private.growth_events where organization_id = v_org and event_name = 'training_created_or_duplicated' and occurred_at = timestamptz '2026-08-22 03:24:56.584383+00') <> 1
     or (select count(*) from private.growth_events where organization_id = v_org and event_name = 'training_delivered' and occurred_at = timestamptz '2026-08-22 03:24:56.584383+00') <> 1
     or (select count(*) from private.growth_events where organization_id = v_org and event_name = 'workout_logged' and source_entity_id = v_session and occurred_at = timestamptz '2026-08-22 03:27:39.113229+00') <> 1
     or (select count(*) from private.growth_attribution where organization_id = v_org) <> 0
     or (select count(*) from private.growth_events) <> 11 then
    raise exception using errcode = 'P0001', message = 'STAGE33_CLEANUP_GROWTH_RECEIPT_DRIFT';
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
    raise exception using errcode = 'P0001', message = 'STAGE33_CLEANUP_UNEXPECTED_SYNTHETIC_DOMAIN_MUTATION';
  end if;

  -- Edge path created exactly five network-origin buckets in the proof minute. The raw
  -- origin and its digest are deliberately not embedded. Empty customer domain before the
  -- proof, a single origin hash across the five route operations, exact minute/count and
  -- the historical 13-row baseline make this proof residue uniquely bounded.
  if (select count(*) from private.student_access_network_rate_buckets) <> 18
     or (select count(*) from private.student_access_network_rate_buckets
          where operation in ('get_workout','start_workout','set_completion','get_feedback_context','submit_feedback')
            and window_started_at = v_proof_window
            and request_count = 1
            and last_seen_at >= v_proof_window
            and last_seen_at < v_proof_window + interval '1 minute') <> 5
     or (select count(distinct origin_hash) from private.student_access_network_rate_buckets
          where operation in ('get_workout','start_workout','set_completion','get_feedback_context','submit_feedback')
            and window_started_at = v_proof_window
            and request_count = 1
            and last_seen_at >= v_proof_window
            and last_seen_at < v_proof_window + interval '1 minute') <> 1 then
    raise exception using errcode = 'P0001', message = 'STAGE33_CLEANUP_EDGE_NETWORK_RECEIPT_DRIFT';
  end if;

  -- Revocation is now the production security boundary: external direct execution must
  -- remain denied while the privileged Edge backend retains all five and token issuance
  -- remains authenticated-only authority.
  select count(*)::integer into v_count
    from pg_proc p
    join pg_namespace n on n.oid = p.pronamespace
   where n.nspname = 'public'
     and p.proname in ('get_student_feedback_context_v2','get_student_workout_v2','set_student_exercise_completion_v2','start_student_workout_v2','submit_student_workout_feedback_v2')
     and not has_function_privilege('anon', p.oid, 'EXECUTE')
     and not has_function_privilege('authenticated', p.oid, 'EXECUTE')
     and has_function_privilege('service_role', p.oid, 'EXECUTE');
  if v_count <> 5 or not has_function_privilege('authenticated','public.issue_student_access_token_v2(uuid)','EXECUTE') then
    raise exception using errcode = 'P0001', message = 'STAGE33_CLEANUP_REVOCATION_BOUNDARY_DRIFT';
  end if;

  -- Security-event link FK uses ON DELETE SET NULL, so delete exact proof events first.
  delete from private.student_access_security_events
   where link_id = v_link or organization_id = v_org or student_id = v_student;
  get diagnostics v_deleted = row_count;
  if v_deleted <> 3 then
    raise exception using errcode = 'P0001', message = 'STAGE33_CLEANUP_SECURITY_EVENT_DELETE_COUNT_MISMATCH';
  end if;

  delete from private.student_access_security_signals
   where link_id = v_link or organization_id = v_org or student_id = v_student;
  get diagnostics v_deleted = row_count;
  if v_deleted <> 0 then
    raise exception using errcode = 'P0001', message = 'STAGE33_CLEANUP_UNEXPECTED_SECURITY_SIGNAL_DELETE';
  end if;

  -- Remove only the five exact synthetic Edge network buckets; preserve the 13 historical rows.
  delete from private.student_access_network_rate_buckets
   where operation in ('get_workout','start_workout','set_completion','get_feedback_context','submit_feedback')
     and window_started_at = v_proof_window
     and request_count = 1
     and last_seen_at >= v_proof_window
     and last_seen_at < v_proof_window + interval '1 minute';
  get diagnostics v_deleted = row_count;
  if v_deleted <> 5 then
    raise exception using errcode = 'P0001', message = 'STAGE33_CLEANUP_NETWORK_BUCKET_DELETE_COUNT_MISMATCH';
  end if;

  delete from public.organizations where id = v_org;
  get diagnostics v_deleted = row_count;
  if v_deleted <> 1 then
    raise exception using errcode = 'P0001', message = 'STAGE33_CLEANUP_ORGANIZATION_DELETE_FAILED';
  end if;

  delete from auth.users where id = v_user;
  get diagnostics v_deleted = row_count;
  if v_deleted <> 1 then
    raise exception using errcode = 'P0001', message = 'STAGE33_CLEANUP_AUTH_USER_DELETE_FAILED';
  end if;

  -- Zero exact synthetic residue; preserve historical global telemetry and revocation.
  if (select count(*) from auth.users) <> 0
     or (select count(*) from public.profiles) <> 0
     or (select count(*) from public.organizations) <> 0
     or (select count(*) from public.organization_members) <> 0
     or (select count(*) from public.organization_subscriptions) <> 0
     or (select count(*) from public.subscription_authority_events) <> 0
     or (select count(*) from public.students) <> 0
     or (select count(*) from public.training_plans) <> 0
     or (select count(*) from public.training_exercises) <> 0
     or (select count(*) from public.student_access_links) <> 0
     or (select count(*) from public.workout_sessions) <> 0
     or (select count(*) from public.workout_exercise_logs) <> 0
     or (select count(*) from public.workout_feedback) <> 0
     or (select count(*) from private.student_access_command_receipts) <> 0
     or (select count(*) from private.student_access_rate_buckets) <> 0
     or (select count(*) from private.student_access_security_events) <> 0
     or (select count(*) from private.student_access_security_signals) <> 0
     or (select count(*) from private.growth_events where organization_id = v_org) <> 0
     or (select count(*) from private.growth_attribution where organization_id = v_org) <> 0
     or (select count(*) from private.growth_events) <> 6
     or (select count(*) from private.student_access_network_rate_buckets) <> 13 then
    raise exception using errcode = 'P0001', message = 'STAGE33_CLEANUP_POSTCONDITION_SYNTHETIC_RESIDUE';
  end if;

  select count(*)::integer into v_count
    from pg_proc p
    join pg_namespace n on n.oid = p.pronamespace
   where n.nspname = 'public'
     and p.proname in ('get_student_feedback_context_v2','get_student_workout_v2','set_student_exercise_completion_v2','start_student_workout_v2','submit_student_workout_feedback_v2')
     and not has_function_privilege('anon', p.oid, 'EXECUTE')
     and not has_function_privilege('authenticated', p.oid, 'EXECUTE')
     and has_function_privilege('service_role', p.oid, 'EXECUTE');
  if v_count <> 5 or not has_function_privilege('authenticated','public.issue_student_access_token_v2(uuid)','EXECUTE') then
    raise exception using errcode = 'P0001', message = 'STAGE33_CLEANUP_POSTCONDITION_REVOCATION_CHANGED';
  end if;
end;
$$;
