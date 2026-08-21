-- Stage 30: controlled synthetic fixture for full five-route Edge runtime smoke.
--
-- Failure class:
--   BGF-STAGE30-RUNTIME-SMOKE-FIXTURE-RESIDUE-203
--
-- This migration is repository-first and may be applied only while the authoritative
-- customer domain is empty. The synthetic possession token is derived from a public test
-- seed at migration/runtime and only SHA-256(token) is persisted. No real customer data,
-- credential, raw network origin or origin digest is embedded in repository source.
-- A dedicated fail-closed cleanup migration is mandatory after the live smoke receipt.

do $$
declare
  v_user constant uuid := '33e39af7-f470-510e-8a9c-fc70b16ba26e';
  v_org constant uuid := 'a0749405-6367-52d5-ad8b-5115b8d3a905';
  v_student constant uuid := '81d3be6f-824e-59bc-8fa0-27acf046d6d3';
  v_plan constant uuid := '82b92191-a8e3-5bb2-8f5d-fec9a59a57bb';
  v_exercise constant uuid := 'fe116050-9061-5627-8e3a-dedd863d6447';
  v_link constant uuid := '53dfab53-5ff8-573a-ab2a-faaea24107db';
  v_token constant text := encode(
    extensions.digest(
      convert_to('fitnexus-stage30-edge-runtime-smoke-fixture-v1', 'UTF8'),
      'sha256'
    ),
    'hex'
  );
  v_count integer;
begin
  if (select count(*) from auth.users) <> 0
     or (select count(*) from public.organizations) <> 0
     or (select count(*) from public.students) <> 0
     or (select count(*) from public.training_plans) <> 0
     or (select count(*) from public.training_exercises) <> 0
     or (select count(*) from public.student_access_links) <> 0
     or (select count(*) from public.workout_sessions) <> 0
     or (select count(*) from public.workout_exercise_logs) <> 0
     or (select count(*) from public.workout_feedback) <> 0 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE30_EDGE_RUNTIME_SMOKE_FIXTURE_REQUIRES_EMPTY_CUSTOMER_DOMAIN';
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
    '{"provider":"stage30_synthetic_fixture","providers":[]}'::jsonb,
    '{"fixture":"stage30_edge_runtime_smoke"}'::jsonb,
    now(),
    now(),
    false,
    false
  );

  insert into public.organizations (id, name, owner_user_id)
  values (v_org, 'Stage30 Synthetic Organization', v_user);

  select count(*)::integer into v_count
    from public.organization_subscriptions s
   where s.organization_id = v_org
     and s.plan_code = 'trial'
     and s.status = 'trialing';
  if v_count <> 1 then
    raise exception using errcode = 'P0001', message = 'STAGE30_SYNTHETIC_TRIAL_INITIALIZATION_FAILED';
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
    'Stage30 Synthetic Student',
    'Five-route Edge runtime smoke',
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
    'Stage30 Synthetic Plan',
    'Synthetic smoke only',
    'Controlled five-route Edge smoke; no real student data.',
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
    'Stage30 Synthetic Exercise',
    '1 x 1 controlled smoke'
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
    raise exception using errcode = 'P0001', message = 'STAGE30_SYNTHETIC_TOKEN_RESOLUTION_FAILED';
  end if;

  if (select count(*) from auth.users where id = v_user) <> 1
     or (select count(*) from public.profiles where user_id = v_user) <> 1
     or (select count(*) from public.organizations where id = v_org and owner_user_id = v_user) <> 1
     or (select count(*) from public.organization_members where organization_id = v_org and user_id = v_user and role = 'owner') <> 1
     or (select count(*) from public.organization_subscriptions where organization_id = v_org and plan_code = 'trial' and status = 'trialing') <> 1
     or (select count(*) from public.students where id = v_student and organization_id = v_org and status = 'Ativo') <> 1
     or (select count(*) from public.training_plans where id = v_plan and student_id = v_student and organization_id = v_org and is_active) <> 1
     or (select count(*) from public.training_exercises where id = v_exercise and training_plan_id = v_plan and organization_id = v_org) <> 1
     or (select count(*) from public.student_access_links where id = v_link and student_id = v_student and organization_id = v_org and is_active) <> 1
     or (select count(*) from public.workout_sessions) <> 0
     or (select count(*) from public.workout_exercise_logs) <> 0
     or (select count(*) from public.workout_feedback) <> 0 then
    raise exception using errcode = 'P0001', message = 'STAGE30_SYNTHETIC_FIXTURE_POSTCONDITION_FAILED';
  end if;
end;
$$;
