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
STAGE32 = BACKEND / "student_access_production_edge_selection_authority.json"
LEDGER = BACKEND / "migration_ledger_authority.json"
CONTRACT = APP / "lib" / "features" / "student" / "student_access_transport_contract.dart"
WORKFLOW = ROOT / ".github" / "workflows" / "stage30_runtime_rollback_proof.yml"

RECONCILIATION_CLASS = "BGF-ROLLBACK-PROOF-CUTOVER-RECONCILIATION-213"
HISTORICAL_ADVANCE_CLASS = "BGF-HISTORICAL-GUARD-DOWNSTREAM-AUTHORITY-ADVANCE-214"
RETRIGGER_CLASS = "BGF-ROLLBACK-PROOF-WORKFLOW-CROSS-PR-RETRIGGER-215"
DIRECT_CUTOVER_STATE = "CLIENT_RUNTIME_ROLLBACK_VERIFIED_DIRECT_MODE"
EDGE_CUTOVER_STATE = "CLIENT_EDGE_SELECTED_POST_CUTOVER_PROOF_PENDING"
STAGE32_EDGE_STATE = "PRODUCTION_EDGE_SELECTION_CANDIDATE_EDGE_MODE_POST_CUTOVER_PROOF_PENDING"
HISTORICAL_CUTOVER_STATE = "CLIENT_EDGE_ERROR_CONTRACT_ROLLBACK_HARNESS_READY_DIRECT_MODE"
CURRENT_ROLLBACK_STATE = "RUNTIME_ROLLBACK_PROOF_RECONCILED_DIRECT_MODE"
HISTORICAL_ROLLBACK_STATE = "RUNTIME_ROLLBACK_PROOF_VERIFIED_DIRECT_MODE"
ROLLBACK_RECONCILIATION_BASELINE = "eb578b06fed57987b3dba94d7c9a7931974743c4"
EDGE_SELECTION_BASELINE = "3cec9ebd5f01bf0b595b7c2f1600c571725e3d41"
HISTORICAL_CUTOVER_BASELINE = "5f088a361f2ee78a88fc0435250a83d571eda34c"
PROOF_BASELINE = "f1b97f3b56124f2fd2d3edcff7060afd82f08c1e"
SEALED_RUN = 32464990624
SEALED_JOB = 96719614075
BLOCKED_RETRIGGER_RUN = 32473348632
BLOCKED_RETRIGGER_JOB = 96744561273
SEALED_PR = 57
SEALED_HEAD = "blackgold/stage30-runtime-rollback-proof"

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


def validate_rollback_history(rollback: dict) -> None:
    reconciliation_classes = [RECONCILIATION_CLASS, HISTORICAL_ADVANCE_CLASS, RETRIGGER_CLASS]
    require(
        rollback,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "current_state": CURRENT_ROLLBACK_STATE,
            "baseline_main_sha": ROLLBACK_RECONCILIATION_BASELINE,
            "proof_baseline_main_sha": PROOF_BASELINE,
            "reconciliation_failure_classes": reconciliation_classes,
        },
        "historical rollback authority",
    )
    require(
        rollback.get("runtime_proof", {}),
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
        "sealed rollback proof",
    )
    require(
        rollback.get("reexecution_sentinel", {}),
        {
            "failure_class": RETRIGGER_CLASS,
            "observed_cross_pr_workflow_run_id": BLOCKED_RETRIGGER_RUN,
            "observed_cross_pr_job_id": BLOCKED_RETRIGGER_JOB,
            "observed_pr_number": 58,
            "candidate_guard_failed_before_flutter_setup": True,
            "focused_proof_step_executed": False,
            "proof_boundary_receipt_executed": False,
            "second_proof_execution_occurred": False,
            "permanent_job_condition_installed": True,
            "allowed_pr_number": SEALED_PR,
            "allowed_head_ref": SEALED_HEAD,
            "future_cross_pr_execution_allowed": False,
        },
        "rollback reexecution sentinel",
    )
    require(
        rollback.get("cutover_reconciliation", {}),
        {
            "cutover_authority_reconciled": True,
            "reconciled_state": DIRECT_CUTOVER_STATE,
            "reconciled_against_main_sha": ROLLBACK_RECONCILIATION_BASELINE,
            "production_transport_change_allowed_in_reconciliation": False,
            "production_transport_changed": False,
            "edge_selection_allowed_in_reconciliation": False,
            "edge_selected": False,
            "direct_rpc_execute_revocation_allowed_in_reconciliation": False,
            "direct_rpc_execute_revoked": False,
            "launch_gate_promoted": False,
        },
        "historical rollback reconciliation receipt",
    )


