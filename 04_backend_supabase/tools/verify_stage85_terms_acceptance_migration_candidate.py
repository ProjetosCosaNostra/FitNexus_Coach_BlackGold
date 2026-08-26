from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage85_terms_acceptance_migration_candidate_authority.json"
CANDIDATE = BACKEND / "operations" / "stage85_terms_acceptance_registry_ledger_candidate.sql"
BUILDER = BACKEND / "tools" / "build_stage85_terms_acceptance_migration_candidate.py"
OPEN_DECISIONS = ROOT / "10_compliance" / "drafts" / "COMPLIANCE_OPEN_DECISIONS.json"
TERMS_DRAFT = ROOT / "10_compliance" / "drafts" / "TERMS_OF_USE_CANDIDATE_PTBR.md"
STAGE84 = BACKEND / "stage84_terms_acceptance_versioning_preparation_authority.json"
STAGE84_INVENTORY = ROOT / "10_compliance" / "inventory" / "STAGE84_TERMS_ACCEPTANCE_VERSIONING_IMPLEMENTATION_PREPARATION.json"
MIGRATION_LEDGER = BACKEND / "migration_ledger_authority.json"
WORKFLOW = ROOT / ".github" / "workflows" / "stage85_terms_acceptance_migration_candidate.yml"
FAILURE_CLASS = "BGF-STAGE85-TERMS-ACCEPTANCE-MIGRATION-CANDIDATE-GUARD-850"
CANONICAL_REQUIRED = "Production mechanism binding user acceptance to immutable terms version/digest."
CANONICAL_RESOLUTION = "product implementation plus independent review"
FORBIDDEN_IMPORT_ROOTS = {"os", "subprocess", "socket", "urllib", "http", "requests", "psycopg", "supabase"}
FORBIDDEN_WORKFLOW_TOKENS = (
    "apply_migration", "execute_sql", "supabase db", "git push", "curl ", "wget ",
    "deploy-pages", "actions/deploy-pages", "powershell",
)


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE85_TERMS_ACCEPTANCE_MIGRATION_CANDIDATE_GUARD=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\nDETAIL={detail}"
    )


def load_json(path: Path) -> dict:
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


def sql_without_line_comments(sql: str) -> str:
    return "\n".join(line.split("--", 1)[0] for line in sql.splitlines())


def verify_authority_and_upstream() -> None:
    authority = load_json(AUTHORITY)
    if authority.get("schema_version") != 1 or authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("Stage85 authority identity drift")
    if authority.get("stage") != "STAGE85_TERMS_ACCEPTANCE_MIGRATION_CANDIDATE":
        fail("Stage85 authority stage drift")
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

    target = authority.get("canonical_target_open_decision", {})
    if target.get("id") != "TERMS_ACCEPTANCE_VERSIONING" or target.get("state") != "OPEN":
        fail("Stage85 target decision identity/state drift")
    if target.get("affected_gates") != ["legal_terms_of_use"]:
        fail("Stage85 target gate drift")
    if target.get("required") != CANONICAL_REQUIRED or target.get("resolution_authority") != CANONICAL_RESOLUTION:
        fail("Stage85 target decision wording drift")
    if target.get("stage85_can_close_decision") is not False:
        fail("Stage85 cannot close TERMS_ACCEPTANCE_VERSIONING")

    pins = authority.get("sealed_upstream_inputs", {})
    pinned = {
        OPEN_DECISIONS: pins.get("open_decisions_blob"),
        TERMS_DRAFT: pins.get("terms_candidate_blob"),
        STAGE84: pins.get("stage84_authority_blob"),
        STAGE84_INVENTORY: pins.get("stage84_inventory_blob"),
        MIGRATION_LEDGER: pins.get("migration_ledger_authority_blob"),
    }
    for path, expected in pinned.items():
        if not isinstance(expected, str) or git_blob_sha(path) != expected:
            fail(f"sealed upstream input drift: {path.relative_to(ROOT)}")

    exact = authority.get("exact_candidate", {})
    if exact.get("repository_file") != "04_backend_supabase/operations/stage85_terms_acceptance_registry_ledger_candidate.sql":
        fail("Stage85 exact candidate path drift")
    if exact.get("repository_blob_sha") != "990ee4b1a5d36324d8eb395c7096b3f6af23cdfa":
        fail("Stage85 authority candidate blob pin drift")
    if git_blob_sha(CANDIDATE) != exact.get("repository_blob_sha"):
        fail("Stage85 exact candidate bytes drift")
    if exact.get("is_migration") is not False or exact.get("remote_application_allowed") is not False:
        fail("Stage85 candidate prematurely promoted")
    if exact.get("inserts_terms_registry_rows_at_migration_apply") is not False:
        fail("Stage85 candidate must not seed Terms registry rows")
    if exact.get("inserts_acceptance_rows_at_migration_apply") is not False:
        fail("Stage85 candidate must not create acceptance rows at migration apply")
    if exact.get("runtime_acceptance_rpc_appends_acceptance_row") is not True:
        fail("Stage85 runtime acceptance append contract drift")

    remote = authority.get("fresh_remote_read_only_precondition", {})
    if [remote.get("auth_users"), remote.get("organizations"), remote.get("organization_members")] != [0, 0, 0]:
        fail("Stage85 fresh remote empty-domain observation drift")
    for key in (
        "terms_registry_exists", "acceptance_ledger_exists", "current_terms_rpc_exists",
        "accept_terms_rpc_exists", "acceptance_gate_rpc_exists", "remote_mutation_performed",
    ):
        if remote.get(key) is not False:
            fail(f"Stage85 remote precondition must keep {key}=false")
    if remote.get("is_org_member_helper_exists") is not True:
        fail("Stage85 private.is_org_member(uuid) precondition drift")

    hard = authority.get("hard_boundaries", {})
    if not hard or any(value is not False for value in hard.values()):
        fail("Stage85 hard boundaries must all remain false")
    gates = authority.get("gates", {})
    if gates.get("legal_terms_of_use") != "DENIED" or gates.get("controlled_launch") != "DENIED" or gates.get("paid_media") != "DENIED":
        fail("Stage85 gate boundary drift")


