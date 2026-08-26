from __future__ import annotations

# PR synchronize marker: dedicated Stage84 workflow now exists in the head before this commit.

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage84_terms_acceptance_versioning_preparation_authority.json"
INVENTORY = ROOT / "10_compliance" / "inventory" / "STAGE84_TERMS_ACCEPTANCE_VERSIONING_IMPLEMENTATION_PREPARATION.json"
OPEN_DECISIONS = ROOT / "10_compliance" / "drafts" / "COMPLIANCE_OPEN_DECISIONS.json"
TERMS_DRAFT = ROOT / "10_compliance" / "drafts" / "TERMS_OF_USE_CANDIDATE_PTBR.md"
STAGE83 = BACKEND / "stage83_billing_policy_review_questionnaire_skeleton_authority.json"
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
FAILURE_CLASS = "BGF-STAGE84-TERMS-ACCEPTANCE-VERSIONING-PREPARATION-GUARD-839"
CANONICAL_REQUIRED = "Production mechanism binding user acceptance to immutable terms version/digest."
CANONICAL_RESOLUTION = "product implementation plus independent review"


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE84_TERMS_ACCEPTANCE_VERSIONING_PREPARATION=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\nDETAIL={detail}"
    )


def load_json(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to load {label}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"{label} must be a JSON object")
    return value


def git_blob_sha(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(f"blob {len(raw)}\0".encode("utf-8") + raw).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_decision() -> dict:
    decisions = load_json(OPEN_DECISIONS, "open decisions")
    unresolved = decisions.get("unresolved")
    target = next(
        (row for row in unresolved if isinstance(row, dict) and row.get("id") == "TERMS_ACCEPTANCE_VERSIONING"),
        None,
    ) if isinstance(unresolved, list) else None
    if not isinstance(target, dict):
        fail("TERMS_ACCEPTANCE_VERSIONING missing")
    if target.get("state") != "OPEN" or target.get("applies_to") != ["legal_terms_of_use"]:
        fail("canonical terms acceptance decision state/scope drift")
    if target.get("required") != CANONICAL_REQUIRED or target.get("resolution_authority") != CANONICAL_RESOLUTION:
        fail("canonical terms acceptance decision wording drift")
    return target


def validate_sources() -> tuple[dict, dict]:
    authority = load_json(AUTHORITY, "Stage84 authority")
    if authority.get("stage") != "STAGE84_TERMS_ACCEPTANCE_VERSIONING_IMPLEMENTATION_PREPARATION":
        fail("Stage84 authority identity drift")
    if authority.get("baseline_main_sha") != "07366968780d6efa732022237116eb7f79201646":
        fail("Stage84 baseline main SHA drift")

    pins = authority.get("sealed_inputs", {})
    expected_pins = {
        OPEN_DECISIONS: pins.get("open_decisions_blob"),
        TERMS_DRAFT: pins.get("terms_candidate_blob"),
        STAGE83: pins.get("stage83_authority_blob"),
    }
    for path, expected in expected_pins.items():
        if not isinstance(expected, str) or git_blob_sha(path) != expected:
            fail(f"sealed upstream source drift: {path.relative_to(ROOT)}")

    terms_text = TERMS_DRAFT.read_text(encoding="utf-8")
    for marker in (
        "DRAFT_UNREVIEWED_NOT_PUBLISHED_NOT_LEGAL_EVIDENCE",
        "`terms_version` imutável",
        "digest SHA-256 do documento aprovado",
        "evidência de aceite vinculada à versão",
        "Mecanismo real de aceite versionado",
        "legal_terms_of_use = BLOCKED",
    ):
        if marker not in terms_text:
            fail(f"terms draft source marker missing: {marker}")

    stage83 = load_json(STAGE83, "Stage83 authority")
    if stage83.get("canonical_target_open_decision", {}).get("id") != "BILLING_CANCELLATION_REFUND_POLICY":
        fail("Stage83 source identity drift")
    if stage83.get("hard_boundaries", {}).get("terms_of_use_modified") is not False:
        fail("Stage83 unexpectedly modified Terms")

    inventory = load_json(INVENTORY, "Stage84 inventory")
    if inventory.get("status") != "TECHNICAL_IMPLEMENTATION_PREPARATION_ONLY_NOT_TERMS_NOT_APPROVAL_NOT_EVIDENCE":
        fail("Stage84 inventory status drift")
    units = inventory.get("implementation_units")
    ids = [row.get("unit_id") for row in units if isinstance(row, dict)] if isinstance(units, list) else []
    if ids != ["terms_document_registry", "terms_acceptance_ledger", "current_terms_resolver", "acceptance_gate"]:
        fail("Stage84 implementation-unit identity/order drift")
    boundaries = inventory.get("stage84_boundaries", {})
    if not boundaries or any(value is not False for value in boundaries.values()):
        fail("Stage84 inventory must remain non-mutating and non-attesting")
    return authority, inventory


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    source_sha = args.source_sha.strip().lower()
    if SHA40_RE.fullmatch(source_sha) is None:
        fail("source-sha must be exact lowercase 40-character Git SHA")

    canonical = canonical_decision()
    authority, inventory = validate_sources()
    output = {
        "schema_version": 1,
        "stage": "STAGE84_TERMS_ACCEPTANCE_VERSIONING_IMPLEMENTATION_PREPARATION",
        "output_kind": "NON_ATTESTING_TERMS_ACCEPTANCE_VERSIONING_PREPARATION_PACKET",
        "state": "TECHNICAL_PREPARATION_GREEN_CANDIDATE_NO_SCHEMA_MUTATION_NO_APPROVED_TERMS_NO_ACCEPTANCE_COLLECTION",
        "source_sha": source_sha,
        "canonical_target_open_decision": {
            "id": canonical["id"],
            "state": canonical["state"],
            "applies_to": canonical["applies_to"],
            "required": canonical["required"],
            "resolution_authority": canonical["resolution_authority"],
        },
        "source_bindings": {
            "authority_git_blob": git_blob_sha(AUTHORITY),
            "inventory_git_blob": git_blob_sha(INVENTORY),
            "inventory_sha256": sha256_file(INVENTORY),
            "open_decisions_git_blob": git_blob_sha(OPEN_DECISIONS),
            "terms_candidate_git_blob": git_blob_sha(TERMS_DRAFT),
            "stage83_authority_git_blob": git_blob_sha(STAGE83),
        },
        "implementation_unit_count": len(inventory["implementation_units"]),
        "implementation_units": [row["unit_id"] for row in inventory["implementation_units"]],
        "hard_boundaries": {
            "terms_candidate_approved": False,
            "terms_candidate_published": False,
            "real_acceptance_collected": False,
            "schema_migration_created": False,
            "remote_mutation": False,
            "target_decision_closed": False,
            "legal_terms_gate_ready": False,
            "deployment": False,
            "controlled_launch_promoted": False,
            "paid_media_promoted": False,
        },
        "next_after_green": authority["next_after_green"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("STAGE84_TERMS_ACCEPTANCE_VERSIONING_PREPARATION=PASS")
    print("IMPLEMENTATION_UNIT_COUNT=4")
    print("TERMS_CANDIDATE_APPROVED=false")
    print("REAL_ACCEPTANCE_COLLECTED=false")
    print("SCHEMA_MIGRATION_CREATED=false")
    print("REMOTE_MUTATION=false")
    print("TARGET_DECISION_CLOSED=false")
    print("LEGAL_TERMS_GATE_READY=false")


if __name__ == "__main__":
    main()
