from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
PLACEHOLDER_RE = re.compile(r"<[^>]+>|placeholder|tbd|to[_ -]?be[_ -]?defined|example", re.IGNORECASE)
FAILURE = "BGF-STAGE91-CONTROLLED-EXERCISE-INDEPENDENT-REVIEW-INTAKE-GUARD-901"
EXPECTED_DSR = {
    "DSR_ACCESS_EXPORT_SAME_TENANT",
    "DSR_CROSS_TENANT_FAIL_CLOSED",
    "DSR_AUDITED_CORRECTION",
    "DSR_DELETION_RETENTION_HANDOFF",
    "DSR_IDENTITY_INSUFFICIENT_PAUSE",
}
EXPECTED_INCIDENT = {
    "INCIDENT_CROSS_TENANT_EXPOSURE",
    "INCIDENT_CREDENTIAL_COMPROMISE",
    "INCIDENT_SENSITIVE_STUDENT_DATA",
}
EXPECTED = EXPECTED_DSR | EXPECTED_INCIDENT
DSR_REVIEW_KEYS = {
    "owner_backup_assignment_supported",
    "identity_verification_before_disclosure",
    "tenant_scoped_access_export_exercised",
    "correction_workflow_exercised",
    "deletion_retention_decision_path_exercised",
    "controller_operator_handoff_addressed",
    "response_time_policy_not_invented",
    "synthetic_non_customer_fixtures_only",
}
INCIDENT_REVIEW_KEYS = {
    "owner_assignment_supported",
    "risk_classification_human_decision_path_exercised",
    "operator_controller_handoff_exercised",
    "notification_decision_remained_human_legal_authority",
    "incident_evidence_retention_path_exercised",
    "three_required_scenarios_executed_synthetically",
    "postmortem_followup_recorded",
}


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE91_CONTROLLED_EXERCISE_INDEPENDENT_REVIEW_INTAKE=FAIL\n"
        f"FAILURE_CLASS={FAILURE}\nDETAIL={detail}"
    )


def load(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to load {label}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"{label} must be a JSON object")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def real_file(raw: object, label: str) -> Path:
    value = str(raw or "").strip()
    if not value or PLACEHOLDER_RE.search(value):
        fail(f"{label} path missing or placeholder")
    path = Path(value).expanduser().resolve()
    if not path.is_file() or path.stat().st_size <= 0:
        fail(f"{label} must be a real non-empty file")
    return path


def assert_real_record(value: dict, label: str) -> None:
    if value.get("test_fixture") is not False:
        fail(f"{label} must not be a test fixture")
    if value.get("contains_placeholders") is not False:
        fail(f"{label} declares placeholders")
    if PLACEHOLDER_RE.search(str(value.get("status", ""))):
        fail(f"{label} status remains placeholder-like")


def validate_session(path: Path) -> tuple[dict, str, dict[str, dict]]:
    session = load(path, "Stage69 session candidate")
    if session.get("schema_version") != 1:
        fail("Stage69 session schema drift")
    if session.get("stage") != "STAGE69_CONTROLLED_EXERCISE_EXECUTION_BOUNDARY":
        fail("Stage69 session stage drift")
    if session.get("output_kind") != "NON_ATTESTING_CONTROLLED_EXERCISE_SESSION_CANDIDATE":
        fail("Stage69 session output kind drift")
    if session.get("session_state") != "READY_FOR_HUMAN_CONTROLLED_EXERCISE_NOT_EXECUTED_NOT_EVIDENCE":
        fail("Stage69 session state drift")
    if session.get("exercise_executed") is not False:
        fail("Stage69 session must remain a pre-exercise candidate")
    if session.get("owner_identity_copied_to_receipt") is not False:
        fail("Stage69 session leaked owner identity")
    assignments = session.get("assignment_artifacts")
    if not isinstance(assignments, list) or len(assignments) != 6:
        fail("Stage69 session must contain six assignment artifact digests")
    for row in assignments:
        if not isinstance(row, dict) or not SHA256_RE.fullmatch(str(row.get("assignment_artifact_sha256", ""))):
            fail("Stage69 assignment artifact digest drift")
        if row.get("owner_identity_copied") is not False or row.get("assignment_artifact_path_copied") is not False:
            fail("Stage69 assignment privacy boundary drift")
    packets = session.get("packet_bindings")
    if not isinstance(packets, list) or len(packets) != 8:
        fail("Stage69 session must bind eight rehearsal packets")
    indexed: dict[str, dict] = {}
    for row in packets:
        if not isinstance(row, dict):
            fail("Stage69 packet binding must be an object")
        scenario_id = str(row.get("scenario_id", "")).strip()
        if not scenario_id or scenario_id in indexed:
            fail("Stage69 scenario id missing or duplicated")
        if row.get("kind") not in {"dsr", "incident"}:
            fail("Stage69 scenario kind drift")
        if not SHA256_RE.fullmatch(str(row.get("scenario_definition_sha256", ""))):
            fail("Stage69 scenario digest drift")
        indexed[scenario_id] = row
    if set(indexed) != EXPECTED:
        fail("Stage69 scenario set drift")
    return session, sha256_file(path), indexed


