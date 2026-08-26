from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage74_controller_processor_independent_review_intake_authority.json"
STAGE73 = BACKEND / "stage73_cross_gate_decision_frontier_authority.json"
DECISIONS = ROOT / "10_compliance" / "drafts" / "COMPLIANCE_OPEN_DECISIONS.json"
QUESTIONNAIRE = ROOT / "10_compliance" / "review" / "STAGE74_CONTROLLER_PROCESSOR_REVIEW_QUESTIONNAIRE.md"
INPUT_TEMPLATE = ROOT / "10_compliance" / "review" / "STAGE74_INDEPENDENT_REVIEW_INPUT_TEMPLATE.json"
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
FAILURE_CLASS = "BGF-STAGE74-INDEPENDENT-REVIEW-INTAKE-GUARD-715"

SOURCES = {
    "privacy_notice": ROOT / "10_compliance" / "drafts" / "PRIVACY_NOTICE_CANDIDATE_PTBR.md",
    "processing_role_matrix": ROOT / "10_compliance" / "drafts" / "PROCESSING_ROLE_MATRIX_CANDIDATE.md",
    "dsr_runbook": ROOT / "10_compliance" / "drafts" / "DATA_SUBJECT_REQUEST_RUNBOOK_CANDIDATE.md",
    "incident_runbook": ROOT / "10_compliance" / "drafts" / "INCIDENT_RESPONSE_RUNBOOK_CANDIDATE.md",
    "open_decisions": DECISIONS,
}
EXPECTED_MARKERS = {
    "privacy_notice": "DRAFT_UNREVIEWED_NOT_PUBLISHED_NOT_LEGAL_EVIDENCE",
    "processing_role_matrix": "DRAFT_UNREVIEWED_NOT_LEGAL_EVIDENCE",
    "dsr_runbook": "DRAFT_UNREVIEWED_NOT_OPERATIONAL_EVIDENCE",
    "incident_runbook": "DRAFT_UNREVIEWED_NOT_OPERATIONAL_EVIDENCE",
}
EXPECTED_AFFECTED_GATES = [
    "data_subject_request_channel",
    "incident_response",
    "legal_privacy_notice",
    "legal_role_mapping",
]


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE74_CONTROLLER_PROCESSOR_REVIEW_PACKET=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\n"
        f"DETAIL={detail}"
    )


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to load {path.relative_to(ROOT)}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"expected JSON object: {path.relative_to(ROOT)}")
    return value


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_sources() -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for key, path in SOURCES.items():
        if key == "open_decisions":
            value = load_json(path)
            if value.get("status") != "DRAFT_UNREVIEWED_NOT_EVIDENCE":
                fail("open-decision registry no longer has unreviewed status")
            marker = "DRAFT_UNREVIEWED_NOT_EVIDENCE"
        else:
            try:
                text = path.read_text(encoding="utf-8")
            except OSError as exc:
                fail(f"unable to read {path.relative_to(ROOT)}: {type(exc).__name__}")
            marker = EXPECTED_MARKERS[key]
            if marker not in text:
                fail(f"candidate source status marker drift: {key}")
        result[key] = {
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha256_file(path),
            "status_marker": marker,
            "approved": False,
            "published": False if key == "privacy_notice" else False,
            "gate_evidence": False,
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    source_sha = args.source_sha.strip().lower()
    if not SHA1_RE.fullmatch(source_sha):
        fail("--source-sha must be exact 40-character lower-hex Git SHA")

    authority = load_json(AUTHORITY)
    stage73 = load_json(STAGE73)
    decisions = load_json(DECISIONS)
    template = load_json(INPUT_TEMPLATE)

    if authority.get("stage") != "STAGE74_CONTROLLER_PROCESSOR_INDEPENDENT_REVIEW_INTAKE":
        fail("Stage74 authority drift")
    scope = authority.get("review_scope")
    if not isinstance(scope, dict):
        fail("Stage74 review scope missing")
    if scope.get("decision_id") != "CONTROLLER_PROCESSOR_ROLE_MATRIX" or scope.get("fanout_count") != 4:
        fail("Stage74 review scope decision/fanout drift")
    if sorted(scope.get("affected_external_gates", [])) != EXPECTED_AFFECTED_GATES:
        fail("Stage74 affected external gate set drift")

    stage73_contract = stage73.get("frontier_contract", {})
    if stage73_contract.get("top_shared_decision_expected") != "CONTROLLER_PROCESSOR_ROLE_MATRIX":
        fail("Stage73 top shared decision drift")
    if stage73_contract.get("top_shared_decision_expected_fanout") != 4:
        fail("Stage73 top shared decision fanout drift")

    unresolved = decisions.get("unresolved")
    if not isinstance(unresolved, list):
        fail("open-decision registry unresolved array missing")
    target = next((item for item in unresolved if isinstance(item, dict) and item.get("id") == "CONTROLLER_PROCESSOR_ROLE_MATRIX"), None)
    if not isinstance(target, dict) or target.get("state") != "OPEN":
        fail("CONTROLLER_PROCESSOR_ROLE_MATRIX must remain OPEN")
    if sorted(target.get("applies_to", [])) != EXPECTED_AFFECTED_GATES:
        fail("target decision applies_to drift")
    if target.get("resolution_authority") != "independent legal/privacy review":
        fail("target decision resolution authority drift")

    try:
        questionnaire_text = QUESTIONNAIRE.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"questionnaire unreadable: {type(exc).__name__}")
    for marker in (
        "NON_ATTESTING_REVIEW_INTAKE_QUESTIONNAIRE_NOT_LEGAL_EVIDENCE",
        "APPROVED_WITHOUT_CHANGES",
        "APPROVED_WITH_REQUIRED_CHANGES",
        "NOT_APPROVED_REQUIRES_REVISION",
        "não fecha automaticamente nenhum gate",
    ):
        if marker not in questionnaire_text:
            fail(f"questionnaire boundary marker missing: {marker}")

    if template.get("input_kind") != "REAL_INDEPENDENT_CONTROLLER_PROCESSOR_REVIEW_INPUT":
        fail("review input template kind drift")
    if template.get("test_fixture") is not True or template.get("contains_placeholders") is not True:
        fail("committed review input template must remain an invalid placeholder fixture")
    if template.get("status") != "PLACEHOLDER_TEMPLATE_NOT_REAL_REVIEW":
        fail("committed review input template status drift")

    sources = validate_sources()
    packet = {
        "schema_version": 1,
        "stage": "STAGE74_CONTROLLER_PROCESSOR_INDEPENDENT_REVIEW_INTAKE",
        "output_kind": "NON_ATTESTING_INDEPENDENT_REVIEW_INTAKE_PACKET",
        "packet_state": "EXACT_DRAFT_BYTES_BOUND_FOR_EXTERNAL_REVIEW_NO_REVIEW_PERFORMED_NOT_EVIDENCE",
        "source_commit_sha": source_sha,
        "decision": {
            "decision_id": target["id"],
            "state": target["state"],
            "required": target.get("required"),
            "resolution_authority": target.get("resolution_authority"),
            "fanout_count": 4,
            "affected_external_gates": EXPECTED_AFFECTED_GATES,
            "resolved": False,
        },
        "review_sources": sources,
        "questionnaire": {
            "path": str(QUESTIONNAIRE.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha256_file(QUESTIONNAIRE),
            "legal_conclusion_present": False,
            "gate_evidence": False,
        },
        "external_review_input_template": {
            "path": str(INPUT_TEMPLATE.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha256_file(INPUT_TEMPLATE),
            "placeholder_only": True,
            "real_review_input_present": False,
        },
        "allowed_real_review_outcomes": [
            "APPROVED_WITHOUT_CHANGES",
            "APPROVED_WITH_REQUIRED_CHANGES",
            "NOT_APPROVED_REQUIRES_REVISION",
        ],
        "real_reviewer_reference_present": False,
        "real_review_artifact_present": False,
        "independent_review_completed": False,
        "candidate_documents_promoted": False,
        "open_decision_closed": False,
        "evidence_ref_created": False,
        "evidence_digest_promoted": False,
        "evidence_migration_created": False,
        "gate_ready_attested": False,
        "network_call_performed": False,
        "provider_call_performed": False,
        "supabase_mutation_performed": False,
        "deployment_performed": False,
        "controlled_launch_promoted": False,
        "paid_media_promoted": False,
        "next_action": "REAL_EXTERNAL_INDEPENDENT_REVIEW_OF_EXACT_BOUND_BYTES_REQUIRED",
    }

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(packet, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

    print("STAGE74_CONTROLLER_PROCESSOR_REVIEW_PACKET=PASS_NON_ATTESTING")
    print("DECISION=CONTROLLER_PROCESSOR_ROLE_MATRIX")
    print("FANOUT=4")
    print(f"REVIEW_SOURCE_COUNT={len(sources)}")
    print("REAL_REVIEW_PRESENT=false")
    print("CANDIDATE_DOCUMENTS_PROMOTED=false")
    print("GATE_READY=false")
    print("REMOTE_MUTATION=false")


if __name__ == "__main__":
    main()
