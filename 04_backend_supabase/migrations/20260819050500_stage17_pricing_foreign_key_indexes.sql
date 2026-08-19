create index if not exists subscription_plan_prices_pricing_decision_version_idx
  on public.subscription_plan_prices(pricing_decision_version);

create index if not exists billing_checkout_intents_pricing_decision_version_idx
  on public.billing_checkout_intents(pricing_decision_version);

create index if not exists billing_fee_assumptions_provider_code_idx
  on public.billing_fee_assumptions(provider_code);
