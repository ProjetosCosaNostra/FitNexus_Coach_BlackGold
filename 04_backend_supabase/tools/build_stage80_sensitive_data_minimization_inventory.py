from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage80_sensitive_data_minimization_inventory_authority.json"
REGISTRY = ROOT / "10_compliance" / "inventory" / "STAGE80_TECHNICAL_SENSITIVE_DATA_MINIMIZATION_REGISTRY.json"
OPEN_DECISIONS = ROOT / "10_compliance" / "drafts" / "COMPLIANCE_OPEN_DECISIONS.json"
ROLE_MATRIX = ROOT / "10_compliance" / "drafts" / "PROCESSING_ROLE_MATRIX_CANDIDATE.md"
PRIVACY = ROOT / "10_compliance" / "drafts" / "PRIVACY_NOTICE_CANDIDATE_PTBR.md"
INCIDENT = ROOT / "10_compliance" / "drafts" / "INCIDENT_RESPONSE_RUNBOOK_CANDIDATE.md"
MIGRATIONS = BACKEND / "migrations"
FAILURE_CLASS = "BGF-STAGE80-SENSITIVE-DATA-MINIMIZATION-GUARD-775"
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")

EXPECTED_TABLE_SURFACE_IDS = [
    "student_profile_objective_and_context",
    "training_prescription_notes_and_lineage",
    "workout_feedback_pain_energy_and_notes",
    "decision_intelligence_context_and_outcomes",
    "coach_action_notes",
    "student_access_security_identifiers_and_alerts",
    "growth_attribution_and_marketing_boundary",
]
EXPECTED_NON_TABLE_IDS = [
    "support_and_dsr_free_form_ingress",
    "incident_response_sensitive_data_handling",
]


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE80_SENSITIVE_DATA_MINIMIZATION_INVENTORY=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\n"
        f"DETAIL={detail}"
    )


def load_json(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to load {label}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"{label} must be a JSON object")
    return value


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    try:
        return sha256_bytes(path.read_bytes())
    except OSError as exc:
        fail(f"unable to hash {path.relative_to(ROOT)}: {type(exc).__name__}")


