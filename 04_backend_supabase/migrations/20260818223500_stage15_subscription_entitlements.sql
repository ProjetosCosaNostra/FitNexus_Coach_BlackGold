create table if not exists public.subscription_plans (
  code text primary key check (code ~ '^[a-z0-9_]{2,40}$'),
  display_name text not null check (char_length(btrim(display_name)) between 2 and 80),
  lifecycle text not null default 'active' check (lifecycle in ('active','retired')),
  student_limit integer not null check (student_limit between 1 and 100000),
  member_limit integer not null check (member_limit between 1 and 1000),
  trial_days integer not null default 0 check (trial_days between 0 and 90),
  feature_flags jsonb not null default '{}'::jsonb check (jsonb_typeof(feature_flags) = 'object'),
  sort_order integer not null default 100,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

insert into public.subscription_plans (
  code,
  display_name,
  lifecycle,
  student_limit,
  member_limit,
  trial_days,
  feature_flags,
  sort_order
)
values
  (
    'trial',
    'BlackGold Trial',
    'active',
    10,
    1,
    14,
    jsonb_build_object(
      'coach_action_center', true,
      'decision_intelligence', true,
      'smart_templates', true,
      'training_lineage', true,
      'student_feedback', true
    ),
    10
  ),
  (
    'solo',
    'Coach Solo',
    'active',
    30,
    1,
    0,
    jsonb_build_object(
      'coach_action_center', true,
      'decision_intelligence', true,
      'smart_templates', true,
      'training_lineage', true,
      'student_feedback', true
    ),
    20
  ),
  (
    'pro',
    'Coach Pro',
    'active',
    100,
    3,
    0,
    jsonb_build_object(
      'coach_action_center', true,
      'decision_intelligence', true,
      'smart_templates', true,
      'training_lineage', true,
      'student_feedback', true
    ),
    30
  ),
  (
    'studio',
    'Studio',
    'active',
    300,
    10,
    0,
    jsonb_build_object(
      'coach_action_center', true,
      'decision_intelligence', true,
      'smart_templates', true,
      'training_lineage', true,
      'student_feedback', true
    ),
    40
  )
on conflict (code) do nothing;

create table if not exists public.organization_subscriptions (
  organization_id uuid primary key references public.organizations(id) on delete cascade,
  plan_code text not null references public.subscription_plans(code) on update restrict on delete restrict,
  status text not null check (status in ('trialing','active','grace','past_due','canceled','expired')),
  trial_started_at timestamptz,
  trial_ends_at timestamptz,
  current_period_start timestamptz,
  current_period_end timestamptz,
  cancel_at_period_end boolean not null default false,
  provider text,
  provider_customer_ref text,
  provider_subscription_ref text,
  authority_source text not null default 'system_trial' check (authority_source in ('system_trial','provider_webhook','admin_recovery')),
  authority_version bigint not null default 1 check (authority_version > 0),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (
    (status <> 'trialing')
    or (
      trial_started_at is not null
      and trial_ends_at is not null
      and trial_ends_at > trial_started_at
    )
  ),
  check (
    current_period_end is null
    or current_period_start is null
    or current_period_end > current_period_start
  )
);

create unique index if not exists organization_subscriptions_provider_subscription_uidx
  on public.organization_subscriptions(provider, provider_subscription_ref)
  where provider is not null and provider_subscription_ref is not null;

create table if not exists public.subscription_authority_events (
  id uuid primary key default extensions.gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  event_type text not null check (char_length(btrim(event_type)) between 2 and 80),
  from_plan_code text references public.subscription_plans(code) on update restrict on delete restrict,
  to_plan_code text not null references public.subscription_plans(code) on update restrict on delete restrict,
  from_status text,
  to_status text not null check (to_status in ('trialing','active','grace','past_due','canceled','expired')),
  authority_source text not null check (authority_source in ('system_trial','provider_webhook','admin_recovery')),
  external_event_ref text,
  payload_sha256 text check (payload_sha256 is null or payload_sha256 ~ '^[0-9a-f]{64}$'),
  effective_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);

create unique index if not exists subscription_authority_events_external_uidx
  on public.subscription_authority_events(authority_source, external_event_ref)
  where external_event_ref is not null;

create index if not exists subscription_authority_events_org_created_idx
  on public.subscription_authority_events(organization_id, created_at desc);

alter table public.subscription_plans enable row level security;
alter table public.organization_subscriptions enable row level security;
alter table public.subscription_authority_events enable row level security;

create or replace function private.is_org_billing_manager(target_org uuid)
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
      and m.role in ('owner','admin')
  );
