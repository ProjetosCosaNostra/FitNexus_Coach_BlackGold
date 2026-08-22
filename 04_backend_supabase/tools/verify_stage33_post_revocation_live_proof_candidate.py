from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
APP = ROOT / "03_app_flutter" / "fitnexus_app"

AUTHORITY = BACKEND / "stage33_post_revocation_live_proof_candidate_authority.json"
PROMOTION = BACKEND / "stage33_direct_rpc_revocation_migration_promotion_authority.json"
LEDGER = BACKEND / "migration_ledger_authority.json"
EXPOSURE = BACKEND / "security_definer_exposure_authority.json"
MIGRATION = BACKEND / "migrations" / "20260822022000_stage33_direct_rpc_revocation_and_post_revocation_fixture.sql"
RECOVERY = BACKEND / "operations" / "stage33_direct_rpc_regrant_recovery.sql"
TEST = APP / "test" / "student_access_stage33_post_revocation_live_edge_proof_test.dart"
CONTRACT = APP / "lib" / "features" / "student" / "student_access_transport_contract.dart"
PROOF_WORKFLOW = ROOT / ".github" / "workflows" / "stage33_post_revocation_edge_runtime_live_proof.yml"

FAILURE_CLASS = "BGF-STAGE33-POST-REVOCATION-CANDIDATE-DRIFT-257"
STATE = "POST_REVOCATION_PROOF_CANDIDATE_FROZEN_PRE_REMOTE_APPLY"
BASELINE = "c64222cc0dc22886dcfe569b2629a5c9ea2efb71"
MIGRATION_NAME = "stage33_direct_rpc_revocation_and_post_revocation_fixture"
MIGRATION_BLOB = "8f079770f077913d94229df272583945320d943d"
RECOVERY_BLOB = "2a620b8a951d30bd4d9688158d36e9d1736b65a3"
TEST_BLOB = "d2882d6560a18e259afe74ccbc18d3d275d7f001"


