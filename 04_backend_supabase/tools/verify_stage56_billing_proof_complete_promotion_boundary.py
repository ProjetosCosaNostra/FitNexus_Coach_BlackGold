from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from stage56_billing_proof_promotion_contract import (
    EVIDENCE_VERSION,
    PROJECT_REF,
    PROVIDER_CODE,
    PROVIDER_ENVIRONMENT_ID,
    PROTOCOL,
    SCOPE,
    SOURCE_STATE,
    TARGET_STATE,
    load_authority,
    normalize_executable_sql,
    render_executable_sql,
    validate_authority,
)

FAILURE_CLASS = "BGF-STAGE56-PROOF-COMPLETE-PROMOTION-BOUNDARY-GUARD-543"
ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage56_billing_proof_complete_promotion_boundary_authority.json"
MIGRATIONS = BACKEND / "migrations"
PROMOTIONS = BACKEND / "billing_proof_promotions"
CONTRACT = BACKEND / "tools/stage56_billing_proof_promotion_contract.py"
BUILDER = BACKEND / "tools/build_stage56_billing_proof_complete_candidate.py"

EXPECTED_BASELINE = "34465012863a54ecfb561a3fb28c9643eb349a15"
EXPECTED_STATE = "PROOF_COMPLETE_PROMOTION_BOUNDARY_PREPARED_NO_PROVIDER_CALL_NO_PROVIDER_ACTIVATION_NO_REMOTE_MUTATION"
EXPECTED_SEALED = {
    "stage38_billing_evidence_bound_activation": (
        "04_backend_supabase/migrations/20260823174500_stage38_billing_evidence_bound_activation.sql",
        "a09aa83eb6eb24739ad0a73b7c08db3185eb4f63",
    ),
    "stage40_production_environment_interlock": (
        "04_backend_supabase/migrations/20260824003000_stage40_billing_production_environment_interlock.sql",
        "9900408bec1b7d60f40c39f4e97e5e8c0c1c96cf",
    ),
    "billing_provider_contract_guard": (
        "04_backend_supabase/tools/verify_billing_provider_contract.py",
        "aafc61f9844476f35a86487e736db87e826068a2",
    ),
    "stage54_promotion_boundary": (
        "04_backend_supabase/stage54_billing_external_evidence_promotion_boundary_authority.json",
        "05c99cdc785bcd8872b51773078a8c97b56675af",
    ),
    "stage55_stage54_final_reconciliation": (
        "04_backend_supabase/stage55_stage54_final_reconciliation_authority.json",
        "f76d81fe709a6f643dcb534115b109265106cffe",
    ),
}
EXPECTED_FAILURE_CLASSES = {
    "BGF-STAGE56-UNREGISTERED-PROOF-COMPLETE-MIGRATION-527",
    "BGF-STAGE56-PROOF-COMPLETE-WITHOUT-CREDENTIALS-VERIFIED-528",
    "BGF-STAGE56-PROOF-COMPLETE-WITHOUT-ACTIVE-SELECTION-529",
    "BGF-STAGE56-BASE-CREDENTIAL-AUTHORITY-REBIND-530",
    "BGF-STAGE56-PRODUCTION-ENVIRONMENT-REBIND-531",
    "BGF-STAGE56-WEBHOOK-AUTH-PROOF-UNBOUND-532",
    "BGF-STAGE56-WEBHOOK-REPLAY-PROOF-UNBOUND-533",
    "BGF-STAGE56-CHECKOUT-E2E-PROOF-UNBOUND-534",
    "BGF-STAGE56-SYNTHETIC-FIXTURE-CLEANUP-UNBOUND-535",
    "BGF-STAGE56-INDEPENDENT-REVIEW-UNBOUND-536",
    "BGF-STAGE56-PROOF-DIGEST-COLLISION-537",
    "BGF-STAGE56-PROVIDER-ACTIVATION-BUNDLED-IN-MIGRATION-538",
    "BGF-STAGE56-PROVIDER-CALL-BUNDLED-IN-MIGRATION-539",
    "BGF-STAGE56-STAGE54-SEALED-GUARD-MUTATION-540",
    "BGF-STAGE56-PROOF-COMPLETE-BODY-DRIFT-541",
    "BGF-STAGE56-EXECUTE-SQL-PROOF-DML-542",
    "BGF-STAGE56-PROOF-COMPLETE-PROMOTION-BOUNDARY-GUARD-543",
}


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE56_BILLING_PROOF_COMPLETE_PROMOTION_BOUNDARY=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\nDETAIL={detail}"
    )


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"JSON unreadable: {path.name}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"JSON must be object: {path.name}")
    return value