$$;

create or replace function private.subscription_effective_status(target_org uuid)
returns text
language sql
stable
security definer
set search_path = ''
as $$
  select case
    when s.organization_id is null then 'uninitialized'
    when s.status = 'trialing' and (
      s.trial_started_at is null
      or s.trial_ends_at is null
      or s.trial_started_at > now()
      or s.trial_ends_at <= now()
    ) then 'expired'
    when s.status in ('active','grace')
      and s.current_period_end is not null
      and s.current_period_end <= now()
    then 'expired'
    else s.status
  end
  from (select target_org as organization_id) target
  left join public.organization_subscriptions s
    on s.organization_id = target.organization_id;
$$;

create or replace function private.subscription_write_enabled(target_org uuid)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select coalesce(
    private.subscription_effective_status(target_org) in ('trialing','active','grace'),
    false
  );
$$;

create or replace function private.subscription_usage_snapshot(target_org uuid)
returns jsonb
language plpgsql
stable
security definer
set search_path = ''
as $$
declare
  v_students integer;
  v_members integer;
begin
  if auth.uid() is not null and not private.is_org_member(target_org) then
    raise exception using errcode = '42501', message = 'ORG_MEMBER_REQUIRED';
  end if;

  select count(*)::int
  into v_students
  from public.students s
  where s.organization_id = target_org;

  select count(*)::int
  into v_members
  from public.organization_members m
  where m.organization_id = target_org;

  return jsonb_build_object(
    'students', v_students,
    'members', v_members
  );
end;
$$;

revoke all on function private.is_org_billing_manager(uuid) from public, anon;
revoke all on function private.subscription_effective_status(uuid) from public, anon;
revoke all on function private.subscription_write_enabled(uuid) from public, anon;
revoke all on function private.subscription_usage_snapshot(uuid) from public, anon;
grant execute on function private.is_org_billing_manager(uuid) to authenticated;
grant execute on function private.subscription_effective_status(uuid) to authenticated;
grant execute on function private.subscription_write_enabled(uuid) to authenticated;
grant execute on function private.subscription_usage_snapshot(uuid) to authenticated;

create or replace function private.initialize_organization_subscription()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_inserted uuid;
begin
  insert into public.organization_subscriptions (
    organization_id,
    plan_code,
    status,
    trial_started_at,
    trial_ends_at,
    authority_source
  )
  values (
    new.id,
    'trial',
    'trialing',
    now(),
    now() + interval '14 days',
    'system_trial'
  )
  on conflict (organization_id) do nothing
  returning organization_id into v_inserted;

  if v_inserted is not null then
    insert into public.subscription_authority_events (
      organization_id,
      event_type,
      from_plan_code,
      to_plan_code,
      from_status,
      to_status,
      authority_source,
      external_event_ref,
      effective_at
    )
    values (
      new.id,
      'trial_initialized',
      null,
      'trial',
      null,
      'trialing',
      'system_trial',
      'system_trial:' || new.id::text,
      now()
    )
    on conflict do nothing;
  end if;

  return new;
end;
$$;

revoke all on function private.initialize_organization_subscription() from public, anon, authenticated;

drop trigger if exists aa_on_organization_subscription_created on public.organizations;
create trigger aa_on_organization_subscription_created
after insert on public.organizations
for each row execute function private.initialize_organization_subscription();

