param(
    [switch]$ValidateOnly
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$BaseV1Path = Join-Path $PSScriptRoot 'FITNEXUS_PLAY_STORE_SCREENSHOT_02_CAPTURE_V1.ps1'
$V6Path = Join-Path $PSScriptRoot 'FITNEXUS_PLAY_STORE_SCREENSHOT_02_EXPLICIT_LAUNCH_AUTHORITY_V6.ps1'
$V7Path = Join-Path $PSScriptRoot 'FITNEXUS_PLAY_STORE_SCREENSHOT_02_RENDER_READY_AUTHORITY_V7.ps1'

foreach ($required in @($BaseV1Path,$V6Path,$V7Path)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw ('FNX_PLAY_SCREENSHOT_03_REQUIRED_SOURCE_MISSING=' + $required)
    }
}

$AppRoot = Split-Path -Parent $PSScriptRoot
$DecisionRepoPath = Join-Path $AppRoot 'lib\features\professor\professor_decision_intelligence_repository.dart'
$StoreEntrypoint = Join-Path $AppRoot 'lib\store_capture_main.dart'
$Contract03 = Join-Path $AppRoot 'android\play_store\PLAY_STORE_SCREENSHOT_03_CAPTURE_V1.json'

foreach ($required in @($DecisionRepoPath,$StoreEntrypoint,$Contract03)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw ('FNX_PLAY_SCREENSHOT_03_CONTRACT_SOURCE_MISSING=' + $required)
    }
}

$entrypointText = Get-Content -LiteralPath $StoreEntrypoint -Raw
$decisionRepoText = Get-Content -LiteralPath $DecisionRepoPath -Raw
if ($entrypointText -notmatch "fitNexusStoreCaptureShot == '03'") {
    throw 'FNX_PLAY_SCREENSHOT_03_ROUTING_NOT_PROVEN'
}
if ($entrypointText -notmatch 'ProfessorDecisionIntelligencePage') {
    throw 'FNX_PLAY_SCREENSHOT_03_TARGET_WIDGET_NOT_PROVEN'
}
if ($decisionRepoText -notmatch 'fitNexusStoreCaptureDataMode') {
    throw 'FNX_PLAY_SCREENSHOT_03_SYNTHETIC_GATE_NOT_PROVEN'
}
if ($decisionRepoText -notmatch 'STORE_CAPTURE_REMOTE_MUTATION_FORBIDDEN') {
    throw 'FNX_PLAY_SCREENSHOT_03_REMOTE_MUTATION_GUARD_NOT_PROVEN'
}

$contract = Get-Content -LiteralPath $Contract03 -Raw | ConvertFrom-Json
if ([string]$contract.capture.dart_define_shot -ne '03') {
    throw 'FNX_PLAY_SCREENSHOT_03_CONTRACT_SHOT_DRIFT'
}
if ([string]$contract.capture.production_ui_widget -ne 'ProfessorDecisionIntelligencePage') {
    throw 'FNX_PLAY_SCREENSHOT_03_CONTRACT_WIDGET_DRIFT'
}
if ([string]$contract.capture.output_filename -ne '03_decision_intelligence_1080x1920.png') {
    throw 'FNX_PLAY_SCREENSHOT_03_CONTRACT_OUTPUT_DRIFT'
}
foreach ($property in $contract.hard_boundaries.PSObject.Properties) {
    if ([bool]$property.Value) {
        throw ('FNX_PLAY_SCREENSHOT_03_BOUNDARY_DRIFT_' + $property.Name)
    }
}

$baseText = Get-Content -LiteralPath $BaseV1Path -Raw
$v6Text = Get-Content -LiteralPath $V6Path -Raw
$v7Text = Get-Content -LiteralPath $V7Path -Raw

$requiredBasePatterns = @(
    'PLAY_STORE_SCREENSHOT_02_CAPTURE_V1.json',
    "`$ShotDefine = '02'",
    'StudentAccessManagementPage',
    'FITNEXUS_PLAY_STORE_SCREENSHOT_02_RECEIPT_V1.json',
    'fitnexus_play_screenshot_02.png'
)
foreach ($pattern in $requiredBasePatterns) {
    if ($baseText.IndexOf($pattern,[System.StringComparison]::Ordinal) -lt 0) {
        throw ('FNX_PLAY_SCREENSHOT_03_BASE_PATTERN_DRIFT=' + $pattern)
    }
}
if ($v6Text.IndexOf('02_student_management_1080x1920.png',[System.StringComparison]::Ordinal) -lt 0) {
    throw 'FNX_PLAY_SCREENSHOT_03_V6_OUTPUT_PATTERN_DRIFT'
}

