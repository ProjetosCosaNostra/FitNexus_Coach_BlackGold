-- Stage 30: fail-closed cleanup for the controlled five-route Edge runtime smoke fixture.
--
-- Failure classes:
--   BGF-STAGE30-RUNTIME-SMOKE-FIXTURE-RESIDUE-203
--   BGF-STAGE30-RUNTIME-SMOKE-CLEANUP-SCOPE-207
--
-- The cleanup may run only while the customer domain consists exclusively of the exact
-- Stage 30 synthetic fixture after the sealed five-route proof. It removes the five
-- privacy-minimized network-rate buckets created by that proof using operation/time/count
-- selectors. No raw network origin or network-origin digest is embedded in this source.

do $$
declare
  v_user constant uuid := '33e39af7-f470-510e-8a9c-fc70b16ba26e';
  v_org constant uuid := 'a0749405-6367-52d5-ad8b-5115b8d3a905';
  v_student constant uuid := '81d3be6f-824e-59bc-8fa0-27acf046d6d3';
  v_plan constant uuid := '82b92191-a8e3-5bb2-8f5d-fec9a59a57bb';
  v_exercise constant uuid := 'fe116050-9061-5627-8e3a-dedd863d6447';
  v_link constant uuid := '53dfab53-5ff8-573a-ab2a-faaea24107db';
  v_window_0802 constant timestamptz := timestamptz '2026-08-21 08:02:00+00';
  v_window_0803 constant timestamptz := timestamptz '2026-08-21 08:03:00+00';
  v_start_command constant text := 'fadd0c2168b5e958a5e7497e3219c84e';
  v_completion_command constant text := 'd3ecb7c48b714739111f99b9be656b85';
  v_feedback_command constant text := '774b6b75ac6dce7f0467a28c9df68e62';
  v_session uuid;
  v_count integer;
  v_deleted integer;
