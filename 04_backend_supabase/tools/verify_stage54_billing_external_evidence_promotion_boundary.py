from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from stage54_billing_evidence_promotion_contract import (
    EVIDENCE_STATE,
    EVIDENCE_VERSION,
    PROVIDER_CODE,
    PROVIDER_ENVIRONMENT_ID,
    PROTOCOL,
    SCOPE,
    SOURCE_STAGE,
    load_authority,
    normalize_executable_sql,
    render_executable_sql,
    validate_authority,
)

FAILURE_CLASS = "BGF-STAGE54-BILLING-EVIDENCE-PROMOTION-BOUNDARY-GUARD-519"
ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage54_billing_external_evidence_promotion_boundary_authority.json"
MIGRATIONS = BACKEND / "migrations"
PROMOTIONS = BACKEND / "billing_evidence_promotions"
CONTRACT = BACKEND / "tools/stage54_billing_evidence_promotion_contract.py"
BUILDER = BACKEND / "tools/build_stage54_billing_external_evidence_credentials_candidate.py"

EXPECTED_BASELINE = "1a1bc55b74c0fdb3806c111aafa236eea9cb5d75"
EXPECTED_STATE = "CREDENTIAL_EVIDENCE_PROMOTION_BOUNDARY_PREPARED_NO_EXTERNAL_REVIEW_NO_EVIDENCE_INSERT_NO_PROVIDER_ACTIVATION_NO_REMOTE_MUTATION"
EXPECTED_FAILURE_CLASSES = {
    "BGF-STAGE54-UNREGISTERED-BILLING-EVIDENCE-MIGRATION-508",
    "BGF-STAGE54-PROOF-COMPLETE-WITHOUT-DEDICATED-PROTOCOL-509",
    "BGF-STAGE54-SOURCE-RECEIPT-DIGEST-UNBOUND-510",
    "BGF-STAGE54-INDEPENDENT-REVIEW-DIGEST-UNBOUND-511",
    "BGF-STAGE54-PRODUCTION-ENVIRONMENT-MISMATCH-512",
    "BGF-STAGE54-SECRET-MATERIAL-IN-PROMOTION-AUTHORITY-513",
    "BGF-STAGE54-ACTIVATION-BUNDLED-WITH-EVIDENCE-MIGRATION-514",
    "BGF-STAGE54-STAGE47-AGGREGATE-SUBSTITUTION-515",
    "BGF-STAGE54-SYNTHETIC-REVIEW-FALSE-AUTHORITY-516",
    "BGF-STAGE54-CANDIDATE-DIRECT-APPLY-517",
    "BGF-STAGE54-EXECUTE-SQL-EVIDENCE-DML-518",
    "BGF-STAGE54-BILLING-EVIDENCE-PROMOTION-BOUNDARY-GUARD-519",
    "BGF-STAGE54-REGISTERED-PROMOTION-BODY-DRIFT-520",
}


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE54_BILLING_EXTERNAL_EVIDENCE_PROMOTION_BOUNDARY=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\nDETAIL={detail}"
    )


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"JSON unreadable: {path.name}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"JSON must be object: {path.name}")
    return value


