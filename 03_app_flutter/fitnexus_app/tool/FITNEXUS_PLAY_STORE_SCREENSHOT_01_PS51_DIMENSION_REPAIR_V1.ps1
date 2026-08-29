param(
    [switch]$ValidateOnly
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$sourcePath = Join-Path $PSScriptRoot 'FITNEXUS_PLAY_STORE_SCREENSHOT_01_CAPTURE_V1.ps1'
if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
    throw 'FNX_PLAY_SCREENSHOT_01_PS51_REPAIR_SOURCE_MISSING'
}

$source = Get-Content -LiteralPath $sourcePath -Raw
$pattern = '(?s)function Get-BigEndianInt32\s*\{.*?\r?\n\}\r?\n\r?\nfunction Get-PngDimensions\s*\{'
$replacement = @'
function Get-BigEndianInt32 {
    param(
        [Parameter(Mandatory = $true)][byte[]]$Bytes,
        [Parameter(Mandatory = $true)][int]$Offset
    )
    return ((([int]$Bytes[$Offset]) -shl 24) -bor
            (([int]$Bytes[$Offset + 1]) -shl 16) -bor
            (([int]$Bytes[$Offset + 2]) -shl 8) -bor
            ([int]$Bytes[$Offset + 3]))
}

function Get-PngDimensions {
'@

$patched = [regex]::Replace($source, $pattern, $replacement, 1)
if ($patched -eq $source) {
    throw 'FNX_PLAY_SCREENSHOT_01_PS51_REPAIR_PATTERN_NOT_FOUND'
}
if ($patched -notmatch '\(\[int\]\$Bytes\[\$Offset \+ 2\]\) -shl 8') {
    throw 'FNX_PLAY_SCREENSHOT_01_PS51_REPAIR_INT_CAST_GUARD_FAILED'
}

$runtimePath = Join-Path $PSScriptRoot ('FITNEXUS_PLAY_STORE_SCREENSHOT_01_CAPTURE_V1.__ps51_fixed_' + [guid]::NewGuid().ToString('N') + '.ps1')
$encoding = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($runtimePath, $patched, $encoding)

try {
    Write-Output 'PS51_PNG_DIMENSION_REPAIR=ACTIVE'
    if ($ValidateOnly) {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $runtimePath -ValidateOnly
    }
    else {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $runtimePath
    }
    $code = $LASTEXITCODE
    if ($null -eq $code) { $code = 1 }
    exit $code
}
finally {
    if (Test-Path -LiteralPath $runtimePath -PathType Leaf) {
        Remove-Item -LiteralPath $runtimePath -Force -ErrorAction SilentlyContinue
    }
}
