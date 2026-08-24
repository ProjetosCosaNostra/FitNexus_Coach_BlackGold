[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$LegalReviewerReference,
    [Parameter(Mandatory=$true)][string]$ApprovedProcessingRoleMatrixVersion,
    [Parameter(Mandatory=$true)][string]$LegalPrivacyRoleReviewArtifact,
    [Parameter(Mandatory=$true)][string]$ApprovedProcessingRoleMatrixDocument,
    [Parameter(Mandatory=$true)][string]$PurposeToRoleMappingArtifact,
    [Parameter(Mandatory=$true)][string]$PurposeToLegalBasisReviewArtifact,
    [Parameter(Mandatory=$true)][string]$SensitiveDataTreatmentReviewArtifact,
    [Parameter(Mandatory=$true)][string]$ProcessorSubprocessorMapArtifact,
    [Parameter(Mandatory=$true)][string]$InternationalTransferMechanismMapArtifact,
    [Parameter(Mandatory=$true)][ValidateSet('APPLICABLE','NOT_APPLICABLE_REVIEWED')][string]$InternationalTransferApplicability,
    [Parameter(Mandatory=$true)][ValidateSet('I_CONFIRM_ARTIFACTS_REDACTED_AND_NO_SECRETS')][string]$RedactionConfirmation,
    [Parameter(Mandatory=$true)][string]$OutputPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Fail([string]$Message) { throw "STAGE43_LEGAL_ROLE_MAPPING_EVIDENCE_COLLECTION_BLOCKED: $Message" }
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
if ([string]::IsNullOrWhiteSpace($ApprovedProcessingRoleMatrixVersion)) { Fail 'approved processing-role matrix version is required' }
if ($ApprovedProcessingRoleMatrixVersion.Length -gt 120) { Fail 'approved processing-role matrix version is unexpectedly long' }
if ($RedactionConfirmation -ne 'I_CONFIRM_ARTIFACTS_REDACTED_AND_NO_SECRETS') { Fail 'redaction confirmation missing' }

$review = Resolve-EvidenceFile $LegalPrivacyRoleReviewArtifact 'legal/privacy role review artifact'
$matrix = Resolve-EvidenceFile $ApprovedProcessingRoleMatrixDocument 'approved processing-role matrix document'
$purposeRole = Resolve-EvidenceFile $PurposeToRoleMappingArtifact 'purpose-to-role mapping artifact'
$legalBasis = Resolve-EvidenceFile $PurposeToLegalBasisReviewArtifact 'purpose-to-legal-basis review artifact'
$sensitive = Resolve-EvidenceFile $SensitiveDataTreatmentReviewArtifact 'sensitive-data treatment review artifact'
$processors = Resolve-EvidenceFile $ProcessorSubprocessorMapArtifact 'processor/subprocessor map artifact'
$transfer = Resolve-EvidenceFile $InternationalTransferMechanismMapArtifact 'international-transfer mechanism map artifact'

$receipt = [ordered]@{
    schema_version = 1
    stage = 'STAGE43_LEGAL_ROLE_MAPPING_EXTERNAL_EVIDENCE_PREPARATION'
    output_kind = 'DIGEST_ONLY_LEGAL_ROLE_MAPPING_EVIDENCE_INTAKE_CANDIDATE'
    gate_code = 'legal_role_mapping'
    candidate_state = 'AWAITING_INDEPENDENT_REVIEW_NOT_ATTESTATION'
    collected_at_utc = (Get-Date).ToUniversalTime().ToString('o')
    legal_reviewer_reference = $LegalReviewerReference.Trim()
    approved_processing_role_matrix_version = $ApprovedProcessingRoleMatrixVersion.Trim()
    legal_privacy_role_review_artifact_digest = Get-Sha256 $review
    approved_processing_role_matrix_digest = Get-Sha256 $matrix
    purpose_to_role_mapping_digest = Get-Sha256 $purposeRole
    purpose_to_legal_basis_review_digest = Get-Sha256 $legalBasis
    sensitive_data_treatment_review_digest = Get-Sha256 $sensitive
    processor_subprocessor_map_digest = Get-Sha256 $processors
    international_transfer_mechanism_map_digest = Get-Sha256 $transfer
    international_transfer_applicability = $InternationalTransferApplicability
    redaction_confirmation = 'CONFIRMED'
    raw_artifact_content_copied_to_receipt = $false
    artifact_path_or_filename_copied_to_receipt = $false
    personal_or_secret_material_collected = $false
    network_call_performed = $false
    supabase_mutation_performed = $false
    evidence_migration_created = $false
    legal_or_privacy_review_self_attested = $false
    gate_ready_attested = $false
    controlled_launch_promoted = $false
    next_action = 'INDEPENDENT_REVIEW_REQUIRED_BEFORE_ANY_EVIDENCE_MIGRATION'
}

$out = [System.IO.Path]::GetFullPath($OutputPath)
$parent = Split-Path -Parent $out
if ($parent -and -not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
$receipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $out -Encoding UTF8
Write-Output 'STAGE43_LEGAL_ROLE_MAPPING_EVIDENCE_COLLECTION=PASS_CANDIDATE_ONLY'
Write-Output "RECEIPT=$out"
Write-Output 'GATE_READY=false'
Write-Output 'INDEPENDENT_REVIEW_REQUIRED=true'
