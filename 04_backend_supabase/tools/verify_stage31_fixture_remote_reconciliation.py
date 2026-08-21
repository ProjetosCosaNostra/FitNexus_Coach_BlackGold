from __future__ import annotations

import importlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
APP = ROOT / "03_app_flutter" / "fitnexus_app"
AUTHORITY = BACKEND / "student_access_client_edge_runtime_proof_authority.json"
LEDGER = BACKEND / "migration_ledger_authority.json"
CUTOVER = BACKEND / "student_access_client_cutover_authority.json"
CONTRACT = APP / "lib" / "features" / "student" / "student_access_transport_contract.dart"
FIXTURE_SQL = BACKEND / "migrations" / "20260821104600_stage31_client_edge_runtime_fixture.sql"

CURRENT_STATE = "CLIENT_EDGE_RUNTIME_PROOF_FIXTURE_REMOTE_LIVE_PROOF_PENDING_DIRECT_MODE"
REPO_STATE = "CLIENT_EDGE_RUNTIME_PROOF_FIXTURE_REPO_ONLY_DIRECT_MODE"
CURRENT_BASELINE = "669b5f4816aafcaf87647e4eaa98dd0a1bb43ffb"
PREPARATION_BASELINE = "40042c82a658dd991b6b025ec619fa064898fc52"
STAGE31_PREREQ_CUTOVER_STATE = "CLIENT_RUNTIME_ROLLBACK_VERIFIED_DIRECT_MODE"
STAGE31_PREREQ_CUTOVER_BASELINE = "eb578b06fed57987b3dba94d7c9a7931974743c4"
REMOTE_VERSION = "20260821113205"
FIXTURE_NAME = "stage31_client_edge_runtime_fixture"
HISTORICAL_CLASS = "BGF-STAGE31-HISTORICAL-GUARD-REPOONLY-PROJECTION-220"
RECONCILIATION_CLASS = "BGF-STAGE31-FIXTURE-REMOTE-RECONCILIATION-221"
FAILURE_CLASSES = [
    "BGF-STAGE31-CLIENT-EDGE-RUNTIME-FIXTURE-216",
    "BGF-STAGE31-VERIFICATION-SEAM-PRODUCTION-LEAK-217",
    "BGF-STAGE31-CLIENT-EDGE-RUNTIME-PROOF-PREMATURE-218",
    "BGF-STAGE31-CLIENT-EDGE-RUNTIME-PROOF-REEXECUTION-219",
]
MODES = {"stage31", "rate_limit", "valid_route", "smoke", "rollback"}


def fail(message: str) -> None:
    raise SystemExit("STAGE31_FIXTURE_REMOTE_RECONCILIATION_GUARD=FAIL\n" + message)


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to read {path.relative_to(ROOT)}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"expected JSON object: {path.relative_to(ROOT)}")
    return value


def require(mapping: dict, expected: dict, label: str) -> None:
    for key, value in expected.items():
        if mapping.get(key) != value:
            fail(f"{label} drift: {key}")


