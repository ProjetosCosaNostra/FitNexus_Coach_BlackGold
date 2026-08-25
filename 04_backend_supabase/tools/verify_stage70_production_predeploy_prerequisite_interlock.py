from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage70_production_predeploy_prerequisite_interlock_authority.json"
STAGE46 = BACKEND / "stage46_production_deployment_external_evidence_preparation_authority.json"
STAGE66 = BACKEND / "stage66_production_release_candidate_evidence_pipeline_authority.json"
BINDER = BACKEND / "tools" / "bind_stage70_production_predeploy_prerequisites.py"
TEMPLATE = ROOT / "10_compliance" / "deployment" / "STAGE70_PRODUCTION_PREDEPLOY_PREREQUISITE_INPUT_TEMPLATE.json"
WORKFLOW = ROOT / ".github" / "workflows" / "stage70_production_predeploy_prerequisite_interlock.yml"

BASELINE_MAIN = "2f74ed0f282e32cec81e706e013ff18d9337ac65"
STAGE46_BLOB = "bec2751cbeaa5e0fc8c97dc0eb65dbbb7db65134"
STAGE66_BLOB = "8f3be15da1027d9a5bed6e7d1f43cefebcf6a9eb"
BINDER_BLOB = "4d3d60c03ed25fc0fb2af1db2ed53396e2b4957e"
TEMPLATE_BLOB = "943c8fccdc96f2b58d5b0df38cce3c9f021f6a79"
FAILURE_CLASS = "BGF-STAGE70-PREDEPLOY-INTERLOCK-GUARD-675"


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE70_PRODUCTION_PREDEPLOY_PREREQUISITE_INTERLOCK=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\n"
        f"DETAIL={detail}"
    )


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to load {path.relative_to(ROOT)}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"expected JSON object: {path.relative_to(ROOT)}")
    return value


