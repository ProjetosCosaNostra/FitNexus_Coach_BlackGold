from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

import verify_stage49_evidence_migration_promotion_boundary as boundary
from stage49_evidence_promotion_contract import (
    SOURCE_STAGE_BY_GATE,
    render_executable_sql,
    validate_authority,
)

FAILURE_CLASS = "BGF-STAGE50-ADVERSARIAL-REGRESSION-GUARD-473"
ROOT = Path(__file__).resolve().parents[2]
AUTHORITY = ROOT / "04_backend_supabase/stage50_evidence_promotion_adversarial_regression_authority.json"
MIGRATIONS = ROOT / "04_backend_supabase/migrations"
OPERATIONS = ROOT / "04_backend_supabase/operations"
BUILDER = ROOT / "04_backend_supabase/tools/build_stage49_evidence_promotion_candidate.py"

EXPECTED_BASELINE = "8c4d1effc758ea2ff551eadc95506b5151446531"
EXPECTED_STATE = "ADVERSARIAL_REGRESSION_PREPARED_NO_EXTERNAL_EVIDENCE_NO_PROMOTION_NO_REMOTE_MUTATION"
EXPECTED_MATRIX = {
    "SYNTHETIC_REVIEW_AUTHORITY_REJECTED",
    "STAGE47_AGGREGATE_SUBSTITUTION_REJECTED",
    "STAGE48_REGRESSION_SUBSTITUTION_REJECTED",
    "SOURCE_AND_REVIEW_RECEIPT_DIGEST_COLLISION_REJECTED",
    "CANONICAL_SOURCE_STAGE_MISMATCH_REJECTED",
    "EVIDENCE_REF_MISMATCH_REJECTED",
    "EVIDENCE_DIGEST_MISMATCH_REJECTED",
    "UNREGISTERED_PROMOTION_MIGRATION_REJECTED",
    "MULTI_GATE_PROMOTION_BODY_REJECTED",
    "REGISTERED_PROMOTION_BODY_DRIFT_REJECTED",
    "CANDIDATE_MIGRATION_MASQUERADE_REJECTED",
}
EXPECTED_FAILURE_CLASSES = {
    "BGF-STAGE50-SYNTHETIC-REVIEW-FALSE-AUTHORITY-462",
    "BGF-STAGE50-STAGE47-AGGREGATE-SUBSTITUTION-463",
    "BGF-STAGE50-STAGE48-REGRESSION-SUBSTITUTION-464",
    "BGF-STAGE50-SOURCE-REVIEW-DIGEST-COLLISION-465",
    "BGF-STAGE50-CANONICAL-SOURCE-STAGE-SPOOF-466",
    "BGF-STAGE50-EVIDENCE-REF-REBIND-467",
    "BGF-STAGE50-EVIDENCE-DIGEST-REBIND-468",
    "BGF-STAGE50-UNREGISTERED-PROMOTION-MIGRATION-469",
    "BGF-STAGE50-MULTI-GATE-PROMOTION-BODY-470",
    "BGF-STAGE50-REGISTERED-PROMOTION-BODY-DRIFT-471",
    "BGF-STAGE50-CANDIDATE-MIGRATION-MASQUERADE-472",
    "BGF-STAGE50-ADVERSARIAL-REGRESSION-GUARD-473",
}


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE50_EVIDENCE_PROMOTION_ADVERSARIAL_REGRESSION=FAIL\n"
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


def valid_manifest(
    *,
    gate: str = "legal_terms_of_use",
    state: str = "REVIEWED_CANDIDATE_NO_MIGRATION",
    migration_filename: str | None = None,
) -> dict[str, Any]:
    source_digest = "a" * 64
    review_digest = "b" * 64
    bundle_digest = "d" * 64
    return {
        "schema_version": 1,
        "protocol": "STAGE49_V1",
        "project_ref": "mceukeondizkwlpfxzgf",
        "gate_code": gate,
        "source_receipt_stage": SOURCE_STAGE_BY_GATE[gate],
        "promotion_state": state,
        "independent_review_decision": "APPROVED_FOR_EVIDENCE_MIGRATION_DRAFT",
        "source_receipt_sha256": source_digest,
        "independent_review_receipt_sha256": review_digest,
        "source_artifact_review_digest": "c" * 64,
        "review_bundle_digest": bundle_digest,
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
        "evidence_ref": f"stage49://external-evidence/{gate}/{review_digest}",
        "evidence_digest": bundle_digest,
        "migration_filename": migration_filename,
    }