def migration_corpus() -> tuple[list[Path], str, str]:
    paths = sorted(MIGRATIONS.glob("*.sql"), key=lambda p: p.name)
    if not paths:
        fail("migration corpus is empty")
    digest = hashlib.sha256()
    texts: list[str] = []
    for path in paths:
        rel = path.relative_to(ROOT).as_posix()
        try:
            raw = path.read_bytes()
            text = raw.decode("utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            fail(f"migration corpus unreadable: {rel}: {type(exc).__name__}")
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(raw)
        digest.update(b"\0")
        texts.append(text)
    return paths, digest.hexdigest(), "\n".join(texts).lower()


def validate_authority() -> dict:
    authority = load_json(AUTHORITY, "Stage80 authority")
    if authority.get("schema_version") != 1 or authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("Stage80 authority identity drift")
    if authority.get("stage") != "STAGE80_TECHNICAL_SENSITIVE_DATA_MINIMIZATION_INVENTORY":
        fail("Stage80 authority stage drift")
    if authority.get("baseline_main_sha") != "1f9de92a9add0bc6762f153fd9ad2d40ac23fc71":
        fail("Stage80 baseline main SHA drift")

    target = authority.get("target_open_decision")
    if not isinstance(target, dict):
        fail("Stage80 target decision missing")
    if target.get("id") != "SENSITIVE_DATA_TREATMENT" or target.get("state") != "OPEN":
        fail("SENSITIVE_DATA_TREATMENT must remain OPEN")
    if target.get("affected_gates") != ["legal_role_mapping", "legal_privacy_notice", "incident_response"]:
        fail("Stage80 affected gate set/order drift")
    if target.get("required") != "Approved treatment/minimization rules for health, injury, pain or other potentially sensitive student information.":
        fail("Stage80 target requirement drift")
    if target.get("resolution_authority") != "independent legal/privacy review":
        fail("Stage80 resolution authority drift")

    remote = authority.get("fresh_remote_read_only_receipt")
    if not isinstance(remote, dict):
        fail("Stage80 remote read-only receipt missing")
    if remote.get("auth_users") != 0 or remote.get("organizations") != 0 or remote.get("students") != 0:
        fail("Stage80 remote customer baseline drift")
    if remote.get("asaas_state") != "selected_pending_credentials" or remote.get("asaas_activated_at") is not None:
        fail("Stage80 Asaas baseline drift")
    if remote.get("reviewed_public_table_count") != 8 or remote.get("reviewed_public_rls_enabled_count") != 8:
        fail("Stage80 bounded public RLS observation drift")
    if remote.get("reviewed_private_table_count") != 6:
        fail("Stage80 bounded private table observation drift")
    if remote.get("anon_authenticated_direct_table_grant_count") != 0:
        fail("Stage80 bounded direct grant observation drift")
    if remote.get("remote_mutation_performed") is not False:
        fail("Stage80 remote receipt must preserve no mutation")
    boundaries = remote.get("interpretation_boundaries")
    if not isinstance(boundaries, dict) or not boundaries:
        fail("Stage80 remote interpretation boundaries missing")
    for key, value in boundaries.items():
        if value is not False:
            fail(f"Stage80 remote interpretation boundary must remain false: {key}")

    contract = authority.get("inventory_contract")
    if not isinstance(contract, dict):
        fail("Stage80 inventory contract missing")
    if contract.get("expected_table_backed_surface_count") != 7 or contract.get("expected_non_table_surface_count") != 2:
        fail("Stage80 expected surface count drift")
    for key in (
        "technical_source_binding_required",
        "draft_document_boundary_binding_required",
        "migration_corpus_digest_required",
        "registry_digest_required",
        "technical_minimization_requirements_may_be_reported",
        "potentially_sensitive_source_flags_may_be_reported",
    ):
        if contract.get(key) is not True:
            fail(f"Stage80 contract must keep {key}=true")
    for key in (
        "potentially_sensitive_source_flags_are_final_legal_classification",
        "technical_minimization_requirements_are_approved_legal_policy",
        "legal_basis_may_be_selected",
        "consent_requirement_may_be_selected",
        "necessity_or_proportionality_may_be_legally_approved",
        "retention_period_may_be_selected",
        "incident_notification_decision_may_be_selected",
        "controller_processor_role_may_be_selected",
        "external_ai_sensitive_data_use_may_be_authorized",
        "marketing_sensitive_data_use_may_be_authorized",
        "target_open_decision_can_be_closed",
        "inventory_is_legal_review",
        "inventory_is_incident_evidence",
        "network_calls_allowed",
        "provider_calls_allowed",
        "supabase_mutation_allowed",
        "deployment_action_allowed",
        "evidence_ref_creation_allowed",
        "evidence_digest_promotion_allowed",
        "evidence_migration_creation_allowed",
        "gate_promotion_allowed",
        "controlled_launch_promotion_allowed",
        "paid_media_promotion_allowed",
    ):
        if contract.get(key) is not False:
            fail(f"Stage80 contract must keep {key}=false")
    return authority


def validate_open_decision() -> None:
    decisions = load_json(OPEN_DECISIONS, "open decisions")
    unresolved = decisions.get("unresolved")
    if not isinstance(unresolved, list):
        fail("open decisions unresolved list missing")
    target = next((item for item in unresolved if isinstance(item, dict) and item.get("id") == "SENSITIVE_DATA_TREATMENT"), None)
    if not isinstance(target, dict):
        fail("SENSITIVE_DATA_TREATMENT missing")
    if target.get("state") != "OPEN":
        fail("SENSITIVE_DATA_TREATMENT must remain OPEN")
    if target.get("applies_to") != ["legal_role_mapping", "legal_privacy_notice", "incident_response"]:
        fail("SENSITIVE_DATA_TREATMENT applies_to drift")
    if target.get("resolution_authority") != "independent legal/privacy review":
        fail("SENSITIVE_DATA_TREATMENT resolution authority drift")


def validate_documents() -> dict[str, str]:
    try:
        role = ROLE_MATRIX.read_text(encoding="utf-8")
        privacy = PRIVACY.read_text(encoding="utf-8")
        incident = INCIDENT.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"unable to read draft compliance document: {type(exc).__name__}")
    for marker in (
        "DRAFT_UNREVIEWED_NOT_LEGAL_EVIDENCE",
        "HIPÓTESE, NÃO CONCLUSÃO JURÍDICA",
        "Execução/feedback",
        "dados sensíveis não entram em UTMs/advertising payloads",
        "Decision Intelligence human-in-the-loop",
    ):
        if marker not in role:
            fail(f"processing role matrix boundary missing: {marker}")
    for marker in (
        "DRAFT_UNREVIEWED_NOT_PUBLISHED_NOT_LEGAL_EVIDENCE",
        "saúde, lesão, dor, limitações",
        "dados sensíveis não devem ser enviados em UTMs, payloads de advertising, logs desnecessários ou recibos de engenharia",
        "Dados de saúde/sensíveis não devem ser reutilizados para segmentação publicitária",
        "Qualquer provedor externo de IA exige avaliação de privacidade",
    ):
        if marker not in privacy:
            fail(f"privacy notice sensitive-data boundary missing: {marker}")
    for marker in (
        "DRAFT_UNREVIEWED_NOT_OPERATIONAL_EVIDENCE",
        "Proteger tenants e dados potencialmente sensíveis",
        "blast radius",
        "Potentially sensitive student data",
        "somente dados sintéticos/non-customer",
        "O script/CI não pode auto-concluir",
    ):
        if marker not in incident:
            fail(f"incident runbook sensitive-data boundary missing: {marker}")
    return {
        "processing_role_matrix_sha256": sha256_file(ROLE_MATRIX),
        "privacy_notice_candidate_sha256": sha256_file(PRIVACY),
        "incident_runbook_candidate_sha256": sha256_file(INCIDENT),
        "open_decisions_sha256": sha256_file(OPEN_DECISIONS),
    }


