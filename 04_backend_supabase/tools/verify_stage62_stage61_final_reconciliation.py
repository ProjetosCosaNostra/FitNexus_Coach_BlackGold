from __future__ import annotations

import hashlib
import json
from pathlib import Path

FAILURE_CLASS = "BGF-STAGE62-FINAL-RECONCILIATION-GUARD-601"
ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage62_stage61_final_reconciliation_authority.json"
MIGRATIONS = BACKEND / "migrations"

EXPECTED_BASELINE = "237a9091d8194ab005620c899cdd11d7121329ba"
EXPECTED_STAGE61_HEAD = "e5242a0e30dbf084922e3148f9e117f408283f6a"
EXPECTED_STAGE61_MERGE = "237a9091d8194ab005620c899cdd11d7121329ba"
EXPECTED_STAGE61_RUN = 32833269860
EXPECTED_FLUTTER_RUN = 32833269930
EXPECTED_OBSERVED = "2026-08-25T09:43:57.522015+00:00"
EXPECTED_AUTHORITY_BLOB = "3225b3c5d03fc45c57a4f043411d03b092e31c13"
EXPECTED_VERIFIER_BLOB = "9e8b67893de038460b519a0a01d9c9ef4c1abf7a"
EXPECTED_FAILURE_CLASSES = {
    "BGF-STAGE62-STAGE61-SEALED-INPUT-DRIFT-595",
    "BGF-STAGE62-POSTMERGE-REMOTE-STATE-DRIFT-596",
    "BGF-STAGE62-CI-RECEIPT-DRIFT-597",
    "BGF-STAGE62-FALSE-STATE-MACHINE-AUTHORITY-598",
    "BGF-STAGE62-FIRST-EXTERNAL-BOUNDARY-DRIFT-599",
    "BGF-STAGE62-REMOTE-MUTATION-DURING-RECONCILIATION-600",
    "BGF-STAGE62-FINAL-RECONCILIATION-GUARD-601",
}


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE62_STAGE61_FINAL_RECONCILIATION=FAIL\n"
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
    for key, expected in {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE62_STAGE61_FINAL_RECONCILIATION",
        "baseline_main_sha": EXPECTED_BASELINE,
        "final_state": "STAGE61_MERGED_GREEN_REMOTE_UNCHANGED_FIRST_EXTERNAL_BOUNDARY_STILL_OPERATOR_CREDENTIAL_EVIDENCE",
    }.items():
        if authority.get(key) != expected:
            fail(f"authority drift: {key}")

    if authority.get("stage61_pr") != {
        "number": 152,
        "head_sha": EXPECTED_STAGE61_HEAD,
        "merge_sha": EXPECTED_STAGE61_MERGE,
        "mergeable_before_merge": True,
        "exact_head_merge_enforced": True,
    }:
        fail("Stage61 PR receipt drift")

    ci = authority.get("stage61_ci")
    if ci != {
        "stage61_run_id": EXPECTED_STAGE61_RUN,
        "stage61_conclusion": "success",
        "flutter_run_id": EXPECTED_FLUTTER_RUN,
        "flutter_conclusion": "success",
        "consumed_live_proof_workflows_replayed": False,
    }:
        fail("Stage61 CI receipt drift")

    sealed = authority.get("sealed_stage61_inputs")
    expected_sealed = {
        "authority": (
            BACKEND / "stage61_billing_authorization_state_machine_authority.json",
            EXPECTED_AUTHORITY_BLOB,
        ),
        "verifier": (
            BACKEND / "tools/verify_stage61_billing_authorization_state_machine.py",
            EXPECTED_VERIFIER_BLOB,
        ),
    }
    if not isinstance(sealed, dict) or set(sealed) != set(expected_sealed):
        fail("sealed Stage61 registry drift")
    for label, (path, expected_blob) in expected_sealed.items():
        entry = sealed[label]
        expected_path = str(path.relative_to(ROOT)).replace("\\", "/")
        if entry != {"path": expected_path, "git_blob_sha": expected_blob}:
            fail(f"sealed declaration drift: {label}")
        if not path.is_file() or git_blob_sha(path) != expected_blob:
            fail(f"sealed bytes drift: {label}")

    snapshot = authority.get("postmerge_remote_read_only_snapshot")
    if not isinstance(snapshot, dict):
        fail("postmerge snapshot missing")
    for key, expected in {
        "observed_at_utc": EXPECTED_OBSERVED,
        "read_only": True,
        "remote_mutation_performed": False,
        "billing_external_evidence_total": 0,
        "credentials_verified_rows": 0,
        "proof_complete_rows": 0,
        "checkout_intents": 0,
        "webhook_receipts": 0,
        "evidence_migration_ready_rows": 0,
    }.items():
        if snapshot.get(key) != expected:
            fail(f"postmerge snapshot drift: {key}")
    if snapshot.get("billing_selection") != {
        "scope": "BR_V1",
        "provider_code": "asaas",
        "state": "selected_pending_credentials",
        "evidence_version": "2026-08-18-official-docs-v1",
        "activated_at": None,
    }:
        fail("billing selection postmerge drift")

    governance = authority.get("governance")
    if not isinstance(governance, dict):
        fail("governance missing")
    if governance.get("stage61_boundary") != "PASS_MERGED_REPO_ONLY":
        fail("Stage61 boundary not merged-green")
    if governance.get("current_structural_state") != "AWAITING_REAL_OPERATOR_CREDENTIAL_EVIDENCE":
        fail("first external boundary drift")
    for key in (
        "state_machine_truth_verified",
        "stage61_remote_apply_required",
        "stage61_remote_apply_authorized",
        "execute_sql_dml_or_ddl_allowed",
        "evidence_fabrication_allowed",
        "continuation_command_is_external_authorization",
    ):
        if governance.get(key) is not False:
            fail(f"forbidden Stage62 authority enabled: {key}")
    for gate in (
        "operator_credentials_evidence",
        "credentials_verified",
        "provider_activation",
        "provider_call",
        "controlled_proof",
        "stage58_complete_bundle",
        "stage59_independent_review",
        "stage56_reviewed_candidate",
        "proof_complete",
        "billing_provider_credentials",
        "incident_response",
        "production_deployment",
        "controlled_launch",
        "paid_media",
        "launch",
    ):
        if not str(governance.get(gate, "")).startswith("DENIED"):
            fail(f"Stage62 cannot promote gate: {gate}")

    if set(authority.get("failure_classes", [])) != EXPECTED_FAILURE_CLASSES:
        fail("Stage62 failure-class registry drift")
    if list(MIGRATIONS.glob("*stage61*.sql")) or list(MIGRATIONS.glob("*stage62*.sql")):
        fail("Stage61/62 are repository-only and must not add migrations")

    print("STAGE62_STAGE61_FINAL_RECONCILIATION=PASS")
    print("STAGE61_BOUNDARY=PASS_MERGED_REPO_ONLY")
    print("CURRENT_STRUCTURAL_STATE=AWAITING_REAL_OPERATOR_CREDENTIAL_EVIDENCE")
    print("REMOTE_STATE_UNCHANGED=true")
    print("REMOTE_MUTATION=false")
    print("PROVIDER_ACTIVATION=DENIED")
    print("CONTROLLED_PROOF=DENIED")
    print("PROOF_COMPLETE=DENIED")
    print("CONTROLLED_LAUNCH=DENIED")


if __name__ == "__main__":
    main()
