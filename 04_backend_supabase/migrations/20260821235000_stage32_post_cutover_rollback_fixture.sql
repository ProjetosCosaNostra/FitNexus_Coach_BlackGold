-- Stage 32: isolated synthetic fixture for the real post-cutover explicit rollback proof.
--
-- Failure class:
--   BGF-STAGE32-POST-CUTOVER-ROLLBACK-FIXTURE-240
--
-- Repository-first only. Apply only after CI + merge, only with an empty customer
-- domain, only while production remains Edge-selected, and only while all five direct
-- v2 RPC grants remain intact. The public synthetic bearer is derived from a stable
-- test seed; only SHA-256(token) is persisted. No real customer data, raw network
-- origin, origin digest, production credential or bearer literal is embedded.
do $$
declare
  v_user constant uuid := '5f5166fe-e774-593b-b86d-ddb9d93e16ca';
  v_org constant uuid := 'b01e4654-8a8e-5634-9ee7-3635114b1346';
  v_student constant uuid := 'e17f6053-d6dc-543a-bce7-c06cdf432e46';
  v_plan constant uuid := '8409e7e1-b853-5aab-97dd-50cf8b0d40f2';
  v_exercise constant uuid := '28a281ea-8f9e-542b-85f7-9ccd7a7ef7ee';
  v_link constant uuid := 'e2252055-fed6-5d3f-9410-1cccbe7d20c9';
  v_token constant text := encode(
    extensions.digest(
      convert_to('fitnexus-stage32-post-cutover-rollback-proof-v1', 'UTF8'),
      'sha256'
    ),
    'hex'
  );
  v_count integer;
begin
  if (select count(*) from auth.users) <> 0
     or (select count(*) from public.profiles) <> 0
     or (select count(*) from public.organizations) <> 0
     or (select count(*) from public.organization_members) <> 0
     or (select count(*) from public.organization_subscriptions) <> 0
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
     or (select count(*) from private.student_access_security_signals) <> 0 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE32_POST_CUTOVER_ROLLBACK_FIXTURE_REQUIRES_EMPTY_CUSTOMER_DOMAIN';
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
    raise exception using
      errcode = 'P0001',
      message = 'STAGE32_POST_CUTOVER_ROLLBACK_DIRECT_GRANTS_NOT_INTACT';
  end if;

  insert into auth.users (
    id,
    aud,
    role,
    raw_app_meta_data,
    raw_user_meta_data,
    created_at,
    updated_at,
    is_sso_user,
    is_anonymous
  ) values (
    v_user,
    'authenticated',
    'authenticated',
    '{"provider":"stage32_rollback_synthetic_fixture","providers":[]}'::jsonb,
    '{"fixture":"stage32_post_cutover_rollback_proof"}'::jsonb,
    now(),
    now(),
    false,
    false
  );

  insert into public.organizations (id, name, owner_user_id)
  values (v_org, 'Stage32 Rollback Synthetic Organization', v_user);

  select count(*)::integer into v_count
    from public.organization_subscriptions s
   where s.organization_id = v_org
     and s.plan_code = 'trial'
     and s.status = 'trialing';
  if v_count <> 1 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE32_POST_CUTOVER_ROLLBACK_TRIAL_INITIALIZATION_FAILED';
  end if;

  insert into public.students (
    id,
    organization_id,
    name,
    objective,
    level,
    adherence,
    status
  ) values (
    v_student,
    v_org,
    'Stage32 Rollback Synthetic Student',
    'Post-cutover explicit Edge-to-direct rollback proof',
    'Iniciante',
    0,
    'Ativo'
  );

  insert into public.training_plans (
    id,
    organization_id,
    student_id,
    name,
    next_session,
    notes,
    is_active
  ) values (
    v_plan,
    v_org,
    v_student,
    'Stage32 Rollback Synthetic Plan',
    'Synthetic rollback proof only',
    'Controlled post-cutover Edge-to-direct rollback proof; no real student data.',
    true
  );

  insert into public.training_exercises (
    id,
    organization_id,
    training_plan_id,
    position,
    name,
    prescription
  ) values (
    v_exercise,
    v_org,
    v_plan,
    0,
    'Stage32 Rollback Synthetic Exercise',
    '1 x 1 controlled rollback proof'
  );

  insert into public.student_access_links (
    id,
    organization_id,
    student_id,
    token_hash,
    is_active,
    expires_at,
    created_by,
    rotation_number
  ) values (
    v_link,
    v_org,
    v_student,
    extensions.digest(v_token, 'sha256'),
    true,
    now() + interval '4 hours',
    null,
    1
  );

  select count(*)::integer into v_count
    from private.resolve_student_access(v_token) r
   where r.link_id = v_link
     and r.organization_id = v_org
     and r.student_id = v_student;
  if v_count <> 1 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE32_POST_CUTOVER_ROLLBACK_TOKEN_RESOLUTION_FAILED';
  end if;

  if (select count(*) from auth.users where id = v_user) <> 1
     or (select count(*) from public.profiles where user_id = v_user) <> 1
     or (select count(*) from public.organizations where id = v_org and owner_user_id = v_user and name = 'Stage32 Rollback Synthetic Organization') <> 1
     or (select count(*) from public.organization_members where organization_id = v_org and user_id = v_user and role = 'owner') <> 1
     or (select count(*) from public.organization_subscriptions where organization_id = v_org and plan_code = 'trial' and status = 'trialing') <> 1
     or (select count(*) from public.students where id = v_student and organization_id = v_org and name = 'Stage32 Rollback Synthetic Student' and status = 'Ativo' and adherence = 0) <> 1
     or (select count(*) from public.training_plans where id = v_plan and student_id = v_student and organization_id = v_org and name = 'Stage32 Rollback Synthetic Plan' and is_active) <> 1
     or (select count(*) from public.training_exercises where id = v_exercise and training_plan_id = v_plan and organization_id = v_org and name = 'Stage32 Rollback Synthetic Exercise') <> 1
     or (select count(*) from public.student_access_links where id = v_link and student_id = v_student and organization_id = v_org and is_active and rotation_number = 1 and revoked_at is null) <> 1
     or (select count(*) from public.workout_sessions) <> 0
     or (select count(*) from public.workout_exercise_logs) <> 0
     or (select count(*) from public.workout_feedback) <> 0
     or (select count(*) from private.student_access_command_receipts) <> 0
     or (select count(*) from private.student_access_rate_buckets) <> 0
     or (select count(*) from private.student_access_security_events) <> 0
     or (select count(*) from private.student_access_security_signals) <> 0 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE32_POST_CUTOVER_ROLLBACK_FIXTURE_POSTCONDITION_FAILED';
  end if;
end;
$$;
