[CmdletBinding()]
param(
  [string]$RepoRoot = 'E:\FitNexus_Coach_BlackGold',
  [string]$CandidateSha = '6eadba69783006467a1f0f2d6cd92b5f2128a15b',
  [int]$Port = 8765
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ArtifactId = '9940529004'
$ArtifactUrl = "https://api.github.com/repos/ProjetosCosaNostra/FitNexus_Coach_BlackGold/actions/artifacts/$ArtifactId/zip"
$PreviewRoot = Join-Path $RepoRoot '_visual_preview_current'
$ZipPath = Join-Path $PreviewRoot 'stage66.zip'
$ExtractRoot = Join-Path $PreviewRoot 'artifact'
$PidFile = Join-Path $RepoRoot '.fitnexus_preview_server.pid'
$WebRoot = $null

function Stop-OldPreviewServer {
  if (Test-Path -LiteralPath $PidFile) {
    try {
      $oldPid = [int](Get-Content -LiteralPath $PidFile -Raw).Trim()
      $p = Get-Process -Id $oldPid -ErrorAction SilentlyContinue
      if ($p) { Stop-Process -Id $oldPid -Force -ErrorAction SilentlyContinue }
    } catch {}
    Remove-Item -LiteralPath $PidFile -Force -ErrorAction SilentlyContinue
  }
}

function Get-WebRootFromArtifact {
  param([string]$Root)
  $index = Get-ChildItem -LiteralPath $Root -Filter index.html -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -match '[\\/]03_app_flutter[\\/]fitnexus_app[\\/]build[\\/]web[\\/]index\.html$' } |
    Select-Object -First 1
  if ($index) { return [string]$index.Directory.FullName }
  return $null
}

function Build-LocalFallback {
  Write-Host 'DOWNLOAD_UNAVAILABLE -> FALLBACK_LOCAL_BUILD'
  $git = (Get-Command git -ErrorAction Stop).Source
  $flutter = (Get-Command flutter -ErrorAction Stop).Source

  Write-Host 'FITNEXUS_FASTPATH_STAGE=FETCH_CANDIDATE'
  $null = & $git -C $RepoRoot fetch origin blackgold/mobile-home-premium-redesign-v1
  if ($LASTEXITCODE -ne 0) { throw 'git fetch failed' }
  $null = & $git -C $RepoRoot cat-file -e "$CandidateSha^{commit}"
  if ($LASTEXITCODE -ne 0) { throw "Candidate SHA not available locally: $CandidateSha" }

  $wt = Join-Path $env:TEMP ('FitNexusPreview_' + $CandidateSha.Substring(0,12))
  if (Test-Path -LiteralPath $wt) {
    try { $null = & $git -C $RepoRoot worktree remove --force $wt } catch {}
    Remove-Item -LiteralPath $wt -Recurse -Force -ErrorAction SilentlyContinue
  }

  Write-Host 'FITNEXUS_FASTPATH_STAGE=CREATE_ISOLATED_WORKTREE'
  $null = & $git -C $RepoRoot worktree add --detach $wt $CandidateSha
  if ($LASTEXITCODE -ne 0) { throw 'git worktree add failed' }

  try {
    $app = Join-Path $wt '03_app_flutter\fitnexus_app'
    if (-not (Test-Path -LiteralPath (Join-Path $app 'pubspec.yaml'))) {
      throw "Flutter app not found in isolated worktree: $app"
    }

    Push-Location $app
    try {
      Write-Host 'FITNEXUS_FASTPATH_STAGE=FLUTTER_PUB_GET'
      $null = & $flutter pub get
      if ($LASTEXITCODE -ne 0) { throw 'flutter pub get failed' }

      Write-Host 'FITNEXUS_FASTPATH_STAGE=BUILD_WEB_RELEASE'
      $null = & $flutter build web --release --no-wasm-dry-run
      if ($LASTEXITCODE -ne 0) { throw 'flutter build web --release failed' }
    }
    finally {
      Pop-Location
    }

    $builtWeb = Join-Path $app 'build\web'
    if (-not (Test-Path -LiteralPath (Join-Path $builtWeb 'index.html'))) {
      throw 'LOCAL_BUILD_WEB_INDEX_NOT_FOUND'
    }

    $dest = Join-Path $PreviewRoot 'local_build_web'
    if (Test-Path -LiteralPath $dest) {
      Remove-Item -LiteralPath $dest -Recurse -Force
    }
    Copy-Item -LiteralPath $builtWeb -Destination $dest -Recurse -Force

    # IMPORTANT: all native command output above is consumed into $null, so the
    # function emits exactly one scalar value: the web root path.
    return [string]$dest
  }
  finally {
    try { $null = & $git -C $RepoRoot worktree remove --force $wt } catch {}
    Remove-Item -LiteralPath $wt -Recurse -Force -ErrorAction SilentlyContinue
  }
}

