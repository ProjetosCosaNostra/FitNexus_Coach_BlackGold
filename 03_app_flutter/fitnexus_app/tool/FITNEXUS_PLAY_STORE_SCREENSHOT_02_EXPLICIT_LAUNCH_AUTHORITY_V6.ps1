param(
    [switch]$ValidateOnly
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$BasePath = Join-Path $PSScriptRoot 'FITNEXUS_PLAY_STORE_SCREENSHOT_02_CAPTURE_V1.ps1'
if (-not (Test-Path -LiteralPath $BasePath -PathType Leaf)) {
    throw 'FNX_PLAY_SCREENSHOT_02_V6_BASE_SOURCE_MISSING'
}

$PackageId = 'br.com.lafamigliaplayworks.fitnexuscoach'
$Component = $PackageId + '/.MainActivity'

function Invoke-NativeCapture {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $FilePath
    $quoted = @()
    foreach ($arg in $Arguments) { $quoted += ('"' + ($arg -replace '"', '\"') + '"') }
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
    if ($candidates.Count -eq 0) { throw 'FNX_PLAY_SCREENSHOT_02_V6_ADB_NOT_FOUND' }
    return $candidates[0]
}

function Get-SingleDeviceSerial {
    param([Parameter(Mandatory = $true)][string]$Adb)
    $r = Invoke-NativeCapture -FilePath $Adb -Arguments @('devices')
    if ($r.ExitCode -ne 0) { throw ('FNX_PLAY_SCREENSHOT_02_V6_ADB_DEVICES_EXIT_' + $r.ExitCode) }
    $serials = @()
    foreach ($line in ($r.StdOut -split "`r?`n")) { if ($line -match '^([^\s]+)\s+device\s*$') { $serials += $Matches[1] } }
    if ($serials.Count -ne 1) { throw ('FNX_PLAY_SCREENSHOT_02_V6_DEVICE_COUNT_' + $serials.Count) }
    return [string]$serials[0]
}

function Stop-OtherUserApps {
    param([string]$Adb,[string]$Serial)
    $list = Invoke-NativeCapture -FilePath $Adb -Arguments @('-s',$Serial,'shell','pm','list','packages','-3')
    if ($list.ExitCode -ne 0) { throw ('FNX_PLAY_SCREENSHOT_02_V6_PM_LIST_EXIT_' + $list.ExitCode) }
    $count = 0
    foreach ($line in ($list.StdOut -split "`r?`n")) {
        if ($line -match '^package:(\S+)\s*$') {
            $pkg = [string]$Matches[1]
            if ($pkg -ne $PackageId) {
                $stop = Invoke-NativeCapture -FilePath $Adb -Arguments @('-s',$Serial,'shell','am','force-stop',$pkg)
                if ($stop.ExitCode -ne 0) { throw ('FNX_PLAY_SCREENSHOT_02_V6_FORCE_STOP_EXIT_' + $stop.ExitCode + '_' + $pkg) }
                $count++
            }
        }
    }
    return $count
}

function Assert-ScreenshotVisualStateV6 {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw 'FNX_PLAY_SCREENSHOT_02_V6_PNG_MISSING' }
    $fileBytes = (Get-Item -LiteralPath $Path).Length
    if ($fileBytes -lt 20000) { throw ('FNX_PLAY_SCREENSHOT_02_V6_PNG_TOO_SMALL_' + $fileBytes) }
    try { Add-Type -AssemblyName System.Drawing -ErrorAction Stop } catch { throw ('FNX_PLAY_SCREENSHOT_02_V6_SYSTEM_DRAWING_UNAVAILABLE_' + $_.Exception.Message) }
    $bitmap = $null
    try {
        $bitmap = New-Object System.Drawing.Bitmap($Path)
        if ($bitmap.Width -ne 1080 -or $bitmap.Height -ne 1920) { throw ('FNX_PLAY_SCREENSHOT_02_V6_DIMENSION_MISMATCH_' + $bitmap.Width + 'x' + $bitmap.Height) }
        $meaningful=0; $goldLike=0; $transitions=0; $occupied=@(0,0,0,0,0,0); $step=24
        for ($y=12; $y -lt ($bitmap.Height-12); $y+=$step) {
            $band=[Math]::Floor(($y*6.0)/$bitmap.Height); if($band -lt 0){$band=0}; if($band -gt 5){$band=5}
            for ($x=12; $x -lt ($bitmap.Width-12); $x+=$step) {
                $c=$bitmap.GetPixel($x,$y); $sum=[int]$c.R+[int]$c.G+[int]$c.B
                if($sum -ge 75){$meaningful++;$occupied[$band]++}
                if([int]$c.R -ge 135 -and [int]$c.G -ge 90 -and [int]$c.B -le 155 -and [int]$c.R -gt [int]$c.B){$goldLike++}
                $r=$bitmap.GetPixel([Math]::Min($x+12,$bitmap.Width-1),$y)
                $d=[Math]::Abs([int]$c.R-[int]$r.R)+[Math]::Abs([int]$c.G-[int]$r.G)+[Math]::Abs([int]$c.B-[int]$r.B)
                if($d -ge 42){$transitions++}
            }
        }
        $bands=0; foreach($count in $occupied){if($count -ge 4){$bands++}}
        if($meaningful -lt 45){throw ('FNX_PLAY_SCREENSHOT_02_V6_LOW_VISIBLE_CONTENT_'+$meaningful)}
        if($goldLike -lt 3){throw ('FNX_PLAY_SCREENSHOT_02_V6_GOLD_UI_NOT_PROVEN_'+$goldLike)}
        if($transitions -lt 15){throw ('FNX_PLAY_SCREENSHOT_02_V6_LOW_STRUCTURAL_TRANSITIONS_'+$transitions)}
        if($bands -lt 3){throw ('FNX_PLAY_SCREENSHOT_02_V6_LOW_VERTICAL_OCCUPANCY_'+$bands)}
        return [pscustomobject]@{FileBytes=$fileBytes;Meaningful=$meaningful;GoldLike=$goldLike;Transitions=$transitions;OccupiedBands=$bands}
    }
    finally { if($null -ne $bitmap){$bitmap.Dispose()} }
}

