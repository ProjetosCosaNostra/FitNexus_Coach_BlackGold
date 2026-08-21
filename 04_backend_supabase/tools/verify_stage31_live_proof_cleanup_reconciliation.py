from __future__ import annotations

import importlib
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "student_access_client_edge_runtime_proof_authority.json"
LEDGER = BACKEND / "migration_ledger_authority.json"
SEAL = BACKEND / "stage31_live_proof_workflow_seal_authority.json"
CLEANUP_SQL = BACKEND / "migrations" / "20260821121700_stage31_client_edge_runtime_cleanup.sql"

STATE_REPO = "CLIENT_EDGE_RUNTIME_PROOF_LIVE_VERIFIED_CLEANUP_REPO_ONLY_DIRECT_MODE"
STATE_CLEAN = "CLIENT_EDGE_RUNTIME_PROOF_LIVE_VERIFIED_CLEANUP_COMPLETE_DIRECT_MODE"
PRE_PROOF_STATE = "CLIENT_EDGE_RUNTIME_PROOF_FIXTURE_REMOTE_LIVE_PROOF_PENDING_DIRECT_MODE"
BASELINES = {
    STATE_REPO: "543d3d103d4656c0e4976829320d54f31c944eee",
    STATE_CLEAN: "05b44ebda7976c679ec8198260def688d1e203f8",
}
LEDGER_OBSERVED = {
    STATE_REPO: "2026-08-21T12:16:43Z",
    STATE_CLEAN: "2026-08-21T16:15:04Z",
}
PRE_PROOF_BASELINE = "669b5f4816aafcaf87647e4eaa98dd0a1bb43ffb"
FIXTURE_NAME = "stage31_client_edge_runtime_fixture"
FIXTURE_VERSION = "20260821113205"
CLEANUP_NAME = "stage31_client_edge_runtime_cleanup"
CLEANUP_VERSION = "20260821161224"
CLEANUP_CLASS = "BGF-STAGE31-CLIENT-EDGE-RUNTIME-CLEANUP-225"
DELIVERY_CLASS = "BGF-STAGE31-READY-FOR-REVIEW-EVENT-NONDELIVERY-224"
RUN_ID = 32480597745
JOB_ID = 96765899124
PROOF_HEAD = "b8be62be0ba36c61b9557bed03e72dc05b0a43f0"
TRIGGER_HEAD = "8f1c1933c5822d4a20abc8bb9260007f1a109cc3"
MODES = {"stage31", "rate_limit", "valid_route", "smoke", "rollback"}


def fail(message: str) -> None:
    raise SystemExit("STAGE31_LIVE_PROOF_CLEANUP_RECONCILIATION_GUARD=FAIL\n" + message)


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to read {path.relative_to(ROOT)}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"expected JSON object: {path.relative_to(ROOT)}")
    return value


def require(mapping: dict, expected: dict, label: str) -> None:
    for key, value in expected.items():
        if mapping.get(key) != value:
            fail(f"{label} drift: {key}")


