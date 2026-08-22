from __future__ import annotations

import importlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
LEDGER = BACKEND / "migration_ledger_authority.json"
EXPOSURE = BACKEND / "security_definer_exposure_authority.json"
REVOCATION_FILE = BACKEND / "migrations" / "20260822022000_stage33_direct_rpc_revocation_and_post_revocation_fixture.sql"

CURRENT_BASELINE = "35e1c117d63349f27470160da5f58ef6077c47bc"
CURRENT_OBSERVED = "2026-08-22T06:00:17.171196Z"
HISTORICAL_STAGE33_BASELINE = "2f8bd11ac0a4ba4e605807fb17c6c78ff3939041"
HISTORICAL_STAGE33_OBSERVED = "2026-08-22T02:15:46.465445Z"
REVOCATION_NAME = "stage33_direct_rpc_revocation_and_post_revocation_fixture"
REVOCATION_VERSION = "20260822032456"
CLEANUP_NAME = "stage33_post_revocation_proof_cleanup"
STAGE32_MODES = {
    "cleanup", "current_rearm", "r0_seal", "r1_recovery", "stage31",
    "rate_limit", "valid_route", "smoke", "rollback", "rollback_prep", "rollback_seal",
}
MODES = STAGE32_MODES | {"assessment", "preparation", "promotion", "seal"}


def fail(message: str) -> None:
    raise SystemExit("STAGE33_CLEANUP_HISTORICAL_COMPAT=FAIL\n" + message)


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to read {path.relative_to(ROOT)}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"expected JSON object: {path.relative_to(ROOT)}")
    return value


def project_ledger(current: dict) -> dict:
    if current.get("baseline_main_sha") != CURRENT_BASELINE:
        fail("current cleanup ledger baseline drifted")
    if current.get("observed_at_utc") != CURRENT_OBSERVED:
        fail("current cleanup ledger observation drifted")
    remote = {
        row.get("name"): row.get("version")
        for row in current.get("remote_migrations", []) if isinstance(row, dict)
    }
    if remote.get(REVOCATION_NAME) != REVOCATION_VERSION:
        fail("current Stage33 remote revocation receipt missing")
    repo_only = [
        row for row in current.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    ]
    if len(repo_only) != 1 or repo_only[0].get("name") != CLEANUP_NAME:
        fail("current cleanup must be unique repo-only divergence")

    value = json.loads(json.dumps(current))
    value["baseline_main_sha"] = HISTORICAL_STAGE33_BASELINE
    value["observed_at_utc"] = HISTORICAL_STAGE33_OBSERVED
    value["remote_migrations"] = [
        row for row in value.get("remote_migrations", [])
        if not (isinstance(row, dict) and row.get("name") == REVOCATION_NAME)
    ]
    value["declared_divergences"] = [
        row for row in value.get("declared_divergences", [])
        if not (
            isinstance(row, dict)
            and row.get("direction") == "repo_only"
            and row.get("name") == CLEANUP_NAME
        )
    ]
    value["declared_divergences"].append({
        "direction": "repo_only",
        "name": REVOCATION_NAME,
        "reason": "Historical Stage33 pre-remote projection used only for immutable guard replay after the real revocation was applied and verified.",
        "owner": "BlackGold Forge",
        "related_failure_class": "BGF-STAGE33-PRIVILEGE-REVOCATION-PREMATURE-245",
    })
    return value


def project_exposure(current: dict) -> dict:
    if current.get("schema_version") != 2:
        fail("current exposure authority schema drifted")
    if current.get("current_state") != "STAGE33_REVOCATION_REMOTE_RECONCILED_POST_REVOCATION":
        fail("current exposure authority is not remote-reconciled")
    transition = current.get("stage33_transition", {})
    if transition.get("migration_name") != REVOCATION_NAME:
        fail("current exposure transition migration drifted")
    if transition.get("remote_version") != REVOCATION_VERSION or transition.get("remote_applied") is not True:
        fail("current exposure remote receipt drifted")

    value = json.loads(json.dumps(current))
    value["current_state"] = "STAGE33_REVOCATION_REPO_ONLY_REMOTE_PRE_REVOCATION"
    value["baseline_main_sha"] = HISTORICAL_STAGE33_BASELINE
    value["observed_at_utc"] = HISTORICAL_STAGE33_OBSERVED
    value["policy"]["anonymous_exposure"] = "only possession_token_v2_boundary_until_stage33_remote_revocation"
    value["policy"].pop("authenticated_student_route_exposure", None)
    projected_transition = value["stage33_transition"]
    projected_transition["migration_ledger_state"] = "repo_only"
    projected_transition["remote_applied"] = False
    projected_transition["remote_version"] = None
    projected_transition["remote_revocation_allowed_now"] = False
    projected_transition.pop("post_revocation_live_anon_execute_count", None)
    projected_transition.pop("post_revocation_live_authenticated_execute_count", None)
    projected_transition.pop("post_revocation_live_service_role_execute_count", None)
    projected_transition.pop("post_revocation_student_route_advisor_warnings", None)
    return value


