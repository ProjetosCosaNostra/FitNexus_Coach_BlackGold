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

STATE = "POST_CUTOVER_EDGE_RUNTIME_PROOF_R1_VERIFIED_CLEANUP_REPO_ONLY"
CLEANUP_NAME = "stage32_post_cutover_live_proof_r1_cleanup"
CLEANUP_FAILURE = "BGF-STAGE32-POST-CUTOVER-R1-CLEANUP-239"
EVENT_FAILURE = "BGF-GITHUB-R1-READY-EVENT-NONMATERIALIZATION-238"
PROOF_RUN = 32532170382
PROOF_JOB = 96926178484
PROOF_HEAD = "344433bf502b519563fe328ab71e59249766e3dd"
TRIGGER_HEAD = "65e35282aa0e004134807553545e0859512cdef6"
BASELINE = "6be68c35e4e7f1ec4e69bc0c8a9a872b62abad48"
LEDGER_OBSERVED = "2026-08-21T22:18:35.737097Z"
PROOF_WINDOW = "2026-08-21 22:15:00+00"


def fail(message: str, failure_class: str = CLEANUP_FAILURE) -> None:
    raise SystemExit(
        "STAGE32_POST_CUTOVER_LIVE_PROOF_R1_CLEANUP_PREPARATION_GUARD=FAIL\n"
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
    cleanup = text(CLEANUP)
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

    proof = authority.get("sealed_proof", {})
    require(
        proof,
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

    delivery = authority.get("event_delivery_receipt", {})
    require(
        delivery,
        {
            "preferred_event": "ready_for_review",
            "preferred_event_delivered_on_pr": 77,
            "new_r1_workflow_materialized_on_preferred_event": False,
            "historical_r0_workflow_materialized_and_skipped": True,
            "stage31_workflow_materialized_and_skipped": True,
            "fallback_event": "opened",
            "fallback_pr": 79,
            "fallback_head_sha": TRIGGER_HEAD,
            "new_r1_workflow_materialized_on_fallback": True,
            "proof_head_changed_for_fallback": False,
            "fallback_merge_allowed": False,
        },
        "R1 event delivery receipt",
    )

    pre = authority.get("pre_event_live_gate", {})
    require(
        pre,
        {
            "observed_at_utc": "2026-08-21T22:14:46.513334Z",
            "workout_sessions": 0,
            "workout_logs": 0,
            "workout_feedback": 0,
            "expected_active_link": 1,
            "ttl_over_60_minutes": True,
            "fixture_command_receipts": 0,
            "fixture_rate_buckets": 0,
            "fixture_security_events": 0,
            "fixture_security_signals": 0,
            "rpc_count": 5,
            "all_five_anon_execute_intact": True,
            "all_five_authenticated_execute_intact": True,
        },
        "pre-event live gate",
    )
    if not isinstance(pre.get("ttl_minutes_remaining"), (int, float)) or pre["ttl_minutes_remaining"] <= 60:
        fail("pre-event TTL interlock was not satisfied")

    post = authority.get("post_proof_database_receipt", {})
    require(
        post,
        {
            "observed_at_utc": "2026-08-21T22:17:41.499084Z",
            "workout_sessions": 1,
            "workout_logs": 1,
            "workout_feedback": 1,
            "student_status": "Treino concluído",
            "student_adherence": 100,
            "student_last_workout": "Stage32 Synthetic Plan",
            "session_id": "29721756-f091-4b33-9106-82a253e9f9c8",
            "session_status": "completed",
            "exercise_log_id": "07df75e0-36f2-4ce3-b090-4d72261e0717",
            "exercise_completed": True,
            "feedback_id": "58972689-2208-4ee0-ab34-8ebe75c0f6cb",
            "feedback_perceived_exertion": 5,
            "feedback_pain_score": 0,
            "feedback_energy_score": 4,
            "feedback_pain_location": None,
            "feedback_note": None,
            "command_receipts": 3,
            "fixture_rate_buckets": 5,
            "fixture_security_events": 3,
            "fixture_security_signals": 0,
            "growth_events": 5,
            "growth_attribution": 0,
            "rpc_count": 5,
            "all_five_anon_execute_intact": True,
            "all_five_authenticated_execute_intact": True,
        },
        "post-proof database receipt",
    )
    if post.get("command_ids") != [
        "32000000000000000000000000000001",
        "32000000000000000000000000000002",
        "32000000000000000000000000000003",
    ]:
        fail("R1 command receipt identity/order drifted")

    window = authority.get("proof_window_receipt", {})
    require(
        window,
        {
            "observed_at_utc": LEDGER_OBSERVED,
            "proof_window_started_at_utc": "2026-08-21T22:15:00Z",
            "global_network_bucket_count": 5,
            "each_request_count": 1,
            "network_origin_or_hash_recorded_in_repository": False,
            "subscription_authority_event": "trial_initialized",
            "unexpected_domain_mutation_counts_all_zero": True,
        },
        "proof-window receipt",
    )
    if set(window.get("operations", [])) != {
        "get_workout", "start_workout", "set_completion", "get_feedback_context", "submit_feedback"
    }:
        fail("proof-window operation set drifted")
    if set(window.get("growth_event_names", [])) != {
        "trial_started", "student_created", "training_created_or_duplicated", "training_delivered", "workout_logged"
    }:
        fail("growth proof receipt drifted")

    repo_only = [
        row for row in ledger.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    ]
    if len(repo_only) != 1:
        fail("cleanup migration must be the unique repo_only divergence")
    if repo_only[0].get("name") != CLEANUP_NAME or repo_only[0].get("related_failure_class") != CLEANUP_FAILURE:
        fail("cleanup repo_only divergence identity drifted")
    remote = {
        row.get("name"): row.get("version")
        for row in ledger.get("remote_migrations", []) if isinstance(row, dict)
    }
    if remote.get("stage32_post_cutover_edge_runtime_fixture") != "20260821171334":
        fail("Stage32 fixture remote receipt disappeared")
    if remote.get("stage32_rearm_expired_fixture_r1") != "20260821214005":
        fail("Stage32 rearm remote receipt disappeared")
    if CLEANUP_NAME in remote:
        fail("cleanup self-attested as remotely applied before merge/apply")
    if ledger.get("baseline_main_sha") != BASELINE or ledger.get("observed_at_utc") != LEDGER_OBSERVED:
        fail("cleanup ledger baseline/observation drifted")

    cleanup_authority = authority.get("cleanup", {})
    require(
        cleanup_authority,
        {
            "migration_file": "04_backend_supabase/migrations/20260821222000_stage32_post_cutover_live_proof_r1_cleanup.sql",
            "migration_name": CLEANUP_NAME,
            "migration_ledger_state": "repo_only",
            "remote_applied": False,
            "remote_version": None,
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
            "cleanup_completed": False,
        },
        "cleanup authority",
    )

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
        if fragment not in cleanup:
            fail(f"cleanup SQL drift: {fragment}")
    lower = cleanup.lower()
    if "origin_hash" in lower:
        fail("cleanup SQL embedded a network-origin hash selector")
    if lower.count("delete from private.student_access_network_rate_buckets") != 1:
        fail("cleanup must delete global network buckets exactly once")
    security_pos = lower.find("delete from private.student_access_security_events")
    org_pos = lower.find("delete from public.organizations")
    if security_pos < 0 or org_pos < 0 or security_pos > org_pos:
        fail("security events are not deleted before organization/link cascade")

    # Cross-check the immutable pre-execution seal. The execution receipt lives only
    # in the newer cleanup authority; the old seal remains a historical snapshot.
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

    boundary = authority.get("production_boundary", {})
    require(
        boundary,
        {
            "active_transport": "edgeGateway",
            "production_singleton": "StudentAccessTransport.instance",
            "automatic_edge_to_direct_fallback": False,
            "direct_rpc_execute_revoked": False,
            "post_cutover_live_proof_verified": True,
            "post_cutover_rollback_verified": False,
            "launch_gate_promotion": False,
        },
        "production boundary",
    )
    rules = authority.get("promotion_rules", {})
    for key in (
        "may_reexecute_r0_proof",
        "may_reexecute_r1_proof",
        "may_apply_cleanup_before_ci_and_merge",
        "may_use_execute_sql_for_cleanup_dml",
        "may_revoke_direct_rpc_execute_before_cleanup_and_post_cutover_rollback_proof",
        "may_promote_launch_gates",
    ):
        if rules.get(key) is not False:
            fail(f"cleanup authority gained prohibited permission: {key}")
    if rules.get("post_cutover_rollback_proof_required_after_cleanup") is not True:
        fail("post-cutover rollback interlock disappeared")

    print("STAGE32_POST_CUTOVER_LIVE_PROOF_R1_CLEANUP_PREPARATION_GUARD=PASS")
    print(f"CURRENT_STATE={STATE}")
    print(f"PROOF_RUN={PROOF_RUN}")
    print(f"PROOF_JOB={PROOF_JOB}")
    print("ALL_FIVE_ROUTES_VERIFIED=true")
    print("PRODUCTION_SINGLETON_VERIFIED=true")
    print("PRODUCTION_ACTIVE_TRANSPORT=edgeGateway")
    print("PROOF_REEXECUTION_ALLOWED=false")
    print(f"CLEANUP_MIGRATION={CLEANUP_NAME}")
    print("CLEANUP_LEDGER=REPO_ONLY")
    print("CLEANUP_REMOTE_APPLIED=false")
    print("DIRECT_RPC_GRANTS=INTACT")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")
    print("POST_CUTOVER_ROLLBACK_PROOF_REQUIRED=true")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
