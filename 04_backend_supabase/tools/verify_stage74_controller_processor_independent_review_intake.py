from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage74_controller_processor_independent_review_intake_authority.json"
STAGE73 = BACKEND / "stage73_cross_gate_decision_frontier_authority.json"
DECISIONS = ROOT / "10_compliance" / "drafts" / "COMPLIANCE_OPEN_DECISIONS.json"
QUESTIONNAIRE = ROOT / "10_compliance" / "review" / "STAGE74_CONTROLLER_PROCESSOR_REVIEW_QUESTIONNAIRE.md"
INPUT_TEMPLATE = ROOT / "10_compliance" / "review" / "STAGE74_INDEPENDENT_REVIEW_INPUT_TEMPLATE.json"
BUILDER = BACKEND / "tools" / "build_stage74_controller_processor_review_packet.py"
COLLECTOR = BACKEND / "tools" / "collect_stage74_independent_review_candidate.py"
WORKFLOW = ROOT / ".github" / "workflows" / "stage74_controller_processor_independent_review_intake.yml"
FAILURE_CLASS = "BGF-STAGE74-INDEPENDENT-REVIEW-INTAKE-GUARD-715"
EXPECTED_STAGE73_BLOB = "6ef6cce7e3be3b51fe53ad99c9367b7cada43f14"
EXPECTED_DECISIONS_BLOB = "215d527c1cb79d7b72697f03f1f84887e3a72d95"
EXPECTED_AFFECTED_GATES = {
    "legal_privacy_notice",
    "legal_role_mapping",
    "data_subject_request_channel",
    "incident_response",
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
    "deploy-pages",
    "actions/deploy-pages",
    "powershell",
)


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE74_INDEPENDENT_REVIEW_INTAKE_GUARD=FAIL\n"
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


def verify_authority() -> tuple[dict, dict, dict]:
    authority = load(AUTHORITY)
    stage73 = load(STAGE73)
    decisions = load(DECISIONS)

    if authority.get("schema_version") != 1 or authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("Stage74 authority identity drift")
    if authority.get("stage") != "STAGE74_CONTROLLER_PROCESSOR_INDEPENDENT_REVIEW_INTAKE":
        fail("Stage74 authority stage drift")
    if authority.get("baseline_main_sha") != "5ac1ded742eb71d9e9b124a8c878473e70d3dbbc":
        fail("Stage74 baseline main SHA drift")

    upstream = authority.get("upstream_authority")
    if not isinstance(upstream, dict):
        fail("Stage74 upstream authority missing")
    if upstream.get("stage73_decision_frontier_blob") != EXPECTED_STAGE73_BLOB:
        fail("Stage73 authority blob pin drift")
    if upstream.get("stage67_open_decisions_blob") != EXPECTED_DECISIONS_BLOB:
        fail("Stage67 open-decisions blob pin drift")

    scope = authority.get("review_scope")
    if not isinstance(scope, dict):
        fail("Stage74 review scope missing")
    if scope.get("decision_id") != "CONTROLLER_PROCESSOR_ROLE_MATRIX" or scope.get("fanout_count") != 4:
        fail("Stage74 target decision/fanout drift")
    if set(scope.get("affected_external_gates", [])) != EXPECTED_AFFECTED_GATES:
        fail("Stage74 affected gate set drift")
    if scope.get("resolution_authority") != "independent legal/privacy review":
        fail("Stage74 resolution authority drift")

    contract = authority.get("review_contract")
    if not isinstance(contract, dict):
        fail("Stage74 review contract missing")
    must_true = (
        "candidate_sources_remain_draft",
        "real_independent_reviewer_reference_required_for_review_candidate",
        "real_review_artifact_required_for_review_candidate",
        "exact_candidate_source_digests_must_match_review_input",
        "review_input_completed_copy_must_remain_outside_repo",
        "committed_placeholder_review_input_must_fail",
        "test_fixture_review_input_must_fail",
        "review_outcome_may_be_recorded_only_from_real_external_input",
        "review_candidate_requires_canonical_gate_review_afterward",
        "reviewer_reference_sha256_allowed",
        "review_artifact_sha256_allowed",
    )
    for key in must_true:
        if contract.get(key) is not True:
            fail(f"Stage74 review contract must keep {key}=true")
    must_false = (
        "candidate_sources_can_be_promoted_by_packet",
        "review_outcome_automatically_changes_candidate_documents",
        "review_outcome_automatically_closes_open_decision",
        "review_outcome_is_gate_evidence",
        "reviewer_identity_copied_to_candidate_output",
        "review_artifact_path_copied_to_candidate_output",
        "network_calls_allowed",
        "provider_calls_allowed",
        "supabase_mutation_allowed",
        "deployment_action_allowed",
        "evidence_ref_creation_allowed",
        "evidence_digest_promotion_allowed",
        "evidence_migration_creation_allowed",
        "gate_promotion_allowed",
        "controlled_launch_promotion_allowed",
        "paid_media_promotion_allowed",
    )
    for key in must_false:
        if contract.get(key) is not False:
            fail(f"Stage74 review contract must keep {key}=false")

    outcomes = authority.get("outcome_contract", {})
    if outcomes.get("allowed_real_review_outcomes") != [
        "APPROVED_WITHOUT_CHANGES",
        "APPROVED_WITH_REQUIRED_CHANGES",
        "NOT_APPROVED_REQUIRES_REVISION",
    ]:
        fail("Stage74 allowed review outcomes drift")
    for key in (
        "approved_without_changes_still_does_not_close_any_gate",
        "approved_with_required_changes_requires_new_candidate_bytes_and_new_review",
        "not_approved_requires_revision_and_new_review",
        "document_approval_version_or_effective_date_is_not_created_by_stage74",
    ):
        if outcomes.get(key) is not True:
            fail(f"Stage74 outcome boundary drift: {key}")

    remote = authority.get("fresh_remote_read_only_receipt")
    if not isinstance(remote, dict):
        fail("Stage74 fresh remote receipt missing")
    if remote.get("auth_users") != 0 or remote.get("organizations") != 0 or remote.get("students") != 0:
        fail("Stage74 remote empty-customer baseline drift")
    if remote.get("asaas_state") != "selected_pending_credentials" or remote.get("asaas_activated_at") is not None:
        fail("Stage74 remote Asaas boundary drift")
    if remote.get("remote_mutation_performed") is not False:
        fail("Stage74 remote receipt must state no mutation")

    if stage73.get("frontier_contract", {}).get("top_shared_decision_expected") != "CONTROLLER_PROCESSOR_ROLE_MATRIX":
        fail("Stage73 top frontier decision drift")
    if stage73.get("frontier_contract", {}).get("top_shared_decision_expected_fanout") != 4:
        fail("Stage73 top frontier fanout drift")

    return authority, stage73, decisions


