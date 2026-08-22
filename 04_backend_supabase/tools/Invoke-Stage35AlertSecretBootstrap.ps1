[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Repository = 'ProjetosCosaNostra/FitNexus_Coach_BlackGold'
$ProjectRef = 'mceukeondizkwlpfxzgf'
$FailureClassCli = 'BGF-STAGE35-ALERT-SECRET-BOOTSTRAP-CLI-PREREQUISITE-293'
$FailureClassTransport = 'BGF-STAGE35-ALERT-SECRET-BOOTSTRAP-PLAINTEXT-TRANSPORT-294'
$FailureClassPartial = 'BGF-STAGE35-ALERT-SECRET-BOOTSTRAP-PARTIAL-WRITE-295'
$FailureClassResidue = 'BGF-STAGE35-ALERT-SECRET-BOOTSTRAP-LOCAL-RESIDUE-296'

$SupabaseRuntimeSecretNames = @(
    'STUDENT_ACCESS_ALERT_DISPATCH_TOKEN',
    'STUDENT_ACCESS_ALERT_TELEGRAM_BOT_TOKEN',
    'STUDENT_ACCESS_ALERT_TELEGRAM_CHAT_ID'
)
$GitHubSecretNames = @(
    'SUPABASE_ACCESS_TOKEN',
    'STUDENT_ACCESS_ALERT_DISPATCH_TOKEN',
    'STUDENT_ACCESS_ALERT_TELEGRAM_BOT_TOKEN',
    'STUDENT_ACCESS_ALERT_TELEGRAM_CHAT_ID'
)

function Fail-Closed {
    param(
        [Parameter(Mandatory = $true)][string]$FailureClass,
        [Parameter(Mandatory = $true)][string]$Code
    )
    Write-Error "STAGE35_ALERT_SECRET_BOOTSTRAP=FAIL FAILURE_CLASS=$FailureClass CODE=$Code"
    exit 1
}

function ConvertFrom-SecureStringPlainText {
    param([Parameter(Mandatory = $true)][Security.SecureString]$SecureValue)
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecureValue)
    try {
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    }
}

function Read-SecretMaterial {
    param(
        [Parameter(Mandatory = $true)][string]$EnvironmentName,
        [Parameter(Mandatory = $true)][string]$Prompt
    )

    $existing = [Environment]::GetEnvironmentVariable($EnvironmentName, 'Process')
    if (-not [string]::IsNullOrWhiteSpace($existing)) {
        return $existing
    }

    $secure = Read-Host -Prompt $Prompt -AsSecureString
    $plain = ConvertFrom-SecureStringPlainText -SecureValue $secure
    if ([string]::IsNullOrWhiteSpace($plain)) {
        Fail-Closed -FailureClass $FailureClassTransport -Code "EMPTY_$EnvironmentName"
    }
    return $plain
}

function Assert-SingleLineSecret {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$Value
    )
    if ([string]::IsNullOrWhiteSpace($Value)) {
        Fail-Closed -FailureClass $FailureClassTransport -Code "EMPTY_$Name"
    }
    if ($Value.Contains("`r") -or $Value.Contains("`n") -or $Value.Contains([char]0)) {
        Fail-Closed -FailureClass $FailureClassTransport -Code "MULTILINE_OR_NUL_$Name"
    }
}

function New-DispatchToken {
    $bytes = New-Object byte[] 32
    $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $rng.GetBytes($bytes)
    }
    finally {
        $rng.Dispose()
    }
    return ([Convert]::ToBase64String($bytes)).TrimEnd('=').Replace('+', '-').Replace('/', '_')
}

function Invoke-SupabaseCli {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)

    if ($script:SupabaseCommandKind -eq 'direct') {
        $output = & $script:SupabaseCommand @Arguments 2>&1
    }
    else {
        $output = & $script:SupabaseCommand --yes 'supabase@latest' @Arguments 2>&1
    }
    $exitCode = $LASTEXITCODE
    return [pscustomobject]@{
        ExitCode = $exitCode
        Output = @($output | ForEach-Object { [string]$_ })
    }
}

function Set-GitHubSecretFromStdin {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$Value
    )

    $output = $Value | & $script:GhCommand secret set $Name --repo $Repository 2>&1
    if ($LASTEXITCODE -ne 0) {
        Fail-Closed -FailureClass $FailureClassPartial -Code "GITHUB_SECRET_SET_FAILED_$Name"
    }
    $null = $output
}

function Assert-NamesPresent {
    param(
        [Parameter(Mandatory = $true)][string[]]$RequiredNames,
        [Parameter(Mandatory = $true)][string[]]$ObservedLines,
        [Parameter(Mandatory = $true)][string]$FailurePrefix
    )

    $joined = $ObservedLines -join "`n"
    foreach ($name in $RequiredNames) {
        if ($joined -notmatch [regex]::Escape($name)) {
            Fail-Closed -FailureClass $FailureClassPartial -Code "${FailurePrefix}_MISSING_$name"
        }
    }
}

