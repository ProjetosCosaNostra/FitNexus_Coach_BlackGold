# FitNexus — Screenshot 02 cross-project ANR contamination

Date: 2026-08-30

## Stable failure class
`FNX-PLAY-SCREENSHOT-02-CROSS-PROJECT-ANR-FOREGROUND-CONTAMINATION-005`

## Evidence
Human visual inspection of the generated `02_student_management_1080x1920.png` showed an Android system ANR dialog reading `petdearest isn't responding`, with `Close app` and `Wait` actions, covering a grey background. The intended FitNexus `StudentAccessManagementPage` was not visible.

This explains the earlier `GOLD_UI_NOT_PROVEN_0`: the detector was correctly rejecting a screenshot that did not show the intended FitNexus UI.

## Root cause class
The emulator is reused across multiple BlackGold projects. A stale ANR system dialog from another application can remain above the FitNexus activity and contaminate ADB screenshots even when the FitNexus capture APK is installed and launched successfully.

## Permanent prevention
1. Do not weaken the visual-quality guard to make this screenshot pass.
2. Before capture, inspect the Android UI hierarchy for ANR/system-error dialogs.
3. Resolve only the explicit Android `aerr_close` / `Close app` / `Fechar app` action; never tap arbitrary coordinates without proving the target node.
4. If an ANR is detected after a failed capture, dismiss it and retry the full capture at most once.
5. Keep production APK restoration and Play Console/Supabase non-mutation boundaries intact.
6. Preserve mandatory human visual review before Google Play publication.

Implemented by `FITNEXUS_PLAY_STORE_SCREENSHOT_02_FOREGROUND_RECOVERY_V3.ps1`.
