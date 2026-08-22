from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage35_alert_secret_post_bootstrap_reconciliation_contract_authority.json"
BOOTSTRAP = BACKEND / "stage35_alert_secret_bootstrap_tooling_authority.json"
READINESS = BACKEND / "stage35_alert_controlled_fixture_promotion_and_secret_readiness_authority.json"
WORKFLOW = ROOT / ".github" / "workflows" / "stage35_alert_secret_post_bootstrap_reconciliation.yml"
TRIGGER = BACKEND / "stage35_alert_secret_post_bootstrap_recheck_trigger.json"

BASELINE = "8e9eb268af5df0a94e57b93a997b7c4411f11607"
PROJECT_REF = "mceukeondizkwlpfxzgf"
RECHECK_BRANCH = "blackgold/stage35-alert-secret-recheck"
FAILURE_CLASS = "BGF-STAGE35-ALERT-SECRET-RECHECK-CONTRACT-DRIFT-303"
GITHUB_NAMES = [
    "SUPABASE_ACCESS_TOKEN",
    "STUDENT_ACCESS_ALERT_DISPATCH_TOKEN",
    "STUDENT_ACCESS_ALERT_TELEGRAM_BOT_TOKEN",
    "STUDENT_ACCESS_ALERT_TELEGRAM_CHAT_ID",
]
RUNTIME_NAMES = [
    "STUDENT_ACCESS_ALERT_DISPATCH_TOKEN",
    "STUDENT_ACCESS_ALERT_TELEGRAM_BOT_TOKEN",
    "STUDENT_ACCESS_ALERT_TELEGRAM_CHAT_ID",
]


def fail(message: str) -> None:
    raise SystemExit(
        "STAGE35_ALERT_SECRET_POST_BOOTSTRAP_RECONCILIATION_CONTRACT_GUARD=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\nDETAIL={message}"
    )


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to read {path.relative_to(ROOT)}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"expected object: {path.relative_to(ROOT)}")
    return value


def require(mapping: dict, expected: dict, label: str) -> None:
    if not isinstance(mapping, dict):
        fail(f"{label} must be an object")
    for key, expected_value in expected.items():
        if mapping.get(key) != expected_value:
            fail(f"{label} drift: {key}")


