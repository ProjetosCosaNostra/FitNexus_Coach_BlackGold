# FITNEXUS COACH BLACKGOLD - LOCAL VISUAL APPROVAL RUNNER V2
# Purpose: build, install and visually prove the exact remote HEAD on a dedicated local Android emulator.
# This runner NEVER publishes to Google Play and NEVER uses the Play upload key.

[CmdletBinding()]
param(
    [string]$RepoRoot = 'E:\FitNexus_Coach_BlackGold',
    [string]$Branch = 'blackgold/mobile-home-premium-redesign-v1',
    [string]$ExpectedSha = '',
    [string]$AvdName = 'FitNexus_API35_Visual',
    [int]$ApiLevel = 35,
    [int]$BootTimeoutSec = 420
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepositoryFullName = 'ProjetosCosaNostra/FitNexus_Coach_BlackGold'
$PackageName = 'br.com.lafamigliaplayworks.fitnexuscoach'
$RequestedViewport = '1080x1920'
$RequestedDensity = '420'
$SystemImagePackage = "system-images;android-$ApiLevel;google_apis;x86_64"
$State = [ordered]@{
    schema_version = 2
    kind = 'FITNEXUS_ANDROID_LOCAL_VISUAL_APPROVAL'
    status = 'STARTED'
    generated_at_utc = $null
    repository = $RepositoryFullName
    branch = $Branch
    source_commit_sha = $null
    remote_head_after = $null
    application_id = $PackageName
    version_name = $null
    version_code = $null
    build_mode = 'release'
    signing_mode = 'LOCAL_VALIDATION_KEY_DPAPI'
    play_upload_key_used = $false
    api_level = $ApiLevel
    avd_name = $AvdName
    emulator_serial = $null
    requested_viewport = $RequestedViewport
    requested_density = [int]$RequestedDensity
    apk_path = $null
    apk_sha256 = $null
    screenshot_path = $null
    screenshot_sha256 = $null
    install_result = $null
    launch_result = $null
    process_id = $null
    ui_dump_path = $null
    logcat_path = $null
    package_dumpsys_path = $null
    zip_path = $null
    zip_sha256 = $null
    play_publication_performed = $false
    leave_emulator_open = $true
    data_wipe_performed = $false
    purpose = 'exact_sha_premerge_visual_approval'
    failure = $null
}

$WorktreePath = $null
$WorktreeAdded = $false
$KeyPropertiesPath = $null
$OutputDir = $null
$ReceiptPath = $null
$ZipPath = $null
$ZipHashPath = $null
$Failure = $null
$CoreSucceeded = $false

function Write-Section {
    param([Parameter(Mandatory=$true)][string]$Title)
    Write-Host ''
    Write-Host ('=' * 72)
    Write-Host $Title
    Write-Host ('=' * 72)
}

function Resolve-RequiredCommand {
    param([Parameter(Mandatory=$true)][string[]]$Names)
    foreach ($Name in $Names) {
        $Command = Get-Command $Name -ErrorAction SilentlyContinue
        if ($null -ne $Command) { return $Command.Source }
    }
    throw "Required command not found: $($Names -join ', ')"
}

function Invoke-Native {
    param(
        [Parameter(Mandatory=$true)][string]$FilePath,
        [string[]]$Arguments = @(),
        [string]$WorkingDirectory = ''
    )
    $Pushed = $false
    try {
        if ($WorkingDirectory) {
            Push-Location -LiteralPath $WorkingDirectory
            $Pushed = $true
        }
        & $FilePath @Arguments
        $ExitCode = $LASTEXITCODE
        if ($ExitCode -ne 0) {
            throw "Command failed with exit code $ExitCode: $FilePath $($Arguments -join ' ')"
        }
    }
    finally {
        if ($Pushed) { Pop-Location }
    }
}

function Invoke-NativeCapture {
    param(
        [Parameter(Mandatory=$true)][string]$FilePath,
        [string[]]$Arguments = @(),
        [string]$WorkingDirectory = ''
    )
    $Pushed = $false
    try {
        if ($WorkingDirectory) {
            Push-Location -LiteralPath $WorkingDirectory
            $Pushed = $true
        }
        $Output = & $FilePath @Arguments 2>&1
        $ExitCode = $LASTEXITCODE
        $Text = (($Output | ForEach-Object { "$_" }) -join [Environment]::NewLine).Trim()
        if ($ExitCode -ne 0) {
            throw "Command failed with exit code $ExitCode: $FilePath $($Arguments -join ' ')`n$Text"
        }
        return $Text
    }
    finally {
        if ($Pushed) { Pop-Location }
    }
}

function Write-Utf8NoBom {
    param(
        [Parameter(Mandatory=$true)][string]$Path,
        [Parameter(Mandatory=$true)][string]$Content
    )
    $Encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content, $Encoding)
}

