from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
MIGRATIONS = BACKEND / "migrations"
AUTHORITY = BACKEND / "stage37_billing_external_authority_preparation.json"
BASE = MIGRATIONS / "20260818225500_stage16_billing_provider_gate.sql"
HARDENING = MIGRATIONS / "20260818230000_stage16_billing_authority_hardening.sql"
CHECKOUT = MIGRATIONS / "20260819051500_stage17_checkout_authority_private_bridge.sql"
LAUNCH = MIGRATIONS / "20260819062000_stage20_controlled_launch_admission.sql"
PLACEHOLDERS = BACKEND / "external_gate_evidence_placeholders.json"
STAGE36 = BACKEND / "stage36_controlled_launch_external_gate_assessment_authority.json"

EXPECTED_MAIN = "6a9a96c77ade7f350c95b1fb1008127809de3904"
EXPECTED_OBSERVED = "2026-08-23T17:35:12.046993+00:00"
EXPECTED_EVIDENCE_VERSION = "2026-08-18-official-docs-v1"


def fail(code: str, detail: str) -> None:
    print("STAGE37_BILLING_EXTERNAL_AUTHORITY_PREPARATION=FAIL")
    print(f"FAILURE_CLASS={code}")
    print(f"DETAIL={detail}")
    raise SystemExit(1)


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail("BGF-STAGE37-BILLING-PREP-FILE-MISSING-325", f"missing {path.relative_to(ROOT)}")
    except json.JSONDecodeError as exc:
        fail("BGF-STAGE37-BILLING-PREP-JSON-326", f"invalid JSON in {path.relative_to(ROOT)}: {exc}")
    if not isinstance(value, dict):
        fail("BGF-STAGE37-BILLING-PREP-JSON-326", f"expected object in {path.relative_to(ROOT)}")
    return value


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail("BGF-STAGE37-BILLING-PREP-FILE-MISSING-325", f"missing {path.relative_to(ROOT)}")


def require(text: str, needle: str, code: str, detail: str) -> None:
    if needle not in text:
        fail(code, detail)


def forbid(text: str, needle: str, code: str, detail: str) -> None:
    if needle in text:
        fail(code, detail)


def require_bool(obj: dict, key: str, expected: bool, code: str) -> None:
    if obj.get(key) is not expected:
        fail(code, f"{key} must be {expected}")


