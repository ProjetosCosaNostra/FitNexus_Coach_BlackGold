-- Stage 33 candidate only: atomically seed the deterministic post-revocation Edge proof fixture
-- and retire direct anon/authenticated EXECUTE on the five student route v2 RPCs.
--
-- This file is NOT a migration and MUST NOT be executed from operations/. It is the exact
-- repository-first source candidate that a later promotion lifecycle may copy into a named
-- migration only after its preparation gate is merged and revalidated.
--
-- Failure classes:
--   BGF-STAGE33-PRIVILEGE-REVOCATION-PREMATURE-245
--   BGF-STAGE33-POST-REVOCATION-FIXTURE-249
--   BGF-STAGE33-REVOCATION-TARGET-DRIFT-250
--   BGF-STAGE33-REVOCATION-SERVICE-ROLE-LOSS-251
--
-- The Edge gateway uses a privileged backend credential; service_role EXECUTE must remain.
-- issue_student_access_token_v2(uuid) is professor/manager authority and is not a target.
do $$
declare
  v_user constant uuid := 'c91c6cec-618b-58fc-99fc-948ab08895c4';
  v_org constant uuid := '3e4d79f5-9565-5ac9-b5e0-32ea4937d85b';
  v_student constant uuid := '87b426f7-73f0-53ec-880b-a75767415dbf';
  v_plan constant uuid := '059af7ff-3b6b-5e41-ac46-e4e73e4b5107';
  v_exercise constant uuid := '5f1b2d42-20f7-5701-9484-f1dcb9e1dcc2';
  v_link constant uuid := 'e412e8d8-7b09-5b09-bd06-dd9ea8fb6af1';
  v_token constant text := encode(
    extensions.digest(
      convert_to('fitnexus-stage33-post-revocation-edge-proof-v1', 'UTF8'),
      'sha256'
    ),
    'hex'
  );
  v_count integer;
  v_posture text;
