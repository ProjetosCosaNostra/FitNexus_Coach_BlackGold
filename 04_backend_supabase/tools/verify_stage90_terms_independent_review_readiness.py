from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage90_terms_independent_review_readiness_authority.json"
STAGE89 = BACKEND / "stage89_terms_acceptance_remote_apply_reconciliation_authority.json"
CONTRACT = ROOT / "10_compliance" / "drafts" / "STAGE90_TERMS_INDEPENDENT_REVIEW_READINESS_CONTRACT.json"
TERMS = ROOT / "10_compliance" / "drafts" / "TERMS_OF_USE_CANDIDATE_PTBR.md"
DECISIONS = ROOT / "10_compliance" / "drafts" / "COMPLIANCE_OPEN_DECISIONS.json"
BUILDER = BACKEND / "tools" / "build_stage90_terms_independent_review_packet.py"
WORKFLOW = ROOT / ".github" / "workflows" / "stage90_terms_independent_review_readiness.yml"
FAILURE = "BGF-STAGE90-INDEPENDENT-REVIEW-READINESS-GUARD-892"
FORBIDDEN_IMPORTS = {"os", "subprocess", "socket", "urllib", "http", "requests", "psycopg", "supabase"}
FORBIDDEN_WORKFLOW = (
    "apply_migration", "execute_sql", "supabase db", "service_role", "supabase_access_token",
    "database_url", "curl ", "wget ", "workflow_dispatch", "schedule:", "deploy-pages",
)


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE90_TERMS_INDEPENDENT_REVIEW_READINESS_GUARD=FAIL\n"
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


def expect(mapping: dict, expected: dict, label: str) -> None:
    for key, value in expected.items():
        if mapping.get(key) != value:
            fail(f"{label} drift:{key}")


