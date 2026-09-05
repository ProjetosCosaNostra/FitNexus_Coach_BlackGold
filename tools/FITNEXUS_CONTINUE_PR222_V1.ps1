[CmdletBinding()]
param(
    [string]$RepoRoot = 'E:\FitNexus_Coach_BlackGold',
    [string]$CandidateSha = '202d4b8d1f08a8b7865c1ca2c40c0a23bfef15dc'
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$SourceBranch = 'blackgold/mobile-home-premium-redesign-v1'
$StageRoot = Join-Path $RepoRoot '_fitnexus_current_only\PR222_LIFECYCLE_DIAGNOSTIC'
$Worktree = Join-Path $env:TEMP ('FitNexus_PR222_' + $CandidateSha.Substring(0, 12))
$AppRelative = '03_app_flutter\fitnexus_app'
$StartedAt = (Get-Date).ToString('o')

function Write-Stage {
    param([string]$Message)
    Write-Host ''
    Write-Host ('=== ' + $Message + ' ===') -ForegroundColor Cyan
}

function Invoke-Native {
    param(
        [Parameter(Mandatory = $true)][string]$Exe,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$LogPath,
        [string]$WorkingDirectory = $RepoRoot
    )

    $parent = Split-Path -Parent $LogPath
    if ($parent -and -not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }

    Add-Content -LiteralPath $LogPath -Value ("`r`n> " + $Exe + ' ' + ($Arguments -join ' ')) -Encoding UTF8
    Push-Location $WorkingDirectory
    $oldPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        & $Exe @Arguments 2>&1 | ForEach-Object {
            $text = $_.ToString()
            Add-Content -LiteralPath $LogPath -Value $text -Encoding UTF8
            Write-Host $text
        }
        $exitCode = $LASTEXITCODE
        if ($null -eq $exitCode) { $exitCode = 0 }
    }
    finally {
        $ErrorActionPreference = $oldPreference
        Pop-Location
    }
    return [int]$exitCode
}

function Save-FailureArtifacts {
    param([string]$AppDir)
    $failureDir = Join-Path $AppDir 'test\failures'
    if (Test-Path -LiteralPath $failureDir) {
        $dest = Join-Path $StageRoot 'flutter_test_failures'
        if (Test-Path -LiteralPath $dest) { Remove-Item -LiteralPath $dest -Recurse -Force }
        Copy-Item -LiteralPath $failureDir -Destination $dest -Recurse -Force
    }
}

if (-not (Test-Path -LiteralPath $RepoRoot)) {
    throw "REPO_ROOT_NOT_FOUND: $RepoRoot"
}

$GitCommand = Get-Command git.exe -ErrorAction SilentlyContinue
if (-not $GitCommand) { $GitCommand = Get-Command git -ErrorAction Stop }
$Git = $GitCommand.Source

$FlutterCommand = Get-Command flutter.bat -ErrorAction SilentlyContinue
if (-not $FlutterCommand) { $FlutterCommand = Get-Command flutter.exe -ErrorAction SilentlyContinue }
if (-not $FlutterCommand) { $FlutterCommand = Get-Command flutter -ErrorAction Stop }
$Flutter = $FlutterCommand.Source

