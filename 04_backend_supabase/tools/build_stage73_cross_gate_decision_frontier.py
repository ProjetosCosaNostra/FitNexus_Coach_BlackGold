from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage73_cross_gate_decision_frontier_authority.json"
STAGE72 = BACKEND / "stage72_external_readiness_dashboard_authority.json"
OPEN_DECISIONS = ROOT / "10_compliance" / "drafts" / "COMPLIANCE_OPEN_DECISIONS.json"
CANDIDATE_DOCS = {
    "privacy_notice": ROOT / "10_compliance" / "drafts" / "PRIVACY_NOTICE_CANDIDATE_PTBR.md",
    "terms_of_use": ROOT / "10_compliance" / "drafts" / "TERMS_OF_USE_CANDIDATE_PTBR.md",
    "processing_role_matrix": ROOT / "10_compliance" / "drafts" / "PROCESSING_ROLE_MATRIX_CANDIDATE.md",
    "dsr_runbook": ROOT / "10_compliance" / "drafts" / "DATA_SUBJECT_REQUEST_RUNBOOK_CANDIDATE.md",
    "incident_runbook": ROOT / "10_compliance" / "drafts" / "INCIDENT_RESPONSE_RUNBOOK_CANDIDATE.md",
}
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
FAILURE_CLASS = "BGF-STAGE73-CROSS-GATE-FRONTIER-GUARD-705"

EXPECTED_DOC_MARKERS = {
    "privacy_notice": "DRAFT_UNREVIEWED_NOT_PUBLISHED_NOT_LEGAL_EVIDENCE",
    "terms_of_use": "DRAFT_UNREVIEWED_NOT_PUBLISHED_NOT_LEGAL_EVIDENCE",
    "processing_role_matrix": "DRAFT_UNREVIEWED_NOT_LEGAL_EVIDENCE",
    "dsr_runbook": "DRAFT_UNREVIEWED_NOT_OPERATIONAL_EVIDENCE",
    "incident_runbook": "DRAFT_UNREVIEWED_NOT_OPERATIONAL_EVIDENCE",
}


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE73_CROSS_GATE_DECISION_FRONTIER=FAIL\n"
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