def main() -> None:
    authority = load(AUTHORITY)
    stage89 = load(STAGE89)
    contract = load(CONTRACT)
    decisions = load(DECISIONS)

    expect(authority, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE90_TERMS_INDEPENDENT_REVIEW_READINESS",
        "baseline_main_sha": "d6ebd4522ef2e15dc3369f74e174b056872c851c",
        "current_state": "TERMS_REVIEW_PACKET_PREPARED_DRAFT_UNAPPROVED_UNPUBLISHED_NO_REGISTRY_INSERT_NO_ACCEPTANCE_LEGAL_GATE_DENIED",
    }, "Stage90 authority")
    if stage89.get("stage") != "STAGE89_TERMS_ACCEPTANCE_REMOTE_APPLY_RECONCILIATION":
        fail("Stage89 authority identity drift")
    if stage89.get("next_after_green", {}).get("remote_apply_must_not_repeat") is not True:
        fail("Stage89 no-second-apply boundary missing")

    upstream = authority.get("upstream_stage89_green", {})
    expect(upstream, {
        "merged_main_sha": "d6ebd4522ef2e15dc3369f74e174b056872c851c",
        "green_head_sha": "d5b025e0fd05cda24dfeae79836f4e0322e444cf",
        "dedicated_ci_run_id": 33004325980,
        "dedicated_ci_conclusion": "success",
        "flutter_quality_gate_run_id": 33004325845,
        "flutter_quality_gate_conclusion": "success",
        "artifact_id": 9619888017,
        "artifact_digest": "sha256:cece0bcfa080d16f1d689c46db4b9e9d826cad1b86b950d281995b78467cc7d5",
    }, "Stage89 GREEN provenance")

    pins = authority.get("sealed_inputs", {})
    for key, path, expected_blob in (
        ("stage89_authority_blob", STAGE89, "70fcae1902568c070b2a82a52eca338c8e8da6bd"),
        ("review_contract_blob", CONTRACT, "7fc73339b51a5f48bb961c55f4df657f790c4c78"),
        ("terms_draft_blob", TERMS, "0652fb664db57842a8d9dd5d22f0b0b48d645d2d"),
        ("open_decisions_blob", DECISIONS, "215d527c1cb79d7b72697f03f1f84887e3a72d95"),
    ):
        if pins.get(key) != expected_blob or blob(path) != expected_blob:
            fail(f"sealed input drift:{key}")

    if contract.get("stage") != "STAGE90_TERMS_INDEPENDENT_REVIEW_READINESS":
        fail("review contract identity drift")
    exact = contract.get("exact_draft_input", {})
    expect(exact, {
        "git_blob_sha": "0652fb664db57842a8d9dd5d22f0b0b48d645d2d",
        "status_marker": "DRAFT_UNREVIEWED_NOT_PUBLISHED_NOT_LEGAL_EVIDENCE",
        "legal_gate_marker": "legal_terms_of_use = BLOCKED",
        "is_current_legal_terms": False,
        "is_publication_authority": False,
    }, "exact draft input")

    terms_text = TERMS.read_text(encoding="utf-8")
    for marker in (
        "DRAFT_UNREVIEWED_NOT_PUBLISHED_NOT_LEGAL_EVIDENCE",
        "CANDIDATO NÃO REVISADO",
        "legal_terms_of_use = BLOCKED",
        "PREENCHER APÓS REVISÃO JURÍDICA",
    ):
        if marker not in terms_text:
            fail(f"Terms draft marker missing:{marker}")

    unresolved = decisions.get("unresolved")
    if not isinstance(unresolved, list):
        fail("open decisions array missing")
    by_id = {row.get("id"): row for row in unresolved if isinstance(row, dict)}
    for decision_id in (
        "LEGAL_ENTITY_IDENTITY",
        "LEGAL_REVIEWER_REFERENCE",
        "BILLING_CANCELLATION_REFUND_POLICY",
        "RETENTION_MATRIX",
        "TERMS_ACCEPTANCE_VERSIONING",
    ):
        row = by_id.get(decision_id)
        if not isinstance(row, dict) or row.get("state") != "OPEN":
            fail(f"required legal/review blocker is not OPEN:{decision_id}")

    receipt = authority.get("fresh_remote_nonregistration_receipt", {})
    expect(receipt, {
        "observed_at_utc": "2026-08-26T19:19:30.994984Z",
        "terms_registry_rows": 0,
        "acceptance_ledger_rows": 0,
        "current_terms_rpc_exists": True,
        "accept_terms_rpc_exists": True,
        "acceptance_gate_rpc_exists": True,
        "is_org_member_helper_exists": True,
        "remote_mutation_performed": False,
    }, "fresh remote nonregistration receipt")

    blockers = contract.get("review_blockers")
    if not isinstance(blockers, list) or len(blockers) != 7:
        fail("review blocker count drift")
    blocker_ids = {row.get("id") for row in blockers if isinstance(row, dict)}
    required_blockers = {
        "LEGAL_ENTITY_IDENTITY",
        "LEGAL_REVIEWER_REFERENCE",
        "BILLING_CANCELLATION_REFUND_POLICY",
        "TERMS_LIABILITY_AND_CONSUMER_RULES",
        "RETENTION_EXPORT_RULES",
        "VERSION_EFFECTIVE_DATE_DIGEST_URL",
        "TERMS_ACCEPTANCE_VERSIONING",
    }
    if blocker_ids != required_blockers:
        fail("review blocker identity drift")

    shortcuts = contract.get("forbidden_shortcuts", {})
    if not shortcuts or any(value is not True for value in shortcuts.values()):
        fail("forbidden shortcut contract drift")
    hard = authority.get("hard_boundaries", {})
    if not hard or any(value is not False for value in hard.values()):
        fail("Stage90 hard boundary drift")
    gates = authority.get("gates", {})
    if gates.get("external_independent_review") != "REQUIRED_NOT_SUPPLIED":
        fail("external review gate must remain required and unsupplied")
    if gates.get("terms_acceptance_versioning") != "OPEN":
        fail("TERMS_ACCEPTANCE_VERSIONING must remain OPEN")
    if gates.get("legal_terms_of_use") != "DENIED":
        fail("legal_terms_of_use must remain denied")
    if authority.get("next_after_green", {}).get("no_registry_candidate_from_current_draft") is not True:
        fail("Stage90 current-draft registry prohibition missing")

    try:
        builder_source = BUILDER.read_text(encoding="utf-8")
        tree = ast.parse(builder_source)
    except (OSError, SyntaxError) as exc:
        fail(f"builder invalid:{type(exc).__name__}")
    for node in ast.walk(tree):
        roots = []
        if isinstance(node, ast.Import):
            roots += [item.name.split('.')[0] for item in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.append(node.module.split('.')[0])
        if any(root in FORBIDDEN_IMPORTS for root in roots):
            fail("Stage90 builder imports remote execution module")

    workflow = WORKFLOW.read_text(encoding="utf-8")
    low = workflow.lower()
    for token in FORBIDDEN_WORKFLOW:
        if token in low:
            fail(f"Stage90 workflow contains forbidden side-effect token:{token}")
    for marker in (
        "permissions:\n  contents: read",
        "blackgold/stage90-terms-independent-review-readiness",
        "Verify Stage90 Terms independent review readiness",
        "Build deterministic Stage90 review packet twice",
        "EXTERNAL_INDEPENDENT_REVIEW=REQUIRED_NOT_SUPPLIED",
        "TERMS_REGISTRY_ROWS=0",
        "ACCEPTANCE_LEDGER_ROWS=0",
        "LEGAL_TERMS_GATE_READY=false",
    ):
        if marker not in workflow:
            fail(f"workflow marker missing:{marker}")

    print("STAGE90_TERMS_INDEPENDENT_REVIEW_READINESS_GUARD=PASS")
    print("EXACT_DRAFT_PINNED=true")
    print("REVIEW_BLOCKERS=7")
    print("EXTERNAL_INDEPENDENT_REVIEW=REQUIRED_NOT_SUPPLIED")
    print("TERMS_REGISTRY_ROWS=0")
    print("ACCEPTANCE_LEDGER_ROWS=0")
    print("TERMS_ACCEPTANCE_VERSIONING=OPEN")
    print("LEGAL_TERMS_GATE_READY=false")


if __name__ == "__main__":
    main()
