# FITNEXUS — Play Screenshot 01 — Windows PowerShell 5.1 PNG Byte-Shift Truncation

Date: 2026-08-29

## Stable failure class

`FNX-PLAY-SCREENSHOT-PS51-BYTE-SHIFT-TRUNCATION-002`

## Observed exact-head evidence

The repaired Screenshot 01 runner advanced through temporary capture APK installation and real device screenshot capture, then reported:

`FNX_PLAY_SCREENSHOT_01_DIMENSION_MISMATCH_56x128`

The fail-safe immediately restored the canonical production release and the terminal reported `PRODUCTION_RELEASE_RESTORED=true`. Play Console and Supabase mutation remained false.

## Root cause

The PNG IHDR parser used `[byte]` array elements directly in shift expressions. In the Windows PowerShell 5.1 runtime path, the shifted values were truncated back to byte width before the bitwise OR was completed.

This is proven by the exact observed values:

- expected width 1080 = hex `0x00000438`; low byte `0x38` = 56;
- expected height 1920 = hex `0x00000780`; low byte `0x80` = 128.

Therefore the PNG itself was not shown to be 56x128. The parser discarded the significant high bytes.

## Permanent prevention

1. Cast each IHDR byte to `[int]` before every left shift and before the final OR term.
2. Keep a CI guard asserting the `[int]` casts in the Windows compatibility repair path.
3. Do not classify a PNG as dimension-invalid when the parser itself has not been proven against the target Windows PowerShell runtime.
4. Keep local exact-head Windows proof mandatory before merging screenshot capture automation.
5. Preserve the fail-safe production APK restoration path for every failure after a temporary capture APK is installed.

## Repair path

`FITNEXUS_PLAY_STORE_SCREENSHOT_01_PS51_DIMENSION_REPAIR_V1.ps1` materializes a same-directory temporary runtime copy of the capture runner with the corrected `[int]` casts, executes it, propagates the exit code, and deletes the temporary copy. This preserves `$PSScriptRoot` semantics and keeps production/capture boundaries unchanged.
