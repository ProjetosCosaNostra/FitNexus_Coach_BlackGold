[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$InputPath,
    [string]$OutputRoot = (Join-Path $env:USERPROFILE 'Documents\FitNexus_Coach_BlackGold_EXTERNAL\support_ops\current')
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$engine = Join-Path $scriptDir 'support_ops_autopilot_v1.py'
$markerName = '.fitnexus_support_ops_autopilot_v1'
$markerValue = 'FITNEXUS_SUPPORT_OPS_AUTOPILOT_V1_CURRENT_ONLY'

if (-not (Test-Path -LiteralPath $InputPath -PathType Leaf)) {
    throw "INPUT_NOT_FOUND=$InputPath"
}

$repoRoot = (Resolve-Path (Join-Path $scriptDir '..\..')).Path
$resolvedOutputParent = Split-Path -Parent $OutputRoot
if (-not (Test-Path -LiteralPath $resolvedOutputParent)) {
    New-Item -ItemType Directory -Force -Path $resolvedOutputParent | Out-Null
}

$repoPrefix = $repoRoot.TrimEnd('\') + '\'
$outputFull = [System.IO.Path]::GetFullPath($OutputRoot)
if ($outputFull.StartsWith($repoPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'OUTPUT_MUST_BE_OUTSIDE_REPOSITORY'
}

if (Test-Path -LiteralPath $OutputRoot) {
    $marker = Join-Path $OutputRoot $markerName
    if (-not (Test-Path -LiteralPath $marker -PathType Leaf)) {
        throw "REFUSING_TO_REPLACE_UNMARKED_OUTPUT=$OutputRoot"
    }
    if ((Get-Content -LiteralPath $marker -Raw).Trim() -ne $markerValue) {
        throw "REFUSING_TO_REPLACE_INVALID_MARKER=$OutputRoot"
    }
    Remove-Item -LiteralPath $OutputRoot -Recurse -Force
}

New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null
Set-Content -LiteralPath (Join-Path $OutputRoot $markerName) -Value $markerValue -Encoding UTF8

$pythonExe = $null
$pythonArgs = @()
if (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonExe = 'py'
    $pythonArgs = @('-3')
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonExe = 'python'
} else {
    throw 'PYTHON_NOT_FOUND'
}

$outputFile = Join-Path $OutputRoot 'TRIAGE_CANDIDATE.json'
& $pythonExe @pythonArgs $engine --input $InputPath --output $outputFile
if ($LASTEXITCODE -ne 0) {
    throw "SUPPORT_OPS_ENGINE_FAILED_EXIT_CODE=$LASTEXITCODE"
}

$manifest = [ordered]@{
    schema_version = 1
    kind = 'SUPPORT_OPS_LOCAL_TRIAGE_RECEIPT'
    generated_at_utc = [DateTime]::UtcNow.ToString('o')
    input_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $InputPath).Hash.ToLowerInvariant()
    candidate_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $outputFile).Hash.ToLowerInvariant()
    remote_supabase_mutation = $false
    gmail_mutation = $false
    automatic_send = $false
    commercial_progress_credit = 0
}
$manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $OutputRoot 'MANIFEST.json') -Encoding UTF8

Write-Host 'SUPPORT_OPS_AUTOPILOT_V1=PASS'
Write-Host "CURRENT_ONLY_OUTPUT=$OutputRoot"
Write-Host 'REMOTE_SUPABASE_MUTATION=false'
Write-Host 'GMAIL_MUTATION=false'
Write-Host 'AUTOMATIC_SEND=false'
Write-Host 'NEXT_ACTION=Review candidate; database protocol assignment remains separately gated.'
