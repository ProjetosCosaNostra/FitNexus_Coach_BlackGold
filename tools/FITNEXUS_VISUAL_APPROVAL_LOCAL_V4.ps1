[CmdletBinding()]
param(
    [string]$RepoRoot = 'E:\FitNexus_Coach_BlackGold',
    [string]$Branch = 'blackgold/mobile-home-premium-redesign-v1'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Step([string]$Text) {
    Write-Host "`n=== $Text ===" -ForegroundColor Cyan
}

function Require-Command([string]$Name) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Comando obrigatório não encontrado: $Name"
    }
}

Require-Command git
Require-Command flutter

if (-not (Test-Path -LiteralPath $RepoRoot)) {
    throw "Repositório local não encontrado: $RepoRoot"
}

$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$exchange = Join-Path $RepoRoot '00_CODEX_EXCHANGE'
New-Item -ItemType Directory -Force -Path $exchange | Out-Null
$receipt = Join-Path $exchange "FITNEXUS_VISUAL_APPROVAL_V4_$timestamp.txt"

Start-Transcript -Path $receipt -Force | Out-Null
try {
    Step 'Sincronizando exatamente a branch candidata'
    Set-Location -LiteralPath $RepoRoot

    $dirty = git status --porcelain
    if ($LASTEXITCODE -ne 0) { throw 'git status falhou.' }

    if ($dirty) {
        $stashMessage = "FITNEXUS_AUTO_BACKUP_$timestamp"
        Write-Host "Alterações locais detectadas. Salvando automaticamente em stash: $stashMessage" -ForegroundColor Yellow
        git stash push -u -m $stashMessage
        if ($LASTEXITCODE -ne 0) { throw 'Não foi possível proteger as alterações locais com git stash.' }
    }

    git fetch origin $Branch
    if ($LASTEXITCODE -ne 0) { throw 'git fetch falhou.' }

    git checkout -B $Branch "origin/$Branch"
    if ($LASTEXITCODE -ne 0) { throw 'git checkout da branch candidata falhou.' }

    git reset --hard "origin/$Branch"
    if ($LASTEXITCODE -ne 0) { throw 'git reset para o commit remoto falhou.' }

    $head = (git rev-parse HEAD).Trim()
    Write-Host "HEAD: $head" -ForegroundColor Green

    $appRoot = Join-Path $RepoRoot '03_app_flutter\fitnexus_app'
    if (-not (Test-Path -LiteralPath (Join-Path $appRoot 'pubspec.yaml'))) {
        throw "Aplicativo Flutter não encontrado em: $appRoot"
    }

    Step 'Resolvendo dependências Flutter'
    Set-Location -LiteralPath $appRoot
    flutter pub get
    if ($LASTEXITCODE -ne 0) { throw 'flutter pub get falhou.' }

    Step 'Localizando o emulador Android já aberto'
    $deviceJson = flutter devices --machine
    if ($LASTEXITCODE -ne 0) { throw 'flutter devices falhou.' }

    $devices = @($deviceJson | ConvertFrom-Json)
    $android = @($devices | Where-Object {
        ($_.targetPlatform -like 'android-*') -or
        ($_.sdk -like 'Android*') -or
        ($_.id -like 'emulator-*')
    } | Select-Object -First 1)

    if (-not $android -or -not $android[0].id) {
        throw 'Nenhum Android/emulador foi encontrado. Deixe o emulador aberto e execute novamente o mesmo comando.'
    }

    $deviceId = [string]$android[0].id
    Write-Host "Dispositivo: $deviceId" -ForegroundColor Green

    Step 'Instalando e abrindo a versão exata para aprovação visual'
    flutter run -d $deviceId --debug --no-resident
    if ($LASTEXITCODE -ne 0) { throw 'flutter run falhou.' }

    Step 'Capturando evidência visual sem abrir Explorer'
    $adb = Get-Command adb -ErrorAction SilentlyContinue
    if ($adb) {
        Start-Sleep -Seconds 4
        $remoteShot = '/sdcard/fitnexus_visual_approval_v4.png'
        $localShot = Join-Path $exchange "FITNEXUS_MOBILE_APPROVAL_V4_$timestamp.png"
        adb -s $deviceId shell screencap -p $remoteShot | Out-Null
        if ($LASTEXITCODE -eq 0) {
            adb -s $deviceId pull $remoteShot $localShot | Out-Null
            if ($LASTEXITCODE -eq 0) {
                adb -s $deviceId shell rm -f $remoteShot | Out-Null
                Write-Host "SCREENSHOT: $localShot" -ForegroundColor Green
            }
        }
    } else {
        Write-Host 'ADB não está no PATH; o app foi aberto no emulador, mas a captura automática foi ignorada.' -ForegroundColor Yellow
    }

    Write-Host "`nCANDIDATO VISUAL ABERTO — não fazer merge sem aprovação explícita do usuário." -ForegroundColor Green
    Write-Host "COMMIT: $head"
    Write-Host "RECEIPT: $receipt"
}
finally {
    Stop-Transcript | Out-Null
}
