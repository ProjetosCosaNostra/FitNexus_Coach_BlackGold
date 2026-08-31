# FNX-PLAY-SCREENSHOT-02-EMPTY-UI-HIERARCHY-BINDING-006

Date: 2026-08-30

## Evidence
Windows exact-head execution of `FITNEXUS_PLAY_STORE_SCREENSHOT_02_FOREGROUND_RECOVERY_V3.ps1` reached the foreground-recovery guard and failed before capture with a PowerShell parameter-binding error:

`Dismiss-AnrDialogs: Não é possível associar o argumento ao parâmetro 'Xml' porque ele é uma cadeia de caracteres vazia.`

The call stack pointed to the first `Dismiss-AnrDialogs` pass. `Get-UiHierarchy` is intentionally allowed to return an empty string when `uiautomator dump` or `cat` cannot provide a hierarchy, but `Test-AnrDialogPresent` declared `Xml` as a mandatory string without `AllowEmptyString`, so PowerShell 5.1 rejected the value before the function's own `IsNullOrWhiteSpace` guard could execute.

## Root cause
The V3 design correctly modeled an empty UI hierarchy as "no proven ANR action", but the PowerShell parameter contract contradicted that runtime model.

## Repair
- `Test-AnrDialogPresent` now explicitly permits an empty string with `[AllowEmptyString()]`.
- `Dismiss-AnrDialogs` checks `IsNullOrWhiteSpace` before calling the ANR detector and treats an empty hierarchy as `EMPTY_NO_ANR_ACTION`.
- the post-failure ANR check also short-circuits on an empty hierarchy.
- no arbitrary coordinate tap is introduced and the V2 visual guard is not weakened.

## Permanent prevention
CI must assert that foreground recovery includes both the empty-string parameter allowance and the whitespace short-circuit. Empty UI hierarchy is an observational absence, not an exceptional state and not proof of an ANR.