if (Test-Path -LiteralPath $StageRoot) {
    Remove-Item -LiteralPath $StageRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $StageRoot -Force | Out-Null

$BootstrapLog = Join-Path $StageRoot '01_bootstrap.log'
$TargetLog = Join-Path $StageRoot '04_targeted_test.log'
$FullLog = Join-Path $StageRoot '05_full_suite.log'
$ContextLog = Join-Path $StageRoot '03_lifecycle_source_context.txt'
$InventoryLog = Join-Path $StageRoot '02_test_inventory.txt'
$ReceiptPath = Join-Path $StageRoot 'RECEIPT.json'

$TargetExit = $null
$FullExit = $null
$TargetTest = $null
$FinalStatus = 'FAIL_UNCLASSIFIED'
$ShouldExit = 90

try {
    Write-Stage 'FITNEXUS PR222 - EXACT SHA BOOTSTRAP'
    Write-Host "Repository: $RepoRoot"
    Write-Host "Candidate SHA: $CandidateSha"
    Write-Host "Evidence: $StageRoot"

    $repoCheck = Invoke-Native -Exe $Git -Arguments @('-C', $RepoRoot, 'rev-parse', '--show-toplevel') -LogPath $BootstrapLog
    if ($repoCheck -ne 0) { throw 'REPOSITORY_VALIDATION_FAILED' }

    $fetchExit = Invoke-Native -Exe $Git -Arguments @('-C', $RepoRoot, 'fetch', 'origin', $SourceBranch, '--prune') -LogPath $BootstrapLog
    if ($fetchExit -ne 0) { throw "GIT_FETCH_FAILED_EXIT_$fetchExit" }

    $verifyExit = Invoke-Native -Exe $Git -Arguments @('-C', $RepoRoot, 'cat-file', '-e', ($CandidateSha + '^{commit}')) -LogPath $BootstrapLog
    if ($verifyExit -ne 0) { throw 'CANDIDATE_SHA_NOT_AVAILABLE_AFTER_FETCH' }

    if (Test-Path -LiteralPath $Worktree) {
        $null = Invoke-Native -Exe $Git -Arguments @('-C', $RepoRoot, 'worktree', 'remove', '--force', $Worktree) -LogPath $BootstrapLog
        if (Test-Path -LiteralPath $Worktree) { Remove-Item -LiteralPath $Worktree -Recurse -Force }
    }

    $worktreeExit = Invoke-Native -Exe $Git -Arguments @('-C', $RepoRoot, 'worktree', 'add', '--detach', $Worktree, $CandidateSha) -LogPath $BootstrapLog
    if ($worktreeExit -ne 0) { throw "WORKTREE_CREATE_FAILED_EXIT_$worktreeExit" }

    $AppDir = Join-Path $Worktree $AppRelative
    $TestRoot = Join-Path $AppDir 'test'
    if (-not (Test-Path -LiteralPath $TestRoot)) { throw "FLUTTER_TEST_ROOT_NOT_FOUND: $TestRoot" }

    Write-Stage 'LOCATING REAL LIFECYCLE TEST'
    $dartFiles = @(Get-ChildItem -LiteralPath $TestRoot -Recurse -File -Filter '*.dart')
    if ($dartFiles.Count -eq 0) { throw 'NO_DART_TEST_FILES_FOUND' }

    $goldenMatches = @(
        $dartFiles | Select-String -SimpleMatch 'app_lifecycle_guard_all_states' -ErrorAction SilentlyContinue
    )
    $goldenCandidates = @($goldenMatches | ForEach-Object { $_.Path } | Sort-Object -Unique)
    $namedCandidates = @($dartFiles | Where-Object { $_.Name -match 'lifecycle' } | ForEach-Object { $_.FullName } | Sort-Object -Unique)

    @(
        'Candidate SHA: ' + $CandidateSha
        'Golden string matches:'
        ($goldenCandidates -join "`r`n")
        ''
        'Lifecycle-named tests:'
        ($namedCandidates -join "`r`n")
        ''
        'All lifecycle-state references:'
    ) | Set-Content -LiteralPath $InventoryLog -Encoding UTF8

    $stateRefs = @(
        $dartFiles | Select-String -Pattern 'AppLifecycleState|didChangeAppLifecycleState|handleAppLifecycleState' -ErrorAction SilentlyContinue
    )
    foreach ($ref in $stateRefs) {
        Add-Content -LiteralPath $InventoryLog -Value ("{0}:{1}: {2}" -f $ref.Path, $ref.LineNumber, $ref.Line.Trim()) -Encoding UTF8
    }

    if ($goldenCandidates.Count -gt 0) {
        $TargetTest = $goldenCandidates[0]
    }
    elseif ($namedCandidates.Count -gt 0) {
        $TargetTest = $namedCandidates[0]
    }
    else {
        throw 'TARGET_LIFECYCLE_TEST_NOT_FOUND'
    }

    Write-Host "Target test: $TargetTest" -ForegroundColor Yellow

    $context = Select-String -LiteralPath $TargetTest -Pattern 'app_lifecycle_guard_all_states|AppLifecycleState|didChangeAppLifecycleState|handleAppLifecycleState|addTearDown|tearDown|setUp' -Context 4,4 -ErrorAction SilentlyContinue | Out-String -Width 500
    if ([string]::IsNullOrWhiteSpace($context)) {
        $context = Get-Content -LiteralPath $TargetTest -Raw
    }
    Set-Content -LiteralPath $ContextLog -Value $context -Encoding UTF8

    Write-Stage 'FLUTTER ENVIRONMENT'
    $versionExit = Invoke-Native -Exe $Flutter -Arguments @('--version') -LogPath $BootstrapLog -WorkingDirectory $AppDir
    if ($versionExit -ne 0) { throw "FLUTTER_VERSION_FAILED_EXIT_$versionExit" }

    $pubExit = Invoke-Native -Exe $Flutter -Arguments @('pub', 'get') -LogPath $BootstrapLog -WorkingDirectory $AppDir
    if ($pubExit -ne 0) { throw "FLUTTER_PUB_GET_FAILED_EXIT_$pubExit" }

    $relativeTarget = $TargetTest.Substring($AppDir.Length).TrimStart('\').Replace('\', '/')

    Write-Stage 'TARGETED LIFECYCLE TEST'
    $TargetExit = Invoke-Native -Exe $Flutter -Arguments @('test', $relativeTarget, '--reporter', 'expanded') -LogPath $TargetLog -WorkingDirectory $AppDir

    if ($TargetExit -ne 0) {
        Save-FailureArtifacts -AppDir $AppDir
        $FinalStatus = 'FAIL_TARGETED'
        $ShouldExit = 20
    }
    else {
        Write-Stage 'TARGET PASSED - REPRODUCING FULL QUALITY SUITE'
        $FullExit = Invoke-Native -Exe $Flutter -Arguments @('test', '--reporter', 'expanded') -LogPath $FullLog -WorkingDirectory $AppDir
        if ($FullExit -ne 0) {
            Save-FailureArtifacts -AppDir $AppDir
            $FinalStatus = 'FAIL_FULL_SUITE'
            $ShouldExit = 30
        }
        else {
            $FinalStatus = 'PASS_LOCAL'
            $ShouldExit = 0
        }
    }
}
catch {
    $FinalStatus = 'RUNNER_ERROR'
    $ShouldExit = 91
    $message = $_.Exception.Message
    Add-Content -LiteralPath $BootstrapLog -Value ("RUNNER_ERROR: " + $message) -Encoding UTF8
    Write-Host "RUNNER_ERROR: $message" -ForegroundColor Red
}
finally {
    $FinishedAt = (Get-Date).ToString('o')

    $hashes = @()
    foreach ($file in @(Get-ChildItem -LiteralPath $StageRoot -File -ErrorAction SilentlyContinue)) {
        try {
            $h = Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256
            $hashes += [ordered]@{ file = $file.Name; sha256 = $h.Hash.ToLowerInvariant() }
        }
        catch { }
    }

    $receipt = [ordered]@{
        project = 'FitNexus Coach BlackGold'
        pr = 222
        candidate_sha = $CandidateSha
        source_branch = $SourceBranch
        target_test = $TargetTest
        targeted_test_exit = $TargetExit
        full_suite_exit = $FullExit
        status = $FinalStatus
        started_at = $StartedAt
        finished_at = $FinishedAt
        evidence_root = $StageRoot
        emulator_used = $false
        play_publication_performed = $false
        golden_updated = $false
        signing_key_touched = $false
        files = $hashes
    }
    $receipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $ReceiptPath -Encoding UTF8

    if (Test-Path -LiteralPath $Worktree) {
        try {
            $cleanupLog = Join-Path $StageRoot '06_cleanup.log'
            $null = Invoke-Native -Exe $Git -Arguments @('-C', $RepoRoot, 'worktree', 'remove', '--force', $Worktree) -LogPath $cleanupLog
        }
        catch {
            Add-Content -LiteralPath (Join-Path $StageRoot '06_cleanup.log') -Value $_.Exception.Message -Encoding UTF8
        }
        if (Test-Path -LiteralPath $Worktree) {
            try { Remove-Item -LiteralPath $Worktree -Recurse -Force } catch { }
        }
    }

    Write-Host ''
    Write-Host '============================================================' -ForegroundColor DarkYellow
    Write-Host "FITNEXUS_PR222_LIFECYCLE=$FinalStatus" -ForegroundColor Yellow
    Write-Host "HEAD_SHA=$CandidateSha"
    Write-Host "TARGET_TEST=$TargetTest"
    Write-Host "EVIDENCE=$StageRoot"
    Write-Host "RECEIPT=$ReceiptPath"
    Write-Host 'NO_EMULATOR=true'
    Write-Host 'GOLDEN_UPDATED=false'
    Write-Host 'PLAY_PUBLICATION_PERFORMED=false'
    Write-Host 'SIGNING_KEY_TOUCHED=false'
    Write-Host '============================================================' -ForegroundColor DarkYellow
}

exit $ShouldExit