# Toolchain preflight happens before any secret mutation.
$gh = Get-Command gh -ErrorAction SilentlyContinue
if ($null -eq $gh) {
    Fail-Closed -FailureClass $FailureClassCli -Code 'GH_CLI_NOT_FOUND'
}
$script:GhCommand = $gh.Source

$ghAuth = & $script:GhCommand auth status --hostname github.com 2>&1
if ($LASTEXITCODE -ne 0) {
    $null = $ghAuth
    Fail-Closed -FailureClass $FailureClassCli -Code 'GH_AUTH_REQUIRED'
}
$repoProbe = & $script:GhCommand repo view $Repository --json nameWithOwner --jq '.nameWithOwner' 2>&1
if ($LASTEXITCODE -ne 0 -or (($repoProbe | Select-Object -First 1) -ne $Repository)) {
    Fail-Closed -FailureClass $FailureClassCli -Code 'GH_REPOSITORY_ACCESS_NOT_PROVEN'
}

$supabase = Get-Command supabase -ErrorAction SilentlyContinue
if ($null -ne $supabase) {
    $script:SupabaseCommandKind = 'direct'
    $script:SupabaseCommand = $supabase.Source
}
else {
    $npx = Get-Command npx -ErrorAction SilentlyContinue
    if ($null -eq $npx) {
        Fail-Closed -FailureClass $FailureClassCli -Code 'SUPABASE_CLI_AND_NPX_NOT_FOUND'
    }
    $script:SupabaseCommandKind = 'npx'
    $script:SupabaseCommand = $npx.Source
}

$versionProbe = Invoke-SupabaseCli -Arguments @('--version')
if ($versionProbe.ExitCode -ne 0) {
    Fail-Closed -FailureClass $FailureClassCli -Code 'SUPABASE_CLI_NOT_EXECUTABLE'
}

# Secret values are read from process environment when already supplied, otherwise from
# secure prompts. No secret value is accepted as a command-line parameter.
$supabaseAccessToken = Read-SecretMaterial -EnvironmentName 'SUPABASE_ACCESS_TOKEN' -Prompt 'Supabase access token'
$telegramBotToken = Read-SecretMaterial -EnvironmentName 'STUDENT_ACCESS_ALERT_TELEGRAM_BOT_TOKEN' -Prompt 'Telegram bot token'
$telegramChatId = Read-SecretMaterial -EnvironmentName 'STUDENT_ACCESS_ALERT_TELEGRAM_CHAT_ID' -Prompt 'Telegram destination chat ID'
$dispatchToken = New-DispatchToken

Assert-SingleLineSecret -Name 'SUPABASE_ACCESS_TOKEN' -Value $supabaseAccessToken
Assert-SingleLineSecret -Name 'STUDENT_ACCESS_ALERT_TELEGRAM_BOT_TOKEN' -Value $telegramBotToken
Assert-SingleLineSecret -Name 'STUDENT_ACCESS_ALERT_TELEGRAM_CHAT_ID' -Value $telegramChatId
Assert-SingleLineSecret -Name 'STUDENT_ACCESS_ALERT_DISPATCH_TOKEN' -Value $dispatchToken

if ($telegramChatId -notmatch '^-?[0-9]+$') {
    Fail-Closed -FailureClass $FailureClassTransport -Code 'TELEGRAM_CHAT_ID_NOT_NUMERIC'
}
if ($telegramBotToken.Length -lt 20) {
    Fail-Closed -FailureClass $FailureClassTransport -Code 'TELEGRAM_BOT_TOKEN_TOO_SHORT'
}

# Prove the Supabase management token can access the exact project before mutating either
# secret store. The response body is never printed.
try {
    $headers = @{ Authorization = "Bearer $supabaseAccessToken" }
    $projectProbe = Invoke-RestMethod -Method Get -Uri "https://api.supabase.com/v1/projects/$ProjectRef" -Headers $headers
    if ($null -eq $projectProbe -or [string]$projectProbe.id -ne $ProjectRef) {
        Fail-Closed -FailureClass $FailureClassCli -Code 'SUPABASE_PROJECT_ACCESS_MISMATCH'
    }
}
catch {
    Fail-Closed -FailureClass $FailureClassCli -Code 'SUPABASE_MANAGEMENT_TOKEN_PROJECT_ACCESS_NOT_PROVEN'
}

$oldSupabaseAccessToken = [Environment]::GetEnvironmentVariable('SUPABASE_ACCESS_TOKEN', 'Process')
$tempEnvFile = $null
$runtimeSecretsWritten = $false
$githubSecretsWritten = $false

