from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage87_terms_acceptance_remote_apply_gate_preparation_authority.json"
CONTRACT = BACKEND / "operations" / "stage87_terms_acceptance_remote_apply_gate_contract.json"
STAGE86 = BACKEND / "stage86_terms_acceptance_migration_promotion_authority.json"
MIGRATION = BACKEND / "migrations" / "20260826180000_stage85_terms_acceptance_registry_ledger.sql"
SOURCE = BACKEND / "operations" / "stage85_terms_acceptance_registry_ledger_candidate.sql"
LEDGER = BACKEND / "migration_ledger_authority.json"
BUILDER = BACKEND / "tools" / "build_stage87_terms_acceptance_remote_apply_gate_preparation.py"
WORKFLOW = ROOT / ".github" / "workflows" / "stage87_terms_acceptance_remote_apply_gate_preparation.yml"
OPEN_DECISIONS = ROOT / "10_compliance" / "drafts" / "COMPLIANCE_OPEN_DECISIONS.json"
TERMS_DRAFT = ROOT / "10_compliance" / "drafts" / "TERMS_OF_USE_CANDIDATE_PTBR.md"
FAILURE_CLASS = "BGF-STAGE87-REMOTE-APPLY-GATE-PREPARATION-GUARD-869"
TARGET = "stage85_terms_acceptance_registry_ledger"
FORBIDDEN_IMPORT_ROOTS = {"os", "subprocess", "socket", "urllib", "http", "requests", "psycopg", "supabase"}
FORBIDDEN_WORKFLOW_TOKENS = (
    "apply_migration", "execute_sql", "supabase db", "supabase migration", "service_role",
    "supabase_access_token", "database_url", "git push", "curl ", "wget ",
    "workflow_dispatch", "schedule:", "actions/deploy-pages", "deploy-pages",
)


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE87_TERMS_ACCEPTANCE_REMOTE_APPLY_GATE_PREPARATION_GUARD=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\nDETAIL={detail}"
    )


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to load {path.relative_to(ROOT)}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"expected JSON object: {path.relative_to(ROOT)}")
    return value


