-- Stage 22: adversarial tenant-isolation relational interlock.
--
-- The student possession-token path already resolves tenant identity server-side. This
-- migration moves two remaining assumptions from procedural correctness into database
-- referential integrity so privileged/future code cannot silently bind a session or a
-- token-rotation lineage to a different student/organization.
--
-- Failure class: BGF-TENANT-RELATIONSHIP-DECOUPLING-154

create unique index if not exists student_access_links_id_student_org_uq
  on public.student_access_links(id, student_id, organization_id);

-- A rotation predecessor must belong to the same student and organization. Keep the
-- intended SET NULL semantics only on the optional predecessor column.
alter table public.student_access_links
  drop constraint if exists student_access_links_rotated_from_link_id_fkey;

alter table public.student_access_links
  drop constraint if exists student_access_links_rotation_same_student_org_fk;

alter table public.student_access_links
  add constraint student_access_links_rotation_same_student_org_fk
  foreign key (rotated_from_link_id, student_id, organization_id)
  references public.student_access_links(id, student_id, organization_id)
  on delete set null (rotated_from_link_id);

alter table public.student_access_links
  drop constraint if exists student_access_links_rotation_not_self_chk;

alter table public.student_access_links
  add constraint student_access_links_rotation_not_self_chk
  check (rotated_from_link_id is null or rotated_from_link_id <> id);

-- A workout session may only reference the possession-token link that belongs to the
-- exact same student and tenant. This closes the last single-column relationship on
-- the student execution chain.
alter table public.workout_sessions
  drop constraint if exists workout_sessions_student_access_link_id_fkey;

alter table public.workout_sessions
  drop constraint if exists workout_sessions_access_link_same_student_org_fk;

alter table public.workout_sessions
  add constraint workout_sessions_access_link_same_student_org_fk
  foreign key (student_access_link_id, student_id, organization_id)
  references public.student_access_links(id, student_id, organization_id)
  on delete set null (student_access_link_id);
