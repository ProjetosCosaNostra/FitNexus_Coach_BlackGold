-- Support Ops service-role synthetic idempotency proof V1.
-- REPOSITORY-ONLY CANDIDATE. DO NOT APPLY REMOTELY FROM operations/.
-- Promotion to migrations/ and remote execution require separate gated approval.
-- Synthetic-only: no customer identity, Gmail mutation, outbound email, billing, Terms, or deployment.

-- Fail closed on the privilege boundary before entering service_role.
do $$
begin
  if not has_function_privilege(
    'service_role',
    'public.support_ingest_email_v1(text,text,text,text,text,boolean,boolean,timestamptz)',
    'EXECUTE'
  ) then
    raise exception using errcode = 'P0001', message = 'SUPPORT_OPS_IDEMPOTENCY_SERVICE_ROLE_INGEST_EXECUTE_MISSING';
  end if;

  if not has_function_privilege(
    'service_role',
    'public.support_record_event_v1(text,text,text,text,text)',
    'EXECUTE'
  ) then
    raise exception using errcode = 'P0001', message = 'SUPPORT_OPS_IDEMPOTENCY_SERVICE_ROLE_RECORD_EXECUTE_MISSING';
  end if;

  if has_function_privilege(
      'anon',
      'public.support_ingest_email_v1(text,text,text,text,text,boolean,boolean,timestamptz)',
      'EXECUTE'
    )
    or has_function_privilege(
      'authenticated',
      'public.support_ingest_email_v1(text,text,text,text,text,boolean,boolean,timestamptz)',
      'EXECUTE'
    )
    or has_function_privilege(
      'public',
      'public.support_ingest_email_v1(text,text,text,text,text,boolean,boolean,timestamptz)',
      'EXECUTE'
    )
  then
    raise exception using errcode = 'P0001', message = 'SUPPORT_OPS_IDEMPOTENCY_INGEST_PUBLIC_BOUNDARY_DRIFT';
  end if;

  if has_function_privilege(
      'anon',
      'public.support_record_event_v1(text,text,text,text,text)',
      'EXECUTE'
    )
    or has_function_privilege(
      'authenticated',
      'public.support_record_event_v1(text,text,text,text,text)',
      'EXECUTE'
    )
    or has_function_privilege(
      'public',
      'public.support_record_event_v1(text,text,text,text,text)',
      'EXECUTE'
    )
  then
    raise exception using errcode = 'P0001', message = 'SUPPORT_OPS_IDEMPOTENCY_RECORD_PUBLIC_BOUNDARY_DRIFT';
  end if;
end;
$$;

-- Execute the exact RPC surface under the actual database service_role.
set local role service_role;

do $$
declare
  v_marker constant text := 'fitnexus-support-ops-idempotency-v1';
  v_email constant text := 'synthetic-support-ops-idempotency@invalid.example';
  v_subject constant text := '[SYNTHETIC] Support Ops service-role idempotency proof';
  v_received_at constant timestamptz := '2026-08-28T09:30:00Z'::timestamptz;
  v_id_first uuid;
  v_protocol_first text;
  v_created_first boolean;
  v_id_second uuid;
  v_protocol_second text;
  v_created_second boolean;
