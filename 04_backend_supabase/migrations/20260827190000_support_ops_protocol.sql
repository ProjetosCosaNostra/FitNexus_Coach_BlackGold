-- Support Ops Autopilot V1
-- Candidate only. Do not apply remotely without a separately authorized migration gate.

create sequence if not exists public.fitnexus_support_protocol_seq;

create table if not exists public.support_requests (
  id uuid primary key default gen_random_uuid(),
  protocol_number text not null unique,
  source_channel text not null default 'EMAIL',
  source_message_id text not null unique,
  requester_email text not null,
  subject text not null default '',
  category text not null default 'OTHER',
  status text not null default 'RECEIVED',
  triage_summary text,
  attention_security boolean not null default false,
  attention_privacy boolean not null default false,
  received_at timestamptz not null default now(),
  triaged_at timestamptz,
  resolved_at timestamptz,
  closed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint support_requests_source_channel_check check (source_channel in ('EMAIL')),
  constraint support_requests_category_check check (category in ('SUPPORT','BILLING','PRIVACY_DATA','SECURITY','OTHER')),
  constraint support_requests_status_check check (status in ('RECEIVED','TRIAGED','NEEDS_ACTION','WAITING_REQUESTER','RESOLVED','CLOSED')),
  constraint support_requests_email_nonempty_check check (length(btrim(requester_email)) > 2),
  constraint support_requests_message_id_nonempty_check check (length(btrim(source_message_id)) > 0),
  constraint support_requests_protocol_format_check check (protocol_number ~ '^FNX-[0-9]{8}-[0-9]{8}$')
);

comment on table public.support_requests is
  'Private support/DSR/security protocol ledger. Full email bodies remain in the source mailbox by default.';

create table if not exists public.support_request_events (
  id bigint generated always as identity primary key,
  support_request_id uuid not null references public.support_requests(id) on delete restrict,
  event_type text not null,
  from_status text,
  to_status text,
  event_summary text,
  source_reference text,
  created_at timestamptz not null default now(),
  constraint support_request_events_event_type_check check (event_type in ('RECEIVED','TRIAGE_UPDATED','STATUS_CHANGED','DRAFT_PREPARED','FOLLOWUP_DUE','NOTE','RESOLUTION_RECORDED')),
  constraint support_request_events_from_status_check check (from_status is null or from_status in ('RECEIVED','TRIAGED','NEEDS_ACTION','WAITING_REQUESTER','RESOLVED','CLOSED')),
  constraint support_request_events_to_status_check check (to_status is null or to_status in ('RECEIVED','TRIAGED','NEEDS_ACTION','WAITING_REQUESTER','RESOLVED','CLOSED'))
);

create index if not exists support_requests_status_received_idx
  on public.support_requests(status, received_at);

create index if not exists support_requests_category_received_idx
  on public.support_requests(category, received_at);

create index if not exists support_request_events_request_created_idx
  on public.support_request_events(support_request_id, created_at);

alter table public.support_requests enable row level security;
alter table public.support_request_events enable row level security;

-- No anon/authenticated policies are intentionally created.
-- service_role bypasses RLS and is the only intended caller for ingestion/operations.

create or replace function public.support_ingest_email_v1(
  p_source_message_id text,
  p_requester_email text,
  p_subject text,
  p_category text default 'OTHER',
  p_triage_summary text default null,
  p_attention_security boolean default false,
  p_attention_privacy boolean default false,
  p_received_at timestamptz default now()
)
returns table (
  request_id uuid,
  protocol_number text,
  created_new boolean
)
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_existing public.support_requests%rowtype;
  v_protocol text;
  v_request_id uuid;
