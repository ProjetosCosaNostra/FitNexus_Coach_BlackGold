#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "android/play_store/PLAY_STORE_PUBLICATION_PACK_V1.json"
SHOTLIST = ROOT / "android/play_store/PLAY_STORE_SCREENSHOT_SHOTLIST_V1.md"
DATA_SAFETY = ROOT / "android/play_store/PLAY_DATA_SAFETY_INVENTORY_V1.md"
PUBSPEC = ROOT / "pubspec.yaml"
GRADLE = ROOT / "android/app/build.gradle.kts"


def fail(message: str) -> None:
    raise SystemExit(f"PLAY_STORE_PUBLICATION_PACK=FAIL::{message}")


def read(path: Path) -> str:
    if not path.exists():
        fail(f"missing::{path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8-sig")


def main() -> None:
    pack = json.loads(read(PACK))
    shotlist = read(SHOTLIST)
    data_safety = read(DATA_SAFETY)
    pubspec = read(PUBSPEC)
    gradle = read(GRADLE)

    app_id_match = re.search(r'applicationId\s*=\s*"([^"]+)"', gradle)
    version_match = re.search(r"^version:\s*([^\s]+)", pubspec, re.MULTILINE)
    app_id = app_id_match.group(1) if app_id_match else ""
    version = version_match.group(1) if version_match else ""

    if pack.get("kind") != "NON_ATTESTING_PLAY_STORE_PUBLICATION_PACK":
        fail("kind")
    if pack.get("application_id") != app_id:
        fail(f"application_id_mismatch::{pack.get('application_id')}::{app_id}")
    if pack.get("release_train_version") != version:
        fail(f"version_mismatch::{pack.get('release_train_version')}::{version}")

    limits = pack["listing_limits"]
    listings = pack["localized_listing"]
    required_locales = {"pt-BR", "en-US", "es-419"}
    if set(listings) != required_locales:
        fail(f"locales::{sorted(listings)}")

    prohibited_short_tokens = (
        "baixe agora",
        "instale agora",
        "download now",
        "install now",
        "descarga ahora",
        "instala ahora",
        "nº 1",
        "#1",
        "melhor",
        "best app",
        "mejor app",
    )

    for locale, listing in listings.items():
        name = str(listing.get("app_name") or "")
        short = str(listing.get("short_description") or "")
        full = str(listing.get("full_description") or "")
        if not name or len(name) > limits["app_name_max_chars"]:
            fail(f"app_name_length::{locale}::{len(name)}")
        if not short or len(short) > limits["short_description_max_chars"]:
            fail(f"short_description_length::{locale}::{len(short)}")
        if not full or len(full) > limits["full_description_max_chars"]:
            fail(f"full_description_length::{locale}::{len(full)}")
        normalized_short = short.casefold()
        if any(token.casefold() in normalized_short for token in prohibited_short_tokens):
            fail(f"short_description_metadata_policy_token::{locale}")

    assets = pack["preview_assets"]
    icon = assets["app_icon"]
    if (icon["width_px"], icon["height_px"], icon["max_bytes"]) != (512, 512, 1048576):
        fail("icon_contract")
    feature = assets["feature_graphic"]
    if (feature["width_px"], feature["height_px"]) != (1024, 500):
        fail("feature_graphic_contract")
    screenshots = assets["phone_screenshots"]
    if screenshots["minimum_for_publication"] < 2 or screenshots["target_count"] < 4:
        fail("screenshot_contract")

    testing = pack["testing_policy_snapshot"]["new_personal_accounts_after_2023_11_13"]
    if testing["closed_test_minimum_testers"] != 12 or testing["continuous_days"] != 14:
        fail("closed_test_snapshot")
    if testing["applicable_to_this_account"] != "NOT_ATTESTED":
        fail("closed_test_account_applicability_must_remain_external")

    hard = pack["hard_boundaries"]
    required_false = (
        "pack_authorizes_play_console_mutation",
        "pack_authorizes_upload",
        "pack_is_data_safety_submission",
        "pack_is_privacy_legal_review",
        "candidate_copy_is_published",
        "candidate_category_is_final",
        "asset_shotlist_is_asset_evidence",
    )
    for key in required_false:
        if hard.get(key) is not False:
            fail(f"hard_boundary::{key}")

    if "PLAY_SCREENSHOT_EVIDENCE=NOT_PROVEN" not in shotlist:
        fail("shotlist_fail_closed_marker")
    if "PLAY_DATA_SAFETY=NOT_READY_FOR_SUBMISSION" not in data_safety:
        fail("data_safety_fail_closed_marker")

    sources = pack.get("official_sources", [])
    if len(sources) < 4 or not all(url.startswith("https://support.google.com/googleplay/") for url in sources):
        fail("official_source_contract")

    print("PLAY_STORE_PUBLICATION_PACK=PASS")
    print(f"APPLICATION_ID={app_id}")
    print(f"VERSION={version}")
    for locale, listing in listings.items():
        print(f"LISTING::{locale}::NAME_CHARS={len(listing['app_name'])}::SHORT_CHARS={len(listing['short_description'])}::FULL_CHARS={len(listing['full_description'])}")
    print("PLAY_STORE_COPY_PUBLISHED=false")
    print("PLAY_ASSET_EVIDENCE=false")
    print("PLAY_DATA_SAFETY_SUBMITTED=false")
    print("PLAY_CONSOLE_MUTATION=false")


if __name__ == "__main__":
    main()
