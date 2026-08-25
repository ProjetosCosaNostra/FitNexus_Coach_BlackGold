from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "03_app_flutter" / "fitnexus_app"
BUILD_WEB = APP / "build" / "web"
EXPECTED_BASE_HREF = "/FitNexus_Coach_BlackGold/"
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
FAILURE_CLASS = "BGF-STAGE66-BUILD-MANIFEST-NONDETERMINISM-630"
FORBIDDEN_PATH_FRAGMENTS = (
    ".env",
    "credentials",
    "private_key",
    "service_role",
    "secret_value",
)


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE66_PRODUCTION_RELEASE_CANDIDATE_MANIFEST=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\n"
        f"DETAIL={detail}"
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    source_sha = args.source_sha.strip().lower()
    if not SHA1_RE.fullmatch(source_sha):
        fail("--source-sha must be the exact 40-character lower-hex Git commit SHA")

    if not BUILD_WEB.is_dir():
        fail("Flutter web release build is missing; run flutter build web --release first")

    index = BUILD_WEB / "index.html"
    if not index.is_file():
        fail("build/web/index.html missing")
    index_text = index.read_text(encoding="utf-8")
    if not re.search(
        r'<base\s+href=["\']' + re.escape(EXPECTED_BASE_HREF) + r'["\']\s*/?>',
        index_text,
        flags=re.IGNORECASE,
    ):
        fail(f"built index is not bound to base href {EXPECTED_BASE_HREF}")

    entries: list[dict[str, object]] = []
    for path in sorted(p for p in BUILD_WEB.rglob("*") if p.is_file()):
        relative = path.relative_to(BUILD_WEB).as_posix()
        lowered = relative.lower()
        if any(fragment in lowered for fragment in FORBIDDEN_PATH_FRAGMENTS):
            fail(f"secret-bearing or configuration-sensitive path present in build: {relative}")
        entries.append(
            {
                "path": relative,
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )

    if not entries:
        fail("build/web contains no files")

    aggregate = hashlib.sha256()
    for entry in entries:
        aggregate.update(str(entry["path"]).encode("utf-8"))
        aggregate.update(b"\0")
        aggregate.update(str(entry["size"]).encode("ascii"))
        aggregate.update(b"\0")
        aggregate.update(str(entry["sha256"]).encode("ascii"))
        aggregate.update(b"\n")

    manifest = {
        "schema_version": 1,
        "stage": "STAGE66_PRODUCTION_RELEASE_CANDIDATE_EVIDENCE_PIPELINE",
        "output_kind": "NON_ATTESTING_WEB_RELEASE_CANDIDATE_BUILD_MANIFEST",
        "candidate_state": "BUILT_FROM_EXACT_SOURCE_SHA_NOT_DEPLOYED_NOT_PRODUCTION_EVIDENCE",
        "source_commit_sha": source_sha,
        "base_href": EXPECTED_BASE_HREF,
        "build_root": "03_app_flutter/fitnexus_app/build/web",
        "file_count": len(entries),
        "aggregate_sha256": aggregate.hexdigest(),
        "files": entries,
        "network_production_probe_performed": False,
        "deployment_performed": False,
        "gh_pages_written": False,
        "supabase_mutation_performed": False,
        "evidence_migration_created": False,
        "production_deployment_gate_ready_attested": False,
        "controlled_launch_promoted": False,
        "paid_media_promoted": False,
        "next_action": "INDEPENDENT_DEPLOYMENT_PREREQUISITE_BINDING_REQUIRED_BEFORE_ANY_PUBLISH",
    }

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("STAGE66_PRODUCTION_RELEASE_CANDIDATE_MANIFEST=PASS_CANDIDATE_ONLY")
    print(f"SOURCE_SHA={source_sha}")
    print(f"FILE_COUNT={len(entries)}")
    print(f"AGGREGATE_SHA256={manifest['aggregate_sha256']}")
    print("DEPLOYMENT_PERFORMED=false")
    print("PRODUCTION_DEPLOYMENT_GATE_READY=false")


if __name__ == "__main__":
    main()