def verify_authority() -> None:
    authority = read_json(AUTHORITY)
    expected = {
        "schema_version": 1,
        "project_ref": PROJECT_REF,
        "stage": "STAGE56_BILLING_PROOF_COMPLETE_PROMOTION_BOUNDARY",
        "baseline_main_sha": EXPECTED_BASELINE,
        "current_state": EXPECTED_STATE,
    }
    for key, value in expected.items():
        if authority.get(key) != value:
            fail(f"authority drift: {key}")

    remote = authority.get("fresh_remote_read_only_receipt")
    expected_remote = {
        "source": "Supabase.execute_sql_read_only",
        "observed_at_utc": "2026-08-25T01:30:20.699771+00:00",
        "scope": SCOPE,
        "provider_code": PROVIDER_CODE,
        "selection_state": "selected_pending_credentials",
        "selection_evidence_version": EVIDENCE_VERSION,
        "selection_activated_at": None,
        "billing_external_evidence_total": 0,
        "credentials_verified_rows": 0,
        "proof_complete_rows": 0,
        "checkout_intents": 0,
        "webhook_receipts": 0,
        "runtime_write_grants": 0,
        "checkout_runtime_write_grants": 0,
        "webhook_runtime_write_grants": 0,
        "provider_code_index_present": True,
        "activation_function_requires_proof_complete_or_credentials_verified": True,
        "readiness_function_requires_proof_complete": True,
        "readiness_function_requires_asaas_production": True,
        "remote_mutation_performed": False,
    }
    if not isinstance(remote, dict):
        fail("fresh remote read-only receipt missing")
    for key, value in expected_remote.items():
        if remote.get(key) != value:
            fail(f"fresh remote read-only receipt drift: {key}")

    sealed = authority.get("sealed_inputs")
    if not isinstance(sealed, dict) or set(sealed) != set(EXPECTED_SEALED):
        fail("sealed input registry drift")
    for label, (path_rel, blob) in EXPECTED_SEALED.items():
        entry = sealed[label]
        path = ROOT / path_rel
        if entry.get("path") != path_rel or entry.get("git_blob_sha") != blob:
            fail(f"sealed input declaration drift: {label}")
        if not path.is_file() or git_blob_sha(path) != blob:
            fail(f"sealed input bytes drift: {label}")

    problem = authority.get("problem_statement")
    if not isinstance(problem, dict):
        fail("problem statement missing")
    for key in (
        "stage38_requires_three_live_proof_digests_for_launch_readiness",
        "stage54_intentionally_forbids_proof_complete_updates",
    ):
        if problem.get(key) is not True:
            fail(f"problem statement drift: {key}")
    for key in (
        "proof_complete_can_be_inferred_from_provider_activation_alone",
        "proof_complete_can_be_inferred_from_checkout_row_presence_alone",
        "proof_complete_can_be_inferred_from_webhook_row_presence_alone",
    ):
        if problem.get(key) is not False:
            fail(f"proof inference must remain denied: {key}")

    protocol = authority.get("promotion_protocol")
    if not isinstance(protocol, dict):
        fail("promotion protocol missing")
    exact_protocol = {
        "protocol_id": PROTOCOL,
        "eligible_scope": SCOPE,
        "eligible_provider_code": PROVIDER_CODE,
        "eligible_evidence_version": EVIDENCE_VERSION,
        "eligible_source_state": SOURCE_STATE,
        "eligible_target_state": TARGET_STATE,
        "required_provider_environment_id": PROVIDER_ENVIRONMENT_ID,
        "companion_authority_directory": "04_backend_supabase/billing_proof_promotions",
    }
    for key, value in exact_protocol.items():
        if protocol.get(key) != value:
            fail(f"promotion protocol drift: {key}")

    required_true = {
        "existing_credentials_verified_row_required",
        "selection_active_and_activated_required_before_proof_complete_migration",
        "provider_account_owner_authorization_digest_must_be_preserved_exactly",
        "credential_activation_digest_must_be_preserved_exactly",
        "credentials_verified_at_must_be_preserved_exactly",
        "provider_environment_id_must_be_preserved_exactly",
        "webhook_auth_test_receipt_digest_required",
        "webhook_replay_receipt_digest_required",
        "checkout_end_to_end_receipt_digest_required",
        "provider_activation_receipt_sha256_required",
        "synthetic_fixture_manifest_sha256_required",
        "synthetic_fixture_cleanup_receipt_sha256_required",
        "independent_review_receipt_sha256_required",
        "proof_bundle_digest_required",
        "reviewer_reference_digest_required",
        "reviewer_independence_attested_required",
        "source_artifacts_reviewed_out_of_band_attested_required",
        "synthetic_non_customer_fixture_attested_required",
        "proof_provider_call_may_occur_only_in_future_controlled_proof_stage",
        "migration_update_must_affect_exactly_one_row",
        "remote_apply_requires_fresh_preapply_read_only_verification",
        "remote_apply_requires_separate_exact_migration_apply",
        "remote_apply_requires_postapply_read_only_reconciliation",
        "stage54_historical_guard_must_not_be_mutated_to_admit_stage56",
        "future_stage56_migration_promotion_requires_historical_projection_or_compatibility_wrapper",
    }
    for key in required_true:
        if protocol.get(key) is not True:
            fail(f"fail-closed proof protocol drift: {key}")

    required_false = {
        "customer_data_used_allowed",
        "raw_secret_copied_to_receipts_allowed",
        "real_financial_charge_required",
        "paid_subscription_creation_required",
        "proof_provider_call_allowed_in_stage56_tooling",
        "provider_activation_allowed_in_stage56_tooling",
        "migration_may_insert_new_billing_evidence_row",
        "migration_may_change_scope_provider_or_evidence_version",
        "migration_may_change_base_credential_digests",
        "migration_may_change_provider_environment",
        "migration_may_change_credentials_verified_at",
        "migration_may_delete_billing_evidence",
        "migration_may_activate_provider",
        "migration_may_call_provider",
        "versioned_migration_presence_is_remote_apply_authority",
        "candidate_generation_is_remote_apply_authority",
        "execute_sql_dml_or_ddl_allowed",
    }
    for key in required_false:
        if protocol.get(key) is not False:
            fail(f"forbidden proof protocol surface enabled: {key}")

    if authority.get("current_registry") != {
        "registered_proof_complete_promotions": 0,
        "versioned_proof_complete_promotion_migrations": 0,
        "remote_proof_complete_rows": 0,
    }:
        fail("current proof registry drift")
    if set(authority.get("failure_classes", [])) != EXPECTED_FAILURE_CLASSES:
        fail("failure-class registry drift")
    gates = authority.get("gates")
    if not isinstance(gates, dict) or gates.get("stage56_boundary") != "REPO_ONLY_PENDING_CI":
        fail("Stage56 gate registry drift")
    for key in (
        "credentials_verified",
        "provider_activation",
        "proof_complete",
        "billing_provider_credentials",
        "production_deployment",
        "incident_response",
        "controlled_launch",
        "paid_media",
        "launch",
    ):
        if not str(gates.get(key, "")).startswith("DENIED"):
            fail(f"Stage56 preparation cannot promote gate: {key}")


