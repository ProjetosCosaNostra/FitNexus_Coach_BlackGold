#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTROL = ROOT / "10_compliance/inventory/COMMERCIAL_READINESS_MACROBLOCK_V1.json"

EXPECTED_OPEN_DECISIONS = {
    "LEGAL_ENTITY_IDENTITY",
    "LEGAL_REVIEWER_REFERENCE",
    "CONTROLLER_PROCESSOR_ROLE_MATRIX",
    "SENSITIVE_DATA_TREATMENT",
    "SUBPROCESSOR_AND_TRANSFER_MAP",
    "RETENTION_MATRIX",
    "BILLING_CANCELLATION_REFUND_POLICY",
    "TERMS_ACCEPTANCE_VERSIONING",
    "DSR_STABLE_PUBLIC_ROUTE",
    "DSR_OWNER_AND_BACKUP",
    "DSR_CONTROLLED_TESTS",
    "INCIDENT_OWNER_ASSIGNMENTS",
    "INCIDENT_RISK_AND_COMMUNICATION_PROCEDURE",
    "INCIDENT_TABLETOPS",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"COMMERCIAL_READINESS_MACROBLOCK_V1_GUARD=FAIL::{message}")


def main() -> None:
    control = load_json(CONTROL)

    require(control["kind"] == "NON_ATTESTING_COMMERCIAL_READINESS_CONTROL_TOWER", "kind drift")
    require(control["strategy"]["operating_model"] == "MACROBLOCKS_NOT_MICROSTAGES", "strategy drift")
    require(control["strategy"]["macroblocks"] == [
        "COMMERCIAL_READINESS",
        "PRODUCTION_AND_BILLING",
        "COMMERCIAL_LAUNCH",
    ], "macroblock order drift")
    require(control["strategy"]["one_coherent_pr_per_macroblock"] is True, "macroblock PR policy drift")
    require(control["strategy"]["poll_ci_repeatedly_in_same_work_cycle"] is False, "CI polling policy drift")
    require(control["strategy"]["microstage_credit_without_gate_fact_change"] is False, "progress credit policy drift")
    require(control["strategy"]["dangerous_or_irreversible_operations_remain_separately_gated"] is True, "dangerous-operation gate drift")

    for binding_name, binding in control["source_bindings"].items():
        path = ROOT / binding["path"]
        require(path.exists(), f"missing bound source: {binding_name}")
        require(git_blob_sha(path) == binding["git_blob_sha"], f"bound source blob drift: {binding_name}")

    open_decisions = load_json(ROOT / control["source_bindings"]["open_decisions"]["path"])
    unresolved = open_decisions["unresolved"]
    actual_ids = {item["id"] for item in unresolved}
    require(actual_ids == EXPECTED_OPEN_DECISIONS, "canonical open-decision set drift")
    require(all(item["state"] == "OPEN" for item in unresolved), "canonical decision unexpectedly non-OPEN")
    require(set(control["critical_open_decisions"]) == EXPECTED_OPEN_DECISIONS, "control-tower decision set drift")

    terms = load_json(ROOT / control["source_bindings"]["terms_review_readiness"]["path"])
    require(terms["exact_draft_input"]["status_marker"] == "DRAFT_UNREVIEWED_NOT_PUBLISHED_NOT_LEGAL_EVIDENCE", "Terms draft status drift")
    require(terms["exact_draft_input"]["legal_gate_marker"] == "legal_terms_of_use = BLOCKED", "Terms legal-gate marker drift")
    receipt = terms["fresh_remote_nonregistration_receipt"]
    require(receipt["terms_registry_rows"] == 0, "Terms registry is no longer zero at bound Stage90 receipt")
    require(receipt["acceptance_ledger_rows"] == 0, "Terms acceptance ledger is no longer zero at bound Stage90 receipt")
    require(receipt["remote_mutation_performed"] is False, "Stage90 receipt mutation drift")
    require(terms["hard_boundaries"]["terms_candidate_approved"] is False, "Terms approval shortcut detected")
    require(terms["hard_boundaries"]["controlled_launch_promoted"] is False, "Stage90 controlled-launch promotion drift")

    exercise = load_json(ROOT / control["source_bindings"]["controlled_exercise_review_intake"]["path"])
    for key in (
        "stage69_session_candidate",
        "completed_exercise_record",
        "independent_review_record",
        "reviewer_assignment_or_authority_artifact",
    ):
        require(exercise["required_external_inputs"][key]["required"] is True, f"Stage91 external requirement drift: {key}")
    fail_closed = exercise["fail_closed_rules"]
    require(fail_closed["supabase_mutation_allowed"] is False, "Stage91 Supabase mutation boundary drift")
    require(fail_closed["data_subject_request_gate_promotion_allowed"] is False, "Stage91 DSR promotion boundary drift")
    require(fail_closed["incident_response_gate_promotion_allowed"] is False, "Stage91 incident promotion boundary drift")
    require(fail_closed["controlled_launch_promotion_allowed"] is False, "Stage91 controlled-launch boundary drift")
    require(fail_closed["paid_media_promotion_allowed"] is False, "Stage91 paid-media boundary drift")

    for binding_key in ("predeploy_template", "postdeploy_template"):
        template = load_json(ROOT / control["source_bindings"][binding_key]["path"])
        require(template["test_fixture"] is True, f"{binding_key} unexpectedly operational")
        require(template["contains_placeholders"] is True, f"{binding_key} placeholders unexpectedly cleared")
        require(template["operator_acknowledged"] is False, f"{binding_key} unexpectedly operator-acknowledged")

    estimate = control["management_progress_estimate"]
    areas = estimate["areas"]
    require(sum(item["weight"] for item in areas) == 100, "progress weights must sum to 100")
    require(sum(item["earned"] for item in areas) == estimate["commercial_publication_percent"], "commercial percentage arithmetic drift")
    require(estimate["commercial_publication_percent"] == 74, "management baseline changed without a gate fact")
    require(estimate["technical_product_percent"] == 92, "technical baseline drift")
    require(estimate["status"] == "MANAGEMENT_ESTIMATE_NOT_RELEASE_EVIDENCE", "estimate attestation boundary drift")

    require(control["macroblock_status"]["COMMERCIAL_READINESS"]["state"] == "ACTIVE_EXTERNAL_FACT_COLLECTION", "commercial-readiness state drift")
    require(control["macroblock_status"]["PRODUCTION_AND_BILLING"]["state"] == "BLOCKED_BY_COMMERCIAL_READINESS_AND_REAL_PRODUCTION_AUTHORITY", "production/billing state drift")
    require(control["macroblock_status"]["COMMERCIAL_LAUNCH"]["state"] == "BLOCKED", "launch state drift")

    require(all(value == "DENIED" for value in control["gates"].values()), "a denied gate was promoted by the control tower")
    require(all(value is False for value in control["hard_boundaries"].values()), "hard-boundary drift")

    print("COMMERCIAL_READINESS_MACROBLOCK_V1_GUARD=PASS")
    print(f"COMMERCIAL_PUBLICATION_MANAGEMENT_ESTIMATE={estimate['commercial_publication_percent']}%")
    print(f"TECHNICAL_PRODUCT_MANAGEMENT_ESTIMATE={estimate['technical_product_percent']}%")
    print(f"OPEN_DECISIONS={len(EXPECTED_OPEN_DECISIONS)}")


if __name__ == "__main__":
    main()
