from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

FAILURE_CLASS = "BGF-STAGE48-ADVERSARIAL-REGRESSION-GUARD-449"
ROOT = Path(__file__).resolve().parents[2]
AUTHORITY = ROOT / "04_backend_supabase/stage48_unified_intake_adversarial_regression_authority.json"
STAGE47_AUTHORITY = ROOT / "04_backend_supabase/stage47_unified_external_evidence_intake_orchestration_authority.json"
ORCHESTRATOR = ROOT / "04_backend_supabase/tools/review_stage47_external_evidence_bundle.py"
MIGRATIONS = ROOT / "04_backend_supabase/migrations"

EXPECTED_BASELINE = "1394df63f850cae43cb0a6d43e29e31f7718689b"
EXPECTED_STAGE47_AUTHORITY_BLOB = "9a8d504d3462a926014ced34508cdf42babbff46"
EXPECTED_STAGE47_ORCHESTRATOR_BLOB = "73a3e184bf9128ffec8645d6f5629a03e3c791a3"
EXPECTED_FAILURE_CLASSES = {
    "BGF-STAGE48-STAGE35-RECEIPT-MASQUERADE-443",
    "BGF-STAGE48-DUPLICATE-ROUTE-AMBIGUITY-444",
    "BGF-STAGE48-COMPLETE-MODE-MISSING-FALSE-GREEN-445",
    "BGF-STAGE48-CANONICAL-REVIEWER-FAILURE-SWALLOW-446",
    "BGF-STAGE48-AGGREGATE-SOURCE-PATH-LEAKAGE-447",
    "BGF-STAGE48-OUTPUT-SELF-INGESTION-448",
    "BGF-STAGE48-ADVERSARIAL-REGRESSION-GUARD-449",
}


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE48_UNIFIED_INTAKE_ADVERSARIAL_REGRESSION=FAIL\n"
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
        fail(f"authority unreadable: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail("authority must be a JSON object")
    return value


def run_orchestrator(bundle: Path, output: Path, mode: str) -> tuple[int, dict[str, Any]]:
    completed = subprocess.run(
        [
            sys.executable,
            str(ORCHESTRATOR),
            "--bundle-dir",
            str(bundle),
            "--output",
            str(output),
            "--mode",
            mode,
        ],
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if not output.is_file():
        fail("Stage47 orchestrator did not materialize aggregate")
    try:
        aggregate = json.loads(output.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"Stage47 aggregate unreadable: {type(exc).__name__}")
    if not isinstance(aggregate, dict):
        fail("Stage47 aggregate is not a JSON object")
    return int(completed.returncode), aggregate


def assert_false_authority(aggregate: dict[str, Any], case: str) -> None:
    flags = aggregate.get("authority_flags")
    if not isinstance(flags, dict) or not flags:
        fail(f"{case}: authority flags missing")
    if any(value is not False for value in flags.values()):
        fail(f"{case}: aggregate attempted authority promotion")
    entries = aggregate.get("entries")
    if not isinstance(entries, list) or len(entries) != 7:
        fail(f"{case}: expected exactly seven route entries")
    if any(not isinstance(item, dict) or item.get("gate_ready") is not False for item in entries):
        fail(f"{case}: route gate readiness drift")


def assert_no_source_locator_leak(aggregate: dict[str, Any], bundle: Path, filenames: list[str], case: str) -> None:
    serialized = json.dumps(aggregate, sort_keys=True)
    if str(bundle) in serialized:
        fail(f"{case}: bundle path leaked into aggregate")
    for filename in filenames:
        if filename in serialized:
            fail(f"{case}: source filename leaked into aggregate")


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def verify_authority() -> None:
    authority = load_json(AUTHORITY)
    if authority.get("schema_version") != 1:
        fail("Stage48 schema version drift")
    if authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("Stage48 project ref drift")
    if authority.get("stage") != "STAGE48_UNIFIED_INTAKE_ADVERSARIAL_REGRESSION":
        fail("Stage48 stage drift")
    if authority.get("baseline_main_sha") != EXPECTED_BASELINE:
        fail("Stage48 baseline main drift")
    if authority.get("current_state") != "ADVERSARIAL_REGRESSION_PREPARED_FAIL_CLOSED_NO_EXTERNAL_EVIDENCE_NO_REMOTE_MUTATION":
        fail("Stage48 state drift")

    pins = authority.get("stage47_pins")
    if not isinstance(pins, dict):
        fail("Stage47 pins missing")
    if pins.get("authority_git_blob_sha") != EXPECTED_STAGE47_AUTHORITY_BLOB:
        fail("Stage47 authority pin drift")
    if pins.get("orchestrator_git_blob_sha") != EXPECTED_STAGE47_ORCHESTRATOR_BLOB:
        fail("Stage47 orchestrator pin drift")
    if git_blob_sha(STAGE47_AUTHORITY) != EXPECTED_STAGE47_AUTHORITY_BLOB:
        fail("sealed Stage47 authority bytes drifted")
    if git_blob_sha(ORCHESTRATOR) != EXPECTED_STAGE47_ORCHESTRATOR_BLOB:
        fail("sealed Stage47 orchestrator bytes drifted")

    remote = authority.get("fresh_remote_read_only_receipt")
    expected_remote = {
        "observed_at_utc": "2026-08-24T17:43:27.273595+00:00",
        "auth_users": 0,
        "organizations": 0,
        "billing_provider_state": "selected_pending_credentials",
        "billing_provider_activated_at": None,
        "external_billing_evidence_rows": 0,
        "ready_evidence_migration_count": 0,
        "blocked_evidence_migration_gate_count": 6,
        "stage40_activation_production_environment_interlock": True,
        "stage40_readiness_production_environment_interlock": True,
        "remote_mutation_performed": False,
    }
    if not isinstance(remote, dict):
        fail("Stage48 remote receipt missing")
    for key, expected in expected_remote.items():
        if remote.get(key) != expected:
            fail(f"Stage48 remote receipt drift: {key}")

    fixture_contract = authority.get("non_evidence_fixture_contract")
    if not isinstance(fixture_contract, dict):
        fail("non-evidence fixture contract missing")
    if fixture_contract.get("fixtures_are_intentionally_malformed") is not True:
        fail("adversarial fixtures must remain intentionally malformed")
    for key in (
        "fixtures_are_external_evidence",
        "fixtures_can_promote_gate",
        "fixtures_can_create_evidence_migration",
        "fixtures_can_trigger_provider_call",
        "fixtures_can_trigger_deployment",
        "real_customer_data_used",
        "raw_secret_used",
        "network_call_performed",
        "supabase_mutation_performed",
    ):
        if fixture_contract.get(key) is not False:
            fail(f"non-evidence fixture authority drift: {key}")

    if set(authority.get("failure_classes", [])) != EXPECTED_FAILURE_CLASSES:
        fail("Stage48 failure-class registry drift")
    gates = authority.get("gates")
    if not isinstance(gates, dict) or any(value != "DENIED" for value in gates.values()):
        fail("Stage48 may not promote any external/launch gate")
    if list(MIGRATIONS.glob("*stage48*.sql")):
        fail("Stage48 adversarial regression must not add a migration")


def case_empty_inventory(root: Path) -> None:
    bundle = root / "empty-inventory"
    bundle.mkdir()
    output = root / "aggregate-empty-inventory.json"
    code, aggregate = run_orchestrator(bundle, output, "inventory")
    if code != 0 or aggregate.get("overall_state") != "INCOMPLETE_MISSING_EXTERNAL_EVIDENCE":
        fail("EMPTY_INVENTORY did not remain incomplete")
    if aggregate.get("missing_receipt_count") != 7 or aggregate.get("valid_structural_candidate_count") != 0:
        fail("EMPTY_INVENTORY counts drift")
    assert_false_authority(aggregate, "EMPTY_INVENTORY")


def case_empty_complete(root: Path) -> None:
    bundle = root / "empty-complete"
    bundle.mkdir()
    output = root / "aggregate-empty-complete.json"
    code, aggregate = run_orchestrator(bundle, output, "complete")
    if code != 3 or aggregate.get("overall_state") != "INCOMPLETE_MISSING_EXTERNAL_EVIDENCE":
        fail("EMPTY_COMPLETE_MODE false-green")
    if aggregate.get("missing_receipt_count") != 7:
        fail("EMPTY_COMPLETE_MODE missing count drift")
    assert_false_authority(aggregate, "EMPTY_COMPLETE_MODE")


def case_stage35_masquerade(root: Path) -> None:
    bundle = root / "stage35-masquerade"
    bundle.mkdir()
    filename = "stage35-not-stage47-evidence.json"
    write_json(bundle / filename, {"stage": "STAGE35_ALERT_EXTERNAL_DELIVERY_PROOF", "result": "PASS_IMMUTABLE"})
    output = root / "aggregate-stage35-masquerade.json"
    code, aggregate = run_orchestrator(bundle, output, "inventory")
    if code != 2 or aggregate.get("overall_state") != "INVALID_EXTERNAL_EVIDENCE_CANDIDATE_PRESENT":
        fail("STAGE35_RECEIPT_MASQUERADE was not rejected")
    if aggregate.get("unknown_or_unreadable_json_receipt_count") != 1:
        fail("STAGE35_RECEIPT_MASQUERADE unknown count drift")
    assert_false_authority(aggregate, "STAGE35_RECEIPT_MASQUERADE")
    assert_no_source_locator_leak(aggregate, bundle, [filename], "STAGE35_RECEIPT_MASQUERADE")


def case_duplicate_source(root: Path) -> None:
    bundle = root / "duplicate-source"
    bundle.mkdir()
    filenames = ["duplicate-a.json", "duplicate-b.json"]
    payload = {"stage": "STAGE41_LEGAL_TERMS_EXTERNAL_EVIDENCE_PREPARATION"}
    for filename in filenames:
        write_json(bundle / filename, payload)
    output = root / "aggregate-duplicate-source.json"
    code, aggregate = run_orchestrator(bundle, output, "inventory")
    if code != 2 or aggregate.get("duplicate_source_stage_count") != 1:
        fail("DUPLICATE_CANONICAL_SOURCE_STAGE was not rejected")
    route = next(item for item in aggregate["entries"] if item["gate_code"] == "legal_terms_of_use")
    if route.get("status") != "DUPLICATE" or route.get("reviewer_exit_code") is not None:
        fail("duplicate route must fail before canonical reviewer execution")
    assert_false_authority(aggregate, "DUPLICATE_CANONICAL_SOURCE_STAGE")
    assert_no_source_locator_leak(aggregate, bundle, filenames, "DUPLICATE_CANONICAL_SOURCE_STAGE")


def case_canonical_reviewer_rejects(root: Path) -> None:
    bundle = root / "canonical-reviewer-rejects"
    bundle.mkdir()
    filename = "malformed-privacy-candidate.json"
    write_json(bundle / filename, {"stage": "STAGE42_PRIVACY_NOTICE_EXTERNAL_EVIDENCE_PREPARATION"})
    output = root / "aggregate-canonical-reject.json"
    code, aggregate = run_orchestrator(bundle, output, "inventory")
    if code != 2 or aggregate.get("overall_state") != "INVALID_EXTERNAL_EVIDENCE_CANDIDATE_PRESENT":
        fail("canonical reviewer failure was swallowed")
    route = next(item for item in aggregate["entries"] if item["gate_code"] == "legal_privacy_notice")
    if route.get("status") != "INVALID_BY_CANONICAL_REVIEWER":
        fail("canonical reviewer rejection status drift")
    if not isinstance(route.get("reviewer_exit_code"), int) or route["reviewer_exit_code"] == 0:
        fail("canonical reviewer rejection exit code drift")
    assert_false_authority(aggregate, "CANONICAL_REVIEWER_REJECTS_MALFORMED_RECEIPT")
    assert_no_source_locator_leak(aggregate, bundle, [filename], "CANONICAL_REVIEWER_REJECTS_MALFORMED_RECEIPT")


def case_output_self_ingestion(root: Path) -> None:
    bundle = root / "self-ingestion"
    bundle.mkdir()
    output = bundle / "stage47-aggregate.json"
    first_code, first = run_orchestrator(bundle, output, "inventory")
    second_code, second = run_orchestrator(bundle, output, "inventory")
    for code, aggregate in ((first_code, first), (second_code, second)):
        if code != 0 or aggregate.get("overall_state") != "INCOMPLETE_MISSING_EXTERNAL_EVIDENCE":
            fail("OUTPUT_SELF_INGESTION changed empty inventory state")
        if aggregate.get("unknown_or_unreadable_json_receipt_count") != 0:
            fail("OUTPUT_SELF_INGESTION counted its own aggregate")
        assert_false_authority(aggregate, "OUTPUT_SELF_INGESTION")


def main() -> None:
    verify_authority()
    with tempfile.TemporaryDirectory(prefix="stage48-regression-") as temp:
        root = Path(temp)
        case_empty_inventory(root)
        case_empty_complete(root)
        case_stage35_masquerade(root)
        case_duplicate_source(root)
        case_canonical_reviewer_rejects(root)
        case_output_self_ingestion(root)

    print("STAGE48_UNIFIED_INTAKE_ADVERSARIAL_REGRESSION=PASS")
    print("ADVERSARIAL_CASES=6_PASS")
    print("REAL_EXTERNAL_EVIDENCE_USED=false")
    print("REAL_CUSTOMER_DATA_USED=false")
    print("NETWORK_CALL=false")
    print("SUPABASE_MUTATION=false")
    print("GATE_PROMOTION=false")


if __name__ == "__main__":
    main()
