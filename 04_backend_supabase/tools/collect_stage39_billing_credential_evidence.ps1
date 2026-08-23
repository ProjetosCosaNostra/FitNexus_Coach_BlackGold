[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('asaas-sandbox', 'asaas-production')]
    [string]$ProviderEnvironmentId,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$ProviderAccountOwnerAuthorizationArtifact,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$CredentialActivationArtifact,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9._:/ -]{2,127}$')]
    [string]$SecretBoundaryRef,

    [Parameter(Mandatory = $true)]
    [ValidateSet('I_AUTHORIZE_FITNEXUS_ASAAS_INTEGRATION')]
    [string]$ProviderAccountOwnerAuthorization,

    [Parameter(Mandatory = $true)]
    [ValidateSet('SECRET_VALUE_ABSENT_OR_REDACTED')]
    [string]$CredentialArtifactRedactionConfirmation,

    [Parameter(Mandatory = $false)]
    [ValidateNotNullOrEmpty()]
    [string]$OutputPath = (Join-Path (Get-Location) 'STAGE39_BILLING_CREDENTIAL_EVIDENCE_RECEIPT.json')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Assert-EvidenceFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [string]$Label
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "$Label artifact not found."
    }

    $item = Get-Item -LiteralPath $Path
    if ($item.Length -le 0) {
        throw "$Label artifact is empty."
    }

    return $item
}

$ownerArtifact = Assert-EvidenceFile -Path $ProviderAccountOwnerAuthorizationArtifact -Label 'Provider account owner authorization'
$credentialArtifact = Assert-EvidenceFile -Path $CredentialActivationArtifact -Label 'Credential activation'

$ownerDigest = (Get-FileHash -LiteralPath $ownerArtifact.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
$credentialDigest = (Get-FileHash -LiteralPath $credentialArtifact.FullName -Algorithm SHA256).Hash.ToLowerInvariant()

if ($ownerDigest -notmatch '^[0-9a-f]{64}$') {
    throw 'Provider account owner authorization digest is invalid.'
}
if ($credentialDigest -notmatch '^[0-9a-f]{64}$') {
    throw 'Credential activation digest is invalid.'
}

$environmentFacts = if ($ProviderEnvironmentId -eq 'asaas-sandbox') {
    [ordered]@{
        provider_environment_id = 'asaas-sandbox'
        provider_base_url = 'https://api-sandbox.asaas.com/v3'
        real_financial_impact_expected = $false
    }
}
else {
    [ordered]@{
        provider_environment_id = 'asaas-production'
        provider_base_url = 'https://api.asaas.com/v3'
        real_financial_impact_expected = $true
    }
}

$receipt = [ordered]@{
    schema_version = 1
    stage = 'STAGE39_BILLING_CREDENTIAL_AUTHORITY_EXTERNAL_EVIDENCE'
    result = 'DIGEST_ONLY_EVIDENCE_INTAKE_CANDIDATE'
    project_ref = 'mceukeondizkwlpfxzgf'
    scope = 'BR_V1'
    provider_code = 'asaas'
    evidence_version = '2026-08-18-official-docs-v1'
    provider_environment_id = $environmentFacts.provider_environment_id
    provider_base_url = $environmentFacts.provider_base_url
    real_financial_impact_expected = $environmentFacts.real_financial_impact_expected
    secret_boundary_ref = $SecretBoundaryRef
    provider_account_owner_authorization_digest = $ownerDigest
    credential_activation_digest = $credentialDigest
    provider_account_owner_authorization_confirmed = $true
    credential_artifact_secret_value_absent_or_redacted_confirmed = $true
    collected_at_utc = [DateTime]::UtcNow.ToString('o')
    raw_secret_value_collected = $false
    raw_artifact_content_copied_to_receipt = $false
    artifact_path_or_filename_copied_to_receipt = $false
    provider_called = $false
    provider_activation_performed = $false
    supabase_mutation_performed = $false
    customer_data_used = $false
    credentials_verified_state_attested = $false
    billing_gate_promoted = $false
    launch_gate_promoted = $false
    next_action = 'INDEPENDENT_REVIEW_REQUIRED_BEFORE_ANY_EVIDENCE_MIGRATION'
}

$outputFullPath = [System.IO.Path]::GetFullPath($OutputPath)
$outputDirectory = Split-Path -Parent $outputFullPath
if (-not [string]::IsNullOrWhiteSpace($outputDirectory) -and -not (Test-Path -LiteralPath $outputDirectory)) {
    New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
}

$receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $outputFullPath -Encoding utf8NoBOM

Write-Host 'STAGE39_BILLING_CREDENTIAL_EVIDENCE_COLLECTOR=PASS'
Write-Host 'RESULT=DIGEST_ONLY_EVIDENCE_INTAKE_CANDIDATE'
Write-Host "PROVIDER_ENVIRONMENT_ID=$ProviderEnvironmentId"
Write-Host 'RAW_SECRET_VALUE_COLLECTED=false'
Write-Host 'RAW_ARTIFACT_CONTENT_COPIED=false'
Write-Host 'PROVIDER_CALLED=false'
Write-Host 'PROVIDER_ACTIVATION_PERFORMED=false'
Write-Host 'SUPABASE_MUTATION_PERFORMED=false'
Write-Host 'CREDENTIALS_VERIFIED_STATE_ATTESTED=false'
Write-Host 'BILLING_GATE_PROMOTED=false'
Write-Host "RECEIPT_PATH=$outputFullPath"
