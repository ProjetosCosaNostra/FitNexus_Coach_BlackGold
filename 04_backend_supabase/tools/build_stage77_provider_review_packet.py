from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUTHORITY = ROOT / "04_backend_supabase" / "stage77_provider_review_packet_assembler_authority.json"
STAGE76 = ROOT / "04_backend_supabase" / "stage76_provider_evidence_acquisition_boundary_authority.json"
OPEN_DECISIONS = ROOT / "10_compliance" / "drafts" / "COMPLIANCE_OPEN_DECISIONS.json"
FAILURE_CLASS = "BGF-STAGE77-PROVIDER-REVIEW-PACKET-ASSEMBLER-GUARD-745"
PLACEHOLDER_RE = re.compile(r"<[^>]+>|placeholder|tbd|to[_ -]?be[_ -]?defined|example", re.IGNORECASE)
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

EXPECTED_IDS = [
    "supabase",
    "telegram_bot_api",
    "asaas",
    "cloudflare_edge_signal",
    "github_repository_ci_pages",
]
ARTIFACT_KEYS = [
    "relationship_scope_resolution",
    "provider_legal_entity_source",
    "contract_dpa_or_data_terms_source",
    "processing_purpose_and_data_categories_source",
    "processing_or_hosting_regions_source",
    "retention_and_deletion_terms_source",
    "subprocessor_chain_source",
    "international_transfer_mechanism_source",
]
FALSE_STAGE76_FLAGS = [
    "stage75_relationship_status_is_legal_classification",
    "artifact_paths_copied",
    "artifact_contents_copied",
    "secret_values_copied",
    "provider_facts_extracted_or_attested",
    "provider_legal_entity_verified",
    "contract_or_dpa_sufficiency_verified",
    "processing_regions_verified",
    "retention_terms_verified",
    "subprocessor_chain_verified",
    "transfer_mechanism_legality_verified",
    "legal_relationship_classified",
    "cloudflare_direct_contract_proven_by_collector",
    "github_production_authority_proven_by_collector",
    "asaas_credentials_or_activation_proven_by_collector",
    "billing_credential_evidence",
    "checkout_proof",
    "production_deployment_evidence",
    "target_open_decision_closed",
    "legal_gate_ready_attested",
    "evidence_ref_created",
    "evidence_digest_promoted",
    "evidence_migration_created",
    "network_call_performed",
    "provider_call_performed",
    "supabase_mutation_performed",
    "deployment_performed",
    "controlled_launch_promoted",
    "paid_media_promoted",
]
SCOPE_KEYS = [
    "candidate_set_is_provider_fact_evidence",
    "candidate_set_is_legal_review",
    "candidate_set_closes_subprocessor_transfer_decision",
    "candidate_set_marks_legal_gate_ready",
    "candidate_set_is_billing_credential_evidence",
    "candidate_set_is_checkout_proof",
    "candidate_set_is_production_deployment_evidence",
    "candidate_set_creates_evidence_migration",
]


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE77_PROVIDER_REVIEW_PACKET=FAIL\n"
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
        fail(f"unable to hash candidate file: {type(exc).__name__}")


def validate_repo_authorities() -> None:
    authority = load_json(AUTHORITY, "Stage77 authority")
    if authority.get("stage") != "STAGE77_PROVIDER_REVIEW_PACKET_ASSEMBLER_BOUNDARY":
        fail("Stage77 authority stage drift")
    if authority.get("baseline_main_sha") != "c83fa7ae55876ada43b12d06985e87b7da44d8af":
        fail("Stage77 baseline main SHA drift")
    upstream = authority.get("upstream_authority")
    if not isinstance(upstream, dict) or upstream.get("stage76_provider_evidence_acquisition_blob") != "c07c2fca4894a2f6076ed86bb6587c3a878d93ec":
        fail("Stage77 Stage76 authority pin drift")

    stage76 = load_json(STAGE76, "Stage76 authority")
    if stage76.get("stage") != "STAGE76_PROVIDER_EVIDENCE_ACQUISITION_BOUNDARY":
        fail("Stage76 authority stage drift")
    contract = stage76.get("acquisition_contract")
    if not isinstance(contract, dict) or contract.get("allowed_service_ids") != EXPECTED_IDS:
        fail("Stage76 allowed service IDs drift")
    if contract.get("target_open_decision_remains_open_after_collection") is not True:
        fail("Stage76 target decision boundary drift")

    decisions = load_json(OPEN_DECISIONS, "open decisions")
    unresolved = decisions.get("unresolved")
    if not isinstance(unresolved, list):
        fail("open decisions registry missing unresolved list")
    target = next((item for item in unresolved if isinstance(item, dict) and item.get("id") == "SUBPROCESSOR_AND_TRANSFER_MAP"), None)
    if not isinstance(target, dict) or target.get("state") != "OPEN":
        fail("SUBPROCESSOR_AND_TRANSFER_MAP must remain OPEN")
    if target.get("resolution_authority") != "provider evidence plus legal/privacy review":
        fail("SUBPROCESSOR_AND_TRANSFER_MAP resolution authority drift")


