param(
    [switch]$ValidateOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ToolDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AppRoot = (Resolve-Path (Join-Path $ToolDir '..')).Path
$RepoRoot = (Resolve-Path (Join-Path $AppRoot '..\..')).Path
$AndroidDir = Join-Path $AppRoot 'android'
$GradleFile = Join-Path $AndroidDir 'app\build.gradle.kts'
$ContractFile = Join-Path $AndroidDir 'PLAY_SIGNED_AAB_RUNNER_V1.json'
$KeyPropertiesFile = Join-Path $AndroidDir 'key.properties'
$GitPath = '03_app_flutter/fitnexus_app/android/key.properties'
$Marker = '# GENERATED_BY=FITNEXUS_PLAY_SIGNED_AAB_RUNNER_V1'
$UploadAlias = 'fitnexus_upload'
$ExternalRoot = Join-Path $env:USERPROFILE 'Documents\FitNexus_Coach_BlackGold_EXTERNAL\play_signing'
$AuthorityDir = Join-Path $ExternalRoot 'authority'
$CurrentDir = Join-Path $ExternalRoot 'current'
$KeystoreFile = Join-Path $AuthorityDir 'fitnexus-upload-key.jks'
$ProtectedSecretFile = Join-Path $AuthorityDir 'upload-key-secret.dpapi'

function Fail([string]$Message) {
    throw "FITNEXUS_SIGNED_AAB_RUNNER=FAIL::$Message"
}

function Assert-File([string]$Path, [string]$Name) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        Fail "missing::$Name"
    }
}

function Resolve-JavaTool([string]$Name) {
    if ($env:JAVA_HOME) {
        $candidate = Join-Path $env:JAVA_HOME "bin\$Name.exe"
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return $candidate
        }
    }
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($null -ne $command) {
        return $command.Source
    }
    Fail "java_tool_not_found::$Name"
}

function New-StrongPassword {
    $bytes = New-Object byte[] 32
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $rng.GetBytes($bytes)
    }
    finally {
        $rng.Dispose()
    }
    $base = [Convert]::ToBase64String($bytes).Replace('+', 'A').Replace('/', 'B').TrimEnd('=')
    return ($base + '!9aZ')
}

function Write-Utf8NoBom([string]$Path, [string]$Content) {
    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content, $encoding)
}

function Assert-KeyPropertiesGitBoundary {
    Push-Location $RepoRoot
    try {
        & git check-ignore -q -- $GitPath
        if ($LASTEXITCODE -ne 0) {
            Fail 'key_properties_not_gitignored'
        }

        & git ls-files --error-unmatch -- $GitPath 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Fail 'key_properties_is_tracked'
        }
    }
    finally {
        Pop-Location
    }
}

Assert-File $GradleFile 'android/app/build.gradle.kts'
Assert-File $ContractFile 'android/PLAY_SIGNED_AAB_RUNNER_V1.json'

$gradle = Get-Content -LiteralPath $GradleFile -Raw
$contract = Get-Content -LiteralPath $ContractFile -Raw | ConvertFrom-Json
if ($gradle -notmatch 'rootProject\.file\("key\.properties"\)') {
    Fail 'gradle_external_key_properties_wiring_missing'
}
if ($gradle -match 'signingConfigs\.getByName\("debug"\)') {
    Fail 'debug_release_signing_regression'
}
if (-not $contract.runner.single_command_required) {
    Fail 'contract_single_command_required_false'
}
if ($contract.secret_boundary.persistent_password_storage -ne 'WINDOWS_DPAPI_CURRENT_USER') {
    Fail 'contract_dpapi_boundary_missing'
}

Assert-KeyPropertiesGitBoundary

if ($ValidateOnly) {
    Write-Output 'FITNEXUS_SIGNED_AAB_RUNNER=VALIDATE_ONLY_PASS'
    Write-Output 'UPLOAD_KEY_CREATED=false'
    Write-Output 'SIGNED_AAB_CREATED=false'
    Write-Output 'PLAY_UPLOAD_PERFORMED=false'
    exit 0
}

if ($env:OS -ne 'Windows_NT') {
    Fail 'execution_requires_windows_for_dpapi_secret_storage'
}

$flutter = Get-Command flutter -ErrorAction SilentlyContinue
if ($null -eq $flutter) {
    Fail 'flutter_not_found'
}
$keytool = Resolve-JavaTool 'keytool'
$jarsigner = Resolve-JavaTool 'jarsigner'

New-Item -ItemType Directory -Force -Path $AuthorityDir | Out-Null
New-Item -ItemType Directory -Force -Path $CurrentDir | Out-Null

$keystoreExists = Test-Path -LiteralPath $KeystoreFile -PathType Leaf
$secretExists = Test-Path -LiteralPath $ProtectedSecretFile -PathType Leaf
if ($keystoreExists -xor $secretExists) {
    Fail 'external_signing_authority_incomplete_keystore_secret_pair'
}

