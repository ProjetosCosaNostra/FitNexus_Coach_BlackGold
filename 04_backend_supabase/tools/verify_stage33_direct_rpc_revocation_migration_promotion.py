from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
APP = ROOT / "03_app_flutter" / "fitnexus_app"

AUTHORITY = BACKEND / "stage33_direct_rpc_revocation_migration_promotion_authority.json"
PREPARATION = BACKEND / "stage33_direct_rpc_revocation_preparation_authority.json"
EXPOSURE = BACKEND / "security_definer_exposure_authority.json"
LEDGER = BACKEND / "migration_ledger_authority.json"
MIGRATION = BACKEND / "migrations" / "20260822022000_stage33_direct_rpc_revocation_and_post_revocation_fixture.sql"
CANDIDATE = BACKEND / "operations" / "stage33_direct_rpc_revocation_and_post_revocation_fixture_candidate.sql"
RECOVERY = BACKEND / "operations" / "stage33_direct_rpc_regrant_recovery.sql"
TEST = APP / "test" / "student_access_stage33_post_revocation_live_edge_proof_test.dart"
CONTRACT = APP / "lib" / "features" / "student" / "student_access_transport_contract.dart"
PROOF_WORKFLOW = ROOT / ".github" / "workflows" / "stage33_post_revocation_edge_runtime_live_proof.yml"

FAILURE_CLASS = "BGF-STAGE33-REVOCATION-MIGRATION-PROMOTION-254"
STATE = "REVOCATION_MIGRATION_REPO_ONLY_PROOF_SEAL_PENDING"
BASELINE = "2f8bd11ac0a4ba4e605807fb17c6c78ff3939041"
MIGRATION_NAME = "stage33_direct_rpc_revocation_and_post_revocation_fixture"
MIGRATION_BLOB = "8f079770f077913d94229df272583945320d943d"
CANDIDATE_BLOB = "08fbbf71ec51583c8e46792ed88b28825394e9f1"
RECOVERY_BLOB = "2a620b8a951d30bd4d9688158d36e9d1736b65a3"
TEST_BLOB = "d2882d6560a18e259afe74ccbc18d3d275d7f001"
TARGETS = (
    "get_student_feedback_context_v2(text)",
    "get_student_workout_v2(text)",
    "set_student_exercise_completion_v2(text,uuid,uuid,boolean,text)",
    "start_student_workout_v2(text,text)",
    "submit_student_workout_feedback_v2(text,uuid,integer,integer,integer,text,text,text)",
)


