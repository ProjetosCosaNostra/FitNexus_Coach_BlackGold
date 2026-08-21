from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
APP = ROOT / "03_app_flutter" / "fitnexus_app"

AUTHORITY = BACKEND / "stage32_post_cutover_live_proof_failure_r0_authority.json"
LEDGER = BACKEND / "migration_ledger_authority.json"
HISTORICAL_OPERATION = BACKEND / "operations" / "stage32_rearm_expired_fixture_r1.sql"
REARM_MIGRATION = BACKEND / "migrations" / "20260821213000_stage32_rearm_expired_fixture_r1.sql"
LIVE_TEST = APP / "test" / "student_access_stage32_post_cutover_live_edge_proof_test.dart"
OLD_SEAL = BACKEND / "stage32_post_cutover_live_proof_workflow_seal_authority.json"
OLD_WORKFLOW = ROOT / ".github" / "workflows" / "stage32_post_cutover_edge_runtime_live_proof.yml"

FAIL_PLUGIN = "BGF-STAGE32-FLUTTER-TEST-SHARED-PREFERENCES-PLUGIN-235"
FAIL_TTL = "BGF-STAGE32-SYNTHETIC-FIXTURE-TTL-EXPIRED-BEFORE-RETRY-236"
FAIL_READONLY = "BGF-SUPABASE-EXECUTE-SQL-READONLY-DML-237"
REARM_NAME = "stage32_rearm_expired_fixture_r1"
REARM_FILE = "04_backend_supabase/migrations/20260821213000_stage32_rearm_expired_fixture_r1.sql"
OLD_RUN = 32508349425
OLD_JOB = 96853509377
OLD_PROOF_HEAD = "370cfe65d3df5188c3f840d84b5a8748f1357cf2"
OLD_TRIGGER_HEAD = "84a51d97f3b7a7c53965567e21760d5d59c85f5a"
LINK_ID = "378baa18-c8fc-5765-b01f-6fd3dd898f64"
R2_BASELINE = "2b3dbfa2543230f8ae17a9838c610b326d453d02"


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
    historical_operation = text(HISTORICAL_OPERATION)
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
            "r2_baseline_main_sha": R2_BASELINE,
            "status": "PRE_NETWORK_FAILURE_RECORDED_REARM_MIGRATION_REPO_ONLY",
        },
        "failure authority",
    )

    classes = authority.get("failure_classes")
    if not isinstance(classes, list) or len(classes) != 3:
        fail("failure class set drifted")
    ids = [item.get("id") for item in classes if isinstance(item, dict)]
    if ids != [FAIL_PLUGIN, FAIL_TTL, FAIL_READONLY]:
        fail("failure class identity/order drifted")
    if not all(isinstance(item.get("rule"), str) and item.get("rule") for item in classes):
        fail("failure class prevention rule missing")

    attempt = authority.get("consumed_attempt", {})
    require(
        attempt,
        {
            "workflow_run_id": OLD_RUN,
            "workflow_job_id": OLD_JOB,
            "run_attempt": 1,
            "proof_pr": 71,
            "proof_head_sha": OLD_PROOF_HEAD,
            "trigger_pr": 73,
            "trigger_head_sha": OLD_TRIGGER_HEAD,
            "result": "FAIL_PRE_NETWORK_BOOTSTRAP",
            "candidate_guard_passed": True,
            "flutter_setup_passed": True,
            "dependencies_resolved": True,
            "synthetic_token_derived_and_masked": True,
            "failing_step": "Execute sealed production-singleton five-route proof once",
            "exception_type": "MissingPluginException",
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
    if "shared_preferences" not in str(attempt.get("exception_message_class", "")):
        fail("shared_preferences failure signature missing")
    if "Supabase.initialize" not in str(attempt.get("failure_site", "")):
        fail("pre-network failure site drifted")

    receipt = authority.get("post_failure_database_receipt", {})
    require(
        receipt,
        {
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
            "expected_user": 1,
            "expected_org": 1,
            "expected_student": 1,
            "expected_plan": 1,
            "expected_exercise": 1,
            "expected_active_link": 1,
            "real_customer_rows_observed": False,
            "synthetic_business_mutation_residue": False,
        },
        "post-failure database receipt",
    )

    expiry = authority.get("fixture_expiry_receipt", {})
    require(
        expiry,
        {
            "link_id": LINK_ID,
            "link_is_active": True,
            "link_not_expired": False,
            "fixture_usable_for_new_live_proof": False,
        },
        "expired fixture receipt",
    )
    if expiry.get("link_expires_at_utc") != "2026-08-21T19:13:34.175674Z":
        fail("expired fixture timestamp drifted")

    pre = authority.get("pre_rearm_receipt", {})
    require(
        pre,
        {
            "observed_at_utc": "2026-08-21T21:29:21.68853Z",
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
            "link_expired": True,
            "rpc_count": 5,
            "all_five_anon_execute_intact": True,
            "all_five_authenticated_execute_intact": True,
        },
        "fresh pre-rearm receipt",
    )

    dml = authority.get("execute_sql_dml_failure_receipt", {})
    require(
        dml,
        {
            "source": "Supabase.execute_sql",
            "attempted_after_preflight_observed_at_utc": "2026-08-21T21:29:21.68853Z",
            "operation_file": "04_backend_supabase/operations/stage32_rearm_expired_fixture_r1.sql",
            "result": "FAIL_READ_ONLY_TRANSACTION",
            "sqlstate": "25006",
            "message_class": "cannot execute UPDATE in a read-only transaction",
            "failed_statement_class": "UPDATE public.student_access_links expires_at",
            "transaction_mutation_applied": False,
            "retry_through_execute_sql_allowed": False,
            "replacement_mechanism": "Supabase.apply_migration",
        },
        "read-only DML failure receipt",
    )

    grants = authority.get("direct_rpc_grant_receipt", {})
    require(
        grants,
        {
            "rpc_count": 5,
            "all_five_anon_execute_intact": True,
            "all_five_authenticated_execute_intact": True,
            "grants_changed_by_failed_attempt": False,
        },
        "direct RPC grants",
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
            "historical_operation_file": "04_backend_supabase/operations/stage32_rearm_expired_fixture_r1.sql",
            "historical_operation_execution_allowed": False,
            "fixture_rearm_migration_file": REARM_FILE,
            "fixture_rearm_migration_name": REARM_NAME,
            "migration_ledger_state": "repo_only",
            "remote_applied": False,
            "remote_version": None,
            "authorized_remote_mutation_tool": "Supabase.apply_migration",
            "fixture_rearm_hours": 6,
            "requires_exact_synthetic_fixture_identity": True,
            "requires_zero_runtime_mutation_residue": True,
            "requires_expired_link_before_rearm": True,
            "requires_fresh_direct_rpc_grant_check_before_rearm": True,
            "requires_fresh_migration_ledger_check_immediately_before_apply": True,
            "requires_exact_merged_sql": True,
            "requires_new_proof_head": True,
            "requires_new_workflow_seal": True,
            "requires_new_trigger_head": True,
            "old_proof_pr_must_remain_closed_unmerged": True,
            "old_trigger_pr_must_remain_closed_unmerged": True,
        },
        "repair R1 contract",
    )

    repo_only = [
        row
        for row in ledger.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    ]
    if len(repo_only) != 1 or repo_only[0].get("name") != REARM_NAME:
        fail("rearm migration must be the unique repo_only migration")
    if repo_only[0].get("related_failure_class") != FAIL_READONLY:
        fail("rearm ledger failure-class binding drifted")
    remote = {
        row.get("name"): row.get("version")
        for row in ledger.get("remote_migrations", [])
        if isinstance(row, dict)
    }
    if remote.get("stage32_post_cutover_edge_runtime_fixture") != "20260821171334":
        fail("Stage32 original fixture remote receipt disappeared")
    if REARM_NAME in remote:
        fail("rearm migration self-attested as remote before apply")
    if ledger.get("baseline_main_sha") != R2_BASELINE:
        fail("rearm ledger baseline drifted")

    for source, label in (
        (historical_operation, "historical operation"),
        (migration, "rearm migration"),
    ):
        for fragment in (
            "STAGE32_R1_REARM_CUSTOMER_DOMAIN_NOT_EXACT_SYNTHETIC_FIXTURE",
            "STAGE32_R1_REARM_FIXTURE_IDENTITY_OR_EXPIRY_MISMATCH",
            "STAGE32_R1_REARM_RUNTIME_RESIDUE_DETECTED",
            "STAGE32_R1_REARM_GROWTH_FIXTURE_DRIFT",
            "STAGE32_R1_REARM_UPDATE_COUNT_MISMATCH",
            "STAGE32_R1_REARM_POSTCONDITION_FAILED",
            "set expires_at = now() + interval '6 hours'",
            "expires_at <= now()",
            "token_hash = extensions.digest(v_token, 'sha256')",
            "fitnexus-stage32-post-cutover-edge-runtime-proof-v1",
            LINK_ID,
        ):
            if fragment not in source:
                fail(f"{label} drift: {fragment}")
        lower_source = source.lower()
        if "delete from" in lower_source or "insert into" in lower_source:
            fail(f"{label} may only update the exact existing synthetic link")
        if lower_source.count("update public.student_access_links") != 1:
            fail(f"{label} must contain exactly one link update")
    if FAIL_READONLY not in migration:
        fail("rearm migration does not record the execute_sql read-only failure class")

    mock_import = "import 'package:shared_preferences/shared_preferences.dart';"
    mock_call = "SharedPreferences.setMockInitialValues(<String, Object>{});"
    supabase_init = "await Supabase.initialize("
    if mock_import not in live_test or mock_call not in live_test:
        fail(f"{FAIL_PLUGIN} SharedPreferences mock not installed in live proof")
    if live_test.index(mock_call) > live_test.index(supabase_init):
        fail(f"{FAIL_PLUGIN} SharedPreferences mock occurs after Supabase.initialize")
    if "StudentAccessTransport.forVerification" in live_test or ".forVerification(" in live_test:
        fail("repair weakened production-singleton proof boundary")
    if "final transport = StudentAccessTransport.instance;" not in live_test:
        fail("production singleton disappeared from repaired proof")

    require(
        old_seal.get("proof_pr", {}),
        {"number": 71, "head_sha": OLD_PROOF_HEAD, "merge_allowed": False},
        "historical R0 proof seal",
    )
    require(
        old_seal.get("open_trigger", {}),
        {"head_sha": OLD_TRIGGER_HEAD, "merge_allowed": False},
        "historical R0 trigger seal",
    )
    if "workflow_dispatch:" in old_workflow or "schedule:" in old_workflow:
        fail("consumed R0 workflow became replayable")

    next_stage = authority.get("next_stage", {})
    require(
        next_stage,
        {
            "name": "APPLY_STAGE32_REARM_EXPIRED_FIXTURE_R1_MIGRATION",
            "allowed_only_after_ci_and_merge": True,
            "may_rearm_fixture_before_ci_and_merge": False,
            "may_mutate_via_execute_sql": False,
            "requires_apply_migration": True,
            "may_deliver_new_live_proof_event_before_rearm_receipt": False,
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
    print(f"CONSUMED_RUN={OLD_RUN}")
    print("ROUTES_ATTEMPTED=0")
    print("FIXTURE_EXPIRED=true")
    print("SHARED_PREFERENCES_MOCK_INSTALLED=true")
    print(f"REARM_MIGRATION={REARM_NAME}")
    print("REARM_LEDGER=REPO_ONLY")
    print("EXECUTE_SQL_DML_ALLOWED=false")
    print("AUTHORIZED_REMOTE_MUTATION_TOOL=Supabase.apply_migration")
    print("DIRECT_RPC_GRANTS=INTACT")
    print("PRODUCTION_ACTIVE_TRANSPORT=edgeGateway")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
