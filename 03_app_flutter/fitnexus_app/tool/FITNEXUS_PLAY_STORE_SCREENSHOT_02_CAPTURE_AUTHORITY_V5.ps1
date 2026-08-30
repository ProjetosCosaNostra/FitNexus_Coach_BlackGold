param(
    [switch]$ValidateOnly
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$BasePath = Join-Path $PSScriptRoot 'FITNEXUS_PLAY_STORE_SCREENSHOT_02_CAPTURE_V1.ps1'
if (-not (Test-Path -LiteralPath $BasePath -PathType Leaf)) {
    throw 'FNX_PLAY_SCREENSHOT_02_V5_BASE_SOURCE_MISSING'
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
    if ($candidates.Count -eq 0) { throw 'FNX_PLAY_SCREENSHOT_02_V5_ADB_NOT_FOUND' }
    return $candidates[0]
}

function Get-SingleDeviceSerial {
    param([Parameter(Mandatory = $true)][string]$Adb)
    $r = Invoke-NativeCapture -FilePath $Adb -Arguments @('devices')
    if ($r.ExitCode -ne 0) { throw ('FNX_PLAY_SCREENSHOT_02_V5_ADB_DEVICES_EXIT_' + $r.ExitCode) }
    $serials = @()
    foreach ($line in ($r.StdOut -split "`r?`n")) {
        if ($line -match '^([^\s]+)\s+device\s*$') { $serials += $Matches[1] }
    }
    if ($serials.Count -ne 1) { throw ('FNX_PLAY_SCREENSHOT_02_V5_DEVICE_COUNT_' + $serials.Count) }
    return [string]$serials[0]
}

function Stop-OtherUserApps {
    param(
        [Parameter(Mandatory = $true)][string]$Adb,
        [Parameter(Mandatory = $true)][string]$Serial
    )
    $list = Invoke-NativeCapture -FilePath $Adb -Arguments @('-s',$Serial,'shell','pm','list','packages','-3')
    if ($list.ExitCode -ne 0) { throw ('FNX_PLAY_SCREENSHOT_02_V5_PM_LIST_EXIT_' + $list.ExitCode) }
    $stopped = New-Object System.Collections.Generic.List[string]
    foreach ($line in ($list.StdOut -split "`r?`n")) {
        if ($line -match '^package:(\S+)\s*$') {
            $pkg = [string]$Matches[1]
            if ($pkg -ne $PackageId) {
                $stop = Invoke-NativeCapture -FilePath $Adb -Arguments @('-s',$Serial,'shell','am','force-stop',$pkg)
                if ($stop.ExitCode -ne 0) { throw ('FNX_PLAY_SCREENSHOT_02_V5_FORCE_STOP_EXIT_' + $stop.ExitCode + '_' + $pkg) }
                $stopped.Add($pkg)
            }
        }
    }
    [void](Invoke-NativeCapture -FilePath $Adb -Arguments @('-s',$Serial,'shell','input','keyevent','3'))
    [void](Invoke-NativeCapture -FilePath $Adb -Arguments @('-s',$Serial,'shell','am','broadcast','-a','android.intent.action.CLOSE_SYSTEM_DIALOGS'))
    return $stopped
}

function Assert-ScreenshotVisualStateV5 {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw 'FNX_PLAY_SCREENSHOT_02_V5_PNG_MISSING'
    }
    $fileBytes = (Get-Item -LiteralPath $Path).Length
    if ($fileBytes -lt 20000) {
        throw ('FNX_PLAY_SCREENSHOT_02_V5_PNG_TOO_SMALL_' + $fileBytes)
    }
    try { Add-Type -AssemblyName System.Drawing -ErrorAction Stop } catch { throw ('FNX_PLAY_SCREENSHOT_02_V5_SYSTEM_DRAWING_UNAVAILABLE_' + $_.Exception.Message) }
    $bitmap = $null
    try {
        $bitmap = New-Object System.Drawing.Bitmap($Path)
        if ($bitmap.Width -ne 1080 -or $bitmap.Height -ne 1920) {
            throw ('FNX_PLAY_SCREENSHOT_02_V5_DIMENSION_MISMATCH_' + $bitmap.Width + 'x' + $bitmap.Height)
        }
        $meaningful = 0
        $goldLike = 0
        $transitions = 0
        $occupied = @(0,0,0,0,0,0)
        $step = 24
        for ($y = 12; $y -lt ($bitmap.Height - 12); $y += $step) {
            $band = [Math]::Floor(($y * 6.0) / $bitmap.Height)
            if ($band -lt 0) { $band = 0 }
            if ($band -gt 5) { $band = 5 }
            for ($x = 12; $x -lt ($bitmap.Width - 12); $x += $step) {
                $c = $bitmap.GetPixel($x,$y)
                $sum = [int]$c.R + [int]$c.G + [int]$c.B
                if ($sum -ge 75) { $meaningful++; $occupied[$band]++ }
                if ([int]$c.R -ge 135 -and [int]$c.G -ge 90 -and [int]$c.B -le 155 -and [int]$c.R -gt [int]$c.B) { $goldLike++ }
                $r = $bitmap.GetPixel([Math]::Min($x + 12,$bitmap.Width - 1),$y)
                $d = [Math]::Abs([int]$c.R-[int]$r.R)+[Math]::Abs([int]$c.G-[int]$r.G)+[Math]::Abs([int]$c.B-[int]$r.B)
                if ($d -ge 42) { $transitions++ }
            }
        }
        $occupiedBands = 0
        foreach ($count in $occupied) { if ($count -ge 4) { $occupiedBands++ } }
        if ($meaningful -lt 45) { throw ('FNX_PLAY_SCREENSHOT_02_V5_LOW_VISIBLE_CONTENT_' + $meaningful) }
        if ($goldLike -lt 3) { throw ('FNX_PLAY_SCREENSHOT_02_V5_GOLD_UI_NOT_PROVEN_' + $goldLike) }
        if ($transitions -lt 15) { throw ('FNX_PLAY_SCREENSHOT_02_V5_LOW_STRUCTURAL_TRANSITIONS_' + $transitions) }
        if ($occupiedBands -lt 3) { throw ('FNX_PLAY_SCREENSHOT_02_V5_LOW_VERTICAL_OCCUPANCY_' + $occupiedBands) }
        return [pscustomobject]@{ FileBytes=$fileBytes; Meaningful=$meaningful; GoldLike=$goldLike; Transitions=$transitions; OccupiedBands=$occupiedBands }
    }
    finally { if ($null -ne $bitmap) { $bitmap.Dispose() } }
}