try {
    # Supabase CLI officially supports production secret loading from an env file. The file
    # lives only in the OS temp directory, outside the repository, and is removed in finally.
    $tempEnvFile = Join-Path ([IO.Path]::GetTempPath()) ("fitnexus-stage35-alert-secrets-{0}.env" -f ([Guid]::NewGuid().ToString('N')))
    $envText = @(
        "STUDENT_ACCESS_ALERT_DISPATCH_TOKEN=$dispatchToken",
        "STUDENT_ACCESS_ALERT_TELEGRAM_BOT_TOKEN=$telegramBotToken",
        "STUDENT_ACCESS_ALERT_TELEGRAM_CHAT_ID=$telegramChatId"
    ) -join "`n"
    [IO.File]::WriteAllText($tempEnvFile, $envText, (New-Object Text.UTF8Encoding($false)))

    [Environment]::SetEnvironmentVariable('SUPABASE_ACCESS_TOKEN', $supabaseAccessToken, 'Process')

    $setRuntime = Invoke-SupabaseCli -Arguments @('secrets', 'set', '--project-ref', $ProjectRef, '--env-file', $tempEnvFile)
    if ($setRuntime.ExitCode -ne 0) {
        Fail-Closed -FailureClass $FailureClassPartial -Code 'SUPABASE_RUNTIME_SECRET_SET_FAILED'
    }
    $runtimeSecretsWritten = $true

    $listRuntime = Invoke-SupabaseCli -Arguments @('secrets', 'list', '--project-ref', $ProjectRef)
    if ($listRuntime.ExitCode -ne 0) {
        Fail-Closed -FailureClass $FailureClassPartial -Code 'SUPABASE_RUNTIME_SECRET_LIST_FAILED_AFTER_WRITE'
    }
    Assert-NamesPresent -RequiredNames $SupabaseRuntimeSecretNames -ObservedLines $listRuntime.Output -FailurePrefix 'SUPABASE_RUNTIME_SECRET'

    # GitHub values are streamed over stdin to gh; no secret value appears in process args.
    Set-GitHubSecretFromStdin -Name 'SUPABASE_ACCESS_TOKEN' -Value $supabaseAccessToken
    Set-GitHubSecretFromStdin -Name 'STUDENT_ACCESS_ALERT_DISPATCH_TOKEN' -Value $dispatchToken
    Set-GitHubSecretFromStdin -Name 'STUDENT_ACCESS_ALERT_TELEGRAM_BOT_TOKEN' -Value $telegramBotToken
    Set-GitHubSecretFromStdin -Name 'STUDENT_ACCESS_ALERT_TELEGRAM_CHAT_ID' -Value $telegramChatId
    $githubSecretsWritten = $true

    $githubSecretList = & $script:GhCommand secret list --repo $Repository 2>&1
    if ($LASTEXITCODE -ne 0) {
        Fail-Closed -FailureClass $FailureClassPartial -Code 'GITHUB_SECRET_LIST_FAILED_AFTER_WRITE'
    }
    Assert-NamesPresent -RequiredNames $GitHubSecretNames -ObservedLines @($githubSecretList | ForEach-Object { [string]$_ }) -FailurePrefix 'GITHUB_ACTIONS_SECRET'
}
finally {
    [Environment]::SetEnvironmentVariable('SUPABASE_ACCESS_TOKEN', $oldSupabaseAccessToken, 'Process')
    if ($null -ne $tempEnvFile -and (Test-Path -LiteralPath $tempEnvFile)) {
        Remove-Item -LiteralPath $tempEnvFile -Force -ErrorAction SilentlyContinue
    }
}

if ($null -ne $tempEnvFile -and (Test-Path -LiteralPath $tempEnvFile)) {
    Fail-Closed -FailureClass $FailureClassResidue -Code 'TEMP_SECRET_ENV_FILE_REMAINS'
}
if (-not $runtimeSecretsWritten -or -not $githubSecretsWritten) {
    Fail-Closed -FailureClass $FailureClassPartial -Code 'SECRET_BOOTSTRAP_NOT_COMPLETE'
}

Write-Host 'STAGE35_ALERT_SECRET_BOOTSTRAP=PASS'
Write-Host 'GITHUB_ACTIONS_SECRET_NAMES_VERIFIED=4/4'
Write-Host 'SUPABASE_EDGE_RUNTIME_SECRET_NAMES_VERIFIED=3/3'
Write-Host 'DISPATCH_TOKEN_GENERATED_LOCALLY=true'
Write-Host 'SECRET_VALUES_PRINTED=false'
Write-Host 'SECRET_VALUES_STORED_IN_REPOSITORY=false'
Write-Host 'TEMP_SECRET_FILE_RESIDUE=false'
Write-Host 'DATABASE_MIGRATION_APPLIED=false'
Write-Host 'EDGE_FUNCTION_DEPLOYED=false'
Write-Host 'TELEGRAM_PROVIDER_CALLED=false'
Write-Host 'ONE_SHOT_EXTERNAL_DELIVERY_PROOF_CONSUMED=false'
Write-Host 'NEXT_ACTION=RERUN_STAGE35_ALERT_RUNTIME_SECRET_READINESS'
