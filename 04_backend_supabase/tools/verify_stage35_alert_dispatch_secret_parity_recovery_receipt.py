from __future__ import annotations

import importlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage35_alert_dispatch_secret_parity_recovery_receipt_authority.json"
FAILED_TRIGGER = "761bd84534350cd5f7a0cb1530f8e511c620de77"
BASELINE = "ca298277ac4550fe69ef36f79c64f7bb1fcf78ef"


def fail(message: str) -> None:
    raise SystemExit("STAGE35_DISPATCH_SECRET_PARITY_RECOVERY_RECEIPT_GUARD=FAIL\n" + message)


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"unable to read {path.relative_to(ROOT)}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"expected JSON object: {path.relative_to(ROOT)}")
    return value


def require(mapping: dict, expected: dict, label: str) -> None:
    if not isinstance(mapping, dict):
        fail(f"{label} must be an object")
    for key, value in expected.items():
        if mapping.get(key) != value:
            fail(f"{label} drift: {key}")


def main() -> None:
    # Prove the merged recovery seal is still internally consistent first.
    recovery = importlib.import_module("verify_stage35_alert_dispatch_secret_parity_recovery")
    recovery.main()

    authority = load(AUTHORITY)
    require(authority, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE35_ALERT_DISPATCH_SECRET_PARITY_RECOVERY_RECEIPT",
        "baseline_main_sha": BASELINE,
        "current_state": "DISPATCH_SECRET_PARITY_VERIFIED_PROVIDER_FREE_FRESH_REMOTE_RECEIPT_COMPLETE",
    }, "recovery receipt authority")

    if set(authority.get("failure_classes", [])) != {
        "BGF-STAGE35-ALERT-MANAGEMENT-SECRET-READBACK-PLAINTEXT-ASSUMPTION-303",
        "BGF-STAGE35-ALERT-DISPATCH-SECRET-PARITY-304",
        "BGF-STAGE35-ALERT-FAILED-ONE-SHOT-RETRY-WITHOUT-PARITY-305",
        "BGF-STAGE35-ALERT-PARITY-ATTESTATION-PROVIDER-CROSSOVER-306",
        "BGF-STAGE35-ALERT-PARITY-RECOVERY-RECEIPT-DRIFT-307",
    }:
        fail("failure-class set drifted")

    require(authority.get("recovery_seal_receipt", {}), {
        "pull_request": 113,
        "head_sha": "1618476d261b3bc39df1bcb8b3f6964145959893",
        "merge_main_sha": BASELINE,
        "recovery_contract_run": 32647706269,
        "recovery_contract_job": 97214411829,
        "recovery_contract_result": "PASS",
        "v5_guard_run": 32647706289,
        "v5_guard_job": 97214411874,
        "v5_guard_result": "PASS",
        "quality_gate_run": 32647706241,
        "quality_gate_job": 97214411792,
        "quality_gate_result": "PASS",
        "historical_one_shot_proofs_reexecuted": False,
    }, "recovery seal receipt")

    require(authority.get("failed_external_proof_frozen", {}), {
        "pull_request": 112,
        "run": 32647288419,
        "job": 97213360238,
        "http_status": 401,
        "provider_call_reached": False,
        "pull_request_closed_unmerged": True,
        "run_rerun_allowed": False,
        "pull_request_reopen_allowed": False,
    }, "failed external proof frozen receipt")

    require(authority.get("provider_free_parity_attestation", {}), {
        "pull_request": 114,
        "head_sha": "1ff161184db2b91912c94fd8a4e89a3a71c42566",
        "run": 32648015715,
        "job": 97215180531,
        "result": "PASS",
        "pull_request_closed_unmerged": True,
        "expected_http_status": 400,
        "expected_error": "ALERT_DISPATCH_BODY_FIELD_FORBIDDEN",
        "custom_auth_gate_passed": True,
        "body_rejected_before_runtime_provider_config": True,
        "database_claim_called": False,
        "delivery_receipt_written": False,
        "telegram_provider_called": False,
        "secret_value_printed": False,
        "secret_digest_printed": False,
        "attestation_pr_reopen_allowed": False,
        "attestation_pr_merge_allowed": False,
    }, "provider-free parity attestation")

    receipt = authority.get("fresh_remote_receipt", {})
    require(receipt, {
        "source": "Supabase.execute_sql+Supabase.list_migrations+Supabase.list_edge_functions",
        "observed_at_utc": "2026-08-23T15:16:57.960466Z",
        "auth_users": 0,
        "organizations": 0,
        "students": 0,
        "security_events": 0,
        "security_signals": 1,
        "exact_controlled_proof_signals": 1,
        "alert_delivery_receipts": 0,
        "controlled_proof_receipts": 0,
        "network_buckets": 13,
        "growth_events": 6,
        "anon_execute_count": 0,
        "authenticated_execute_count": 0,
        "service_role_execute_count": 5,
        "issue_student_access_token_v2_authenticated_execute": True,
        "receipt_store_remote_version": "20260823092354",
        "controlled_fixture_remote_version": "20260823145908",
        "stage35_remote_migration_count": 2,
        "deployed_edge_function_count": 2,
        "dispatcher_source_bundle_unchanged_from_initial_deploy": True,
        "provider_delivery_consumed": False,
        "proof_signal_still_unclaimed": True,
    }, "fresh remote receipt")
    expected_functions = [
        {
            "slug": "student-access-gateway",
            "version": 8,
            "status": "ACTIVE",
            "verify_jwt": False,
            "bundle_sha256": "b57892b3f399b76f8127c9a39d3d8c021ffe639aa7bf92c7fa9a459d35721b82",
        },
        {
            "slug": "student-access-alert-dispatcher",
            "version": 2,
            "status": "ACTIVE",
            "verify_jwt": False,
            "bundle_sha256": "56cfef7be1dc327ac21a8e1aaacd3b82d20a810cb8a4819da4061e1204d4a627",
        },
    ]
    if receipt.get("deployed_edge_functions") != expected_functions:
        fail("fresh Edge inventory drifted")

    require(authority.get("recovery_observation_boundary", {}), {
        "recovery_push_run_id_directly_observed_by_connector": False,
        "parity_recovery_effect_independently_proven": True,
        "secret_value_equality_now_proven_operationally": True,
        "secret_values_observed": False,
        "secret_digests_observed": False,
        "telegram_bot_token_rotated_by_recovery_contract": False,
        "telegram_chat_id_rotated_by_recovery_contract": False,
        "database_rows_mutated_by_parity_attestation": False,
        "provider_called_by_parity_attestation": False,
    }, "recovery observation boundary")

    require(authority.get("external_delivery_retry_authority", {}), {
        "failed_run_32647288419_may_be_rerun": False,
        "pr112_may_be_reopened": False,
        "pr114_may_be_reopened": False,
        "new_trigger_must_use_fresh_head": True,
        "new_trigger_must_use_current_main_base": True,
        "new_trigger_branch": "blackgold/stage35-alert-external-delivery-proof-trigger",
        "new_trigger_file": "04_backend_supabase/stage35_alert_external_delivery_proof_trigger.json",
        "existing_failed_trigger_head_may_be_reused": False,
        "provider_delivery_proof_consumed": False,
        "new_one_shot_trigger_allowed_now": True,
        "successful_new_proof_may_be_replayed": False,
    }, "external delivery retry authority")

    require(authority.get("launch_boundary", {}), {
        "incident_response_gate": "DENIED",
        "production_deployment_gate": "DENIED",
        "paid_media_gate": "DENIED",
        "launch_gate": "DENIED",
    }, "launch boundary")

    next_stage = authority.get("next_stage", {})
    require(next_stage, {
        "name": "PREPARE_FRESH_STAGE35_EXTERNAL_DELIVERY_ONE_SHOT_TRIGGER",
        "allowed_now": True,
        "requires_recovery_receipt_merge_to_main": True,
        "requires_fresh_trigger_head_not_equal": FAILED_TRIGGER,
        "requires_exact_one_signal_zero_receipts": True,
        "requires_no_customer_data": True,
        "requires_no_reopen_pr112": True,
        "requires_no_rerun_32647288419": True,
        "may_promote_launch_gates": False,
    }, "next stage")

    print("STAGE35_DISPATCH_SECRET_PARITY_RECOVERY_RECEIPT_GUARD=PASS")
    print(f"BASELINE_MAIN_SHA={BASELINE}")
    print("PARITY_ATTESTATION=PASS")
    print("PARITY_ATTESTATION_PROVIDER_CALLED=false")
    print("EXACT_PROOF_SIGNALS=1")
    print("PROOF_RECEIPTS=0")
    print("RECEIPT_STORE_REMOTE_VERSION=20260823092354")
    print("CONTROLLED_FIXTURE_REMOTE_VERSION=20260823145908")
    print("FRESH_EXTERNAL_DELIVERY_TRIGGER_ALLOWED=true")
    print("FAILED_EXTERNAL_PROOF_RERUN_ALLOWED=false")
    print("PR112_REOPEN_ALLOWED=false")
    print("PR114_REOPEN_ALLOWED=false")
    print("INCIDENT_RESPONSE_GATE=DENIED")
    print("PRODUCTION_DEPLOYMENT_GATE=DENIED")
    print("PAID_MEDIA_GATE=DENIED")
    print("LAUNCH_GATE=DENIED")


if __name__ == "__main__":
    main()