def validate_current() -> tuple[dict, dict, str]:
    authority = load(AUTHORITY)
    ledger = load(LEDGER)
    seal = load(SEAL)
    sql = CLEANUP_SQL.read_text(encoding="utf-8")

    state = authority.get("current_state")
    if state not in BASELINES:
        fail(f"unsupported Stage 31 cleanup lifecycle state: {state}")

    require(
        authority,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "baseline_main_sha": BASELINES[state],
            "workflow_delivery_failure_class": DELIVERY_CLASS,
            "cleanup_failure_class": CLEANUP_CLASS,
        },
        "Stage 31 authority",
    )
    require(
        authority.get("production_boundary", {}),
        {
            "active_transport": "directRpc",
            "resolved_transport": "directRpc",
            "edge_gateway_selected": False,
            "flutter_uses_edge_gateway_in_production": False,
            "direct_v2_rpc_path_active": True,
            "direct_anon_v2_rpc_execute_revoked": False,
            "automatic_edge_to_direct_fallback": False,
            "client_cutover_verified": False,
            "behavioral_transport_change": False,
        },
        "production boundary",
    )
    require(
        authority.get("fixture", {}),
        {
            "migration_name": FIXTURE_NAME,
            "migration_ledger_state": "remote_reconciled",
            "remote_applied": True,
            "remote_version": FIXTURE_VERSION,
            "synthetic_only": True,
            "cleanup_required_after_proof": True,
        },
        "Stage 31 fixture",
    )

    cleanup_complete = state == STATE_CLEAN
    runtime_expected = {
        "workflow_run_id": RUN_ID,
        "workflow_job_id": JOB_ID,
        "result": "PASS",
        "proof_pr": 61,
        "proof_head": PROOF_HEAD,
        "trigger_pr": 64,
        "trigger_head": TRIGGER_HEAD,
        "trigger_pr_closed_unmerged_after_execution": True,
        "flutter_transport_edge_path_verified": True,
        "get_workout_verified": True,
        "start_workout_verified": True,
        "set_completion_verified": True,
        "get_feedback_context_verified": True,
        "submit_feedback_verified": True,
        "all_five_routes_verified": True,
        "synthetic_fixture_mutated_as_expected": True,
        "raw_token_returned": False,
        "raw_network_origin_returned": False,
        "real_customer_data_used": False,
        "real_customer_data_mutated": False,
        "proof_reexecution_allowed": False,
        "cleanup_completed": cleanup_complete,
    }
    if cleanup_complete:
        runtime_expected.update(
            {
                "synthetic_business_rows_remaining": 0,
                "synthetic_security_rows_remaining": 0,
                "synthetic_network_proof_rows_remaining": 0,
            }
        )
    require(authority.get("runtime_proof", {}), runtime_expected, "Stage 31 live proof receipt")

    require(
        authority.get("post_proof_database_receipt", {}),
        {
            "source": "Supabase.execute_sql",
            "observed_at_utc": "2026-08-21T12:13:33Z",
            "auth_users": 1,
            "profiles": 1,
            "organizations": 1,
            "organization_members": 1,
            "students": 1,
            "training_plans": 1,
            "training_exercises": 1,
            "access_links": 1,
            "workout_sessions": 1,
            "workout_logs": 1,
            "workout_feedback": 1,
            "command_receipts": 3,
            "link_rate_buckets": 5,
            "security_events": 3,
            "security_signals": 0,
            "growth_events": 5,
            "network_rate_buckets_in_proof_minute": 5,
            "real_customer_rows_detected": False,
        },
        "post-proof database receipt",
    )
    require(
        authority.get("proof_objects", {}),
        {
            "session_id": "b7555999-5d2c-4ee5-8ccd-faad53d77939",
            "exercise_log_id": "22b55e28-f217-4da0-aff3-d5dbaf937b89",
            "feedback_id": "20bb7e8c-9a1b-4f45-af41-6cf009142dea",
            "network_proof_window_utc": "2026-08-21T12:11:00Z",
            "command_ids": [
                "31000000000000000000000000000001",
                "31000000000000000000000000000002",
                "31000000000000000000000000000003",
            ],
        },
        "proof object receipt",
    )

    cleanup_expected = {
        "repository_file": "04_backend_supabase/migrations/20260821121700_stage31_client_edge_runtime_cleanup.sql",
        "migration_name": CLEANUP_NAME,
        "failure_class": CLEANUP_CLASS,
        "requires_exact_proof_receipt": True,
        "requires_synthetic_only_customer_domain": True,
        "raw_network_origin_selector_forbidden": True,
        "origin_digest_selector_forbidden": True,
        "cleanup_completed": cleanup_complete,
    }
    if cleanup_complete:
        cleanup_expected.update(
            {
                "migration_ledger_state": "remote_reconciled",
                "remote_applied": True,
                "remote_version": CLEANUP_VERSION,
            }
        )
    else:
        cleanup_expected.update(
            {
                "migration_ledger_state": "repo_only",
                "remote_applied": False,
                "remote_version": None,
            }
        )
    require(authority.get("cleanup", {}), cleanup_expected, "cleanup authority")

    if cleanup_complete:
        require(
            authority.get("cleanup_receipt", {}),
            {
                "source": "Supabase.execute_sql",
                "observed_at_utc": "2026-08-21T16:14:54Z",
                "migration_name": CLEANUP_NAME,
                "remote_version": CLEANUP_VERSION,
                "remote_applied": True,
                "result": "PASS",
                "auth_users_remaining": 0,
                "profiles_remaining": 0,
                "organizations_remaining": 0,
                "organization_members_remaining": 0,
                "organization_subscriptions_remaining": 0,
                "subscription_authority_events_remaining": 0,
                "students_remaining": 0,
                "training_plans_remaining": 0,
                "training_exercises_remaining": 0,
                "access_links_remaining": 0,
                "workout_sessions_remaining": 0,
                "workout_logs_remaining": 0,
                "workout_feedback_remaining": 0,
                "fixture_growth_events_remaining": 0,
                "fixture_growth_attribution_remaining": 0,
                "fixture_link_rate_buckets_remaining": 0,
                "fixture_command_receipts_remaining": 0,
                "fixture_security_events_remaining": 0,
                "fixture_security_signals_remaining": 0,
                "proof_network_buckets_remaining": 0,
                "raw_network_origin_read": False,
                "network_origin_digest_read": False,
                "migration_ledger_state": "remote_reconciled",
            },
            "cleanup completion receipt",
        )
        require(
            authority.get("next_stage", {}),
            {
                "name": "PREPARE_PRODUCTION_EDGE_TRANSPORT_SELECTION",
                "allowed_now": True,
                "requires_cleanup_complete": True,
                "requires_all_five_routes_cutover": True,
                "requires_no_automatic_edge_to_direct_fallback": True,
                "requires_direct_rpc_grants_intact": True,
                "may_revoke_direct_rpc_execute_now": False,
            },
            "post-cleanup frontier",
        )
    else:
        if "cleanup_receipt" in authority:
            fail("cleanup receipt appeared before remote cleanup")
        require(
            authority.get("next_stage", {}),
            {
                "name": "APPLY_STAGE31_CLIENT_EDGE_RUNTIME_CLEANUP",
                "allowed_now": True,
                "requires_ci_and_merge_first": True,
                "requires_exact_merged_sql": True,
                "requires_fresh_migration_ledger_check_immediately_before_apply": True,
                "may_select_edge_gateway_now": False,
                "may_revoke_direct_rpc_execute_now": False,
            },
            "Stage 31 cleanup frontier",
        )

    if any(value is not False for value in authority.get("launch_authority", {}).values()):
        fail("Stage 31 authority gained launch authority")

    require(
        seal.get("execution_receipt", {}),
        {
            "workflow_run_id": RUN_ID,
            "job_id": JOB_ID,
            "result": "SUCCESS",
            "executed": True,
            "run_attempt": 1,
            "proof_test_result": "ALL_TESTS_PASSED",
            "routes_verified": 5,
            "proof_head_checked_out": PROOF_HEAD,
            "raw_synthetic_token_printed": False,
            "production_transport_change": False,
            "edge_selection": False,
            "automatic_edge_to_direct_fallback": False,
            "direct_rpc_grants_changed": False,
            "real_customer_data_used": False,
            "launch_gate_promotion": False,
            "proof_reexecution_allowed": False,
            "cleanup_completed": False,
        },
        "historical workflow execution seal",
    )

    if ledger.get("baseline_main_sha") != BASELINES[state]:
        fail("migration ledger baseline drifted")
    if ledger.get("observed_at_utc") != LEDGER_OBSERVED[state]:
        fail("migration ledger observation timestamp drifted")
    remote = {
        row.get("name"): row.get("version")
        for row in ledger.get("remote_migrations", [])
        if isinstance(row, dict)
    }
    if remote.get(FIXTURE_NAME) != FIXTURE_VERSION:
        fail("Stage 31 fixture remote receipt disappeared from ledger")
    repo_only = [
        row
        for row in ledger.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    ]
    if cleanup_complete:
        if remote.get(CLEANUP_NAME) != CLEANUP_VERSION:
            fail("Stage 31 cleanup remote receipt missing")
        if repo_only:
            fail("Stage 31 cleanup reconciliation left a repo_only divergence")
    else:
        if CLEANUP_NAME in remote:
            fail("Stage 31 cleanup self-attested as remotely applied before merge/apply")
        if len(repo_only) != 1 or repo_only[0].get("name") != CLEANUP_NAME:
            fail("Stage 31 cleanup is not the unique repo_only migration divergence")
        if repo_only[0].get("related_failure_class") != CLEANUP_CLASS:
            fail("Stage 31 cleanup repo_only failure-class authority drifted")

    required_sql = (
        CLEANUP_CLASS,
        "STAGE31_CLEANUP_CUSTOMER_DOMAIN_NO_LONGER_SYNTHETIC_ONLY",
        "STAGE31_CLEANUP_FIXTURE_IDENTITY_MISMATCH",
        "STAGE31_CLEANUP_LIVE_PROOF_BUSINESS_RECEIPT_DRIFT",
        "STAGE31_CLEANUP_COMMAND_RECEIPT_DRIFT",
        "STAGE31_CLEANUP_LINK_RATE_BUCKET_DRIFT",
        "STAGE31_CLEANUP_SECURITY_RECEIPT_DRIFT",
        "STAGE31_CLEANUP_GROWTH_RECEIPT_DRIFT",
        "STAGE31_CLEANUP_UNEXPECTED_SYNTHETIC_DOMAIN_MUTATION",
        "STAGE31_CLEANUP_NETWORK_BUCKET_SELECTOR_MISMATCH",
        "STAGE31_CLEANUP_NETWORK_BUCKET_DELETE_COUNT_MISMATCH",
        "STAGE31_CLEANUP_POSTCONDITION_FAILED",
        "b7555999-5d2c-4ee5-8ccd-faad53d77939",
        "22b55e28-f217-4da0-aff3-d5dbaf937b89",
        "20bb7e8c-9a1b-4f45-af41-6cf009142dea",
        "2026-08-21 12:11:00+00",
        "31000000000000000000000000000001",
        "31000000000000000000000000000002",
        "31000000000000000000000000000003",
        "delete from private.student_access_network_rate_buckets",
        "delete from public.organizations where id = v_org",
        "delete from auth.users where id = v_user",
    )
    for fragment in required_sql:
        if fragment not in sql:
            fail(f"Stage 31 cleanup SQL drift: {fragment}")
    lowered = sql.lower()
    for forbidden in ("origin_hash", "cf-connecting-ip", "x-forwarded-for", "x-real-ip"):
        if forbidden in lowered:
            fail(f"Stage 31 cleanup embeds forbidden network-origin material: {forbidden}")
    if re.findall(r"(?<![0-9a-fA-F])[0-9a-fA-F]{64}(?![0-9a-fA-F])", sql):
        fail("Stage 31 cleanup contains a bearer-looking 64-hex literal")

    return authority, ledger, state


