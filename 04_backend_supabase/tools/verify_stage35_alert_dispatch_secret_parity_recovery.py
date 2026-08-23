from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage35_alert_dispatch_secret_parity_recovery_authority.json"
WORKFLOW = ROOT / ".github" / "workflows" / "stage35_alert_dispatch_secret_parity_recovery.yml"
V5 = BACKEND / "tools" / "Invoke-Stage35AlertSecretBootstrapV5.ps1"
V5_GUARD = BACKEND / "tools" / "verify_stage35_alert_secret_bootstrap_v5.py"
DISPATCHER = BACKEND / "functions" / "student-access-alert-dispatcher" / "index.ts"

BASELINE = "8b9216260aa26933aea18db84d4a641e6914d301"
FAILED_PR = 112
FAILED_RUN = 32647288419
FAILED_JOB = 97213360238
PROOF_MARKER = "fitnexus-stage34-alert-delivery-proof-v1"
RECOVERY_BRANCH = "blackgold/stage35-dispatch-secret-parity-recovery-trigger"
RECOVERY_TRIGGER = "04_backend_supabase/stage35_alert_dispatch_secret_parity_recovery_trigger.json"


def fail(message: str) -> None:
    raise SystemExit("STAGE35_ALERT_DISPATCH_SECRET_PARITY_RECOVERY_GUARD=FAIL\n" + message)


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"unable to read {path.relative_to(ROOT)}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"expected JSON object: {path.relative_to(ROOT)}")
    return value


def require(mapping: dict, expected: dict, label: str) -> None:
    if not isinstance(mapping, dict):
        fail(f"{label} must be an object")
    for key, value in expected.items():
        if mapping.get(key) != value:
            fail(f"{label} drift: {key}")


