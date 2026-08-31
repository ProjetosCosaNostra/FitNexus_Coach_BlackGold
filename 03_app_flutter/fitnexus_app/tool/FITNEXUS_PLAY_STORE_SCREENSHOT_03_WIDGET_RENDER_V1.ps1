param(
    [switch]$ValidateOnly
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$AppRoot = Split-Path -Parent $PSScriptRoot
$TestPath = Join-Path $AppRoot 'test\store_capture_screenshot_test.dart'
$DecisionPage = Join-Path $AppRoot 'lib\features\professor\professor_decision_intelligence_page.dart'
$DecisionRepo = Join-Path $AppRoot 'lib\features\professor\professor_decision_intelligence_repository.dart'

foreach ($required in @($TestPath, $DecisionPage, $DecisionRepo)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw ('FNX_SCREENSHOT_03_WIDGET_RENDER_REQUIRED_FILE_MISSING=' + $required)
    }
}

$testText = Get-Content -LiteralPath $TestPath -Raw
$repoText = Get-Content -LiteralPath $DecisionRepo -Raw
if ($testText -notmatch 'ProfessorDecisionIntelligencePage') { throw 'FNX_SCREENSHOT_03_WIDGET_TARGET_MISSING' }
if ($testText -notmatch 'pixelRatio: 3.0') { throw 'FNX_SCREENSHOT_03_WIDGET_PIXEL_RATIO_DRIFT' }
if ($repoText -notmatch 'fitNexusStoreCaptureDataMode') { throw 'FNX_SCREENSHOT_03_SYNTHETIC_MODE_MISSING' }
if ($repoText -notmatch 'STORE_CAPTURE_REMOTE_MUTATION_FORBIDDEN') { throw 'FNX_SCREENSHOT_03_REMOTE_MUTATION_GUARD_MISSING' }

if ($ValidateOnly) {
    Write-Output 'FITNEXUS_PLAY_STORE_SCREENSHOT_03_WIDGET_RENDER_V1_VALIDATE_ONLY=PASS'
    Write-Output 'EMULATOR_REQUIRED=false'
    Write-Output 'ADB_REQUIRED=false'
    Write-Output 'APK_BUILD_REQUIRED=false'
    Write-Output 'OUTPUT_SIZE=1080x1920'
    exit 0
}

$flutter = Get-Command flutter -ErrorAction SilentlyContinue
if ($null -eq $flutter) { throw 'FNX_SCREENSHOT_03_FLUTTER_NOT_FOUND' }

$documents = [Environment]::GetFolderPath('MyDocuments')
if ([string]::IsNullOrWhiteSpace($documents)) { throw 'FNX_SCREENSHOT_03_DOCUMENTS_UNRESOLVED' }
$output = Join-Path $documents 'FitNexus_Coach_BlackGold_EXTERNAL\play_store_assets\current\screenshots\03_decision_intelligence_1080x1920.png'
New-Item -ItemType Directory -Path (Split-Path -Parent $output) -Force | Out-Null
Remove-Item -LiteralPath $output -Force -ErrorAction SilentlyContinue

$previous = $env:FNX_STORE_SCREENSHOT_OUTPUT
try {
    $env:FNX_STORE_SCREENSHOT_OUTPUT = $output
    Push-Location $AppRoot
    try {
        Write-Output 'SCREENSHOT_03_FAST_RENDER_PHASE=FLUTTER_TEST_RENDER'
        & $flutter.Source test 'test/store_capture_screenshot_test.dart' '--dart-define=FITNEXUS_STORE_CAPTURE=true' '--dart-define=FITNEXUS_STORE_CAPTURE_SHOT=03' '--reporter=expanded'
        $exitCode = $LASTEXITCODE
        if ($null -eq $exitCode -or $exitCode -ne 0) {
            throw ('FNX_SCREENSHOT_03_WIDGET_TEST_EXIT_' + $exitCode)
        }
    }
    finally {
        Pop-Location
    }
}
finally {
    if ($null -eq $previous) { Remove-Item Env:FNX_STORE_SCREENSHOT_OUTPUT -ErrorAction SilentlyContinue }
    else { $env:FNX_STORE_SCREENSHOT_OUTPUT = $previous }
}

if (-not (Test-Path -LiteralPath $output -PathType Leaf)) { throw 'FNX_SCREENSHOT_03_OUTPUT_MISSING' }
$bytes = (Get-Item -LiteralPath $output).Length
if ($bytes -lt 20000) { throw ('FNX_SCREENSHOT_03_OUTPUT_TOO_SMALL_' + $bytes) }
$sha = (Get-FileHash -LiteralPath $output -Algorithm SHA256).Hash.ToLowerInvariant()

Write-Output 'FITNEXUS_PLAY_STORE_SCREENSHOT_03_WIDGET_RENDER_V1=PASS'
Write-Output ('SCREENSHOT=' + $output)
Write-Output ('SCREENSHOT_BYTES=' + $bytes)
Write-Output ('SCREENSHOT_SHA256=' + $sha)
Write-Output 'SCREENSHOT_SIZE=1080x1920'
Write-Output 'EMULATOR_REQUIRED=false'
Write-Output 'ADB_REQUIRED=false'
Write-Output 'APK_BUILD_REQUIRED=false'
Write-Output 'SYNTHETIC_DATA=true'
Write-Output 'REAL_USER_DATA=false'
Write-Output 'REMOTE_MUTATION_PERFORMED=false'
Write-Output 'HUMAN_VISUAL_REVIEW_REQUIRED=true'
