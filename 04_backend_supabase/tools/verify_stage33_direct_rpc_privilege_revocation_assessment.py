from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
APP = ROOT / "03_app_flutter" / "fitnexus_app"

AUTHORITY = BACKEND / "stage33_direct_rpc_privilege_revocation_assessment_authority.json"
ROLLBACK_AUTHORITY = BACKEND / "stage32_post_cutover_rollback_proof_authority.json"
EXPOSURE_AUTHORITY = BACKEND / "security_definer_exposure_authority.json"
ABUSE_MIGRATION = BACKEND / "migrations" / "20260819192100_stage24_student_access_abuse_observability.sql"
GATEWAY = BACKEND / "functions" / "student-access-gateway" / "index.ts"
TRANSPORT_CONTRACT = APP / "lib" / "features" / "student" / "student_access_transport_contract.dart"

STATE = "DIRECT_RPC_REVOCATION_GATES_ASSESSED_PREPARATION_ALLOWED_NO_MUTATION"
FAILURE_CLASS = "BGF-STAGE33-PRIVILEGE-REVOCATION-PREMATURE-245"
BASELINE = "8648c7160bf1f7410f933a75583d714205d864c5"
OBSERVED = "2026-08-22T02:00:41.968609Z"
TARGETS = {
    "public.get_student_feedback_context_v2(text)",
    "public.get_student_workout_v2(text)",
    "public.set_student_exercise_completion_v2(text,uuid,uuid,boolean,text)",
    "public.start_student_workout_v2(text,text)",
    "public.submit_student_workout_feedback_v2(text,uuid,integer,integer,integer,text,text,text)",
}