def verify_canonical_sources() -> None:
    decisions = load_json(OPEN_DECISIONS)
    rows = decisions.get("unresolved")
    target = next((row for row in rows if isinstance(row, dict) and row.get("id") == "TERMS_ACCEPTANCE_VERSIONING"), None) if isinstance(rows, list) else None
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

    s84 = load_json(STAGE84)
    if s84.get("next_after_green", {}).get("remote_mutation_allowed") is not False:
        fail("Stage84 unexpectedly authorizes remote mutation")
    if "Stage85 may prepare an exact migration/RLS/RPC implementation candidate" not in s84.get("next_after_green", {}).get("safe_internal_work", ""):
        fail("Stage84 does not authorize this Stage85 preparation scope")


def verify_candidate_sql() -> None:
    try:
        sql = CANDIDATE.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"unable to read Stage85 SQL candidate: {type(exc).__name__}")
    raw_low = sql.lower()
    semantic_sql = sql_without_line_comments(sql)
    low = semantic_sql.lower()

    if "not a migration and must not be executed from operations/" not in raw_low:
        fail("candidate-only execution boundary missing")
    if "insert into private.terms_document_registry" in low:
        fail("candidate must not seed/register a Terms artifact")
    if low.count("insert into private.terms_acceptance_ledger") != 1:
        fail("candidate acceptance ledger INSERT count must be exactly one runtime RPC append")
    accept_start = low.find("create or replace function public.accept_current_terms_v1(")
    accept_end = low.find("revoke all on function public.accept_current_terms_v1", accept_start)
    insert_pos = low.find("insert into private.terms_acceptance_ledger")
    if accept_start < 0 or accept_end < 0 or not (accept_start < insert_pos < accept_end):
        fail("acceptance ledger INSERT must exist only inside authenticated acceptance RPC")
    if re.search(r"\bis_current\b", semantic_sql, flags=re.IGNORECASE):
        fail("mutable is_current flag is forbidden in executable SQL")
    if "terms_of_use_candidate_ptbr" in low:
        fail("candidate SQL must never reference repository draft Terms as runtime authority")

    required = (
        "create table private.terms_document_registry",
        "primary key (document_kind, version)",
        "unique (document_kind, sha256)",
        "before update or delete on private.terms_document_registry",
        "TERMS_DOCUMENT_REGISTRY_IS_IMMUTABLE",
        "create table private.terms_acceptance_ledger",
        "foreign key (document_kind, terms_version, terms_sha256)",
        "unique (actor_user_id, organization_id, document_kind, idempotency_key)",
        "before update or delete on private.terms_acceptance_ledger",
        "TERMS_ACCEPTANCE_HISTORY_IS_APPEND_ONLY",
        "alter table private.terms_document_registry enable row level security",
        "alter table private.terms_acceptance_ledger enable row level security",
        "revoke all on table private.terms_document_registry from public, anon, authenticated",
        "revoke all on table private.terms_acceptance_ledger from public, anon, authenticated",
        "create or replace function public.get_current_terms_v1(p_document_kind text)",
        "CURRENT_APPROVED_PUBLISHED_TERMS_NOT_AVAILABLE",
        "grant execute on function public.get_current_terms_v1(text) to anon, authenticated",
        "v_uid uuid := auth.uid()",
        "private.is_org_member(p_organization_id)",
        "TERMS_VERSION_OR_DIGEST_STALE_OR_FORGED",
        "on conflict (actor_user_id, organization_id, document_kind, idempotency_key)",
        "IDEMPOTENCY_KEY_REUSED_WITH_DIFFERENT_ACCEPTANCE",
        "grant execute on function public.accept_current_terms_v1(uuid,text,text,text,text,text) to authenticated",
        "create or replace function public.get_my_terms_acceptance_gate_v1(",
        "grant execute on function public.get_my_terms_acceptance_gate_v1(uuid,text) to authenticated",
    )
    for marker in required:
        if marker.lower() not in low:
            fail(f"candidate SQL contract marker missing: {marker}")

    forbidden = (
        "grant insert on table private.terms_document_registry to anon",
        "grant insert on table private.terms_document_registry to authenticated",
        "grant select on table private.terms_acceptance_ledger to anon",
        "grant select on table private.terms_acceptance_ledger to authenticated",
        "grant insert on table private.terms_acceptance_ledger to anon",
        "grant insert on table private.terms_acceptance_ledger to authenticated",
        "disable row level security",
    )
    for token in forbidden:
        if token in low:
            fail(f"candidate SQL contains forbidden access token: {token}")


