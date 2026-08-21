from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "student_access_client_runtime_smoke_authority.json"
CUTOVER = BACKEND / "student_access_client_cutover_authority.json"
LEDGER = BACKEND / "migration_ledger_authority.json"
FIXTURE_SQL = BACKEND / "migrations" / "20260821063000_stage30_edge_runtime_smoke_fixture.sql"
CLEANUP_SQL = BACKEND / "migrations" / "20260821081005_stage30_edge_runtime_smoke_cleanup.sql"
LIVE = BACKEND / "tools" / "verify_student_access_stage30_edge_runtime_live.py"

FAILURE_CLASS = "BGF-STAGE30-RUNTIME-SMOKE-FIXTURE-RESIDUE-203"
REEXECUTION_CLASS = "BGF-STAGE30-RUNTIME-SMOKE-PROOF-REEXECUTION-204"
DATA_LEAK_CLASS = "BGF-STAGE30-RUNTIME-SMOKE-RESPONSE-DATA-LEAK-205"
COMMAND_FLOW_CLASS = "BGF-STAGE30-RUNTIME-SMOKE-COMMAND-FLOW-206"
CLEANUP_CLASS = "BGF-STAGE30-RUNTIME-SMOKE-CLEANUP-SCOPE-207"
FIXTURE_NAME = "stage30_edge_runtime_smoke_fixture"
CLEANUP_NAME = "stage30_edge_runtime_smoke_cleanup"
FIXTURE_REMOTE_VERSION = "20260821075532"
CLEANUP_REMOTE_VERSION = "20260821083507"
SEALED_RUN = 32461357789
SEED = "fitnexus-stage30-edge-runtime-smoke-fixture-v1"

STATE_REPO = "EDGE_RUNTIME_SMOKE_FIXTURE_REPO_ONLY"
STATE_REMOTE = "EDGE_RUNTIME_SMOKE_FIXTURE_REMOTE_LIVE_PROOF_PENDING"
STATE_PROVEN = "EDGE_RUNTIME_SMOKE_LIVE_VERIFIED_CLEANUP_PENDING"
STATE_CLEANUP_REPO = "EDGE_RUNTIME_SMOKE_LIVE_VERIFIED_CLEANUP_REPO_ONLY"
STATE_CLEAN = "EDGE_RUNTIME_SMOKE_LIVE_VERIFIED_CLEANUP_COMPLETE"
ALLOWED_STATES = {STATE_REPO, STATE_REMOTE, STATE_PROVEN, STATE_CLEANUP_REPO, STATE_CLEAN}
BASELINES = {
    STATE_REPO: "59385ef6a7b4d8ad90703b1cbb52c0755f1f8948",
    STATE_REMOTE: "ff29a59626f7a4ab5e198cfef2c27b5cd1dfde1b",
    STATE_PROVEN: "ff29a59626f7a4ab5e198cfef2c27b5cd1dfde1b",
    STATE_CLEANUP_REPO: "aba1937b426c1bb681e4e39065fbfb840653c41e",
    STATE_CLEAN: "0a240a0481bcc13794b887e9ff755c058140172d",
}
ROUTES = ["get_workout", "start_workout", "set_completion", "get_feedback_context", "submit_feedback"]
EXPECTED_IDS = {
    "user_id": "33e39af7-f470-510e-8a9c-fc70b16ba26e",
    "organization_id": "a0749405-6367-52d5-ad8b-5115b8d3a905",
    "student_id": "81d3be6f-824e-59bc-8fa0-27acf046d6d3",
    "plan_id": "82b92191-a8e3-5bb2-8f5d-fec9a59a57bb",
    "exercise_id": "fe116050-9061-5627-8e3a-dedd863d6447",
    "link_id": "53dfab53-5ff8-573a-ab2a-faaea24107db",
}


def fail(message: str) -> None:
    raise SystemExit("STUDENT_ACCESS_CLIENT_RUNTIME_SMOKE_GUARD=FAIL\n" + message)