def validate_manifest(path: Path) -> tuple[dict, list[Path], str]:
    manifest = load_json(path, "Stage77 real Stage76 candidate set")
    if manifest.get("schema_version") != 1:
        fail("candidate set schema_version must be 1")
    if manifest.get("manifest_kind") != "STAGE77_REAL_STAGE76_DIGEST_CANDIDATE_SET":
        fail("candidate set manifest_kind drift")
    status = str(manifest.get("status", "")).strip()
    if status != "REAL_STAGE76_DIGEST_CANDIDATE_SET_FOR_REVIEW_PREPARATION" or PLACEHOLDER_RE.search(status):
        fail("candidate set is not a real Stage76 digest candidate set")
    if manifest.get("test_fixture") is not False:
        fail("test fixture candidate set cannot create a Stage77 review packet")
    if manifest.get("contains_placeholders") is not False:
        fail("candidate set still declares placeholders")

    reference = str(manifest.get("review_preparation_reference", "")).strip()
    if len(reference) < 3 or PLACEHOLDER_RE.search(reference):
        fail("real traceable review_preparation_reference is required")

    raw_paths = manifest.get("candidate_paths")
    if not isinstance(raw_paths, list) or not 1 <= len(raw_paths) <= len(EXPECTED_IDS):
        fail("candidate_paths must contain between one and five real Stage76 candidate files")
    candidate_paths: list[Path] = []
    seen_paths: set[Path] = set()
    for raw in raw_paths:
        text = str(raw).strip()
        if not text or PLACEHOLDER_RE.search(text):
            fail("candidate_paths contains a missing or placeholder path")
        candidate = Path(text).expanduser()
        if not candidate.is_absolute():
            candidate = (path.parent / candidate).resolve()
        else:
            candidate = candidate.resolve()
        if candidate in seen_paths:
            fail("candidate_paths contains a duplicate file path")
        if not candidate.is_file() or candidate.stat().st_size <= 0:
            fail("candidate_paths contains a missing or empty file")
        seen_paths.add(candidate)
        candidate_paths.append(candidate)

    boundary = manifest.get("scope_boundary")
    if not isinstance(boundary, dict) or list(boundary) != SCOPE_KEYS:
        fail("candidate set scope_boundary keys drift")
    for key in SCOPE_KEYS:
        if boundary.get(key) is not False:
            fail(f"candidate set scope boundary must remain false: {key}")
    return manifest, candidate_paths, reference


