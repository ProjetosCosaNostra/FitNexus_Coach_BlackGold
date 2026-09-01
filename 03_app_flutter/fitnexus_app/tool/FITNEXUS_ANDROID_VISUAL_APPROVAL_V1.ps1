param(
    [switch]$ValidateOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ToolDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AppRoot = (Resolve-Path (Join-Path $ToolDir '..')).Path
$AndroidDir = Join-Path $AppRoot 'android'
$KeyPropertiesFile = Join-Path $AndroidDir 'key.properties'
$PackageId = 'br.com.lafamigliaplayworks.fitnexuscoach'
$ExpectedVersionName = '0.9.0'
$ExpectedVersionCode = '3'
$UploadAlias = 'fitnexus_upload'
$Marker = '# GENERATED_BY=FITNEXUS_ANDROID_VISUAL_APPROVAL_V1'

function Fail([string]$Message) {
    throw "FITNEXUS_ANDROID_VISUAL_APPROVAL=FAIL::$Message"
}

function Resolve-AndroidSdkRoot {
    $roots = @()
    if ($env:ANDROID_SDK_ROOT) { $roots += [string]$env:ANDROID_SDK_ROOT }
    if ($env:ANDROID_HOME) { $roots += [string]$env:ANDROID_HOME }
    if ($env:LOCALAPPDATA) { $roots += (Join-Path $env:LOCALAPPDATA 'Android\Sdk') }
    if ($env:USERPROFILE) { $roots += (Join-Path $env:USERPROFILE 'AppData\Local\Android\Sdk') }
    foreach ($root in $roots) {
        if (-not [string]::IsNullOrWhiteSpace($root) -and (Test-Path -LiteralPath $root -PathType Container)) {
            return (Resolve-Path -LiteralPath $root).Path
        }
    }
    Fail 'ANDROID_SDK_NOT_FOUND'
}

function Write-Utf8NoBom([string]$Path, [string]$Content) {
    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content, $encoding)
}

function Get-FreeEmulatorPort([string]$Adb) {
    $used = @{}
    $lines = & $Adb devices
    if ($LASTEXITCODE -ne 0) { Fail 'ADB_DEVICES_FAILED' }
    foreach ($line in $lines) {
        if ($line -match '^emulator-(\d+)\s+') {
            $used[[int]$Matches[1]] = $true
        }
    }
    for ($port = 5680; $port -ge 5580; $port -= 2) {
        if (-not $used.ContainsKey($port)) { return $port }
    }
    Fail 'NO_FREE_ISOLATED_EMULATOR_PORT'
}

function Wait-ForDevice([string]$Adb, [string]$Serial, [int]$TimeoutSeconds = 240) {
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        $state = (& $Adb -s $Serial get-state 2>$null | Select-Object -First 1)
        if ($state -eq 'device') { return }
        Start-Sleep -Seconds 2
    }
    Fail ('ISOLATED_EMULATOR_ADB_TIMEOUT_' + $Serial)
}

function Wait-ForBoot([string]$Adb, [string]$Serial, [int]$TimeoutSeconds = 300) {
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        $boot = (& $Adb -s $Serial shell getprop sys.boot_completed 2>$null | Select-Object -First 1)
        if ($boot -eq '1') { return }
        Start-Sleep -Seconds 2
    }
    Fail ('ISOLATED_EMULATOR_BOOT_TIMEOUT_' + $Serial)
}

$pubspec = Get-Content -LiteralPath (Join-Path $AppRoot 'pubspec.yaml') -Raw
if ($pubspec -notmatch '(?m)^version:\s*0\.9\.0\+3\s*$') {
    Fail 'RELEASE_VERSION_NOT_0_9_0_PLUS_3'
}

if ($ValidateOnly) {
    Write-Output 'FITNEXUS_ANDROID_VISUAL_APPROVAL_VALIDATE_ONLY=PASS'
    Write-Output 'EXPECTED_VERSION=0.9.0+3'
    Write-Output 'NEW_ISOLATED_EMULATOR_REQUIRED=true'
    Write-Output 'EXISTING_EMULATORS_MUST_REMAIN_UNTOUCHED=true'
    Write-Output 'SCREENSHOT_CAPTURE_PERFORMED=false'
    Write-Output 'PLAY_UPLOAD_PERFORMED=false'
    exit 0
}

if ($env:OS -ne 'Windows_NT') { Fail 'WINDOWS_REQUIRED' }
if ([string]::IsNullOrWhiteSpace($env:USERPROFILE)) { Fail 'USERPROFILE_MISSING' }