function Write-Receipt {
    if (-not $ReceiptPath) { return }
    $State.generated_at_utc = [DateTime]::UtcNow.ToString('o')
    $Json = $State | ConvertTo-Json -Depth 8
    Write-Utf8NoBom -Path $ReceiptPath -Content ($Json + [Environment]::NewLine)
}

function Resolve-AndroidSdkRoot {
    $Candidates = New-Object System.Collections.Generic.List[string]
    if ($env:ANDROID_SDK_ROOT) { $Candidates.Add($env:ANDROID_SDK_ROOT) }
    if ($env:ANDROID_HOME) { $Candidates.Add($env:ANDROID_HOME) }
    if ($env:LOCALAPPDATA) { $Candidates.Add((Join-Path $env:LOCALAPPDATA 'Android\Sdk')) }
    foreach ($Candidate in ($Candidates | Select-Object -Unique)) {
        if ($Candidate -and (Test-Path -LiteralPath $Candidate)) { return $Candidate }
    }
    throw 'Android SDK root not found. Set ANDROID_SDK_ROOT/ANDROID_HOME or install Android Studio SDK.'
}

function Resolve-SdkTool {
    param(
        [Parameter(Mandatory=$true)][string]$SdkRoot,
        [Parameter(Mandatory=$true)][string]$FileName
    )
    $CmdlineRoot = Join-Path $SdkRoot 'cmdline-tools'
    if (-not (Test-Path -LiteralPath $CmdlineRoot)) {
        throw "Android SDK Command-line Tools not found under $CmdlineRoot"
    }
    $Tool = Get-ChildItem -LiteralPath $CmdlineRoot -Filter $FileName -Recurse -File -ErrorAction SilentlyContinue |
        Sort-Object FullName |
        Select-Object -Last 1
    if ($null -eq $Tool) { throw "Android SDK tool not found: $FileName" }
    return $Tool.FullName
}

function Resolve-KeyTool {
    $Command = Get-Command 'keytool.exe' -ErrorAction SilentlyContinue
    if ($null -ne $Command) { return $Command.Source }
    if ($env:JAVA_HOME) {
        $Candidate = Join-Path $env:JAVA_HOME 'bin\keytool.exe'
        if (Test-Path -LiteralPath $Candidate) { return $Candidate }
    }
    if ($env:ProgramFiles) {
        $AndroidStudioKeytool = Join-Path $env:ProgramFiles 'Android\Android Studio\jbr\bin\keytool.exe'
        if (Test-Path -LiteralPath $AndroidStudioKeytool) { return $AndroidStudioKeytool }
    }
    throw 'keytool.exe not found in PATH, JAVA_HOME, or Android Studio JBR.'
}

function Get-RemoteHead {
    param(
        [Parameter(Mandatory=$true)][string]$Git,
        [Parameter(Mandatory=$true)][string]$Root,
        [Parameter(Mandatory=$true)][string]$RemoteBranch
    )
    Invoke-Native -FilePath $Git -Arguments @('-C', $Root, 'fetch', '--prune', 'origin', $RemoteBranch)
    $Sha = Invoke-NativeCapture -FilePath $Git -Arguments @('-C', $Root, 'rev-parse', "refs/remotes/origin/$RemoteBranch")
    $Sha = $Sha.Trim()
    if ($Sha -notmatch '^[0-9a-f]{40}$') { throw "Invalid remote SHA: $Sha" }
    return $Sha
}

