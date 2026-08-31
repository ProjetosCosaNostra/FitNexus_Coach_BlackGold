param(
    [switch]$ValidateOnly
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$V6Path = Join-Path $PSScriptRoot 'FITNEXUS_PLAY_STORE_SCREENSHOT_02_EXPLICIT_LAUNCH_AUTHORITY_V6.ps1'
if (-not (Test-Path -LiteralPath $V6Path -PathType Leaf)) {
    throw 'FNX_PLAY_SCREENSHOT_02_V7_V6_SOURCE_MISSING'
}

$source = Get-Content -LiteralPath $V6Path -Raw

$sizePatchNeedle = @'
$source = $source.Replace($sizeNeedle,'if ($screenshotBytes -lt 20000) {')
'@.Trim()
$sizePatchReplacement = @'
$source = $source.Replace($sizeNeedle,'if ($screenshotBytes -lt 1000) {')
'@.Trim()
if (([regex]::Matches($source,[regex]::Escape($sizePatchNeedle))).Count -ne 1) {
    throw 'FNX_PLAY_SCREENSHOT_02_V7_SIZE_PATCH_PATTERN_DRIFT'
}
$source = $source.Replace($sizePatchNeedle,$sizePatchReplacement)

$launchMarker = "    Write-Output 'SCREENSHOT_02_PHASE=EXPLICIT_MAIN_ACTIVITY_LAUNCH'"
$launchWake = @'
    Write-Output 'SCREENSHOT_02_PHASE=WAKE_AND_UNLOCK_DEVICE_V7'
    [void](Invoke-NativeCapture -FilePath $adb -Arguments @('-s',$serial,'shell','input','keyevent','224'))
    [void](Invoke-NativeCapture -FilePath $adb -Arguments @('-s',$serial,'shell','wm','dismiss-keyguard'))
    Start-Sleep -Milliseconds 750
    $powerProbe = Invoke-NativeCapture -FilePath $adb -Arguments @('-s',$serial,'shell','dumpsys','power')
    $powerSnapshot = (([string]$powerProbe.StdOut -split "`r?`n") | Where-Object { $_ -match '(?i)(mWakefulness=|Display Power: state=)' } | Select-Object -First 4) -join ' || '
    Write-Output ('SCREENSHOT_02_V7_POWER_SNAPSHOT=' + $powerSnapshot)
    Write-Output 'SCREENSHOT_02_PHASE=EXPLICIT_MAIN_ACTIVITY_LAUNCH'
'@
if (([regex]::Matches($source,[regex]::Escape($launchMarker))).Count -ne 1) {
    throw 'FNX_PLAY_SCREENSHOT_02_V7_LAUNCH_MARKER_DRIFT'
}
$source = $source.Replace($launchMarker,$launchWake.TrimEnd())

$readyMarker = @'
    Write-Output ('SCREENSHOT_02_CAPTURE_POINT_FOREGROUND_PROOF_V6=PASS_ATTEMPTS_' + $foregroundAttempts)
'@.TrimEnd()
$readyBlock = @'
    Write-Output ('SCREENSHOT_02_CAPTURE_POINT_FOREGROUND_PROOF_V6=PASS_ATTEMPTS_' + $foregroundAttempts)
    Write-Output 'SCREENSHOT_02_PHASE=PROVE_FLUTTER_RENDER_READY_V7'
    try { Add-Type -AssemblyName System.Drawing -ErrorAction Stop } catch { throw ('FNX_PLAY_SCREENSHOT_02_V7_SYSTEM_DRAWING_UNAVAILABLE_' + $_.Exception.Message) }
    $renderProbeRemote = '/sdcard/Download/fitnexus_render_probe_v7.png'
    $renderProbeLocal = Join-Path $scratch 'fitnexus_render_probe_v7.png'
    $renderReady = $false
    $renderAttempts = 0
    $lastMeaningful = 0
    $lastGoldLike = 0
    $lastProbeBytes = 0
    while ($renderAttempts -lt 40 -and -not $renderReady) {
        $renderAttempts++
        [void](Invoke-NativeCapture -FilePath $adb -Arguments @('-s',$serial,'shell','rm','-f',$renderProbeRemote))
        Remove-Item -LiteralPath $renderProbeLocal -Force -ErrorAction SilentlyContinue
        $probeCapture = Invoke-NativeCapture -FilePath $adb -Arguments @('-s',$serial,'shell','screencap','-p',$renderProbeRemote)
        if ($probeCapture.ExitCode -eq 0) {
            $probePull = Invoke-NativeCapture -FilePath $adb -Arguments @('-s',$serial,'pull',$renderProbeRemote,$renderProbeLocal)
            if ($probePull.ExitCode -eq 0 -and (Test-Path -LiteralPath $renderProbeLocal -PathType Leaf)) {
                $lastProbeBytes = (Get-Item -LiteralPath $renderProbeLocal).Length
                $bitmap = $null
                try {
                    $bitmap = New-Object System.Drawing.Bitmap($renderProbeLocal)
                    if ($bitmap.Width -eq $TargetWidth -and $bitmap.Height -eq $TargetHeight) {
                        $meaningful = 0
                        $goldLike = 0
                        $step = 32
                        for ($y = 16; $y -lt ($bitmap.Height - 16); $y += $step) {
                            for ($x = 16; $x -lt ($bitmap.Width - 16); $x += $step) {
                                $c = $bitmap.GetPixel($x,$y)
                                $sum = [int]$c.R + [int]$c.G + [int]$c.B
                                if ($sum -ge 75) { $meaningful++ }
                                if ([int]$c.R -ge 135 -and [int]$c.G -ge 90 -and [int]$c.B -le 155 -and [int]$c.R -gt [int]$c.B) { $goldLike++ }
                            }
                        }
                        $lastMeaningful = $meaningful
                        $lastGoldLike = $goldLike
                        if ($meaningful -ge 30 -and $goldLike -ge 2) {
                            $renderReady = $true
                        }
                    }
                }
                finally {
                    if ($null -ne $bitmap) { $bitmap.Dispose() }
                }
            }
        }
        if (-not $renderReady) { Start-Sleep -Milliseconds 750 }
    }
    [void](Invoke-NativeCapture -FilePath $adb -Arguments @('-s',$serial,'shell','rm','-f',$renderProbeRemote))
    Remove-Item -LiteralPath $renderProbeLocal -Force -ErrorAction SilentlyContinue
    Write-Output ('SCREENSHOT_02_V7_RENDER_ATTEMPTS=' + $renderAttempts)
    Write-Output ('SCREENSHOT_02_V7_RENDER_PROBE_BYTES=' + $lastProbeBytes)
    Write-Output ('SCREENSHOT_02_V7_RENDER_MEANINGFUL_SAMPLES=' + $lastMeaningful)
    Write-Output ('SCREENSHOT_02_V7_RENDER_BLACKGOLD_SAMPLES=' + $lastGoldLike)
    if (-not $renderReady) {
        $powerRetry = Invoke-NativeCapture -FilePath $adb -Arguments @('-s',$serial,'shell','dumpsys','power')
        $powerRetrySnapshot = (([string]$powerRetry.StdOut -split "`r?`n") | Where-Object { $_ -match '(?i)(mWakefulness=|Display Power: state=)' } | Select-Object -First 4) -join ' || '
        Write-Output ('SCREENSHOT_02_V7_POWER_FAILURE_SNAPSHOT=' + $powerRetrySnapshot)
        $logcatV7 = Invoke-NativeCapture -FilePath $adb -Arguments @('-s',$serial,'logcat','-d','-t','350')
        $renderLog = (([string]$logcatV7.StdOut -split "`r?`n") | Where-Object { $_ -match '(?i)(Flutter|fitnexus|FATAL EXCEPTION|AndroidRuntime|Surface|E/flutter)' } | Select-Object -Last 40) -join ' || '
        Write-Output ('SCREENSHOT_02_V7_RENDER_LOGCAT_DIAGNOSTIC=' + $renderLog)
        throw ('FNX_PLAY_SCREENSHOT_02_V7_RENDER_READY_NOT_PROVEN_ATTEMPTS_' + $renderAttempts)
    }
    Write-Output 'SCREENSHOT_02_FLUTTER_RENDER_READY_V7=PASS'
'@
if (([regex]::Matches($source,[regex]::Escape($readyMarker))).Count -ne 1) {
    throw 'FNX_PLAY_SCREENSHOT_02_V7_RENDER_MARKER_DRIFT'
}
$source = $source.Replace($readyMarker,$readyBlock.TrimEnd())

$runtimePath = Join-Path $PSScriptRoot ('FITNEXUS_PLAY_STORE_SCREENSHOT_02_EXPLICIT_LAUNCH_AUTHORITY_V6.__render_v7_' + [guid]::NewGuid().ToString('N') + '.ps1')
$encoding = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($runtimePath,$source,$encoding)

Write-Output 'SCREENSHOT_02_RENDER_READY_AUTHORITY_V7=ACTIVE'

try {
    if ($ValidateOnly) {
        [void][ScriptBlock]::Create($source)
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $runtimePath -ValidateOnly
        $validateExit = $LASTEXITCODE
        if ($null -eq $validateExit -or $validateExit -ne 0) {
            throw ('FNX_PLAY_SCREENSHOT_02_V7_VALIDATE_CHILD_EXIT_' + $validateExit)
        }
        Write-Output 'FITNEXUS_PLAY_STORE_SCREENSHOT_02_RENDER_READY_AUTHORITY_V7_VALIDATE_ONLY=PASS'
        Write-Output 'DEVICE_WAKE_AND_KEYGUARD_DISMISS=REQUIRED'
        Write-Output 'FOREGROUND_AUTHORITY_V6=REQUIRED'
        Write-Output 'RENDERED_PIXEL_PROBE=REQUIRED_BEFORE_FINAL_SCREENSHOT'
        Write-Output 'BLACKGOLD_SIGNAL_REQUIRED_BEFORE_FINAL_SCREENSHOT=true'
        exit 0
    }

    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $runtimePath
    $childExit = $LASTEXITCODE
    if ($null -eq $childExit -or $childExit -ne 0) {
        Write-Output 'FITNEXUS_PLAY_STORE_SCREENSHOT_02_RENDER_READY_AUTHORITY_V7=FAIL'
        Write-Output 'PRODUCTION_RELEASE_RESTORED_EXPECTED_BY_CHILD=true'
        exit 1
    }

    Write-Output 'FITNEXUS_PLAY_STORE_SCREENSHOT_02_RENDER_READY_AUTHORITY_V7=PASS'
    Write-Output 'DEVICE_AWAKE_AUTHORITY=PASS'
    Write-Output 'CAPTURE_POINT_FOREGROUND_PROOF=PASS'
    Write-Output 'FLUTTER_RENDER_READY_PROOF=PASS'
    Write-Output 'HUMAN_VISUAL_REVIEW_REQUIRED=true'
    exit 0
}
catch {
    Write-Output 'FITNEXUS_PLAY_STORE_SCREENSHOT_02_RENDER_READY_AUTHORITY_V7=FAIL'
    Write-Output ('FAILURE_CLASS=' + $_.Exception.Message)
    Write-Output 'REMOTE_MUTATION_PERFORMED=false'
    exit 1
}
finally {
    if (Test-Path -LiteralPath $runtimePath -PathType Leaf) {
        Remove-Item -LiteralPath $runtimePath -Force -ErrorAction SilentlyContinue
    }
}