def read(path: Path) -> str:
    if not path.is_file():
        fail(f"missing source: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def load(path: Path) -> dict:
    try:
        value = json.loads(read(path))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path.relative_to(ROOT)}: {exc}")
    if not isinstance(value, dict):
        fail(f"expected JSON object: {path.relative_to(ROOT)}")
    return value


def require_exact(mapping: dict, expected: dict, label: str) -> None:
    for key, value in expected.items():
        if mapping.get(key) != value:
            fail(f"{label} drift: {key}")


def verify_cutover_boundary(authority: dict, cutover: dict) -> None:
    ref = authority.get("client_cutover_authority", {})
    require_exact(
        ref,
        {
            "file": "04_backend_supabase/student_access_client_cutover_authority.json",
            "required_state": "CLIENT_EDGE_ERROR_CONTRACT_ROLLBACK_HARNESS_READY_DIRECT_MODE",
            "active_transport": "directRpc",
            "edge_gateway_selected": False,
            "rollback_verified": False,
            "direct_rpc_execute_revoked": False,
        },
        "runtime smoke client boundary",
    )
    if cutover.get("schema_version") != 2 or cutover.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("cutover authority identity drifted")
    if cutover.get("current_state") != ref.get("required_state"):
        fail("cutover authority prerequisite state drifted")

    inventory = cutover.get("current_client_inventory", {})
    require_exact(
        inventory,
        {
            "transport_mode": "direct_rpc",
            "flutter_uses_edge_gateway": False,
            "direct_v2_rpc_path_active": True,
            "direct_anon_v2_rpc_execute_revoked": False,
            "repositories_call_supabase_rpc_directly": False,
            "repositories_call_single_transport": True,
        },
        "cutover current-client inventory",
    )

    contract = cutover.get("transport_contract", {})
    require_exact(
        contract,
        {
            "active_mode": "directRpc",
            "resolved_mode": "directRpc",
            "edge_gateway_selected": False,
            "automatic_edge_to_direct_fallback": False,
            "explicit_rollback_requested": False,
            "explicit_rollback_authorized": False,
            "direct_rpc_execute_revoked": False,
            "rollback_verified": False,
            "client_cutover_verified": False,
            "behavioral_transport_change": False,
        },
        "cutover transport contract",
    )

    harness = cutover.get("rollback_harness", {})
    require_exact(
        harness,
        {
            "production_active_mode": "directRpc",
            "explicit_rollback_requested": False,
            "explicit_rollback_authorized": False,
            "unauthorized_rollback_fails_closed": True,
            "rollback_from_non_edge_mode_rejected": True,
            "authorized_edge_to_direct_transition_unit_tested": True,
            "runtime_rollback_verified": False,
            "harness_ready": True,
        },
        "cutover rollback harness",
    )


def verify_fixture(authority: dict, state: str) -> None:
    fixture = authority.get("fixture", {})
    require_exact(
        fixture,
        {
            "repository_file": "04_backend_supabase/migrations/20260821063000_stage30_edge_runtime_smoke_fixture.sql",
            "migration_name": FIXTURE_NAME,
            "requires_empty_customer_domain": True,
            "synthetic_only": True,
            "token_seed": SEED,
            "raw_token_is_public_synthetic_test_material": True,
            "database_stores_token_hash_only": True,
            "repository_contains_bearer_literal": False,
            "expiry_hours": 2,
            "cleanup_required_after_proof": True,
        },
        "fixture authority",
    )
    for key, expected in EXPECTED_IDS.items():
        if fixture.get(key) != expected:
            fail(f"fixture identifier drift: {key}")

    if state == STATE_REPO:
        require_exact(
            fixture,
            {"migration_ledger_state": "repo_only", "remote_applied": False, "remote_version": None},
            "repository-only fixture receipt",
        )
    else:
        require_exact(
            fixture,
            {
                "migration_ledger_state": "remote_reconciled",
                "remote_applied": True,
                "remote_version": FIXTURE_REMOTE_VERSION,
            },
            "remote fixture receipt",
        )

    source = read(FIXTURE_SQL)
    for fragment in (
        FAILURE_CLASS,
        "STAGE30_EDGE_RUNTIME_SMOKE_FIXTURE_REQUIRES_EMPTY_CUSTOMER_DOMAIN",
        "STAGE30_SYNTHETIC_FIXTURE_POSTCONDITION_FAILED",
        SEED,
        "extensions.digest(v_token, 'sha256')",
        "now() + interval '2 hours'",
        "Stage30 Synthetic Student",
        "Stage30 Synthetic Plan",
        "Stage30 Synthetic Exercise",
    ):
        if fragment not in source:
            fail(f"fixture migration drift: {fragment}")
    if re.findall(r"(?<![0-9a-fA-F])[0-9a-fA-F]{64}(?![0-9a-fA-F])", source):
        fail(f"{DATA_LEAK_CLASS} bearer-looking literal committed in fixture migration")


