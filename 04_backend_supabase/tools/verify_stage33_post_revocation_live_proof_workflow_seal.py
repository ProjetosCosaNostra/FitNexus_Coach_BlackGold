from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
APP = ROOT / "03_app_flutter" / "fitnexus_app"

AUTHORITY = BACKEND / "stage33_post_revocation_live_proof_workflow_seal_authority.json"
PROMOTION = BACKEND / "stage33_direct_rpc_revocation_migration_promotion_authority.json"
LEDGER = BACKEND / "migration_ledger_authority.json"
EXPOSURE = BACKEND / "security_definer_exposure_authority.json"
WORKFLOW = ROOT / ".github" / "workflows" / "stage33_post_revocation_edge_runtime_live_proof.yml"
MIGRATION = BACKEND / "migrations" / "20260822022000_stage33_direct_rpc_revocation_and_post_revocation_fixture.sql"
RECOVERY = BACKEND / "operations" / "stage33_direct_rpc_regrant_recovery.sql"
TEST = APP / "test" / "student_access_stage33_post_revocation_live_edge_proof_test.dart"
CONTRACT = APP / "lib" / "features" / "student" / "student_access_transport_contract.dart"

FAILURE_CLASS = "BGF-STAGE33-POST-REVOCATION-WORKFLOW-SEAL-259"
STATE = "POST_REVOCATION_ONE_SHOT_SEALED_REMOTE_APPLY_PENDING"
BASELINE = "c64222cc0dc22886dcfe569b2629a5c9ea2efb71"
CANDIDATE_HEAD = "b8123abb7f0dda364f49d9f7342e5887c7da6553"
FALLBACK_HEAD = "d2ac5815532ac1671c942ac6e8d491c7ac5ecd89"
WORKFLOW_BLOB = "5490d1569f7de8c93e5822426d2c75d588a0e3ef"
MIGRATION_NAME = "stage33_direct_rpc_revocation_and_post_revocation_fixture"
MIGRATION_BLOB = "8f079770f077913d94229df272583945320d943d"
RECOVERY_BLOB = "2a620b8a951d30bd4d9688158d36e9d1736b65a3"
TEST_BLOB = "d2882d6560a18e259afe74ccbc18d3d275d7f001"


