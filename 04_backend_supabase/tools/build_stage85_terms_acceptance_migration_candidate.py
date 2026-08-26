from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage85_terms_acceptance_migration_candidate_authority.json"
CANDIDATE = BACKEND / "operations" / "stage85_terms_acceptance_registry_ledger_candidate.sql"
OPEN_DECISIONS = ROOT / "10_compliance" / "drafts" / "COMPLIANCE_OPEN_DECISIONS.json"
TERMS_DRAFT = ROOT / "10_compliance" / "drafts" / "TERMS_OF_USE_CANDIDATE_PTBR.md"
STAGE84 = BACKEND / "stage84_terms_acceptance_versioning_preparation_authority.json"
STAGE84_INVENTORY = ROOT / "10_compliance" / "inventory" / "STAGE84_TERMS_ACCEPTANCE_VERSIONING_IMPLEMENTATION_PREPARATION.json"
MIGRATION_LEDGER = BACKEND / "migration_ledger_authority.json"
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
FAILURE_CLASS = "BGF-STAGE85-TERMS-ACCEPTANCE-MIGRATION-CANDIDATE-GUARD-850"
CANONICAL_REQUIRED = "Production mechanism binding user acceptance to immutable terms version/digest."
CANONICAL_RESOLUTION = "product implementation plus independent review"


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE85_TERMS_ACCEPTANCE_MIGRATION_CANDIDATE=FAIL\n"
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


def sql_without_line_comments(sql: str) -> str:
    return "\n".join(line.split("--", 1)[0] for line in sql.splitlines())


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
        fail("canonical target state/scope drift")
    if target.get("required") != CANONICAL_REQUIRED or target.get("resolution_authority") != CANONICAL_RESOLUTION:
        fail("canonical target wording drift")
    return target