def verify_authority() -> dict[str, Any]:
    authority = load_json(AUTHORITY)
    expected_top = {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE54_BILLING_EXTERNAL_EVIDENCE_PROMOTION_BOUNDARY",
        "baseline_main_sha": EXPECTED_BASELINE,
        "current_state": EXPECTED_STATE,
    }
    for key, expected in expected_top.items():
        if authority.get(key) != expected:
            fail(f"Stage54 authority drift: {key}")

    problem = authority.get("problem_statement")
    if not isinstance(problem, dict):
        fail("problem_statement missing")
    if problem.get("stage47_structural_aggregate_is_external_billing_authority") is not False:
        fail("Stage47 structural aggregate cannot become billing external authority")
    if problem.get("stage49_evidence_migration_protocol_applies_to_billing_provider_credentials") is not False:
        fail("Stage49 protocol cannot silently subsume billing external authorization")
    if problem.get("proof_complete_has_dedicated_external_proof_protocol_today") is not False:
        fail("Stage54 must not pretend proof_complete protocol exists")

    remote = authority.get("fresh_remote_read_only_receipt")
    expected_remote = {
        "source": "Supabase.execute_sql_read_only",
        "observed_at_utc": "2026-08-25T00:18:33.060924+00:00",
        "billing_evidence_rows": 0,
        "credentials_verified_rows": 0,
        "proof_complete_rows": 0,
        "selection_scope": SCOPE,
        "selection_provider_code": PROVIDER_CODE,
        "selection_state": "selected_pending_credentials",
        "selection_evidence_version": EVIDENCE_VERSION,
        "selection_activated_at": None,
        "runtime_write_grants": 0,
        "provider_code_index_present": True,
        "remote_mutation_performed": False,
    }
    if not isinstance(remote, dict):
        fail("fresh remote receipt missing")
    for key, expected in expected_remote.items():
        if remote.get(key) != expected:
            fail(f"fresh remote receipt drift: {key}")

    sealed = authority.get("sealed_inputs")
    if not isinstance(sealed, dict) or len(sealed) != 7:
        fail("sealed input set drift")
    for label, item in sealed.items():
        if not isinstance(item, dict):
            fail(f"sealed input malformed: {label}")
        path = ROOT / str(item.get("path", ""))
        expected_blob = str(item.get("git_blob_sha", ""))
        if not path.is_file():
            fail(f"sealed input missing: {label}")
        if git_blob_sha(path) != expected_blob:
            fail(f"sealed input blob drift: {label}")

    protocol = authority.get("promotion_protocol")
    if not isinstance(protocol, dict):
        fail("promotion protocol missing")
    expected_protocol_values = {
        "protocol_id": PROTOCOL,
        "eligible_scope": SCOPE,
        "eligible_provider_code": PROVIDER_CODE,
        "eligible_evidence_version": EVIDENCE_VERSION,
        "eligible_state": EVIDENCE_STATE,
        "required_provider_environment_id": PROVIDER_ENVIRONMENT_ID,
        "canonical_source_receipt_stage": SOURCE_STAGE,
        "companion_authority_directory": "04_backend_supabase/billing_evidence_promotions",
    }
    for key, expected in expected_protocol_values.items():
        if protocol.get(key) != expected:
            fail(f"promotion protocol drift: {key}")

    required_true = {
        "companion_authority_required_for_future_credentials_verified_migration",
        "canonical_source_receipt_sha256_required",
        "independent_review_receipt_sha256_required",
        "source_artifact_review_digest_required",
        "review_bundle_digest_required",
        "reviewer_reference_digest_required",
        "reviewer_independence_attestation_required",
        "source_artifacts_reviewed_out_of_band_attestation_required",
        "operator_redaction_confirmation_required",
        "provider_account_owner_authorization_digest_required",
        "credential_activation_digest_required",
        "production_environment_exact_match_required",
        "selected_evidence_version_exact_match_required",
        "migration_precondition_requires_pending_unactivated_selection",
        "one_credentials_verified_row_per_migration",
        "remote_apply_requires_separate_preapply_authority_reread",
        "provider_activation_requires_separate_postapply_remote_evidence_read",
    }
    for key in required_true:
        if protocol.get(key) is not True:
            fail(f"Stage54 fail-closed protocol drift: {key}")

    required_false = {
        "script_can_verify_reviewer_independence",
        "synthetic_fixture_can_satisfy_promotion",
        "stage47_aggregate_can_satisfy_promotion",
        "stage48_regression_can_satisfy_promotion",
        "stage49_protocol_can_substitute_for_billing_authorization",
        "candidate_generation_is_remote_apply_authority",
        "versioned_migration_presence_is_remote_apply_authority",
        "provider_activation_may_be_bundled_with_evidence_migration",
        "provider_call_may_be_bundled_with_evidence_migration",
        "proof_complete_promotion_allowed_by_stage54_v1",
        "update_or_delete_existing_billing_evidence_allowed_by_stage54_v1",
        "execute_sql_dml_or_ddl_allowed",
    }
    for key in required_false:
        if protocol.get(key) is not False:
            fail(f"Stage54 forbidden protocol surface enabled: {key}")

    registry = authority.get("current_registry")
    if registry != {
        "registered_billing_evidence_promotions": 0,
        "versioned_credentials_verified_promotion_migrations": 0,
        "remote_credentials_verified_rows": 0,
        "remote_proof_complete_rows": 0,
    }:
        fail("historical zero-promotion registry drift")

    if set(authority.get("failure_classes", [])) != EXPECTED_FAILURE_CLASSES:
        fail("Stage54 failure-class registry drift")

    gates = authority.get("gates")
    if not isinstance(gates, dict):
        fail("gate registry missing")
    if gates.get("stage54_boundary") != "REPO_ONLY_PENDING_CI":
        fail("Stage54 boundary state drift")
    for key in (
        "billing_provider_credentials",
        "provider_activation",
        "provider_call",
        "proof_complete",
        "production_deployment",
        "incident_response",
        "controlled_launch",
        "paid_media",
        "launch",
    ):
        if not str(gates.get(key, "")).startswith("DENIED"):
            fail(f"Stage54 preparation cannot promote gate: {key}")

    serialized = json.dumps(authority, sort_keys=True).lower()
    for forbidden_key in (
        '"api_key"',
        '"access_token"',
        '"password"',
        '"webhook_token"',
        '"credential_value"',
        '"secret_value"',
    ):
        if forbidden_key in serialized:
            fail(f"secret-bearing key found in Stage54 authority: {forbidden_key}")
    return authority


