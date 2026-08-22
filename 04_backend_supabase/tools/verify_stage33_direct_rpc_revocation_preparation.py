from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
APP = ROOT / "03_app_flutter" / "fitnexus_app"

AUTHORITY = BACKEND / "stage33_direct_rpc_revocation_preparation_authority.json"
ASSESSMENT = BACKEND / "stage33_direct_rpc_privilege_revocation_assessment_authority.json"
ROLLBACK = BACKEND / "stage32_post_cutover_rollback_proof_authority.json"
EXPOSURE = BACKEND / "security_definer_exposure_authority.json"
LEDGER = BACKEND / "migration_ledger_authority.json"
CANDIDATE = BACKEND / "operations" / "stage33_direct_rpc_revocation_and_post_revocation_fixture_candidate.sql"
RECOVERY = BACKEND / "operations" / "stage33_direct_rpc_regrant_recovery.sql"
TEST = APP / "test" / "student_access_stage33_post_revocation_live_edge_proof_test.dart"
CONTRACT = APP / "lib" / "features" / "student" / "student_access_transport_contract.dart"

FAILURE_CLASS = "BGF-STAGE33-PRIVILEGE-REVOCATION-PREMATURE-245"
STATE = "DIRECT_RPC_REVOCATION_CANDIDATE_STAGED_NO_REMOTE_MUTATION"
BASELINE = "ecdd98c87c7bdc9a4071475300df2699b0a260e5"
CANDIDATE_BLOB = "39f4a13e7b6fdeb0675a8cc5a5afa424b409ef6a"
RECOVERY_BLOB = "1c26c7aff1679bd85b359756eb3eb2c5eeaeaae1"
TEST_BLOB = "d2882d6560a18e259afe74ccbc18d3d275d7f001"
TARGET_NAMES = {
    "get_student_feedback_context_v2",
    "get_student_workout_v2",
    "set_student_exercise_completion_v2",
    "start_student_workout_v2",
    "submit_student_workout_feedback_v2",
}
TARGET_SIGNATURES = {
    "public.get_student_feedback_context_v2(text)",
    "public.get_student_workout_v2(text)",
    "public.set_student_exercise_completion_v2(text,uuid,uuid,boolean,text)",
    "public.start_student_workout_v2(text,text)",
    "public.submit_student_workout_feedback_v2(text,uuid,integer,integer,integer,text,text,text)",
}


