from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
APP = ROOT / "03_app_flutter" / "fitnexus_app"
AUTHORITY = BACKEND / "stage66_production_release_candidate_evidence_pipeline_authority.json"
STAGE65 = BACKEND / "stage65_stage64_final_reconciliation_authority.json"
STAGE46 = BACKEND / "stage46_production_deployment_external_evidence_preparation_authority.json"
BUILDER = BACKEND / "tools" / "build_stage66_production_release_candidate_manifest.py"
WORKFLOW = ROOT / ".github" / "workflows" / "stage66_production_release_candidate_evidence_pipeline.yml"
WEB_INDEX = APP / "web" / "index.html"

BASELINE_MAIN = "4a52b0323eed780db80050e5bbba5fd5dc37dd51"
STAGE65_BLOB = "0bd298c14d51f079c18d7f74dc8931bec4819396"
STAGE46_BLOB = "bec2751cbeaa5e0fc8c97dc0eb65dbbb7db65134"
GH_PAGES_HEAD = "ad8069aa5d47910fdcc54fc333de8185841a218f"
FAILURE_CLASS = "BGF-STAGE66-PRODUCTION-CANDIDATE-PIPELINE-GUARD-635"


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE66_PRODUCTION_RELEASE_CANDIDATE_EVIDENCE_PIPELINE=FAIL\n"
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
    stage65 = load(STAGE65)
    stage46 = load(STAGE46)

    if git_blob(STAGE65) != STAGE65_BLOB:
        fail("Stage65 sealed authority blob drift")
    if git_blob(STAGE46) != STAGE46_BLOB:
        fail("Stage46 production-deployment preparation authority blob drift")

    require(
        authority,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "stage": "STAGE66_PRODUCTION_RELEASE_CANDIDATE_EVIDENCE_PIPELINE",
            "baseline_main_sha": BASELINE_MAIN,
            "current_state": "PUBLIC_GH_PAGES_SURFACE_STALE_VS_CURRENT_MAIN_RELEASE_CANDIDATE_PIPELINE_PREPARED_NO_DEPLOYMENT_NO_GATE_PROMOTION",
        },
        "Stage66 authority",
    )
    require(
        stage65,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "stage": "STAGE65_STAGE64_FINAL_RECONCILIATION",
        },
        "Stage65 authority",
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

    assessment = authority.get("fresh_public_surface_read_only_assessment", {})
    require(
        assessment,
        {
            "official_route": "https://projetoscosanostra.github.io/FitNexus_Coach_BlackGold/",
            "https_reachable": True,
            "observed_document_title": "fitnexus_app",
            "gh_pages_branch": "gh-pages",
            "gh_pages_head_sha": GH_PAGES_HEAD,
            "current_main_sha": BASELINE_MAIN,
            "current_repo_web_contract_requires_title": "FitNexus Coach BlackGold",
            "current_repo_web_contract_rejects_title": "fitnexus_app",
            "public_surface_bound_to_current_main": False,
            "public_surface_can_satisfy_stage46_production_release_binding": False,
            "remote_mutation_performed": False,
        },
        "public surface assessment",
    )

    required_stage46 = stage46.get("required_real_evidence", {})
    for key in (
        "stable_production_domain",
        "tls_evidence_artifact",
        "environment_configuration_receipt_without_secrets",
        "release_commit_sha",
        "production_smoke_test_receipt",
        "rollback_test_receipt",
        "monitoring_alerting_readiness_receipt",
        "backup_restore_readiness_reference_artifact",
        "release_evidence_manifest_artifact",
    ):
        if not isinstance(required_stage46.get(key), dict) or required_stage46[key].get("required") is not True:
            fail(f"Stage46 required evidence drift: {key}")

    if stage46.get("gates", {}).get("production_deployment") != "DENIED_AWAITING_REAL_PRODUCTION_RELEASE_AND_OPERATIONS_EVIDENCE":
        fail("Stage46 production gate is no longer in the expected denied state")
    if stage65.get("gates", {}).get("production_deployment") != "DENIED":
        fail("Stage65 final reconciliation no longer preserves production deployment denial")

    index_text = WEB_INDEX.read_text(encoding="utf-8").lower()
    if "<title>fitnexus coach blackgold</title>" not in index_text:
        fail("current repository web shell branded title missing")
    if "<title>fitnexus_app</title>" in index_text:
        fail("current repository web shell regressed to stale public title")

    builder_text = BUILDER.read_text(encoding="utf-8")
    try:
        builder_tree = ast.parse(builder_text)
    except SyntaxError as exc:
        fail(f"builder syntax invalid: {exc.msg}")

    forbidden_import_roots = {"os", "subprocess", "socket", "urllib", "http", "requests"}
    for node in ast.walk(builder_tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".", 1)[0] in forbidden_import_roots:
                    fail(f"builder imports forbidden production/network module: {alias.name}")
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module.split(".", 1)[0] in forbidden_import_roots:
                fail(f"builder imports forbidden production/network module: {node.module}")

    for fragment in (
        "NON_ATTESTING_WEB_RELEASE_CANDIDATE_BUILD_MANIFEST",
        "BUILT_FROM_EXACT_SOURCE_SHA_NOT_DEPLOYED_NOT_PRODUCTION_EVIDENCE",
        "EXPECTED_BASE_HREF = \"/FitNexus_Coach_BlackGold/\"",
        "source_commit_sha",
        "aggregate_sha256",
        "deployment_performed\": False",
        "gh_pages_written\": False",
        "supabase_mutation_performed\": False",
        "production_deployment_gate_ready_attested\": False",
        "INDEPENDENT_DEPLOYMENT_PREREQUISITE_BINDING_REQUIRED_BEFORE_ANY_PUBLISH",
    ):
        if fragment not in builder_text:
            fail(f"builder invariant missing: {fragment}")

    workflow = WORKFLOW.read_text(encoding="utf-8")
    workflow_lower = workflow.lower()
    for fragment in (
        "permissions:\n  contents: read",
        "verify_stage66_production_release_candidate_evidence_pipeline.py",
        "verify_web_release_contract.py",
        "flutter analyze",
        "flutter test",
        "flutter build web --release --base-href /FitNexus_Coach_BlackGold/",
        "build_stage66_production_release_candidate_manifest.py",
        "actions/upload-artifact@v4",
        "retention-days: 7",
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

    pipeline = authority.get("pipeline_contract", {})
    require(
        pipeline,
        {
            "exact_source_sha_required": True,
            "flutter_analyze_required": True,
            "flutter_tests_required": True,
            "web_release_contract_guard_required": True,
            "manifest_records_file_sha256_and_size": True,
            "manifest_records_aggregate_sha256": True,
            "candidate_artifact_uploaded_to_ci": True,
            "candidate_artifact_is_production_evidence": False,
            "candidate_artifact_is_deployment_authority": False,
            "production_network_probe_allowed": False,
            "deployment_action_allowed": False,
            "gh_pages_write_allowed": False,
            "supabase_mutation_allowed": False,
            "evidence_migration_creation_allowed": False,
            "production_deployment_gate_promotion_allowed": False,
            "controlled_launch_promotion_allowed": False,
            "paid_media_promotion_allowed": False,
        },
        "pipeline contract",
    )

    if list((BACKEND / "migrations").glob("*stage66*.sql")):
        fail("Stage66 candidate pipeline must not create a migration")

    print("STAGE66_PRODUCTION_RELEASE_CANDIDATE_EVIDENCE_PIPELINE=PASS")
    print("PUBLIC_GH_PAGES_SURFACE_BOUND_TO_CURRENT_MAIN=false")
    print("RELEASE_CANDIDATE_PIPELINE=READY_FOR_CI")
    print("DEPLOYMENT_ACTION=false")
    print("REMOTE_MUTATION=false")
    print("PRODUCTION_DEPLOYMENT_GATE=BLOCKED")
    print("CONTROLLED_LAUNCH=DENIED")


if __name__ == "__main__":
    main()