def billing_evidence_write_migrations() -> tuple[list[Path], list[Path]]:
    credential_inserts: list[Path] = []
    forbidden_writes: list[Path] = []
    for path in sorted(MIGRATIONS.glob("*.sql")):
        text = normalize_executable_sql(path.read_text(encoding="utf-8")).lower()
        if "insert into private.billing_provider_external_evidence" in text:
            if "'credentials_verified'" in text and "'proof_complete'" not in text:
                credential_inserts.append(path)
            else:
                forbidden_writes.append(path)
        if (
            "update private.billing_provider_external_evidence" in text
            or "delete from private.billing_provider_external_evidence" in text
            or "truncate private.billing_provider_external_evidence" in text
        ):
            forbidden_writes.append(path)
    return credential_inserts, sorted(set(forbidden_writes))


def verify_registered_promotions() -> int:
    credential_inserts, forbidden_writes = billing_evidence_write_migrations()
    if forbidden_writes:
        fail(
            "Stage54 V1 forbids proof_complete/update/delete billing evidence writes: "
            + ",".join(path.name for path in forbidden_writes)
        )

    registered = 0
    for migration in credential_inserts:
        companion = PROMOTIONS / f"{migration.stem}.json"
        if not companion.is_file():
            fail(f"unregistered billing evidence migration: {migration.name}")
        manifest = load_authority(companion)
        try:
            validate_authority(manifest, require_migration=True)
        except ValueError as exc:
            fail(f"invalid billing promotion authority {companion.name}: {exc}")
        if manifest.get("migration_filename") != migration.name:
            fail(f"promotion authority migration filename mismatch: {migration.name}")
        actual_sql = normalize_executable_sql(migration.read_text(encoding="utf-8"))
        expected_sql = normalize_executable_sql(render_executable_sql(manifest))
        if actual_sql != expected_sql:
            fail(f"registered billing promotion body drift: {migration.name}")
        registered += 1

    if PROMOTIONS.is_dir():
        for companion in sorted(PROMOTIONS.glob("*.json")):
            manifest = load_authority(companion)
            try:
                validate_authority(
                    manifest,
                    require_migration=manifest.get("promotion_state") != "REVIEWED_CANDIDATE_NO_MIGRATION",
                )
            except ValueError as exc:
                fail(f"invalid billing promotion authority {companion.name}: {exc}")
            state = manifest["promotion_state"]
            if state != "REVIEWED_CANDIDATE_NO_MIGRATION":
                migration = MIGRATIONS / str(manifest["migration_filename"])
                if not migration.is_file():
                    fail(f"promotion authority claims missing migration: {companion.name}")
                if companion.name != f"{migration.stem}.json":
                    fail(f"promotion authority filename is not migration-bound: {companion.name}")
    return registered


def base_fixture() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "protocol": PROTOCOL,
        "project_ref": "mceukeondizkwlpfxzgf",
        "scope": SCOPE,
        "provider_code": PROVIDER_CODE,
        "evidence_version": EVIDENCE_VERSION,
        "evidence_state": EVIDENCE_STATE,
        "provider_environment_id": PROVIDER_ENVIRONMENT_ID,
        "source_receipt_stage": SOURCE_STAGE,
        "promotion_state": "REVIEWED_CANDIDATE_NO_MIGRATION",
        "independent_review_decision": "APPROVED_FOR_CREDENTIAL_EVIDENCE_MIGRATION_DRAFT",
        "source_receipt_sha256": "a" * 64,
        "independent_review_receipt_sha256": "b" * 64,
        "source_artifact_review_digest": "c" * 64,
        "review_bundle_digest": "d" * 64,
        "reviewer_reference_digest": "e" * 64,
        "provider_account_owner_authorization_digest": "f" * 64,
        "credential_activation_digest": "1" * 64,
        "secret_boundary_ref_digest": "2" * 64,
        "reviewer_independence_attested": True,
        "source_artifacts_reviewed_out_of_band_attested": True,
        "operator_redaction_confirmed": True,
        "credential_artifact_contains_secret_value": False,
        "script_verifies_reviewer_independence": False,
        "synthetic_test_fixture": False,
        "stage47_aggregate_used_as_external_review_authority": False,
        "stage48_regression_used_as_external_review_authority": False,
        "stage49_protocol_used_as_billing_authorization": False,
        "provider_activation_performed": False,
        "provider_call_performed": False,
        "gate_ready_attested_by_tool": False,
        "remote_apply_performed": False,
        "controlled_launch_promoted": False,
        "paid_media_promoted": False,
        "launch_promoted": False,
        "credentials_verified_at_utc": "2026-08-25T00:00:00+00:00",
        "independent_review_completed_at_utc": "2026-08-25T00:05:00+00:00",
        "evidence_ref": f"stage54://billing-credentials/{SCOPE}/{PROVIDER_CODE}/" + "b" * 64,
        "evidence_digest": "d" * 64,
        "migration_filename": None,
    }


