from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from stage49_evidence_promotion_contract import (
    ELIGIBLE_GATES,
    SOURCE_STAGE_BY_GATE,
    load_authority,
    normalize_executable_sql,
    render_executable_sql,
    validate_authority,
)

FAILURE_CLASS = "BGF-STAGE49-PROMOTION-BOUNDARY-GUARD-461"
ROOT = Path(__file__).resolve().parents[2]
AUTHORITY = ROOT / "04_backend_supabase/stage49_evidence_migration_promotion_boundary_authority.json"
MIGRATIONS = ROOT / "04_backend_supabase/migrations"
PROMOTIONS = ROOT / "04_backend_supabase/evidence_promotions"
BUILDER = ROOT / "04_backend_supabase/tools/build_stage49_evidence_promotion_candidate.py"
CONTRACT = ROOT / "04_backend_supabase/tools/stage49_evidence_promotion_contract.py"

STAGE20_BOOTSTRAP = ROOT / "04_backend_supabase/migrations/20260819062000_stage20_controlled_launch_admission.sql"
EXPECTED_BASELINE = "8be14d0d157f6372af662ee62bcd0f430774cd76"
EXPECTED_STATE = "PROMOTION_BOUNDARY_PREPARED_NO_EXTERNAL_REVIEW_NO_EVIDENCE_MIGRATION_NO_REMOTE_MUTATION"
EXPECTED_FAILURE_CLASSES = {
    "BGF-STAGE49-MIGRATION-SELF-ATTESTATION-450",
    "BGF-STAGE49-STAGE47-AGGREGATE-AS-PROMOTION-AUTHORITY-451",
    "BGF-STAGE49-UNREGISTERED-EVIDENCE-PROMOTION-MIGRATION-452",
    "BGF-STAGE49-MULTI-GATE-PROMOTION-MIGRATION-453",
    "BGF-STAGE49-REVIEW-RECEIPT-DIGEST-UNBOUND-454",
    "BGF-STAGE49-SOURCE-RECEIPT-DIGEST-UNBOUND-455",
    "BGF-STAGE49-SYNTHETIC-REVIEW-AS-EXTERNAL-AUTHORITY-456",
    "BGF-STAGE49-REVIEWER-INDEPENDENCE-SELF-VERIFICATION-457",
    "BGF-STAGE49-EVIDENCE-REF-DIGEST-MISMATCH-458",
    "BGF-STAGE49-CANDIDATE-DIRECT-APPLY-459",
    "BGF-STAGE49-EXECUTE-SQL-EVIDENCE-DML-460",
    "BGF-STAGE49-PROMOTION-BOUNDARY-GUARD-461",
}


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE49_EVIDENCE_MIGRATION_PROMOTION_BOUNDARY=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\n"
        f"DETAIL={detail}"
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


