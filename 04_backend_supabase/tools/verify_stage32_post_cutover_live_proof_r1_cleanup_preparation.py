from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage32_post_cutover_live_proof_r1_cleanup_authority.json"
LEDGER = BACKEND / "migration_ledger_authority.json"
CLEANUP = BACKEND / "migrations" / "20260821222000_stage32_post_cutover_live_proof_r1_cleanup.sql"
R1_SEAL = BACKEND / "stage32_post_cutover_live_proof_r1_workflow_seal_authority.json"
R1_WORKFLOW = ROOT / ".github" / "workflows" / "stage32_post_cutover_edge_runtime_live_proof_r1.yml"

STATE = "POST_CUTOVER_EDGE_RUNTIME_PROOF_R1_VERIFIED_CLEANUP_COMPLETE_ROLLBACK_PROOF_PENDING_EDGE_MODE"
CLEANUP_NAME = "stage32_post_cutover_live_proof_r1_cleanup"
CLEANUP_VERSION = "20260821222724"
CLEANUP_FAILURE = "BGF-STAGE32-POST-CUTOVER-R1-CLEANUP-239"
EVENT_FAILURE = "BGF-GITHUB-R1-READY-EVENT-NONMATERIALIZATION-238"
PROOF_RUN = 32532170382
PROOF_JOB = 96926178484
PROOF_HEAD = "344433bf502b519563fe328ab71e59249766e3dd"
TRIGGER_HEAD = "65e35282aa0e004134807553545e0859512cdef6"
BASELINE = "62809bbd4f27d0616110dae19024b163a4911521"
LEDGER_OBSERVED = "2026-08-21T22:27:43.951028Z"
PROOF_WINDOW = "2026-08-21 22:15:00+00"
CLEANUP_FILE_SHA = "6e18eb6d497b75b710b0bca5784c755ca6312980"


def fail(message: str, failure_class: str = CLEANUP_FAILURE) -> None:
    raise SystemExit(
        "STAGE32_POST_CUTOVER_LIVE_PROOF_R1_CLEANUP_RECONCILIATION_GUARD=FAIL\n"
        f"FAILURE_CLASS={failure_class}\nDETAIL={message}"
    )


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to read {path.relative_to(ROOT)}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"expected JSON object: {path.relative_to(ROOT)}")
    return value


def text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"unable to read {path.relative_to(ROOT)}: {type(exc).__name__}")
    raise AssertionError("unreachable")


def require(mapping: dict, expected: dict, label: str) -> None:
    for key, value in expected.items():
        if mapping.get(key) != value:
            fail(f"{label} drift: {key}")


