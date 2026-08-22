from __future__ import annotations

import hashlib
import importlib
import json
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
APP = ROOT / "03_app_flutter" / "fitnexus_app"
AUTHORITY = BACKEND / "stage35_alert_controlled_fixture_promotion_and_secret_readiness_authority.json"
LEDGER = BACKEND / "migration_ledger_authority.json"
RECEIPT_MIGRATION = BACKEND / "migrations" / "20260822075500_stage35_alert_delivery_receipt_store.sql"
FIXTURE_MIGRATION = BACKEND / "migrations" / "20260822182700_stage35_alert_delivery_controlled_proof_fixture.sql"
FIXTURE_CANDIDATE = BACKEND / "operations" / "stage35_alert_delivery_controlled_proof_fixture_candidate.sql"
DISPATCHER = BACKEND / "functions" / "student-access-alert-dispatcher" / "index.ts"
ONE_SHOT = ROOT / ".github" / "workflows" / "stage35_alert_external_delivery_one_shot_proof.yml"
CLEANUP = BACKEND / "operations" / "stage35_alert_delivery_controlled_proof_cleanup_candidate.sql"
TRANSPORT = APP / "lib" / "features" / "student" / "student_access_transport_contract.dart"

BASELINE = "4654c2c1d02ffe817958861fef52babef5a7d375"
OBSERVED = "2026-08-22T18:25:55.841264Z"
RECEIPT_NAME = "stage35_alert_delivery_receipt_store"
FIXTURE_NAME = "stage35_alert_delivery_controlled_proof_fixture"
RECEIPT_BLOB = "9f1a625cd316362874aefcfd9e33d64f9ecd173d"
FIXTURE_MIGRATION_BLOB = "c302a6a5abbaeb2858d8e9937d93c389a421358c"
FIXTURE_CANDIDATE_BLOB = "745fd77814fa40909069e00de6b41c7292e8df7b"
DISPATCHER_BLOB = "0aece761d707d8befb64a0fb89ce495fc50255a0"
ONE_SHOT_BLOB = "079a140e36a851eb0f787397929ffbe3351aba48"
CLEANUP_BLOB = "ca8a824131120d912d0fe98687820c2b320e33f5"
FAILURE_CLASS = "BGF-STAGE35-ALERT-FIXTURE-MIGRATION-PROMOTION-291"
BODY_MARKER = b"do $$\n"


