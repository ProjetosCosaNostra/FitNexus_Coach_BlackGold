from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
DRAFTS = ROOT / "10_compliance" / "drafts"
REHEARSALS = ROOT / "10_compliance" / "rehearsals"
AUTHORITY = BACKEND / "stage68_synthetic_governance_rehearsal_compiler_authority.json"
STAGE44 = BACKEND / "stage44_data_subject_request_external_evidence_preparation_authority.json"
STAGE45 = BACKEND / "stage45_incident_response_external_evidence_preparation_authority.json"
STAGE67 = BACKEND / "stage67_compliance_operations_candidate_pack_authority.json"
SCENARIOS = REHEARSALS / "STAGE68_SYNTHETIC_REHEARSAL_SCENARIOS.json"
COMPILER = BACKEND / "tools" / "build_stage68_synthetic_governance_rehearsal_bundle.py"
WORKFLOW = ROOT / ".github" / "workflows" / "stage68_synthetic_governance_rehearsal_compiler.yml"
DSR_RUNBOOK = DRAFTS / "DATA_SUBJECT_REQUEST_RUNBOOK_CANDIDATE.md"
INCIDENT_RUNBOOK = DRAFTS / "INCIDENT_RESPONSE_RUNBOOK_CANDIDATE.md"
OPEN_DECISIONS = DRAFTS / "COMPLIANCE_OPEN_DECISIONS.json"

BASELINE_MAIN = "8f2868f13a75c115cb70ad78964d740572bb0668"
STAGE44_BLOB = "53321a9af19ba3423fca44191bf000815eb617d5"
STAGE45_BLOB = "d5d32990e8ef7a3c4f13dc63e2088ea28e471f12"
STAGE67_BLOB = "f383f49a6b56afc39fb2de34c5f7b07cb177cefc"
FAILURE_CLASS = "BGF-STAGE68-REHEARSAL-COMPILER-GUARD-655"


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE68_SYNTHETIC_GOVERNANCE_REHEARSAL_COMPILER=FAIL\n"
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


