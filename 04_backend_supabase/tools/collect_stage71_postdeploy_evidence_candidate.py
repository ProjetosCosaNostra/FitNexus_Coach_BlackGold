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
    "live_tls_receipt",
    "production_smoke_receipt",
    "postdeploy_rollback_receipt",
    "monitoring_alerting_live_receipt",
    "final_release_evidence_manifest",
)
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", re.IGNORECASE),
    re.compile(r"\b(?:password|passwd|api[_-]?key|access[_-]?token|service[_-]?role[_-]?key|client[_-]?secret|secret[_-]?value)\s*[:=]\s*[^\s,}\]]+", re.IGNORECASE),
)
FAILURE_CLASS = "BGF-STAGE71-POSTDEPLOY-INTAKE-GUARD-685"


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE71_POSTDEPLOY_EVIDENCE_INTAKE=FAIL\n"
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


def validate_receipt_artifact(path: Path, label: str) -> str:
    if not path.is_file() or path.stat().st_size <= 0:
        fail(f"{label} must be a real non-empty file")
    if path.stat().st_size > 8 * 1024 * 1024:
        fail(f"{label} exceeds 8 MiB intake boundary")
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        fail(f"{label} must be UTF-8 text for secret-marker inspection")
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            fail(f"{label} contains a secret-like marker; redact before intake")
    return sha256_file(path)


def validate_postdeploy_input(path: Path) -> tuple[str, str, dict[str, str], str]:
    value = load_json(path, "postdeploy input")
    if value.get("schema_version") != 1:
        fail("postdeploy schema_version must be 1")
    if value.get("input_kind") != "REAL_POSTDEPLOY_EVIDENCE_INPUT":
        fail("postdeploy input_kind drift")
    if value.get("test_fixture") is not False:
        fail("postdeploy input is a test fixture; real receipts are required")
    if value.get("contains_placeholders") is not False:
        fail("postdeploy input still contains placeholders")
    if value.get("operator_acknowledged") is not True:
        fail("real operator acknowledgment is required")
    if PLACEHOLDER_RE.search(str(value.get("status", ""))):
        fail("postdeploy input status remains placeholder-like")

    deployed_sha = str(value.get("deployed_release_sha", "")).strip().lower()
    if not SHA1_RE.fullmatch(deployed_sha):
        fail("deployed_release_sha must be exact 40-character lower-hex Git SHA")
    domain = str(value.get("stable_production_domain", "")).strip()
    if not DOMAIN_RE.fullmatch(domain) or PLACEHOLDER_RE.search(domain):
        fail("stable production domain must be a real HTTPS URL")
    lowered = domain.lower()
    for forbidden in ("localhost", "127.0.0.1", "staging", "preview", "example.", ".test", ".invalid"):
        if forbidden in lowered:
            fail("stable production domain uses a forbidden local/staging/example marker")

    artifacts = value.get("artifacts")
    if not isinstance(artifacts, dict) or set(artifacts) != set(ARTIFACT_KEYS):
        fail("postdeploy artifacts must contain exactly the required five keys")
    digests: dict[str, str] = {}
    for key in ARTIFACT_KEYS:
        raw = str(artifacts.get(key, "")).strip()
        if not raw or PLACEHOLDER_RE.search(raw):
            fail(f"postdeploy artifact path missing or placeholder: {key}")
        digests[key] = validate_receipt_artifact(Path(raw).expanduser().resolve(), key)
    return deployed_sha, domain, digests, sha256_file(path)