Stop-OldPreviewServer
if (Test-Path -LiteralPath $PreviewRoot) { Remove-Item -LiteralPath $PreviewRoot -Recurse -Force }
New-Item -ItemType Directory -Path $PreviewRoot -Force | Out-Null

Write-Host 'FITNEXUS_FASTPATH_STAGE=DOWNLOAD_COMPILED_ARTIFACT'
$curl = Get-Command curl.exe -ErrorAction SilentlyContinue
$downloadOk = $false
if ($curl) {
  $null = & $curl.Source -L --fail --silent --show-error -H 'Accept: application/vnd.github+json' -H 'X-GitHub-Api-Version: 2022-11-28' $ArtifactUrl -o $ZipPath
  if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $ZipPath) -and ((Get-Item $ZipPath).Length -gt 1000000)) {
    try {
      Expand-Archive -LiteralPath $ZipPath -DestinationPath $ExtractRoot -Force
      $WebRoot = Get-WebRootFromArtifact -Root $ExtractRoot
      if ($WebRoot) { $downloadOk = $true }
    } catch {}
  }
}

if (-not $downloadOk) {
  $WebRoot = [string](Build-LocalFallback)
}

if ([string]::IsNullOrWhiteSpace([string]$WebRoot)) {
  throw 'WEB_PREVIEW_ROOT_EMPTY'
}
$IndexPath = Join-Path -Path ([string]$WebRoot) -ChildPath 'index.html'
if (-not (Test-Path -LiteralPath $IndexPath)) {
  throw "WEB_PREVIEW_ROOT_NOT_FOUND: $WebRoot"
}

Write-Host "FITNEXUS_FASTPATH_WEBROOT=$WebRoot"

$python = Get-Command python.exe -ErrorAction SilentlyContinue
$py = Get-Command py.exe -ErrorAction SilentlyContinue
if (-not $python -and -not $py) { throw 'Python was not found for the local preview server.' }

if ($python) {
  $server = Start-Process -FilePath $python.Source -ArgumentList @('-m','http.server',"$Port",'--bind','127.0.0.1','--directory',([string]$WebRoot)) -WindowStyle Hidden -PassThru
} else {
  $server = Start-Process -FilePath $py.Source -ArgumentList @('-3','-m','http.server',"$Port",'--bind','127.0.0.1','--directory',([string]$WebRoot)) -WindowStyle Hidden -PassThru
}
Set-Content -LiteralPath $PidFile -Value $server.Id -Encoding Ascii

$url = "http://127.0.0.1:$Port/"
$deadline = (Get-Date).AddSeconds(20)
$ready = $false
while ((Get-Date) -lt $deadline) {
  try {
    $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2
    if ($r.StatusCode -eq 200) { $ready = $true; break }
  } catch {}
  Start-Sleep -Milliseconds 500
}
if (-not $ready) { throw 'LOCAL_PREVIEW_SERVER_NOT_READY' }

$edgeCandidates = @(
  (Join-Path ${env:ProgramFiles(x86)} 'Microsoft\Edge\Application\msedge.exe'),
  (Join-Path $env:ProgramFiles 'Microsoft\Edge\Application\msedge.exe')
) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }
if ($edgeCandidates.Count -gt 0) {
  Start-Process -FilePath $edgeCandidates[0] -ArgumentList @("--app=$url",'--window-size=430,850','--window-position=40,40') | Out-Null
} else {
  Start-Process $url | Out-Null
}

Write-Host 'FITNEXUS_FASTPATH_PREVIEW=PASS'
Write-Host "CANDIDATE_SHA=$CandidateSha"
Write-Host "SERVER_PID=$($server.Id)"
Write-Host "URL=$url"
Write-Host 'NO_EMULATOR=true'
Write-Host 'NO_MANUAL_EXTRACTION=true'
Write-Host 'PLAY_PUBLICATION_PERFORMED=false'