def main() -> None:
    authority = load(AUTHORITY)
    workflow = WORKFLOW.read_text(encoding="utf-8")
    v5 = V5.read_text(encoding="utf-8")
    v5_guard = V5_GUARD.read_text(encoding="utf-8")
    dispatcher = DISPATCHER.read_text(encoding="utf-8")

    require(authority, {
        "schema_version": 1,
        "project_ref": "mceukeondizkwlpfxzgf",
        "stage": "STAGE35_ALERT_DISPATCH_SECRET_PARITY_RECOVERY",
        "baseline_main_sha": BASELINE,
        "current_state": "PARITY_RECOVERY_SEALED_FAILED_PROOF_FROZEN_NO_PROVIDER_CALL",
    }, "recovery authority")
    if set(authority.get("failure_classes", [])) != {
        "BGF-STAGE35-ALERT-MANAGEMENT-SECRET-READBACK-PLAINTEXT-ASSUMPTION-303",
        "BGF-STAGE35-ALERT-DISPATCH-SECRET-PARITY-304",
        "BGF-STAGE35-ALERT-FAILED-ONE-SHOT-RETRY-WITHOUT-PARITY-305",
    }:
        fail("failure-class set drifted")

    require(authority.get("failed_one_shot_receipt", {}), {
        "pull_request": FAILED_PR,
        "trigger_base_sha": BASELINE,
        "trigger_head_sha": "761bd84534350cd5f7a0cb1530f8e511c620de77",
        "workflow_run": FAILED_RUN,
        "workflow_job": FAILED_JOB,
        "workflow_run_attempt": 1,
        "trigger_guard": "PASS",
        "github_dispatch_secret_presence_gate": "PASS",
        "delivery_step_result": "FAIL",
        "first_dispatch_http_status": 401,
        "expected_http_status": 200,
        "pull_request_closed_unmerged": True,
        "pull_request_reopen_allowed": False,
        "workflow_rerun_allowed": False,
    }, "failed proof receipt")

    require(authority.get("post_failure_remote_receipt", {}), {
        "observed_at_utc": "2026-08-23T15:03:34.975648Z",
        "auth_users": 0,
        "organizations": 0,
        "students": 0,
        "security_signals": 1,
        "exact_controlled_proof_signals": 1,
        "alert_delivery_receipts": 0,
        "controlled_proof_receipts": 0,
        "network_buckets": 13,
        "growth_events": 6,
        "receipt_store_remote_version": "20260823092354",
        "controlled_fixture_remote_version": "20260823145908",
        "dispatcher_slug": "student-access-alert-dispatcher",
        "dispatcher_version": 1,
        "dispatcher_status": "ACTIVE",
        "dispatcher_verify_jwt": False,
        "dispatcher_bundle_sha256": "56cfef7be1dc327ac21a8e1aaacd3b82d20a810cb8a4819da4061e1204d4a627",
        "provider_call_reached": False,
    }, "post-failure remote receipt")

    require(authority.get("root_cause_boundary", {}), {
        "v5_bootstrap_file": "04_backend_supabase/tools/Invoke-Stage35AlertSecretBootstrapV5.ps1",
        "plaintext_reusability_of_management_readback_was_proven": False,
        "runtime_and_github_dispatch_secret_value_equality_was_proven": False,
        "name_presence_4_of_4_plus_3_of_3_was_value_parity": False,
        "http_401_is_empirical_parity_failure": True,
        "v5_may_be_executed_again": False,
    }, "root-cause boundary")

    recovery = authority.get("recovery_contract", {})
    require(recovery, {
        "source_of_truth_for_recovery": "existing_GitHub_Actions_STUDENT_ACCESS_ALERT_DISPATCH_TOKEN",
        "required_github_secrets": ["SUPABASE_ACCESS_TOKEN", "STUDENT_ACCESS_ALERT_DISPATCH_TOKEN"],
        "dispatch_token_min_length": 32,
        "dispatch_token_max_length": 256,
        "reject_multiline_or_nul": True,
        "reject_obvious_redaction_placeholders": True,
        "writes_only_supabase_runtime_secret": "STUDENT_ACCESS_ALERT_DISPATCH_TOKEN",
        "rotates_telegram_bot_token": False,
        "rotates_telegram_chat_id": False,
        "database_mutation": False,
        "provider_call": False,
        "proof_signal_claim": False,
        "proof_receipt_write": False,
        "parity_probe_request_body": {"parity_probe": True},
        "expected_parity_probe_http_status": 400,
        "expected_parity_probe_error": "ALERT_DISPATCH_BODY_FIELD_FORBIDDEN",
        "raw_secret_printing_allowed": False,
        "secret_digest_printing_allowed": False,
    }, "recovery contract")

    require(authority.get("recovery_trigger", {}), {
        "workflow": ".github/workflows/stage35_alert_dispatch_secret_parity_recovery.yml",
        "branch": RECOVERY_BRANCH,
        "file": RECOVERY_TRIGGER,
        "event": "push",
        "run_attempt_must_equal": 1,
        "workflow_dispatch_allowed": False,
        "schedule_allowed": False,
        "one_execution_only": True,
    }, "recovery trigger")

    require(authority.get("retry_boundary", {}), {
        "failed_run_32647288419_may_be_rerun": False,
        "pr112_may_be_reopened": False,
        "new_external_delivery_trigger_allowed_before_parity_recovery_pass": False,
        "new_external_delivery_trigger_allowed_after_parity_recovery_pass_and_fresh_remote_receipt": True,
        "successful_external_delivery_proof_may_be_replayed": False,
    }, "retry boundary")

    require(authority.get("launch_boundary", {}), {
        "incident_response_gate": "DENIED",
        "production_deployment_gate": "DENIED",
        "paid_media_gate": "DENIED",
        "launch_gate": "DENIED",
    }, "launch boundary")

    lower_workflow = workflow.lower()
    required_workflow = (
        "blackgold/stage35-dispatch-secret-parity-recovery-trigger",
        "stage35_alert_dispatch_secret_parity_recovery_trigger.json",
        "github.run_attempt == 1",
        "secrets.supabase_access_token",
        "secrets.student_access_alert_dispatch_token",
        "student_access_alert_dispatch_token",
        "https://api.supabase.com/v1/projects/mceukeondizkwlpfxzgf/secrets",
        "student-access-alert-dispatcher",
        "parity_probe",
        "alert_dispatch_body_field_forbidden",
        "parity_recovery=pass",
        "telegram_provider_called=false",
    )
    for fragment in required_workflow:
        if fragment not in lower_workflow:
            fail(f"recovery workflow invariant missing: {fragment}")
    for forbidden in (
        "workflow_dispatch:",
        "schedule:",
        "student_access_alert_telegram_bot_token: ${{",
        "student_access_alert_telegram_chat_id: ${{",
        "api.telegram.org",
        "claim_student_access_alert_delivery_v1",
        "record_student_access_alert_delivery_v1",
    ):
        if forbidden in lower_workflow:
            fail(f"forbidden recovery workflow surface appeared: {forbidden}")

    lower_dispatcher = dispatcher.lower()
    auth_pos = lower_dispatcher.find("alert_dispatch_unauthorized")
    body_pos = lower_dispatcher.find("alert_dispatch_body_field_forbidden")
    claim_pos = lower_dispatcher.find("const claim = await callrpc")
    telegram_pos = lower_dispatcher.find("/sendmessage")
    if min(auth_pos, body_pos, claim_pos, telegram_pos) < 0:
        fail("dispatcher recovery ordering anchors missing")
    if not (auth_pos < body_pos < claim_pos < telegram_pos):
        fail("dispatcher no-provider parity-probe ordering drifted")

    lower_v5 = v5.lower()
    for fragment in (
        "stage35_alert_secret_bootstrap_v5=disabled",
        "bgf-stage35-alert-management-secret-readback-plaintext-assumption-303",
        "do_not_execute_v5",
        "stage35-dispatch-secret-parity-recovery",
    ):
        if fragment not in lower_v5:
            fail(f"V5 deprecation invariant missing: {fragment}")
    for forbidden in (
        "invoke-webrequest",
        "invoke-restmethod",
        "secret set",
        "read-host",
        "api.supabase.com",
    ):
        if forbidden in lower_v5:
            fail(f"deprecated V5 still contains secret I/O surface: {forbidden}")

    if "v5_deprecated_fail_closed=pass" not in v5_guard.lower():
        fail("V5 guard does not enforce fail-closed deprecation")

    print("STAGE35_ALERT_DISPATCH_SECRET_PARITY_RECOVERY_GUARD=PASS")
    print(f"BASELINE_MAIN_SHA={BASELINE}")
    print(f"FAILED_PROOF_RUN={FAILED_RUN}")
    print(f"FAILED_PROOF_JOB={FAILED_JOB}")
    print("FAILED_PROOF_RERUN_ALLOWED=false")
    print("PR112_REOPEN_ALLOWED=false")
    print("FAILED_PROOF_PROVIDER_CALLED=false")
    print("EXACT_PROOF_SIGNAL_PRESERVED=true")
    print("PROOF_RECEIPTS=0")
    print("RECOVERY_WRITES_ONLY_RUNTIME_DISPATCH_SECRET=true")
    print("PARITY_PROBE_DB_CLAIM=false")
    print("PARITY_PROBE_PROVIDER_CALL=false")
    print("V5_DEPRECATED_FAIL_CLOSED=true")
    print("INCIDENT_RESPONSE_GATE=DENIED")
    print("PRODUCTION_DEPLOYMENT_GATE=DENIED")
    print("PAID_MEDIA_GATE=DENIED")
    print("LAUNCH_GATE=DENIED")


if __name__ == "__main__":
    main()