def verify_proof(authority: dict, state: str) -> None:
    runtime = authority.get("runtime_proof", {})
    proof_complete = state in {STATE_PROVEN, STATE_CLEANUP_REPO, STATE_CLEAN}
    fixture_currently_deployed = state in {STATE_REMOTE, STATE_PROVEN, STATE_CLEANUP_REPO}

    if runtime.get("edge_runtime_version") != 3:
        fail("runtime proof not anchored to Edge v3")
    if runtime.get("fixture_deployed") is not fixture_currently_deployed:
        fail("fixture current-deployment state drifted")

    for key in (
        "get_workout_verified",
        "start_workout_verified",
        "set_completion_verified",
        "get_feedback_context_verified",
        "submit_feedback_verified",
        "all_five_routes_verified",
        "completed_session_verified",
        "feedback_submitted_verified",
    ):
        if runtime.get(key) is not proof_complete:
            fail(f"runtime proof lifecycle drift: {key}")

    for key in (
        "raw_token_returned",
        "raw_network_origin_returned",
        "real_student_data_used",
        "real_student_data_mutated",
        "proof_reexecution_allowed",
    ):
        if runtime.get(key) is not False:
            fail(f"privacy/reexecution invariant drift: {key}")

    cleanup_complete = state == STATE_CLEAN
    if runtime.get("cleanup_completed") is not cleanup_complete:
        fail("cleanup completion authority drifted")

    if cleanup_complete:
        require_exact(
            runtime,
            {
                "synthetic_business_rows_remaining": 0,
                "synthetic_security_rows_remaining": 0,
                "synthetic_network_proof_rows_remaining": 0,
            },
            "post-cleanup residue authority",
        )

    if not proof_complete:
        if runtime.get("proof_workflow_run_id") is not None or runtime.get("proof_result") is not None:
            fail("proof receipt appeared before live proof completion")
        return

    require_exact(
        runtime,
        {"proof_workflow_run_id": SEALED_RUN, "proof_result": "PASS"},
        "sealed runtime receipt",
    )
    receipt = authority.get("live_proof_receipt", {})
    require_exact(
        receipt,
        {
            "workflow_run_id": SEALED_RUN,
            "result": "PASS",
            "live_smoke_mode": "EXECUTED_ONCE",
            "gateway_health": "PASS",
            "routes_verified": 5,
            "get_workout": "PASS",
            "start_workout": "PASS",
            "set_completion": "PASS",
            "get_feedback_context": "PASS",
            "submit_feedback": "PASS",
            "completed_session_verified": True,
            "feedback_submitted_verified": True,
            "feedback_risk_signal": "low",
            "raw_synthetic_token_returned": False,
            "raw_network_origin_returned": False,
            "real_student_data_used": False,
            "real_student_data_mutated": False,
            "proof_reexecution_allowed": False,
        },
        "sealed live smoke receipt",
    )

    db = authority.get("database_proof_receipt", {})
    require_exact(
        db,
        {
            "sessions_total": 1,
            "session_completed": 1,
            "exercise_logs_total": 1,
            "exercise_log_completed": 1,
            "feedback_total": 1,
            "feedback_expected": 1,
            "link_last_used": 1,
            "student_status": "Treino concluído",
            "student_adherence": 100,
            "command_receipts_total": 3,
            "start_receipt_exact": 1,
            "completion_receipt_exact": 1,
            "feedback_receipt_exact": 1,
        },
        "database smoke receipt",
    )
    expected_rate = {route: 1 for route in ROUTES}
    if db.get("link_rate_bucket_request_counts") != expected_rate:
        fail("link rate-bucket proof drifted")
    network = db.get("network_rate_bucket_proof", {})
    if {key: network.get(key) for key in ROUTES} != expected_rate:
        fail("network rate-bucket proof drifted")
    if network.get("raw_origin_hash_read") is not False:
        fail(f"{DATA_LEAK_CLASS} network proof read origin digest")
    if db.get("allowed_security_events") != {
        "start_workout": 1,
        "set_completion": 1,
        "submit_feedback": 1,
    }:
        fail("security-event proof drifted")

    live = read(LIVE)
    for fragment in (
        REEXECUTION_CLASS,
        "SEALED_SKIP_REEXECUTION",
        f"SEALED_WORKFLOW_RUN = {SEALED_RUN}",
        "NETWORK_CALL_EXECUTED=false",
    ):
        if fragment not in live:
            fail(f"{REEXECUTION_CLASS} sealed verifier drift: {fragment}")


