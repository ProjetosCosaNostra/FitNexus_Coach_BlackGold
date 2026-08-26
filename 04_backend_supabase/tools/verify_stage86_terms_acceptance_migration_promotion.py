from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage86_terms_acceptance_migration_promotion_authority.json"
STAGE85 = BACKEND / "stage85_terms_acceptance_migration_candidate_authority.json"
SOURCE = BACKEND / "operations" / "stage85_terms_acceptance_registry_ledger_candidate.sql"
MIGRATION = BACKEND / "migrations" / "20260826180000_stage85_terms_acceptance_registry_ledger.sql"
LEDGER = BACKEND / "migration_ledger_authority.json"
BUILDER = BACKEND / "tools" / "build_stage86_terms_acceptance_migration_promotion.py"
WORKFLOW = ROOT / ".github" / "workflows" / "stage86_terms_acceptance_migration_promotion.yml"
OPEN_DECISIONS = ROOT / "10_compliance" / "drafts" / "COMPLIANCE_OPEN_DECISIONS.json"
TERMS_DRAFT = ROOT / "10_compliance" / "drafts" / "TERMS_OF_USE_CANDIDATE_PTBR.md"
FAILURE_CLASS = "BGF-STAGE86-TERMS-ACCEPTANCE-MIGRATION-PROMOTION-GUARD-858"
CANONICAL_REQUIRED = "Production mechanism binding user acceptance to immutable terms version/digest."
CANONICAL_RESOLUTION = "product implementation plus independent review"
FORBIDDEN_IMPORT_ROOTS = {"os", "subprocess", "socket", "urllib", "http", "requests", "psycopg", "supabase"}
FORBIDDEN_WORKFLOW_TOKENS = (
    "apply_migration", "execute_sql", "supabase db", "supabase migration", "git push",
    "curl ", "wget ", "deploy-pages", "actions/deploy-pages", "powershell",
    "service_role", "supabase_access_token", "workflow_dispatch", "schedule:",
)
TARGET_MIGRATION = "stage85_terms_acceptance_registry_ledger"
HISTORICAL_REMOTE_ONLY = {
    "stage17_pricing_guard_indexes_marker",
    "stage17_pricing_advisor_reconciliation",
    "stage17_pricing_advisor_guard",
}


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE86_TERMS_ACCEPTANCE_MIGRATION_PROMOTION_GUARD=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\nDETAIL={detail}"
    )


def load_json(path: Path, label: str | None = None) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to load {label or path.relative_to(ROOT)}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"expected JSON object: {label or path.relative_to(ROOT)}")
    return value


