from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

FAILURE_CLASS = "BGF-STAGE45-INCIDENT-RESPONSE-RECEIPT-STRUCTURAL-REVIEW-418"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE45_INCIDENT_RESPONSE_RECEIPT_REVIEW=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\n"
        f"DETAIL={detail}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()
    try:
        receipt = json.loads(args.receipt.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"receipt unreadable: {type(exc).__name__}")
    if not isinstance(receipt, dict):
        fail("receipt must be a JSON object")

    expected = {
        "schema_version": 1,
        "stage": "STAGE45_INCIDENT_RESPONSE_EXTERNAL_EVIDENCE_PREPARATION",
        "output_kind": "DIGEST_ONLY_INCIDENT_RESPONSE_EVIDENCE_INTAKE_CANDIDATE",
        "gate_code": "incident_response",
        "candidate_state": "AWAITING_INDEPENDENT_REVIEW_NOT_ATTESTATION",
        "synthetic_or_non_customer_tabletop_fixture_confirmation": "CONFIRMED",
        "redaction_confirmation": "CONFIRMED",
        "raw_artifact_content_copied_to_receipt": False,
        "artifact_path_or_filename_copied_to_receipt": False,
        "personal_or_secret_material_collected": False,
        "real_customer_data_used_in_tabletops": False,
        "live_incident_required": False,
        "network_call_performed": False,
        "supabase_mutation_performed": False,
        "evidence_migration_created": False,
        "operational_or_legal_self_attested": False,
        "gate_ready_attested": False,
        "controlled_launch_promoted": False,
        "next_action": "INDEPENDENT_REVIEW_REQUIRED_BEFORE_ANY_EVIDENCE_MIGRATION",
    }
    for key, value in expected.items():
        if receipt.get(key) != value:
            fail(f"receipt invariant drift: {key}")

    for key in (
        "incident_commander_privacy_owner_technical_owner_assignment_digest",
        "risk_classification_matrix_digest",
        "operator_to_controller_handoff_procedure_digest",
        "anpd_data_subject_communication_decision_procedure_digest",
        "incident_registry_retention_control_digest",
        "cross_tenant_exposure_tabletop_receipt_digest",
        "credential_compromise_tabletop_receipt_digest",
        "potentially_sensitive_student_data_tabletop_receipt_digest",
        "final_drill_postmortem_digest",
    ):
        if not SHA256_RE.fullmatch(str(receipt.get(key, ""))):
            fail(f"invalid SHA-256 digest: {key}")

    serialized = json.dumps(receipt, sort_keys=True).lower()
    for forbidden in (
        '"api_key"',
        '"access_token"',
        '"password"',
        '"webhook_token"',
        '"secret_value"',
        '"cpf"',
        '"student_name"',
        '"customer_email"',
        '"customer_name"',
        '"real_incident_payload"',
    ):
        if forbidden in serialized:
            fail(f"secret/personal/live-incident-bearing key present: {forbidden}")

    print("STAGE45_INCIDENT_RESPONSE_RECEIPT_REVIEW=PASS_STRUCTURAL_CANDIDATE_ONLY")
    print("INCIDENT_OWNERSHIP_OPERATIONALLY_VERIFIED_BY_SCRIPT=false")
    print("RISK_CLASSIFICATION_LEGAL_SUFFICIENCY_VERIFIED_BY_SCRIPT=false")
    print("ANPD_DATA_SUBJECT_NOTIFICATION_CONCLUSION_VERIFIED_BY_SCRIPT=false")
    print("TABLETOP_OPERATIONAL_SUFFICIENCY_VERIFIED_BY_SCRIPT=false")
    print("POSTMORTEM_REMEDIATION_COMPLETENESS_VERIFIED_BY_SCRIPT=false")
    print("REAL_CUSTOMER_DATA_USED=false")
    print("LIVE_INCIDENT_REQUIRED=false")
    print("GATE_READY=false")
    print("INDEPENDENT_SOURCE_ARTIFACT_REVIEW_REQUIRED=true")


if __name__ == "__main__":
    main()