def verify_target_decision(decisions: dict) -> None:
    if decisions.get("status") != "DRAFT_UNREVIEWED_NOT_EVIDENCE":
        fail("Stage67 decision registry status drift")
    unresolved = decisions.get("unresolved")
    if not isinstance(unresolved, list):
        fail("Stage67 unresolved decisions missing")
    target = next((item for item in unresolved if isinstance(item, dict) and item.get("id") == "CONTROLLER_PROCESSOR_ROLE_MATRIX"), None)
    if not isinstance(target, dict):
        fail("target controller/processor decision missing")
    if target.get("state") != "OPEN":
        fail("target controller/processor decision must remain OPEN")
    if set(target.get("applies_to", [])) != EXPECTED_AFFECTED_GATES:
        fail("target decision applies_to drift")
    if target.get("resolution_authority") != "independent legal/privacy review":
        fail("target decision resolution authority drift")


def verify_questionnaire() -> None:
    try:
        text = QUESTIONNAIRE.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"questionnaire unreadable: {type(exc).__name__}")
    required = (
        "NON_ATTESTING_REVIEW_INTAKE_QUESTIONNAIRE_NOT_LEGAL_EVIDENCE",
        "CONTROLLER_PROCESSOR_ROLE_MATRIX",
        "legal_privacy_notice",
        "legal_role_mapping",
        "data_subject_request_channel",
        "incident_response",
        "APPROVED_WITHOUT_CHANGES",
        "APPROVED_WITH_REQUIRED_CHANGES",
        "NOT_APPROVED_REQUIRES_REVISION",
        "não fecha automaticamente nenhum gate",
    )
    for marker in required:
        if marker not in text:
            fail(f"questionnaire missing required boundary marker: {marker}")


def verify_template() -> None:
    template = load(INPUT_TEMPLATE)
    if template.get("schema_version") != 1:
        fail("review input template schema drift")
    if template.get("input_kind") != "REAL_INDEPENDENT_CONTROLLER_PROCESSOR_REVIEW_INPUT":
        fail("review input template kind drift")
    if template.get("status") != "PLACEHOLDER_TEMPLATE_NOT_REAL_REVIEW":
        fail("review input template status drift")
    if template.get("test_fixture") is not True or template.get("contains_placeholders") is not True:
        fail("committed review input template must remain an invalid fixture")
    if template.get("decision_id") != "CONTROLLER_PROCESSOR_ROLE_MATRIX":
        fail("review input template decision drift")
    for key in (
        "independent_review_confirmed",
        "reviewer_acknowledged_exact_source_digests",
        "review_artifact_secret_values_absent_or_redacted_confirmed",
    ):
        if template.get(key) is not False:
            fail(f"committed review template must not attest {key}")
    source_digests = template.get("reviewed_source_sha256")
    if not isinstance(source_digests, dict) or set(source_digests) != {
        "privacy_notice",
        "processing_role_matrix",
        "dsr_runbook",
        "incident_runbook",
        "open_decisions",
    }:
        fail("review template source digest key set drift")


