from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage84_terms_acceptance_versioning_preparation_authority.json"
INVENTORY = ROOT / "10_compliance" / "inventory" / "STAGE84_TERMS_ACCEPTANCE_VERSIONING_IMPLEMENTATION_PREPARATION.json"
BUILDER = BACKEND / "tools" / "build_stage84_terms_acceptance_versioning_preparation.py"
OPEN_DECISIONS = ROOT / "10_compliance" / "drafts" / "COMPLIANCE_OPEN_DECISIONS.json"
TERMS_DRAFT = ROOT / "10_compliance" / "drafts" / "TERMS_OF_USE_CANDIDATE_PTBR.md"
STAGE83 = BACKEND / "stage83_billing_policy_review_questionnaire_skeleton_authority.json"
WORKFLOW = ROOT / ".github" / "workflows" / "stage84_terms_acceptance_versioning_preparation.yml"
FAILURE_CLASS = "BGF-STAGE84-TERMS-ACCEPTANCE-VERSIONING-PREPARATION-GUARD-839"
CANONICAL_REQUIRED = "Production mechanism binding user acceptance to immutable terms version/digest."
CANONICAL_RESOLUTION = "product implementation plus independent review"
FORBIDDEN_IMPORT_ROOTS = {"os", "subprocess", "socket", "urllib", "http", "requests", "psycopg", "supabase"}
FORBIDDEN_WORKFLOW_TOKENS = (
    "git push", "apply_migration", "execute_sql", "supabase db", "curl ", "wget ",
    "deploy-pages", "actions/deploy-pages", "powershell",
)


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE84_TERMS_ACCEPTANCE_VERSIONING_PREPARATION_GUARD=FAIL\n"
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


def verify_authority_and_upstream() -> None:
    authority = load_json(AUTHORITY)
    if authority.get("schema_version") != 1 or authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("Stage84 authority identity drift")
    if authority.get("stage") != "STAGE84_TERMS_ACCEPTANCE_VERSIONING_IMPLEMENTATION_PREPARATION":
        fail("Stage84 stage drift")
    if authority.get("baseline_main_sha") != "07366968780d6efa732022237116eb7f79201646":
        fail("Stage84 baseline main SHA drift")

    upstream = authority.get("upstream_stage83_green", {})
    expected = {
        "merged_main_sha": "07366968780d6efa732022237116eb7f79201646",
        "green_head_sha": "0062fa75bcc0ceb66172f9c864453e7550438b72",
        "dedicated_ci_run_id": 32990197181,
        "dedicated_ci_conclusion": "success",
        "flutter_quality_gate_run_id": 32990197521,
        "flutter_quality_gate_conclusion": "success",
        "artifact_id": 9614302419,
        "artifact_digest": "sha256:5b6c13ce3f2cbb09447cd90fd689151bd63d0419fd52a6b2b66acff87fec4e62",
        "artifact_is_legal_or_gate_evidence": False,
    }
    for key, value in expected.items():
        if upstream.get(key) != value:
            fail(f"Stage83 GREEN provenance drift: {key}")

    target = authority.get("canonical_target_open_decision", {})
    if target.get("id") != "TERMS_ACCEPTANCE_VERSIONING" or target.get("state") != "OPEN":
        fail("Stage84 target decision identity/state drift")
    if target.get("affected_gates") != ["legal_terms_of_use"]:
        fail("Stage84 target gate drift")
    if target.get("required") != CANONICAL_REQUIRED or target.get("resolution_authority") != CANONICAL_RESOLUTION:
        fail("Stage84 target decision wording drift")
    if target.get("stage84_can_close_decision") is not False:
        fail("Stage84 cannot close TERMS_ACCEPTANCE_VERSIONING")

    pins = authority.get("sealed_inputs", {})
    pinned = {
        OPEN_DECISIONS: pins.get("open_decisions_blob"),
        TERMS_DRAFT: pins.get("terms_candidate_blob"),
        STAGE83: pins.get("stage83_authority_blob"),
    }
    for path, expected_blob in pinned.items():
        if not isinstance(expected_blob, str) or git_blob_sha(path) != expected_blob:
            fail(f"sealed upstream input drift: {path.relative_to(ROOT)}")

    # Prevent the Stage83 fixed-source-pin cascade class from being recreated here.
    for key in pins:
        if key.startswith("stage84_"):
            fail("Stage84 sealed_inputs must not self-pin mutable Stage84 files")

    remote = authority.get("fresh_remote_read_only_observation", {})
    if remote.get("terms_or_acceptance_schema_surface_found") is not False:
        fail("Stage84 remote source observation changed")
    if remote.get("matching_business_terms_tables") != [] or remote.get("matching_business_acceptance_tables") != []:
        fail("Stage84 remote business terms/acceptance surface unexpectedly present")
    if remote.get("remote_mutation_performed") is not False:
        fail("Stage84 source observation must remain read-only")

    hard = authority.get("hard_boundaries", {})
    if not hard or any(value is not False for value in hard.values()):
        fail("Stage84 authority hard boundaries must all remain false")
    gates = authority.get("gates", {})
    if gates.get("legal_terms_of_use") != "DENIED" or gates.get("controlled_launch") != "DENIED" or gates.get("paid_media") != "DENIED":
        fail("Stage84 gate boundary drift")