def pre_proof_authority_projection(current: dict) -> dict:
    value = json.loads(json.dumps(current))
    value["current_state"] = PRE_PROOF_STATE
    value["baseline_main_sha"] = PRE_PROOF_BASELINE
    value.pop("proof_guard_sentinel_failure_class", None)
    value.pop("workflow_seal_failure_class", None)
    value.pop("workflow_delivery_failure_class", None)
    value.pop("cleanup_failure_class", None)
    value.pop("post_proof_database_receipt", None)
    value.pop("proof_objects", None)
    value.pop("cleanup", None)
    value.pop("cleanup_receipt", None)
    value["runtime_proof"] = {
        "workflow_run_id": None,
        "result": None,
        "flutter_transport_edge_path_verified": False,
        "get_workout_verified": False,
        "start_workout_verified": False,
        "set_completion_verified": False,
        "get_feedback_context_verified": False,
        "submit_feedback_verified": False,
        "all_five_routes_verified": False,
        "raw_token_returned": False,
        "raw_network_origin_returned": False,
        "real_customer_data_used": False,
        "real_customer_data_mutated": False,
        "proof_reexecution_allowed": False,
        "cleanup_completed": False,
    }
    value["promotion_rules"] = {
        "may_apply_fixture_before_ci_and_merge": False,
        "may_execute_live_client_proof_before_fixture_remote_apply": False,
        "may_change_production_active_mode_during_preparation_or_proof": False,
        "may_select_edge_gateway_during_preparation_or_proof": False,
        "may_enable_automatic_edge_to_direct_fallback": False,
        "may_revoke_direct_rpc_execute_during_preparation_or_proof": False,
        "may_use_real_customer_data": False,
        "may_promote_launch_gates": False,
        "cleanup_required_before_any_edge_selection": True,
        "post_cutover_rollback_proof_still_required_before_direct_rpc_revocation": True,
    }
    value["next_stage"] = {
        "name": "PREPARE_STAGE31_CLIENT_EDGE_RUNTIME_LIVE_PROOF",
        "allowed_now": True,
        "requires_exact_pr_and_head_seal_before_first_execution": True,
        "requires_one_shot_workflow": True,
        "requires_fixture_remote_applied": True,
        "may_select_edge_gateway_now": False,
        "may_revoke_direct_rpc_execute_now": False,
    }
    return value