def git_blob(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def require(mapping: dict, expected: dict, label: str) -> None:
    if not isinstance(mapping, dict):
        fail(f"{label} must be object")
    for key, value in expected.items():
        if mapping.get(key) != value:
            fail(f"{label} drift: {key}")


def main() -> None:
    authority = load(AUTHORITY)
    stage46 = load(STAGE46)
    stage66 = load(STAGE66)
    template = load(TEMPLATE)

    if git_blob(STAGE46) != STAGE46_BLOB:
        fail("Stage46 authority blob drift")
    if git_blob(STAGE66) != STAGE66_BLOB:
        fail("Stage66 authority blob drift")
    if git_blob(BINDER) != BINDER_BLOB:
        fail("Stage70 binder blob drift")
    if git_blob(TEMPLATE) != TEMPLATE_BLOB:
        fail("Stage70 prerequisite template blob drift")

    require(
        authority,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "stage": "STAGE70_PRODUCTION_PREDEPLOY_PREREQUISITE_INTERLOCK",
            "baseline_main_sha": BASELINE_MAIN,
            "current_state": "EXACT_RELEASE_CANDIDATE_PREDEPLOY_PREREQUISITE_BINDING_PREPARED_NO_DEPLOYMENT_NO_PRODUCTION_EVIDENCE_NO_GATE_PROMOTION",
        },
        "Stage70 authority",
    )
    require(
        stage46,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "stage": "STAGE46_PRODUCTION_DEPLOYMENT_EXTERNAL_EVIDENCE_PREPARATION",
            "current_state": "PREPARED_REAL_PRODUCTION_RELEASE_AND_OPERATIONS_EVIDENCE_REQUIRED_NO_DEPLOYMENT_NO_ATTESTATION_NO_GATE_PROMOTION",
        },
        "Stage46 authority",
    )
    require(
        stage66,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "stage": "STAGE66_PRODUCTION_RELEASE_CANDIDATE_EVIDENCE_PIPELINE",
            "current_state": "PUBLIC_GH_PAGES_SURFACE_STALE_VS_CURRENT_MAIN_RELEASE_CANDIDATE_PIPELINE_PREPARED_NO_DEPLOYMENT_NO_GATE_PROMOTION",
        },
        "Stage66 authority",
    )

    remote = authority.get("fresh_remote_read_only_receipt", {})
    require(
        remote,
        {
            "source": "Supabase.execute_sql_read_only",
            "observed_at_utc": "2026-08-25T17:57:01.715964+00:00",
            "auth_users": 0,
            "organizations": 0,
            "students": 0,
            "asaas_state": "selected_pending_credentials",
            "asaas_activated_at": None,
            "ready_evidence_migration_count": 0,
            "remote_mutation_performed": False,
        },
        "remote receipt",
    )

    contract = authority.get("predeploy_contract", {})
    for key in (
        "exact_release_candidate_manifest_required",
        "release_candidate_source_sha_must_match_requested_source_sha",
        "stable_production_domain_required",
        "tls_baseline_artifact_required",
        "secret_free_environment_readiness_artifact_required",
        "rollback_readiness_artifact_required",
        "monitoring_alerting_readiness_artifact_required",
        "backup_restore_readiness_artifact_required",
        "deployment_destination_control_artifact_required",
        "real_operator_acknowledgment_required",
        "placeholder_prerequisite_input_must_fail",
        "test_fixture_prerequisite_input_must_fail",
        "artifact_sha256_only_in_output",
    ):
        if contract.get(key) is not True:
            fail(f"predeploy contract must remain true: {key}")
    for key in (
        "artifact_paths_copied_to_output",
        "artifact_contents_copied_to_output",
        "secret_values_allowed",
        "deployment_action_allowed",
        "gh_pages_write_allowed",
        "network_probe_allowed",
        "supabase_mutation_allowed",
        "provider_call_allowed",
        "production_smoke_claim_allowed_before_deploy",
        "production_evidence_claim_allowed",
        "evidence_migration_creation_allowed",
        "production_deployment_gate_promotion_allowed",
        "controlled_launch_promotion_allowed",
        "paid_media_promotion_allowed",
    ):
        if contract.get(key) is not False:
            fail(f"predeploy contract must remain false: {key}")

    require(
        template,
        {
            "schema_version": 1,
            "input_kind": "REAL_PRODUCTION_PREDEPLOY_PREREQUISITE_INPUT",
            "status": "PLACEHOLDER_TEMPLATE_NOT_OPERATIONAL_EVIDENCE",
            "test_fixture": True,
            "contains_placeholders": True,
            "operator_acknowledged": False,
            "stable_production_domain": "<REAL_STABLE_HTTPS_DOMAIN_REQUIRED>",
        },
        "predeploy template",
    )
    expected_artifact_keys = {
        "tls_baseline",
        "environment_readiness_without_secrets",
        "rollback_readiness",
        "monitoring_alerting_readiness",
        "backup_restore_readiness",
        "deployment_destination_control",
    }
    artifacts = template.get("artifacts")
    if not isinstance(artifacts, dict) or set(artifacts) != expected_artifact_keys:
        fail("predeploy template artifact set drift")
    if any(value != "<REAL_NONEMPTY_ARTIFACT_PATH_REQUIRED>" for value in artifacts.values()):
        fail("predeploy template must retain only artifact placeholders")

    binder_text = BINDER.read_text(encoding="utf-8")
    try:
        tree = ast.parse(binder_text)
    except SyntaxError as exc:
        fail(f"Stage70 binder syntax invalid: {exc.msg}")
    forbidden_import_roots = {"os", "subprocess", "socket", "urllib", "http", "requests", "supabase"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".", 1)[0] in forbidden_import_roots:
                    fail(f"binder imports forbidden module: {alias.name}")
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module.split(".", 1)[0] in forbidden_import_roots:
                fail(f"binder imports forbidden module: {node.module}")

    for fragment in (
        'value.get("test_fixture") is not False',
        'value.get("contains_placeholders") is not False',
        'value.get("operator_acknowledged") is not True',
        'manifest.get("source_commit_sha") != source_sha',
        '"NON_ATTESTING_PRODUCTION_PREDEPLOY_BINDING_CANDIDATE"',
        '"PREDEPLOY_PREREQUISITES_HASH_BOUND_TO_EXACT_RELEASE_CANDIDATE_NOT_DEPLOYED_NOT_PRODUCTION_EVIDENCE"',
        '"artifact_paths_copied_to_receipt": False',
        '"artifact_contents_copied_to_receipt": False',
        '"network_probe_performed": False',
        '"deployment_performed": False',
        '"production_smoke_performed": False',
        '"production_evidence_attested": False',
        '"production_deployment_gate_ready_attested": False',
    ):
        if fragment not in binder_text:
            fail(f"binder fail-closed invariant missing: {fragment}")
    for forbidden in (
        "--allow-placeholder",
        "--skip-prerequisite-validation",
        "execute_sql",
        "apply_migration",
        "git push",
        "actions/deploy-pages",
    ):
        if forbidden in binder_text.lower():
            fail(f"binder contains forbidden bypass/remote fragment: {forbidden}")

    workflow = WORKFLOW.read_text(encoding="utf-8")
    workflow_lower = workflow.lower()
    for fragment in (
        "permissions:\n  contents: read",
        "verify_stage70_production_predeploy_prerequisite_interlock.py",
        "flutter build web --release --base-href /FitNexus_Coach_BlackGold/",
        "build_stage66_production_release_candidate_manifest.py",
        "STAGE70_PRODUCTION_PREDEPLOY_PREREQUISITE_INPUT_TEMPLATE.json",
        "bind_stage70_production_predeploy_prerequisites.py",
        "PLACEHOLDER_PREDEPLOY_INPUT_REFUSED=PASS",
        "test ! -e /tmp/stage70_predeploy.json",
    ):
        if fragment not in workflow:
            fail(f"workflow invariant missing: {fragment}")
    for forbidden in (
        "actions/deploy-pages",
        "peaceiris/actions-gh-pages",
        "git push",
        "supabase db",
        "apply_migration",
        "execute_sql",
        "curl ",
        "wget ",
    ):
        if forbidden in workflow_lower:
            fail(f"workflow contains forbidden deployment/remote action: {forbidden}")

    if stage46.get("gates", {}).get("production_deployment") != "DENIED_AWAITING_REAL_PRODUCTION_RELEASE_AND_OPERATIONS_EVIDENCE":
        fail("Stage46 production deployment gate drift")
    if authority.get("gates", {}).get("production_deployment") != "DENIED_AWAITING_REAL_PRODUCTION_RELEASE_AND_OPERATIONS_EVIDENCE":
        fail("Stage70 production deployment gate drift")
    if authority.get("gates", {}).get("controlled_launch") != "DENIED":
        fail("Stage70 controlled launch boundary drift")

    if list((BACKEND / "migrations").glob("*stage70*.sql")):
        fail("Stage70 predeploy interlock must not create a migration")

    print("STAGE70_PRODUCTION_PREDEPLOY_PREREQUISITE_INTERLOCK=PASS")
    print("PLACEHOLDER_PREDEPLOY_INPUT_ALLOWED=false")
    print("DEPLOYMENT_ACTION=false")
    print("NETWORK_PROBE=false")
    print("PRODUCTION_EVIDENCE=false")
    print("PRODUCTION_DEPLOYMENT_GATE=BLOCKED")
    print("REMOTE_MUTATION=false")
    print("CONTROLLED_LAUNCH=DENIED")


if __name__ == "__main__":
    main()
