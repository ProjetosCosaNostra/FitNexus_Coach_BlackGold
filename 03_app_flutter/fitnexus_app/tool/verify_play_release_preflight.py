#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRADLE = ROOT / "android/app/build.gradle.kts"
PUBSPEC = ROOT / "pubspec.yaml"
APP_ROUTES = ROOT / "lib/app/fitnexus_app.dart"
LANDING = ROOT / "lib/features/landing/responsive_landing_page.dart"
SUBSCRIPTION_REPO = ROOT / "lib/features/professor/professor_subscription_repository.dart"
SUBSCRIPTION_PAGE = ROOT / "lib/features/professor/professor_subscription_page.dart"
AUTHORITY = ROOT / "android/PLAY_RELEASE_AUTHORITY_V1.json"


def read(path: Path) -> str:
    if not path.exists():
        raise SystemExit(f"PLAY_RELEASE_PREFLIGHT=FAIL::missing::{path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def check(name: str, ok: bool, detail: str, *, blocker: bool = False) -> dict:
    return {
        "name": name,
        "passed": bool(ok),
        "blocker": bool(blocker and not ok),
        "detail": detail,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("inventory", "publish-gate"), default="inventory")
    args = parser.parse_args()

    gradle = read(GRADLE)
    pubspec = read(PUBSPEC)
    routes = read(APP_ROUTES)
    landing = read(LANDING)
    subscription_repo = read(SUBSCRIPTION_REPO)
    subscription_page = read(SUBSCRIPTION_PAGE)
    authority = json.loads(read(AUTHORITY))

    app_id_match = re.search(r'applicationId\s*=\s*"([^"]+)"', gradle)
    app_id = app_id_match.group(1) if app_id_match else ""
    placeholder_id = (not app_id) or app_id.startswith("com.example")
    debug_release_signing = 'signingConfig = signingConfigs.getByName("debug")' in gradle
    version_match = re.search(r"^version:\s*([^\s]+)", pubspec, flags=re.MULTILINE)
    version = version_match.group(1) if version_match else "UNKNOWN"

    required_routes = ("/start", "/professor", "/student", "/support")
    routes_ready = all(f"'{route}'" in routes for route in required_routes)
    free_entry_ready = "Começar grátis" in landing and "pushNamed('/start')" in landing
    entitlement_ready = (
        "get_subscription_entitlement_snapshot" in subscription_repo
        and "subscription_plans" in subscription_repo
        and "trial_days" in subscription_repo
    )
    billing_guardrails_ready = (
        "checkoutReady" in subscription_page
        and "Nenhum segredo foi exposto ao aplicativo" in subscription_page
        and "O Flutter não pode informar o valor ao checkout" in subscription_page
    )

    checks = [
        check("android_project", GRADLE.exists(), "Android Flutter project exists."),
        check("canonical_application_id", not placeholder_id, f"applicationId={app_id or 'MISSING'}", blocker=True),
        check("production_release_signing", not debug_release_signing, "Release signing must not use debug keys.", blocker=True),
        check("version_declared", version != "UNKNOWN", f"pubspec version={version}", blocker=True),
        check("core_routes", routes_ready, f"Required routes={','.join(required_routes)}", blocker=True),
        check("free_entry", free_entry_ready, "Public free-start CTA routes to registration.", blocker=True),
        check("server_entitlements", entitlement_ready, "Trial, plan catalog and entitlement snapshot are server-backed.", blocker=True),
        check("billing_client_guardrails", billing_guardrails_ready, "Client does not invent price/provider secrets and keeps checkout gated.", blocker=True),
        check(
            "play_payment_strategy",
            authority["distribution_model"]["in_app_external_provider_checkout_enabled"] is False
            and authority["distribution_model"]["external_billing_link_from_play_app_enabled"] is False,
            "External-provider in-app checkout/linking remains fail-closed pending policy-compliant implementation.",
            blocker=True,
        ),
        check(
            "play_public_upload_authority",
            authority["release_signing"]["public_upload_authorized"] is True,
            "Explicit publication authority is required before upload.",
            blocker=True,
        ),
    ]

    blockers = [item for item in checks if item["blocker"]]
    passed = sum(1 for item in checks if item["passed"])
    score = round(passed / len(checks) * 100)

    print("PLAY_RELEASE_PREFLIGHT=INVENTORY")
    print(f"APPLICATION_ID={app_id or 'MISSING'}")
    print(f"VERSION={version}")
    print(f"CHECKS_PASSED={passed}/{len(checks)}")
    print(f"PREFLIGHT_SCORE={score}%")
    print(f"PUBLICATION_BLOCKERS={len(blockers)}")
    for item in checks:
        state = "PASS" if item["passed"] else ("BLOCK" if item["blocker"] else "WARN")
        print(f"{state}::{item['name']}::{item['detail']}")

    if args.mode == "publish-gate" and blockers:
        raise SystemExit("PLAY_RELEASE_PREFLIGHT=BLOCKED")

    if args.mode == "publish-gate":
        print("PLAY_RELEASE_PREFLIGHT=GREEN_FOR_UPLOAD_PRECONDITIONS")


if __name__ == "__main__":
    main()
