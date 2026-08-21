from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
APP = ROOT / "03_app_flutter" / "fitnexus_app"
AUTHORITY = BACKEND / "stage32_post_cutover_live_proof_failure_r0_authority.json"
LEDGER = BACKEND / "migration_ledger_authority.json"
REARM_MIGRATION = BACKEND / "migrations" / "20260821213000_stage32_rearm_expired_fixture_r1.sql"
LIVE_TEST = APP / "test" / "student_access_stage32_post_cutover_live_edge_proof_test.dart"
OLD_SEAL = BACKEND / "stage32_post_cutover_live_proof_workflow_seal_authority.json"
OLD_WORKFLOW = ROOT / ".github" / "workflows" / "stage32_post_cutover_edge_runtime_live_proof.yml"

FAIL_PLUGIN = "BGF-STAGE32-FLUTTER-TEST-SHARED-PREFERENCES-PLUGIN-235"
FAIL_TTL = "BGF-STAGE32-SYNTHETIC-FIXTURE-TTL-EXPIRED-BEFORE-RETRY-236"
FAIL_READONLY = "BGF-SUPABASE-EXECUTE-SQL-READONLY-DML-237"
REARM_NAME = "stage32_rearm_expired_fixture_r1"
REARM_FILE = "04_backend_supabase/migrations/20260821213000_stage32_rearm_expired_fixture_r1.sql"
REARM_VERSION = "20260821214005"
REARM_SOURCE_MAIN = "71a4e8de96f903d142e63ab9fb98ff6d24035e6d"
REARM_OBSERVED = "2026-08-21T21:40:30.546568Z"
OLD_PROOF_HEAD = "370cfe65d3df5188c3f840d84b5a8748f1357cf2"
OLD_TRIGGER_HEAD = "84a51d97f3b7a7c53965567e21760d5d59c85f5a"


