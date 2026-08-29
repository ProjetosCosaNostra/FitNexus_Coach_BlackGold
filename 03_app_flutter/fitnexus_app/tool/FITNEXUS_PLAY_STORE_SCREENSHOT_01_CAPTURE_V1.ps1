param(
    [switch]$ValidateOnly
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

function Invoke-NativeCapture {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [string]$WorkingDirectory = ''
    )

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $FilePath
    $quoted = @()
    foreach ($arg in $Arguments) {
        $quoted += ('"' + ($arg -replace '"', '\"') + '"')
    }
    $psi.Arguments = ($quoted -join ' ')
    if (-not [string]::IsNullOrWhiteSpace($WorkingDirectory)) {
        $psi.WorkingDirectory = $WorkingDirectory
    }
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $psi
    [void]$process.Start()
    $stdout = $process.StandardOutput.ReadToEnd()
    $stderr = $process.StandardError.ReadToEnd()
    $process.WaitForExit()

    return [pscustomobject]@{
        ExitCode = $process.ExitCode
        StdOut   = $stdout
        StdErr   = $stderr
    }
}

function Write-Utf8NoBom {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Content
    )
    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content, $encoding)
}

function Get-TextSha256 {
    param([Parameter(Mandatory = $true)][string]$Value)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Value)
        return ([System.BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '').ToLowerInvariant()
    }
    finally {
        $sha.Dispose()
    }
}

function Get-BigEndianInt32 {
    param(
        [Parameter(Mandatory = $true)][byte[]]$Bytes,
        [Parameter(Mandatory = $true)][int]$Offset
    )
    return (($Bytes[$Offset] -shl 24) -bor
            ($Bytes[$Offset + 1] -shl 16) -bor
            ($Bytes[$Offset + 2] -shl 8) -bor
            $Bytes[$Offset + 3])
}

function Get-PngDimensions {
    param([Parameter(Mandatory = $true)][string]$Path)
    $bytes = [System.IO.File]::ReadAllBytes($Path)
    if ($bytes.Length -lt 24) {
        throw 'FNX_PLAY_SCREENSHOT_01_PNG_TOO_SMALL'
    }
    $signature = @(137, 80, 78, 71, 13, 10, 26, 10)
    for ($i = 0; $i -lt $signature.Count; $i++) {
        if ($bytes[$i] -ne $signature[$i]) {
            throw 'FNX_PLAY_SCREENSHOT_01_INVALID_PNG_SIGNATURE'
        }
    }
    return [pscustomobject]@{
        Width = Get-BigEndianInt32 -Bytes $bytes -Offset 16
        Height = Get-BigEndianInt32 -Bytes $bytes -Offset 20
    }
}