$flutter = Get-Command flutter -ErrorAction SilentlyContinue
if ($null -eq $flutter) { Fail 'FLUTTER_NOT_FOUND' }
$SdkRoot = Resolve-AndroidSdkRoot
$Adb = Join-Path $SdkRoot 'platform-tools\adb.exe'
$Emulator = Join-Path $SdkRoot 'emulator\emulator.exe'
if (-not (Test-Path -LiteralPath $Adb -PathType Leaf)) { Fail 'ADB_NOT_FOUND' }
if (-not (Test-Path -LiteralPath $Emulator -PathType Leaf)) { Fail 'EMULATOR_EXE_NOT_FOUND' }

$Avds = @(& $Emulator -list-avds | ForEach-Object { $_.Trim() } | Where-Object { $_ })
if ($Avds.Count -lt 1) { Fail 'NO_ANDROID_AVD_AVAILABLE_AS_TEMPLATE' }
$TemplateAvd = @($Avds | Where-Object { $_ -match '(?i)pixel' } | Select-Object -First 1)[0]
if ([string]::IsNullOrWhiteSpace($TemplateAvd)) { $TemplateAvd = [string]$Avds[0] }

$Port = Get-FreeEmulatorPort -Adb $Adb
$Serial = 'emulator-' + $Port
$EmulatorStarted = $false
$Success = $false
$plainPassword = $null

