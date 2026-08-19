from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PLACEHOLDERS = ROOT / "04_backend_supabase" / "external_gate_evidence_placeholders.json"
IDENTITY = ROOT / "04_backend_supabase" / "project_identity.json"

EXPECTED_GATES = {
    "billing_provider_credentials": "external_authorization",
    "legal_privacy_notice": "evidence_migration",
    "legal_terms_of_use": "evidence_migration",
    "legal_role_mapping": "evidence_migration",
    "data_subject_request_channel": "evidence_migration",
    "incident_response": "evidence_migration",
    "production_deployment": "evidence_migration",
}


def fail(detail: str) -> None:
    raise SystemExit(
        "EXTERNAL_GATE_EVIDENCE_PLACEHOLDER_GUARD=FAIL\n"
        "FAILURE_CLASS=BGF-LAUNCH-EXTERNAL-EVIDENCE-SELF-ATTESTATION-145\n"
        f"DETAIL={detail}"
    )


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing required file: {path}")
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path}: {exc}")
    if not isinstance(value, dict):
        fail(f"expected JSON object in {path}")
    return value


def main() -> None:
    payload = load(PLACEHOLDERS)
    identity = load(IDENTITY)

    if payload.get("schema_version") != 1:
        fail("placeholder schema_version must remain 1")
    if payload.get("template_state") != "PLACEHOLDER_ONLY_NOT_ATTESTATION":
        fail("template_state must explicitly remain non-attesting")
    if payload.get("project_ref") != identity.get("project_ref"):
        fail("placeholder project_ref does not match authoritative project_identity.json")

    rules = payload.get("rules")
    if not isinstance(rules, dict):
        fail("rules object missing")
    for key in (
        "this_file_can_mark_gate_ready",
        "this_file_can_hold_evidence_ref",
        "this_file_can_hold_evidence_digest",
    ):
        if rules.get(key) is not False:
            fail(f"{key} must remain false")
    if rules.get("promotion_authority") != (
        "dedicated_versioned_evidence_migration_after_real_external_review_or_operational_test"
    ):
        fail("promotion authority drifted away from dedicated evidence migration")

    gates = payload.get("gates")
    if not isinstance(gates, dict):
        fail("gates object missing")
    if set(gates) != set(EXPECTED_GATES):
        missing = sorted(set(EXPECTED_GATES) - set(gates))
        extra = sorted(set(gates) - set(EXPECTED_GATES))
        fail(f"gate set drifted; missing={missing} extra={extra}")

    for gate_code, authority_mode in EXPECTED_GATES.items():
        gate = gates.get(gate_code)
        if not isinstance(gate, dict):
            fail(f"{gate_code} must be an object")
        if gate.get("authority_mode") != authority_mode:
            fail(f"{gate_code} authority_mode drifted")
        if gate.get("placeholder_only") is not True:
            fail(f"{gate_code} must remain placeholder_only=true")
        if gate.get("evidence_ref") is not None:
            fail(f"{gate_code} placeholder must never contain evidence_ref")
        if gate.get("evidence_digest") is not None:
            fail(f"{gate_code} placeholder must never contain evidence_digest")
        if "state" in gate or "ready" in gate:
            fail(f"{gate_code} placeholder must not carry live readiness state")

        required = gate.get("required_evidence")
        if not isinstance(required, list) or len(required) < 3:
            fail(f"{gate_code} required_evidence must contain at least three items")
        if any(not isinstance(item, str) or not item.strip() for item in required):
            fail(f"{gate_code} required_evidence contains an empty/non-string item")

    print("EXTERNAL_GATE_EVIDENCE_PLACEHOLDER_GUARD=PASS")
    print(f"PROJECT_REF={payload['project_ref']}")
    print(f"PLACEHOLDER_GATES={len(gates)}")
    print("LIVE_ATTESTATION_VALUES=NONE")
    print("GATE_PROMOTION_AUTHORITY=DEDICATED_VERSIONED_EVIDENCE_MIGRATION")


if __name__ == "__main__":
    main()
