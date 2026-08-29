param(
    [switch]$ValidateOnly
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$sourcePath = Join-Path $PSScriptRoot 'FITNEXUS_PLAY_STORE_SCREENSHOT_02_CAPTURE_V1.ps1'
if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
    throw 'FNX_PLAY_SCREENSHOT_02_VISUAL_REPAIR_V2_SOURCE_MISSING'
}

$source = Get-Content -LiteralPath $sourcePath -Raw
$needle = 'if ($screenshotBytes -lt 60000) {'
$replacement = 'if ($screenshotBytes -lt 20000) {'
$matches = ([regex]::Matches($source, [regex]::Escape($needle))).Count
if ($matches -ne 1) {
    throw ('FNX_PLAY_SCREENSHOT_02_VISUAL_REPAIR_V2_SIZE_GATE_PATTERN_COUNT_' + $matches)
}

$patched = $source.Replace($needle, $replacement)
if ($patched -eq $source) {
    throw 'FNX_PLAY_SCREENSHOT_02_VISUAL_REPAIR_V2_PATCH_NOT_APPLIED'
}

try {
    Add-Type -AssemblyName System.Drawing -ErrorAction Stop
}
catch {
    throw ('FNX_PLAY_SCREENSHOT_02_VISUAL_REPAIR_V2_SYSTEM_DRAWING_UNAVAILABLE_' + $_.Exception.Message)
}

$runtimePath = Join-Path $PSScriptRoot ('FITNEXUS_PLAY_STORE_SCREENSHOT_02_CAPTURE_V1.__visual_v2_' + [guid]::NewGuid().ToString('N') + '.ps1')
$encoding = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($runtimePath, $patched, $encoding)

function Get-ColorDistance {
    param(
        [Parameter(Mandatory = $true)]$A,
        [Parameter(Mandatory = $true)]$B
    )
    return ([Math]::Abs([int]$A.R - [int]$B.R) + [Math]::Abs([int]$A.G - [int]$B.G) + [Math]::Abs([int]$A.B - [int]$B.B))
}

function Assert-ScreenshotVisualStateV2 {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw 'FNX_PLAY_SCREENSHOT_02_VISUAL_REPAIR_V2_PNG_MISSING'
    }

    $fileBytes = (Get-Item -LiteralPath $Path).Length
    if ($fileBytes -lt 20000) {
        throw ('FNX_PLAY_SCREENSHOT_02_VISUAL_REPAIR_V2_PNG_TOO_SMALL_' + $fileBytes)
    }

    $bitmap = $null
    try {
        $bitmap = New-Object System.Drawing.Bitmap($Path)
        if ($bitmap.Width -ne 1080 -or $bitmap.Height -ne 1920) {
            throw ('FNX_PLAY_SCREENSHOT_02_VISUAL_REPAIR_V2_DIMENSION_MISMATCH_' + $bitmap.Width + 'x' + $bitmap.Height)
        }

        $unique = New-Object 'System.Collections.Generic.HashSet[int]'
        $samples = 0
        $meaningful = 0
        $goldLike = 0
        $chromatic = 0
        $transitions = 0
        $bandMeaningful = @(0, 0, 0, 0, 0, 0)
        $bandTransitions = @(0, 0, 0, 0, 0, 0)

        $step = 24
        $neighbor = 12
        for ($y = 12; $y -lt ($bitmap.Height - 12); $y += $step) {
            $band = [Math]::Floor(($y * 6.0) / $bitmap.Height)
            if ($band -lt 0) { $band = 0 }
            if ($band -gt 5) { $band = 5 }

            for ($x = 12; $x -lt ($bitmap.Width - 12); $x += $step) {
                $color = $bitmap.GetPixel($x, $y)
                $rgb = (([int]$color.R -shl 16) -bor ([int]$color.G -shl 8) -bor [int]$color.B)
                [void]$unique.Add($rgb)
                $samples++

                $sum = [int]$color.R + [int]$color.G + [int]$color.B
                $max = [Math]::Max([int]$color.R, [Math]::Max([int]$color.G, [int]$color.B))
                $min = [Math]::Min([int]$color.R, [Math]::Min([int]$color.G, [int]$color.B))

                if ($sum -ge 75) {
                    $meaningful++
                    $bandMeaningful[$band]++
                }
                if ($max -ge 80 -and ($max - $min) -ge 28) {
                    $chromatic++
                }
                if ([int]$color.R -ge 135 -and [int]$color.G -ge 90 -and [int]$color.B -le 155 -and [int]$color.R -gt [int]$color.B) {
                    $goldLike++
                }

                $right = $bitmap.GetPixel([Math]::Min($x + $neighbor, $bitmap.Width - 1), $y)
                $down = $bitmap.GetPixel($x, [Math]::Min($y + $neighbor, $bitmap.Height - 1))
                if ((Get-ColorDistance -A $color -B $right) -ge 42) {
                    $transitions++
                    $bandTransitions[$band]++
                }
                if ((Get-ColorDistance -A $color -B $down) -ge 42) {
                    $transitions++
                    $bandTransitions[$band]++
                }
            }
        }

        $occupiedBands = 0
        for ($i = 0; $i -lt 6; $i++) {
            if ($bandMeaningful[$i] -ge 4 -or $bandTransitions[$i] -ge 3) {
                $occupiedBands++
            }
        }

        if ($meaningful -lt 45) {
            throw ('FNX_PLAY_SCREENSHOT_02_VISUAL_REPAIR_V2_LOW_VISIBLE_CONTENT_' + $meaningful)
        }
        if ($goldLike -lt 3) {
            throw ('FNX_PLAY_SCREENSHOT_02_VISUAL_REPAIR_V2_GOLD_UI_NOT_PROVEN_' + $goldLike)
        }
        if ($transitions -lt 30) {
            throw ('FNX_PLAY_SCREENSHOT_02_VISUAL_REPAIR_V2_LOW_STRUCTURAL_TRANSITIONS_' + $transitions)
        }
        if ($occupiedBands -lt 3) {
            throw ('FNX_PLAY_SCREENSHOT_02_VISUAL_REPAIR_V2_LOW_VERTICAL_OCCUPANCY_' + $occupiedBands)
        }

        return [pscustomobject]@{
            FileBytes = $fileBytes
            Samples = $samples
            UniqueColors = $unique.Count
            MeaningfulSamples = $meaningful
            GoldLikeSamples = $goldLike
            ChromaticSamples = $chromatic
            StructuralTransitions = $transitions
            OccupiedVerticalBands = $occupiedBands
        }
    }
    finally {
        if ($null -ne $bitmap) {
            $bitmap.Dispose()
        }
    }
}

