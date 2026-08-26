from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage73_cross_gate_decision_frontier_authority.json"
STAGE72 = BACKEND / "stage72_external_readiness_dashboard_authority.json"
DECISIONS = ROOT / "10_compliance" / "drafts" / "COMPLIANCE_OPEN_DECISIONS.json"
BUILDER = BACKEND / "tools" / "build_stage73_cross_gate_decision_frontier.py"
WORKFLOW = ROOT / ".github" / "workflows" / "stage73_cross_gate_decision_frontier.yml"
FAILURE_CLASS = "BGF-STAGE73-CROSS-GATE-FRONTIER-GUARD-705"

EXPECTED_STAGE72_BLOB = "d142f3f4e690072c08cbb0968e02ef73df4c3e22"
EXPECTED_DECISIONS_BLOB = "215d527c1cb79d7b72697f03f1f84887e3a72d95"
EXPECTED_GATES = [
    "billing_provider_credentials",
    "legal_terms_of_use",
    "legal_privacy_notice",
    "legal_role_mapping",
    "data_subject_request_channel",
    "incident_response",
    "production_deployment",
]
EXPECTED_FANOUT = {
    "CONTROLLER_PROCESSOR_ROLE_MATRIX": 4,
    "LEGAL_REVIEWER_REFERENCE": 3,
    "RETENTION_MATRIX": 3,
    "SENSITIVE_DATA_TREATMENT": 3,
    "LEGAL_ENTITY_IDENTITY": 2,
    "SUBPROCESSOR_AND_TRANSFER_MAP": 2,
    "BILLING_CANCELLATION_REFUND_POLICY": 1,
    "TERMS_ACCEPTANCE_VERSIONING": 1,
    "DSR_STABLE_PUBLIC_ROUTE": 1,
    "DSR_OWNER_AND_BACKUP": 1,
    "DSR_CONTROLLED_TESTS": 1,
    "INCIDENT_OWNER_ASSIGNMENTS": 1,
    "INCIDENT_RISK_AND_COMMUNICATION_PROCEDURE": 1,
    "INCIDENT_TABLETOPS": 1,
}
FORBIDDEN_IMPORT_ROOTS = {
    "os",
    "subprocess",
    "socket",
    "urllib",
    "http",
    "requests",
    "psycopg",
    "supabase",
}
FORBIDDEN_WORKFLOW_TOKENS = (
    "git push",
    "apply_migration",
    "execute_sql",
    "supabase db",
    "curl ",
    "wget ",
    "gh pages",
    "deploy-pages",
    "actions/deploy-pages",
    "powershell",
)


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE73_CROSS_GATE_DECISION_FRONTIER_GUARD=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\n"
        f"DETAIL={detail}"
    )


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to load {path.relative_to(ROOT)}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"expected JSON object: {path.relative_to(ROOT)}")
    return value


def require_false(mapping: dict, key: str, label: str) -> None:
    if mapping.get(key) is not False:
        fail(f"{label} must keep {key}=false")