insert into public.organization_subscriptions (
  organization_id,
  plan_code,
  status,
  trial_started_at,
  trial_ends_at,
  authority_source
)
select
  o.id,
  'trial',
  'trialing',
  now(),
  now() + interval '14 days',
  'system_trial'
from public.organizations o
where not exists (
  select 1
  from public.organization_subscriptions s
  where s.organization_id = o.id
)
on conflict (organization_id) do nothing;

insert into public.subscription_authority_events (
  organization_id,
  event_type,
  to_plan_code,
  to_status,
  authority_source,
  external_event_ref,
  effective_at
)
select
  s.organization_id,
  'trial_initialized',
  s.plan_code,
  s.status,
  'system_trial',
  'system_trial:' || s.organization_id::text,
  s.created_at
from public.organization_subscriptions s
where s.authority_source = 'system_trial'
  and not exists (
    select 1
    from public.subscription_authority_events e
    where e.authority_source = 'system_trial'
      and e.external_event_ref = 'system_trial:' || s.organization_id::text
  )
on conflict do nothing;

create or replace function private.enforce_student_subscription_limit()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_limit integer;
  v_usage integer;
  v_status text;
begin
  v_status := private.subscription_effective_status(new.organization_id);
  if v_status = 'uninitialized' then
    raise exception using errcode = '42501', message = 'SUBSCRIPTION_NOT_INITIALIZED';
  end if;
  if not private.subscription_write_enabled(new.organization_id) then
    raise exception using errcode = '42501', message = 'SUBSCRIPTION_WRITE_DISABLED';
  end if;

  select p.student_limit
  into v_limit
  from public.organization_subscriptions s
  join public.subscription_plans p on p.code = s.plan_code
  where s.organization_id = new.organization_id
    and p.lifecycle = 'active';

  if v_limit is null then
    raise exception using errcode = '42501', message = 'SUBSCRIPTION_PLAN_UNAVAILABLE';
  end if;

  select count(*)::int
  into v_usage
  from public.students s
  where s.organization_id = new.organization_id;

  if v_usage >= v_limit then
    raise exception using
      errcode = '23514',
      message = 'STUDENT_LIMIT_REACHED',
      detail = format('student_limit=%s current_usage=%s', v_limit, v_usage);
  end if;

  return new;
end;
$$;

revoke all on function private.enforce_student_subscription_limit() from public, anon, authenticated;

drop trigger if exists students_subscription_limit_gate on public.students;
create trigger students_subscription_limit_gate
before insert on public.students
for each row execute function private.enforce_student_subscription_limit();

create or replace function private.enforce_member_subscription_limit()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_limit integer;
  v_usage integer;
  v_owner uuid;
  v_status text;
begin
  select o.owner_user_id into v_owner
  from public.organizations o
  where o.id = new.organization_id;

  if not exists (
    select 1
    from public.organization_subscriptions s
    where s.organization_id = new.organization_id
  ) then
    if new.user_id = v_owner and new.role = 'owner' then
      return new;
    end if;
    raise exception using errcode = '42501', message = 'SUBSCRIPTION_NOT_INITIALIZED';
  end if;

  v_status := private.subscription_effective_status(new.organization_id);
  if not private.subscription_write_enabled(new.organization_id) then
    raise exception using errcode = '42501', message = 'SUBSCRIPTION_WRITE_DISABLED';
  end if;

  select p.member_limit
  into v_limit
  from public.organization_subscriptions s
  join public.subscription_plans p on p.code = s.plan_code
  where s.organization_id = new.organization_id
    and p.lifecycle = 'active';

  if v_limit is null then
    raise exception using errcode = '42501', message = 'SUBSCRIPTION_PLAN_UNAVAILABLE';
  end if;

  select count(*)::int
  into v_usage
  from public.organization_members m
  where m.organization_id = new.organization_id;

  if v_usage >= v_limit then
    raise exception using
      errcode = '23514',
      message = 'MEMBER_LIMIT_REACHED',
      detail = format('member_limit=%s current_usage=%s', v_limit, v_usage);
  end if;

  return new;
