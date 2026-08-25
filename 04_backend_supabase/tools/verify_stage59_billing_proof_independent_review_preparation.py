from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from stage59_billing_proof_independent_review_contract import (
    CONTRACT,
    DIGEST_FIELDS,
    EVIDENCE_VERSION,
    PROJECT_REF,
    PROVIDER_CODE,
    PROVIDER_ENVIRONMENT_ID,
    SCOPE,
    validate_review_receipt,
)

FAILURE_CLASS = "BGF-STAGE59-INDEPENDENT-REVIEW-PREPARATION-GUARD-576"
ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage59_billing_proof_independent_review_preparation_authority.json"
CONTRACT_PATH = BACKEND / "tools/stage59_billing_proof_independent_review_contract.py"
BUILDER_PATH = BACKEND / "tools/build_stage59_stage56_proof_promotion_authority.py"
MIGRATIONS = BACKEND / "migrations"

EXPECTED_BASELINE = "f62d5e4f2b8e3f3005b2fcd7ba87b1b5012c715d"
EXPECTED_STATE = "INDEPENDENT_REVIEW_CONTRACT_PREPARED_NO_PROOF_RECEIPTS_NO_REVIEW_RECEIPT_NO_PROMOTION_AUTHORITY_NO_REMOTE_MUTATION"
EXPECTED_SEALED = {
    "stage56_proof_promotion_contract": (
        "04_backend_supabase/tools/stage56_billing_proof_promotion_contract.py",
        "149efb9f83e3448031ed0b4940cb5f88ab0e792c",
    ),
    "stage58_intake_authority": (
        "04_backend_supabase/stage58_billing_controlled_proof_intake_preparation_authority.json",
        "0990c03db4f60f0f7252c74527d064442822c7e3",
    ),
    "stage58_receipt_contract": (
        "04_backend_supabase/tools/stage58_billing_controlled_proof_receipt_contract.py",
        "5c5f66b3bbcbb415c47e9912c1547c95d31baf06",
    ),
    "stage58_bundle_reviewer": (
        "04_backend_supabase/tools/review_stage58_billing_controlled_proof_bundle.py",
        "6a871385a074b9b1a505708cff6f45b95b8392f4",
    ),
}
EXPECTED_FAILURE_CLASSES = {
    "BGF-STAGE59-STRUCTURAL-BUNDLE-SELF-APPROVAL-563",
    "BGF-STAGE59-INDEPENDENT-REVIEW-RECEIPT-FABRICATION-564",
    "BGF-STAGE59-STAGE58-AGGREGATE-DIGEST-MISMATCH-565",
    "BGF-STAGE59-PROOF-BUNDLE-DIGEST-MISMATCH-566",
    "BGF-STAGE59-STAGE56-DIGEST-MAPPING-MISMATCH-567",
    "BGF-STAGE59-REVIEWER-INDEPENDENCE-NOT-ATTESTED-568",
    "BGF-STAGE59-SOURCE-ARTIFACTS-NOT-REVIEWED-569",
    "BGF-STAGE59-CLEANUP-NOT-INDEPENDENTLY-VERIFIED-570",
    "BGF-STAGE59-CREDENTIAL-EVIDENCE-REBIND-571",
    "BGF-STAGE59-TIMESTAMP-ORDER-VIOLATION-572",
    "BGF-STAGE59-REJECTED-REVIEW-CANDIDATE-GENERATION-573",
    "BGF-STAGE59-CANDIDATE-AS-REMOTE-AUTHORITY-574",
    "BGF-STAGE59-PROVIDER-SIDE-EFFECT-DURING-REVIEW-575",
    "BGF-STAGE59-INDEPENDENT-REVIEW-PREPARATION-GUARD-576",
}


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE59_BILLING_PROOF_INDEPENDENT_REVIEW_PREPARATION=FAIL\n"
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
        "stage": "STAGE59_BILLING_PROOF_INDEPENDENT_REVIEW_PREPARATION",
        "baseline_main_sha": EXPECTED_BASELINE,
        "current_state": EXPECTED_STATE,
    }
    for key, expected in expected_top.items():
        if authority.get(key) != expected:
            fail(f"authority drift: {key}")

    remote = authority.get("fresh_remote_read_only_snapshot")
    expected_remote = {
        "observed_at_utc": "2026-08-25T01:52:27.619775+00:00",
        "selection_state": "selected_pending_credentials",
        "selection_activated_at": None,
        "evidence_version": EVIDENCE_VERSION,
        "billing_external_evidence_total": 0,
        "credentials_verified_rows": 0,
        "proof_complete_rows": 0,
        "checkout_intents": 0,
        "webhook_receipts": 0,
        "evidence_migration_ready_rows": 0,
        "remote_mutation_performed": False,
    }
    if not isinstance(remote, dict):
        fail("fresh remote snapshot missing")
    for key, expected in expected_remote.items():
        if remote.get(key) != expected:
            fail(f"fresh remote snapshot drift: {key}")

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

    contract = authority.get("review_contract")
    if not isinstance(contract, dict) or contract.get("contract_id") != CONTRACT:
        fail("review contract missing or drifted")
    exact = {
        "eligible_scope": SCOPE,
        "eligible_provider_code": PROVIDER_CODE,
        "eligible_evidence_version": EVIDENCE_VERSION,
        "eligible_provider_environment_id": PROVIDER_ENVIRONMENT_ID,
        "required_stage58_overall_state": "STRUCTURALLY_COMPLETE_AWAITING_INDEPENDENT_REVIEW",
        "required_stage58_receipt_count": 6,
    }
    for key, expected in exact.items():
        if contract.get(key) != expected:
            fail(f"review contract drift: {key}")
    for key in (
        "stage58_aggregate_sha256_required",
        "stage58_proof_bundle_digest_required",
        "all_six_stage56_digest_mapping_fields_required",
        "reviewed_source_artifact_set_digest_required",
        "reviewer_reference_digest_required",
        "reviewer_independence_attestation_required",
        "source_artifacts_reviewed_out_of_band_attestation_required",
        "synthetic_non_customer_fixture_attestation_required",
        "cleanup_zero_residue_attestation_required",
        "stage54_credentials_evidence_fields_required",
        "provider_selection_activation_timestamp_required",
        "proof_completion_timestamp_required",
        "approval_decision_required_for_stage56_candidate",
        "rejection_decision_must_block_stage56_candidate",
        "approved_review_can_only_create_reviewed_candidate_no_migration",
    ):
        if contract.get(key) is not True:
            fail(f"fail-closed review contract drift: {key}")
    for key in (
        "structural_validator_can_verify_reviewer_independence",
        "structural_validator_can_verify_source_artifact_truth",
        "stage58_structural_bundle_can_self_approve",
        "stage59_tooling_can_create_review_receipt",
        "stage59_tooling_can_invent_missing_evidence",
        "stage59_tooling_can_call_provider",
        "stage59_tooling_can_activate_provider",
        "stage59_tooling_can_mutate_supabase",
        "stage59_tooling_can_create_stage56_migration",
        "stage59_tooling_can_apply_stage56_migration",
        "reviewed_candidate_is_remote_apply_authority",
        "reviewed_candidate_is_proof_complete_authority",
        "reviewed_candidate_is_launch_authority",
    ):
        if contract.get(key) is not False:
            fail(f"forbidden Stage59 authority enabled: {key}")

    output = authority.get("stage56_candidate_output_contract")
    if not isinstance(output, dict):
        fail("Stage56 candidate output contract missing")
    expected_output = {
        "promotion_state": "REVIEWED_CANDIDATE_NO_MIGRATION",
        "migration_filename": None,
        "remote_apply_performed": False,
        "provider_call_performed_by_tooling": False,
        "provider_activation_performed_by_tooling": False,
        "controlled_launch_promoted": False,
        "paid_media_promoted": False,
        "launch_promoted": False,
        "independent_review_receipt_sha256_is_actual_review_file_sha256": True,
        "proof_bundle_digest_must_equal_stage58_aggregate": True,
        "six_stage56_receipt_digests_must_equal_stage58_aggregate": True,
    }
    if output != expected_output:
        fail("Stage56 candidate output contract drift")

    if authority.get("current_registry") != {
        "complete_stage58_bundles_supplied": 0,
        "independent_review_receipts_supplied": 0,
        "stage56_reviewed_candidates_generated": 0,
        "proof_complete_rows_remote": 0,
    }:
        fail("Stage59 zero-evidence registry drift")
    if set(authority.get("failure_classes", [])) != EXPECTED_FAILURE_CLASSES:
        fail("Stage59 failure-class registry drift")
    gates = authority.get("gates")
    if not isinstance(gates, dict) or gates.get("stage59_review_contract") != "REPO_ONLY_PENDING_CI":
        fail("Stage59 gate registry drift")
    for gate in (
        "independent_review",
        "stage56_reviewed_candidate",
        "proof_complete",
        "billing_provider_credentials",
        "provider_activation",
        "provider_call",
        "production_deployment",
        "incident_response",
        "controlled_launch",
        "paid_media",
        "launch",
    ):
        if not str(gates.get(gate, "")).startswith("DENIED"):
            fail(f"Stage59 preparation cannot promote gate: {gate}")


