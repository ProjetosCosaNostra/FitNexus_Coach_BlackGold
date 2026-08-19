create or replace function private.growth_on_profile_completed()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_org_id uuid;
  v_became_complete boolean;
begin
  if tg_op = 'INSERT' then
    v_became_complete := nullif(btrim(coalesce(new.display_name, '')), '') is not null;
  else
    v_became_complete := nullif(btrim(coalesce(new.display_name, '')), '') is not null
      and nullif(btrim(coalesce(old.display_name, '')), '') is null;
  end if;

  if not v_became_complete then
    return new;
  end if;

  select m.organization_id
  into v_org_id
  from public.organization_members m
  where m.user_id = new.user_id
  order by m.created_at
  limit 1;

  perform private.append_growth_event(
    'coach_profile_completed',
    v_org_id,
    new.user_id,
    'server_trigger',
    'public.profiles',
    new.user_id,
    coalesce(new.updated_at, now())
  );

  return new;
end;
$$;

revoke execute on function private.growth_on_profile_completed()
from public, anon, authenticated, service_role;