def proof_write_migrations() -> tuple[list[Path], list[Path]]:
    proof_updates: list[Path] = []
    forbidden: list[Path] = []
    for path in sorted(MIGRATIONS.glob("*.sql")):
        text = normalize_executable_sql(path.read_text(encoding="utf-8")).lower()
        if "update private.billing_provider_external_evidence" in text:
            if "state = 'proof_complete'" in text:
                proof_updates.append(path)
            else:
                forbidden.append(path)
        if "insert into private.billing_provider_external_evidence" in text and "'proof_complete'" in text:
            forbidden.append(path)
        if "delete from private.billing_provider_external_evidence" in text or "truncate private.billing_provider_external_evidence" in text:
            forbidden.append(path)
    return proof_updates, sorted(set(forbidden))


def verify_registered_promotions() -> int:
    proof_updates, forbidden = proof_write_migrations()
    if forbidden:
        fail("forbidden billing proof write migration present: " + ",".join(path.name for path in forbidden))
    registered = 0
    for migration in proof_updates:
        companion = PROMOTIONS / f"{migration.stem}.json"
        if not companion.is_file():
            fail(f"unregistered proof_complete migration: {migration.name}")
        manifest = load_authority(companion)
        try:
            validate_authority(manifest, require_migration=True)
        except ValueError as exc:
            fail(f"invalid proof promotion authority {companion.name}: {exc}")
        if manifest.get("migration_filename") != migration.name:
            fail(f"proof promotion filename mismatch: {migration.name}")
        actual = normalize_executable_sql(migration.read_text(encoding="utf-8"))
        expected = normalize_executable_sql(render_executable_sql(manifest))
        if actual != expected:
            fail(f"registered proof_complete body drift: {migration.name}")
        registered += 1
    return registered


