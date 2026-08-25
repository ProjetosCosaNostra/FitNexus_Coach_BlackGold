from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
PLACEHOLDER_RE = re.compile(r"<[^>]+>|placeholder|tbd|to[_ -]?be[_ -]?defined|example", re.IGNORECASE)
DOMAIN_RE = re.compile(r"^https://[A-Za-z0-9.-]+(?::\d+)?(?:/[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]*)?$")
ARTIFACT_KEYS = (
    "tls_baseline",
    "environment_readiness_without_secrets",
    "rollback_readiness",
    "monitoring_alerting_readiness",
    "backup_restore_readiness",
    "deployment_destination_control",
)
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", re.IGNORECASE),
    re.compile(r"\b(?:password|passwd|api[_-]?key|access[_-]?token|service[_-]?role[_-]?key|client[_-]?secret|secret[_-]?value)\s*[:=]\s*[^\s,}\]]+", re.IGNORECASE),
)
FAILURE_CLASS = "BGF-STAGE70-PREDEPLOY-INTERLOCK-GUARD-675"


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE70_PRODUCTION_PREDEPLOY_PREREQUISITE_BINDING=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\n"
        f"DETAIL={detail}"
    )


def load_json(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to load {label}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"{label} must be a JSON object")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_text_artifact(path: Path, label: str) -> str:
    if not path.is_file() or path.stat().st_size <= 0:
        fail(f"{label} must be a real non-empty file")
    if path.stat().st_size > 8 * 1024 * 1024:
        fail(f"{label} exceeds 8 MiB predeploy evidence boundary")
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        fail(f"{label} must be UTF-8 text so the predeploy secret-marker guard can inspect it")
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            fail(f"{label} contains a secret-like marker; redact before binding")
    return sha256_file(path)


def validate_candidate_manifest(path: Path, source_sha: str) -> tuple[dict, str]:
    manifest = load_json(path, "Stage66 candidate manifest")
    if manifest.get("schema_version") != 1:
        fail("Stage66 candidate manifest schema drift")
    if manifest.get("stage") != "STAGE66_PRODUCTION_RELEASE_CANDIDATE_EVIDENCE_PIPELINE":
        fail("Stage66 candidate manifest stage drift")
    if manifest.get("output_kind") != "NON_ATTESTING_WEB_RELEASE_CANDIDATE_BUILD_MANIFEST":
        fail("Stage66 candidate manifest output_kind drift")
    if manifest.get("candidate_state") != "BUILT_FROM_EXACT_SOURCE_SHA_NOT_DEPLOYED_NOT_PRODUCTION_EVIDENCE":
        fail("Stage66 candidate manifest state drift")
    if manifest.get("source_commit_sha") != source_sha:
        fail("Stage66 candidate source SHA mismatch")
    if manifest.get("base_href") != "/FitNexus_Coach_BlackGold/":
        fail("Stage66 candidate base href drift")
    if not isinstance(manifest.get("file_count"), int) or manifest["file_count"] <= 0:
        fail("Stage66 candidate file_count invalid")
    if not SHA256_RE.fullmatch(str(manifest.get("aggregate_sha256", ""))):
        fail("Stage66 candidate aggregate SHA-256 invalid")
    for key in (
        "network_production_probe_performed",
        "deployment_performed",
        "gh_pages_written",
        "supabase_mutation_performed",
        "evidence_migration_created",
        "production_deployment_gate_ready_attested",
        "controlled_launch_promoted",
        "paid_media_promoted",
    ):
        if manifest.get(key) is not False:
            fail(f"Stage66 candidate boundary drift: {key}")
    return manifest, sha256_file(path)


