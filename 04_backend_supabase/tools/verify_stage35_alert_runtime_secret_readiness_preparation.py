from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage35_alert_controlled_fixture_promotion_and_secret_readiness_authority.json"
LEDGER = BACKEND / "migration_ledger_authority.json"
FIXTURE_CANDIDATE = BACKEND / "operations" / "stage35_alert_delivery_controlled_proof_fixture_candidate.sql"
CLEANUP_CANDIDATE = BACKEND / "operations" / "stage35_alert_delivery_controlled_proof_cleanup_candidate.sql"
RECEIPT_MIGRATION = BACKEND / "migrations" / "20260822075500_stage35_alert_delivery_receipt_store.sql"
DISPATCHER = BACKEND / "functions" / "student-access-alert-dispatcher" / "index.ts"
ONE_SHOT = ROOT / ".github" / "workflows" / "stage35_alert_external_delivery_one_shot_proof.yml"

BASELINE = "4654c2c1d02ffe817958861fef52babef5a7d375"
RECEIPT_BLOB = "9f1a625cd316362874aefcfd9e33d64f9ecd173d"
FIXTURE_BLOB = "745fd77814fa40909069e00de6b41c7292e8df7b"
CLEANUP_BLOB = "ca8a824131120d912d0fe98687820c2b320e33f5"
DISPATCHER_BLOB = "0aece761d707d8befb64a0fb89ce495fc50255a0"
ONE_SHOT_BLOB = "079a140e36a851eb0f787397929ffbe3351aba48"
FAILURE_CLASS = "BGF-STAGE35-ALERT-SECRET-READINESS-SELF-ATTESTATION-292"


def fail(message: str) -> None:
    raise SystemExit(
        "STAGE35_ALERT_RUNTIME_SECRET_READINESS_PREPARATION=FAIL\n"
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


def blob(path: Path) -> str:
    try:
        data = path.read_bytes()
    except OSError as exc:
        fail(f"unable to read {path.relative_to(ROOT)}: {type(exc).__name__}")
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def require(mapping: dict, expected: dict, label: str) -> None:
    if not isinstance(mapping, dict):
        fail(f"{label} must be an object")
    for key, expected_value in expected.items():
        if mapping.get(key) != expected_value:
            fail(f"{label} drift: {key}")


def main() -> None:
    # First replay only the repository guards of the already-merged Stage35 seal.
    # This does not trigger its one-shot external provider workflow.
    seal = importlib.import_module("verify_stage35_alert_dispatcher_deployment_proof_seal_lifecycle")
    seal.main()

    authority = load(AUTHORITY)
    ledger = load(LEDGER)

    require(authority, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE35_ALERT_RUNTIME_SECRET_READINESS_ASSESSMENT",
        "baseline_main_sha": BASELINE,
        "current_state": "RUNTIME_SECRET_READINESS_ASSESSMENT_STAGED_FIXTURE_NOT_PROMOTED",
    }, "secret readiness authority")

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
    }, "seal receipt")

    receipt = authority.get("fresh_post_seal_remote_receipt", {})
    require(receipt, {
        "observed_at_utc": "2026-08-22T18:25:55.841264Z",
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
        FIXTURE_CANDIDATE: FIXTURE_BLOB,
        CLEANUP_CANDIDATE: CLEANUP_BLOB,
        DISPATCHER: DISPATCHER_BLOB,
        ONE_SHOT: ONE_SHOT_BLOB,
    }
    for path, expected in expected_blobs.items():
        if blob(path) != expected:
            fail(f"sealed repository blob drift: {path.relative_to(ROOT)}")

    fixture_migrations = sorted((BACKEND / "migrations").glob("*stage35*controlled*fixture*.sql"))
    if fixture_migrations:
        fail("controlled fixture was promoted before runtime-secret readiness evidence")

    if ledger.get("baseline_main_sha") != "6aad66c159c82c634af8ec58f0ec742267484b70":
        fail("receipt-store repo-only ledger baseline drifted")
    repo_only = [
        row for row in ledger.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    ]
    if len(repo_only) != 1 or repo_only[0].get("name") != "stage35_alert_delivery_receipt_store":
        fail("secret readiness must not advance the migration ledger")

    readiness = authority.get("runtime_secret_readiness", {})
    require(readiness, {
        "status": "UNVERIFIED",
        "assessment_scope": "github_actions_secret_presence_only",
        "required_secret_names": [
            "SUPABASE_ACCESS_TOKEN",
            "STUDENT_ACCESS_ALERT_DISPATCH_TOKEN",
            "STUDENT_ACCESS_ALERT_TELEGRAM_BOT_TOKEN",
            "STUDENT_ACCESS_ALERT_TELEGRAM_CHAT_ID",
        ],
        "assessment_run_id": None,
        "assessment_job_id": None,
        "supabase_access_token_present": None,
        "dispatch_token_present": None,
        "telegram_bot_token_present": None,
        "telegram_chat_id_present": None,
        "all_required_github_secrets_present": None,
        "secret_values_may_be_printed": False,
        "github_presence_proves_supabase_edge_runtime_configured": False,
        "provider_destination_verified": False,
        "remote_mutation_allowed_while_unverified": False,
    }, "secret readiness")

    require(authority.get("promotion_rules", {}), {
        "may_promote_fixture_migration_now": False,
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

    print("STAGE35_ALERT_RUNTIME_SECRET_READINESS_PREPARATION=PASS")
    print("ASSESSMENT_SCOPE=github_actions_secret_presence_only")
    print("SECRET_VALUES_PRINTED=false")
    print("CONTROLLED_FIXTURE_PROMOTED=false")
    print("REMOTE_MUTATION=false")
    print("PROVIDER_CALLED=false")
    print("PROOF_REEXECUTION_ALLOWED=false")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
