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
CLEANUP_MIGRATION = BACKEND / "migrations" / "20260823161000_stage35_alert_delivery_controlled_proof_cleanup.sql"
PROOF_WORKFLOW = ROOT / ".github" / "workflows" / "stage35_alert_external_delivery_one_shot_proof.yml"
TRIGGER_FILE = BACKEND / "stage35_alert_external_delivery_proof_trigger.json"

BASELINE = "8324413284aaad9fc932f8f86269b6c339f240e9"
OBSERVED = "2026-08-23T09:05:47.415327Z"
CURRENT_RECONCILED_BASELINE = "a23dd9d892189b92a633634caf750606504e83ee"
CURRENT_RECONCILED_OBSERVED = "2026-08-23T15:56:57.947085Z"
CLEANUP_PROMOTION_BASELINE = "db522140cc2b21840b5b48727cb15a82ca22f975"
CLEANUP_PROMOTION_OBSERVED = "2026-08-23T16:06:48.978350Z"
FIXTURE_NAME = "stage35_alert_delivery_controlled_proof_fixture"
RECEIPT_NAME = "stage35_alert_delivery_receipt_store"
CLEANUP_NAME = "stage35_alert_delivery_controlled_proof_cleanup"
FIXTURE_REMOTE_VERSION = "20260823145908"
RECEIPT_REMOTE_VERSION = "20260823092354"
FIXTURE_BLOB = "7d3631fc425903b013606b4a7731eaa273867a9b"
CANDIDATE_BLOB = "745fd77814fa40909069e00de6b41c7292e8df7b"
RECEIPT_BLOB = "9f1a625cd316362874aefcfd9e33d64f9ecd173d"
DISPATCHER_BLOB = "0aece761d707d8befb64a0fb89ce495fc50255a0"
CLEANUP_BLOB = "ca8a824131120d912d0fe98687820c2b320e33f5"
CLEANUP_MIGRATION_BLOB = "a53354ed3a4983ebfe1017d4df622ed5dc6a97d0"
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


def normalize_to_reconciled_frontier(ledger: dict) -> tuple[dict, bool]:
    baseline = ledger.get("baseline_main_sha")
    observed = ledger.get("observed_at_utc")
    divergences = [row for row in ledger.get("declared_divergences", []) if isinstance(row, dict)]
    remote_only = [row for row in divergences if row.get("direction") == "remote_only"]
    repo_only = [row for row in divergences if row.get("direction") == "repo_only"]
    if len(remote_only) != 3:
        fail("historical remote-only divergence count drifted")

    remote = {
        row.get("name"): row.get("version")
        for row in ledger.get("remote_migrations", []) if isinstance(row, dict)
    }
    if remote.get(RECEIPT_NAME) != RECEIPT_REMOTE_VERSION:
        fail("current receipt-store remote version drifted")
    if remote.get(FIXTURE_NAME) != FIXTURE_REMOTE_VERSION:
        fail("current controlled-fixture remote version drifted")

    if baseline == CURRENT_RECONCILED_BASELINE and observed == CURRENT_RECONCILED_OBSERVED:
        if repo_only:
            fail("reconciled frontier unexpectedly contains repo-only rows")
        return json.loads(json.dumps(ledger)), False

    if baseline == CLEANUP_PROMOTION_BASELINE and observed == CLEANUP_PROMOTION_OBSERVED:
        if {row.get("name") for row in repo_only} != {CLEANUP_NAME} or len(repo_only) != 1:
            fail("cleanup-promotion frontier must contain exactly one cleanup repo-only row")
        projected = json.loads(json.dumps(ledger))
        projected["baseline_main_sha"] = CURRENT_RECONCILED_BASELINE
        projected["observed_at_utc"] = CURRENT_RECONCILED_OBSERVED
        projected["declared_divergences"] = remote_only
        return projected, True

    fail("ledger baseline is neither current reconciled nor cleanup-promotion frontier")
    raise AssertionError("unreachable")


def historical_fixture_frontier(ledger: dict) -> tuple[dict, bool]:
    reconciled, cleanup_frontier = normalize_to_reconciled_frontier(ledger)
    projected = json.loads(json.dumps(reconciled))
    projected["baseline_main_sha"] = BASELINE
    projected["observed_at_utc"] = OBSERVED
    projected["remote_migrations"] = [
        row for row in projected.get("remote_migrations", [])
        if not (isinstance(row, dict) and row.get("name") in {RECEIPT_NAME, FIXTURE_NAME})
    ]
    remote_only = [
        row for row in projected.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "remote_only"
    ]
    projected["declared_divergences"] = remote_only + [
        {
            "direction": "repo_only",
            "name": RECEIPT_NAME,
            "reason": "Exact repository promotion of the reviewed Stage35 privacy-minimized alert delivery receipt-store candidate. Remote application remains forbidden until a separate dispatcher deployment and controlled external-delivery proof sequence is authorized.",
            "owner": "BlackGold Forge",
            "related_failure_class": "BGF-STAGE35-ALERT-CANDIDATE-REMOTE-MUTATION-281",
        },
        {
            "direction": "repo_only",
            "name": FIXTURE_NAME,
            "reason": "Exact repository promotion of the reviewed Stage35 synthetic controlled-delivery fixture after runtime secret-name readiness was proven. Remote application remains forbidden until this promotion is merged green and the receipt-store apply / dispatcher deployment sequence is separately authorized.",
            "owner": "BlackGold Forge",
            "related_failure_class": "BGF-STAGE35-ALERT-CONTROLLED-FIXTURE-PREMATURE-284",
        },
    ]
    return projected, cleanup_frontier