def main() -> None:
    authority = load_json(AUTHORITY)
    base = read(BASE)
    hardening = read(HARDENING)
    checkout = read(CHECKOUT)
    launch = read(LAUNCH)
    placeholders = load_json(PLACEHOLDERS)
    stage36 = load_json(STAGE36)

    if authority.get("schema_version") != 1:
        fail("BGF-STAGE37-BILLING-PREP-JSON-326", "schema_version must remain 1")
    if authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("BGF-STAGE37-BILLING-PREP-PROJECT-327", "project_ref drifted")
    if authority.get("stage") != "STAGE37_BILLING_EXTERNAL_AUTHORITY_PREPARATION":
        fail("BGF-STAGE37-BILLING-PREP-STAGE-328", "stage identifier drifted")
    if authority.get("baseline_main_sha") != EXPECTED_MAIN:
        fail("BGF-STAGE37-BILLING-PREP-BASELINE-329", "baseline main SHA drifted")
    if authority.get("current_state") != (
        "PREPARED_EXTERNAL_ACTION_REQUIRED_INTERNAL_ACTIVATION_NOT_EXTERNAL_EVIDENCE_BOUND_NO_PROMOTION"
    ):
        fail("BGF-STAGE37-BILLING-EVIDENCE-BINDING-GAP-320", "current_state hides the evidence-binding gap")

    remote = authority.get("fresh_remote_assessment")
    if not isinstance(remote, dict):
        fail("BGF-STAGE37-BILLING-PREP-REMOTE-330", "fresh_remote_assessment missing")
    if remote.get("observed_at_utc") != EXPECTED_OBSERVED:
        fail("BGF-STAGE37-BILLING-PREP-REMOTE-330", "remote observation timestamp drifted")
    selection = remote.get("selection")
    expected_selection = {
        "scope": "BR_V1",
        "provider_code": "asaas",
        "state": "selected_pending_credentials",
        "evidence_version": EXPECTED_EVIDENCE_VERSION,
        "activated_at": None,
    }
    if selection != expected_selection:
        fail("BGF-STAGE37-BILLING-PREMATURE-ACTIVATION-319", f"unexpected remote selection: {selection!r}")
    for key, value in {
        "checkout_intents": 0,
        "webhook_receipts": 0,
        "active_brl_prices": 6,
        "organizations": 0,
        "auth_users": 0,
    }.items():
        if remote.get(key) != value:
            fail("BGF-STAGE37-BILLING-PREP-REMOTE-330", f"{key} expected {value}, got {remote.get(key)!r}")
    for key in (
        "service_direct_selection_update",
        "service_direct_checkout_update",
        "service_direct_webhook_insert",
        "remote_mutation_performed",
        "provider_called",
        "customer_data_used",
    ):
        require_bool(remote, key, False, "BGF-STAGE37-BILLING-PREP-REMOTE-330")

    privileges = remote.get("service_command_privileges")
    if not isinstance(privileges, dict) or set(privileges) != {
        "activate_billing_provider_selection",
        "attach_billing_provider_checkout",
        "record_billing_webhook_receipt",
        "mark_billing_webhook_receipt",
    }:
        fail("BGF-STAGE37-BILLING-PREP-PRIVILEGE-331", "service command privilege inventory drifted")
    for name, row in privileges.items():
        if row != {"anon": False, "authenticated": False, "service_role": True}:
            fail("BGF-STAGE37-BILLING-PREP-PRIVILEGE-331", f"unexpected privileges for {name}: {row!r}")

    require(base, "'BR_V1',\n  'asaas',\n  'selected_pending_credentials'", "BGF-STAGE37-BILLING-PREMATURE-ACTIVATION-319", "Asaas selection no longer starts pending")
    require(base, EXPECTED_EVIDENCE_VERSION, "BGF-STAGE37-BILLING-EVIDENCE-BINDING-GAP-320", "billing evidence version disappeared")
    require(base, "BILLING_PROVIDER_CREDENTIALS_NOT_READY", "BGF-STAGE37-BILLING-PREMATURE-ACTIVATION-319", "checkout no longer blocks before activation")
    require(base, "idempotency_key uuid not null unique", "BGF-STAGE37-BILLING-CHECKOUT-PROOF-MISSING-322", "checkout idempotency constraint missing")
    require(base, "unique (provider_code, provider_event_id)", "BGF-STAGE37-BILLING-WEBHOOK-PROOF-MISSING-321", "webhook replay constraint missing")
    require(base, "auth_verified boolean not null check (auth_verified)", "BGF-STAGE37-BILLING-WEBHOOK-PROOF-MISSING-321", "webhook auth storage constraint missing")

    activation = re.search(
        r"create or replace function public\.activate_billing_provider_selection\(.*?\n\$\$;",
        hardening,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if activation is None:
        fail("BGF-STAGE37-BILLING-PREP-CONTRACT-332", "activation function not found")
    activation_text = activation.group(0)
    for needle in (
        "SILENT_PROVIDER_FALLBACK_FORBIDDEN",
        "BILLING_PROVIDER_EVIDENCE_VERSION_MISMATCH",
        "state = 'active'",
        "activated_at = coalesce(activated_at, now())",
    ):
        require(activation_text, needle, "BGF-STAGE37-BILLING-PREP-CONTRACT-332", f"activation contract lost {needle}")
    # This absence is intentionally documented as a blocker: current activation checks an
    # internal evidence-version string but does not bind external proof receipts.
    for forbidden in ("billing_webhook_receipts", "billing_checkout_intents", "provider_event_id", "payload_sha256"):
        forbid(activation_text, forbidden, "BGF-STAGE37-BILLING-EVIDENCE-BINDING-GAP-320", "authority claim no longer matches the observed activation contract")

    for signature in (
        "public.activate_billing_provider_selection(text,text,text)",
        "public.attach_billing_provider_checkout(uuid,text,text,timestamptz)",
        "public.record_billing_webhook_receipt(text,text,text,text,boolean,uuid,text)",
        "public.mark_billing_webhook_receipt(text,text,text,uuid,text)",
    ):
        require(hardening, f"revoke execute on function {signature} from public, anon, authenticated;", "BGF-STAGE37-BILLING-PREP-PRIVILEGE-331", f"normal-client denial missing for {signature}")
        require(hardening, f"grant execute on function {signature} to service_role;", "BGF-STAGE37-BILLING-PREP-PRIVILEGE-331", f"service authority missing for {signature}")

    require(hardening, "WEBHOOK_AUTH_NOT_VERIFIED", "BGF-STAGE37-BILLING-WEBHOOK-PROOF-MISSING-321", "webhook auth fail-closed guard missing")
    require(hardening, "on conflict (provider_code, provider_event_id) do nothing", "BGF-STAGE37-BILLING-WEBHOOK-PROOF-MISSING-321", "webhook replay idempotency implementation missing")
    require(hardening, "BILLING_PROVIDER_AUTHORITY_NOT_ACTIVE", "BGF-STAGE37-BILLING-CHECKOUT-PROOF-MISSING-322", "provider checkout attachment no longer requires active authority")
    require(checkout, "BILLING_PROVIDER_CREDENTIALS_NOT_READY", "BGF-STAGE37-BILLING-PREMATURE-ACTIVATION-319", "private checkout authority no longer blocks pending credentials")

    require(launch, "s.provider_code='asaas'", "BGF-STAGE37-BILLING-GATE-CROSS-PROMOTION-324", "Stage20 billing gate provider drifted")
    require(launch, "s.state='active'", "BGF-STAGE37-BILLING-EVIDENCE-BINDING-GAP-320", "Stage20 billing gate no longer depends on active state")
    require(launch, "s.activated_at is not null", "BGF-STAGE37-BILLING-EVIDENCE-BINDING-GAP-320", "Stage20 billing gate no longer depends on activation timestamp")

    billing_placeholder = placeholders.get("gates", {}).get("billing_provider_credentials", {})
    required = billing_placeholder.get("required_evidence")
    if not isinstance(required, list):
        fail("BGF-STAGE37-BILLING-EVIDENCE-BINDING-GAP-320", "billing external evidence list missing")
    for item in (
        "provider account owner authorization",
        "credential activation evidence without committing secrets",
        "provider environment identifier",
        "webhook authentication and replay/idempotency test receipt",
        "checkout end-to-end receipt",
        "activation timestamp from authoritative billing state",
    ):
        if item not in required:
            fail("BGF-STAGE37-BILLING-EVIDENCE-BINDING-GAP-320", f"required external evidence disappeared: {item}")

    if stage36.get("gates", {}).get("billing_provider_credentials") != "DENIED":
        fail("BGF-STAGE37-BILLING-GATE-CROSS-PROMOTION-324", "Stage36 billing gate was unexpectedly promoted")

    gap = authority.get("evidence_binding_gap")
    if not isinstance(gap, dict) or gap.get("present") is not True:
        fail("BGF-STAGE37-BILLING-EVIDENCE-BINDING-GAP-320", "authority must explicitly acknowledge the activation/evidence gap")
    for key in (
        "activation_command_verifies_provider_credentials_directly",
        "activation_command_requires_webhook_auth_test_receipt",
        "activation_command_requires_webhook_replay_idempotency_receipt",
        "activation_command_requires_checkout_end_to_end_receipt",
    ):
        require_bool(gap, key, False, "BGF-STAGE37-BILLING-EVIDENCE-BINDING-GAP-320")
    require_bool(gap, "stage20_billing_gate_becomes_ready_from_active_state_and_activated_at", True, "BGF-STAGE37-BILLING-EVIDENCE-BINDING-GAP-320")
    require_bool(gap, "placeholder_requires_more_evidence_than_stage20_runtime_predicate", True, "BGF-STAGE37-BILLING-EVIDENCE-BINDING-GAP-320")

    boundaries = authority.get("stage37_boundaries")
    if not isinstance(boundaries, dict):
        fail("BGF-STAGE37-BILLING-GATE-CROSS-PROMOTION-324", "Stage37 boundaries missing")
    require_bool(boundaries, "repo_only", True, "BGF-STAGE37-BILLING-GATE-CROSS-PROMOTION-324")
    require_bool(boundaries, "read_only_remote_assessment", True, "BGF-STAGE37-BILLING-GATE-CROSS-PROMOTION-324")
    for key in (
        "migration_added",
        "supabase_mutation_allowed",
        "provider_call_allowed",
        "provider_activation_allowed",
        "credential_value_recording_allowed",
        "secret_value_recording_allowed",
        "customer_data_allowed",
        "billing_gate_promotion_allowed",
        "launch_gate_promotion_allowed",
        "paid_media_allowed",
        "stage35_proof_reexecution_allowed",
    ):
        require_bool(boundaries, key, False, "BGF-STAGE37-BILLING-GATE-CROSS-PROMOTION-324")

    if list(MIGRATIONS.glob("*stage37*")):
        fail("BGF-STAGE37-BILLING-GATE-CROSS-PROMOTION-324", "Stage37 preparation must not add a migration")

    serialized = json.dumps(authority, sort_keys=True).lower()
    for forbidden_key in ('"api_key"', '"access_token"', '"password"', '"webhook_token"', '"credential_secret"'):
        if forbidden_key in serialized:
            fail("BGF-STAGE37-BILLING-SECRET-LEAK-323", f"secret-bearing key found: {forbidden_key}")

    gates = authority.get("gates", {})
    expected_gates = {
        "billing_provider_credentials": "DENIED_PREPARED_EXTERNAL_ACTION_REQUIRED",
        "controlled_launch": "DENIED",
        "production_deployment": "DENIED",
        "incident_response": "DENIED",
        "paid_media": "DENIED",
        "launch": "DENIED",
    }
    if gates != expected_gates:
        fail("BGF-STAGE37-BILLING-GATE-CROSS-PROMOTION-324", f"gate boundary drifted: {gates!r}")

    next_stage = authority.get("next_stage", {})
    if next_stage.get("name") != "STAGE38_BILLING_EVIDENCE_BOUND_ACTIVATION_CONTRACT":
        fail("BGF-STAGE37-BILLING-EVIDENCE-BINDING-GAP-320", "next stage must close evidence-bound activation")
    for key in ("may_activate_provider_now", "may_call_provider_now", "may_promote_billing_gate_now"):
        require_bool(next_stage, key, False, "BGF-STAGE37-BILLING-PREMATURE-ACTIVATION-319")

    print("STAGE37_BILLING_EXTERNAL_AUTHORITY_PREPARATION=PASS")
    print("REMOTE_SELECTION=ASAAS_SELECTED_PENDING_CREDENTIALS")
    print("REMOTE_ACTIVATED_AT=NULL")
    print("CHECKOUT_INTENTS=0")
    print("WEBHOOK_RECEIPTS=0")
    print("SERVICE_DIRECT_BILLING_MUTATION=DENIED")
    print("SERVICE_COMMANDS=SERVICE_ROLE_ONLY")
    print("EXTERNAL_EVIDENCE_BINDING_GAP=CONFIRMED_BLOCKER")
    print("PROVIDER_ACTIVATION=DENIED")
    print("PROVIDER_CALL=DENIED")
    print("BILLING_GATE_PROMOTION=DENIED")
    print("NEXT_STAGE=STAGE38_BILLING_EVIDENCE_BOUND_ACTIVATION_CONTRACT")


if __name__ == "__main__":
    main()
