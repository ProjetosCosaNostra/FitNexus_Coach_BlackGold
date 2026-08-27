[CmdletBinding()]
param(
    [string]$OutputRoot = (Join-Path $env:USERPROFILE 'Documents\FitNexus_Coach_BlackGold_EXTERNAL\finance_tax\current')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Builder = Join-Path $PSScriptRoot 'build_finance_tax_autopilot_workspace_v1.py'
if (-not (Test-Path -LiteralPath $Builder -PathType Leaf)) {
    throw "Builder not found: $Builder"
}

$PythonExe = $null
$PythonArgs = @()
$PyLauncher = Get-Command py -ErrorAction SilentlyContinue
if ($PyLauncher) {
    $PythonExe = $PyLauncher.Source
    $PythonArgs = @('-3')
}
else {
    $Python = Get-Command python -ErrorAction SilentlyContinue
    if ($Python) { $PythonExe = $Python.Source }
}
if (-not $PythonExe) {
    throw 'Python 3 was not found.'
}

& $PythonExe @PythonArgs $Builder '--output-root' $OutputRoot
$Code = $LASTEXITCODE
if ($Code -ne 0) {
    throw "Finance Tax Autopilot workspace builder failed with exit code $Code"
}

Write-Host 'FINANCE_TAX_AUTOPILOT_V1=PASS'
Write-Host "CURRENT_ONLY_OUTPUT=$OutputRoot"
Write-Host 'NEXT_ACTION=Keep pre-revenue until real revenue or a legal requirement triggers the reviewed authority workflow.'
exit 0