def run(mode: str) -> None:
    if mode not in MODES:
        fail(f"unsupported mode: {mode}")

    # Always prove the actual current frontier before projecting immutable history.
    cleanup_guard = importlib.import_module(
        "verify_stage33_post_revocation_proof_cleanup_preparation"
    )
    cleanup_guard.main()

    projected_ledger = project_ledger(load(LEDGER))
    projected_exposure = project_exposure(load(EXPOSURE))

    assessment = importlib.import_module("verify_stage33_direct_rpc_privilege_revocation_assessment")
    preparation = importlib.import_module("verify_stage33_direct_rpc_revocation_preparation")
    promotion = importlib.import_module("verify_stage33_direct_rpc_revocation_migration_promotion")
    seal = importlib.import_module("verify_stage33_post_revocation_live_proof_workflow_seal")
    seal_history = importlib.import_module("verify_stage33_post_revocation_seal_historical_compat")
    stage32_history = importlib.import_module("verify_stage33_revocation_historical_compat")

    with tempfile.TemporaryDirectory(prefix="fitnexus-stage33-cleanup-history-") as tmp:
        temp_root = Path(tmp)
        temp_ledger = temp_root / "migration_ledger_authority.json"
        temp_exposure = temp_root / "security_definer_exposure_authority.json"
        historical_backend = temp_root / "historical_backend"
        historical_migrations = historical_backend / "migrations"
        historical_migrations.mkdir(parents=True)
        if not REVOCATION_FILE.is_file():
            fail("immutable Stage33 revocation migration disappeared before historical projection")
        shutil.copy2(REVOCATION_FILE, historical_migrations / REVOCATION_FILE.name)
        temp_ledger.write_text(json.dumps(projected_ledger, indent=2) + "\n", encoding="utf-8")
        temp_exposure.write_text(json.dumps(projected_exposure, indent=2) + "\n", encoding="utf-8")

        modules = (assessment, preparation, promotion, seal)
        originals = [(module, module.LEDGER if hasattr(module, "LEDGER") else None, module.EXPOSURE) for module in modules]
        old_stage32_ledger = stage32_history.LEDGER
        old_assessment_backend = assessment.BACKEND
        try:
            for module in modules:
                if hasattr(module, "LEDGER"):
                    module.LEDGER = temp_ledger
                module.EXPOSURE = temp_exposure
            stage32_history.LEDGER = temp_ledger

            if mode == "assessment":
                # The immutable assessment enumerates Stage33 revocation migration filenames
                # dynamically through BACKEND/migrations. Project only that historical directory
                # so the later cleanup migration cannot masquerade as part of the old assessment.
                assessment.BACKEND = historical_backend
                assessment.main()
            elif mode == "preparation":
                preparation.main()
            elif mode == "promotion":
                seal_history.main()
            elif mode == "seal":
                seal.main()
            else:
                stage32_history.run(mode)
        finally:
            assessment.BACKEND = old_assessment_backend
            for module, old_ledger, old_exposure in originals:
                if hasattr(module, "LEDGER") and old_ledger is not None:
                    module.LEDGER = old_ledger
                module.EXPOSURE = old_exposure
            stage32_history.LEDGER = old_stage32_ledger

    print("STAGE33_CLEANUP_HISTORICAL_COMPAT=PASS")
    print(f"MODE={mode}")
    print("ACTUAL_STAGE33_STATE=POST_REVOCATION_EDGE_PROOF_VERIFIED_CLEANUP_REPO_ONLY")
    print(f"ACTUAL_REVOCATION_REMOTE_VERSION={REVOCATION_VERSION}")
    print(f"ACTUAL_CLEANUP_REPO_ONLY={CLEANUP_NAME}")
    print("PROJECTED_HISTORICAL_REVOCATION_REMOTE_APPLIED=false")
    print("PROJECTED_HISTORICAL_REVOCATION_REPO_ONLY=true")
    print("PROJECTED_HISTORICAL_LATER_CLEANUP_MIGRATION_VISIBLE=false")
    print("PROOF_REEXECUTION_ALLOWED=false")
    print("REMOTE_REGRANT_ALLOWED=false")
    print("LAUNCH_GATE_PROMOTION=DENIED")


def main() -> None:
    if len(sys.argv) != 2:
        fail(
            "usage: verify_stage33_cleanup_historical_compat.py "
            "<assessment|preparation|promotion|seal|cleanup|current_rearm|r0_seal|r1_recovery|stage31|rate_limit|valid_route|smoke|rollback|rollback_prep|rollback_seal>"
        )
    run(sys.argv[1])


if __name__ == "__main__":
    main()
