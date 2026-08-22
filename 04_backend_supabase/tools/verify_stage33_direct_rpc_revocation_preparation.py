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
PROMOTION = BACKEND / "stage33_direct_rpc_revocation_migration_promotion_authority.json"
CANDIDATE = BACKEND / "operations" / "stage33_direct_rpc_revocation_and_post_revocation_fixture_candidate.sql"
RECOVERY = BACKEND / "operations" / "stage33_direct_rpc_regrant_recovery.sql"
TEST = APP / "test" / "student_access_stage33_post_revocation_live_edge_proof_test.dart"
CONTRACT = APP / "lib" / "features" / "student" / "student_access_transport_contract.dart"
MIGRATION = BACKEND / "migrations" / "20260822022000_stage33_direct_rpc_revocation_and_post_revocation_fixture.sql"

FAILURE_CLASS = "BGF-STAGE33-PRIVILEGE-REVOCATION-PREMATURE-245"
STATE = "DIRECT_RPC_REVOCATION_CANDIDATE_STAGED_NO_REMOTE_MUTATION"
BASELINE = "ecdd98c87c7bdc9a4071475300df2699b0a260e5"
CANDIDATE_BLOB = "08fbbf71ec51583c8e46792ed88b28825394e9f1"
RECOVERY_BLOB = "2a620b8a951d30bd4d9688158d36e9d1736b65a3"
TEST_BLOB = "d2882d6560a18e259afe74ccbc18d3d275d7f001"
MIGRATION_BLOB = "8f079770f077913d94229df272583945320d943d"
MIGRATION_NAME = "stage33_direct_rpc_revocation_and_post_revocation_fixture"
TARGET_SIGNATURES = {
    "public.get_student_feedback_context_v2(text)",
    "public.get_student_workout_v2(text)",
    "public.set_student_exercise_completion_v2(text,uuid,uuid,boolean,text)",
    "public.start_student_workout_v2(text,text)",
    "public.submit_student_workout_feedback_v2(text,uuid,integer,integer,integer,text,text,text)",
}
TARGET_NAMES = {s.split(".", 1)[1].split("(", 1)[0] for s in TARGET_SIGNATURES}


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
    for key, expected_value in expected.items():
        if mapping.get(key) != expected_value:
            fail(f"{label} drift: {key}")


