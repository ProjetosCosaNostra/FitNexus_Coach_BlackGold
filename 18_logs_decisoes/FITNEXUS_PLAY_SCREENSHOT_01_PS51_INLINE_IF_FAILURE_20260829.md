# FITNEXUS — Play Screenshot 01 — Windows PowerShell 5.1 Inline-If Failure

Date: 2026-08-29

## Stable failure class

`FNX-PLAY-SCREENSHOT-PS51-PARENTHESIZED-INLINE-IF-VALUE-001`

## Observed failure

The first Windows execution of `FITNEXUS_PLAY_STORE_SCREENSHOT_01_CAPTURE_V1.ps1` aborted before ADB/device work with the native Windows PowerShell error that the term `if` was not recognized as a cmdlet/function/program.

## Root cause

The ADB resolver built SDK candidates using hashtable values shaped like:

`Root = (if (...) { ... } else { ... })`

This parenthesized statement-as-value form is not a valid value expression for Windows PowerShell 5.1 in this context. The existing CI used PowerShell 7 and `-ValidateOnly`, so it did not execute the resolver and therefore produced a false green for Windows compatibility.

## Permanent prevention

1. Precompute optional SDK roots with ordinary `if` statements before constructing candidate objects.
2. Never use `= (if (` as a hashtable/property value pattern in Windows-targeted PowerShell runners.
3. CI must regex-guard against `=\s*\(\s*if\s*\(`.
4. `ValidateOnly` green is not sufficient evidence for code paths that are Windows-runtime-only; local exact-head proof remains mandatory before merge.
5. A failure before capture side effects must keep `PRODUCTION_RELEASE_RESTORED=false`, Play Console mutation false, and Supabase mutation false; no successful capture may be claimed.

## Repair

PR #211 head was amended so `LOCALAPPDATA` and `USERPROFILE` Android SDK roots are materialized into variables first, then consumed by the candidate list. The screenshot workflow now contains a dedicated regression guard for this incompatibility class.
