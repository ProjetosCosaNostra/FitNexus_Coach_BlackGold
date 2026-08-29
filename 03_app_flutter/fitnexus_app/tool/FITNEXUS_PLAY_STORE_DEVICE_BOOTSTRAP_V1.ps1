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

function Write-Utf8NoBom {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Content
    )
    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content, $encoding)
}

function Resolve-AdbExecutable {
    $candidates = New-Object System.Collections.Generic.List[object]

    $pathCommand = Get-Command adb -ErrorAction SilentlyContinue
    if ($null -ne $pathCommand -and (Test-Path -LiteralPath $pathCommand.Source -PathType Leaf)) {
        $candidates.Add([pscustomobject]@{ Path = [string]$pathCommand.Source; Source = 'PATH' })
    }

    foreach ($rootInfo in @(
        [pscustomobject]@{ Root = $env:ANDROID_SDK_ROOT; Source = 'ANDROID_SDK_ROOT' },
        [pscustomobject]@{ Root = $env:ANDROID_HOME; Source = 'ANDROID_HOME' },
        [pscustomobject]@{ Root = (if ($env:LOCALAPPDATA) { Join-Path $env:LOCALAPPDATA 'Android\Sdk' } else { '' }); Source = 'LOCALAPPDATA_STANDARD' },
        [pscustomobject]@{ Root = (if ($env:USERPROFILE) { Join-Path $env:USERPROFILE 'AppData\Local\Android\Sdk' } else { '' }); Source = 'USERPROFILE_STANDARD' }
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
        throw 'FNX_PLAY_DEVICE_BOOTSTRAP_ADB_NOT_FOUND'
    }

    return $candidates[0]
}

$AppRoot = Split-Path -Parent $PSScriptRoot
$AndroidDir = Join-Path $AppRoot 'android'
$ContractPath = Join-Path $AndroidDir 'play_store\PLAY_STORE_DEVICE_BOOTSTRAP_V1.json'
$KeyPropertiesFile = Join-Path $AndroidDir 'key.properties'
$Marker = '# GENERATED_BY=FITNEXUS_PLAY_STORE_DEVICE_BOOTSTRAP_V1'
$PackageId = 'br.com.lafamigliaplayworks.fitnexuscoach'
$UploadAlias = 'fitnexus_upload'

if (-not (Test-Path -LiteralPath $ContractPath -PathType Leaf)) {
    throw 'FNX_PLAY_DEVICE_BOOTSTRAP_CONTRACT_MISSING'
}
$Contract = Get-Content -LiteralPath $ContractPath -Raw | ConvertFrom-Json
if ([string]$Contract.application_id -ne $PackageId) {
    throw 'FNX_PLAY_DEVICE_BOOTSTRAP_PACKAGE_DRIFT'
}
foreach ($property in $Contract.hard_boundaries.PSObject.Properties) {
    if ([bool]$property.Value) {
        throw ('FNX_PLAY_DEVICE_BOOTSTRAP_BOUNDARY_DRIFT_' + $property.Name)
    }
}

if ($ValidateOnly) {
    Write-Output 'FITNEXUS_PLAY_STORE_DEVICE_BOOTSTRAP_VALIDATE_ONLY=PASS'
    Write-Output ('APPLICATION_ID=' + $PackageId)
    Write-Output 'DEVICE_INSTALL_PERFORMED=false'
    Write-Output 'REMOTE_MUTATION_PERFORMED=false'
    exit 0
}

$plainPassword = $null
try {
    if ($env:OS -ne 'Windows_NT') {
        throw 'FNX_PLAY_DEVICE_BOOTSTRAP_WINDOWS_REQUIRED'
    }
    if ([string]::IsNullOrWhiteSpace($env:USERPROFILE)) {
        throw 'FNX_PLAY_DEVICE_BOOTSTRAP_USERPROFILE_MISSING'
    }

    $adbInfo = Resolve-AdbExecutable
    $Adb = [string]$adbInfo.Path
    $AdbSource = [string]$adbInfo.Source

    $devicesResult = Invoke-NativeCapture -FilePath $Adb -Arguments @('devices')
    if ($devicesResult.ExitCode -ne 0) {
        throw ('FNX_PLAY_DEVICE_BOOTSTRAP_ADB_DEVICES_EXIT_' + $devicesResult.ExitCode)
    }
    $serials = @()
    foreach ($line in ($devicesResult.StdOut -split "`r?`n")) {
        if ($line -match '^([^\s]+)\s+device\s*$') {
            $serials += $Matches[1]
        }
    }
    if ($serials.Count -ne 1) {
        throw ('FNX_PLAY_DEVICE_BOOTSTRAP_DEVICE_COUNT_' + $serials.Count)
    }
    $Serial = [string]$serials[0]

    $packageBefore = Invoke-NativeCapture -FilePath $Adb -Arguments @('-s', $Serial, 'shell', 'pm', 'path', $PackageId)
    $alreadyInstalled = ($packageBefore.ExitCode -eq 0 -and $packageBefore.StdOut -match 'package:')
    $installPerformed = $false
    $apkSha = ''
    $apkBytes = 0

    if (-not $alreadyInstalled) {
        $flutter = Get-Command flutter -ErrorAction SilentlyContinue
        if ($null -eq $flutter) {
            throw 'FNX_PLAY_DEVICE_BOOTSTRAP_FLUTTER_NOT_FOUND'
        }

        $ExternalRoot = Join-Path $env:USERPROFILE 'Documents\FitNexus_Coach_BlackGold_EXTERNAL\play_signing'
        $AuthorityDir = Join-Path $ExternalRoot 'authority'
        $KeystoreFile = Join-Path $AuthorityDir 'fitnexus-upload-key.jks'
        $ProtectedSecretFile = Join-Path $AuthorityDir 'upload-key-secret.dpapi'
        if (-not (Test-Path -LiteralPath $KeystoreFile -PathType Leaf) -or -not (Test-Path -LiteralPath $ProtectedSecretFile -PathType Leaf)) {
            throw 'FNX_PLAY_DEVICE_BOOTSTRAP_SIGNING_AUTHORITY_MISSING'
        }

        $protected = (Get-Content -LiteralPath $ProtectedSecretFile -Raw).Trim()
        $secure = ConvertTo-SecureString $protected
        $credential = New-Object System.Net.NetworkCredential('', $secure)
        $plainPassword = $credential.Password
        if ([string]::IsNullOrWhiteSpace($plainPassword)) {
            throw 'FNX_PLAY_DEVICE_BOOTSTRAP_DPAPI_SECRET_EMPTY'
        }

        if (Test-Path -LiteralPath $KeyPropertiesFile -PathType Leaf) {
            $existing = Get-Content -LiteralPath $KeyPropertiesFile -Raw
            if ($existing -notmatch [regex]::Escape($Marker)) {
                throw 'FNX_PLAY_DEVICE_BOOTSTRAP_FOREIGN_KEY_PROPERTIES_PRESENT'
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

        $pubGet = Invoke-NativeCapture -FilePath $flutter.Source -Arguments @('pub', 'get') -WorkingDirectory $AppRoot
        if ($pubGet.ExitCode -ne 0) {
            throw ('FNX_PLAY_DEVICE_BOOTSTRAP_FLUTTER_PUB_GET_EXIT_' + $pubGet.ExitCode)
        }
        $build = Invoke-NativeCapture -FilePath $flutter.Source -Arguments @('build', 'apk', '--release') -WorkingDirectory $AppRoot
        if ($build.ExitCode -ne 0) {
            throw ('FNX_PLAY_DEVICE_BOOTSTRAP_RELEASE_APK_BUILD_EXIT_' + $build.ExitCode)
        }

        $apk = Join-Path $AppRoot 'build\app\outputs\flutter-apk\app-release.apk'
        if (-not (Test-Path -LiteralPath $apk -PathType Leaf)) {
            throw 'FNX_PLAY_DEVICE_BOOTSTRAP_RELEASE_APK_MISSING'
        }
        $apkSha = (Get-FileHash -LiteralPath $apk -Algorithm SHA256).Hash.ToLowerInvariant()
        $apkBytes = (Get-Item -LiteralPath $apk).Length

        $install = Invoke-NativeCapture -FilePath $Adb -Arguments @('-s', $Serial, 'install', '-r', $apk)
        if ($install.ExitCode -ne 0 -or $install.StdOut -notmatch 'Success') {
            throw ('FNX_PLAY_DEVICE_BOOTSTRAP_ADB_INSTALL_FAILED_' + $install.ExitCode)
        }
        $installPerformed = $true
    }

    $packageAfter = Invoke-NativeCapture -FilePath $Adb -Arguments @('-s', $Serial, 'shell', 'pm', 'path', $PackageId)
    if ($packageAfter.ExitCode -ne 0 -or $packageAfter.StdOut -notmatch 'package:') {
        throw 'FNX_PLAY_DEVICE_BOOTSTRAP_CANONICAL_PACKAGE_STILL_MISSING'
    }

    $dump = Invoke-NativeCapture -FilePath $Adb -Arguments @('-s', $Serial, 'shell', 'dumpsys', 'package', $PackageId)
    $versionName = ''
    $versionCode = ''
    if ($dump.ExitCode -eq 0) {
        if ($dump.StdOut -match 'versionName=([^\s]+)') { $versionName = [string]$Matches[1] }
        if ($dump.StdOut -match 'versionCode=(\d+)') { $versionCode = [string]$Matches[1] }
    }
    if ($versionName -ne '0.9.0' -or $versionCode -ne '2') {
        throw ('FNX_PLAY_DEVICE_BOOTSTRAP_VERSION_MISMATCH_' + $versionName + '_' + $versionCode)
    }

    $modelResult = Invoke-NativeCapture -FilePath $Adb -Arguments @('-s', $Serial, 'shell', 'getprop', 'ro.product.model')
    $model = if ($modelResult.ExitCode -eq 0) { $modelResult.StdOut.Trim() } else { '' }

    $documents = [Environment]::GetFolderPath('MyDocuments')
    if ([string]::IsNullOrWhiteSpace($documents)) {
        throw 'FNX_PLAY_DEVICE_BOOTSTRAP_DOCUMENTS_UNRESOLVED'
    }
    $current = Join-Path $documents 'FitNexus_Coach_BlackGold_EXTERNAL\play_store_device_bootstrap\current'
    New-Item -ItemType Directory -Path $current -Force | Out-Null
    Get-ChildItem -LiteralPath $current -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force

    $receiptPath = Join-Path $current 'FITNEXUS_PLAY_STORE_DEVICE_BOOTSTRAP_RECEIPT_V1.json'
    $receipt = [ordered]@{
        schema_version = 1
        kind = 'FITNEXUS_PLAY_STORE_DEVICE_BOOTSTRAP_RECEIPT'
        generated_at_utc = [DateTime]::UtcNow.ToString('o')
        result = 'PASS'
        application_id = $PackageId
        release_train_version = [string]$Contract.release_train_version
        adb_resolution_source = $AdbSource
        adb_path_sha256 = (Get-TextSha256 -Value $Adb)
        device_serial_sha256 = (Get-TextSha256 -Value $Serial)
        device_model = $model
        package_was_installed_before = $alreadyInstalled
        device_install_performed = $installPerformed
        installed_version_name = $versionName
        installed_version_code = $versionCode
        release_apk_sha256 = $apkSha
        release_apk_bytes = $apkBytes
        temporary_key_properties_removed = $true
        remote_mutation_performed = $false
        play_console_mutation_performed = $false
        supabase_mutation_performed = $false
        aab_upload_performed = $false
        screenshot_capture_performed = $false
        next_gate = 'PLAY_STORE_REAL_ASSETS_PREFLIGHT_PASS'
    }
    Write-Utf8NoBom -Path $receiptPath -Content (($receipt | ConvertTo-Json -Depth 6) + [Environment]::NewLine)
    $receiptSha = (Get-FileHash -LiteralPath $receiptPath -Algorithm SHA256).Hash.ToLowerInvariant()

    Write-Output 'FITNEXUS_PLAY_STORE_DEVICE_BOOTSTRAP=PASS'
    Write-Output ('APPLICATION_ID=' + $PackageId)
    Write-Output ('ADB_RESOLUTION_SOURCE=' + $AdbSource)
    Write-Output ('DEVICE_MODEL=' + $model)
    Write-Output ('INSTALLED_VERSION_NAME=' + $versionName)
    Write-Output ('INSTALLED_VERSION_CODE=' + $versionCode)
    Write-Output ('DEVICE_INSTALL_PERFORMED=' + $installPerformed.ToString().ToLowerInvariant())
    Write-Output ('RECEIPT=' + $receiptPath)
    Write-Output ('RECEIPT_SHA256=' + $receiptSha)
    Write-Output 'SCREENSHOT_CAPTURE_PERFORMED=false'
    Write-Output 'REMOTE_MUTATION_PERFORMED=false'
}
catch {
    Write-Output 'FITNEXUS_PLAY_STORE_DEVICE_BOOTSTRAP=FAIL'
    Write-Output ('FAILURE_CLASS=' + $_.Exception.Message)
    Write-Output 'SCREENSHOT_CAPTURE_PERFORMED=false'
    Write-Output 'REMOTE_MUTATION_PERFORMED=false'
    exit 1
}
finally {
    if (Test-Path -LiteralPath $KeyPropertiesFile -PathType Leaf) {
        $owned = Get-Content -LiteralPath $KeyPropertiesFile -Raw -ErrorAction SilentlyContinue
        if ($owned -match [regex]::Escape($Marker)) {
            Remove-Item -LiteralPath $KeyPropertiesFile -Force
        }
    }
    $plainPassword = $null
}