def verify_cleanup(authority: dict, state: str, remote: dict[str, str], repo_only: set[str]) -> None:
    if state not in {STATE_CLEANUP_REPO, STATE_CLEAN}:
        if authority.get("cleanup_migration") is not None:
            fail("cleanup authority appeared before cleanup stage")
        return

    if authority.get("cleanup_scope_failure_class") != CLEANUP_CLASS:
        fail("cleanup failure-class authority missing")

    cleanup = authority.get("cleanup_migration", {})
    require_exact(
        cleanup,
        {
            "repository_file": "04_backend_supabase/migrations/20260821081005_stage30_edge_runtime_smoke_cleanup.sql",
            "migration_name": CLEANUP_NAME,
            "requires_synthetic_only_customer_domain": True,
            "expected_auth_users_before_cleanup": 1,
            "expected_organizations_before_cleanup": 1,
            "expected_students_before_cleanup": 1,
            "expected_training_plans_before_cleanup": 1,
            "expected_training_exercises_before_cleanup": 1,
            "expected_access_links_before_cleanup": 1,
            "expected_workout_sessions_before_cleanup": 1,
            "expected_workout_logs_before_cleanup": 1,
            "expected_workout_feedback_before_cleanup": 1,
            "expected_growth_events_for_fixture_org": 5,
            "expected_link_rate_bucket_rows": 5,
            "expected_command_receipt_rows": 3,
            "expected_allowed_security_events": 3,
            "expected_network_proof_bucket_rows": 5,
            "raw_network_origin_embedded_in_repository": False,
            "network_origin_digest_embedded_in_repository": False,
            "organization_deleted_before_auth_user": True,
            "transactional_postcondition_required": True,
        },
        "cleanup migration authority",
    )
    if cleanup.get("network_proof_windows_utc") != ["2026-08-21T08:02:00Z", "2026-08-21T08:03:00Z"]:
        fail("cleanup network proof windows drifted")

    if state == STATE_CLEANUP_REPO:
        require_exact(
            cleanup,
            {"migration_ledger_state": "repo_only", "remote_applied": False, "remote_version": None},
            "repository-only cleanup receipt",
        )
        if repo_only != {CLEANUP_NAME} or CLEANUP_NAME in remote:
            fail("cleanup repository-only ledger mismatch")
    else:
        require_exact(
            cleanup,
            {
                "migration_ledger_state": "remote_reconciled",
                "remote_applied": True,
                "remote_version": CLEANUP_REMOTE_VERSION,
            },
            "remote cleanup receipt",
        )
        if repo_only:
            fail(f"final cleanup state has repo-only divergence: {sorted(repo_only)}")
        if remote.get(CLEANUP_NAME) != CLEANUP_REMOTE_VERSION:
            fail("cleanup remote ledger receipt missing")

        receipt = authority.get("cleanup_receipt", {})
        expected_zero = {
            "auth_users_remaining": 0,
            "profiles_remaining": 0,
            "organizations_remaining": 0,
            "organization_members_remaining": 0,
            "organization_subscriptions_remaining": 0,
            "students_remaining": 0,
            "training_plans_remaining": 0,
            "training_exercises_remaining": 0,
            "access_links_remaining": 0,
            "workout_sessions_remaining": 0,
            "workout_logs_remaining": 0,
            "workout_feedback_remaining": 0,
            "fixture_growth_events_remaining": 0,
            "fixture_link_rate_buckets_remaining": 0,
            "fixture_command_receipts_remaining": 0,
            "fixture_security_events_remaining": 0,
            "fixture_security_signals_remaining": 0,
            "proof_network_buckets_remaining": 0,
        }
        require_exact(
            receipt,
            {
                "migration_name": CLEANUP_NAME,
                "remote_version": CLEANUP_REMOTE_VERSION,
                "remote_applied": True,
                "result": "PASS",
                "raw_network_origin_read": False,
                "network_origin_digest_read": False,
                "migration_ledger_state": "remote_reconciled",
                **expected_zero,
            },
            "cleanup completion receipt",
        )

    source = read(CLEANUP_SQL)
    for fragment in (
        CLEANUP_CLASS,
        "STAGE30_CLEANUP_CUSTOMER_DOMAIN_NO_LONGER_SYNTHETIC_ONLY",
        "STAGE30_CLEANUP_PROOF_MUTATION_STATE_DRIFT",
        "STAGE30_CLEANUP_NETWORK_BUCKET_SELECTOR_MISMATCH",
        "STAGE30_CLEANUP_POSTCONDITION_FAILED",
        "2026-08-21 08:02:00+00",
        "2026-08-21 08:03:00+00",
        "fadd0c2168b5e958a5e7497e3219c84e",
        "d3ecb7c48b714739111f99b9be656b85",
        "774b6b75ac6dce7f0467a28c9df68e62",
        "delete from public.organizations where id = v_org",
        "delete from auth.users where id = v_user",
    ):
        if fragment not in source:
            fail(f"cleanup migration drift: {fragment}")
    lowered = source.lower()
    for forbidden in ("origin_hash", "cf-connecting-ip", "x-forwarded-for", "x-real-ip"):
        if forbidden in lowered:
            fail(f"{DATA_LEAK_CLASS} cleanup source contains network-origin material: {forbidden}")


