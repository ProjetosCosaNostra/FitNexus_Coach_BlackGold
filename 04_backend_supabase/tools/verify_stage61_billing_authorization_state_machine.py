from __future__ import annotations

import hashlib
import json
from pathlib import Path

from stage61_billing_authorization_state_machine import (
    ORDERED_CLAIMS,
    PROTOCOL,
    STATES,
    authority_flags,
    evaluate,
)

FAILURE_CLASS = "BGF-STAGE61-AUTHORIZATION-STATE-MACHINE-GUARD-594"
ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage61_billing_authorization_state_machine_authority.json"
EVALUATOR = BACKEND / "tools/stage61_billing_authorization_state_machine.py"
MIGRATIONS = BACKEND / "migrations"

EXPECTED_BASELINE = "47fe740eb087c3e27a2269120f6801f3dc6a40e0"
EXPECTED_STATE = "AUTHORIZATION_STATE_MACHINE_PREPARED_REMOTE_UNCHANGED_NO_EXTERNAL_EVIDENCE"
EXPECTED_SEALED = {
    "stage54_credentials_evidence_promotion_boundary": (
        "04_backend_supabase/stage54_billing_external_evidence_promotion_boundary_authority.json",
        "05c99cdc785bcd8872b51773078a8c97b56675af",
    ),
    "stage56_proof_complete_promotion_boundary": (
        "04_backend_supabase/stage56_billing_proof_complete_promotion_boundary_authority.json",
        "4822ad8f32aa7154c851b15a79804698388c8311",
    ),
    "stage58_controlled_proof_intake": (
        "04_backend_supabase/stage58_billing_controlled_proof_intake_preparation_authority.json",
        "0990c03db4f60f0f7252c74527d064442822c7e3",
    ),
    "stage59_independent_proof_review": (
        "04_backend_supabase/stage59_billing_proof_independent_review_preparation_authority.json",
        "7da5bc11b15d0813f77a00b2fd5e19f7a72ee4ca",
    ),
    "stage60_final_reconciliation": (
        "04_backend_supabase/stage60_stage59_final_reconciliation_authority.json",
        "9a35ec73bdcfea91e51c4c4dcd68b4b8032ca159",
    ),
}
EXPECTED_FUNCTIONS = {
    "activate_billing_provider_selection": {
        "identity_args": "p_scope text, p_provider_code text, p_evidence_version text",
        "security_definer": True,
        "service_role_execute": True,
        "authenticated_execute": False,
        "anon_execute": False,
        "definition_sha256": "d1ce2db8809c6b4fa66a7018b54baa05725ee97b14508080a5f52f0894400e7c",
    },
    "create_billing_checkout_intent": {
        "identity_args": "p_organization_id uuid, p_plan_code text, p_billing_interval text, p_idempotency_key uuid",
        "security_definer": False,
        "service_role_execute": False,
        "authenticated_execute": True,
        "anon_execute": False,
        "definition_sha256": "341a9fee068212dae3212b953615674b9a018f8254516ec50baee4816152c80d",
    },
    "attach_billing_provider_checkout": {
        "identity_args": "p_checkout_intent_id uuid, p_provider_checkout_ref text, p_checkout_url text, p_expires_at timestamp with time zone",
        "security_definer": True,
        "service_role_execute": True,
        "authenticated_execute": False,
        "anon_execute": False,
        "definition_sha256": "30a45ec42e2e50570fb75609f4e4fd2be67619e8b9d12edbda71c5b25a72d88c",
    },
    "record_billing_webhook_receipt": {
        "identity_args": "p_provider_code text, p_provider_event_id text, p_event_type text, p_payload_sha256 text, p_auth_verified boolean, p_organization_id uuid, p_provider_subscription_ref text",
        "security_definer": True,
        "service_role_execute": True,
        "authenticated_execute": False,
        "anon_execute": False,
        "definition_sha256": "2a609c89e954c8bc334219e52e1f197bca00228bccdbaf1ce4115e4a34374e44",
    },
    "mark_billing_webhook_receipt": {
        "identity_args": "p_provider_code text, p_provider_event_id text, p_processing_status text, p_organization_id uuid, p_provider_subscription_ref text",
        "security_definer": True,
        "service_role_execute": True,
        "authenticated_execute": False,
        "anon_execute": False,
        "definition_sha256": "07fad48fd549366cf95aa206fdb3e83f98cab3e0b3038a42703b6259dfbf2e9f",
    },
}
EXPECTED_FAILURE_CLASSES = {
    "BGF-STAGE61-OUT-OF-ORDER-AUTHORIZATION-CLAIM-583",
    "BGF-STAGE61-MULTI-TRANSITION-COLLAPSE-584",
    "BGF-STAGE61-STRUCTURAL-STATE-AS-REMOTE-AUTHORITY-585",
    "BGF-STAGE61-CONTINUATION-AS-PROVIDER-AUTHORIZATION-586",
    "BGF-STAGE61-CREDENTIAL-APPLY-ACTIVATION-BUNDLE-587",
    "BGF-STAGE61-ACTIVATION-PROOF-BUNDLE-588",
    "BGF-STAGE61-PROOF-CLEANUP-CONFLATION-589",
    "BGF-STAGE61-REVIEW-APPLY-BUNDLE-590",
    "BGF-STAGE61-REMOTE-BOUNDARY-DRIFT-591",
    "BGF-STAGE61-SEALED-AUTHORITY-DRIFT-592",
    "BGF-STAGE61-FALSE-BILLING-READY-593",
    "BGF-STAGE61-AUTHORIZATION-STATE-MACHINE-GUARD-594",
}


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE61_BILLING_AUTHORIZATION_STATE_MACHINE=FAIL\n"
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