begin
  -- Customer/runtime domain must still be empty after Stage32 cleanup.
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
    raise exception using errcode = 'P0001',
      message = 'STAGE33_REVOCATION_REQUIRES_EMPTY_CUSTOMER_DOMAIN';
  end if;

  -- A fresh quiet 60-minute posture is required at the moment privileges are changed.
  select p.posture into v_posture
    from private.student_access_security_posture_v1 p;
  if v_posture is distinct from 'quiet'
     or (select count(*) from private.student_access_security_signals where last_seen_at >= now() - interval '60 minutes') <> 0
     or (select count(*) from private.student_access_security_events where occurred_at >= now() - interval '60 minutes') <> 0
     or (select count(*) from private.student_access_network_rate_buckets where last_seen_at >= now() - interval '60 minutes') <> 0 then
    raise exception using errcode = 'P0001',
      message = 'STAGE33_REVOCATION_SECURITY_OBSERVATION_NOT_QUIET';
  end if;

  -- Exact five route functions must exist and still expose the old direct roles before cut.
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
     and has_function_privilege('authenticated', p.oid, 'EXECUTE')
     and has_function_privilege('service_role', p.oid, 'EXECUTE');
  if v_count <> 5 then
    raise exception using errcode = 'P0001',
      message = 'STAGE33_REVOCATION_PRECONDITION_DIRECT_GRANTS_DRIFT';
  end if;

  if not has_function_privilege(
    'authenticated',
    'public.issue_student_access_token_v2(uuid)',
    'EXECUTE'
  ) then
    raise exception using errcode = 'P0001',
      message = 'STAGE33_REVOCATION_ISSUE_TOKEN_AUTHORITY_NOT_INTACT';
  end if;

  -- Deterministic synthetic customer used only by the post-revocation production Edge proof.
  insert into auth.users (
    id, aud, role, raw_app_meta_data, raw_user_meta_data,
    created_at, updated_at, is_sso_user, is_anonymous
  ) values (
    v_user,
    'authenticated',
    'authenticated',
    '{"provider":"stage33_post_revocation_synthetic_fixture","providers":[]}'::jsonb,
    '{"fixture":"stage33_post_revocation_edge_proof"}'::jsonb,
    now(), now(), false, false
  );

  insert into public.organizations (id, name, owner_user_id)
  values (v_org, 'Stage33 Post-Revocation Synthetic Organization', v_user);

  if (select count(*) from public.organization_subscriptions
       where organization_id = v_org and plan_code = 'trial' and status = 'trialing') <> 1 then
    raise exception using errcode = 'P0001',
      message = 'STAGE33_REVOCATION_FIXTURE_TRIAL_INITIALIZATION_FAILED';
  end if;

  insert into public.students (
    id, organization_id, name, objective, level, adherence, status
  ) values (
    v_student,
    v_org,
    'Stage33 Post-Revocation Synthetic Student',
    'Production Edge verification after direct RPC privilege retirement',
    'Iniciante',
    0,
    'Ativo'
  );

  insert into public.training_plans (
    id, organization_id, student_id, name, next_session, notes, is_active
  ) values (
    v_plan,
    v_org,
    v_student,
    'Stage33 Post-Revocation Synthetic Plan',
    'Synthetic post-revocation proof only',
    'Five-route production Edge verification after anon/auth direct RPC execute retirement.',
    true
  );

  insert into public.training_exercises (
    id, organization_id, training_plan_id, position, name, prescription
  ) values (
    v_exercise,
    v_org,
    v_plan,
    0,
    'Stage33 Post-Revocation Synthetic Exercise',
    '1 x 1 controlled post-revocation Edge proof'
  );

  insert into public.student_access_links (
    id, organization_id, student_id, token_hash, is_active,
    expires_at, created_by, rotation_number
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

  if (select count(*) from private.resolve_student_access(v_token) r
       where r.link_id = v_link and r.organization_id = v_org and r.student_id = v_student) <> 1 then
    raise exception using errcode = 'P0001',
      message = 'STAGE33_REVOCATION_FIXTURE_TOKEN_RESOLUTION_FAILED';
  end if;

  -- Exact privilege retirement. PUBLIC is explicitly denied as a default-execute sentinel.
  revoke execute on function public.get_student_feedback_context_v2(text)
    from public, anon, authenticated;
  revoke execute on function public.get_student_workout_v2(text)
    from public, anon, authenticated;
  revoke execute on function public.set_student_exercise_completion_v2(text,uuid,uuid,boolean,text)
    from public, anon, authenticated;
  revoke execute on function public.start_student_workout_v2(text,text)
    from public, anon, authenticated;
  revoke execute on function public.submit_student_workout_feedback_v2(text,uuid,integer,integer,integer,text,text,text)
    from public, anon, authenticated;

  -- Postcondition: external direct execution is gone; privileged Edge backend remains usable.
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
     and not has_function_privilege('public', p.oid, 'EXECUTE')
     and not has_function_privilege('anon', p.oid, 'EXECUTE')
     and not has_function_privilege('authenticated', p.oid, 'EXECUTE')
     and has_function_privilege('service_role', p.oid, 'EXECUTE');
  if v_count <> 5 then
    raise exception using errcode = 'P0001',
      message = 'STAGE33_REVOCATION_POSTCONDITION_ROLE_BOUNDARY_FAILED';
  end if;

  if not has_function_privilege(
    'authenticated',
    'public.issue_student_access_token_v2(uuid)',
    'EXECUTE'
  ) then
    raise exception using errcode = 'P0001',
      message = 'STAGE33_REVOCATION_POSTCONDITION_ISSUE_TOKEN_AUTHORITY_CHANGED';
  end if;

  if (select count(*) from auth.users where id = v_user) <> 1
     or (select count(*) from public.profiles where user_id = v_user) <> 1
     or (select count(*) from public.organizations where id = v_org and owner_user_id = v_user and name = 'Stage33 Post-Revocation Synthetic Organization') <> 1
     or (select count(*) from public.organization_members where organization_id = v_org and user_id = v_user and role = 'owner') <> 1
     or (select count(*) from public.organization_subscriptions where organization_id = v_org and plan_code = 'trial' and status = 'trialing') <> 1
     or (select count(*) from public.students where id = v_student and organization_id = v_org and name = 'Stage33 Post-Revocation Synthetic Student' and status = 'Ativo' and adherence = 0) <> 1
     or (select count(*) from public.training_plans where id = v_plan and student_id = v_student and organization_id = v_org and name = 'Stage33 Post-Revocation Synthetic Plan' and is_active) <> 1
     or (select count(*) from public.training_exercises where id = v_exercise and training_plan_id = v_plan and organization_id = v_org and name = 'Stage33 Post-Revocation Synthetic Exercise') <> 1
     or (select count(*) from public.student_access_links where id = v_link and student_id = v_student and organization_id = v_org and is_active and rotation_number = 1 and revoked_at is null) <> 1
     or (select count(*) from public.workout_sessions) <> 0
     or (select count(*) from public.workout_exercise_logs) <> 0
     or (select count(*) from public.workout_feedback) <> 0
     or (select count(*) from private.student_access_command_receipts) <> 0
     or (select count(*) from private.student_access_rate_buckets) <> 0
     or (select count(*) from private.student_access_security_events) <> 0
     or (select count(*) from private.student_access_security_signals) <> 0 then
    raise exception using errcode = 'P0001',
      message = 'STAGE33_REVOCATION_FIXTURE_POSTCONDITION_FAILED';
  end if;
end;
$$;