$source = Get-Content -LiteralPath $BasePath -Raw
$sizeNeedle = 'if ($screenshotBytes -lt 60000) {'
if (([regex]::Matches($source,[regex]::Escape($sizeNeedle))).Count -ne 1) {
    throw 'FNX_PLAY_SCREENSHOT_02_V5_SIZE_GATE_PATTERN_DRIFT'
}
$source = $source.Replace($sizeNeedle,'if ($screenshotBytes -lt 20000) {')

$waitNeedle = '    Start-Sleep -Seconds 5'
if (([regex]::Matches($source,[regex]::Escape($waitNeedle))).Count -ne 1) {
    throw 'FNX_PLAY_SCREENSHOT_02_V5_LAUNCH_WAIT_PATTERN_DRIFT'
}
$foregroundGuard = @'
    Write-Output 'SCREENSHOT_02_PHASE=PROVE_FITNEXUS_FOREGROUND'
    Start-Sleep -Seconds 2
    $foregroundConsecutive = 0
    $foregroundAttempts = 0
    $lastActivityText = ''
    $lastWindowText = ''
    while ($foregroundAttempts -lt 20 -and $foregroundConsecutive -lt 3) {
        $foregroundAttempts++
        $activityProof = Invoke-NativeCapture -FilePath $adb -Arguments @('-s',$serial,'shell','dumpsys','activity','activities')
        $windowProof = Invoke-NativeCapture -FilePath $adb -Arguments @('-s',$serial,'shell','dumpsys','window','windows')
        $lastActivityText = [string]$activityProof.StdOut
        $lastWindowText = [string]$windowProof.StdOut
        $activityOwned = ($activityProof.ExitCode -eq 0 -and $lastActivityText -match [regex]::Escape($PackageId))
        $windowOwned = ($windowProof.ExitCode -eq 0 -and $lastWindowText -match ('mCurrentFocus=.*' + [regex]::Escape($PackageId)))
        if ($activityOwned -and $windowOwned) { $foregroundConsecutive++ } else { $foregroundConsecutive = 0 }
        if ($foregroundConsecutive -lt 3) { Start-Sleep -Seconds 1 }
    }
    if ($foregroundConsecutive -lt 3) {
        throw ('FNX_PLAY_SCREENSHOT_02_CAPTURE_POINT_FOREGROUND_NOT_PROVEN_ATTEMPTS_' + $foregroundAttempts)
    }
    Write-Output ('SCREENSHOT_02_CAPTURE_POINT_FOREGROUND_PROOF=PASS_ATTEMPTS_' + $foregroundAttempts)
