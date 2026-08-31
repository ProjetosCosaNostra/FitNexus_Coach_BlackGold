# FNX Play Screenshot 02 — V5 foreground authority not proven

Date: 2026-08-30

## Windows evidence
The V5 proof reached the capture-point ownership gate but failed after 20 attempts:

- `FNX_PLAY_SCREENSHOT_02_CAPTURE_POINT_FOREGROUND_NOT_PROVEN_ATTEMPTS_20`
- `PRODUCTION_RELEASE_RESTORED=true`
- `PLAY_CONSOLE_MUTATION_PERFORMED=false`
- `SUPABASE_MUTATION_PERFORMED=false`
- `FITNEXUS_PLAY_STORE_SCREENSHOT_02_CAPTURE_AUTHORITY_V5=FAIL`

## Interpretation
The old V5 authority used a broad activity search plus only `dumpsys window windows` / `mCurrentFocus`. On modern Android emulator output, that is not sufficient to distinguish:

1. the app never reaching a resumed state,
2. the process crashing immediately after launch,
3. the launcher resolver starting a different task/state,
4. window authority being reported under a different dumpsys surface.

## Stable prevention
Class: `FNX-PLAY-SCREENSHOT-02-V5-FOREGROUND-AUTHORITY-NOT-PROVEN-009`.

V6 must:
- launch the canonical `.MainActivity` explicitly with `am start -W -n`;
- require a live package PID;
- require resumed/top-resumed activity ownership;
- require focused-window ownership from `dumpsys window displays`;
- require three consecutive capture-point proofs immediately before screencap;
- print activity/window/logcat diagnostics if authority cannot be proven;
- keep production restore and remote-mutation boundaries unchanged.