def validate_current() -> tuple[dict, dict]:
    authority = load(AUTHORITY)
    ledger = load(LEDGER)

    require(
        authority,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "current_state": CURRENT_STATE,
            "baseline_main_sha": CURRENT_BASELINE,
            "preparation_baseline_main_sha": PREPARATION_BASELINE,
            "failure_classes": FAILURE_CLASSES,
            "historical_guard_projection_failure_class": HISTORICAL_CLASS,
            "fixture_remote_reconciliation_failure_class": RECONCILIATION_CLASS,
        },
        "Stage 31 remote authority",
    )
    fixture = authority.get("fixture", {})
    require(
        fixture,
        {
            "repository_file": "04_backend_supabase/migrations/20260821104600_stage31_client_edge_runtime_fixture.sql",
            "migration_name": FIXTURE_NAME,
            "migration_ledger_state": "remote_reconciled",
            "remote_applied": True,
            "remote_version": REMOTE_VERSION,
            "requires_empty_customer_domain": True,
            "synthetic_only": True,
            "database_stores_token_hash_only": True,
            "repository_contains_bearer_literal": False,
            "raw_network_origin_embedded": False,
            "network_origin_digest_embedded": False,
            "cleanup_required_after_proof": True,
        },
        "Stage 31 remote fixture",
    )
    pre = authority.get("pre_apply_receipt", {})
    if pre.get("source") != "Supabase.execute_sql" or pre.get("observed_at_utc") != "2026-08-21T11:31:17Z":
        fail("fresh pre-apply receipt identity drifted")
    for key in (
        "auth_users", "profiles", "organizations", "students", "training_plans",
        "training_exercises", "access_links", "workout_sessions", "workout_logs", "workout_feedback",
    ):
        if pre.get(key) != 0:
            fail(f"pre-apply customer domain was not empty: {key}")
    if pre.get("customer_domain_empty") is not True:
        fail("pre-apply customer-domain empty seal missing")

    receipt = authority.get("remote_apply_receipt", {})
    require(
        receipt,
        {
            "source_sql_main_sha": CURRENT_BASELINE,
            "source_file_sha": "d64787b2fec532676fc2914e0ef707d4d2973c40",
            "migration_name": FIXTURE_NAME,
            "remote_version": REMOTE_VERSION,
            "apply_result": "SUCCESS",
            "migration_postcondition_included_token_resolution": True,
            "raw_synthetic_token_returned": False,
            "raw_network_origin_returned": False,
            "real_customer_data_used": False,
        },
        "Stage 31 remote apply receipt",
    )
    require(
        receipt.get("post_apply_counts", {}),
        {
            "auth_users": 1,
            "organizations": 1,
            "students": 1,
            "training_plans": 1,
            "training_exercises": 1,
            "access_links": 1,
            "workout_sessions": 0,
            "workout_logs": 0,
            "workout_feedback": 0,
        },
        "Stage 31 fixture post-apply counts",
    )
    require(
        authority.get("production_boundary", {}),
        {
            "active_transport": "directRpc",
            "resolved_transport": "directRpc",
            "edge_gateway_selected": False,
            "flutter_uses_edge_gateway_in_production": False,
            "direct_v2_rpc_path_active": True,
            "direct_anon_v2_rpc_execute_revoked": False,
            "explicit_rollback_requested": False,
            "explicit_rollback_authorized": False,
            "automatic_edge_to_direct_fallback": False,
            "client_cutover_verified": False,
            "behavioral_transport_change": False,
        },
        "historical Stage 31 production boundary",
    )
    runtime = authority.get("runtime_proof", {})
    if runtime.get("workflow_run_id") is not None or runtime.get("result") is not None:
        fail("live client proof receipt appeared before the dedicated proof stage")
    for key in (
        "flutter_transport_edge_path_verified", "get_workout_verified", "start_workout_verified",
        "set_completion_verified", "get_feedback_context_verified", "submit_feedback_verified",
        "all_five_routes_verified", "raw_token_returned", "raw_network_origin_returned",
        "real_customer_data_used", "real_customer_data_mutated", "proof_reexecution_allowed", "cleanup_completed",
    ):
        if runtime.get(key) is not False:
            fail(f"Stage 31 runtime proof self-attested during fixture reconciliation: {key}")
    require(
        authority.get("next_stage", {}),
        {
            "name": "PREPARE_STAGE31_CLIENT_EDGE_RUNTIME_LIVE_PROOF",
            "allowed_now": True,
            "requires_exact_pr_and_head_seal_before_first_execution": True,
            "requires_one_shot_workflow": True,
            "requires_fixture_remote_applied": True,
            "may_select_edge_gateway_now": False,
            "may_revoke_direct_rpc_execute_now": False,
        },
        "Stage 31 remote next stage",
    )
    if any(value is not False for value in authority.get("launch_authority", {}).values()):
        fail("Stage 31 fixture reconciliation gained launch authority")

    if ledger.get("baseline_main_sha") != CURRENT_BASELINE or ledger.get("observed_at_utc") != "2026-08-21T11:34:15Z":
        fail("Stage 31 migration ledger observation/baseline drifted")
    remote = {row.get("name"): row.get("version") for row in ledger.get("remote_migrations", []) if isinstance(row, dict)}
    if remote.get(FIXTURE_NAME) != REMOTE_VERSION:
        fail("Stage 31 remote migration receipt missing from ledger")
    repo_only = {
        row.get("name") for row in ledger.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    }
    if repo_only:
        fail(f"remote-reconciled Stage 31 ledger still has repo_only divergence: {sorted(repo_only)}")

    sql = FIXTURE_SQL.read_text(encoding="utf-8")
    for fragment in (
        "BGF-STAGE31-CLIENT-EDGE-RUNTIME-FIXTURE-216",
        "STAGE31_CLIENT_EDGE_RUNTIME_FIXTURE_REQUIRES_EMPTY_CUSTOMER_DOMAIN",
        "STAGE31_CLIENT_EDGE_RUNTIME_FIXTURE_POSTCONDITION_FAILED",
        "extensions.digest(v_token, 'sha256')",
    ):
        if fragment not in sql:
            fail(f"merged Stage 31 fixture source drifted: {fragment}")
    return authority, ledger


