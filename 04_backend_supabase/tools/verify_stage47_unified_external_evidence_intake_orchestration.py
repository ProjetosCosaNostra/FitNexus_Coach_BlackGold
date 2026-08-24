from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

FAILURE_CLASS = "BGF-STAGE47-UNIFIED-EXTERNAL-EVIDENCE-INTAKE-GUARD-442"
ROOT = Path(__file__).resolve().parents[2]
AUTHORITY = ROOT / "04_backend_supabase/stage47_unified_external_evidence_intake_orchestration_authority.json"
ORCHESTRATOR = ROOT / "04_backend_supabase/tools/review_stage47_external_evidence_bundle.py"
MIGRATIONS = ROOT / "04_backend_supabase/migrations"

EXPECTED_BASELINE = "652848909e5e0eb1cee3ee5b85a25020b6ca9485"
EXPECTED_STATE = "PREPARED_UNIFIED_LOCAL_RECEIPT_REVIEW_ORCHESTRATION_NO_EVIDENCE_INGESTION_NO_GATE_PROMOTION_NO_REMOTE_MUTATION"
EXPECTED_REVIEWERS = (
    ("billing_provider_credentials", "STAGE39_BILLING_CREDENTIAL_AUTHORITY_EXTERNAL_EVIDENCE", "04_backend_supabase/tools/review_stage39_billing_credential_evidence_receipt.py", "9caf186172eff35ea3f216b86565a3a98387a5cd"),
    ("legal_terms_of_use", "STAGE41_LEGAL_TERMS_EXTERNAL_EVIDENCE_PREPARATION", "04_backend_supabase/tools/review_stage41_legal_terms_evidence_receipt.py", "f846a334b29e8a221789dfba46f2d9fee2fbbb92"),
    ("legal_privacy_notice", "STAGE42_PRIVACY_NOTICE_EXTERNAL_EVIDENCE_PREPARATION", "04_backend_supabase/tools/review_stage42_privacy_notice_evidence_receipt.py", "f07ab6154ca83badb2093dff84a3b67b4324b3ef"),
    ("legal_role_mapping", "STAGE43_LEGAL_ROLE_MAPPING_EXTERNAL_EVIDENCE_PREPARATION", "04_backend_supabase/tools/review_stage43_legal_role_mapping_evidence_receipt.py", "6718d2376fdacfc92158504b87177c2ad6935394"),
    ("data_subject_request_channel", "STAGE44_DATA_SUBJECT_REQUEST_EXTERNAL_EVIDENCE_PREPARATION", "04_backend_supabase/tools/review_stage44_data_subject_request_evidence_receipt.py", "caec56a1e00f6d2c32e90ab2c6a42bd7a28f62c1"),
    ("incident_response", "STAGE45_INCIDENT_RESPONSE_EXTERNAL_EVIDENCE_PREPARATION", "04_backend_supabase/tools/review_stage45_incident_response_evidence_receipt.py", "8ac25b8d8c89242b9ae357630a66b820e1801c68"),
    ("production_deployment", "STAGE46_PRODUCTION_DEPLOYMENT_EXTERNAL_EVIDENCE_PREPARATION", "04_backend_supabase/tools/review_stage46_production_deployment_evidence_receipt.py", "80ec9db645a58950b956898dd227a6b1c9f0b2ab"),
)
EXPECTED_FAILURE_CLASSES = {
    "BGF-STAGE47-AGGREGATE-SELF-ATTESTATION-433",
    "BGF-STAGE47-CANONICAL-REVIEWER-BYPASS-434",
    "BGF-STAGE47-DUPLICATE-RECEIPT-AMBIGUITY-435",
    "BGF-STAGE47-UNRECOGNIZED-RECEIPT-MASQUERADE-436",
    "BGF-STAGE47-AGGREGATE-GATE-PROMOTION-437",
    "BGF-STAGE47-RAW-RECEIPT-DATA-LEAKAGE-438",
    "BGF-STAGE47-NETWORK-OR-REMOTE-MUTATION-439",
    "BGF-STAGE47-STAGE35-PRODUCTION-SUBSTITUTION-440",
    "BGF-STAGE47-INCOMPLETE-BUNDLE-FALSE-GREEN-441",
    "BGF-STAGE47-UNIFIED-EXTERNAL-EVIDENCE-INTAKE-GUARD-442",
}


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE47_UNIFIED_EXTERNAL_EVIDENCE_INTAKE_GUARD=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\n"
        f"DETAIL={detail}"
    )


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def require_false(mapping: dict[str, Any], key: str) -> None:
    if mapping.get(key) is not False:
        fail(f"authority flag must remain false: {key}")


