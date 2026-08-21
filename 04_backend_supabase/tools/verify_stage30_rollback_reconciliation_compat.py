from __future__ import annotations

import importlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
APP = ROOT / "03_app_flutter" / "fitnexus_app"
CUTOVER = BACKEND / "student_access_client_cutover_authority.json"
ROLLBACK = BACKEND / "student_access_runtime_rollback_authority.json"
SMOKE = BACKEND / "student_access_client_runtime_smoke_authority.json"
LEDGER = BACKEND / "migration_ledger_authority.json"
CONTRACT = APP / "lib" / "features" / "student" / "student_access_transport_contract.dart"

RECONCILIATION_CLASS = "BGF-ROLLBACK-PROOF-CUTOVER-RECONCILIATION-213"
HISTORICAL_ADVANCE_CLASS = "BGF-HISTORICAL-GUARD-DOWNSTREAM-AUTHORITY-ADVANCE-214"
CURRENT_CUTOVER_STATE = "CLIENT_RUNTIME_ROLLBACK_VERIFIED_DIRECT_MODE"
HISTORICAL_CUTOVER_STATE = "CLIENT_EDGE_ERROR_CONTRACT_ROLLBACK_HARNESS_READY_DIRECT_MODE"
CURRENT_ROLLBACK_STATE = "RUNTIME_ROLLBACK_PROOF_RECONCILED_DIRECT_MODE"
HISTORICAL_ROLLBACK_STATE = "RUNTIME_ROLLBACK_PROOF_VERIFIED_DIRECT_MODE"
CURRENT_BASELINE = "eb578b06fed57987b3dba94d7c9a7931974743c4"
HISTORICAL_CUTOVER_BASELINE = "5f088a361f2ee78a88fc0435250a83d571eda34c"
PROOF_BASELINE = "f1b97f3b56124f2fd2d3edcff7060afd82f08c1e"
SEALED_RUN = 32464990624
SEALED_JOB = 96719614075

TARGETS = {
    "cutover": "verify_student_access_client_cutover_preparation",
    "smoke": "verify_student_access_client_runtime_smoke",
    "rollback": "verify_student_access_runtime_rollback_candidate",
}


def fail(message: str) -> None:
    raise SystemExit("STAGE30_ROLLBACK_RECONCILIATION_COMPAT=FAIL\n" + message)


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