def repo_authority_projection(current: dict) -> dict:
    value = json.loads(json.dumps(current))
    value["current_state"] = REPO_STATE
    value["baseline_main_sha"] = PREPARATION_BASELINE
    value.pop("preparation_baseline_main_sha", None)
    value.pop("historical_guard_projection_failure_class", None)
    value.pop("fixture_remote_reconciliation_failure_class", None)
    value.pop("pre_apply_receipt", None)
    value.pop("remote_apply_receipt", None)
    value["fixture"]["migration_ledger_state"] = "repo_only"
    value["fixture"]["remote_applied"] = False
    value["fixture"]["remote_version"] = None
    value["next_stage"] = {
        "name": "APPLY_STAGE31_CLIENT_EDGE_RUNTIME_FIXTURE",
        "allowed_now": True,
        "requires_ci_and_merge_first": True,
        "requires_exact_merged_sql": True,
        "requires_fresh_migration_ledger_check_immediately_before_apply": True,
        "may_select_edge_gateway_now": False,
        "may_revoke_direct_rpc_execute_now": False,
    }
    return value


def repo_ledger_projection(current: dict) -> dict:
    value = json.loads(json.dumps(current))
    value["baseline_main_sha"] = PREPARATION_BASELINE
    value["observed_at_utc"] = "2026-08-21T10:44:35Z"
    value["remote_migrations"] = [
        row for row in value.get("remote_migrations", [])
        if not (isinstance(row, dict) and row.get("name") == FIXTURE_NAME)
    ]
    value["declared_divergences"].append(
        {
            "direction": "repo_only",
            "name": FIXTURE_NAME,
            "reason": "Controlled synthetic fixture for the Stage 31 Flutter-client-to-Edge runtime proof. Apply only after CI and merge while the authoritative customer domain remains empty.",
            "owner": "BlackGold Forge",
            "related_failure_class": "BGF-STAGE31-CLIENT-EDGE-RUNTIME-FIXTURE-216",
        }
    )
    return value


def historical_cutover_projection(current: dict) -> dict:
    value = json.loads(json.dumps(current))
    value["current_state"] = STAGE31_PREREQ_CUTOVER_STATE
    value["baseline_main_sha"] = STAGE31_PREREQ_CUTOVER_BASELINE
    value["current_client_inventory"].update(
        {
            "transport_mode": "direct_rpc",
            "flutter_uses_edge_gateway": False,
            "direct_v2_rpc_path_active": True,
            "direct_anon_v2_rpc_execute_revoked": False,
            "client_direct_rpc_fallback_removed": False,
            "repositories_call_supabase_rpc_directly": False,
            "repositories_call_single_transport": True,
        }
    )
    value["transport_contract"].update(
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
            "edge_candidate_path_compiled_behind_inactive_mode": True,
            "behavioral_transport_change": False,
        }
    )
    value["transport_contract"].pop("edge_path_active_in_repository_source", None)
    value["rollback_harness"].update(
        {
            "production_active_mode": "directRpc",
            "explicit_rollback_requested": False,
            "explicit_rollback_authorized": False,
            "runtime_rollback_verified": True,
            "runtime_rollback_proof_kind": "isolated_resolver_no_network",
            "harness_ready": True,
        }
    )
    value["rollback_harness"].pop("pre_cutover_runtime_rollback_verified", None)
    value["rollback_harness"].pop("post_cutover_runtime_rollback_verified", None)
    value.pop("stage32_selection", None)
    value["next_stage"] = {
        "name": "STAGE31_CLIENT_EDGE_RUNTIME_PROOF_PREPARATION",
        "allowed_now": True,
        "requires_synthetic_customer_fixture": True,
        "requires_production_transport_change": False,
        "requires_direct_rpc_grants_to_remain": True,
        "may_select_edge_gateway_now": False,
        "may_revoke_direct_rpc_execute_now": False,
    }
    return value


