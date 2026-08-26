from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage75_technical_external_provider_inventory_authority.json"
REGISTRY = ROOT / "10_compliance" / "inventory" / "STAGE75_TECHNICAL_EXTERNAL_SERVICE_SOURCE_REGISTRY.json"
OPEN_DECISIONS = ROOT / "10_compliance" / "drafts" / "COMPLIANCE_OPEN_DECISIONS.json"
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
FAILURE_CLASS = "BGF-STAGE75-TECHNICAL-PROVIDER-INVENTORY-GUARD-725"

EXPECTED_IDS = [
    "supabase",
    "telegram_bot_api",
    "asaas",
    "cloudflare_edge_signal",
    "github_repository_ci_pages",
]
REQUIRED_UNKNOWN_FIELDS = [
    "provider_legal_entity",
    "contract_or_dpa_reference",
    "processing_regions",
    "retention_terms",
    "international_transfer_mechanism",
    "subprocessor_chain",
    "legal_relationship_classification",
]


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE75_TECHNICAL_EXTERNAL_PROVIDER_INVENTORY=FAIL\n"
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


def read_source(path_text: str) -> tuple[Path, str]:
    path = (ROOT / path_text).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError:
        fail(f"source path escapes repository: {path_text}")
    if not path.is_file():
        fail(f"source artifact missing: {path_text}")
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        fail(f"source artifact must be UTF-8 text: {path_text}")
    return path, text


def validate_target_decision(decisions: dict) -> dict:
    if decisions.get("status") != "DRAFT_UNREVIEWED_NOT_EVIDENCE":
        fail("Stage67 open-decision registry status drift")
    unresolved = decisions.get("unresolved")
    if not isinstance(unresolved, list):
        fail("Stage67 unresolved decisions missing")
    target = next(
        (item for item in unresolved if isinstance(item, dict) and item.get("id") == "SUBPROCESSOR_AND_TRANSFER_MAP"),
        None,
    )
    if not isinstance(target, dict):
        fail("SUBPROCESSOR_AND_TRANSFER_MAP decision missing")
    if target.get("state") != "OPEN":
        fail("SUBPROCESSOR_AND_TRANSFER_MAP must remain OPEN")
    if sorted(target.get("applies_to", [])) != ["legal_privacy_notice", "legal_role_mapping"]:
        fail("SUBPROCESSOR_AND_TRANSFER_MAP affected-gate set drift")
    if target.get("resolution_authority") != "provider evidence plus legal/privacy review":
        fail("SUBPROCESSOR_AND_TRANSFER_MAP resolution authority drift")
    return target