function Resolve-AdbExecutable {
    $candidates = New-Object System.Collections.Generic.List[object]

    $pathCommand = Get-Command adb -ErrorAction SilentlyContinue
    if ($null -ne $pathCommand -and (Test-Path -LiteralPath $pathCommand.Source -PathType Leaf)) {
        $candidates.Add([pscustomobject]@{ Path = [string]$pathCommand.Source; Source = 'PATH' })
    }

    $localAppDataSdk = ''
    if (-not [string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
        $localAppDataSdk = Join-Path $env:LOCALAPPDATA 'Android\Sdk'
    }
    $userProfileSdk = ''
    if (-not [string]::IsNullOrWhiteSpace($env:USERPROFILE)) {
        $userProfileSdk = Join-Path $env:USERPROFILE 'AppData\Local\Android\Sdk'
    }

    foreach ($rootInfo in @(
        [pscustomobject]@{ Root = $env:ANDROID_SDK_ROOT; Source = 'ANDROID_SDK_ROOT' },
        [pscustomobject]@{ Root = $env:ANDROID_HOME; Source = 'ANDROID_HOME' },
        [pscustomobject]@{ Root = $localAppDataSdk; Source = 'LOCALAPPDATA_STANDARD' },
        [pscustomobject]@{ Root = $userProfileSdk; Source = 'USERPROFILE_STANDARD' }
    )) {
        if (-not [string]::IsNullOrWhiteSpace([string]$rootInfo.Root)) {
            $candidate = Join-Path ([string]$rootInfo.Root) 'platform-tools\adb.exe'
            if (Test-Path -LiteralPath $candidate -PathType Leaf) {
                $candidates.Add([pscustomobject]@{ Path = $candidate; Source = [string]$rootInfo.Source })
            }
        }
    }

    if ($candidates.Count -eq 0) {
        $flutterCommand = Get-Command flutter -ErrorAction SilentlyContinue
        if ($null -ne $flutterCommand) {
            $doctor = Invoke-NativeCapture -FilePath $flutterCommand.Source -Arguments @('doctor', '-v')
            if ($doctor.ExitCode -eq 0 -and $doctor.StdOut -match 'Android SDK at\s+([^\r\n]+)') {
                $sdk = $Matches[1].Trim()
                $candidate = Join-Path $sdk 'platform-tools\adb.exe'
                if (Test-Path -LiteralPath $candidate -PathType Leaf) {
                    $candidates.Add([pscustomobject]@{ Path = $candidate; Source = 'FLUTTER_DOCTOR_ANDROID_SDK' })
                }
            }
        }
    }

    if ($candidates.Count -eq 0) {
        throw 'FNX_PLAY_SCREENSHOT_01_ADB_NOT_FOUND'
    }

    return $candidates[0]
}

function Assert-AdbSuccess {
    param(
        [Parameter(Mandatory = $true)]$Result,
        [Parameter(Mandatory = $true)][string]$FailureClass
    )
    if ($Result.ExitCode -ne 0) {
        throw ($FailureClass + '_EXIT_' + $Result.ExitCode)
    }
}

function Install-Apk {
    param(
        [Parameter(Mandatory = $true)][string]$Adb,
        [Parameter(Mandatory = $true)][string]$Serial,
        [Parameter(Mandatory = $true)][string]$Apk,
        [Parameter(Mandatory = $true)][string]$FailureClass
    )
    $result = Invoke-NativeCapture -FilePath $Adb -Arguments @('-s', $Serial, 'install', '-r', $Apk)
    if ($result.ExitCode -ne 0 -or $result.StdOut -notmatch 'Success') {
        throw ($FailureClass + '_EXIT_' + $result.ExitCode)
    }
}

$AppRoot = Split-Path -Parent $PSScriptRoot
$AndroidDir = Join-Path $AppRoot 'android'
$ContractPath = Join-Path $AndroidDir 'play_store\PLAY_STORE_SCREENSHOT_01_CAPTURE_V1.json'
$StoreEntrypoint = Join-Path $AppRoot 'lib\store_capture_main.dart'
$RepositoryPath = Join-Path $AppRoot 'lib\features\professor\professor_coach_action_repository.dart'
$KeyPropertiesFile = Join-Path $AndroidDir 'key.properties'
$Marker = '# GENERATED_BY=FITNEXUS_PLAY_STORE_SCREENSHOT_01_CAPTURE_V1'
$PackageId = 'br.com.lafamigliaplayworks.fitnexuscoach'
$UploadAlias = 'fitnexus_upload'
$TargetWidth = 1080
$TargetHeight = 1920

if (-not (Test-Path -LiteralPath $ContractPath -PathType Leaf)) {
    throw 'FNX_PLAY_SCREENSHOT_01_CONTRACT_MISSING'
}
if (-not (Test-Path -LiteralPath $StoreEntrypoint -PathType Leaf)) {
    throw 'FNX_PLAY_SCREENSHOT_01_ENTRYPOINT_MISSING'
}
if (-not (Test-Path -LiteralPath $RepositoryPath -PathType Leaf)) {
    throw 'FNX_PLAY_SCREENSHOT_01_REPOSITORY_MISSING'
}

$Contract = Get-Content -LiteralPath $ContractPath -Raw | ConvertFrom-Json
if ([string]$Contract.application_id -ne $PackageId) {
    throw 'FNX_PLAY_SCREENSHOT_01_PACKAGE_DRIFT'
}
if ([int]$Contract.capture.target_width_px -ne $TargetWidth -or [int]$Contract.capture.target_height_px -ne $TargetHeight) {
    throw 'FNX_PLAY_SCREENSHOT_01_DIMENSION_CONTRACT_DRIFT'
}
foreach ($property in $Contract.hard_boundaries.PSObject.Properties) {
    if ([bool]$property.Value) {
        throw ('FNX_PLAY_SCREENSHOT_01_BOUNDARY_DRIFT_' + $property.Name)
    }
}

$repositoryText = Get-Content -LiteralPath $RepositoryPath -Raw
$entrypointText = Get-Content -LiteralPath $StoreEntrypoint -Raw
if ($repositoryText -notmatch 'FITNEXUS_STORE_CAPTURE') {
    throw 'FNX_PLAY_SCREENSHOT_01_SYNTHETIC_GATE_MISSING'
}
if ($entrypointText -notmatch 'fitNexusStoreCaptureMode') {
    throw 'FNX_PLAY_SCREENSHOT_01_ENTRYPOINT_GATE_MISSING'
}
if ($entrypointText -match 'Supabase\.initialize') {
    throw 'FNX_PLAY_SCREENSHOT_01_CAPTURE_ENTRYPOINT_REMOTE_INIT_FORBIDDEN'
}

if ($ValidateOnly) {
    Write-Output 'FITNEXUS_PLAY_STORE_SCREENSHOT_01_CAPTURE_VALIDATE_ONLY=PASS'
    Write-Output ('APPLICATION_ID=' + $PackageId)
    Write-Output 'TARGET=1080x1920'
    Write-Output 'SYNTHETIC_DATA=true'
    Write-Output 'PRODUCTION_UI_WIDGET=ProfessorCoachActionCenterPage'
    Write-Output 'REMOTE_MUTATION_PERFORMED=false'
    exit 0
}

$plainPassword = $null
$adb = $null
$serial = $null
$originalOverride = ''
$displayChanged = $false
$captureInstalled = $false
$productionRestored = $false
$remoteScreenshot = '/sdcard/Download/fitnexus_play_screenshot_01.png'
$scratch = Join-Path $env:TEMP ('FNX_PLAY_SCREENSHOT_01_' + [guid]::NewGuid().ToString('N'))
$failure = $null
$screenshotPath = $null
$receiptPath = $null
$receiptSha = ''
$screenshotSha = ''

try {
    if ($env:OS -ne 'Windows_NT') {
        throw 'FNX_PLAY_SCREENSHOT_01_WINDOWS_REQUIRED'
    }
    if ([string]::IsNullOrWhiteSpace($env:USERPROFILE)) {
        throw 'FNX_PLAY_SCREENSHOT_01_USERPROFILE_MISSING'
    }

    New-Item -ItemType Directory -Path $scratch -Force | Out-Null

    $adbInfo = Resolve-AdbExecutable
    $adb = [string]$adbInfo.Path
    $adbSource = [string]$adbInfo.Source

    $devicesResult = Invoke-NativeCapture -FilePath $adb -Arguments @('devices')
    Assert-AdbSuccess -Result $devicesResult -FailureClass 'FNX_PLAY_SCREENSHOT_01_ADB_DEVICES'
    $serials = @()
    foreach ($line in ($devicesResult.StdOut -split "`r?`n")) {
        if ($line -match '^([^\s]+)\s+device\s*$') {
            $serials += $Matches[1]
        }
    }
    if ($serials.Count -ne 1) {
        throw ('FNX_PLAY_SCREENSHOT_01_DEVICE_COUNT_' + $serials.Count)
    }
    $serial = [string]$serials[0]

    $sizeBefore = Invoke-NativeCapture -FilePath $adb -Arguments @('-s', $serial, 'shell', 'wm', 'size')
    Assert-AdbSuccess -Result $sizeBefore -FailureClass 'FNX_PLAY_SCREENSHOT_01_WM_SIZE_BEFORE'
    if ($sizeBefore.StdOut -match 'Override size:\s*(\d+x\d+)') {
        $originalOverride = [string]$Matches[1]
    }

    $setSize = Invoke-NativeCapture -FilePath $adb -Arguments @('-s', $serial, 'shell', 'wm', 'size', ($TargetWidth.ToString() + 'x' + $TargetHeight.ToString()))
    Assert-AdbSuccess -Result $setSize -FailureClass 'FNX_PLAY_SCREENSHOT_01_WM_SIZE_SET'
    $displayChanged = $true

    $sizeAfter = Invoke-NativeCapture -FilePath $adb -Arguments @('-s', $serial, 'shell', 'wm', 'size')
    Assert-AdbSuccess -Result $sizeAfter -FailureClass 'FNX_PLAY_SCREENSHOT_01_WM_SIZE_AFTER'
    if ($sizeAfter.StdOut -notmatch ('Override size:\s*' + $TargetWidth + 'x' + $TargetHeight)) {
        throw 'FNX_PLAY_SCREENSHOT_01_CAPTURE_SIZE_NOT_APPLIED'
    }

    $flutter = Get-Command flutter -ErrorAction SilentlyContinue
    if ($null -eq $flutter) {
        throw 'FNX_PLAY_SCREENSHOT_01_FLUTTER_NOT_FOUND'
    }

    $ExternalSigning = Join-Path $env:USERPROFILE 'Documents\FitNexus_Coach_BlackGold_EXTERNAL\play_signing\authority'
    $KeystoreFile = Join-Path $ExternalSigning 'fitnexus-upload-key.jks'
    $ProtectedSecretFile = Join-Path $ExternalSigning 'upload-key-secret.dpapi'
    if (-not (Test-Path -LiteralPath $KeystoreFile -PathType Leaf) -or -not (Test-Path -LiteralPath $ProtectedSecretFile -PathType Leaf)) {
        throw 'FNX_PLAY_SCREENSHOT_01_SIGNING_AUTHORITY_MISSING'
    }

    $protected = (Get-Content -LiteralPath $ProtectedSecretFile -Raw).Trim()
    $secure = ConvertTo-SecureString $protected
    $credential = New-Object System.Net.NetworkCredential('', $secure)
    $plainPassword = $credential.Password
    if ([string]::IsNullOrWhiteSpace($plainPassword)) {
        throw 'FNX_PLAY_SCREENSHOT_01_DPAPI_SECRET_EMPTY'
    }

    if (Test-Path -LiteralPath $KeyPropertiesFile -PathType Leaf) {
        $existing = Get-Content -LiteralPath $KeyPropertiesFile -Raw
        if ($existing -notmatch [regex]::Escape($Marker)) {
            throw 'FNX_PLAY_SCREENSHOT_01_FOREIGN_KEY_PROPERTIES_PRESENT'
        }
    }

    $storePathForGradle = $KeystoreFile.Replace('\', '/')
    $keyProperties = @(
        $Marker,
        ('storePassword=' + $plainPassword),
        ('keyPassword=' + $plainPassword),
        ('keyAlias=' + $UploadAlias),
        ('storeFile=' + $storePathForGradle)
    ) -join [Environment]::NewLine
    Write-Utf8NoBom -Path $KeyPropertiesFile -Content ($keyProperties + [Environment]::NewLine)

    Write-Output 'SCREENSHOT_01_PHASE=FLUTTER_PUB_GET'
    $pubGet = Invoke-NativeCapture -FilePath $flutter.Source -Arguments @('pub', 'get') -WorkingDirectory $AppRoot
    if ($pubGet.ExitCode -ne 0) {
        throw ('FNX_PLAY_SCREENSHOT_01_FLUTTER_PUB_GET_EXIT_' + $pubGet.ExitCode)
    }

    Write-Output 'SCREENSHOT_01_PHASE=BUILD_PRODUCTION_RESTORE_APK'
    $productionBuild = Invoke-NativeCapture -FilePath $flutter.Source -Arguments @('build', 'apk', '--release') -WorkingDirectory $AppRoot
    if ($productionBuild.ExitCode -ne 0) {
        throw ('FNX_PLAY_SCREENSHOT_01_PRODUCTION_APK_BUILD_EXIT_' + $productionBuild.ExitCode)
    }
    $builtApk = Join-Path $AppRoot 'build\app\outputs\flutter-apk\app-release.apk'
    if (-not (Test-Path -LiteralPath $builtApk -PathType Leaf)) {
        throw 'FNX_PLAY_SCREENSHOT_01_PRODUCTION_APK_MISSING'
    }
    $productionApk = Join-Path $scratch 'fitnexus-production-restore.apk'
    Copy-Item -LiteralPath $builtApk -Destination $productionApk -Force

    Write-Output 'SCREENSHOT_01_PHASE=BUILD_CAPTURE_APK'
    $captureBuild = Invoke-NativeCapture -FilePath $flutter.Source -Arguments @(
        'build', 'apk', '--release',
        '--target', 'lib/store_capture_main.dart',
        '--dart-define=FITNEXUS_STORE_CAPTURE=true'
    ) -WorkingDirectory $AppRoot
    if ($captureBuild.ExitCode -ne 0) {
        throw ('FNX_PLAY_SCREENSHOT_01_CAPTURE_APK_BUILD_EXIT_' + $captureBuild.ExitCode)
    }
    if (-not (Test-Path -LiteralPath $builtApk -PathType Leaf)) {
        throw 'FNX_PLAY_SCREENSHOT_01_CAPTURE_APK_MISSING'
    }
    $captureApk = Join-Path $scratch 'fitnexus-store-capture.apk'
    Copy-Item -LiteralPath $builtApk -Destination $captureApk -Force

    Write-Output 'SCREENSHOT_01_PHASE=INSTALL_CAPTURE_APK'
    Install-Apk -Adb $adb -Serial $serial -Apk $captureApk -FailureClass 'FNX_PLAY_SCREENSHOT_01_CAPTURE_INSTALL_FAILED'
    $captureInstalled = $true

    $forceStop = Invoke-NativeCapture -FilePath $adb -Arguments @('-s', $serial, 'shell', 'am', 'force-stop', $PackageId)
    Assert-AdbSuccess -Result $forceStop -FailureClass 'FNX_PLAY_SCREENSHOT_01_FORCE_STOP'
    $launch = Invoke-NativeCapture -FilePath $adb -Arguments @('-s', $serial, 'shell', 'monkey', '-p', $PackageId, '-c', 'android.intent.category.LAUNCHER', '1')
    Assert-AdbSuccess -Result $launch -FailureClass 'FNX_PLAY_SCREENSHOT_01_LAUNCH'
    Start-Sleep -Seconds 5

    $documents = [Environment]::GetFolderPath('MyDocuments')
    if ([string]::IsNullOrWhiteSpace($documents)) {
        throw 'FNX_PLAY_SCREENSHOT_01_DOCUMENTS_UNRESOLVED'
    }
    $current = Join-Path $documents 'FitNexus_Coach_BlackGold_EXTERNAL\play_store_assets\current'
    New-Item -ItemType Directory -Path $current -Force | Out-Null
    Get-ChildItem -LiteralPath $current -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
    $screenshotPath = Join-Path $current '01_coach_action_center_1080x1920.png'
    $receiptPath = Join-Path $current 'FITNEXUS_PLAY_STORE_SCREENSHOT_01_RECEIPT_V1.json'

    Write-Output 'SCREENSHOT_01_PHASE=CAPTURE_DEVICE_PNG'
    $capture = Invoke-NativeCapture -FilePath $adb -Arguments @('-s', $serial, 'shell', 'screencap', '-p', $remoteScreenshot)
    Assert-AdbSuccess -Result $capture -FailureClass 'FNX_PLAY_SCREENSHOT_01_SCREENCAP'
    $pull = Invoke-NativeCapture -FilePath $adb -Arguments @('-s', $serial, 'pull', $remoteScreenshot, $screenshotPath)
    Assert-AdbSuccess -Result $pull -FailureClass 'FNX_PLAY_SCREENSHOT_01_PULL'
    [void](Invoke-NativeCapture -FilePath $adb -Arguments @('-s', $serial, 'shell', 'rm', '-f', $remoteScreenshot))

    if (-not (Test-Path -LiteralPath $screenshotPath -PathType Leaf)) {
        throw 'FNX_PLAY_SCREENSHOT_01_LOCAL_PNG_MISSING'
    }
    $png = Get-PngDimensions -Path $screenshotPath
    if ($png.Width -ne $TargetWidth -or $png.Height -ne $TargetHeight) {
        throw ('FNX_PLAY_SCREENSHOT_01_DIMENSION_MISMATCH_' + $png.Width + 'x' + $png.Height)
    }
    $screenshotBytes = (Get-Item -LiteralPath $screenshotPath).Length
    if ($screenshotBytes -lt 100000) {
        throw ('FNX_PLAY_SCREENSHOT_01_SUSPICIOUSLY_SMALL_' + $screenshotBytes)
    }
    $screenshotSha = (Get-FileHash -LiteralPath $screenshotPath -Algorithm SHA256).Hash.ToLowerInvariant()

    Write-Output 'SCREENSHOT_01_PHASE=RESTORE_PRODUCTION_APK'
    Install-Apk -Adb $adb -Serial $serial -Apk $productionApk -FailureClass 'FNX_PLAY_SCREENSHOT_01_PRODUCTION_RESTORE_FAILED'
    $productionRestored = $true

    $packageAfter = Invoke-NativeCapture -FilePath $adb -Arguments @('-s', $serial, 'shell', 'pm', 'path', $PackageId)
    if ($packageAfter.ExitCode -ne 0 -or $packageAfter.StdOut -notmatch 'package:') {
        throw 'FNX_PLAY_SCREENSHOT_01_PRODUCTION_PACKAGE_NOT_RESTORED'
    }

    $dump = Invoke-NativeCapture -FilePath $adb -Arguments @('-s', $serial, 'shell', 'dumpsys', 'package', $PackageId)
    $versionName = ''
    $versionCode = ''
    if ($dump.ExitCode -eq 0) {
        if ($dump.StdOut -match 'versionName=([^\s]+)') { $versionName = [string]$Matches[1] }
        if ($dump.StdOut -match 'versionCode=(\d+)') { $versionCode = [string]$Matches[1] }
    }
    if ($versionName -ne '0.9.0' -or $versionCode -ne '2') {
        throw ('FNX_PLAY_SCREENSHOT_01_RESTORED_VERSION_MISMATCH_' + $versionName + '_' + $versionCode)
    }

    $modelResult = Invoke-NativeCapture -FilePath $adb -Arguments @('-s', $serial, 'shell', 'getprop', 'ro.product.model')
    $model = if ($modelResult.ExitCode -eq 0) { $modelResult.StdOut.Trim() } else { '' }

    $receipt = [ordered]@{
        schema_version = 1
        kind = 'FITNEXUS_PLAY_STORE_SCREENSHOT_01_RECEIPT'
        generated_at_utc = [DateTime]::UtcNow.ToString('o')
        result = 'PASS'
        application_id = $PackageId
        release_train_version = [string]$Contract.release_train_version
        shot_id = [string]$Contract.shot_id
        production_ui_widget = [string]$Contract.capture.production_ui_widget
        synthetic_data = $true
        real_user_data = $false
        screenshot_path = $screenshotPath
        screenshot_width_px = $png.Width
        screenshot_height_px = $png.Height
        screenshot_bytes = $screenshotBytes
        screenshot_sha256 = $screenshotSha
        adb_resolution_source = $adbSource
        adb_path_sha256 = (Get-TextSha256 -Value $adb)
        device_serial_sha256 = (Get-TextSha256 -Value $serial)
        device_model = $model
        installed_version_name = $versionName
        installed_version_code = $versionCode
        capture_build_installed_temporarily = $captureInstalled
        production_release_restored = $productionRestored
        screenshot_capture_performed = $true
        supabase_mutation_performed = $false
        play_console_mutation_performed = $false
        aab_upload_performed = $false
        asset_publication_performed = $false
        billing_activation_performed = $false
        next_gate = 'VISUAL_REVIEW_SCREENSHOT_01_THEN_CAPTURE_02_STUDENT_MANAGEMENT'
    }
    Write-Utf8NoBom -Path $receiptPath -Content (($receipt | ConvertTo-Json -Depth 6) + [Environment]::NewLine)
    $receiptSha = (Get-FileHash -LiteralPath $receiptPath -Algorithm SHA256).Hash.ToLowerInvariant()
}
catch {
    $failure = $_.Exception.Message
}
finally {
    if ($null -ne $adb -and -not [string]::IsNullOrWhiteSpace([string]$serial)) {
        try {
            [void](Invoke-NativeCapture -FilePath $adb -Arguments @('-s', $serial, 'shell', 'rm', '-f', $remoteScreenshot))
        }
        catch { }

        if ($displayChanged) {
            try {
                if (-not [string]::IsNullOrWhiteSpace($originalOverride)) {
                    [void](Invoke-NativeCapture -FilePath $adb -Arguments @('-s', $serial, 'shell', 'wm', 'size', $originalOverride))
                }
                else {
                    [void](Invoke-NativeCapture -FilePath $adb -Arguments @('-s', $serial, 'shell', 'wm', 'size', 'reset'))
                }
            }
            catch { }
        }
    }

    if (Test-Path -LiteralPath $KeyPropertiesFile -PathType Leaf) {
        $owned = Get-Content -LiteralPath $KeyPropertiesFile -Raw -ErrorAction SilentlyContinue
        if ($owned -match [regex]::Escape($Marker)) {
            Remove-Item -LiteralPath $KeyPropertiesFile -Force
        }
    }
    if (Test-Path -LiteralPath $scratch) {
        Remove-Item -LiteralPath $scratch -Recurse -Force -ErrorAction SilentlyContinue
    }
    $plainPassword = $null
}

if ($null -ne $failure) {
    Write-Output 'FITNEXUS_PLAY_STORE_SCREENSHOT_01_CAPTURE=FAIL'
    Write-Output ('FAILURE_CLASS=' + $failure)
    Write-Output ('PRODUCTION_RELEASE_RESTORED=' + $productionRestored.ToString().ToLowerInvariant())
    Write-Output 'PLAY_CONSOLE_MUTATION_PERFORMED=false'
    Write-Output 'SUPABASE_MUTATION_PERFORMED=false'
    exit 1
}

Write-Output 'FITNEXUS_PLAY_STORE_SCREENSHOT_01_CAPTURE=PASS'
Write-Output ('SCREENSHOT=' + $screenshotPath)
Write-Output ('SCREENSHOT_SHA256=' + $screenshotSha)
Write-Output 'SCREENSHOT_SIZE=1080x1920'
Write-Output ('RECEIPT=' + $receiptPath)
Write-Output ('RECEIPT_SHA256=' + $receiptSha)
Write-Output ('PRODUCTION_RELEASE_RESTORED=' + $productionRestored.ToString().ToLowerInvariant())
Write-Output 'SYNTHETIC_DATA=true'
Write-Output 'REAL_USER_DATA=false'
Write-Output 'PLAY_CONSOLE_MUTATION_PERFORMED=false'
Write-Output 'SUPABASE_MUTATION_PERFORMED=false'
