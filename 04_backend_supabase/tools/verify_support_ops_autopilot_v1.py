#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "04_backend_supabase/operations/SUPPORT_OPS_AUTOPILOT_V1_CONTRACT.json"
MIGRATION = ROOT / "04_backend_supabase/operations/candidates/SUPPORT_OPS_PROTOCOL_CANDIDATE.sql"
ENGINE = ROOT / "04_backend_supabase/tools/support_ops_autopilot_v1.py"
OPEN_DECISIONS = ROOT / "10_compliance/drafts/COMPLIANCE_OPEN_DECISIONS.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    sql = MIGRATION.read_text(encoding="utf-8")
    engine = ENGINE.read_text(encoding="utf-8")
    decisions = json.loads(OPEN_DECISIONS.read_text(encoding="utf-8"))

    require(contract["public_contact"] == "projetoscosanostra@gmail.com", "public contact drift")
    require(contract["state"] == "SOURCE_PREPARED_NOT_REMOTE_APPLIED_NOT_OPERATIONAL_EVIDENCE", "state must remain non-attesting")
    require(contract["deployment_boundary"]["remote_supabase_apply_allowed_by_this_contract"] is False, "remote apply must stay denied")
    require(contract["deployment_boundary"]["gmail_mutation_allowed_by_this_contract"] is False, "gmail mutation must stay denied")
    require(contract["response_model"]["automatic_send_allowed"] is False, "automatic send must stay denied")
    require(contract["commercial_progress"]["credit_percent_points"] == 0, "source prep cannot raise commercial readiness")
    require(contract["data_minimization"]["gmail_remains_source_of_truth_for_full_message_body"] is True, "full body minimization required")

    required_sql = (
        "create sequence if not exists public.fitnexus_support_protocol_seq",
        "create table if not exists public.support_requests",
        "create table if not exists public.support_request_events",
        "source_message_id text not null unique",
        "alter table public.support_requests enable row level security",
        "alter table public.support_request_events enable row level security",
        "security definer",
        "support_ingest_email_v1",
        "support_record_event_v1",
        "revoke all on table public.support_requests from anon, authenticated",
        "grant execute on function public.support_ingest_email_v1",
        "to service_role",
    )
    lowered = sql.lower()
    for marker in required_sql:
        require(marker.lower() in lowered, f"missing SQL marker: {marker}")

    forbidden_sql = (
        "grant select on public.support_requests to anon",
        "grant select on public.support_requests to authenticated",
        "grant execute on function public.support_ingest_email_v1(text,text,text,text,text,boolean,boolean,timestamptz) to anon",
        "grant execute on function public.support_ingest_email_v1(text,text,text,text,text,boolean,boolean,timestamptz) to authenticated",
    )
    for marker in forbidden_sql:
        require(marker not in lowered, f"unsafe SQL grant present: {marker}")

    require('"full_message_body_persisted": False' in engine, "engine must omit full body")
    require('"send_authorized": False' in engine, "engine must not authorize outbound send")
    require("--self-test" in engine, "engine self-test missing")

    open_map = {item["id"]: item["state"] for item in decisions["unresolved"]}
    require(open_map.get("DSR_STABLE_PUBLIC_ROUTE") == "OPEN", "DSR route must remain OPEN until production evidence")
    require(open_map.get("DSR_CONTROLLED_TESTS") == "OPEN", "DSR tests must remain OPEN")

    print("SUPPORT_OPS_AUTOPILOT_V1_CONTRACT=PASS")
    print("CANDIDATE_SQL_LOCATION=OPERATIONS_NOT_MIGRATIONS_LEDGER")
    print("REMOTE_APPLY_ALLOWED=false")
    print("AUTOMATIC_SEND_ALLOWED=false")
    print("DSR_STABLE_PUBLIC_ROUTE=OPEN")
    print("COMMERCIAL_PROGRESS_CREDIT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
