from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
DRAFTS = ROOT / "10_compliance" / "drafts"
AUTHORITY = BACKEND / "stage67_compliance_operations_candidate_pack_authority.json"
PLACEHOLDERS = BACKEND / "external_gate_evidence_placeholders.json"
STAGE45 = BACKEND / "stage45_incident_response_external_evidence_preparation_authority.json"
STAGE66 = BACKEND / "stage66_production_release_candidate_evidence_pipeline_authority.json"
OPEN_DECISIONS = DRAFTS / "COMPLIANCE_OPEN_DECISIONS.json"

BASELINE_MAIN = "90653a6df4efc497f196ddd1ff482fe8082911c0"
PLACEHOLDER_BLOB = "07e6eb3330076f3e576ed2dd2a2e385f5fa3b2db"
STAGE45_BLOB = "d5d32990e8ef7a3c4f13dc63e2088ea28e471f12"
STAGE66_BLOB = "8f3be15da1027d9a5bed6e7d1f43cefebcf6a9eb"
FAILURE_CLASS = "BGF-STAGE67-COMPLIANCE-CANDIDATE-PACK-GUARD-645"

DOCS = {
    "privacy": DRAFTS / "PRIVACY_NOTICE_CANDIDATE_PTBR.md",
    "terms": DRAFTS / "TERMS_OF_USE_CANDIDATE_PTBR.md",
    "roles": DRAFTS / "PROCESSING_ROLE_MATRIX_CANDIDATE.md",
    "dsr": DRAFTS / "DATA_SUBJECT_REQUEST_RUNBOOK_CANDIDATE.md",
    "incident": DRAFTS / "INCIDENT_RESPONSE_RUNBOOK_CANDIDATE.md",
}


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE67_COMPLIANCE_OPERATIONS_CANDIDATE_PACK=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\n"
        f"DETAIL={detail}"
    )


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to load {path.relative_to(ROOT)}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"expected JSON object: {path.relative_to(ROOT)}")
    return value


def git_blob(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def require(mapping: dict, expected: dict, label: str) -> None:
    if not isinstance(mapping, dict):
        fail(f"{label} must be object")
    for key, value in expected.items():
        if mapping.get(key) != value:
            fail(f"{label} drift: {key}")


def read_doc(name: str) -> str:
    path = DOCS[name]
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"unable to read {path.relative_to(ROOT)}: {type(exc).__name__}")
    if len(text.strip()) < 500:
        fail(f"candidate document unexpectedly empty: {path.relative_to(ROOT)}")
    return text