def base_fixture() -> dict[str, Any]:
    values = {
        "schema_version": 1,
        "protocol": PROTOCOL,
        "project_ref": PROJECT_REF,
        "scope": SCOPE,
        "provider_code": PROVIDER_CODE,
        "evidence_version": EVIDENCE_VERSION,
        "source_state": SOURCE_STATE,
        "target_state": TARGET_STATE,
        "provider_environment_id": PROVIDER_ENVIRONMENT_ID,
        "promotion_state": "REVIEWED_CANDIDATE_NO_MIGRATION",
        "independent_review_decision": "APPROVED_FOR_PROOF_COMPLETE_MIGRATION_DRAFT",
        "provider_account_owner_authorization_digest": "1" * 64,
        "credential_activation_digest": "2" * 64,
        "credentials_verified_at_utc": "2026-08-25T01:00:00+00:00",
        "provider_selection_activated_at_utc": "2026-08-25T01:05:00+00:00",
        "provider_activation_receipt_sha256": "3" * 64,
        "webhook_auth_test_receipt_digest": "4" * 64,
        "webhook_replay_receipt_digest": "5" * 64,
        "checkout_end_to_end_receipt_digest": "6" * 64,
        "synthetic_fixture_manifest_sha256": "7" * 64,
        "synthetic_fixture_cleanup_receipt_sha256": "8" * 64,
        "independent_review_receipt_sha256": "9" * 64,
        "proof_bundle_digest": "a" * 64,
        "reviewer_reference_digest": "b" * 64,
        "reviewer_independence_attested": True,
        "source_artifacts_reviewed_out_of_band_attested": True,
        "synthetic_non_customer_fixture_attested": True,
        "customer_data_used": False,
        "raw_secret_copied_to_receipts": False,
        "real_financial_charge_completed": False,
        "paid_subscription_created": False,
        "provider_call_performed_by_tooling": False,
        "provider_activation_performed_by_tooling": False,
        "remote_apply_performed": False,
        "controlled_launch_promoted": False,
        "paid_media_promoted": False,
        "launch_promoted": False,
        "proof_completed_at_utc": "2026-08-25T01:20:00+00:00",
        "independent_review_completed_at_utc": "2026-08-25T01:25:00+00:00",
        "migration_filename": None,
    }
    return values


