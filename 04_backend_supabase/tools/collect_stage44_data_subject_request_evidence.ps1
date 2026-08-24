[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$PublishedDataSubjectRequestRoute,
    [Parameter(Mandatory=$true)][string]$OwnerAndBackupAssignmentArtifact,
    [Parameter(Mandatory=$true)][string]$IdentityVerificationProcedureArtifact,
    [Parameter(Mandatory=$true)][string]$TenantScopedAccessExportTestReceipt,
    [Parameter(Mandatory=$true)][string]$CorrectionWorkflowTestReceipt,
    [Parameter(Mandatory=$true)][string]$DeletionAnonymizationBlockingRetentionHoldTestReceipt,
    [Parameter(Mandatory=$true)][string]$ControllerOperatorHandoffProcedureArtifact,
    [Parameter(Mandatory=$true)][string]$ReviewedResponseTimePolicyArtifact,
    [Parameter(Mandatory=$true)][string]$TabletopRequestReceipt,
    [Parameter(Mandatory=$true)][ValidateSet('I_CONFIRM_TEST_RECEIPTS_USE_SYNTHETIC_OR_NON_CUSTOMER_FIXTURES')][string]$SyntheticFixtureConfirmation,
    [Parameter(Mandatory=$true)][ValidateSet('I_CONFIRM_ARTIFACTS_REDACTED_AND_NO_SECRETS')][string]$RedactionConfirmation,
    [Parameter(Mandatory=$true)][string]$OutputPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Fail([string]$Message) { throw "STAGE44_DATA_SUBJECT_REQUEST_EVIDENCE_COLLECTION_BLOCKED: $Message" }
function Resolve-EvidenceFile([string]$PathValue, [string]$Label) {
    if ([string]::IsNullOrWhiteSpace($PathValue)) { Fail "$Label path is empty" }
    $item = Get-Item -LiteralPath $PathValue -ErrorAction Stop
    if (-not $item.PSIsContainer -and $item.Length -gt 0) { return $item }
    Fail "$Label must be a non-empty file"
}
function Get-Sha256([System.IO.FileInfo]$File) {
    return (Get-FileHash -LiteralPath $File.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
}

$uri = $null
if (-not [Uri]::TryCreate($PublishedDataSubjectRequestRoute, [UriKind]::Absolute, [ref]$uri)) { Fail 'published data-subject request route is not absolute' }
if ($uri.Scheme -ne 'https') { Fail 'published data-subject request route must use https' }
$hostValue = $uri.Host.ToLowerInvariant()
if ($hostValue -in @('localhost','127.0.0.1','::1','example.com','www.example.com')) { Fail 'published data-subject request route is placeholder/local' }
if ($hostValue -match '(^|\.)(test|staging|preview|dev)(\.|$)') { Fail 'published data-subject request route appears non-production' }
if ($PublishedDataSubjectRequestRoute -match '(?i)(example|placeholder|localhost|preview)') { Fail 'published data-subject request route contains placeholder marker' }
if ($SyntheticFixtureConfirmation -ne 'I_CONFIRM_TEST_RECEIPTS_USE_SYNTHETIC_OR_NON_CUSTOMER_FIXTURES') { Fail 'synthetic/non-customer fixture confirmation missing' }
if ($RedactionConfirmation -ne 'I_CONFIRM_ARTIFACTS_REDACTED_AND_NO_SECRETS') { Fail 'redaction confirmation missing' }

$owners = Resolve-EvidenceFile $OwnerAndBackupAssignmentArtifact 'owner and backup assignment artifact'
$identity = Resolve-EvidenceFile $IdentityVerificationProcedureArtifact 'identity verification procedure artifact'
$accessExport = Resolve-EvidenceFile $TenantScopedAccessExportTestReceipt 'tenant-scoped access/export test receipt'
$correction = Resolve-EvidenceFile $CorrectionWorkflowTestReceipt 'correction workflow test receipt'
$deletion = Resolve-EvidenceFile $DeletionAnonymizationBlockingRetentionHoldTestReceipt 'deletion/anonymization/blocking/retention-hold test receipt'
$handoff = Resolve-EvidenceFile $ControllerOperatorHandoffProcedureArtifact 'controller/operator handoff procedure artifact'
$responseTime = Resolve-EvidenceFile $ReviewedResponseTimePolicyArtifact 'reviewed response-time policy artifact'
$tabletop = Resolve-EvidenceFile $TabletopRequestReceipt 'tabletop request receipt'

$receipt = [ordered]@{
    schema_version = 1
    stage = 'STAGE44_DATA_SUBJECT_REQUEST_EXTERNAL_EVIDENCE_PREPARATION'
    output_kind = 'DIGEST_ONLY_DATA_SUBJECT_REQUEST_EVIDENCE_INTAKE_CANDIDATE'
    gate_code = 'data_subject_request_channel'
    candidate_state = 'AWAITING_INDEPENDENT_REVIEW_NOT_ATTESTATION'
    collected_at_utc = (Get-Date).ToUniversalTime().ToString('o')
    stable_published_titular_contact_route = $uri.AbsoluteUri
    owner_and_backup_owner_assignment_digest = Get-Sha256 $owners
    identity_verification_procedure_digest = Get-Sha256 $identity
    tenant_scoped_access_export_test_receipt_digest = Get-Sha256 $accessExport
    correction_workflow_test_receipt_digest = Get-Sha256 $correction
    deletion_anonymization_blocking_retention_hold_test_receipt_digest = Get-Sha256 $deletion
    controller_operator_handoff_procedure_digest = Get-Sha256 $handoff
    reviewed_response_time_policy_digest = Get-Sha256 $responseTime
    tabletop_request_receipt_digest = Get-Sha256 $tabletop
    synthetic_or_non_customer_fixture_confirmation = 'CONFIRMED'
    redaction_confirmation = 'CONFIRMED'
    raw_artifact_content_copied_to_receipt = $false
    artifact_path_or_filename_copied_to_receipt = $false
    personal_or_secret_material_collected = $false
    real_customer_data_used_in_test_receipts = $false
    network_call_performed = $false
    supabase_mutation_performed = $false
    evidence_migration_created = $false
    operational_or_legal_self_attested = $false
    gate_ready_attested = $false
    controlled_launch_promoted = $false
    next_action = 'INDEPENDENT_REVIEW_REQUIRED_BEFORE_ANY_EVIDENCE_MIGRATION'
}

$out = [System.IO.Path]::GetFullPath($OutputPath)
$parent = Split-Path -Parent $out
if ($parent -and -not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
$receipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $out -Encoding UTF8
Write-Output 'STAGE44_DATA_SUBJECT_REQUEST_EVIDENCE_COLLECTION=PASS_CANDIDATE_ONLY'
Write-Output "RECEIPT=$out"
Write-Output 'GATE_READY=false'
Write-Output 'REAL_CUSTOMER_DATA_USED=false'
Write-Output 'INDEPENDENT_REVIEW_REQUIRED=true'