def git_blob_sha(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(f"blob {len(raw)}\0".encode("utf-8") + raw).hexdigest()


def canonical_target() -> dict:
    rows = load(OPEN_DECISIONS).get("unresolved")
    target = next(
        (row for row in rows if isinstance(row, dict) and row.get("id") == "TERMS_ACCEPTANCE_VERSIONING"),
        None,
    ) if isinstance(rows, list) else None
    if not isinstance(target, dict):
        fail("TERMS_ACCEPTANCE_VERSIONING missing")
    if target.get("state") != "OPEN" or target.get("applies_to") != ["legal_terms_of_use"]:
        fail("canonical Terms acceptance decision state/scope drift")
    if target.get("required") != "Production mechanism binding user acceptance to immutable terms version/digest.":
        fail("canonical Terms acceptance decision wording drift")
    if target.get("resolution_authority") != "product implementation plus independent review":
        fail("canonical Terms acceptance resolution authority drift")
    return target


def verify_sources() -> tuple[dict, dict]:
    authority = load(AUTHORITY)
    contract = load(CONTRACT)
    stage86 = load(STAGE86)
    ledger = load(LEDGER)
    target = canonical_target()

    if authority.get("schema_version") != 1 or authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("Stage87 authority identity drift")
    if authority.get("stage") != "STAGE87_TERMS_ACCEPTANCE_REMOTE_APPLY_GATE_PREPARATION":
        fail("Stage87 authority stage drift")
    if authority.get("baseline_main_sha") != "3430f91141737ca10494cbb0972956b72fd2f1ec":
        fail("Stage87 baseline main drift")

    upstream = authority.get("upstream_stage86_green", {})
    expected_upstream = {
        "merged_main_sha": "3430f91141737ca10494cbb0972956b72fd2f1ec",
        "green_head_sha": "ee58248032e899d4210154af89184cddbd8fba34",
        "dedicated_ci_run_id": 32999646353,
        "dedicated_ci_conclusion": "success",
        "flutter_quality_gate_run_id": 32999646323,
        "flutter_quality_gate_conclusion": "success",
        "artifact_id": 9617995121,
        "artifact_digest": "sha256:46b80dd1b03bfa36b3a7d174d07ee2a0a7a45feba6c51942ddcda43bb696b28a",
        "artifact_is_remote_apply_evidence": False,
        "artifact_is_legal_or_gate_evidence": False,
    }
    for key, value in expected_upstream.items():
        if upstream.get(key) != value:
            fail(f"Stage86 GREEN provenance drift: {key}")

    if stage86.get("stage") != "STAGE86_TERMS_ACCEPTANCE_MIGRATION_PROMOTION":
        fail("Stage86 authority identity drift")
    if "Stage87 may prepare a one-shot remote migration apply gate" not in stage86.get("next_after_green", {}).get("safe_internal_work", ""):
        fail("Stage86 does not authorize Stage87 preparation scope")
    if stage86.get("next_after_green", {}).get("remote_apply_allowed_during_stage86") is not False:
        fail("Stage86 unexpectedly authorized remote apply")

    pins = authority.get("sealed_inputs", {})
    expected_pins = {
        "stage86_authority_blob": (STAGE86, "dba49d634a5e448661f744e3bfaef90671ec85f8"),
        "migration_blob": (MIGRATION, "a9a77ebbf61f464e5549f338362cdd3a59df8df1"),
        "source_candidate_blob": (SOURCE, "990ee4b1a5d36324d8eb395c7096b3f6af23cdfa"),
        "migration_ledger_blob": (LEDGER, "427f83c2ae6c8430cf9d050380e6f1cfa15c2c87"),
        "apply_gate_contract_blob": (CONTRACT, "80e70b9bdfbb2a70a1b6c67c5b8af781c118aaef"),
    }
    for key, (path, expected) in expected_pins.items():
        if pins.get(key) != expected or git_blob_sha(path) != expected:
            fail(f"Stage87 sealed input drift: {key}")

    receipt = authority.get("fresh_post_merge_remote_precondition_receipt", {})
    expected_receipt = {
        "observed_at_utc": "2026-08-26T18:29:13.017814Z",
        "remote_migration_count": 67,
        "target_remote_migration_present": False,
        "auth_users": 0,
        "organizations": 0,
        "organization_members": 0,
        "terms_registry_exists": False,
        "acceptance_ledger_exists": False,
        "current_terms_rpc_exists": False,
        "accept_terms_rpc_exists": False,
        "acceptance_gate_rpc_exists": False,
        "is_org_member_helper_exists": True,
        "remote_mutation_performed": False,
    }
    for key, value in expected_receipt.items():
        if receipt.get(key) != value:
            fail(f"Stage87 fresh remote receipt drift: {key}")

    repo_only = [
        row for row in ledger.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    ]
    if len(repo_only) != 1 or repo_only[0].get("name") != TARGET:
        fail("Stage87 requires target as unique repo-only divergence")
    remote_names = {
        row.get("name") for row in ledger.get("remote_migrations", []) if isinstance(row, dict)
    }
    if TARGET in remote_names:
        fail("target migration appears in repository remote baseline")

    canonical = authority.get("canonical_target_open_decision", {})
    if canonical.get("id") != target.get("id") or canonical.get("state") != "OPEN":
        fail("Stage87 canonical decision receipt drift")
    if canonical.get("stage87_can_close_decision") is not False:
        fail("Stage87 cannot close TERMS_ACCEPTANCE_VERSIONING")

    hard = authority.get("hard_boundaries", {})
    if not hard or any(value is not False for value in hard.values()):
        fail("Stage87 hard boundaries must all remain false")
    gates = authority.get("gates", {})
    if gates.get("stage87_remote_apply_execution") != "FORBIDDEN":
        fail("Stage87 remote apply execution must remain forbidden")
    for gate in ("legal_terms_of_use", "controlled_launch", "paid_media", "launch"):
        if gates.get(gate) != "DENIED":
            fail(f"Stage87 forbidden gate promotion: {gate}")

    terms = TERMS_DRAFT.read_text(encoding="utf-8")
    for marker in (
        "DRAFT_UNREVIEWED_NOT_PUBLISHED_NOT_LEGAL_EVIDENCE",
        "legal_terms_of_use = BLOCKED",
    ):
        if marker not in terms:
            fail(f"Terms draft marker missing: {marker}")
    return authority, contract


def verify_contract(contract: dict) -> None:
    if contract.get("schema_version") != 1 or contract.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("Stage87 contract identity drift")
    if contract.get("stage") != "STAGE87_TERMS_ACCEPTANCE_REMOTE_APPLY_GATE_PREPARATION":
        fail("Stage87 contract stage drift")
    target = contract.get("target_migration", {})
    if target.get("name") != TARGET or target.get("repository_blob_sha") != git_blob_sha(MIGRATION):
        fail("Stage87 contract target migration drift")
    execution = contract.get("execution_contract", {})
    expected = {
        "stage87_executes_remote_apply": False,
        "later_execution_must_be_one_shot": True,
        "migration_name_must_match_exactly": True,
        "migration_bytes_must_match_exactly": True,
        "remote_apply_count_before_execution": 0,
        "remote_apply_count_after_success": 1,
        "retry_after_ambiguous_result_without_remote_reconciliation": False,
        "raw_execute_sql_for_ddl_allowed": False,
        "terms_data_seed_allowed": False,
        "acceptance_data_seed_allowed": False,
    }
    for key, value in expected.items():
        if execution.get(key) != value:
            fail(f"Stage87 execution contract drift: {key}")
    pre = contract.get("mandatory_fresh_pre_apply_checks")
    post = contract.get("mandatory_post_apply_checks_for_later_execution")
    if not isinstance(pre, list) or len(pre) < 10:
        fail("Stage87 mandatory fresh pre-apply checks incomplete")
    if not isinstance(post, list) or len(post) < 10:
        fail("Stage87 mandatory post-apply checks incomplete")
    ambiguous = contract.get("ambiguous_or_failed_execution_policy", {})
    if ambiguous.get("automatic_second_apply") is not False:
        fail("Stage87 ambiguous apply policy allows blind retry")
    if ambiguous.get("automatic_drop_or_rollback") is not False:
        fail("Stage87 ambiguous apply policy allows destructive auto rollback")
    if ambiguous.get("fail_closed_on_partial_or_ambiguous_evidence") is not True:
        fail("Stage87 ambiguous apply policy is not fail-closed")


def verify_builder_and_workflow() -> None:
    try:
        source = BUILDER.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (OSError, SyntaxError) as exc:
        fail(f"Stage87 builder unreadable/invalid: {type(exc).__name__}")
    for node in ast.walk(tree):
        roots: list[str] = []
        if isinstance(node, ast.Import):
            roots.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.append(node.module.split(".")[0])
        for root in roots:
            if root in FORBIDDEN_IMPORT_ROOTS:
                fail(f"Stage87 builder imports forbidden module: {root}")

    workflow = WORKFLOW.read_text(encoding="utf-8")
    low = workflow.lower()
    for token in FORBIDDEN_WORKFLOW_TOKENS:
        if token in low:
            fail(f"Stage87 workflow contains forbidden execution token: {token}")
    required = (
        "permissions:\n  contents: read",
        "blackgold/stage87-terms-acceptance-remote-apply-gate-preparation",
        "Checkout exact head",
        "Verify Stage87 Terms acceptance remote apply gate preparation",
        "Verify migration ledger contract",
        "Build deterministic Stage87 gate packet twice",
        "cmp /tmp/stage87_gate_a.json /tmp/stage87_gate_b.json",
        "Upload non-attesting Stage87 gate packet",
        "ONE_SHOT_GATE_PREPARED=true",
        "REMOTE_MIGRATION_APPLIED=false",
        "SUPABASE_MUTATION=false",
        "LEGAL_TERMS_GATE_READY=false",
    )
    for marker in required:
        if marker not in workflow:
            fail(f"Stage87 workflow marker missing: {marker}")


def main() -> None:
    _authority, contract = verify_sources()
    verify_contract(contract)
    verify_builder_and_workflow()
    print("STAGE87_TERMS_ACCEPTANCE_REMOTE_APPLY_GATE_PREPARATION_GUARD=PASS")
    print("ONE_SHOT_GATE_PREPARED=true")
    print("REMOTE_MIGRATION_APPLIED=false")
    print("SUPABASE_MUTATION=false")
    print("TERMS_REGISTRY_ROW_CREATED=false")
    print("REAL_ACCEPTANCE_COLLECTED=false")
    print("TARGET_DECISION_CLOSED=false")
    print("LEGAL_TERMS_GATE_READY=false")


if __name__ == "__main__":
    main()
