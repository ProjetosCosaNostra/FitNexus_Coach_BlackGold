from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
APP = ROOT / "03_app_flutter" / "fitnexus_app"
AUTHORITY = BACKEND / "stage33_direct_rpc_privilege_revocation_assessment_authority.json"
ROLLBACK = BACKEND / "stage32_post_cutover_rollback_proof_authority.json"
EXPOSURE = BACKEND / "security_definer_exposure_authority.json"
ABUSE = BACKEND / "migrations" / "20260819192100_stage24_student_access_abuse_observability.sql"
GATEWAY = BACKEND / "functions" / "student-access-gateway" / "index.ts"
CONTRACT = APP / "lib" / "features" / "student" / "student_access_transport_contract.dart"

FAILURE_CLASS = "BGF-STAGE33-PRIVILEGE-REVOCATION-PREMATURE-245"
STATE = "DIRECT_RPC_REVOCATION_GATES_ASSESSED_PREPARATION_ALLOWED_NO_MUTATION"
BASELINE = "8648c7160bf1f7410f933a75583d714205d864c5"
OBSERVED = "2026-08-22T02:00:41.968609Z"
STAGE33_MIGRATION_FILE = "20260822022000_stage33_direct_rpc_revocation_and_post_revocation_fixture.sql"
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


def normalized_exposures(exposure: dict) -> dict[str, set[str]]:
    if exposure.get("schema_version") == 1:
        rows = exposure.get("approved_exposures", [])
    elif exposure.get("schema_version") == 2:
        rows = exposure.get("remote_pre_revocation_approved_exposures", [])
    else:
        fail("unsupported exposure authority schema")
    result: dict[str, set[str]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        fn = row.get("function")
        args = row.get("identity_arguments")
        roles = row.get("roles")
        if isinstance(fn, str) and isinstance(args, str) and isinstance(roles, list):
            result[f"public.{fn}({args.replace(' ', '')})"] = {
                str(role) for role in roles
            }
    return result


def main() -> None:
    authority = load(AUTHORITY)
    rollback = load(ROLLBACK)
    exposure = load(EXPOSURE)
    abuse_sql = text(ABUSE)
    gateway = text(GATEWAY)
    contract = text(CONTRACT)

    require(authority, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE33_DIRECT_RPC_PRIVILEGE_REVOCATION_ASSESSMENT",
        "baseline_main_sha": BASELINE,
        "current_state": STATE,
    }, "assessment authority")
    require(rollback, {
        "current_state": "POST_CUTOVER_ROLLBACK_PROOF_VERIFIED_CLEANUP_COMPLETE_EDGE_MODE",
    }, "rollback authority")
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
    }, "historical remote production boundary")

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
        "result": "PASS",
    }, "observation receipt")
    if int(observation.get("seconds_since_checkpoint", 0)) < 3600:
        fail("historical observation window shorter than Stage24 semantics")
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

    require(authority.get("security_advisor_gate", {}), {
        "rechecked_after_observation_window": True,
        "total_warning_count": 11,
        "anon_security_definer_warning_count": 5,
        "authenticated_security_definer_warning_count": 6,
        "target_direct_rpc_anon_warning_count": 5,
        "target_direct_rpc_authenticated_warning_count": 5,
        "issue_student_access_token_v2_authenticated_warning_count": 1,
        "unexpected_warning_count": 0,
        "result": "PASS_WITH_EXPECTED_PRE_REVOCATION_WARNINGS",
    }, "security advisor receipt")

    surface = authority.get("target_direct_rpc_surface", {})
    if set(surface.get("functions", [])) != TARGETS:
        fail("historical five-function target set drifted")
    require(surface, {
        "function_count": 5,
        "anon_execute_count": 5,
        "authenticated_execute_count": 5,
        "service_role_execute_count": 5,
        "direct_grants_intact_before_preparation": True,
        "issue_student_access_token_v2_is_target": False,
    }, "historical target surface")

    roles = normalized_exposures(exposure)
    expected = {signature: {"anon", "authenticated"} for signature in TARGETS}
    expected["public.issue_student_access_token_v2(uuid)"] = {"authenticated"}
    if roles != expected:
        fail("remote pre-revocation exposure authority no longer preserves historical assessment truth")

    # A later repo-only Stage33 migration is allowed only when the lifecycle-aware exposure
    # authority explicitly identifies it as not remotely applied. This preserves the historical
    # assessment without blocking valid downstream repository preparation.
    stage33_files = [
        path.name for path in (BACKEND / "migrations").glob("*stage33*revocation*.sql")
        if path.is_file()
    ]
    if stage33_files:
        transition = exposure.get("stage33_transition", {})
        if exposure.get("schema_version") != 2:
            fail("Stage33 migration appeared without lifecycle-aware exposure authority")
        if stage33_files != [STAGE33_MIGRATION_FILE]:
            fail("unexpected Stage33 revocation migration set")
        if exposure.get("current_state") != "STAGE33_REVOCATION_REPO_ONLY_REMOTE_PRE_REVOCATION":
            fail("historical assessment accepts migration only in repo-only pre-remote state")
        if transition.get("migration_ledger_state") != "repo_only" or transition.get("remote_applied") is not False:
            fail("Stage33 transition falsely claims remote revocation during historical assessment")

    for fragment in (
        'get_workout: "get_student_workout_v2"',
        'start_workout: "start_student_workout_v2"',
        'set_completion: "set_student_exercise_completion_v2"',
        'get_feedback_context: "get_student_feedback_context_v2"',
        'submit_feedback: "submit_student_workout_feedback_v2"',
        'Deno.env.get("SUPABASE_SECRET_KEYS")',
        'Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")',
    ):
        if fragment not in gateway:
            fail(f"gateway privileged backend drift: {fragment}")
    for fragment in (
        "StudentAccessTransportMode.edgeGateway;",
        "static const bool edgeGatewaySelected = true;",
        "static const bool automaticEdgeToDirectFallback = false;",
        "static const bool explicitRollbackRequested = false;",
        "static const bool explicitRollbackAuthorized = false;",
        "static const bool directRpcExecuteRevoked = false;",
    ):
        if fragment not in contract:
            fail(f"production source boundary drift: {fragment}")

    require(authority.get("decision", {}), {
        "observation_window_gate": "PASS",
        "security_advisor_recheck_gate": "PASS_WITH_EXPECTED_PRE_REVOCATION_WARNINGS",
        "repository_first_revocation_preparation_allowed": True,
        "remote_privilege_revocation_allowed_now": False,
        "incident_response_gate_promoted": False,
        "production_deployment_gate_promoted": False,
        "paid_ads_gate_promoted": False,
    }, "historical assessment decision")

    print("STAGE33_DIRECT_RPC_PRIVILEGE_REVOCATION_ASSESSMENT_GUARD=PASS")
    print(f"HISTORICAL_BASELINE_MAIN_SHA={BASELINE}")
    print(f"HISTORICAL_OBSERVED_AT_UTC={OBSERVED}")
    print("OBSERVATION_WINDOW_SECONDS=3600")
    print("HISTORICAL_SECURITY_POSTURE=quiet")
    print("HISTORICAL_SECURITY_ADVISOR_WARNINGS=11")
    print("REMOTE_PRE_REVOCATION_TARGETS=5")
    print("REMOTE_PRIVILEGE_REVOCATION_ALLOWED_BY_ASSESSMENT=false")
    print("PRODUCTION_ACTIVE_TRANSPORT=edgeGateway")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
