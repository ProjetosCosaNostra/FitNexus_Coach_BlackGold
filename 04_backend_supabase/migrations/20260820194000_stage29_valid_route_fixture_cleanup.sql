-- Stage 29: fail-closed cleanup for the controlled valid-route synthetic fixture.
--
-- Failure classes:
--   BGF-SYNTHETIC-VALID-ROUTE-FIXTURE-RESIDUE-188
--   BGF-LIVE-PROOF-REEXECUTION-192
--   BGF-STAGE29-CLEANUP-SCOPE-DRIFT-193
--
-- The cleanup may run only while the customer domain still consists exclusively of the
-- Stage 29 fixture. It removes the two privacy-minimized network-origin buckets created by
-- the two original live-proof executions using a narrow operation/time/count selector; no
-- origin digest or raw network origin is embedded in repository source.

do $$
declare
  v_user constant uuid := '2615749d-ffca-5319-84e0-b775578ceaf6';
  v_org constant uuid := '13678787-eeae-5f6a-8828-190723a22594';
  v_student constant uuid := '659eafee-0508-5dfb-9fcb-d285d9e846db';
  v_plan constant uuid := 'fd5762db-0a0c-54dc-81c9-2aeade199ee5';
  v_exercise constant uuid := '2ec1260b-88f2-5a2c-ba81-3433d2c147d5';
  v_link constant uuid := 'f31a3c36-4ee1-5d64-b30d-f00fc98aea9b';
  v_proof_window constant timestamptz := timestamptz '2026-08-20 19:30:00+00';
  v_count integer;
  v_deleted integer;
begin
  -- Fail closed if any real customer-domain row appeared after fixture creation.
  if (select count(*) from auth.users) <> 1
     or (select count(*) from public.organizations) <> 1
     or (select count(*) from public.students) <> 1
     or (select count(*) from public.training_plans) <> 1
     or (select count(*) from public.training_exercises) <> 1
     or (select count(*) from public.student_access_links) <> 1 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE29_CLEANUP_CUSTOMER_DOMAIN_NO_LONGER_SYNTHETIC_ONLY';
  end if;

  if (select count(*) from auth.users where id = v_user) <> 1
     or (select count(*) from public.profiles where user_id = v_user) <> 1
     or (select count(*) from public.organizations where id = v_org and owner_user_id = v_user) <> 1
     or (select count(*) from public.organization_members where organization_id = v_org and user_id = v_user and role = 'owner') <> 1
     or (select count(*) from public.organization_subscriptions where organization_id = v_org and plan_code = 'trial' and status = 'trialing') <> 1
     or (select count(*) from public.subscription_authority_events where organization_id = v_org and event_type = 'trial_initialized') <> 1
     or (select count(*) from public.students where id = v_student and organization_id = v_org) <> 1
     or (select count(*) from public.training_plans where id = v_plan and student_id = v_student and organization_id = v_org and is_active) <> 1
     or (select count(*) from public.training_exercises where id = v_exercise and training_plan_id = v_plan and organization_id = v_org) <> 1
     or (select count(*) from public.student_access_links where id = v_link and student_id = v_student and organization_id = v_org) <> 1 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE29_CLEANUP_FIXTURE_IDENTITY_MISMATCH';
  end if;

  -- The successful proof was GET-only and must not have mutated workout/business state.
  if (select count(*) from public.workout_sessions) <> 0
     or (select count(*) from public.workout_exercise_logs) <> 0
     or (select count(*) from public.workout_feedback) <> 0
     or (select count(*) from public.billing_checkout_intents where organization_id = v_org) <> 0
     or (select count(*) from public.billing_webhook_receipts where organization_id = v_org) <> 0
     or (select count(*) from public.coach_action_events where organization_id = v_org) <> 0
     or (select count(*) from public.decision_intelligence_runs where organization_id = v_org) <> 0
     or (select count(*) from public.decision_intelligence_outcomes where organization_id = v_org) <> 0 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE29_CLEANUP_UNEXPECTED_SYNTHETIC_BUSINESS_MUTATION';
  end if;

  if (select count(*) from private.growth_events where organization_id = v_org) <> 4
     or (select count(*) from private.growth_attribution where organization_id = v_org) <> 0 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE29_CLEANUP_GROWTH_FIXTURE_DRIFT';
  end if;

  select count(*)::integer into v_count
    from private.student_access_rate_buckets
   where link_id = v_link
     and operation = 'get_workout'
     and window_started_at = v_proof_window
     and request_count = 2;
  if v_count <> 1 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE29_CLEANUP_LINK_RATE_BUCKET_DRIFT';
  end if;

  if (select count(*) from private.student_access_command_receipts where link_id = v_link) <> 0
     or (select count(*) from private.student_access_security_events where link_id = v_link) <> 0
     or (select count(*) from private.student_access_security_signals where link_id = v_link) <> 0 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE29_CLEANUP_UNEXPECTED_LINK_SECURITY_RESIDUE';
  end if;

  select count(*)::integer into v_count
    from private.student_access_network_rate_buckets
   where operation = 'get_workout'
     and window_started_at = v_proof_window
     and request_count = 1
     and last_seen_at >= v_proof_window
     and last_seen_at < v_proof_window + interval '1 minute';
  if v_count <> 2 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE29_CLEANUP_NETWORK_BUCKET_SELECTOR_MISMATCH';
  end if;

  delete from private.student_access_network_rate_buckets
   where operation = 'get_workout'
     and window_started_at = v_proof_window
     and request_count = 1
     and last_seen_at >= v_proof_window
     and last_seen_at < v_proof_window + interval '1 minute';
  get diagnostics v_deleted = row_count;
  if v_deleted <> 2 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE29_CLEANUP_NETWORK_BUCKET_DELETE_COUNT_MISMATCH';
  end if;

  -- Delete the organization first because organizations.owner_user_id restricts auth-user
  -- deletion. Organization cascades remove the synthetic student domain, subscription,
  -- membership, growth telemetry and link-owned rate bucket.
  delete from public.organizations where id = v_org;
  get diagnostics v_deleted = row_count;
  if v_deleted <> 1 then
    raise exception using errcode = 'P0001', message = 'STAGE29_CLEANUP_ORGANIZATION_DELETE_FAILED';
  end if;

  delete from auth.users where id = v_user;
  get diagnostics v_deleted = row_count;
  if v_deleted <> 1 then
    raise exception using errcode = 'P0001', message = 'STAGE29_CLEANUP_AUTH_USER_DELETE_FAILED';
  end if;

  -- Complete postcondition: customer domain returns to the pre-fixture empty baseline and
  -- all specifically observed proof residue is absent. Any mismatch aborts transactionally.
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
     or (select count(*) from private.growth_events where organization_id = v_org) <> 0
     or (select count(*) from private.growth_attribution where organization_id = v_org) <> 0
     or (select count(*) from private.student_access_rate_buckets where link_id = v_link) <> 0
     or (select count(*) from private.student_access_command_receipts where link_id = v_link) <> 0
     or (select count(*) from private.student_access_security_events where link_id = v_link) <> 0
     or (select count(*) from private.student_access_security_signals where link_id = v_link) <> 0
     or (select count(*) from private.student_access_network_rate_buckets
          where operation = 'get_workout'
            and window_started_at = v_proof_window
            and request_count = 1
            and last_seen_at >= v_proof_window
            and last_seen_at < v_proof_window + interval '1 minute') <> 0 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE29_CLEANUP_POSTCONDITION_FAILED';
  end if;
end;
$$;
