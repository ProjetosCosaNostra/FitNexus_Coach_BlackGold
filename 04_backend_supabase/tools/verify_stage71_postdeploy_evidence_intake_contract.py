from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage71_postdeploy_evidence_intake_contract_authority.json"
STAGE46 = BACKEND / "stage46_production_deployment_external_evidence_preparation_authority.json"
STAGE70 = BACKEND / "stage70_production_predeploy_prerequisite_interlock_authority.json"
COLLECTOR = BACKEND / "tools" / "collect_stage71_postdeploy_evidence_candidate.py"
TEMPLATE = ROOT / "10_compliance" / "deployment" / "STAGE71_POSTDEPLOY_EVIDENCE_INPUT_TEMPLATE.json"
WORKFLOW = ROOT / ".github" / "workflows" / "stage71_postdeploy_evidence_intake_contract.yml"

BASELINE_MAIN = "be1e6026095c48d322428ffd84e2994c9a683f8f"
STAGE46_BLOB = "bec2751cbeaa5e0fc8c97dc0eb65dbbb7db65134"
STAGE70_BLOB = "f62630cb17ffa0e6e92f5a7f9d78f9a9cff17660"
COLLECTOR_BLOB = "9a5487f725caa20e04356a939ce65ac72b9d4f7e"
TEMPLATE_BLOB = "52235154070642330bb08cdccc7c27d2e09b0e81"
FAILURE_CLASS = "BGF-STAGE71-POSTDEPLOY-INTAKE-GUARD-685"


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE71_POSTDEPLOY_EVIDENCE_INTAKE_CONTRACT=FAIL\n"
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
    stage70 = load(STAGE70)
    template = load(TEMPLATE)

    if git_blob(STAGE46) != STAGE46_BLOB:
        fail("Stage46 authority blob drift")
    if git_blob(STAGE70) != STAGE70_BLOB:
        fail("Stage70 authority blob drift")
    if git_blob(COLLECTOR) != COLLECTOR_BLOB:
        fail("Stage71 collector blob drift")
    if git_blob(TEMPLATE) != TEMPLATE_BLOB:
        fail("Stage71 input template blob drift")

    require(
        authority,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "stage": "STAGE71_POSTDEPLOY_EVIDENCE_INTAKE_CONTRACT",
            "baseline_main_sha": BASELINE_MAIN,
            "current_state": "POSTDEPLOY_DIGEST_ONLY_EVIDENCE_INTAKE_CONTRACT_PREPARED_NO_DEPLOYMENT_NO_GATE_PROMOTION",
        },
        "Stage71 authority",
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
        stage70,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "stage": "STAGE70_PRODUCTION_PREDEPLOY_PREREQUISITE_INTERLOCK",
            "current_state": "EXACT_RELEASE_CANDIDATE_PREDEPLOY_PREREQUISITE_BINDING_PREPARED_NO_DEPLOYMENT_NO_PRODUCTION_EVIDENCE_NO_GATE_PROMOTION",
        },
        "Stage70 authority",
    )

    remote = authority.get("fresh_remote_read_only_receipt", {})
    require(
        remote,
        {
            "source": "Supabase.execute_sql_read_only",
            "observed_at_utc": "2026-08-25T18:02:36.623308+00:00",
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

    contract = authority.get("postdeploy_contract", {})
    for key in (
        "predeploy_binding_required",
        "exact_deployed_release_sha_required",
        "stable_domain_must_match_predeploy_binding",
        "live_tls_receipt_required",
        "production_smoke_receipt_required",
        "postdeploy_rollback_receipt_required",
        "monitoring_alerting_live_receipt_required",
        "final_release_evidence_manifest_required",
        "operator_acknowledgment_required",
        "placeholder_input_must_fail",
        "test_fixture_input_must_fail",
        "artifact_sha256_only_in_output",
    ):
        if contract.get(key) is not True:
            fail(f"postdeploy contract must remain true: {key}")
    for key in (
        "artifact_paths_copied_to_output",
        "artifact_contents_copied_to_output",
        "network_calls_allowed",
        "deployment_action_allowed",
        "gh_pages_write_allowed",
        "supabase_mutation_allowed",
        "provider_calls_allowed",
        "production_gate_ready_attestation_allowed",
        "evidence_migration_creation_allowed",
        "controlled_launch_promotion_allowed",
        "paid_media_promotion_allowed",
    ):
        if contract.get(key) is not False:
            fail(f"postdeploy contract must remain false: {key}")

    require(
        template,
        {
            "schema_version": 1,
            "input_kind": "REAL_POSTDEPLOY_EVIDENCE_INPUT",
            "status": "PLACEHOLDER_TEMPLATE_NOT_PRODUCTION_EVIDENCE",
            "test_fixture": True,
            "contains_placeholders": True,
            "operator_acknowledged": False,
            "deployed_release_sha": "<EXACT_40_HEX_DEPLOYED_RELEASE_SHA_REQUIRED>",
            "stable_production_domain": "<REAL_STABLE_HTTPS_DOMAIN_REQUIRED>",
        },
        "postdeploy template",
    )
    expected_artifacts = {
        "live_tls_receipt",
        "production_smoke_receipt",
        "postdeploy_rollback_receipt",
        "monitoring_alerting_live_receipt",
        "final_release_evidence_manifest",
    }
    artifacts = template.get("artifacts")
    if not isinstance(artifacts, dict) or set(artifacts) != expected_artifacts:
        fail("postdeploy template artifact set drift")
    if any(value != "<REAL_NONEMPTY_ARTIFACT_PATH_REQUIRED>" for value in artifacts.values()):
        fail("postdeploy template must retain only artifact placeholders")

    collector_text = COLLECTOR.read_text(encoding="utf-8")
    try:
        tree = ast.parse(collector_text)
    except SyntaxError as exc:
        fail(f"Stage71 collector syntax invalid: {exc.msg}")
    forbidden_import_roots = {"os", "subprocess", "socket", "urllib", "http", "requests", "supabase"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".", 1)[0] in forbidden_import_roots:
                    fail(f"collector imports forbidden module: {alias.name}")
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module.split(".", 1)[0] in forbidden_import_roots:
                fail(f"collector imports forbidden module: {node.module}")

    for fragment in (
        'value.get("test_fixture") is not False',
        'value.get("contains_placeholders") is not False',
        'value.get("operator_acknowledged") is not True',
        'value.get("source_commit_sha") != deployed_sha',
        'value.get("stable_production_domain") != domain',
        '"DIGEST_ONLY_POSTDEPLOY_EVIDENCE_INTAKE_CANDIDATE"',
        '"REAL_RECEIPT_DIGESTS_BOUND_AWAITING_INDEPENDENT_REVIEW_NOT_GATE_EVIDENCE"',
        '"artifact_paths_copied_to_receipt": False',
        '"deployment_performed_by_collector": False',
        '"production_gate_ready_attested": False',
        '"evidence_migration_created": False',
        '"independent_review_required": True',
    ):
        if fragment not in collector_text:
            fail(f"collector invariant missing: {fragment}")
    if collector_text.index("validate_postdeploy_input") > collector_text.index("validate_predeploy_binding"):
        fail("collector must validate real postdeploy input before opening predeploy binding")
    for forbidden in (
        "--allow-placeholder",
        "--skip-review",
        "execute_sql",
        "apply_migration",
        "git push",
        "actions/deploy-pages",
    ):
        if forbidden in collector_text.lower():
            fail(f"collector contains forbidden bypass/remote fragment: {forbidden}")

    workflow = WORKFLOW.read_text(encoding="utf-8")
    workflow_lower = workflow.lower()
    for fragment in (
        "permissions:\n  contents: read",
        "verify_stage71_postdeploy_evidence_intake_contract.py",
        "collect_stage71_postdeploy_evidence_candidate.py",
        "STAGE71_POSTDEPLOY_EVIDENCE_INPUT_TEMPLATE.json",
        "PLACEHOLDER_POSTDEPLOY_INPUT_REFUSED=PASS",
        "test ! -e /tmp/stage71_postdeploy.json",
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
            fail(f"workflow contains forbidden remote action: {forbidden}")

    if stage46.get("gates", {}).get("production_deployment") != "DENIED_AWAITING_REAL_PRODUCTION_RELEASE_AND_OPERATIONS_EVIDENCE":
        fail("Stage46 production gate drift")
    if authority.get("gates", {}).get("production_deployment") != "DENIED_AWAITING_REAL_PRODUCTION_RELEASE_AND_OPERATIONS_EVIDENCE":
        fail("Stage71 production gate drift")
    if authority.get("gates", {}).get("controlled_launch") != "DENIED":
        fail("Stage71 controlled launch drift")
    if list((BACKEND / "migrations").glob("*stage71*.sql")):
        fail("Stage71 intake contract must not create a migration")

    print("STAGE71_POSTDEPLOY_EVIDENCE_INTAKE_CONTRACT=PASS")
    print("PLACEHOLDER_POSTDEPLOY_INPUT_ALLOWED=false")
    print("DEPLOYMENT_ACTION=false")
    print("NETWORK_CALL=false")
    print("PRODUCTION_GATE_READY=false")
    print("EVIDENCE_MIGRATION=false")
    print("REMOTE_MUTATION=false")
    print("CONTROLLED_LAUNCH=DENIED")


if __name__ == "__main__":
    main()