def main() -> None:
    authority = load(AUTHORITY)
    source_ledger = load(LEDGER)
    ledger, cleanup_frontier = historical_fixture_frontier(source_ledger)
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
        "operator_execution_result": "PASS",
        "operator_execution_secret_values_printed": False,
        "operator_execution_supabase_runtime_names_verified": "3/3",
        "operator_execution_github_actions_names_verified": "4/4",
        "operator_execution_runtime_secret_rotated": False,
        "provider_credential_validity_proven": False,
        "telegram_delivery_proven": False,
    }, "secret readiness receipt")
    require(reconciliation.get("success_semantics", {}), {
        "github_actions_four_of_four_names_present": True,
        "supabase_edge_runtime_three_of_three_names_present": True,
        "secret_values_observed_by_logs": False,
        "runtime_secret_name_presence_is_sufficient_to_unblock_fixture_repo_promotion": True,
        "runtime_secret_name_presence_is_not_external_delivery_proof": True,
    }, "reconciliation success semantics")

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

    if cleanup_frontier:
        if not CLEANUP_MIGRATION.exists():
            fail("cleanup-promotion frontier missing cleanup migration")
        if blob(CLEANUP_MIGRATION) != CLEANUP_MIGRATION_BLOB:
            fail("cleanup migration blob drifted")
        if body(raw(CLEANUP_MIGRATION), "cleanup migration") != body(raw(CLEANUP), "cleanup candidate"):
            fail("cleanup migration executable body is not byte-identical to candidate")

    require(authority.get("fixture_promotion", {}), {
        "migration_name": FIXTURE_NAME,
        "migration_git_blob_sha": FIXTURE_BLOB,
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

    if ledger.get("baseline_main_sha") != BASELINE or ledger.get("observed_at_utc") != OBSERVED:
        fail("historical fixture frontier projection drifted")
    divergences = [row for row in ledger.get("declared_divergences", []) if isinstance(row, dict)]
    remote_only = [row for row in divergences if row.get("direction") == "remote_only"]
    repo_only = [row for row in divergences if row.get("direction") == "repo_only"]
    if len(remote_only) != 3:
        fail("historical remote-only divergence count drifted")
    if {row.get("name") for row in repo_only} != {RECEIPT_NAME, FIXTURE_NAME} or len(repo_only) != 2:
        fail("Stage35 historical repo-only frontier drifted")
    remote_names = {row.get("name") for row in ledger.get("remote_migrations", []) if isinstance(row, dict)}
    if RECEIPT_NAME in remote_names or FIXTURE_NAME in remote_names:
        fail("Stage35 migration unexpectedly remote in historical fixture frontier")

    expected_stage35 = [
        "20260822075500_stage35_alert_delivery_receipt_store.sql",
        "20260823091500_stage35_alert_delivery_controlled_proof_fixture.sql",
    ]
    if cleanup_frontier:
        expected_stage35.append("20260823161000_stage35_alert_delivery_controlled_proof_cleanup.sql")
    stage35_migrations = sorted(path.name for path in (BACKEND / "migrations").glob("*stage35*.sql"))
    if stage35_migrations != sorted(expected_stage35):
        fail(f"unexpected Stage35 migration inventory: {stage35_migrations}")
    if TRIGGER_FILE.exists():
        fail("one-shot external delivery proof trigger materialized in mergeable repository history")
    if seal.get("current_state") != "DEPLOYMENT_AND_EXTERNAL_DELIVERY_PROOF_SEAL_STAGED_NO_REMOTE_MUTATION":
        fail("dispatcher deployment/proof seal authority drifted")

    require(authority.get("sequence_boundary", {}), {
        "may_skip_sequence_step": False,
        "may_execute_operations_sql_directly": False,
        "may_use_execute_sql_for_dml_or_ddl": False,
    }, "sequence boundary")
    require(authority.get("gates", {}), {
        "incident_response": "DENIED",
        "production_deployment": "DENIED",
        "paid_media": "DENIED",
        "external_delivery_proof": "NOT_YET_CONSUMED",
    }, "historical gates")

    serialized = json.dumps(authority, sort_keys=True).lower()
    for fragment in ("sbp_", "x-fitnexus-alert-dispatch-token\": \"", "telegram_bot_token\": \"", "telegram_chat_id\": \""):
        if fragment in serialized:
            fail("authority appears to contain a secret value")

    print("STAGE35_ALERT_CONTROLLED_FIXTURE_MIGRATION_PROMOTION_GUARD=PASS")
    print(f"HISTORICAL_BASELINE_MAIN_SHA={BASELINE}")
    print(f"FIXTURE_MIGRATION_BLOB={FIXTURE_BLOB}")
    print(f"FIXTURE_CANDIDATE_BLOB={CANDIDATE_BLOB}")
    print("HISTORICAL_FIXTURE_MIGRATION_LEDGER_STATE=repo_only")
    print(f"CURRENT_CLEANUP_PROMOTION_FRONTIER={str(cleanup_frontier).lower()}")
    print("CURRENT_REMOTE_RECONCILIATION_COMPATIBLE=true")
    print("PROOF_REEXECUTION_ALLOWED=false")
    print("TELEGRAM_PROVIDER_CALLED_BY_HISTORICAL_GUARD=false")
    print("INCIDENT_RESPONSE_GATE=DENIED")
    print("PRODUCTION_DEPLOYMENT_GATE=DENIED")
    print("PAID_MEDIA_GATE=DENIED")


if __name__ == "__main__":
    main()