def pre_proof_ledger_projection(current: dict) -> dict:
    value = json.loads(json.dumps(current))
    value["baseline_main_sha"] = PRE_PROOF_BASELINE
    value["observed_at_utc"] = "2026-08-21T11:34:15Z"
    value["declared_divergences"] = [
        row
        for row in value.get("declared_divergences", [])
        if not (isinstance(row, dict) and row.get("direction") == "repo_only")
    ]
    value["remote_migrations"] = [
        row
        for row in value.get("remote_migrations", [])
        if not (isinstance(row, dict) and row.get("name") == CLEANUP_NAME)
    ]
    return value


def run(mode: str) -> None:
    if mode not in MODES:
        fail(f"unsupported mode: {mode}")
    authority, ledger, state = validate_current()

    with tempfile.TemporaryDirectory(prefix="fitnexus-stage31-post-proof-compat-") as tmp:
        temp_root = Path(tmp)
        temp_authority = temp_root / "student_access_client_edge_runtime_proof_authority.json"
        temp_ledger = temp_root / "migration_ledger_authority.json"
        temp_authority.write_text(
            json.dumps(pre_proof_authority_projection(authority), indent=2) + "\n",
            encoding="utf-8",
        )
        temp_ledger.write_text(
            json.dumps(pre_proof_ledger_projection(ledger), indent=2) + "\n",
            encoding="utf-8",
        )
        historical = importlib.import_module("verify_stage31_fixture_remote_reconciliation")
        historical.AUTHORITY = temp_authority
        historical.LEDGER = temp_ledger
        historical.run(mode)

    cleanup_complete = state == STATE_CLEAN
    print("STAGE31_LIVE_PROOF_CLEANUP_RECONCILIATION_GUARD=PASS")
    print(f"MODE={mode}")
    print(f"CURRENT_STATE={state}")
    print(f"WORKFLOW_RUN_ID={RUN_ID}")
    print(f"WORKFLOW_JOB_ID={JOB_ID}")
    print("FLUTTER_EDGE_ROUTES_VERIFIED=5")
    print("PROOF_REEXECUTION_ALLOWED=false")
    print("CLEANUP_LEDGER=" + ("REMOTE_RECONCILED" if cleanup_complete else "REPO_ONLY"))
    print("CLEANUP_REMOTE_APPLIED=" + str(cleanup_complete).lower())
    print("SYNTHETIC_RESIDUE=" + ("ZERO" if cleanup_complete else "CONTROLLED_PENDING"))
    print("PRODUCTION_ACTIVE_TRANSPORT=directRpc")
    print("EDGE_SELECTION=false")
    print("AUTOMATIC_EDGE_TO_DIRECT_FALLBACK=false")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")
    print(
        "NEXT="
        + (
            "PREPARE_PRODUCTION_EDGE_TRANSPORT_SELECTION"
            if cleanup_complete
            else "APPLY_STAGE31_CLIENT_EDGE_RUNTIME_CLEANUP_AFTER_CI_AND_MERGE"
        )
    )
    print("LAUNCH_GATE_PROMOTION=DENIED")


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: verify_stage31_live_proof_cleanup_reconciliation.py <stage31|rate_limit|valid_route|smoke|rollback>")
    run(sys.argv[1])


if __name__ == "__main__":
    main()
