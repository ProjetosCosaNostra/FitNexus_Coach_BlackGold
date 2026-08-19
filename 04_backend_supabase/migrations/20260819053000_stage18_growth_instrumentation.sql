create table if not exists private.growth_event_catalog (
  event_name text primary key check (event_name ~ '^[a-z0-9_]{3,80}$'),
  funnel_stage text not null check (funnel_stage in ('acquisition','signup','onboarding','activation','retention','revenue')),
  capture_authority text not null check (capture_authority in ('server_trigger','future_public_capture','provider_authority')),
  capture_status text not null check (capture_status in ('active','pending')),
  marketing_safe boolean not null default true,
  description text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

insert into private.growth_event_catalog (
  event_name, funnel_stage, capture_authority, capture_status, marketing_safe, description
)
values
  ('landing_view','acquisition','future_public_capture','pending',true,'Public landing-page view; intentionally pending until a public acquisition surface exists.'),
  ('signup_started','signup','future_public_capture','pending',true,'Signup form started; intentionally pending until public capture is implemented with abuse/privacy controls.'),
  ('signup_completed','signup','server_trigger','active',true,'Supabase auth user created. No email or profile payload is copied into growth telemetry.'),
  ('coach_profile_completed','onboarding','server_trigger','active',true,'Coach profile obtained a non-empty display name.'),
  ('student_created','activation','server_trigger','active',true,'Student record created. Growth telemetry stores no student name, email, objective or health-related field.'),
  ('training_created_or_duplicated','activation','server_trigger','active',true,'Training plan row created. The event intentionally does not copy training content.'),
  ('training_delivered','activation','server_trigger','active',true,'Active student access link issued; operational delivery signal for the coach-to-student loop.'),
  ('workout_logged','retention','server_trigger','active',true,'Workout session reached completed state. No exercise, pain, feedback or health payload is copied.'),
  ('trial_started','revenue','server_trigger','active',true,'Organization subscription entered the initial trial state.'),
  ('checkout_started','revenue','server_trigger','active',true,'Server-authoritative billing checkout intent created.'),
  ('paid','revenue','provider_authority','active',true,'Organization subscription transitioned to active through subscription authority.')
on conflict (event_name) do update set
  funnel_stage = excluded.funnel_stage,
  capture_authority = excluded.capture_authority,
  capture_status = excluded.capture_status,
  marketing_safe = excluded.marketing_safe,
  description = excluded.description,
  updated_at = now();

create table if not exists private.growth_events (
  id uuid primary key default extensions.gen_random_uuid(),
  event_name text not null references private.growth_event_catalog(event_name) on update restrict on delete restrict,
  organization_id uuid references public.organizations(id) on delete cascade,
  actor_user_id uuid references auth.users(id) on delete set null,
  event_source text not null check (event_source in ('server_trigger','provider_authority')),
  source_entity_table text not null check (char_length(btrim(source_entity_table)) between 2 and 100),
  source_entity_id uuid,
  occurred_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);

create unique index if not exists growth_events_entity_uidx
  on private.growth_events(event_name, source_entity_table, source_entity_id)
  where source_entity_id is not null;

create index if not exists growth_events_org_occurred_idx
  on private.growth_events(organization_id, occurred_at desc)
  where organization_id is not null;

create index if not exists growth_events_actor_occurred_idx
  on private.growth_events(actor_user_id, occurred_at desc)
  where actor_user_id is not null;

create index if not exists growth_events_name_occurred_idx
  on private.growth_events(event_name, occurred_at desc);

create table if not exists private.growth_attribution (
  organization_id uuid primary key references public.organizations(id) on delete cascade,
  first_actor_user_id uuid references auth.users(id) on delete set null,
  first_source text,
  first_medium text,
  first_campaign text,
  first_term text,
  first_content text,
  first_landing_path text,
  first_referrer_host text,
  first_captured_at timestamptz,
  last_actor_user_id uuid references auth.users(id) on delete set null,
  last_source text,
  last_medium text,
  last_campaign text,
  last_term text,
  last_content text,
  last_landing_path text,
  last_referrer_host text,
  last_captured_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

revoke all on private.growth_event_catalog from public, anon, authenticated;
revoke all on private.growth_events from public, anon, authenticated;
revoke all on private.growth_attribution from public, anon, authenticated;

revoke all on private.growth_event_catalog from service_role;
revoke all on private.growth_events from service_role;
revoke all on private.growth_attribution from service_role;
grant select on private.growth_event_catalog to service_role;
grant select on private.growth_events to service_role;
grant select on private.growth_attribution to service_role;

create or replace function private.append_growth_event(
  p_event_name text,
  p_organization_id uuid,
  p_actor_user_id uuid,
  p_event_source text,
  p_source_entity_table text,
  p_source_entity_id uuid,
  p_occurred_at timestamptz default now()
)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_catalog private.growth_event_catalog%rowtype;
begin
  select * into v_catalog
  from private.growth_event_catalog c
  where c.event_name = p_event_name;

  if v_catalog.event_name is null or v_catalog.capture_status <> 'active' then
    raise exception using errcode = '22023', message = 'GROWTH_EVENT_NOT_ACTIVE';
  end if;
  if p_event_source not in ('server_trigger','provider_authority') then
    raise exception using errcode = '22023', message = 'INVALID_GROWTH_EVENT_SOURCE';
  end if;

  insert into private.growth_events (
    event_name,
    organization_id,
    actor_user_id,
    event_source,
    source_entity_table,
    source_entity_id,
    occurred_at
  )
  values (
    p_event_name,
    p_organization_id,
    p_actor_user_id,
    p_event_source,
    p_source_entity_table,
    p_source_entity_id,
    coalesce(p_occurred_at, now())
  )
  on conflict do nothing;
end;
$$;

revoke execute on function private.append_growth_event(text,uuid,uuid,text,text,uuid,timestamptz) from public, anon, authenticated, service_role;

create or replace function private.growth_on_auth_user_created()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  perform private.append_growth_event(
    'signup_completed', null, new.id, 'server_trigger', 'auth.users', new.id, coalesce(new.created_at, now())
  );
  return new;
end;
$$;

revoke execute on function private.growth_on_auth_user_created() from public, anon, authenticated, service_role;

drop trigger if exists zz_growth_auth_user_created on auth.users;
create trigger zz_growth_auth_user_created
after insert on auth.users
for each row execute function private.growth_on_auth_user_created();

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
  v_became_complete := nullif(btrim(coalesce(new.display_name,'')), '') is not null
    and (tg_op = 'INSERT' or nullif(btrim(coalesce(old.display_name,'')), '') is null);

  if not v_became_complete then return new; end if;

  select m.organization_id into v_org_id
  from public.organization_members m
  where m.user_id = new.user_id
  order by m.created_at
  limit 1;

  perform private.append_growth_event(
    'coach_profile_completed', v_org_id, new.user_id, 'server_trigger', 'public.profiles', new.user_id, coalesce(new.updated_at, now())
  );
  return new;
end;
$$;

revoke execute on function private.growth_on_profile_completed() from public, anon, authenticated, service_role;

drop trigger if exists zz_growth_profile_completed on public.profiles;
create trigger zz_growth_profile_completed
after insert or update of display_name on public.profiles
for each row execute function private.growth_on_profile_completed();

create or replace function private.growth_on_student_created()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  perform private.append_growth_event(
    'student_created', new.organization_id, auth.uid(), 'server_trigger', 'public.students', new.id, new.created_at
  );
  return new;
end;
$$;

revoke execute on function private.growth_on_student_created() from public, anon, authenticated, service_role;

drop trigger if exists zz_growth_student_created on public.students;
create trigger zz_growth_student_created
after insert on public.students
for each row execute function private.growth_on_student_created();

create or replace function private.growth_on_training_created()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  perform private.append_growth_event(
    'training_created_or_duplicated', new.organization_id, auth.uid(), 'server_trigger', 'public.training_plans', new.id, new.created_at
  );
  return new;
end;
$$;

revoke execute on function private.growth_on_training_created() from public, anon, authenticated, service_role;

drop trigger if exists zz_growth_training_created on public.training_plans;
create trigger zz_growth_training_created
after insert on public.training_plans
for each row execute function private.growth_on_training_created();

create or replace function private.growth_on_training_delivered()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if new.is_active then
    perform private.append_growth_event(
      'training_delivered', new.organization_id, coalesce(new.created_by, auth.uid()), 'server_trigger', 'public.student_access_links', new.id, new.created_at
    );
  end if;
  return new;
end;
$$;

revoke execute on function private.growth_on_training_delivered() from public, anon, authenticated, service_role;

drop trigger if exists zz_growth_training_delivered on public.student_access_links;
create trigger zz_growth_training_delivered
after insert on public.student_access_links
for each row execute function private.growth_on_training_delivered();

create or replace function private.growth_on_workout_logged()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_completed_now boolean;
  v_was_completed boolean := false;
begin
  v_completed_now := new.status = 'completed' or new.completed_at is not null;
  if tg_op = 'UPDATE' then
    v_was_completed := old.status = 'completed' or old.completed_at is not null;
  end if;

  if v_completed_now and not v_was_completed then
    perform private.append_growth_event(
      'workout_logged', new.organization_id, null, 'server_trigger', 'public.workout_sessions', new.id, coalesce(new.completed_at, new.updated_at, now())
    );
  end if;
  return new;
end;
$$;

revoke execute on function private.growth_on_workout_logged() from public, anon, authenticated, service_role;

drop trigger if exists zz_growth_workout_logged on public.workout_sessions;
create trigger zz_growth_workout_logged
after insert or update of status, completed_at on public.workout_sessions
for each row execute function private.growth_on_workout_logged();

create or replace function private.growth_on_subscription_state()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_trial_started boolean;
  v_paid_now boolean;
  v_paid_before boolean := false;
begin
  v_trial_started := tg_op = 'INSERT' and new.status = 'trialing';
  v_paid_now := new.status = 'active';
  if tg_op = 'UPDATE' then v_paid_before := old.status = 'active'; end if;

  if v_trial_started then
    perform private.append_growth_event(
      'trial_started', new.organization_id, null, 'server_trigger', 'public.organization_subscriptions', new.organization_id, coalesce(new.trial_started_at, new.created_at, now())
    );
  end if;

  if v_paid_now and not v_paid_before then
    perform private.append_growth_event(
      'paid', new.organization_id, null, 'provider_authority', 'public.organization_subscriptions', new.organization_id, coalesce(new.current_period_start, new.updated_at, now())
    );
  end if;
  return new;
end;
$$;

revoke execute on function private.growth_on_subscription_state() from public, anon, authenticated, service_role;

drop trigger if exists zz_growth_subscription_state on public.organization_subscriptions;
create trigger zz_growth_subscription_state
after insert or update of status on public.organization_subscriptions
for each row execute function private.growth_on_subscription_state();

create or replace function private.growth_on_checkout_started()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  perform private.append_growth_event(
    'checkout_started', new.organization_id, new.created_by, 'server_trigger', 'public.billing_checkout_intents', new.id, new.created_at
  );
  return new;
end;
$$;

revoke execute on function private.growth_on_checkout_started() from public, anon, authenticated, service_role;

drop trigger if exists zz_growth_checkout_started on public.billing_checkout_intents;
create trigger zz_growth_checkout_started
after insert on public.billing_checkout_intents
for each row execute function private.growth_on_checkout_started();

create or replace function private.attach_growth_attribution_authority(
  p_organization_id uuid,
  p_actor_user_id uuid,
  p_source text,
  p_medium text,
  p_campaign text,
  p_term text,
  p_content text,
  p_landing_path text,
  p_referrer_host text
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_now timestamptz := now();
  v_row private.growth_attribution%rowtype;
  v_source text := nullif(left(btrim(coalesce(p_source,'')),100),'');
  v_medium text := nullif(left(btrim(coalesce(p_medium,'')),100),'');
  v_campaign text := nullif(left(btrim(coalesce(p_campaign,'')),160),'');
  v_term text := nullif(left(btrim(coalesce(p_term,'')),160),'');
  v_content text := nullif(left(btrim(coalesce(p_content,'')),160),'');
  v_landing text := nullif(left(btrim(coalesce(p_landing_path,'')),500),'');
  v_referrer text := nullif(left(lower(btrim(coalesce(p_referrer_host,''))),253),'');
begin
  if p_actor_user_id is null or auth.uid() is distinct from p_actor_user_id then
    raise exception using errcode = '42501', message = 'ATTRIBUTION_ACTOR_MISMATCH';
  end if;
  if p_organization_id is null or not private.is_org_member(p_organization_id) then
    raise exception using errcode = '42501', message = 'ORG_MEMBER_REQUIRED';
  end if;
  if v_landing is not null and left(v_landing,1) <> '/' then
    raise exception using errcode = '22023', message = 'LANDING_PATH_MUST_BE_RELATIVE';
  end if;
  if v_source is null and v_medium is null and v_campaign is null and v_referrer is null then
    raise exception using errcode = '22023', message = 'ATTRIBUTION_TOUCH_EMPTY';
  end if;

  insert into private.growth_attribution (
    organization_id,
    first_actor_user_id, first_source, first_medium, first_campaign, first_term, first_content, first_landing_path, first_referrer_host, first_captured_at,
    last_actor_user_id, last_source, last_medium, last_campaign, last_term, last_content, last_landing_path, last_referrer_host, last_captured_at
  )
  values (
    p_organization_id,
    p_actor_user_id, v_source, v_medium, v_campaign, v_term, v_content, v_landing, v_referrer, v_now,
    p_actor_user_id, v_source, v_medium, v_campaign, v_term, v_content, v_landing, v_referrer, v_now
  )
  on conflict (organization_id) do update set
    last_actor_user_id = excluded.last_actor_user_id,
    last_source = excluded.last_source,
    last_medium = excluded.last_medium,
    last_campaign = excluded.last_campaign,
    last_term = excluded.last_term,
    last_content = excluded.last_content,
    last_landing_path = excluded.last_landing_path,
    last_referrer_host = excluded.last_referrer_host,
    last_captured_at = excluded.last_captured_at,
    updated_at = now()
  returning * into v_row;

  return jsonb_build_object(
    'organization_id', v_row.organization_id,
    'first_touch', jsonb_build_object('source',v_row.first_source,'medium',v_row.first_medium,'campaign',v_row.first_campaign,'landing_path',v_row.first_landing_path,'referrer_host',v_row.first_referrer_host,'captured_at',v_row.first_captured_at),
    'last_touch', jsonb_build_object('source',v_row.last_source,'medium',v_row.last_medium,'campaign',v_row.last_campaign,'landing_path',v_row.last_landing_path,'referrer_host',v_row.last_referrer_host,'captured_at',v_row.last_captured_at)
  );
end;
$$;

revoke execute on function private.attach_growth_attribution_authority(uuid,uuid,text,text,text,text,text,text,text) from public, anon, service_role;
grant execute on function private.attach_growth_attribution_authority(uuid,uuid,text,text,text,text,text,text,text) to authenticated;

create or replace function public.attach_growth_attribution(
  p_organization_id uuid,
  p_source text default null,
  p_medium text default null,
  p_campaign text default null,
  p_term text default null,
  p_content text default null,
  p_landing_path text default null,
  p_referrer_host text default null
)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
begin
  if auth.uid() is null then raise exception using errcode='42501',message='AUTH_REQUIRED'; end if;
  if p_organization_id is null or not private.is_org_member(p_organization_id) then raise exception using errcode='42501',message='ORG_MEMBER_REQUIRED'; end if;
  return private.attach_growth_attribution_authority(p_organization_id,auth.uid(),p_source,p_medium,p_campaign,p_term,p_content,p_landing_path,p_referrer_host);
end;
$$;

revoke execute on function public.attach_growth_attribution(uuid,text,text,text,text,text,text,text) from public, anon, service_role;
grant execute on function public.attach_growth_attribution(uuid,text,text,text,text,text,text,text) to authenticated;

create or replace function private.get_growth_funnel_snapshot_authority(
  p_organization_id uuid,
  p_days integer
)
returns jsonb
language plpgsql
stable
security definer
set search_path = ''
as $$
declare
  v_since timestamptz;
  v_signup_at timestamptz;
  v_profile_at timestamptz;
  v_student_at timestamptz;
  v_training_at timestamptz;
  v_delivery_at timestamptz;
  v_checkout_at timestamptz;
  v_paid_at timestamptz;
  v_trial_at timestamptz;
  v_workout_count integer;
  v_delivery_count integer;
  v_weekly_coaches integer;
  v_ttfv bigint;
  v_attribution private.growth_attribution%rowtype;
  v_pending_public jsonb;
begin
  if p_days is null or p_days < 1 or p_days > 365 then
    raise exception using errcode = '22023', message = 'INVALID_GROWTH_WINDOW';
  end if;
  v_since := now() - make_interval(days => p_days);

  select min(e.occurred_at) into v_signup_at
  from private.growth_events e
  where e.event_name = 'signup_completed'
    and e.occurred_at >= v_since
    and (
      e.organization_id = p_organization_id
      or exists (select 1 from public.organization_members m where m.organization_id=p_organization_id and m.user_id=e.actor_user_id)
    );

  select min(e.occurred_at) filter (where e.event_name='coach_profile_completed'),
         min(e.occurred_at) filter (where e.event_name='student_created'),
         min(e.occurred_at) filter (where e.event_name='training_created_or_duplicated'),
         min(e.occurred_at) filter (where e.event_name='training_delivered'),
         min(e.occurred_at) filter (where e.event_name='trial_started'),
         min(e.occurred_at) filter (where e.event_name='checkout_started'),
         min(e.occurred_at) filter (where e.event_name='paid'),
         count(*) filter (where e.event_name='workout_logged')::int,
         count(*) filter (where e.event_name='training_delivered')::int
    into v_profile_at,v_student_at,v_training_at,v_delivery_at,v_trial_at,v_checkout_at,v_paid_at,v_workout_count,v_delivery_count
  from private.growth_events e
  where e.organization_id=p_organization_id and e.occurred_at>=v_since;

  select count(distinct e.actor_user_id)::int into v_weekly_coaches
  from private.growth_events e
  where e.organization_id=p_organization_id and e.event_name='training_delivered'
    and e.occurred_at>=now()-interval '7 days' and e.actor_user_id is not null;

  if v_signup_at is not null and v_delivery_at is not null and v_delivery_at>=v_signup_at then
    v_ttfv := extract(epoch from (v_delivery_at-v_signup_at))::bigint;
  end if;

  select * into v_attribution from private.growth_attribution a where a.organization_id=p_organization_id;

  select coalesce(jsonb_agg(c.event_name order by c.event_name),'[]'::jsonb) into v_pending_public
  from private.growth_event_catalog c where c.capture_status='pending';

  return jsonb_build_object(
    'organization_id',p_organization_id,
    'window_days',p_days,
    'funnel',jsonb_build_object(
      'signup_completed_at',v_signup_at,
      'coach_profile_completed_at',v_profile_at,
      'student_created_at',v_student_at,
      'training_created_or_duplicated_at',v_training_at,
      'training_delivered_at',v_delivery_at,
      'trial_started_at',v_trial_at,
      'checkout_started_at',v_checkout_at,
      'paid_at',v_paid_at,
      'time_to_first_value_seconds',v_ttfv
    ),
    'usage',jsonb_build_object('training_deliveries',v_delivery_count,'workouts_logged',v_workout_count),
    'north_star',jsonb_build_object(
      'definition','coaches_with_at_least_one_training_delivery_in_last_7_days',
      'weekly_value_coaches',v_weekly_coaches,
      'organization_has_weekly_value',v_weekly_coaches>0
    ),
    'attribution',case when v_attribution.organization_id is null then null else jsonb_build_object(
      'first_source',v_attribution.first_source,'first_medium',v_attribution.first_medium,'first_campaign',v_attribution.first_campaign,
      'last_source',v_attribution.last_source,'last_medium',v_attribution.last_medium,'last_campaign',v_attribution.last_campaign
    ) end,
    'instrumentation',jsonb_build_object(
      'server_authoritative_capture',true,
      'pending_public_capture_events',v_pending_public,
      'return_d7_measurement','PENDING_SESSION_ACTIVITY_EVENT',
      'paid_media_gate',case when jsonb_array_length(v_pending_public)=0 then 'TRACKING_CORE_READY' else 'BLOCKED_TRACKING_INCOMPLETE' end,
      'sensitive_health_payload_in_growth_events',false
    ),
    'generated_at',now()
  );
end;
$$;

revoke execute on function private.get_growth_funnel_snapshot_authority(uuid,integer) from public, anon, service_role;
grant execute on function private.get_growth_funnel_snapshot_authority(uuid,integer) to authenticated;

create or replace function public.get_growth_funnel_snapshot(
  p_organization_id uuid,
  p_days integer default 30
)
returns jsonb
language plpgsql
stable
security invoker
set search_path = ''
as $$
begin
  if auth.uid() is null then raise exception using errcode='42501',message='AUTH_REQUIRED'; end if;
  if p_organization_id is null or not private.is_org_member(p_organization_id) then raise exception using errcode='42501',message='ORG_MEMBER_REQUIRED'; end if;
  return private.get_growth_funnel_snapshot_authority(p_organization_id,p_days);
end;
$$;

revoke execute on function public.get_growth_funnel_snapshot(uuid,integer) from public, anon, service_role;
grant execute on function public.get_growth_funnel_snapshot(uuid,integer) to authenticated;
