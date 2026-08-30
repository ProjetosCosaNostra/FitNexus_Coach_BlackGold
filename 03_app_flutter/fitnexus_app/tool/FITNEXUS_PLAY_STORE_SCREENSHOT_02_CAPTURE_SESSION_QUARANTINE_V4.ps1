param(
    [switch]$ValidateOnly
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$V3Path = Join-Path $PSScriptRoot 'FITNEXUS_PLAY_STORE_SCREENSHOT_02_FOREGROUND_RECOVERY_V3.ps1'
if (-not (Test-Path -LiteralPath $V3Path -PathType Leaf)) {
    throw 'FNX_PLAY_SCREENSHOT_02_V4_V3_SOURCE_MISSING'
}

$PackageId = 'br.com.lafamigliaplayworks.fitnexuscoach'

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
    $p = New-Object System.Diagnostics.Process
    $p.StartInfo = $psi
    [void]$p.Start()
    $stdout = $p.StandardOutput.ReadToEnd()
    $stderr = $p.StandardError.ReadToEnd()
    $p.WaitForExit()
    return [pscustomobject]@{ ExitCode = $p.ExitCode; StdOut = $stdout; StdErr = $stderr }
}

function Resolve-AdbExecutable {
    $candidates = New-Object System.Collections.Generic.List[string]
    $cmd = Get-Command adb -ErrorAction SilentlyContinue
    if ($null -ne $cmd -and (Test-Path -LiteralPath $cmd.Source -PathType Leaf)) {
        $candidates.Add([string]$cmd.Source)
    }
    foreach ($root in @($env:ANDROID_SDK_ROOT, $env:ANDROID_HOME, (Join-Path $env:LOCALAPPDATA 'Android\Sdk'), (Join-Path $env:USERPROFILE 'AppData\Local\Android\Sdk'))) {
        if (-not [string]::IsNullOrWhiteSpace([string]$root)) {
            $candidate = Join-Path ([string]$root) 'platform-tools\adb.exe'
            if (Test-Path -LiteralPath $candidate -PathType Leaf) { $candidates.Add($candidate) }
        }
    }
    if ($candidates.Count -eq 0) { throw 'FNX_PLAY_SCREENSHOT_02_V4_ADB_NOT_FOUND' }
    return $candidates[0]
}

function Get-SingleDeviceSerial {
    param([Parameter(Mandatory = $true)][string]$Adb)
    $r = Invoke-NativeCapture -FilePath $Adb -Arguments @('devices')
    if ($r.ExitCode -ne 0) { throw ('FNX_PLAY_SCREENSHOT_02_V4_ADB_DEVICES_EXIT_' + $r.ExitCode) }
    $serials = @()
    foreach ($line in ($r.StdOut -split "`r?`n")) {
        if ($line -match '^([^\s]+)\s+device\s*$') { $serials += $Matches[1] }
    }
    if ($serials.Count -ne 1) { throw ('FNX_PLAY_SCREENSHOT_02_V4_DEVICE_COUNT_' + $serials.Count) }
    return [string]$serials[0]
}

function Enter-CaptureSessionQuarantine {
    param(
        [Parameter(Mandatory = $true)][string]$Adb,
        [Parameter(Mandatory = $true)][string]$Serial
    )

    $list = Invoke-NativeCapture -FilePath $Adb -Arguments @('-s',$Serial,'shell','pm','list','packages','-3')
    if ($list.ExitCode -ne 0) { throw ('FNX_PLAY_SCREENSHOT_02_V4_PM_LIST_EXIT_' + $list.ExitCode) }

    $stopped = New-Object System.Collections.Generic.List[string]
    foreach ($line in ($list.StdOut -split "`r?`n")) {
        if ($line -match '^package:(\S+)\s*$') {
            $pkg = [string]$Matches[1]
            if ($pkg -ne $PackageId) {
                $stop = Invoke-NativeCapture -FilePath $Adb -Arguments @('-s',$Serial,'shell','am','force-stop',$pkg)
                if ($stop.ExitCode -ne 0) { throw ('FNX_PLAY_SCREENSHOT_02_V4_FORCE_STOP_EXIT_' + $stop.ExitCode + '_' + $pkg) }
                $stopped.Add($pkg)
            }
        }
    }

    [void](Invoke-NativeCapture -FilePath $Adb -Arguments @('-s',$Serial,'shell','input','keyevent','3'))
    [void](Invoke-NativeCapture -FilePath $Adb -Arguments @('-s',$Serial,'shell','am','broadcast','-a','android.intent.action.CLOSE_SYSTEM_DIALOGS'))
    Start-Sleep -Seconds 2

    return $stopped
}

Write-Output 'SCREENSHOT_02_CAPTURE_SESSION_QUARANTINE_V4=ACTIVE'

if ($ValidateOnly) {
    $v3Text = Get-Content -LiteralPath $V3Path -Raw
    [void][ScriptBlock]::Create($v3Text)
    Write-Output 'FITNEXUS_PLAY_STORE_SCREENSHOT_02_CAPTURE_SESSION_QUARANTINE_V4_VALIDATE_ONLY=PASS'
    Write-Output 'QUARANTINE_SCOPE=USER_INSTALLED_APPS_EXCEPT_FITNEXUS'
    Write-Output 'UNINSTALL_PERFORMED=false'
    Write-Output 'APP_DATA_CLEAR_PERFORMED=false'
    Write-Output 'REMOTE_MUTATION_PERFORMED=false'
    exit 0
}

if ($env:OS -ne 'Windows_NT') { throw 'FNX_PLAY_SCREENSHOT_02_V4_WINDOWS_REQUIRED' }

$adb = Resolve-AdbExecutable
$serial = Get-SingleDeviceSerial -Adb $adb
$stopped = Enter-CaptureSessionQuarantine -Adb $adb -Serial $serial

Write-Output ('SCREENSHOT_02_V4_OTHER_USER_APPS_FORCE_STOPPED=' + $stopped.Count)
if ($stopped.Count -gt 0) {
    Write-Output ('SCREENSHOT_02_V4_QUARANTINED_PACKAGES=' + ($stopped -join ','))
}
Write-Output 'SCREENSHOT_02_V4_CROSS_PROJECT_PROCESSES=QUIESCED'

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $V3Path
$childExit = $LASTEXITCODE
if ($null -eq $childExit -or $childExit -ne 0) {
    Write-Output 'FITNEXUS_PLAY_STORE_SCREENSHOT_02_CAPTURE_SESSION_QUARANTINE_V4=FAIL'
    Write-Output 'UNINSTALL_PERFORMED=false'
    Write-Output 'APP_DATA_CLEAR_PERFORMED=false'
    Write-Output 'PRODUCTION_RELEASE_RESTORED_EXPECTED_BY_CHILD=true'
    exit 1
}

Write-Output 'FITNEXUS_PLAY_STORE_SCREENSHOT_02_CAPTURE_SESSION_QUARANTINE_V4=PASS'
Write-Output 'CAPTURE_SESSION_ISOLATION=PASS'
Write-Output 'UNINSTALL_PERFORMED=false'
Write-Output 'APP_DATA_CLEAR_PERFORMED=false'
Write-Output 'REMOTE_MUTATION_PERFORMED=false'
exit 0