def reject(label: str, fixture: dict[str, Any]) -> None:
    try:
        validate_authority(fixture, require_migration=False)
    except ValueError:
        return
    fail(f"negative control accepted: {label}")


def verify_negative_controls() -> None:
    base = base_fixture()
    try:
        validate_authority(base, require_migration=False)
    except ValueError as exc:
        fail(f"valid in-memory proof authority unexpectedly rejected: {exc}")

    sandbox = dict(base)
    sandbox["provider_environment_id"] = "asaas-sandbox"
    reject("sandbox proof", sandbox)

    wrong_source = dict(base)
    wrong_source["source_state"] = "proof_complete"
    reject("missing credentials_verified source state", wrong_source)

    customer = dict(base)
    customer["customer_data_used"] = True
    reject("customer data proof", customer)

    secret = dict(base)
    secret["raw_secret_copied_to_receipts"] = True
    reject("raw secret proof", secret)

    paid = dict(base)
    paid["real_financial_charge_completed"] = True
    reject("financial charge proof", paid)

    collision = dict(base)
    collision["webhook_replay_receipt_digest"] = collision["webhook_auth_test_receipt_digest"]
    reject("proof digest collision", collision)

    pre_activation = dict(base)
    pre_activation["proof_completed_at_utc"] = "2026-08-25T01:01:00+00:00"
    reject("proof before provider activation", pre_activation)

    no_cleanup = dict(base)
    no_cleanup["synthetic_fixture_cleanup_receipt_sha256"] = ""
    reject("missing cleanup receipt", no_cleanup)

    rendered = normalize_executable_sql(render_executable_sql(base)).lower()
    required = (
        "update private.billing_provider_external_evidence e",
        "state = 'proof_complete'",
        "e.state = 'credentials_verified'",
        "e.provider_environment_id = 'asaas-production'",
        "e.webhook_auth_test_receipt_digest is null",
        "e.webhook_replay_receipt_digest is null",
        "e.checkout_end_to_end_receipt_digest is null",
        "e.proof_completed_at is null",
        "s.state = 'active'",
        "s.activated_at =",
        "get diagnostics v_updated = row_count",
        "if v_updated <> 1 then",
        "stage56_proof_complete_promotion_precondition_failed",
    )
    for marker in required:
        if marker not in rendered:
            fail(f"rendered proof SQL lost fail-closed marker: {marker}")
    forbidden = (
        "insert into private.billing_provider_external_evidence",
        "delete from private.billing_provider_external_evidence",
        "activate_billing_provider_selection(",
        "update public.billing_provider_selections",
    )
    for marker in forbidden:
        if marker in rendered:
            fail(f"rendered proof SQL contains forbidden bundled action: {marker}")


def verify_local_only_tooling() -> None:
    combined = (CONTRACT.read_text(encoding="utf-8") + "\n" + BUILDER.read_text(encoding="utf-8")).lower()
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
            fail(f"Stage56 local tooling contains forbidden remote/execution surface: {marker}")
    if list(MIGRATIONS.glob("*stage56*.sql")):
        fail("Stage56 boundary preparation must not create a Stage56 migration")


def main() -> None:
    verify_authority()
    registered = verify_registered_promotions()
    verify_negative_controls()
    verify_local_only_tooling()
    print("STAGE56_BILLING_PROOF_COMPLETE_PROMOTION_BOUNDARY=PASS")
    print(f"REGISTERED_PROOF_COMPLETE_PROMOTIONS={registered}")
    print("REMOTE_PROOF_COMPLETE_ROWS=0")
    print("PROVIDER_CALL_BY_TOOLING=false")
    print("PROVIDER_ACTIVATION_BY_TOOLING=false")
    print("REMOTE_MUTATION=false")
    print("CONTROLLED_LAUNCH=DENIED")


if __name__ == "__main__":
    main()