begin
  -- Customer domain must still be synthetic-only. Any real row aborts the transaction.
  if (select count(*) from auth.users) <> 1
     or (select count(*) from public.profiles) <> 1
     or (select count(*) from public.organizations) <> 1
     or (select count(*) from public.organization_members) <> 1
     or (select count(*) from public.organization_subscriptions) <> 1
     or (select count(*) from public.students) <> 1
     or (select count(*) from public.training_plans) <> 1
     or (select count(*) from public.training_exercises) <> 1
     or (select count(*) from public.student_access_links) <> 1
     or (select count(*) from public.workout_sessions) <> 1
     or (select count(*) from public.workout_exercise_logs) <> 1
     or (select count(*) from public.workout_feedback) <> 1 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE30_CLEANUP_CUSTOMER_DOMAIN_NO_LONGER_SYNTHETIC_ONLY';
  end if;

  if (select count(*) from auth.users where id = v_user) <> 1
     or (select count(*) from public.profiles where user_id = v_user) <> 1
     or (select count(*) from public.organizations where id = v_org and owner_user_id = v_user and name = 'Stage30 Synthetic Organization') <> 1
     or (select count(*) from public.organization_members where organization_id = v_org and user_id = v_user and role = 'owner') <> 1
     or (select count(*) from public.organization_subscriptions where organization_id = v_org and plan_code = 'trial' and status = 'trialing') <> 1
     or (select count(*) from public.subscription_authority_events where organization_id = v_org and event_type = 'trial_initialized') <> 1
     or (select count(*) from public.students where id = v_student and organization_id = v_org and name = 'Stage30 Synthetic Student' and status = 'Treino concluído' and adherence = 100) <> 1
     or (select count(*) from public.training_plans where id = v_plan and student_id = v_student and organization_id = v_org and name = 'Stage30 Synthetic Plan' and is_active) <> 1
     or (select count(*) from public.training_exercises where id = v_exercise and training_plan_id = v_plan and organization_id = v_org and name = 'Stage30 Synthetic Exercise') <> 1
     or (select count(*) from public.student_access_links where id = v_link and student_id = v_student and organization_id = v_org and is_active and last_used_at is not null) <> 1 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE30_CLEANUP_FIXTURE_IDENTITY_MISMATCH';
  end if;

  select ws.id into v_session
    from public.workout_sessions ws
   where ws.organization_id = v_org
     and ws.student_id = v_student
     and ws.training_plan_id = v_plan
     and ws.student_access_link_id = v_link
     and ws.status = 'completed'
     and ws.completed_at is not null;
  if v_session is null then
    raise exception using errcode = 'P0001', message = 'STAGE30_CLEANUP_COMPLETED_SESSION_MISSING';
  end if;

  if (select count(*) from public.workout_exercise_logs
       where organization_id = v_org
         and session_id = v_session
         and training_plan_id = v_plan
         and exercise_id = v_exercise
         and completed
         and completed_at is not null) <> 1
     or (select count(*) from public.workout_feedback
          where organization_id = v_org
            and student_id = v_student
            and session_id = v_session
            and perceived_exertion = 5
            and pain_score = 0
            and energy_score = 4
            and pain_location is null
            and note is null) <> 1 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE30_CLEANUP_PROOF_MUTATION_STATE_DRIFT';
  end if;

  if (select count(*) from private.growth_events where organization_id = v_org) <> 5
     or (select count(*) from private.growth_attribution where organization_id = v_org) <> 0
     or (select count(*) from public.billing_checkout_intents where organization_id = v_org) <> 0
     or (select count(*) from public.billing_webhook_receipts where organization_id = v_org) <> 0
     or (select count(*) from public.coach_action_events where organization_id = v_org) <> 0
     or (select count(*) from public.decision_intelligence_runs where organization_id = v_org) <> 0
     or (select count(*) from public.decision_intelligence_outcomes where organization_id = v_org) <> 0 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE30_CLEANUP_UNEXPECTED_SYNTHETIC_BUSINESS_MUTATION';
  end if;

  if (select count(*) from private.student_access_rate_buckets where link_id = v_link) <> 5
     or (select count(*) from private.student_access_rate_buckets where link_id = v_link and operation = 'get_workout' and request_count = 1) <> 1
     or (select count(*) from private.student_access_rate_buckets where link_id = v_link and operation = 'start_workout' and request_count = 1) <> 1
     or (select count(*) from private.student_access_rate_buckets where link_id = v_link and operation = 'set_completion' and request_count = 1) <> 1
     or (select count(*) from private.student_access_rate_buckets where link_id = v_link and operation = 'get_feedback_context' and request_count = 1) <> 1
     or (select count(*) from private.student_access_rate_buckets where link_id = v_link and operation = 'submit_feedback' and request_count = 1) <> 1 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE30_CLEANUP_LINK_RATE_BUCKET_DRIFT';
  end if;

  if (select count(*) from private.student_access_command_receipts where link_id = v_link) <> 3
     or (select count(*) from private.student_access_command_receipts where link_id = v_link and operation = 'start_workout' and command_id = v_start_command and completed_at is not null and response is not null) <> 1
     or (select count(*) from private.student_access_command_receipts where link_id = v_link and operation = 'set_completion' and command_id = v_completion_command and completed_at is not null and response is not null) <> 1
     or (select count(*) from private.student_access_command_receipts where link_id = v_link and operation = 'submit_feedback' and command_id = v_feedback_command and completed_at is not null and response is not null) <> 1 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE30_CLEANUP_COMMAND_RECEIPT_DRIFT';
  end if;

  if (select count(*) from private.student_access_security_events where link_id = v_link) <> 3
     or (select count(*) from private.student_access_security_events where link_id = v_link and operation = 'start_workout' and outcome = 'allowed' and command_id = v_start_command) <> 1
     or (select count(*) from private.student_access_security_events where link_id = v_link and operation = 'set_completion' and outcome = 'allowed' and command_id = v_completion_command) <> 1
     or (select count(*) from private.student_access_security_events where link_id = v_link and operation = 'submit_feedback' and outcome = 'allowed' and command_id = v_feedback_command) <> 1
     or (select count(*) from private.student_access_security_signals where link_id = v_link) <> 0 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE30_CLEANUP_LINK_SECURITY_STATE_DRIFT';
  end if;

  -- Narrow proof-network selector. Each operation must have exactly one one-request bucket
  -- inside the observed proof minute; no pseudonymous digest is read or embedded.
  if (select count(*) from private.student_access_network_rate_buckets
       where operation = 'get_workout' and window_started_at = v_window_0802 and request_count = 1
         and last_seen_at >= v_window_0802 and last_seen_at < v_window_0802 + interval '1 minute') <> 1
     or (select count(*) from private.student_access_network_rate_buckets
          where operation = 'start_workout' and window_started_at = v_window_0802 and request_count = 1
            and last_seen_at >= v_window_0802 and last_seen_at < v_window_0802 + interval '1 minute') <> 1
     or (select count(*) from private.student_access_network_rate_buckets
          where operation = 'set_completion' and window_started_at = v_window_0802 and request_count = 1
            and last_seen_at >= v_window_0802 and last_seen_at < v_window_0802 + interval '1 minute') <> 1
     or (select count(*) from private.student_access_network_rate_buckets
          where operation = 'get_feedback_context' and window_started_at = v_window_0802 and request_count = 1
            and last_seen_at >= v_window_0802 and last_seen_at < v_window_0802 + interval '1 minute') <> 1
     or (select count(*) from private.student_access_network_rate_buckets
          where operation = 'submit_feedback' and window_started_at = v_window_0803 and request_count = 1
            and last_seen_at >= v_window_0803 and last_seen_at < v_window_0803 + interval '1 minute') <> 1 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE30_CLEANUP_NETWORK_BUCKET_SELECTOR_MISMATCH';
  end if;

  delete from private.student_access_network_rate_buckets
   where (operation = 'get_workout' and window_started_at = v_window_0802 and request_count = 1
            and last_seen_at >= v_window_0802 and last_seen_at < v_window_0802 + interval '1 minute')
      or (operation = 'start_workout' and window_started_at = v_window_0802 and request_count = 1
            and last_seen_at >= v_window_0802 and last_seen_at < v_window_0802 + interval '1 minute')
      or (operation = 'set_completion' and window_started_at = v_window_0802 and request_count = 1
            and last_seen_at >= v_window_0802 and last_seen_at < v_window_0802 + interval '1 minute')
      or (operation = 'get_feedback_context' and window_started_at = v_window_0802 and request_count = 1
            and last_seen_at >= v_window_0802 and last_seen_at < v_window_0802 + interval '1 minute')
      or (operation = 'submit_feedback' and window_started_at = v_window_0803 and request_count = 1
            and last_seen_at >= v_window_0803 and last_seen_at < v_window_0803 + interval '1 minute');
  get diagnostics v_deleted = row_count;
  if v_deleted <> 5 then
    raise exception using errcode = 'P0001', message = 'STAGE30_CLEANUP_NETWORK_BUCKET_DELETE_COUNT_MISMATCH';
  end if;

  -- Security events use ON DELETE SET NULL for link ownership, so delete the exact three
  -- synthetic command events before organization deletion while the fixed link is available.
  delete from private.student_access_security_events
   where link_id = v_link
     and outcome = 'allowed'
     and ((operation = 'start_workout' and command_id = v_start_command)
       or (operation = 'set_completion' and command_id = v_completion_command)
       or (operation = 'submit_feedback' and command_id = v_feedback_command));
  get diagnostics v_deleted = row_count;
  if v_deleted <> 3 then
    raise exception using errcode = 'P0001', message = 'STAGE30_CLEANUP_SECURITY_EVENT_DELETE_COUNT_MISMATCH';
  end if;

  -- Organization first: owner_user_id prevents deleting the synthetic auth user first.
  -- Cascades remove student/workout/subscription/growth/link-owned private state.
  delete from public.organizations where id = v_org;
  get diagnostics v_deleted = row_count;
  if v_deleted <> 1 then
    raise exception using errcode = 'P0001', message = 'STAGE30_CLEANUP_ORGANIZATION_DELETE_FAILED';
  end if;

  delete from auth.users where id = v_user;
  get diagnostics v_deleted = row_count;
  if v_deleted <> 1 then
    raise exception using errcode = 'P0001', message = 'STAGE30_CLEANUP_AUTH_USER_DELETE_FAILED';
  end if;

  -- Transactional postcondition: return to the pre-fixture empty customer baseline and
  -- prove all specifically owned smoke residue is gone.
  if (select count(*) from auth.users) <> 0
     or (select count(*) from public.profiles) <> 0
     or (select count(*) from public.organizations) <> 0
     or (select count(*) from public.organization_members) <> 0
     or (select count(*) from public.organization_subscriptions) <> 0
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
     or (select count(*) from private.student_access_security_events where link_id = v_link) <> 0
     or (select count(*) from private.student_access_security_signals where link_id = v_link) <> 0
     or (select count(*) from private.student_access_network_rate_buckets
          where (operation in ('get_workout','start_workout','set_completion','get_feedback_context')
                 and window_started_at = v_window_0802 and request_count = 1
                 and last_seen_at >= v_window_0802 and last_seen_at < v_window_0802 + interval '1 minute')
             or (operation = 'submit_feedback' and window_started_at = v_window_0803 and request_count = 1
                 and last_seen_at >= v_window_0803 and last_seen_at < v_window_0803 + interval '1 minute')) <> 0 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE30_CLEANUP_POSTCONDITION_FAILED';
  end if;
end;
$$;