def validate_stage76_candidate(path: Path) -> dict:
    candidate = load_json(path, "Stage76 digest candidate")
    if candidate.get("schema_version") != 1:
        fail("Stage76 candidate schema_version drift")
    if candidate.get("stage") != "STAGE76_PROVIDER_EVIDENCE_ACQUISITION_BOUNDARY":
        fail("non-Stage76 candidate supplied")
    if candidate.get("output_kind") != "DIGEST_ONLY_PROVIDER_PRIVACY_EVIDENCE_INTAKE_CANDIDATE":
        fail("Stage76 candidate output_kind drift")
    if candidate.get("candidate_state") != "REAL_EXTERNAL_SOURCE_ARTIFACT_DIGESTS_BOUND_AWAITING_INDEPENDENT_LEGAL_PRIVACY_REVIEW_NOT_GATE_EVIDENCE":
        fail("Stage76 candidate state drift")

    service_id = str(candidate.get("service_id", "")).strip()
    if service_id not in EXPECTED_IDS:
        fail("Stage76 candidate service_id is outside the Stage75 inventory")
    relationship_status = candidate.get("stage75_relationship_status")
    if not isinstance(relationship_status, str) or not relationship_status.strip():
        fail("Stage76 candidate relationship status missing")

    for key in ("provider_input_sha256", "collection_reference_sha256"):
        value = candidate.get(key)
        if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
            fail(f"Stage76 candidate invalid SHA-256 field: {key}")

    artifact_sha256 = candidate.get("artifact_sha256")
    if not isinstance(artifact_sha256, dict) or list(artifact_sha256) != ARTIFACT_KEYS:
        fail("Stage76 candidate artifact digest keys drift")
    for key in ARTIFACT_KEYS:
        digest = artifact_sha256.get(key)
        if not isinstance(digest, str) or SHA256_RE.fullmatch(digest) is None:
            fail(f"Stage76 candidate invalid artifact digest: {key}")

    for key in FALSE_STAGE76_FLAGS:
        if candidate.get(key) is not False:
            fail(f"Stage76 candidate boundary flag must remain false: {key}")
    if candidate.get("independent_legal_privacy_review_required") is not True:
        fail("Stage76 candidate must require independent legal/privacy review")

    return {
        "service_id": service_id,
        "stage75_relationship_status": relationship_status,
        "stage76_candidate_sha256": sha256_file(path),
        "provider_input_sha256": candidate["provider_input_sha256"],
        "collection_reference_sha256": candidate["collection_reference_sha256"],
        "artifact_sha256": {key: artifact_sha256[key] for key in ARTIFACT_KEYS},
        "provider_facts_attested": False,
        "legal_relationship_classified": False,
        "independent_legal_privacy_review_required": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-manifest", required=True, type=Path)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    source_sha = args.source_sha.strip().lower()
    if SHA40_RE.fullmatch(source_sha) is None:
        fail("source-sha must be an exact lowercase 40-character Git SHA")

    validate_repo_authorities()
    manifest_path = args.candidate_manifest.expanduser().resolve()
    manifest, candidate_paths, review_reference = validate_manifest(manifest_path)

    entries = [validate_stage76_candidate(path) for path in candidate_paths]
    entries.sort(key=lambda item: item["service_id"])
    ids = [item["service_id"] for item in entries]
    if len(ids) != len(set(ids)):
        fail("duplicate Stage76 candidate for the same service_id")

    missing = [service_id for service_id in EXPECTED_IDS if service_id not in set(ids)]
    packet = {
        "schema_version": 1,
        "stage": "STAGE77_PROVIDER_REVIEW_PACKET_ASSEMBLER_BOUNDARY",
        "output_kind": "NON_ATTESTING_MULTI_PROVIDER_STAGE76_DIGEST_REVIEW_PACKET",
        "packet_state": "REAL_STAGE76_DIGEST_CANDIDATES_ASSEMBLED_AWAITING_INDEPENDENT_LEGAL_PRIVACY_REVIEW_NOT_GATE_EVIDENCE",
        "source_sha": source_sha,
        "candidate_manifest_sha256": sha256_file(manifest_path),
        "review_preparation_reference_sha256": sha256_bytes(review_reference.encode("utf-8")),
        "provider_candidate_count": len(entries),
        "all_stage75_services_represented": len(entries) == len(EXPECTED_IDS) and not missing,
        "missing_service_ids": missing,
        "provider_candidates": entries,
        "candidate_paths_copied": False,
        "raw_provider_artifacts_copied": False,
        "secret_values_copied": False,
        "provider_facts_extracted_or_attested": False,
        "provider_legal_entities_verified": False,
        "contracts_or_dpas_sufficiency_verified": False,
        "processing_regions_verified": False,
        "retention_terms_verified": False,
        "subprocessor_chains_verified": False,
        "transfer_mechanisms_legality_verified": False,
        "legal_relationships_classified": False,
        "independent_legal_privacy_review_performed": False,
        "target_open_decision_closed": False,
        "legal_gate_ready_attested": False,
        "billing_credential_evidence": False,
        "checkout_proof": False,
        "production_deployment_evidence": False,
        "evidence_ref_created": False,
        "evidence_digest_promoted": False,
        "evidence_migration_created": False,
        "network_call_performed": False,
        "provider_call_performed": False,
        "supabase_mutation_performed": False,
        "deployment_performed": False,
        "controlled_launch_promoted": False,
        "paid_media_promoted": False,
        "independent_legal_privacy_review_required": True,
        "next_action": "REAL_INDEPENDENT_LEGAL_PRIVACY_REVIEW_REQUIRED_BEFORE_SUBPROCESSOR_AND_TRANSFER_MAP_DECISION",
    }

    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(packet, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

    print("STAGE77_PROVIDER_REVIEW_PACKET=PASS_NON_ATTESTING")
    print(f"PROVIDER_CANDIDATE_COUNT={len(entries)}")
    print(f"ALL_STAGE75_SERVICES_REPRESENTED={str(packet['all_stage75_services_represented']).lower()}")
    print("PROVIDER_FACTS_ATTESTED=false")
    print("LEGAL_REVIEW_PERFORMED=false")
    print("TARGET_DECISION_CLOSED=false")
    print("GATE_PROMOTION=false")
    print("REMOTE_MUTATION=false")


if __name__ == "__main__":
    main()
