param(
    [switch]$ValidateOnly
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$V2Path = Join-Path $PSScriptRoot 'FITNEXUS_PLAY_STORE_SCREENSHOT_02_VISUAL_STATE_REPAIR_V2.ps1'
if (-not (Test-Path -LiteralPath $V2Path -PathType Leaf)) {
    throw 'FNX_PLAY_SCREENSHOT_02_V3_V2_SOURCE_MISSING'
}

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
    if ($null -ne $cmd -and (Test-Path -LiteralPath $cmd.Source -PathType Leaf)) { $candidates.Add([string]$cmd.Source) }
    foreach ($root in @($env:ANDROID_SDK_ROOT, $env:ANDROID_HOME, (Join-Path $env:LOCALAPPDATA 'Android\Sdk'), (Join-Path $env:USERPROFILE 'AppData\Local\Android\Sdk'))) {
        if (-not [string]::IsNullOrWhiteSpace([string]$root)) {
            $candidate = Join-Path ([string]$root) 'platform-tools\adb.exe'
            if (Test-Path -LiteralPath $candidate -PathType Leaf) { $candidates.Add($candidate) }
        }
    }
    if ($candidates.Count -eq 0) { throw 'FNX_PLAY_SCREENSHOT_02_V3_ADB_NOT_FOUND' }
    return $candidates[0]
}

function Get-SingleDeviceSerial {
    param([Parameter(Mandatory = $true)][string]$Adb)
    $r = Invoke-NativeCapture -FilePath $Adb -Arguments @('devices')
    if ($r.ExitCode -ne 0) { throw ('FNX_PLAY_SCREENSHOT_02_V3_ADB_DEVICES_EXIT_' + $r.ExitCode) }
    $serials = @()
    foreach ($line in ($r.StdOut -split "`r?`n")) {
        if ($line -match '^([^\s]+)\s+device\s*$') { $serials += $Matches[1] }
    }
    if ($serials.Count -ne 1) { throw ('FNX_PLAY_SCREENSHOT_02_V3_DEVICE_COUNT_' + $serials.Count) }
    return [string]$serials[0]
}

function Get-UiHierarchy {
    param([Parameter(Mandatory = $true)][string]$Adb, [Parameter(Mandatory = $true)][string]$Serial)
    $remote = '/sdcard/fnx_store_capture_ui.xml'
    [void](Invoke-NativeCapture -FilePath $Adb -Arguments @('-s',$Serial,'shell','rm','-f',$remote))
    $dump = Invoke-NativeCapture -FilePath $Adb -Arguments @('-s',$Serial,'shell','uiautomator','dump',$remote)
    if ($dump.ExitCode -ne 0) { return '' }
    $cat = Invoke-NativeCapture -FilePath $Adb -Arguments @('-s',$Serial,'shell','cat',$remote)
    [void](Invoke-NativeCapture -FilePath $Adb -Arguments @('-s',$Serial,'shell','rm','-f',$remote))
    if ($cat.ExitCode -ne 0) { return '' }
    return [string]$cat.StdOut
}

function Test-AnrDialogPresent {
    param([Parameter(Mandatory = $true)][AllowEmptyString()][string]$Xml)
    if ([string]::IsNullOrWhiteSpace($Xml)) { return $false }
    return ($Xml -match 'android:id/aerr_close' -or $Xml -match "isn.t responding" -or $Xml -match 'not responding' -or $Xml -match 'n.o est. respondendo' -or $Xml -match 'n.o responde')
}