def verify_ledger(state: str, ledger: dict) -> tuple[dict[str, str], set[str]]:
    remote = {row.get("name"): row.get("version") for row in ledger.get("remote_migrations", []) if isinstance(row, dict)}
    repo_only = {
        row.get("name")
        for row in ledger.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    }

    if state == STATE_REPO:
        if repo_only != {FIXTURE_NAME} or FIXTURE_NAME in remote:
            fail("fixture repository-only ledger mismatch")
    else:
        if remote.get(FIXTURE_NAME) != FIXTURE_REMOTE_VERSION:
            fail("fixture remote ledger receipt missing")
        if state in {STATE_REMOTE, STATE_PROVEN} and repo_only:
            fail(f"unexpected repo-only divergence before cleanup: {sorted(repo_only)}")

    return remote, repo_only


def verify_promotion_and_next(authority: dict, state: str) -> None:
    promotion = authority.get("promotion_rules", {})
    if promotion.get("may_apply_fixture_after_ci_and_merge") is not True:
        fail("fixture application authority drifted")
    for key in (
        "may_execute_live_smoke_before_fixture_remote_apply",
        "may_select_edge_gateway_after_fixture_apply_only",
        "may_revoke_direct_rpc_execute_now",
        "launch_gate_authority",
    ):
        if promotion.get(key) is not False:
            fail(f"premature promotion authority: {key}")
    for key in (
        "live_smoke_required_before_edge_selection",
        "cleanup_required_before_edge_selection",
        "runtime_rollback_proof_required_before_edge_selection",
    ):
        if promotion.get(key) is not True:
            fail(f"missing promotion interlock: {key}")

    next_stage = authority.get("next_stage", {})
    expected_name = {
        STATE_REPO: "APPLY_STAGE30_EDGE_RUNTIME_SMOKE_FIXTURE",
        STATE_REMOTE: "EXECUTE_STAGE30_FIVE_ROUTE_EDGE_RUNTIME_SMOKE",
        STATE_PROVEN: "PREPARE_STAGE30_RUNTIME_SMOKE_CLEANUP",
        STATE_CLEANUP_REPO: "APPLY_STAGE30_RUNTIME_SMOKE_CLEANUP",
        STATE_CLEAN: "PROVE_STAGE30_RUNTIME_ROLLBACK_HARNESS",
    }[state]
    if next_stage.get("name") != expected_name or next_stage.get("allowed_now") is not True:
        fail("Stage 30 next-stage authority drifted")

    if state == STATE_CLEANUP_REPO:
        require_exact(
            next_stage,
            {"requires_ci_and_merge_first": True, "requires_exact_merged_sql": True},
            "cleanup application interlock",
        )
    if state == STATE_CLEAN:
        require_exact(
            next_stage,
            {
                "requires_production_transport_change": False,
                "requires_real_customer_data": False,
                "requires_direct_rpc_grants_intact": True,
                "may_select_edge_gateway_after_this_state_only": False,
            },
            "rollback-proof next-stage interlock",
        )