def main() -> None:
    authority = load(AUTHORITY)
    placeholders = load(PLACEHOLDERS)
    stage45 = load(STAGE45)
    stage66 = load(STAGE66)
    open_decisions = load(OPEN_DECISIONS)

    if git_blob(PLACEHOLDERS) != PLACEHOLDER_BLOB:
        fail("external gate placeholder blob drift")
    if git_blob(STAGE45) != STAGE45_BLOB:
        fail("Stage45 incident preparation blob drift")
    if git_blob(STAGE66) != STAGE66_BLOB:
        fail("Stage66 release-candidate authority blob drift")

    require(
        authority,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "stage": "STAGE67_COMPLIANCE_OPERATIONS_CANDIDATE_PACK",
            "baseline_main_sha": BASELINE_MAIN,
            "current_state": "UNREVIEWED_COMPLIANCE_AND_OPERATIONS_CANDIDATES_PREPARED_OPEN_DECISIONS_EXPLICIT_NO_PUBLICATION_NO_GATE_PROMOTION",
        },
        "Stage67 authority",
    )

    required_gates = {
        "legal_privacy_notice",
        "legal_terms_of_use",
        "legal_role_mapping",
        "data_subject_request_channel",
        "incident_response",
    }
    placeholder_gates = placeholders.get("gates", {})
    if not required_gates.issubset(set(placeholder_gates)):
        fail("required compliance/operations gates missing from placeholder authority")
    for gate in required_gates:
        item = placeholder_gates.get(gate, {})
        if item.get("placeholder_only") is not True or item.get("evidence_ref") is not None or item.get("evidence_digest") is not None:
            fail(f"placeholder authority unexpectedly attests gate: {gate}")

    if stage45.get("gates", {}).get("incident_response") != "DENIED_AWAITING_REAL_GOVERNANCE_AND_CONTROLLED_TABLETOP_EVIDENCE":
        fail("Stage45 incident-response denied boundary drift")
    if stage66.get("gates", {}).get("production_deployment") != "DENIED_AWAITING_REAL_PRODUCTION_RELEASE_AND_OPERATIONS_EVIDENCE":
        fail("Stage66 production-deployment denied boundary drift")

    texts = {name: read_doc(name) for name in DOCS}
    lowered = {name: text.lower() for name, text in texts.items()}

    status_requirements = {
        "privacy": "draft_unreviewed_not_published_not_legal_evidence",
        "terms": "draft_unreviewed_not_published_not_legal_evidence",
        "roles": "draft_unreviewed_not_legal_evidence",
        "dsr": "draft_unreviewed_not_operational_evidence",
        "incident": "draft_unreviewed_not_operational_evidence",
    }
    for name, marker in status_requirements.items():
        if marker not in lowered[name]:
            fail(f"candidate status marker missing: {name}")

    for name, text in lowered.items():
        if "gate" not in text or "blocked" not in text:
            fail(f"candidate does not preserve blocked gate language: {name}")
        if "projetoscosanostra@gmail.com" not in text and name in {"privacy", "terms", "dsr"}:
            fail(f"official contact candidate missing: {name}")

    if "preencher após revisão jurídica" not in lowered["privacy"] or "preencher após revisão jurídica" not in lowered["terms"]:
        fail("unknown legal entity was not preserved as an explicit placeholder")
    if re.search(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b", texts["privacy"] + texts["terms"]):
        fail("candidate unexpectedly contains a CNPJ-like value")

    for phrase in (
        "selected_pending_credentials",
        "não devem ser congelados por este candidato jurídico",
    ):
        if phrase.lower() not in lowered["terms"]:
            fail(f"terms candidate authority boundary missing: {phrase}")

    for phrase in (
        "hipótese",
        "não conclusão jurídica",
        "legal_role_mapping = blocked",
    ):
        if phrase.lower() not in lowered["roles"]:
            fail(f"role-matrix hypothesis boundary missing: {phrase}")

    for phrase in (
        "não usar customer data em testes/tabletops",
        "tabletop obrigatório antes do gate",
        "data_subject_request_channel = blocked",
    ):
        if phrase.lower() not in lowered["dsr"]:
            fail(f"DSR fail-closed boundary missing: {phrase}")

    for phrase in (
        "o script/ci não pode auto-concluir",
        "somente dados sintéticos/non-customer",
        "incident_response = blocked",
    ):
        if phrase.lower() not in lowered["incident"]:
            fail(f"incident-response fail-closed boundary missing: {phrase}")

    require(
        open_decisions,
        {
            "schema_version": 1,
            "status": "DRAFT_UNREVIEWED_NOT_EVIDENCE",
            "project": "FitNexus Coach BlackGold",
            "official_contact_candidate": "projetoscosanostra@gmail.com",
        },
        "open decisions",
    )
    unresolved = open_decisions.get("unresolved")
    if not isinstance(unresolved, list) or len(unresolved) < 12:
        fail("open decision inventory is unexpectedly incomplete")
    ids: set[str] = set()
    for item in unresolved:
        if not isinstance(item, dict) or item.get("state") != "OPEN":
            fail("all unresolved decisions must remain OPEN")
        item_id = str(item.get("id", ""))
        if not item_id or item_id in ids:
            fail("open decision id missing or duplicated")
        ids.add(item_id)

    require(
        open_decisions.get("hard_boundaries", {}),
        {
            "can_mark_any_gate_ready": False,
            "can_create_evidence_ref": False,
            "can_create_evidence_digest": False,
            "can_replace_legal_review": False,
            "can_replace_operational_test": False,
            "can_trigger_evidence_migration": False,
            "controlled_launch_promoted": False,
            "paid_media_promoted": False,
        },
        "open decision hard boundaries",
    )

    require(
        authority.get("candidate_contract", {}),
        {
            "all_documents_must_be_explicitly_unreviewed": True,
            "all_documents_must_deny_gate_promotion": True,
            "unknown_legal_entity_must_remain_placeholder": True,
            "unknown_legal_deadlines_must_not_be_invented": True,
            "pricing_experiment_must_not_become_legal_price_commitment": True,
            "asaas_must_remain_pending_until_real_activation": True,
            "controller_processor_mapping_must_remain_hypothesis_until_review": True,
            "sensitive_data_ad_targeting_prohibited": True,
            "real_customer_data_allowed_in_tests": False,
            "drafts_can_be_published_as_official": False,
            "drafts_can_be_used_as_evidence_ref": False,
            "drafts_can_be_used_as_evidence_digest": False,
            "drafts_can_create_evidence_migration": False,
            "supabase_mutation_allowed": False,
            "provider_call_allowed": False,
            "deployment_action_allowed": False,
            "controlled_launch_promotion_allowed": False,
            "paid_media_promotion_allowed": False,
        },
        "candidate contract",
    )

    if list((BACKEND / "migrations").glob("*stage67*.sql")):
        fail("Stage67 candidate pack must not create an evidence migration")

    print("STAGE67_COMPLIANCE_OPERATIONS_CANDIDATE_PACK=PASS")
    print("DRAFTS=UNREVIEWED_NOT_PUBLISHED_NOT_EVIDENCE")
    print("LEGAL_PRIVACY_NOTICE_GATE=BLOCKED")
    print("LEGAL_TERMS_GATE=BLOCKED")
    print("LEGAL_ROLE_MAPPING_GATE=BLOCKED")
    print("DSR_GATE=BLOCKED")
    print("INCIDENT_RESPONSE_GATE=BLOCKED")
    print("REMOTE_MUTATION=false")
    print("CONTROLLED_LAUNCH=DENIED")


if __name__ == "__main__":
    main()
