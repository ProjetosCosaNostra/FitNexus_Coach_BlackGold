from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage72_external_readiness_dashboard_authority.json"
STAGE47 = BACKEND / "stage47_unified_external_evidence_intake_orchestration_authority.json"
PLACEHOLDERS = BACKEND / "external_gate_evidence_placeholders.json"
OPEN_DECISIONS = ROOT / "10_compliance" / "drafts" / "COMPLIANCE_OPEN_DECISIONS.json"
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
FAILURE_CLASS = "BGF-STAGE72-EXTERNAL-READINESS-DASHBOARD-GUARD-695"


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE72_EXTERNAL_READINESS_DASHBOARD=FAIL\n"
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


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    source_sha = args.source_sha.strip().lower()
    if not SHA1_RE.fullmatch(source_sha):
        fail("--source-sha must be exact 40-character lower-hex Git SHA")

    authority = load(AUTHORITY)
    stage47 = load(STAGE47)
    placeholders = load(PLACEHOLDERS)
    decisions = load(OPEN_DECISIONS)

    if authority.get("stage") != "STAGE72_EXTERNAL_READINESS_DASHBOARD":
        fail("Stage72 authority drift")
    contract = authority.get("dashboard_contract")
    if not isinstance(contract, dict):
        fail("Stage72 dashboard contract missing")
    gate_order = contract.get("gate_order")
    if not isinstance(gate_order, list) or len(gate_order) != 7 or len(set(gate_order)) != 7:
        fail("Stage72 external gate order must contain seven unique gates")

    placeholder_gates = placeholders.get("gates")
    if not isinstance(placeholder_gates, dict) or set(gate_order) != set(placeholder_gates):
        fail("Stage20 placeholder gate set drift")
    if placeholders.get("template_state") != "PLACEHOLDER_ONLY_NOT_ATTESTATION":
        fail("Stage20 placeholder authority boundary drift")

    canonical = stage47.get("canonical_reviewers")
    if not isinstance(canonical, list) or len(canonical) != 7:
        fail("Stage47 canonical reviewer count drift")
    reviewers: dict[str, dict] = {}
    for item in canonical:
        if not isinstance(item, dict):
            fail("Stage47 canonical reviewer entry must be object")
        gate = str(item.get("gate_code", ""))
        if gate in reviewers or gate not in gate_order:
            fail(f"invalid or duplicate canonical reviewer gate: {gate}")
        reviewers[gate] = item
    if set(reviewers) != set(gate_order):
        fail("Stage47 canonical reviewer coverage drift")

    unresolved = decisions.get("unresolved")
    if decisions.get("status") != "DRAFT_UNREVIEWED_NOT_EVIDENCE" or not isinstance(unresolved, list):
        fail("Stage67 open decision registry boundary drift")
    decision_map: dict[str, list[dict]] = {gate: [] for gate in gate_order}
    for decision in unresolved:
        if not isinstance(decision, dict) or decision.get("state") != "OPEN":
            fail("Stage67 decision must remain an OPEN object")
        decision_id = str(decision.get("id", ""))
        applies = decision.get("applies_to")
        if not decision_id or not isinstance(applies, list):
            fail("Stage67 open decision shape drift")
        for gate in applies:
            if gate in decision_map:
                decision_map[gate].append(decision)

    candidate_inventory = authority.get("candidate_tooling_inventory")
    if not isinstance(candidate_inventory, dict) or set(candidate_inventory) != set(gate_order):
        fail("Stage72 candidate tooling inventory coverage drift")

    gates = []
    required_total = 0
    for gate in gate_order:
        placeholder = placeholder_gates[gate]
        if not isinstance(placeholder, dict):
            fail(f"placeholder gate must be object: {gate}")
        required = placeholder.get("required_evidence")
        if not isinstance(required, list) or not required:
            fail(f"required evidence missing: {gate}")
        if placeholder.get("placeholder_only") is not True:
            fail(f"placeholder-only boundary drift: {gate}")
        if placeholder.get("evidence_ref") is not None or placeholder.get("evidence_digest") is not None:
            fail(f"placeholder unexpectedly contains evidence: {gate}")
        required_total += len(required)

        reviewer = reviewers[gate]
        open_for_gate = sorted(decision_map[gate], key=lambda item: str(item["id"]))
        tooling = candidate_inventory[gate]
        if not isinstance(tooling, list) or not tooling:
            fail(f"candidate tooling inventory missing: {gate}")
        gate_state = authority.get("gates", {}).get(gate)
        if not isinstance(gate_state, str) or not gate_state.startswith("DENIED_"):
            fail(f"external gate no longer has expected denied state: {gate}")

        gates.append(
            {
                "gate_code": gate,
                "authority_mode": placeholder.get("authority_mode"),
                "state": gate_state,
                "ready": False,
                "required_evidence_count": len(required),
                "required_evidence": list(required),
                "open_decision_count": len(open_for_gate),
                "open_decisions": [
                    {
                        "id": item["id"],
                        "required": item.get("required"),
                        "resolution_authority": item.get("resolution_authority"),
                    }
                    for item in open_for_gate
                ],
                "canonical_reviewer": {
                    "source_stage": reviewer.get("source_stage"),
                    "reviewer": reviewer.get("reviewer"),
                    "git_blob_sha": reviewer.get("git_blob_sha"),
                },
                "candidate_tooling": list(tooling),
                "candidate_tooling_is_evidence": False,
                "evidence_ref": None,
                "evidence_digest": None,
                "next_transition": "REAL_EXTERNAL_OR_OPERATIONAL_INPUT_THEN_CANONICAL_REVIEW_THEN_SEPARATE_EVIDENCE_PROMOTION",
            }
        )

    remote = authority.get("fresh_remote_read_only_receipt")
    if not isinstance(remote, dict):
        fail("Stage72 fresh remote receipt missing")
    automatic = {
        "tracking_core": {
            "ready": remote.get("tracking_core_ready") is True,
            "grants_launch_authority": False,
        },
        "pricing_experiment": {
            "ready": remote.get("pricing_experiment_ready") is True,
            "grants_checkout_or_launch_authority": False,
        },
        "billing_provider_credentials": {
            "asaas_state": remote.get("asaas_state"),
            "activated_at": remote.get("asaas_activated_at"),
            "ready": False,
            "requires_external_authorization": True,
        },
    }

    dashboard = {
        "schema_version": 1,
        "stage": "STAGE72_EXTERNAL_READINESS_DASHBOARD",
        "output_kind": "NON_ATTESTING_EXTERNAL_READINESS_BLOCKER_DASHBOARD",
        "dashboard_state": "ALL_EXTERNAL_GATES_BLOCKED_REAL_INPUTS_REQUIRED",
        "source_commit_sha": source_sha,
        "source_sha256": {
            "stage72_authority": sha256_file(AUTHORITY),
            "stage47_unified_intake": sha256_file(STAGE47),
            "external_gate_placeholders": sha256_file(PLACEHOLDERS),
            "stage67_open_decisions": sha256_file(OPEN_DECISIONS),
        },
        "fresh_remote_read_only_receipt": dict(remote),
        "summary": {
            "external_gate_count": len(gates),
            "ready_external_gate_count": 0,
            "blocked_external_gate_count": len(gates),
            "required_evidence_item_count": required_total,
            "open_decision_count": len(unresolved),
            "ready_evidence_migration_count": remote.get("ready_evidence_migration_count"),
            "blocked_evidence_migration_count": remote.get("blocked_evidence_migration_count"),
        },
        "automatic_internal_signals": automatic,
        "gates": gates,
        "guardrails": {
            "candidate_tooling_is_not_evidence": True,
            "internal_ready_signals_are_not_launch_authority": True,
            "dashboard_can_mark_gate_ready": False,
            "dashboard_can_create_evidence_ref": False,
            "dashboard_can_create_evidence_digest": False,
            "dashboard_can_create_evidence_migration": False,
            "remote_mutation_performed": False,
            "deployment_performed": False,
            "provider_call_performed": False,
            "controlled_launch_promoted": False,
            "paid_media_promoted": False,
        },
        "next_action": "RANK_REAL_EXTERNAL_BLOCKERS_WITHOUT_INVENTING_MISSING_FACTS",
    }

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(dashboard, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

    print("STAGE72_EXTERNAL_READINESS_DASHBOARD=PASS_NON_ATTESTING")
    print(f"EXTERNAL_GATES={len(gates)}")
    print("READY_EXTERNAL_GATES=0")
    print(f"REQUIRED_EVIDENCE_ITEMS={required_total}")
    print(f"OPEN_DECISIONS={len(unresolved)}")
    print("REMOTE_MUTATION=false")
    print("CONTROLLED_LAUNCH=DENIED")


if __name__ == "__main__":
    main()
