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
  if auth.uid() is null then
    raise exception using errcode = '42501', message = 'AUTH_REQUIRED';
  end if;
  if p_organization_id is null or not private.is_org_member(p_organization_id) then
    raise exception using errcode = '42501', message = 'ORG_MEMBER_REQUIRED';
  end if;
  if p_days is null or p_days < 1 or p_days > 365 then
    raise exception using errcode = '22023', message = 'INVALID_GROWTH_WINDOW';
  end if;

  v_since := now() - make_interval(days => p_days);

  select min(e.occurred_at)
  into v_signup_at
  from private.growth_events e
  where e.event_name = 'signup_completed'
    and e.occurred_at >= v_since
    and (
      e.organization_id = p_organization_id
      or exists (
        select 1
        from public.organization_members m
        where m.organization_id = p_organization_id
          and m.user_id = e.actor_user_id
      )
    );

  select
    min(e.occurred_at) filter (where e.event_name = 'coach_profile_completed'),
    min(e.occurred_at) filter (where e.event_name = 'student_created'),
    min(e.occurred_at) filter (where e.event_name = 'training_created_or_duplicated'),
    min(e.occurred_at) filter (where e.event_name = 'training_delivered'),
    min(e.occurred_at) filter (where e.event_name = 'trial_started'),
    min(e.occurred_at) filter (where e.event_name = 'checkout_started'),
    min(e.occurred_at) filter (where e.event_name = 'paid'),
    count(*) filter (where e.event_name = 'workout_logged')::int,
    count(*) filter (where e.event_name = 'training_delivered')::int
  into
    v_profile_at,
    v_student_at,
    v_training_at,
    v_delivery_at,
    v_trial_at,
    v_checkout_at,
    v_paid_at,
    v_workout_count,
    v_delivery_count
  from private.growth_events e
  where e.organization_id = p_organization_id
    and e.occurred_at >= v_since;

  select count(distinct e.actor_user_id)::int
  into v_weekly_coaches
  from private.growth_events e
  where e.organization_id = p_organization_id
    and e.event_name = 'training_delivered'
    and e.occurred_at >= now() - interval '7 days'
    and e.actor_user_id is not null;

  if v_signup_at is not null
    and v_delivery_at is not null
    and v_delivery_at >= v_signup_at
  then
    v_ttfv := extract(epoch from (v_delivery_at - v_signup_at))::bigint;
  end if;

  select *
  into v_attribution
  from private.growth_attribution a
  where a.organization_id = p_organization_id;

  select coalesce(jsonb_agg(c.event_name order by c.event_name), '[]'::jsonb)
  into v_pending_public
  from private.growth_event_catalog c
  where c.capture_status = 'pending';

  return jsonb_build_object(
    'organization_id', p_organization_id,
    'window_days', p_days,
    'funnel', jsonb_build_object(
      'signup_completed_at', v_signup_at,
      'coach_profile_completed_at', v_profile_at,
      'student_created_at', v_student_at,
      'training_created_or_duplicated_at', v_training_at,
      'training_delivered_at', v_delivery_at,
      'trial_started_at', v_trial_at,
      'checkout_started_at', v_checkout_at,
      'paid_at', v_paid_at,
      'time_to_first_value_seconds', v_ttfv
    ),
    'usage', jsonb_build_object(
      'training_deliveries', v_delivery_count,
      'workouts_logged', v_workout_count
    ),
    'north_star', jsonb_build_object(
      'definition', 'coaches_with_at_least_one_training_delivery_in_last_7_days',
      'weekly_value_coaches', v_weekly_coaches,
      'organization_has_weekly_value', v_weekly_coaches > 0
    ),
    'attribution', case
      when v_attribution.organization_id is null then null
      else jsonb_build_object(
        'first_source', v_attribution.first_source,
        'first_medium', v_attribution.first_medium,
        'first_campaign', v_attribution.first_campaign,
        'last_source', v_attribution.last_source,
        'last_medium', v_attribution.last_medium,
        'last_campaign', v_attribution.last_campaign
      )
    end,
    'instrumentation', jsonb_build_object(
      'server_authoritative_capture', true,
      'pending_public_capture_events', v_pending_public,
      'return_d7_measurement', 'PENDING_SESSION_ACTIVITY_EVENT',
      'paid_media_gate', case
        when jsonb_array_length(v_pending_public) = 0 then 'TRACKING_CORE_READY'
        else 'BLOCKED_TRACKING_INCOMPLETE'
      end,
      'sensitive_health_payload_in_growth_events', false
    ),
    'generated_at', now()
  );
end;
$$;

revoke execute on function private.get_growth_funnel_snapshot_authority(uuid,integer)
from public, anon, service_role;
grant execute on function private.get_growth_funnel_snapshot_authority(uuid,integer)
to authenticated;
