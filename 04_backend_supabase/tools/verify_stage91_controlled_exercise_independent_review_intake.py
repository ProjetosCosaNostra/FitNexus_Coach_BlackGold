from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
REHEARSALS = ROOT / "10_compliance" / "rehearsals"
AUTHORITY = BACKEND / "stage91_controlled_exercise_independent_review_intake_authority.json"
STAGE69 = BACKEND / "stage69_controlled_exercise_execution_boundary_authority.json"
STAGE68 = BACKEND / "stage68_synthetic_governance_rehearsal_compiler_authority.json"
STAGE44 = BACKEND / "stage44_data_subject_request_external_evidence_preparation_authority.json"
STAGE45 = BACKEND / "stage45_incident_response_external_evidence_preparation_authority.json"
SCENARIOS = REHEARSALS / "STAGE68_SYNTHETIC_REHEARSAL_SCENARIOS.json"
OWNER_TEMPLATE = REHEARSALS / "STAGE69_REAL_OWNER_ASSIGNMENT_INPUT_TEMPLATE.json"
CONTRACT = REHEARSALS / "STAGE91_CONTROLLED_EXERCISE_INDEPENDENT_REVIEW_INTAKE_CONTRACT.json"
INPUT_TEMPLATE = REHEARSALS / "STAGE91_REAL_CONTROLLED_EXERCISE_REVIEW_INPUT_TEMPLATE.json"
COLLECTOR = BACKEND / "tools" / "collect_stage91_controlled_exercise_independent_review.py"
WORKFLOW = ROOT / ".github" / "workflows" / "stage91_controlled_exercise_independent_review_intake.yml"
FAILURE = "BGF-STAGE91-CONTROLLED-EXERCISE-INDEPENDENT-REVIEW-INTAKE-GUARD-901"
FORBIDDEN_IMPORTS = {"os", "subprocess", "socket", "urllib", "http", "requests", "psycopg", "supabase"}
FORBIDDEN_WORKFLOW = (
    "apply_migration", "execute_sql", "supabase db", "service_role", "supabase_access_token",
    "database_url", "curl ", "wget ", "workflow_dispatch", "schedule:", "deploy-pages",
)
EXPECTED_DSR = [
    "DSR_ACCESS_EXPORT_SAME_TENANT",
    "DSR_CROSS_TENANT_REQUEST_FAIL_CLOSED",
    "DSR_CORRECTION_AUDITED",
    "DSR_DELETION_WITH_RETENTION_HOLD",
    "DSR_INSUFFICIENT_IDENTITY_PAUSE",
]
EXPECTED_INCIDENT = [
    "INCIDENT_CROSS_TENANT_EXPOSURE",
    "INCIDENT_CREDENTIAL_COMPROMISE",
    "INCIDENT_POTENTIALLY_SENSITIVE_STUDENT_DATA",
]


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE91_CONTROLLED_EXERCISE_INDEPENDENT_REVIEW_INTAKE_GUARD=FAIL\n"
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
    stage69 = load(STAGE69)
    stage68 = load(STAGE68)
    stage44 = load(STAGE44)
    stage45 = load(STAGE45)
    scenarios = load(SCENARIOS)
    owner_template = load(OWNER_TEMPLATE)
    contract = load(CONTRACT)
    input_template = load(INPUT_TEMPLATE)

    expect(authority, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE91_CONTROLLED_EXERCISE_INDEPENDENT_REVIEW_INTAKE",
        "baseline_main_sha": "3940e7d7b28a8f14be0912ce17edc61bf0073a87",
        "current_state": "DIGEST_ONLY_CONTROLLED_EXERCISE_INDEPENDENT_REVIEW_INTAKE_PREPARED_NO_REAL_INPUT_NO_EXERCISE_EXECUTION_NO_REVIEW_ATTESTATION_NO_GATE_PROMOTION",
    }, "Stage91 authority")

    upstream = authority.get("upstream_boundaries", {})
    for key, path, expected_blob in (
        ("stage69_execution_boundary_blob", STAGE69, "3c139c652eea102ae7ac84b274eb60bf01539d3d"),
        ("stage68_rehearsal_compiler_blob", STAGE68, "45459541f7e8516258f3cabcba4dd46cd45d256f"),
        ("stage44_dsr_preparation_blob", STAGE44, "53321a9af19ba3423fca44191bf000815eb617d5"),
        ("stage45_incident_preparation_blob", STAGE45, "d5d32990e8ef7a3c4f13dc63e2088ea28e471f12"),
    ):
        if upstream.get(key) != expected_blob or blob(path) != expected_blob:
            fail(f"upstream boundary blob drift:{key}")
    if upstream.get("terms_path_external_review_required") is not True:
        fail("Stage91 must preserve Stage90 external Terms review boundary")
    if stage69.get("next_after_green", {}).get("safe_internal_work", "").find("independent-review intake") < 0:
        fail("Stage69 next-safe-work authority no longer points to independent-review intake")
    if stage68.get("compiler_contract", {}).get("stage68_packet_count_required") is not None:
        fail("unexpected Stage68 authority shape")
    if stage68.get("compiler_contract", {}).get("dsr_scenario_count") != 5 or stage68.get("compiler_contract", {}).get("incident_scenario_count") != 3:
        fail("Stage68 scenario counts drift")
    if stage44.get("independent_review_boundary", {}).get("receipt_is_candidate_only") is not True:
        fail("Stage44 independent review boundary drift")
    if stage45.get("independent_review_boundary", {}).get("receipt_is_candidate_only") is not True:
        fail("Stage45 independent review boundary drift")

    pins = authority.get("sealed_inputs", {})
    for key, path, expected_blob in (
        ("stage68_scenario_registry_blob", SCENARIOS, "c3960d3410e6bf12b7336b71ce1cedfd0f2670e6"),
        ("stage69_owner_template_blob", OWNER_TEMPLATE, "78284ac6cd6479dab901278ecd95e71f5b7a79cd"),
        ("stage91_intake_contract_blob", CONTRACT, "80785cc36f1f718fb171a8d3af9d9fb78fadff78"),
        ("stage91_input_template_blob", INPUT_TEMPLATE, "6bfb8f80a16622c7263ac41d7c86590bddcd860e"),
        ("stage91_collector_blob", COLLECTOR, "ec83e38c552f0967ffcd4eb974a3ff34bdcec9c3"),
    ):
        if pins.get(key) != expected_blob or blob(path) != expected_blob:
            fail(f"sealed input blob drift:{key}")

    if scenarios.get("stage") != "STAGE68_SYNTHETIC_GOVERNANCE_REHEARSAL_COMPILER":
        fail("Stage68 scenario registry identity drift")
    dsr_rows = scenarios.get("dsr_scenarios")
    incident_rows = scenarios.get("incident_scenarios")
    if not isinstance(dsr_rows, list) or not isinstance(incident_rows, list):
        fail("Stage68 scenario arrays missing")
    dsr_ids = [row.get("scenario_id") for row in dsr_rows if isinstance(row, dict)]
    incident_ids = [row.get("scenario_id") for row in incident_rows if isinstance(row, dict)]
    if dsr_ids != EXPECTED_DSR or incident_ids != EXPECTED_INCIDENT:
        fail("Stage68 exact scenario ID registry drift")

    binding = authority.get("scenario_registry_binding", {})
    expect(binding, {
        "dsr_scenario_count": 5,
        "incident_scenario_count": 3,
        "total_scenario_count": 8,
        "dsr_ids": EXPECTED_DSR,
        "incident_ids": EXPECTED_INCIDENT,
        "collector_must_match_registry_exactly": True,
    }, "scenario registry binding")

    collector_source = COLLECTOR.read_text(encoding="utf-8")
    for scenario_id in EXPECTED_DSR + EXPECTED_INCIDENT:
        if f'"{scenario_id}"' not in collector_source:
            fail(f"collector missing exact Stage68 scenario ID:{scenario_id}")
    for stale_id in (
        "DSR_CROSS_TENANT_FAIL_CLOSED",
        "DSR_AUDITED_CORRECTION",
        "DSR_DELETION_RETENTION_HANDOFF",
        "DSR_IDENTITY_INSUFFICIENT_PAUSE",
        "INCIDENT_SENSITIVE_STUDENT_DATA",
    ):
        if f'"{stale_id}"' in collector_source:
            fail(f"collector retained stale inferred scenario ID:{stale_id}")

    if owner_template.get("test_fixture") is not True or owner_template.get("contains_placeholders") is not True:
        fail("Stage69 committed owner template must remain a rejected placeholder")
    if input_template.get("input_kind") != "REAL_CONTROLLED_EXERCISE_REVIEW_INPUT":
        fail("Stage91 input template identity drift")
    if input_template.get("test_fixture") is not True or input_template.get("contains_placeholders") is not True:
        fail("Stage91 committed intake template must remain a rejected placeholder")
    if "PLACEHOLDER" not in str(input_template.get("status", "")).upper():
        fail("Stage91 input template lost placeholder status")

    if contract.get("stage") != "STAGE91_CONTROLLED_EXERCISE_INDEPENDENT_REVIEW_INTAKE":
        fail("Stage91 contract identity drift")
    if contract.get("current_main_baseline") != "3940e7d7b28a8f14be0912ce17edc61bf0073a87":
        fail("Stage91 contract main baseline drift")
    required_inputs = contract.get("required_external_inputs", {})
    if set(required_inputs) != {
        "stage69_session_candidate", "completed_exercise_record",
        "independent_review_record", "reviewer_assignment_or_authority_artifact",
    } or any(row.get("required") is not True for row in required_inputs.values() if isinstance(row, dict)):
        fail("Stage91 external input contract drift")
    digest = contract.get("digest_only_output_contract", {})
    for key in (
        "owner_names_copied", "reviewer_name_copied", "artifact_paths_copied",
        "artifact_filenames_copied", "raw_artifact_content_copied",
    ):
        if digest.get(key) is not False:
            fail(f"Stage91 digest-only privacy boundary drift:{key}")
    for key in (
        "stage69_session_sha256_recorded", "completed_exercise_record_sha256_recorded",
        "independent_review_record_sha256_recorded", "reviewer_authority_artifact_sha256_recorded",
        "coverage_boolean_summary_recorded", "unresolved_findings_count_recorded",
    ):
        if digest.get(key) is not True:
            fail(f"Stage91 digest output requirement drift:{key}")

    boundary = authority.get("intake_boundary", {})
    true_keys = (
        "real_stage69_session_required", "real_completed_human_exercise_record_required",
        "real_independent_review_record_required", "real_reviewer_authority_artifact_required",
        "committed_placeholder_input_must_fail", "test_fixture_input_must_fail",
        "exercise_executed_false_must_fail", "independent_review_completed_false_must_fail",
        "real_customer_data_true_must_fail", "production_secrets_true_must_fail",
        "collector_output_digest_only",
    )
    false_keys = (
        "owner_identity_copied", "reviewer_identity_copied", "artifact_path_or_filename_copied",
        "raw_artifact_content_copied", "network_calls_allowed", "supabase_mutation_allowed",
        "provider_calls_allowed", "stage44_evidence_attestation_allowed",
        "stage45_evidence_attestation_allowed", "evidence_ref_creation_allowed",
        "evidence_digest_promotion_allowed", "evidence_migration_creation_allowed",
        "gate_promotion_allowed",
    )
    for key in true_keys:
        if boundary.get(key) is not True:
            fail(f"Stage91 required fail-closed boundary drift:{key}")
    for key in false_keys:
        if boundary.get(key) is not False:
            fail(f"Stage91 forbidden boundary drift:{key}")

    ci = authority.get("ci_semantics", {})
    if ci.get("ci_uses_only_committed_placeholder_input") is not True or ci.get("ci_must_prove_placeholder_rejected") is not True:
        fail("Stage91 CI placeholder-negative-proof contract drift")
    for key in (
        "ci_exercise_executed", "ci_independent_review_attested", "ci_stage44_evidence_attested",
        "ci_stage45_evidence_attested", "ci_gate_ready", "ci_supabase_mutation",
    ):
        if ci.get(key) is not False:
            fail(f"Stage91 CI non-attesting boundary drift:{key}")

    try:
        tree = ast.parse(collector_source)
    except SyntaxError as exc:
        fail(f"collector syntax invalid:{exc.msg}")
    for node in ast.walk(tree):
        roots: list[str] = []
        if isinstance(node, ast.Import):
            roots += [item.name.split('.')[0] for item in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.append(node.module.split('.')[0])
        if any(root in FORBIDDEN_IMPORTS for root in roots):
            fail("Stage91 collector imports remote or side-effect module")

    workflow = WORKFLOW.read_text(encoding="utf-8")
    low = workflow.lower()
    for token in FORBIDDEN_WORKFLOW:
        if token in low:
            fail(f"Stage91 workflow contains forbidden side-effect token:{token}")
    for marker in (
        "permissions:\n  contents: read",
        "blackgold/stage91-controlled-exercise-independent-review-intake",
        "Verify Stage91 controlled exercise independent review intake",
        "Prove committed Stage91 placeholder intake is refused",
        "REAL_OWNER_ASSIGNMENTS_REQUIRED=true",
        "HUMAN_EXERCISE_EXECUTION_REQUIRED=true",
        "INDEPENDENT_REVIEW_REQUIRED=true",
        "CI_EXERCISE_EXECUTED=false",
        "CI_INDEPENDENT_REVIEW_ATTESTED=false",
        "STAGE44_EVIDENCE=false",
        "STAGE45_EVIDENCE=false",
        "SUPABASE_MUTATION=false",
        "DSR_GATE_READY=false",
        "INCIDENT_RESPONSE_GATE_READY=false",
    ):
        if marker not in workflow:
            fail(f"Stage91 workflow marker missing:{marker}")

    gates = authority.get("gates", {})
    if gates.get("data_subject_request_channel", "").startswith("DENIED") is not True:
        fail("DSR gate must remain denied")
    if gates.get("incident_response", "").startswith("DENIED") is not True:
        fail("incident response gate must remain denied")
    if gates.get("controlled_launch") != "DENIED" or gates.get("paid_media") != "DENIED":
        fail("launch gates must remain denied")
    if authority.get("next_after_green", {}).get("evidence_migration_allowed") is not False:
        fail("Stage91 cannot authorize an evidence migration")

    print("STAGE91_CONTROLLED_EXERCISE_INDEPENDENT_REVIEW_INTAKE_GUARD=PASS")
    print("SCENARIO_REGISTRY_BINDING=8_EXACT")
    print("COMMITTED_PLACEHOLDER_INPUT_REQUIRED_TO_FAIL=true")
    print("REAL_OWNER_ASSIGNMENTS_REQUIRED=true")
    print("HUMAN_EXERCISE_EXECUTION_REQUIRED=true")
    print("INDEPENDENT_REVIEW_REQUIRED=true")
    print("CI_EXERCISE_EXECUTED=false")
    print("CI_INDEPENDENT_REVIEW_ATTESTED=false")
    print("STAGE44_EVIDENCE=false")
    print("STAGE45_EVIDENCE=false")
    print("GATE_READY=false")


if __name__ == "__main__":
    main()