def base_review_receipt() -> dict[str, Any]:
    mapping = {
        "provider_activation_receipt_sha256": "1" * 64,
        "webhook_auth_test_receipt_digest": "2" * 64,
        "webhook_replay_receipt_digest": "3" * 64,
        "checkout_end_to_end_receipt_digest": "4" * 64,
        "synthetic_fixture_manifest_sha256": "5" * 64,
        "synthetic_fixture_cleanup_receipt_sha256": "6" * 64,
    }
    return {
        "schema_version": 1,
        "contract": CONTRACT,
        "project_ref": PROJECT_REF,
        "scope": SCOPE,
        "provider_code": PROVIDER_CODE,
        "evidence_version": EVIDENCE_VERSION,
        "provider_environment_id": PROVIDER_ENVIRONMENT_ID,
        "decision": "APPROVED_FOR_STAGE56_PROOF_PROMOTION_DRAFT",
        "stage58_aggregate_sha256": "7" * 64,
        "proof_bundle_digest": "8" * 64,
        "stage56_candidate_digest_mapping": mapping,
        "reviewed_source_artifact_set_digest": "9" * 64,
        "reviewer_reference_digest": "a" * 64,
        "review_notes_digest": "b" * 64,
        "reviewer_independence_attested": True,
        "source_artifacts_reviewed_out_of_band_attested": True,
        "synthetic_non_customer_fixture_attested": True,
        "cleanup_zero_residue_attested": True,
        "customer_data_used": False,
        "raw_secret_copied_to_review_receipt": False,
        "provider_call_performed_by_review_tooling": False,
        "provider_activation_performed_by_review_tooling": False,
        "supabase_mutation_performed_by_review_tooling": False,
        "provider_account_owner_authorization_digest": "c" * 64,
        "credential_activation_digest": "d" * 64,
        "credentials_verified_at_utc": "2026-08-25T01:00:00+00:00",
        "provider_selection_activated_at_utc": "2026-08-25T01:05:00+00:00",
        "proof_completed_at_utc": "2026-08-25T01:20:00+00:00",
        "independent_review_completed_at_utc": "2026-08-25T01:30:00+00:00",
    }