end;
$$;

revoke all on function private.enforce_member_subscription_limit() from public, anon, authenticated;

drop trigger if exists organization_members_subscription_limit_gate on public.organization_members;
create trigger organization_members_subscription_limit_gate
before insert on public.organization_members
for each row execute function private.enforce_member_subscription_limit();

create or replace function private.enforce_decision_intelligence_entitlement()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_enabled boolean;
begin
  if not private.subscription_write_enabled(new.organization_id) then
    raise exception using errcode = '42501', message = 'SUBSCRIPTION_WRITE_DISABLED';
  end if;

  select coalesce((p.feature_flags ->> 'decision_intelligence')::boolean, false)
  into v_enabled
  from public.organization_subscriptions s
  join public.subscription_plans p on p.code = s.plan_code
  where s.organization_id = new.organization_id
    and p.lifecycle = 'active';

  if not coalesce(v_enabled, false) then
    raise exception using errcode = '42501', message = 'ENTITLEMENT_DECISION_INTELLIGENCE_REQUIRED';
  end if;

  return new;
end;
$$;

revoke all on function private.enforce_decision_intelligence_entitlement() from public, anon, authenticated;

drop trigger if exists decision_intelligence_subscription_gate on public.decision_intelligence_runs;
create trigger decision_intelligence_subscription_gate
before insert on public.decision_intelligence_runs
for each row execute function private.enforce_decision_intelligence_entitlement();

create or replace function private.enforce_training_plan_subscription_write()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if not private.subscription_write_enabled(new.organization_id) then
    raise exception using errcode = '42501', message = 'SUBSCRIPTION_WRITE_DISABLED';
  end if;
  return new;
end;
$$;

revoke all on function private.enforce_training_plan_subscription_write() from public, anon, authenticated;

drop trigger if exists training_plans_subscription_write_gate on public.training_plans;
create trigger training_plans_subscription_write_gate
before insert on public.training_plans
for each row execute function private.enforce_training_plan_subscription_write();

create or replace function public.get_subscription_entitlement_snapshot(
  p_organization_id uuid
)
returns jsonb
language plpgsql
stable
security invoker
set search_path = ''
as $$
declare
  v_subscription public.organization_subscriptions%rowtype;
  v_plan public.subscription_plans%rowtype;
  v_usage jsonb;
  v_effective_status text;
  v_student_usage integer;
  v_member_usage integer;
  v_student_remaining integer;
  v_member_remaining integer;
  v_trial_seconds bigint;