def verify_remote_snapshot(authority: dict) -> None:
    remote = authority.get("fresh_remote_read_only_snapshot")
    if not isinstance(remote, dict):
        fail("fresh remote snapshot missing")
    expected = {
        "observed_at_utc": "2026-08-25T09:35:31.698457+00:00",
        "read_only": True,
        "remote_mutation_performed": False,
        "billing_external_evidence_total": 0,
        "credentials_verified_rows": 0,
        "proof_complete_rows": 0,
        "checkout_intents": 0,
        "webhook_receipts": 0,
        "evidence_migration_ready_rows": 0,
    }
    for key, value in expected.items():
        if remote.get(key) != value:
            fail(f"remote snapshot drift: {key}")
    if remote.get("billing_selection") != {
        "scope": "BR_V1",
        "provider_code": "asaas",
        "state": "selected_pending_credentials",
        "evidence_version": "2026-08-18-official-docs-v1",
        "activated_at": None,
    }:
        fail("billing selection snapshot drift")


def verify_function_boundary(authority: dict) -> None:
    boundary = authority.get("fresh_runtime_function_boundary")
    if not isinstance(boundary, dict):
        fail("runtime function boundary missing")
    if boundary.get("observed_at_utc") != "2026-08-25T09:36:31.98135+00:00" or boundary.get("read_only") is not True:
        fail("runtime boundary timestamp/read-only drift")
    functions = boundary.get("functions")
    if functions != EXPECTED_FUNCTIONS:
        fail("runtime function hashes or grants drift")


def verify_sealed_inputs(authority: dict) -> None:
    sealed = authority.get("sealed_inputs")
    if not isinstance(sealed, dict) or set(sealed) != set(EXPECTED_SEALED):
        fail("sealed input registry drift")
    for label, (rel, expected_blob) in EXPECTED_SEALED.items():
        entry = sealed[label]
        path = ROOT / rel
        if entry != {"path": rel, "git_blob_sha": expected_blob}:
            fail(f"sealed input declaration drift: {label}")
        if not path.is_file() or git_blob_sha(path) != expected_blob:
            fail(f"sealed input bytes drift: {label}")


def verify_state_machine(authority: dict) -> None:
    machine = authority.get("state_machine")
    if not isinstance(machine, dict):
        fail("state machine missing")
    exact = {
        "protocol": PROTOCOL,
        "scope": "BR_V1",
        "provider_code": "asaas",
        "evidence_version": "2026-08-18-official-docs-v1",
        "provider_environment_id": "asaas-production",
        "ordered_claims": list(ORDERED_CLAIMS),
        "current_structural_index": 0,
        "current_structural_state": STATES[0],
    }
    for key, expected in exact.items():
        if machine.get(key) != expected:
            fail(f"state machine drift: {key}")

    states = machine.get("states")
    expected_states = [{"index": i, "code": code} for i, code in enumerate(STATES)]
    if states != expected_states:
        fail("state registry drift")

    for key in (
        "truth_validation_is_external_to_evaluator",
        "later_claim_without_all_prior_claims_is_invalid",
    ):
        if machine.get(key) is not True:
            fail(f"required fail-closed state-machine rule disabled: {key}")

    for key in (
        "state_evaluator_output_is_authorization",
        "state_evaluator_output_is_remote_apply_authority",
        "state_evaluator_output_is_provider_call_authority",
        "state_evaluator_output_is_launch_authority",
        "one_chat_continuation_command_can_satisfy_external_authorization",
        "single_action_may_collapse_multiple_remote_side_effect_transitions",
        "credentials_evidence_apply_and_provider_activation_may_be_bundled",
        "provider_activation_and_controlled_proof_may_be_bundled",
        "controlled_proof_and_cleanup_may_be_treated_as_same_receipt",
        "independent_review_and_proof_complete_apply_may_be_bundled",
        "proof_complete_confirmation_is_controlled_launch_authority",
    ):
        if machine.get(key) is not False:
            fail(f"forbidden collapsed authority enabled: {key}")


