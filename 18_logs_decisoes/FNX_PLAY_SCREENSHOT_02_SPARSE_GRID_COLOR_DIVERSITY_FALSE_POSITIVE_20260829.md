# FitNexus Play Screenshot 02 — sparse-grid color diversity false positive

Date: 2026-08-29

## Stable failure class

`FNX-PLAY-SCREENSHOT-02-SPARSE-GRID-UNIQUE-COLOR-FALSE-POSITIVE-004`

## Observed proof

The repaired Screenshot 02 runner completed capture and restored the production release, but the post-capture visual validator rejected the 1080x1920 PNG with:

`FNX_PLAY_SCREENSHOT_02_VISUAL_REPAIR_LOW_COLOR_DIVERSITY_15`

The receipt was invalidated and `PRODUCTION_RELEASE_RESTORED=true` remained proven. Play Console and Supabase mutation remained false.

## Root cause

The first content-aware validator sampled one fixed 48 px lattice and treated the exact count of sampled RGB values as a hard visual-quality oracle. Thin text, borders, icons and narrow gold accents can fall between lattice points, especially on a dark BlackGold interface. Exact unique-color count is also sensitive to sampling alignment and is not a reliable proof of meaningful UI structure.

## Permanent prevention

Do not use exact sampled color cardinality as a hard gate for dark product screenshots.

Screenshot visual proof must instead combine:

- exact PNG dimensions;
- corruption-size floor only, never compressed byte count as a beauty oracle;
- visible/non-dark sample count;
- BlackGold/gold signal;
- local pixel-transition evidence using nearby samples;
- content occupancy across multiple vertical bands;
- mandatory human visual review before publication.

Unique color count may be emitted as informational telemetry only.

## Repair

`FITNEXUS_PLAY_STORE_SCREENSHOT_02_VISUAL_STATE_REPAIR_V2.ps1` replaces the sparse-lattice unique-color hard gate with denser structural-transition and multi-band occupancy evidence while preserving PowerShell 5.1 compatibility, fail-safe production APK restoration and all no-remote-mutation boundaries.