def main() -> None:
    try:
        authority = json.loads(AUTHORITY.read_text(encoding="utf-8"))
        source = ORCHESTRATOR.read_text(encoding="utf-8")
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"Stage47 authority/orchestrator unreadable: {type(exc).__name__}")

    if authority.get("schema_version") != 1:
        fail("schema_version drift")
    if authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("project_ref drift")
    if authority.get("stage") != "STAGE47_UNIFIED_EXTERNAL_EVIDENCE_INTAKE_ORCHESTRATION":
        fail("stage drift")
    if authority.get("baseline_main_sha") != EXPECTED_BASELINE:
        fail("baseline main SHA drift")
    if authority.get("current_state") != EXPECTED_STATE:
        fail("current state drift")

    remote = authority.get("fresh_remote_read_only_receipt")
    if not isinstance(remote, dict):
        fail("fresh remote read-only receipt missing")
    expected_remote = {
        "observed_at_utc": "2026-08-24T17:34:35.757678+00:00",
        "auth_users": 0,
        "organizations": 0,
        "billing_provider_state": "selected_pending_credentials",
        "billing_provider_activated_at": None,
        "external_billing_evidence_rows": 0,
        "ready_evidence_migration_count": 0,
        "blocked_evidence_migration_gate_count": 6,
        "stage40_activation_production_environment_interlock": True,
        "stage40_readiness_production_environment_interlock": True,
        "remote_mutation_performed": False,
    }
    for key, expected in expected_remote.items():
        if remote.get(key) != expected:
            fail(f"fresh remote receipt drift: {key}")

    reviewers = authority.get("canonical_reviewers")
    if not isinstance(reviewers, list) or len(reviewers) != 7:
        fail("canonical reviewer set must contain exactly seven entries")
    actual = {
        (item.get("gate_code"), item.get("source_stage"), item.get("reviewer"), item.get("git_blob_sha"))
        for item in reviewers
        if isinstance(item, dict)
    }
    if actual != set(EXPECTED_REVIEWERS):
        fail("canonical reviewer mapping or blob pin drift")

    for gate_code, source_stage, reviewer_rel, expected_blob in EXPECTED_REVIEWERS:
        reviewer = ROOT / reviewer_rel
        if not reviewer.is_file():
            fail(f"canonical reviewer missing: {gate_code}")
        if git_blob_sha(reviewer) != expected_blob:
            fail(f"canonical reviewer blob drift: {gate_code}")
        if source_stage not in source or reviewer_rel not in source:
            fail(f"orchestrator does not pin canonical route: {gate_code}")

    contract = authority.get("orchestration_contract")
    if not isinstance(contract, dict):
        fail("orchestration contract missing")
    required_true = {
        "complete_mode_requires_all_seven_receipts",
        "unknown_json_receipt_is_error",
        "duplicate_source_stage_is_error",
    }
    for key in required_true:
        if contract.get(key) is not True:
            fail(f"fail-closed orchestration contract drift: {key}")
    for key in (
        "canonical_reviewer_bypass_allowed",
        "canonical_reviewer_stdout_or_stderr_copied_to_aggregate",
        "raw_receipt_content_copied_to_aggregate",
        "receipt_path_or_filename_copied_to_aggregate",
        "network_calls_allowed",
        "provider_calls_allowed",
        "supabase_mutation_allowed",
        "deployment_action_allowed",
        "evidence_migration_creation_allowed",
        "gate_promotion_allowed",
        "controlled_launch_promotion_allowed",
        "stage35_alert_proof_alone_can_satisfy_production_deployment",
    ):
        require_false(contract, key)

    if set(authority.get("failure_classes", [])) != EXPECTED_FAILURE_CLASSES:
        fail("Stage47 failure-class registry drift")

    gates = authority.get("gates")
    if not isinstance(gates, dict):
        fail("gate state registry missing")
    for gate_code, *_ in EXPECTED_REVIEWERS:
        if not str(gates.get(gate_code, "")).startswith("DENIED"):
            fail(f"Stage47 cannot promote gate: {gate_code}")
    for gate_code in ("controlled_launch", "paid_media", "launch"):
        if gates.get(gate_code) != "DENIED":
            fail(f"launch authority drift: {gate_code}")

    required_source_markers = (
        "subprocess.run(",
        "sys.executable",
        "VALID_FOR_INDEPENDENT_REVIEW_ONLY",
        "INVALID_BY_CANONICAL_REVIEWER",
        "DUPLICATE",
        "MISSING",
        "INVALID_EXTERNAL_EVIDENCE_CANDIDATE_PRESENT",
        "INCOMPLETE_MISSING_EXTERNAL_EVIDENCE",
        "COMPLETE_STRUCTURAL_CANDIDATES_AWAITING_INDEPENDENT_REVIEW",
        '"gate_ready_attested": False',
        '"evidence_migration_created": False',
        '"controlled_launch_promoted": False',
        '"network_call_performed": False',
        '"supabase_mutation_performed": False',
        '"deployment_action_performed": False',
        '"raw_receipt_content_copied": False',
        '"receipt_path_or_filename_copied": False',
        '"canonical_reviewer_stdout_or_stderr_copied": False',
        '"stage35_alert_proof_alone_can_satisfy_production_deployment": False',
        "if args.mode == \"complete\" and missing_count",
    )
    for marker in required_source_markers:
        if marker not in source:
            fail(f"orchestrator safety marker missing: {marker}")

    forbidden_source_markers = (
        "shell=True",
        "execute_sql",
        "apply_migration",
        "requests.",
        "urllib.request",
        "urlopen(",
        "http.client",
        "socket.",
        "psycopg",
        "supabase.create_client",
        '"receipt_path":',
        '"receipt_filename":',
        '"reviewer_stdout":',
        '"reviewer_stderr":',
    )
    for marker in forbidden_source_markers:
        if marker in source:
            fail(f"forbidden Stage47 orchestration surface present: {marker}")

    stage47_migrations = list(MIGRATIONS.glob("*stage47*.sql"))
    if stage47_migrations:
        fail("Stage47 is preparation/orchestration only; migration is forbidden")

    print("STAGE47_UNIFIED_EXTERNAL_EVIDENCE_INTAKE_GUARD=PASS")
    print("CANONICAL_REVIEWERS_PINNED=7")
    print("REMOTE_MUTATION=false")
    print("EVIDENCE_MIGRATION_CREATED=false")
    print("GATE_PROMOTION=false")
    print("CONTROLLED_LAUNCH=false")


if __name__ == "__main__":
    main()