begin
  if auth.uid() is null then
    raise exception using errcode = '42501', message = 'AUTH_REQUIRED';
  end if;
  if p_organization_id is null or not private.is_org_member(p_organization_id) then
    raise exception using errcode = '42501', message = 'ORG_MEMBER_REQUIRED';
  end if;

  select * into v_subscription
  from public.organization_subscriptions s
  where s.organization_id = p_organization_id;

  if v_subscription.organization_id is null then
    raise exception using errcode = 'P0002', message = 'SUBSCRIPTION_NOT_INITIALIZED';
  end if;

  select * into v_plan
  from public.subscription_plans p
  where p.code = v_subscription.plan_code;

  if v_plan.code is null then
    raise exception using errcode = 'P0002', message = 'SUBSCRIPTION_PLAN_UNAVAILABLE';
  end if;

  v_usage := private.subscription_usage_snapshot(p_organization_id);
  v_student_usage := coalesce((v_usage ->> 'students')::int, 0);
  v_member_usage := coalesce((v_usage ->> 'members')::int, 0);
  v_effective_status := private.subscription_effective_status(p_organization_id);
  v_student_remaining := greatest(v_plan.student_limit - v_student_usage, 0);
  v_member_remaining := greatest(v_plan.member_limit - v_member_usage, 0);
  v_trial_seconds := case
    when v_effective_status = 'trialing' and v_subscription.trial_ends_at is not null
      then greatest(extract(epoch from (v_subscription.trial_ends_at - now()))::bigint, 0)
    else 0
  end;

  return jsonb_build_object(
    'organization_id', p_organization_id,
    'plan', jsonb_build_object(
      'code', v_plan.code,
      'display_name', v_plan.display_name,
      'student_limit', v_plan.student_limit,
      'member_limit', v_plan.member_limit,
      'feature_flags', v_plan.feature_flags
    ),
    'subscription', jsonb_build_object(
      'status', v_subscription.status,
      'effective_status', v_effective_status,
      'write_enabled', private.subscription_write_enabled(p_organization_id),
      'trial_started_at', v_subscription.trial_started_at,
      'trial_ends_at', v_subscription.trial_ends_at,
      'trial_seconds_remaining', v_trial_seconds,
      'current_period_start', v_subscription.current_period_start,
      'current_period_end', v_subscription.current_period_end,
      'cancel_at_period_end', v_subscription.cancel_at_period_end,
      'provider_connected', v_subscription.provider is not null,
      'authority_source', v_subscription.authority_source,
      'authority_version', v_subscription.authority_version
    ),
    'usage', jsonb_build_object(
      'students', v_student_usage,
      'student_limit', v_plan.student_limit,
      'student_remaining', v_student_remaining,
      'members', v_member_usage,
      'member_limit', v_plan.member_limit,
      'member_remaining', v_member_remaining
    ),
    'features', v_plan.feature_flags,
    'pricing', jsonb_build_object(
      'state', 'UNFROZEN',
      'provider_bound', v_subscription.provider is not null
    ),
    'guardrails', jsonb_build_object(
      'server_enforced_student_limit', true,
      'server_enforced_member_limit', true,
      'server_enforced_training_write', true,
      'server_enforced_decision_intelligence', true,
      'direct_subscription_mutation', false,
      'provider_neutral_core', true
    ),
    'generated_at', now()
  );
end;
$$;

revoke execute on function public.get_subscription_entitlement_snapshot(uuid) from public, anon;
grant execute on function public.get_subscription_entitlement_snapshot(uuid) to authenticated;

create or replace function public.apply_subscription_authority_event(
  p_organization_id uuid,
  p_plan_code text,
  p_status text,
  p_authority_source text,
  p_external_event_ref text,
  p_effective_at timestamptz default now(),
  p_current_period_start timestamptz default null,
  p_current_period_end timestamptz default null,
  p_cancel_at_period_end boolean default false,
  p_provider text default null,
  p_provider_customer_ref text default null,
  p_provider_subscription_ref text default null,
  p_payload_sha256 text default null
)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_current public.organization_subscriptions%rowtype;
  v_event_id uuid;
  v_event_ref text;
  v_next_version bigint;