def verify_stage49_authority() -> dict[str, Any]:
    authority = load_json(AUTHORITY)
    if authority.get("schema_version") != 1:
        fail("Stage49 schema_version drift")
    if authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("Stage49 project_ref drift")
    if authority.get("stage") != "STAGE49_EVIDENCE_MIGRATION_PROMOTION_BOUNDARY":
        fail("Stage49 stage drift")
    if authority.get("baseline_main_sha") != EXPECTED_BASELINE:
        fail("Stage49 baseline SHA drift")
    if authority.get("current_state") != EXPECTED_STATE:
        fail("Stage49 current state drift")

    problem = authority.get("problem_statement")
    if not isinstance(problem, dict):
        fail("Stage49 problem statement missing")
    if problem.get("stage47_aggregate_is_launch_authority") is not False:
        fail("Stage47 aggregate must never become launch authority")
    if problem.get("stage48_adversarial_pass_is_external_evidence") is not False:
        fail("Stage48 adversarial pass must never become external evidence")

    remote = authority.get("fresh_remote_read_only_receipt")
    expected_remote = {
        "observed_at_utc": "2026-08-24T18:19:08.437154+00:00",
        "auth_users": 0,
        "organizations": 0,
        "billing_provider_state": "selected_pending_credentials",
        "billing_provider_activated_at": None,
        "external_billing_evidence_rows": 0,
        "evidence_migration_rows": 6,
        "evidence_migration_ready_rows": 0,
        "evidence_migration_blocked_rows": 6,
        "non_null_evidence_refs": 0,
        "non_null_evidence_digests": 0,
        "anon_write_privileges": False,
        "authenticated_write_privileges": False,
        "service_role_write_privileges": False,
        "readiness_function_accepts_ready_rows": True,
        "stage40_activation_production_environment_interlock": True,
        "stage40_readiness_production_environment_interlock": True,
        "remote_mutation_performed": False,
    }
    if not isinstance(remote, dict):
        fail("fresh remote read-only receipt missing")
    for key, expected in expected_remote.items():
        if remote.get(key) != expected:
            fail(f"fresh remote receipt drift: {key}")

    sealed = authority.get("sealed_inputs")
    if not isinstance(sealed, dict):
        fail("sealed inputs missing")
    for item in sealed.values():
        if not isinstance(item, dict):
            fail("sealed input entry malformed")
        path = ROOT / str(item.get("path", ""))
        expected_blob = str(item.get("git_blob_sha", ""))
        if not path.is_file():
            fail(f"sealed input missing: {path}")
        if git_blob_sha(path) != expected_blob:
            fail(f"sealed input blob drift: {path.name}")

    protocol = authority.get("promotion_protocol")
    if not isinstance(protocol, dict):
        fail("promotion protocol missing")
    if protocol.get("protocol_id") != "STAGE49_V1":
        fail("promotion protocol id drift")
    if set(protocol.get("eligible_gate_codes", [])) != ELIGIBLE_GATES:
        fail("eligible evidence_migration gate set drift")
    required_true = {
        "one_gate_per_migration",
        "historical_stage20_bootstrap_is_allowlisted",
        "companion_authority_required_for_future_promotion_migration",
        "canonical_source_receipt_sha256_required",
        "independent_review_receipt_sha256_required",
        "source_artifact_review_digest_required",
        "review_bundle_digest_required",
        "reviewer_reference_digest_required",
        "reviewer_independence_attestation_required",
        "source_artifacts_reviewed_out_of_band_attestation_required",
        "remote_apply_requires_separate_preapply_authority_reread",
    }
    for key in required_true:
        if protocol.get(key) is not True:
            fail(f"Stage49 fail-closed protocol drift: {key}")
    required_false = {
        "billing_provider_credentials_uses_this_protocol",
        "future_unregistered_gate_ready_migration_allowed",
        "script_can_verify_reviewer_independence",
        "synthetic_fixture_can_satisfy_promotion",
        "stage47_aggregate_can_satisfy_promotion",
        "stage48_regression_can_satisfy_promotion",
        "stage35_alert_proof_alone_can_satisfy_production_deployment",
        "candidate_generation_is_remote_apply_authority",
        "versioned_migration_presence_is_remote_apply_authority",
        "execute_sql_dml_or_ddl_allowed",
    }
    for key in required_false:
        if protocol.get(key) is not False:
            fail(f"Stage49 forbidden protocol surface enabled: {key}")

    registry = authority.get("current_registry")
    if registry != {
        "registered_external_evidence_promotions": 0,
        "versioned_external_evidence_promotion_migrations": 0,
        "remote_external_evidence_promotions": 0,
    }:
        fail("Stage49 historical zero-promotion registry drift")

    if set(authority.get("failure_classes", [])) != EXPECTED_FAILURE_CLASSES:
        fail("Stage49 failure-class registry drift")

    gates = authority.get("gates")
    if not isinstance(gates, dict):
        fail("Stage49 gate registry missing")
    for value in gates.values():
        if not str(value).startswith("DENIED"):
            fail("Stage49 preparation cannot promote a gate")
    return authority


def promotion_migrations() -> list[Path]:
    result: list[Path] = []
    for path in sorted(MIGRATIONS.glob("*.sql")):
        if path == STAGE20_BOOTSTRAP:
            continue
        text = path.read_text(encoding="utf-8")
        normalized = normalize_executable_sql(text).lower()
        if (
            "update private.controlled_launch_gate_evidence" in normalized
            and "set state = 'ready'" in normalized
        ):
            result.append(path)
    return result


def verify_registered_promotions() -> int:
    migrations = promotion_migrations()
    registered = 0

    for migration in migrations:
        companion = PROMOTIONS / f"{migration.stem}.json"
        if not companion.is_file():
            fail(f"unregistered evidence promotion migration: {migration.name}")
        manifest = load_authority(companion)
        try:
            validate_authority(manifest, require_migration=True)
        except ValueError as exc:
            fail(f"invalid promotion authority {companion.name}: {exc}")
        if manifest.get("migration_filename") != migration.name:
            fail(f"promotion authority migration filename mismatch: {migration.name}")

        actual_sql = migration.read_text(encoding="utf-8")
        expected_sql = render_executable_sql(manifest)
        if normalize_executable_sql(actual_sql) != normalize_executable_sql(expected_sql):
            fail(f"promotion migration executable body drift: {migration.name}")
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
                fail(f"invalid promotion authority {companion.name}: {exc}")
            state = manifest["promotion_state"]
            if state != "REVIEWED_CANDIDATE_NO_MIGRATION":
                migration = MIGRATIONS / str(manifest["migration_filename"])
                if not migration.is_file():
                    fail(f"promotion authority claims missing migration: {companion.name}")
                expected_companion = f"{migration.stem}.json"
                if companion.name != expected_companion:
                    fail(f"promotion authority filename is not migration-bound: {companion.name}")
    return registered


