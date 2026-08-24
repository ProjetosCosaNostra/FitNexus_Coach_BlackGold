[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$LegalReviewerReference,
    [Parameter(Mandatory=$true)][string]$ApprovedPrivacyNoticeVersion,
    [Parameter(Mandatory=$true)][string]$PublishedPrivacyUrl,
    [Parameter(Mandatory=$true)][datetime]$EffectiveDate,
    [Parameter(Mandatory=$true)][string]$LegalPrivacyReviewArtifact,
    [Parameter(Mandatory=$true)][string]$ApprovedPrivacyNoticeDocument,
    [Parameter(Mandatory=$true)][string]$ProcessorSubprocessorInventoryArtifact,
    [Parameter(Mandatory=$true)][string]$RetentionMatrixArtifact,
    [Parameter(Mandatory=$true)][string]$InternationalTransferReviewArtifact,
    [Parameter(Mandatory=$true)][ValidateSet('APPLICABLE','NOT_APPLICABLE_REVIEWED')][string]$InternationalTransferApplicability,
    [Parameter(Mandatory=$true)][string]$EncarregadoOrExemptionContactReviewArtifact,
    [Parameter(Mandatory=$true)][ValidateSet('I_CONFIRM_ARTIFACTS_REDACTED_AND_NO_SECRETS')][string]$RedactionConfirmation,
    [Parameter(Mandatory=$true)][string]$OutputPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Fail([string]$Message) { throw "STAGE42_PRIVACY_NOTICE_EVIDENCE_COLLECTION_BLOCKED: $Message" }
function Resolve-EvidenceFile([string]$PathValue, [string]$Label) {
    if ([string]::IsNullOrWhiteSpace($PathValue)) { Fail "$Label path is empty" }
    $item = Get-Item -LiteralPath $PathValue -ErrorAction Stop
    if (-not $item.PSIsContainer -and $item.Length -gt 0) { return $item }
    Fail "$Label must be a non-empty file"
}
function Get-Sha256([System.IO.FileInfo]$File) {
    return (Get-FileHash -LiteralPath $File.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
}

if ([string]::IsNullOrWhiteSpace($LegalReviewerReference)) { Fail 'real legal/privacy reviewer reference is required' }
if ($LegalReviewerReference.Length -gt 240) { Fail 'legal/privacy reviewer reference is unexpectedly long' }
if ([string]::IsNullOrWhiteSpace($ApprovedPrivacyNoticeVersion)) { Fail 'approved privacy notice version is required' }
if ($ApprovedPrivacyNoticeVersion.Length -gt 120) { Fail 'approved privacy notice version is unexpectedly long' }

$uri = $null
if (-not [Uri]::TryCreate($PublishedPrivacyUrl, [UriKind]::Absolute, [ref]$uri)) { Fail 'published privacy URL is not absolute' }
if ($uri.Scheme -ne 'https') { Fail 'published privacy URL must use https' }
$hostValue = $uri.Host.ToLowerInvariant()
if ($hostValue -in @('localhost','127.0.0.1','::1','example.com','www.example.com')) { Fail 'published privacy URL is placeholder/local' }
if ($hostValue -match '(^|\.)(test|staging|preview|dev)(\.|$)') { Fail 'published privacy URL appears non-production' }
if ($PublishedPrivacyUrl -match '(?i)(example|placeholder|localhost|preview)') { Fail 'published privacy URL contains placeholder marker' }
if ($EffectiveDate.Year -lt 2024 -or $EffectiveDate.Year -gt 2100) { Fail 'effective date outside accepted range' }
if ($RedactionConfirmation -ne 'I_CONFIRM_ARTIFACTS_REDACTED_AND_NO_SECRETS') { Fail 'redaction confirmation missing' }

$review = Resolve-EvidenceFile $LegalPrivacyReviewArtifact 'legal/privacy review artifact'
$notice = Resolve-EvidenceFile $ApprovedPrivacyNoticeDocument 'approved privacy notice document'
$processors = Resolve-EvidenceFile $ProcessorSubprocessorInventoryArtifact 'processor/subprocessor inventory artifact'
$retention = Resolve-EvidenceFile $RetentionMatrixArtifact 'retention matrix artifact'
$transfer = Resolve-EvidenceFile $InternationalTransferReviewArtifact 'international transfer review artifact'
$encarregado = Resolve-EvidenceFile $EncarregadoOrExemptionContactReviewArtifact 'encarregado/exemption/contact review artifact'

$receipt = [ordered]@{
    schema_version = 1
    stage = 'STAGE42_PRIVACY_NOTICE_EXTERNAL_EVIDENCE_PREPARATION'
    output_kind = 'DIGEST_ONLY_PRIVACY_NOTICE_EVIDENCE_INTAKE_CANDIDATE'
    gate_code = 'legal_privacy_notice'
    candidate_state = 'AWAITING_INDEPENDENT_REVIEW_NOT_ATTESTATION'
    collected_at_utc = (Get-Date).ToUniversalTime().ToString('o')
    legal_reviewer_reference = $LegalReviewerReference.Trim()
    approved_privacy_notice_version = $ApprovedPrivacyNoticeVersion.Trim()
    stable_published_privacy_url = $uri.AbsoluteUri
    effective_date = $EffectiveDate.ToString('yyyy-MM-dd')
    legal_privacy_review_artifact_digest = Get-Sha256 $review
    approved_document_sha256_digest = Get-Sha256 $notice
    processor_subprocessor_inventory_digest = Get-Sha256 $processors
    retention_matrix_digest = Get-Sha256 $retention
    international_transfer_review_digest = Get-Sha256 $transfer
    international_transfer_applicability = $InternationalTransferApplicability
    encarregado_or_exemption_contact_review_digest = Get-Sha256 $encarregado
    redaction_confirmation = 'CONFIRMED'
    raw_artifact_content_copied_to_receipt = $false
    artifact_path_or_filename_copied_to_receipt = $false
    personal_or_secret_material_collected = $false
    network_call_performed = $false
    supabase_mutation_performed = $false
    evidence_migration_created = $false
    privacy_or_legal_review_self_attested = $false
    gate_ready_attested = $false
    controlled_launch_promoted = $false
    next_action = 'INDEPENDENT_REVIEW_REQUIRED_BEFORE_ANY_EVIDENCE_MIGRATION'
}

$out = [System.IO.Path]::GetFullPath($OutputPath)
$parent = Split-Path -Parent $out
if ($parent -and -not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
$receipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $out -Encoding UTF8
Write-Output 'STAGE42_PRIVACY_NOTICE_EVIDENCE_COLLECTION=PASS_CANDIDATE_ONLY'
Write-Output "RECEIPT=$out"
Write-Output 'GATE_READY=false'
Write-Output 'INDEPENDENT_REVIEW_REQUIRED=true'
