param(
    [switch]$ValidateOnly
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

function Invoke-NativeCapture {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $FilePath
    $quoted = @()
    foreach ($arg in $Arguments) {
        $quoted += ('"' + ($arg -replace '"', '\"') + '"')
    }
    $psi.Arguments = ($quoted -join ' ')
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

function Resolve-AdbExecutable {
    $command = Get-Command adb -ErrorAction SilentlyContinue
    if ($null -ne $command -and -not [string]::IsNullOrWhiteSpace([string]$command.Source) -and (Test-Path -LiteralPath ([string]$command.Source))) {
        return [pscustomobject]@{
            Path = [string]$command.Source
            Source = 'PATH'
        }
    }

    $sdkRoots = @()
    if (-not [string]::IsNullOrWhiteSpace($env:ANDROID_SDK_ROOT)) { $sdkRoots += [string]$env:ANDROID_SDK_ROOT }
    if (-not [string]::IsNullOrWhiteSpace($env:ANDROID_HOME)) { $sdkRoots += [string]$env:ANDROID_HOME }
    if (-not [string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) { $sdkRoots += (Join-Path $env:LOCALAPPDATA 'Android\Sdk') }
    if (-not [string]::IsNullOrWhiteSpace($env:USERPROFILE)) { $sdkRoots += (Join-Path $env:USERPROFILE 'AppData\Local\Android\Sdk') }

    $seen = @{}
    foreach ($root in $sdkRoots) {
        if ([string]::IsNullOrWhiteSpace($root)) { continue }
        $normalized = $root.Trim().TrimEnd('\')
        if ($seen.ContainsKey($normalized.ToLowerInvariant())) { continue }
        $seen[$normalized.ToLowerInvariant()] = $true
        $candidate = Join-Path $normalized 'platform-tools\adb.exe'
        if (Test-Path -LiteralPath $candidate) {
            return [pscustomobject]@{
                Path = $candidate
                Source = 'ANDROID_SDK_CANDIDATE'
            }
        }
    }

    $flutter = Get-Command flutter -ErrorAction SilentlyContinue
    if ($null -ne $flutter -and -not [string]::IsNullOrWhiteSpace([string]$flutter.Source)) {
        try {
            $doctor = Invoke-NativeCapture -FilePath ([string]$flutter.Source) -Arguments @('doctor', '-v')
            if ($doctor.ExitCode -eq 0) {
                foreach ($line in ($doctor.StdOut -split "`r?`n")) {
                    if ($line -match 'Android SDK at\s+(.+)$') {
                        $doctorRoot = ([string]$Matches[1]).Trim()
                        $doctorCandidate = Join-Path $doctorRoot 'platform-tools\adb.exe'
                        if (Test-Path -LiteralPath $doctorCandidate) {
                            return [pscustomobject]@{
                                Path = $doctorCandidate
                                Source = 'FLUTTER_DOCTOR_ANDROID_SDK'
                            }
                        }
                    }
                }
            }
        }
        catch {
            # Expected discovery miss: continue fail-closed without hiding the final resolver outcome.
        }
    }

    return $null
}

$AppRoot = Split-Path -Parent $PSScriptRoot
$ContractPath = Join-Path $AppRoot 'android\play_store\PLAY_STORE_REAL_ASSETS_PREFLIGHT_V1.json'
if (-not (Test-Path -LiteralPath $ContractPath)) {
    throw 'FNX_PLAY_ASSET_PREFLIGHT_CONTRACT_MISSING'
}

$Contract = Get-Content -LiteralPath $ContractPath -Raw | ConvertFrom-Json
$PackageId = [string]$Contract.application_id
if ($PackageId -ne 'br.com.lafamigliaplayworks.fitnexuscoach') {
    throw 'FNX_PLAY_ASSET_PREFLIGHT_PACKAGE_DRIFT'
}

if ([bool]$Contract.hard_boundaries.captures_store_screenshots -or
    [bool]$Contract.hard_boundaries.creates_test_accounts -or
    [bool]$Contract.hard_boundaries.mutates_supabase -or
    [bool]$Contract.hard_boundaries.mutates_play_console -or
    [bool]$Contract.hard_boundaries.uploads_aab -or
    [bool]$Contract.hard_boundaries.publishes_assets -or
    [bool]$Contract.hard_boundaries.activates_billing) {
    throw 'FNX_PLAY_ASSET_PREFLIGHT_BOUNDARY_DRIFT'
}

if ($ValidateOnly) {
    Write-Output 'FITNEXUS_PLAY_STORE_REAL_ASSETS_PREFLIGHT_VALIDATE_ONLY=PASS'
    Write-Output ('APPLICATION_ID=' + $PackageId)
    Write-Output 'ADB_RESOLVER=PATH+ANDROID_SDK_ROOT+ANDROID_HOME+LOCALAPPDATA+USERPROFILE+FLUTTER_DOCTOR'
    Write-Output 'REMOTE_MUTATION_PERFORMED=false'
    Write-Output 'SCREENSHOT_CAPTURE_PERFORMED=false'
    exit 0
}

try {
    if ($env:OS -ne 'Windows_NT') {
        throw 'FNX_PLAY_ASSET_PREFLIGHT_WINDOWS_REQUIRED'
    }

    $AdbResolution = Resolve-AdbExecutable
    if ($null -eq $AdbResolution) {
        throw 'FNX_PLAY_ASSET_PREFLIGHT_ADB_UNRESOLVED_AFTER_SDK_DISCOVERY'
    }
    $Adb = [string]$AdbResolution.Path
    $AdbResolutionSource = [string]$AdbResolution.Source

    $DevicesResult = Invoke-NativeCapture -FilePath $Adb -Arguments @('devices')
    if ($DevicesResult.ExitCode -ne 0) {
        throw ('FNX_PLAY_ASSET_PREFLIGHT_ADB_DEVICES_EXIT_' + $DevicesResult.ExitCode)
    }

    $DeviceSerials = @()
    foreach ($line in ($DevicesResult.StdOut -split "`r?`n")) {
        if ($line -match '^([^\s]+)\s+device\s*$') {
            $DeviceSerials += $Matches[1]
        }
    }
    if ($DeviceSerials.Count -ne 1) {
        throw ('FNX_PLAY_ASSET_PREFLIGHT_DEVICE_COUNT_' + $DeviceSerials.Count)
    }
    $Serial = [string]$DeviceSerials[0]

    $PackageResult = Invoke-NativeCapture -FilePath $Adb -Arguments @('-s', $Serial, 'shell', 'pm', 'path', $PackageId)
    if ($PackageResult.ExitCode -ne 0 -or [string]::IsNullOrWhiteSpace($PackageResult.StdOut) -or $PackageResult.StdOut -notmatch 'package:') {
        throw 'FNX_PLAY_ASSET_PREFLIGHT_CANONICAL_PACKAGE_NOT_INSTALLED'
    }

    $SizeResult = Invoke-NativeCapture -FilePath $Adb -Arguments @('-s', $Serial, 'shell', 'wm', 'size')
    if ($SizeResult.ExitCode -ne 0) {
        throw ('FNX_PLAY_ASSET_PREFLIGHT_WM_SIZE_EXIT_' + $SizeResult.ExitCode)
    }
    $DisplayWidth = 0
    $DisplayHeight = 0
    if ($SizeResult.StdOut -match '(?:Physical|Override) size:\s*(\d+)x(\d+)') {
        $DisplayWidth = [int]$Matches[1]
        $DisplayHeight = [int]$Matches[2]
    }
    if ($DisplayWidth -le 0 -or $DisplayHeight -le 0) {
        throw 'FNX_PLAY_ASSET_PREFLIGHT_DISPLAY_SIZE_UNRESOLVED'
    }

    $ModelResult = Invoke-NativeCapture -FilePath $Adb -Arguments @('-s', $Serial, 'shell', 'getprop', 'ro.product.model')
    $Model = if ($ModelResult.ExitCode -eq 0) { $ModelResult.StdOut.Trim() } else { '' }

    $PackageDump = Invoke-NativeCapture -FilePath $Adb -Arguments @('-s', $Serial, 'shell', 'dumpsys', 'package', $PackageId)
    $VersionName = ''
    $VersionCode = ''
    if ($PackageDump.ExitCode -eq 0) {
        if ($PackageDump.StdOut -match 'versionName=([^\s]+)') { $VersionName = [string]$Matches[1] }
        if ($PackageDump.StdOut -match 'versionCode=(\d+)') { $VersionCode = [string]$Matches[1] }
    }

    $Documents = [Environment]::GetFolderPath('MyDocuments')
    if ([string]::IsNullOrWhiteSpace($Documents)) {
        throw 'FNX_PLAY_ASSET_PREFLIGHT_DOCUMENTS_UNRESOLVED'
    }
    $Current = Join-Path $Documents 'FitNexus_Coach_BlackGold_EXTERNAL\play_store_assets\current'
    New-Item -ItemType Directory -Path $Current -Force | Out-Null
    Get-ChildItem -LiteralPath $Current -File -ErrorAction SilentlyContinue | Remove-Item -Force

    $ReceiptPath = Join-Path $Current 'FITNEXUS_PLAY_STORE_REAL_ASSETS_PREFLIGHT_RECEIPT_V1.json'
    $Receipt = [ordered]@{
        schema_version = 2
        kind = 'FITNEXUS_PLAY_STORE_REAL_ASSETS_PREFLIGHT_RECEIPT'
        generated_at_utc = [DateTime]::UtcNow.ToString('o')
        result = 'PASS'
        application_id = $PackageId
        release_train_version = [string]$Contract.release_train_version
        adb_resolution_source = $AdbResolutionSource
        adb_path_sha256 = (Get-TextSha256 -Value $Adb)
        device_serial_sha256 = (Get-TextSha256 -Value $Serial)
        device_model = $Model
        display_width_px = $DisplayWidth
        display_height_px = $DisplayHeight
        portrait_ready = ($DisplayHeight -gt $DisplayWidth)
        installed_version_name = $VersionName
        installed_version_code = $VersionCode
        canonical_package_installed = $true
        screenshot_capture_performed = $false
        remote_mutation_performed = $false
        play_console_mutation_performed = $false
        supabase_mutation_performed = $false
        aab_upload_performed = $false
        next_gate = 'REAL_APP_AUTHENTICATED_SYNTHETIC_DATA_CAPTURE_AUTOMATION'
    }
    $Receipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $ReceiptPath -Encoding UTF8
    $ReceiptSha = (Get-FileHash -LiteralPath $ReceiptPath -Algorithm SHA256).Hash.ToLowerInvariant()

    Write-Output 'FITNEXUS_PLAY_STORE_REAL_ASSETS_PREFLIGHT=PASS'
    Write-Output ('APPLICATION_ID=' + $PackageId)
    Write-Output ('ADB_RESOLUTION_SOURCE=' + $AdbResolutionSource)
    Write-Output ('DEVICE_MODEL=' + $Model)
    Write-Output ('DISPLAY_SIZE=' + $DisplayWidth + 'x' + $DisplayHeight)
    Write-Output ('INSTALLED_VERSION_NAME=' + $VersionName)
    Write-Output ('INSTALLED_VERSION_CODE=' + $VersionCode)
    Write-Output ('RECEIPT=' + $ReceiptPath)
    Write-Output ('RECEIPT_SHA256=' + $ReceiptSha)
    Write-Output 'SCREENSHOT_CAPTURE_PERFORMED=false'
    Write-Output 'REMOTE_MUTATION_PERFORMED=false'
}
catch {
    Write-Output 'FITNEXUS_PLAY_STORE_REAL_ASSETS_PREFLIGHT=FAIL'
    Write-Output ('FAILURE_CLASS=' + $_.Exception.Message)
    Write-Output 'SCREENSHOT_CAPTURE_PERFORMED=false'
    Write-Output 'REMOTE_MUTATION_PERFORMED=false'
    exit 1
}