def fail(message: str) -> None:
    raise SystemExit(
        "STAGE33_POST_REVOCATION_LIVE_PROOF_CANDIDATE_GUARD=FAIL\n"
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
    for key, value in expected.items():
        if mapping.get(key) != value:
            fail(f"{label} drift: {key}")


def main() -> None:
    # The migration-promotion lifecycle must remain valid before a candidate is trusted.
    promotion_guard = importlib.import_module(
        "verify_stage33_direct_rpc_revocation_migration_promotion"
    )
    promotion_guard.main()

    authority = load(AUTHORITY)
    promotion = load(PROMOTION)
    ledger = load(LEDGER)
    exposure = load(EXPOSURE)
    test = text(TEST)
    contract = text(CONTRACT)

    require(authority, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE33_POST_REVOCATION_LIVE_PROOF_CANDIDATE",
        "baseline_main_sha": BASELINE,
        "current_state": STATE,
    }, "candidate authority")
    if set(authority.get("failure_classes", [])) != {
        FAILURE_CLASS,
        "BGF-STAGE33-POST-REVOCATION-PROOF-SEAM-BYPASS-253",
        "BGF-STAGE33-REVOCATION-PROOF-REEXECUTION-255",
        "BGF-STAGE33-PROOF-BEFORE-REMOTE-REVOCATION-258",
    }:
        fail("candidate failure-class set drifted")

    require(promotion, {
        "current_state": "REVOCATION_MIGRATION_REPO_ONLY_PROOF_SEAL_PENDING",
        "baseline_main_sha": "2f8bd11ac0a4ba4e605807fb17c6c78ff3939041",
    }, "promotion authority")
    require(authority.get("promotion_receipt", {}), {
        "promotion_pr": 91,
        "promotion_head_sha": "9f34e5e89b1e19e8ccc6b59a0fb6b07f76a35e4b",
        "quality_gate_run_id": 32548219593,
        "quality_gate_job_id": 96970462892,
        "quality_gate_result": "SUCCESS",
        "postgres_compat_run_id": 32548219583,
        "postgres_compat_job_id": 96970463027,
        "postgres_compat_result": "SUCCESS",
        "merge_main_sha": BASELINE,
    }, "promotion receipt")

    migration = authority.get("revocation_migration", {})
    require(migration, {
        "name": MIGRATION_NAME,
        "repository_blob_sha": MIGRATION_BLOB,
        "migration_ledger_state": "repo_only",
        "remote_applied": False,
        "remote_version": None,
        "apply_count": 0,
        "remote_apply_required_before_live_proof_event": True,
    }, "revocation migration")
    if git_blob_sha(MIGRATION) != MIGRATION_BLOB:
        fail("revocation migration blob drifted")
    if git_blob_sha(RECOVERY) != RECOVERY_BLOB:
        fail("regrant recovery blob drifted")
    if git_blob_sha(TEST) != TEST_BLOB:
        fail("focused proof test blob drifted")

    remote = {
        row.get("name"): row.get("version")
        for row in ledger.get("remote_migrations", []) if isinstance(row, dict)
    }
    if MIGRATION_NAME in remote:
        fail("Stage33 revocation migration is already remote before proof seal")
    repo_only = [
        row for row in ledger.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    ]
    if len(repo_only) != 1 or repo_only[0].get("name") != MIGRATION_NAME:
        fail("Stage33 revocation migration must remain the sole repo-only divergence")

    require(exposure, {
        "schema_version": 2,
        "current_state": "STAGE33_REVOCATION_REPO_ONLY_REMOTE_PRE_REVOCATION",
    }, "exposure authority")
    transition = exposure.get("stage33_transition", {})
    require(transition, {
        "migration_name": MIGRATION_NAME,
        "migration_ledger_state": "repo_only",
        "remote_applied": False,
        "remote_version": None,
        "remote_revocation_allowed_now": False,
    }, "exposure transition")

    proof = authority.get("focused_proof", {})
    require(proof, {
        "blob_sha": TEST_BLOB,
        "enabled_environment": "STAGE33_POST_REVOCATION_LIVE_PROOF_ENABLED",
        "production_transport_object": "StudentAccessTransport.instance",
        "route_count": 5,
        "for_verification_factory_allowed": False,
        "authorized_rollback_factory_allowed": False,
        "direct_rpc_calls_allowed": False,
        "raw_edge_function_calls_allowed": False,
        "direct_http_denial_check_is_workflow_owned": True,
    }, "focused proof")
    if proof.get("route_sequence") != [
        "get_workout", "start_workout", "set_completion",
        "get_feedback_context", "submit_feedback",
    ]:
        fail("focused proof route sequence drifted")
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
    ):
        if fragment not in test:
            fail(f"focused proof source drift: {fragment}")
    for forbidden in ("forVerification", "forAuthorizedRollbackProof", ".rpc(", ".functions.invoke("):
        if forbidden in test:
            fail(f"focused proof seam bypass: {forbidden}")

    require(authority.get("production_boundary", {}), {
        "active_transport": "edgeGateway",
        "automatic_edge_to_direct_fallback": False,
        "explicit_rollback_requested": False,
        "explicit_rollback_authorized": False,
        "direct_rpc_execute_revoked_source_flag": False,
        "source_flag_may_self_promote_in_candidate": False,
    }, "production boundary")
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

    recovery = authority.get("recovery_boundary", {})
    require(recovery, {
        "blob_sha": RECOVERY_BLOB,
        "automatic_execution_allowed": False,
        "execution_allowed_before_failed_live_proof": False,
    }, "recovery boundary")

    boundary = authority.get("candidate_boundary", {})
    require(boundary, {
        "must_remain_draft_until_remote_revocation_applied": True,
        "must_never_merge": True,
        "head_must_be_frozen_after_candidate_ci": True,
        "proof_event_may_be_delivered_before_remote_apply": False,
        "proof_run_attempt_must_equal_one": True,
        "proof_rerun_allowed": False,
        "fallback_trigger_must_never_merge": True,
        "launch_gate_promotion": False,
    }, "candidate boundary")

    # The one-shot workflow belongs to the next seal branch and must not be in this candidate.
    if PROOF_WORKFLOW.exists():
        fail("post-revocation live proof workflow exists in proof candidate before seal")

    print("STAGE33_POST_REVOCATION_LIVE_PROOF_CANDIDATE_GUARD=PASS")
    print(f"BASELINE_MAIN_SHA={BASELINE}")
    print(f"MIGRATION_BLOB_SHA={MIGRATION_BLOB}")
    print(f"FOCUSED_TEST_BLOB_SHA={TEST_BLOB}")
    print("MIGRATION_LEDGER_STATE=repo_only")
    print("REMOTE_REVOCATION_APPLIED=false")
    print("PROOF_EVENT_ALLOWED_NOW=false")
    print("PROOF_ROUTE_COUNT=5")
    print("PRODUCTION_ACTIVE_TRANSPORT=edgeGateway")
    print("CANDIDATE_MERGE_ALLOWED=false")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