def fail(message: str) -> None:
    raise SystemExit(
        "STAGE33_DIRECT_RPC_REVOCATION_PREPARATION_GUARD=FAIL\n"
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
    assessment = load(ASSESSMENT)
    rollback = load(ROLLBACK)
    exposure = load(EXPOSURE)
    ledger = load(LEDGER)
    candidate = text(CANDIDATE)
    recovery = text(RECOVERY)
    proof_test = text(TEST)
    contract = text(CONTRACT)

    require(authority, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE33_DIRECT_RPC_REVOCATION_PREPARATION",
        "baseline_main_sha": BASELINE,
        "current_state": STATE,
    }, "Stage33 preparation authority")

    if set(authority.get("failure_classes", [])) != {
        "BGF-STAGE33-PRIVILEGE-REVOCATION-PREMATURE-245",
        "BGF-STAGE33-POST-REVOCATION-FIXTURE-249",
        "BGF-STAGE33-REVOCATION-TARGET-DRIFT-250",
        "BGF-STAGE33-REVOCATION-SERVICE-ROLE-LOSS-251",
        "BGF-STAGE33-REGRANT-RECOVERY-SCOPE-252",
        "BGF-STAGE33-POST-REVOCATION-PROOF-SEAM-BYPASS-253",
    }:
        fail("preparation failure-class set drifted")

    require(assessment, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "current_state": "DIRECT_RPC_REVOCATION_GATES_ASSESSED_PREPARATION_ALLOWED_NO_MUTATION",
    }, "assessment authority")
    require(authority.get("assessment_receipt", {}), {
        "assessment_pr": 89,
        "assessment_head_sha": "1769492591d6a89604d4596df5dd0effbcbc9990",
        "assessment_ci_run_id": 32545166067,
        "assessment_ci_job_id": 96962225683,
        "assessment_ci_result": "SUCCESS",
        "assessment_merge_main_sha": BASELINE,
        "observation_window_gate": "PASS",
        "security_advisor_recheck_gate": "PASS_WITH_EXPECTED_PRE_REVOCATION_WARNINGS",
    }, "assessment receipt")

    require(rollback, {
        "current_state": "POST_CUTOVER_ROLLBACK_PROOF_VERIFIED_CLEANUP_COMPLETE_EDGE_MODE",
    }, "Stage32 rollback lifecycle")
    require(rollback.get("production_boundary", {}), {
        "active_transport": "edgeGateway",
        "resolved_transport": "edgeGateway",
        "automatic_edge_to_direct_fallback": False,
        "explicit_rollback_requested": False,
        "explicit_rollback_authorized": False,
        "direct_rpc_execute_revoked": False,
        "post_cutover_live_proof_verified": True,
        "post_cutover_rollback_verified": True,
        "post_cutover_rollback_cleanup_verified": True,
    }, "Stage32 production boundary")

    require(authority.get("fresh_post_assessment_receipt", {}), {
        "source": "Supabase.execute_sql",
        "observed_at_utc": "2026-08-22T02:05:06.82829Z",
        "security_posture": "quiet",
        "signals_60m": 0,
        "security_events_60m": 0,
        "network_buckets_60m": 0,
        "auth_users": 0,
        "organizations": 0,
        "students": 0,
        "sessions": 0,
        "target_anon_execute_count": 5,
        "target_authenticated_execute_count": 5,
        "target_service_role_execute_count": 5,
        "issue_student_access_token_v2_authenticated_execute": True,
        "remote_privilege_mutation_observed": False,
    }, "fresh post-assessment receipt")

    revocation = authority.get("revocation_candidate", {})
    require(revocation, {
        "repository_file": "04_backend_supabase/operations/stage33_direct_rpc_revocation_and_post_revocation_fixture_candidate.sql",
        "repository_blob_sha": CANDIDATE_BLOB,
        "is_migration": False,
        "remote_application_allowed": False,
        "future_migration_name": "stage33_direct_rpc_revocation_and_post_revocation_fixture",
        "atomic_fixture_and_privilege_cut": True,
        "requires_empty_customer_domain": True,
        "requires_quiet_60m_security_posture_at_apply": True,
        "exact_target_count": 5,
        "revokes_public_execute": True,
        "revokes_anon_execute": True,
        "revokes_authenticated_execute": True,
        "preserves_service_role_execute": True,
        "preserves_issue_student_access_token_v2_authenticated_execute": True,
    }, "revocation candidate")
    if set(authority.get("target_functions", [])) != TARGET_SIGNATURES:
        fail("exact five revocation target signatures drifted")

    fixture = authority.get("post_revocation_fixture", {})
    require(fixture, {
        "synthetic_only": True,
        "token_seed": "fitnexus-stage33-post-revocation-edge-proof-v1",
        "database_stores_token_hash_only": True,
        "user_id": "c91c6cec-618b-58fc-99fc-948ab08895c4",
        "organization_id": "3e4d79f5-9565-5ac9-b5e0-32ea4937d85b",
        "student_id": "87b426f7-73f0-53ec-880b-a75767415dbf",
        "plan_id": "059af7ff-3b6b-5e41-ac46-e4e73e4b5107",
        "exercise_id": "5f1b2d42-20f7-5701-9484-f1dcb9e1dcc2",
        "link_id": "e412e8d8-7b09-5b09-bd06-dd9ea8fb6af1",
        "expires_after_hours": 4,
        "cleanup_required_after_proof": True,
    }, "post-revocation fixture")

    regrant = authority.get("regrant_recovery", {})
    require(regrant, {
        "repository_file": "04_backend_supabase/operations/stage33_direct_rpc_regrant_recovery.sql",
        "repository_blob_sha": RECOVERY_BLOB,
        "is_migration": False,
        "automatic_execution_allowed": False,
        "execution_allowed_before_remote_revocation": False,
        "execution_condition": "only_after_confirmed_remote_revocation_and_failed_post_revocation_edge_proof",
        "restores_only_exact_five_targets": True,
        "restores_anon_execute": True,
        "restores_authenticated_execute": True,
        "requires_service_role_execute_intact": True,
        "preserves_issue_student_access_token_v2_authenticated_execute": True,
        "production_transport_constant_change": False,
        "automatic_fallback_enablement": False,
    }, "regrant recovery")

    proof = authority.get("post_revocation_edge_proof_candidate", {})
    require(proof, {
        "focused_test_file": "03_app_flutter/fitnexus_app/test/student_access_stage33_post_revocation_live_edge_proof_test.dart",
        "focused_test_blob_sha": TEST_BLOB,
        "enabled_environment": "STAGE33_POST_REVOCATION_LIVE_PROOF_ENABLED",
        "production_transport_object": "StudentAccessTransport.instance",
        "for_verification_factory_allowed": False,
        "authorized_rollback_factory_allowed": False,
        "direct_rpc_calls_from_focused_test_allowed": False,
        "raw_edge_function_calls_from_focused_test_allowed": False,
        "route_count": 5,
        "workflow_must_separately_prove_direct_http_rpc_denied": True,
        "source_direct_rpc_execute_revoked_flag_may_self_promote": False,
        "one_shot_workflow_required_before_remote_apply": True,
    }, "post-revocation proof candidate")
    if proof.get("route_sequence") != [
        "get_workout", "start_workout", "set_completion",
        "get_feedback_context", "submit_feedback",
    ]:
        fail("post-revocation route sequence drifted")
    if proof.get("command_ids") != [
        "34000000000000000000000000000001",
        "34000000000000000000000000000002",
        "34000000000000000000000000000003",
    ]:
        fail("post-revocation command IDs drifted")

    # Current remote truth remains pre-revocation. No Stage33 revocation migration may exist yet.
    if any(
        path.is_file() and "stage33" in path.name and "revocation" in path.name
        for path in (BACKEND / "migrations").glob("*.sql")
    ):
        fail("Stage33 revocation migration materialized before candidate preparation merged")
    repo_only = [
        row for row in ledger.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    ]
    if repo_only:
        fail("assessment/preparation lifecycle must not introduce a repo-only migration divergence")
    remote_names = {
        row.get("name") for row in ledger.get("remote_migrations", [])
        if isinstance(row, dict)
    }
    if "stage33_direct_rpc_revocation_and_post_revocation_fixture" in remote_names:
        fail("Stage33 revocation unexpectedly appears in remote migration ledger")

    # Candidate SQL exact safety contract.
    for fragment in (
        "STAGE33_REVOCATION_REQUIRES_EMPTY_CUSTOMER_DOMAIN",
        "STAGE33_REVOCATION_SECURITY_OBSERVATION_NOT_QUIET",
        "now() - interval '60 minutes'",
        "fitnexus-stage33-post-revocation-edge-proof-v1",
        "c91c6cec-618b-58fc-99fc-948ab08895c4",
        "3e4d79f5-9565-5ac9-b5e0-32ea4937d85b",
        "87b426f7-73f0-53ec-880b-a75767415dbf",
        "059af7ff-3b6b-5e41-ac46-e4e73e4b5107",
        "5f1b2d42-20f7-5701-9484-f1dcb9e1dcc2",
        "e412e8d8-7b09-5b09-bd06-dd9ea8fb6af1",
        "STAGE33_REVOCATION_PRECONDITION_DIRECT_GRANTS_DRIFT",
        "STAGE33_REVOCATION_POSTCONDITION_ROLE_BOUNDARY_FAILED",
        "STAGE33_REVOCATION_POSTCONDITION_ISSUE_TOKEN_AUTHORITY_CHANGED",
    ):
        if fragment not in candidate:
            fail(f"revocation candidate SQL drift: {fragment}")
    for signature in TARGET_SIGNATURES:
        sql_signature = signature.removeprefix("public.")
        if f"revoke execute on function public.{sql_signature}" not in candidate:
            fail(f"revocation candidate missing exact target: {signature}")
    if "grant execute on function public." in candidate.lower():
        fail("revocation candidate unexpectedly grants public function execute")

    # Recovery is exact and separate; it must never alter service_role or production transport.
    for signature in TARGET_SIGNATURES:
        sql_signature = signature.removeprefix("public.")
        if f"grant execute on function public.{sql_signature}" not in recovery:
            fail(f"regrant recovery missing exact target: {signature}")
    if recovery.lower().count("grant execute on function public.") != 5:
        fail("regrant recovery must contain exactly five public function grants")
    for forbidden in (
        "grant execute on function public.issue_student_access_token_v2",
        "revoke execute",
        "student_access_transport_contract",
    ):
        if forbidden in recovery.lower():
            fail(f"regrant recovery scope drift: {forbidden}")

    # Focused proof must use only the production singleton and its five-action invoke seam.
    for fragment in (
        "StudentAccessTransport.instance",
        "STAGE33_POST_REVOCATION_LIVE_PROOF_ENABLED",
        "STAGE33_SYNTHETIC_TOKEN",
        "STAGE33_SUPABASE_URL",
        "STAGE33_SUPABASE_PUBLISHABLE_KEY",
        "SharedPreferences.setMockInitialValues",
        "HttpOverrides.global = null",
        "'get_workout'",
        "'start_workout'",
        "'set_completion'",
        "'get_feedback_context'",
        "'submit_feedback'",
        "34000000000000000000000000000001",
        "34000000000000000000000000000002",
        "34000000000000000000000000000003",
    ):
        if fragment not in proof_test:
            fail(f"focused Stage33 proof test drift: {fragment}")
    for forbidden in (
        "forVerification",
        "forAuthorizedRollbackProof",
        ".rpc(",
        ".functions.invoke(",
    ):
        if forbidden in proof_test:
            fail(f"focused Stage33 proof bypasses production singleton: {forbidden}")

    # Exposure authority must still describe live pre-revocation truth on this preparation branch.
    approved = exposure.get("approved_exposures", [])
    exposed_names = {
        row.get("function") for row in approved if isinstance(row, dict)
    }
    if exposed_names != TARGET_NAMES | {"issue_student_access_token_v2"}:
        fail("current pre-revocation SECURITY DEFINER authority set drifted")

    for fragment in (
        "static const StudentAccessTransportMode activeMode =",
        "StudentAccessTransportMode.edgeGateway;",
        "static const bool edgeGatewaySelected = true;",
        "static const bool automaticEdgeToDirectFallback = false;",
        "static const bool explicitRollbackRequested = false;",
        "static const bool explicitRollbackAuthorized = false;",
        "static const bool directRpcExecuteRevoked = false;",
    ):
        if fragment not in contract:
            fail(f"production transport contract drift: {fragment}")

    require(authority.get("promotion_boundary", {}), {
        "candidate_sql_may_execute_from_operations": False,
        "may_create_remote_migration_now": False,
        "may_revoke_remote_privileges_now": False,
        "may_execute_regrant_now": False,
        "must_merge_preparation_before_migration_promotion": True,
        "must_prepare_exact_one_shot_post_revocation_workflow_before_remote_apply": True,
        "must_prepare_exact_open_trigger_fallback_before_remote_apply": True,
        "must_refresh_security_advisor_and_quiet_posture_before_remote_apply": True,
        "must_preserve_service_role": True,
        "must_preserve_issue_token_authority": True,
        "launch_gate_promotion": False,
    }, "promotion boundary")

    require(authority.get("next_stage", {}), {
        "name": "MERGE_STAGE33_REVOCATION_PREPARATION_THEN_PROMOTE_EXACT_CANDIDATE_TO_MIGRATION_AND_SEAL_PROOF",
        "allowed_now": True,
        "requires_full_ci_green": True,
        "requires_exact_candidate_blob_sha": CANDIDATE_BLOB,
        "requires_exact_recovery_blob_sha": RECOVERY_BLOB,
        "requires_exact_focused_test_blob_sha": TEST_BLOB,
        "may_apply_remote_revocation_now": False,
        "may_execute_recovery_now": False,
        "may_promote_launch_gates": False,
    }, "next stage")

    print("STAGE33_DIRECT_RPC_REVOCATION_PREPARATION_GUARD=PASS")
    print(f"BASELINE_MAIN_SHA={BASELINE}")
    print(f"CANDIDATE_BLOB_SHA={CANDIDATE_BLOB}")
    print(f"RECOVERY_BLOB_SHA={RECOVERY_BLOB}")
    print(f"FOCUSED_TEST_BLOB_SHA={TEST_BLOB}")
    print("REVOCATION_TARGETS=5")
    print("CANDIDATE_IS_MIGRATION=false")
    print("REMOTE_PRIVILEGE_MUTATION=false")
    print("REGRANT_AUTOMATIC_EXECUTION=false")
    print("POST_REVOCATION_EDGE_PROOF=PREPARED_NOT_EXECUTED")
    print("PRODUCTION_ACTIVE_TRANSPORT=edgeGateway")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