def expect_value_error(case: str, mutate: Callable[[dict[str, Any]], None]) -> None:
    manifest = valid_manifest()
    mutate(manifest)
    try:
        validate_authority(manifest, require_migration=False)
    except ValueError:
        return
    fail(f"{case}: adversarial promotion authority was accepted")


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def expect_boundary_failure(
    case: str,
    migrations: Path,
    promotions: Path,
) -> None:
    old_migrations = boundary.MIGRATIONS
    old_promotions = boundary.PROMOTIONS
    old_stage20 = boundary.STAGE20_BOOTSTRAP
    try:
        boundary.MIGRATIONS = migrations
        boundary.PROMOTIONS = promotions
        boundary.STAGE20_BOOTSTRAP = migrations / "historical_stage20_allowlist.sql"
        try:
            boundary.verify_registered_promotions()
        except SystemExit:
            return
        fail(f"{case}: Stage49 boundary accepted adversarial repository fixture")
    finally:
        boundary.MIGRATIONS = old_migrations
        boundary.PROMOTIONS = old_promotions
        boundary.STAGE20_BOOTSTRAP = old_stage20


def verify_authority() -> None:
    authority = load_json(AUTHORITY)
    if authority.get("schema_version") != 1:
        fail("Stage50 schema_version drift")
    if authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("Stage50 project_ref drift")
    if authority.get("stage") != "STAGE50_EVIDENCE_PROMOTION_ADVERSARIAL_REGRESSION":
        fail("Stage50 stage drift")
    if authority.get("baseline_main_sha") != EXPECTED_BASELINE:
        fail("Stage50 baseline main SHA drift")
    if authority.get("current_state") != EXPECTED_STATE:
        fail("Stage50 current state drift")

    pins = authority.get("stage49_pins")
    expected_pins = {
        "authority": (
            "04_backend_supabase/stage49_evidence_migration_promotion_boundary_authority.json",
            "6378fdc6435123ce1809c235b9d1c5342357e4d3",
        ),
        "contract": (
            "04_backend_supabase/tools/stage49_evidence_promotion_contract.py",
            "cdf83a123e4f13209590eda7987bcd42013622db",
        ),
        "guard": (
            "04_backend_supabase/tools/verify_stage49_evidence_migration_promotion_boundary.py",
            "2437596934d7fc3e0834c0173d02148a27009957",
        ),
        "candidate_builder": (
            "04_backend_supabase/tools/build_stage49_evidence_promotion_candidate.py",
            "7292b40b3ad90e26c61a6966cd2dd36c311f4396",
        ),
    }
    if not isinstance(pins, dict):
        fail("Stage49 pin registry missing")
    for key, (relative, blob) in expected_pins.items():
        item = pins.get(key)
        if not isinstance(item, dict):
            fail(f"Stage49 pin missing: {key}")
        if item.get("path") != relative or item.get("git_blob_sha") != blob:
            fail(f"Stage49 pin metadata drift: {key}")
        path = ROOT / relative
        if not path.is_file() or git_blob_sha(path) != blob:
            fail(f"Stage49 sealed bytes drift: {key}")

    remote = authority.get("fresh_remote_read_only_receipt")
    expected_remote = {
        "observed_at_utc": "2026-08-24T18:29:37.215667+00:00",
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
        "stage40_activation_production_environment_interlock": True,
        "stage40_readiness_production_environment_interlock": True,
        "remote_mutation_performed": False,
    }
    if not isinstance(remote, dict):
        fail("Stage50 fresh remote receipt missing")
    for key, expected in expected_remote.items():
        if remote.get(key) != expected:
            fail(f"Stage50 fresh remote receipt drift: {key}")

    if set(authority.get("adversarial_matrix", [])) != EXPECTED_MATRIX:
        fail("Stage50 adversarial matrix drift")
    fixture = authority.get("fixture_contract")
    if not isinstance(fixture, dict):
        fail("Stage50 fixture contract missing")
    if fixture.get("fixtures_are_in_memory_or_temporary") is not True:
        fail("Stage50 fixtures must remain in-memory/temporary")
    for key in (
        "fixtures_are_external_evidence",
        "fixtures_are_independent_review",
        "fixtures_can_create_persistent_migration",
        "fixtures_can_promote_gate",
        "fixtures_can_authorize_remote_apply",
        "real_customer_data_used",
        "raw_secret_used",
        "provider_call_performed",
        "network_call_performed",
        "supabase_mutation_performed",
        "deployment_action_performed",
    ):
        if fixture.get(key) is not False:
            fail(f"Stage50 non-evidence fixture contract drift: {key}")

    if set(authority.get("failure_classes", [])) != EXPECTED_FAILURE_CLASSES:
        fail("Stage50 failure-class registry drift")
    gates = authority.get("gates")
    if not isinstance(gates, dict) or any(value != "DENIED" for value in gates.values()):
        fail("Stage50 may not promote any external or launch gate")
    if list(MIGRATIONS.glob("*stage50*.sql")):
        fail("Stage50 adversarial regression must not create a migration")


