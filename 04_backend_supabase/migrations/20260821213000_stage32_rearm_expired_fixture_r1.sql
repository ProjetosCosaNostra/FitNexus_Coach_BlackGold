-- Stage 32 recovery R2: rearm only the exact expired synthetic fixture after the
-- first sealed proof attempt failed before any network call.
--
-- Failure classes:
--   BGF-STAGE32-FLUTTER-TEST-SHARED-PREFERENCES-PLUGIN-235
--   BGF-STAGE32-SYNTHETIC-FIXTURE-TTL-EXPIRED-BEFORE-RETRY-236
--   BGF-SUPABASE-EXECUTE-SQL-READONLY-DML-237
--
-- Supabase.execute_sql is read-only in the authoritative production connector for
-- this project. This repository-first migration is therefore the only authorized
-- remote mutation mechanism for the rearm. It is synthetic-only, fail-closed, and
-- may only extend the expiry of the already-existing exact Stage 32 access link.
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
  v_updated integer;
begin
  if (select count(*) from auth.users) <> 1
     or (select count(*) from public.profiles) <> 1
     or (select count(*) from public.organizations) <> 1
     or (select count(*) from public.organization_members) <> 1
     or (select count(*) from public.organization_subscriptions) <> 1
     or (select count(*) from public.students) <> 1
     or (select count(*) from public.training_plans) <> 1
     or (select count(*) from public.training_exercises) <> 1
     or (select count(*) from public.student_access_links) <> 1
     or (select count(*) from public.workout_sessions) <> 0
     or (select count(*) from public.workout_exercise_logs) <> 0
     or (select count(*) from public.workout_feedback) <> 0 then
    raise exception using errcode = 'P0001', message = 'STAGE32_R1_REARM_CUSTOMER_DOMAIN_NOT_EXACT_SYNTHETIC_FIXTURE';
  end if;

  if (select count(*) from auth.users where id = v_user) <> 1
     or (select count(*) from public.profiles where user_id = v_user) <> 1
     or (select count(*) from public.organizations where id = v_org and owner_user_id = v_user and name = 'Stage32 Synthetic Organization') <> 1
     or (select count(*) from public.organization_members where organization_id = v_org and user_id = v_user and role = 'owner') <> 1
     or (select count(*) from public.organization_subscriptions where organization_id = v_org and plan_code = 'trial' and status = 'trialing') <> 1
     or (select count(*) from public.students where id = v_student and organization_id = v_org and name = 'Stage32 Synthetic Student' and status = 'Ativo' and adherence = 0) <> 1
     or (select count(*) from public.training_plans where id = v_plan and student_id = v_student and organization_id = v_org and name = 'Stage32 Synthetic Plan' and is_active) <> 1
     or (select count(*) from public.training_exercises where id = v_exercise and training_plan_id = v_plan and organization_id = v_org and name = 'Stage32 Synthetic Exercise') <> 1
     or (select count(*) from public.student_access_links
          where id = v_link
            and student_id = v_student
            and organization_id = v_org
            and token_hash = extensions.digest(v_token, 'sha256')
            and is_active
            and rotation_number = 1
            and revoked_at is null
            and expires_at <= now()) <> 1 then
    raise exception using errcode = 'P0001', message = 'STAGE32_R1_REARM_FIXTURE_IDENTITY_OR_EXPIRY_MISMATCH';
  end if;

  if (select count(*) from private.student_access_command_receipts where link_id = v_link) <> 0
     or (select count(*) from private.student_access_rate_buckets where link_id = v_link) <> 0
     or (select count(*) from private.student_access_security_events where link_id = v_link or organization_id = v_org or student_id = v_student) <> 0
     or (select count(*) from private.student_access_security_signals where link_id = v_link or organization_id = v_org or student_id = v_student) <> 0 then
    raise exception using errcode = 'P0001', message = 'STAGE32_R1_REARM_RUNTIME_RESIDUE_DETECTED';
  end if;

  if (select count(*) from private.growth_events where organization_id = v_org) <> 4
     or (select count(*) from private.growth_events where organization_id = v_org and event_name = 'trial_started') <> 1
     or (select count(*) from private.growth_events where organization_id = v_org and event_name = 'student_created') <> 1
     or (select count(*) from private.growth_events where organization_id = v_org and event_name = 'training_created_or_duplicated') <> 1
     or (select count(*) from private.growth_events where organization_id = v_org and event_name = 'training_delivered') <> 1
     or (select count(*) from private.growth_attribution where organization_id = v_org) <> 0 then
    raise exception using errcode = 'P0001', message = 'STAGE32_R1_REARM_GROWTH_FIXTURE_DRIFT';
  end if;

  update public.student_access_links
     set expires_at = now() + interval '6 hours'
   where id = v_link
     and is_active
     and revoked_at is null
     and expires_at <= now();
  get diagnostics v_updated = row_count;
  if v_updated <> 1 then
    raise exception using errcode = 'P0001', message = 'STAGE32_R1_REARM_UPDATE_COUNT_MISMATCH';
  end if;

  if (select count(*) from public.student_access_links
       where id = v_link
         and is_active
         and revoked_at is null
         and expires_at > now() + interval '5 hours 55 minutes') <> 1
     or (select count(*) from public.workout_sessions) <> 0
     or (select count(*) from public.workout_exercise_logs) <> 0
     or (select count(*) from public.workout_feedback) <> 0
     or (select count(*) from private.student_access_command_receipts where link_id = v_link) <> 0
     or (select count(*) from private.student_access_rate_buckets where link_id = v_link) <> 0
     or (select count(*) from private.student_access_security_events where link_id = v_link or organization_id = v_org or student_id = v_student) <> 0
     or (select count(*) from private.student_access_security_signals where link_id = v_link or organization_id = v_org or student_id = v_student) <> 0 then
    raise exception using errcode = 'P0001', message = 'STAGE32_R1_REARM_POSTCONDITION_FAILED';
  end if;
end;
$$;
