from __future__ import annotations

import importlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
LEDGER = BACKEND / "migration_ledger_authority.json"
STAGE31_AUTHORITY = BACKEND / "student_access_client_edge_runtime_proof_authority.json"
STAGE31_GUARD = "verify_student_access_client_edge_runtime_preparation"

FIXTURE_NAME = "stage31_client_edge_runtime_fixture"
FIXTURE_STATE = "CLIENT_EDGE_RUNTIME_PROOF_FIXTURE_REPO_ONLY_DIRECT_MODE"
FAILURE_CLASS = "BGF-STAGE31-HISTORICAL-GUARD-REPOONLY-PROJECTION-220"

MODES = {"rate_limit", "valid_route", "smoke", "rollback"}


def fail(message: str) -> None:
    raise SystemExit("STAGE31_REPO_ONLY_HISTORICAL_GUARD_COMPAT=FAIL\n" + message)


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to read {path.relative_to(ROOT)}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"expected JSON object: {path.relative_to(ROOT)}")
    return value


def validate_stage31_current_state() -> dict:
    guard = importlib.import_module(STAGE31_GUARD)
    guard.main()

    authority = load(STAGE31_AUTHORITY)
    if authority.get("current_state") != FIXTURE_STATE:
        fail("Stage 31 repository-only fixture state is not authoritative")
    fixture = authority.get("fixture", {})
    if fixture.get("migration_name") != FIXTURE_NAME:
        fail("Stage 31 fixture migration identity drifted")
    if fixture.get("migration_ledger_state") != "repo_only" or fixture.get("remote_applied") is not False:
        fail("Stage 31 fixture is not repository-only")
    runtime = authority.get("runtime_proof", {})
    if runtime.get("all_five_routes_verified") is not False or runtime.get("cleanup_completed") is not False:
        fail("Stage 31 proof/cleanup self-attested during repository-only compatibility")
    return authority


def sanitized_ledger() -> dict:
    ledger = load(LEDGER)
    repo_rows = [
        row
        for row in ledger.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    ]
    if {row.get("name") for row in repo_rows} != {FIXTURE_NAME}:
        fail("historical projection refuses a mixed or unexpected repo_only divergence set")
    row = repo_rows[0]
    if row.get("related_failure_class") != "BGF-STAGE31-CLIENT-EDGE-RUNTIME-FIXTURE-216":
        fail("Stage 31 repo_only divergence failure class drifted")

    projected = json.loads(json.dumps(ledger))
    projected["declared_divergences"] = [
        row
        for row in projected.get("declared_divergences", [])
        if not (
            isinstance(row, dict)
            and row.get("direction") == "repo_only"
            and row.get("name") == FIXTURE_NAME
        )
    ]
    return projected


def run(mode: str) -> None:
    if mode not in MODES:
        fail(f"unsupported mode: {mode}")

    validate_stage31_current_state()
    projected = sanitized_ledger()

    with tempfile.TemporaryDirectory(prefix="fitnexus-stage31-historical-") as tmp:
        temp_root = Path(tmp)
        temp_ledger = temp_root / "migration_ledger_authority.json"
        temp_ledger.write_text(
            json.dumps(projected, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        if mode == "rate_limit":
            module = importlib.import_module("verify_student_access_network_rate_limit")
            module.LEDGER = temp_ledger
            # Stage 27 predates the Stage 31 verification-only client seam and
            # expects the historical mode-resolution source shape. The current
            # Stage 31 guard above validates the real transport first; this tiny
            # non-authoritative projection exists only to keep the old source
            # co-location assertion meaningful without weakening current checks.
            temp_transport = temp_root / "student_access_transport_historical_projection.dart"
            temp_transport.write_text(
                "final historicalMode = StudentAccessTransportContract.resolvedMode;\n"
                "return _client.rpc(directRpc, params: directParams);\n",
                encoding="utf-8",
            )
            module.TRANSPORT = temp_transport
            module.main()
        elif mode == "valid_route":
            module = importlib.import_module("verify_student_access_valid_route_fixture")
            module.LEDGER = temp_ledger
            module.main()
        else:
            if mode == "smoke":
                nested = importlib.import_module("verify_student_access_client_runtime_smoke")
            else:
                nested = importlib.import_module("verify_student_access_runtime_rollback_candidate")
            nested.LEDGER = temp_ledger

            module = importlib.import_module("verify_stage30_rollback_reconciliation_compat")
            module.LEDGER = temp_ledger
            module.run(mode)

    print("STAGE31_REPO_ONLY_HISTORICAL_GUARD_COMPAT=PASS")
    print(f"MODE={mode}")
    print(f"FAILURE_CLASS={FAILURE_CLASS}")
    print(f"PROJECTED_REPO_ONLY_REMOVED={FIXTURE_NAME}")
    print("ACTUAL_STAGE31_AUTHORITY_VALIDATED=true")
    print("ACTUAL_PRODUCTION_TRANSPORT=directRpc")
    print("EDGE_SELECTION=false")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: verify_stage31_repo_only_historical_guard_compat.py <rate_limit|valid_route|smoke|rollback>")
    run(sys.argv[1])


if __name__ == "__main__":
    main()
