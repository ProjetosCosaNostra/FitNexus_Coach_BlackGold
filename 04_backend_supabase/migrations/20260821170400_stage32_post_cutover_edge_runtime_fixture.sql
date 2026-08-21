-- Stage 32: controlled synthetic fixture for the production-selected Flutter -> Edge path.
--
-- Failure class:
--   BGF-STAGE32-POST-CUTOVER-RUNTIME-FIXTURE-231
--
-- Repository-first only. Apply only after CI + merge and only while the authoritative
-- customer domain is empty. The public synthetic bearer is derived from a deterministic
-- seed at apply/proof time and only SHA-256(token) is persisted. No real customer data,
-- credential, raw network origin, network-origin digest or bearer literal is embedded.
-- A dedicated fail-closed cleanup is mandatory after the one-shot Stage 32 proof.
do $$
declare
  v_user constant uuid := '728ea3d2-335f-5936-b78b-0289f9e732b8';
  v_org constant uuid := '51143353-1492-54a9-b5f8-1ad99cf4c6f3';
  v_student constant uuid := 'bdbe631a-4c44-53fc-a0da-38310bbdf90e';
  v_plan constant uuid := 'a1c29966-b4c1-59fc-bb9e-ac0b055ea577';
  v_exercise constant uuid := '585b0618-8141-513c-a37e-02cb5ccd93f1';
  v_link constant uuid := '378baa18-c8fc-5765-b01f-6fd3dd898f64';
  v_token constant text := encode(
    extensions.digest(
      convert_to('fitnexus-stage32-post-cutover-edge-runtime-proof-v1', 'UTF8'),
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
     or (select count(*) from public.workout_feedback) <> 0 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE32_POST_CUTOVER_FIXTURE_REQUIRES_EMPTY_CUSTOMER_DOMAIN';
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
    '{"provider":"stage32_synthetic_fixture","providers":[]}'::jsonb,
    '{"fixture":"stage32_post_cutover_edge_runtime_proof"}'::jsonb,
    now(),
    now(),
    false,
    false
  );

  insert into public.organizations (id, name, owner_user_id)
  values (v_org, 'Stage32 Synthetic Organization', v_user);

  select count(*)::integer into v_count
    from public.organization_subscriptions s
   where s.organization_id = v_org
     and s.plan_code = 'trial'
     and s.status = 'trialing';
  if v_count <> 1 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE32_SYNTHETIC_TRIAL_INITIALIZATION_FAILED';
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
    'Stage32 Synthetic Student',
    'Production-selected Flutter Edge post-cutover proof',
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
    'Stage32 Synthetic Plan',
    'Synthetic post-cutover proof only',
    'Controlled production-selected Flutter-to-Edge proof; no real student data.',
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
    'Stage32 Synthetic Exercise',
    '1 x 1 controlled post-cutover proof'
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
    now() + interval '2 hours',
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
      message = 'STAGE32_SYNTHETIC_TOKEN_RESOLUTION_FAILED';
  end if;

  if (select count(*) from auth.users where id = v_user) <> 1
     or (select count(*) from public.profiles where user_id = v_user) <> 1
     or (select count(*) from public.organizations where id = v_org and owner_user_id = v_user and name = 'Stage32 Synthetic Organization') <> 1
     or (select count(*) from public.organization_members where organization_id = v_org and user_id = v_user and role = 'owner') <> 1
     or (select count(*) from public.organization_subscriptions where organization_id = v_org and plan_code = 'trial' and status = 'trialing') <> 1
     or (select count(*) from public.students where id = v_student and organization_id = v_org and name = 'Stage32 Synthetic Student' and status = 'Ativo' and adherence = 0) <> 1
     or (select count(*) from public.training_plans where id = v_plan and student_id = v_student and organization_id = v_org and name = 'Stage32 Synthetic Plan' and is_active) <> 1
     or (select count(*) from public.training_exercises where id = v_exercise and training_plan_id = v_plan and organization_id = v_org and name = 'Stage32 Synthetic Exercise') <> 1
     or (select count(*) from public.student_access_links where id = v_link and student_id = v_student and organization_id = v_org and is_active and rotation_number = 1 and revoked_at is null) <> 1
     or (select count(*) from public.workout_sessions) <> 0
     or (select count(*) from public.workout_exercise_logs) <> 0
     or (select count(*) from public.workout_feedback) <> 0 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE32_POST_CUTOVER_FIXTURE_POSTCONDITION_FAILED';
  end if;
end;
$$;