def expect_rejected(label: str, receipt: dict[str, Any], *, require_approved: bool = True) -> None:
    try:
        validate_review_receipt(receipt, require_approved=require_approved)
    except ValueError:
        return
    fail(f"negative control accepted: {label}")


def verify_review_contract_negative_controls() -> None:
    base = base_review_receipt()
    try:
        validate_review_receipt(base, require_approved=True)
    except ValueError as exc:
        fail(f"valid in-memory review contract rejected: {exc}")

    rejected = copy.deepcopy(base)
    rejected["decision"] = "REJECTED"
    expect_rejected("rejected review candidate generation", rejected, require_approved=True)
    try:
        validate_review_receipt(rejected, require_approved=False)
    except ValueError as exc:
        fail(f"structurally valid rejected review receipt rejected: {exc}")

    independence = copy.deepcopy(base)
    independence["reviewer_independence_attested"] = False
    expect_rejected("reviewer independence missing", independence)

    source_review = copy.deepcopy(base)
    source_review["source_artifacts_reviewed_out_of_band_attested"] = False
    expect_rejected("source artifacts not reviewed", source_review)

    cleanup = copy.deepcopy(base)
    cleanup["cleanup_zero_residue_attested"] = False
    expect_rejected("cleanup not independently verified", cleanup)

    customer = copy.deepcopy(base)
    customer["customer_data_used"] = True
    expect_rejected("customer data used", customer)

    side_effect = copy.deepcopy(base)
    side_effect["provider_call_performed_by_review_tooling"] = True
    expect_rejected("review tooling provider side effect", side_effect)

    order = copy.deepcopy(base)
    order["proof_completed_at_utc"] = "2026-08-25T01:01:00+00:00"
    expect_rejected("proof before activation", order)

    collision = copy.deepcopy(base)
    collision["stage56_candidate_digest_mapping"]["webhook_replay_receipt_digest"] = collision["stage56_candidate_digest_mapping"]["webhook_auth_test_receipt_digest"]
    expect_rejected("receipt digest collision", collision)


