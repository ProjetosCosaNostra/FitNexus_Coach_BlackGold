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

# Screenshot 02 V1 derives the local PNG path from Contract.capture.output_filename.
# Screenshot 03 V1 still asserted a stale hardcoded Screenshot 02 filename and tried
# to replace that literal in the base runner. Remove only those stale assumptions.
$stalePatternEntry = "    '02_student_management_1080x1920.png',`r`n"
if ($source.IndexOf($stalePatternEntry,[System.StringComparison]::Ordinal) -lt 0) {
    $stalePatternEntry = "    '02_student_management_1080x1920.png',`n"
}
if ($source.IndexOf($stalePatternEntry,[System.StringComparison]::Ordinal) -lt 0) {
    throw 'FNX_PLAY_SCREENSHOT_03_V2_STALE_PATTERN_ENTRY_NOT_FOUND'
}
$source = $source.Replace($stalePatternEntry,'')

$staleReplaceLine = '$adaptedBase = $adaptedBase.Replace(''02_student_management_1080x1920.png'',''03_decision_intelligence_1080x1920.png'')'
if ($source.IndexOf($staleReplaceLine,[System.StringComparison]::Ordinal) -lt 0) {
    throw 'FNX_PLAY_SCREENSHOT_03_V2_STALE_REPLACE_LINE_NOT_FOUND'
}
$source = $source.Replace($staleReplaceLine,'# V2: base output filename is contract-driven; no hardcoded local PNG replacement required.')

# V6 still owns a concrete post-capture validation path and therefore its explicit
# Screenshot 02 -> Screenshot 03 path adaptation must remain present.
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