def historical_contract_projection(source: str) -> str:
    value = source.replace("StudentAccessTransportMode.edgeGateway;", "StudentAccessTransportMode.directRpc;", 1)
    value = value.replace("static const bool edgeGatewaySelected = true;", "static const bool edgeGatewaySelected = false;", 1)
    return value


def run(mode: str) -> None:
    if mode not in MODES:
        fail(f"unsupported mode: {mode}")

    current_authority, current_ledger = validate_current()
    current_cutover = load(CUTOVER)
    current_contract = CONTRACT.read_text(encoding="utf-8")

    with tempfile.TemporaryDirectory(prefix="fitnexus-stage31-remote-reconcile-") as tmp:
        temp_root = Path(tmp)
        temp_authority = temp_root / "student_access_client_edge_runtime_proof_authority.json"
        temp_ledger = temp_root / "migration_ledger_authority.json"
        temp_cutover = temp_root / "student_access_client_cutover_authority.json"
        temp_contract = temp_root / "student_access_transport_contract_historical.dart"
        temp_authority.write_text(json.dumps(repo_authority_projection(current_authority), indent=2) + "\n", encoding="utf-8")
        temp_ledger.write_text(json.dumps(repo_ledger_projection(current_ledger), indent=2) + "\n", encoding="utf-8")
        temp_cutover.write_text(json.dumps(historical_cutover_projection(current_cutover), indent=2) + "\n", encoding="utf-8")
        temp_contract.write_text(historical_contract_projection(current_contract), encoding="utf-8")

        stage31_guard = importlib.import_module("verify_student_access_client_edge_runtime_preparation")
        stage31_guard.AUTHORITY = temp_authority
        stage31_guard.LEDGER = temp_ledger
        stage31_guard.CUTOVER = temp_cutover
        stage31_guard.CONTRACT = temp_contract

        if mode == "stage31":
            stage31_guard.main()
        else:
            compat = importlib.import_module("verify_stage31_repo_only_historical_guard_compat")
            compat.STAGE31_AUTHORITY = temp_authority
            compat.LEDGER = temp_ledger
            compat.CUTOVER = temp_cutover
            compat.CONTRACT = temp_contract
            compat.run(mode)

    print("STAGE31_FIXTURE_REMOTE_RECONCILIATION_GUARD=PASS")
    print(f"MODE={mode}")
    print(f"CURRENT_STATE={CURRENT_STATE}")
    print(f"REMOTE_VERSION={REMOTE_VERSION}")
    print(f"FAILURE_CLASS={RECONCILIATION_CLASS}")
    print("FIXTURE_REMOTE_APPLIED=true")
    print("FIXTURE_LEDGER=REMOTE_RECONCILED")
    print("LIVE_CLIENT_EDGE_PROOF=NOT_EXECUTED")
    print("HISTORICAL_STAGE31_PRODUCTION_TRANSPORT=directRpc")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")
    print("NEXT=PREPARE_STAGE31_CLIENT_EDGE_RUNTIME_LIVE_PROOF")
    print("LAUNCH_GATE_PROMOTION=DENIED")


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: verify_stage31_fixture_remote_reconciliation.py <stage31|rate_limit|valid_route|smoke|rollback>")
    run(sys.argv[1])


if __name__ == "__main__":
    main()
