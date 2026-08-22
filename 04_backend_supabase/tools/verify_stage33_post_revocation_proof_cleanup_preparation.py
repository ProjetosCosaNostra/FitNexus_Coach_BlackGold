from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
APP = ROOT / "03_app_flutter" / "fitnexus_app"
AUTHORITY = BACKEND / "stage33_post_revocation_proof_cleanup_authority.json"
LEDGER = BACKEND / "migration_ledger_authority.json"
EXPOSURE = BACKEND / "security_definer_exposure_authority.json"
CLEANUP = BACKEND / "migrations" / "20260822033500_stage33_post_revocation_proof_cleanup.sql"
REVOCATION = BACKEND / "migrations" / "20260822022000_stage33_direct_rpc_revocation_and_post_revocation_fixture.sql"
WORKFLOW = ROOT / ".github" / "workflows" / "stage33_post_revocation_edge_runtime_live_proof.yml"
CONTRACT = APP / "lib" / "features" / "student" / "student_access_transport_contract.dart"

STATE = "POST_REVOCATION_EDGE_PROOF_VERIFIED_CLEANUP_REMOTE_COMPLETE"
BASELINE = "e30aa197fe5d19b9e385a8720944c6c9c10d34ee"
OBSERVED = "2026-08-22T06:11:53.105067Z"
REVOCATION_NAME = "stage33_direct_rpc_revocation_and_post_revocation_fixture"
REVOCATION_VERSION = "20260822032456"
REVOCATION_BLOB = "8f079770f077913d94229df272583945320d943d"
CLEANUP_NAME = "stage33_post_revocation_proof_cleanup"
CLEANUP_VERSION = "20260822061133"
CLEANUP_BLOB = "d432cbe4cb77f7b5664c399bc11fa53ad89c60bf"
WORKFLOW_BLOB = "5490d1569f7de8c93e5822426d2c75d588a0e3ef"
FAILURE_CLASS = "BGF-STAGE33-POST-REVOCATION-PROOF-CLEANUP-262"