def validate_completion(path: Path, session_packets: dict[str, dict]) -> tuple[dict, str, dict[str, dict]]:
    record = load(path, "completed exercise record")
    if record.get("schema_version") != 1 or record.get("record_kind") != "REAL_CONTROLLED_EXERCISE_COMPLETION_RECORD":
        fail("completed exercise record identity drift")
    assert_real_record(record, "completed exercise record")
    if record.get("exercise_executed") is not True:
        fail("completed exercise record does not attest human execution")
    if record.get("real_customer_data_used") is not False:
        fail("real customer data is forbidden in controlled exercise")
    if record.get("production_secrets_used") is not False:
        fail("production secrets are forbidden in controlled exercise")
    results = record.get("scenario_results")
    if not isinstance(results, list) or len(results) != 8:
        fail("completed exercise record must contain eight scenario results")
    indexed: dict[str, dict] = {}
    for row in results:
        if not isinstance(row, dict):
            fail("scenario result must be object")
        scenario_id = str(row.get("scenario_id", "")).strip()
        if scenario_id in indexed or scenario_id not in session_packets:
            fail("scenario result id missing, duplicated or not Stage69-bound")
        if row.get("kind") != session_packets[scenario_id].get("kind"):
            fail(f"scenario kind drift:{scenario_id}")
        if row.get("completed") is not True:
            fail(f"scenario not completed:{scenario_id}")
        if str(row.get("outcome", "")).upper() not in {"PASS", "COMPLETED_WITH_FINDING"}:
            fail(f"unsupported scenario outcome:{scenario_id}")
        indexed[scenario_id] = row
    if set(indexed) != set(session_packets):
        fail("completed exercise coverage does not match Stage69 session")
    return record, sha256_file(path), indexed


