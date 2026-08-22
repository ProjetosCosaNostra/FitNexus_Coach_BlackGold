from __future__ import annotations

import json
from pathlib import Path

import verify_stage35_alert_dispatcher_deployment_proof_seal as seal

ROOT = Path(__file__).resolve().parents[2]
AUTHORITY = ROOT / "04_backend_supabase" / "stage35_alert_dispatcher_deployment_proof_seal_authority.json"
ONE_SHOT = ROOT / ".github" / "workflows" / "stage35_alert_external_delivery_one_shot_proof.yml"
EXPECTED_PATH = ".github/workflows/stage35_alert_external_delivery_one_shot_proof.yml"
EXPECTED_BLOB = "079a140e36a851eb0f787397929ffbe3351aba48"


def fail(message: str) -> None:
    raise SystemExit("STAGE35_ALERT_DEPLOYMENT_PROOF_SEAL_LIFECYCLE=FAIL\n" + message)


def main() -> None:
    if not ONE_SHOT.is_file():
        fail("sealed one-shot proof workflow missing")
    try:
        authority = json.loads(AUTHORITY.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"seal authority unreadable: {type(exc).__name__}")
    sealed = authority.get("sealed_artifacts", {})
    if sealed.get("one_shot_proof_workflow_file") != EXPECTED_PATH:
        fail("seal authority one-shot workflow path drifted")
    if sealed.get("one_shot_proof_workflow_git_blob_sha") != EXPECTED_BLOB:
        fail("seal authority one-shot workflow blob drifted")

    old = seal.PROOF_WORKFLOW
    try:
        seal.PROOF_WORKFLOW = ONE_SHOT
        seal.main()
    finally:
        seal.PROOF_WORKFLOW = old

    print("STAGE35_ALERT_DEPLOYMENT_PROOF_SEAL_LIFECYCLE=PASS")
    print(f"ONE_SHOT_WORKFLOW={EXPECTED_PATH}")
    print(f"ONE_SHOT_WORKFLOW_BLOB={EXPECTED_BLOB}")
    print("HISTORICAL_PROMOTION_SENTINEL_PATH_REMAINS_ABSENT=true")
    print("PROOF_REEXECUTION_ALLOWED=false")


if __name__ == "__main__":
    main()
