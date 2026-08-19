-- Read-only live verification probe for the authoritative Supabase project.
-- Run after every migration that touches the student possession-token execution chain.

select
  (select count(*)
     from public.workout_sessions ws
     join public.student_access_links l on l.id = ws.student_access_link_id
    where ws.student_access_link_id is not null
      and (ws.student_id <> l.student_id or ws.organization_id <> l.organization_id))
    as workout_access_link_cross_tenant_mismatches,
  (select count(*)
     from public.student_access_links l
     join public.student_access_links p on p.id = l.rotated_from_link_id
    where l.rotated_from_link_id is not null
      and (l.student_id <> p.student_id or l.organization_id <> p.organization_id))
    as rotation_lineage_cross_tenant_mismatches,
  has_function_privilege('anon', 'public.get_student_workout_v2(text)', 'EXECUTE')
    as anon_v2_workout_execute,
  has_function_privilege('anon', 'public.get_student_workout(text)', 'EXECUTE')
    as anon_legacy_workout_execute,
  has_table_privilege('anon', 'public.student_access_links', 'SELECT')
    as anon_student_access_links_select,
  has_table_privilege('anon', 'public.workout_sessions', 'SELECT')
    as anon_workout_sessions_select;