def main() -> None:
    authority = load(AUTHORITY)
    bootstrap = load(BOOTSTRAP)
    readiness = load(READINESS)
    try:
        workflow = WORKFLOW.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"unable to read workflow: {type(exc).__name__}")

    require(
        authority,
        {
            "schema_version": 1,
            "project_ref": PROJECT_REF,
            "stage": "STAGE35_ALERT_SECRET_POST_BOOTSTRAP_RECONCILIATION_CONTRACT",
            "baseline_main_sha": BASELINE,
            "current_state": "POST_BOOTSTRAP_RECONCILIATION_CONTRACT_STAGED_NO_SECRET_ACCESS",
        },
        "reconciliation authority",
    )
    if set(authority.get("failure_classes", [])) != {
        "BGF-STAGE35-ALERT-SECRET-RECHECK-PREMATURE-298",
        "BGF-STAGE35-ALERT-GITHUB-PRESENCE-FALSE-POSITIVE-299",
        "BGF-STAGE35-ALERT-RUNTIME-SECRET-NAME-GAP-300",
        "BGF-STAGE35-ALERT-SECRET-LIST-DISCLOSURE-301",
        "BGF-STAGE35-ALERT-SECRET-RECHECK-DIFF-DRIFT-302",
    }:
        fail("reconciliation failure-class set drifted")

    require(
        bootstrap,
        {
            "baseline_main_sha": "1d954661a3ed7860572d421ed838bb75e4313954",
            "current_state": "SECRET_BOOTSTRAP_TOOLING_PREPARED_EXTERNAL_VALUES_STILL_REQUIRED",
        },
        "merged bootstrap tooling authority",
    )
    require(
        readiness,
        {
            "current_state": "RUNTIME_SECRET_READINESS_BLOCKED_MISSING_GITHUB_SECRETS_FIXTURE_NOT_PROMOTED",
        },
        "prior readiness authority",
    )

    receipt = authority.get("bootstrap_tooling_receipt", {})
    require(
        receipt,
        {
            "source_pr": 103,
            "source_head_sha": "1a1f969d75dbacc755da99c0fbc2665d26f84cab",
            "source_merge_main_sha": BASELINE,
            "dedicated_guard_run": 32591739341,
            "dedicated_guard_job": 97076540917,
            "dedicated_guard_result": "PASS",
            "quality_gate_run": 32591739355,
            "quality_gate_job": 97076541117,
            "quality_gate_result": "PASS",
            "bootstrap_executed_by_ci": False,
            "secret_values_configured_by_pr103": False,
            "remote_database_mutation_by_pr103": False,
            "edge_function_deployment_by_pr103": False,
            "telegram_provider_call_by_pr103": False,
        },
        "bootstrap tooling receipt",
    )

    remote = authority.get("fresh_remote_receipt", {})
    require(
        remote,
        {
            "observed_at_utc": "2026-08-22T18:50:02.519334Z",
            "auth_users": 0,
            "organizations": 0,
            "students": 0,
            "security_events": 0,
            "security_signals": 0,
            "network_buckets": 13,
            "growth_events": 6,
            "anon_execute_count": 0,
            "authenticated_execute_count": 0,
            "service_role_execute_count": 5,
            "issue_student_access_token_v2_authenticated_execute": True,
            "alert_receipt_table_exists": False,
            "alert_claim_bridge_exists": False,
            "alert_record_bridge_exists": False,
            "remote_stage35_migration_count": 0,
            "deployed_edge_function_count": 1,
            "student_access_alert_dispatcher_deployed": False,
            "security_advisor_warning_count": 1,
            "issue_token_warning_intentionally_unmodified": True,
        },
        "fresh remote receipt",
    )
    if remote.get("deployed_edge_functions") != [{
        "slug": "student-access-gateway",
        "version": 3,
        "status": "ACTIVE",
        "verify_jwt": False,
        "bundle_sha256": "b57892b3f399b76f8127c9a39d3d8c021ffe639aa7bf92c7fa9a459d35721b82",
    }]:
        fail("deployed Edge inventory drifted")

    trigger_contract = authority.get("reconciliation_trigger_contract", {})
    require(
        trigger_contract,
        {
            "workflow": ".github/workflows/stage35_alert_secret_post_bootstrap_reconciliation.yml",
            "runtime_trigger_event": "push",
            "runtime_trigger_branch": RECHECK_BRANCH,
            "runtime_trigger_file": "04_backend_supabase/stage35_alert_secret_post_bootstrap_recheck_trigger.json",
            "trigger_branch_must_be_created_fresh_from_current_main": True,
            "trigger_diff_must_contain_only_trigger_file": True,
            "bootstrap_tooling_main_must_be_ancestor": BASELINE,
            "workflow_dispatch_allowed": False,
            "schedule_allowed": False,
            "pull_request_runtime_secret_access_allowed": False,
            "static_contract_guard_runs_on_pull_request": True,
        },
        "reconciliation trigger contract",
    )
    if TRIGGER.exists():
        fail("runtime recheck trigger materialized during contract preparation")

    require(
        authority.get("github_actions_reconciliation", {}),
        {
            "required_secret_names": GITHUB_NAMES,
            "requires_all_four_nonempty": True,
            "secret_values_printed": False,
            "secret_values_written_to_files": False,
            "github_presence_alone_is_runtime_readiness": False,
        },
        "GitHub secret reconciliation",
    )
    require(
        authority.get("supabase_edge_runtime_reconciliation", {}),
        {
            "method": "supabase_cli_secrets_list_exact_project_ref",
            "project_ref": PROJECT_REF,
            "management_token_source": "github_actions_secret_SUPABASE_ACCESS_TOKEN",
            "required_runtime_secret_names": RUNTIME_NAMES,
            "raw_secrets_list_output_may_be_logged": False,
            "secret_values_may_be_printed": False,
            "digest_values_may_be_printed": False,
            "all_three_names_required": True,
            "provider_credential_validity_proven": False,
            "telegram_destination_validity_proven": False,
            "provider_called": False,
        },
        "Supabase runtime reconciliation",
    )

    required_workflow_fragments = [
        "branches:\n      - blackgold/stage35-alert-secret-recheck",
        "04_backend_supabase/stage35_alert_secret_post_bootstrap_recheck_trigger.json",
        "github.event_name == 'pull_request'",
        "github.event_name == 'push' && github.ref_name == 'blackgold/stage35-alert-secret-recheck'",
        "git fetch origin main --prune",
        "['git', 'merge-base', 'HEAD', 'origin/main']",
        "['git', 'diff', '--name-only', 'origin/main...HEAD']",
        "uses: supabase/setup-cli@v1",
        "supabase secrets list --project-ref mceukeondizkwlpfxzgf",
        "2>\"$ERR_FILE\"",
        "unset RUNTIME_SECRET_LIST",
        "GITHUB_ACTIONS_SECRET_NAMES_4_OF_4=true",
        "SUPABASE_EDGE_RUNTIME_SECRET_NAMES_3_OF_3=true",
        "RAW_SECRET_LIST_OUTPUT_PRINTED=false",
        "PROVIDER_CREDENTIAL_VALIDITY_PROVEN=false",
        "TELEGRAM_PROVIDER_CALLED=false",
        "DATABASE_MIGRATION_APPLIED=false",
        "EDGE_FUNCTION_DEPLOYED=false",
        "ONE_SHOT_EXTERNAL_DELIVERY_PROOF_CONSUMED=false",
        "INCIDENT_RESPONSE_GATE=DENIED",
        "PRODUCTION_DEPLOYMENT_GATE=DENIED",
        "PAID_MEDIA_GATE=DENIED",
    ]
    for fragment in required_workflow_fragments:
        if fragment not in workflow:
            fail(f"workflow invariant missing: {fragment}")
    for name in GITHUB_NAMES:
        if f"secrets.{name}" not in workflow:
            fail(f"GitHub Actions secret binding missing: {name}")
    for name in RUNTIME_NAMES:
        if name not in workflow:
            fail(f"runtime secret name check missing: {name}")

    lower = workflow.lower()
    forbidden_workflow_fragments = [
        "workflow_dispatch:",
        "schedule:",
        "https://api.telegram.org",
        "functions deploy",
        "db push",
        "migration up",
        "apply_migration",
        "gh secret set",
        "supabase secrets set",
        "stage35_alert_external_delivery_one_shot_proof",
        "student-access-alert-dispatcher'",
        'student-access-alert-dispatcher"',
    ]
    for fragment in forbidden_workflow_fragments:
        if fragment.lower() in lower:
            fail(f"forbidden reconciliation behavior appeared: {fragment}")

    for fragment in (
        'echo "$RUNTIME_SECRET_LIST"',
        "echo '$RUNTIME_SECRET_LIST'",
        "cat /tmp/supabase",
        "cat \"$ERR_FILE\"",
    ):
        if fragment.lower() in lower:
            fail(f"raw secret-list disclosure path appeared: {fragment}")

    require(
        authority.get("remote_mutation_boundary", {}),
        {
            "database_migration_applied_by_recheck": False,
            "controlled_fixture_applied_by_recheck": False,
            "edge_function_deployed_by_recheck": False,
            "telegram_provider_called_by_recheck": False,
            "one_shot_external_delivery_proof_consumed_by_recheck": False,
            "direct_rpc_regrant_performed": False,
            "automatic_direct_fallback_enabled": False,
            "source_transport_metadata_advanced": False,
        },
        "remote mutation boundary",
    )
    require(
        authority.get("next_stage", {}),
        {
            "name": "AFTER_REAL_BOOTSTRAP_CREATE_EXACT_RECHECK_TRIGGER_AND_REQUIRE_4_OF_4_PLUS_3_OF_3_PASS",
            "allowed_now": False,
            "blocked_by_external_secret_bootstrap_execution": True,
            "after_reconciliation_success": "PROMOTE_CONTROLLED_FIXTURE_REPO_ONLY_AND_PREPARE_RECEIPT_STORE_REMOTE_APPLY_DISPATCHER_DEPLOYMENT_SEQUENCE",
            "requires_no_secret_values_in_repository_or_logs": True,
            "requires_no_provider_call_during_reconciliation": True,
            "may_promote_launch_gates": False,
        },
        "next-stage contract",
    )

    print("STAGE35_ALERT_SECRET_POST_BOOTSTRAP_RECONCILIATION_CONTRACT_GUARD=PASS")
    print(f"BASELINE_MAIN_SHA={BASELINE}")
    print("RUNTIME_RECHECK_TRIGGER_MATERIALIZED=false")
    print("SECRET_VALUES_ACCESSED_BY_CONTRACT_CI=false")
    print("REMOTE_MUTATION=false")
    print("TELEGRAM_PROVIDER_CALL=false")
    print("ONE_SHOT_EXTERNAL_DELIVERY_PROOF_CONSUMED=false")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
