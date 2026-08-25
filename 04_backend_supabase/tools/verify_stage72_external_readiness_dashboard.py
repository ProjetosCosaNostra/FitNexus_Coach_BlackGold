from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage72_external_readiness_dashboard_authority.json"
STAGE47 = BACKEND / "stage47_unified_external_evidence_intake_orchestration_authority.json"
PLACEHOLDERS = BACKEND / "external_gate_evidence_placeholders.json"
OPEN_DECISIONS = ROOT / "10_compliance" / "drafts" / "COMPLIANCE_OPEN_DECISIONS.json"
STAGE71 = BACKEND / "stage71_postdeploy_evidence_intake_contract_authority.json"
BUILDER = BACKEND / "tools" / "build_stage72_external_readiness_dashboard.py"
WORKFLOW = ROOT / ".github" / "workflows" / "stage72_external_readiness_dashboard.yml"

BASELINE_MAIN = "884589037ad29862f07eb4ab79e38a88f8e305a4"
STAGE47_BLOB = "9a8d504d3462a926014ced34508cdf42babbff46"
PLACEHOLDERS_BLOB = "07e6eb3330076f3e576ed2dd2a2e385f5fa3b2db"
OPEN_DECISIONS_BLOB = "215d527c1cb79d7b72697f03f1f84887e3a72d95"
STAGE71_BLOB = "b365902a5b8777ffc842a6bbf731c98453f6c875"
BUILDER_BLOB = "878e3af23fa5287fd8f4db7ce277ab8a842e7299"
FAILURE_CLASS = "BGF-STAGE72-EXTERNAL-READINESS-DASHBOARD-GUARD-695"


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE72_EXTERNAL_READINESS_DASHBOARD_GUARD=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\n"
        f"DETAIL={detail}"
    )


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to load {path.relative_to(ROOT)}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"expected object: {path.relative_to(ROOT)}")
    return value


