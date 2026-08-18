create index if not exists training_plan_lineage_plan_student_org_fk_idx
  on public.training_plan_lineage(plan_id, student_id, organization_id);

create index if not exists training_plan_lineage_predecessor_student_org_fk_idx
  on public.training_plan_lineage(predecessor_plan_id, student_id, organization_id)
  where predecessor_plan_id is not null;

create index if not exists training_plan_lineage_template_org_fk_idx
  on public.training_plan_lineage(source_template_id, organization_id)
  where source_template_id is not null;
