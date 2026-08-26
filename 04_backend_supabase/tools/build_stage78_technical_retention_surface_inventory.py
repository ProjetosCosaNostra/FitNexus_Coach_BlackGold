from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage78_technical_retention_surface_inventory_authority.json"
REGISTRY = ROOT / "10_compliance" / "inventory" / "STAGE78_TECHNICAL_DATA_RETENTION_SURFACE_REGISTRY.json"
OPEN_DECISIONS = ROOT / "10_compliance" / "drafts" / "COMPLIANCE_OPEN_DECISIONS.json"
PRIVACY = ROOT / "10_compliance" / "drafts" / "PRIVACY_NOTICE_CANDIDATE_PTBR.md"
DSR = ROOT / "10_compliance" / "drafts" / "DATA_SUBJECT_REQUEST_RUNBOOK_CANDIDATE.md"
MIGRATIONS = BACKEND / "migrations"
FAILURE_CLASS = "BGF-STAGE78-TECHNICAL-RETENTION-SURFACE-GUARD-755"
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")

EXPECTED_CATEGORY_IDS = [
    "account_and_tenancy",
    "student_identity_and_coaching_profile",
    "training_prescription_templates_and_lineage",
    "workout_execution_history",
    "potentially_sensitive_workout_feedback",
    "decision_intelligence_and_coach_action_history",
    "student_access_security_and_abuse_telemetry",
    "growth_attribution_and_funnel_telemetry",
    "billing_subscription_and_webhook_history",
    "governance_and_gate_evidence_metadata",
]
EXPECTED_NON_TABLE_IDS = [
    "backup_restore_and_expiration",
    "scheduled_cleanup_or_purge",
]


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE78_TECHNICAL_RETENTION_SURFACE_INVENTORY=FAIL\n"
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
    authority = load_json(AUTHORITY, "Stage78 authority")
    if authority.get("schema_version") != 1 or authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("Stage78 authority identity drift")
    if authority.get("stage") != "STAGE78_TECHNICAL_RETENTION_SURFACE_INVENTORY":
        fail("Stage78 authority stage drift")
    if authority.get("baseline_main_sha") != "c92da46e17e7a8614545c62f6921f22ff661a10c":
        fail("Stage78 baseline main SHA drift")

    upstream = authority.get("upstream_authority")
    if not isinstance(upstream, dict):
        fail("Stage78 upstream authority missing")
    pins = {
        "stage77_provider_review_packet_blob": "12053a4ffbe60919511ca7f119671a291e418f48",
        "open_decisions_blob": "215d527c1cb79d7b72697f03f1f84887e3a72d95",
        "privacy_notice_candidate_blob": "1e5afdba4735469d734490883be8f7e011ac8159",
        "dsr_runbook_candidate_blob": "a4a9ee94d29dc17c9a76db2f8ede629d7c207ab8",
    }
    for key, expected in pins.items():
        if upstream.get(key) != expected:
            fail(f"Stage78 upstream blob pin drift: {key}")

    target = authority.get("target_open_decision")
    if not isinstance(target, dict):
        fail("Stage78 target open decision missing")
    if target.get("id") != "RETENTION_MATRIX" or target.get("state") != "OPEN":
        fail("Stage78 target must remain RETENTION_MATRIX OPEN")
    if target.get("affected_gates") != ["legal_privacy_notice", "data_subject_request_channel", "incident_response"]:
        fail("Stage78 affected gate set/order drift")
    if target.get("resolution_authority") != "legal/privacy/operations review":
        fail("Stage78 retention resolution authority drift")

    remote = authority.get("fresh_remote_read_only_receipt")
    if not isinstance(remote, dict):
        fail("Stage78 remote receipt missing")
    if remote.get("auth_users") != 0 or remote.get("organizations") != 0 or remote.get("students") != 0:
        fail("Stage78 remote customer-row baseline drift")
    if remote.get("asaas_state") != "selected_pending_credentials" or remote.get("asaas_activated_at") is not None:
        fail("Stage78 remote Asaas baseline drift")
    if remote.get("public_private_table_count") != 45:
        fail("Stage78 observed public/private table count drift")
    if remote.get("cleanup_like_named_routines_observed") != 0:
        fail("Stage78 named cleanup routine observation drift")
    if remote.get("storage_bucket_count") != 0 or remote.get("pg_cron_installed") is not False:
        fail("Stage78 storage/pg_cron observation drift")
    if remote.get("remote_mutation_performed") is not False:
        fail("Stage78 remote receipt must remain read-only")
    boundaries = remote.get("interpretation_boundaries")
    if not isinstance(boundaries, dict) or not boundaries:
        fail("Stage78 remote interpretation boundaries missing")
    for key, value in boundaries.items():
        if value is not False:
            fail(f"Stage78 remote interpretation boundary must remain false: {key}")

    contract = authority.get("inventory_contract")
    if not isinstance(contract, dict):
        fail("Stage78 inventory contract missing")
    if contract.get("expected_category_count") != 10 or contract.get("expected_non_table_surface_count") != 2:
        fail("Stage78 expected inventory cardinality drift")
    for key in (
        "technical_source_binding_required",
        "migration_corpus_digest_required",
        "registry_digest_required",
        "candidate_document_digests_required",
        "technical_lifecycle_markers_may_be_reported",
    ):
        if contract.get(key) is not True:
            fail(f"Stage78 contract must keep {key}=true")
    for key in (
        "technical_lifecycle_marker_is_retention_policy",
        "retention_periods_may_be_selected",
        "backup_expiration_may_be_selected",
        "legal_hold_rules_may_be_selected",
        "cancellation_or_delinquency_retention_may_be_selected",
        "anonymization_or_deletion_obligations_may_be_approved",
        "legal_basis_may_be_selected",
        "sensitivity_flags_are_final_legal_classification",
        "target_open_decision_can_be_closed",
        "inventory_is_legal_review",
        "inventory_is_operational_deletion_test",
        "inventory_is_dsr_evidence",
        "inventory_is_incident_response_evidence",
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
            fail(f"Stage78 contract must keep {key}=false")
    return authority


def validate_open_decision() -> None:
    decisions = load_json(OPEN_DECISIONS, "open decisions registry")
    if decisions.get("status") != "DRAFT_UNREVIEWED_NOT_EVIDENCE":
        fail("open decisions registry status drift")
    unresolved = decisions.get("unresolved")
    if not isinstance(unresolved, list):
        fail("open decisions unresolved list missing")
    target = next((item for item in unresolved if isinstance(item, dict) and item.get("id") == "RETENTION_MATRIX"), None)
    if not isinstance(target, dict):
        fail("RETENTION_MATRIX missing from open decisions")
    if target.get("state") != "OPEN":
        fail("RETENTION_MATRIX must remain OPEN")
    if target.get("applies_to") != ["legal_privacy_notice", "data_subject_request_channel", "incident_response"]:
        fail("RETENTION_MATRIX applies_to drift")
    if target.get("required") != "Approved category-by-category retention, backup expiration and legal-hold rules.":
        fail("RETENTION_MATRIX requirement drift")
    if target.get("resolution_authority") != "legal/privacy/operations review":
        fail("RETENTION_MATRIX resolution authority drift")


def validate_candidate_documents() -> dict[str, str]:
    try:
        privacy = PRIVACY.read_text(encoding="utf-8")
        dsr = DSR.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"unable to read candidate compliance documents: {type(exc).__name__}")
    privacy_markers = (
        "DRAFT_UNREVIEWED_NOT_PUBLISHED_NOT_LEGAL_EVIDENCE",
        "## 8. Retenção e eliminação",
        "backups e janela de expurgo",
        "legal hold quando necessário",
        "Nenhum prazo deve ser inventado neste candidato.",
    )
    for marker in privacy_markers:
        if marker not in privacy:
            fail(f"privacy candidate retention boundary missing: {marker}")
    dsr_markers = (
        "DRAFT_UNREVIEWED_NOT_OPERATIONAL_EVIDENCE",
        "## 9. Eliminação, anonimização, bloqueio e retention hold — teste exigido",
        "backup ainda em janela de retenção",
        "eventos de segurança/auditoria que possuam fundamento próprio de retenção",
        "Nenhum prazo ou obrigação é congelado por este candidato.",
    )
    for marker in dsr_markers:
        if marker not in dsr:
            fail(f"DSR candidate retention boundary missing: {marker}")
    return {
        "privacy_notice_candidate_sha256": sha256_file(PRIVACY),
        "dsr_runbook_candidate_sha256": sha256_file(DSR),
        "open_decisions_sha256": sha256_file(OPEN_DECISIONS),
    }


