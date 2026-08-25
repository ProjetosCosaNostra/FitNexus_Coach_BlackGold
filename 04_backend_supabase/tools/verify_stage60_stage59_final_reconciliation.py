from __future__ import annotations

import hashlib
import json
from pathlib import Path

FAILURE_CLASS = "BGF-STAGE60-FINAL-RECONCILIATION-GUARD-582"
ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage60_stage59_final_reconciliation_authority.json"
MIGRATIONS = BACKEND / "migrations"

EXPECTED_BASELINE = "ec939ea19c20d74c689d7193cf645d4b2fe2c20a"
EXPECTED_STAGE59_HEAD = "61527ad9ee2a03ca7766e113746e2169b1770705"
EXPECTED_STAGE59_MERGE = "ec939ea19c20d74c689d7193cf645d4b2fe2c20a"
EXPECTED_STAGE59_RUN = 32831867830
EXPECTED_FLUTTER_RUN = 32831867904
EXPECTED_OBSERVED = "2026-08-25T09:28:14.063689+00:00"
EXPECTED_STAGE59_AUTHORITY_BLOB = "7da5bc11b15d0813f77a00b2fd5e19f7a72ee4ca"
EXPECTED_STAGE59_VERIFIER_BLOB = "33da0da1c8483304161045703463856da99609ee"
EXPECTED_FAILURE_CLASSES = {
    "BGF-STAGE60-STAGE59-SEALED-INPUT-DRIFT-577",
    "BGF-STAGE60-POSTMERGE-REMOTE-STATE-DRIFT-578",
    "BGF-STAGE60-CI-RECEIPT-DRIFT-579",
    "BGF-STAGE60-FALSE-INDEPENDENT-REVIEW-READY-580",
    "BGF-STAGE60-REMOTE-MUTATION-DURING-RECONCILIATION-581",
    "BGF-STAGE60-FINAL-RECONCILIATION-GUARD-582",
}


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE60_STAGE59_FINAL_RECONCILIATION=FAIL\n"
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
        "stage": "STAGE60_STAGE59_FINAL_RECONCILIATION",
        "baseline_main_sha": EXPECTED_BASELINE,
        "final_state": "STAGE59_MERGED_GREEN_REMOTE_UNCHANGED_REAL_PROOF_AND_INDEPENDENT_REVIEW_STILL_MISSING",
    }
    for key, expected in expected_top.items():
        if authority.get(key) != expected:
            fail(f"authority drift: {key}")

    pr = authority.get("stage59_pr")
    if pr != {
        "number": 150,
        "head_sha": EXPECTED_STAGE59_HEAD,
        "merge_sha": EXPECTED_STAGE59_MERGE,
        "mergeable_before_merge": True,
        "exact_head_merge_enforced": True,
    }:
        fail("Stage59 PR reconciliation drift")

    ci = authority.get("stage59_ci")
    if not isinstance(ci, dict):
        fail("Stage59 CI receipt missing")
    if ci.get("stage59_run_id") != EXPECTED_STAGE59_RUN or ci.get("stage59_conclusion") != "success":
        fail("Stage59 workflow success receipt drift")
    if ci.get("flutter_run_id") != EXPECTED_FLUTTER_RUN or ci.get("flutter_conclusion") != "success":
        fail("Flutter workflow success receipt drift")
    if ci.get("consumed_live_proof_workflows_replayed") is not False:
        fail("consumed live-proof workflow replay must remain false")

    sealed = authority.get("sealed_stage59_inputs")
    expected_sealed = {
        "authority": (
            BACKEND / "stage59_billing_proof_independent_review_preparation_authority.json",
            EXPECTED_STAGE59_AUTHORITY_BLOB,
        ),
        "verifier": (
            BACKEND / "tools/verify_stage59_billing_proof_independent_review_preparation.py",
            EXPECTED_STAGE59_VERIFIER_BLOB,
        ),
    }
    if not isinstance(sealed, dict) or set(sealed) != set(expected_sealed):
        fail("sealed Stage59 input registry drift")
    for label, (path, expected_blob) in expected_sealed.items():
        entry = sealed[label]
        if not path.is_file():
            fail(f"sealed Stage59 input missing: {label}")
        if entry.get("path") != str(path.relative_to(ROOT)).replace("\\", "/"):
            fail(f"sealed Stage59 path drift: {label}")
        if entry.get("git_blob_sha") != expected_blob:
            fail(f"declared Stage59 blob drift: {label}")
        if git_blob_sha(path) != expected_blob:
            fail(f"actual Stage59 blob drift: {label}")

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
    if governance.get("stage59_boundary") != "PASS_MERGED_REPO_ONLY":
        fail("Stage59 boundary is not merged repo-only PASS")
    for key in (
        "stage59_remote_apply_required",
        "stage59_remote_apply_authorized",
        "execute_sql_dml_or_ddl_allowed",
        "evidence_fabrication_allowed",
    ):
        if governance.get(key) is not False:
            fail(f"forbidden Stage60 authority enabled: {key}")
    if governance.get("real_stage58_complete_bundle") != "DENIED_NOT_SUPPLIED":
        fail("Stage60 falsely claims a real Stage58 complete bundle")
    if governance.get("independent_review") != "DENIED_NOT_SUPPLIED":
        fail("Stage60 falsely claims independent review")
    for gate in (
        "stage56_reviewed_candidate",
        "proof_complete",
        "billing_provider_credentials",
        "provider_activation",
        "provider_call",
        "incident_response",
        "production_deployment",
        "controlled_launch",
        "paid_media",
        "launch",
    ):
        if not str(governance.get(gate, "")).startswith("DENIED"):
            fail(f"Stage60 cannot promote gate: {gate}")

    if set(authority.get("failure_classes", [])) != EXPECTED_FAILURE_CLASSES:
        fail("Stage60 failure-class registry drift")

    if list(MIGRATIONS.glob("*stage59*.sql")) or list(MIGRATIONS.glob("*stage60*.sql")):
        fail("Stage59/60 reconciliation is repository-only and must not add a migration")

    print("STAGE60_STAGE59_FINAL_RECONCILIATION=PASS")
    print("STAGE59_BOUNDARY=PASS_MERGED_REPO_ONLY")
    print("REMOTE_STATE_UNCHANGED=true")
    print("REAL_STAGE58_COMPLETE_BUNDLE=NOT_SUPPLIED")
    print("INDEPENDENT_REVIEW=DENIED_NOT_SUPPLIED")
    print("STAGE56_REVIEWED_CANDIDATE=DENIED")
    print("PROOF_COMPLETE=DENIED")
    print("BILLING_PROVIDER_CREDENTIALS=DENIED")
    print("REMOTE_MUTATION=false")
    print("CONTROLLED_LAUNCH=DENIED")


if __name__ == "__main__":
    main()
