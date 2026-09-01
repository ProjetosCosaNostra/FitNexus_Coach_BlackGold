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

function Resolve-Adb {
    $cmd = Get-Command adb -ErrorAction SilentlyContinue
    if ($null -ne $cmd) { return $cmd.Source }
    $candidates = @()
    if ($env:ANDROID_SDK_ROOT) { $candidates += (Join-Path $env:ANDROID_SDK_ROOT 'platform-tools\adb.exe') }
    if ($env:ANDROID_HOME) { $candidates += (Join-Path $env:ANDROID_HOME 'platform-tools\adb.exe') }
    if ($env:LOCALAPPDATA) { $candidates += (Join-Path $env:LOCALAPPDATA 'Android\Sdk\platform-tools\adb.exe') }
    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate -PathType Leaf)) { return $candidate }
    }
    Fail 'ADB_NOT_FOUND'
}

function Write-Utf8NoBom([string]$Path, [string]$Content) {
    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content, $encoding)
}

$pubspec = Get-Content -LiteralPath (Join-Path $AppRoot 'pubspec.yaml') -Raw
if ($pubspec -notmatch '(?m)^version:\s*0\.9\.0\+3\s*$') {
    Fail 'RELEASE_VERSION_NOT_0_9_0_PLUS_3'
}

if ($ValidateOnly) {
    Write-Output 'FITNEXUS_ANDROID_VISUAL_APPROVAL_VALIDATE_ONLY=PASS'
    Write-Output 'EXPECTED_VERSION=0.9.0+3'
    Write-Output 'EMULATOR_VISUAL_APPROVAL_REQUIRED=true'
    Write-Output 'SCREENSHOT_CAPTURE_PERFORMED=false'
    Write-Output 'PLAY_UPLOAD_PERFORMED=false'
    exit 0
}

if ($env:OS -ne 'Windows_NT') { Fail 'WINDOWS_REQUIRED' }
if ([string]::IsNullOrWhiteSpace($env:USERPROFILE)) { Fail 'USERPROFILE_MISSING' }

$flutter = Get-Command flutter -ErrorAction SilentlyContinue
if ($null -eq $flutter) { Fail 'FLUTTER_NOT_FOUND' }
$Adb = Resolve-Adb

$deviceLines = & $Adb devices
if ($LASTEXITCODE -ne 0) { Fail 'ADB_DEVICES_FAILED' }
$serials = @()
foreach ($line in $deviceLines) {
    if ($line -match '^([^\s]+)\s+device\s*$') { $serials += $Matches[1] }
}
if ($serials.Count -ne 1) { Fail ("DEVICE_COUNT_" + $serials.Count) }
$Serial = [string]$serials[0]

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

try {
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

    Write-Output 'PHASE=INSTALL_RELEASE_APK'
    & $Adb -s $Serial install -r $Apk
    if ($LASTEXITCODE -ne 0) { Fail 'ADB_INSTALL_FAILED' }

    $dump = (& $Adb -s $Serial shell dumpsys package $PackageId) -join "`n"
    $versionName = if ($dump -match 'versionName=([^\s]+)') { [string]$Matches[1] } else { '' }
    $versionCode = if ($dump -match 'versionCode=(\d+)') { [string]$Matches[1] } else { '' }
    if ($versionName -ne $ExpectedVersionName -or $versionCode -ne $ExpectedVersionCode) {
        Fail ("INSTALLED_VERSION_MISMATCH_${versionName}_${versionCode}")
    }

    Write-Output 'PHASE=WAKE_AND_OPEN_APP'
    & $Adb -s $Serial shell input keyevent 224 | Out-Null
    & $Adb -s $Serial shell wm dismiss-keyguard | Out-Null
    & $Adb -s $Serial shell am force-stop $PackageId | Out-Null
    $launch = (& $Adb -s $Serial shell am start -W -n "$PackageId/.MainActivity") -join "`n"
    if ($LASTEXITCODE -ne 0 -or $launch -match 'Error:') { Fail 'MAIN_ACTIVITY_LAUNCH_FAILED' }

    Start-Sleep -Seconds 2
    $focused = (& $Adb -s $Serial shell dumpsys window windows) -join "`n"
    if ($focused -notmatch [regex]::Escape($PackageId)) { Fail 'FITNEXUS_NOT_FOREGROUND' }

    Write-Output 'FITNEXUS_ANDROID_VISUAL_APPROVAL=READY'
    Write-Output ('DEVICE_SERIAL=' + $Serial)
    Write-Output ('INSTALLED_VERSION_NAME=' + $versionName)
    Write-Output ('INSTALLED_VERSION_CODE=' + $versionCode)
    Write-Output ('APK_SHA256=' + (Get-FileHash -LiteralPath $Apk -Algorithm SHA256).Hash.ToLowerInvariant())
    Write-Output 'APP_OPEN_IN_EMULATOR=true'
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
}