def fail(message: str) -> None:
    raise SystemExit(
        "STAGE33_POST_REVOCATION_LIVE_PROOF_WORKFLOW_SEAL_GUARD=FAIL\n"
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
    authority = load(AUTHORITY)
    promotion = load(PROMOTION)
    ledger = load(LEDGER)
    exposure = load(EXPOSURE)
    workflow = text(WORKFLOW)
    test = text(TEST)
    contract = text(CONTRACT)

    require(authority, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE33_POST_REVOCATION_LIVE_PROOF_WORKFLOW_SEAL",
        "baseline_main_sha": BASELINE,
        "current_state": STATE,
    }, "workflow seal authority")
    if set(authority.get("failure_classes", [])) != {
        "BGF-STAGE33-POST-REVOCATION-CANDIDATE-DRIFT-257",
        "BGF-STAGE33-PROOF-BEFORE-REMOTE-REVOCATION-258",
        FAILURE_CLASS,
        "BGF-STAGE33-DIRECT-DENIAL-PROOF-BYPASS-260",
        "BGF-STAGE33-REVOCATION-PROOF-REEXECUTION-255",
    }:
        fail("workflow seal failure-class set drifted")

    require(promotion, {
        "current_state": "REVOCATION_MIGRATION_REPO_ONLY_PROOF_SEAL_PENDING",
        "baseline_main_sha": "2f8bd11ac0a4ba4e605807fb17c6c78ff3939041",
    }, "migration promotion authority")
    require(authority.get("migration_promotion_receipt", {}), {
        "pr": 91,
        "head_sha": "9f34e5e89b1e19e8ccc6b59a0fb6b07f76a35e4b",
        "quality_gate_run_id": 32548219593,
        "quality_gate_job_id": 96970462892,
        "quality_gate_result": "SUCCESS",
        "postgres_compat_run_id": 32548219583,
        "postgres_compat_job_id": 96970463027,
        "postgres_compat_result": "SUCCESS",
        "merge_main_sha": BASELINE,
    }, "migration promotion receipt")

    require(authority.get("proof_candidate", {}), {
        "pr": 92,
        "branch": "blackgold/stage33-post-revocation-live-proof-candidate",
        "head_sha": CANDIDATE_HEAD,
        "quality_gate_run_id": 32548471258,
        "quality_gate_job_id": 96971104493,
        "quality_gate_result": "SUCCESS",
        "draft": True,
        "head_frozen": True,
        "must_never_merge": True,
    }, "proof candidate receipt")
    require(authority.get("fallback_trigger", {}), {
        "branch": "blackgold/stage33-post-revocation-live-proof-open-trigger",
        "head_sha": FALLBACK_HEAD,
        "marker_file": "04_backend_supabase/stage33_post_revocation_live_proof_open_trigger_marker.json",
        "pr": None,
        "opened": False,
        "open_allowed_before_preferred_event_failure": False,
        "must_never_merge": True,
        "head_frozen": True,
    }, "fallback trigger receipt")

    if git_blob_sha(WORKFLOW) != WORKFLOW_BLOB:
        fail("sealed workflow Git blob SHA drifted")
    if git_blob_sha(MIGRATION) != MIGRATION_BLOB:
        fail("revocation migration blob drifted")
    if git_blob_sha(RECOVERY) != RECOVERY_BLOB:
        fail("regrant recovery blob drifted")
    if git_blob_sha(TEST) != TEST_BLOB:
        fail("focused proof test blob drifted")

    workflow_authority = authority.get("workflow", {})
    require(workflow_authority, {
        "preferred_event": "pull_request.ready_for_review",
        "preferred_exact_pr": 92,
        "preferred_exact_branch": "blackgold/stage33-post-revocation-live-proof-candidate",
        "preferred_exact_head_sha": CANDIDATE_HEAD,
        "fallback_event": "pull_request.opened",
        "fallback_exact_branch": "blackgold/stage33-post-revocation-live-proof-open-trigger",
        "fallback_exact_head_sha": FALLBACK_HEAD,
        "run_attempt_required": 1,
        "workflow_dispatch_allowed": False,
        "schedule_allowed": False,
        "synchronize_allowed": False,
        "reopened_allowed": False,
        "checkout_exact_candidate_head": True,
        "candidate_guard_before_network_proof": True,
        "service_role_secret_allowed": False,
        "direct_http_denial_before_edge_test": True,
        "direct_http_denial_target": "public.get_student_workout_v2(text)",
        "direct_http_allowed_statuses": [401, 403, 404],
        "five_route_edge_proof_required": True,
        "focused_test_file": "03_app_flutter/fitnexus_app/test/student_access_stage33_post_revocation_live_edge_proof_test.dart",
    }, "workflow authority")

    required_fragments = (
        "types: [ready_for_review, opened]",
        "github.event.pull_request.number == 92",
        "github.event.pull_request.head.ref == 'blackgold/stage33-post-revocation-live-proof-candidate'",
        f"github.event.pull_request.head.sha == '{CANDIDATE_HEAD}'",
        "github.event.pull_request.head.ref == 'blackgold/stage33-post-revocation-live-proof-open-trigger'",
        f"github.event.pull_request.head.sha == '{FALLBACK_HEAD}'",
        "github.run_attempt == 1",
        f"ref: {CANDIDATE_HEAD}",
        "verify_stage33_post_revocation_live_proof_candidate.py",
        "fitnexus-stage33-post-revocation-edge-proof-v1",
        "::add-mask::$TOKEN",
        "/rest/v1/rpc/get_student_workout_v2",
        "status not in {401, 403, 404}",
        "direct_rpc_still_callable",
        "synthetic_fixture_leaked",
        "flutter test test/student_access_stage33_post_revocation_live_edge_proof_test.dart --reporter expanded",
        "PROOF_REEXECUTION_ALLOWED=false",
        "CANDIDATE_MERGE_ALLOWED=false",
        "FALLBACK_TRIGGER_MERGE_ALLOWED=false",
        "LAUNCH_GATE_PROMOTION=DENIED",
    )
    for fragment in required_fragments:
        if fragment not in workflow:
            fail(f"sealed workflow drift: {fragment}")

    for forbidden in (
        "workflow_dispatch:",
        "schedule:",
        "synchronize",
        "reopened",
        "SUPABASE_SERVICE_ROLE_KEY",
        "SUPABASE_SECRET_KEYS",
        "sb_secret_",
    ):
        if forbidden in workflow:
            fail(f"sealed workflow contains forbidden trigger/credential: {forbidden}")

    candidate_guard_pos = workflow.find("verify_stage33_post_revocation_live_proof_candidate.py")
    denial_pos = workflow.find("Prove direct anonymous RPC execution is denied after revocation")
    flutter_pos = workflow.find("Execute sealed five-route production Edge proof once")
    if min(candidate_guard_pos, denial_pos, flutter_pos) < 0 or not (
        candidate_guard_pos < denial_pos < flutter_pos
    ):
        fail("candidate guard/direct-denial/Edge-proof order drifted")

    migration = authority.get("revocation_migration", {})
    require(migration, {
        "name": MIGRATION_NAME,
        "repository_blob_sha": MIGRATION_BLOB,
        "migration_ledger_state_before_apply": "repo_only",
        "remote_applied_at_seal_creation": False,
        "remote_version": None,
        "apply_count": 0,
        "apply_once_only_after_seal_merge": True,
    }, "revocation migration boundary")
    remote = {
        row.get("name"): row.get("version")
        for row in ledger.get("remote_migrations", []) if isinstance(row, dict)
    }
    if MIGRATION_NAME in remote:
        fail("Stage33 revocation migration unexpectedly remote before seal merge")
    repo_only = [
        row for row in ledger.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    ]
    if len(repo_only) != 1 or repo_only[0].get("name") != MIGRATION_NAME:
        fail("Stage33 revocation migration must remain sole repo-only divergence")

    require(exposure, {
        "schema_version": 2,
        "current_state": "STAGE33_REVOCATION_REPO_ONLY_REMOTE_PRE_REVOCATION",
    }, "security definer exposure authority")

    for forbidden in ("forVerification", "forAuthorizedRollbackProof", ".rpc(", ".functions.invoke("):
        if forbidden in test:
            fail(f"focused proof bypass drift: {forbidden}")
    if "StudentAccessTransport.instance" not in test:
        fail("focused proof no longer uses production singleton")

    require(authority.get("production_boundary", {}), {
        "active_transport": "edgeGateway",
        "automatic_edge_to_direct_fallback": False,
        "explicit_rollback_requested": False,
        "explicit_rollback_authorized": False,
        "source_direct_rpc_execute_revoked": False,
        "source_flag_promotion_during_proof_allowed": False,
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

    require(authority.get("pre_apply_gate", {}), {
        "fresh_gate_required_after_seal_merge": True,
        "security_posture_must_be": "quiet",
        "signals_60m_must_be": 0,
        "security_events_60m_must_be": 0,
        "network_buckets_60m_must_be": 0,
        "customer_runtime_domain_must_be_empty": True,
        "target_anon_execute_before_apply": 5,
        "target_authenticated_execute_before_apply": 5,
        "target_service_role_execute_before_apply": 5,
        "issue_token_authenticated_execute_required": True,
        "security_advisor_recheck_required": True,
        "expected_pre_revocation_advisor_warnings": 11,
        "receipt": None,
        "result": "PENDING",
    }, "pre-apply gate")
    require(authority.get("execution_receipt", {}), {
        "workflow_run_id": None,
        "workflow_job_id": None,
        "run_attempt": None,
        "result": None,
        "delivery_path": None,
        "proof_reexecution_allowed": False,
    }, "execution receipt")
    require(authority.get("seal_boundary", {}), {
        "seal_must_merge_before_remote_apply": True,
        "remote_apply_allowed_before_seal_merge": False,
        "proof_event_allowed_before_verified_remote_apply": False,
        "candidate_ready_for_review_allowed_before_verified_remote_apply": False,
        "fallback_open_allowed_before_preferred_event_failure": False,
        "candidate_merge_allowed": False,
        "fallback_merge_allowed": False,
        "proof_rerun_allowed": False,
        "launch_gate_promotion": False,
    }, "seal boundary")

    print("STAGE33_POST_REVOCATION_LIVE_PROOF_WORKFLOW_SEAL_GUARD=PASS")
    print(f"WORKFLOW_BLOB_SHA={WORKFLOW_BLOB}")
    print(f"PROOF_CANDIDATE_HEAD={CANDIDATE_HEAD}")
    print(f"FALLBACK_TRIGGER_HEAD={FALLBACK_HEAD}")
    print("MIGRATION_LEDGER_STATE=repo_only")
    print("REMOTE_REVOCATION_APPLIED=false")
    print("DIRECT_HTTP_DENIAL_REQUIRED=true")
    print("EDGE_PROOF_ROUTES=5")
    print("SERVICE_ROLE_SECRET_IN_WORKFLOW=false")
    print("PROOF_EVENT_ALLOWED_NOW=false")
    print("PROOF_REEXECUTION_ALLOWED=false")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
