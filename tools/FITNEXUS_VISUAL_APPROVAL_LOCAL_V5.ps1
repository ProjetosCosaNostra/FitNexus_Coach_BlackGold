[CmdletBinding()]
param(
    [string]$RepoRoot = 'E:\FitNexus_Coach_BlackGold',
    [string]$Branch = 'blackgold/mobile-home-premium-redesign-v1'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw 'git nao encontrado no PATH.'
}
if (-not (Get-Command flutter -ErrorAction SilentlyContinue)) {
    throw 'flutter nao encontrado no PATH.'
}
if (-not (Test-Path -LiteralPath $RepoRoot)) {
    throw "Repositorio local nao encontrado: $RepoRoot"
}

$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$exchange = Join-Path $RepoRoot '00_CODEX_EXCHANGE'
New-Item -ItemType Directory -Force -Path $exchange | Out-Null
$receipt = Join-Path $exchange "FITNEXUS_VISUAL_APPROVAL_V5_$timestamp.txt"
$worktree = Join-Path $env:TEMP 'fitnexus_visual_approval_v5'

Start-Transcript -Path $receipt -Force | Out-Null
try {
    Write-Host "`n=== Sincronizando candidato remoto sem tocar no workspace atual ===" -ForegroundColor Cyan
    Set-Location -LiteralPath $RepoRoot
    & git fetch origin $Branch
    if ($LASTEXITCODE -ne 0) { throw 'git fetch falhou.' }

    if (Test-Path -LiteralPath $worktree) {
        & git worktree remove --force $worktree 2>$null
        if (Test-Path -LiteralPath $worktree) {
            Remove-Item -LiteralPath $worktree -Recurse -Force
        }
    }

    & git worktree prune
    & git worktree add --detach $worktree "origin/$Branch"
    if ($LASTEXITCODE -ne 0) { throw 'git worktree add falhou.' }

    $head = (& git -C $worktree rev-parse HEAD).Trim()
    Write-Host "COMMIT: $head" -ForegroundColor Green

    $appRoot = Join-Path $worktree '03_app_flutter\fitnexus_app'
    if (-not (Test-Path -LiteralPath (Join-Path $appRoot 'pubspec.yaml'))) {
        throw "App Flutter nao encontrado em: $appRoot"
    }

    Write-Host "`n=== Dependencias Flutter ===" -ForegroundColor Cyan
    Set-Location -LiteralPath $appRoot
    & flutter pub get
    if ($LASTEXITCODE -ne 0) { throw 'flutter pub get falhou.' }

    Write-Host "`n=== Procurando Android/emulador ===" -ForegroundColor Cyan
    $deviceJson = (& flutter devices --machine | Out-String)
    if ($LASTEXITCODE -ne 0) { throw 'flutter devices falhou.' }
    $devices = @($deviceJson | ConvertFrom-Json)
    $android = @($devices | Where-Object {
        ($_.id -like 'emulator-*') -or ($_.targetPlatform -like 'android-*') -or ($_.sdk -like 'Android*')
    } | Select-Object -First 1)

    if (($android.Count -eq 0) -or (-not $android[0].id)) {
        throw 'Nenhum Android/emulador foi encontrado. Abra o emulador e execute novamente o mesmo comando.'
    }

    $deviceId = [string]$android[0].id
    Write-Host "DEVICE: $deviceId" -ForegroundColor Green

    Write-Host "`n=== Instalando e abrindo candidato visual ===" -ForegroundColor Cyan
    & flutter run -d $deviceId --debug --no-resident
    if ($LASTEXITCODE -ne 0) { throw 'flutter run falhou.' }

    $adbCommand = Get-Command adb -ErrorAction SilentlyContinue
    if ($adbCommand) {
        Start-Sleep -Seconds 4
        $remoteShot = '/sdcard/fitnexus_visual_approval_v5.png'
        $localShot = Join-Path $exchange "FITNEXUS_MOBILE_APPROVAL_V5_$timestamp.png"
        & adb -s $deviceId shell screencap -p $remoteShot | Out-Null
        if ($LASTEXITCODE -eq 0) {
            & adb -s $deviceId pull $remoteShot $localShot | Out-Null
            if ($LASTEXITCODE -eq 0) {
                & adb -s $deviceId shell rm -f $remoteShot | Out-Null
                Write-Host "SCREENSHOT: $localShot" -ForegroundColor Green
            }
        }
    }

    Write-Host "`nCANDIDATO ABERTO. NAO FAZER MERGE SEM APROVACAO VISUAL EXPLICITA." -ForegroundColor Green
    Write-Host "RECEIPT: $receipt"
}
finally {
    Stop-Transcript | Out-Null
}
