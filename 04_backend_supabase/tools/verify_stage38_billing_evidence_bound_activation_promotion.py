from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage38_billing_evidence_bound_activation_promotion_authority.json"
LEDGER = BACKEND / "migration_ledger_authority.json"
MIGRATION = BACKEND / "migrations" / "20260823174500_stage38_billing_evidence_bound_activation.sql"

EXPECTED_BASE = "5ba7caa8dde7d5154b8d20da11c18274e83f41a8"
EXPECTED_BLOB = "a09aa83eb6eb24739ad0a73b7c08db3185eb4f63"
EXPECTED_MIGRATION = "stage38_billing_evidence_bound_activation"
EXPECTED_OBSERVED = "2026-08-23T17:40:52.809092+00:00"


def fail(code: str, detail: str) -> None:
    print("STAGE38_BILLING_EVIDENCE_BOUND_ACTIVATION_PROMOTION=FAIL")
    print(f"FAILURE_CLASS={code}")
    print(f"DETAIL={detail}")
    raise SystemExit(1)


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail("BGF-STAGE38-BILLING-FILE-MISSING-337", f"missing {path.relative_to(ROOT)}")
    except json.JSONDecodeError as exc:
        fail("BGF-STAGE38-BILLING-JSON-338", f"invalid JSON in {path.relative_to(ROOT)}: {exc}")
    if not isinstance(value, dict):
        fail("BGF-STAGE38-BILLING-JSON-338", f"expected object in {path.relative_to(ROOT)}")
    return value


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail("BGF-STAGE38-BILLING-FILE-MISSING-337", f"missing {path.relative_to(ROOT)}")


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def require(text: str, needle: str, code: str, detail: str) -> None:
    if needle not in text:
        fail(code, detail)


def forbid(text: str, needle: str, code: str, detail: str) -> None:
    if needle in text:
        fail(code, detail)


def bool_eq(obj: dict, key: str, expected: bool, code: str) -> None:
    if obj.get(key) is not expected:
        fail(code, f"{key} must be {expected}")