def fail(message: str) -> None:
    raise SystemExit("STAGE32_PRE_NETWORK_FAILURE_RECOVERY_R1_GUARD=FAIL\n" + message)


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
    migration = text(REARM_MIGRATION)
    live_test = text(LIVE_TEST)
    old_seal = load(OLD_SEAL)
    old_workflow = text(OLD_WORKFLOW)

    require(
        authority,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "stage": "STAGE32_POST_CUTOVER_LIVE_PROOF_FAILURE_R0",
            "baseline_main_sha": "c43a2662de1f92b08dad4ed1b22c51357a0ff269",
            "r2_baseline_main_sha": "2b3dbfa2543230f8ae17a9838c610b326d453d02",
            "rearm_apply_source_main_sha": REARM_SOURCE_MAIN,
            "status": "PRE_NETWORK_FAILURE_RECORDED_FIXTURE_REARMED_R1_LIVE_PROOF_R1_PENDING",
        },
        "failure authority",
    )

    classes = authority.get("failure_classes")
    ids = [item.get("id") for item in classes if isinstance(item, dict)] if isinstance(classes, list) else []
    if ids != [FAIL_PLUGIN, FAIL_TTL, FAIL_READONLY]:
        fail("failure class identity/order drifted")

    attempt = authority.get("consumed_attempt", {})
    require(
        attempt,
        {
            "workflow_run_id": 32508349425,
            "workflow_job_id": 96853509377,
            "run_attempt": 1,
            "proof_pr": 71,
            "proof_head_sha": OLD_PROOF_HEAD,
            "trigger_pr": 73,
            "trigger_head_sha": OLD_TRIGGER_HEAD,
            "result": "FAIL_PRE_NETWORK_BOOTSTRAP",
            "network_transport_reached": False,
            "production_singleton_invoke_reached": False,
            "routes_attempted": 0,
            "routes_verified": 0,
            "proof_credit": False,
            "same_workflow_rerun_allowed": False,
            "same_proof_head_reuse_allowed": False,
        },
        "consumed R0 attempt",
    )

    dml = authority.get("execute_sql_dml_failure_receipt", {})
    require(
        dml,
        {
            "source": "Supabase.execute_sql",
            "result": "FAIL_READ_ONLY_TRANSACTION",
            "sqlstate": "25006",
            "transaction_mutation_applied": False,
            "retry_through_execute_sql_allowed": False,
            "replacement_mechanism": "Supabase.apply_migration",
        },
        "read-only DML failure receipt",
    )

    rearm = authority.get("rearm_remote_receipt", {})
    require(
        rearm,
        {
            "source": "Supabase.apply_migration",
            "source_main_sha": REARM_SOURCE_MAIN,
            "source_file": REARM_FILE,
            "source_file_sha": "250381595839d35ed7464c92640389a4b2c89042",
            "migration_name": REARM_NAME,
            "remote_version": REARM_VERSION,
            "pre_apply_observed_at_utc": "2026-08-21T21:39:22.002155Z",
            "apply_result": "SUCCESS",
            "post_apply_observed_at_utc": REARM_OBSERVED,
            "link_id": "378baa18-c8fc-5765-b01f-6fd3dd898f64",
            "link_expires_at_utc": "2026-08-22T03:40:05.481184Z",
            "rearm_horizon_ok": True,
            "expected_live_link": 1,
            "auth_users": 1,
            "profiles": 1,
            "organizations": 1,
            "organization_members": 1,
            "organization_subscriptions": 1,
            "students": 1,
            "training_plans": 1,
            "training_exercises": 1,
            "access_links": 1,
            "workout_sessions": 0,
            "workout_logs": 0,
            "workout_feedback": 0,
            "fixture_command_receipts": 0,
            "fixture_rate_buckets": 0,
            "fixture_security_events": 0,
            "fixture_security_signals": 0,
            "growth_events": 4,
            "trial_started": 1,
            "student_created": 1,
            "training_created_or_duplicated": 1,
            "training_delivered": 1,
            "growth_attribution": 0,
            "rpc_count": 5,
            "all_five_anon_execute_intact": True,
            "all_five_authenticated_execute_intact": True,
            "remote_mutation_was_only_exact_link_expiry_rearm": True,
            "live_proof_executed_during_rearm": False,
            "direct_rpc_grants_changed": False,
        },
        "remote rearm receipt",
    )

    boundary = authority.get("production_boundary", {})
    require(
        boundary,
        {
            "active_transport": "edgeGateway",
            "production_singleton": "StudentAccessTransport.instance",
            "automatic_edge_to_direct_fallback": False,
            "direct_rpc_execute_revoked": False,
            "post_cutover_live_proof_verified": False,
            "post_cutover_rollback_verified": False,
            "launch_gate_promotion": False,
        },
        "production boundary",
    )

    repair = authority.get("repair_r1", {})
    require(
        repair,
        {
            "shared_preferences_mock_required_before_supabase_initialize": True,
            "required_test_fragment": "SharedPreferences.setMockInitialValues(<String, Object>{});",
            "historical_operation_execution_allowed": False,
            "fixture_rearm_migration_file": REARM_FILE,
            "fixture_rearm_migration_name": REARM_NAME,
            "migration_ledger_state": "remote_reconciled",
            "remote_applied": True,
            "remote_version": REARM_VERSION,
            "authorized_remote_mutation_tool": "Supabase.apply_migration",
            "requires_new_proof_head": True,
            "requires_new_workflow_seal": True,
            "requires_new_trigger_head": True,
            "old_proof_pr_must_remain_closed_unmerged": True,
            "old_trigger_pr_must_remain_closed_unmerged": True,
        },
        "repair R1 contract",
    )

    repo_only = [
        row for row in ledger.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    ]
    if repo_only:
        fail("remote-reconciled rearm must leave no repo_only divergence")
    remote = {
        row.get("name"): row.get("version")
        for row in ledger.get("remote_migrations", []) if isinstance(row, dict)
    }
    if remote.get("stage32_post_cutover_edge_runtime_fixture") != "20260821171334":
        fail("Stage32 original fixture remote receipt disappeared")
    if remote.get(REARM_NAME) != REARM_VERSION:
        fail("rearm remote migration receipt missing")
    require(
        ledger,
        {"baseline_main_sha": REARM_SOURCE_MAIN, "observed_at_utc": REARM_OBSERVED},
        "reconciled migration ledger",
    )

    for fragment in (
        FAIL_READONLY,
        "STAGE32_R1_REARM_CUSTOMER_DOMAIN_NOT_EXACT_SYNTHETIC_FIXTURE",
        "STAGE32_R1_REARM_FIXTURE_IDENTITY_OR_EXPIRY_MISMATCH",
        "STAGE32_R1_REARM_RUNTIME_RESIDUE_DETECTED",
        "STAGE32_R1_REARM_GROWTH_FIXTURE_DRIFT",
        "STAGE32_R1_REARM_UPDATE_COUNT_MISMATCH",
        "STAGE32_R1_REARM_POSTCONDITION_FAILED",
        "set expires_at = now() + interval '6 hours'",
    ):
        if fragment not in migration:
            fail(f"rearm migration drift: {fragment}")
    lower = migration.lower()
    if "delete from" in lower or "insert into" in lower or lower.count("update public.student_access_links") != 1:
        fail("rearm migration mutation boundary drifted")

    mock_call = "SharedPreferences.setMockInitialValues(<String, Object>{});"
    supabase_init = "await Supabase.initialize("
    if mock_call not in live_test or supabase_init not in live_test:
        fail("SharedPreferences repair or Supabase initialization missing")
    if live_test.index(mock_call) > live_test.index(supabase_init):
        fail("SharedPreferences mock occurs after Supabase.initialize")
    if "StudentAccessTransport.forVerification" in live_test or ".forVerification(" in live_test:
        fail("repair weakened production singleton boundary")
    if "final transport = StudentAccessTransport.instance;" not in live_test:
        fail("production singleton disappeared from repaired proof")

    require(old_seal.get("proof_pr", {}), {"number": 71, "head_sha": OLD_PROOF_HEAD, "merge_allowed": False}, "R0 proof seal")
    require(old_seal.get("open_trigger", {}), {"head_sha": OLD_TRIGGER_HEAD, "merge_allowed": False}, "R0 trigger seal")
    if "workflow_dispatch:" in old_workflow or "schedule:" in old_workflow:
        fail("consumed R0 workflow became replayable")

    next_stage = authority.get("next_stage", {})
    require(
        next_stage,
        {
            "name": "PREPARE_STAGE32_POST_CUTOVER_LIVE_PROOF_R1",
            "allowed_now": True,
            "requires_rearm_remote_reconciled": True,
            "requires_shared_preferences_mock": True,
            "requires_new_exact_proof_head": True,
            "requires_new_one_shot_workflow_seal": True,
            "requires_new_trigger_head": True,
            "requires_fresh_fixture_expiry_check_immediately_before_event_delivery": True,
            "requires_fresh_direct_rpc_grant_check_immediately_before_event_delivery": True,
            "requires_zero_runtime_mutation_residue_before_event_delivery": True,
            "may_execute_before_new_workflow_seal": False,
            "may_rerun_consumed_workflow": False,
            "may_reuse_consumed_proof_head": False,
            "may_revoke_direct_rpc_execute_now": False,
            "may_promote_launch_gates": False,
        },
        "next stage",
    )

    print("STAGE32_PRE_NETWORK_FAILURE_RECOVERY_R1_GUARD=PASS")
    print(f"FAILURE_CLASS_1={FAIL_PLUGIN}")
    print(f"FAILURE_CLASS_2={FAIL_TTL}")
    print(f"FAILURE_CLASS_3={FAIL_READONLY}")
    print("R0_ROUTES_ATTEMPTED=0")
    print(f"REARM_REMOTE_VERSION={REARM_VERSION}")
    print("REARM_LEDGER=REMOTE_RECONCILED")
    print("SHARED_PREFERENCES_MOCK_INSTALLED=true")
    print("DIRECT_RPC_GRANTS=INTACT")
    print("PRODUCTION_ACTIVE_TRANSPORT=edgeGateway")
    print("NEXT=PREPARE_STAGE32_POST_CUTOVER_LIVE_PROOF_R1")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