def validate_actual_authority() -> tuple[dict, dict]:
    cutover = load(CUTOVER)
    rollback = load(ROLLBACK)
    smoke = load(SMOKE)
    ledger = load(LEDGER)

    require(
        cutover,
        {
            "schema_version": 2,
            "project_ref": "mceukeondizkwlpfxzgf",
            "current_state": CURRENT_CUTOVER_STATE,
            "baseline_main_sha": CURRENT_BASELINE,
            "rollback_reconciliation_failure_classes": [
                RECONCILIATION_CLASS,
                HISTORICAL_ADVANCE_CLASS,
            ],
        },
        "current cutover authority",
    )

    inventory = cutover.get("current_client_inventory", {})
    require(
        inventory,
        {
            "transport_mode": "direct_rpc",
            "flutter_uses_edge_gateway": False,
            "direct_v2_rpc_path_active": True,
            "direct_anon_v2_rpc_execute_revoked": False,
            "client_direct_rpc_fallback_removed": False,
            "repositories_call_supabase_rpc_directly": False,
            "repositories_call_single_transport": True,
        },
        "current client inventory",
    )

    transport = cutover.get("transport_contract", {})
    require(
        transport,
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
        "current transport contract",
    )

    harness = cutover.get("rollback_harness", {})
    require(
        harness,
        {
            "resolver": "resolveStudentAccessTransportMode",
            "production_active_mode": "directRpc",
            "explicit_rollback_requested": False,
            "explicit_rollback_authorized": False,
            "unauthorized_rollback_fails_closed": True,
            "rollback_from_non_edge_mode_rejected": True,
            "authorized_edge_to_direct_transition_unit_tested": True,
            "runtime_rollback_verified": True,
            "runtime_rollback_proof_kind": "isolated_resolver_no_network",
            "harness_ready": True,
        },
        "rollback harness reconciliation",
    )

    receipt = cutover.get("rollback_proof_receipt", {})
    require(
        receipt,
        {
            "workflow_run_id": SEALED_RUN,
            "job_id": SEALED_JOB,
            "result": "PASS",
            "focused_tests_passed_count": 6,
            "production_transport_change": False,
            "network_call_executed": False,
            "real_customer_data_used": False,
            "direct_rpc_grants_changed": False,
            "edge_selection": False,
            "launch_gate_promotion": False,
            "proof_reexecution_allowed": False,
        },
        "cutover rollback receipt",
    )

    before_edge = cutover.get("required_before_edge_selection", {})
    if before_edge.get("explicit_rollback_proof") is not True:
        fail("rollback proof was not reconciled into Edge-selection prerequisites")
    for key in (
        "read_only_edge_runtime_smoke_after_client_source_change",
        "command_edge_runtime_smoke_with_synthetic_fixture",
        "cutover_receipt_materialized",
    ):
        if before_edge.get(key) is not False:
            fail(f"Edge-selection prerequisite self-attested during reconciliation: {key}")

    before_revoke = cutover.get("required_before_direct_rpc_revocation", {})
    if before_revoke.get("automatic_direct_fallback_absent") is not True:
        fail("fail-open fallback invariant disappeared")
    for key in (
        "flutter_edge_gateway_active",
        "five_routes_verified_via_edge",
        "post_cutover_rollback_path_verified",
        "post_cutover_observation_window_passed",
        "security_advisor_rechecked",
    ):
        if before_revoke.get(key) is not False:
            fail(f"direct-RPC revocation prerequisite self-attested: {key}")

    reconciliation = cutover.get("reconciliation", {})
    require(
        reconciliation,
        {
            "failure_class": RECONCILIATION_CLASS,
            "historical_guard_advance_failure_class": HISTORICAL_ADVANCE_CLASS,
            "rollback_proof_reconciled": True,
            "production_transport_changed": False,
            "edge_gateway_selected": False,
            "direct_rpc_execute_revoked": False,
            "launch_gate_promoted": False,
            "historical_guards_must_validate_current_authority_before_projection": True,
        },
        "cutover reconciliation receipt",
    )

    next_stage = cutover.get("next_stage", {})
    require(
        next_stage,
        {
            "name": "STAGE31_CLIENT_EDGE_RUNTIME_PROOF_PREPARATION",
            "allowed_now": True,
            "requires_synthetic_customer_fixture": True,
            "requires_production_transport_change": False,
            "requires_direct_rpc_grants_to_remain": True,
            "may_select_edge_gateway_now": False,
            "may_revoke_direct_rpc_execute_now": False,
        },
        "cutover next stage",
    )
    if any(value is not False for value in cutover.get("launch_authority", {}).values()):
        fail("rollback reconciliation gained launch authority")

    require(
        rollback,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "current_state": CURRENT_ROLLBACK_STATE,
            "baseline_main_sha": CURRENT_BASELINE,
            "proof_baseline_main_sha": PROOF_BASELINE,
            "reconciliation_failure_classes": [
                RECONCILIATION_CLASS,
                HISTORICAL_ADVANCE_CLASS,
            ],
        },
        "rollback authority reconciliation",
    )

    proof = rollback.get("runtime_proof", {})
    require(
        proof,
        {
            "workflow_run_id": SEALED_RUN,
            "result": "PASS",
            "focused_test_passed": True,
            "focused_tests_passed_count": 6,
            "production_constants_unchanged": True,
            "edge_without_rollback_verified": True,
            "unauthorized_rollback_fail_closed_verified": True,
            "authorized_edge_to_direct_verified": True,
            "rollback_from_direct_rejected_verified": True,
            "deterministic_resolution_verified": True,
            "network_call_executed": False,
            "real_customer_data_used": False,
            "direct_rpc_grants_changed": False,
            "edge_selected": False,
            "launch_gate_promoted": False,
            "proof_reexecution_allowed": False,
        },
        "rollback proof",
    )

    rollback_reconciliation = rollback.get("cutover_reconciliation", {})
    require(
        rollback_reconciliation,
        {
            "cutover_authority_reconciled": True,
            "reconciled_state": CURRENT_CUTOVER_STATE,
            "reconciled_against_main_sha": CURRENT_BASELINE,
            "production_transport_change_allowed_in_reconciliation": False,
            "production_transport_changed": False,
            "edge_selection_allowed_in_reconciliation": False,
            "edge_selected": False,
            "direct_rpc_execute_revocation_allowed_in_reconciliation": False,
            "direct_rpc_execute_revoked": False,
            "launch_gate_promoted": False,
        },
        "rollback reconciliation",
    )

    smoke_runtime = smoke.get("runtime_proof", {})
    if smoke.get("current_state") != "EDGE_RUNTIME_SMOKE_LIVE_VERIFIED_CLEANUP_COMPLETE":
        fail("sealed five-route smoke authority regressed")
    for key in ("all_five_routes_verified", "cleanup_completed"):
        if smoke_runtime.get(key) is not True:
            fail(f"sealed smoke prerequisite regressed: {key}")
    for key in (
        "synthetic_business_rows_remaining",
        "synthetic_security_rows_remaining",
        "synthetic_network_proof_rows_remaining",
    ):
        if smoke_runtime.get(key) != 0:
            fail(f"synthetic smoke residue returned: {key}")

    repo_only = [
        row
        for row in ledger.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    ]
    if repo_only:
        fail("rollback reconciliation must not carry a repo_only migration divergence")

    try:
        contract = CONTRACT.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"transport contract unavailable: {type(exc).__name__}")
    for fragment in (
        "StudentAccessTransportMode.directRpc;",
        "static const bool edgeGatewaySelected = false;",
        "static const bool automaticEdgeToDirectFallback = false;",
        "static const bool explicitRollbackRequested = false;",
        "static const bool explicitRollbackAuthorized = false;",
        "static const bool directRpcExecuteRevoked = false;",
        "static const bool rollbackVerified = false;",
        "static const bool clientCutoverVerified = false;",
    ):
        if fragment not in contract:
            fail(f"production source changed during reconciliation: {fragment}")

    return cutover, rollback