$adaptedBase = $baseText
$adaptedBase = $adaptedBase.Replace('PLAY_STORE_SCREENSHOT_02_CAPTURE_V1.json','PLAY_STORE_SCREENSHOT_03_CAPTURE_V1.json')
$adaptedBase = $adaptedBase.Replace("`$ShotDefine = '02'","`$ShotDefine = '03'")
$adaptedBase = $adaptedBase.Replace('StudentAccessManagementPage','ProfessorDecisionIntelligencePage')
$adaptedBase = $adaptedBase.Replace('FITNEXUS_PLAY_STORE_SCREENSHOT_02_RECEIPT_V1.json','FITNEXUS_PLAY_STORE_SCREENSHOT_03_RECEIPT_V1.json')
$adaptedBase = $adaptedBase.Replace('fitnexus_play_screenshot_02.png','fitnexus_play_screenshot_03.png')
$adaptedBase = $adaptedBase.Replace("Write-Output 'SHOT=02'","Write-Output 'SHOT=03'")
$adaptedBase = $adaptedBase.Replace("Write-Output 'PRODUCTION_UI_WIDGET=StudentAccessManagementPage'","Write-Output 'PRODUCTION_UI_WIDGET=ProfessorDecisionIntelligencePage'")

# Screenshot 02 V1 derives the local PNG filename from Contract.capture.output_filename.
# V6 still has a concrete post-capture path, so only V6 needs literal path adaptation.
$adaptedV6 = $v6Text.Replace('02_student_management_1080x1920.png','03_decision_intelligence_1080x1920.png')

$runtimeRoot = Join-Path $env:TEMP ('FNX_PLAY_SCREENSHOT_03_ADAPTER_' + [guid]::NewGuid().ToString('N'))
$runtimeTool = Join-Path $runtimeRoot 'tool'
$runtimeAppRoot = Join-Path $runtimeRoot 'fitnexus_app'
$runtimeAndroidPlayStore = Join-Path $runtimeAppRoot 'android\play_store'
$runtimeLib = Join-Path $runtimeAppRoot 'lib'
$runtimeProfessor = Join-Path $runtimeLib 'features\professor'

