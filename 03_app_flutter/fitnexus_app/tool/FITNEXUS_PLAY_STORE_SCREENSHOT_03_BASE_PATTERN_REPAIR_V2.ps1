param(
    [switch]$ValidateOnly
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$SourcePath = Join-Path $PSScriptRoot 'FITNEXUS_PLAY_STORE_SCREENSHOT_03_DECISION_INTELLIGENCE_V1.ps1'
if (-not (Test-Path -LiteralPath $SourcePath -PathType Leaf)) {
    throw 'FNX_PLAY_SCREENSHOT_03_V2_SOURCE_MISSING'
}

$source = Get-Content -LiteralPath $SourcePath -Raw

# Screenshot 02 V1 no longer hardcodes the local PNG filename; it derives it from
# Contract.capture.output_filename. Screenshot 03 V1 incorrectly kept a stale
# literal-presence assertion and literal replacement for that old implementation.
$stalePatternEntry = "    '02_student_management_1080x1920.png',`r`n"
if ($source.IndexOf($stalePatternEntry,[System.StringComparison]::Ordinal) -lt 0) {
    $stalePatternEntry = "    '02_student_management_1080x1920.png',`n"
}
if ($source.IndexOf($stalePatternEntry,[System.StringComparison]::Ordinal) -lt 0) {
    throw 'FNX_PLAY_SCREENSHOT_03_V2_STALE_PATTERN_ENTRY_NOT_FOUND'
}
$source = $source.Replace($stalePatternEntry,'')

$staleReplaceLine = "$adaptedBase = $adaptedBase.Replace('02_student_management_1080x1920.png','03_decision_intelligence_1080x1920.png')"
# The variables above are intentionally literal source text; rebuild without interpolation.
$staleReplaceLine = '$adaptedBase = $adaptedBase.Replace(''02_student_management_1080x1920.png'',''03_decision_intelligence_1080x1920.png'')'
if ($source.IndexOf($staleReplaceLine,[System.StringComparison]::Ordinal) -lt 0) {
    throw 'FNX_PLAY_SCREENSHOT_03_V2_STALE_REPLACE_LINE_NOT_FOUND'
}
$source = $source.Replace($staleReplaceLine,'# V2: output filename is contract-driven in Screenshot 02 V1; no base literal replacement required.')

# Preserve the V6 output-path adaptation: V6 owns a post-capture validator with a
# concrete Screenshot 02 path and therefore still must be adapted to Screenshot 03.
if ($source.IndexOf("$adaptedV6 = $v6Text.Replace('02_student_management_1080x1920.png','03_decision_intelligence_1080x1920.png')",[System.StringComparison]::Ordinal) -ge 0) {
    # interpolation can make this check unreliable on Windows PowerShell 5.1; the
    # literal check below is the authority.
}
$requiredV6Literal = '$adaptedV6 = $v6Text.Replace(''02_student_management_1080x1920.png'',''03_decision_intelligence_1080x1920.png'')'
if ($source.IndexOf($requiredV6Literal,[System.StringComparison]::Ordinal) -lt 0) {
    throw 'FNX_PLAY_SCREENSHOT_03_V2_V6_OUTPUT_ADAPTATION_MISSING'
}

$runtimePath = Join-Path $PSScriptRoot ('FITNEXUS_PLAY_STORE_SCREENSHOT_03_DECISION_INTELLIGENCE_V1.__v2_' + [guid]::NewGuid().ToString('N') + '.ps1')
$encoding = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($runtimePath,$source,$encoding)

Write-Output 'FITNEXUS_PLAY_STORE_SCREENSHOT_03_BASE_PATTERN_REPAIR_V2=ACTIVE'
Write-Output 'OUTPUT_PATH_AUTHORITY=CONTRACT_CAPTURE_OUTPUT_FILENAME'
Write-Output 'V6_POST_CAPTURE_PATH_ADAPTATION=PRESERVED'

try {
    [void][ScriptBlock]::Create($source)
    if ($ValidateOnly) {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $runtimePath -ValidateOnly
        $childExit = $LASTEXITCODE
        if ($null -eq $childExit -or $childExit -ne 0) {
            throw ('FNX_PLAY_SCREENSHOT_03_V2_VALIDATE_CHILD_EXIT_' + $childExit)
        }
        Write-Output 'FITNEXUS_PLAY_STORE_SCREENSHOT_03_BASE_PATTERN_REPAIR_V2_VALIDATE_ONLY=PASS'
        exit 0
    }

    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $runtimePath
    $childExit = $LASTEXITCODE
    if ($null -eq $childExit -or $childExit -ne 0) {
        Write-Output 'FITNEXUS_PLAY_STORE_SCREENSHOT_03_BASE_PATTERN_REPAIR_V2=FAIL'
        Write-Output 'PRODUCTION_RELEASE_RESTORED_EXPECTED_BY_CHILD=true'
        exit 1
    }

    Write-Output 'FITNEXUS_PLAY_STORE_SCREENSHOT_03_BASE_PATTERN_REPAIR_V2=PASS'
    Write-Output 'SCREENSHOT_03_BASE_PATTERN_DRIFT=REPAIRED'
    Write-Output 'HUMAN_VISUAL_REVIEW_REQUIRED=true'
    exit 0
}
catch {
    Write-Output 'FITNEXUS_PLAY_STORE_SCREENSHOT_03_BASE_PATTERN_REPAIR_V2=FAIL'
    Write-Output ('FAILURE_CLASS=' + $_.Exception.Message)
    Write-Output 'REMOTE_MUTATION_PERFORMED=false'
    exit 1
}
finally {
    if (Test-Path -LiteralPath $runtimePath -PathType Leaf) {
        Remove-Item -LiteralPath $runtimePath -Force -ErrorAction SilentlyContinue
    }
}