def fail(message: str) -> None:
    raise SystemExit(
        "STAGE33_DIRECT_RPC_REVOCATION_MIGRATION_PROMOTION_GUARD=FAIL\n"
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
    payload = f"blob {len(data)}\0".encode("ascii") + data
    return hashlib.sha1(payload).hexdigest()


def require(mapping: dict, expected: dict, label: str) -> None:
    for key, expected_value in expected.items():
        if mapping.get(key) != expected_value:
            fail(f"{label} drift: {key}")


def executable_body(source: str) -> str:
    # BGF-STAGE33-SQL-MARKER-COMMENT-COLLISION-256:
    # a marker-looking substring inside documentation/comments is not executable SQL.
    # Only a standalone trimmed marker line may begin the immutable do-block comparison.
    offset = 0
    for line in source.splitlines(keepends=True):
        if line.strip().lower() == "do $$":
            return source[offset:]
        offset += len(line)
    fail("SQL source missing standalone do-block marker")
    raise AssertionError("unreachable")


def main() -> None:
    # First prove the immutable Stage33 preparation and its exact downstream transition.
    preparation_guard = importlib.import_module(
        "verify_stage33_direct_rpc_revocation_preparation"
    )
    preparation_guard.main()

    authority = load(AUTHORITY)
    preparation = load(PREPARATION)
    exposure = load(EXPOSURE)
    ledger = load(LEDGER)
    migration = text(MIGRATION)
    candidate = text(CANDIDATE)
    recovery = text(RECOVERY)
    proof_test = text(TEST)
    contract = text(CONTRACT)

    require(authority, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE33_DIRECT_RPC_REVOCATION_MIGRATION_PROMOTION",
        "baseline_main_sha": BASELINE,
        "current_state": STATE,
    }, "promotion authority")
    if set(authority.get("failure_classes", [])) != {
        "BGF-STAGE33-PRIVILEGE-REVOCATION-PREMATURE-245",
        "BGF-STAGE33-POST-REVOCATION-FIXTURE-249",
        "BGF-STAGE33-REVOCATION-TARGET-DRIFT-250",
        "BGF-STAGE33-REVOCATION-SERVICE-ROLE-LOSS-251",
        "BGF-STAGE33-REGRANT-RECOVERY-SCOPE-252",
        "BGF-STAGE33-POST-REVOCATION-PROOF-SEAM-BYPASS-253",
        FAILURE_CLASS,
        "BGF-STAGE33-REVOCATION-PROOF-REEXECUTION-255",
        "BGF-STAGE33-SQL-MARKER-COMMENT-COLLISION-256",
    }:
        fail("promotion failure-class set drifted")

    require(preparation, {
        "current_state": "DIRECT_RPC_REVOCATION_CANDIDATE_STAGED_NO_REMOTE_MUTATION",
    }, "preparation authority")
    require(authority.get("preparation_receipt", {}), {
        "required_state": "DIRECT_RPC_REVOCATION_CANDIDATE_STAGED_NO_REMOTE_MUTATION",
        "pr": 90,
        "head_sha": "1a8419892c4a5329dc2d5a828ca7c914d1885776",
        "ci_run_id": 32545666853,
        "ci_job_id": 96963540504,
        "ci_result": "SUCCESS",
        "merge_main_sha": BASELINE,
    }, "preparation receipt")
    require(authority.get("fresh_pre_promotion_receipt", {}), {
        "source": "Supabase.execute_sql",
        "observed_at_utc": "2026-08-22T02:15:46.465445Z",
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
    }, "fresh pre-promotion receipt")

    failure_receipt = authority.get("guard_failure_receipt", {})
    require(failure_receipt, {
        "workflow_run_id": 32548083102,
        "workflow_job_id": 96970087080,
        "result": "FAIL_CLOSED_BEFORE_REMOTE_MUTATION",
        "failure_class": "BGF-STAGE33-SQL-MARKER-COMMENT-COLLISION-256",
        "migration_sql_changed": False,
        "remote_privilege_mutation_observed": False,
        "supabase_mutation_observed": False,
    }, "guard failure receipt")
    if failure_receipt.get("prevention_rule") != (
        "SQL executable marker extraction must match a standalone trimmed marker line exactly and must never accept comment/sub-string collisions."
    ):
        fail("SQL marker collision prevention rule drifted")

    migration_authority = authority.get("migration", {})
    require(migration_authority, {
        "name": MIGRATION_NAME,
        "repository_file": "04_backend_supabase/migrations/20260822022000_stage33_direct_rpc_revocation_and_post_revocation_fixture.sql",
        "repository_blob_sha": MIGRATION_BLOB,
        "source_candidate_file": "04_backend_supabase/operations/stage33_direct_rpc_revocation_and_post_revocation_fixture_candidate.sql",
        "source_candidate_blob_sha": CANDIDATE_BLOB,
        "executable_body_from_do_block_byte_identical": True,
        "migration_ledger_state": "repo_only",
        "remote_applied": False,
        "remote_version": None,
        "apply_count": 0,
        "atomic_fixture_and_privilege_cut": True,
        "exact_target_count": 5,
        "revokes_public_execute": True,
        "revokes_anon_execute": True,
        "revokes_authenticated_execute": True,
        "preserves_service_role_execute": True,
        "preserves_issue_student_access_token_v2_authenticated_execute": True,
        "requires_empty_customer_domain": True,
        "requires_quiet_60m_security_posture_at_apply": True,
    }, "migration authority")
    if git_blob_sha(MIGRATION) != MIGRATION_BLOB:
        fail("migration Git blob SHA drifted")
    if git_blob_sha(CANDIDATE) != CANDIDATE_BLOB:
        fail("source candidate Git blob SHA drifted")
    if git_blob_sha(RECOVERY) != RECOVERY_BLOB:
        fail("regrant recovery Git blob SHA drifted")
    if git_blob_sha(TEST) != TEST_BLOB:
        fail("focused test Git blob SHA drifted")
    if executable_body(migration) != executable_body(candidate):
        fail("promoted migration executable do-block differs from reviewed candidate")

    # Exact privilege cut and fixture invariants are present in the promoted body.
    lower = migration.lower()
    if lower.count("revoke execute on function public.") != 5:
        fail("promoted migration must revoke exactly five public functions")
    for target in TARGETS:
        if f"revoke execute on function public.{target}" not in lower:
            fail(f"promoted migration missing target: {target}")
    for fragment in (
        "from public, anon, authenticated;",
        "has_function_privilege('service_role'",
        "public.issue_student_access_token_v2(uuid)",
        "fitnexus-stage33-post-revocation-edge-proof-v1",
        "now() - interval '60 minutes'",
        "stage33_revocation_requires_empty_customer_domain",
        "stage33_revocation_security_observation_not_quiet",
        "stage33_revocation_postcondition_role_boundary_failed",
    ):
        if fragment not in lower:
            fail(f"promoted migration invariant missing: {fragment}")
    if "grant execute on function public." in lower:
        fail("promoted migration contains an execute grant")

    # Migration ledger is still pre-remote and has one exact Stage33 repo-only divergence.
    if ledger.get("baseline_main_sha") != BASELINE:
        fail("migration ledger promotion baseline drifted")
    if ledger.get("observed_at_utc") != "2026-08-22T02:15:46.465445Z":
        fail("migration ledger promotion observation drifted")
    repo_only = [
        row for row in ledger.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    ]
    if len(repo_only) != 1 or repo_only[0].get("name") != MIGRATION_NAME:
        fail("Stage33 migration must be the unique repo-only divergence")
    if repo_only[0].get("related_failure_class") != "BGF-STAGE33-PRIVILEGE-REVOCATION-PREMATURE-245":
        fail("Stage33 repo-only failure-class binding drifted")
    remote = {
        row.get("name"): row.get("version")
        for row in ledger.get("remote_migrations", []) if isinstance(row, dict)
    }
    if MIGRATION_NAME in remote:
        fail("Stage33 migration unexpectedly remote before proof seal")
    if remote.get("stage32_post_cutover_rollback_proof_cleanup") != "20260822003559":
        fail("Stage32 rollback cleanup receipt disappeared")

    require(exposure, {
        "schema_version": 2,
        "project_ref": "mceukeondizkwlpfxzgf",
        "current_state": "STAGE33_REVOCATION_REPO_ONLY_REMOTE_PRE_REVOCATION",
    }, "exposure authority")
    require(exposure.get("stage33_transition", {}), {
        "migration_name": MIGRATION_NAME,
        "migration_file": "04_backend_supabase/migrations/20260822022000_stage33_direct_rpc_revocation_and_post_revocation_fixture.sql",
        "migration_blob_sha": MIGRATION_BLOB,
        "migration_ledger_state": "repo_only",
        "remote_applied": False,
        "remote_version": None,
        "target_student_route_count": 5,
        "repository_target_anon_exposures": 0,
        "repository_target_authenticated_exposures": 1,
        "service_role_preserved_for_edge_backend": True,
        "issue_student_access_token_v2_preserved": True,
        "remote_revocation_allowed_now": False,
    }, "exposure transition")
    target_rows = exposure.get("repository_target_approved_exposures", [])
    if not isinstance(target_rows, list) or len(target_rows) != 1:
        fail("repository target exposure count must be one")
    if target_rows[0].get("function") != "issue_student_access_token_v2" or target_rows[0].get("roles") != ["authenticated"]:
        fail("repository target must preserve only authenticated issue_student_access_token_v2")

    require(authority.get("proof_and_recovery_assets", {}), {
        "focused_test_blob_sha": TEST_BLOB,
        "regrant_recovery_blob_sha": RECOVERY_BLOB,
        "regrant_is_migration": False,
        "automatic_regrant_allowed": False,
        "proof_uses_production_singleton": True,
        "proof_route_count": 5,
        "direct_http_denial_check_required_before_edge_test": True,
        "one_shot_workflow_sealed_before_remote_apply": False,
        "fallback_open_trigger_sealed_before_remote_apply": False,
    }, "proof/recovery assets")
    for forbidden in ("forVerification", "forAuthorizedRollbackProof", ".rpc(", ".functions.invoke("):
        if forbidden in proof_test:
            fail(f"focused post-revocation proof bypasses production singleton: {forbidden}")
    if "StudentAccessTransport.instance" not in proof_test:
        fail("focused post-revocation proof lost production singleton")

    for fragment in (
        "StudentAccessTransportMode.edgeGateway;",
        "static const bool edgeGatewaySelected = true;",
        "static const bool automaticEdgeToDirectFallback = false;",
        "static const bool explicitRollbackRequested = false;",
        "static const bool explicitRollbackAuthorized = false;",
        "static const bool directRpcExecuteRevoked = false;",
    ):
        if fragment not in contract:
            fail(f"production source contract drift: {fragment}")

    # Proof workflow MUST NOT exist yet; it belongs to the next sealed lifecycle.
    if PROOF_WORKFLOW.exists():
        fail("Stage33 post-revocation one-shot workflow appeared before promotion merge")

    require(authority.get("promotion_boundary", {}), {
        "migration_may_merge_after_full_ci": True,
        "migration_may_apply_after_this_pr_alone": False,
        "remote_privilege_revocation_allowed_now": False,
        "proof_workflow_must_be_on_main_before_apply": True,
        "proof_candidate_exact_head_must_be_sealed": True,
        "fallback_trigger_exact_head_must_be_sealed": True,
        "run_attempt_must_equal_one": True,
        "fresh_quiet_security_posture_required_immediately_before_apply": True,
        "fresh_security_advisor_required_immediately_before_apply": True,
        "regrant_recovery_must_remain_available_before_apply": True,
        "production_transport_must_remain_edge": True,
        "automatic_fallback_must_remain_false": True,
        "launch_gate_promotion": False,
    }, "promotion boundary")

    print("STAGE33_DIRECT_RPC_REVOCATION_MIGRATION_PROMOTION_GUARD=PASS")
    print(f"MIGRATION_NAME={MIGRATION_NAME}")
    print(f"MIGRATION_BLOB_SHA={MIGRATION_BLOB}")
    print(f"SOURCE_CANDIDATE_BLOB_SHA={CANDIDATE_BLOB}")
    print("MIGRATION_LEDGER_STATE=repo_only")
    print("REMOTE_APPLIED=false")
    print("REMOTE_PRIVILEGE_REVOCATION=false")
    print("REPOSITORY_TARGET_ANON_EXPOSURES=0")
    print("REPOSITORY_TARGET_AUTH_EXPOSURES=1_ISSUE_TOKEN_ONLY")
    print("SQL_EXECUTABLE_MARKER_MATCH=STANDALONE_LINE_ONLY")
    print("PROOF_WORKFLOW_SEALED=false")
    print("PRODUCTION_ACTIVE_TRANSPORT=edgeGateway")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