def validate_predeploy_binding(path: Path, deployed_sha: str, domain: str) -> tuple[dict, str]:
    value = load_json(path, "Stage70 predeploy binding")
    if value.get("schema_version") != 1:
        fail("Stage70 predeploy binding schema drift")
    if value.get("stage") != "STAGE70_PRODUCTION_PREDEPLOY_PREREQUISITE_INTERLOCK":
        fail("Stage70 predeploy binding stage drift")
    if value.get("output_kind") != "NON_ATTESTING_PRODUCTION_PREDEPLOY_BINDING_CANDIDATE":
        fail("Stage70 predeploy binding output_kind drift")
    if value.get("candidate_state") != "PREDEPLOY_PREREQUISITES_HASH_BOUND_TO_EXACT_RELEASE_CANDIDATE_NOT_DEPLOYED_NOT_PRODUCTION_EVIDENCE":
        fail("Stage70 predeploy binding state drift")
    if value.get("source_commit_sha") != deployed_sha:
        fail("deployed release SHA does not match Stage70 source candidate")
    if value.get("stable_production_domain") != domain:
        fail("postdeploy domain does not match Stage70 predeploy domain")
    if not SHA256_RE.fullmatch(str(value.get("release_candidate_aggregate_sha256", ""))):
        fail("Stage70 release candidate aggregate digest invalid")
    for key in (
        "artifact_paths_copied_to_receipt",
        "artifact_contents_copied_to_receipt",
        "secret_values_copied_to_receipt",
        "network_probe_performed",
        "deployment_performed",
        "gh_pages_written",
        "supabase_mutation_performed",
        "provider_call_performed",
        "production_smoke_performed",
        "production_evidence_attested",
        "evidence_migration_created",
        "production_deployment_gate_ready_attested",
        "controlled_launch_promoted",
        "paid_media_promoted",
    ):
        if value.get(key) is not False:
            fail(f"Stage70 predeploy binding boundary drift: {key}")
    return value, sha256_file(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predeploy-binding", required=True, type=Path)
    parser.add_argument("--postdeploy-input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    deployed_sha, domain, receipt_digests, input_sha = validate_postdeploy_input(args.postdeploy_input.resolve())
    predeploy, predeploy_sha = validate_predeploy_binding(args.predeploy_binding.resolve(), deployed_sha, domain)

    receipt = {
        "schema_version": 1,
        "stage": "STAGE71_POSTDEPLOY_EVIDENCE_INTAKE_CONTRACT",
        "output_kind": "DIGEST_ONLY_POSTDEPLOY_EVIDENCE_INTAKE_CANDIDATE",
        "candidate_state": "REAL_RECEIPT_DIGESTS_BOUND_AWAITING_INDEPENDENT_REVIEW_NOT_GATE_EVIDENCE",
        "deployed_release_sha": deployed_sha,
        "stable_production_domain": domain,
        "release_candidate_aggregate_sha256": predeploy.get("release_candidate_aggregate_sha256"),
        "predeploy_binding_sha256": predeploy_sha,
        "postdeploy_input_sha256": input_sha,
        "postdeploy_receipt_sha256": receipt_digests,
        "artifact_paths_copied_to_receipt": False,
        "artifact_contents_copied_to_receipt": False,
        "secret_values_copied_to_receipt": False,
        "network_call_performed": False,
        "deployment_performed_by_collector": False,
        "supabase_mutation_performed": False,
        "provider_call_performed": False,
        "production_gate_ready_attested": False,
        "evidence_migration_created": False,
        "controlled_launch_promoted": False,
        "paid_media_promoted": False,
        "independent_review_required": True,
        "next_action": "INDEPENDENTLY_REVIEW_REAL_POSTDEPLOY_SOURCE_ARTIFACTS_BEFORE_ANY_EVIDENCE_MIGRATION",
    }

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("STAGE71_POSTDEPLOY_EVIDENCE_INTAKE=PASS_CANDIDATE_ONLY")
    print(f"DEPLOYED_RELEASE_SHA={deployed_sha}")
    print(f"DOMAIN={domain}")
    print("ARTIFACT_PATHS_COPIED=false")
    print("DEPLOYMENT_PERFORMED_BY_COLLECTOR=false")
    print("PRODUCTION_GATE_READY=false")
    print("INDEPENDENT_REVIEW_REQUIRED=true")
    print("REMOTE_MUTATION=false")


if __name__ == "__main__":
    main()
