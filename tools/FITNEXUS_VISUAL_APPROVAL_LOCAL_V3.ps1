# FITNEXUS COACH BLACKGOLD - LOCAL VISUAL APPROVAL RUNNER V3
# Windows bootstrap for the exact-SHA V2 runner.
# Handles Windows PowerShell 5.1 native stderr semantics, patches parser compatibility,
# then executes the real runner under PowerShell 7 (pwsh). No Play publication occurs.

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

    # IMPORTANT: do not merge stderr into stdout here. On Windows PowerShell 5.1,
    # ordinary native stderr (for example git fetch progress) becomes a PowerShell
    # error record and $ErrorActionPreference='Stop' aborts even when git exits 0.
    $Output = & git @Arguments
    $ExitCode = $LASTEXITCODE
    $Text = (($Output | ForEach-Object { "$_" }) -join [Environment]::NewLine).Trim()
    if ($ExitCode -ne 0) {
        throw "Git command failed with exit code ${ExitCode}: git $($Arguments -join ' ')"
    }
    return $Text
}

if (-not (Test-Path -LiteralPath $RepoRoot)) {
    throw "Repository root not found: $RepoRoot"
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw 'git was not found in PATH.'
}

$PwshCommand = Get-Command pwsh.exe -ErrorAction SilentlyContinue
if (-not $PwshCommand) {
    $PwshCommand = Get-Command pwsh -ErrorAction SilentlyContinue
}
if (-not $PwshCommand) {
    throw 'PowerShell 7 (pwsh) was not found. The FitNexus local visual approval runner requires pwsh on Windows.'
}
$Pwsh = $PwshCommand.Source

Write-Host 'FITNEXUS_V3_STAGE=FETCH_REMOTE_HEAD'
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

Write-Host 'FITNEXUS_V3_STAGE=MATERIALIZE_EXACT_SHA_V2'
$SourceSpec = "${RemoteSha}:tools/FITNEXUS_VISUAL_APPROVAL_LOCAL_V2.ps1"
$SourceLines = & git -C $RepoRoot show $SourceSpec
$GitExitCode = $LASTEXITCODE
if ($GitExitCode -ne 0) {
    throw "Unable to read V2 runner from exact SHA ${RemoteSha}."
}
$Source = ($SourceLines | ForEach-Object { "$_" }) -join [Environment]::NewLine

# Windows PowerShell parses "$name:" as a scoped-variable expression. Delimit
# the message interpolation token without changing runner behavior.
$Patched = $Source.Replace('$ExitCode:', '${ExitCode}:')
if ($Patched -eq $Source) {
    throw 'V3_HOTFIX_TARGET_NOT_FOUND: expected V2 interpolation token was not present.'
}

# Ensure PowerShell 7 does not promote native-process exit handling into the
# PowerShell error-action pipeline. The runner itself checks $LASTEXITCODE and
# remains fail-closed on non-zero native exits.
$Needle = "`$ErrorActionPreference = 'Stop'"
$Insert = @"
`$ErrorActionPreference = 'Stop'
if (Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    `$PSNativeCommandUseErrorActionPreference = `$false
}
"@.TrimEnd()
$Patched2 = $Patched.Replace($Needle, $Insert)
if ($Patched2 -eq $Patched) {
    throw 'V3_NATIVE_COMPAT_PATCH_TARGET_NOT_FOUND'
}
$Patched = $Patched2

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
Write-Host "CHILD_SHELL=$Pwsh"
Write-Host 'PLAY_PUBLICATION_PERFORMED=false'
Write-Host 'FITNEXUS_V3_STAGE=EXECUTE_REAL_LOCAL_RUNNER'

& $Pwsh -NoProfile -ExecutionPolicy Bypass -File $Tmp -RepoRoot $RepoRoot -Branch $Branch -ExpectedSha $RemoteSha
$RunnerExit = $LASTEXITCODE
if ($RunnerExit -ne 0) {
    throw "FITNEXUS_VISUAL_RUNNER_V2_FIXED_FAILED_EXIT_$RunnerExit"
}

Write-Host 'FITNEXUS_VISUAL_APPROVAL_V3=PASS'
exit 0
