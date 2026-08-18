from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
IDENTITY_PATH = ROOT / "04_backend_supabase" / "project_identity.json"
DART_CONFIG_PATH = (
    ROOT
    / "03_app_flutter"
    / "fitnexus_app"
    / "lib"
    / "core"
    / "config"
    / "supabase_config.dart"
)


def fail(message: str) -> None:
    raise SystemExit(f"SUPABASE_PROJECT_IDENTITY_GUARD=FAIL\n{message}")


def main() -> None:
    identity = json.loads(IDENTITY_PATH.read_text(encoding="utf-8"))
    config = DART_CONFIG_PATH.read_text(encoding="utf-8")

    project_ref = str(identity.get("project_ref", "")).strip()
    project_url = str(identity.get("project_url", "")).strip().rstrip("/")
    project_name = str(identity.get("project_name", "")).strip()

    if not re.fullmatch(r"[a-z0-9]{20}", project_ref):
        fail("project_identity.json contains an invalid Supabase project_ref")

    expected_url = f"https://{project_ref}.supabase.co"
    if project_url != expected_url:
        fail(
            "project_identity.json project_url does not match project_ref: "
            f"expected={expected_url} actual={project_url}"
        )

    match = re.search(
        r"static\s+const\s+String\s+url\s*=\s*'([^']+)'",
        config,
    )
    if match is None:
        fail("Flutter Supabase config URL could not be resolved")

    flutter_url = match.group(1).strip().rstrip("/")
    if flutter_url != project_url:
        fail(
            "Flutter Supabase config points at a different project: "
            f"manifest={project_url} flutter={flutter_url}"
        )

    if project_ref not in flutter_url:
        fail("Flutter Supabase config does not contain the authoritative project_ref")

    print("SUPABASE_PROJECT_IDENTITY_GUARD=PASS")
    print(f"PROJECT_NAME={project_name}")
    print(f"PROJECT_REF={project_ref}")
    print(f"PROJECT_URL={project_url}")


if __name__ == "__main__":
    main()