def verify_manifest_adversaries() -> None:
    expect_value_error(
        "SYNTHETIC_REVIEW_AUTHORITY_REJECTED",
        lambda m: m.__setitem__("synthetic_test_fixture", True),
    )
    expect_value_error(
        "STAGE47_AGGREGATE_SUBSTITUTION_REJECTED",
        lambda m: m.__setitem__("stage47_aggregate_used_as_external_review_authority", True),
    )
    expect_value_error(
        "STAGE48_REGRESSION_SUBSTITUTION_REJECTED",
        lambda m: m.__setitem__("stage48_regression_used_as_external_review_authority", True),
    )
    expect_value_error(
        "SOURCE_AND_REVIEW_RECEIPT_DIGEST_COLLISION_REJECTED",
        lambda m: m.__setitem__("independent_review_receipt_sha256", m["source_receipt_sha256"]),
    )
    expect_value_error(
        "CANONICAL_SOURCE_STAGE_MISMATCH_REJECTED",
        lambda m: m.__setitem__("source_receipt_stage", SOURCE_STAGE_BY_GATE["legal_privacy_notice"]),
    )
    expect_value_error(
        "EVIDENCE_REF_MISMATCH_REJECTED",
        lambda m: m.__setitem__("evidence_ref", "stage49://external-evidence/legal_terms_of_use/" + "f" * 64),
    )
    expect_value_error(
        "EVIDENCE_DIGEST_MISMATCH_REJECTED",
        lambda m: m.__setitem__("evidence_digest", "f" * 64),
    )


