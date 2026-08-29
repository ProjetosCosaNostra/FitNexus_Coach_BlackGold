# FNX Play Screenshot 02 — compressed dark UI false-positive

Date: 2026-08-29

## Stable failure class
`FNX-PLAY-SCREENSHOT-02-COMPRESSED-DARK-UI-FILESIZE-FALSE-POSITIVE-003`

## Observed Windows evidence
The exact-head Screenshot 02 runner reached `INSTALL_CAPTURE_APK`, `CAPTURE_DEVICE_PNG` and then emitted:

`FNX_PLAY_SCREENSHOT_02_SUSPICIOUSLY_SMALL_52863`

The fail-safe restored the normal production APK and reported `PRODUCTION_RELEASE_RESTORED=true`. Play Console and Supabase mutation remained false.

## Root cause
The runner used an absolute PNG byte-size heuristic (`< 60000` bytes) as a proxy for visual validity. A mostly black, static 1080x1920 Flutter screen can compress efficiently and legitimately fall below that threshold. Dimensions had already validated as 1080x1920, so file size alone was insufficient evidence of a blank or invalid screenshot.

## Permanent prevention
Screenshot 02 local proof now runs through `FITNEXUS_PLAY_STORE_SCREENSHOT_02_VISUAL_STATE_REPAIR_V1.ps1`, which:

- keeps a low corruption floor of 20 KB instead of treating 60 KB as a visual-quality oracle;
- validates exact 1080x1920 dimensions through `System.Drawing`;
- samples the real PNG and requires color diversity, visible non-dark content, and BlackGold-like gold UI pixels;
- invalidates the PASS receipt if the content-aware visual guard fails;
- preserves production-APK restoration, DPAPI signing reuse, no real-user data and zero remote mutation;
- creates its patched runtime copy in the same directory so `$PSScriptRoot` semantics remain correct;
- removes the runtime copy after execution.

## Rule
Never use compressed file byte size by itself as proof that a dark-theme store screenshot is visually empty. Use structural dimensions plus content-aware pixel evidence, then perform human visual review before publication.
