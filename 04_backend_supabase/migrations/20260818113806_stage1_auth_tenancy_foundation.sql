create extension if not exists pgcrypto with schema extensions;

create schema if not exists private;
revoke all on schema private from public;
revoke all on schema private from anon;
grant usage on schema private to authenticated;

create table if not exists public.profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  display_name text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.organizations (
  id uuid primary key default extensions.gen_random_uuid(),
  name text not null check (char_length(btrim(name)) between 2 and 120),
  owner_user_id uuid not null references auth.users(id) on delete restrict,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.organization_members (
  organization_id uuid not null references public.organizations(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null default 'member' check (role in ('owner','admin','member')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (organization_id, user_id)
);

create index if not exists organizations_owner_user_id_idx
  on public.organizations(owner_user_id);

create index if not exists organization_members_user_id_idx
  on public.organization_members(user_id);

alter table public.profiles enable row level security;
alter table public.organizations enable row level security;
alter table public.organization_members enable row level security;

create or replace function private.set_updated_at()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create or replace function private.is_org_member(target_org uuid)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select 1
    from public.organization_members m
    where m.organization_id = target_org
      and m.user_id = (select auth.uid())
  );
$$;

create or replace function private.is_org_owner(target_org uuid)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select 1
    from public.organizations o
    where o.id = target_org
      and o.owner_user_id = (select auth.uid())
  );
$$;

create or replace function private.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  insert into public.profiles (user_id, display_name)
  values (
    new.id,
    coalesce(new.raw_user_meta_data ->> 'full_name', new.raw_user_meta_data ->> 'name')
  )
  on conflict (user_id) do nothing;
  return new;
end;
$$;

create or replace function private.handle_new_organization()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  insert into public.organization_members (organization_id, user_id, role)
  values (new.id, new.owner_user_id, 'owner')
  on conflict (organization_id, user_id)
  do update set role = 'owner', updated_at = now();
  return new;
end;
$$;

revoke all on function private.is_org_member(uuid) from public, anon;
revoke all on function private.is_org_owner(uuid) from public, anon;
grant execute on function private.is_org_member(uuid) to authenticated;
grant execute on function private.is_org_owner(uuid) to authenticated;

revoke all on function private.handle_new_user() from public, anon, authenticated;
revoke all on function private.handle_new_organization() from public, anon, authenticated;
revoke all on function private.set_updated_at() from public, anon, authenticated;

drop trigger if exists profiles_set_updated_at on public.profiles;
create trigger profiles_set_updated_at
before update on public.profiles
for each row execute function private.set_updated_at();

drop trigger if exists organizations_set_updated_at on public.organizations;
create trigger organizations_set_updated_at
before update on public.organizations
for each row execute function private.set_updated_at();

drop trigger if exists organization_members_set_updated_at on public.organization_members;
create trigger organization_members_set_updated_at
before update on public.organization_members
for each row execute function private.set_updated_at();

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
after insert on auth.users
for each row execute function private.handle_new_user();

drop trigger if exists on_organization_created on public.organizations;
create trigger on_organization_created
after insert on public.organizations
for each row execute function private.handle_new_organization();

revoke all on public.profiles from anon;
revoke all on public.organizations from anon;
revoke all on public.organization_members from anon;

revoke all on public.profiles from authenticated;
revoke all on public.organizations from authenticated;
revoke all on public.organization_members from authenticated;

grant select, update on public.profiles to authenticated;
grant select, insert, update, delete on public.organizations to authenticated;
grant select, insert, update, delete on public.organization_members to authenticated;

drop policy if exists profiles_select_self on public.profiles;
create policy profiles_select_self
on public.profiles
for select
to authenticated
using (user_id = (select auth.uid()));

drop policy if exists profiles_update_self on public.profiles;
create policy profiles_update_self
on public.profiles
for update
to authenticated
using (user_id = (select auth.uid()))
with check (user_id = (select auth.uid()));

drop policy if exists organizations_select on public.organizations;
create policy organizations_select
on public.organizations
for select
to authenticated
using (
  owner_user_id = (select auth.uid())
  or (select private.is_org_member(id))
);

drop policy if exists organizations_insert on public.organizations;
create policy organizations_insert
on public.organizations
for insert
to authenticated
with check (owner_user_id = (select auth.uid()));

drop policy if exists organizations_update_owner on public.organizations;
create policy organizations_update_owner
on public.organizations
for update
to authenticated
using (owner_user_id = (select auth.uid()))
with check (owner_user_id = (select auth.uid()));

drop policy if exists organizations_delete_owner on public.organizations;
create policy organizations_delete_owner
on public.organizations
for delete
to authenticated
using (owner_user_id = (select auth.uid()));

drop policy if exists organization_members_select on public.organization_members;
create policy organization_members_select
on public.organization_members
for select
to authenticated
using (
  user_id = (select auth.uid())
  or (select private.is_org_owner(organization_id))
);

drop policy if exists organization_members_insert_owner on public.organization_members;
create policy organization_members_insert_owner
on public.organization_members
for insert
to authenticated
with check ((select private.is_org_owner(organization_id)));

drop policy if exists organization_members_update_owner on public.organization_members;
create policy organization_members_update_owner
on public.organization_members
for update
to authenticated
using ((select private.is_org_owner(organization_id)))
with check ((select private.is_org_owner(organization_id)));

drop policy if exists organization_members_delete_owner on public.organization_members;
create policy organization_members_delete_owner
on public.organization_members
for delete
to authenticated
using ((select private.is_org_owner(organization_id)));