try {
    Write-Output ('PHASE=START_NEW_ISOLATED_EMULATOR::TEMPLATE=' + $TemplateAvd + '::PORT=' + $Port)
    $emuArgs = @(
        '-avd', $TemplateAvd,
        '-port', [string]$Port,
        '-read-only',
        '-no-snapshot-save',
        '-no-boot-anim',
        '-netdelay', 'none',
        '-netspeed', 'full'
    )
    $emuProcess = Start-Process -FilePath $Emulator -ArgumentList $emuArgs -PassThru
    if ($null -eq $emuProcess) { Fail 'ISOLATED_EMULATOR_START_FAILED' }
    $EmulatorStarted = $true

    Wait-ForDevice -Adb $Adb -Serial $Serial
    Wait-ForBoot -Adb $Adb -Serial $Serial
    & $Adb -s $Serial shell input keyevent 224 | Out-Null
    & $Adb -s $Serial shell wm dismiss-keyguard | Out-Null

    $ExternalRoot = Join-Path $env:USERPROFILE 'Documents\FitNexus_Coach_BlackGold_EXTERNAL\play_signing'
    $AuthorityDir = Join-Path $ExternalRoot 'authority'
    $KeystoreFile = Join-Path $AuthorityDir 'fitnexus-upload-key.jks'
    $ProtectedSecretFile = Join-Path $AuthorityDir 'upload-key-secret.dpapi'
    if (-not (Test-Path -LiteralPath $KeystoreFile -PathType Leaf)) { Fail 'SIGNING_KEYSTORE_MISSING' }
    if (-not (Test-Path -LiteralPath $ProtectedSecretFile -PathType Leaf)) { Fail 'SIGNING_SECRET_MISSING' }

    $protected = (Get-Content -LiteralPath $ProtectedSecretFile -Raw).Trim()
    $secure = ConvertTo-SecureString $protected
    $credential = New-Object System.Net.NetworkCredential('', $secure)
    $plainPassword = $credential.Password
    if ([string]::IsNullOrWhiteSpace($plainPassword)) { Fail 'DPAPI_SECRET_EMPTY' }

    $storePath = $KeystoreFile.Replace('\','/')
    $keyProperties = @(
        $Marker,
        "storePassword=$plainPassword",
        "keyPassword=$plainPassword",
        "keyAlias=$UploadAlias",
        "storeFile=$storePath"
    ) -join [Environment]::NewLine
    Write-Utf8NoBom $KeyPropertiesFile ($keyProperties + [Environment]::NewLine)

    Push-Location $AppRoot
    try {
        Write-Output 'PHASE=FLUTTER_PUB_GET'
        & $flutter.Source pub get
        if ($LASTEXITCODE -ne 0) { Fail 'FLUTTER_PUB_GET_FAILED' }

        Write-Output 'PHASE=BUILD_SIGNED_RELEASE_APK'
        & $flutter.Source build apk --release
        if ($LASTEXITCODE -ne 0) { Fail 'RELEASE_APK_BUILD_FAILED' }
    }
    finally {
        Pop-Location
    }

    $Apk = Join-Path $AppRoot 'build\app\outputs\flutter-apk\app-release.apk'
    if (-not (Test-Path -LiteralPath $Apk -PathType Leaf)) { Fail 'RELEASE_APK_NOT_FOUND' }

    Write-Output ('PHASE=INSTALL_ONLY_ON_ISOLATED_EMULATOR::SERIAL=' + $Serial)
    $installOutput = (& $Adb -s $Serial install -r $Apk) -join "`n"
    if ($LASTEXITCODE -ne 0 -or $installOutput -notmatch 'Success') { Fail 'ADB_INSTALL_FAILED' }

    $dump = (& $Adb -s $Serial shell dumpsys package $PackageId) -join "`n"
    $versionName = if ($dump -match 'versionName=([^\s]+)') { [string]$Matches[1] } else { '' }
    $versionCode = if ($dump -match 'versionCode=(\d+)') { [string]$Matches[1] } else { '' }
    if ($versionName -ne $ExpectedVersionName -or $versionCode -ne $ExpectedVersionCode) {
        Fail ("INSTALLED_VERSION_MISMATCH_${versionName}_${versionCode}")
    }

    Write-Output 'PHASE=OPEN_FITNEXUS_FOR_HUMAN_APPROVAL'
    & $Adb -s $Serial shell am force-stop $PackageId | Out-Null
    $launch = (& $Adb -s $Serial shell am start -W -n "$PackageId/.MainActivity") -join "`n"
    if ($LASTEXITCODE -ne 0 -or $launch -match 'Error:') { Fail 'MAIN_ACTIVITY_LAUNCH_FAILED' }

    Start-Sleep -Seconds 3
    $focused = (& $Adb -s $Serial shell dumpsys window windows) -join "`n"
    if ($focused -notmatch [regex]::Escape($PackageId)) { Fail 'FITNEXUS_NOT_FOREGROUND' }

    $Documents = [Environment]::GetFolderPath('MyDocuments')
    $ReceiptDir = Join-Path $Documents 'FitNexus_Coach_BlackGold_EXTERNAL\android_visual_approval\current'
    New-Item -ItemType Directory -Force -Path $ReceiptDir | Out-Null
    Get-ChildItem -LiteralPath $ReceiptDir -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
    $ReceiptPath = Join-Path $ReceiptDir 'FITNEXUS_ANDROID_VISUAL_APPROVAL_RECEIPT_V1.json'
    $Receipt = [ordered]@{
        schema_version = 1
        kind = 'FITNEXUS_ANDROID_VISUAL_APPROVAL_READY'
        generated_at_utc = [DateTime]::UtcNow.ToString('o')
        application_id = $PackageId
        version_name = $versionName
        version_code = [int]$versionCode
        emulator_template = $TemplateAvd
        isolated_emulator_serial = $Serial
        isolated_emulator_port = $Port
        existing_emulators_touched = $false
        apk_sha256 = (Get-FileHash -LiteralPath $Apk -Algorithm SHA256).Hash.ToLowerInvariant()
        human_visual_approval_required = $true
        screenshot_capture_performed = $false
        play_upload_performed = $false
        play_console_mutation_performed = $false
    }
    Write-Utf8NoBom $ReceiptPath (($Receipt | ConvertTo-Json -Depth 6) + [Environment]::NewLine)

    $Success = $true
    Write-Output 'FITNEXUS_ANDROID_VISUAL_APPROVAL=READY'
    Write-Output ('ISOLATED_EMULATOR_SERIAL=' + $Serial)
    Write-Output ('ISOLATED_EMULATOR_TEMPLATE=' + $TemplateAvd)
    Write-Output ('INSTALLED_VERSION_NAME=' + $versionName)
    Write-Output ('INSTALLED_VERSION_CODE=' + $versionCode)
    Write-Output 'EXISTING_EMULATORS_TOUCHED=false'
    Write-Output 'APP_OPEN_IN_NEW_EMULATOR=true'
    Write-Output 'HUMAN_VISUAL_APPROVAL_REQUIRED=true'
    Write-Output 'SCREENSHOT_CAPTURE_PERFORMED=false'
    Write-Output 'PLAY_UPLOAD_PERFORMED=false'
}
finally {
    if (Test-Path -LiteralPath $KeyPropertiesFile -PathType Leaf) {
        $owned = Get-Content -LiteralPath $KeyPropertiesFile -Raw -ErrorAction SilentlyContinue
        if ($owned -match [regex]::Escape($Marker)) {
            Remove-Item -LiteralPath $KeyPropertiesFile -Force -ErrorAction SilentlyContinue
        }
    }
    $plainPassword = $null

    if (-not $Success -and $EmulatorStarted) {
        try { & $Adb -s $Serial emu kill | Out-Null } catch { }
    }
}
