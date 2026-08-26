[CmdletBinding()]
param(
    [string]$OutputRoot = (Join-Path $env:USERPROFILE 'Documents\FitNexus_Coach_BlackGold_EXTERNAL\commercial_readiness\current')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Builder = Join-Path $PSScriptRoot 'build_commercial_readiness_external_fact_pack_v1.py'
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
    if ($Python) {
        $PythonExe = $Python.Source
    }
}

if (-not $PythonExe) {
    throw 'Python 3 was not found. Install/restore Python 3 before running this one-command pack builder.'
}

$InvokeArgs = @()
$InvokeArgs += $PythonArgs
$InvokeArgs += @($Builder, '--output-root', $OutputRoot)

& $PythonExe @InvokeArgs
$Code = $LASTEXITCODE
if ($Code -ne 0) {
    throw "Commercial Readiness external fact pack builder failed with exit code $Code"
}

Write-Host "COMMERCIAL_READINESS_EXTERNAL_FACT_PACK_V1=PASS"
Write-Host "CURRENT_ONLY_OUTPUT=$OutputRoot"
Write-Host 'NEXT_ACTION=Fill only real external facts; do not commit completed sensitive inputs.'
exit 0
