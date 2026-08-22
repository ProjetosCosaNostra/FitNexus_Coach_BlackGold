from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
APP = ROOT / "03_app_flutter" / "fitnexus_app"
AUTHORITY = BACKEND / "stage32_post_cutover_rollback_proof_authority.json"
LEDGER = BACKEND / "migration_ledger_authority.json"
CLEANUP = BACKEND / "migrations" / "20260822002500_stage32_post_cutover_rollback_proof_cleanup.sql"
CONTRACT = APP / "lib" / "features" / "student" / "student_access_transport_contract.dart"
TRANSPORT = APP / "lib" / "features" / "student" / "student_access_transport.dart"

STATE = "POST_CUTOVER_ROLLBACK_PROOF_VERIFIED_CLEANUP_COMPLETE_EDGE_MODE"
FAILURE_CLASS = "BGF-STAGE32-POST-CUTOVER-ROLLBACK-CLEANUP-244"
CLEANUP_NAME = "stage32_post_cutover_rollback_proof_cleanup"
CLEANUP_VERSION = "20260822003559"
BASELINE = "0e7324c47771be2c9c66e3c7bbf05481abea41aa"
OBSERVED = "2026-08-22T00:37:12.866972Z"
PROOF_HEAD = "cb734b3ef51fe607d7d4de2709d517625a9c8101"