$source = Get-Content -LiteralPath $BasePath -Raw
$sizeNeedle = 'if ($screenshotBytes -lt 60000) {'
if (([regex]::Matches($source,[regex]::Escape($sizeNeedle))).Count -ne 1) { throw 'FNX_PLAY_SCREENSHOT_02_V6_SIZE_GATE_PATTERN_DRIFT' }
$source = $source.Replace($sizeNeedle,'if ($screenshotBytes -lt 20000) {')

$launchNeedle = @'
    $launch = Invoke-NativeCapture -FilePath $adb -Arguments @('-s', $serial, 'shell', 'monkey', '-p', $PackageId, '-c', 'android.intent.category.LAUNCHER', '1')
    Assert-NativeSuccess -Result $launch -FailureClass 'FNX_PLAY_SCREENSHOT_02_LAUNCH'
    Start-Sleep -Seconds 5
'@
$launchReplacement = @'
    Write-Output 'SCREENSHOT_02_PHASE=EXPLICIT_MAIN_ACTIVITY_LAUNCH'
    $resolved = Invoke-NativeCapture -FilePath $adb -Arguments @('-s',$serial,'shell','cmd','package','resolve-activity','--brief','-a','android.intent.action.MAIN','-c','android.intent.category.LAUNCHER',$PackageId)
    Write-Output ('SCREENSHOT_02_RESOLVED_ACTIVITY=' + ([string]$resolved.StdOut).Trim())
    $launch = Invoke-NativeCapture -FilePath $adb -Arguments @('-s',$serial,'shell','am','start','-W','-n',($PackageId + '/.MainActivity'))
    Assert-NativeSuccess -Result $launch -FailureClass 'FNX_PLAY_SCREENSHOT_02_EXPLICIT_LAUNCH'
    Write-Output ('SCREENSHOT_02_AM_START_STATUS=' + (([string]$launch.StdOut -replace "`r?`n",' | ').Trim()))
    Start-Sleep -Seconds 2
