-- Read-only Stage 24 operational probe.
-- This file never creates evidence for the external incident_response gate.

select
  posture,
  evaluated_at,
  signals_60m,
  rate_limit_burst_signals_60m,
  command_replay_burst_signals_60m,
  token_rotation_burst_signals_60m,
  security_events_15m,
  rate_limited_events_15m,
  replay_events_15m
from private.student_access_security_posture_v1;

select
  signal_type,
  severity,
  count(*) as signals,
  max(last_seen_at) as last_seen_at
from private.student_access_security_signals
where last_seen_at >= now() - interval '24 hours'
group by signal_type, severity
order by signal_type, severity;

select
  count(*) filter (where outcome = 'rate_limited' and occurred_at >= now() - interval '60 minutes') as rate_limited_60m,
  count(*) filter (where outcome = 'replay' and occurred_at >= now() - interval '60 minutes') as replay_60m,
  count(*) filter (where outcome = 'rotated' and occurred_at >= now() - interval '60 minutes') as rotated_60m,
  count(distinct link_id) filter (where occurred_at >= now() - interval '60 minutes') as distinct_links_60m
from private.student_access_security_events;

select
  has_table_privilege('anon', 'private.student_access_security_signals', 'select') as anon_signal_select,
  has_table_privilege('authenticated', 'private.student_access_security_signals', 'select') as authenticated_signal_select,
  has_table_privilege('service_role', 'private.student_access_security_signals', 'select') as service_signal_select,
  has_table_privilege('service_role', 'private.student_access_security_posture_v1', 'select') as service_posture_select;