def main() -> None:
    authority = load(AUTHORITY)
    ledger = load(LEDGER)
    cleanup_sql = text(CLEANUP)
    seal = load(R1_SEAL)
    workflow = text(R1_WORKFLOW)

    require(
        authority,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "stage": "STAGE32_POST_CUTOVER_LIVE_PROOF_R1_CLEANUP",
            "baseline_main_sha": BASELINE,
            "current_state": STATE,
        },
        "current R1 cleanup authority",
    )
    failure_ids = {
        item.get("id")
        for item in authority.get("failure_classes", [])
        if isinstance(item, dict)
    }
    if {EVENT_FAILURE, CLEANUP_FAILURE} - failure_ids:
        fail("R1 cleanup/event-delivery prevention classes disappeared")

    require(
        authority.get("sealed_proof", {}),
        {
            "workflow_run_id": PROOF_RUN,
            "workflow_job_id": PROOF_JOB,
            "run_attempt": 1,
            "result": "PASS",
            "proof_pr": 77,
            "proof_head_sha": PROOF_HEAD,
            "fallback_trigger_pr": 79,
            "fallback_trigger_head_sha": TRIGGER_HEAD,
            "proof_pr_closed_unmerged": True,
            "fallback_trigger_pr_closed_unmerged": True,
            "proof_reexecution_allowed": False,
            "candidate_guard_passed": True,
            "exact_proof_head_checkout_verified": True,
            "shared_preferences_mock_verified": True,
            "production_singleton_verified": True,
            "production_edge_mode_verified": True,
            "get_workout_verified": True,
            "start_workout_verified": True,
            "set_completion_verified": True,
            "get_feedback_context_verified": True,
            "submit_feedback_verified": True,
            "all_five_routes_verified": True,
            "route_count": 5,
            "raw_synthetic_token_printed": False,
            "real_customer_data_used": False,
            "production_transport_changed": False,
            "automatic_edge_to_direct_fallback": False,
            "direct_rpc_grants_changed": False,
            "direct_rpc_execute_revoked": False,
            "cleanup_required": True,
            "post_cutover_rollback_proof_required": True,
            "launch_gate_promotion": False,
        },
        "sealed R1 proof receipt",
    )

    require(
        authority.get("event_delivery_receipt", {}),
        {
            "preferred_event": "ready_for_review",
            "preferred_event_delivered_on_pr": 77,
            "new_r1_workflow_materialized_on_preferred_event": False,
            "fallback_event": "opened",
            "fallback_pr": 79,
            "fallback_head_sha": TRIGGER_HEAD,
            "new_r1_workflow_materialized_on_fallback": True,
            "proof_head_changed_for_fallback": False,
            "fallback_merge_allowed": False,
        },
        "R1 event delivery receipt",
    )

    pre_cleanup = authority.get("pre_cleanup_receipt", {})
    require(
        pre_cleanup,
        {
            "source": "Supabase.execute_sql",
            "observed_at_utc": "2026-08-21T22:26:45.993106Z",
            "source_main_sha": BASELINE,
            "auth_users": 1,
            "profiles": 1,
            "organizations": 1,
            "organization_members": 1,
            "organization_subscriptions": 1,
            "subscription_authority_events": 1,
            "students": 1,
            "training_plans": 1,
            "training_exercises": 1,
            "access_links": 1,
            "workout_sessions": 1,
            "workout_logs": 1,
            "workout_feedback": 1,
            "expected_student": 1,
            "expected_session": 1,
            "expected_log": 1,
            "expected_feedback": 1,
            "command_receipts": 3,
            "link_rate_buckets": 5,
            "security_events": 3,
            "security_signals": 0,
            "growth_events": 5,
            "growth_attribution": 0,
            "proof_network_buckets": 5,
            "rpc_count": 5,
            "all_five_anon_execute_intact": True,
            "all_five_authenticated_execute_intact": True,
        },
        "pre-cleanup receipt",
    )

    cleanup = authority.get("cleanup", {})
    require(
        cleanup,
        {
            "migration_file": "04_backend_supabase/migrations/20260821222000_stage32_post_cutover_live_proof_r1_cleanup.sql",
            "migration_name": CLEANUP_NAME,
            "migration_ledger_state": "remote_reconciled",
            "remote_applied": True,
            "remote_version": CLEANUP_VERSION,
            "failure_class": CLEANUP_FAILURE,
            "requires_exact_proof_receipt": True,
            "requires_exact_single_synthetic_customer_domain": True,
            "requires_exact_three_command_receipts": True,
            "requires_exact_five_link_rate_buckets": True,
            "requires_exact_three_allowed_security_events": True,
            "requires_zero_security_signals": True,
            "requires_exact_five_growth_events": True,
            "requires_exact_five_global_network_buckets_in_proof_window": True,
            "deletes_raw_network_origin_or_hash": False,
            "security_events_deleted_before_link_cascade": True,
            "cleanup_must_be_applied_via": "Supabase.apply_migration",
            "cleanup_completed": True,
        },
        "cleanup authority",
    )

    remote_receipt = authority.get("cleanup_remote_receipt", {})
    require(
        remote_receipt,
        {
            "source": "Supabase.apply_migration",
            "source_main_sha": BASELINE,
            "source_file": "04_backend_supabase/migrations/20260821222000_stage32_post_cutover_live_proof_r1_cleanup.sql",
            "source_file_sha": CLEANUP_FILE_SHA,
            "migration_name": CLEANUP_NAME,
            "remote_version": CLEANUP_VERSION,
            "pre_apply_observed_at_utc": "2026-08-21T22:26:45.993106Z",
            "apply_result": "SUCCESS",
            "post_apply_observed_at_utc": LEDGER_OBSERVED,
            "auth_users": 0,
            "profiles": 0,
            "organizations": 0,
            "organization_members": 0,
            "organization_subscriptions": 0,
            "subscription_authority_events": 0,
            "students": 0,
            "training_plans": 0,
            "training_exercises": 0,
            "access_links": 0,
            "workout_sessions": 0,
            "workout_logs": 0,
            "workout_feedback": 0,
            "fixture_growth_events": 0,
            "fixture_growth_attribution": 0,
            "fixture_command_receipts": 0,
            "fixture_link_rate_buckets": 0,
            "fixture_security_events": 0,
            "fixture_security_signals": 0,
            "proof_network_buckets_remaining": 0,
            "global_network_buckets_total": 13,
            "rpc_count": 5,
            "all_five_anon_execute_intact": True,
            "all_five_authenticated_execute_intact": True,
            "direct_rpc_grants_changed": False,
            "real_customer_data_used": False,
            "cleanup_exact_synthetic_residue_zero": True,
        },
        "cleanup remote receipt",
    )

    repo_only = [
        row for row in ledger.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    ]
    if repo_only:
        fail("cleanup remains repo_only after authoritative remote apply")
    remote = {
        row.get("name"): row.get("version")
        for row in ledger.get("remote_migrations", []) if isinstance(row, dict)
    }
    expected_remote = {
        "stage32_post_cutover_edge_runtime_fixture": "20260821171334",
        "stage32_rearm_expired_fixture_r1": "20260821214005",
        CLEANUP_NAME: CLEANUP_VERSION,
    }
    for name, version in expected_remote.items():
        if remote.get(name) != version:
            fail(f"remote migration receipt drift: {name}")
    if ledger.get("baseline_main_sha") != BASELINE or ledger.get("observed_at_utc") != LEDGER_OBSERVED:
        fail("cleanup remote ledger baseline/observation drifted")

    for fragment in (
        CLEANUP_FAILURE,
        "32532170382",
        "STAGE32_R1_CLEANUP_CUSTOMER_DOMAIN_NO_LONGER_EXACT_SYNTHETIC_PROOF",
        "STAGE32_R1_CLEANUP_FIXTURE_IDENTITY_MISMATCH",
        "STAGE32_R1_CLEANUP_LIVE_PROOF_BUSINESS_RECEIPT_DRIFT",
        "STAGE32_R1_CLEANUP_COMMAND_RECEIPT_DRIFT",
        "STAGE32_R1_CLEANUP_LINK_RATE_BUCKET_DRIFT",
        "STAGE32_R1_CLEANUP_SECURITY_RECEIPT_DRIFT",
        "STAGE32_R1_CLEANUP_GROWTH_RECEIPT_DRIFT",
        "STAGE32_R1_CLEANUP_UNEXPECTED_SYNTHETIC_DOMAIN_MUTATION",
        "STAGE32_R1_CLEANUP_NETWORK_BUCKET_SELECTOR_MISMATCH",
        "STAGE32_R1_CLEANUP_NETWORK_BUCKET_DELETE_COUNT_MISMATCH",
        "STAGE32_R1_CLEANUP_SECURITY_EVENT_DELETE_COUNT_MISMATCH",
        "STAGE32_R1_CLEANUP_POSTCONDITION_FAILED",
        "29721756-f091-4b33-9106-82a253e9f9c8",
        "07df75e0-36f2-4ce3-b090-4d72261e0717",
        "58972689-2208-4ee0-ab34-8ebe75c0f6cb",
        PROOF_WINDOW,
        "32000000000000000000000000000001",
        "32000000000000000000000000000002",
        "32000000000000000000000000000003",
    ):
        if fragment not in cleanup_sql:
            fail(f"cleanup SQL drift: {fragment}")
    lower = cleanup_sql.lower()
    if "origin_hash" in lower:
        fail("cleanup SQL embedded a network-origin hash selector")
    if lower.count("delete from private.student_access_network_rate_buckets") != 1:
        fail("cleanup must delete global network buckets exactly once")
    security_pos = lower.find("delete from private.student_access_security_events")
    org_pos = lower.find("delete from public.organizations")
    if security_pos < 0 or org_pos < 0 or security_pos > org_pos:
        fail("security events are not deleted before organization/link cascade")

    require(
        seal.get("proof_pr", {}),
        {"number": 77, "head_sha": PROOF_HEAD, "merge_allowed": False, "candidate_ci_conclusion": "success"},
        "immutable R1 proof seal",
    )
    require(
        seal.get("open_trigger", {}),
        {"head_sha": TRIGGER_HEAD, "merge_allowed": False},
        "immutable R1 fallback seal",
    )
    for fragment in (PROOF_HEAD, TRIGGER_HEAD, "github.run_attempt == 1", "PROOF_REEXECUTION_ALLOWED=false"):
        if fragment not in workflow:
            fail(f"sealed R1 workflow drift: {fragment}")

    require(
        authority.get("production_boundary", {}),
        {
            "active_transport": "edgeGateway",
            "production_singleton": "StudentAccessTransport.instance",
            "automatic_edge_to_direct_fallback": False,
            "direct_rpc_execute_revoked": False,
            "post_cutover_live_proof_verified": True,
            "post_cutover_cleanup_verified": True,
            "post_cutover_rollback_verified": False,
            "launch_gate_promotion": False,
        },
        "production boundary",
    )

    rules = authority.get("promotion_rules", {})
    for key in (
        "may_reexecute_r0_proof",
        "may_reexecute_r1_proof",
        "may_reapply_cleanup",
        "may_use_execute_sql_for_cleanup_dml",
        "may_revoke_direct_rpc_execute_before_post_cutover_rollback_proof",
        "may_promote_launch_gates",
    ):
        if rules.get(key) is not False:
            fail(f"cleanup authority gained prohibited permission: {key}")
    if rules.get("post_cutover_rollback_proof_required_after_cleanup") is not True:
        fail("post-cutover rollback interlock disappeared")

    require(
        authority.get("next_stage", {}),
        {
            "name": "PREPARE_REAL_POST_CUTOVER_ROLLBACK_PROOF",
            "allowed_now": True,
            "requires_cleanup_remote_reconciled": True,
            "requires_zero_stage32_synthetic_residue": True,
            "requires_new_isolated_rollback_fixture": True,
            "requires_new_exact_rollback_proof_head": True,
            "requires_new_one_shot_rollback_workflow_seal": True,
            "requires_fresh_direct_rpc_grant_check_before_rollback_fixture_apply": True,
            "requires_production_edge_gateway_before_rollback_proof": True,
            "may_execute_stage32_live_proof_again": False,
            "may_reapply_cleanup": False,
            "may_revoke_direct_rpc_execute_now": False,
            "may_promote_launch_gates": False,
        },
        "next-stage authority",
    )

    print("STAGE32_POST_CUTOVER_LIVE_PROOF_R1_CLEANUP_RECONCILIATION_GUARD=PASS")
    print(f"CURRENT_STATE={STATE}")
    print(f"PROOF_RUN={PROOF_RUN}")
    print(f"PROOF_JOB={PROOF_JOB}")
    print("ALL_FIVE_ROUTES_VERIFIED=true")
    print("PROOF_REEXECUTION_ALLOWED=false")
    print(f"CLEANUP_REMOTE_VERSION={CLEANUP_VERSION}")
    print("CLEANUP_COMPLETED=true")
    print("STAGE32_SYNTHETIC_RESIDUE=0")
    print("PRODUCTION_ACTIVE_TRANSPORT=edgeGateway")
    print("DIRECT_RPC_GRANTS=INTACT")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")
    print("POST_CUTOVER_ROLLBACK_PROOF_REQUIRED=true")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
