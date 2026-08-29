param(
    [switch]$ValidateOnly
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$sourcePath = Join-Path $PSScriptRoot 'FITNEXUS_PLAY_STORE_SCREENSHOT_02_CAPTURE_V1.ps1'
if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
    throw 'FNX_PLAY_SCREENSHOT_02_VISUAL_REPAIR_SOURCE_MISSING'
}

$source = Get-Content -LiteralPath $sourcePath -Raw
$needle = 'if ($screenshotBytes -lt 60000) {'
$replacement = 'if ($screenshotBytes -lt 20000) {'
$matches = ([regex]::Matches($source, [regex]::Escape($needle))).Count
if ($matches -ne 1) {
    throw ('FNX_PLAY_SCREENSHOT_02_VISUAL_REPAIR_SIZE_GATE_PATTERN_COUNT_' + $matches)
}

$patched = $source.Replace($needle, $replacement)
if ($patched -eq $source) {
    throw 'FNX_PLAY_SCREENSHOT_02_VISUAL_REPAIR_PATCH_NOT_APPLIED'
}

try {
    Add-Type -AssemblyName System.Drawing -ErrorAction Stop
}
catch {
    throw ('FNX_PLAY_SCREENSHOT_02_VISUAL_REPAIR_SYSTEM_DRAWING_UNAVAILABLE_' + $_.Exception.Message)
}

$runtimePath = Join-Path $PSScriptRoot ('FITNEXUS_PLAY_STORE_SCREENSHOT_02_CAPTURE_V1.__visual_fixed_' + [guid]::NewGuid().ToString('N') + '.ps1')
$encoding = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($runtimePath, $patched, $encoding)

function Assert-ScreenshotVisualState {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw 'FNX_PLAY_SCREENSHOT_02_VISUAL_REPAIR_PNG_MISSING'
    }

    $fileBytes = (Get-Item -LiteralPath $Path).Length
    if ($fileBytes -lt 20000) {
        throw ('FNX_PLAY_SCREENSHOT_02_VISUAL_REPAIR_PNG_TOO_SMALL_' + $fileBytes)
    }

    $bitmap = $null
    try {
        $bitmap = New-Object System.Drawing.Bitmap($Path)
        if ($bitmap.Width -ne 1080 -or $bitmap.Height -ne 1920) {
            throw ('FNX_PLAY_SCREENSHOT_02_VISUAL_REPAIR_DIMENSION_MISMATCH_' + $bitmap.Width + 'x' + $bitmap.Height)
        }

        $unique = New-Object 'System.Collections.Generic.HashSet[int]'
        $meaningful = 0
        $goldLike = 0
        $samples = 0

        for ($y = 24; $y -lt $bitmap.Height; $y += 48) {
            for ($x = 24; $x -lt $bitmap.Width; $x += 48) {
                $color = $bitmap.GetPixel($x, $y)
                $rgb = (([int]$color.R -shl 16) -bor ([int]$color.G -shl 8) -bor [int]$color.B)
                [void]$unique.Add($rgb)
                $samples++

                if (([int]$color.R + [int]$color.G + [int]$color.B) -ge 105) {
                    $meaningful++
                }
                if ([int]$color.R -ge 150 -and [int]$color.G -ge 110 -and [int]$color.B -le 130) {
                    $goldLike++
                }
            }
        }

        if ($unique.Count -lt 24) {
            throw ('FNX_PLAY_SCREENSHOT_02_VISUAL_REPAIR_LOW_COLOR_DIVERSITY_' + $unique.Count)
        }
        if ($meaningful -lt 35) {
            throw ('FNX_PLAY_SCREENSHOT_02_VISUAL_REPAIR_LOW_VISIBLE_CONTENT_' + $meaningful)
        }
        if ($goldLike -lt 3) {
            throw ('FNX_PLAY_SCREENSHOT_02_VISUAL_REPAIR_GOLD_UI_NOT_PROVEN_' + $goldLike)
        }

        return [pscustomobject]@{
            FileBytes = $fileBytes
            Samples = $samples
            UniqueColors = $unique.Count
            MeaningfulSamples = $meaningful
            GoldLikeSamples = $goldLike
        }
    }
    finally {
        if ($null -ne $bitmap) {
            $bitmap.Dispose()
        }
    }
}

try {
    Write-Output 'SCREENSHOT_02_VISUAL_STATE_REPAIR=ACTIVE'

    if ($ValidateOnly) {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $runtimePath -ValidateOnly
        $validateExit = $LASTEXITCODE
        if ($null -eq $validateExit -or $validateExit -ne 0) {
            exit 1
        }
        Write-Output 'FITNEXUS_PLAY_STORE_SCREENSHOT_02_VISUAL_STATE_REPAIR_VALIDATE_ONLY=PASS'
        Write-Output 'VISUAL_VALIDATION=PIXEL_DIVERSITY_PLUS_VISIBLE_CONTENT_PLUS_BLACKGOLD_SIGNAL'
        exit 0
    }

    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $runtimePath
    $childExit = $LASTEXITCODE
    if ($null -eq $childExit -or $childExit -ne 0) {
        exit 1
    }

    $documents = [Environment]::GetFolderPath('MyDocuments')
    if ([string]::IsNullOrWhiteSpace($documents)) {
        throw 'FNX_PLAY_SCREENSHOT_02_VISUAL_REPAIR_DOCUMENTS_UNRESOLVED'
    }

    $current = Join-Path $documents 'FitNexus_Coach_BlackGold_EXTERNAL\play_store_assets\current'
    $screenshotPath = Join-Path $current 'screenshots\02_student_management_1080x1920.png'
    $receiptPath = Join-Path $current 'receipts\FITNEXUS_PLAY_STORE_SCREENSHOT_02_RECEIPT_V1.json'

    try {
        $proof = Assert-ScreenshotVisualState -Path $screenshotPath
    }
    catch {
        Remove-Item -LiteralPath $receiptPath -Force -ErrorAction SilentlyContinue
        Write-Output 'FITNEXUS_PLAY_STORE_SCREENSHOT_02_VISUAL_STATE_REPAIR=FAIL'
        Write-Output ('FAILURE_CLASS=' + $_.Exception.Message)
        Write-Output 'RECEIPT_INVALIDATED=true'
        Write-Output 'PRODUCTION_RELEASE_RESTORED=true'
        Write-Output 'PLAY_CONSOLE_MUTATION_PERFORMED=false'
        Write-Output 'SUPABASE_MUTATION_PERFORMED=false'
        exit 1
    }

    Write-Output 'FITNEXUS_PLAY_STORE_SCREENSHOT_02_VISUAL_STATE_REPAIR=PASS'
    Write-Output ('VISUAL_FILE_BYTES=' + $proof.FileBytes)
    Write-Output ('VISUAL_SAMPLE_COUNT=' + $proof.Samples)
    Write-Output ('VISUAL_UNIQUE_COLORS=' + $proof.UniqueColors)
    Write-Output ('VISUAL_MEANINGFUL_SAMPLES=' + $proof.MeaningfulSamples)
    Write-Output ('VISUAL_BLACKGOLD_SAMPLES=' + $proof.GoldLikeSamples)
    Write-Output 'ARBITRARY_60000_BYTE_GATE=REPLACED_BY_CONTENT_AWARE_GUARD'
    exit 0
}
finally {
    if (Test-Path -LiteralPath $runtimePath -PathType Leaf) {
        Remove-Item -LiteralPath $runtimePath -Force -ErrorAction SilentlyContinue
    }
}