function Get-OrCreateValidationSigning {
    param([Parameter(Mandatory=$true)][string]$KeyTool)
    if (-not $env:LOCALAPPDATA) { throw 'LOCALAPPDATA is not available.' }
    $SigningRoot = Join-Path $env:LOCALAPPDATA 'BlackGold\FitNexus\VisualApprovalSigning'
    New-Item -ItemType Directory -Path $SigningRoot -Force | Out-Null
    $KeyStore = Join-Path $SigningRoot 'fitnexus-visual-validation.jks'
    $ProtectedPasswordFile = Join-Path $SigningRoot 'fitnexus-visual-validation.password.dpapi'

    if ((Test-Path -LiteralPath $KeyStore) -xor (Test-Path -LiteralPath $ProtectedPasswordFile)) {
        throw "Local validation signing state is inconsistent at $SigningRoot. Refusing to replace it automatically because that could break APK update signatures."
    }

    if (-not (Test-Path -LiteralPath $KeyStore)) {
        $RandomBytes = New-Object byte[] 32
        [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($RandomBytes)
        $Password = [Convert]::ToBase64String($RandomBytes)
        Invoke-Native -FilePath $KeyTool -Arguments @(
            '-genkeypair',
            '-keystore', $KeyStore,
            '-storepass', $Password,
            '-keypass', $Password,
            '-alias', 'visual_approval',
            '-keyalg', 'RSA',
            '-keysize', '2048',
            '-validity', '3650',
            '-dname', 'CN=FitNexus Visual Approval,O=BlackGold,C=BR',
            '-noprompt'
        )
        $PlainBytes = [System.Text.Encoding]::UTF8.GetBytes($Password)
        $ProtectedBytes = [System.Security.Cryptography.ProtectedData]::Protect(
            $PlainBytes,
            $null,
            [System.Security.Cryptography.DataProtectionScope]::CurrentUser
        )
        [System.IO.File]::WriteAllBytes($ProtectedPasswordFile, $ProtectedBytes)
        [Array]::Clear($PlainBytes, 0, $PlainBytes.Length)
    }

    $CipherBytes = [System.IO.File]::ReadAllBytes($ProtectedPasswordFile)
    $UnprotectedBytes = [System.Security.Cryptography.ProtectedData]::Unprotect(
        $CipherBytes,
        $null,
        [System.Security.Cryptography.DataProtectionScope]::CurrentUser
    )
    try {
        $RecoveredPassword = [System.Text.Encoding]::UTF8.GetString($UnprotectedBytes)
    }
    finally {
        [Array]::Clear($UnprotectedBytes, 0, $UnprotectedBytes.Length)
    }
    return [pscustomobject]@{
        KeyStore = $KeyStore
        Password = $RecoveredPassword
        Alias = 'visual_approval'
    }
}

function Find-DedicatedEmulatorSerial {
    param(
        [Parameter(Mandatory=$true)][string]$Adb,
        [Parameter(Mandatory=$true)][string]$TargetAvdName
    )
    $DevicesText = Invoke-NativeCapture -FilePath $Adb -Arguments @('devices')
    foreach ($Line in ($DevicesText -split "`r?`n")) {
        if ($Line -match '^(emulator-\d+)\s+(device|offline)') {
            $Serial = $Matches[1]
            try {
                $NameText = Invoke-NativeCapture -FilePath $Adb -Arguments @('-s', $Serial, 'emu', 'avd', 'name')
                $Name = (($NameText -split "`r?`n") | Where-Object { $_ -and $_.Trim() -ne 'OK' } | Select-Object -First 1).Trim()
                if ($Name -eq $TargetAvdName) { return $Serial }
            }
            catch {
                continue
            }
        }
    }
    return $null
}

function Select-UnusedEmulatorPort {
    param([Parameter(Mandatory=$true)][string]$Adb)
    $Used = @{}
    try {
        $DevicesText = Invoke-NativeCapture -FilePath $Adb -Arguments @('devices')
        foreach ($Line in ($DevicesText -split "`r?`n")) {
            if ($Line -match '^emulator-(\d+)\s+') { $Used[[int]$Matches[1]] = $true }
        }
    }
    catch { }
    for ($Port = 5580; $Port -le 5680; $Port += 2) {
        if (-not $Used.ContainsKey($Port)) { return $Port }
    }
    throw 'No free emulator port found in the dedicated range 5580-5680.'
}

function Wait-ForAndroidBoot {
    param(
        [Parameter(Mandatory=$true)][string]$Adb,
        [Parameter(Mandatory=$true)][string]$Serial,
        [Parameter(Mandatory=$true)][int]$TimeoutSec
    )
    $Deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $Deadline) {
        try {
            $DeviceState = Invoke-NativeCapture -FilePath $Adb -Arguments @('-s', $Serial, 'get-state')
            if ($DeviceState.Trim() -eq 'device') {
                $Boot = Invoke-NativeCapture -FilePath $Adb -Arguments @('-s', $Serial, 'shell', 'getprop', 'sys.boot_completed')
                if ($Boot.Trim() -eq '1') { return }
            }
        }
        catch { }
        Start-Sleep -Seconds 2
    }
    throw "Android emulator $Serial did not finish booting within $TimeoutSec seconds."
}

