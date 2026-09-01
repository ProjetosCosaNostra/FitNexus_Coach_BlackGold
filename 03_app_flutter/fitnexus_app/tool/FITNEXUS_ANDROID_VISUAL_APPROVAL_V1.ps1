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

function Write-Utf8NoBom([string]$Path, [string]$Content) {
    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content, $encoding)
}

function Invoke-NativeCapture {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [string]$WorkingDirectory = ''
    )
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $FilePath
    $quoted = @()
    foreach ($arg in $Arguments) { $quoted += ('"' + ($arg -replace '"', '\"') + '"') }
    $psi.Arguments = ($quoted -join ' ')
    if (-not [string]::IsNullOrWhiteSpace($WorkingDirectory)) { $psi.WorkingDirectory = $WorkingDirectory }
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
    [pscustomobject]@{ ExitCode = $process.ExitCode; StdOut = $stdout; StdErr = $stderr }
}

function Resolve-Adb {
    $cmd = Get-Command adb -ErrorAction SilentlyContinue
    if ($null -ne $cmd -and (Test-Path -LiteralPath $cmd.Source -PathType Leaf)) { return $cmd.Source }
    $candidates = @()
    if ($env:ANDROID_SDK_ROOT) { $candidates += (Join-Path $env:ANDROID_SDK_ROOT 'platform-tools\adb.exe') }
    if ($env:ANDROID_HOME) { $candidates += (Join-Path $env:ANDROID_HOME 'platform-tools\adb.exe') }
    if ($env:LOCALAPPDATA) { $candidates += (Join-Path $env:LOCALAPPDATA 'Android\Sdk\platform-tools\adb.exe') }
    if ($env:USERPROFILE) { $candidates += (Join-Path $env:USERPROFILE 'AppData\Local\Android\Sdk\platform-tools\adb.exe') }
    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate -PathType Leaf)) { return $candidate }
    }
    Fail 'ADB_NOT_FOUND'
}

function Resolve-Emulator {
    $candidates = @()
    if ($env:ANDROID_SDK_ROOT) { $candidates += (Join-Path $env:ANDROID_SDK_ROOT 'emulator\emulator.exe') }
    if ($env:ANDROID_HOME) { $candidates += (Join-Path $env:ANDROID_HOME 'emulator\emulator.exe') }
    if ($env:LOCALAPPDATA) { $candidates += (Join-Path $env:LOCALAPPDATA 'Android\Sdk\emulator\emulator.exe') }
    if ($env:USERPROFILE) { $candidates += (Join-Path $env:USERPROFILE 'AppData\Local\Android\Sdk\emulator\emulator.exe') }
    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate -PathType Leaf)) { return $candidate }
    }
    Fail 'ANDROID_EMULATOR_EXE_NOT_FOUND'
}

function Get-AdbDeviceSnapshot([string]$Adb) {
    $result = Invoke-NativeCapture -FilePath $Adb -Arguments @('devices')
    if ($result.ExitCode -ne 0) { Fail ('ADB_DEVICES_FAILED_' + $result.ExitCode) }
    $devices = @()
    foreach ($line in ($result.StdOut -split "`r?`n")) {
        if ($line -match '^([^\s]+)\s+(device|offline|unauthorized)\s*$') {
            $devices += [pscustomobject]@{ Serial = [string]$Matches[1]; State = [string]$Matches[2] }
        }
    }
    return @($devices)
}

function Get-FreeEmulatorPort([string]$Adb) {
    $used = New-Object 'System.Collections.Generic.HashSet[int]'
    foreach ($device in @(Get-AdbDeviceSnapshot -Adb $Adb)) {
        if ($device.Serial -match '^emulator-(\d+)$') {
            [void]$used.Add([int]$Matches[1]); [void]$used.Add(([int]$Matches[1]) + 1)
        }
    }
    try {
        $props = [System.Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties()
        foreach ($endpoint in $props.GetActiveTcpListeners()) { [void]$used.Add([int]$endpoint.Port) }
        foreach ($endpoint in $props.GetActiveUdpListeners()) { [void]$used.Add([int]$endpoint.Port) }
    } catch {}
    for ($port = 5580; $port -le 5680; $port += 2) {
        if (-not $used.Contains($port) -and -not $used.Contains($port + 1)) { return $port }
    }
    Fail 'NO_FREE_EMULATOR_PORT_IN_5580_5680'
}

function Wait-NewEmulatorRegistered {
    param([string]$Adb,[string]$Serial,[System.Diagnostics.Process]$EmulatorProcess,[int]$TimeoutSeconds = 180)
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        if ($EmulatorProcess.HasExited) { Fail ('NEW_EMULATOR_PROCESS_EXITED_' + $EmulatorProcess.ExitCode) }
        foreach ($device in @(Get-AdbDeviceSnapshot -Adb $Adb)) {
            if ($device.Serial -eq $Serial) { return }
        }
        Start-Sleep -Seconds 2
    }
    Fail ('NEW_EMULATOR_NOT_REGISTERED_TIMEOUT_' + $Serial)
}