def git_blob(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def require(mapping: dict, expected: dict, label: str) -> None:
    if not isinstance(mapping, dict):
        fail(f"{label} must be object")
    for key, value in expected.items():
        if mapping.get(key) != value:
            fail(f"{label} drift: {key}")


def main() -> None:
    authority = load(AUTHORITY)
    stage47 = load(STAGE47)
    placeholders = load(PLACEHOLDERS)
    decisions = load(OPEN_DECISIONS)
    stage71 = load(STAGE71)

    pinned = (
        (STAGE47, STAGE47_BLOB, "Stage47"),
        (PLACEHOLDERS, PLACEHOLDERS_BLOB, "external gate placeholders"),
        (OPEN_DECISIONS, OPEN_DECISIONS_BLOB, "Stage67 open decisions"),
        (STAGE71, STAGE71_BLOB, "Stage71"),
        (BUILDER, BUILDER_BLOB, "Stage72 builder"),
    )
    for path, expected, label in pinned:
        if git_blob(path) != expected:
            fail(f"{label} blob drift")

    require(
        authority,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "stage": "STAGE72_EXTERNAL_READINESS_DASHBOARD",
            "baseline_main_sha": BASELINE_MAIN,
            "current_state": "DETERMINISTIC_NON_ATTESTING_EXTERNAL_BLOCKER_DASHBOARD_PREPARED_NO_EVIDENCE_PROMOTION_NO_REMOTE_MUTATION",
        },
        "Stage72 authority",
    )
    require(
        stage47,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "stage": "STAGE47_UNIFIED_EXTERNAL_EVIDENCE_INTAKE_ORCHESTRATION",
            "current_state": "PREPARED_UNIFIED_LOCAL_RECEIPT_REVIEW_ORCHESTRATION_NO_EVIDENCE_INGESTION_NO_GATE_PROMOTION_NO_REMOTE_MUTATION",
        },
        "Stage47 authority",
    )
    require(
        placeholders,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "template_state": "PLACEHOLDER_ONLY_NOT_ATTESTATION",
        },
        "external gate placeholders",
    )
    require(
        decisions,
        {
            "schema_version": 1,
            "status": "DRAFT_UNREVIEWED_NOT_EVIDENCE",
        },
        "Stage67 open decisions",
    )
    require(
        stage71,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "stage": "STAGE71_POSTDEPLOY_EVIDENCE_INTAKE_CONTRACT",
            "current_state": "POSTDEPLOY_DIGEST_ONLY_EVIDENCE_INTAKE_CONTRACT_PREPARED_NO_DEPLOYMENT_NO_GATE_PROMOTION",
        },
        "Stage71 authority",
    )

    remote = authority.get("fresh_remote_read_only_receipt", {})
    require(
        remote,
        {
            "source": "Supabase.execute_sql_read_only",
            "observed_at_utc": "2026-08-25T18:08:25.942073+00:00",
            "auth_users": 0,
            "organizations": 0,
            "students": 0,
            "asaas_state": "selected_pending_credentials",
            "asaas_activated_at": None,
            "ready_evidence_migration_count": 0,
            "blocked_evidence_migration_count": 6,
            "tracking_core_ready": True,
            "pricing_experiment_ready": True,
            "remote_mutation_performed": False,
        },
        "fresh remote receipt",
    )

    contract = authority.get("dashboard_contract", {})
    expected_order = [
        "billing_provider_credentials",
        "legal_terms_of_use",
        "legal_privacy_notice",
        "legal_role_mapping",
        "data_subject_request_channel",
        "incident_response",
        "production_deployment",
    ]
    if contract.get("external_gate_count") != 7 or contract.get("gate_order") != expected_order:
        fail("external gate order/count drift")
    for key in (
        "automatic_internal_signals_reported_separately",
        "candidate_tooling_reported_separately_from_evidence",
        "required_evidence_items_come_only_from_stage20_placeholders",
        "open_decisions_come_only_from_stage67_registry",
        "canonical_reviewers_come_only_from_stage47",
        "remote_state_is_pinned_read_only_observation",
    ):
        if contract.get(key) is not True:
            fail(f"dashboard contract must remain true: {key}")
    for key in (
        "dashboard_can_mark_gate_ready",
        "dashboard_can_create_evidence_ref",
        "dashboard_can_create_evidence_digest",
        "dashboard_can_create_evidence_migration",
        "dashboard_can_call_provider",
        "dashboard_can_deploy",
        "dashboard_can_mutate_supabase",
        "dashboard_can_promote_controlled_launch",
        "dashboard_can_promote_paid_media",
    ):
        if contract.get(key) is not False:
            fail(f"dashboard contract must remain false: {key}")

    canonical = stage47.get("canonical_reviewers")
    placeholder_gates = placeholders.get("gates")
    inventory = authority.get("candidate_tooling_inventory")
    if not isinstance(canonical, list) or len(canonical) != 7:
        fail("canonical reviewer count drift")
    if not isinstance(placeholder_gates, dict) or set(placeholder_gates) != set(expected_order):
        fail("placeholder gate coverage drift")
    if not isinstance(inventory, dict) or set(inventory) != set(expected_order):
        fail("candidate tooling inventory coverage drift")
    if len({item.get("gate_code") for item in canonical if isinstance(item, dict)}) != 7:
        fail("canonical reviewer gate coverage/uniqueness drift")

    unresolved = decisions.get("unresolved")
    if not isinstance(unresolved, list) or len(unresolved) != 14:
        fail("Stage67 open decision count drift")
    if any(not isinstance(item, dict) or item.get("state") != "OPEN" for item in unresolved):
        fail("Stage67 decisions must remain OPEN")

    for gate in expected_order:
        gate_state = authority.get("gates", {}).get(gate)
        if not isinstance(gate_state, str) or not gate_state.startswith("DENIED_"):
            fail(f"external gate is not denied: {gate}")
        placeholder = placeholder_gates[gate]
        if placeholder.get("placeholder_only") is not True:
            fail(f"placeholder boundary drift: {gate}")
        if placeholder.get("evidence_ref") is not None or placeholder.get("evidence_digest") is not None:
            fail(f"placeholder contains evidence: {gate}")
        required = placeholder.get("required_evidence")
        if not isinstance(required, list) or not required:
            fail(f"required evidence missing: {gate}")

    if authority.get("gates", {}).get("controlled_launch") != "DENIED":
        fail("controlled launch boundary drift")
    if authority.get("gates", {}).get("paid_media") != "DENIED":
        fail("paid media boundary drift")

    builder_text = BUILDER.read_text(encoding="utf-8")
    try:
        tree = ast.parse(builder_text)
    except SyntaxError as exc:
        fail(f"builder syntax invalid: {exc.msg}")
    forbidden_import_roots = {"os", "subprocess", "socket", "urllib", "http", "requests", "supabase"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".", 1)[0] in forbidden_import_roots:
                    fail(f"builder imports forbidden remote/mutation module: {alias.name}")
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module.split(".", 1)[0] in forbidden_import_roots:
                fail(f"builder imports forbidden remote/mutation module: {node.module}")

    for fragment in (
        '"NON_ATTESTING_EXTERNAL_READINESS_BLOCKER_DASHBOARD"',
        '"ALL_EXTERNAL_GATES_BLOCKED_REAL_INPUTS_REQUIRED"',
        '"ready": False',
        '"candidate_tooling_is_evidence": False',
        '"evidence_ref": None',
        '"evidence_digest": None',
        '"candidate_tooling_is_not_evidence": True',
        '"internal_ready_signals_are_not_launch_authority": True',
        '"dashboard_can_mark_gate_ready": False',
        '"dashboard_can_create_evidence_migration": False',
        '"remote_mutation_performed": False',
        '"controlled_launch_promoted": False',
    ):
        if fragment not in builder_text:
            fail(f"builder non-attesting invariant missing: {fragment}")
    for forbidden in (
        "execute_sql",
        "apply_migration",
        "git push",
        "actions/deploy-pages",
        "--mark-ready",
        "--promote",
    ):
        if forbidden in builder_text.lower():
            fail(f"builder contains forbidden action/bypass: {forbidden}")

    workflow = WORKFLOW.read_text(encoding="utf-8")
    workflow_lower = workflow.lower()
    for fragment in (
        "permissions:\n  contents: read",
        "verify_stage72_external_readiness_dashboard.py",
        "build_stage72_external_readiness_dashboard.py",
        "cmp /tmp/stage72_dashboard_a.json /tmp/stage72_dashboard_b.json",
        "actions/upload-artifact@v4",
        "retention-days: 7",
    ):
        if fragment not in workflow:
            fail(f"workflow invariant missing: {fragment}")
    for forbidden in (
        "actions/deploy-pages",
        "peaceiris/actions-gh-pages",
        "git push",
        "supabase db",
        "apply_migration",
        "execute_sql",
        "curl ",
        "wget ",
    ):
        if forbidden in workflow_lower:
            fail(f"workflow contains forbidden remote action: {forbidden}")

    if list((BACKEND / "migrations").glob("*stage72*.sql")):
        fail("Stage72 dashboard must not create a migration")

    print("STAGE72_EXTERNAL_READINESS_DASHBOARD_GUARD=PASS")
    print("EXTERNAL_GATE_COUNT=7")
    print("READY_EXTERNAL_GATE_COUNT=0")
    print("TRACKING_CORE_READY=true")
    print("PRICING_EXPERIMENT_READY=true")
    print("INTERNAL_READY_IS_LAUNCH_AUTHORITY=false")
    print("REMOTE_MUTATION=false")
    print("CONTROLLED_LAUNCH=DENIED")


if __name__ == "__main__":
    main()