def validate_registry(corpus_text: str) -> tuple[dict, list[dict], list[dict]]:
    registry = load_json(REGISTRY, "Stage78 technical retention registry")
    if registry.get("schema_version") != 1:
        fail("Stage78 registry schema drift")
    if registry.get("status") != "TECHNICAL_DATA_RETENTION_SURFACE_REGISTRY_NOT_APPROVED_RETENTION_POLICY_NOT_EVIDENCE":
        fail("Stage78 registry status drift")
    boundary = registry.get("policy_boundary")
    if not isinstance(boundary, dict) or not boundary:
        fail("Stage78 registry policy boundary missing")
    for key, value in boundary.items():
        if value is not False:
            fail(f"Stage78 registry policy boundary must remain false: {key}")

    categories = registry.get("categories")
    if not isinstance(categories, list) or len(categories) != len(EXPECTED_CATEGORY_IDS):
        fail("Stage78 category cardinality drift")
    ids = [item.get("category_id") for item in categories if isinstance(item, dict)]
    if ids != EXPECTED_CATEGORY_IDS:
        fail("Stage78 category identity/order drift")

    built_categories: list[dict] = []
    for item in categories:
        category_id = item.get("category_id")
        tables = item.get("source_tables")
        markers = item.get("key_field_markers")
        lifecycle = item.get("observed_lifecycle_markers")
        if not isinstance(tables, list) or not tables:
            fail(f"Stage78 category source_tables missing: {category_id}")
        if not isinstance(markers, list) or not markers:
            fail(f"Stage78 category key_field_markers missing: {category_id}")
        if not isinstance(lifecycle, list) or not lifecycle:
            fail(f"Stage78 category lifecycle markers missing: {category_id}")
        if item.get("explicit_retention_period_in_registry") is not None:
            fail(f"Stage78 category invented a retention period: {category_id}")
        state = item.get("retention_policy_state")
        if not isinstance(state, str) or not state.startswith("UNRESOLVED_REQUIRES_"):
            fail(f"Stage78 category retention state must remain unresolved: {category_id}")
        for table in tables:
            if not isinstance(table, str) or table.lower() not in corpus_text:
                fail(f"Stage78 migration corpus missing source table marker: {category_id}:{table}")
        for marker in markers:
            if not isinstance(marker, str) or marker.lower() not in corpus_text:
                fail(f"Stage78 migration corpus missing field marker: {category_id}:{marker}")
        built_categories.append({
            "category_id": category_id,
            "source_tables": tables,
            "technical_table_count": len(tables),
            "key_field_markers": markers,
            "observed_lifecycle_markers": lifecycle,
            "data_subject_linkage_possible": item.get("data_subject_linkage_possible"),
            "potentially_sensitive_source_flag": item.get("potentially_sensitive"),
            "potentially_sensitive_source_flag_is_final_legal_classification": False,
            "explicit_retention_period": None,
            "retention_policy_state": state,
            "technical_source_markers_validated": True,
        })

    non_table = registry.get("non_table_surfaces")
    if not isinstance(non_table, list) or len(non_table) != len(EXPECTED_NON_TABLE_IDS):
        fail("Stage78 non-table surface cardinality drift")
    non_table_ids = [item.get("surface_id") for item in non_table if isinstance(item, dict)]
    if non_table_ids != EXPECTED_NON_TABLE_IDS:
        fail("Stage78 non-table surface identity/order drift")
    for item in non_table:
        state = item.get("retention_policy_state")
        if not isinstance(state, str) or not state.startswith("UNRESOLVED_REQUIRES_"):
            fail(f"Stage78 non-table retention state must remain unresolved: {item.get('surface_id')}")
    return registry, built_categories, non_table


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
    document_digests = validate_candidate_documents()
    migration_paths, migration_digest, corpus_text = migration_corpus()
    registry, categories, non_table = validate_registry(corpus_text)

    unique_tables = sorted({table for category in categories for table in category["source_tables"]})
    lifecycle_markers = sorted({marker for category in categories for marker in category["observed_lifecycle_markers"]})

    output_value = {
        "schema_version": 1,
        "stage": "STAGE78_TECHNICAL_RETENTION_SURFACE_INVENTORY",
        "output_kind": "NON_ATTESTING_TECHNICAL_RETENTION_SURFACE_INVENTORY",
        "inventory_state": "TECHNICAL_SURFACES_BOUND_RETENTION_PERIODS_AND_LEGAL_HOLD_BACKUP_PURGE_RULES_UNRESOLVED_NOT_GATE_EVIDENCE",
        "source_sha": source_sha,
        "target_open_decision": "RETENTION_MATRIX",
        "target_open_decision_state": "OPEN",
        "affected_external_gates": ["legal_privacy_notice", "data_subject_request_channel", "incident_response"],
        "registry_sha256": sha256_file(REGISTRY),
        "migration_corpus_sha256": migration_digest,
        "migration_file_count": len(migration_paths),
        "candidate_document_digests": document_digests,
        "technical_category_count": len(categories),
        "non_table_surface_count": len(non_table),
        "unique_source_table_count": len(unique_tables),
        "unique_source_tables": unique_tables,
        "technical_lifecycle_marker_count": len(lifecycle_markers),
        "technical_lifecycle_markers": lifecycle_markers,
        "categories": categories,
        "non_table_surfaces": non_table,
        "remote_read_only_snapshot": authority["fresh_remote_read_only_receipt"],
        "retention_periods_defined_count": 0,
        "all_category_retention_periods_unresolved": True,
        "technical_lifecycle_markers_are_retention_policy": False,
        "zero_customer_rows_resolves_retention": False,
        "zero_cleanup_named_routines_proves_no_deletion_paths": False,
        "zero_storage_buckets_proves_no_backup_or_provider_retention": False,
        "pg_cron_absence_proves_no_external_cleanup": False,
        "sensitivity_source_flags_are_final_legal_classification": False,
        "backup_expiration_approved": False,
        "legal_hold_rules_approved": False,
        "cancellation_or_delinquency_retention_approved": False,
        "anonymization_or_deletion_rules_approved": False,
        "legal_basis_approved": False,
        "independent_legal_privacy_operations_review_performed": False,
        "operational_deletion_or_hold_test_performed": False,
        "target_open_decision_closed": False,
        "legal_privacy_notice_gate_ready": False,
        "data_subject_request_channel_gate_ready": False,
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
        "next_action": "REAL_LEGAL_PRIVACY_OPERATIONS_REVIEW_REQUIRED_TO_SELECT_CATEGORY_RETENTION_BACKUP_PURGE_LEGAL_HOLD_AND_DELETION_RULES",
    }

    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(output_value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

    print("STAGE78_TECHNICAL_RETENTION_SURFACE_INVENTORY=PASS_NON_ATTESTING")
    print(f"CATEGORY_COUNT={len(categories)}")
    print(f"UNIQUE_SOURCE_TABLE_COUNT={len(unique_tables)}")
    print("RETENTION_PERIODS_DEFINED=0")
    print("LEGAL_HOLD_RULES_APPROVED=false")
    print("BACKUP_EXPIRATION_APPROVED=false")
    print("TARGET_DECISION_CLOSED=false")
    print("GATE_PROMOTION=false")
    print("REMOTE_MUTATION=false")


if __name__ == "__main__":
    main()