def fail(message: str) -> None:
    raise SystemExit(
        "STAGE33_POST_REVOCATION_PROOF_CLEANUP_LIFECYCLE_GUARD=FAIL\n"
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


def raw(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        fail(f"unable to read {path.relative_to(ROOT)}: {type(exc).__name__}")
    raise AssertionError("unreachable")


def text(path: Path) -> str:
    return raw(path).decode("utf-8")


def git_blob_sha(path: Path) -> str:
    data = raw(path)
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def require(mapping: dict, expected: dict, label: str) -> None:
    if not isinstance(mapping, dict):
        fail(f"{label} must be an object")
    for key, expected_value in expected.items():
        if mapping.get(key) != expected_value:
            fail(f"{label} drift: {key}")


def main() -> None:
    authority = load(AUTHORITY)
    ledger = load(LEDGER)
    exposure = load(EXPOSURE)
    cleanup = text(CLEANUP)
    contract = text(CONTRACT)

    require(authority, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE33_POST_REVOCATION_PROOF_CLEANUP",
        "baseline_main_sha": BASELINE,
        "current_state": STATE,
    }, "cleanup authority")
    if set(authority.get("failure_classes", [])) != {
        "BGF-STAGE33-REVOCATION-PROOF-REEXECUTION-255",
        "BGF-STAGE33-READY-FOR-REVIEW-EVENT-NONMATERIALIZATION-261",
        FAILURE_CLASS,
        "BGF-STAGE33-POST-REVOCATION-NETWORK-RESIDUE-263",
    }:
        fail("cleanup authority failure-class set drifted")

    require(authority.get("sealed_proof", {}), {
        "workflow_run_id": 32548995700,
        "workflow_job_id": 96972506797,
        "run_attempt": 1,
        "result": "PASS",
        "proof_candidate_pr": 92,
        "proof_candidate_head_sha": "b8123abb7f0dda364f49d9f7342e5887c7da6553",
        "fallback_trigger_pr": 94,
        "fallback_trigger_head_sha": "d2ac5815532ac1671c942ac6e8d491c7ac5ecd89",
        "preferred_ready_for_review_materialized": False,
        "fallback_opened_materialized": True,
        "proof_candidate_closed_unmerged": True,
        "fallback_trigger_closed_unmerged": True,
        "proof_reexecution_allowed": False,
        "direct_http_rpc_denial_verified": True,
        "direct_http_rpc_denial_status": 401,
        "direct_http_synthetic_data_returned": False,
        "production_singleton": "StudentAccessTransport.instance",
        "production_active_transport": "edgeGateway",
        "automatic_edge_to_direct_fallback": False,
        "all_five_routes_verified_via_edge": True,
        "route_count": 5,
        "real_customer_data_used": False,
        "raw_synthetic_token_printed": False,
        "launch_gate_promotion": False,
    }, "sealed proof")

    require(authority.get("remote_revocation_receipt", {}), {
        "migration_name": REVOCATION_NAME,
        "migration_blob_sha": REVOCATION_BLOB,
        "remote_version": REVOCATION_VERSION,
        "applied_once": True,
        "reapply_allowed": False,
        "target_rpc_count": 5,
        "anon_execute_count": 0,
        "authenticated_execute_count": 0,
        "service_role_execute_count": 5,
        "issue_student_access_token_v2_authenticated_execute": True,
        "direct_student_route_security_definer_warnings_remaining": 0,
    }, "remote revocation receipt")

    require(authority.get("cleanup", {}), {
        "migration_name": CLEANUP_NAME,
        "migration_file": "04_backend_supabase/migrations/20260822033500_stage33_post_revocation_proof_cleanup.sql",
        "migration_blob_sha": CLEANUP_BLOB,
        "migration_ledger_state": "remote_reconciled",
        "remote_applied": True,
        "remote_version": CLEANUP_VERSION,
        "apply_count": 1,
        "apply_via": "Supabase.apply_migration",
        "requires_global_network_baseline_after_cleanup": 13,
        "requires_global_growth_baseline_after_cleanup": 6,
        "requires_anon_execute_after_cleanup": 0,
        "requires_authenticated_execute_after_cleanup": 0,
        "requires_service_role_execute_after_cleanup": 5,
        "requires_issue_token_authenticated_execute_after_cleanup": True,
        "cleanup_completed": True,
        "reapply_allowed": False,
    }, "cleanup remote receipt")

    require(authority.get("post_cleanup_receipt", {}), {
        "source": "Supabase.execute_sql+Supabase.get_advisors",
        "observed_at_utc": OBSERVED,
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
        "command_receipts": 0,
        "link_rate_buckets": 0,
        "security_events": 0,
        "security_signals": 0,
        "fixture_growth_events": 0,
        "fixture_growth_attribution": 0,
        "global_growth_events": 6,
        "global_network_buckets": 13,
        "proof_network_buckets": 0,
        "anon_execute_count": 0,
        "authenticated_execute_count": 0,
        "service_role_execute_count": 5,
        "issue_student_access_token_v2_authenticated_execute": True,
        "security_posture_after_cleanup": "quiet",
        "direct_student_route_security_definer_warnings": 0,
    }, "post-cleanup receipt")
    if authority["post_cleanup_receipt"].get("remaining_security_advisor_warnings") != [
        "authenticated_security_definer_function_executable:issue_student_access_token_v2"
    ]:
        fail("post-cleanup advisor warning set drifted")

    require(authority.get("production_boundary", {}), {
        "active_transport": "edgeGateway",
        "production_singleton": "StudentAccessTransport.instance",
        "automatic_edge_to_direct_fallback": False,
        "remote_direct_rpc_execute_revoked": True,
        "source_direct_rpc_execute_revoked_flag": False,
        "post_revocation_edge_runtime_proof_verified": True,
        "cleanup_verified": True,
        "launch_gate_promotion": False,
    }, "production boundary")

    if git_blob_sha(REVOCATION) != REVOCATION_BLOB:
        fail("revocation migration blob drifted")
    if git_blob_sha(CLEANUP) != CLEANUP_BLOB:
        fail("cleanup migration blob drifted")
    if git_blob_sha(WORKFLOW) != WORKFLOW_BLOB:
        fail("consumed one-shot workflow blob drifted")

    if ledger.get("baseline_main_sha") != BASELINE or ledger.get("observed_at_utc") != OBSERVED:
        fail("migration ledger post-cleanup receipt drifted")
    remote = {
        row.get("name"): row.get("version")
        for row in ledger.get("remote_migrations", []) if isinstance(row, dict)
    }
    if remote.get(REVOCATION_NAME) != REVOCATION_VERSION:
        fail("Stage33 revocation remote receipt missing or changed")
    if remote.get(CLEANUP_NAME) != CLEANUP_VERSION:
        fail("Stage33 cleanup remote receipt missing or changed")
    repo_only = [
        row for row in ledger.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    ]
    if repo_only:
        fail("remote-complete cleanup lifecycle must not retain repo-only divergence")

    require(exposure, {
        "schema_version": 2,
        "project_ref": "mceukeondizkwlpfxzgf",
        "current_state": "STAGE33_REVOCATION_REMOTE_RECONCILED_POST_REVOCATION",
    }, "SECURITY DEFINER exposure authority")
    require(exposure.get("stage33_transition", {}), {
        "migration_name": REVOCATION_NAME,
        "migration_blob_sha": REVOCATION_BLOB,
        "migration_ledger_state": "remote_reconciled",
        "remote_applied": True,
        "remote_version": REVOCATION_VERSION,
        "repository_target_anon_exposures": 0,
        "repository_target_authenticated_exposures": 1,
        "service_role_preserved_for_edge_backend": True,
        "issue_student_access_token_v2_preserved": True,
        "post_revocation_live_anon_execute_count": 0,
        "post_revocation_live_authenticated_execute_count": 0,
        "post_revocation_live_service_role_execute_count": 5,
        "post_revocation_student_route_advisor_warnings": 0,
    }, "exposure transition")

    lower = cleanup.lower()
    for required in (
        "workflow run 32548995700 / job 96972506797",
        "b8123abb7f0dda364f49d9f7342e5887c7da6553",
        "34000000000000000000000000000001",
        "34000000000000000000000000000002",
        "34000000000000000000000000000003",
        "2026-08-22 03:27:00+00",
        "count(distinct origin_hash)",
        "student_access_network_rate_buckets) <> 18",
        "student_access_network_rate_buckets) <> 13",
        "growth_events) <> 11",
        "growth_events) <> 6",
        "not has_function_privilege('anon'",
        "not has_function_privilege('authenticated'",
        "has_function_privilege('service_role'",
        "public.issue_student_access_token_v2(uuid)",
        "stage33_cleanup_postcondition_revocation_changed",
    ):
        if required not in lower:
            fail(f"cleanup invariant missing: {required}")
    if lower.count("delete from private.student_access_network_rate_buckets") != 1:
        fail("cleanup must contain exactly one bounded global network-bucket delete")
    if "grant execute on function" in lower or "revoke execute on function" in lower:
        fail("cleanup must not change function EXECUTE privileges")

    for fragment in (
        "StudentAccessTransportMode.edgeGateway;",
        "static const bool edgeGatewaySelected = true;",
        "static const bool automaticEdgeToDirectFallback = false;",
        "static const bool explicitRollbackRequested = false;",
        "static const bool explicitRollbackAuthorized = false;",
        "static const bool directRpcExecuteRevoked = false;",
    ):
        if fragment not in contract:
            fail(f"production transport source drift: {fragment}")

    require(authority.get("promotion_rules", {}), {
        "may_reexecute_stage33_proof": False,
        "may_reapply_stage33_revocation_migration": False,
        "may_reapply_stage33_cleanup_migration": False,
        "may_use_execute_sql_for_cleanup_dml": False,
        "may_regrant_direct_rpc_execute_automatically": False,
        "may_promote_launch_gates": False,
    }, "promotion rules")

    require(authority.get("next_stage", {}), {
        "name": "RECONCILE_POST_REVOCATION_SECURITY_AND_CLIENT_AUTHORITIES",
        "allowed_now": True,
        "requires_cleanup_remote_reconciled": True,
        "requires_zero_synthetic_residue": True,
        "requires_direct_anon_execute": 0,
        "requires_direct_authenticated_execute": 0,
        "requires_service_role_execute": 5,
        "requires_issue_token_authenticated_execute": True,
        "may_replay_proof": False,
        "may_regrant_direct_rpc_execute": False,
        "may_promote_launch_gates": False,
    }, "next stage")

    print("STAGE33_POST_REVOCATION_PROOF_CLEANUP_LIFECYCLE_GUARD=PASS")
    print(f"REVOCATION_REMOTE_VERSION={REVOCATION_VERSION}")
    print(f"CLEANUP_REMOTE_VERSION={CLEANUP_VERSION}")
    print(f"CLEANUP_BLOB_SHA={CLEANUP_BLOB}")
    print("CLEANUP_LEDGER_STATE=remote_reconciled")
    print("SYNTHETIC_RESIDUE=0")
    print("HISTORICAL_NETWORK_BUCKETS=13")
    print("HISTORICAL_GROWTH_EVENTS=6")
    print("DIRECT_ANON_EXECUTE=0")
    print("DIRECT_AUTHENTICATED_EXECUTE=0")
    print("EDGE_SERVICE_ROLE_EXECUTE=5")
    print("ISSUE_TOKEN_AUTHENTICATED_EXECUTE=true")
    print("PROOF_REEXECUTION_ALLOWED=false")
    print("CLEANUP_REAPPLY_ALLOWED=false")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