def fail(message: str) -> None:
    raise SystemExit(
        "STAGE35_ALERT_CONTROLLED_FIXTURE_PROMOTION_GUARD=FAIL\n"
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


def git_blob_sha(path: Path) -> str:
    data = raw(path)
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def executable_body(data: bytes, label: str) -> bytes:
    index = data.find(BODY_MARKER)
    if index < 0:
        fail(f"{label} executable body marker missing")
    return data[index:]


def require(mapping: dict, expected: dict, label: str) -> None:
    if not isinstance(mapping, dict):
        fail(f"{label} must be an object")
    for key, expected_value in expected.items():
        if mapping.get(key) != expected_value:
            fail(f"{label} drift: {key}")


def projected_receipt_store_ledger(current: dict) -> dict:
    value = json.loads(json.dumps(current))
    value["baseline_main_sha"] = "6aad66c159c82c634af8ec58f0ec742267484b70"
    value["observed_at_utc"] = "2026-08-22T07:54:12.776139Z"
    value["declared_divergences"] = [
        row for row in value.get("declared_divergences", [])
        if not (
            isinstance(row, dict)
            and row.get("direction") == "repo_only"
            and row.get("name") == FIXTURE_NAME
        )
    ]
    return value


def prove_historical_seal(current_ledger: dict) -> None:
    projected = projected_receipt_store_ledger(current_ledger)
    with tempfile.TemporaryDirectory(prefix="fitnexus-stage35-fixture-history-") as tmp:
        temp_root = Path(tmp)
        temp_ledger = temp_root / "migration_ledger_authority.json"
        temp_backend = temp_root / "backend"
        temp_migrations = temp_backend / "migrations"
        temp_migrations.mkdir(parents=True)
        temp_ledger.write_text(json.dumps(projected, indent=2) + "\n", encoding="utf-8")
        shutil.copy2(RECEIPT_MIGRATION, temp_migrations / RECEIPT_MIGRATION.name)

        promotion = importlib.import_module("verify_stage35_alert_receipt_store_migration_promotion")
        seal = importlib.import_module("verify_stage35_alert_dispatcher_deployment_proof_seal")
        seal_lifecycle = importlib.import_module("verify_stage35_alert_dispatcher_deployment_proof_seal_lifecycle")

        old_promotion_ledger = promotion.LEDGER
        old_promotion_backend = promotion.BACKEND
        old_seal_ledger = seal.LEDGER
        try:
            promotion.LEDGER = temp_ledger
            promotion.BACKEND = temp_backend
            seal.LEDGER = temp_ledger
            seal_lifecycle.main()
        finally:
            promotion.LEDGER = old_promotion_ledger
            promotion.BACKEND = old_promotion_backend
            seal.LEDGER = old_seal_ledger


def main() -> None:
    authority = load(AUTHORITY)
    ledger = load(LEDGER)

    require(authority, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE35_ALERT_CONTROLLED_FIXTURE_PROMOTION_AND_SECRET_READINESS",
        "baseline_main_sha": BASELINE,
        "current_state": "CONTROLLED_FIXTURE_REPO_ONLY_RUNTIME_SECRET_READINESS_UNVERIFIED",
    }, "current authority")

    require(authority.get("deployment_proof_seal_receipt", {}), {
        "seal_pr": 101,
        "seal_head_sha": "dd9544a3622c73fcd2b4362792ead4b1a2543846",
        "seal_merge_main_sha": BASELINE,
        "quality_gate_run": 32590560566,
        "quality_gate_job": 97073617459,
        "quality_gate_result": "PASS",
        "seal_workflow_run": 32590560504,
        "seal_workflow_job": 97073617270,
        "seal_workflow_result": "PASS",
        "consumed_stage31_32_33_proofs_reexecuted": False,
    }, "deployment/proof seal receipt")

    receipt = authority.get("fresh_post_seal_remote_receipt", {})
    require(receipt, {
        "source": "Supabase.execute_sql+Supabase.list_migrations+Supabase.list_edge_functions",
        "observed_at_utc": OBSERVED,
        "auth_users": 0,
        "organizations": 0,
        "students": 0,
        "security_events": 0,
        "security_signals": 0,
        "network_buckets": 13,
        "growth_events": 6,
        "anon_execute_count": 0,
        "authenticated_execute_count": 0,
        "service_role_execute_count": 5,
        "issue_student_access_token_v2_authenticated_execute": True,
        "security_posture": "quiet",
        "alert_receipt_table_exists": False,
        "alert_claim_bridge_exists": False,
        "alert_record_bridge_exists": False,
        "receipt_store_remote_migration_present": False,
        "controlled_fixture_remote_migration_present": False,
        "deployed_edge_function_count": 1,
        "student_access_alert_dispatcher_deployed": False,
    }, "fresh remote receipt")

    expected_blobs = {
        RECEIPT_MIGRATION: RECEIPT_BLOB,
        FIXTURE_MIGRATION: FIXTURE_MIGRATION_BLOB,
        FIXTURE_CANDIDATE: FIXTURE_CANDIDATE_BLOB,
        DISPATCHER: DISPATCHER_BLOB,
        ONE_SHOT: ONE_SHOT_BLOB,
        CLEANUP: CLEANUP_BLOB,
    }
    for path, expected in expected_blobs.items():
        actual = git_blob_sha(path)
        if actual != expected:
            fail(f"Git blob drift: {path.relative_to(ROOT)} => {actual}")

    if executable_body(raw(FIXTURE_MIGRATION), "fixture migration") != executable_body(raw(FIXTURE_CANDIDATE), "fixture candidate"):
        fail("promoted controlled fixture executable body is not byte-identical")

    require(authority.get("controlled_fixture_promotion", {}), {
        "migration_name": FIXTURE_NAME,
        "migration_git_blob_sha": FIXTURE_MIGRATION_BLOB,
        "source_candidate_git_blob_sha": FIXTURE_CANDIDATE_BLOB,
        "executable_body_byte_identical": True,
        "migration_ledger_state": "repo_only",
        "remote_applied": False,
        "apply_count": 0,
        "remote_apply_allowed_after_this_pr_alone": False,
        "real_customer_data_allowed": False,
        "proof_marker": "fitnexus-stage34-alert-delivery-proof-v1",
    }, "fixture promotion")

    if ledger.get("baseline_main_sha") != BASELINE or ledger.get("observed_at_utc") != OBSERVED:
        fail("migration ledger current observation drifted")
    remote = {
        row.get("name"): row.get("version")
        for row in ledger.get("remote_migrations", []) if isinstance(row, dict)
    }
    if RECEIPT_NAME in remote or FIXTURE_NAME in remote:
        fail("Stage35 migration unexpectedly remote before secret readiness")
    if remote.get("stage33_direct_rpc_revocation_and_post_revocation_fixture") != "20260822032456":
        fail("Stage33 revocation receipt drifted")
    if remote.get("stage33_post_revocation_proof_cleanup") != "20260822061133":
        fail("Stage33 cleanup receipt drifted")
    repo_only = [
        row for row in ledger.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    ]
    if [row.get("name") for row in repo_only] != [RECEIPT_NAME, FIXTURE_NAME]:
        fail("current repo-only frontier must be receipt-store then controlled fixture")
    if repo_only[1].get("related_failure_class") != "BGF-STAGE35-ALERT-CONTROLLED-FIXTURE-PREMATURE-284":
        fail("fixture repo-only failure-class binding drifted")

    stage35_migrations = sorted(path.name for path in (BACKEND / "migrations").glob("*stage35*.sql"))
    if stage35_migrations != [
        "20260822075500_stage35_alert_delivery_receipt_store.sql",
        "20260822182700_stage35_alert_delivery_controlled_proof_fixture.sql",
    ]:
        fail(f"unexpected Stage35 migration inventory: {stage35_migrations}")

    readiness = authority.get("runtime_secret_readiness", {})
    require(readiness, {
        "status": "UNVERIFIED",
        "assessment_source": "github_actions_secret_presence_only",
        "assessment_run_id": None,
        "assessment_job_id": None,
        "supabase_access_token_present": None,
        "dispatch_token_present": None,
        "telegram_bot_token_present": None,
        "telegram_chat_id_present": None,
        "secret_values_may_be_printed": False,
        "github_presence_proves_supabase_edge_runtime_configured": False,
        "remote_mutation_allowed_while_unverified": False,
    }, "runtime secret readiness")

    transport = TRANSPORT.read_text(encoding="utf-8")
    for fragment in (
        "StudentAccessTransportMode.edgeGateway;",
        "static const bool edgeGatewaySelected = true;",
        "static const bool automaticEdgeToDirectFallback = false;",
        "static const bool explicitRollbackRequested = false;",
        "static const bool explicitRollbackAuthorized = false;",
        "static const bool directRpcExecuteRevoked = false;",
    ):
        if fragment not in transport:
            fail(f"fixture promotion changed production transport metadata: {fragment}")

    prove_historical_seal(ledger)

    require(authority.get("promotion_rules", {}), {
        "may_apply_receipt_store_now": False,
        "may_apply_controlled_fixture_now": False,
        "may_deploy_dispatcher_now": False,
        "may_open_proof_trigger_pr_now": False,
        "may_call_telegram_now": False,
        "may_execute_operations_sql_directly": False,
        "may_use_execute_sql_for_dml": False,
        "may_store_secret_values_in_repository": False,
        "may_reexecute_consumed_stage31_32_33_proofs": False,
        "may_regrant_direct_rpc_execute": False,
        "may_enable_automatic_direct_fallback": False,
        "may_advance_source_transport_metadata": False,
        "may_promote_incident_response_gate": False,
        "may_promote_production_deployment_gate": False,
        "may_enable_paid_ads": False,
    }, "promotion rules")

    print("STAGE35_ALERT_CONTROLLED_FIXTURE_PROMOTION_GUARD=PASS")
    print(f"BASELINE_MAIN_SHA={BASELINE}")
    print(f"RECEIPT_STORE_REPO_ONLY={RECEIPT_NAME}")
    print(f"CONTROLLED_FIXTURE_REPO_ONLY={FIXTURE_NAME}")
    print(f"CONTROLLED_FIXTURE_MIGRATION_BLOB={FIXTURE_MIGRATION_BLOB}")
    print("FIXTURE_EXECUTABLE_BODY_BYTE_IDENTICAL=true")
    print("STAGE35_REMOTE_MIGRATION_COUNT=0")
    print("RUNTIME_SECRET_READINESS=UNVERIFIED")
    print("REMOTE_MUTATION_ALLOWED=false")
    print("PROOF_REEXECUTION_ALLOWED=false")
    print("INCIDENT_RESPONSE_GATE=DENIED")
    print("PRODUCTION_DEPLOYMENT_GATE=DENIED")
    print("PAID_MEDIA_GATE=DENIED")


if __name__ == "__main__":
    main()