def expect_rejected(label: str, fixture: dict[str, Any]) -> None:
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
        fail(f"valid in-memory Stage54 contract unexpectedly rejected: {exc}")

    sandbox = dict(base)
    sandbox["provider_environment_id"] = "asaas-sandbox"
    expect_rejected("sandbox production crossover", sandbox)

    proof_complete = dict(base)
    proof_complete["evidence_state"] = "proof_complete"
    expect_rejected("proof_complete without dedicated protocol", proof_complete)

    synthetic = dict(base)
    synthetic["synthetic_test_fixture"] = True
    expect_rejected("synthetic review authority", synthetic)

    aggregate = dict(base)
    aggregate["stage47_aggregate_used_as_external_review_authority"] = True
    expect_rejected("Stage47 aggregate substitution", aggregate)

    no_independence = dict(base)
    no_independence["reviewer_independence_attested"] = False
    expect_rejected("missing independent reviewer attestation", no_independence)

    leaked_secret = dict(base)
    leaked_secret["credential_artifact_contains_secret_value"] = True
    expect_rejected("credential secret material", leaked_secret)

    activated = dict(base)
    activated["provider_activation_performed"] = True
    expect_rejected("activation bundled with evidence promotion", activated)

    collision = dict(base)
    collision["independent_review_receipt_sha256"] = collision["source_receipt_sha256"]
    collision["evidence_ref"] = f"stage54://billing-credentials/{SCOPE}/{PROVIDER_CODE}/" + collision["source_receipt_sha256"]
    expect_rejected("source/review digest collision", collision)

    rendered = normalize_executable_sql(render_executable_sql(base)).lower()
    required_markers = (
        "insert into private.billing_provider_external_evidence",
        "'credentials_verified'",
        "'asaas-production'",
        "s.state = 'selected_pending_credentials'",
        "s.activated_at is null",
        "and not exists",
        "get diagnostics v_inserted = row_count",
        "if v_inserted <> 1 then",
        "stage54_credential_evidence_promotion_precondition_failed",
        "review_bundle_sha256=",
        "independent_review_sha256=",
    )
    for marker in required_markers:
        if marker not in rendered:
            fail(f"rendered credential evidence SQL lost fail-closed marker: {marker}")
    forbidden_markers = (
        "activate_billing_provider_selection(",
        "update public.billing_provider_selections",
        "'proof_complete'",
    )
    for marker in forbidden_markers:
        if marker in rendered:
            fail(f"rendered credential evidence SQL contains forbidden bundled action: {marker}")


def verify_local_only_tooling() -> None:
    combined = (CONTRACT.read_text(encoding="utf-8") + "\n" + BUILDER.read_text(encoding="utf-8")).lower()
    forbidden = (
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
    )
    for marker in forbidden:
        if marker in combined:
            fail(f"Stage54 local tooling contains forbidden remote/execution surface: {marker}")

    if list(MIGRATIONS.glob("*stage54*.sql")):
        fail("Stage54 boundary preparation must not create a Stage54 migration")


def main() -> None:
    verify_authority()
    registered = verify_registered_promotions()
    verify_negative_controls()
    verify_local_only_tooling()

    print("STAGE54_BILLING_EXTERNAL_EVIDENCE_PROMOTION_BOUNDARY=PASS")
    print(f"REGISTERED_BILLING_EVIDENCE_PROMOTIONS={registered}")
    print("CURRENT_CREDENTIALS_VERIFIED_ROWS=0")
    print("PROOF_COMPLETE_PROMOTION_ALLOWED=false")
    print("STAGE47_AGGREGATE_IS_BILLING_AUTHORITY=false")
    print("PROVIDER_ACTIVATION_BUNDLED=false")
    print("PROVIDER_CALL=false")
    print("REMOTE_MUTATION=false")
    print("CONTROLLED_LAUNCH=false")


if __name__ == "__main__":
    main()