def validate_sources() -> tuple[dict, str]:
    authority = load_json(AUTHORITY, "Stage85 authority")
    if authority.get("stage") != "STAGE85_TERMS_ACCEPTANCE_MIGRATION_CANDIDATE":
        fail("Stage85 authority identity drift")
    if authority.get("baseline_main_sha") != "d706d7e05cbb778d3c5c3dc7368175c848b24204":
        fail("Stage85 baseline main SHA drift")

    upstream = authority.get("upstream_stage84_green", {})
    expected_green = {
        "merged_main_sha": "d706d7e05cbb778d3c5c3dc7368175c848b24204",
        "green_head_sha": "407bb91e2178be1218b697573654f73da895e62a",
        "dedicated_ci_run_id": 32995231447,
        "dedicated_ci_conclusion": "success",
        "flutter_quality_gate_run_id": 32995232485,
        "flutter_quality_gate_conclusion": "success",
        "artifact_id": 9616196439,
        "artifact_digest": "sha256:d26888d13d038537bd9f4005c036974da92b73460ec3b0be2d6efddd679bc20f",
        "artifact_is_legal_or_gate_evidence": False,
    }
    for key, expected in expected_green.items():
        if upstream.get(key) != expected:
            fail(f"Stage84 GREEN provenance drift: {key}")

    pins = authority.get("sealed_upstream_inputs", {})
    expected_pins = {
        OPEN_DECISIONS: pins.get("open_decisions_blob"),
        TERMS_DRAFT: pins.get("terms_candidate_blob"),
        STAGE84: pins.get("stage84_authority_blob"),
        STAGE84_INVENTORY: pins.get("stage84_inventory_blob"),
        MIGRATION_LEDGER: pins.get("migration_ledger_authority_blob"),
    }
    for path, expected in expected_pins.items():
        if not isinstance(expected, str) or git_blob_sha(path) != expected:
            fail(f"sealed upstream source drift: {path.relative_to(ROOT)}")

    exact = authority.get("exact_candidate", {})
    if exact.get("repository_file") != str(CANDIDATE.relative_to(ROOT)).replace("\\", "/"):
        fail("candidate path drift")
    if exact.get("repository_blob_sha") != git_blob_sha(CANDIDATE):
        fail("exact candidate blob drift")
    if exact.get("is_migration") is not False or exact.get("remote_application_allowed") is not False:
        fail("candidate prematurely promoted")
    if exact.get("future_migration_name") != "stage85_terms_acceptance_registry_ledger":
        fail("future migration name drift")

    remote = authority.get("fresh_remote_read_only_precondition", {})
    for key in (
        "terms_registry_exists",
        "acceptance_ledger_exists",
        "current_terms_rpc_exists",
        "accept_terms_rpc_exists",
        "acceptance_gate_rpc_exists",
        "remote_mutation_performed",
    ):
        if remote.get(key) is not False:
            fail(f"remote precondition drift: {key}")
    if remote.get("is_org_member_helper_exists") is not True:
        fail("required private.is_org_member(uuid) helper missing")

    sql = CANDIDATE.read_text(encoding="utf-8")
    required_sql_markers = (
        "This file is NOT a migration and MUST NOT be executed from operations/.",
        "create table private.terms_document_registry",
        "create table private.terms_acceptance_ledger",
        "create or replace function public.get_current_terms_v1(p_document_kind text)",
        "create or replace function public.accept_current_terms_v1(",
        "create or replace function public.get_my_terms_acceptance_gate_v1(",
        "private.is_org_member(p_organization_id)",
        "v_uid uuid := auth.uid()",
        "TERMS_VERSION_OR_DIGEST_STALE_OR_FORGED",
        "IDEMPOTENCY_KEY_REUSED_WITH_DIFFERENT_ACCEPTANCE",
        "CURRENT_APPROVED_PUBLISHED_TERMS_NOT_AVAILABLE",
        "TERMS_DOCUMENT_REGISTRY_IS_IMMUTABLE",
        "TERMS_ACCEPTANCE_HISTORY_IS_APPEND_ONLY",
        "revoke all on table private.terms_document_registry from public, anon, authenticated",
        "revoke all on table private.terms_acceptance_ledger from public, anon, authenticated",
    )
    for marker in required_sql_markers:
        if marker not in sql:
            fail(f"candidate SQL marker missing: {marker}")
    return authority, sql


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    source_sha = args.source_sha.strip().lower()
    if SHA40_RE.fullmatch(source_sha) is None:
        fail("source-sha must be exact lowercase 40-character Git SHA")

    canonical = canonical_decision()
    authority, sql = validate_sources()
    semantic_sql = sql_without_line_comments(sql)
    semantic_low = semantic_sql.lower()
    output = {
        "schema_version": 1,
        "stage": "STAGE85_TERMS_ACCEPTANCE_MIGRATION_CANDIDATE",
        "output_kind": "NON_ATTESTING_REPO_ONLY_TERMS_ACCEPTANCE_MIGRATION_CANDIDATE_PACKET",
        "state": "EXACT_CANDIDATE_PREPARED_NO_REMOTE_MUTATION_NO_TERMS_DATA_NO_ACCEPTANCE_DATA_NO_GATE_PROMOTION",
        "source_sha": source_sha,
        "canonical_target_open_decision": {
            "id": canonical["id"],
            "state": canonical["state"],
            "applies_to": canonical["applies_to"],
            "required": canonical["required"],
            "resolution_authority": canonical["resolution_authority"],
        },
        "candidate": {
            "path": str(CANDIDATE.relative_to(ROOT)).replace("\\", "/"),
            "git_blob_sha": git_blob_sha(CANDIDATE),
            "sha256": sha256_file(CANDIDATE),
            "byte_count": len(CANDIDATE.read_bytes()),
            "future_migration_name": authority["exact_candidate"]["future_migration_name"],
            "is_migration": False,
            "remote_application_allowed": False,
        },
        "implementation_unit_count": 4,
        "implementation_units": [
            "terms_document_registry",
            "terms_acceptance_ledger",
            "current_terms_resolver",
            "acceptance_gate_with_authenticated_acceptance_rpc",
        ],
        "sql_contract_signals": {
            "registry_insert_seed_present": "insert into private.terms_document_registry" in semantic_low,
            "runtime_acceptance_insert_count": semantic_low.count("insert into private.terms_acceptance_ledger"),
            "mutable_is_current_flag_present": bool(re.search(r"\bis_current\b", semantic_sql, flags=re.IGNORECASE)),
        },
        "hard_boundaries": {
            "terms_candidate_approved": False,
            "terms_candidate_published": False,
            "terms_registry_row_created": False,
            "real_acceptance_collected": False,
            "candidate_is_migration": False,
            "migration_applied": False,
            "migration_ledger_modified": False,
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
    print("STAGE85_TERMS_ACCEPTANCE_MIGRATION_CANDIDATE=PASS")
    print("IMPLEMENTATION_UNIT_COUNT=4")
    print("CANDIDATE_IS_MIGRATION=false")
    print("REMOTE_MUTATION=false")
    print("TERMS_REGISTRY_ROW_CREATED=false")
    print("REAL_ACCEPTANCE_COLLECTED=false")
    print("TARGET_DECISION_CLOSED=false")
    print("LEGAL_TERMS_GATE_READY=false")


if __name__ == "__main__":
    main()