def verify_candidate_source_statuses(authority: dict) -> None:
    paths = authority.get("candidate_sources")
    expected = {
        "10_compliance/drafts/PRIVACY_NOTICE_CANDIDATE_PTBR.md": "DRAFT_UNREVIEWED_NOT_PUBLISHED_NOT_LEGAL_EVIDENCE",
        "10_compliance/drafts/PROCESSING_ROLE_MATRIX_CANDIDATE.md": "DRAFT_UNREVIEWED_NOT_LEGAL_EVIDENCE",
        "10_compliance/drafts/DATA_SUBJECT_REQUEST_RUNBOOK_CANDIDATE.md": "DRAFT_UNREVIEWED_NOT_OPERATIONAL_EVIDENCE",
        "10_compliance/drafts/INCIDENT_RESPONSE_RUNBOOK_CANDIDATE.md": "DRAFT_UNREVIEWED_NOT_OPERATIONAL_EVIDENCE",
        "10_compliance/drafts/COMPLIANCE_OPEN_DECISIONS.json": "DRAFT_UNREVIEWED_NOT_EVIDENCE",
    }
    if not isinstance(paths, list) or set(paths) != set(expected):
        fail("Stage74 candidate source inventory drift")
    for raw, marker in expected.items():
        path = ROOT / raw
        if raw.endswith(".json"):
            if load(path).get("status") != marker:
                fail(f"candidate JSON source status drift: {raw}")
        else:
            if marker not in path.read_text(encoding="utf-8"):
                fail(f"candidate document source status drift: {raw}")


def verify_python_source(path: Path, label: str, required_markers: tuple[str, ...]) -> None:
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (OSError, SyntaxError) as exc:
        fail(f"{label} unreadable or invalid Python: {type(exc).__name__}")
    for node in ast.walk(tree):
        roots: list[str] = []
        if isinstance(node, ast.Import):
            roots.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.append(node.module.split(".")[0])
        for root in roots:
            if root in FORBIDDEN_IMPORT_ROOTS:
                fail(f"{label} imports forbidden network/remote module: {root}")
    for marker in required_markers:
        if marker not in source:
            fail(f"{label} missing required marker: {marker}")


def verify_sources() -> None:
    verify_python_source(
        BUILDER,
        "builder",
        (
            "NON_ATTESTING_INDEPENDENT_REVIEW_INTAKE_PACKET",
            "EXACT_DRAFT_BYTES_BOUND_FOR_EXTERNAL_REVIEW_NO_REVIEW_PERFORMED_NOT_EVIDENCE",
            "REAL_EXTERNAL_INDEPENDENT_REVIEW_OF_EXACT_BOUND_BYTES_REQUIRED",
            "CONTROLLER_PROCESSOR_ROLE_MATRIX",
        ),
    )
    verify_python_source(
        COLLECTOR,
        "collector",
        (
            "DIGEST_ONLY_INDEPENDENT_REVIEW_CANDIDATE",
            "REAL_REVIEW_DIGEST_BOUND_AWAITING_CANONICAL_GATE_REVIEW_NOT_GATE_EVIDENCE",
            "APPROVED_WITHOUT_CHANGES",
            "APPROVED_WITH_REQUIRED_CHANGES",
            "NOT_APPROVED_REQUIRES_REVISION",
            "reviewer_reference_sha256",
            "OPEN_DECISION_CLOSED=false",
            "GATE_READY=false",
        ),
    )


def verify_workflow() -> None:
    try:
        text = WORKFLOW.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"workflow unreadable: {type(exc).__name__}")
    lowered = text.lower()
    for token in FORBIDDEN_WORKFLOW_TOKENS:
        if token in lowered:
            fail(f"workflow contains forbidden token/action: {token}")
    required = (
        "permissions:\n  contents: read",
        "Checkout exact head",
        "Verify Stage74 review intake contract",
        "Build deterministic review packet twice",
        "cmp",
        "Prove committed placeholder review input is refused",
        "PLACEHOLDER_REVIEW_INPUT_REFUSED=PASS",
        "Upload non-attesting review packet",
        "retention-days: 7",
        "REAL_REVIEW=false",
        "CANDIDATE_DOCUMENT_PROMOTION=false",
        "GATE_PROMOTION=false",
        "CONTROLLED_LAUNCH=DENIED",
        "REMOTE_MUTATION=false",
    )
    for marker in required:
        if marker not in text:
            fail(f"workflow missing required marker: {marker}")


def verify_no_stage74_migration() -> None:
    roots = [BACKEND / "migrations", BACKEND / "supabase" / "migrations"]
    matches = []
    for root in roots:
        if root.exists():
            matches.extend(root.glob("*stage74*"))
    if matches:
        fail("Stage74 must not create a Supabase migration")


def main() -> None:
    authority, _stage73, decisions = verify_authority()
    verify_target_decision(decisions)
    verify_questionnaire()
    verify_template()
    verify_candidate_source_statuses(authority)
    verify_sources()
    verify_workflow()
    verify_no_stage74_migration()

    print("STAGE74_INDEPENDENT_REVIEW_INTAKE_GUARD=PASS")
    print("DECISION=CONTROLLER_PROCESSOR_ROLE_MATRIX")
    print("AFFECTED_GATES=4")
    print("REAL_REVIEW=false")
    print("CANDIDATE_DOCUMENT_PROMOTION=false")
    print("OPEN_DECISION_CLOSED=false")
    print("GATE_PROMOTION=false")
    print("REMOTE_MUTATION=false")


if __name__ == "__main__":
    main()