def historical_cutover_projection(current: dict) -> dict:
    value = json.loads(json.dumps(current))
    value["current_state"] = HISTORICAL_CUTOVER_STATE
    value["baseline_main_sha"] = HISTORICAL_CUTOVER_BASELINE
    value["rollback_harness"]["runtime_rollback_verified"] = False
    value["rollback_harness"].pop("runtime_rollback_proof_kind", None)
    value["cutover_invariants"]["direct_execute_must_remain_until_rollback_proof"] = True
    value["required_before_edge_selection"]["explicit_rollback_proof"] = False
    value["required_before_direct_rpc_revocation"]["rollback_path_verified"] = False
    value["next_stage"] = {
        "name": "STAGE30_CONTROLLED_EDGE_RUNTIME_SMOKE_FIXTURE",
        "allowed_now": True,
        "requires_synthetic_customer_fixture": True,
        "requires_migration_ledger_protocol": True,
        "may_select_edge_gateway_now": False,
        "may_revoke_direct_rpc_execute_now": False,
    }
    return value


def historical_rollback_projection(current: dict) -> dict:
    value = json.loads(json.dumps(current))
    value["current_state"] = HISTORICAL_ROLLBACK_STATE
    value["baseline_main_sha"] = PROOF_BASELINE
    value["prerequisites"]["cutover_required_state"] = HISTORICAL_CUTOVER_STATE
    value["cutover_reconciliation"] = {
        "cutover_authority_reconciled": False,
        "required_next_state": CURRENT_CUTOVER_STATE,
        "production_transport_change_allowed_in_reconciliation": False,
        "edge_selection_allowed_in_reconciliation": False,
        "direct_rpc_execute_revocation_allowed_in_reconciliation": False,
    }
    value["next_stage"] = {
        "name": "RECONCILE_STAGE30_ROLLBACK_PROOF_IN_CUTOVER_AUTHORITY",
        "allowed_now": True,
        "requires_production_transport_change": False,
        "may_select_edge_gateway_now": False,
        "may_revoke_direct_rpc_execute_now": False,
    }
    return value


def run(mode: str) -> None:
    module_name = TARGETS.get(mode)
    if module_name is None:
        fail(f"unsupported mode: {mode}")

    current_cutover, current_rollback = validate_actual_authority()
    module = importlib.import_module(module_name)

    with tempfile.TemporaryDirectory(prefix="fitnexus-stage30-rollback-reconcile-") as tmp:
        temp_root = Path(tmp)
        temp_cutover = temp_root / "student_access_client_cutover_authority.json"
        temp_cutover.write_text(
            json.dumps(historical_cutover_projection(current_cutover), indent=2) + "\n",
            encoding="utf-8",
        )

        if mode == "cutover":
            module.AUTHORITY = temp_cutover
        elif mode == "smoke":
            module.CUTOVER = temp_cutover
        else:
            temp_rollback = temp_root / "student_access_runtime_rollback_authority.json"
            temp_rollback.write_text(
                json.dumps(historical_rollback_projection(current_rollback), indent=2) + "\n",
                encoding="utf-8",
            )
            module.CUTOVER = temp_cutover
            module.AUTHORITY = temp_rollback

        module.main()

    print("STAGE30_ROLLBACK_RECONCILIATION_COMPAT=PASS")
    print(f"MODE={mode}")
    print(f"CURRENT_CUTOVER_STATE={CURRENT_CUTOVER_STATE}")
    print(f"CURRENT_ROLLBACK_STATE={CURRENT_ROLLBACK_STATE}")
    print(f"FAILURE_CLASS={RECONCILIATION_CLASS}")
    print(f"HISTORICAL_ADVANCE_PREVENTION={HISTORICAL_ADVANCE_CLASS}")
    print("PRODUCTION_ACTIVE_TRANSPORT=directRpc")
    print("EDGE_SELECTION=false")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")
    print("NEXT=STAGE31_CLIENT_EDGE_RUNTIME_PROOF_PREPARATION")


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: verify_stage30_rollback_reconciliation_compat.py <cutover|smoke|rollback>")
    run(sys.argv[1])


if __name__ == "__main__":
    main()