def validate_prerequisites(path: Path) -> tuple[str, dict[str, str], str]:
    value = load_json(path, "predeploy prerequisite input")
    if value.get("schema_version") != 1:
        fail("prerequisite schema_version must be 1")
    if value.get("input_kind") != "REAL_PRODUCTION_PREDEPLOY_PREREQUISITE_INPUT":
        fail("prerequisite input_kind drift")
    if value.get("test_fixture") is not False:
        fail("predeploy input is a test fixture; real operational prerequisites are required")
    if value.get("contains_placeholders") is not False:
        fail("predeploy input still contains placeholders")
    if value.get("operator_acknowledged") is not True:
        fail("real operator acknowledgment is required")
    if PLACEHOLDER_RE.search(str(value.get("status", ""))):
        fail("predeploy input status remains placeholder-like")

    domain = str(value.get("stable_production_domain", "")).strip()
    if not DOMAIN_RE.fullmatch(domain) or PLACEHOLDER_RE.search(domain):
        fail("stable production domain must be a real HTTPS URL")
    lowered = domain.lower()
    for forbidden in ("localhost", "127.0.0.1", "staging", "preview", "example.", ".test", ".invalid"):
        if forbidden in lowered:
            fail("stable production domain uses a forbidden local/staging/example marker")

    artifacts = value.get("artifacts")
    if not isinstance(artifacts, dict) or set(artifacts) != set(ARTIFACT_KEYS):
        fail("predeploy artifacts must contain exactly the required six keys")
    digests: dict[str, str] = {}
    for key in ARTIFACT_KEYS:
        raw = str(artifacts.get(key, "")).strip()
        if not raw or PLACEHOLDER_RE.search(raw):
            fail(f"predeploy artifact path missing or placeholder: {key}")
        artifact = Path(raw).expanduser().resolve()
        digests[key] = validate_text_artifact(artifact, key)
    return domain, digests, sha256_file(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--candidate-manifest", required=True, type=Path)
    parser.add_argument("--prerequisite-input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    source_sha = args.source_sha.strip().lower()
    if not SHA1_RE.fullmatch(source_sha):
        fail("--source-sha must be exact 40-character lower-hex Git SHA")

    candidate, candidate_file_sha = validate_candidate_manifest(args.candidate_manifest.resolve(), source_sha)
    domain, prerequisite_digests, prerequisite_input_sha = validate_prerequisites(args.prerequisite_input.resolve())

    receipt = {
        "schema_version": 1,
        "stage": "STAGE70_PRODUCTION_PREDEPLOY_PREREQUISITE_INTERLOCK",
        "output_kind": "NON_ATTESTING_PRODUCTION_PREDEPLOY_BINDING_CANDIDATE",
        "candidate_state": "PREDEPLOY_PREREQUISITES_HASH_BOUND_TO_EXACT_RELEASE_CANDIDATE_NOT_DEPLOYED_NOT_PRODUCTION_EVIDENCE",
        "source_commit_sha": source_sha,
        "stable_production_domain": domain,
        "release_candidate_manifest_file_sha256": candidate_file_sha,
        "release_candidate_aggregate_sha256": candidate.get("aggregate_sha256"),
        "predeploy_input_sha256": prerequisite_input_sha,
        "predeploy_artifact_sha256": prerequisite_digests,
        "artifact_paths_copied_to_receipt": False,
        "artifact_contents_copied_to_receipt": False,
        "secret_values_copied_to_receipt": False,
        "network_probe_performed": False,
        "deployment_performed": False,
        "gh_pages_written": False,
        "supabase_mutation_performed": False,
        "provider_call_performed": False,
        "production_smoke_performed": False,
        "production_evidence_attested": False,
        "evidence_migration_created": False,
        "production_deployment_gate_ready_attested": False,
        "controlled_launch_promoted": False,
        "paid_media_promoted": False,
        "next_action": "EXPLICIT_DEPLOYMENT_AUTHORIZATION_AND_POSTDEPLOY_EVIDENCE_COLLECTION_REQUIRED_BEFORE_PRODUCTION_GATE_REVIEW",
    }

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("STAGE70_PRODUCTION_PREDEPLOY_PREREQUISITE_BINDING=PASS_CANDIDATE_ONLY")
    print(f"SOURCE_SHA={source_sha}")
    print(f"DOMAIN={domain}")
    print("ARTIFACT_PATHS_COPIED=false")
    print("DEPLOYMENT_PERFORMED=false")
    print("PRODUCTION_SMOKE_PERFORMED=false")
    print("PRODUCTION_EVIDENCE=false")
    print("PRODUCTION_DEPLOYMENT_GATE_READY=false")
    print("REMOTE_MUTATION=false")


if __name__ == "__main__":
    main()
