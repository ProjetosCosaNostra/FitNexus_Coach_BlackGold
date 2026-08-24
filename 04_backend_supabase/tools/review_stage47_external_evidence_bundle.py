from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

FAILURE_CLASS = "BGF-STAGE47-UNIFIED-EXTERNAL-EVIDENCE-INTAKE-GUARD-442"
MAX_RECEIPT_BYTES = 1024 * 1024

SPECS: tuple[dict[str, str], ...] = (
    {
        "gate_code": "billing_provider_credentials",
        "source_stage": "STAGE39_BILLING_CREDENTIAL_AUTHORITY_EXTERNAL_EVIDENCE",
        "reviewer": "04_backend_supabase/tools/review_stage39_billing_credential_evidence_receipt.py",
    },
    {
        "gate_code": "legal_terms_of_use",
        "source_stage": "STAGE41_LEGAL_TERMS_EXTERNAL_EVIDENCE_PREPARATION",
        "reviewer": "04_backend_supabase/tools/review_stage41_legal_terms_evidence_receipt.py",
    },
    {
        "gate_code": "legal_privacy_notice",
        "source_stage": "STAGE42_PRIVACY_NOTICE_EXTERNAL_EVIDENCE_PREPARATION",
        "reviewer": "04_backend_supabase/tools/review_stage42_privacy_notice_evidence_receipt.py",
    },
    {
        "gate_code": "legal_role_mapping",
        "source_stage": "STAGE43_LEGAL_ROLE_MAPPING_EXTERNAL_EVIDENCE_PREPARATION",
        "reviewer": "04_backend_supabase/tools/review_stage43_legal_role_mapping_evidence_receipt.py",
    },
    {
        "gate_code": "data_subject_request_channel",
        "source_stage": "STAGE44_DATA_SUBJECT_REQUEST_EXTERNAL_EVIDENCE_PREPARATION",
        "reviewer": "04_backend_supabase/tools/review_stage44_data_subject_request_evidence_receipt.py",
    },
    {
        "gate_code": "incident_response",
        "source_stage": "STAGE45_INCIDENT_RESPONSE_EXTERNAL_EVIDENCE_PREPARATION",
        "reviewer": "04_backend_supabase/tools/review_stage45_incident_response_evidence_receipt.py",
    },
    {
        "gate_code": "production_deployment",
        "source_stage": "STAGE46_PRODUCTION_DEPLOYMENT_EXTERNAL_EVIDENCE_PREPARATION",
        "reviewer": "04_backend_supabase/tools/review_stage46_production_deployment_evidence_receipt.py",
    },
)

SPEC_BY_STAGE = {spec["source_stage"]: spec for spec in SPECS}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 128), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_load_stage(path: Path) -> tuple[str | None, bool]:
    try:
        if path.stat().st_size > MAX_RECEIPT_BYTES:
            return None, False
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None, False
    if not isinstance(value, dict):
        return None, False
    stage = value.get("stage")
    if not isinstance(stage, str) or not stage:
        return None, False
    return stage, True


