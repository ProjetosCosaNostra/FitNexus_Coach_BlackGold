from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "10_compliance" / "inventory" / "STAGE75_TECHNICAL_EXTERNAL_SERVICE_SOURCE_REGISTRY.json"
PLACEHOLDER_RE = re.compile(r"<[^>]+>|placeholder|tbd|to[_ -]?be[_ -]?defined|example", re.IGNORECASE)
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", re.IGNORECASE),
    re.compile(r"\b(?:password|passwd|api[_-]?key|access[_-]?token|service[_-]?role[_-]?key|client[_-]?secret|webhook[_-]?token|secret[_-]?value)\s*[:=]\s*[^\s,}\]]+", re.IGNORECASE),
)
ARTIFACT_KEYS = (
    "relationship_scope_resolution",
    "provider_legal_entity_source",
    "contract_dpa_or_data_terms_source",
    "processing_purpose_and_data_categories_source",
    "processing_or_hosting_regions_source",
    "retention_and_deletion_terms_source",
    "subprocessor_chain_source",
    "international_transfer_mechanism_source",
)
FAILURE_CLASS = "BGF-STAGE76-PROVIDER-EVIDENCE-ACQUISITION-GUARD-735"


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE76_PROVIDER_EVIDENCE_CANDIDATE=FAIL\n"
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
    return sha256_bytes(path.read_bytes())


def validate_timestamp(value: object) -> str:
    if not isinstance(value, str) or not value.strip() or PLACEHOLDER_RE.search(value):
        fail("collected_at_utc must be a real timezone-aware ISO-8601 timestamp")
    raw = value.strip()
    try:
        parsed = datetime.fromisoformat(raw[:-1] + "+00:00" if raw.endswith("Z") else raw)
    except ValueError:
        fail("collected_at_utc is not valid ISO-8601")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        fail("collected_at_utc must be timezone-aware")
    if parsed.astimezone(timezone.utc) > datetime.now(timezone.utc):
        fail("collected_at_utc cannot be in the future")
    return parsed.astimezone(timezone.utc).isoformat()


def validate_artifact(path: Path, label: str) -> str:
    if not path.is_file() or path.stat().st_size <= 0:
        fail(f"{label} must be a real non-empty file")
    if path.stat().st_size > 8 * 1024 * 1024:
        fail(f"{label} exceeds 8 MiB intake boundary")
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        fail(f"{label} must be UTF-8 text for secret-marker inspection")
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            fail(f"{label} contains a secret-like marker; redact before intake")
    return sha256_file(path)