def fail(message: str) -> None:
    raise SystemExit(
        "STAGE32_POST_CUTOVER_ROLLBACK_PROOF_PREPARATION_GUARD=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\nDETAIL={message}"
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
    cleanup = text(CLEANUP)
    contract = text(CONTRACT)
    transport = text(TRANSPORT)

    require(authority, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE32_POST_CUTOVER_ROLLBACK_PROOF",
        "baseline_main_sha": BASELINE,
        "current_state": STATE,
    }, "rollback authority")

    if set(authority.get("failure_classes", [])) != {
        "BGF-STAGE32-POST-CUTOVER-ROLLBACK-FIXTURE-240",
        "BGF-STAGE32-ROLLBACK-PROOF-SEAM-BYPASS-241",
        "BGF-STAGE32-ROLLBACK-PROOF-REEXECUTION-242",
        "BGF-STAGE32-ROLLBACK-PRODUCTION-MUTATION-243",
        FAILURE_CLASS,
    }:
        fail("failure-class set drifted")

    require(authority.get("workflow_seal", {}), {
        "seal_pr": 85,
        "seal_merge_main_sha": "3a4f52114a9ad9fa57610f67b006e76a26d98009",
        "proof_pr": 84,
        "proof_head_sha": PROOF_HEAD,
        "fallback_trigger_pr": 86,
        "fallback_trigger_head_sha": "777bb51f698c0648cf641bba1070f5f71f001e87",
        "fallback_consumed_once": True,
        "proof_pr_closed_unmerged": True,
        "fallback_pr_closed_unmerged": True,
        "proof_reexecution_allowed": False,
    }, "workflow seal receipt")

    require(authority.get("runtime_proof", {}), {
        "workflow_run_id": 32540031081,
        "workflow_job_id": 96948118831,
        "run_attempt": 1,
        "result": "SUCCESS",
        "proof_head_sha": PROOF_HEAD,
        "delivery_path": "fallback_pull_request_opened",
        "authorized_rollback_object_verified": True,
        "direct_rpc_branch_verified": True,
        "get_workout_verified": True,
        "start_workout_verified": True,
        "set_completion_verified": True,
        "get_feedback_context_verified": True,
        "submit_feedback_verified": True,
        "all_five_routes_verified": True,
        "production_edge_mode_preserved": True,
        "automatic_fallback_remained_false": True,
        "production_rollback_requested_remained_false": True,
        "production_rollback_authorized_remained_false": True,
        "direct_rpc_grants_changed": False,
        "direct_rpc_privilege_revocation": False,
        "real_customer_data_used": False,
        "raw_synthetic_token_printed": False,
        "cleanup_completed": True,
        "proof_reexecution_allowed": False,
        "launch_gate_promotion": False,
    }, "runtime proof")

    require(authority.get("cleanup", {}), {
        "repository_file": "04_backend_supabase/migrations/20260822002500_stage32_post_cutover_rollback_proof_cleanup.sql",
        "migration_name": CLEANUP_NAME,
        "migration_ledger_state": "remote_reconciled",
        "remote_applied": True,
        "remote_version": CLEANUP_VERSION,
        "source_main_sha": BASELINE,
        "apply_result": "SUCCESS",
        "cleanup_completed": True,
        "requires_exact_receipts": True,
        "requires_zero_direct_path_network_origin_rows": True,
        "preserves_historical_global_network_rows": True,
        "requires_direct_rpc_grants_intact_before_cleanup": True,
        "requires_direct_rpc_grants_intact_after_cleanup": True,
        "revokes_direct_rpc_execute": False,
    }, "cleanup authority")

    require(authority.get("post_cleanup_receipt", {}), {
        "source": "Supabase.list_migrations+Supabase.execute_sql",
        "observed_at_utc": OBSERVED,
        "remote_cleanup_version": CLEANUP_VERSION,
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
        "proof_window_network_rows": 0,
        "global_network_buckets": 13,
        "rpc_count": 5,
        "all_five_anon_execute_intact": True,
        "all_five_authenticated_execute_intact": True,
        "synthetic_residue_zero": True,
        "direct_rpc_grants_changed": False,
    }, "post-cleanup receipt")

    if ledger.get("baseline_main_sha") != BASELINE or ledger.get("observed_at_utc") != OBSERVED:
        fail("migration ledger current receipt drifted")
    repo_only = [
        row for row in ledger.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    ]
    if repo_only:
        fail("repo-only migration remains after rollback cleanup reconciliation")
    remote = {
        row.get("name"): row.get("version")
        for row in ledger.get("remote_migrations", []) if isinstance(row, dict)
    }
    if remote.get("stage32_post_cutover_rollback_fixture") != "20260821235550":
        fail("rollback fixture remote receipt disappeared")
    if remote.get(CLEANUP_NAME) != CLEANUP_VERSION:
        fail("rollback cleanup remote receipt disappeared or changed")

    for fragment in (
        "BGF-STAGE32-POST-CUTOVER-ROLLBACK-CLEANUP-244",
        "32540031081 / job 96948118831",
        PROOF_HEAD,
        "STAGE32_ROLLBACK_CLEANUP_DIRECT_PATH_NETWORK_BUCKET_UNEXPECTED",
        "STAGE32_ROLLBACK_CLEANUP_DIRECT_GRANTS_NOT_INTACT",
        "STAGE32_ROLLBACK_CLEANUP_POSTCONDITION_DIRECT_GRANTS_CHANGED",
        "delete from private.student_access_security_events",
        "delete from public.organizations",
        "delete from auth.users",
    ):
        if fragment not in cleanup:
            fail(f"cleanup SQL drift: {fragment}")
    lower = cleanup.lower()
    if "revoke execute" in lower or "grant execute" in lower:
        fail("cleanup migration changes direct-RPC grants")
    if "delete from private.student_access_network_rate_buckets" in lower:
        fail("cleanup mutated historical network-origin buckets")

    for fragment in (
        "static const StudentAccessTransportMode activeMode =",
        "StudentAccessTransportMode.edgeGateway;",
        "static const bool edgeGatewaySelected = true;",
        "static const bool automaticEdgeToDirectFallback = false;",
        "static const bool explicitRollbackRequested = false;",
        "static const bool explicitRollbackAuthorized = false;",
        "static const bool directRpcExecuteRevoked = false;",
        "static const bool rollbackVerified = false;",
        "static const bool clientCutoverVerified = false;",
    ):
        if fragment not in contract:
            fail(f"production transport contract drift: {fragment}")
    if "factory StudentAccessTransport.forAuthorizedRollbackProof" not in transport:
        fail("proof-only rollback factory disappeared")

    require(authority.get("production_boundary", {}), {
        "active_transport": "edgeGateway",
        "resolved_transport": "edgeGateway",
        "production_singleton": "StudentAccessTransport.instance",
        "edge_gateway_selected": True,
        "automatic_edge_to_direct_fallback": False,
        "explicit_rollback_requested": False,
        "explicit_rollback_authorized": False,
        "direct_rpc_execute_revoked": False,
        "post_cutover_live_proof_verified": True,
        "post_cutover_live_proof_cleanup_verified": True,
        "post_cutover_rollback_verified": True,
        "post_cutover_rollback_cleanup_verified": True,
        "production_transport_change_allowed": False,
        "launch_gate_promotion": False,
    }, "production boundary")

    require(authority.get("next_stage", {}), {
        "name": "ASSESS_POST_CUTOVER_DIRECT_RPC_PRIVILEGE_REVOCATION_GATES",
        "allowed_now": True,
        "requires_cleanup_remote_reconciled": True,
        "requires_zero_synthetic_residue": True,
        "requires_direct_rpc_grants_currently_intact": True,
        "requires_observation_and_security_authority_review": True,
        "requires_separate_explicit_privilege_revocation_authority": True,
        "may_rerun_rollback_proof": False,
        "may_reapply_cleanup": False,
        "may_revoke_direct_rpc_execute_now": False,
        "may_promote_launch_gates": False,
    }, "next stage")

    print("STAGE32_POST_CUTOVER_ROLLBACK_PROOF_PREPARATION_GUARD=PASS")
    print("CURRENT_LIFECYCLE=ROLLBACK_PROOF_SUCCESS_CLEANUP_REMOTE_COMPLETE")
    print("ROLLBACK_PROOF_RUN=32540031081")
    print("ROLLBACK_PROOF_JOB=96948118831")
    print(f"ROLLBACK_PROOF_HEAD={PROOF_HEAD}")
    print("ROLLBACK_ROUTES_VERIFIED=5")
    print("ROLLBACK_PROOF_REEXECUTION_ALLOWED=false")
    print(f"CLEANUP_REMOTE_VERSION={CLEANUP_VERSION}")
    print("ROLLBACK_SYNTHETIC_RESIDUE=ZERO")
    print("DIRECT_PATH_NETWORK_BUCKETS=0")
    print("DIRECT_RPC_GRANTS=INTACT")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")
    print("PRODUCTION_ACTIVE_TRANSPORT=edgeGateway")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
