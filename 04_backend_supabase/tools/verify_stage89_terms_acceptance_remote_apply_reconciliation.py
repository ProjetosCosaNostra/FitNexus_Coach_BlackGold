from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage89_terms_acceptance_remote_apply_reconciliation_authority.json"
STAGE88 = BACKEND / "stage88_terms_acceptance_remote_apply_execution_seal_authority.json"
PLAN = BACKEND / "operations" / "stage88_terms_acceptance_remote_apply_execution_plan.json"
MIGRATION = BACKEND / "migrations" / "20260826180000_stage85_terms_acceptance_registry_ledger.sql"
LEDGER = BACKEND / "migration_ledger_authority.json"
EXPOSURE = BACKEND / "security_definer_exposure_authority.json"
EXPOSURE_GUARD = BACKEND / "tools" / "verify_security_definer_exposure_authority.py"
BUILDER = BACKEND / "tools" / "build_stage89_terms_acceptance_remote_apply_reconciliation.py"
WORKFLOW = ROOT / ".github" / "workflows" / "stage89_terms_acceptance_remote_apply_reconciliation.yml"
OPEN_DECISIONS = ROOT / "10_compliance" / "drafts" / "COMPLIANCE_OPEN_DECISIONS.json"
TERMS = ROOT / "10_compliance" / "drafts" / "TERMS_OF_USE_CANDIDATE_PTBR.md"
FAILURE = "BGF-STAGE89-REMOTE-APPLY-RECONCILIATION-GUARD-885"
TARGET = "stage85_terms_acceptance_registry_ledger"
REMOTE_VERSION = "20260826184218"
FORBIDDEN_IMPORTS = {"os", "subprocess", "socket", "urllib", "http", "requests", "psycopg", "supabase"}
FORBIDDEN_WORKFLOW = (
    "apply_migration", "execute_sql", "supabase db", "service_role", "supabase_access_token",
    "database_url", "curl ", "wget ", "workflow_dispatch", "schedule:", "deploy-pages",
)


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE89_TERMS_ACCEPTANCE_REMOTE_APPLY_RECONCILIATION_GUARD=FAIL\n"
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
    stage88 = load(STAGE88)
    plan = load(PLAN)
    ledger = load(LEDGER)
    exposure = load(EXPOSURE)
    decisions = load(OPEN_DECISIONS)

    expect(authority, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE89_TERMS_ACCEPTANCE_REMOTE_APPLY_RECONCILIATION",
        "baseline_main_sha": "e18ebc4ef534238348b57b699abacc122857e8c0",
        "current_state": "TERMS_ACCEPTANCE_INFRASTRUCTURE_REMOTE_APPLIED_ONCE_RECONCILED_ZERO_ROWS_NO_TERMS_ARTIFACT_NO_ACCEPTANCE_NO_LEGAL_GATE_PROMOTION",
    }, "Stage89 authority")

    upstream = authority.get("upstream_stage88_green", {})
    expect(upstream, {
        "merged_main_sha": "e18ebc4ef534238348b57b699abacc122857e8c0",
        "green_head_sha": "3b466ae096d821bdb46934046af625492385a5aa",
        "dedicated_ci_run_id": 33000782070,
        "dedicated_ci_conclusion": "success",
        "flutter_quality_gate_run_id": 33000782225,
        "flutter_quality_gate_conclusion": "success",
        "artifact_id": 9618445251,
        "artifact_digest": "sha256:05ccf58782d79aa670d6590000d8784e10d93ebdc14fa52b011bd50a0b8c85b9",
        "artifact_is_remote_apply_result": False,
        "artifact_is_legal_or_gate_evidence": False,
    }, "Stage88 GREEN provenance")

    if stage88.get("stage") != "STAGE88_TERMS_ACCEPTANCE_REMOTE_APPLY_EXECUTION_SEAL":
        fail("Stage88 authority identity drift")
    if stage88.get("execution_seal", {}).get("later_one_shot_execution_allowed_only_after_stage88_merge") is not True:
        fail("Stage88 did not seal later one-shot execution")
    if plan.get("execution_seal", {}).get("future_execution_is_one_shot") is not True:
        fail("Stage88 execution plan lost one-shot requirement")

    pins = authority.get("sealed_execution_inputs", {})
    for key, path, expected_blob in (
        ("stage88_authority_blob", STAGE88, "2989e82f3f061eac3cbd95599576aea2e05962ec"),
        ("stage88_execution_plan_blob", PLAN, "5c1a138a416baaf3daef416d370e645435b49fab"),
        ("migration_blob", MIGRATION, "a9a77ebbf61f464e5549f338362cdd3a59df8df1"),
    ):
        if pins.get(key) != expected_blob or blob(path) != expected_blob:
            fail(f"sealed execution input drift:{key}")

    pre = authority.get("fresh_post_stage88_merge_pre_apply_receipt", {})
    expect(pre, {
        "observed_at_utc": "2026-08-26T18:41:24.019251Z",
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
        "remote_mutation_performed_by_precheck": False,
    }, "fresh pre-apply receipt")

    apply_receipt = authority.get("one_shot_remote_apply_receipt", {})
    expect(apply_receipt, {
        "interface": "Supabase.apply_migration",
        "project_ref": "mceukeondizkwlpfxzgf",
        "migration_name": TARGET,
        "migration_blob": "a9a77ebbf61f464e5549f338362cdd3a59df8df1",
        "result": "success",
        "apply_attempt_count": 1,
        "blind_retry_count": 0,
        "automatic_rollback_count": 0,
        "observed_remote_version": REMOTE_VERSION,
    }, "one-shot apply receipt")

    post = authority.get("immediate_post_apply_receipt", {})
    expect(post, {
        "observed_at_utc": "2026-08-26T18:42:39.672815Z",
        "target_remote_migration_present": True,
        "remote_version": REMOTE_VERSION,
        "terms_registry_exists": True,
        "acceptance_ledger_exists": True,
        "current_terms_rpc_exists": True,
        "accept_terms_rpc_exists": True,
        "acceptance_gate_rpc_exists": True,
        "is_org_member_helper_exists": True,
        "terms_registry_rows": 0,
        "acceptance_ledger_rows": 0,
        "anon_current_terms_execute": True,
        "authenticated_current_terms_execute": True,
        "anon_accept_terms_execute": False,
        "authenticated_accept_terms_execute": True,
        "anon_acceptance_gate_execute": False,
        "authenticated_acceptance_gate_execute": True,
    }, "immediate post-apply receipt")

    privilege = authority.get("fresh_privilege_reconciliation_receipt", {})
    expect(privilege, {
        "observed_at_utc": "2026-08-26T19:10:54.951712Z",
        "student_direct_route_anon_execute_count": 0,
        "student_direct_route_authenticated_execute_count": 0,
        "issue_student_access_token_v2_anon_execute": False,
        "issue_student_access_token_v2_authenticated_execute": True,
        "get_current_terms_v1_roles": ["anon", "authenticated"],
        "accept_current_terms_v1_roles": ["authenticated"],
        "get_my_terms_acceptance_gate_v1_roles": ["authenticated"],
    }, "fresh privilege reconciliation")

    reconciliation = authority.get("repository_reconciliation", {})
    for key, path, expected_blob in (
        ("migration_ledger_blob", LEDGER, "0921f9ed4f27960749099d0432a5970769122b0c"),
        ("security_definer_authority_blob", EXPOSURE, "dcd08c5222658bb0a11a7bc5cf8245a1d9ba77eb"),
        ("security_definer_verifier_blob", EXPOSURE_GUARD, "7bab6478c1e4ee15b2585638f0a71200b1703d59"),
    ):
        if reconciliation.get(key) != expected_blob or blob(path) != expected_blob:
            fail(f"repository reconciliation blob drift:{key}")
    expect(reconciliation, {
        "migration_ledger_target_state": "remote_reconciled",
        "repo_only_target_divergence_present": False,
        "remote_target_version": REMOTE_VERSION,
        "historical_remote_only_divergence_count": 3,
        "repository_target_security_definer_exposure_count": 4,
        "remote_new_terms_security_definer_exposure_count": 3,
    }, "repository reconciliation")

    repo_only = [
        row for row in ledger.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    ]
    if repo_only:
        fail("reconciled Stage89 ledger retained repo-only divergence")
    remote = [
        row for row in ledger.get("remote_migrations", [])
        if isinstance(row, dict) and row.get("name") == TARGET
    ]
    if len(remote) != 1 or remote[0].get("version") != REMOTE_VERSION:
        fail("Stage89 target remote migration receipt must exist exactly once")

    transition = exposure.get("stage86_repository_target_transition", {})
    expect(transition, {
        "migration_name": TARGET,
        "migration_ledger_state": "remote_reconciled",
        "remote_applied": True,
        "remote_version": REMOTE_VERSION,
        "remote_current_new_terms_exposure_count": 3,
        "terms_registry_seeded": False,
        "acceptance_seeded": False,
        "legal_terms_gate_promoted": False,
    }, "SECURITY DEFINER Terms transition")
    if not isinstance(exposure.get("stage89_terms_remote_reconciliation"), dict):
        fail("Stage89 SECURITY DEFINER reconciliation receipt missing")

    unresolved = decisions.get("unresolved")
    target_decision = next(
        (row for row in unresolved if isinstance(row, dict) and row.get("id") == "TERMS_ACCEPTANCE_VERSIONING"),
        None,
    ) if isinstance(unresolved, list) else None
    if not isinstance(target_decision, dict) or target_decision.get("state") != "OPEN":
        fail("TERMS_ACCEPTANCE_VERSIONING must remain OPEN")
    terms_text = TERMS.read_text(encoding="utf-8")
    if "DRAFT_UNREVIEWED_NOT_PUBLISHED_NOT_LEGAL_EVIDENCE" not in terms_text:
        fail("Terms draft lost non-evidence marker")
    if "legal_terms_of_use = BLOCKED" not in terms_text:
        fail("Terms legal gate marker drift")

    hard = authority.get("hard_boundaries", {})
    if hard.get("remote_migration_applied_exactly_once") is not True:
        fail("Stage89 must truthfully record exact one-shot remote apply")
    for key in (
        "terms_candidate_approved", "terms_candidate_published", "terms_registry_row_created",
        "real_acceptance_collected", "target_decision_closed", "legal_terms_gate_ready",
        "evidence_ref_creation_allowed", "evidence_digest_promotion_allowed", "deployment_allowed",
        "controlled_launch_promoted", "paid_media_promoted", "launch_promoted",
    ):
        if hard.get(key) is not False:
            fail(f"Stage89 hard boundary drift:{key}")
    if authority.get("gates", {}).get("legal_terms_of_use") != "DENIED":
        fail("legal_terms_of_use must remain denied")
    if authority.get("next_after_green", {}).get("remote_apply_must_not_repeat") is not True:
        fail("Stage89 lost no-second-apply boundary")

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
            fail("Stage89 builder imports remote execution module")

    workflow = WORKFLOW.read_text(encoding="utf-8")
    low = workflow.lower()
    for token in FORBIDDEN_WORKFLOW:
        if token in low:
            fail(f"Stage89 workflow contains forbidden remote/side-effect token:{token}")
    for marker in (
        "permissions:\n  contents: read",
        "blackgold/stage89-terms-acceptance-remote-apply-reconciliation",
        "Verify Stage89 Terms acceptance remote apply reconciliation",
        "Verify SECURITY DEFINER exposure authority",
        "Build deterministic Stage89 reconciliation packet twice",
        "REMOTE_MIGRATION_APPLIED_EXACTLY_ONCE=true",
        "TERMS_REGISTRY_ROWS=0",
        "ACCEPTANCE_LEDGER_ROWS=0",
        "LEGAL_TERMS_GATE_READY=false",
    ):
        if marker not in workflow:
            fail(f"workflow marker missing:{marker}")

    print("STAGE89_TERMS_ACCEPTANCE_REMOTE_APPLY_RECONCILIATION_GUARD=PASS")
    print("REMOTE_MIGRATION_APPLIED_EXACTLY_ONCE=true")
    print(f"REMOTE_VERSION={REMOTE_VERSION}")
    print("TERMS_REGISTRY_ROWS=0")
    print("ACCEPTANCE_LEDGER_ROWS=0")
    print("REMOTE_TERMS_SECURITY_DEFINER_EXPOSURES=3")
    print("TERMS_ACCEPTANCE_VERSIONING=OPEN")
    print("LEGAL_TERMS_GATE_READY=false")


if __name__ == "__main__":
    main()