def find_service(service_id: str) -> dict:
    registry = load_json(REGISTRY, "Stage75 source registry")
    if registry.get("status") != "TECHNICAL_SOURCE_REGISTRY_NOT_LEGAL_PROVIDER_MAP_NOT_EVIDENCE":
        fail("Stage75 source registry status drift")
    services = registry.get("services")
    if not isinstance(services, list):
        fail("Stage75 source registry services missing")
    service = next(
        (item for item in services if isinstance(item, dict) and item.get("service_id") == service_id),
        None,
    )
    if not isinstance(service, dict):
        fail("service_id is not one of the Stage75 inventoried services")
    return service


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider-input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    input_path = args.provider_input.resolve()
    value = load_json(input_path, "real provider privacy evidence input")
    if value.get("schema_version") != 1:
        fail("provider evidence input schema_version must be 1")
    if value.get("input_kind") != "REAL_PROVIDER_PRIVACY_EVIDENCE_INPUT":
        fail("provider evidence input_kind drift")
    if value.get("status") == "PLACEHOLDER_TEMPLATE_NOT_REAL_PROVIDER_EVIDENCE" or PLACEHOLDER_RE.search(str(value.get("status", ""))):
        fail("provider evidence input is still placeholder-like")
    if value.get("test_fixture") is not False:
        fail("provider evidence input is a test fixture; real external artifacts are required")
    if value.get("contains_placeholders") is not False:
        fail("provider evidence input declares placeholders")

    service_id = str(value.get("service_id", "")).strip()
    if not service_id or PLACEHOLDER_RE.search(service_id):
        fail("real Stage75 service_id is required")
    service = find_service(service_id)

    collection_ref = str(value.get("evidence_collection_reference", "")).strip()
    if len(collection_ref) < 3 or PLACEHOLDER_RE.search(collection_ref):
        fail("real traceable evidence_collection_reference is required")
    collected_at_utc = validate_timestamp(value.get("collected_at_utc"))

    if value.get("collector_acknowledges_stage75_relationship_status_only") is not True:
        fail("collector must acknowledge that Stage75 relationship status is technical only")
    if value.get("artifact_secret_values_absent_or_redacted_confirmed") is not True:
        fail("secret-value absence/redaction confirmation is required")

    artifacts = value.get("artifacts")
    if not isinstance(artifacts, dict) or set(artifacts) != set(ARTIFACT_KEYS):
        fail("provider evidence artifacts must contain exactly the eight required keys")
    artifact_sha256: dict[str, str] = {}
    for key in ARTIFACT_KEYS:
        raw = str(artifacts.get(key, "")).strip()
        if not raw or PLACEHOLDER_RE.search(raw):
            fail(f"provider evidence artifact path missing or placeholder: {key}")
        artifact_sha256[key] = validate_artifact(Path(raw).expanduser().resolve(), key)

    boundary = value.get("scope_boundary")
    if not isinstance(boundary, dict):
        fail("provider evidence scope_boundary missing")
    for key in (
        "this_input_is_billing_credential_evidence",
        "this_input_is_checkout_proof",
        "this_input_is_production_deployment_evidence",
        "collector_makes_legal_classification",
        "collector_asserts_provider_facts_from_artifact_contents",
        "collector_marks_subprocessor_transfer_decision_resolved",
        "collector_marks_gate_ready",
        "collector_creates_evidence_migration",
    ):
        if boundary.get(key) is not False:
            fail(f"provider evidence scope boundary drift: {key}")

    candidate = {
        "schema_version": 1,
        "stage": "STAGE76_PROVIDER_EVIDENCE_ACQUISITION_BOUNDARY",
        "output_kind": "DIGEST_ONLY_PROVIDER_PRIVACY_EVIDENCE_INTAKE_CANDIDATE",
        "candidate_state": "REAL_EXTERNAL_SOURCE_ARTIFACT_DIGESTS_BOUND_AWAITING_INDEPENDENT_LEGAL_PRIVACY_REVIEW_NOT_GATE_EVIDENCE",
        "service_id": service_id,
        "stage75_relationship_status": service.get("relationship_status"),
        "stage75_relationship_status_is_legal_classification": False,
        "collected_at_utc": collected_at_utc,
        "collection_reference_sha256": sha256_bytes(collection_ref.encode("utf-8")),
        "provider_input_sha256": sha256_file(input_path),
        "artifact_sha256": artifact_sha256,
        "artifact_paths_copied": False,
        "artifact_contents_copied": False,
        "secret_values_copied": False,
        "provider_facts_extracted_or_attested": False,
        "provider_legal_entity_verified": False,
        "contract_or_dpa_sufficiency_verified": False,
        "processing_regions_verified": False,
        "retention_terms_verified": False,
        "subprocessor_chain_verified": False,
        "transfer_mechanism_legality_verified": False,
        "legal_relationship_classified": False,
        "cloudflare_direct_contract_proven_by_collector": False,
        "github_production_authority_proven_by_collector": False,
        "asaas_credentials_or_activation_proven_by_collector": False,
        "billing_credential_evidence": False,
        "checkout_proof": False,
        "production_deployment_evidence": False,
        "target_open_decision_closed": False,
        "legal_gate_ready_attested": False,
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
        "next_action": "INDEPENDENT_LEGAL_PRIVACY_REVIEW_OF_REAL_SOURCE_ARTIFACTS_REQUIRED_BEFORE_PROVIDER_MAP_DECISION",
    }

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(candidate, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

    print("STAGE76_PROVIDER_EVIDENCE_CANDIDATE=PASS_DIGEST_ONLY")
    print(f"SERVICE_ID={service_id}")
    print("PROVIDER_FACTS_ATTESTED=false")
    print("LEGAL_RELATIONSHIP_CLASSIFIED=false")
    print("TARGET_DECISION_CLOSED=false")
    print("LEGAL_GATE_READY=false")
    print("REMOTE_MUTATION=false")


if __name__ == "__main__":
    main()