function Wait-NewEmulatorBooted {
    param([string]$Adb,[string]$Serial,[System.Diagnostics.Process]$EmulatorProcess,[int]$TimeoutSeconds = 300)
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        if ($EmulatorProcess.HasExited) { Fail ('NEW_EMULATOR_PROCESS_EXITED_DURING_BOOT_' + $EmulatorProcess.ExitCode) }
        $state = Invoke-NativeCapture -FilePath $Adb -Arguments @('-s',$Serial,'get-state')
        if ($state.ExitCode -eq 0 -and $state.StdOut.Trim() -eq 'device') {
            $boot = Invoke-NativeCapture -FilePath $Adb -Arguments @('-s',$Serial,'shell','getprop','sys.boot_completed')
            if ($boot.ExitCode -eq 0 -and $boot.StdOut.Trim() -eq '1') { return }
        }
        Start-Sleep -Seconds 2
    }
    Fail ('NEW_EMULATOR_BOOT_TIMEOUT_' + $Serial)
}

$pubspec = Get-Content -LiteralPath (Join-Path $AppRoot 'pubspec.yaml') -Raw
if ($pubspec -notmatch '(?m)^version:\s*0\.9\.0\+3\s*$') { Fail 'RELEASE_VERSION_NOT_0_9_0_PLUS_3' }
if ($ValidateOnly) {
    Write-Output 'FITNEXUS_ANDROID_VISUAL_APPROVAL_VALIDATE_ONLY=PASS'
    Write-Output 'EXPECTED_VERSION=0.9.0+3'
    Write-Output 'NEW_DEDICATED_EMULATOR_REQUIRED=true'
    Write-Output 'EXISTING_EMULATORS_TOUCHED=false'
    Write-Output 'SCREENSHOT_CAPTURE_PERFORMED=false'
    Write-Output 'PLAY_UPLOAD_PERFORMED=false'
    exit 0
}
if ($env:OS -ne 'Windows_NT') { Fail 'WINDOWS_REQUIRED' }
if ([string]::IsNullOrWhiteSpace($env:USERPROFILE)) { Fail 'USERPROFILE_MISSING' }

$flutter = Get-Command flutter -ErrorAction SilentlyContinue
if ($null -eq $flutter) { Fail 'FLUTTER_NOT_FOUND' }
$Adb = Resolve-Adb
$Emulator = Resolve-Emulator
$existingDevices = @(Get-AdbDeviceSnapshot -Adb $Adb)
$existingSerials = @($existingDevices | ForEach-Object { $_.Serial })
Write-Output ('EXISTING_DEVICE_COUNT=' + $existingSerials.Count)
Write-Output 'EXISTING_EMULATORS_TOUCHED=false'

$avdResult = Invoke-NativeCapture -FilePath $Emulator -Arguments @('-list-avds')
if ($avdResult.ExitCode -ne 0) { Fail ('AVD_LIST_FAILED_' + $avdResult.ExitCode) }
$avds = @($avdResult.StdOut -split "`r?`n" | ForEach-Object { $_.Trim() } | Where-Object { $_ })
if ($avds.Count -lt 1) { Fail 'NO_INSTALLED_AVD_TEMPLATE' }
$AvdName = [string]$avds[0]
$Port = Get-FreeEmulatorPort -Adb $Adb
$Serial = 'emulator-' + $Port
if ($existingSerials -contains $Serial) { Fail ('SERIAL_COLLISION_' + $Serial) }