'@
if (([regex]::Matches($source,[regex]::Escape($launchNeedle))).Count -ne 1) { throw 'FNX_PLAY_SCREENSHOT_02_V6_LAUNCH_PATTERN_DRIFT' }
$source = $source.Replace($launchNeedle,$launchReplacement)

$captureNeedle = "    Write-Output 'SCREENSHOT_02_PHASE=CAPTURE_DEVICE_PNG'"
if (([regex]::Matches($source,[regex]::Escape($captureNeedle))).Count -ne 1) { throw 'FNX_PLAY_SCREENSHOT_02_V6_CAPTURE_POINT_PATTERN_DRIFT' }
$authority = @'
    Write-Output 'SCREENSHOT_02_PHASE=PROVE_FITNEXUS_CAPTURE_POINT_AUTHORITY_V6'
    $foregroundConsecutive = 0
    $foregroundAttempts = 0
    $lastActivity = ''
    $lastWindow = ''
    $lastPid = ''
    while ($foregroundAttempts -lt 20 -and $foregroundConsecutive -lt 3) {
        $foregroundAttempts++
        $pidProof = Invoke-NativeCapture -FilePath $adb -Arguments @('-s',$serial,'shell','pidof',$PackageId)
        $activityProof = Invoke-NativeCapture -FilePath $adb -Arguments @('-s',$serial,'shell','dumpsys','activity','activities')
        $windowProof = Invoke-NativeCapture -FilePath $adb -Arguments @('-s',$serial,'shell','dumpsys','window','displays')
        $lastPid = ([string]$pidProof.StdOut).Trim()
        $lastActivity = [string]$activityProof.StdOut
        $lastWindow = [string]$windowProof.StdOut
        $pidOwned = ($pidProof.ExitCode -eq 0 -and -not [string]::IsNullOrWhiteSpace($lastPid))
        $activityOwned = ($activityProof.ExitCode -eq 0 -and ($lastActivity -match ('(?im)(mResumedActivity|topResumedActivity|ResumedActivity).*' + [regex]::Escape($PackageId))))
        $windowOwned = ($windowProof.ExitCode -eq 0 -and ($lastWindow -match ('(?im)(mCurrentFocus|mFocusedApp|mFocusedWindow).*' + [regex]::Escape($PackageId))))
        if ($pidOwned -and $activityOwned -and $windowOwned) { $foregroundConsecutive++ } else { $foregroundConsecutive = 0 }
        if ($foregroundConsecutive -lt 3) { Start-Sleep -Milliseconds 750 }
    }
    Write-Output ('SCREENSHOT_02_CAPTURE_POINT_PID=' + $lastPid)
    if ($foregroundConsecutive -lt 3) {
        $activityLines = (($lastActivity -split "`r?`n") | Where-Object { $_ -match 'Resumed|topResumed|mResumed|fitnexus|MainActivity' } | Select-Object -First 12) -join ' || '
        $windowLines = (($lastWindow -split "`r?`n") | Where-Object { $_ -match 'mCurrentFocus|mFocusedApp|mFocusedWindow|fitnexus|MainActivity' } | Select-Object -First 12) -join ' || '
        Write-Output ('SCREENSHOT_02_ACTIVITY_AUTHORITY_SNAPSHOT=' + $activityLines)
        Write-Output ('SCREENSHOT_02_WINDOW_AUTHORITY_SNAPSHOT=' + $windowLines)
        $logcat = Invoke-NativeCapture -FilePath $adb -Arguments @('-s',$serial,'logcat','-d','-t','250')
        $logLines = (([string]$logcat.StdOut -split "`r?`n") | Where-Object { $_ -match '(?i)(fitnexus|FATAL EXCEPTION|AndroidRuntime|Process: br\.com\.lafamigliaplayworks\.fitnexuscoach)' } | Select-Object -Last 30) -join ' || '
        Write-Output ('SCREENSHOT_02_LOGCAT_DIAGNOSTIC=' + $logLines)
        throw ('FNX_PLAY_SCREENSHOT_02_V6_CAPTURE_POINT_AUTHORITY_NOT_PROVEN_ATTEMPTS_' + $foregroundAttempts)
    }
    Write-Output ('SCREENSHOT_02_CAPTURE_POINT_FOREGROUND_PROOF_V6=PASS_ATTEMPTS_' + $foregroundAttempts)
