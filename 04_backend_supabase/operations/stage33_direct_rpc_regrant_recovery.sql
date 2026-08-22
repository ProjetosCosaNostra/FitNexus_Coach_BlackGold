-- Stage 33 emergency recovery artifact. DO NOT execute proactively.
--
-- Purpose: restore only the five retired student-route v2 EXECUTE grants to anon and
-- authenticated if the sealed post-revocation Edge runtime proof fails after the exact
-- Stage33 revocation migration is applied. This is a controlled recovery path, not an
-- automatic fallback and not a migration. Production transport constants remain Edge.
--
-- Failure classes:
--   BGF-STAGE33-PRIVILEGE-REVOCATION-PREMATURE-245
--   BGF-STAGE33-REVOCATION-SERVICE-ROLE-LOSS-251
--   BGF-STAGE33-REGRANT-RECOVERY-SCOPE-252
--
-- Preconditions deliberately fail closed: the exact five targets must be externally
-- revoked, service_role must still execute all five, and professor token issuance must
-- remain authenticated. If those facts are not true, this artifact refuses mutation.
do $$
declare
  v_count integer;
begin
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
      message = 'STAGE33_REGRANT_RECOVERY_PRECONDITION_TARGET_STATE_MISMATCH';
  end if;

  if not has_function_privilege(
    'authenticated',
    'public.issue_student_access_token_v2(uuid)',
    'EXECUTE'
  ) then
    raise exception using errcode = 'P0001',
      message = 'STAGE33_REGRANT_RECOVERY_ISSUE_TOKEN_AUTHORITY_DRIFT';
  end if;

  grant execute on function public.get_student_feedback_context_v2(text)
    to anon, authenticated;
  grant execute on function public.get_student_workout_v2(text)
    to anon, authenticated;
  grant execute on function public.set_student_exercise_completion_v2(text,uuid,uuid,boolean,text)
    to anon, authenticated;
  grant execute on function public.start_student_workout_v2(text,text)
    to anon, authenticated;
  grant execute on function public.submit_student_workout_feedback_v2(text,uuid,integer,integer,integer,text,text,text)
    to anon, authenticated;

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
     and has_function_privilege('anon', p.oid, 'EXECUTE')
     and has_function_privilege('authenticated', p.oid, 'EXECUTE')
     and has_function_privilege('service_role', p.oid, 'EXECUTE');
  if v_count <> 5 then
    raise exception using errcode = 'P0001',
      message = 'STAGE33_REGRANT_RECOVERY_POSTCONDITION_FAILED';
  end if;

  if not has_function_privilege(
    'authenticated',
    'public.issue_student_access_token_v2(uuid)',
    'EXECUTE'
  ) then
    raise exception using errcode = 'P0001',
      message = 'STAGE33_REGRANT_RECOVERY_POSTCONDITION_ISSUE_TOKEN_CHANGED';
  end if;
end;
$$;
