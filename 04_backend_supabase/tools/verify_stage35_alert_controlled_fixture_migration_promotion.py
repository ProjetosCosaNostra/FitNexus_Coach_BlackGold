from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage35_alert_controlled_fixture_migration_promotion_authority.json"
LEDGER = BACKEND / "migration_ledger_authority.json"
RECONCILIATION = BACKEND / "stage35_alert_secret_post_bootstrap_reconciliation_contract_authority.json"
SEAL = BACKEND / "stage35_alert_dispatcher_deployment_proof_seal_authority.json"
MIGRATION = BACKEND / "migrations" / "20260823091500_stage35_alert_delivery_controlled_proof_fixture.sql"
CANDIDATE = BACKEND / "operations" / "stage35_alert_delivery_controlled_proof_fixture_candidate.sql"
RECEIPT_MIGRATION = BACKEND / "migrations" / "20260822075500_stage35_alert_delivery_receipt_store.sql"
DISPATCHER = BACKEND / "functions" / "student-access-alert-dispatcher" / "index.ts"
CLEANUP = BACKEND / "operations" / "stage35_alert_delivery_controlled_proof_cleanup_candidate.sql"
PROOF_WORKFLOW = ROOT / ".github" / "workflows" / "stage35_alert_external_delivery_one_shot_proof.yml"
TRIGGER_FILE = BACKEND / "stage35_alert_external_delivery_proof_trigger.json"

BASELINE = "8324413284aaad9fc932f8f86269b6c339f240e9"
FIXTURE_NAME = "stage35_alert_delivery_controlled_proof_fixture"
RECEIPT_NAME = "stage35_alert_delivery_receipt_store"
FIXTURE_BLOB = "7d3631fc425903b013606b4a7731eaa273867a9b"
CANDIDATE_BLOB = "745fd77814fa40909069e00de6b41c7292e8df7b"
RECEIPT_BLOB = "9f1a625cd316362874aefcfd9e33d64f9ecd173d"
DISPATCHER_BLOB = "0aece761d707d8befb64a0fb89ce495fc50255a0"
CLEANUP_BLOB = "ca8a824131120d912d0fe98687820c2b320e33f5"
PROOF_WORKFLOW_BLOB = "079a140e36a851eb0f787397929ffbe3351aba48"
FAILURE_CLASS = "BGF-STAGE35-ALERT-CONTROLLED-FIXTURE-PROMOTION-303"
BODY_MARKER = b"do $$"


def fail(message: str) -> None:
    raise SystemExit(
        "STAGE35_ALERT_CONTROLLED_FIXTURE_MIGRATION_PROMOTION_GUARD=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\nDETAIL={message}"
    )


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to read {path.relative_to(ROOT)}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"expected object: {path.relative_to(ROOT)}")
    return value