def verify_builder_and_workflow() -> None:
    try:
        source = BUILDER.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (OSError, SyntaxError) as exc:
        fail(f"Stage85 builder unreadable/invalid: {type(exc).__name__}")
    for node in ast.walk(tree):
        roots: list[str] = []
        if isinstance(node, ast.Import):
            roots.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.append(node.module.split(".")[0])
        for root in roots:
            if root in FORBIDDEN_IMPORT_ROOTS:
                fail(f"Stage85 builder imports forbidden module: {root}")

    for marker in (
        "NON_ATTESTING_REPO_ONLY_TERMS_ACCEPTANCE_MIGRATION_CANDIDATE_PACKET",
        "candidate_is_migration\": False",
        "remote_mutation\": False",
        "terms_registry_row_created\": False",
        "real_acceptance_collected\": False",
        "target_decision_closed\": False",
        "legal_terms_gate_ready\": False",
    ):
        if marker not in source:
            fail(f"Stage85 builder boundary marker missing: {marker}")

    try:
        text = WORKFLOW.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"Stage85 workflow unreadable: {type(exc).__name__}")
    low = text.lower()
    for token in FORBIDDEN_WORKFLOW_TOKENS:
        if token in low:
            fail(f"Stage85 workflow contains forbidden token: {token}")
    for marker in (
        "permissions:\n  contents: read",
        "blackgold/stage85-terms-acceptance-migration-candidate",
        "Checkout exact head",
        "Verify Stage85 Terms acceptance migration candidate",
        "Build deterministic Stage85 candidate packet twice",
        "cmp /tmp/stage85_candidate_a.json /tmp/stage85_candidate_b.json",
        "Upload non-attesting Stage85 candidate packet",
        "CANDIDATE_IS_MIGRATION=false",
        "REMOTE_MUTATION=false",
        "TERMS_REGISTRY_ROW_CREATED=false",
        "REAL_ACCEPTANCE_COLLECTED=false",
        "TARGET_DECISION_CLOSED=false",
        "LEGAL_TERMS_GATE_READY=false",
        "CONTROLLED_LAUNCH=DENIED",
        "PAID_MEDIA=DENIED",
    ):
        if marker not in text:
            fail(f"Stage85 workflow marker missing: {marker}")


def verify_no_migration_promotion() -> None:
    found: list[Path] = []
    for root in (BACKEND / "migrations", BACKEND / "supabase" / "migrations"):
        if root.exists():
            found.extend(root.glob("*stage85*terms*acceptance*"))
    if found:
        fail("Stage85 must not promote candidate into migrations")


def main() -> None:
    verify_authority_and_upstream()
    verify_canonical_sources()
    verify_candidate_sql()
    verify_builder_and_workflow()
    verify_no_migration_promotion()
    print("STAGE85_TERMS_ACCEPTANCE_MIGRATION_CANDIDATE_GUARD=PASS")
    print("IMPLEMENTATION_UNIT_COUNT=4")
    print("CANDIDATE_IS_MIGRATION=false")
    print("REMOTE_MUTATION=false")
    print("TERMS_REGISTRY_ROW_CREATED=false")
    print("REAL_ACCEPTANCE_COLLECTED=false")
    print("TARGET_DECISION_CLOSED=false")
    print("LEGAL_TERMS_GATE_READY=false")


if __name__ == "__main__":
    main()
