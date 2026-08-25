from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from stage58_billing_controlled_proof_receipt_contract import (
    CONTRACT,
    EVIDENCE_VERSION,
    FUNCTION_HASHES,
    PROJECT_REF,
    PROVIDER_CODE,
    PROVIDER_ENVIRONMENT_ID,
    RECEIPT_TYPES,
    RESULT_BY_TYPE,
    SCOPE,
    validate_receipt,
)

FAILURE_CLASS = "BGF-STAGE58-CONTROLLED-PROOF-INTAKE-GUARD-562"
ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage58_billing_controlled_proof_intake_preparation_authority.json"
CONTRACT_PATH = BACKEND / "tools/stage58_billing_controlled_proof_receipt_contract.py"
REVIEWER_PATH = BACKEND / "tools/review_stage58_billing_controlled_proof_bundle.py"
MIGRATIONS = BACKEND / "migrations"

EXPECTED_BASELINE = "a291556a26937ba117921b90ee9c61ad4e61ba99"
EXPECTED_STATE = "CONTROLLED_PROOF_RECEIPT_INTAKE_PREPARED_NO_LIVE_PROOF_NO_PROVIDER_CALL_NO_ACTIVATION_NO_FIXTURE_MUTATION"
EXPECTED_SEALED = {
    "stage56_authority": (
        "04_backend_supabase/stage56_billing_proof_complete_promotion_boundary_authority.json",
        "4822ad8f32aa7154c851b15a79804698388c8311",
    ),
    "stage56_verifier": (
        "04_backend_supabase/tools/verify_stage56_billing_proof_complete_promotion_boundary.py",
        "6560d29765cbf793f304bffab45642ae29b3add5",
    ),
    "stage57_final_reconciliation": (
        "04_backend_supabase/stage57_stage56_final_reconciliation_authority.json",
        "87f86d2685aea4ca8499a7345906e5ee6c04a8dc",
    ),
    "billing_provider_contract_guard": (
        "04_backend_supabase/tools/verify_billing_provider_contract.py",
        "aafc61f9844476f35a86487e736db87e826068a2",
    ),
}
EXPECTED_FAILURE_CLASSES = {
    "BGF-STAGE58-LIVE-PROOF-DURING-INTAKE-PREPARATION-550",
    "BGF-STAGE58-MISSING-STAGE54-CREDENTIAL-AUTHORITY-BYPASS-551",
    "BGF-STAGE58-RECEIPT-TYPE-MASQUERADE-552",
    "BGF-STAGE58-DUPLICATE-RECEIPT-TYPE-553",
    "BGF-STAGE58-RAW-SECRET-IN-RECEIPT-554",
    "BGF-STAGE58-CUSTOMER-DATA-IN-PROOF-555",
    "BGF-STAGE58-FINANCIAL-CHARGE-FALSE-REQUIREMENT-556",
    "BGF-STAGE58-RECEIPT-STRUCTURE-AS-INDEPENDENT-REVIEW-557",
    "BGF-STAGE58-BUNDLE-AS-PROOF-COMPLETE-AUTHORITY-558",
    "BGF-STAGE58-RECEIPT-PATH-LEAKAGE-559",
    "BGF-STAGE58-FUNCTION-AUTHORITY-DRIFT-560",
    "BGF-STAGE58-CLEANUP-OMISSION-561",
    "BGF-STAGE58-CONTROLLED-PROOF-INTAKE-GUARD-562",
}


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE58_BILLING_CONTROLLED_PROOF_INTAKE_PREPARATION=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\nDETAIL={detail}"
    )


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def load_authority() -> dict[str, Any]:
    try:
        value = json.loads(AUTHORITY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"authority unreadable: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail("authority must be a JSON object")
    return value


def verify_authority() -> None:
    authority = load_authority()
    expected_top = {
        "schema_version": 1,
        "project_ref": PROJECT_REF,
        "stage": "STAGE58_BILLING_CONTROLLED_PROOF_INTAKE_PREPARATION",
        "baseline_main_sha": EXPECTED_BASELINE,
        "current_state": EXPECTED_STATE,
    }
    for key, expected in expected_top.items():
        if authority.get(key) != expected:
            fail(f"authority drift: {key}")

    remote = authority.get("fresh_remote_read_only_snapshot")
    if not isinstance(remote, dict):
        fail("fresh remote snapshot missing")
    expected_remote = {
        "observed_at_utc": "2026-08-25T01:45:34.110756+00:00",
        "selection_state": "selected_pending_credentials",
        "selection_activated_at": None,
        "credentials_verified_rows": 0,
        "proof_complete_rows": 0,
        "checkout_intents": 0,
        "webhook_receipts": 0,
        "remote_mutation_performed": False,
    }
    for key, expected in expected_remote.items():
        if remote.get(key) != expected:
            fail(f"fresh remote snapshot drift: {key}")

    functions = remote.get("functions")
    if not isinstance(functions, dict) or set(functions) != {
        "activate_billing_provider_selection",
        "create_billing_checkout_intent",
        "attach_billing_provider_checkout",
        "record_billing_webhook_receipt",
        "mark_billing_webhook_receipt",
    }:
        fail("remote billing function inventory drift")
    function_expected = {
        "activate_billing_provider_selection": (FUNCTION_HASHES["activate"], True, True, False, False),
        "create_billing_checkout_intent": (FUNCTION_HASHES["create_checkout"], False, False, True, False),
        "attach_billing_provider_checkout": (FUNCTION_HASHES["attach_checkout"], True, True, False, False),
        "record_billing_webhook_receipt": (FUNCTION_HASHES["record_webhook"], True, True, False, False),
        "mark_billing_webhook_receipt": (FUNCTION_HASHES["mark_webhook"], True, True, False, False),
    }
    for name, (digest, security_definer, service_exec, authenticated_exec, anon_exec) in function_expected.items():
        entry = functions[name]
        if entry.get("definition_sha256") != digest:
            fail(f"remote billing function hash drift: {name}")
        if entry.get("security_definer") is not security_definer:
            fail(f"remote billing security mode drift: {name}")
        if entry.get("service_role_execute") is not service_exec:
            fail(f"service-role execute authority drift: {name}")
        if entry.get("authenticated_execute") is not authenticated_exec:
            fail(f"authenticated execute authority drift: {name}")
        if entry.get("anon_execute") is not anon_exec:
            fail(f"anon execute authority drift: {name}")

    sealed = authority.get("sealed_inputs")
    if not isinstance(sealed, dict) or set(sealed) != set(EXPECTED_SEALED):
        fail("sealed input registry drift")
    for label, (path_rel, expected_blob) in EXPECTED_SEALED.items():
        entry = sealed[label]
        path = ROOT / path_rel
        if entry.get("path") != path_rel or entry.get("git_blob_sha") != expected_blob:
            fail(f"sealed input declaration drift: {label}")
        if not path.is_file() or git_blob_sha(path) != expected_blob:
            fail(f"sealed input bytes drift: {label}")

    contract = authority.get("intake_contract")
    if not isinstance(contract, dict) or contract.get("contract_id") != CONTRACT:
        fail("intake contract missing or drifted")
    if set(contract.get("required_receipt_types", [])) != set(RECEIPT_TYPES):
        fail("required receipt type set drift")
    for key in (
        "exactly_one_receipt_per_type",
        "canonical_receipt_sha256_is_stage56_proof_digest",
        "proof_bundle_digest_is_canonical_digest_map_sha256",
        "future_live_proof_requires_separate_explicit_authorization",
        "future_live_proof_requires_real_stage54_credentials_verified_authority",
        "future_live_proof_must_use_synthetic_non_customer_fixtures",
        "future_live_proof_requires_cleanup_before_independent_review",
    ):
        if contract.get(key) is not True:
            fail(f"fail-closed intake contract drift: {key}")
    for key in (
        "receipt_path_or_filename_copied_to_bundle",
        "raw_receipt_body_copied_to_bundle",
        "unknown_receipt_type_allowed",
        "duplicate_receipt_type_allowed",
        "customer_data_allowed",
        "raw_secret_allowed_in_receipt",
        "real_financial_charge_required",
        "paid_subscription_creation_required",
        "stage58_tooling_provider_call_allowed",
        "stage58_tooling_provider_activation_allowed",
        "stage58_tooling_supabase_mutation_allowed",
        "stage58_tooling_network_allowed",
        "receipt_structural_pass_is_independent_review",
        "receipt_bundle_complete_is_proof_complete_authority",
        "receipt_bundle_complete_is_remote_apply_authority",
        "receipt_bundle_complete_is_launch_authority",
    ):
        if contract.get(key) is not False:
            fail(f"forbidden intake authority enabled: {key}")

    mapping = authority.get("stage56_digest_mapping")
    if not isinstance(mapping, dict) or set(mapping) != set(RECEIPT_TYPES):
        fail("Stage56 digest mapping drift")
    if len(set(mapping.values())) != len(RECEIPT_TYPES):
        fail("Stage56 digest mapping is not one-to-one")

    if set(authority.get("failure_classes", [])) != EXPECTED_FAILURE_CLASSES:
        fail("failure-class registry drift")
    gates = authority.get("gates")
    if not isinstance(gates, dict) or gates.get("stage58_intake") != "REPO_ONLY_PENDING_CI":
        fail("Stage58 gate registry drift")
    for gate in (
        "credentials_verified",
        "provider_activation",
        "provider_call",
        "controlled_proof_execution",
        "proof_complete",
        "billing_provider_credentials",
        "production_deployment",
        "incident_response",
        "controlled_launch",
        "paid_media",
        "launch",
    ):
        if not str(gates.get(gate, "")).startswith("DENIED"):
            fail(f"Stage58 preparation cannot promote gate: {gate}")


def base_receipt(receipt_type: str) -> dict[str, Any]:
    common: dict[str, Any] = {
        "schema_version": 1,
        "contract": CONTRACT,
        "receipt_type": receipt_type,
        "project_ref": PROJECT_REF,
        "scope": SCOPE,
        "provider_code": PROVIDER_CODE,
        "evidence_version": EVIDENCE_VERSION,
        "provider_environment_id": PROVIDER_ENVIRONMENT_ID,
        "result": RESULT_BY_TYPE[receipt_type],
        "source_commit_sha": "1" * 40,
        "execution_authorization_ref_digest": "2" * 64,
        "credentials_evidence_ref_digest": "3" * 64,
        "synthetic_fixture_id_digest": "4" * 64,
        "source_artifact_digest": "5" * 64,
        "collected_at_utc": "2026-08-25T01:00:00+00:00",
        "customer_data_used": False,
        "raw_secret_copied_to_receipt": False,
        "real_financial_charge_completed": False,
        "paid_subscription_created": False,
        "controlled_launch_promoted": False,
        "provider_call_performed": False,
        "provider_activation_performed": False,
        "supabase_mutation_performed": False,
        "outcome": {},
    }
    outcomes = {
        "SYNTHETIC_FIXTURE_MANIFEST": {
            "synthetic_only_attested": True,
            "cleanup_required": True,
            "fixture_manifest_digest": "6" * 64,
            "fixture_raw_identifiers_copied": False,
        },
        "PROVIDER_SELECTION_ACTIVATION": {
            "selection_before_state": "selected_pending_credentials",
            "selection_after_state": "active",
            "activation_function_definition_sha256": FUNCTION_HASHES["activate"],
            "activation_receipt_digest": "6" * 64,
            "credential_evidence_bound": True,
        },
        "WEBHOOK_AUTH": {
            "valid_auth_accepted": True,
            "invalid_auth_rejected": True,
            "missing_auth_rejected": True,
            "record_function_definition_sha256": FUNCTION_HASHES["record_webhook"],
            "raw_webhook_secret_copied": False,
        },
        "WEBHOOK_REPLAY": {
            "first_receipt_durable": True,
            "replay_idempotent": True,
            "duplicate_durable_receipt_created": False,
            "duplicate_subscription_transition_applied": False,
            "record_function_definition_sha256": FUNCTION_HASHES["record_webhook"],
            "mark_function_definition_sha256": FUNCTION_HASHES["mark_webhook"],
        },
        "CHECKOUT_END_TO_END": {
            "idempotent_replay": True,
            "conflicting_reuse_rejected": True,
            "server_amount_authority": True,
            "silent_provider_fallback": False,
            "https_checkout_url": True,
            "provider_ref_durable": True,
            "create_function_definition_sha256": FUNCTION_HASHES["create_checkout"],
            "attach_function_definition_sha256": FUNCTION_HASHES["attach_checkout"],
        },
        "SYNTHETIC_FIXTURE_CLEANUP": {
            "cleanup_complete": True,
            "fixture_scoped_residual_count": 0,
            "customer_rows_touched": False,
            "cleanup_receipt_digest": "6" * 64,
        },
    }
    common["outcome"] = outcomes[receipt_type]
    if receipt_type == "PROVIDER_SELECTION_ACTIVATION":
        common["provider_activation_performed"] = True
        common["supabase_mutation_performed"] = True
    return common


def expect_rejected(label: str, receipt: dict[str, Any]) -> None:
    try:
        validate_receipt(receipt)
    except ValueError:
        return
    fail(f"negative control accepted: {label}")


def verify_receipt_contract_negative_controls() -> None:
    for receipt_type in RECEIPT_TYPES:
        try:
            validate_receipt(base_receipt(receipt_type))
        except ValueError as exc:
            fail(f"valid in-memory contract rejected for {receipt_type}: {exc}")

    raw_secret = base_receipt("WEBHOOK_AUTH")
    raw_secret["raw_secret_copied_to_receipt"] = True
    expect_rejected("raw secret", raw_secret)

    customer = base_receipt("CHECKOUT_END_TO_END")
    customer["customer_data_used"] = True
    expect_rejected("customer data", customer)

    charge = base_receipt("CHECKOUT_END_TO_END")
    charge["real_financial_charge_completed"] = True
    expect_rejected("real financial charge", charge)

    sandbox = base_receipt("WEBHOOK_AUTH")
    sandbox["provider_environment_id"] = "asaas-sandbox"
    expect_rejected("sandbox crossover", sandbox)

    function_drift = base_receipt("WEBHOOK_REPLAY")
    function_drift["outcome"]["record_function_definition_sha256"] = "f" * 64
    expect_rejected("function authority drift", function_drift)

    duplicate_side_effect = base_receipt("WEBHOOK_REPLAY")
    duplicate_side_effect["outcome"]["duplicate_durable_receipt_created"] = True
    expect_rejected("webhook duplicate side effect", duplicate_side_effect)

    missing_cleanup = base_receipt("SYNTHETIC_FIXTURE_CLEANUP")
    missing_cleanup["outcome"]["fixture_scoped_residual_count"] = 1
    expect_rejected("nonzero cleanup residue", missing_cleanup)


def verify_tooling_is_local_only() -> None:
    combined = (CONTRACT_PATH.read_text(encoding="utf-8") + "\n" + REVIEWER_PATH.read_text(encoding="utf-8")).lower()
    for marker in (
        "execute_sql",
        "apply_migration",
        "requests.",
        "urllib.request",
        "urlopen(",
        "http.client",
        "socket.",
        "psycopg",
        "supabase.create_client",
        "subprocess.run",
        "shell=true",
    ):
        if marker in combined:
            fail(f"Stage58 intake tooling contains forbidden remote/execution surface: {marker}")
    if list(MIGRATIONS.glob("*stage58*.sql")):
        fail("Stage58 intake preparation must not create a migration")


def main() -> None:
    verify_authority()
    verify_receipt_contract_negative_controls()
    verify_tooling_is_local_only()
    print("STAGE58_BILLING_CONTROLLED_PROOF_INTAKE_PREPARATION=PASS")
    print("REQUIRED_RECEIPT_TYPES=6")
    print("LIVE_PROOF_EXECUTED=false")
    print("PROVIDER_CALL_BY_STAGE58_TOOLING=false")
    print("PROVIDER_ACTIVATION_BY_STAGE58_TOOLING=false")
    print("SUPABASE_MUTATION_BY_STAGE58_TOOLING=false")
    print("PROOF_COMPLETE_AUTHORIZED=false")
    print("CONTROLLED_LAUNCH=DENIED")


if __name__ == "__main__":
    main()