def validate_review(path: Path, completion: dict[str, dict]) -> tuple[dict, str, int]:
    review = load(path, "independent review record")
    if review.get("schema_version") != 1 or review.get("record_kind") != "REAL_INDEPENDENT_CONTROLLED_EXERCISE_REVIEW":
        fail("independent review record identity drift")
    assert_real_record(review, "independent review record")
    if review.get("review_completed") is not True:
        fail("independent review is not complete")
    if review.get("reviewer_is_automated_ci") is not False:
        fail("automated CI cannot be the independent reviewer")
    if review.get("review_scope_dsr") is not True or review.get("review_scope_incident") is not True:
        fail("independent review must cover both DSR and incident exercises")

    findings = review.get("scenario_findings")
    if not isinstance(findings, list) or len(findings) != 8:
        fail("independent review must contain eight scenario findings")
    seen: set[str] = set()
    unresolved = 0
    for row in findings:
        if not isinstance(row, dict):
            fail("review scenario finding must be object")
        scenario_id = str(row.get("scenario_id", "")).strip()
        if scenario_id in seen or scenario_id not in completion:
            fail("review scenario id missing, duplicated or not completed")
        if row.get("reviewed") is not True:
            fail(f"scenario was not independently reviewed:{scenario_id}")
        status = str(row.get("status", "")).upper()
        if status not in {"PASS", "UNRESOLVED"}:
            fail(f"unsupported review status:{scenario_id}")
        if status == "UNRESOLVED":
            unresolved += 1
        seen.add(scenario_id)
    if seen != set(completion):
        fail("independent review scenario coverage mismatch")

    dsr = review.get("dsr_review_findings")
    incident = review.get("incident_review_findings")
    if not isinstance(dsr, dict) or set(dsr) != DSR_REVIEW_KEYS:
        fail("DSR review finding key set drift")
    if not isinstance(incident, dict) or set(incident) != INCIDENT_REVIEW_KEYS:
        fail("incident review finding key set drift")
    for key, value in {**dsr, **incident}.items():
        if value not in {True, False}:
            fail(f"review finding must be boolean:{key}")
        if value is False:
            unresolved += 1
    return review, sha256_file(path), unresolved


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--intake-input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    source_sha = args.source_sha.strip().lower()
    if SHA1_RE.fullmatch(source_sha) is None:
        fail("--source-sha must be a 40-character lower-hex Git SHA")

    intake = load(args.intake_input.resolve(), "Stage91 intake input")
    if intake.get("schema_version") != 1 or intake.get("input_kind") != "REAL_CONTROLLED_EXERCISE_REVIEW_INPUT":
        fail("Stage91 intake input identity drift")
    assert_real_record(intake, "Stage91 intake input")

    session_path = real_file(intake.get("stage69_session_candidate_path"), "Stage69 session candidate")
    completion_path = real_file(intake.get("completed_exercise_record_path"), "completed exercise record")
    review_path = real_file(intake.get("independent_review_record_path"), "independent review record")
    reviewer_authority_path = real_file(intake.get("reviewer_authority_artifact_path"), "reviewer authority artifact")

    session, session_sha, session_packets = validate_session(session_path)
    _completion_record, completion_sha, completion = validate_completion(completion_path, session_packets)
    _review_record, review_sha, unresolved = validate_review(review_path, completion)
    reviewer_authority_sha = sha256_file(reviewer_authority_path)

    result = {
        "schema_version": 1,
        "stage": "STAGE91_CONTROLLED_EXERCISE_INDEPENDENT_REVIEW_INTAKE",
        "output_kind": "DIGEST_ONLY_CONTROLLED_EXERCISE_INDEPENDENT_REVIEW_CANDIDATE",
        "candidate_state": (
            "READY_FOR_SEPARATE_EVIDENCE_REVIEW_NOT_GATE_EVIDENCE"
            if unresolved == 0
            else "STRUCTURALLY_COLLECTED_WITH_UNRESOLVED_FINDINGS_GATE_DENIED"
        ),
        "source_commit_sha": source_sha,
        "stage69_session_sha256": session_sha,
        "completed_exercise_record_sha256": completion_sha,
        "independent_review_record_sha256": review_sha,
        "reviewer_authority_artifact_sha256": reviewer_authority_sha,
        "stage68_bundle_sha256": session.get("stage68_bundle_sha256"),
        "scenario_count": 8,
        "dsr_scenario_count": 5,
        "incident_scenario_count": 3,
        "exercise_executed": True,
        "independent_review_completed": True,
        "unresolved_findings_count": unresolved,
        "real_customer_data_used": False,
        "production_secrets_used": False,
        "owner_identity_copied": False,
        "reviewer_identity_copied": False,
        "artifact_path_or_filename_copied": False,
        "raw_artifact_content_copied": False,
        "stage44_evidence_attested": False,
        "stage45_evidence_attested": False,
        "evidence_ref_created": False,
        "evidence_digest_promoted": False,
        "evidence_migration_created": False,
        "data_subject_request_gate_ready_attested": False,
        "incident_response_gate_ready_attested": False,
        "controlled_launch_promoted": False,
        "paid_media_promoted": False,
        "next_action": "INDEPENDENTLY_INSPECT_SOURCE_ARTIFACTS_AND_RESOLVE_ALL_FINDINGS_BEFORE_ANY_STAGE44_OR_STAGE45_EVIDENCE_CANDIDATE",
    }

    args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.output.resolve().write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("STAGE91_CONTROLLED_EXERCISE_INDEPENDENT_REVIEW_INTAKE=PASS_CANDIDATE_ONLY")
    print("EXERCISE_EXECUTED=true")
    print("INDEPENDENT_REVIEW_COMPLETED=true")
    print(f"UNRESOLVED_FINDINGS={unresolved}")
    print("OWNER_IDENTITY_COPIED=false")
    print("REVIEWER_IDENTITY_COPIED=false")
    print("STAGE44_EVIDENCE=false")
    print("STAGE45_EVIDENCE=false")
    print("GATE_READY=false")


if __name__ == "__main__":
    main()