def verify_authority() -> tuple[dict, dict, dict]:
    authority = load(AUTHORITY)
    stage72 = load(STAGE72)
    decisions = load(DECISIONS)

    if authority.get("schema_version") != 1:
        fail("authority schema_version drift")
    if authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("authority project_ref drift")
    if authority.get("stage") != "STAGE73_CROSS_GATE_DECISION_FRONTIER":
        fail("authority stage drift")
    if authority.get("baseline_main_sha") != "1589c7c4598dee54442dcdea664c2193687dab06":
        fail("authority baseline main SHA drift")

    upstream = authority.get("upstream_authority")
    if not isinstance(upstream, dict):
        fail("upstream authority missing")
    if upstream.get("stage72_external_readiness_dashboard_blob") != EXPECTED_STAGE72_BLOB:
        fail("Stage72 authority blob pin drift")
    if upstream.get("stage67_open_decisions_blob") != EXPECTED_DECISIONS_BLOB:
        fail("Stage67 open-decision blob pin drift")

    contract = authority.get("frontier_contract")
    if not isinstance(contract, dict):
        fail("frontier contract missing")
    expected_exact = {
        "ranking_metric": "decision_gate_fanout_count_only",
        "ranking_order": "fanout_desc_then_decision_id_asc",
        "ranking_is_business_priority": False,
        "ranking_is_legal_priority": False,
        "ranking_is_launch_authority": False,
        "top_shared_decision_expected": "CONTROLLER_PROCESSOR_ROLE_MATRIX",
        "top_shared_decision_expected_fanout": 4,
        "zero_open_decisions_means_gate_ready": False,
        "billing_and_production_without_stage67_decisions_remain_external_blockers": True,
        "candidate_documents_must_remain_unreviewed": True,
        "candidate_document_digests_are_not_approval_digests": True,
        "review_packet_is_evidence": False,
        "review_packet_can_replace_independent_review": False,
    }
    for key, expected in expected_exact.items():
        if contract.get(key) != expected:
            fail(f"frontier contract drift: {key}")
    for key in (
        "network_calls_allowed",
        "provider_calls_allowed",
        "supabase_mutation_allowed",
        "deployment_action_allowed",
        "evidence_migration_creation_allowed",
        "gate_promotion_allowed",
        "controlled_launch_promotion_allowed",
        "paid_media_promotion_allowed",
    ):
        require_false(contract, key, "frontier contract")

    gate_order = stage72.get("dashboard_contract", {}).get("gate_order")
    if gate_order != EXPECTED_GATES:
        fail("Stage72 gate order drift")
    if set(authority.get("gates", {})) != set(EXPECTED_GATES + ["stage73_decision_frontier", "controlled_launch", "paid_media", "launch"]):
        fail("Stage73 gate set drift")
    for gate in EXPECTED_GATES:
        state = authority["gates"].get(gate)
        if not isinstance(state, str) or not state.startswith("DENIED_"):
            fail(f"external gate must remain denied: {gate}")
    for gate in ("controlled_launch", "paid_media", "launch"):
        if authority["gates"].get(gate) != "DENIED":
            fail(f"{gate} must remain DENIED")

    remote = authority.get("fresh_remote_read_only_receipt")
    if not isinstance(remote, dict):
        fail("fresh remote read-only receipt missing")
    if remote.get("auth_users") != 0 or remote.get("organizations") != 0 or remote.get("students") != 0:
        fail("fresh remote empty-customer baseline drift")
    if remote.get("asaas_state") != "selected_pending_credentials" or remote.get("asaas_activated_at") is not None:
        fail("fresh remote Asaas boundary drift")
    if remote.get("ready_evidence_migration_count") != 0 or remote.get("blocked_evidence_migration_count") != 6:
        fail("fresh remote evidence-migration counts drift")
    require_false(remote, "remote_mutation_performed", "fresh remote receipt")

    return authority, stage72, decisions


def verify_decision_fanout(decisions: dict) -> None:
    if decisions.get("status") != "DRAFT_UNREVIEWED_NOT_EVIDENCE":
        fail("open-decision registry status drift")
    unresolved = decisions.get("unresolved")
    if not isinstance(unresolved, list) or len(unresolved) != 14:
        fail("expected exactly fourteen open decisions")

    gate_set = set(EXPECTED_GATES)
    actual: dict[str, int] = {}
    affected: dict[str, set[str]] = {}
    for item in unresolved:
        if not isinstance(item, dict) or item.get("state") != "OPEN":
            fail("all decisions must remain OPEN objects")
        decision_id = str(item.get("id", ""))
        applies = item.get("applies_to")
        if not decision_id or not isinstance(applies, list):
            fail("decision shape drift")
        gates = {str(gate) for gate in applies if gate in gate_set}
        actual[decision_id] = len(gates)
        affected[decision_id] = gates

    if actual != EXPECTED_FANOUT:
        fail(f"decision fanout map drift: actual={actual}")
    if affected.get("CONTROLLER_PROCESSOR_ROLE_MATRIX") != {
        "legal_privacy_notice",
        "legal_role_mapping",
        "data_subject_request_channel",
        "incident_response",
    }:
        fail("top shared decision affected-gate set drift")

    per_gate = {gate: 0 for gate in EXPECTED_GATES}
    for gates in affected.values():
        for gate in gates:
            per_gate[gate] += 1
    zero = {gate for gate, count in per_gate.items() if count == 0}
    if zero != {"billing_provider_credentials", "production_deployment"}:
        fail(f"zero-decision gate set drift: {sorted(zero)}")


