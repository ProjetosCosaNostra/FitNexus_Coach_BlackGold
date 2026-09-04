# FITNEXUS COACH BLACKGOLD - LOCAL VISUAL APPROVAL RUNNER V3
# Hotfix/bootstrap for V2 PowerShell parser compatibility on Windows PowerShell 5.1.
# It materializes the exact remote V2 source, fixes ambiguous variable-colon interpolation,
# validates syntax, and executes the exact current remote SHA. No Play publication is performed.

[CmdletBinding()]
param(
    [string]$RepoRoot = 'E:\FitNexus_Coach_BlackGold',
    [string]$Branch = 'blackgold/mobile-home-premium-redesign-v1',
    [string]$ExpectedSha = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Invoke-GitCapture {
    param([string[]]$Arguments)
    $Output = & git @Arguments 2>&1
    $ExitCode = $LASTEXITCODE
    $Text = (($Output | ForEach-Object { "$_" }) -join [Environment]::NewLine).Trim()
    if ($ExitCode -ne 0) {
        throw "Git command failed with exit code ${ExitCode}: git $($Arguments -join ' ')`n$Text"
    }
    return $Text
}

if (-not (Test-Path -LiteralPath $RepoRoot)) {
    throw "Repository root not found: $RepoRoot"
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw 'git was not found in PATH.'
}

Invoke-GitCapture -Arguments @('-C', $RepoRoot, 'fetch', '--prune', 'origin', $Branch) | Out-Null
$RemoteSha = (Invoke-GitCapture -Arguments @('-C', $RepoRoot, 'rev-parse', "refs/remotes/origin/$Branch")).Trim()
if ($RemoteSha -notmatch '^[0-9a-f]{40}$') {
    throw "Invalid remote SHA: $RemoteSha"
}

if ($ExpectedSha) {
    $ExpectedSha = $ExpectedSha.Trim().ToLowerInvariant()
    if ($ExpectedSha -notmatch '^[0-9a-f]{40}$') {
        throw "ExpectedSha is invalid: $ExpectedSha"
    }
    if ($ExpectedSha -ne $RemoteSha) {
        throw "REMOTE_HEAD_MISMATCH: expected $ExpectedSha but origin/$Branch is $RemoteSha"
    }
}
else {
    $ExpectedSha = $RemoteSha
}

$SourceSpec = "${RemoteSha}:tools/FITNEXUS_VISUAL_APPROVAL_LOCAL_V2.ps1"
$SourceLines = & git -C $RepoRoot show $SourceSpec 2>&1
$GitExitCode = $LASTEXITCODE
if ($GitExitCode -ne 0) {
    $GitText = (($SourceLines | ForEach-Object { "$_" }) -join [Environment]::NewLine).Trim()
    throw "Unable to read V2 runner from exact SHA ${RemoteSha}: $GitText"
}
$Source = ($SourceLines | ForEach-Object { "$_" }) -join [Environment]::NewLine

# Windows PowerShell parses "$name:" as a scoped-variable expression. The V2 source
# contained two ordinary message strings with "$ExitCode:". Delimit only those
# interpolation sites, leaving runner behavior unchanged.
$Patched = $Source.Replace('$ExitCode:', '${ExitCode}:')
if ($Patched -eq $Source) {
    throw 'V3_HOTFIX_TARGET_NOT_FOUND: expected V2 interpolation token was not present.'
}

$Tmp = Join-Path $env:TEMP ("FITNEXUS_VISUAL_APPROVAL_LOCAL_V2_FIXED_" + $RemoteSha.Substring(0, 12) + '.ps1')
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($Tmp, $Patched + [Environment]::NewLine, $Utf8NoBom)

$Tokens = $null
$ParseErrors = $null
[System.Management.Automation.Language.Parser]::ParseFile($Tmp, [ref]$Tokens, [ref]$ParseErrors) | Out-Null
if ($ParseErrors -and $ParseErrors.Count -gt 0) {
    $Details = ($ParseErrors | ForEach-Object { "line $($_.Extent.StartLineNumber): $($_.Message)" }) -join [Environment]::NewLine
    throw "V3_PATCHED_RUNNER_PARSE_FAILED`n$Details"
}

Write-Host 'FITNEXUS_VISUAL_APPROVAL_V3_BOOTSTRAP=PASS'
Write-Host "EXACT_SHA=$RemoteSha"
Write-Host "PATCHED_V2=$Tmp"
Write-Host 'PLAY_PUBLICATION_PERFORMED=false'

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Tmp -RepoRoot $RepoRoot -Branch $Branch -ExpectedSha $RemoteSha
$RunnerExit = $LASTEXITCODE
if ($RunnerExit -ne 0) {
    throw "FITNEXUS_VISUAL_RUNNER_V2_FIXED_FAILED_EXIT_$RunnerExit"
}

exit 0
