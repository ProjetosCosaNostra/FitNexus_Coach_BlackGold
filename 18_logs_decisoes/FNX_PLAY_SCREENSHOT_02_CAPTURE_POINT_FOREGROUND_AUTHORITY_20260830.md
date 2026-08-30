# FNX Play Screenshot 02 — Capture-point foreground authority

Date: 2026-08-30

Stable failure class: `FNX-PLAY-SCREENSHOT-02-CAPTURE-POINT-FOREGROUND-OWNERSHIP-NOT-PROVEN-008`

## Evidence
The V4 capture-session quarantine successfully stopped cross-project user apps before the nested capture chain, but the Windows proof still ended with `FITNEXUS_PLAY_STORE_SCREENSHOT_02_FOREGROUND_RECOVERY_V3=FAIL`, `SYSTEM_ANR_DIALOGS_DISMISSED=0`, `CAPTURE_RETRY_PERFORMED=false`, and receipt invalidation. The previous human review had already shown a PetDearest ANR overlay in the screenshot.

## Root cause
Session-level quarantine and `uiautomator` observation are not sufficient authorities for the exact frame being captured. The capture runner launched FitNexus through `monkey`, waited a fixed five seconds, and then took `screencap` without proving that the canonical FitNexus package owned both the resumed activity and the current focused window at capture time.

## Permanent prevention
`FITNEXUS_PLAY_STORE_SCREENSHOT_02_CAPTURE_AUTHORITY_V5.ps1` consolidates the capture decision around capture-point authority:

1. force-stop all other user-installed apps except the canonical FitNexus package without uninstalling or clearing data;
2. execute the existing production/capture APK isolation flow;
3. replace the arbitrary 60 KB PNG threshold with a corruption floor of 20 KB;
4. after the capture APK launch, require three consecutive proofs that both `dumpsys activity activities` and `dumpsys window windows` identify `br.com.lafamigliaplayworks.fitnexuscoach` before screencap;
5. fail closed if foreground ownership is not proved within the bounded wait;
6. retain structural BlackGold visual validation and mandatory human review before publication.

## Boundaries
- no Play Console mutation;
- no Supabase mutation;
- no AAB upload;
- no app uninstall;
- no app data clear;
- no real user data.

The objective is to stop patching symptoms around Android dialogs and make exact-frame ownership a required authority before screenshot capture.