def main() -> None:
    authority = load(AUTHORITY)
    cutover = load(CUTOVER)
    ledger = load(LEDGER)

    if authority.get("schema_version") != 1 or authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("runtime smoke authority identity drifted")
    require_exact(
        authority,
        {
            "failure_class": FAILURE_CLASS,
            "proof_reexecution_failure_class": REEXECUTION_CLASS,
            "response_data_leak_failure_class": DATA_LEAK_CLASS,
            "command_flow_failure_class": COMMAND_FLOW_CLASS,
        },
        "runtime smoke failure-class authority",
    )

    state = authority.get("current_state")
    if state not in ALLOWED_STATES:
        fail(f"unsupported Stage 30 smoke lifecycle state: {state}")
    if authority.get("baseline_main_sha") != BASELINES[state]:
        fail("runtime smoke baseline main SHA drifted")

    if authority.get("expected_route_sequence") != ROUTES:
        fail("five-route smoke sequence drifted")
    if authority.get("expected_command_inputs") != {
        "set_completion_completed": True,
        "feedback_perceived_exertion": 5,
        "feedback_pain_score": 0,
        "feedback_energy_score": 4,
        "feedback_pain_location": None,
        "feedback_note": None,
        "expected_feedback_risk_signal": "low",
    }:
        fail("safe synthetic smoke inputs drifted")

    verify_cutover_boundary(authority, cutover)
    verify_fixture(authority, state)
    verify_proof(authority, state)
    remote, repo_only = verify_ledger(state, ledger)
    verify_cleanup(authority, state, remote, repo_only)
    verify_promotion_and_next(authority, state)

    print("STUDENT_ACCESS_CLIENT_RUNTIME_SMOKE_GUARD=PASS")
    print(f"CURRENT_STATE={state}")
    print("EDGE_RUNTIME_VERSION=3")
    print("EXPECTED_EDGE_ROUTES=5")
    print("LIVE_SMOKE_EXECUTED=" + str(state in {STATE_PROVEN, STATE_CLEANUP_REPO, STATE_CLEAN}).lower())
    print("LIVE_SMOKE_REEXECUTION=" + ("SEALED" if state in {STATE_PROVEN, STATE_CLEANUP_REPO, STATE_CLEAN} else "NOT_YET_SEALED"))
    print("CLEANUP_COMPLETE=" + str(state == STATE_CLEAN).lower())
    print("SYNTHETIC_RESIDUE=" + ("ZERO" if state == STATE_CLEAN else "CONTROLLED_PENDING"))
    print("FLUTTER_ACTIVE_TRANSPORT=directRpc")
    print("EDGE_SELECTION=DENIED")
    print("ROLLBACK_VERIFIED=false")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
