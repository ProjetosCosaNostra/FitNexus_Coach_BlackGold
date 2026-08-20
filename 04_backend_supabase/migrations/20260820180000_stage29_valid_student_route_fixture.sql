-- Stage 29: controlled synthetic fixture for live valid-token Edge routing proof.
--
-- Failure classes:
--   BGF-VALID-STUDENT-ROUTE-UNPROVEN-187
--   BGF-SYNTHETIC-VALID-ROUTE-FIXTURE-RESIDUE-188
--   BGF-VALID-ROUTE-RESPONSE-DATA-LEAK-189
--   BGF-MIGRATION-APPLY-SYNTHETIC-LITERAL-SCREENING-191
--
-- This fixture is permitted only while the authoritative project has no real auth users,
-- organizations, students, training plans, or student access links. The bearer is derived
-- deterministically from a public synthetic fixture seed inside the migration, so no
-- bearer-looking 64-hex literal is stored in repository source. It can resolve only this
-- isolated fixture, is never a credential for a real user, and the database persists only
-- SHA-256(token). A dedicated cleanup migration is mandatory immediately after live proof.

do $$
declare
  v_user constant uuid := '2615749d-ffca-5319-84e0-b775578ceaf6';
  v_org constant uuid := '13678787-eeae-5f6a-8828-190723a22594';
  v_student constant uuid := '659eafee-0508-5dfb-9fcb-d285d9e846db';
  v_plan constant uuid := 'fd5762db-0a0c-54dc-81c9-2aeade199ee5';
  v_exercise constant uuid := '2ec1260b-88f2-5a2c-ba81-3433d2c147d5';
  v_link constant uuid := 'f31a3c36-4ee1-5d64-b30d-f00fc98aea9b';
  v_token constant text := encode(
    extensions.digest(convert_to('fitnexus-stage29-valid-route-fixture-v1', 'UTF8'), 'sha256'),
    'hex'
  );
  v_count integer;
begin
  if (select count(*) from auth.users) <> 0
     or (select count(*) from public.organizations) <> 0
     or (select count(*) from public.students) <> 0
     or (select count(*) from public.training_plans) <> 0
     or (select count(*) from public.student_access_links) <> 0 then
    raise exception using
      errcode = 'P0001',
      message = 'STAGE29_VALID_ROUTE_FIXTURE_REQUIRES_EMPTY_CUSTOMER_DOMAIN';
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
    '{"provider":"stage29_synthetic_fixture","providers":[]}'::jsonb,
    '{"fixture":"stage29_valid_student_route"}'::jsonb,
    now(),
    now(),
    false,
    false
  );

  insert into public.organizations (id, name, owner_user_id)
  values (v_org, 'Stage29 Synthetic Organization', v_user);

  select count(*)::integer into v_count
  from public.organization_subscriptions s
  where s.organization_id = v_org
    and s.plan_code = 'trial'
    and s.status = 'trialing';
  if v_count <> 1 then
    raise exception using errcode = 'P0001', message = 'STAGE29_SYNTHETIC_TRIAL_INITIALIZATION_FAILED';
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
    'Stage29 Synthetic Student',
    'Valid Edge Route Proof',
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
    'Stage29 Synthetic Plan',
    'Synthetic proof only',
    'Controlled live GET proof; no real student data.',
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
    'Stage29 Synthetic Exercise',
    '1 x 1 controlled proof'
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
    raise exception using errcode = 'P0001', message = 'STAGE29_SYNTHETIC_TOKEN_RESOLUTION_FAILED';
  end if;

  if (select count(*) from public.profiles where user_id = v_user) <> 1
     or (select count(*) from public.organization_members where organization_id = v_org and user_id = v_user and role = 'owner') <> 1
     or (select count(*) from public.students where id = v_student and organization_id = v_org) <> 1
     or (select count(*) from public.training_plans where id = v_plan and student_id = v_student and organization_id = v_org and is_active) <> 1
     or (select count(*) from public.training_exercises where id = v_exercise and training_plan_id = v_plan and organization_id = v_org) <> 1
     or (select count(*) from public.student_access_links where id = v_link and student_id = v_student and organization_id = v_org and is_active) <> 1 then
    raise exception using errcode = 'P0001', message = 'STAGE29_SYNTHETIC_FIXTURE_POSTCONDITION_FAILED';
  end if;
end;
$$;