$plainPassword = $null
$createdKey = $false
try {
    if (-not $keystoreExists) {
        $plainPassword = New-StrongPassword
        $env:FNX_UPLOAD_KEY_PASS = $plainPassword

        & $keytool -genkeypair -noprompt -v `
            -keystore $KeystoreFile `
            -storetype JKS `
            -alias $UploadAlias `
            -keyalg RSA `
            -keysize 4096 `
            -validity 10000 `
            -dname 'CN=FitNexus Coach BlackGold, OU=La Famiglia PlayWorks, O=Projetos Cosa Nostra, C=BR' `
            '-storepass:env' 'FNX_UPLOAD_KEY_PASS' `
            '-keypass:env' 'FNX_UPLOAD_KEY_PASS'
        if ($LASTEXITCODE -ne 0) {
            Fail 'keytool_genkeypair_failed'
        }

        $secure = ConvertTo-SecureString $plainPassword -AsPlainText -Force
        $protected = ConvertFrom-SecureString $secure
        Write-Utf8NoBom $ProtectedSecretFile $protected
        $createdKey = $true
    }
    else {
        $protected = (Get-Content -LiteralPath $ProtectedSecretFile -Raw).Trim()
        $secure = ConvertTo-SecureString $protected
        $credential = New-Object System.Net.NetworkCredential('', $secure)
        $plainPassword = $credential.Password
        if ([string]::IsNullOrWhiteSpace($plainPassword)) {
            Fail 'dpapi_secret_decryption_empty'
        }
        $env:FNX_UPLOAD_KEY_PASS = $plainPassword
    }

    if (Test-Path -LiteralPath $KeyPropertiesFile -PathType Leaf) {
        $existingKeyProperties = Get-Content -LiteralPath $KeyPropertiesFile -Raw
        if ($existingKeyProperties -notmatch [regex]::Escape($Marker)) {
            Fail 'existing_key_properties_not_owned_by_runner'
        }
    }

    $storePathForGradle = $KeystoreFile.Replace('\', '/')
    $keyProperties = @(
        $Marker,
        "storePassword=$plainPassword",
        "keyPassword=$plainPassword",
        "keyAlias=$UploadAlias",
        "storeFile=$storePathForGradle"
    ) -join [Environment]::NewLine
    Write-Utf8NoBom $KeyPropertiesFile ($keyProperties + [Environment]::NewLine)
    Assert-KeyPropertiesGitBoundary

    Get-ChildItem -LiteralPath $CurrentDir -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force

    Push-Location $AppRoot
    try {
        & flutter pub get
        if ($LASTEXITCODE -ne 0) { Fail 'flutter_pub_get_failed' }

        & python tool/verify_play_release_preflight.py --mode inventory
        if ($LASTEXITCODE -ne 0) { Fail 'play_preflight_inventory_failed' }

        & flutter analyze
        if ($LASTEXITCODE -ne 0) { Fail 'flutter_analyze_failed' }

        & flutter test
        if ($LASTEXITCODE -ne 0) { Fail 'flutter_test_failed' }

        & flutter build appbundle --release
        if ($LASTEXITCODE -ne 0) { Fail 'flutter_build_appbundle_failed' }
    }
    finally {
        Pop-Location
    }

    $aab = Join-Path $AppRoot 'build\app\outputs\bundle\release\app-release.aab'
    Assert-File $aab 'signed_release_aab'

    $verifyLog = Join-Path $CurrentDir 'JARSIGNER_VERIFY.txt'
    & $jarsigner -verify -verbose -certs $aab 2>&1 | Out-File -LiteralPath $verifyLog -Encoding utf8
    if ($LASTEXITCODE -ne 0) {
        Fail 'jarsigner_verification_failed'
    }

    $pubspec = Get-Content -LiteralPath (Join-Path $AppRoot 'pubspec.yaml') -Raw
    $versionMatch = [regex]::Match($pubspec, '(?m)^version:\s*([^\s]+)')
    $version = if ($versionMatch.Success) { $versionMatch.Groups[1].Value } else { 'UNKNOWN' }
    $safeVersion = $version.Replace('+', '_').Replace('.', '_')
    $publishedAab = Join-Path $CurrentDir "FitNexus_Coach_BlackGold_${safeVersion}_SIGNED.aab"
    Copy-Item -LiteralPath $aab -Destination $publishedAab -Force

    $hash = (Get-FileHash -LiteralPath $publishedAab -Algorithm SHA256).Hash.ToLowerInvariant()
    $bytes = (Get-Item -LiteralPath $publishedAab).Length
    $receipt = [ordered]@{
        schema_version = 1
        kind = 'FITNEXUS_SIGNED_AAB_LOCAL_PROOF'
        generated_at_utc = [DateTime]::UtcNow.ToString('o')
        application_id = 'br.com.lafamigliaplayworks.fitnexuscoach'
        version = $version
        upload_alias = $UploadAlias
        upload_key_created_this_run = $createdKey
        upload_key_storage = 'EXTERNAL_AUTHORITY_DIRECTORY'
        password_storage = 'WINDOWS_DPAPI_CURRENT_USER'
        signed_aab_path = $publishedAab
        signed_aab_bytes = $bytes
        signed_aab_sha256 = $hash
        jarsigner_verified = $true
        play_console_uniqueness_attested = $false
        play_app_signing_enrollment_attested = $false
        play_upload_authorized = $false
        play_upload_performed = $false
        production_release_performed = $false
    }
    $receiptPath = Join-Path $CurrentDir 'FITNEXUS_PLAY_SIGNED_AAB_RECEIPT_V1.json'
    Write-Utf8NoBom $receiptPath (($receipt | ConvertTo-Json -Depth 5) + [Environment]::NewLine)

    Write-Output 'FITNEXUS_SIGNED_AAB_RUNNER=PASS'
    Write-Output "SIGNED_AAB=$publishedAab"
    Write-Output "SIGNED_AAB_SHA256=$hash"
    Write-Output "RECEIPT=$receiptPath"
    Write-Output 'PLAY_UPLOAD_PERFORMED=false'
}
finally {
    if (Test-Path -LiteralPath $KeyPropertiesFile -PathType Leaf) {
        $owned = Get-Content -LiteralPath $KeyPropertiesFile -Raw -ErrorAction SilentlyContinue
        if ($owned -match [regex]::Escape($Marker)) {
            Remove-Item -LiteralPath $KeyPropertiesFile -Force
        }
    }
    Remove-Item Env:FNX_UPLOAD_KEY_PASS -ErrorAction SilentlyContinue
    $plainPassword = $null
}