begin
  if p_source_message_id is null or length(btrim(p_source_message_id)) = 0 then
    raise exception 'source_message_id_required';
  end if;
  if p_requester_email is null or length(btrim(p_requester_email)) <= 2 then
    raise exception 'requester_email_required';
  end if;
  if p_category not in ('SUPPORT','BILLING','PRIVACY_DATA','SECURITY','OTHER') then
    raise exception 'invalid_category';
  end if;

  select * into v_existing
  from public.support_requests
  where source_message_id = p_source_message_id;

  if found then
    return query select v_existing.id, v_existing.protocol_number, false;
    return;
  end if;

  v_protocol := 'FNX-' || to_char((p_received_at at time zone 'UTC')::date, 'YYYYMMDD') || '-' ||
    lpad(nextval('public.fitnexus_support_protocol_seq')::text, 8, '0');

  insert into public.support_requests (
    protocol_number,
    source_channel,
    source_message_id,
    requester_email,
    subject,
    category,
    status,
    triage_summary,
    attention_security,
    attention_privacy,
    received_at
  ) values (
    v_protocol,
    'EMAIL',
    btrim(p_source_message_id),
    lower(btrim(p_requester_email)),
    coalesce(p_subject, ''),
    p_category,
    'RECEIVED',
    nullif(btrim(coalesce(p_triage_summary, '')), ''),
    p_attention_security,
    p_attention_privacy,
    p_received_at
  )
  returning id into v_request_id;

  insert into public.support_request_events (
    support_request_id,
    event_type,
    to_status,
    event_summary,
    source_reference
  ) values (
    v_request_id,
    'RECEIVED',
    'RECEIVED',
    'Request ingested from authorized email channel.',
    btrim(p_source_message_id)
  );

  return query select v_request_id, v_protocol, true;
end;
$$;

create or replace function public.support_record_event_v1(
  p_protocol_number text,
  p_event_type text,
  p_to_status text default null,
  p_event_summary text default null,
  p_source_reference text default null
)
returns void
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_request public.support_requests%rowtype;
begin
  select * into v_request
  from public.support_requests
  where protocol_number = p_protocol_number
  for update;

  if not found then
    raise exception 'protocol_not_found';
  end if;

  if p_event_type not in ('TRIAGE_UPDATED','STATUS_CHANGED','DRAFT_PREPARED','FOLLOWUP_DUE','NOTE','RESOLUTION_RECORDED') then
    raise exception 'invalid_event_type';
  end if;

  if p_to_status is not null and p_to_status not in ('RECEIVED','TRIAGED','NEEDS_ACTION','WAITING_REQUESTER','RESOLVED','CLOSED') then
    raise exception 'invalid_status';
  end if;

  insert into public.support_request_events (
    support_request_id,
    event_type,
    from_status,
    to_status,
    event_summary,
    source_reference
  ) values (
    v_request.id,
    p_event_type,
    v_request.status,
    p_to_status,
    nullif(btrim(coalesce(p_event_summary, '')), ''),
    nullif(btrim(coalesce(p_source_reference, '')), '')
  );

  if p_to_status is not null then
    update public.support_requests
    set status = p_to_status,
        triaged_at = case when p_to_status = 'TRIAGED' and triaged_at is null then now() else triaged_at end,
        resolved_at = case when p_to_status = 'RESOLVED' and resolved_at is null then now() else resolved_at end,
        closed_at = case when p_to_status = 'CLOSED' and closed_at is null then now() else closed_at end,
        updated_at = now()
    where id = v_request.id;
  else
    update public.support_requests
    set updated_at = now()
    where id = v_request.id;
  end if;
end;
$$;

revoke all on table public.support_requests from anon, authenticated;
revoke all on table public.support_request_events from anon, authenticated;
revoke all on sequence public.fitnexus_support_protocol_seq from anon, authenticated;
revoke all on function public.support_ingest_email_v1(text,text,text,text,text,boolean,boolean,timestamptz) from public, anon, authenticated;
revoke all on function public.support_record_event_v1(text,text,text,text,text) from public, anon, authenticated;

grant execute on function public.support_ingest_email_v1(text,text,text,text,text,boolean,boolean,timestamptz) to service_role;
grant execute on function public.support_record_event_v1(text,text,text,text,text) to service_role;
