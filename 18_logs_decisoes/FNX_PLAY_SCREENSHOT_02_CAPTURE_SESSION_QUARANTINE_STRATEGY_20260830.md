# FNX Play Screenshot 02 — Capture Session Quarantine Strategy

Date: 2026-08-30

## Trigger
After the empty-UI-hierarchy binding repair, the V3 runner no longer crashed on an empty `uiautomator` result, but the local Windows proof still ended with `FITNEXUS_PLAY_STORE_SCREENSHOT_02_FOREGROUND_RECOVERY_V3=FAIL`, `SYSTEM_ANR_DIALOGS_DISMISSED=0`, `CAPTURE_RETRY_PERFORMED=false`, and child receipt invalidation.

The prior human visual proof had already demonstrated a cross-project Android system ANR (`petdearest isn't responding`) contaminating the screenshot. An empty UI hierarchy means the V3 observer can be blind even when the emulator has stale cross-project state.

## Strategy change
Do not keep weakening visual validators or depend on UI hierarchy observability. Before a store capture, create a deterministic capture session on the shared emulator:

1. enumerate user-installed Android packages with `pm list packages -3`;
2. preserve the canonical FitNexus package `br.com.lafamigliaplayworks.fitnexuscoach`;
3. `am force-stop` every other user-installed package for the capture session;
4. return to HOME and request Android system-dialog closure;
5. run the existing V3 + V2 capture/visual guards unchanged.

This is process quiescing only. It does **not** uninstall apps, clear app data, mutate Supabase, mutate Play Console, upload an AAB, publish an asset, or alter billing.

## Stable prevention class
`FNX-PLAY-SCREENSHOT-02-SHARED-EMULATOR-CROSS-PROJECT-STATE-QUARANTINE-007`

## Permanent rule
Store-asset capture on a shared development emulator must establish a deterministic capture session before launch. Cross-project apps may be force-stopped for the capture session, but must never be uninstalled or data-cleared by the capture automation. Human visual review remains mandatory before promotion.
