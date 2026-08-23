[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Repository = 'ProjetosCosaNostra/FitNexus_Coach_BlackGold'
$ProjectRef = 'mceukeondizkwlpfxzgf'
$FailureClassCli = 'BGF-STAGE35-ALERT-SECRET-BOOTSTRAP-CLI-PREREQUISITE-293'
$FailureClassTransport = 'BGF-STAGE35-ALERT-SECRET-BOOTSTRAP-PLAINTEXT-TRANSPORT-294'
$FailureClassPartial = 'BGF-STAGE35-ALERT-SECRET-BOOTSTRAP-PARTIAL-WRITE-295'
$FailureClassObservation = 'BGF-STAGE35-ALERT-SECRET-BOOTSTRAP-SET-READBACK-DIVERGENCE-299'
$FailureClassJsonArray = 'BGF-STAGE35-ALERT-SECRET-BULK-JSON-ARRAY-PIPELINE-300'

$RuntimeNames = @(
  'STUDENT_ACCESS_ALERT_DISPATCH_TOKEN',
  'STUDENT_ACCESS_ALERT_TELEGRAM_BOT_TOKEN',
  'STUDENT_ACCESS_ALERT_TELEGRAM_CHAT_ID'
)
$GitHubNames = @(
  'SUPABASE_ACCESS_TOKEN',
  'STUDENT_ACCESS_ALERT_DISPATCH_TOKEN',
  'STUDENT_ACCESS_ALERT_TELEGRAM_BOT_TOKEN',
  'STUDENT_ACCESS_ALERT_TELEGRAM_CHAT_ID'
)

function Fail-Closed {
  param([string]$FailureClass,[string]$Code)
  Write-Error "STAGE35_ALERT_SECRET_BOOTSTRAP_V4=FAIL FAILURE_CLASS=$FailureClass CODE=$Code"
  exit 1
}

function To-Plain {
  param([Security.SecureString]$SecureValue)
  $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecureValue)
  try { [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
  finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
}

function Read-Secret {
  param([string]$EnvironmentName,[string]$Prompt)
  $existing = [Environment]::GetEnvironmentVariable($EnvironmentName,'Process')
  if (-not [string]::IsNullOrWhiteSpace($existing)) { return $existing }
  $plain = To-Plain (Read-Host -Prompt $Prompt -AsSecureString)
  if ([string]::IsNullOrWhiteSpace($plain)) {
    Fail-Closed $FailureClassTransport "EMPTY_$EnvironmentName"
  }
  return $plain
}

function Assert-SingleLine {
  param([string]$Name,[string]$Value)
  if ([string]::IsNullOrWhiteSpace($Value)) { Fail-Closed $FailureClassTransport "EMPTY_$Name" }
  if ($Value.Contains("`r") -or $Value.Contains("`n") -or $Value.Contains([char]0)) {
    Fail-Closed $FailureClassTransport "MULTILINE_OR_NUL_$Name"
  }
}

function New-DispatchToken {
  $bytes = New-Object byte[] 32
  $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
  try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
  ([Convert]::ToBase64String($bytes)).TrimEnd('=').Replace('+','-').Replace('/','_')
}

function Set-GitHubSecretFromStdin {
  param([string]$Name,[string]$Value)
  $null = $Value | & $script:GhCommand secret set $Name --repo $Repository 2>&1
  if ($LASTEXITCODE -ne 0) { Fail-Closed $FailureClassPartial "GITHUB_SECRET_SET_FAILED_$Name" }
}

$gh = Get-Command gh -ErrorAction SilentlyContinue
if ($null -eq $gh) { Fail-Closed $FailureClassCli 'GH_CLI_NOT_FOUND' }
$script:GhCommand = $gh.Source
$null = & $script:GhCommand auth status --hostname github.com 2>&1
if ($LASTEXITCODE -ne 0) { Fail-Closed $FailureClassCli 'GH_AUTH_REQUIRED' }
$repoProbe = & $script:GhCommand repo view $Repository --json nameWithOwner --jq '.nameWithOwner' 2>&1
if ($LASTEXITCODE -ne 0 -or (($repoProbe | Select-Object -First 1) -ne $Repository)) {
  Fail-Closed $FailureClassCli 'GH_REPOSITORY_ACCESS_NOT_PROVEN'
}

$supabaseAccessToken = Read-Secret 'SUPABASE_ACCESS_TOKEN' 'Supabase access token'
$telegramBotToken = Read-Secret 'STUDENT_ACCESS_ALERT_TELEGRAM_BOT_TOKEN' 'Telegram bot token'
$telegramChatId = Read-Secret 'STUDENT_ACCESS_ALERT_TELEGRAM_CHAT_ID' 'Telegram destination chat ID'
$dispatchToken = New-DispatchToken

Assert-SingleLine 'SUPABASE_ACCESS_TOKEN' $supabaseAccessToken
Assert-SingleLine 'STUDENT_ACCESS_ALERT_TELEGRAM_BOT_TOKEN' $telegramBotToken
Assert-SingleLine 'STUDENT_ACCESS_ALERT_TELEGRAM_CHAT_ID' $telegramChatId
Assert-SingleLine 'STUDENT_ACCESS_ALERT_DISPATCH_TOKEN' $dispatchToken
if ($telegramChatId -notmatch '^-?[0-9]+$') { Fail-Closed $FailureClassTransport 'TELEGRAM_CHAT_ID_NOT_NUMERIC' }
if ($telegramBotToken.Length -lt 20) { Fail-Closed $FailureClassTransport 'TELEGRAM_BOT_TOKEN_TOO_SHORT' }

$headers = @{ Authorization = "Bearer $supabaseAccessToken" }
try {
  $projectProbe = Invoke-RestMethod -Method Get -Uri "https://api.supabase.com/v1/projects/$ProjectRef" -Headers $headers
} catch {
  Fail-Closed $FailureClassCli 'SUPABASE_MANAGEMENT_TOKEN_PROJECT_ACCESS_NOT_PROVEN'
}
if ($null -eq $projectProbe -or [string]$projectProbe.id -ne $ProjectRef) {
  Fail-Closed $FailureClassCli 'SUPABASE_PROJECT_ACCESS_MISMATCH'
}

# V3 fed a PowerShell array into ConvertTo-Json through the pipeline. PowerShell
# enumerates native arrays on pipeline input, so that construction does not
# prove one JSON array document. The Management API bulk endpoint requires one
# JSON array of {name,value} objects. V4 binds the array through -InputObject
# and fail-closes unless the resulting body is exactly one string containing
# an array with the three expected names.
$secretObjects = [object[]]@(
  [ordered]@{ name = 'STUDENT_ACCESS_ALERT_DISPATCH_TOKEN'; value = $dispatchToken },
  [ordered]@{ name = 'STUDENT_ACCESS_ALERT_TELEGRAM_BOT_TOKEN'; value = $telegramBotToken },
  [ordered]@{ name = 'STUDENT_ACCESS_ALERT_TELEGRAM_CHAT_ID'; value = $telegramChatId }
)
$secretBody = ConvertTo-Json -InputObject $secretObjects -Depth 4 -Compress
if (-not ($secretBody -is [string])) {
  Fail-Closed $FailureClassJsonArray 'SECRET_BODY_NOT_SINGLE_STRING'
}
$trimmedBody = $secretBody.Trim()
if (-not $trimmedBody.StartsWith('[') -or -not $trimmedBody.EndsWith(']')) {
  Fail-Closed $FailureClassJsonArray 'SECRET_BODY_NOT_JSON_ARRAY_DOCUMENT'
}
try {
  $shapeProbe = @($secretBody | ConvertFrom-Json)
} catch {
  Fail-Closed $FailureClassJsonArray 'SECRET_BODY_JSON_PARSE_FAILED'
}
if ($shapeProbe.Count -ne 3) {
  Fail-Closed $FailureClassJsonArray 'SECRET_BODY_ITEM_COUNT_NOT_THREE'
}
$shapeNames = @($shapeProbe | ForEach-Object { [string]$_.name })
foreach ($name in $RuntimeNames) {
  if ($shapeNames -notcontains $name) {
    Fail-Closed $FailureClassJsonArray "SECRET_BODY_NAME_MISSING_$name"
  }
}

$runtimeWritten = $false
$githubWritten = $false
try {
  $null = Invoke-RestMethod -Method Post -Uri "https://api.supabase.com/v1/projects/$ProjectRef/secrets" -Headers $headers -ContentType 'application/json' -Body $secretBody
  $runtimeWritten = $true
} catch {
  Fail-Closed $FailureClassPartial 'SUPABASE_RUNTIME_SECRET_MANAGEMENT_API_WRITE_FAILED'
}

$observedNames = @()
$readbackVerified = $false
for ($attempt = 1; $attempt -le 12; $attempt++) {
  if ($attempt -gt 1) { Start-Sleep -Seconds 2 }
  try {
    $secretProbe = @(Invoke-RestMethod -Method Get -Uri "https://api.supabase.com/v1/projects/$ProjectRef/secrets" -Headers $headers)
  } catch {
    if ($attempt -eq 12) {
      Fail-Closed $FailureClassObservation 'SUPABASE_RUNTIME_SECRET_NAME_OBSERVATION_FAILED'
    }
    continue
  }

  $observedNames = @($secretProbe | ForEach-Object {
    if ($null -ne $_ -and $_.PSObject.Properties.Name -contains 'name') { [string]$_.name }
  })
  $missing = @($RuntimeNames | Where-Object { $observedNames -notcontains $_ })
  if ($missing.Count -eq 0) {
    $readbackVerified = $true
    break
  }
}
if (-not $readbackVerified) {
  Fail-Closed $FailureClassObservation 'SUPABASE_RUNTIME_SECRET_NAMES_NOT_VISIBLE_AFTER_BOUNDED_READBACK'
}

Set-GitHubSecretFromStdin 'SUPABASE_ACCESS_TOKEN' $supabaseAccessToken
Set-GitHubSecretFromStdin 'STUDENT_ACCESS_ALERT_DISPATCH_TOKEN' $dispatchToken
Set-GitHubSecretFromStdin 'STUDENT_ACCESS_ALERT_TELEGRAM_BOT_TOKEN' $telegramBotToken
Set-GitHubSecretFromStdin 'STUDENT_ACCESS_ALERT_TELEGRAM_CHAT_ID' $telegramChatId
$githubWritten = $true

$githubSecretList = @(& $script:GhCommand secret list --repo $Repository 2>&1 | ForEach-Object { [string]$_ })
if ($LASTEXITCODE -ne 0) { Fail-Closed $FailureClassPartial 'GITHUB_SECRET_LIST_FAILED_AFTER_WRITE' }
$joined = $githubSecretList -join "`n"
foreach ($name in $GitHubNames) {
  if ($joined -notmatch [regex]::Escape($name)) {
    Fail-Closed $FailureClassPartial "GITHUB_ACTIONS_SECRET_MISSING_$name"
  }
}

if (-not $runtimeWritten -or -not $githubWritten -or -not $readbackVerified) {
  Fail-Closed $FailureClassPartial 'SECRET_BOOTSTRAP_NOT_COMPLETE'
}

Remove-Variable secretBody,secretObjects,shapeProbe,shapeNames,dispatchToken,telegramBotToken,telegramChatId,supabaseAccessToken -ErrorAction SilentlyContinue

Write-Host 'STAGE35_ALERT_SECRET_BOOTSTRAP_V4=PASS'
Write-Host 'SECRET_BULK_JSON_ARRAY_SHAPE=PASS'
Write-Host 'GITHUB_ACTIONS_SECRET_NAMES_VERIFIED=4/4'
Write-Host 'SUPABASE_EDGE_RUNTIME_SECRET_NAMES_VERIFIED=3/3'
Write-Host 'RUNTIME_SECRET_WRITE=SUPABASE_MANAGEMENT_API_EXACT_ARRAY_BODY'
Write-Host 'RUNTIME_SECRET_VERIFICATION=SUPABASE_MANAGEMENT_API_NAMES_ONLY_BOUNDED_RETRY'
Write-Host 'SECRET_VALUES_PRINTED=false'
Write-Host 'SECRET_VALUES_STORED_IN_REPOSITORY=false'
Write-Host 'TEMP_SECRET_FILE_CREATED=false'
Write-Host 'DATABASE_MIGRATION_APPLIED=false'
Write-Host 'EDGE_FUNCTION_DEPLOYED=false'
Write-Host 'TELEGRAM_PROVIDER_CALLED=false'
Write-Host 'ONE_SHOT_EXTERNAL_DELIVERY_PROOF_CONSUMED=false'
Write-Host 'NEXT_ACTION=RERUN_STAGE35_ALERT_RUNTIME_SECRET_READINESS'