def validate_current_cutover(cutover: dict, stage32: dict, contract: str) -> str:
    reconciliation_classes = [RECONCILIATION_CLASS, HISTORICAL_ADVANCE_CLASS, RETRIGGER_CLASS]
    require(
        cutover,
        {
            "schema_version": 2,
            "project_ref": "mceukeondizkwlpfxzgf",
            "rollback_reconciliation_failure_classes": reconciliation_classes,
        },
        "current cutover identity",
    )
    state = cutover.get("current_state")
    if state == DIRECT_CUTOVER_STATE:
        require(cutover, {"baseline_main_sha": ROLLBACK_RECONCILIATION_BASELINE}, "direct cutover baseline")
        require(
            cutover.get("transport_contract", {}),
            {
                "active_mode": "directRpc",
                "resolved_mode": "directRpc",
                "edge_gateway_selected": False,
                "automatic_edge_to_direct_fallback": False,
                "direct_rpc_execute_revoked": False,
                "rollback_verified": False,
                "client_cutover_verified": False,
                "behavioral_transport_change": False,
            },
            "direct cutover contract",
        )
        for fragment in (
            "StudentAccessTransportMode.directRpc;",
            "static const bool edgeGatewaySelected = false;",
            "static const bool automaticEdgeToDirectFallback = false;",
            "static const bool directRpcExecuteRevoked = false;",
        ):
            if fragment not in contract:
                fail(f"direct production source drift: {fragment}")
        return "directRpc"

    if state != EDGE_CUTOVER_STATE:
        fail(f"unsupported downstream cutover state: {state}")
    if stage32.get("current_state") != STAGE32_EDGE_STATE:
        fail(f"{HISTORICAL_ADVANCE_CLASS} downstream Edge source lacks Stage 32 authority")
    require(cutover, {"baseline_main_sha": EDGE_SELECTION_BASELINE}, "Edge selection baseline")
    require(
        cutover.get("current_client_inventory", {}),
        {
            "transport_mode": "edge_gateway",
            "flutter_uses_edge_gateway": True,
            "direct_v2_rpc_path_active": True,
            "direct_anon_v2_rpc_execute_revoked": False,
            "repositories_call_supabase_rpc_directly": False,
            "repositories_call_single_transport": True,
        },
        "Edge-selected client inventory",
    )
    require(
        cutover.get("transport_contract", {}),
        {
            "active_mode": "edgeGateway",
            "resolved_mode": "edgeGateway",
            "edge_gateway_selected": True,
            "automatic_edge_to_direct_fallback": False,
            "explicit_rollback_requested": False,
            "explicit_rollback_authorized": False,
            "direct_rpc_execute_revoked": False,
            "rollback_verified": False,
            "client_cutover_verified": False,
            "exact_route_count": 5,
            "edge_path_active_in_repository_source": True,
            "behavioral_transport_change": True,
        },
        "Edge-selected transport contract",
    )
    require(
        cutover.get("stage32_selection", {}),
        {
            "pre_selection_main_sha": EDGE_SELECTION_BASELINE,
            "source_selected_edge_gateway": True,
            "all_five_routes_share_single_transport": True,
            "automatic_edge_to_direct_fallback": False,
            "direct_rpc_grants_changed": False,
            "post_cutover_live_proof_completed": False,
            "post_cutover_rollback_proof_completed": False,
            "launch_gate_promoted": False,
        },
        "Stage 32 cutover selection",
    )
    for fragment in (
        "StudentAccessTransportMode.edgeGateway;",
        "static const bool edgeGatewaySelected = true;",
        "static const bool automaticEdgeToDirectFallback = false;",
        "static const bool directRpcExecuteRevoked = false;",
        "static const bool rollbackVerified = false;",
        "static const bool clientCutoverVerified = false;",
    ):
        if fragment not in contract:
            fail(f"Edge-selected production source drift: {fragment}")
    return "edgeGateway"