Write-Output ('NEW_EMULATOR_AVD_TEMPLATE=' + $AvdName)
Write-Output ('NEW_EMULATOR_SERIAL=' + $Serial)
Write-Output 'PHASE=START_ISOLATED_VISIBLE_EMULATOR'
$EmulatorProcess = Start-Process -FilePath $Emulator -ArgumentList @('-avd',$AvdName,'-port',[string]$Port,'-read-only','-no-snapshot-save','-no-boot-anim') -PassThru
if ($null -eq $EmulatorProcess) { Fail 'NEW_EMULATOR_START_PROCESS_FAILED' }
Write-Output ('NEW_EMULATOR_PID=' + $EmulatorProcess.Id)
Write-Output 'PHASE=WAIT_NEW_EMULATOR_REGISTRATION'
Wait-NewEmulatorRegistered -Adb $Adb -Serial $Serial -EmulatorProcess $EmulatorProcess
Write-Output 'PHASE=WAIT_NEW_EMULATOR_BOOT'
Wait-NewEmulatorBooted -Adb $Adb -Serial $Serial -EmulatorProcess $EmulatorProcess

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
    $keyProperties = @($Marker,"storePassword=$plainPassword","keyPassword=$plainPassword","keyAlias=$UploadAlias","storeFile=$storePath") -join [Environment]::NewLine
    Write-Utf8NoBom $KeyPropertiesFile ($keyProperties + [Environment]::NewLine)
    Write-Output 'PHASE=FLUTTER_PUB_GET'
    $pubGet = Invoke-NativeCapture -FilePath $flutter.Source -Arguments @('pub','get') -WorkingDirectory $AppRoot
    if ($pubGet.ExitCode -ne 0) { Fail ('FLUTTER_PUB_GET_FAILED_' + $pubGet.ExitCode) }
    Write-Output 'PHASE=BUILD_SIGNED_RELEASE_APK'
    $build = Invoke-NativeCapture -FilePath $flutter.Source -Arguments @('build','apk','--release') -WorkingDirectory $AppRoot
    if ($build.ExitCode -ne 0) { Fail ('RELEASE_APK_BUILD_FAILED_' + $build.ExitCode) }
    $Apk = Join-Path $AppRoot 'build\app\outputs\flutter-apk\app-release.apk'
    if (-not (Test-Path -LiteralPath $Apk -PathType Leaf)) { Fail 'RELEASE_APK_NOT_FOUND' }
    Write-Output 'PHASE=INSTALL_RELEASE_APK_ONLY_ON_NEW_EMULATOR'
    $install = Invoke-NativeCapture -FilePath $Adb -Arguments @('-s',$Serial,'install','-r',$Apk)
    if ($install.ExitCode -ne 0 -or $install.StdOut -notmatch 'Success') { Fail ('ADB_INSTALL_FAILED_' + $install.ExitCode) }
    $dumpResult = Invoke-NativeCapture -FilePath $Adb -Arguments @('-s',$Serial,'shell','dumpsys','package',$PackageId)
    if ($dumpResult.ExitCode -ne 0) { Fail 'PACKAGE_DUMPSYS_FAILED' }
    $dump = $dumpResult.StdOut
    $versionName = if ($dump -match 'versionName=([^\s]+)') { [string]$Matches[1] } else { '' }
    $versionCode = if ($dump -match 'versionCode=(\d+)') { [string]$Matches[1] } else { '' }
    if ($versionName -ne $ExpectedVersionName -or $versionCode -ne $ExpectedVersionCode) { Fail ("INSTALLED_VERSION_MISMATCH_${versionName}_${versionCode}") }
    Write-Output 'PHASE=WAKE_AND_OPEN_FITNEXUS_ONLY_ON_NEW_EMULATOR'
    [void](Invoke-NativeCapture -FilePath $Adb -Arguments @('-s',$Serial,'shell','input','keyevent','224'))
    [void](Invoke-NativeCapture -FilePath $Adb -Arguments @('-s',$Serial,'shell','wm','dismiss-keyguard'))
    [void](Invoke-NativeCapture -FilePath $Adb -Arguments @('-s',$Serial,'shell','am','force-stop',$PackageId))
    $launch = Invoke-NativeCapture -FilePath $Adb -Arguments @('-s',$Serial,'shell','am','start','-W','-n',"$PackageId/.MainActivity")
    if ($launch.ExitCode -ne 0 -or $launch.StdOut -match 'Error:') { Fail 'MAIN_ACTIVITY_LAUNCH_FAILED' }
    Start-Sleep -Seconds 3
    $focused = Invoke-NativeCapture -FilePath $Adb -Arguments @('-s',$Serial,'shell','dumpsys','window','windows')
    if ($focused.ExitCode -ne 0 -or $focused.StdOut -notmatch [regex]::Escape($PackageId)) { Fail 'FITNEXUS_NOT_FOREGROUND_ON_NEW_EMULATOR' }
    Write-Output 'FITNEXUS_ANDROID_VISUAL_APPROVAL=READY'
    Write-Output ('NEW_EMULATOR_SERIAL=' + $Serial)
    Write-Output ('NEW_EMULATOR_PID=' + $EmulatorProcess.Id)
    Write-Output ('INSTALLED_VERSION_NAME=' + $versionName)
    Write-Output ('INSTALLED_VERSION_CODE=' + $versionCode)
    Write-Output ('APK_SHA256=' + (Get-FileHash -LiteralPath $Apk -Algorithm SHA256).Hash.ToLowerInvariant())
    Write-Output 'APP_OPEN_IN_NEW_EMULATOR=true'
    Write-Output 'EXISTING_EMULATORS_TOUCHED=false'
    Write-Output 'HUMAN_VISUAL_APPROVAL_REQUIRED=true'
    Write-Output 'SCREENSHOT_CAPTURE_PERFORMED=false'
    Write-Output 'PLAY_UPLOAD_PERFORMED=false'
}
finally {
    if (Test-Path -LiteralPath $KeyPropertiesFile -PathType Leaf) {
        $owned = Get-Content -LiteralPath $KeyPropertiesFile -Raw -ErrorAction SilentlyContinue
        if ($owned -match [regex]::Escape($Marker)) { Remove-Item -LiteralPath $KeyPropertiesFile -Force -ErrorAction SilentlyContinue }
    }
    $plainPassword = $null
}
