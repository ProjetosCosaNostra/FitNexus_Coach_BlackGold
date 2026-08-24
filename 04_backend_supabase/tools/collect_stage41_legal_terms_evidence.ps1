[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$LegalReviewerReference,
    [Parameter(Mandatory=$true)][string]$ApprovedTermsVersion,
    [Parameter(Mandatory=$true)][string]$PublishedTermsUrl,
    [Parameter(Mandatory=$true)][datetime]$EffectiveDate,
    [Parameter(Mandatory=$true)][string]$LegalReviewArtifact,
    [Parameter(Mandatory=$true)][string]$ApprovedTermsDocument,
    [Parameter(Mandatory=$true)][string]$BillingCancellationRefundPolicyArtifact,
    [Parameter(Mandatory=$true)][string]$ContractAcceptanceVersioningArtifact,
    [Parameter(Mandatory=$true)][ValidateSet('I_CONFIRM_ARTIFACTS_REDACTED_AND_NO_SECRETS')][string]$RedactionConfirmation,
    [Parameter(Mandatory=$true)][string]$OutputPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Fail([string]$Message) {
    throw "STAGE41_LEGAL_TERMS_EVIDENCE_COLLECTION_BLOCKED: $Message"
}

function Resolve-EvidenceFile([string]$PathValue, [string]$Label) {
    if ([string]::IsNullOrWhiteSpace($PathValue)) { Fail "$Label path is empty" }
    $item = Get-Item -LiteralPath $PathValue -ErrorAction Stop
    if (-not $item.PSIsContainer -and $item.Length -gt 0) { return $item }
    Fail "$Label must be a non-empty file"
}

function Get-Sha256([System.IO.FileInfo]$File) {
    return (Get-FileHash -LiteralPath $File.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
}

if ([string]::IsNullOrWhiteSpace($LegalReviewerReference)) { Fail 'real legal reviewer/reference is required' }
if ($LegalReviewerReference.Length -gt 240) { Fail 'legal reviewer/reference is unexpectedly long' }
if ([string]::IsNullOrWhiteSpace($ApprovedTermsVersion)) { Fail 'approved terms version is required' }
if ($ApprovedTermsVersion.Length -gt 120) { Fail 'approved terms version is unexpectedly long' }

$uri = $null
if (-not [Uri]::TryCreate($PublishedTermsUrl, [UriKind]::Absolute, [ref]$uri)) { Fail 'published terms URL is not absolute' }
if ($uri.Scheme -ne 'https') { Fail 'published terms URL must use https' }
$hostValue = $uri.Host.ToLowerInvariant()
if ($hostValue -in @('localhost','127.0.0.1','::1','example.com','www.example.com')) { Fail 'published terms URL is placeholder/local' }
if ($hostValue -match '(^|\.)(test|staging|preview|dev)(\.|$)') { Fail 'published terms URL appears non-production' }
if ($PublishedTermsUrl -match '(?i)(example|placeholder|localhost|preview)') { Fail 'published terms URL contains placeholder marker' }

if ($EffectiveDate.Year -lt 2024 -or $EffectiveDate.Year -gt 2100) { Fail 'effective date outside accepted range' }
if ($RedactionConfirmation -ne 'I_CONFIRM_ARTIFACTS_REDACTED_AND_NO_SECRETS') { Fail 'redaction confirmation missing' }

$legalReview = Resolve-EvidenceFile $LegalReviewArtifact 'legal review artifact'
$terms = Resolve-EvidenceFile $ApprovedTermsDocument 'approved terms document'
$billingPolicy = Resolve-EvidenceFile $BillingCancellationRefundPolicyArtifact 'billing/cancellation/refund policy artifact'
$acceptance = Resolve-EvidenceFile $ContractAcceptanceVersioningArtifact 'contract acceptance/versioning artifact'

$receipt = [ordered]@{
    schema_version = 1
    stage = 'STAGE41_LEGAL_TERMS_EXTERNAL_EVIDENCE_PREPARATION'
    output_kind = 'DIGEST_ONLY_LEGAL_TERMS_EVIDENCE_INTAKE_CANDIDATE'
    gate_code = 'legal_terms_of_use'
    candidate_state = 'AWAITING_INDEPENDENT_REVIEW_NOT_ATTESTATION'
    collected_at_utc = (Get-Date).ToUniversalTime().ToString('o')
    legal_reviewer_reference = $LegalReviewerReference.Trim()
    approved_terms_version = $ApprovedTermsVersion.Trim()
    stable_published_terms_url = $uri.AbsoluteUri
    effective_date = $EffectiveDate.ToString('yyyy-MM-dd')
    legal_review_artifact_digest = Get-Sha256 $legalReview
    approved_document_sha256_digest = Get-Sha256 $terms
    billing_cancellation_refund_policy_digest = Get-Sha256 $billingPolicy
    contract_acceptance_versioning_digest = Get-Sha256 $acceptance
    redaction_confirmation = 'CONFIRMED'
    raw_artifact_content_copied_to_receipt = $false
    artifact_path_or_filename_copied_to_receipt = $false
    personal_or_secret_material_collected = $false
    network_call_performed = $false
    supabase_mutation_performed = $false
    evidence_migration_created = $false
    legal_review_self_attested = $false
    gate_ready_attested = $false
    controlled_launch_promoted = $false
    next_action = 'INDEPENDENT_REVIEW_REQUIRED_BEFORE_ANY_EVIDENCE_MIGRATION'
}

$out = [System.IO.Path]::GetFullPath($OutputPath)
$parent = Split-Path -Parent $out
if ($parent -and -not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
$receipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $out -Encoding UTF8
Write-Output "STAGE41_LEGAL_TERMS_EVIDENCE_COLLECTION=PASS_CANDIDATE_ONLY"
Write-Output "RECEIPT=$out"
Write-Output "GATE_READY=false"
Write-Output "INDEPENDENT_REVIEW_REQUIRED=true"