def validate_actual_authority() -> tuple[dict, dict, str]:
    cutover = load(CUTOVER)
    rollback = load(ROLLBACK)
    smoke = load(SMOKE)
    stage32 = load(STAGE32)
    ledger = load(LEDGER)
    contract = CONTRACT.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")

    validate_rollback_history(rollback)
    current_transport = validate_current_cutover(cutover, stage32, contract)

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

    if any(
        isinstance(row, dict) and row.get("direction") == "repo_only"
        for row in ledger.get("declared_divergences", [])
    ):
        fail("rollback historical compatibility refuses repo_only migration divergence")

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
        "historical cutover rollback receipt",
    )
    if cutover.get("rollback_harness", {}).get("runtime_rollback_verified") is not True:
        fail("pre-cutover isolated rollback proof disappeared")
    if any(value is not False for value in cutover.get("launch_authority", {}).values()):
        fail("downstream cutover gained launch authority")

    sealed_condition = (
        "if: github.event.pull_request.number == 57 && "
        "github.event.pull_request.head.ref == 'blackgold/stage30-runtime-rollback-proof'"
    )
    if workflow.count(sealed_condition) != 1:
        fail(f"{RETRIGGER_CLASS} one-shot rollback workflow is not sealed")
    if "types: [opened]" not in workflow:
        fail("rollback proof workflow trigger semantics drifted")
    for forbidden in ("workflow_dispatch:", "schedule:", "types: [synchronize]", "types: [opened, synchronize]"):
        if forbidden in workflow:
            fail(f"{RETRIGGER_CLASS} rollback proof workflow became replayable: {forbidden}")

    return cutover, rollback, current_transport


def historical_cutover_projection(current: dict) -> dict:
    value = json.loads(json.dumps(current))
    value["current_state"] = HISTORICAL_CUTOVER_STATE
    value["baseline_main_sha"] = HISTORICAL_CUTOVER_BASELINE
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
            "runtime_rollback_verified": False,
            "harness_ready": True,
        }
    )
    value["rollback_harness"].pop("runtime_rollback_proof_kind", None)
    value["rollback_harness"].pop("pre_cutover_runtime_rollback_verified", None)
    value["rollback_harness"].pop("post_cutover_runtime_rollback_verified", None)
    value.pop("stage32_selection", None)
    value["required_before_edge_selection"] = {
        "edge_transport_implementation_compiles": True,
        "all_five_repository_calls_routed_through_single_transport": True,
        "edge_error_contract_mapped_to_existing_student_errors": True,
        "rollback_harness_ready": True,
        "explicit_rollback_proof": False,
        "cutover_receipt_materialized": False,
    }
    value["required_before_direct_rpc_revocation"] = {
        "flutter_edge_gateway_active": False,
        "five_routes_verified_via_edge": False,
        "automatic_direct_fallback_absent": True,
        "rollback_path_verified": False,
        "post_cutover_observation_window_passed": False,
        "security_advisor_rechecked": False,
    }
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
        "required_next_state": DIRECT_CUTOVER_STATE,
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


def historical_contract_projection(source: str) -> str:
    value = source.replace(
        "StudentAccessTransportMode.edgeGateway;",
        "StudentAccessTransportMode.directRpc;",
        1,
    )
    value = value.replace(
        "static const bool edgeGatewaySelected = true;",
        "static const bool edgeGatewaySelected = false;",
        1,
    )
    return value


def run(mode: str) -> None:
    module_name = TARGETS.get(mode)
    if module_name is None:
        fail(f"unsupported mode: {mode}")

    current_cutover, current_rollback, current_transport = validate_actual_authority()
    module = importlib.import_module(module_name)

    with tempfile.TemporaryDirectory(prefix="fitnexus-stage30-rollback-reconcile-") as tmp:
        temp_root = Path(tmp)
        temp_cutover = temp_root / "student_access_client_cutover_authority.json"
        temp_cutover.write_text(
            json.dumps(historical_cutover_projection(current_cutover), indent=2) + "\n",
            encoding="utf-8",
        )
        temp_contract = temp_root / "student_access_transport_contract_historical.dart"
        temp_contract.write_text(
            historical_contract_projection(CONTRACT.read_text(encoding="utf-8")),
            encoding="utf-8",
        )

        if mode == "cutover":
            module.AUTHORITY = temp_cutover
            module.CONTRACT = temp_contract
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
            module.CONTRACT = temp_contract

        module.main()

    print("STAGE30_ROLLBACK_RECONCILIATION_COMPAT=PASS")
    print(f"MODE={mode}")
    print(f"CURRENT_CUTOVER_STATE={current_cutover.get('current_state')}")
    print(f"CURRENT_ROLLBACK_STATE={CURRENT_ROLLBACK_STATE}")
    print(f"FAILURE_CLASS={RECONCILIATION_CLASS}")
    print(f"HISTORICAL_ADVANCE_PREVENTION={HISTORICAL_ADVANCE_CLASS}")
    print(f"CROSS_PR_RETRIGGER_PREVENTION={RETRIGGER_CLASS}")
    print(f"CURRENT_PRODUCTION_TRANSPORT={current_transport}")
    print("HISTORICAL_PROJECTED_TRANSPORT=directRpc")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: verify_stage30_rollback_reconciliation_compat.py <cutover|smoke|rollback>")
    run(sys.argv[1])


if __name__ == "__main__":
    main()
