drop policy if exists decision_intelligence_runs_insert_manager on public.decision_intelligence_runs;
create policy decision_intelligence_runs_insert_manager
on public.decision_intelligence_runs
for insert to authenticated
with check (
  (select private.is_org_manager(organization_id))
  and created_by = (select auth.uid())
);
