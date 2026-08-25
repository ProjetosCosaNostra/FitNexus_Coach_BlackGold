from __future__ import annotations

import hashlib
import json
from pathlib import Path

FAILURE_CLASS = "BGF-STAGE57-FINAL-RECONCILIATION-GUARD-549"
ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage57_stage56_final_reconciliation_authority.json"
MIGRATIONS = BACKEND / "migrations"

EXPECTED_BASELINE = "0cf9c72827d622fd0c093ac3c7dd4b2aaa9cbbe2"
EXPECTED_STAGE56_HEAD = "0d6d89507d37d749d31859e5e467939e0df41e56"
EXPECTED_STAGE56_MERGE = "0cf9c72827d622fd0c093ac3c7dd4b2aaa9cbbe2"
EXPECTED_STAGE56_RUN = 32798284211
EXPECTED_FLUTTER_RUN = 32798284071
EXPECTED_OBSERVED = "2026-08-25T01:40:03.959689+00:00"
EXPECTED_STAGE56_AUTHORITY_BLOB = "4822ad8f32aa7154c851b15a79804698388c8311"
EXPECTED_STAGE56_VERIFIER_BLOB = "6560d29765cbf793f304bffab45642ae29b3add5"
EXPECTED_FAILURE_CLASSES = {
    "BGF-STAGE57-POSTMERGE-PROOF-STATE-DRIFT-544",
    "BGF-STAGE57-STAGE56-SEALED-INPUT-DRIFT-545",
    "BGF-STAGE57-REMOTE-MUTATION-DURING-RECONCILIATION-546",
    "BGF-STAGE57-FALSE-PROOF-COMPLETE-READY-547",
    "BGF-STAGE57-CONSUMED-LIVE-PROOF-REPLAY-548",
    "BGF-STAGE57-FINAL-RECONCILIATION-GUARD-549",
}


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE57_STAGE56_FINAL_RECONCILIATION=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\nDETAIL={detail}"
    )


def blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def main() -> None:
    try:
        authority = json.loads(AUTHORITY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"authority unreadable: {type(exc).__name__}")
    if not isinstance(authority, dict):
        fail("authority must be a JSON object")

    expected_top = {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE57_STAGE56_FINAL_RECONCILIATION",
        "baseline_main_sha": EXPECTED_BASELINE,
        "final_state": "STAGE56_MERGED_GREEN_REMOTE_UNCHANGED_PROOF_COMPLETE_AUTHORITY_PREPARED_NO_LIVE_PROOF",
    }
    for key, expected in expected_top.items():
        if authority.get(key) != expected:
            fail(f"authority drift: {key}")

    if authority.get("stage56_pr") != {
        "number": 147,
        "head_sha": EXPECTED_STAGE56_HEAD,
        "merge_sha": EXPECTED_STAGE56_MERGE,
        "mergeable_before_merge": True,
        "exact_head_merge_enforced": True,
    }:
        fail("Stage56 PR reconciliation drift")

    ci = authority.get("stage56_ci")
    if not isinstance(ci, dict):
        fail("Stage56 CI receipt missing")
    if ci.get("stage56_run_id") != EXPECTED_STAGE56_RUN or ci.get("stage56_conclusion") != "success":
        fail("Stage56 workflow success receipt drift")
    if ci.get("flutter_run_id") != EXPECTED_FLUTTER_RUN or ci.get("flutter_conclusion") != "success":
        fail("Flutter workflow success receipt drift")
    if ci.get("consumed_live_proof_workflows_replayed") is not False:
        fail("consumed live proof replay must remain false")

    sealed = authority.get("sealed_stage56_inputs")
    expected_sealed = {
        "authority": (
            BACKEND / "stage56_billing_proof_complete_promotion_boundary_authority.json",
            EXPECTED_STAGE56_AUTHORITY_BLOB,
        ),
        "verifier": (
            BACKEND / "tools/verify_stage56_billing_proof_complete_promotion_boundary.py",
            EXPECTED_STAGE56_VERIFIER_BLOB,
        ),
    }
    if not isinstance(sealed, dict) or set(sealed) != set(expected_sealed):
        fail("sealed Stage56 registry drift")
    for label, (path, expected_blob) in expected_sealed.items():
        entry = sealed[label]
        if entry.get("git_blob_sha") != expected_blob:
            fail(f"declared Stage56 blob drift: {label}")
        if not path.is_file() or blob_sha(path) != expected_blob:
            fail(f"actual Stage56 blob drift: {label}")

    snapshot = authority.get("postmerge_remote_read_only_snapshot")
    if not isinstance(snapshot, dict):
        fail("postmerge read-only snapshot missing")
    expected_snapshot = {
        "observed_at_utc": EXPECTED_OBSERVED,
        "read_only": True,
        "remote_mutation_performed": False,
        "billing_external_evidence_total": 0,
        "credentials_verified_rows": 0,
        "proof_complete_rows": 0,
        "checkout_intents": 0,
        "webhook_receipts": 0,
        "evidence_migration_ready_rows": 0,
        "runtime_write_grants": 0,
        "provider_code_index_present": True,
    }
    for key, expected in expected_snapshot.items():
        if snapshot.get(key) != expected:
            fail(f"postmerge snapshot drift: {key}")
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
    if governance.get("stage56_boundary") != "PASS_MERGED_REPO_ONLY":
        fail("Stage56 final state is not merged repo-only PASS")
    for key in (
        "stage56_remote_apply_required",
        "stage56_remote_apply_authorized",
        "execute_sql_dml_or_ddl_allowed",
    ):
        if governance.get(key) is not False:
            fail(f"forbidden reconciliation authority enabled: {key}")
    for gate in (
        "credentials_verified",
        "provider_activation",
        "provider_call",
        "proof_complete",
        "billing_provider_credentials",
        "incident_response",
        "production_deployment",
        "controlled_launch",
        "paid_media",
        "launch",
    ):
        if not str(governance.get(gate, "")).startswith("DENIED"):
            fail(f"Stage57 cannot promote gate: {gate}")

    if set(authority.get("failure_classes", [])) != EXPECTED_FAILURE_CLASSES:
        fail("Stage57 failure-class registry drift")
    if list(MIGRATIONS.glob("*stage56*.sql")) or list(MIGRATIONS.glob("*stage57*.sql")):
        fail("Stage56/57 reconciliation is repository-only and must not add a migration")

    print("STAGE57_STAGE56_FINAL_RECONCILIATION=PASS")
    print("STAGE56_BOUNDARY=PASS_MERGED_REPO_ONLY")
    print("REMOTE_STATE_UNCHANGED=true")
    print("BILLING_EXTERNAL_EVIDENCE_ROWS=0")
    print("PROOF_COMPLETE_ROWS=0")
    print("PROVIDER_ACTIVATION=DENIED")
    print("PROVIDER_CALL=DENIED")
    print("REMOTE_MUTATION=false")
    print("CONTROLLED_LAUNCH=DENIED")


if __name__ == "__main__":
    main()