def verify_canonical_sources_and_inventory() -> None:
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
    required_markers = (
        "DRAFT_UNREVIEWED_NOT_PUBLISHED_NOT_LEGAL_EVIDENCE",
        "`terms_version` imutável",
        "digest SHA-256 do documento aprovado",
        "data de vigência",
        "URL pública estável",
        "evidência de aceite vinculada à versão",
        "histórico de versões",
        "Mecanismo real de aceite versionado",
        "legal_terms_of_use = BLOCKED",
    )
    for marker in required_markers:
        if marker not in terms:
            fail(f"terms draft marker missing: {marker}")

    inventory = load_json(INVENTORY)
    if inventory.get("status") != "TECHNICAL_IMPLEMENTATION_PREPARATION_ONLY_NOT_TERMS_NOT_APPROVAL_NOT_EVIDENCE":
        fail("Stage84 inventory status drift")
    units = inventory.get("implementation_units")
    expected_ids = ["terms_document_registry", "terms_acceptance_ledger", "current_terms_resolver", "acceptance_gate"]
    if not isinstance(units, list) or [row.get("unit_id") for row in units if isinstance(row, dict)] != expected_ids:
        fail("Stage84 implementation units drift")
    if any(row.get("materialized_in_stage84") is not False for row in units):
        fail("Stage84 must not materialize implementation units")
    boundaries = inventory.get("stage84_boundaries", {})
    if not boundaries or any(value is not False for value in boundaries.values()):
        fail("Stage84 inventory boundaries must remain false")


def verify_builder_and_workflow() -> None:
    source = BUILDER.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        fail(f"Stage84 builder syntax error: {exc.msg}")
    for node in ast.walk(tree):
        roots: list[str] = []
        if isinstance(node, ast.Import):
            roots.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.append(node.module.split(".")[0])
        for root in roots:
            if root in FORBIDDEN_IMPORT_ROOTS:
                fail(f"Stage84 builder imports forbidden module: {root}")
    for marker in (
        "NON_ATTESTING_TERMS_ACCEPTANCE_VERSIONING_PREPARATION_PACKET",
        "terms_candidate_approved\": False",
        "real_acceptance_collected\": False",
        "schema_migration_created\": False",
        "remote_mutation\": False",
        "target_decision_closed\": False",
        "legal_terms_gate_ready\": False",
    ):
        if marker not in source:
            fail(f"Stage84 builder boundary marker missing: {marker}")

    text = WORKFLOW.read_text(encoding="utf-8")
    low = text.lower()
    for token in FORBIDDEN_WORKFLOW_TOKENS:
        if token in low:
            fail(f"Stage84 workflow contains forbidden token: {token}")
    for marker in (
        "permissions:\n  contents: read",
        "Checkout exact head",
        "Verify Stage84 terms acceptance versioning preparation",
        "Build deterministic Stage84 preparation packet twice",
        "cmp /tmp/stage84_terms_a.json /tmp/stage84_terms_b.json",
        "Upload non-attesting Stage84 preparation packet",
        "TERMS_CANDIDATE_APPROVED=false",
        "REAL_ACCEPTANCE_COLLECTED=false",
        "SCHEMA_MIGRATION_CREATED=false",
        "REMOTE_MUTATION=false",
        "TARGET_DECISION_CLOSED=false",
        "LEGAL_TERMS_GATE_READY=false",
        "CONTROLLED_LAUNCH=DENIED",
        "PAID_MEDIA=DENIED",
    ):
        if marker not in text:
            fail(f"Stage84 workflow marker missing: {marker}")


def verify_no_stage84_migration_or_collection() -> None:
    found: list[Path] = []
    for root in (BACKEND / "migrations", BACKEND / "supabase" / "migrations"):
        if root.exists():
            found.extend(root.glob("*stage84*"))
    if found:
        fail("Stage84 preparation must not create a Supabase migration")
    forbidden = [
        ROOT / "10_compliance" / "review" / "STAGE84_TERMS_APPROVAL.json",
        ROOT / "10_compliance" / "review" / "STAGE84_REAL_TERMS_ACCEPTANCE.json",
    ]
    for path in forbidden:
        if path.exists():
            fail(f"Stage84 must not create approval/acceptance evidence: {path.relative_to(ROOT)}")


def main() -> None:
    verify_authority_and_upstream()
    verify_canonical_sources_and_inventory()
    verify_builder_and_workflow()
    verify_no_stage84_migration_or_collection()
    print("STAGE84_TERMS_ACCEPTANCE_VERSIONING_PREPARATION_GUARD=PASS")
    print("IMPLEMENTATION_UNIT_COUNT=4")
    print("TERMS_CANDIDATE_APPROVED=false")
    print("REAL_ACCEPTANCE_COLLECTED=false")
    print("SCHEMA_MIGRATION_CREATED=false")
    print("REMOTE_MUTATION=false")
    print("TARGET_DECISION_CLOSED=false")
    print("LEGAL_TERMS_GATE_READY=false")


if __name__ == "__main__":
    main()
