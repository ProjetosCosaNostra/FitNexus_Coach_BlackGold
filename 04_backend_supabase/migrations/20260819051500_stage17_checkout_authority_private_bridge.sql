drop policy if exists billing_fee_assumptions_service_read on public.billing_fee_assumptions;
create policy billing_fee_assumptions_service_read
on public.billing_fee_assumptions
for select
to service_role
using (true);

create or replace function private.create_billing_checkout_intent_authority(
  p_organization_id uuid,
  p_plan_code text,
  p_billing_interval text,
  p_idempotency_key uuid
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_selection public.billing_provider_selections%rowtype;
  v_price public.subscription_plan_prices%rowtype;
  v_decision public.pricing_decisions%rowtype;
  v_intent public.billing_checkout_intents%rowtype;
begin
  if auth.uid() is null then raise exception using errcode='42501',message='AUTH_REQUIRED'; end if;
  if p_organization_id is null or not private.is_org_billing_manager(p_organization_id) then raise exception using errcode='42501',message='ORG_BILLING_MANAGER_REQUIRED'; end if;
  if p_billing_interval not in ('month','year') then raise exception using errcode='22023',message='INVALID_BILLING_INTERVAL'; end if;

  select * into v_selection from public.billing_provider_selections s where s.scope='BR_V1';
  if v_selection.scope is null then raise exception using errcode='P0002',message='BILLING_PROVIDER_NOT_SELECTED'; end if;
  if v_selection.state<>'active' then raise exception using errcode='42501',message='BILLING_PROVIDER_CREDENTIALS_NOT_READY'; end if;

  select * into v_price
  from public.subscription_plan_prices p
  where p.plan_code=p_plan_code and p.currency='BRL' and p.billing_interval=p_billing_interval
    and p.lifecycle='active' and p.pricing_decision_version is not null
    and (p.effective_from is null or p.effective_from<=now())
    and (p.effective_until is null or p.effective_until>now())
  limit 1;
  if v_price.id is null then raise exception using errcode='42501',message='COMMERCIAL_PRICE_NOT_PROMOTED'; end if;

  select * into v_decision
  from public.pricing_decisions d
  where d.decision_version=v_price.pricing_decision_version
    and d.mode in ('experiment','frozen') and d.scope='BR_V1' and d.currency='BRL';
  if v_decision.decision_version is null then raise exception using errcode='42501',message='PRICING_DECISION_NOT_CURRENT'; end if;

  select * into v_intent from public.billing_checkout_intents i where i.idempotency_key=p_idempotency_key;
  if v_intent.id is not null then
    if v_intent.organization_id<>p_organization_id or v_intent.plan_code<>p_plan_code
      or v_intent.billing_interval<>p_billing_interval
      or v_intent.pricing_decision_version<>v_price.pricing_decision_version
    then raise exception using errcode='40900',message='CHECKOUT_IDEMPOTENCY_KEY_CONFLICT'; end if;
    return jsonb_build_object('checkout_intent_id',v_intent.id,'idempotent_replay',true,'status',v_intent.status,'provider_code',v_intent.provider_code,'pricing_decision_version',v_intent.pricing_decision_version,'checkout_url',v_intent.checkout_url);
  end if;

  insert into public.billing_checkout_intents(
    organization_id,plan_code,price_id,provider_code,currency,amount_minor,billing_interval,idempotency_key,created_by,pricing_decision_version
  ) values(
    p_organization_id,p_plan_code,v_price.id,v_selection.provider_code,v_price.currency,v_price.amount_minor,v_price.billing_interval,p_idempotency_key,auth.uid(),v_price.pricing_decision_version
  ) returning * into v_intent;

  return jsonb_build_object('checkout_intent_id',v_intent.id,'idempotent_replay',false,'status',v_intent.status,'provider_code',v_intent.provider_code,'plan_code',v_intent.plan_code,'currency',v_intent.currency,'amount_minor',v_intent.amount_minor,'billing_interval',v_intent.billing_interval,'pricing_decision_version',v_intent.pricing_decision_version,'checkout_url',null);
end;
$$;

revoke execute on function private.create_billing_checkout_intent_authority(uuid,text,text,uuid) from public, anon, service_role;
grant execute on function private.create_billing_checkout_intent_authority(uuid,text,text,uuid) to authenticated;

create or replace function public.create_billing_checkout_intent(
  p_organization_id uuid,
  p_plan_code text,
  p_billing_interval text default 'month',
  p_idempotency_key uuid default extensions.gen_random_uuid()
)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
begin
  if auth.uid() is null then raise exception using errcode='42501',message='AUTH_REQUIRED'; end if;
  if p_organization_id is null or not private.is_org_billing_manager(p_organization_id) then raise exception using errcode='42501',message='ORG_BILLING_MANAGER_REQUIRED'; end if;
  if p_billing_interval not in ('month','year') then raise exception using errcode='22023',message='INVALID_BILLING_INTERVAL'; end if;
  return private.create_billing_checkout_intent_authority(p_organization_id,p_plan_code,p_billing_interval,p_idempotency_key);
end;
$$;

revoke execute on function public.create_billing_checkout_intent(uuid,text,text,uuid) from public, anon, service_role;
grant execute on function public.create_billing_checkout_intent(uuid,text,text,uuid) to authenticated;