begin
  if p_organization_id is null then
    raise exception using errcode = '22023', message = 'ORGANIZATION_REQUIRED';
  end if;
  if not exists (
    select 1 from public.subscription_plans p
    where p.code = p_plan_code and p.lifecycle = 'active'
  ) then
    raise exception using errcode = '22023', message = 'SUBSCRIPTION_PLAN_UNAVAILABLE';
  end if;
  if p_status not in ('trialing','active','grace','past_due','canceled','expired') then
    raise exception using errcode = '22023', message = 'INVALID_SUBSCRIPTION_STATUS';
  end if;
  if p_authority_source not in ('provider_webhook','admin_recovery') then
    raise exception using errcode = '22023', message = 'INVALID_SUBSCRIPTION_AUTHORITY_SOURCE';
  end if;

  v_event_ref := nullif(btrim(coalesce(p_external_event_ref, '')), '');
  if v_event_ref is null then
    raise exception using errcode = '22023', message = 'EXTERNAL_EVENT_REF_REQUIRED';
  end if;
  if p_payload_sha256 is not null and p_payload_sha256 !~ '^[0-9a-f]{64}$' then
    raise exception using errcode = '22023', message = 'INVALID_PAYLOAD_SHA256';
  end if;

  select * into v_current
  from public.organization_subscriptions s
  where s.organization_id = p_organization_id
  for update;

  if v_current.organization_id is null then
    raise exception using errcode = 'P0002', message = 'SUBSCRIPTION_NOT_INITIALIZED';
  end if;

  insert into public.subscription_authority_events (
    organization_id,
    event_type,
    from_plan_code,
    to_plan_code,
    from_status,
    to_status,
    authority_source,
    external_event_ref,
    payload_sha256,
    effective_at
  )
  values (
    p_organization_id,
    'subscription_authority_event',
    v_current.plan_code,
    p_plan_code,
    v_current.status,
    p_status,
    p_authority_source,
    v_event_ref,
    p_payload_sha256,
    coalesce(p_effective_at, now())
  )
  on conflict do nothing
  returning id into v_event_id;

  if v_event_id is null then
    return jsonb_build_object(
      'applied', false,
      'idempotent_replay', true,
      'organization_id', p_organization_id,
      'external_event_ref', v_event_ref
    );
  end if;

  v_next_version := v_current.authority_version + 1;

  update public.organization_subscriptions
  set
    plan_code = p_plan_code,
    status = p_status,
    current_period_start = p_current_period_start,
    current_period_end = p_current_period_end,
    cancel_at_period_end = coalesce(p_cancel_at_period_end, false),
    provider = nullif(btrim(coalesce(p_provider, '')), ''),
    provider_customer_ref = nullif(btrim(coalesce(p_provider_customer_ref, '')), ''),
    provider_subscription_ref = nullif(btrim(coalesce(p_provider_subscription_ref, '')), ''),
    authority_source = p_authority_source,
    authority_version = v_next_version,
    updated_at = now()
  where organization_id = p_organization_id;

  return jsonb_build_object(
    'applied', true,
    'idempotent_replay', false,
    'organization_id', p_organization_id,
    'event_id', v_event_id,
    'plan_code', p_plan_code,
    'status', p_status,
    'authority_version', v_next_version
  );
end;
$$;

revoke execute on function public.apply_subscription_authority_event(uuid,text,text,text,text,timestamptz,timestamptz,timestamptz,boolean,text,text,text,text) from public, anon, authenticated;
grant execute on function public.apply_subscription_authority_event(uuid,text,text,text,text,timestamptz,timestamptz,timestamptz,boolean,text,text,text,text) to service_role;

revoke all on public.subscription_plans from anon, authenticated;
revoke all on public.organization_subscriptions from anon, authenticated;
revoke all on public.subscription_authority_events from anon, authenticated;
grant select on public.subscription_plans to authenticated;
grant select on public.organization_subscriptions to authenticated;
grant select on public.subscription_authority_events to authenticated;
grant all on public.subscription_plans to service_role;
grant all on public.organization_subscriptions to service_role;
grant all on public.subscription_authority_events to service_role;

drop policy if exists subscription_plans_select_active on public.subscription_plans;
create policy subscription_plans_select_active
on public.subscription_plans
for select
to authenticated
using (lifecycle = 'active');

drop policy if exists organization_subscriptions_select_member on public.organization_subscriptions;
create policy organization_subscriptions_select_member
on public.organization_subscriptions
for select
to authenticated
using ((select private.is_org_member(organization_id)));

drop policy if exists subscription_authority_events_select_billing_manager on public.subscription_authority_events;
create policy subscription_authority_events_select_billing_manager
on public.subscription_authority_events
for select
to authenticated
using ((select private.is_org_billing_manager(organization_id)));

drop trigger if exists subscription_plans_set_updated_at on public.subscription_plans;
create trigger subscription_plans_set_updated_at
before update on public.subscription_plans
for each row execute function private.set_updated_at();

drop trigger if exists organization_subscriptions_set_updated_at on public.organization_subscriptions;
create trigger organization_subscriptions_set_updated_at
before update on public.organization_subscriptions
for each row execute function private.set_updated_at();
