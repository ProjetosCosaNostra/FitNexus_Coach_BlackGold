-- STAGE52 OPERATIONS CANDIDATE ONLY — DO NOT APPLY DIRECTLY
-- Purpose: remove the authenticated student-id existence oracle from
-- public.issue_student_access_token_v2(uuid) without changing the intentional
-- authenticated manager boundary established by Stage21/Stage51.
--
-- Current remote behavior distinguishes:
--   nonexistent student -> STUDENT_NOT_FOUND
--   existing student in another organization -> ORG_MANAGER_REQUIRED
-- A signed-in non-manager can therefore learn whether a guessed UUID exists.
--
-- This candidate resolves student + caller-manager authority in one query and
-- emits one indistinguishable error when no authorized target is visible.
-- It is not a migration and is not remote-apply authority.

create or replace function public.issue_student_access_token_v2(p_student_id uuid)
returns text
language plpgsql
volatile
security definer
set search_path = ''
as $$
declare
  v_org uuid;
  v_previous_id uuid;
  v_previous_rotation integer := 0;
  v_token text;
  v_new_id uuid;
begin
  if auth.uid() is null then
    raise exception using errcode = '42501', message = 'AUTH_REQUIRED';
  end if;

  -- Authorization and target lookup are deliberately coalesced. A caller that
  -- does not manage the target organization receives the same response as a
  -- caller presenting a nonexistent student id, preventing cross-tenant
  -- student-existence enumeration through RPC error differences.
  select s.organization_id
    into v_org
    from public.students s
    join public.organization_members m
      on m.organization_id = s.organization_id
     and m.user_id = (select auth.uid())
     and m.role in ('owner', 'admin')
   where s.id = p_student_id
   limit 1;

  if v_org is null then
    raise exception using
      errcode = '42501',
      message = 'STUDENT_ACCESS_TARGET_UNAVAILABLE';
  end if;

  select l.id, l.rotation_number
    into v_previous_id, v_previous_rotation
    from public.student_access_links l
   where l.student_id = p_student_id
     and l.organization_id = v_org
     and l.is_active
   order by l.created_at desc
   limit 1;

  if v_previous_id is not null and exists (
    select 1
      from public.student_access_links l
     where l.id = v_previous_id
       and l.created_at > now() - interval '30 seconds'
  ) then
    raise exception using errcode = 'P0001', message = 'STUDENT_ACCESS_ROTATION_COOLDOWN';
  end if;

  -- Reuse the mature v1 issuance mutation only after the v2 wrapper has proven
  -- that the signed-in caller manages the student's organization. v1 repeats
  -- the manager check defensively and is not directly executable by anon or
  -- authenticated roles.
  v_token := public.issue_student_access_token(p_student_id);

  select l.id into v_new_id
    from public.student_access_links l
   where l.token_hash = extensions.digest(v_token, 'sha256')
     and l.student_id = p_student_id
     and l.organization_id = v_org
   limit 1;

  if v_new_id is null then
    raise exception using errcode = 'P0001', message = 'STUDENT_ACCESS_ROTATION_RESULT_MISSING';
  end if;

  update public.student_access_links
     set expires_at = now() + interval '30 days',
         rotated_from_link_id = v_previous_id,
         rotation_number = greatest(1, coalesce(v_previous_rotation, 0) + 1)
   where id = v_new_id
     and organization_id = v_org;

  if v_previous_id is not null then
    update public.student_access_links
       set revoked_at = coalesce(revoked_at, now()),
           revocation_reason = coalesce(revocation_reason, 'rotated')
     where id = v_previous_id
       and organization_id = v_org;
  end if;

  insert into private.student_access_security_events (
    link_id, organization_id, student_id, operation, outcome
  )
  select l.id, l.organization_id, l.student_id, 'issue_token', 'rotated'
    from public.student_access_links l
   where l.id = v_new_id;

  return v_token;
end;
$$;

revoke all on function public.issue_student_access_token_v2(uuid) from public, anon;
grant execute on function public.issue_student_access_token_v2(uuid) to authenticated;

comment on function public.issue_student_access_token_v2(uuid) is
  'Manager-authorized student access rotation boundary. Student target lookup and manager authorization are coalesced so unauthorized and nonexistent targets are externally indistinguishable; raw token is returned once, hashed at rest and expires after 30 days.';
