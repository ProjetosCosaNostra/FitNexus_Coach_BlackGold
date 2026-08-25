from __future__ import annotations

import hashlib
import json
from pathlib import Path

FAILURE_CLASS = "BGF-STAGE55-FINAL-RECONCILIATION-GUARD-526"
ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage55_stage54_final_reconciliation_authority.json"
MIGRATIONS = BACKEND / "migrations"

EXPECTED_BASELINE = "6db1a0c500355a0d7e7e04aaca92099ec5390820"
EXPECTED_STAGE54_HEAD = "4fa5db8077622486991f5ea14fc665de3c8e9fae"
EXPECTED_STAGE54_MERGE = "6db1a0c500355a0d7e7e04aaca92099ec5390820"
EXPECTED_STAGE54_RUN = 32793487853
EXPECTED_FLUTTER_RUN = 32793487921
EXPECTED_OBSERVED = "2026-08-25T00:34:19.673533+00:00"
EXPECTED_STAGE54_AUTHORITY_BLOB = "05c99cdc785bcd8872b51773078a8c97b56675af"
EXPECTED_STAGE54_VERIFIER_BLOB = "e7d3a1d65fc30526ea1b05dd05ffbe7a6f07ffbf"
EXPECTED_FAILURE_CLASSES = {
    "BGF-STAGE55-READONLY-PRIVATE-FUNCTION-CONNECTOR-ROLE-DENIED-521",
    "BGF-STAGE55-POSTMERGE-GATE-DRIFT-522",
    "BGF-STAGE55-STAGE54-SEALED-INPUT-DRIFT-523",
    "BGF-STAGE55-REMOTE-MUTATION-DURING-RECONCILIATION-524",
    "BGF-STAGE55-FALSE-BILLING-READY-525",
    "BGF-STAGE55-FINAL-RECONCILIATION-GUARD-526",
}
EXPECTED_BLOCKED_EVIDENCE_GATES = {
    "data_subject_request_channel",
    "incident_response",
    "legal_privacy_notice",
    "legal_role_mapping",
    "legal_terms_of_use",
    "production_deployment",
}


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE55_STAGE54_FINAL_RECONCILIATION=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\nDETAIL={detail}"
    )


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def load_authority() -> dict:
    try:
        value = json.loads(AUTHORITY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"authority unreadable: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail("authority must be a JSON object")
    return value


def main() -> None:
    authority = load_authority()
    expected_top = {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE55_STAGE54_FINAL_RECONCILIATION",
        "baseline_main_sha": EXPECTED_BASELINE,
        "final_state": "STAGE54_MERGED_GREEN_REMOTE_UNCHANGED_BILLING_EXTERNAL_AUTHORITY_STILL_MISSING",
    }
    for key, expected in expected_top.items():
        if authority.get(key) != expected:
            fail(f"authority drift: {key}")

    pr = authority.get("stage54_pr")
    if pr != {
        "number": 145,
        "head_sha": EXPECTED_STAGE54_HEAD,
        "merge_sha": EXPECTED_STAGE54_MERGE,
        "mergeable_before_merge": True,
        "exact_head_merge_enforced": True,
    }:
        fail("Stage54 PR reconciliation drift")

    ci = authority.get("stage54_ci")
    if not isinstance(ci, dict):
        fail("Stage54 CI receipt missing")
    if ci.get("stage54_run_id") != EXPECTED_STAGE54_RUN or ci.get("stage54_conclusion") != "success":
        fail("Stage54 workflow success receipt drift")
    if ci.get("flutter_run_id") != EXPECTED_FLUTTER_RUN or ci.get("flutter_conclusion") != "success":
        fail("Flutter workflow success receipt drift")
    if ci.get("consumed_live_proof_workflows_replayed") is not False:
        fail("consumed live proof replay must remain false")

    sealed = authority.get("sealed_stage54_inputs")
    expected_sealed = {
        "authority": (
            BACKEND / "stage54_billing_external_evidence_promotion_boundary_authority.json",
            EXPECTED_STAGE54_AUTHORITY_BLOB,
        ),
        "verifier": (
            BACKEND / "tools/verify_stage54_billing_external_evidence_promotion_boundary.py",
            EXPECTED_STAGE54_VERIFIER_BLOB,
        ),
    }
    if not isinstance(sealed, dict) or set(sealed) != set(expected_sealed):
        fail("sealed Stage54 input registry drift")
    for label, (path, expected_blob) in expected_sealed.items():
        entry = sealed[label]
        if not path.is_file():
            fail(f"sealed Stage54 input missing: {label}")
        if entry.get("git_blob_sha") != expected_blob:
            fail(f"declared Stage54 blob drift: {label}")
        if git_blob_sha(path) != expected_blob:
            fail(f"actual Stage54 blob drift: {label}")

    snapshot = authority.get("postmerge_remote_read_only_snapshot")
    if not isinstance(snapshot, dict):
        fail("postmerge read-only snapshot missing")
    expected_snapshot = {
        "observed_at_utc": EXPECTED_OBSERVED,
        "read_only": True,
        "remote_mutation_performed": False,
        "canonical_private_function_call_succeeded": False,
        "canonical_private_function_failure": "permission denied for function get_controlled_launch_readiness_authority",
        "fallback_projection": "DIRECT_SELECT_EQUIVALENT_OF_STAGE20_READINESS_LOGIC",
        "ready_mandatory_gates": 2,
        "mandatory_gates": 9,
        "blocking_gate_count": 7,
        "tracking_core_ready": True,
        "pricing_experiment_ready": True,
        "billing_provider_credentials_ready": False,
        "manual_evidence_ready_rows": 0,
        "billing_external_evidence_total": 0,
        "credentials_verified_rows": 0,
        "proof_complete_rows": 0,
    }
    for key, expected in expected_snapshot.items():
        if snapshot.get(key) != expected:
            fail(f"postmerge snapshot drift: {key}")
    if set(snapshot.get("blocked_evidence_migration_gates", [])) != EXPECTED_BLOCKED_EVIDENCE_GATES:
        fail("blocked evidence-migration gate set drift")
    if snapshot.get("billing_selection") != {
        "scope": "BR_V1",
        "provider_code": "asaas",
        "state": "selected_pending_credentials",
        "evidence_version": "2026-08-18-official-docs-v1",
        "activated_at": None,
    }:
        fail("billing selection postmerge snapshot drift")

    governance = authority.get("governance")
    if not isinstance(governance, dict):
        fail("governance registry missing")
    if governance.get("stage54_boundary") != "PASS_MERGED_REPO_ONLY":
        fail("Stage54 final state is not merged repo-only PASS")
    required_false = (
        "stage54_remote_apply_required",
        "stage54_remote_apply_authorized",
        "execute_sql_dml_or_ddl_allowed",
        "private_function_permission_failure_may_be_repaired_by_privilege_mutation",
    )
    for key in required_false:
        if governance.get(key) is not False:
            fail(f"forbidden reconciliation authority enabled: {key}")
    for gate in (
        "billing_provider_credentials",
        "proof_complete",
        "provider_activation",
        "provider_call",
        "incident_response",
        "production_deployment",
        "controlled_launch",
        "paid_media",
        "launch",
    ):
        if not str(governance.get(gate, "")).startswith("DENIED"):
            fail(f"Stage55 cannot promote gate: {gate}")

    if set(authority.get("failure_classes", [])) != EXPECTED_FAILURE_CLASSES:
        fail("Stage55 failure-class registry drift")

    if list(MIGRATIONS.glob("*stage54*.sql")) or list(MIGRATIONS.glob("*stage55*.sql")):
        fail("Stage54/55 reconciliation is repository-only and must not add a migration")

    print("STAGE55_STAGE54_FINAL_RECONCILIATION=PASS")
    print("STAGE54_BOUNDARY=PASS_MERGED_REPO_ONLY")
    print("REMOTE_STATE_UNCHANGED=true")
    print("READY_MANDATORY_GATES=2/9")
    print("BILLING_EXTERNAL_EVIDENCE_ROWS=0")
    print("BILLING_PROVIDER_CREDENTIALS=DENIED")
    print("PROVIDER_ACTIVATION=DENIED")
    print("PROOF_COMPLETE=DENIED")
    print("REMOTE_MUTATION=false")
    print("CONTROLLED_LAUNCH=DENIED")


if __name__ == "__main__":
    main()