def exposure_rows(exposure: dict) -> list[dict]:
    if exposure.get("schema_version") == 1:
        rows = exposure.get("approved_exposures", [])
    elif exposure.get("schema_version") == 2:
        rows = exposure.get("remote_pre_revocation_approved_exposures", [])
    else:
        fail("unsupported SECURITY DEFINER authority schema")
    return [row for row in rows if isinstance(row, dict)]


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
    }, "preparation authority")
    require(assessment, {
        "current_state": "DIRECT_RPC_REVOCATION_GATES_ASSESSED_PREPARATION_ALLOWED_NO_MUTATION",
    }, "assessment authority")
    require(rollback, {
        "current_state": "POST_CUTOVER_ROLLBACK_PROOF_VERIFIED_CLEANUP_COMPLETE_EDGE_MODE",
    }, "Stage32 rollback authority")
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
    }, "historical production boundary")

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
    require(authority.get("fresh_post_assessment_receipt", {}), {
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
    }, "fresh preparation receipt")

    require(authority.get("revocation_candidate", {}), {
        "repository_blob_sha": CANDIDATE_BLOB,
        "is_migration": False,
        "remote_application_allowed": False,
        "future_migration_name": MIGRATION_NAME,
        "atomic_fixture_and_privilege_cut": True,
        "exact_target_count": 5,
        "preserves_service_role_execute": True,
        "preserves_issue_student_access_token_v2_authenticated_execute": True,
    }, "candidate authority")
    require(authority.get("regrant_recovery", {}), {
        "repository_blob_sha": RECOVERY_BLOB,
        "is_migration": False,
        "automatic_execution_allowed": False,
        "execution_allowed_before_remote_revocation": False,
        "restores_only_exact_five_targets": True,
        "requires_service_role_execute_intact": True,
        "preserves_issue_student_access_token_v2_authenticated_execute": True,
        "production_transport_constant_change": False,
        "automatic_fallback_enablement": False,
    }, "regrant authority")
    proof = authority.get("post_revocation_edge_proof_candidate", {})
    require(proof, {
        "focused_test_blob_sha": TEST_BLOB,
        "production_transport_object": "StudentAccessTransport.instance",
        "for_verification_factory_allowed": False,
        "authorized_rollback_factory_allowed": False,
        "direct_rpc_calls_from_focused_test_allowed": False,
        "raw_edge_function_calls_from_focused_test_allowed": False,
        "route_count": 5,
        "workflow_must_separately_prove_direct_http_rpc_denied": True,
        "source_direct_rpc_execute_revoked_flag_may_self_promote": False,
        "one_shot_workflow_required_before_remote_apply": True,
    }, "proof candidate authority")
    if set(authority.get("target_functions", [])) != TARGET_SIGNATURES:
        fail("exact five target signatures drifted")

    # Immutable asset safety contract.
    for fragment in (
        "STAGE33_REVOCATION_REQUIRES_EMPTY_CUSTOMER_DOMAIN",
        "STAGE33_REVOCATION_SECURITY_OBSERVATION_NOT_QUIET",
        "fitnexus-stage33-post-revocation-edge-proof-v1",
        "STAGE33_REVOCATION_PRECONDITION_DIRECT_GRANTS_DRIFT",
        "STAGE33_REVOCATION_POSTCONDITION_ROLE_BOUNDARY_FAILED",
    ):
        if fragment not in candidate:
            fail(f"candidate drift: {fragment}")
    for signature in TARGET_SIGNATURES:
        short = signature.removeprefix("public.")
        if f"revoke execute on function public.{short}" not in candidate:
            fail(f"candidate missing revoke target: {signature}")
        if f"grant execute on function public.{short}" not in recovery:
            fail(f"recovery missing grant target: {signature}")
    if candidate.lower().count("revoke execute on function public.") != 5:
        fail("candidate revoke count is not exactly five")
    if recovery.lower().count("grant execute on function public.") != 5:
        fail("recovery grant count is not exactly five")
    if "has_function_privilege('public'" in candidate.lower() or "has_function_privilege('public'" in recovery.lower():
        fail("PUBLIC pseudo-role privilege check reintroduced")
    for forbidden in ("forVerification", "forAuthorizedRollbackProof", ".rpc(", ".functions.invoke("):
        if forbidden in proof_test:
            fail(f"focused proof bypass: {forbidden}")
    if "StudentAccessTransport.instance" not in proof_test:
        fail("focused proof no longer uses production singleton")

    remote_rows = exposure_rows(exposure)
    remote_names = {row.get("function") for row in remote_rows}
    if remote_names != TARGET_NAMES | {"issue_student_access_token_v2"}:
        fail("remote pre-revocation exposure receipt drifted")
    for fragment in (
        "StudentAccessTransportMode.edgeGateway;",
        "static const bool edgeGatewaySelected = true;",
        "static const bool automaticEdgeToDirectFallback = false;",
        "static const bool explicitRollbackRequested = false;",
        "static const bool explicitRollbackAuthorized = false;",
        "static const bool directRpcExecuteRevoked = false;",
    ):
        if fragment not in contract:
            fail(f"production source drift: {fragment}")

    repo_only = [
        row for row in ledger.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    ]
    remote_migrations = {
        row.get("name"): row.get("version")
        for row in ledger.get("remote_migrations", []) if isinstance(row, dict)
    }
    migration_exists = MIGRATION.exists()

    if not migration_exists:
        if repo_only:
            fail("pre-promotion preparation unexpectedly has repo-only divergence")
        lifecycle = "PREPARATION_ONLY"
    else:
        promotion = load(PROMOTION)
        require(promotion, {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "stage": "STAGE33_DIRECT_RPC_REVOCATION_MIGRATION_PROMOTION",
            "baseline_main_sha": "2f8bd11ac0a4ba4e605807fb17c6c78ff3939041",
            "current_state": "REVOCATION_MIGRATION_REPO_ONLY_PROOF_SEAL_PENDING",
        }, "downstream promotion authority")
        require(promotion.get("migration", {}), {
            "name": MIGRATION_NAME,
            "repository_blob_sha": MIGRATION_BLOB,
            "source_candidate_blob_sha": CANDIDATE_BLOB,
            "migration_ledger_state": "repo_only",
            "remote_applied": False,
            "remote_version": None,
            "apply_count": 0,
        }, "downstream promotion migration")
        if len(repo_only) != 1 or repo_only[0].get("name") != MIGRATION_NAME:
            fail("Stage33 migration must be unique repo-only divergence")
        if MIGRATION_NAME in remote_migrations:
            fail("Stage33 migration became remote before proof seal")
        if exposure.get("schema_version") != 2 or exposure.get("current_state") != "STAGE33_REVOCATION_REPO_ONLY_REMOTE_PRE_REVOCATION":
            fail("lifecycle-aware exposure authority missing during promotion")
        transition = exposure.get("stage33_transition", {})
        require(transition, {
            "migration_name": MIGRATION_NAME,
            "migration_ledger_state": "repo_only",
            "remote_applied": False,
            "remote_version": None,
            "service_role_preserved_for_edge_backend": True,
            "issue_student_access_token_v2_preserved": True,
            "remote_revocation_allowed_now": False,
        }, "exposure transition")
        lifecycle = "MIGRATION_PROMOTION_REPO_ONLY"

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
    }, "preparation promotion boundary")

    print("STAGE33_DIRECT_RPC_REVOCATION_PREPARATION_GUARD=PASS")
    print(f"CURRENT_DOWNSTREAM_LIFECYCLE={lifecycle}")
    print(f"CANDIDATE_BLOB_SHA={CANDIDATE_BLOB}")
    print(f"RECOVERY_BLOB_SHA={RECOVERY_BLOB}")
    print(f"FOCUSED_TEST_BLOB_SHA={TEST_BLOB}")
    print("REVOCATION_TARGETS=5")
    print("REMOTE_PRIVILEGE_MUTATION=false")
    print("REGRANT_AUTOMATIC_EXECUTION=false")
    print("PRODUCTION_ACTIVE_TRANSPORT=edgeGateway")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
