from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage35_alert_secret_bootstrap_tooling_authority.json"
READINESS = BACKEND / "stage35_alert_controlled_fixture_promotion_and_secret_readiness_authority.json"
SCRIPT = BACKEND / "tools" / "Invoke-Stage35AlertSecretBootstrap.ps1"

BASELINE = "1d954661a3ed7860572d421ed838bb75e4313954"
FAILURE_CLASS = "BGF-STAGE35-ALERT-SECRET-BOOTSTRAP-TOOLING-DRIFT-297"
EXPECTED_GITHUB_NAMES = [
    "SUPABASE_ACCESS_TOKEN",
    "STUDENT_ACCESS_ALERT_DISPATCH_TOKEN",
    "STUDENT_ACCESS_ALERT_TELEGRAM_BOT_TOKEN",
    "STUDENT_ACCESS_ALERT_TELEGRAM_CHAT_ID",
]
EXPECTED_RUNTIME_NAMES = [
    "STUDENT_ACCESS_ALERT_DISPATCH_TOKEN",
    "STUDENT_ACCESS_ALERT_TELEGRAM_BOT_TOKEN",
    "STUDENT_ACCESS_ALERT_TELEGRAM_CHAT_ID",
]


def fail(message: str) -> None:
    raise SystemExit(
        "STAGE35_ALERT_SECRET_BOOTSTRAP_TOOLING_GUARD=FAIL\n"
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
    readiness = load(READINESS)
    try:
        script = SCRIPT.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"unable to read bootstrap script: {type(exc).__name__}")

    require(
        authority,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "stage": "STAGE35_ALERT_SECRET_BOOTSTRAP_TOOLING",
            "baseline_main_sha": BASELINE,
            "current_state": "SECRET_BOOTSTRAP_TOOLING_PREPARED_EXTERNAL_VALUES_STILL_REQUIRED",
        },
        "tooling authority",
    )
    if set(authority.get("failure_classes", [])) != {
        "BGF-STAGE35-ALERT-SECRET-BOOTSTRAP-CLI-PREREQUISITE-293",
        "BGF-STAGE35-ALERT-SECRET-BOOTSTRAP-PLAINTEXT-TRANSPORT-294",
        "BGF-STAGE35-ALERT-SECRET-BOOTSTRAP-PARTIAL-WRITE-295",
        "BGF-STAGE35-ALERT-SECRET-BOOTSTRAP-LOCAL-RESIDUE-296",
    }:
        fail("tooling failure-class set drifted")

    require(
        readiness,
        {
            "current_state": "RUNTIME_SECRET_READINESS_BLOCKED_MISSING_GITHUB_SECRETS_FIXTURE_NOT_PROMOTED",
        },
        "prior readiness authority",
    )
    runtime_readiness = readiness.get("runtime_secret_readiness", {})
    require(
        runtime_readiness,
        {
            "status": "BLOCKED_MISSING_GITHUB_SECRETS",
            "all_required_github_secrets_present": False,
            "missing_secret_names": EXPECTED_GITHUB_NAMES,
            "secret_values_printed": False,
            "github_presence_proves_supabase_edge_runtime_configured": False,
            "remote_mutation_allowed": False,
        },
        "prior secret readiness receipt",
    )

    tooling = authority.get("tooling_contract", {})
    require(
        tooling,
        {
            "script": "04_backend_supabase/tools/Invoke-Stage35AlertSecretBootstrap.ps1",
            "repository": "ProjetosCosaNostra/FitNexus_Coach_BlackGold",
            "project_ref": "mceukeondizkwlpfxzgf",
            "requires_authenticated_gh_cli": True,
            "requires_supabase_cli_or_npx": True,
            "may_install_cli_automatically": False,
            "dispatch_token_generated_locally": True,
            "dispatch_token_random_bytes": 32,
            "secret_values_accepted_via_command_line_arguments": False,
            "secret_values_printed": False,
            "secret_values_written_inside_repository": False,
            "temporary_supabase_env_file_outside_repository": True,
            "temporary_supabase_env_file_deleted_in_finally": True,
            "github_secret_transport": "gh_secret_set_stdin",
            "supabase_runtime_secret_transport": "supabase_secrets_set_env_file",
            "supabase_runtime_secret_names": EXPECTED_RUNTIME_NAMES,
            "github_actions_secret_names": EXPECTED_GITHUB_NAMES,
            "telegram_provider_call_performed": False,
            "edge_function_deployment_performed": False,
            "database_migration_applied": False,
            "controlled_fixture_applied": False,
            "proof_trigger_created": False,
        },
        "tooling contract",
    )

    normalized = script.replace("\r\n", "\n")
    if not normalized.startswith("[CmdletBinding()]\nparam()\n"):
        fail("bootstrap top-level parameter block must be exactly empty")

    expected_fragments = [
        "param()",
        "Read-Host -Prompt $Prompt -AsSecureString",
        "RandomNumberGenerator]::Create()",
        "$rng.GetBytes($bytes)",
        "$Value | & $script:GhCommand secret set $Name --repo $Repository",
        "'secrets', 'set', '--project-ref', $ProjectRef, '--env-file', $tempEnvFile",
        "'secrets', 'list', '--project-ref', $ProjectRef",
        "Invoke-RestMethod -Method Get -Uri \"https://api.supabase.com/v1/projects/$ProjectRef\"",
        "[IO.Path]::GetTempPath()",
        "Remove-Item -LiteralPath $tempEnvFile -Force",
        "finally {",
        "SECRET_VALUES_PRINTED=false",
        "DATABASE_MIGRATION_APPLIED=false",
        "EDGE_FUNCTION_DEPLOYED=false",
        "TELEGRAM_PROVIDER_CALLED=false",
        "ONE_SHOT_EXTERNAL_DELIVERY_PROOF_CONSUMED=false",
    ]
    for fragment in expected_fragments:
        if fragment not in script:
            fail(f"bootstrap invariant missing: {fragment}")

    for name in EXPECTED_GITHUB_NAMES:
        if name not in script:
            fail(f"required GitHub secret name absent from script: {name}")
    for name in EXPECTED_RUNTIME_NAMES:
        if name not in script:
            fail(f"required runtime secret name absent from script: {name}")

    forbidden_fragments = [
        "https://api.telegram.org",
        "functions deploy",
        "db push",
        "migration up",
        "apply_migration",
        "workflow run stage35_alert_external_delivery",
        "gh pr create",
        "winget install",
        "choco install",
        "scoop install",
        "Set-Content -Path 04_backend_supabase",
        "Out-File 04_backend_supabase",
    ]
    lower = script.lower()
    for fragment in forbidden_fragments:
        if fragment.lower() in lower:
            fail(f"forbidden bootstrap behavior appeared: {fragment}")

    if "--body $" in lower:
        fail("GitHub secret value appeared in command arguments")

    require(
        authority.get("post_bootstrap_boundary", {}),
        {
            "github_secret_presence_must_be_reassessed_by_existing_stage35_workflow": True,
            "supabase_runtime_secret_names_must_be_verified_without_values": True,
            "fixture_promotion_still_requires_separate_repository_pr": True,
            "receipt_store_remote_apply_still_requires_separate_controlled_stage": True,
            "dispatcher_deployment_still_requires_separate_controlled_stage": True,
            "one_shot_external_delivery_proof_still_unconsumed": True,
            "incident_response_gate_promoted": False,
            "production_deployment_gate_promoted": False,
            "paid_media_gate_promoted": False,
        },
        "post-bootstrap boundary",
    )
    require(
        authority.get("next_stage", {}),
        {
            "name": "EXECUTE_SECRET_BOOTSTRAP_WITH_REAL_EXTERNAL_CREDENTIALS_THEN_REASSESS",
            "allowed_now": False,
            "blocked_by_external_credential_values": True,
            "requires_secret_values_outside_repository_and_chat_artifacts": True,
            "requires_no_remote_database_or_edge_deployment_mutation": True,
            "after_success": "RERUN_STAGE35_ALERT_RUNTIME_SECRET_READINESS_THEN_PROMOTE_CONTROLLED_FIXTURE_REPO_ONLY",
            "may_promote_launch_gates": False,
        },
        "next-stage contract",
    )

    print("STAGE35_ALERT_SECRET_BOOTSTRAP_TOOLING_GUARD=PASS")
    print(f"BASELINE_MAIN_SHA={BASELINE}")
    print("SECRET_VALUES_IN_REPOSITORY=false")
    print("BOOTSTRAP_EXECUTED_BY_CI=false")
    print("REMOTE_DATABASE_MUTATION=false")
    print("EDGE_FUNCTION_DEPLOYMENT=false")
    print("TELEGRAM_PROVIDER_CALL=false")
    print("PROOF_CONSUMED=false")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
