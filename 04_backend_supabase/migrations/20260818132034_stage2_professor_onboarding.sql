create unique index if not exists organizations_one_owner_idx
  on public.organizations(owner_user_id);

create or replace function public.ensure_my_organization(p_name text)
returns uuid
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_uid uuid := auth.uid();
  v_name text := btrim(coalesce(p_name, ''));
  v_org uuid;
begin
  if v_uid is null then
    raise exception using errcode = '42501', message = 'AUTH_REQUIRED';
  end if;

  if char_length(v_name) < 2 or char_length(v_name) > 120 then
    raise exception using errcode = '22023', message = 'ORGANIZATION_NAME_INVALID';
  end if;

  select o.id
    into v_org
  from public.organizations o
  where o.owner_user_id = v_uid
  limit 1;

  if v_org is not null then
    return v_org;
  end if;

  begin
    insert into public.organizations(name, owner_user_id)
    values (v_name, v_uid)
    returning id into v_org;
  exception
    when unique_violation then
      select o.id
        into v_org
      from public.organizations o
      where o.owner_user_id = v_uid
      limit 1;
  end;

  if v_org is null then
    raise exception using errcode = 'P0001', message = 'ORGANIZATION_ENSURE_FAILED';
  end if;

  return v_org;
end;
$$;

revoke execute on function public.ensure_my_organization(text) from public, anon;
grant execute on function public.ensure_my_organization(text) to authenticated;
