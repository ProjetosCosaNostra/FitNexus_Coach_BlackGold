#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
GRADLE = ROOT / "android/app/build.gradle.kts"
MANIFEST = ROOT / "android/app/src/main/AndroidManifest.xml"
PUBSPEC = ROOT / "pubspec.yaml"
APP_ROUTES = ROOT / "lib/app/fitnexus_app.dart"
LANDING = ROOT / "lib/features/landing/responsive_landing_page.dart"
SUBSCRIPTION_REPO = ROOT / "lib/features/professor/professor_subscription_repository.dart"
SUBSCRIPTION_PAGE = ROOT / "lib/features/professor/professor_subscription_page.dart"
AUTHORITY = ROOT / "android/PLAY_RELEASE_AUTHORITY_V1.json"
SIGNED_AAB_CONTRACT = ROOT / "android/PLAY_SIGNED_AAB_RUNNER_V1.json"
SIGNED_AAB_RUNNER = ROOT / "tool/FITNEXUS_PLAY_SIGNED_AAB_RUNNER_V1.ps1"
GITIGNORE = REPO_ROOT / ".gitignore"


def read(path: Path) -> str:
    if not path.exists():
        try:
            relative = path.relative_to(REPO_ROOT)
        except ValueError:
            relative = path
        raise SystemExit(f"PLAY_RELEASE_PREFLIGHT=FAIL::missing::{relative}")
    return path.read_text(encoding="utf-8-sig")


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
    manifest = read(MANIFEST)
    pubspec = read(PUBSPEC)
    routes = read(APP_ROUTES)
    landing = read(LANDING)
    subscription_repo = read(SUBSCRIPTION_REPO)
    subscription_page = read(SUBSCRIPTION_PAGE)
    authority = json.loads(read(AUTHORITY))
    signed_aab_contract = json.loads(read(SIGNED_AAB_CONTRACT))
    signed_aab_runner = read(SIGNED_AAB_RUNNER)
    gitignore = read(GITIGNORE)

    app_id_match = re.search(r'applicationId\s*=\s*"([^"]+)"', gradle)
    app_id = app_id_match.group(1) if app_id_match else ""
    namespace_match = re.search(r'namespace\s*=\s*"([^"]+)"', gradle)
    namespace = namespace_match.group(1) if namespace_match else ""
    placeholder_id = (not app_id) or app_id.startswith("com.example")
    debug_release_signing = 'signingConfig = signingConfigs.getByName("debug")' in gradle
    secure_external_signing_wiring = all(
        token in gradle
        for token in (
            'rootProject.file("key.properties")',
            "releaseSigningConfigured",
            'create("release")',
            'signingConfig = signingConfigs.getByName("release")',
        )
    )
    key_properties_ignored = "**/key.properties" in gitignore or "key.properties" in gitignore.splitlines()
    keystore_extensions_ignored = "*.jks" in gitignore and "*.keystore" in gitignore
    version_match = re.search(r"^version:\s*([^\s]+)", pubspec, flags=re.MULTILINE)
    version = version_match.group(1) if version_match else "UNKNOWN"

    package_authority = authority.get("package_identity", {})
    canonical_id = str(package_authority.get("canonical_application_id") or "")
    authority_current_id = str(package_authority.get("current_application_id") or "")
    release_train = authority.get("release_train", {})
    authority_version = str(release_train.get("current_version") or "")
    release_signing = authority.get("release_signing", {})

    runner_contract_ready = (
        signed_aab_contract.get("kind") == "NON_ATTESTING_SIGNED_AAB_RUNNER_CONTRACT"
        and signed_aab_contract.get("runner", {}).get("single_command_required") is True
        and signed_aab_contract.get("runner", {}).get("validate_only_mode_required") is True
        and signed_aab_contract.get("secret_boundary", {}).get("upload_key_repository_storage_allowed") is False
        and signed_aab_contract.get("secret_boundary", {}).get("plaintext_password_repository_storage_allowed") is False
        and signed_aab_contract.get("secret_boundary", {}).get("persistent_password_storage") == "WINDOWS_DPAPI_CURRENT_USER"
        and signed_aab_contract.get("secret_boundary", {}).get("transient_key_properties_cleanup_required") is True
        and signed_aab_contract.get("publication_boundary", {}).get("play_upload_performed_by_runner") is False
    )
    runner_static_ready = all(
        token in signed_aab_runner
        for token in (
            "FITNEXUS_SIGNED_AAB_RUNNER=PASS",
            "ConvertFrom-SecureString",
            "flutter build appbundle --release",
            "jarsigner -verify",
            "Get-FileHash",
            "PLAY_UPLOAD_PERFORMED=false",
            "Remove-Item -LiteralPath $KeyPropertiesFile",
        )
    )

    activity_path = ROOT / "android/app/src/main/kotlin" / Path(*app_id.split(".")) / "MainActivity.kt"
    activity = read(activity_path) if app_id and activity_path.exists() else ""
    activity_package_match = re.search(r"^package\s+([^\s]+)", activity, flags=re.MULTILINE)
    activity_package = activity_package_match.group(1) if activity_package_match else ""

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
        check(
            "canonical_application_id",
            not placeholder_id and app_id == canonical_id == authority_current_id,
            f"applicationId={app_id or 'MISSING'} authority={canonical_id or 'MISSING'}",
            blocker=True,
        ),
        check(
            "namespace_alignment",
            bool(namespace) and namespace == app_id,
            f"namespace={namespace or 'MISSING'} applicationId={app_id or 'MISSING'}",
            blocker=True,
        ),
        check(
            "main_activity_package_alignment",
            bool(activity_package) and activity_package == app_id,
            f"MainActivity package={activity_package or 'MISSING'}",
            blocker=True,
        ),
        check(
            "production_app_label",
            'android:label="FitNexus Coach BlackGold"' in manifest,
            "Android application label must expose the production product name.",
            blocker=True,
        ),
        check(
            "debug_release_signing_removed",
            not debug_release_signing and release_signing.get("debug_signing_used_for_release") is False,
            "Release build must never fall back to the Android debug key.",
            blocker=True,
        ),
        check(
            "external_upload_key_wiring",
            secure_external_signing_wiring
            and release_signing.get("current_state") == "EXTERNAL_UPLOAD_KEY_WIRING_READY_CREDENTIALS_ABSENT",
            "Gradle must consume an external android/key.properties file only when present.",
            blocker=True,
        ),
        check(
            "signing_secret_hygiene",
            key_properties_ignored
            and keystore_extensions_ignored
            and release_signing.get("external_key_properties_must_remain_untracked") is True
            and release_signing.get("upload_key_material_present_in_repository") is False,
            "Signing properties and keystore material must remain outside Git authority.",
            blocker=True,
        ),
        check(
            "one_command_signed_aab_runner",
            runner_contract_ready and runner_static_ready,
            "One command must create/reuse the external upload key, build a signed AAB, verify it and emit a receipt without uploading it.",
            blocker=True,
        ),
        check(
            "release_train_version",
            version != "UNKNOWN" and version == authority_version and version != "0.1.0+1",
            f"pubspec version={version}; authority version={authority_version or 'MISSING'}",
            blocker=True,
        ),
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
            "signed_aab_attestation",
            release_signing.get("signed_aab_proof") == "ATTESTED",
            "A signed AAB produced with the external upload key has not been attested yet.",
            blocker=True,
        ),
        check(
            "play_app_signing_enrollment",
            release_signing.get("play_app_signing_enrollment") == "ATTESTED",
            "Play App Signing enrollment remains an external Play Console fact.",
            blocker=True,
        ),
        check(
            "play_console_uniqueness_attestation",
            package_authority.get("play_console_uniqueness_attested") is True,
            "Repository package selection does not prove Play Console uniqueness/ownership.",
            blocker=True,
        ),
        check(
            "play_public_upload_authority",
            release_signing.get("public_upload_authorized") is True,
            "Explicit publication authority is required before upload.",
            blocker=True,
        ),
    ]

    blockers = [item for item in checks if item["blocker"]]
    passed = sum(1 for item in checks if item["passed"])
    score = round(passed / len(checks) * 100)

    print("PLAY_RELEASE_PREFLIGHT=INVENTORY")
    print(f"APPLICATION_ID={app_id or 'MISSING'}")
    print(f"NAMESPACE={namespace or 'MISSING'}")
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
