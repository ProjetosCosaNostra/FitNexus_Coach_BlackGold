create index if not exists organization_subscriptions_plan_code_idx
  on public.organization_subscriptions(plan_code);

create index if not exists subscription_authority_events_from_plan_code_idx
  on public.subscription_authority_events(from_plan_code);

create index if not exists subscription_authority_events_to_plan_code_idx
  on public.subscription_authority_events(to_plan_code);