def verify_repository_adversaries(temp_root: Path) -> None:
    # 1. Exact Stage49 SQL without its companion authority must fail closed.
    unregistered_migrations = temp_root / "unregistered/migrations"
    unregistered_promotions = temp_root / "unregistered/promotions"
    unregistered_migrations.mkdir(parents=True)
    unregistered_promotions.mkdir(parents=True)
    migration_name = "20260824190000_external_evidence_promotion_legal_terms_of_use.sql"
    manifest = valid_manifest(
        state="VERSIONED_MIGRATION_PRESENT_REPO_ONLY",
        migration_filename=migration_name,
    )
    (unregistered_migrations / migration_name).write_text(render_executable_sql(manifest), encoding="utf-8")
    expect_boundary_failure(
        "UNREGISTERED_PROMOTION_MIGRATION_REJECTED",
        unregistered_migrations,
        unregistered_promotions,
    )

    # 2. A companion authority for one gate cannot authorize a second gate update.
    multi_migrations = temp_root / "multi-gate/migrations"
    multi_promotions = temp_root / "multi-gate/promotions"
    multi_migrations.mkdir(parents=True)
    multi_promotions.mkdir(parents=True)
    multi_name = "20260824190100_external_evidence_promotion_legal_terms_of_use.sql"
    multi_manifest = valid_manifest(
        state="VERSIONED_MIGRATION_PRESENT_REPO_ONLY",
        migration_filename=multi_name,
    )
    extra_gate_update = """
update private.controlled_launch_gate_evidence
set state = 'ready', evidence_ref = 'forbidden', evidence_digest = 'forbidden'
where gate_code = 'legal_privacy_notice';
"""
    (multi_migrations / multi_name).write_text(
        render_executable_sql(multi_manifest) + extra_gate_update,
        encoding="utf-8",
    )
    write_json(multi_promotions / f"{Path(multi_name).stem}.json", multi_manifest)
    expect_boundary_failure(
        "MULTI_GATE_PROMOTION_BODY_REJECTED",
        multi_migrations,
        multi_promotions,
    )

    # 3. Even harmless-looking executable drift after deterministic rendering is rejected.
    drift_migrations = temp_root / "body-drift/migrations"
    drift_promotions = temp_root / "body-drift/promotions"
    drift_migrations.mkdir(parents=True)
    drift_promotions.mkdir(parents=True)
    drift_name = "20260824190200_external_evidence_promotion_legal_terms_of_use.sql"
    drift_manifest = valid_manifest(
        state="VERSIONED_MIGRATION_PRESENT_REPO_ONLY",
        migration_filename=drift_name,
    )
    (drift_migrations / drift_name).write_text(
        render_executable_sql(drift_manifest) + "\nselect 1;\n",
        encoding="utf-8",
    )
    write_json(drift_promotions / f"{Path(drift_name).stem}.json", drift_manifest)
    expect_boundary_failure(
        "REGISTERED_PROMOTION_BODY_DRIFT_REJECTED",
        drift_migrations,
        drift_promotions,
    )


def verify_candidate_masquerade_rejected(temp_root: Path) -> None:
    manifest_path = temp_root / "reviewed-candidate.json"
    write_json(manifest_path, valid_manifest())
    forbidden_output = OPERATIONS / "20991231235959_external_evidence_promotion_legal_terms_of_use.sql"
    if forbidden_output.exists():
        fail("candidate masquerade sentinel path already exists")
    completed = subprocess.run(
        [
            sys.executable,
            str(BUILDER),
            "--authority",
            str(manifest_path),
            "--output",
            str(forbidden_output),
        ],
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    accidentally_created = forbidden_output.exists()
    if accidentally_created:
        forbidden_output.unlink()
    if completed.returncode == 0 or accidentally_created:
        fail("CANDIDATE_MIGRATION_MASQUERADE_REJECTED: builder allowed timestamp migration masquerade")


def main() -> None:
    verify_authority()
    verify_manifest_adversaries()
    with tempfile.TemporaryDirectory(prefix="stage50-promotion-regression-") as raw:
        temp_root = Path(raw)
        verify_repository_adversaries(temp_root)
        verify_candidate_masquerade_rejected(temp_root)

    print("STAGE50_EVIDENCE_PROMOTION_ADVERSARIAL_REGRESSION=PASS")
    print("ADVERSARIAL_CASES=11_PASS")
    print("REAL_EXTERNAL_EVIDENCE_USED=false")
    print("INDEPENDENT_REVIEW_PERFORMED_BY_TEST=false")
    print("PERSISTENT_MIGRATION_CREATED=false")
    print("PROVIDER_CALL=false")
    print("NETWORK_CALL=false")
    print("SUPABASE_MUTATION=false")
    print("GATE_PROMOTION=false")
    print("CONTROLLED_LAUNCH=false")


if __name__ == "__main__":
    main()