def main() -> None:
    authority = load(AUTHORITY)
    ledger = load(LEDGER)
    migration_bytes = MIGRATION.read_bytes() if MIGRATION.exists() else b""
    if not migration_bytes:
        fail("BGF-STAGE38-BILLING-FILE-MISSING-337", "Stage38 migration missing or empty")
    migration = migration_bytes.decode("utf-8")

    if authority.get("schema_version") != 1:
        fail("BGF-STAGE38-BILLING-JSON-338", "schema_version must remain 1")
    if authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("BGF-STAGE38-BILLING-PROJECT-339", "project_ref drifted")
    if authority.get("stage") != "STAGE38_BILLING_EVIDENCE_BOUND_ACTIVATION_PROMOTION":
        fail("BGF-STAGE38-BILLING-STAGE-340", "stage identifier drifted")
    if authority.get("baseline_main_sha") != EXPECTED_BASE:
        fail("BGF-STAGE38-BILLING-BASELINE-341", "baseline main SHA drifted")

    mig = authority.get("migration", {})
    if mig.get("name") != EXPECTED_MIGRATION:
        fail("BGF-STAGE38-BILLING-MIGRATION-342", "migration name drifted")
    if mig.get("git_blob_sha") != EXPECTED_BLOB:
        fail("BGF-STAGE38-BILLING-MIGRATION-342", "authority migration blob drifted")
    if git_blob_sha(migration_bytes) != EXPECTED_BLOB:
        fail("BGF-STAGE38-BILLING-MIGRATION-342", "actual migration blob differs from sealed authority")
    bool_eq(mig, "repo_only", True, "BGF-STAGE38-BILLING-MIGRATION-342")
    if mig.get("remote_apply_count") != 0:
        fail("BGF-STAGE38-BILLING-MIGRATION-342", "pre-merge remote apply count must be zero")
    bool_eq(mig, "apply_allowed_before_green_merge", False, "BGF-STAGE38-BILLING-MIGRATION-342")
    bool_eq(mig, "execute_sql_for_dml_or_ddl_allowed", False, "BGF-STAGE38-BILLING-MIGRATION-342")

    remote = authority.get("fresh_remote_preflight", {})
    if remote.get("observed_at_utc") != EXPECTED_OBSERVED:
        fail("BGF-STAGE38-BILLING-REMOTE-PREFLIGHT-343", "remote preflight timestamp drifted")
    bool_eq(remote, "stage38_remote_migration_present", False, "BGF-STAGE38-BILLING-REMOTE-PREFLIGHT-343")
    bool_eq(remote, "stage38_table_exists", False, "BGF-STAGE38-BILLING-REMOTE-PREFLIGHT-343")
    expected_selection = {
        "scope": "BR_V1",
        "provider_code": "asaas",
        "state": "selected_pending_credentials",
        "evidence_version": "2026-08-18-official-docs-v1",
        "activated_at": None,
    }
    if remote.get("selection") != expected_selection:
        fail("BGF-STAGE38-BILLING-ACTIVATION-BEFORE-CREDENTIAL-EVIDENCE-334", "remote selection is not the sealed pending state")
    for key, expected in {
        "checkout_intents": 0,
        "webhook_receipts": 0,
        "active_brl_prices": 6,
        "auth_users": 0,
        "organizations": 0,
    }.items():
        if remote.get(key) != expected:
            fail("BGF-STAGE38-BILLING-REMOTE-PREFLIGHT-343", f"{key} expected {expected}, got {remote.get(key)!r}")
    for key in ("remote_mutation_performed", "provider_called", "customer_data_used"):
        bool_eq(remote, key, False, "BGF-STAGE38-BILLING-REMOTE-PREFLIGHT-343")

    if ledger.get("baseline_main_sha") != EXPECTED_BASE:
        fail("BGF-STAGE38-BILLING-LEDGER-344", "ledger baseline must be Stage37 merged main")
    if ledger.get("observed_at_utc") != "2026-08-23T17:40:52.809092Z":
        fail("BGF-STAGE38-BILLING-LEDGER-344", "ledger observation timestamp drifted")
    divergences = ledger.get("declared_divergences")
    if not isinstance(divergences, list):
        fail("BGF-STAGE38-BILLING-LEDGER-344", "declared_divergences missing")
    repo_only = [row for row in divergences if isinstance(row, dict) and row.get("direction") == "repo_only"]
    if len(repo_only) != 1 or repo_only[0].get("name") != EXPECTED_MIGRATION:
        fail("BGF-STAGE38-BILLING-LEDGER-344", f"expected exactly one Stage38 repo-only declaration, got {repo_only!r}")
    remote_only = [row for row in divergences if isinstance(row, dict) and row.get("direction") == "remote_only"]
    if len(remote_only) != 3:
        fail("BGF-STAGE38-BILLING-LEDGER-344", "historical Stage17 remote-only count must remain three")
    remote_names = {row.get("name") for row in ledger.get("remote_migrations", []) if isinstance(row, dict)}
    if EXPECTED_MIGRATION in remote_names:
        fail("BGF-STAGE38-BILLING-LEDGER-344", "Stage38 must still be repo-only before promotion merge")

    # Evidence table is migration-owned. Runtime roles receive no DML path.
    require(migration, "create table if not exists private.billing_provider_external_evidence", "BGF-STAGE38-BILLING-RUNTIME-SELF-ATTESTATION-333", "external evidence table missing")
    require(migration, "state text not null check (state in ('credentials_verified','proof_complete'))", "BGF-STAGE38-BILLING-RUNTIME-SELF-ATTESTATION-333", "evidence lifecycle missing")
    for column in (
        "provider_account_owner_authorization_digest",
        "credential_activation_digest",
        "provider_environment_id",
        "webhook_auth_test_receipt_digest",
        "webhook_replay_receipt_digest",
        "checkout_end_to_end_receipt_digest",
        "credentials_verified_at",
        "proof_completed_at",
    ):
        require(migration, column, "BGF-STAGE38-BILLING-RUNTIME-SELF-ATTESTATION-333", f"required evidence field missing: {column}")
    require(migration, "revoke all on private.billing_provider_external_evidence from public, anon, authenticated, service_role;", "BGF-STAGE38-BILLING-RUNTIME-SELF-ATTESTATION-333", "runtime evidence-table privileges not fully revoked")
    forbid(migration.lower(), "grant insert on private.billing_provider_external_evidence", "BGF-STAGE38-BILLING-RUNTIME-SELF-ATTESTATION-333", "runtime INSERT authority appeared")
    forbid(migration.lower(), "grant update on private.billing_provider_external_evidence", "BGF-STAGE38-BILLING-RUNTIME-SELF-ATTESTATION-333", "runtime UPDATE authority appeared")
    forbid(migration.lower(), "grant delete on private.billing_provider_external_evidence", "BGF-STAGE38-BILLING-RUNTIME-SELF-ATTESTATION-333", "runtime DELETE authority appeared")
    forbid(migration.lower(), "insert into private.billing_provider_external_evidence", "BGF-STAGE38-BILLING-RUNTIME-SELF-ATTESTATION-333", "hardening migration must not self-attest external evidence")
    forbid(migration.lower(), "update private.billing_provider_external_evidence", "BGF-STAGE38-BILLING-RUNTIME-SELF-ATTESTATION-333", "hardening migration must not promote external evidence")

    activation = re.search(
        r"create or replace function public\.activate_billing_provider_selection\(.*?\n\$\$;",
        migration,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if activation is None:
        fail("BGF-STAGE38-BILLING-ACTIVATION-BEFORE-CREDENTIAL-EVIDENCE-334", "hardened activation function missing")
    activation_text = activation.group(0)
    for needle in (
        "private.billing_provider_external_evidence",
        "e.scope = v_selection.scope",
        "e.provider_code = v_selection.provider_code",
        "e.evidence_version = v_selection.evidence_version",
        "v_external_evidence.state not in ('credentials_verified','proof_complete')",
        "BILLING_PROVIDER_EXTERNAL_CREDENTIAL_EVIDENCE_REQUIRED",
        "state = 'active'",
        "activated_at = coalesce(activated_at, now())",
    ):
        require(activation_text, needle, "BGF-STAGE38-BILLING-ACTIVATION-BEFORE-CREDENTIAL-EVIDENCE-334", f"activation evidence interlock missing: {needle}")
    require(migration, "revoke execute on function public.activate_billing_provider_selection(text,text,text) from public, anon, authenticated;", "BGF-STAGE38-BILLING-ACTIVATION-BEFORE-CREDENTIAL-EVIDENCE-334", "normal clients can execute activation")
    require(migration, "grant execute on function public.activate_billing_provider_selection(text,text,text) to service_role;", "BGF-STAGE38-BILLING-ACTIVATION-BEFORE-CREDENTIAL-EVIDENCE-334", "service activation authority missing")

    readiness = re.search(
        r"create or replace function private\.get_controlled_launch_readiness_authority\(\).*?\n\$\$;",
        migration,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if readiness is None:
        fail("BGF-STAGE38-BILLING-LAUNCH-BEFORE-PROOF-COMPLETE-335", "hardened launch readiness function missing")
    readiness_text = readiness.group(0)
    for needle in (
        "join private.billing_provider_external_evidence e",
        "s.scope='BR_V1'",
        "s.provider_code='asaas'",
        "s.state='active'",
        "s.activated_at is not null",
        "e.state='proof_complete'",
        "e.provider_account_owner_authorization_digest",
        "e.credential_activation_digest",
        "e.webhook_auth_test_receipt_digest",
        "e.webhook_replay_receipt_digest",
        "e.checkout_end_to_end_receipt_digest",
        "e.credentials_verified_at is not null",
        "e.proof_completed_at is not null",
        "'external_billing_launch_evidence_required',true",
        "'paid_ads_auto_launch',false",
    ):
        require(readiness_text, needle, "BGF-STAGE38-BILLING-LAUNCH-BEFORE-PROOF-COMPLETE-335", f"launch proof-complete interlock missing: {needle}")

    design = authority.get("evidence_authority_design", {})
    if design.get("runtime_dml_authority") != "DENIED_ALL_RUNTIME_ROLES":
        fail("BGF-STAGE38-BILLING-RUNTIME-SELF-ATTESTATION-333", "authority no longer denies runtime DML")
    if design.get("evidence_write_authority") != "DEDICATED_VERSIONED_MIGRATION_ONLY":
        fail("BGF-STAGE38-BILLING-RUNTIME-SELF-ATTESTATION-333", "evidence write authority drifted")
    bool_eq(design, "secret_values_allowed", False, "BGF-STAGE38-BILLING-EVIDENCE-SECRET-LEAK-336")

    boundaries = authority.get("promotion_boundaries", {})
    for key in (
        "provider_activation_performed",
        "provider_call_performed",
        "external_evidence_row_inserted",
        "external_evidence_row_updated",
        "customer_data_used",
        "credential_secret_recorded",
        "billing_gate_promoted",
        "launch_gate_promoted",
        "paid_media_allowed",
        "stage35_proof_reexecution_allowed",
    ):
        bool_eq(boundaries, key, False, "BGF-STAGE38-BILLING-GATE-CROSSOVER-345")

    gates = authority.get("gates", {})
    if gates.get("stage38_repository_promotion") != "PENDING_CI":
        fail("BGF-STAGE38-BILLING-GATE-CROSSOVER-345", "repository promotion must remain pending CI in candidate authority")
    if gates.get("stage38_remote_apply") != "DENIED_UNTIL_GREEN_MERGE":
        fail("BGF-STAGE38-BILLING-GATE-CROSSOVER-345", "remote apply boundary drifted")
    for key in ("billing_provider_credentials", "controlled_launch", "production_deployment", "incident_response", "paid_media", "launch"):
        if gates.get(key) != "DENIED":
            fail("BGF-STAGE38-BILLING-GATE-CROSSOVER-345", f"{key} must remain DENIED")

    serialized = json.dumps(authority, sort_keys=True).lower()
    for forbidden_key in ('"api_key"', '"access_token"', '"password"', '"webhook_token"', '"credential_secret_value"'):
        if forbidden_key in serialized:
            fail("BGF-STAGE38-BILLING-EVIDENCE-SECRET-LEAK-336", f"secret-bearing key found: {forbidden_key}")

    print("STAGE38_BILLING_EVIDENCE_BOUND_ACTIVATION_PROMOTION=PASS")
    print(f"MIGRATION_BLOB={EXPECTED_BLOB}")
    print("MIGRATION_STATE=REPO_ONLY")
    print("EXTERNAL_EVIDENCE_RUNTIME_DML=DENIED")
    print("ACTIVATION_REQUIRES_CREDENTIAL_EVIDENCE=PASS")
    print("LAUNCH_BILLING_REQUIRES_PROOF_COMPLETE=PASS")
    print("PROVIDER_ACTIVATION=NOT_PERFORMED")
    print("PROVIDER_CALL=NOT_PERFORMED")
    print("BILLING_GATE_PROMOTION=DENIED")
    print("REMOTE_APPLY=DENIED_UNTIL_GREEN_MERGE")


if __name__ == "__main__":
    main()