try {
    New-Item -ItemType Directory -Path $runtimeTool -Force | Out-Null
    New-Item -ItemType Directory -Path $runtimeAndroidPlayStore -Force | Out-Null
    New-Item -ItemType Directory -Path $runtimeProfessor -Force | Out-Null

    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText((Join-Path $runtimeTool 'FITNEXUS_PLAY_STORE_SCREENSHOT_02_CAPTURE_V1.ps1'),$adaptedBase,$encoding)
    [System.IO.File]::WriteAllText((Join-Path $runtimeTool 'FITNEXUS_PLAY_STORE_SCREENSHOT_02_EXPLICIT_LAUNCH_AUTHORITY_V6.ps1'),$adaptedV6,$encoding)
    [System.IO.File]::WriteAllText((Join-Path $runtimeTool 'FITNEXUS_PLAY_STORE_SCREENSHOT_02_RENDER_READY_AUTHORITY_V7.ps1'),$v7Text,$encoding)

    Copy-Item -LiteralPath $Contract03 -Destination (Join-Path $runtimeAndroidPlayStore 'PLAY_STORE_SCREENSHOT_03_CAPTURE_V1.json') -Force
    Copy-Item -LiteralPath $StoreEntrypoint -Destination (Join-Path $runtimeLib 'store_capture_main.dart') -Force

    $dataRepo = Join-Path $AppRoot 'lib\features\professor\professor_data_repository.dart'
    Copy-Item -LiteralPath $dataRepo -Destination (Join-Path $runtimeProfessor 'professor_data_repository.dart') -Force
    Copy-Item -LiteralPath $DecisionRepoPath -Destination (Join-Path $runtimeProfessor 'professor_decision_intelligence_repository.dart') -Force

    $runtimeBasePath = Join-Path $runtimeTool 'FITNEXUS_PLAY_STORE_SCREENSHOT_02_CAPTURE_V1.ps1'
    $runtimeBaseText = Get-Content -LiteralPath $runtimeBasePath -Raw
    $runtimeBaseText = $runtimeBaseText.Replace("`$AppRoot = Split-Path -Parent `$PSScriptRoot",("`$AppRoot = '" + ($AppRoot -replace "'","''") + "'"))
    [System.IO.File]::WriteAllText($runtimeBasePath,$runtimeBaseText,$encoding)

    $runner = Join-Path $runtimeTool 'FITNEXUS_PLAY_STORE_SCREENSHOT_02_RENDER_READY_AUTHORITY_V7.ps1'
    Write-Output 'FITNEXUS_PLAY_STORE_SCREENSHOT_03_DECISION_INTELLIGENCE_V1=ACTIVE'
    Write-Output 'SCREENSHOT_03_TARGET=ProfessorDecisionIntelligencePage'
    Write-Output 'SCREENSHOT_03_SYNTHETIC_DATA=true'
    Write-Output 'SCREENSHOT_03_REMOTE_MUTATION_ALLOWED=false'

    if ($ValidateOnly) {
        [void][ScriptBlock]::Create((Get-Content -LiteralPath $runtimeBasePath -Raw))
        [void][ScriptBlock]::Create((Get-Content -LiteralPath (Join-Path $runtimeTool 'FITNEXUS_PLAY_STORE_SCREENSHOT_02_EXPLICIT_LAUNCH_AUTHORITY_V6.ps1') -Raw))
        [void][ScriptBlock]::Create((Get-Content -LiteralPath $runner -Raw))
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $runner -ValidateOnly
        if ($LASTEXITCODE -ne 0) {
            throw ('FNX_PLAY_SCREENSHOT_03_VALIDATE_CHILD_EXIT_' + $LASTEXITCODE)
        }
        Write-Output 'FITNEXUS_PLAY_STORE_SCREENSHOT_03_DECISION_INTELLIGENCE_V1_VALIDATE_ONLY=PASS'
        Write-Output 'REUSE_RENDER_READY_AUTHORITY_V7=true'
        exit 0
    }

    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $runner
    $childExit = $LASTEXITCODE
    if ($null -eq $childExit -or $childExit -ne 0) {
        Write-Output 'FITNEXUS_PLAY_STORE_SCREENSHOT_03_DECISION_INTELLIGENCE_V1=FAIL'
        Write-Output 'PRODUCTION_RELEASE_RESTORED_EXPECTED_BY_CHILD=true'
        exit 1
    }

    $documents = [Environment]::GetFolderPath('MyDocuments')
    $screenshot = Join-Path $documents 'FitNexus_Coach_BlackGold_EXTERNAL\play_store_assets\current\screenshots\03_decision_intelligence_1080x1920.png'
    if (-not (Test-Path -LiteralPath $screenshot -PathType Leaf)) {
        throw 'FNX_PLAY_SCREENSHOT_03_OUTPUT_MISSING'
    }
    $bytes = (Get-Item -LiteralPath $screenshot).Length
    if ($bytes -lt 20000) {
        throw ('FNX_PLAY_SCREENSHOT_03_OUTPUT_TOO_SMALL_' + $bytes)
    }

    Write-Output 'FITNEXUS_PLAY_STORE_SCREENSHOT_03_DECISION_INTELLIGENCE_V1=PASS'
    Write-Output ('SCREENSHOT=' + $screenshot)
    Write-Output ('SCREENSHOT_BYTES=' + $bytes)
    Write-Output 'SCREENSHOT_SIZE=1080x1920'
    Write-Output 'CAPTURE_POINT_FOREGROUND_PROOF=PASS'
    Write-Output 'FLUTTER_RENDER_READY_PROOF=PASS'
    Write-Output 'SYNTHETIC_DATA=true'
    Write-Output 'REAL_USER_DATA=false'
    Write-Output 'PLAY_CONSOLE_MUTATION_PERFORMED=false'
    Write-Output 'SUPABASE_MUTATION_PERFORMED=false'
    Write-Output 'HUMAN_VISUAL_REVIEW_REQUIRED=true'
    exit 0
}
catch {
    Write-Output 'FITNEXUS_PLAY_STORE_SCREENSHOT_03_DECISION_INTELLIGENCE_V1=FAIL'
    Write-Output ('FAILURE_CLASS=' + $_.Exception.Message)
    Write-Output 'PLAY_CONSOLE_MUTATION_PERFORMED=false'
    Write-Output 'SUPABASE_MUTATION_PERFORMED=false'
    exit 1
}
finally {
    if (Test-Path -LiteralPath $runtimeRoot) {
        Remove-Item -LiteralPath $runtimeRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