def review_one(repo_root: Path, receipt: Path, reviewer_rel: str) -> int:
    reviewer = repo_root / reviewer_rel
    if not reviewer.is_file():
        return 127
    completed = subprocess.run(
        [sys.executable, str(reviewer), str(receipt)],
        cwd=str(repo_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    # Canonical reviewer output is intentionally discarded. The aggregate stores
    # only the exit code/status so an unexpected reviewer diagnostic cannot leak
    # source material into the Stage47 aggregate receipt.
    return int(completed.returncode)


def make_authority_flags() -> dict[str, bool]:
    return {
        "gate_ready_attested": False,
        "evidence_migration_created": False,
        "controlled_launch_promoted": False,
        "provider_call_performed": False,
        "provider_activation_performed": False,
        "deployment_action_performed": False,
        "supabase_mutation_performed": False,
        "network_call_performed": False,
        "raw_receipt_content_copied": False,
        "receipt_path_or_filename_copied": False,
        "canonical_reviewer_stdout_or_stderr_copied": False,
        "stage35_alert_proof_alone_can_satisfy_production_deployment": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Locally inventory/review Stage39 and Stage41-46 digest-only evidence receipts without attestation."
    )
    parser.add_argument("--bundle-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--mode", choices=("inventory", "complete"), default="inventory")
    args = parser.parse_args()

    bundle_dir = args.bundle_dir.resolve()
    output = args.output.resolve()
    repo_root = Path(__file__).resolve().parents[2]

    if not bundle_dir.is_dir():
        raise SystemExit(
            f"STAGE47_EXTERNAL_EVIDENCE_BUNDLE_REVIEW=FAIL\nFAILURE_CLASS={FAILURE_CLASS}\nDETAIL=bundle directory missing"
        )

    grouped: dict[str, list[Path]] = {stage: [] for stage in SPEC_BY_STAGE}
    unknown_json_receipt_count = 0

    for candidate in sorted(bundle_dir.glob("*.json")):
        try:
            if candidate.resolve() == output:
                continue
        except OSError:
            unknown_json_receipt_count += 1
            continue
        stage, structurally_readable = safe_load_stage(candidate)
        if not structurally_readable or stage not in SPEC_BY_STAGE:
            unknown_json_receipt_count += 1
            continue
        grouped[stage].append(candidate)

    entries: list[dict[str, Any]] = []
    valid_count = 0
    missing_count = 0
    duplicate_count = 0
    invalid_count = unknown_json_receipt_count

    for spec in SPECS:
        stage = spec["source_stage"]
        candidates = grouped[stage]
        entry: dict[str, Any] = {
            "gate_code": spec["gate_code"],
            "source_stage": stage,
            "canonical_reviewer_module": Path(spec["reviewer"]).name,
            "status": "MISSING",
            "receipt_sha256": None,
            "reviewer_exit_code": None,
            "gate_ready": False,
            "independent_review_required": True,
        }

        if not candidates:
            missing_count += 1
        elif len(candidates) > 1:
            entry["status"] = "DUPLICATE"
            entry["receipt_sha256"] = sorted(sha256_file(path) for path in candidates)
            duplicate_count += 1
            invalid_count += 1
        else:
            receipt = candidates[0]
            digest = sha256_file(receipt)
            exit_code = review_one(repo_root, receipt, spec["reviewer"])
            entry["receipt_sha256"] = digest
            entry["reviewer_exit_code"] = exit_code
            if exit_code == 0:
                entry["status"] = "VALID_FOR_INDEPENDENT_REVIEW_ONLY"
                valid_count += 1
            else:
                entry["status"] = "INVALID_BY_CANONICAL_REVIEWER"
                invalid_count += 1
        entries.append(entry)

    if invalid_count:
        overall = "INVALID_EXTERNAL_EVIDENCE_CANDIDATE_PRESENT"
    elif missing_count:
        overall = "INCOMPLETE_MISSING_EXTERNAL_EVIDENCE"
    else:
        overall = "COMPLETE_STRUCTURAL_CANDIDATES_AWAITING_INDEPENDENT_REVIEW"

    aggregate = {
        "schema_version": 1,
        "stage": "STAGE47_UNIFIED_EXTERNAL_EVIDENCE_INTAKE_ORCHESTRATION",
        "mode": args.mode,
        "overall_state": overall,
        "expected_receipt_count": len(SPECS),
        "valid_structural_candidate_count": valid_count,
        "missing_receipt_count": missing_count,
        "duplicate_source_stage_count": duplicate_count,
        "unknown_or_unreadable_json_receipt_count": unknown_json_receipt_count,
        "invalid_candidate_count": invalid_count,
        "entries": entries,
        "authority_flags": make_authority_flags(),
        "next_action": "INDEPENDENT_SOURCE_ARTIFACT_REVIEW_REQUIRED_BEFORE_ANY_VERSIONED_EVIDENCE_MIGRATION",
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(aggregate, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"STAGE47_EXTERNAL_EVIDENCE_BUNDLE_STATE={overall}")
    print(f"VALID_STRUCTURAL_CANDIDATES={valid_count}")
    print(f"MISSING={missing_count}")
    print(f"INVALID={invalid_count}")
    print("GATE_READY=false")
    print("REMOTE_MUTATION=false")

    if invalid_count:
        return 2
    if args.mode == "complete" and missing_count:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
