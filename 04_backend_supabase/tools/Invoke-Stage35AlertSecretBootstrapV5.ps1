[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Repository = 'ProjetosCosaNostra/FitNexus_Coach_BlackGold'
$ProjectRef = 'mceukeondizkwlpfxzgf'
$FailureClassCli = 'BGF-STAGE35-ALERT-SECRET-BOOTSTRAP-CLI-PREREQUISITE-293'
$FailureClassTransport = 'BGF-STAGE35-ALERT-SECRET-BOOTSTRAP-PLAINTEXT-TRANSPORT-294'
$FailureClassPartial = 'BGF-STAGE35-ALERT-SECRET-BOOTSTRAP-PARTIAL-WRITE-295'
$FailureClassReadback = 'BGF-STAGE35-ALERT-SECRET-READBACK-TOPLEVEL-ARRAY-NESTING-301'

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
  Write-Error "STAGE35_ALERT_SECRET_BOOTSTRAP_V5=FAIL FAILURE_CLASS=$FailureClass CODE=$Code"
  exit 1
}

function To-Plain {
  param([Security.SecureString]$SecureValue)
  $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecureValue)
  try { [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
  finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
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

$supabaseAccessToken = To-Plain (Read-Host -Prompt 'Supabase access token' -AsSecureString)
if ([string]::IsNullOrWhiteSpace($supabaseAccessToken)) { Fail-Closed $FailureClassTransport 'EMPTY_SUPABASE_ACCESS_TOKEN' }

$headers = @{ Authorization = "Bearer $supabaseAccessToken" }
try {
  $response = Invoke-WebRequest -Method Get -Uri "https://api.supabase.com/v1/projects/$ProjectRef/secrets" -Headers $headers -UseBasicParsing
} catch {
  Fail-Closed $FailureClassReadback 'SUPABASE_RUNTIME_SECRET_READ_FAILED'
}
if ([int]$response.StatusCode -ne 200) { Fail-Closed $FailureClassReadback 'SUPABASE_RUNTIME_SECRET_READ_NOT_200' }

try { $decoded = $response.Content | ConvertFrom-Json } catch { Fail-Closed $FailureClassReadback 'SUPABASE_RUNTIME_SECRET_JSON_INVALID' }
if (-not ($decoded -is [array])) { Fail-Closed $FailureClassReadback 'SUPABASE_RUNTIME_SECRET_ROOT_NOT_ARRAY' }
$items = @($decoded)
if ($items.Count -lt 3) { Fail-Closed $FailureClassReadback 'SUPABASE_RUNTIME_SECRET_ARRAY_TOO_SMALL' }

$byName = @{}
foreach ($item in $items) {
  if ($null -eq $item) { continue }
  if (-not ($item.PSObject.Properties.Name -contains 'name')) { continue }
  if (-not ($item.PSObject.Properties.Name -contains 'value')) { continue }
  $name = [string]$item.name
  if ([string]::IsNullOrWhiteSpace($name)) { continue }
  $byName[$name] = [string]$item.value
}
foreach ($name in $RuntimeNames) {
  if (-not $byName.ContainsKey($name)) { Fail-Closed $FailureClassReadback "SUPABASE_RUNTIME_SECRET_MISSING_$name" }
  if ([string]::IsNullOrWhiteSpace([string]$byName[$name])) { Fail-Closed $FailureClassReadback "SUPABASE_RUNTIME_SECRET_VALUE_EMPTY_$name" }
}

# Runtime secrets are already present. Reconcile GitHub from the exact runtime values; do not rotate them again.
Set-GitHubSecretFromStdin 'SUPABASE_ACCESS_TOKEN' $supabaseAccessToken
Set-GitHubSecretFromStdin 'STUDENT_ACCESS_ALERT_DISPATCH_TOKEN' ([string]$byName['STUDENT_ACCESS_ALERT_DISPATCH_TOKEN'])
Set-GitHubSecretFromStdin 'STUDENT_ACCESS_ALERT_TELEGRAM_BOT_TOKEN' ([string]$byName['STUDENT_ACCESS_ALERT_TELEGRAM_BOT_TOKEN'])
Set-GitHubSecretFromStdin 'STUDENT_ACCESS_ALERT_TELEGRAM_CHAT_ID' ([string]$byName['STUDENT_ACCESS_ALERT_TELEGRAM_CHAT_ID'])

$githubSecretList = @(& $script:GhCommand secret list --repo $Repository 2>&1 | ForEach-Object { [string]$_ })
if ($LASTEXITCODE -ne 0) { Fail-Closed $FailureClassPartial 'GITHUB_SECRET_LIST_FAILED_AFTER_RECONCILE' }
$joined = $githubSecretList -join "`n"
foreach ($name in $GitHubNames) {
  if ($joined -notmatch [regex]::Escape($name)) { Fail-Closed $FailureClassPartial "GITHUB_ACTIONS_SECRET_MISSING_$name" }
}

Remove-Variable byName,decoded,items,response,headers,supabaseAccessToken -ErrorAction SilentlyContinue
Write-Host 'STAGE35_ALERT_SECRET_BOOTSTRAP_V5=PASS'
Write-Host 'SUPABASE_RUNTIME_SECRET_ROOT_SHAPE=ARRAY'
Write-Host 'SUPABASE_EDGE_RUNTIME_SECRET_NAMES_VERIFIED=3/3'
Write-Host 'GITHUB_ACTIONS_SECRET_NAMES_VERIFIED=4/4'
Write-Host 'RUNTIME_SECRET_ROTATED=false'
Write-Host 'SECRET_VALUES_PRINTED=false'
Write-Host 'SECRET_VALUES_STORED_IN_REPOSITORY=false'
Write-Host 'DATABASE_MIGRATION_APPLIED=false'
Write-Host 'EDGE_FUNCTION_DEPLOYED=false'
Write-Host 'TELEGRAM_PROVIDER_CALLED=false'
Write-Host 'ONE_SHOT_EXTERNAL_DELIVERY_PROOF_CONSUMED=false'
Write-Host 'NEXT_ACTION=RERUN_STAGE35_ALERT_RUNTIME_SECRET_READINESS'
