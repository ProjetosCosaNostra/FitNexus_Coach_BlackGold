revoke all on public.subscription_plans from service_role;
revoke all on public.organization_subscriptions from service_role;
revoke all on public.subscription_authority_events from service_role;

grant select on public.subscription_plans to service_role;
grant select, update on public.organization_subscriptions to service_role;
grant select, insert on public.subscription_authority_events to service_role;

-- Provider adapters may transition subscription authority, but they cannot
-- mutate the plan catalog or rewrite/delete historical authority events.
