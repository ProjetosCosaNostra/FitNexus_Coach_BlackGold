from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage90_terms_independent_review_readiness_authority.json"
CONTRACT = ROOT / "10_compliance" / "drafts" / "STAGE90_TERMS_INDEPENDENT_REVIEW_READINESS_CONTRACT.json"
TERMS = ROOT / "10_compliance" / "drafts" / "TERMS_OF_USE_CANDIDATE_PTBR.md"
DECISIONS = ROOT / "10_compliance" / "drafts" / "COMPLIANCE_OPEN_DECISIONS.json"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
FAILURE = "BGF-STAGE90-INDEPENDENT-REVIEW-READINESS-GUARD-892"


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE90_TERMS_INDEPENDENT_REVIEW_PACKET=FAIL\n"
        f"FAILURE_CLASS={FAILURE}\nDETAIL={detail}"
    )


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"load failed {path.relative_to(ROOT)}:{type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"expected object {path.relative_to(ROOT)}")
    return value


def blob(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    source_sha = args.source_sha.strip().lower()
    if SHA40.fullmatch(source_sha) is None:
        fail("invalid source sha")

    authority = load(AUTHORITY)
    contract = load(CONTRACT)
    decisions = load(DECISIONS)
    if blob(AUTHORITY) != "46add4066e15598562eeedb799d201efccf4cad1":
        fail("Stage90 authority blob drift")
    pins = authority.get("sealed_inputs", {})
    for key, path in (
        ("review_contract_blob", CONTRACT),
        ("terms_draft_blob", TERMS),
        ("open_decisions_blob", DECISIONS),
    ):
        if pins.get(key) != blob(path):
            fail(f"sealed input drift:{key}")

    terms_text = TERMS.read_text(encoding="utf-8")
    if "DRAFT_UNREVIEWED_NOT_PUBLISHED_NOT_LEGAL_EVIDENCE" not in terms_text:
        fail("draft non-evidence marker missing")
    if "legal_terms_of_use = BLOCKED" not in terms_text:
        fail("draft legal gate marker missing")

    unresolved = decisions.get("unresolved")
    by_id = {row.get("id"): row for row in unresolved if isinstance(row, dict)} if isinstance(unresolved, list) else {}
    required_open = (
        "LEGAL_ENTITY_IDENTITY",
        "LEGAL_REVIEWER_REFERENCE",
        "BILLING_CANCELLATION_REFUND_POLICY",
        "RETENTION_MATRIX",
        "TERMS_ACCEPTANCE_VERSIONING",
    )
    for decision_id in required_open:
        if by_id.get(decision_id, {}).get("state") != "OPEN":
            fail(f"required decision not OPEN:{decision_id}")

    blockers = contract.get("review_blockers")
    if not isinstance(blockers, list) or len(blockers) != 7:
        fail("review blocker count drift")

    packet = {
        "schema_version": 1,
        "stage": "STAGE90_TERMS_INDEPENDENT_REVIEW_READINESS",
        "output_kind": "NON_ATTESTING_EXACT_DRAFT_INDEPENDENT_REVIEW_PACKET",
        "source_sha": source_sha,
        "draft": {
            "path": str(TERMS.relative_to(ROOT)).replace("\\", "/"),
            "git_blob_sha": blob(TERMS),
            "sha256": sha256(TERMS),
            "status": "DRAFT_UNREVIEWED_NOT_PUBLISHED_NOT_LEGAL_EVIDENCE",
            "approved": False,
            "published": False,
            "legal_evidence": False,
        },
        "review_blockers": blockers,
        "required_open_decisions": [
            {
                "id": decision_id,
                "state": by_id[decision_id].get("state"),
                "required": by_id[decision_id].get("required"),
                "resolution_authority": by_id[decision_id].get("resolution_authority"),
            }
            for decision_id in required_open
        ],
        "reviewer_must_return": contract.get("reviewer_must_return"),
        "forbidden_shortcuts": contract.get("forbidden_shortcuts"),
        "captured_remote_nonregistration_receipt": authority.get("fresh_remote_nonregistration_receipt"),
        "hard_boundaries": {
            "supabase_mutation_performed": False,
            "terms_registry_row_created": False,
            "real_acceptance_collected": False,
            "terms_acceptance_versioning_closed": False,
            "legal_terms_gate_ready": False,
        },
        "next_after_green": authority.get("next_after_green"),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("STAGE90_TERMS_INDEPENDENT_REVIEW_PACKET=PASS")
    print(f"TERMS_DRAFT_SHA256={packet['draft']['sha256']}")
    print("REVIEW_BLOCKERS=7")
    print("EXTERNAL_INDEPENDENT_REVIEW=REQUIRED_NOT_SUPPLIED")
    print("LEGAL_TERMS_GATE_READY=false")


if __name__ == "__main__":
    main()