def fail(message: str) -> None:
    raise SystemExit(
        "STAGE33_DIRECT_RPC_PRIVILEGE_REVOCATION_ASSESSMENT_GUARD=FAIL\n"
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
    rollback = load(ROLLBACK_AUTHORITY)
    exposure = load(EXPOSURE_AUTHORITY)
    abuse_sql = text(ABUSE_MIGRATION)
    gateway = text(GATEWAY)
    contract = text(TRANSPORT_CONTRACT)

    require(authority, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE33_DIRECT_RPC_PRIVILEGE_REVOCATION_ASSESSMENT",
        "baseline_main_sha": BASELINE,
        "current_state": STATE,
    }, "Stage33 assessment authority")

    if set(authority.get("failure_classes", [])) != {
        "BGF-STAGE33-PRIVILEGE-REVOCATION-PREMATURE-245",
        "BGF-STAGE33-OBSERVATION-WINDOW-SEMANTIC-DRIFT-246",
        "BGF-STAGE33-SECURITY-ADVISOR-SURFACE-DRIFT-247",
        "BGF-STAGE33-GATEWAY-BACKEND-CREDENTIAL-ASSUMPTION-248",
    }:
        fail("Stage33 failure-class set drifted")

    require(rollback, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "current_state": "POST_CUTOVER_ROLLBACK_PROOF_VERIFIED_CLEANUP_COMPLETE_EDGE_MODE",
    }, "Stage32 rollback authority")
    require(rollback.get("runtime_proof", {}), {
        "workflow_run_id": 32540031081,
        "result": "SUCCESS",
        "all_five_routes_verified": True,
        "production_edge_mode_preserved": True,
        "cleanup_completed": True,
        "proof_reexecution_allowed": False,
    }, "Stage32 rollback proof receipt")
    require(rollback.get("cleanup", {}), {
        "migration_ledger_state": "remote_reconciled",
        "remote_applied": True,
        "remote_version": "20260822003559",
        "cleanup_completed": True,
        "revokes_direct_rpc_execute": False,
    }, "Stage32 rollback cleanup receipt")
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
    }, "production boundary")

    observation = authority.get("observation_gate", {})
    require(observation, {
        "authoritative_window_seconds": 3600,
        "observation_start_checkpoint_utc": "2026-08-22T00:37:12.866972Z",
        "observed_at_utc": OBSERVED,
        "seconds_since_checkpoint": 5009,
        "minimum_window_satisfied": True,
        "posture": "quiet",
        "signals_60m": 0,
        "security_events_60m": 0,
        "network_origin_buckets_seen_60m": 0,
        "latest_network_origin_bucket_seen_at_utc": "2026-08-20T08:46:53.9259Z",
        "customer_domain_auth_users": 0,
        "customer_domain_organizations": 0,
        "customer_domain_students": 0,
        "customer_domain_workout_sessions": 0,
        "source": "Supabase.execute_sql",
        "result": "PASS",
    }, "observation gate")
    if int(observation.get("seconds_since_checkpoint", 0)) < 3600:
        fail("observation window is shorter than Stage24 60-minute posture semantics")

    for fragment in (
        "now() - interval '60 minutes'",
        "then 'investigate'",
        "then 'observe'",
        "else 'quiet'",
        "private.student_access_security_posture_v1",
        "Does not promote the incident_response gate",
    ):
        if fragment not in abuse_sql:
            fail(f"Stage24 observation semantics drift: {fragment}")

    advisor = authority.get("security_advisor_gate", {})
    require(advisor, {
        "source": "Supabase.get_advisors(security)",
        "rechecked_after_observation_window": True,
        "total_warning_count": 11,
        "anon_security_definer_warning_count": 5,
        "authenticated_security_definer_warning_count": 6,
        "target_direct_rpc_anon_warning_count": 5,
        "target_direct_rpc_authenticated_warning_count": 5,
        "issue_student_access_token_v2_authenticated_warning_count": 1,
        "unexpected_warning_count": 0,
        "result": "PASS_WITH_EXPECTED_PRE_REVOCATION_WARNINGS",
    }, "security advisor gate")

    surface = authority.get("target_direct_rpc_surface", {})
    if set(surface.get("functions", [])) != TARGETS:
        fail("exact five-function direct RPC target set drifted")
    require(surface, {
        "function_count": 5,
        "anon_execute_count": 5,
        "authenticated_execute_count": 5,
        "service_role_execute_count": 5,
        "direct_grants_intact_before_preparation": True,
        "issue_student_access_token_v2_is_target": False,
    }, "target direct RPC surface")

    approved = exposure.get("approved_exposures", [])
    normalized: dict[str, set[str]] = {}
    for row in approved:
        if not isinstance(row, dict):
            continue
        function = row.get("function")
        arguments = row.get("identity_arguments")
        roles = row.get("roles")
        if isinstance(function, str) and isinstance(arguments, str) and isinstance(roles, list):
            normalized[f"public.{function}({arguments.replace(' ', '')})"] = {
                role for role in roles if isinstance(role, str)
            }

    expected_role_map = {
        "public.get_student_feedback_context_v2(text)": {"anon", "authenticated"},
        "public.get_student_workout_v2(text)": {"anon", "authenticated"},
        "public.set_student_exercise_completion_v2(text,uuid,uuid,boolean,text)": {"anon", "authenticated"},
        "public.start_student_workout_v2(text,text)": {"anon", "authenticated"},
        "public.submit_student_workout_feedback_v2(text,uuid,integer,integer,integer,text,text,text)": {"anon", "authenticated"},
        "public.issue_student_access_token_v2(uuid)": {"authenticated"},
    }
    for signature, roles in expected_role_map.items():
        if normalized.get(signature) != roles:
            fail(f"SECURITY DEFINER exposure authority drift: {signature}")

    for fragment in (
        'const RATE_LIMIT_RPC = "check_student_access_network_rate_limit_v1";',
        'get_workout: "get_student_workout_v2"',
        'start_workout: "start_student_workout_v2"',
        'set_completion: "set_student_exercise_completion_v2"',
        'get_feedback_context: "get_student_feedback_context_v2"',
        'submit_feedback: "submit_student_workout_feedback_v2"',
        'Deno.env.get("SUPABASE_SECRET_KEYS")',
        'Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")',
        'return { apiKey: secretKey };',
        'authorization: `Bearer ${legacy}`',
    ):
        if fragment not in gateway:
            fail(f"gateway privileged-backend credential contract drift: {fragment}")

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

    # This assessment is intentionally read-only/repository-only. A revocation SQL file
    # appearing before the separate preparation lifecycle is materialized is a hard fail.
    premature = [
        path for path in (BACKEND / "migrations").glob("*stage33*revocation*.sql")
        if path.is_file()
    ]
    if premature:
        fail("Stage33 revocation migration appeared during assessment-only lifecycle")

    decision = authority.get("decision", {})
    require(decision, {
        "post_cutover_edge_proof_gate": "PASS",
        "post_cutover_rollback_proof_gate": "PASS",
        "post_cutover_cleanup_gate": "PASS",
        "observation_window_gate": "PASS",
        "security_advisor_recheck_gate": "PASS_WITH_EXPECTED_PRE_REVOCATION_WARNINGS",
        "repository_first_revocation_preparation_allowed": True,
        "remote_privilege_revocation_allowed_now": False,
        "alert_delivery_gate_is_separate_from_revocation_preparation": True,
        "incident_response_gate_promoted": False,
        "production_deployment_gate_promoted": False,
        "paid_ads_gate_promoted": False,
    }, "assessment decision")

    require(authority.get("next_stage", {}), {
        "name": "PREPARE_STAGE33_DIRECT_RPC_REVOCATION_AND_POST_REVOCATION_EDGE_PROOF_LIFECYCLE",
        "allowed_now": True,
        "requires_repository_first_revocation_migration": True,
        "requires_exact_five_rpc_target_set": True,
        "requires_issue_student_access_token_v2_preserved": True,
        "requires_service_role_execute_preserved": True,
        "requires_anon_and_authenticated_execute_revoked_only_after_ci_merge": True,
        "requires_fresh_quiet_security_posture_before_apply": True,
        "requires_post_revocation_edge_runtime_verification": True,
        "requires_prepared_regrant_recovery_path_before_apply": True,
        "may_revoke_direct_rpc_execute_now": False,
        "may_promote_incident_response_gate": False,
        "may_promote_production_deployment_gate": False,
        "may_enable_paid_ads": False,
    }, "next stage")

    print("STAGE33_DIRECT_RPC_PRIVILEGE_REVOCATION_ASSESSMENT_GUARD=PASS")
    print(f"BASELINE_MAIN_SHA={BASELINE}")
    print(f"OBSERVED_AT_UTC={OBSERVED}")
    print("OBSERVATION_WINDOW_SECONDS=3600")
    print("OBSERVATION_WINDOW_ELAPSED_SECONDS=5009")
    print("SECURITY_POSTURE=quiet")
    print("SECURITY_SIGNALS_60M=0")
    print("SECURITY_EVENTS_60M=0")
    print("NETWORK_ORIGIN_BUCKETS_60M=0")
    print("SECURITY_ADVISOR_WARNINGS=11_EXPECTED_PRE_REVOCATION")
    print("TARGET_DIRECT_RPC_COUNT=5")
    print("TARGET_ANON_EXECUTE=5")
    print("TARGET_AUTHENTICATED_EXECUTE=5")
    print("TARGET_SERVICE_ROLE_EXECUTE=5")
    print("REMOTE_PRIVILEGE_REVOCATION_ALLOWED_NOW=false")
    print("REPOSITORY_FIRST_REVOCATION_PREPARATION_ALLOWED=true")
    print("PRODUCTION_ACTIVE_TRANSPORT=edgeGateway")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
