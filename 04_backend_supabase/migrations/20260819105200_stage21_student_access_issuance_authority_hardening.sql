-- Stage 21 hardening: authorize the professor before inspecting rotation state.
-- This prevents an unauthorized authenticated caller from learning whether a
-- guessed student id has a freshly-issued link via the rotation cooldown path.

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

  select s.organization_id into v_org
    from public.students s
   where s.id = p_student_id;

  if v_org is null then
    raise exception using errcode = 'P0002', message = 'STUDENT_NOT_FOUND';
  end if;

  if not private.is_org_manager(v_org) then
    raise exception using errcode = '42501', message = 'ORG_MANAGER_REQUIRED';
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

  -- Reuse the mature v1 issuance business mutation only after v2 has already
  -- independently established caller authority. v1 performs the same check again.
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
  'Manager-authorized rotation boundary. Authorization is checked before rotation-state lookup; raw token is returned once, hashed at rest and expires after 30 days.';
