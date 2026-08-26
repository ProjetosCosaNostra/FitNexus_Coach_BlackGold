from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage80r1_registry_pin_reconciliation_authority.json"
HISTORICAL_STAGE80_AUTHORITY = BACKEND / "stage80_sensitive_data_minimization_inventory_authority.json"
CURRENT_STAGE80_REGISTRY = ROOT / "10_compliance" / "inventory" / "STAGE80_TECHNICAL_SENSITIVE_DATA_MINIMIZATION_REGISTRY.json"
OPEN_DECISIONS = ROOT / "10_compliance" / "drafts" / "COMPLIANCE_OPEN_DECISIONS.json"
WORKFLOW = ROOT / ".github" / "workflows" / "stage80r1_registry_pin_reconciliation.yml"
FAILURE_CLASS = "BGF-STAGE80R1-REGISTRY-PIN-RECONCILIATION-GUARD-781"
FORBIDDEN_IMPORT_ROOTS = {"os", "subprocess", "socket", "urllib", "http", "requests", "psycopg", "supabase"}
FORBIDDEN_WORKFLOW_TOKENS = (
    "git push", "apply_migration", "execute_sql", "supabase db", "curl ", "wget ",
    "deploy-pages", "actions/deploy-pages", "powershell",
)


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE80R1_REGISTRY_PIN_RECONCILIATION=FAIL\n"
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
    try:
        raw = path.read_bytes()
    except OSError as exc:
        fail(f"unable to read {path.relative_to(ROOT)}: {type(exc).__name__}")
    header = f"blob {len(raw)}\0".encode("utf-8")
    return hashlib.sha1(header + raw).hexdigest()


def verify_authority() -> dict:
    a = load(AUTHORITY)
    if a.get("schema_version") != 1 or a.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("Stage80R1 authority identity drift")
    if a.get("stage") != "STAGE80R1_REGISTRY_PIN_RECONCILIATION":
        fail("Stage80R1 stage drift")
    if a.get("baseline_main_sha") != "32a0b72a001902e6e0417975105023e017798482":
        fail("Stage80R1 baseline main SHA drift")
    if a.get("current_state") != "HISTORICAL_STAGE80_AUTHORITY_SNAPSHOT_PRESERVED_CURRENT_REGISTRY_PIN_RECONCILED_BY_ADDENDUM_NO_POLICY_OR_GATE_PROMOTION":
        fail("Stage80R1 current state drift")

    historical = a.get("historical_stage80_authority", {})
    if historical.get("path") != "04_backend_supabase/stage80_sensitive_data_minimization_inventory_authority.json":
        fail("historical Stage80 authority path drift")
    if historical.get("blob") != "9461cf96aaa44f1b422f78a137fe338ef51eae87":
        fail("historical Stage80 authority blob pin drift")
    if historical.get("embedded_stage80_registry_blob") != "b72c073e5b4079ef78dd3de94a5d3123dc7e4488":
        fail("historical embedded Stage80 registry pin drift")
    if historical.get("historical_snapshot_must_not_be_rewritten") is not True:
        fail("historical authority preservation boundary missing")

    current = a.get("current_stage80_registry", {})
    if current.get("path") != "10_compliance/inventory/STAGE80_TECHNICAL_SENSITIVE_DATA_MINIMIZATION_REGISTRY.json":
        fail("current Stage80 registry path drift")
    if current.get("blob") != "2aacf6d36834f6542e0cc9ef1f9be360fc61019d":
        fail("current Stage80 registry blob pin drift")
    if current.get("status") != "TECHNICAL_SENSITIVE_DATA_MINIMIZATION_REGISTRY_NOT_FINAL_LEGAL_CLASSIFICATION_NOT_POLICY_NOT_EVIDENCE":
        fail("current Stage80 registry status drift")

    rec = a.get("reconciliation", {})
    if rec.get("mismatch_confirmed") is not True:
        fail("Stage80 registry pin mismatch must remain explicitly confirmed")
    for key in (
        "semantic_policy_change", "legal_classification_change", "minimization_policy_approval_change", "target_open_decision_change"
    ):
        if rec.get(key) is not False:
            fail(f"Stage80R1 reconciliation boundary must keep {key}=false")
    if rec.get("current_registry_is_stage80_operational_source_for_downstream_read_only_binding") is not True:
        fail("current Stage80 registry downstream binding missing")
    if rec.get("historical_authority_snapshot_remains_provenance_evidence_only") is not True:
        fail("historical Stage80 authority provenance boundary missing")
    if rec.get("downstream_stage_must_pin_both_addendum_and_current_registry") is not True:
        fail("downstream dual-pin requirement missing")

    green = a.get("stage80_green_evidence", {})
    expected_green = {
        "exact_head_sha": "c29183359eaf21ea421af09c23a7804ad23ab55b",
        "dedicated_workflow_run_id": 32964099011,
        "dedicated_workflow_conclusion": "success",
        "flutter_quality_gate_run_id": 32964098987,
        "flutter_quality_gate_conclusion": "success",
        "artifact_id": 9604997905,
        "artifact_digest": "sha256:f504b98221d3b8c01527523e9f9c793037c984d007aebc74178c7d03fee3a95d",
        "merged_main_sha": "32a0b72a001902e6e0417975105023e017798482",
    }
    for key, value in expected_green.items():
        if green.get(key) != value:
            fail(f"Stage80 green evidence drift: {key}")

    remote = a.get("fresh_remote_read_only_receipt", {})
    if [remote.get("auth_users"), remote.get("organizations"), remote.get("students")] != [0, 0, 0]:
        fail("Stage80R1 remote customer baseline drift")
    if remote.get("asaas_state") != "selected_pending_credentials" or remote.get("asaas_activated_at") is not None:
        fail("Stage80R1 Asaas baseline drift")
    if remote.get("remote_mutation_performed") is not False:
        fail("Stage80R1 remote mutation boundary drift")

    target = a.get("target_open_decision", {})
    if target.get("id") != "SENSITIVE_DATA_TREATMENT" or target.get("state") != "OPEN":
        fail("SENSITIVE_DATA_TREATMENT must remain OPEN")
    if target.get("stage80r1_can_close_decision") is not False:
        fail("Stage80R1 cannot close SENSITIVE_DATA_TREATMENT")

    contract = a.get("reconciliation_contract", {})
    if contract.get("historical_authority_mutation_allowed") is not False or contract.get("current_registry_mutation_allowed") is not False:
        fail("Stage80R1 cannot mutate reconciled upstream artifacts")
    for key in (
        "legal_or_privacy_review_performed", "final_sensitive_data_classification_approved",
        "sensitive_data_processing_policy_approved", "network_calls_allowed", "provider_calls_allowed",
        "supabase_mutation_allowed", "deployment_action_allowed", "evidence_ref_creation_allowed",
        "evidence_digest_promotion_allowed", "evidence_migration_creation_allowed", "gate_promotion_allowed",
        "controlled_launch_promotion_allowed", "paid_media_promotion_allowed",
    ):
        if contract.get(key) is not False:
            fail(f"Stage80R1 contract must keep {key}=false")
    return a