def validate_candidate_documents() -> dict[str, str]:
    digests: dict[str, str] = {}
    for key, path in CANDIDATE_DOCS.items():
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            fail(f"unable to read candidate document {path.relative_to(ROOT)}: {type(exc).__name__}")
        marker = EXPECTED_DOC_MARKERS[key]
        if marker not in text:
            fail(f"candidate document no longer preserves unreviewed marker: {key}")
        digests[key] = sha256_file(path)
    return digests


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    source_sha = args.source_sha.strip().lower()
    if not SHA1_RE.fullmatch(source_sha):
        fail("--source-sha must be exact 40-character lower-hex Git SHA")

    authority = load_json(AUTHORITY)
    stage72 = load_json(STAGE72)
    decisions = load_json(OPEN_DECISIONS)

    if authority.get("stage") != "STAGE73_CROSS_GATE_DECISION_FRONTIER":
        fail("Stage73 authority drift")
    contract = authority.get("frontier_contract")
    if not isinstance(contract, dict):
        fail("Stage73 frontier contract missing")
    if contract.get("ranking_metric") != "decision_gate_fanout_count_only":
        fail("Stage73 ranking metric drift")
    if contract.get("ranking_order") != "fanout_desc_then_decision_id_asc":
        fail("Stage73 ranking order drift")

    stage72_contract = stage72.get("dashboard_contract")
    if not isinstance(stage72_contract, dict):
        fail("Stage72 dashboard contract missing")
    gate_order = stage72_contract.get("gate_order")
    if not isinstance(gate_order, list) or len(gate_order) != 7 or len(set(gate_order)) != 7:
        fail("Stage72 must define seven unique external gates")
    gate_set = set(gate_order)

    for gate in gate_order:
        state = authority.get("gates", {}).get(gate)
        if not isinstance(state, str) or not state.startswith("DENIED_"):
            fail(f"external gate no longer has denied state: {gate}")

    unresolved = decisions.get("unresolved")
    if decisions.get("status") != "DRAFT_UNREVIEWED_NOT_EVIDENCE" or not isinstance(unresolved, list):
        fail("Stage67 open-decision registry boundary drift")
    if len(unresolved) != 14:
        fail("Stage67 open-decision count drift; expected exactly 14")

    doc_digests = validate_candidate_documents()
    ranked: list[dict] = []
    gate_decision_ids: dict[str, list[str]] = {gate: [] for gate in gate_order}
    seen_ids: set[str] = set()

    for item in unresolved:
        if not isinstance(item, dict) or item.get("state") != "OPEN":
            fail("every Stage67 decision must remain an OPEN object")
        decision_id = str(item.get("id", "")).strip()
        applies = item.get("applies_to")
        required = item.get("required")
        resolution_authority = item.get("resolution_authority")
        if not decision_id or decision_id in seen_ids:
            fail(f"missing or duplicate decision id: {decision_id}")
        seen_ids.add(decision_id)
        if not isinstance(applies, list) or not applies:
            fail(f"decision applies_to missing: {decision_id}")
        if not isinstance(required, str) or not required.strip():
            fail(f"decision required text missing: {decision_id}")
        if not isinstance(resolution_authority, str) or not resolution_authority.strip():
            fail(f"decision resolution authority missing: {decision_id}")

        external_gates = sorted({str(gate) for gate in applies if gate in gate_set})
        if not external_gates:
            fail(f"decision has no Stage72 external-gate alignment: {decision_id}")
        for gate in external_gates:
            gate_decision_ids[gate].append(decision_id)

        ranked.append(
            {
                "decision_id": decision_id,
                "state": "OPEN",
                "fanout_count": len(external_gates),
                "affected_external_gates": external_gates,
                "required": required,
                "resolution_authority": resolution_authority,
                "fanout_is_business_priority": False,
                "fanout_is_legal_priority": False,
                "decision_resolved": False,
                "evidence_created": False,
            }
        )

    ranked.sort(key=lambda row: (-int(row["fanout_count"]), str(row["decision_id"])))
    if not ranked:
        fail("decision ranking unexpectedly empty")
    top = ranked[0]
    if top["decision_id"] != contract.get("top_shared_decision_expected"):
        fail("top shared decision drift")
    if top["fanout_count"] != contract.get("top_shared_decision_expected_fanout"):
        fail("top shared decision fanout drift")

    gate_frontier = []
    zero_decision_gates = []
    for gate in gate_order:
        ids = sorted(gate_decision_ids[gate])
        if not ids:
            zero_decision_gates.append(gate)
        gate_frontier.append(
            {
                "gate_code": gate,
                "state": authority["gates"][gate],
                "open_decision_count": len(ids),
                "open_decision_ids": ids,
                "ready": False,
                "zero_open_decisions_means_ready": False,
            }
        )

    expected_zero = {"billing_provider_credentials", "production_deployment"}
    if set(zero_decision_gates) != expected_zero:
        fail(f"zero-decision external gate set drift: {sorted(zero_decision_gates)}")

    top_affected = set(top["affected_external_gates"])
    expected_top_affected = {
        "legal_privacy_notice",
        "legal_role_mapping",
        "data_subject_request_channel",
        "incident_response",
    }
    if top_affected != expected_top_affected:
        fail("CONTROLLER_PROCESSOR_ROLE_MATRIX affected-gate set drift")

    frontier_packet = {
        "decision_id": top["decision_id"],
        "fanout_count": top["fanout_count"],
        "affected_external_gates": list(top["affected_external_gates"]),
        "required": top["required"],
        "resolution_authority": top["resolution_authority"],
        "candidate_documents_for_coherent_review": [
            "10_compliance/drafts/PRIVACY_NOTICE_CANDIDATE_PTBR.md",
            "10_compliance/drafts/PROCESSING_ROLE_MATRIX_CANDIDATE.md",
            "10_compliance/drafts/DATA_SUBJECT_REQUEST_RUNBOOK_CANDIDATE.md",
            "10_compliance/drafts/INCIDENT_RESPONSE_RUNBOOK_CANDIDATE.md",
            "10_compliance/drafts/COMPLIANCE_OPEN_DECISIONS.json",
        ],
        "real_reviewer_reference_present": False,
        "independent_review_completed": False,
        "legal_conclusion_present": False,
        "candidate_document_digests_are_approval_digests": False,
        "packet_is_evidence": False,
        "packet_can_close_gate": False,
    }

    output_value = {
        "schema_version": 1,
        "stage": "STAGE73_CROSS_GATE_DECISION_FRONTIER",
        "output_kind": "NON_ATTESTING_CROSS_GATE_DECISION_FRONTIER",
        "frontier_state": "OPEN_DECISIONS_RANKED_BY_CROSS_GATE_FANOUT_NOT_PRIORITY_NOT_EVIDENCE",
        "source_commit_sha": source_sha,
        "source_sha256": {
            "stage73_authority": sha256_file(AUTHORITY),
            "stage72_authority": sha256_file(STAGE72),
            "stage67_open_decisions": sha256_file(OPEN_DECISIONS),
            "candidate_documents": doc_digests,
        },
        "ranking": {
            "metric": "decision_gate_fanout_count_only",
            "order": "fanout_desc_then_decision_id_asc",
            "is_business_priority": False,
            "is_legal_priority": False,
            "is_launch_authority": False,
            "open_decision_count": len(ranked),
            "shared_decision_count": sum(1 for row in ranked if int(row["fanout_count"]) > 1),
            "ranked_decisions": ranked,
        },
        "gate_frontier": gate_frontier,
        "zero_open_decision_external_gates": zero_decision_gates,
        "zero_decision_gate_warning": "ZERO_STAGE67_DECISIONS_DOES_NOT_MEAN_GATE_READY",
        "highest_fanout_review_packet": frontier_packet,
        "fresh_remote_read_only_receipt": dict(authority.get("fresh_remote_read_only_receipt", {})),
        "guardrails": {
            "candidate_documents_remain_unreviewed": True,
            "candidate_digests_are_not_approval_digests": True,
            "review_packet_is_not_evidence": True,
            "dashboard_or_frontier_can_mark_gate_ready": False,
            "evidence_ref_created": False,
            "evidence_digest_created": False,
            "evidence_migration_created": False,
            "network_call_performed": False,
            "provider_call_performed": False,
            "supabase_mutation_performed": False,
            "deployment_performed": False,
            "controlled_launch_promoted": False,
            "paid_media_promoted": False,
        },
        "next_action": "REAL_INDEPENDENT_REVIEW_REFERENCE_REQUIRED_FOR_HIGHEST_FANOUT_DECISION_PACKET",
    }

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(output_value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

    print("STAGE73_CROSS_GATE_DECISION_FRONTIER=PASS_NON_ATTESTING")
    print(f"OPEN_DECISIONS={len(ranked)}")
    print(f"SHARED_DECISIONS={output_value['ranking']['shared_decision_count']}")
    print(f"TOP_DECISION={top['decision_id']}")
    print(f"TOP_FANOUT={top['fanout_count']}")
    print(f"ZERO_DECISION_GATES={','.join(zero_decision_gates)}")
    print("GATE_READY=false")
    print("REMOTE_MUTATION=false")


if __name__ == "__main__":
    main()