def verify_evaluator_negative_controls() -> None:
    empty = {claim: False for claim in ORDERED_CLAIMS}
    result = evaluate(empty)
    if result.get("evaluation_state") != "STRUCTURALLY_ORDERED_NOT_TRUTH_VERIFIED":
        fail("empty claim set did not remain structurally ordered")
    if result.get("structural_state_index") != 0 or result.get("structural_state") != STATES[0]:
        fail("empty claim set did not remain at initial state")
    if result.get("next_required_claim") != ORDERED_CLAIMS[0]:
        fail("initial next-required claim drift")
    if result.get("truth_verified") is not False or result.get("structural_only") is not True:
        fail("evaluator falsely verifies truth")
    if result.get("authority_flags") != authority_flags() or any(result["authority_flags"].values()):
        fail("evaluator emitted authority")

    first_only = dict(empty)
    first_only[ORDERED_CLAIMS[0]] = True
    result = evaluate(first_only)
    if result.get("structural_state_index") != 1 or result.get("structural_state") != STATES[1]:
        fail("single ordered claim did not advance exactly one structural state")

    skipped = dict(empty)
    skipped[ORDERED_CLAIMS[1]] = True
    result = evaluate(skipped)
    if result.get("evaluation_state") != "INVALID_OUT_OF_ORDER_CLAIM":
        fail("out-of-order claim was accepted")
    if ORDERED_CLAIMS[1] not in result.get("out_of_order_claims", []):
        fail("out-of-order claim not reported")
    if any(result.get("authority_flags", {}).values()):
        fail("invalid sequence emitted authority")

    complete = {claim: True for claim in ORDERED_CLAIMS}
    result = evaluate(complete)
    if result.get("structural_state_index") != len(ORDERED_CLAIMS) or result.get("structural_state") != STATES[-1]:
        fail("complete structural claims did not reach terminal reassessment state")
    if result.get("truth_verified") is not False or any(result.get("authority_flags", {}).values()):
        fail("terminal structural state falsely became authority")


def verify_no_side_effect_surface() -> None:
    source = EVALUATOR.read_text(encoding="utf-8")
    forbidden = (
        "import requests",
        "from requests",
        "import httpx",
        "from httpx",
        "import urllib",
        "from urllib",
        "import socket",
        "from socket",
        "import subprocess",
        "from subprocess",
        "import psycopg",
        "from psycopg",
        "import supabase",
        "from supabase",
        "apply_migration(",
        "execute_sql(",
    )
    lowered = source.lower()
    for token in forbidden:
        if token.lower() in lowered:
            fail(f"state evaluator gained side-effect/network surface: {token}")
    for marker in (
        '"provider_call_authorized": False',
        '"provider_activation_authorized": False',
        '"supabase_mutation_authorized": False',
        '"migration_apply_authorized": False',
        '"controlled_launch_authorized": False',
        '"launch_authorized": False',
    ):
        if marker not in source:
            fail(f"evaluator authority-denial marker missing: {marker}")


def main() -> None:
    authority = load_authority()
    expected_top = {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE61_BILLING_AUTHORIZATION_STATE_MACHINE",
        "baseline_main_sha": EXPECTED_BASELINE,
        "current_state": EXPECTED_STATE,
    }
    for key, expected in expected_top.items():
        if authority.get(key) != expected:
            fail(f"authority drift: {key}")

    verify_remote_snapshot(authority)
    verify_function_boundary(authority)
    verify_sealed_inputs(authority)
    verify_state_machine(authority)
    verify_evaluator_negative_controls()
    verify_no_side_effect_surface()

    transition_authorities = authority.get("transition_authorities")
    if not isinstance(transition_authorities, dict) or set(transition_authorities) != {
        "credentials_evidence",
        "provider_activation",
        "controlled_proof",
        "proof_receipt_intake",
        "proof_independent_review",
        "proof_complete_promotion",
        "controlled_launch",
    }:
        fail("transition authority registry drift")

    forbidden_actions = authority.get("stage61_forbidden_actions")
    if not isinstance(forbidden_actions, dict) or not forbidden_actions or any(value is not True for value in forbidden_actions.values()):
        fail("Stage61 forbidden action registry weakened")

    if set(authority.get("failure_classes", [])) != EXPECTED_FAILURE_CLASSES:
        fail("Stage61 failure-class registry drift")

    gates = authority.get("gates")
    if not isinstance(gates, dict) or gates.get("stage61_state_machine") != "REPO_ONLY_PENDING_CI":
        fail("Stage61 gate state drift")
    for gate, value in gates.items():
        if gate == "stage61_state_machine":
            continue
        if not str(value).startswith("DENIED"):
            fail(f"Stage61 cannot promote gate: {gate}")

    if list(MIGRATIONS.glob("*stage61*.sql")):
        fail("Stage61 is repository-only and must not add a migration")

    print("STAGE61_BILLING_AUTHORIZATION_STATE_MACHINE=PASS")
    print("CURRENT_STRUCTURAL_STATE=AWAITING_REAL_OPERATOR_CREDENTIAL_EVIDENCE")
    print("STATE_MACHINE_TRUTH_VERIFIED=false")
    print("PROVIDER_CALL=DENIED")
    print("PROVIDER_ACTIVATION=DENIED")
    print("CONTROLLED_PROOF=DENIED")
    print("PROOF_COMPLETE=DENIED")
    print("CONTROLLED_LAUNCH=DENIED")
    print("REMOTE_MUTATION=false")


if __name__ == "__main__":
    main()