def verify_builder_is_local_only_and_fail_closed() -> None:
    source = BUILDER_PATH.read_text(encoding="utf-8")
    required_markers = (
        "STRUCTURALLY_COMPLETE_AWAITING_INDEPENDENT_REVIEW",
        "validate_review_receipt(review, require_approved=True)",
        'review["stage58_aggregate_sha256"] != aggregate_sha',
        'review["proof_bundle_digest"] != aggregate["proof_bundle_digest"]',
        'review["stage56_candidate_digest_mapping"] != aggregate["stage56_candidate_digest_mapping"]',
        "validate_stage56_authority(candidate, require_migration=False)",
        '"promotion_state": "REVIEWED_CANDIDATE_NO_MIGRATION"',
        '"migration_filename": None',
        '"remote_apply_performed": False',
        '"provider_call_performed_by_tooling": False',
        '"provider_activation_performed_by_tooling": False',
    )
    for marker in required_markers:
        if marker not in source:
            fail(f"Stage59 builder safety marker missing: {marker}")

    combined = (CONTRACT_PATH.read_text(encoding="utf-8") + "\n" + source).lower()
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
            fail(f"Stage59 tooling contains forbidden remote/execution surface: {marker}")
    if list(MIGRATIONS.glob("*stage59*.sql")):
        fail("Stage59 independent-review preparation must not create a migration")


def main() -> None:
    verify_authority()
    verify_review_contract_negative_controls()
    verify_builder_is_local_only_and_fail_closed()
    print("STAGE59_BILLING_PROOF_INDEPENDENT_REVIEW_PREPARATION=PASS")
    print("REAL_STAGE58_COMPLETE_BUNDLE_SUPPLIED=false")
    print("REAL_INDEPENDENT_REVIEW_RECEIPT_SUPPLIED=false")
    print("STAGE56_REVIEWED_CANDIDATE_GENERATED=false")
    print("PROVIDER_CALL_BY_STAGE59_TOOLING=false")
    print("SUPABASE_MUTATION_BY_STAGE59_TOOLING=false")
    print("PROOF_COMPLETE=DENIED")
    print("CONTROLLED_LAUNCH=DENIED")


if __name__ == "__main__":
    main()
