-- Stage 22 follow-up: cover the new composite tenant-isolation foreign keys.
--
-- Supabase Performance Advisor detected both Stage 22 composite foreign keys without
-- covering indexes immediately after relational-interlock promotion.
--
-- Failure class: BGF-TENANT-FK-INDEX-COVERAGE-158

create index if not exists student_access_links_rotation_same_student_org_fk_idx
  on public.student_access_links(rotated_from_link_id, student_id, organization_id);

create index if not exists workout_sessions_access_link_same_student_org_fk_idx
  on public.workout_sessions(student_access_link_id, student_id, organization_id);
