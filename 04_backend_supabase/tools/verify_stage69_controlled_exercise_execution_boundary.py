from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage69_controlled_exercise_execution_boundary_authority.json"
STAGE68 = BACKEND / "stage68_synthetic_governance_rehearsal_compiler_authority.json"
RUNNER = BACKEND / "tools" / "prepare_stage69_controlled_exercise_session.py"
TEMPLATE = ROOT / "10_compliance" / "rehearsals" / "STAGE69_REAL_OWNER_ASSIGNMENT_INPUT_TEMPLATE.json"
WORKFLOW = ROOT / ".github" / "workflows" / "stage69_controlled_exercise_execution_boundary.yml"

BASELINE_MAIN = "06e912fbb12be5bdc61b3aeb1119ff64a7b7c185"
STAGE68_BLOB = "45459541f7e8516258f3cabcba4dd46cd45d256f"
RUNNER_BLOB = "334703a187a4ac54d309b042061b1a9317134fd8"
TEMPLATE_BLOB = "78284ac6cd6479dab901278ecd95e71f5b7a79cd"
FAILURE_CLASS = "BGF-STAGE69-CONTROLLED-EXERCISE-BOUNDARY-GUARD-665"


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE69_CONTROLLED_EXERCISE_EXECUTION_BOUNDARY=FAIL\n"
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
    stage68 = load(STAGE68)
    template = load(TEMPLATE)

    if git_blob(STAGE68) != STAGE68_BLOB:
        fail("Stage68 authority blob drift")
    if git_blob(RUNNER) != RUNNER_BLOB:
        fail("Stage69 preparer blob drift")
    if git_blob(TEMPLATE) != TEMPLATE_BLOB:
        fail("Stage69 owner template blob drift")

    require(
        authority,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "stage": "STAGE69_CONTROLLED_EXERCISE_EXECUTION_BOUNDARY",
            "baseline_main_sha": BASELINE_MAIN,
            "current_state": "REAL_OWNER_ASSIGNMENT_GATED_EXERCISE_SESSION_PREPARATION_BOUNDARY_NO_EXECUTION_NO_EVIDENCE_NO_GATE_PROMOTION",
        },
        "Stage69 authority",
    )
    require(
        stage68,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "stage": "STAGE68_SYNTHETIC_GOVERNANCE_REHEARSAL_COMPILER",
            "current_state": "DETERMINISTIC_SYNTHETIC_DSR_AND_INCIDENT_REHEARSAL_PACKETS_PREPARED_NOT_EXECUTED_NOT_EVIDENCE_NO_GATE_PROMOTION",
        },
        "Stage68 authority",
    )

    remote = authority.get("fresh_remote_read_only_receipt", {})
    require(
        remote,
        {
            "source": "Supabase.execute_sql_read_only",
            "observed_at_utc": "2026-08-25T17:51:22.747635+00:00",
            "auth_users": 0,
            "organizations": 0,
            "students": 0,
            "asaas_state": "selected_pending_credentials",
            "asaas_activated_at": None,
            "ready_evidence_migration_count": 0,
            "remote_mutation_performed": False,
        },
        "remote receipt",
    )

    contract = authority.get("execution_boundary_contract", {})
    required_false = (
        "owner_name_copied_to_output",
        "owner_artifact_path_copied_to_output",
        "exercise_execution_performed_by_preparer",
        "candidate_receipt_is_operational_evidence",
        "candidate_receipt_is_stage44_evidence",
        "candidate_receipt_is_stage45_evidence",
        "network_calls_allowed",
        "supabase_mutation_allowed",
        "provider_calls_allowed",
        "real_customer_data_allowed",
        "secret_values_allowed",
        "production_identifiers_allowed",
        "legal_review_attestation_allowed",
        "operational_sufficiency_attestation_allowed",
        "evidence_ref_creation_allowed",
        "evidence_digest_promotion_allowed",
        "evidence_migration_creation_allowed",
        "gate_promotion_allowed",
        "controlled_launch_promotion_allowed",
        "paid_media_promotion_allowed",
    )
    for key in required_false:
        if contract.get(key) is not False:
            fail(f"execution boundary must remain false: {key}")
    for key in (
        "owner_input_must_be_external_not_committed",
        "placeholder_owner_input_must_fail",
        "test_fixture_owner_input_must_fail",
        "real_assignment_artifact_required_per_role",
        "assignment_artifact_sha256_only_in_output",
        "stage68_bundle_required",
    ):
        if contract.get(key) is not True:
            fail(f"execution boundary must remain true: {key}")
    if contract.get("stage68_packet_count_required") != 8:
        fail("Stage68 packet count contract drift")

    roles = contract.get("required_real_roles")
    expected_roles = [
        "dsr_primary_owner",
        "dsr_backup_owner",
        "incident_commander",
        "privacy_owner",
        "technical_owner",
        "exercise_facilitator",
    ]
    if roles != expected_roles:
        fail("required real role list drift")

    require(
        template,
        {
            "schema_version": 1,
            "input_kind": "REAL_ASSIGNED_OWNER_INPUT",
            "status": "PLACEHOLDER_TEMPLATE_NOT_REAL_ASSIGNMENT",
            "test_fixture": True,
            "contains_placeholders": True,
        },
        "owner input template",
    )
    template_roles = template.get("roles")
    if not isinstance(template_roles, dict) or set(template_roles) != set(expected_roles):
        fail("owner input template role set drift")
    for role in expected_roles:
        entry = template_roles.get(role)
        if not isinstance(entry, dict):
            fail(f"template role missing: {role}")
        if entry.get("display_name") != "<REAL_NAME_REQUIRED>":
            fail(f"template role name must remain placeholder: {role}")
        if entry.get("assignment_artifact_path") != "<REAL_NONEMPTY_ASSIGNMENT_ARTIFACT_PATH_REQUIRED>":
            fail(f"template assignment artifact must remain placeholder: {role}")
        if entry.get("acknowledged") is not False:
            fail(f"template acknowledgment must remain false: {role}")

    runner_text = RUNNER.read_text(encoding="utf-8")
    try:
        tree = ast.parse(runner_text)
    except SyntaxError as exc:
        fail(f"Stage69 preparer syntax invalid: {exc.msg}")

    forbidden_import_roots = {"os", "subprocess", "socket", "urllib", "http", "requests", "supabase"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".", 1)[0] in forbidden_import_roots:
                    fail(f"preparer imports forbidden module: {alias.name}")
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module.split(".", 1)[0] in forbidden_import_roots:
                fail(f"preparer imports forbidden module: {node.module}")

    for forbidden in (
        "--allow-placeholder",
        "--skip-owner-validation",
        "execute_sql",
        "apply_migration",
        "curl ",
        "wget ",
        "git push",
        "actions/deploy-pages",
    ):
        if forbidden in runner_text.lower():
            fail(f"preparer contains forbidden bypass/remote fragment: {forbidden}")

    for fragment in (
        'owners.get("test_fixture") is not False',
        'owners.get("contains_placeholders") is not False',
        'entry.get("acknowledged") is not True',
        'artifact.stat().st_size <= 0',
        '"NON_ATTESTING_CONTROLLED_EXERCISE_SESSION_CANDIDATE"',
        '"READY_FOR_HUMAN_CONTROLLED_EXERCISE_NOT_EXECUTED_NOT_EVIDENCE"',
        '"owner_identity_copied_to_receipt": False',
        '"owner_artifact_path_copied_to_receipt": False',
        '"exercise_executed": False',
        '"stage44_evidence_attested": False',
        '"stage45_evidence_attested": False',
        '"evidence_migration_created": False',
        '"controlled_launch_promoted": False',
    ):
        if fragment not in runner_text:
            fail(f"preparer fail-closed invariant missing: {fragment}")

    workflow = WORKFLOW.read_text(encoding="utf-8")
    workflow_lower = workflow.lower()
    for fragment in (
        "permissions:\n  contents: read",
        "verify_stage69_controlled_exercise_execution_boundary.py",
        "build_stage68_synthetic_governance_rehearsal_bundle.py",
        "STAGE69_REAL_OWNER_ASSIGNMENT_INPUT_TEMPLATE.json",
        "prepare_stage69_controlled_exercise_session.py",
        "PLACEHOLDER_OWNER_INPUT_REFUSED=PASS",
        "test ! -e /tmp/stage69_session.json",
    ):
        if fragment not in workflow:
            fail(f"workflow invariant missing: {fragment}")
    for forbidden in (
        "actions/deploy-pages",
        "git push",
        "supabase db",
        "apply_migration",
        "execute_sql",
        "curl ",
        "wget ",
    ):
        if forbidden in workflow_lower:
            fail(f"workflow contains forbidden remote action: {forbidden}")

    gates = authority.get("gates", {})
    expected_denied = {
        "data_subject_request_channel": "DENIED_AWAITING_REAL_OPERATIONAL_AND_CONTROLLED_SYNTHETIC_EVIDENCE",
        "incident_response": "DENIED_AWAITING_REAL_GOVERNANCE_AND_CONTROLLED_TABLETOP_EVIDENCE",
        "legal_role_mapping": "DENIED_AWAITING_REAL_PROCESSING_ROLE_AND_LEGAL_BASIS_REVIEW_EVIDENCE",
        "legal_privacy_notice": "DENIED_AWAITING_REAL_PRIVACY_LEGAL_REVIEW_AND_STABLE_PUBLICATION_EVIDENCE",
        "legal_terms_of_use": "DENIED_AWAITING_REAL_LEGAL_REVIEW_AND_STABLE_PUBLICATION_EVIDENCE",
        "billing_provider_credentials": "DENIED_AWAITING_REAL_ASAAS_PRODUCTION_OPERATOR_EVIDENCE",
        "production_deployment": "DENIED_AWAITING_REAL_PRODUCTION_RELEASE_AND_OPERATIONS_EVIDENCE",
        "controlled_launch": "DENIED",
        "paid_media": "DENIED",
        "launch": "DENIED",
    }
    for key, value in expected_denied.items():
        if gates.get(key) != value:
            fail(f"gate boundary drift: {key}")

    if list((BACKEND / "migrations").glob("*stage69*.sql")):
        fail("Stage69 boundary must not create evidence migration")

    print("STAGE69_CONTROLLED_EXERCISE_EXECUTION_BOUNDARY=PASS")
    print("REAL_OWNER_ASSIGNMENT_REQUIRED=true")
    print("PLACEHOLDER_OWNER_INPUT_ALLOWED=false")
    print("TEST_FIXTURE_OWNER_INPUT_ALLOWED=false")
    print("EXERCISE_EXECUTED=false")
    print("STAGE44_EVIDENCE=false")
    print("STAGE45_EVIDENCE=false")
    print("REMOTE_MUTATION=false")
    print("CONTROLLED_LAUNCH=DENIED")


if __name__ == "__main__":
    main()