def verify_contract_negative_controls() -> None:
    gate = "legal_terms_of_use"
    source_stage = SOURCE_STAGE_BY_GATE[gate]
    base = {
        "schema_version": 1,
        "protocol": "STAGE49_V1",
        "project_ref": "mceukeondizkwlpfxzgf",
        "gate_code": gate,
        "source_receipt_stage": source_stage,
        "promotion_state": "REVIEWED_CANDIDATE_NO_MIGRATION",
        "independent_review_decision": "APPROVED_FOR_EVIDENCE_MIGRATION_DRAFT",
        "source_receipt_sha256": "a" * 64,
        "independent_review_receipt_sha256": "b" * 64,
        "source_artifact_review_digest": "c" * 64,
        "review_bundle_digest": "d" * 64,
        "reviewer_reference_digest": "e" * 64,
        "reviewer_independence_attested": True,
        "source_artifacts_reviewed_out_of_band_attested": True,
        "script_verifies_reviewer_independence": False,
        "synthetic_test_fixture": False,
        "stage47_aggregate_used_as_external_review_authority": False,
        "stage48_regression_used_as_external_review_authority": False,
        "stage35_alert_proof_alone_used_for_production_deployment": False,
        "gate_ready_attested_by_tool": False,
        "remote_apply_performed": False,
        "controlled_launch_promoted": False,
        "paid_media_promoted": False,
        "launch_promoted": False,
        "independent_review_completed_at_utc": "2026-08-24T18:00:00+00:00",
        "evidence_ref": f"stage49://external-evidence/{gate}/" + "b" * 64,
        "evidence_digest": "d" * 64,
        "migration_filename": None,
    }

    synthetic = dict(base)
    synthetic["synthetic_test_fixture"] = True
    try:
        validate_authority(synthetic, require_migration=False)
    except ValueError:
        pass
    else:
        fail("synthetic review fixture was accepted as promotion authority")

    self_review = dict(base)
    self_review["reviewer_independence_attested"] = False
    try:
        validate_authority(self_review, require_migration=False)
    except ValueError:
        pass
    else:
        fail("missing reviewer-independence attestation was accepted")

    aggregate_authority = dict(base)
    aggregate_authority["stage47_aggregate_used_as_external_review_authority"] = True
    try:
        validate_authority(aggregate_authority, require_migration=False)
    except ValueError:
        pass
    else:
        fail("Stage47 aggregate was accepted as independent review authority")

    try:
        validate_authority(base, require_migration=False)
    except ValueError as exc:
        fail(f"in-memory contract shape unexpectedly invalid: {exc}")
    rendered = normalize_executable_sql(render_executable_sql(base)).lower()
    required = (
        "update private.controlled_launch_gate_evidence",
        "set state = 'ready'",
        "and state = 'blocked'",
        "and evidence_ref is null",
        "and evidence_digest is null",
        "get diagnostics v_updated = row_count",
        "if v_updated <> 1 then",
        "stage49_evidence_promotion_precondition_failed",
    )
    for marker in required:
        if marker not in rendered:
            fail(f"rendered promotion SQL lost fail-closed marker: {marker}")


def verify_no_remote_surfaces() -> None:
    builder = BUILDER.read_text(encoding="utf-8")
    contract = CONTRACT.read_text(encoding="utf-8")
    combined = (builder + "\n" + contract).lower()
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
            fail(f"Stage49 local tooling contains forbidden remote/execution surface: {marker}")

    if list(MIGRATIONS.glob("*stage49*.sql")):
        fail("Stage49 boundary preparation must not create a Stage49 migration")


def main() -> None:
    verify_stage49_authority()
    registered = verify_registered_promotions()
    verify_contract_negative_controls()
    verify_no_remote_surfaces()

    print("STAGE49_EVIDENCE_MIGRATION_PROMOTION_BOUNDARY=PASS")
    print(f"REGISTERED_PROMOTION_MIGRATIONS={registered}")
    print("CURRENT_EXTERNAL_EVIDENCE_PROMOTIONS=0")
    print("STAGE47_AGGREGATE_IS_PROMOTION_AUTHORITY=false")
    print("SYNTHETIC_REVIEW_IS_PROMOTION_AUTHORITY=false")
    print("SCRIPT_VERIFIES_REVIEWER_INDEPENDENCE=false")
    print("REMOTE_MUTATION=false")
    print("GATE_PROMOTION=false")


if __name__ == "__main__":
    main()