begin
  if current_user <> 'service_role' then
    raise exception using errcode = 'P0001', message = 'SUPPORT_OPS_IDEMPOTENCY_NOT_RUNNING_AS_SERVICE_ROLE';
  end if;

  select request_id, protocol_number, created_new
    into v_id_first, v_protocol_first, v_created_first
    from public.support_ingest_email_v1(
      v_marker,
      v_email,
      v_subject,
      'SUPPORT',
      'Synthetic service-role idempotency proof. No customer data.',
      false,
      false,
      v_received_at
    );

  if v_created_first is not true or v_id_first is null or v_protocol_first is null then
    raise exception using errcode = 'P0001', message = 'SUPPORT_OPS_IDEMPOTENCY_FIRST_INGEST_NOT_CREATED';
  end if;

  select request_id, protocol_number, created_new
    into v_id_second, v_protocol_second, v_created_second
    from public.support_ingest_email_v1(
      v_marker,
      v_email,
      v_subject,
      'SUPPORT',
      'Synthetic service-role idempotency proof. No customer data.',
      false,
      false,
      v_received_at
    );

  if v_created_second is not false then
    raise exception using errcode = 'P0001', message = 'SUPPORT_OPS_IDEMPOTENCY_SECOND_INGEST_CREATED_DUPLICATE';
  end if;

  if v_id_second is distinct from v_id_first
     or v_protocol_second is distinct from v_protocol_first then
    raise exception using errcode = 'P0001', message = 'SUPPORT_OPS_IDEMPOTENCY_SECOND_INGEST_IDENTITY_DRIFT';
  end if;

  perform public.support_record_event_v1(
    v_protocol_first,
    'STATUS_CHANGED',
    'TRIAGED',
    'Synthetic service-role idempotency proof transition.',
    v_marker
  );
end;
$$;

reset role;

-- Privileged postconditions and same-migration cleanup. No synthetic request survives.
do $$
declare
  v_marker constant text := 'fitnexus-support-ops-idempotency-v1';
  v_request_id uuid;
  v_protocol text;
  v_status text;
  v_email text;
  v_request_count bigint;
  v_event_count bigint;
begin
  select count(*)
    into v_request_count
    from public.support_requests
   where source_message_id = v_marker;

  if v_request_count <> 1 then
    raise exception using errcode = 'P0001', message = 'SUPPORT_OPS_IDEMPOTENCY_REQUEST_CARDINALITY_FAILED';
  end if;

  select id, protocol_number, status, requester_email
    into v_request_id, v_protocol, v_status, v_email
    from public.support_requests
   where source_message_id = v_marker;

  if v_status <> 'TRIAGED'
     or v_email <> 'synthetic-support-ops-idempotency@invalid.example'
     or v_protocol !~ '^FNX-20260828-[0-9]{8}$' then
    raise exception using errcode = 'P0001', message = 'SUPPORT_OPS_IDEMPOTENCY_REQUEST_POSTCONDITION_FAILED';
  end if;

  select count(*)
    into v_event_count
    from public.support_request_events
   where support_request_id = v_request_id;

  if v_event_count <> 2 then
    raise exception using errcode = 'P0001', message = 'SUPPORT_OPS_IDEMPOTENCY_EVENT_CARDINALITY_FAILED';
  end if;

  if (
    select count(*)
      from public.support_request_events
     where support_request_id = v_request_id
       and event_type = 'RECEIVED'
       and to_status = 'RECEIVED'
  ) <> 1 then
    raise exception using errcode = 'P0001', message = 'SUPPORT_OPS_IDEMPOTENCY_RECEIVED_EVENT_FAILED';
  end if;

  if (
    select count(*)
      from public.support_request_events
     where support_request_id = v_request_id
       and event_type = 'STATUS_CHANGED'
       and from_status = 'RECEIVED'
       and to_status = 'TRIAGED'
       and source_reference = v_marker
  ) <> 1 then
    raise exception using errcode = 'P0001', message = 'SUPPORT_OPS_IDEMPOTENCY_STATUS_EVENT_FAILED';
  end if;

  delete from public.support_request_events
   where support_request_id = v_request_id;

  delete from public.support_requests
   where id = v_request_id;

  if exists (
    select 1 from public.support_requests where source_message_id = v_marker
  ) or exists (
    select 1 from public.support_request_events where source_reference = v_marker
  ) then
    raise exception using errcode = 'P0001', message = 'SUPPORT_OPS_IDEMPOTENCY_SYNTHETIC_CLEANUP_FAILED';
  end if;
end;
$$;
