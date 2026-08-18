create or replace function public.get_professor_feedback_feed(p_organization_id uuid)
returns jsonb
language plpgsql
stable
security invoker
set search_path = ''
as $$
declare
  v_items jsonb := '[]'::jsonb;
begin
  if auth.uid() is null then
    raise exception using errcode = '42501', message = 'AUTH_REQUIRED';
  end if;

  if p_organization_id is null or not private.is_org_member(p_organization_id) then
    raise exception using errcode = '42501', message = 'ORG_MEMBER_REQUIRED';
  end if;

  select coalesce(jsonb_agg(x.item order by x.submitted_at desc), '[]'::jsonb)
    into v_items
    from (
      select wf.submitted_at,
        jsonb_build_object(
          'feedback_id', wf.id,
          'session_id', wf.session_id,
          'student_id', wf.student_id,
          'student_name', s.name,
          'plan_name', p.name,
          'perceived_exertion', wf.perceived_exertion,
          'pain_score', wf.pain_score,
          'energy_score', wf.energy_score,
          'pain_location', wf.pain_location,
          'note', wf.note,
          'submitted_at', wf.submitted_at,
          'risk_signal', case
            when wf.pain_score >= 7 then 'high'
            when wf.pain_score >= 4 then 'medium'
            when wf.perceived_exertion >= 9 and wf.energy_score <= 2 then 'high'
            when wf.perceived_exertion >= 9 or wf.energy_score <= 2 then 'medium'
            else 'low'
          end
        ) as item
      from public.workout_feedback wf
      join public.students s
        on s.id = wf.student_id
       and s.organization_id = wf.organization_id
      join public.workout_sessions ws
        on ws.id = wf.session_id
       and ws.organization_id = wf.organization_id
      join public.training_plans p
        on p.id = ws.training_plan_id
       and p.organization_id = wf.organization_id
      where wf.organization_id = p_organization_id
      order by wf.submitted_at desc
      limit 50
    ) x;

  return jsonb_build_object('items', v_items, 'generated_at', now());
end;
$$;

revoke execute on function public.get_professor_feedback_feed(uuid) from public, anon;
grant execute on function public.get_professor_feedback_feed(uuid) to authenticated;