'@
$source = $source.Replace($waitNeedle,$foregroundGuard.TrimEnd())

$runtimePath = Join-Path $PSScriptRoot ('FITNEXUS_PLAY_STORE_SCREENSHOT_02_CAPTURE_V1.__authority_v5_' + [guid]::NewGuid().ToString('N') + '.ps1')
$encoding = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($runtimePath,$source,$encoding)

Write-Output 'SCREENSHOT_02_CAPTURE_AUTHORITY_V5=ACTIVE'

if ($ValidateOnly) {
    [void][ScriptBlock]::Create($source)
    Write-Output 'FITNEXUS_PLAY_STORE_SCREENSHOT_02_CAPTURE_AUTHORITY_V5_VALIDATE_ONLY=PASS'
    Write-Output 'CAPTURE_POINT_FOREGROUND_PROOF=REQUIRED'
    Write-Output 'ACTIVITY_AND_WINDOW_FOCUS_AUTHORITY=REQUIRED'
    Write-Output 'CONSECUTIVE_FOREGROUND_PROOFS_REQUIRED=3'
    Write-Output 'ARBITRARY_60000_BYTE_GATE=false'
    Write-Output 'REAL_USER_DATA=false'
    Write-Output 'REMOTE_MUTATION_PERFORMED=false'
    Remove-Item -LiteralPath $runtimePath -Force -ErrorAction SilentlyContinue
    exit 0
}

try {
    if ($env:OS -ne 'Windows_NT') { throw 'FNX_PLAY_SCREENSHOT_02_V5_WINDOWS_REQUIRED' }
    $adb = Resolve-AdbExecutable
    $serial = Get-SingleDeviceSerial -Adb $adb
    $stopped = Stop-OtherUserApps -Adb $adb -Serial $serial
    Write-Output ('SCREENSHOT_02_V5_OTHER_USER_APPS_FORCE_STOPPED=' + $stopped.Count)
    Write-Output 'SCREENSHOT_02_V5_CAPTURE_SESSION=QUIESCED'

    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $runtimePath
    $childExit = $LASTEXITCODE
    if ($null -eq $childExit -or $childExit -ne 0) {
        Write-Output 'FITNEXUS_PLAY_STORE_SCREENSHOT_02_CAPTURE_AUTHORITY_V5=FAIL'
        Write-Output 'CAPTURE_POINT_FOREGROUND_PROOF=FAILED_OR_CHILD_FAILED'
        Write-Output 'PRODUCTION_RELEASE_RESTORED_EXPECTED_BY_CHILD=true'
        exit 1
    }

    $documents = [Environment]::GetFolderPath('MyDocuments')
    if ([string]::IsNullOrWhiteSpace($documents)) { throw 'FNX_PLAY_SCREENSHOT_02_V5_DOCUMENTS_UNRESOLVED' }
    $screenshot = Join-Path $documents 'FitNexus_Coach_BlackGold_EXTERNAL\play_store_assets\current\screenshots\02_student_management_1080x1920.png'
    $proof = Assert-ScreenshotVisualStateV5 -Path $screenshot

    Write-Output 'FITNEXUS_PLAY_STORE_SCREENSHOT_02_CAPTURE_AUTHORITY_V5=PASS'
    Write-Output ('VISUAL_FILE_BYTES=' + $proof.FileBytes)
    Write-Output ('VISUAL_MEANINGFUL_SAMPLES=' + $proof.Meaningful)
    Write-Output ('VISUAL_BLACKGOLD_SAMPLES=' + $proof.GoldLike)
    Write-Output ('VISUAL_STRUCTURAL_TRANSITIONS=' + $proof.Transitions)
    Write-Output ('VISUAL_OCCUPIED_VERTICAL_BANDS=' + $proof.OccupiedBands)
    Write-Output 'CAPTURE_POINT_FOREGROUND_PROOF=PASS'
    Write-Output 'CROSS_PROJECT_CAPTURE_CONTAMINATION_GUARD=PASS'
    Write-Output 'HUMAN_VISUAL_REVIEW_REQUIRED=true'
    exit 0
}
catch {
    Write-Output 'FITNEXUS_PLAY_STORE_SCREENSHOT_02_CAPTURE_AUTHORITY_V5=FAIL'
    Write-Output ('FAILURE_CLASS=' + $_.Exception.Message)
    Write-Output 'REMOTE_MUTATION_PERFORMED=false'
    exit 1
}
finally {
    if (Test-Path -LiteralPath $runtimePath -PathType Leaf) {
        Remove-Item -LiteralPath $runtimePath -Force -ErrorAction SilentlyContinue
    }
}