function Test-PngFile {
    param([Parameter(Mandatory=$true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return $false }
    $Bytes = [System.IO.File]::ReadAllBytes($Path)
    if ($Bytes.Length -lt 24) { return $false }
    $Signature = @(0x89,0x50,0x4E,0x47,0x0D,0x0A,0x1A,0x0A)
    for ($Index = 0; $Index -lt $Signature.Count; $Index++) {
        if ($Bytes[$Index] -ne $Signature[$Index]) { return $false }
    }
    return $true
}

try {
    Write-Section 'FITNEXUS LOCAL VISUAL APPROVAL V2 - EXACT SHA / NO PUBLISH'

    if ($env:OS -ne 'Windows_NT') { throw 'This runner is intentionally Windows-only.' }
    if (-not (Test-Path -LiteralPath $RepoRoot)) { throw "Repository root not found: $RepoRoot" }
    if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot '.git'))) { throw "Not a Git working copy: $RepoRoot" }

    $EvidenceRoot = Join-Path $RepoRoot '03_app_flutter\fitnexus_app\build'
    New-Item -ItemType Directory -Path $EvidenceRoot -Force | Out-Null
    $OutputDir = Join-Path $EvidenceRoot 'visual_approval_local_current'
    $ReceiptPath = Join-Path $OutputDir 'FITNEXUS_VISUAL_APPROVAL_RECEIPT_V2.json'
    $ZipPath = Join-Path $EvidenceRoot 'FITNEXUS_VISUAL_APPROVAL_CURRENT.zip'
    $ZipHashPath = Join-Path $EvidenceRoot 'FITNEXUS_VISUAL_APPROVAL_CURRENT.zip.sha256.txt'
    if (Test-Path -LiteralPath $OutputDir) { Remove-Item -LiteralPath $OutputDir -Recurse -Force }
    if (Test-Path -LiteralPath $ZipPath) { Remove-Item -LiteralPath $ZipPath -Force }
    if (Test-Path -LiteralPath $ZipHashPath) { Remove-Item -LiteralPath $ZipHashPath -Force }
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

    $Git = Resolve-RequiredCommand -Names @('git.exe', 'git')
    $Flutter = Resolve-RequiredCommand -Names @('flutter.bat', 'flutter')
    $KeyTool = Resolve-KeyTool

    $OriginUrl = Invoke-NativeCapture -FilePath $Git -Arguments @('-C', $RepoRoot, 'config', '--get', 'remote.origin.url')
    if ($OriginUrl -notmatch 'github\.com[:/]+ProjetosCosaNostra/FitNexus_Coach_BlackGold(?:\.git)?$') {
        throw 'The local origin does not point to ProjetosCosaNostra/FitNexus_Coach_BlackGold. Refusing to run.'
    }

    Write-Section '1/6 - PIN REMOTE HEAD AND CREATE ISOLATED WORKTREE'
    $HeadSha = Get-RemoteHead -Git $Git -Root $RepoRoot -RemoteBranch $Branch
    $State.source_commit_sha = $HeadSha
    if ($ExpectedSha) {
        $ExpectedSha = $ExpectedSha.Trim().ToLowerInvariant()
        if ($ExpectedSha -notmatch '^[0-9a-f]{40}$') { throw "ExpectedSha is invalid: $ExpectedSha" }
        if ($HeadSha -ne $ExpectedSha) {
            throw "REMOTE_HEAD_MISMATCH: expected $ExpectedSha but origin/$Branch is $HeadSha"
        }
    }
    Write-Host "Pinned HEAD: $HeadSha"

    $WorktreePath = Join-Path $env:TEMP ("FitNexus_Visual_" + $HeadSha.Substring(0, 12))
    if (Test-Path -LiteralPath $WorktreePath) {
        try { Invoke-Native -FilePath $Git -Arguments @('-C', $RepoRoot, 'worktree', 'remove', '--force', $WorktreePath) } catch { Remove-Item -LiteralPath $WorktreePath -Recurse -Force -ErrorAction SilentlyContinue }
    }
    Invoke-Native -FilePath $Git -Arguments @('-C', $RepoRoot, 'worktree', 'add', '--detach', $WorktreePath, $HeadSha)
    $WorktreeAdded = $true
    $ActualWorktreeSha = Invoke-NativeCapture -FilePath $Git -Arguments @('-C', $WorktreePath, 'rev-parse', 'HEAD')
    if ($ActualWorktreeSha.Trim() -ne $HeadSha) { throw 'WORKTREE_SHA_MISMATCH' }

    $AppPath = Join-Path $WorktreePath '03_app_flutter\fitnexus_app'
    if (-not (Test-Path -LiteralPath (Join-Path $AppPath 'pubspec.yaml'))) { throw "Flutter app not found in worktree: $AppPath" }
    $PubspecText = Get-Content -LiteralPath (Join-Path $AppPath 'pubspec.yaml') -Raw
    if ($PubspecText -match '(?m)^version:\s*([^\s+]+)\+(\d+)\s*$') {
        $State.version_name = $Matches[1]
        $State.version_code = [int]$Matches[2]
    }

    Write-Section '2/6 - ANDROID SDK + DEDICATED AVD PREP'
    $SdkRoot = Resolve-AndroidSdkRoot
    $SdkManager = Resolve-SdkTool -SdkRoot $SdkRoot -FileName 'sdkmanager.bat'
    $AvdManager = Resolve-SdkTool -SdkRoot $SdkRoot -FileName 'avdmanager.bat'

    Invoke-Native -FilePath $SdkManager -Arguments @(
        'platform-tools',
        'emulator',
        'platforms;android-36',
        'build-tools;36.0.0',
        $SystemImagePackage
    )

    $Adb = Join-Path $SdkRoot 'platform-tools\adb.exe'
    $Emulator = Join-Path $SdkRoot 'emulator\emulator.exe'
    if (-not (Test-Path -LiteralPath $Adb)) { throw "adb.exe not found: $Adb" }
    if (-not (Test-Path -LiteralPath $Emulator)) { throw "emulator.exe not found: $Emulator" }

    $AvdList = Invoke-NativeCapture -FilePath $Emulator -Arguments @('-list-avds')
    $ExistingAvds = @($AvdList -split "`r?`n" | ForEach-Object { $_.Trim() } | Where-Object { $_ })
    if ($ExistingAvds -notcontains $AvdName) {
        Write-Host "Creating dedicated AVD: $AvdName"
        $CreateOutput = 'no' | & $AvdManager create avd --force --name $AvdName --package $SystemImagePackage --device 'pixel_6' 2>&1
        $CreateExitCode = $LASTEXITCODE
        if ($CreateExitCode -ne 0) {
            Write-Host 'pixel_6 device profile was not accepted; retrying with generic pixel profile.'
            $CreateOutput = 'no' | & $AvdManager create avd --force --name $AvdName --package $SystemImagePackage --device 'pixel' 2>&1
            $CreateExitCode = $LASTEXITCODE
        }
        if ($CreateExitCode -ne 0) {
            throw "Failed to create AVD $AvdName.`n$(($CreateOutput | ForEach-Object { "$_" }) -join [Environment]::NewLine)"
        }
    }

    Write-Section '3/6 - BUILD EXACT-SHA RELEASE APK WITH LOCAL VALIDATION SIGNING'
    Invoke-Native -FilePath $Flutter -Arguments @('pub', 'get') -WorkingDirectory $AppPath

    $Signing = Get-OrCreateValidationSigning -KeyTool $KeyTool
    $KeyPropertiesPath = Join-Path $AppPath 'android\key.properties'
    $LocalValidationKeystore = Join-Path $AppPath 'android\visual-approval-local.jks'
    Copy-Item -LiteralPath $Signing.KeyStore -Destination $LocalValidationKeystore -Force
    try {
        $KeyProperties = @(
            "storePassword=$($Signing.Password)",
            "keyPassword=$($Signing.Password)",
            "keyAlias=$($Signing.Alias)",
            'storeFile=visual-approval-local.jks'
        ) -join [Environment]::NewLine
        Write-Utf8NoBom -Path $KeyPropertiesPath -Content ($KeyProperties + [Environment]::NewLine)
        Invoke-Native -FilePath $Flutter -Arguments @('build', 'apk', '--release') -WorkingDirectory $AppPath
    }
    finally {
        Remove-Item -LiteralPath $KeyPropertiesPath -Force -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath $LocalValidationKeystore -Force -ErrorAction SilentlyContinue
        $KeyPropertiesPath = $null
    }

    $BuiltApkPath = Join-Path $AppPath 'build\app\outputs\flutter-apk\app-release.apk'
    if (-not (Test-Path -LiteralPath $BuiltApkPath)) { throw "Release APK not produced: $BuiltApkPath" }
    $ApkPath = Join-Path $OutputDir 'FITNEXUS_EXACT_SHA_RELEASE.apk'
    Copy-Item -LiteralPath $BuiltApkPath -Destination $ApkPath -Force
    $State.apk_path = $ApkPath
    $State.apk_sha256 = (Get-FileHash -LiteralPath $ApkPath -Algorithm SHA256).Hash.ToLowerInvariant()
    Write-Host "APK SHA-256: $($State.apk_sha256)"

    Write-Section '4/6 - START/REUSE ONLY THE DEDICATED FITNEXUS EMULATOR'
    $Serial = Find-DedicatedEmulatorSerial -Adb $Adb -TargetAvdName $AvdName
    if (-not $Serial) {
        $Port = Select-UnusedEmulatorPort -Adb $Adb
        $Serial = "emulator-$Port"
        Write-Host "Starting visible AVD $AvdName on $Serial"
        Start-Process -FilePath $Emulator -ArgumentList @(
            '-avd', $AvdName,
            '-port', "$Port",
            '-no-snapshot-load',
            '-noaudio',
            '-gpu', 'auto'
        ) | Out-Null
    }
    else {
        Write-Host "Reusing dedicated AVD already running: $Serial"
    }
    $State.emulator_serial = $Serial
    Wait-ForAndroidBoot -Adb $Adb -Serial $Serial -TimeoutSec $BootTimeoutSec

    & $Adb -s $Serial shell settings put system accelerometer_rotation 0 | Out-Null
    & $Adb -s $Serial shell settings put system user_rotation 0 | Out-Null
    & $Adb -s $Serial shell settings put global window_animation_scale 0 | Out-Null
    & $Adb -s $Serial shell settings put global transition_animation_scale 0 | Out-Null
    & $Adb -s $Serial shell settings put global animator_duration_scale 0 | Out-Null
    & $Adb -s $Serial shell wm size $RequestedViewport | Out-Null
    & $Adb -s $Serial shell wm density $RequestedDensity | Out-Null

    Write-Section '5/6 - INSTALL, LAUNCH AND CAPTURE REAL APP EVIDENCE'
    $InstallOutput = & $Adb -s $Serial install -r $ApkPath 2>&1
    $InstallExitCode = $LASTEXITCODE
    $InstallText = (($InstallOutput | ForEach-Object { "$_" }) -join [Environment]::NewLine).Trim()
    $State.install_result = $InstallText
    if ($InstallExitCode -ne 0) {
        if ($InstallText -match 'INSTALL_FAILED_UPDATE_INCOMPATIBLE') {
            throw 'APK_SIGNATURE_MISMATCH: the dedicated AVD already has this package signed by a different validation key. The runner will NOT uninstall it automatically because that would erase app data.'
        }
        throw "ADB_INSTALL_FAILED ($InstallExitCode): $InstallText"
    }

    & $Adb -s $Serial shell am force-stop $PackageName | Out-Null
    $LaunchOutput = & $Adb -s $Serial shell monkey -p $PackageName -c android.intent.category.LAUNCHER 1 2>&1
    $LaunchExitCode = $LASTEXITCODE
    $LaunchText = (($LaunchOutput | ForEach-Object { "$_" }) -join [Environment]::NewLine).Trim()
    $State.launch_result = $LaunchText
    if ($LaunchExitCode -ne 0) { throw "APP_LAUNCH_FAILED ($LaunchExitCode): $LaunchText" }

    Start-Sleep -Seconds 10
    $AppProcessIdText = Invoke-NativeCapture -FilePath $Adb -Arguments @('-s', $Serial, 'shell', 'pidof', $PackageName)
    if (-not $AppProcessIdText.Trim()) { throw 'APP_PROCESS_NOT_RUNNING_AFTER_LAUNCH' }
    $State.process_id = $AppProcessIdText.Trim()

    $ScreenshotPath = Join-Path $OutputDir 'FITNEXUS_HOME_EXACT_SHA.png'
    $RemoteScreenshot = '/sdcard/FITNEXUS_HOME_EXACT_SHA.png'
    Invoke-Native -FilePath $Adb -Arguments @('-s', $Serial, 'shell', 'screencap', '-p', $RemoteScreenshot)
    Invoke-Native -FilePath $Adb -Arguments @('-s', $Serial, 'pull', $RemoteScreenshot, $ScreenshotPath)
    & $Adb -s $Serial shell rm -f $RemoteScreenshot | Out-Null
    if (-not (Test-PngFile -Path $ScreenshotPath)) { throw 'FITNEXUS_LOCAL_SCREENSHOT_INVALID_PNG' }
    $State.screenshot_path = $ScreenshotPath
    $State.screenshot_sha256 = (Get-FileHash -LiteralPath $ScreenshotPath -Algorithm SHA256).Hash.ToLowerInvariant()

    $UiDumpPath = Join-Path $OutputDir 'FITNEXUS_HOME_UI.xml'
    $RemoteUiDump = '/sdcard/fitnexus_ui.xml'
    & $Adb -s $Serial shell uiautomator dump $RemoteUiDump | Out-Null
    if ($LASTEXITCODE -eq 0) {
        & $Adb -s $Serial pull $RemoteUiDump $UiDumpPath | Out-Null
        if ($LASTEXITCODE -eq 0) { $State.ui_dump_path = $UiDumpPath }
        & $Adb -s $Serial shell rm -f $RemoteUiDump | Out-Null
    }

    $LogcatPath = Join-Path $OutputDir 'FITNEXUS_HOME_LOGCAT.txt'
    $LogcatOutput = & $Adb -s $Serial logcat -d -t 500 2>&1
    Write-Utf8NoBom -Path $LogcatPath -Content ((($LogcatOutput | ForEach-Object { "$_" }) -join [Environment]::NewLine) + [Environment]::NewLine)
    $State.logcat_path = $LogcatPath

    $DumpsysPath = Join-Path $OutputDir 'FITNEXUS_PACKAGE_DUMPSYS.txt'
    $DumpsysOutput = & $Adb -s $Serial shell dumpsys package $PackageName 2>&1
    Write-Utf8NoBom -Path $DumpsysPath -Content ((($DumpsysOutput | ForEach-Object { "$_" }) -join [Environment]::NewLine) + [Environment]::NewLine)
    $State.package_dumpsys_path = $DumpsysPath

    Write-Section '6/6 - FAIL-CLOSED HEAD REVALIDATION'
    $HeadAfter = Get-RemoteHead -Git $Git -Root $RepoRoot -RemoteBranch $Branch
    $State.remote_head_after = $HeadAfter
    if ($HeadAfter -ne $HeadSha) {
        throw "HEAD_MOVED_DURING_RUN: built $HeadSha but origin/$Branch is now $HeadAfter. Evidence is preserved but cannot be approved as current."
    }

    $State.status = 'PASS'
    $CoreSucceeded = $true
}
catch {
    $Failure = $_.Exception.Message
    $State.status = 'FAIL'
    $State.failure = $Failure
    Write-Host ''
    Write-Host "FITNEXUS_VISUAL_APPROVAL=FAIL"
    Write-Host $Failure
}
finally {
    if ($KeyPropertiesPath -and (Test-Path -LiteralPath $KeyPropertiesPath)) {
        Remove-Item -LiteralPath $KeyPropertiesPath -Force -ErrorAction SilentlyContinue
    }
    if ($WorktreeAdded -and $WorktreePath) {
        try {
            $GitForCleanup = Get-Command 'git.exe' -ErrorAction SilentlyContinue
            if ($null -eq $GitForCleanup) { $GitForCleanup = Get-Command 'git' -ErrorAction SilentlyContinue }
            if ($null -ne $GitForCleanup) {
                & $GitForCleanup.Source -C $RepoRoot worktree remove --force $WorktreePath 2>&1 | Out-Null
            }
        }
        catch { }
    }
    if ($WorktreePath -and (Test-Path -LiteralPath $WorktreePath)) {
        Remove-Item -LiteralPath $WorktreePath -Recurse -Force -ErrorAction SilentlyContinue
    }

    if ($ReceiptPath -and (Test-Path -LiteralPath (Split-Path -Parent $ReceiptPath))) {
        try {
            Write-Receipt
            if ($CoreSucceeded) {
                Compress-Archive -Path (Join-Path $OutputDir '*') -DestinationPath $ZipPath -CompressionLevel Optimal -Force
                $ZipHash = (Get-FileHash -LiteralPath $ZipPath -Algorithm SHA256).Hash.ToLowerInvariant()
                $State.zip_path = $ZipPath
                $State.zip_sha256 = $ZipHash
                Write-Utf8NoBom -Path $ZipHashPath -Content ("$ZipHash  $(Split-Path -Leaf $ZipPath)" + [Environment]::NewLine)
                Write-Receipt
            }
        }
        catch {
            $Failure = "EVIDENCE_PACKAGE_FAILURE: $($_.Exception.Message)"
            $State.status = 'FAIL'
            $State.failure = $Failure
            try { Write-Receipt } catch { }
        }
    }
}

if ($Failure) {
    Write-Host ''
    Write-Host "Receipt: $ReceiptPath"
    Write-Host 'The dedicated emulator was intentionally left open when it had already been started.'
    exit 1
}

Write-Host ''
Write-Host 'FITNEXUS_VISUAL_APPROVAL=PASS'
Write-Host "EXACT_SHA=$($State.source_commit_sha)"
Write-Host "AVD=$($State.avd_name) ($($State.emulator_serial))"
Write-Host "SCREENSHOT=$($State.screenshot_path)"
Write-Host "RECEIPT=$ReceiptPath"
Write-Host "ZIP=$ZipPath"
Write-Host "ZIP_SHA256=$($State.zip_sha256)"
Write-Host 'PLAY_PUBLICATION_PERFORMED=false'
Write-Host 'EMULATOR_LEFT_OPEN=true'
Write-Host ''
Write-Host 'Compare the REAL app now open in the FitNexus dedicated emulator with the approved premium mockup.'
exit 0