function Dismiss-AnrDialogs {
    param([Parameter(Mandatory = $true)][string]$Adb, [Parameter(Mandatory = $true)][string]$Serial)
    $dismissed = 0
    for ($attempt = 1; $attempt -le 4; $attempt++) {
        $xml = Get-UiHierarchy -Adb $Adb -Serial $Serial
        if ([string]::IsNullOrWhiteSpace([string]$xml)) {
            Write-Output 'SCREENSHOT_02_V3_UI_HIERARCHY=EMPTY_NO_ANR_ACTION'
            break
        }
        if (-not (Test-AnrDialogPresent -Xml $xml)) { break }

        $nodeMatch = [regex]::Match($xml, '<node[^>]*(?:resource-id="android:id/aerr_close"|text="(?:Close app|Fechar app)")[^>]*/?>', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
        if (-not $nodeMatch.Success) {
            throw 'FNX_PLAY_SCREENSHOT_02_V3_ANR_PRESENT_CLOSE_ACTION_UNRESOLVED'
        }
        $bounds = [regex]::Match($nodeMatch.Value, 'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"')
        if (-not $bounds.Success) {
            throw 'FNX_PLAY_SCREENSHOT_02_V3_ANR_CLOSE_BOUNDS_UNRESOLVED'
        }
        $x = [int]( ([int]$bounds.Groups[1].Value + [int]$bounds.Groups[3].Value) / 2 )
        $y = [int]( ([int]$bounds.Groups[2].Value + [int]$bounds.Groups[4].Value) / 2 )
        $tap = Invoke-NativeCapture -FilePath $Adb -Arguments @('-s',$Serial,'shell','input','tap',$x.ToString(),$y.ToString())
        if ($tap.ExitCode -ne 0) { throw ('FNX_PLAY_SCREENSHOT_02_V3_ANR_CLOSE_TAP_EXIT_' + $tap.ExitCode) }
        $dismissed++
        Start-Sleep -Seconds 2
    }
    return $dismissed
}

Write-Output 'SCREENSHOT_02_FOREGROUND_RECOVERY_V3=ACTIVE'

if ($ValidateOnly) {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $V2Path -ValidateOnly
    if ($LASTEXITCODE -ne 0) { exit 1 }
    Write-Output 'FITNEXUS_PLAY_STORE_SCREENSHOT_02_FOREGROUND_RECOVERY_V3_VALIDATE_ONLY=PASS'
    Write-Output 'SYSTEM_ANR_DIALOG_GUARD=ENABLED'
    Write-Output 'EMPTY_UI_HIERARCHY=SAFE_NO_ANR_ACTION'
    Write-Output 'CROSS_PROJECT_FOREGROUND_CONTAMINATION_GUARD=ENABLED'
    Write-Output 'RETRY_ONLY_IF_ANR_DETECTED=true'
    exit 0
}

$adb = Resolve-AdbExecutable
$serial = Get-SingleDeviceSerial -Adb $adb
$totalDismissed = Dismiss-AnrDialogs -Adb $adb -Serial $serial
$retryPerformed = $false

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $V2Path
$childExit = $LASTEXITCODE

if ($childExit -ne 0) {
    $xmlAfterFailure = Get-UiHierarchy -Adb $adb -Serial $serial
    if (-not [string]::IsNullOrWhiteSpace([string]$xmlAfterFailure) -and (Test-AnrDialogPresent -Xml $xmlAfterFailure)) {
        $dismissedAfterFailure = Dismiss-AnrDialogs -Adb $adb -Serial $serial
        $totalDismissed += $dismissedAfterFailure
        if ($dismissedAfterFailure -gt 0) {
            $retryPerformed = $true
            Write-Output 'SCREENSHOT_02_V3_PHASE=ANR_CLEARED_RETRY_CAPTURE_ONCE'
            & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $V2Path
            $childExit = $LASTEXITCODE
        }
    }
}

if ($childExit -ne 0) {
    Write-Output 'FITNEXUS_PLAY_STORE_SCREENSHOT_02_FOREGROUND_RECOVERY_V3=FAIL'
    Write-Output ('SYSTEM_ANR_DIALOGS_DISMISSED=' + $totalDismissed)
    Write-Output ('CAPTURE_RETRY_PERFORMED=' + $retryPerformed.ToString().ToLowerInvariant())
    Write-Output 'PRODUCTION_RELEASE_RESTORED_EXPECTED_BY_CHILD=true'
    exit 1
}

Write-Output 'FITNEXUS_PLAY_STORE_SCREENSHOT_02_FOREGROUND_RECOVERY_V3=PASS'
Write-Output ('SYSTEM_ANR_DIALOGS_DISMISSED=' + $totalDismissed)
Write-Output ('CAPTURE_RETRY_PERFORMED=' + $retryPerformed.ToString().ToLowerInvariant())
Write-Output 'CROSS_PROJECT_FOREGROUND_CONTAMINATION_GUARD=PASS'
exit 0