def verify_pinned_files() -> None:
    if git_blob_sha(HISTORICAL_STAGE80_AUTHORITY) != "9461cf96aaa44f1b422f78a137fe338ef51eae87":
        fail("historical Stage80 authority bytes no longer match pinned snapshot")
    historical = load(HISTORICAL_STAGE80_AUTHORITY)
    if historical.get("stage80_registry", {}).get("blob") != "b72c073e5b4079ef78dd3de94a5d3123dc7e4488":
        fail("historical Stage80 authority no longer exposes the pre-normalization registry pin")

    if git_blob_sha(CURRENT_STAGE80_REGISTRY) != "2aacf6d36834f6542e0cc9ef1f9be360fc61019d":
        fail("current Stage80 registry bytes do not match reconciled pin")
    registry = load(CURRENT_STAGE80_REGISTRY)
    non_tables = registry.get("non_table_surfaces")
    if not isinstance(non_tables, list) or len(non_tables) != 2:
        fail("current Stage80 non-table surface count drift")
    ingress = next((x for x in non_tables if isinstance(x, dict) and x.get("surface_id") == "support_and_dsr_free_form_ingress"), None)
    if not isinstance(ingress, dict):
        fail("support/DSR ingress surface missing")
    if ingress.get("source_document_markers") != ["suporte", "solicitações de direitos", "não enviar excesso"]:
        fail("support/DSR source marker normalization drift")
    if ingress.get("approved_policy_state") != "UNRESOLVED":
        fail("support/DSR sensitive-data policy unexpectedly resolved")

    decisions = load(OPEN_DECISIONS)
    unresolved = decisions.get("unresolved")
    target = next((x for x in unresolved if isinstance(x, dict) and x.get("id") == "SENSITIVE_DATA_TREATMENT"), None) if isinstance(unresolved, list) else None
    if not isinstance(target, dict) or target.get("state") != "OPEN":
        fail("global SENSITIVE_DATA_TREATMENT must remain OPEN")


def verify_self_and_workflow() -> None:
    try:
        source = Path(__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (OSError, SyntaxError) as exc:
        fail(f"Stage80R1 guard unreadable: {type(exc).__name__}")
    for node in ast.walk(tree):
        roots: list[str] = []
        if isinstance(node, ast.Import):
            roots.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.append(node.module.split(".")[0])
        for root in roots:
            if root in FORBIDDEN_IMPORT_ROOTS:
                fail(f"Stage80R1 guard imports forbidden remote module: {root}")

    try:
        workflow = WORKFLOW.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"Stage80R1 workflow unreadable: {type(exc).__name__}")
    low = workflow.lower()
    for token in FORBIDDEN_WORKFLOW_TOKENS:
        if token in low:
            fail(f"Stage80R1 workflow contains forbidden token: {token}")
    for marker in (
        "permissions:\n  contents: read",
        "Checkout exact head",
        "Verify Stage80R1 registry pin reconciliation",
        "Upload non-attesting Stage80R1 reconciliation addendum",
        "HISTORICAL_AUTHORITY_REWRITTEN=false",
        "CURRENT_REGISTRY_MUTATED=false",
        "SENSITIVE_DATA_POLICY_APPROVED=false",
        "TARGET_DECISION_CLOSED=false",
        "GATE_PROMOTION=false",
        "REMOTE_MUTATION=false",
    ):
        if marker not in workflow:
            fail(f"Stage80R1 workflow missing marker: {marker}")


def main() -> None:
    verify_authority()
    verify_pinned_files()
    verify_self_and_workflow()
    print("STAGE80R1_REGISTRY_PIN_RECONCILIATION=PASS")
    print("HISTORICAL_AUTHORITY_BLOB=9461cf96aaa44f1b422f78a137fe338ef51eae87")
    print("HISTORICAL_REGISTRY_PIN=b72c073e5b4079ef78dd3de94a5d3123dc7e4488")
    print("CURRENT_REGISTRY_PIN=2aacf6d36834f6542e0cc9ef1f9be360fc61019d")
    print("SEMANTIC_POLICY_CHANGE=false")
    print("SENSITIVE_DATA_POLICY_APPROVED=false")
    print("TARGET_DECISION_CLOSED=false")
    print("REMOTE_MUTATION=false")


if __name__ == "__main__":
    main()