def git_blob(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def require(mapping: dict, expected: dict, label: str) -> None:
    if not isinstance(mapping, dict):
        fail(f"{label} must be object")
    for key, value in expected.items():
        if mapping.get(key) != value:
            fail(f"{label} drift: {key}")


def collect_strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            result.extend(collect_strings(item))
        return result
    if isinstance(value, dict):
        result = []
        for key, item in value.items():
            result.append(str(key))
            result.extend(collect_strings(item))
        return result
    return []


def validate_scenarios(registry: dict, stage44: dict, stage45: dict) -> None:
    require(
        registry,
        {
            "schema_version": 1,
            "stage": "STAGE68_SYNTHETIC_GOVERNANCE_REHEARSAL_COMPILER",
            "status": "SYNTHETIC_REHEARSAL_DEFINITIONS_ONLY_NOT_OPERATIONAL_EVIDENCE",
        },
        "scenario registry",
    )
    for key in (
        "real_customer_data_allowed",
        "network_calls_allowed",
        "supabase_mutation_allowed",
        "provider_calls_allowed",
        "secrets_allowed",
        "real_access_tokens_allowed",
        "production_identifiers_allowed",
        "gate_promotion_allowed",
    ):
        if registry.get("fixture_policy", {}).get(key) is not False:
            fail(f"fixture policy must remain false: {key}")

    dsr = registry.get("dsr_scenarios")
    incident = registry.get("incident_scenarios")
    if not isinstance(dsr, list) or len(dsr) != 5:
        fail("expected five DSR scenarios")
    if not isinstance(incident, list) or len(incident) != 3:
        fail("expected three incident scenarios")

    stage44_required = set(stage44.get("required_real_evidence", {}))
    stage45_required = set(stage45.get("required_real_evidence", {}))
    ids: set[str] = set()
    for kind, scenarios, alignment_key, allowed in (
        ("DSR", dsr, "stage44_requirement_alignment", stage44_required),
        ("INCIDENT", incident, "stage45_requirement_alignment", stage45_required),
    ):
        for scenario in scenarios:
            if not isinstance(scenario, dict):
                fail(f"{kind} scenario must be object")
            scenario_id = scenario.get("scenario_id")
            if not isinstance(scenario_id, str) or not scenario_id.startswith(kind + "_"):
                fail(f"invalid {kind} scenario id")
            if scenario_id in ids:
                fail(f"duplicate scenario id: {scenario_id}")
            ids.add(scenario_id)
            fixture = scenario.get("synthetic_fixture")
            if not isinstance(fixture, dict) or not fixture:
                fail(f"{scenario_id} fixture missing")
            strings = [s.lower() for s in collect_strings(fixture)]
            if any("@" in s for s in strings):
                fail(f"{scenario_id} fixture must not contain email-like identifiers")
            for forbidden in ("password", "access_token", "service_role", "api_key", "bearer ", "eyj"):
                if any(forbidden in s for s in strings):
                    fail(f"{scenario_id} contains forbidden secret/token marker: {forbidden}")
            for value in fixture.values():
                if isinstance(value, str) and not (
                    value.startswith("synthetic-")
                    or value.startswith("synthetic_")
                    or value.startswith("SYNTHETIC_")
                    or value.startswith("INSUFFICIENT_SYNTHETIC")
                    or value.startswith("HYPOTHETICAL_")
                ):
                    fail(f"{scenario_id} fixture string is not explicitly synthetic/hypothetical: {value}")
            assertions = scenario.get("required_assertions")
            if not isinstance(assertions, list) or "NON_CUSTOMER_FIXTURE_ONLY" not in assertions:
                fail(f"{scenario_id} must assert NON_CUSTOMER_FIXTURE_ONLY")
            alignment = scenario.get(alignment_key)
            if not isinstance(alignment, list) or not alignment:
                fail(f"{scenario_id} authority alignment missing")
            unknown = set(str(item) for item in alignment) - allowed
            if unknown:
                fail(f"{scenario_id} references unknown authority requirements: {sorted(unknown)}")

    required_incident_ids = {
        "INCIDENT_CROSS_TENANT_EXPOSURE",
        "INCIDENT_CREDENTIAL_COMPROMISE",
        "INCIDENT_POTENTIALLY_SENSITIVE_STUDENT_DATA",
    }
    if not required_incident_ids.issubset(ids):
        fail("Stage45 mandatory tabletop scenario coverage incomplete")
    if "DSR_CROSS_TENANT_REQUEST_FAIL_CLOSED" not in ids or "DSR_INSUFFICIENT_IDENTITY_PAUSE" not in ids:
        fail("critical DSR fail-closed scenario coverage incomplete")


def main() -> None:
    authority = load(AUTHORITY)
    stage44 = load(STAGE44)
    stage45 = load(STAGE45)
    stage67 = load(STAGE67)
    registry = load(SCENARIOS)
    open_decisions = load(OPEN_DECISIONS)

    if git_blob(STAGE44) != STAGE44_BLOB:
        fail("Stage44 sealed authority blob drift")
    if git_blob(STAGE45) != STAGE45_BLOB:
        fail("Stage45 sealed authority blob drift")
    if git_blob(STAGE67) != STAGE67_BLOB:
        fail("Stage67 candidate-pack authority blob drift")

    require(
        authority,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "stage": "STAGE68_SYNTHETIC_GOVERNANCE_REHEARSAL_COMPILER",
            "baseline_main_sha": BASELINE_MAIN,
            "current_state": "DETERMINISTIC_SYNTHETIC_DSR_AND_INCIDENT_REHEARSAL_PACKETS_PREPARED_NOT_EXECUTED_NOT_EVIDENCE_NO_GATE_PROMOTION",
        },
        "Stage68 authority",
    )
    if stage44.get("gates", {}).get("data_subject_request_channel") != "DENIED_AWAITING_REAL_OPERATIONAL_AND_CONTROLLED_SYNTHETIC_EVIDENCE":
        fail("Stage44 DSR denied boundary drift")
    if stage45.get("gates", {}).get("incident_response") != "DENIED_AWAITING_REAL_GOVERNANCE_AND_CONTROLLED_TABLETOP_EVIDENCE":
        fail("Stage45 incident denied boundary drift")
    if stage67.get("gates", {}).get("data_subject_request_channel") != "DENIED_AWAITING_REAL_OPERATIONAL_AND_CONTROLLED_SYNTHETIC_EVIDENCE":
        fail("Stage67 DSR denied boundary drift")
    if stage67.get("gates", {}).get("incident_response") != "DENIED_AWAITING_REAL_GOVERNANCE_AND_CONTROLLED_TABLETOP_EVIDENCE":
        fail("Stage67 incident denied boundary drift")
    if open_decisions.get("status") != "DRAFT_UNREVIEWED_NOT_EVIDENCE":
        fail("open decisions no longer unreviewed")
    if any(item.get("state") != "OPEN" for item in open_decisions.get("unresolved", []) if isinstance(item, dict)):
        fail("Stage67 open decisions were prematurely closed")

    for path, marker in (
        (DSR_RUNBOOK, "DRAFT_UNREVIEWED_NOT_OPERATIONAL_EVIDENCE"),
        (INCIDENT_RUNBOOK, "DRAFT_UNREVIEWED_NOT_OPERATIONAL_EVIDENCE"),
    ):
        text = path.read_text(encoding="utf-8")
        if marker not in text:
            fail(f"runbook lost candidate-only status: {path.relative_to(ROOT)}")

    validate_scenarios(registry, stage44, stage45)

    compiler_text = COMPILER.read_text(encoding="utf-8")
    try:
        tree = ast.parse(compiler_text)
    except SyntaxError as exc:
        fail(f"compiler syntax invalid: {exc.msg}")
    forbidden_import_roots = {"os", "subprocess", "socket", "urllib", "http", "requests", "psycopg", "supabase"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".", 1)[0] in forbidden_import_roots:
                    fail(f"compiler imports forbidden module: {alias.name}")
        if isinstance(node, ast.ImportFrom) and node.module and node.module.split(".", 1)[0] in forbidden_import_roots:
            fail(f"compiler imports forbidden module: {node.module}")

    for fragment in (
        "NON_ATTESTING_SYNTHETIC_GOVERNANCE_REHEARSAL_BUNDLE",
        "COMPILED_REHEARSAL_PACKETS_NOT_EXECUTED_NOT_OPERATIONAL_OR_LEGAL_EVIDENCE",
        "exercise_executed\": False",
        "real_customer_data_used\": False",
        "network_call_performed\": False",
        "supabase_mutation_performed\": False",
        "provider_call_performed\": False",
        "legal_review_attested\": False",
        "operational_review_attested\": False",
        "evidence_migration_created\": False",
        "data_subject_request_gate_ready_attested\": False",
        "incident_response_gate_ready_attested\": False",
        "REAL_CONTROLLED_REHEARSAL_EXECUTION_WITH_ASSIGNED_OWNERS_AND_INDEPENDENT_REVIEW_REQUIRED",
    ):
        if fragment not in compiler_text:
            fail(f"compiler non-attesting invariant missing: {fragment}")

    require(
        authority.get("compiler_contract", {}),
        {
            "dsr_scenario_count": 5,
            "incident_scenario_count": 3,
            "compiler_output_kind": "NON_ATTESTING_SYNTHETIC_GOVERNANCE_REHEARSAL_BUNDLE",
            "exact_source_sha_required": True,
            "deterministic_double_compile_required": True,
            "real_customer_data_allowed": False,
            "network_calls_allowed": False,
            "supabase_mutation_allowed": False,
            "provider_calls_allowed": False,
            "secrets_allowed": False,
            "production_identifiers_allowed": False,
            "actual_tabletop_execution_allowed_in_ci": False,
            "operational_owner_assignment_attestation_allowed": False,
            "legal_review_attestation_allowed": False,
            "stage44_receipt_claim_allowed": False,
            "stage45_receipt_claim_allowed": False,
            "evidence_ref_creation_allowed": False,
            "evidence_digest_creation_allowed": False,
            "evidence_migration_creation_allowed": False,
            "gate_promotion_allowed": False,
            "controlled_launch_promotion_allowed": False,
            "paid_media_promotion_allowed": False,
        },
        "compiler contract",
    )

    workflow = WORKFLOW.read_text(encoding="utf-8")
    lower = workflow.lower()
    for required in (
        "permissions:\n  contents: read",
        "verify_stage68_synthetic_governance_rehearsal_compiler.py",
        "build_stage68_synthetic_governance_rehearsal_bundle.py",
        "cmp \"$runner_temp/stage68/bundle_a.json\" \"$runner_temp/stage68/bundle_b.json\"",
        "actions/upload-artifact@v4",
        "retention-days: 7",
    ):
        if required not in workflow:
            fail(f"workflow invariant missing: {required}")
    for forbidden in (
        "actions/deploy-pages",
        "git push",
        "apply_migration",
        "execute_sql",
        "supabase db",
        "curl ",
        "wget ",
        "powershell",
    ):
        if forbidden in lower:
            fail(f"workflow contains forbidden remote/execution action: {forbidden}")

    if list((BACKEND / "migrations").glob("*stage68*.sql")):
        fail("Stage68 rehearsal compiler must not create migration")

    print("STAGE68_SYNTHETIC_GOVERNANCE_REHEARSAL_COMPILER=PASS")
    print("DSR_SCENARIOS=5")
    print("INCIDENT_SCENARIOS=3")
    print("ACTUAL_TABLETOP_EXECUTION=false")
    print("REAL_CUSTOMER_DATA=false")
    print("REMOTE_MUTATION=false")
    print("DSR_GATE=BLOCKED")
    print("INCIDENT_RESPONSE_GATE=BLOCKED")
    print("CONTROLLED_LAUNCH=DENIED")


if __name__ == "__main__":
    main()
