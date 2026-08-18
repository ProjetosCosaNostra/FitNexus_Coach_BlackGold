drop policy if exists student_access_links_deny_direct on public.student_access_links;
create policy student_access_links_deny_direct
on public.student_access_links
for all
to anon, authenticated
using (false)
with check (false);

comment on policy student_access_links_deny_direct on public.student_access_links is
  'Direct table access is intentionally denied. Student possession-token flows are mediated only by validated RPCs.';