def verify_candidate_docs(authority: dict) -> None:
    paths = authority.get("candidate_review_documents")
    if not isinstance(paths, list) or len(paths) != 6:
        fail("candidate review-document inventory must contain six paths")
    expected = {
        "10_compliance/drafts/PRIVACY_NOTICE_CANDIDATE_PTBR.md": "DRAFT_UNREVIEWED_NOT_PUBLISHED_NOT_LEGAL_EVIDENCE",
        "10_compliance/drafts/TERMS_OF_USE_CANDIDATE_PTBR.md": "DRAFT_UNREVIEWED_NOT_PUBLISHED_NOT_LEGAL_EVIDENCE",
        "10_compliance/drafts/PROCESSING_ROLE_MATRIX_CANDIDATE.md": "DRAFT_UNREVIEWED_NOT_LEGAL_EVIDENCE",
        "10_compliance/drafts/DATA_SUBJECT_REQUEST_RUNBOOK_CANDIDATE.md": "DRAFT_UNREVIEWED_NOT_OPERATIONAL_EVIDENCE",
        "10_compliance/drafts/INCIDENT_RESPONSE_RUNBOOK_CANDIDATE.md": "DRAFT_UNREVIEWED_NOT_OPERATIONAL_EVIDENCE",
        "10_compliance/drafts/COMPLIANCE_OPEN_DECISIONS.json": "DRAFT_UNREVIEWED_NOT_EVIDENCE",
    }
    if set(paths) != set(expected):
        fail("candidate review-document inventory drift")
    for raw, marker in expected.items():
        path = ROOT / raw
        if raw.endswith(".json"):
            value = load(path)
            if value.get("status") != marker:
                fail(f"candidate JSON status drift: {raw}")
        else:
            text = path.read_text(encoding="utf-8")
            if marker not in text:
                fail(f"candidate document status marker drift: {raw}")


def verify_builder_source() -> None:
    try:
        source = BUILDER.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (OSError, SyntaxError) as exc:
        fail(f"builder unreadable or invalid Python: {type(exc).__name__}")

    for node in ast.walk(tree):
        roots: list[str] = []
        if isinstance(node, ast.Import):
            roots.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.append(node.module.split(".")[0])
        for root in roots:
            if root in FORBIDDEN_IMPORT_ROOTS:
                fail(f"builder imports forbidden network/remote module: {root}")

    required_markers = (
        "NON_ATTESTING_CROSS_GATE_DECISION_FRONTIER",
        "OPEN_DECISIONS_RANKED_BY_CROSS_GATE_FANOUT_NOT_PRIORITY_NOT_EVIDENCE",
        "decision_gate_fanout_count_only",
        "fanout_desc_then_decision_id_asc",
        "ZERO_STAGE67_DECISIONS_DOES_NOT_MEAN_GATE_READY",
        "REAL_INDEPENDENT_REVIEW_REFERENCE_REQUIRED_FOR_HIGHEST_FANOUT_DECISION_PACKET",
        "candidate_document_digests_are_approval_digests",
        "CONTROLLER_PROCESSOR_ROLE_MATRIX",
    )
    for marker in required_markers:
        if marker not in source:
            fail(f"builder missing required boundary marker: {marker}")


def verify_workflow_source() -> None:
    try:
        text = WORKFLOW.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"workflow unreadable: {type(exc).__name__}")
    lowered = text.lower()
    for token in FORBIDDEN_WORKFLOW_TOKENS:
        if token in lowered:
            fail(f"workflow contains forbidden action/token: {token}")
    required = (
        "permissions:\n  contents: read",
        "Checkout exact head",
        "Verify Stage73 frontier contract",
        "Build deterministic frontier twice",
        "cmp",
        "Upload non-attesting decision frontier",
        "retention-days: 7",
        "GATE_PROMOTION=false",
        "CONTROLLED_LAUNCH=DENIED",
        "REMOTE_MUTATION=false",
    )
    for marker in required:
        if marker not in text:
            fail(f"workflow missing required marker: {marker}")


def verify_no_migration() -> None:
    matches = list((BACKEND / "supabase" / "migrations").glob("*stage73*")) if (BACKEND / "supabase" / "migrations").exists() else []
    matches += list((BACKEND / "migrations").glob("*stage73*")) if (BACKEND / "migrations").exists() else []
    if matches:
        fail("Stage73 must not create a Supabase migration")


def main() -> None:
    authority, _stage72, decisions = verify_authority()
    verify_decision_fanout(decisions)
    verify_candidate_docs(authority)
    verify_builder_source()
    verify_workflow_source()
    verify_no_migration()

    print("STAGE73_CROSS_GATE_DECISION_FRONTIER_GUARD=PASS")
    print("OPEN_DECISIONS=14")
    print("TOP_SHARED_DECISION=CONTROLLER_PROCESSOR_ROLE_MATRIX")
    print("TOP_FANOUT=4")
    print("ZERO_DECISION_GATES=billing_provider_credentials,production_deployment")
    print("FANOUT_IS_PRIORITY=false")
    print("REVIEW_PACKET_IS_EVIDENCE=false")
    print("GATE_PROMOTION=false")
    print("REMOTE_MUTATION=false")


if __name__ == "__main__":
    main()