def validate_registry(corpus: str, docs_text: str) -> tuple[list[dict], list[dict]]:
    registry = load_json(REGISTRY, "Stage80 registry")
    if registry.get("schema_version") != 1:
        fail("Stage80 registry schema drift")
    if registry.get("status") != "TECHNICAL_SENSITIVE_DATA_MINIMIZATION_REGISTRY_NOT_FINAL_LEGAL_CLASSIFICATION_NOT_POLICY_NOT_EVIDENCE":
        fail("Stage80 registry status drift")
    boundary = registry.get("global_boundaries")
    if not isinstance(boundary, dict) or not boundary:
        fail("Stage80 registry global boundaries missing")
    for key, value in boundary.items():
        if value is not False:
            fail(f"Stage80 registry boundary must remain false: {key}")

    tables = registry.get("table_backed_surfaces")
    if not isinstance(tables, list) or len(tables) != 7:
        fail("Stage80 table-backed surface count drift")
    if [item.get("surface_id") for item in tables if isinstance(item, dict)] != EXPECTED_TABLE_SURFACE_IDS:
        fail("Stage80 table-backed surface identity/order drift")

    built: list[dict] = []
    for item in tables:
        sid = item.get("surface_id")
        source_tables = item.get("source_tables")
        fields = item.get("field_markers")
        requirements = item.get("technical_minimization_requirements_for_review")
        if not isinstance(source_tables, list) or not source_tables:
            fail(f"Stage80 source tables missing: {sid}")
        if not isinstance(fields, list) or not fields:
            fail(f"Stage80 field markers missing: {sid}")
        if not isinstance(requirements, list) or not requirements:
            fail(f"Stage80 minimization requirements missing: {sid}")
        if item.get("approved_policy_state") != "UNRESOLVED":
            fail(f"Stage80 surface policy unexpectedly resolved: {sid}")
        final = item.get("final_legal_classification")
        if not isinstance(final, str) or not final.startswith("UNRESOLVED_REQUIRES_"):
            fail(f"Stage80 final legal classification unexpectedly resolved: {sid}")
        for table in source_tables:
            if not isinstance(table, str) or table.lower() not in corpus:
                fail(f"Stage80 migration corpus missing table marker: {sid}:{table}")
        for field in fields:
            if not isinstance(field, str) or field.lower() not in corpus:
                fail(f"Stage80 migration corpus missing field marker: {sid}:{field}")
        built.append({
            "surface_id": sid,
            "source_tables": source_tables,
            "field_markers": fields,
            "potentially_sensitive_source_flag": item.get("potentially_sensitive_source_flag"),
            "sensitive_content_ingress_should_be_prohibited": item.get("sensitive_content_ingress_should_be_prohibited", False),
            "potentially_sensitive_source_flag_is_final_legal_classification": False,
            "technical_minimization_requirements_for_review": requirements,
            "technical_minimization_requirements_are_approved_legal_policy": False,
            "approved_policy_state": "UNRESOLVED",
            "technical_source_markers_validated": True,
        })

    non_table = registry.get("non_table_surfaces")
    if not isinstance(non_table, list) or len(non_table) != 2:
        fail("Stage80 non-table surface count drift")
    if [item.get("surface_id") for item in non_table if isinstance(item, dict)] != EXPECTED_NON_TABLE_IDS:
        fail("Stage80 non-table identity/order drift")
    built_non_table: list[dict] = []
    for item in non_table:
        sid = item.get("surface_id")
        markers = item.get("source_document_markers")
        reqs = item.get("technical_minimization_requirements_for_review")
        if not isinstance(markers, list) or not markers:
            fail(f"Stage80 non-table doc markers missing: {sid}")
        if not isinstance(reqs, list) or not reqs:
            fail(f"Stage80 non-table minimization requirements missing: {sid}")
        for marker in markers:
            if not isinstance(marker, str) or marker.lower() not in docs_text:
                fail(f"Stage80 source documents missing non-table marker: {sid}:{marker}")
        if item.get("approved_policy_state") != "UNRESOLVED":
            fail(f"Stage80 non-table policy unexpectedly resolved: {sid}")
        built_non_table.append({
            "surface_id": sid,
            "source_document_markers": markers,
            "technical_minimization_requirements_for_review": reqs,
            "technical_minimization_requirements_are_approved_legal_policy": False,
            "approved_policy_state": "UNRESOLVED",
            "source_document_markers_validated": True,
        })
    return built, built_non_table


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    source_sha = args.source_sha.strip().lower()
    if SHA40_RE.fullmatch(source_sha) is None:
        fail("source-sha must be an exact lowercase 40-character Git SHA")

    authority = validate_authority()
    validate_open_decision()
    doc_digests = validate_documents()
    migration_paths, migration_digest, corpus = migration_corpus()
    docs_text = "\n".join([
        ROLE_MATRIX.read_text(encoding="utf-8"),
        PRIVACY.read_text(encoding="utf-8"),
        INCIDENT.read_text(encoding="utf-8"),
    ]).lower()
    table_surfaces, non_table_surfaces = validate_registry(corpus, docs_text)

    value = {
        "schema_version": 1,
        "stage": "STAGE80_TECHNICAL_SENSITIVE_DATA_MINIMIZATION_INVENTORY",
        "output_kind": "NON_ATTESTING_TECHNICAL_SENSITIVE_DATA_MINIMIZATION_INVENTORY",
        "inventory_state": "SOURCE_SURFACES_AND_TECHNICAL_MINIMIZATION_REQUIREMENTS_BOUND_FINAL_LEGAL_CLASSIFICATION_AND_POLICY_UNRESOLVED_NOT_GATE_EVIDENCE",
        "source_sha": source_sha,
        "target_open_decision": "SENSITIVE_DATA_TREATMENT",
        "target_open_decision_state": "OPEN",
        "affected_external_gates": ["legal_role_mapping", "legal_privacy_notice", "incident_response"],
        "registry_sha256": sha256_file(REGISTRY),
        "migration_corpus_sha256": migration_digest,
        "migration_file_count": len(migration_paths),
        "draft_document_digests": doc_digests,
        "table_backed_surface_count": len(table_surfaces),
        "non_table_surface_count": len(non_table_surfaces),
        "table_backed_surfaces": table_surfaces,
        "non_table_surfaces": non_table_surfaces,
        "remote_read_only_snapshot": authority["fresh_remote_read_only_receipt"],
        "potentially_sensitive_source_flags_are_final_legal_classification": False,
        "technical_minimization_requirements_are_approved_legal_policy": False,
        "legal_basis_approved": False,
        "consent_requirement_approved": False,
        "necessity_or_proportionality_legally_approved": False,
        "retention_period_approved": False,
        "controller_processor_role_approved": False,
        "external_ai_sensitive_data_use_authorized": False,
        "marketing_sensitive_data_use_authorized": False,
        "incident_notification_decision_made": False,
        "independent_legal_privacy_review_performed": False,
        "target_open_decision_closed": False,
        "legal_role_mapping_gate_ready": False,
        "legal_privacy_notice_gate_ready": False,
        "incident_response_gate_ready": False,
        "evidence_ref_created": False,
        "evidence_digest_promoted": False,
        "evidence_migration_created": False,
        "network_call_performed": False,
        "provider_call_performed": False,
        "supabase_mutation_performed": False,
        "deployment_performed": False,
        "controlled_launch_promoted": False,
        "paid_media_promoted": False,
        "next_action": "REAL_INDEPENDENT_LEGAL_PRIVACY_REVIEW_REQUIRED_TO_APPROVE_SENSITIVE_DATA_CLASSIFICATION_PURPOSE_MINIMIZATION_AND_PROCESSING_RULES",
    }

    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

    print("STAGE80_SENSITIVE_DATA_MINIMIZATION_INVENTORY=PASS_NON_ATTESTING")
    print("TABLE_BACKED_SURFACE_COUNT=7")
    print("NON_TABLE_SURFACE_COUNT=2")
    print("FINAL_LEGAL_CLASSIFICATION_APPROVED=false")
    print("SENSITIVE_DATA_POLICY_APPROVED=false")
    print("TARGET_DECISION_CLOSED=false")
    print("GATE_PROMOTION=false")
    print("REMOTE_MUTATION=false")


if __name__ == "__main__":
    main()