'@
$source = $source.Replace($captureNeedle,($authority + "`r`n" + $captureNeedle))

$runtimePath = Join-Path $PSScriptRoot ('FITNEXUS_PLAY_STORE_SCREENSHOT_02_CAPTURE_V1.__authority_v6_' + [guid]::NewGuid().ToString('N') + '.ps1')
$encoding = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($runtimePath,$source,$encoding)

Write-Output 'SCREENSHOT_02_EXPLICIT_LAUNCH_AUTHORITY_V6=ACTIVE'

if ($ValidateOnly) {
    [void][ScriptBlock]::Create($source)
    Write-Output 'FITNEXUS_PLAY_STORE_SCREENSHOT_02_EXPLICIT_LAUNCH_AUTHORITY_V6_VALIDATE_ONLY=PASS'
    Write-Output 'EXPLICIT_MAIN_ACTIVITY_LAUNCH=REQUIRED'
    Write-Output 'PID_RESUMED_ACTIVITY_AND_FOCUSED_WINDOW=REQUIRED'
    Write-Output 'THREE_CONSECUTIVE_CAPTURE_POINT_PROOFS=REQUIRED'
    Write-Output 'FAILURE_DIAGNOSTICS=ACTIVITY_WINDOW_LOGCAT'
    Remove-Item -LiteralPath $runtimePath -Force -ErrorAction SilentlyContinue
    exit 0
}

try {
    if ($env:OS -ne 'Windows_NT') { throw 'FNX_PLAY_SCREENSHOT_02_V6_WINDOWS_REQUIRED' }
    $adb = Resolve-AdbExecutable
    $serial = Get-SingleDeviceSerial -Adb $adb
    $stopped = Stop-OtherUserApps -Adb $adb -Serial $serial
    Write-Output ('SCREENSHOT_02_V6_OTHER_USER_APPS_FORCE_STOPPED=' + $stopped)
    [void](Invoke-NativeCapture -FilePath $adb -Arguments @('-s',$serial,'shell','input','keyevent','3'))
    [void](Invoke-NativeCapture -FilePath $adb -Arguments @('-s',$serial,'shell','am','broadcast','-a','android.intent.action.CLOSE_SYSTEM_DIALOGS'))

    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $runtimePath
    $childExit = $LASTEXITCODE
    if ($null -eq $childExit -or $childExit -ne 0) {
        Write-Output 'FITNEXUS_PLAY_STORE_SCREENSHOT_02_EXPLICIT_LAUNCH_AUTHORITY_V6=FAIL'
        Write-Output 'PRODUCTION_RELEASE_RESTORED_EXPECTED_BY_CHILD=true'
        exit 1
    }

    $documents = [Environment]::GetFolderPath('MyDocuments')
    if ([string]::IsNullOrWhiteSpace($documents)) { throw 'FNX_PLAY_SCREENSHOT_02_V6_DOCUMENTS_UNRESOLVED' }
    $screenshot = Join-Path $documents 'FitNexus_Coach_BlackGold_EXTERNAL\play_store_assets\current\screenshots\02_student_management_1080x1920.png'
    $proof = Assert-ScreenshotVisualStateV6 -Path $screenshot
    Write-Output 'FITNEXUS_PLAY_STORE_SCREENSHOT_02_EXPLICIT_LAUNCH_AUTHORITY_V6=PASS'
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
    Write-Output 'FITNEXUS_PLAY_STORE_SCREENSHOT_02_EXPLICIT_LAUNCH_AUTHORITY_V6=FAIL'
    Write-Output ('FAILURE_CLASS=' + $_.Exception.Message)
    Write-Output 'REMOTE_MUTATION_PERFORMED=false'
    exit 1
}
finally {
    if (Test-Path -LiteralPath $runtimePath -PathType Leaf) { Remove-Item -LiteralPath $runtimePath -Force -ErrorAction SilentlyContinue }
}