def raw(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        fail(f"unable to read {path.relative_to(ROOT)}: {type(exc).__name__}")
    raise AssertionError("unreachable")


def blob(path: Path) -> str:
    data = raw(path)
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def require(mapping: dict, expected: dict, label: str) -> None:
    if not isinstance(mapping, dict):
        fail(f"{label} must be object")
    for key, expected_value in expected.items():
        if mapping.get(key) != expected_value:
            fail(f"{label} drift: {key}")


def body(data: bytes, label: str) -> bytes:
    index = data.find(BODY_MARKER)
    if index < 0:
        fail(f"{label} executable body missing")
    return data[index:]


def main() -> None:
    authority = load(AUTHORITY)
    ledger = load(LEDGER)
    reconciliation = load(RECONCILIATION)
    seal = load(SEAL)

    require(authority, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE35_ALERT_CONTROLLED_FIXTURE_MIGRATION_PROMOTION",
        "baseline_main_sha": BASELINE,
        "current_state": "CONTROLLED_FIXTURE_MIGRATION_REPO_ONLY_RUNTIME_SECRET_READINESS_PROVEN_REMOTE_APPLY_PENDING",
    }, "fixture promotion authority")

    required_failure_classes = {
        "BGF-STAGE35-ALERT-PROOF-CUSTOMER-CROSSOVER-278",
        "BGF-STAGE35-ALERT-CANDIDATE-REMOTE-MUTATION-281",
        "BGF-STAGE35-ALERT-CONTROLLED-FIXTURE-PREMATURE-284",
        "BGF-STAGE35-ALERT-CONTROLLED-FIXTURE-DRIFT-285",
        "BGF-STAGE35-ALERT-RUNTIME-SECRET-ASSUMPTION-289",
        "BGF-STAGE35-ALERT-PROOF-WORKFLOW-REPLAY-290",
        FAILURE_CLASS,
        "BGF-STAGE35-ALERT-SECRET-READINESS-EVIDENCE-BINDING-304",
    }
    if set(authority.get("failure_classes", [])) != required_failure_classes:
        fail("failure-class set drifted")

    require(authority.get("secret_readiness_receipt", {}), {
        "bootstrap_v5_pr": 109,
        "bootstrap_v5_merge_main_sha": BASELINE,
        "bootstrap_v5_script_blob": "9be7c37c5b993a5a089cde9cad7db7537ae2fa84",
        "operator_execution_observed": True,
        "operator_execution_result": "PASS",
        "operator_execution_secret_values_printed": False,
        "operator_execution_runtime_secret_root_shape": "ARRAY",
        "operator_execution_supabase_runtime_names_verified": "3/3",
        "operator_execution_github_actions_names_verified": "4/4",
        "operator_execution_runtime_secret_rotated": False,
        "independent_github_presence_workflow_run": 32629966098,
        "independent_github_presence_workflow_job": 97171113379,
        "independent_github_presence_result": "PASS",
        "independent_github_required_names_present": "4/4",
        "independent_github_secret_values_printed": False,
        "supabase_management_api_readback_http_status": 200,
        "supabase_management_api_readback_root_shape": "ARRAY",
        "supabase_management_api_readback_item_count": 10,
        "supabase_management_api_required_runtime_names_present": "3/3",
        "supabase_management_api_secret_values_logged": False,
        "provider_credential_validity_proven": False,
        "telegram_delivery_proven": False,
    }, "secret readiness receipt")

    require(reconciliation.get("success_semantics", {}), {
        "github_actions_four_of_four_names_present": True,
        "supabase_edge_runtime_three_of_three_names_present": True,
        "secret_values_observed_by_logs": False,
        "runtime_secret_name_presence_is_sufficient_to_unblock_fixture_repo_promotion": True,
        "runtime_secret_name_presence_is_not_external_delivery_proof": True,
        "runtime_secret_name_presence_is_not_incident_response_readiness": True,
        "runtime_secret_name_presence_is_not_production_deployment_readiness": True,
        "runtime_secret_name_presence_is_not_paid_media_readiness": True,
    }, "reconciliation success semantics")

    require(authority.get("fresh_remote_receipt", {}), {
        "source": "Supabase.execute_sql+Supabase.list_migrations+Supabase.list_edge_functions",
        "observed_at_utc": "2026-08-23T09:05:47.415327Z",
        "auth_users": 0,
        "organizations": 0,
        "students": 0,
        "security_events": 0,
        "security_signals": 0,
        "network_buckets": 13,
        "growth_events": 6,
        "direct_target_rpc_anon_execute_count": 0,
        "direct_target_rpc_authenticated_execute_count": 0,
        "direct_target_rpc_service_role_execute_count": 5,
        "issue_student_access_token_v2_authenticated_execute": True,
        "alert_receipt_table_exists": False,
        "alert_claim_bridge_exists": False,
        "alert_record_bridge_exists": False,
        "remote_stage35_receipt_store_migration_present": False,
        "remote_stage35_controlled_fixture_migration_present": False,
        "deployed_edge_function_count": 1,
        "student_access_alert_dispatcher_deployed": False,
        "student_access_gateway_bundle_sha256": "b57892b3f399b76f8127c9a39d3d8c021ffe639aa7bf92c7fa9a459d35721b82",
    }, "fresh remote receipt")

    if blob(MIGRATION) != FIXTURE_BLOB:
        fail("controlled fixture migration blob drifted")
    if blob(CANDIDATE) != CANDIDATE_BLOB:
        fail("controlled fixture candidate blob drifted")
    if blob(RECEIPT_MIGRATION) != RECEIPT_BLOB:
        fail("receipt-store migration blob drifted")
    if blob(DISPATCHER) != DISPATCHER_BLOB:
        fail("dispatcher blob drifted")
    if blob(CLEANUP) != CLEANUP_BLOB:
        fail("controlled fixture cleanup candidate blob drifted")
    if blob(PROOF_WORKFLOW) != PROOF_WORKFLOW_BLOB:
        fail("one-shot proof workflow blob drifted")

    migration_data = raw(MIGRATION)
    candidate_data = raw(CANDIDATE)
    if body(migration_data, "migration") != body(candidate_data, "candidate"):
        fail("controlled fixture migration executable body is not byte-identical to candidate")
    header = migration_data[: migration_data.find(BODY_MARKER)].decode("utf-8", errors="replace").lower()
    for fragment in ("repository-only", "remote application is forbidden"):
        if fragment not in header:
            fail(f"fixture migration safety header missing: {fragment}")

    require(authority.get("fixture_promotion", {}), {
        "migration_name": FIXTURE_NAME,
        "migration_file": "04_backend_supabase/migrations/20260823091500_stage35_alert_delivery_controlled_proof_fixture.sql",
        "migration_git_blob_sha": FIXTURE_BLOB,
        "source_candidate_file": "04_backend_supabase/operations/stage35_alert_delivery_controlled_proof_fixture_candidate.sql",
        "source_candidate_git_blob_sha": CANDIDATE_BLOB,
        "executable_body_byte_identical": True,
        "migration_ledger_state": "repo_only",
        "remote_applied": False,
        "remote_version": None,
        "apply_count": 0,
        "remote_apply_allowed_after_this_pr_alone": False,
        "synthetic_signal_created_by_this_pr": False,
        "provider_called_by_this_pr": False,
        "one_shot_proof_consumed_by_this_pr": False,
    }, "fixture promotion")

    if ledger.get("baseline_main_sha") != BASELINE:
        fail("ledger baseline drifted")
    if ledger.get("observed_at_utc") != "2026-08-23T09:05:47.415327Z":
        fail("ledger observation drifted")
    divergences = [row for row in ledger.get("declared_divergences", []) if isinstance(row, dict)]
    remote_only = [row for row in divergences if row.get("direction") == "remote_only"]
    repo_only = [row for row in divergences if row.get("direction") == "repo_only"]
    if len(remote_only) != 3:
        fail("historical remote-only divergence count drifted")
    if {row.get("name") for row in repo_only} != {RECEIPT_NAME, FIXTURE_NAME} or len(repo_only) != 2:
        fail("Stage35 repo-only frontier must contain exactly receipt store and controlled fixture")
    remote_names = {row.get("name") for row in ledger.get("remote_migrations", []) if isinstance(row, dict)}
    if RECEIPT_NAME in remote_names or FIXTURE_NAME in remote_names:
        fail("Stage35 migration unexpectedly remote")
    if not any(row.get("name") == "stage33_post_revocation_proof_cleanup" and row.get("version") == "20260822061133" for row in ledger.get("remote_migrations", [])):
        fail("Stage33 cleanup remote receipt drifted")

    stage35_migrations = sorted(path.name for path in (BACKEND / "migrations").glob("*stage35*.sql"))
    if stage35_migrations != [
        "20260822075500_stage35_alert_delivery_receipt_store.sql",
        "20260823091500_stage35_alert_delivery_controlled_proof_fixture.sql",
    ]:
        fail(f"unexpected Stage35 migration inventory: {stage35_migrations}")

    if TRIGGER_FILE.exists():
        fail("one-shot external delivery proof trigger materialized prematurely")

    if seal.get("current_state") != "DEPLOYMENT_AND_EXTERNAL_DELIVERY_PROOF_SEAL_STAGED_NO_REMOTE_MUTATION":
        fail("dispatcher deployment/proof seal authority drifted")
    if seal.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("dispatcher seal project ref drifted")

    require(authority.get("sequence_boundary", {}), {
        "step_1_after_merge": "APPLY_STAGE35_RECEIPT_STORE_ONCE_VIA_SUPABASE_APPLY_MIGRATION",
        "step_2": "VERIFY_RECEIPT_TABLE_BRIDGES_PRIVILEGES_AND_ZERO_CUSTOMER_SECURITY_DOMAIN",
        "step_3": "APPLY_CONTROLLED_FIXTURE_ONCE_VIA_SUPABASE_APPLY_MIGRATION",
        "step_4": "VERIFY_EXACT_ONE_SYNTHETIC_SIGNAL_ZERO_RECEIPTS",
        "step_5": "DEPLOY_EXACT_ALERT_DISPATCHER_WITH_VERIFY_JWT_FALSE_CUSTOM_SECRET_AUTH",
        "step_6": "VERIFY_DEPLOYED_BUNDLE_AND_SECRET_NAME_READINESS",
        "step_7": "ONLY_THEN_OPEN_EXACT_ONE_SHOT_PROOF_TRIGGER_PR",
        "may_skip_sequence_step": False,
        "may_execute_operations_sql_directly": False,
        "may_use_execute_sql_for_dml_or_ddl": False,
    }, "sequence boundary")

    require(authority.get("gates", {}), {
        "incident_response": "DENIED",
        "production_deployment": "DENIED",
        "paid_media": "DENIED",
        "external_delivery_proof": "NOT_YET_CONSUMED",
    }, "gates")
    require(authority.get("next_stage", {}), {
        "name": "AFTER_PROMOTION_GREEN_MERGE_APPLY_RECEIPT_STORE_AND_VERIFY_BEFORE_FIXTURE_APPLY",
        "allowed_now": False,
        "requires_fixture_promotion_full_ci_green": True,
        "requires_fixture_promotion_merge_to_main": True,
        "requires_exact_receipt_store_blob": RECEIPT_BLOB,
        "requires_exact_fixture_blob": FIXTURE_BLOB,
        "requires_exact_dispatcher_blob": DISPATCHER_BLOB,
        "may_promote_launch_gates": False,
    }, "next stage")

    serialized = json.dumps(authority, sort_keys=True).lower()
    forbidden_secret_fragments = (
        "sbp_",
        "x-fitnexus-alert-dispatch-token\": \"",
        "telegram_bot_token\": \"",
        "telegram_chat_id\": \"",
    )
    for fragment in forbidden_secret_fragments:
        if fragment in serialized:
            fail("authority appears to contain a secret value")

    print("STAGE35_ALERT_CONTROLLED_FIXTURE_MIGRATION_PROMOTION_GUARD=PASS")
    print(f"BASELINE_MAIN_SHA={BASELINE}")
    print(f"FIXTURE_MIGRATION_BLOB={FIXTURE_BLOB}")
    print(f"FIXTURE_CANDIDATE_BLOB={CANDIDATE_BLOB}")
    print(f"RECEIPT_STORE_MIGRATION_BLOB={RECEIPT_BLOB}")
    print(f"DISPATCHER_BLOB={DISPATCHER_BLOB}")
    print(f"ONE_SHOT_PROOF_WORKFLOW_BLOB={PROOF_WORKFLOW_BLOB}")
    print("RUNTIME_SECRET_NAMES_VERIFIED=3/3")
    print("GITHUB_ACTIONS_SECRET_NAMES_VERIFIED=4/4")
    print("SECRET_VALUES_PRINTED=false")
    print("FIXTURE_MIGRATION_LEDGER_STATE=repo_only")
    print("RECEIPT_STORE_REMOTE_APPLIED=false")
    print("FIXTURE_REMOTE_APPLIED=false")
    print("ALERT_DISPATCHER_REMOTE_DEPLOYED=false")
    print("TELEGRAM_PROVIDER_CALLED=false")
    print("ONE_SHOT_EXTERNAL_DELIVERY_PROOF_CONSUMED=false")
    print("INCIDENT_RESPONSE_GATE=DENIED")
    print("PRODUCTION_DEPLOYMENT_GATE=DENIED")
    print("PAID_MEDIA_GATE=DENIED")


if __name__ == "__main__":
    main()
