from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "03_app_flutter" / "fitnexus_app" / "web"
INDEX = WEB / "index.html"
MANIFEST = WEB / "manifest.json"

EXPECTED_ICONS = {
    "icons/Icon-192.png",
    "icons/Icon-512.png",
    "icons/Icon-maskable-192.png",
    "icons/Icon-maskable-512.png",
}


def fail(detail: str) -> None:
    raise SystemExit(
        "WEB_RELEASE_CONTRACT_GUARD=FAIL\n"
        "FAILURE_CLASS=BGF-WEB-PWA-RELEASE-CONTRACT-146\n"
        f"DETAIL={detail}"
    )


def main() -> None:
    if not INDEX.is_file():
        fail("web/index.html missing")
    if not MANIFEST.is_file():
        fail("web/manifest.json missing while index references it")

    index = INDEX.read_text(encoding="utf-8")
    lower = index.lower()
    if '<base href="$flutter_base_href">' not in lower:
        fail("Flutter base href placeholder missing")
    if 'name="robots" content="noindex, nofollow, noarchive, nosnippet"' not in lower:
        fail("controlled launch is blocked; web shell must remain noindex")
    if "<title>fitnexus coach blackgold</title>" not in lower:
        fail("branded document title missing")
    if "a new flutter project" in lower or "<title>fitnexus_app</title>" in lower:
        fail("default Flutter placeholder metadata returned")
    if 'rel="manifest" href="manifest.json"' not in lower:
        fail("manifest link missing")
    if 'rel="icon" type="image/png" href="icons/icon-192.png"' not in lower:
        fail("favicon must resolve to an existing tracked icon")

    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"manifest.json invalid JSON: {exc}")
    if not isinstance(manifest, dict):
        fail("manifest root must be an object")

    if manifest.get("name") != "FitNexus Coach BlackGold":
        fail("manifest name drifted")
    if manifest.get("short_name") != "FitNexus":
        fail("manifest short_name drifted")
    if manifest.get("start_url") != "." or manifest.get("scope") != ".":
        fail("PWA start_url/scope must remain base-path safe")
    if manifest.get("display") != "standalone":
        fail("PWA display must remain standalone")

    icons = manifest.get("icons")
    if not isinstance(icons, list) or len(icons) < 4:
        fail("manifest must define regular and maskable 192/512 icons")
    icon_sources = {str(icon.get("src", "")) for icon in icons if isinstance(icon, dict)}
    if icon_sources != EXPECTED_ICONS:
        fail(f"manifest icon set drifted: {sorted(icon_sources)}")
    for relative in EXPECTED_ICONS:
        if not (WEB / relative).is_file():
            fail(f"manifest icon target missing: {relative}")

    print("WEB_RELEASE_CONTRACT_GUARD=PASS")
    print("PWA_MANIFEST=READY_FOR_BUILD")
    print("CONTROLLED_LAUNCH_INDEXING=NOINDEX")
    print("PRODUCTION_DEPLOYMENT_GATE=UNCHANGED_BLOCKED")


if __name__ == "__main__":
    main()