def git_blob_sha(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(f"blob {len(raw)}\0".encode("utf-8") + raw).hexdigest()


def sql_without_line_comments(sql: str) -> str:
    return "\n".join(line.split("--", 1)[0] for line in sql.splitlines())


def extract_from_standalone_do(path: Path) -> bytes:
    raw = path.read_bytes()
    offset = 0
    for line in raw.splitlines(keepends=True):
        try:
            text = line.decode("utf-8").strip()
        except UnicodeDecodeError:
            fail(f"non-UTF8 SQL: {path.relative_to(ROOT)}")
        if text == "do $$":
            return raw[offset:]
        offset += len(line)
    fail(f"standalone do $$ marker missing: {path.relative_to(ROOT)}")
    raise AssertionError("unreachable")


def verify_canonical_decision() -> None:
    decisions = load_json(OPEN_DECISIONS, "open decisions")
    rows = decisions.get("unresolved")
    target = next(
        (row for row in rows if isinstance(row, dict) and row.get("id") == "TERMS_ACCEPTANCE_VERSIONING"),
        None,
    ) if isinstance(rows, list) else None
    if not isinstance(target, dict):
        fail("TERMS_ACCEPTANCE_VERSIONING missing from canonical open decisions")
    if target.get("state") != "OPEN" or target.get("applies_to") != ["legal_terms_of_use"]:
        fail("canonical target state/scope drift")
    if target.get("required") != CANONICAL_REQUIRED or target.get("resolution_authority") != CANONICAL_RESOLUTION:
        fail("canonical target wording drift")

    terms = TERMS_DRAFT.read_text(encoding="utf-8")
    for marker in (
        "DRAFT_UNREVIEWED_NOT_PUBLISHED_NOT_LEGAL_EVIDENCE",
        "`terms_version` imutável",
        "digest SHA-256 do documento aprovado",
        "evidência de aceite vinculada à versão",
        "legal_terms_of_use = BLOCKED",
    ):
        if marker not in terms:
            fail(f"Terms draft source marker missing: {marker}")


def verify_authority() -> dict:
    authority = load_json(AUTHORITY, "Stage86 authority")
    if authority.get("schema_version") != 1 or authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("Stage86 authority identity drift")
    if authority.get("stage") != "STAGE86_TERMS_ACCEPTANCE_MIGRATION_PROMOTION":
        fail("Stage86 authority stage drift")
    if authority.get("baseline_main_sha") != "3d6d14a659611594081b8a22b0ae6c483459de48":
        fail("Stage86 baseline main SHA drift")

    upstream = authority.get("upstream_stage85_green", {})
    expected = {
        "merged_main_sha": "3d6d14a659611594081b8a22b0ae6c483459de48",
        "green_head_sha": "d86ba3d8b1b9194ef028437ffc3e45cd6d6ca60e",
        "dedicated_ci_run_id": 32996441026,
        "dedicated_ci_conclusion": "success",
        "flutter_quality_gate_run_id": 32996441181,
        "flutter_quality_gate_conclusion": "success",
        "artifact_id": 9616720311,
        "artifact_digest": "sha256:ce3613570667e578fffa3f0cdbfe6c7851d29b5bf150e0ad7aa887e5409fed4a",
        "artifact_is_legal_or_gate_evidence": False,
    }
    for key, value in expected.items():
        if upstream.get(key) != value:
            fail(f"Stage85 GREEN provenance drift: {key}")

    target = authority.get("canonical_target_open_decision", {})
    if target.get("id") != "TERMS_ACCEPTANCE_VERSIONING" or target.get("state") != "OPEN":
        fail("Stage86 target decision identity/state drift")
    if target.get("affected_gates") != ["legal_terms_of_use"]:
        fail("Stage86 target gate drift")
    if target.get("required") != CANONICAL_REQUIRED or target.get("resolution_authority") != CANONICAL_RESOLUTION:
        fail("Stage86 target wording drift")
    if target.get("stage86_can_close_decision") is not False:
        fail("Stage86 cannot close TERMS_ACCEPTANCE_VERSIONING")

    pins = authority.get("sealed_inputs", {})
    if pins.get("stage85_authority_blob") != git_blob_sha(STAGE85):
        fail("Stage85 authority sealed input drift")
    if pins.get("source_candidate_blob") != git_blob_sha(SOURCE):
        fail("Stage85 source candidate sealed input drift")
    if pins.get("stage85_authority_blob") != "7c26ff577dcfa8ed5c15e9bab854bb2a51c2a6b3":
        fail("Stage85 authority expected blob drift")
    if pins.get("source_candidate_blob") != "990ee4b1a5d36324d8eb395c7096b3f6af23cdfa":
        fail("Stage85 candidate expected blob drift")
    if pins.get("migration_ledger_pre_promotion_blob") != "dbdf3e75f30bf9322034a33247a628385b23e744":
        fail("pre-promotion migration ledger provenance drift")

    remote = authority.get("fresh_pre_promotion_remote_receipt", {})
    if [remote.get("auth_users"), remote.get("organizations"), remote.get("organization_members")] != [0, 0, 0]:
        fail("Stage86 remote pre-promotion customer domain drift")
    for key in (
        "remote_migration_name_present", "terms_registry_exists", "acceptance_ledger_exists",
        "current_terms_rpc_exists", "accept_terms_rpc_exists", "acceptance_gate_rpc_exists",
        "remote_mutation_performed",
    ):
        if remote.get(key) is not False:
            fail(f"Stage86 remote receipt must keep {key}=false")
    if remote.get("is_org_member_helper_exists") is not True:
        fail("Stage86 required private.is_org_member(uuid) receipt missing")

    migration = authority.get("migration", {})
    if migration.get("name") != TARGET_MIGRATION:
        fail("Stage86 migration name drift")
    if migration.get("repository_file") != str(MIGRATION.relative_to(ROOT)).replace("\\", "/"):
        fail("Stage86 migration path drift")
    if migration.get("repository_blob_sha") != git_blob_sha(MIGRATION):
        fail("Stage86 migration blob drift")
    if migration.get("repository_blob_sha") != "a9a77ebbf61f464e5549f338362cdd3a59df8df1":
        fail("Stage86 exact migration blob pin drift")
    if migration.get("source_candidate_blob_sha") != git_blob_sha(SOURCE):
        fail("Stage86 source candidate blob drift")
    if migration.get("migration_ledger_blob_after_promotion") != git_blob_sha(LEDGER):
        fail("Stage86 migration ledger blob drift")
    if migration.get("migration_ledger_state") != "repo_only":
        fail("Stage86 migration must remain repo_only")
    for key in ("remote_applied", "seeds_terms_registry_rows", "seeds_acceptance_rows"):
        if migration.get(key) is not False:
            fail(f"Stage86 migration boundary drift: {key}")
    if migration.get("apply_count") != 0:
        fail("Stage86 remote apply count must remain zero")
    if migration.get("executable_body_from_standalone_do_marker_byte_identical") is not True:
        fail("Stage86 authority must attest reviewed executable-body identity")

    hard = authority.get("hard_boundaries", {})
    if not hard or any(value is not False for value in hard.values()):
        fail("Stage86 hard boundaries must all remain false")
    gates = authority.get("gates", {})
    if gates.get("stage86_terms_acceptance_migration_promotion") != "REPO_ONLY_PENDING_CI":
        fail("Stage86 repository-only gate state drift")
    for gate in ("legal_terms_of_use", "controlled_launch", "paid_media", "launch"):
        if gates.get(gate) != "DENIED":
            fail(f"Stage86 forbidden gate promotion: {gate}")
    if authority.get("next_after_green", {}).get("remote_apply_allowed_during_stage86") is not False:
        fail("Stage86 unexpectedly authorizes remote apply")
    return authority


def verify_stage85_authority() -> None:
    stage85 = load_json(STAGE85, "Stage85 authority")
    if stage85.get("stage") != "STAGE85_TERMS_ACCEPTANCE_MIGRATION_CANDIDATE":
        fail("Stage85 upstream authority identity drift")
    if stage85.get("exact_candidate", {}).get("repository_blob_sha") != git_blob_sha(SOURCE):
        fail("Stage85 upstream candidate pin drift")
    next_work = stage85.get("next_after_green", {}).get("safe_internal_work", "")
    if "Stage86 may promote only the exact pinned Stage85 SQL candidate bytes" not in next_work:
        fail("Stage85 does not authorize Stage86 repository-only promotion scope")
    if stage85.get("next_after_green", {}).get("remote_mutation_allowed") is not False:
        fail("Stage85 unexpectedly authorizes remote mutation")


def verify_migration_and_source() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    migration = MIGRATION.read_text(encoding="utf-8")
    source_semantic = sql_without_line_comments(source)
    migration_semantic = sql_without_line_comments(migration)
    source_low = source_semantic.lower()
    migration_low = migration_semantic.lower()

    if extract_from_standalone_do(MIGRATION) != extract_from_standalone_do(SOURCE):
        fail("Stage86 executable migration body differs from exact Stage85 candidate")
    if "stage86 repository-only migration promotion" not in migration.lower():
        fail("Stage86 migration repository-only header missing")
    if "must not be applied remotely" not in migration.lower():
        fail("Stage86 migration remote-apply prohibition header missing")
    if "insert into private.terms_document_registry" in migration_low:
        fail("Stage86 migration must not seed/register a Terms artifact")
    if migration_low.count("insert into private.terms_acceptance_ledger") != 1:
        fail("Stage86 migration must contain exactly one runtime acceptance append")
    if re.search(r"\bis_current\b", migration_semantic, flags=re.IGNORECASE):
        fail("Stage86 migration contains mutable is_current executable surface")
    if "terms_of_use_candidate_ptbr" in migration_low:
        fail("Stage86 migration references draft Terms runtime authority")
    if source_low != sql_without_line_comments(source).lower():
        fail("internal source normalization inconsistency")

    required = (
        "create table private.terms_document_registry",
        "create table private.terms_acceptance_ledger",
        "TERMS_DOCUMENT_REGISTRY_IS_IMMUTABLE",
        "TERMS_ACCEPTANCE_HISTORY_IS_APPEND_ONLY",
        "CURRENT_APPROVED_PUBLISHED_TERMS_NOT_AVAILABLE",
        "TERMS_VERSION_OR_DIGEST_STALE_OR_FORGED",
        "IDEMPOTENCY_KEY_REUSED_WITH_DIFFERENT_ACCEPTANCE",
        "private.is_org_member(p_organization_id)",
        "v_uid uuid := auth.uid()",
    )
    for marker in required:
        if marker.lower() not in migration_low:
            fail(f"Stage86 migration contract marker missing: {marker}")


def verify_migration_ledger() -> None:
    ledger = load_json(LEDGER, "migration ledger authority")
    if ledger.get("schema_version") != 1 or ledger.get("failure_class") != "BGF-REMOTE-REPO-MIGRATION-DIVERGENCE-142":
        fail("migration ledger authority identity drift")
    if ledger.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("migration ledger project_ref drift")
    if ledger.get("baseline_main_sha") != "3d6d14a659611594081b8a22b0ae6c483459de48":
        fail("migration ledger Stage86 baseline main drift")
    if ledger.get("observed_at_utc") != "2026-08-26T17:55:56.672117Z":
        fail("migration ledger Stage86 remote observation drift")
    if ledger.get("comparison_key") != "migration_name":
        fail("migration ledger comparison key drift")

    rows = ledger.get("declared_divergences")
    if not isinstance(rows, list):
        fail("migration ledger declared_divergences must be an array")
    remote_only = {
        row.get("name") for row in rows
        if isinstance(row, dict) and row.get("direction") == "remote_only"
    }
    repo_only = [
        row for row in rows
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    ]
    if remote_only != HISTORICAL_REMOTE_ONLY:
        fail("historical remote-only migration divergences drift")
    if len(repo_only) != 1 or repo_only[0].get("name") != TARGET_MIGRATION:
        fail("Stage86 must declare exactly one repo-only migration divergence")
    if repo_only[0].get("related_failure_class") != "BGF-STAGE86-PREMATURE-REMOTE-APPLY-855":
        fail("Stage86 repo-only divergence failure-class provenance drift")

    remote = ledger.get("remote_migrations")
    if not isinstance(remote, list) or not remote:
        fail("migration ledger remote baseline missing")
    remote_names = [row.get("name") for row in remote if isinstance(row, dict)]
    if TARGET_MIGRATION in remote_names:
        fail("Stage86 target migration unexpectedly present in remote baseline")
    if len(remote_names) != len(set(remote_names)):
        fail("migration ledger remote migration names are not unique")

    migration_files = list((BACKEND / "migrations").glob("*.sql"))
    matching = [path for path in migration_files if path.name.endswith(f"_{TARGET_MIGRATION}.sql")]
    if matching != [MIGRATION]:
        fail("Stage86 target migration must exist exactly once in canonical migrations directory")


def verify_builder_and_workflow() -> None:
    try:
        builder_source = BUILDER.read_text(encoding="utf-8")
        tree = ast.parse(builder_source)
    except (OSError, SyntaxError) as exc:
        fail(f"Stage86 builder unreadable/invalid: {type(exc).__name__}")
    for node in ast.walk(tree):
        roots: list[str] = []
        if isinstance(node, ast.Import):
            roots.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.append(node.module.split(".")[0])
        for root in roots:
            if root in FORBIDDEN_IMPORT_ROOTS:
                fail(f"Stage86 builder imports forbidden module: {root}")

    for marker in (
        "NON_ATTESTING_REPOSITORY_ONLY_MIGRATION_PROMOTION_PACKET",
        '"migration_ledger_state": "repo_only"',
        '"remote_applied": False',
        '"supabase_mutation": False',
        '"terms_registry_row_created": False',
        '"real_acceptance_collected": False',
        '"target_decision_closed": False',
        '"legal_terms_gate_ready": False',
    ):
        if marker not in builder_source:
            fail(f"Stage86 builder boundary marker missing: {marker}")

    try:
        workflow = WORKFLOW.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"Stage86 workflow unreadable: {type(exc).__name__}")
    workflow_low = workflow.lower()
    for token in FORBIDDEN_WORKFLOW_TOKENS:
        if token in workflow_low:
            fail(f"Stage86 workflow contains forbidden token: {token}")
    for marker in (
        "permissions:\n  contents: read",
        "blackgold/stage86-terms-acceptance-migration-promotion",
        "Checkout exact head",
        "Verify Stage86 Terms acceptance migration promotion",
        "Verify migration ledger contract",
        "Build deterministic Stage86 promotion packet twice",
        "cmp /tmp/stage86_promotion_a.json /tmp/stage86_promotion_b.json",
        "Upload non-attesting Stage86 promotion packet",
        "MIGRATION_LEDGER_STATE=repo_only",
        "REMOTE_MIGRATION_APPLIED=false",
        "SUPABASE_MUTATION=false",
        "TERMS_REGISTRY_ROW_CREATED=false",
        "REAL_ACCEPTANCE_COLLECTED=false",
        "TARGET_DECISION_CLOSED=false",
        "LEGAL_TERMS_GATE_READY=false",
        "CONTROLLED_LAUNCH=DENIED",
        "PAID_MEDIA=DENIED",
    ):
        if marker not in workflow:
            fail(f"Stage86 workflow marker missing: {marker}")


def main() -> None:
    verify_canonical_decision()
    verify_authority()
    verify_stage85_authority()
    verify_migration_and_source()
    verify_migration_ledger()
    verify_builder_and_workflow()
    print("STAGE86_TERMS_ACCEPTANCE_MIGRATION_PROMOTION_GUARD=PASS")
    print("MIGRATION_LEDGER_STATE=repo_only")
    print("EXECUTABLE_BODY_BYTE_IDENTICAL=true")
    print("REMOTE_MIGRATION_APPLIED=false")
    print("SUPABASE_MUTATION=false")
    print("TERMS_REGISTRY_ROW_CREATED=false")
    print("REAL_ACCEPTANCE_COLLECTED=false")
    print("TARGET_DECISION_CLOSED=false")
    print("LEGAL_TERMS_GATE_READY=false")


if __name__ == "__main__":
    main()
