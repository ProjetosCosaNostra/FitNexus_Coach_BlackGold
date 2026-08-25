from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCENARIOS = ROOT / "10_compliance" / "rehearsals" / "STAGE68_SYNTHETIC_REHEARSAL_SCENARIOS.json"
DSR_RUNBOOK = ROOT / "10_compliance" / "drafts" / "DATA_SUBJECT_REQUEST_RUNBOOK_CANDIDATE.md"
INCIDENT_RUNBOOK = ROOT / "10_compliance" / "drafts" / "INCIDENT_RESPONSE_RUNBOOK_CANDIDATE.md"
OPEN_DECISIONS = ROOT / "10_compliance" / "drafts" / "COMPLIANCE_OPEN_DECISIONS.json"
STAGE44 = ROOT / "04_backend_supabase" / "stage44_data_subject_request_external_evidence_preparation_authority.json"
STAGE45 = ROOT / "04_backend_supabase" / "stage45_incident_response_external_evidence_preparation_authority.json"
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
FAILURE_CLASS = "BGF-STAGE68-REHEARSAL-COMPILER-GUARD-655"


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE68_SYNTHETIC_GOVERNANCE_REHEARSAL_BUNDLE=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\n"
        f"DETAIL={detail}"
    )


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to load {path.relative_to(ROOT)}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"expected JSON object: {path.relative_to(ROOT)}")
    return value


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_sha256(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256_bytes(encoded)


def compile_scenario(kind: str, scenario: dict, source_sha: str, runbook_sha256: str) -> dict:
    scenario_id = scenario.get("scenario_id")
    if not isinstance(scenario_id, str) or not scenario_id:
        fail(f"{kind} scenario missing scenario_id")
    fixture = scenario.get("synthetic_fixture")
    if not isinstance(fixture, dict):
        fail(f"{scenario_id} synthetic_fixture must be object")
    raw = json.dumps(fixture, sort_keys=True, ensure_ascii=False).lower()
    forbidden = ("password", "access_token", "service_role", "api_key", "real-customer", "real_customer")
    if any(token in raw for token in forbidden):
        fail(f"{scenario_id} contains a forbidden real-secret/customer marker")

    assertions = scenario.get("required_assertions")
    steps = scenario.get("exercise_steps")
    alignment_key = "stage44_requirement_alignment" if kind == "dsr" else "stage45_requirement_alignment"
    alignment = scenario.get(alignment_key)
    if not isinstance(assertions, list) or not assertions:
        fail(f"{scenario_id} required_assertions missing")
    if not isinstance(steps, list) or not steps:
        fail(f"{scenario_id} exercise_steps missing")
    if not isinstance(alignment, list) or not alignment:
        fail(f"{scenario_id} authority alignment missing")

    scenario_digest = canonical_sha256(scenario)
    return {
        "scenario_id": scenario_id,
        "kind": kind,
        "packet_state": "COMPILED_SYNTHETIC_REHEARSAL_PACKET_NOT_EXECUTED_NOT_EVIDENCE",
        "source_commit_sha": source_sha,
        "scenario_definition_sha256": scenario_digest,
        "runbook_sha256": runbook_sha256,
        "synthetic_fixture_sha256": canonical_sha256(fixture),
        "step_count": len(steps),
        "assertion_count": len(assertions),
        "authority_requirement_alignment": sorted(str(item) for item in alignment),
        "exercise_executed": False,
        "real_customer_data_used": False,
        "network_call_performed": False,
        "supabase_mutation_performed": False,
        "provider_call_performed": False,
        "secret_value_present": False,
        "operational_owner_assignment_attested": False,
        "legal_review_attested": False,
        "gate_ready_attested": False,
        "evidence_ref_created": False,
        "evidence_digest_created": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    source_sha = args.source_sha.strip().lower()
    if not SHA1_RE.fullmatch(source_sha):
        fail("--source-sha must be exact 40-character lower-hex commit SHA")

    scenarios = load_json(SCENARIOS)
    open_decisions = load_json(OPEN_DECISIONS)
    stage44 = load_json(STAGE44)
    stage45 = load_json(STAGE45)

    if scenarios.get("status") != "SYNTHETIC_REHEARSAL_DEFINITIONS_ONLY_NOT_OPERATIONAL_EVIDENCE":
        fail("scenario registry status drift")
    if open_decisions.get("status") != "DRAFT_UNREVIEWED_NOT_EVIDENCE":
        fail("Stage67 open decisions no longer remain unreviewed")
    if stage44.get("gates", {}).get("data_subject_request_channel") != "DENIED_AWAITING_REAL_OPERATIONAL_AND_CONTROLLED_SYNTHETIC_EVIDENCE":
        fail("Stage44 DSR gate is not in expected denied state")
    if stage45.get("gates", {}).get("incident_response") != "DENIED_AWAITING_REAL_GOVERNANCE_AND_CONTROLLED_TABLETOP_EVIDENCE":
        fail("Stage45 incident gate is not in expected denied state")

    fixture_policy = scenarios.get("fixture_policy", {})
    expected_false = (
        "real_customer_data_allowed",
        "network_calls_allowed",
        "supabase_mutation_allowed",
        "provider_calls_allowed",
        "secrets_allowed",
        "real_access_tokens_allowed",
        "production_identifiers_allowed",
        "gate_promotion_allowed",
    )
    for key in expected_false:
        if fixture_policy.get(key) is not False:
            fail(f"fixture policy drift: {key}")

    dsr_runbook_sha = sha256_file(DSR_RUNBOOK)
    incident_runbook_sha = sha256_file(INCIDENT_RUNBOOK)
    dsr = scenarios.get("dsr_scenarios")
    incident = scenarios.get("incident_scenarios")
    if not isinstance(dsr, list) or len(dsr) != 5:
        fail("expected exactly five DSR rehearsal scenarios")
    if not isinstance(incident, list) or len(incident) != 3:
        fail("expected exactly three incident rehearsal scenarios")

    packets = [compile_scenario("dsr", item, source_sha, dsr_runbook_sha) for item in dsr]
    packets.extend(compile_scenario("incident", item, source_sha, incident_runbook_sha) for item in incident)
    packets.sort(key=lambda item: str(item["scenario_id"]))

    bundle_core = {
        "schema_version": 1,
        "stage": "STAGE68_SYNTHETIC_GOVERNANCE_REHEARSAL_COMPILER",
        "output_kind": "NON_ATTESTING_SYNTHETIC_GOVERNANCE_REHEARSAL_BUNDLE",
        "bundle_state": "COMPILED_REHEARSAL_PACKETS_NOT_EXECUTED_NOT_OPERATIONAL_OR_LEGAL_EVIDENCE",
        "source_commit_sha": source_sha,
        "scenario_registry_sha256": sha256_file(SCENARIOS),
        "dsr_runbook_sha256": dsr_runbook_sha,
        "incident_runbook_sha256": incident_runbook_sha,
        "open_decisions_sha256": sha256_file(OPEN_DECISIONS),
        "stage44_authority_sha256": sha256_file(STAGE44),
        "stage45_authority_sha256": sha256_file(STAGE45),
        "packet_count": len(packets),
        "packets": packets,
        "exercise_executed": False,
        "real_customer_data_used": False,
        "network_call_performed": False,
        "supabase_mutation_performed": False,
        "provider_call_performed": False,
        "legal_review_attested": False,
        "operational_review_attested": False,
        "evidence_migration_created": False,
        "data_subject_request_gate_ready_attested": False,
        "incident_response_gate_ready_attested": False,
        "controlled_launch_promoted": False,
        "paid_media_promoted": False,
        "next_action": "REAL_CONTROLLED_REHEARSAL_EXECUTION_WITH_ASSIGNED_OWNERS_AND_INDEPENDENT_REVIEW_REQUIRED",
    }
    bundle = dict(bundle_core)
    bundle["bundle_sha256"] = canonical_sha256(bundle_core)

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(bundle, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

    print("STAGE68_SYNTHETIC_GOVERNANCE_REHEARSAL_BUNDLE=PASS_COMPILED_ONLY")
    print(f"SOURCE_SHA={source_sha}")
    print(f"PACKET_COUNT={len(packets)}")
    print(f"BUNDLE_SHA256={bundle['bundle_sha256']}")
    print("EXERCISE_EXECUTED=false")
    print("REAL_CUSTOMER_DATA_USED=false")
    print("REMOTE_MUTATION=false")
    print("DSR_GATE_READY=false")
    print("INCIDENT_RESPONSE_GATE_READY=false")


if __name__ == "__main__":
    main()