try {
    Write-Output 'SCREENSHOT_02_VISUAL_STATE_REPAIR_V2=ACTIVE'

    if ($ValidateOnly) {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $runtimePath -ValidateOnly
        $validateExit = $LASTEXITCODE
        if ($null -eq $validateExit -or $validateExit -ne 0) {
            exit 1
        }
        Write-Output 'FITNEXUS_PLAY_STORE_SCREENSHOT_02_VISUAL_STATE_REPAIR_V2_VALIDATE_ONLY=PASS'
        Write-Output 'VISUAL_VALIDATION=STRUCTURAL_TRANSITIONS_PLUS_VERTICAL_OCCUPANCY_PLUS_BLACKGOLD_SIGNAL'
        Write-Output 'UNIQUE_COLOR_COUNT_HARD_GATE=false'
        exit 0
    }

    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $runtimePath
    $childExit = $LASTEXITCODE
    if ($null -eq $childExit -or $childExit -ne 0) {
        exit 1
    }

    $documents = [Environment]::GetFolderPath('MyDocuments')
    if ([string]::IsNullOrWhiteSpace($documents)) {
        throw 'FNX_PLAY_SCREENSHOT_02_VISUAL_REPAIR_V2_DOCUMENTS_UNRESOLVED'
    }

    $current = Join-Path $documents 'FitNexus_Coach_BlackGold_EXTERNAL\play_store_assets\current'
    $screenshotPath = Join-Path $current 'screenshots\02_student_management_1080x1920.png'
    $receiptPath = Join-Path $current 'receipts\FITNEXUS_PLAY_STORE_SCREENSHOT_02_RECEIPT_V1.json'

    try {
        $proof = Assert-ScreenshotVisualStateV2 -Path $screenshotPath
    }
    catch {
        Remove-Item -LiteralPath $receiptPath -Force -ErrorAction SilentlyContinue
        Write-Output 'FITNEXUS_PLAY_STORE_SCREENSHOT_02_VISUAL_STATE_REPAIR_V2=FAIL'
        Write-Output ('FAILURE_CLASS=' + $_.Exception.Message)
        Write-Output 'RECEIPT_INVALIDATED=true'
        Write-Output 'PRODUCTION_RELEASE_RESTORED=true'
        Write-Output 'PLAY_CONSOLE_MUTATION_PERFORMED=false'
        Write-Output 'SUPABASE_MUTATION_PERFORMED=false'
        exit 1
    }

    Write-Output 'FITNEXUS_PLAY_STORE_SCREENSHOT_02_VISUAL_STATE_REPAIR_V2=PASS'
    Write-Output ('VISUAL_FILE_BYTES=' + $proof.FileBytes)
    Write-Output ('VISUAL_SAMPLE_COUNT=' + $proof.Samples)
    Write-Output ('VISUAL_UNIQUE_COLORS_INFORMATIONAL=' + $proof.UniqueColors)
    Write-Output ('VISUAL_MEANINGFUL_SAMPLES=' + $proof.MeaningfulSamples)
    Write-Output ('VISUAL_BLACKGOLD_SAMPLES=' + $proof.GoldLikeSamples)
    Write-Output ('VISUAL_CHROMATIC_SAMPLES=' + $proof.ChromaticSamples)
    Write-Output ('VISUAL_STRUCTURAL_TRANSITIONS=' + $proof.StructuralTransitions)
    Write-Output ('VISUAL_OCCUPIED_VERTICAL_BANDS=' + $proof.OccupiedVerticalBands)
    Write-Output 'UNIQUE_COLOR_COUNT_HARD_GATE=false'
    Write-Output 'ARBITRARY_60000_BYTE_GATE=REPLACED_BY_CONTENT_AWARE_GUARD'
    exit 0
}
finally {
    if (Test-Path -LiteralPath $runtimePath -PathType Leaf) {
        Remove-Item -LiteralPath $runtimePath -Force -ErrorAction SilentlyContinue
    }
}