def validate_service(service: dict, remote: dict) -> dict:
    service_id = str(service.get("service_id", "")).strip()
    if service_id not in EXPECTED_IDS:
        fail(f"unknown service id: {service_id}")
    relationship = str(service.get("relationship_status", "")).strip()
    purposes = service.get("technical_purposes_observed")
    paths = service.get("source_artifacts")
    markers = service.get("source_claim_markers")
    if not relationship:
        fail(f"relationship status missing: {service_id}")
    if not isinstance(purposes, list) or not purposes or not all(isinstance(v, str) and v.strip() for v in purposes):
        fail(f"technical purposes missing: {service_id}")
    if not isinstance(paths, list) or not paths or not all(isinstance(v, str) and v.strip() for v in paths):
        fail(f"source artifacts missing: {service_id}")
    if not isinstance(markers, list) or not markers or not all(isinstance(v, str) and v for v in markers):
        fail(f"source claim markers missing: {service_id}")

    source_bindings = []
    combined = ""
    for raw in paths:
        path, text = read_source(raw)
        combined += "\n" + text
        source_bindings.append(
            {
                "path": raw,
                "sha256": sha256_file(path),
            }
        )
    for marker in markers:
        if marker not in combined:
            fail(f"source claim marker not found for {service_id}: {marker}")

    for key in REQUIRED_UNKNOWN_FIELDS:
        value = str(service.get(key, "")).strip()
        if not value or not (value.startswith("UNKNOWN_") or value.startswith("UNRESOLVED_")):
            fail(f"{service_id} must preserve unresolved external field: {key}")

    if service_id == "supabase":
        if relationship != "CONFIRMED_ACTIVE_DIRECT_TECHNICAL_SERVICE":
            fail("Supabase relationship status drift")
        if service.get("customer_data_processing_possible_from_repo_design") is not True:
            fail("Supabase design may process customer data and must not be understated")
        if service.get("current_customer_rows_observed") != 0:
            fail("Supabase current customer row observation drift")
        if any(remote.get(key) != 0 for key in ("auth_users", "organizations", "students")):
            fail("fresh remote customer counts no longer match Stage75 registry")
    elif service_id == "telegram_bot_api":
        if relationship != "CONFIRMED_ACTIVE_EXTERNAL_ALERT_DELIVERY_SERVICE":
            fail("Telegram relationship status drift")
        if service.get("payload_direct_student_identifiers_forbidden_by_contract") is not True:
            fail("Telegram payload minimization boundary drift")
        if service.get("controlled_proof_used_real_customer_data") is not False:
            fail("Telegram controlled proof must remain explicitly non-customer")
        if service.get("customer_data_processing_possible_from_repo_design") is not False:
            fail("Stage75 must not generalize Telegram controlled alert design into customer-data processing")
    elif service_id == "asaas":
        if relationship != "SELECTED_PRODUCTION_BILLING_PROVIDER_NOT_ACTIVATED":
            fail("Asaas relationship status drift")
        for key in ("production_credentials_verified", "provider_activation_observed", "real_checkout_proof_completed"):
            if service.get(key) is not False:
                fail(f"Asaas premature activation/proof claim: {key}")
        if remote.get("asaas_state") != "selected_pending_credentials" or remote.get("asaas_activated_at") is not None:
            fail("fresh remote Asaas state no longer matches Stage75 source registry")
    elif service_id == "cloudflare_edge_signal":
        if relationship != "INDIRECT_INFRASTRUCTURE_SIGNAL_OBSERVED_CONTRACTUAL_RELATIONSHIP_UNVERIFIED":
            fail("Cloudflare edge-signal relationship status drift")
        for key in ("direct_contract_with_fitnexus_proven", "direct_provider_selection_by_fitnexus_proven"):
            if service.get(key) is not False:
                fail(f"Cloudflare direct relationship must not be inferred: {key}")
        if service.get("must_not_be_called_confirmed_subprocessor_from_repo_evidence") is not True:
            fail("Cloudflare legal relationship caveat missing")
    elif service_id == "github_repository_ci_pages":
        if relationship != "CONFIRMED_REPOSITORY_CI_SERVICE_STALE_PUBLIC_PAGES_SURFACE_NOT_CURRENT_PRODUCTION_AUTHORITY":
            fail("GitHub relationship status drift")
        if service.get("current_pages_surface_is_production_deployment_evidence") is not False:
            fail("stale GitHub Pages surface cannot be production deployment evidence")
        if service.get("customer_data_processing_by_pages_or_ci_attested") is not False:
            fail("Stage75 must not invent customer-data processing by GitHub Pages/CI")

    external_gaps = []
    for key in REQUIRED_UNKNOWN_FIELDS:
        external_gaps.append({"field": key, "state": service[key], "resolved": False})

    passthrough_keys = sorted(
        key
        for key in service
        if key
        not in {
            "source_artifacts",
            "source_claim_markers",
            *REQUIRED_UNKNOWN_FIELDS,
        }
    )
    observed = {key: service[key] for key in passthrough_keys}

    return {
        "service_id": service_id,
        "display_name": service.get("display_name"),
        "relationship_status": relationship,
        "technical_purposes_observed": list(purposes),
        "observed_source_claims": observed,
        "source_bindings": sorted(source_bindings, key=lambda item: item["path"]),
        "external_completion_gaps": external_gaps,
        "legal_relationship_classified": False,
        "confirmed_subprocessor": False,
        "provider_terms_verified": False,
        "processing_regions_verified": False,
        "retention_verified": False,
        "transfer_mechanism_verified": False,
        "inventory_row_is_evidence": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    source_sha = args.source_sha.strip().lower()
    if not SHA1_RE.fullmatch(source_sha):
        fail("--source-sha must be exact 40-character lower-hex Git SHA")

    authority = load_json(AUTHORITY)
    registry = load_json(REGISTRY)
    decisions = load_json(OPEN_DECISIONS)

    if authority.get("stage") != "STAGE75_TECHNICAL_EXTERNAL_PROVIDER_INVENTORY_CANDIDATE":
        fail("Stage75 authority drift")
    contract = authority.get("inventory_contract")
    if not isinstance(contract, dict):
        fail("Stage75 inventory contract missing")
    if contract.get("service_count") != 5 or contract.get("expected_service_ids") != EXPECTED_IDS:
        fail("Stage75 expected service inventory drift")

    target = validate_target_decision(decisions)
    if registry.get("status") != "TECHNICAL_SOURCE_REGISTRY_NOT_LEGAL_PROVIDER_MAP_NOT_EVIDENCE":
        fail("Stage75 source registry status drift")
    services = registry.get("services")
    if not isinstance(services, list) or len(services) != 5:
        fail("Stage75 source registry must contain exactly five services")
    ids = [str(item.get("service_id", "")) for item in services if isinstance(item, dict)]
    if ids != EXPECTED_IDS or len(set(ids)) != 5:
        fail("Stage75 source registry service order/set drift")

    boundaries = registry.get("hard_boundaries")
    if not isinstance(boundaries, dict):
        fail("Stage75 source-registry hard boundaries missing")
    for key in (
        "registry_is_legal_subprocessor_map",
        "registry_is_provider_contract_evidence",
        "registry_is_transfer_assessment",
        "registry_is_retention_assessment",
        "registry_can_close_subprocessor_transfer_decision",
        "registry_can_mark_legal_gate_ready",
        "registry_can_create_evidence_ref_or_digest",
        "registry_can_promote_launch",
    ):
        if boundaries.get(key) is not False:
            fail(f"Stage75 source registry boundary drift: {key}")

    remote = authority.get("fresh_remote_read_only_receipt")
    if not isinstance(remote, dict):
        fail("Stage75 fresh remote receipt missing")
    if remote.get("remote_mutation_performed") is not False:
        fail("Stage75 fresh remote receipt must preserve no-mutation boundary")

    rows = [validate_service(item, remote) for item in services]
    source_count = len({binding["path"] for row in rows for binding in row["source_bindings"]})
    gap_count = sum(len(row["external_completion_gaps"]) for row in rows)

    inventory = {
        "schema_version": 1,
        "stage": "STAGE75_TECHNICAL_EXTERNAL_PROVIDER_INVENTORY_CANDIDATE",
        "output_kind": "NON_ATTESTING_SOURCE_DERIVED_TECHNICAL_EXTERNAL_SERVICE_INVENTORY",
        "inventory_state": "TECHNICAL_SERVICE_RELATIONSHIPS_OBSERVED_LEGAL_PROVIDER_MAP_UNRESOLVED",
        "source_commit_sha": source_sha,
        "source_sha256": {
            "stage75_authority": sha256_file(AUTHORITY),
            "stage75_source_registry": sha256_file(REGISTRY),
            "stage67_open_decisions": sha256_file(OPEN_DECISIONS),
        },
        "target_open_decision": {
            "id": target["id"],
            "state": "OPEN",
            "affected_gates": sorted(target.get("applies_to", [])),
            "required": target.get("required"),
            "resolution_authority": target.get("resolution_authority"),
            "closed_by_stage75": False,
        },
        "summary": {
            "service_count": len(rows),
            "unique_repository_source_artifact_count": source_count,
            "external_completion_gap_count": gap_count,
            "confirmed_legal_subprocessor_count": 0,
            "verified_provider_contract_count": 0,
            "verified_processing_region_count": 0,
            "verified_transfer_mechanism_count": 0,
            "legal_gate_ready_count": 0,
        },
        "services": rows,
        "fresh_remote_read_only_receipt": dict(remote),
        "guardrails": {
            "technical_relationship_is_legal_classification": False,
            "inventory_is_provider_evidence": False,
            "inventory_is_legal_review": False,
            "inventory_closes_target_decision": False,
            "provider_contract_facts_fabricated": False,
            "provider_regions_fabricated": False,
            "retention_terms_fabricated": False,
            "transfer_mechanisms_fabricated": False,
            "evidence_ref_created": False,
            "evidence_digest_promoted": False,
            "evidence_migration_created": False,
            "supabase_mutation_performed": False,
            "provider_call_performed": False,
            "deployment_performed": False,
            "controlled_launch_promoted": False,
            "paid_media_promoted": False,
        },
        "next_action": "OBTAIN_REAL_PROVIDER_TERMS_REGION_RETENTION_TRANSFER_EVIDENCE_THEN_INDEPENDENT_LEGAL_PRIVACY_REVIEW",
    }

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(inventory, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

    print("STAGE75_TECHNICAL_EXTERNAL_PROVIDER_INVENTORY=PASS_NON_ATTESTING")
    print(f"SERVICE_COUNT={len(rows)}")
    print(f"SOURCE_ARTIFACT_COUNT={source_count}")
    print(f"EXTERNAL_COMPLETION_GAPS={gap_count}")
    print("CONFIRMED_LEGAL_SUBPROCESSORS=0")
    print("TARGET_DECISION_CLOSED=false")
    print("LEGAL_GATE_READY=false")
    print("REMOTE_MUTATION=false")


if __name__ == "__main__":
    main()
