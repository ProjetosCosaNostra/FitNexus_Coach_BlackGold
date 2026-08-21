-- Stage 31: controlled synthetic fixture for Flutter client -> Edge runtime proof.
--
-- Failure class:
--   BGF-STAGE31-CLIENT-EDGE-RUNTIME-FIXTURE-216
--
-- Repository-first only. This migration may be applied only while the authoritative
-- customer domain is empty. The possession token is derived from a public synthetic
-- seed at migration/runtime and only SHA-256(token) is persisted. No real customer
-- data, credential, raw network origin or network-origin digest is embedded here.
-- A dedicated fail-closed cleanup is mandatory after the Stage 31 client proof.

do $$
declare
  v_user constant uuid := 'e06ec62d-e9b7-54a8-8fb9-d47828499939';
  v_org constant uuid := 'cd4688ec-cc08-5c2d-ad8c-0149242d809e';
  v_student constant uuid := 'bbdf3d96-0569-51d4-aadc-251ed0abc24e';
  v_plan constant uuid := 'b54064b9-f6a8-539e-b4a2-976d99141844';
  v_exercise constant uuid := '51871b03-c901-5a8f-b659-40f63e1f22e4';
  v_link constant uuid := '4ad0ced0-fc32-50cb-8287-fb4f971942a5';
  v_token constant text := encode(
    extensions.digest(
      convert_to('fitnexus-stage31-client-edge-runtime-proof-v1', 'UTF8'),
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
      message = 'STAGE31_CLIENT_EDGE_RUNTIME_FIXTURE_REQUIRES_EMPTY_CUSTOMER_DOMAIN';
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
    '{"provider":"stage31_synthetic_fixture","providers":[]}'::jsonb,
    '{"fixture":"stage31_client_edge_runtime_proof"}'::jsonb,
    now(),
    now(),
    false,
    false
  );

  insert into public.organizations (id, name, owner_user_id)
  values (v_org, 'Stage31 Synthetic Organization', v_user);

  select count(*)::integer into v_count
    from public.organization_subscriptions s
   where s.organization_id = v_org
     and s.plan_code = 'trial'
     and s.status = 'trialing';
  if v_count <> 1 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE31_SYNTHETIC_TRIAL_INITIALIZATION_FAILED';
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
    'Stage31 Synthetic Student',
    'Flutter client Edge runtime proof',
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
    'Stage31 Synthetic Plan',
    'Synthetic client proof only',
    'Controlled Flutter-to-Edge proof; no real student data.',
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
    'Stage31 Synthetic Exercise',
    '1 x 1 controlled client proof'
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
      message = 'STAGE31_SYNTHETIC_TOKEN_RESOLUTION_FAILED';
  end if;

  if (select count(*) from auth.users where id = v_user) <> 1
     or (select count(*) from public.profiles where user_id = v_user) <> 1
     or (select count(*) from public.organizations where id = v_org and owner_user_id = v_user and name = 'Stage31 Synthetic Organization') <> 1
     or (select count(*) from public.organization_members where organization_id = v_org and user_id = v_user and role = 'owner') <> 1
     or (select count(*) from public.organization_subscriptions where organization_id = v_org and plan_code = 'trial' and status = 'trialing') <> 1
     or (select count(*) from public.subscription_authority_events where organization_id = v_org and event_type = 'trial_initialized') <> 1
     or (select count(*) from public.students where id = v_student and organization_id = v_org and name = 'Stage31 Synthetic Student' and status = 'Ativo' and adherence = 0) <> 1
     or (select count(*) from public.training_plans where id = v_plan and student_id = v_student and organization_id = v_org and is_active) <> 1
     or (select count(*) from public.training_exercises where id = v_exercise and training_plan_id = v_plan and organization_id = v_org) <> 1
     or (select count(*) from public.student_access_links where id = v_link and student_id = v_student and organization_id = v_org and is_active) <> 1
     or (select count(*) from public.workout_sessions) <> 0
     or (select count(*) from public.workout_exercise_logs) <> 0
     or (select count(*) from public.workout_feedback) <> 0 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE31_CLIENT_EDGE_RUNTIME_FIXTURE_POSTCONDITION_FAILED';
  end if;
end;
$$;
