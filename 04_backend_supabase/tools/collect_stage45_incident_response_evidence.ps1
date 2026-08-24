[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$IncidentCommanderPrivacyTechnicalOwnerAssignmentArtifact,
    [Parameter(Mandatory=$true)][string]$RiskClassificationMatrixArtifact,
    [Parameter(Mandatory=$true)][string]$OperatorToControllerHandoffProcedureArtifact,
    [Parameter(Mandatory=$true)][string]$AnpdDataSubjectCommunicationDecisionProcedureArtifact,
    [Parameter(Mandatory=$true)][string]$IncidentRegistryRetentionControlArtifact,
    [Parameter(Mandatory=$true)][string]$CrossTenantExposureTabletopReceipt,
    [Parameter(Mandatory=$true)][string]$CredentialCompromiseTabletopReceipt,
    [Parameter(Mandatory=$true)][string]$PotentiallySensitiveStudentDataTabletopReceipt,
    [Parameter(Mandatory=$true)][string]$FinalDrillPostmortemArtifact,
    [Parameter(Mandatory=$true)][ValidateSet('I_CONFIRM_TABLETOPS_USE_SYNTHETIC_OR_NON_CUSTOMER_FIXTURES')][string]$SyntheticFixtureConfirmation,
    [Parameter(Mandatory=$true)][ValidateSet('I_CONFIRM_ARTIFACTS_REDACTED_AND_NO_SECRETS')][string]$RedactionConfirmation,
    [Parameter(Mandatory=$true)][string]$OutputPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Fail([string]$Message) { throw "STAGE45_INCIDENT_RESPONSE_EVIDENCE_COLLECTION_BLOCKED: $Message" }
function Resolve-EvidenceFile([string]$PathValue, [string]$Label) {
    if ([string]::IsNullOrWhiteSpace($PathValue)) { Fail "$Label path is empty" }
    $item = Get-Item -LiteralPath $PathValue -ErrorAction Stop
    if (-not $item.PSIsContainer -and $item.Length -gt 0) { return $item }
    Fail "$Label must be a non-empty file"
}
function Get-Sha256([System.IO.FileInfo]$File) {
    return (Get-FileHash -LiteralPath $File.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
}

if ($SyntheticFixtureConfirmation -ne 'I_CONFIRM_TABLETOPS_USE_SYNTHETIC_OR_NON_CUSTOMER_FIXTURES') { Fail 'synthetic/non-customer tabletop fixture confirmation missing' }
if ($RedactionConfirmation -ne 'I_CONFIRM_ARTIFACTS_REDACTED_AND_NO_SECRETS') { Fail 'redaction confirmation missing' }

$owners = Resolve-EvidenceFile $IncidentCommanderPrivacyTechnicalOwnerAssignmentArtifact 'incident commander/privacy/technical owner assignment artifact'
$risk = Resolve-EvidenceFile $RiskClassificationMatrixArtifact 'risk classification matrix artifact'
$handoff = Resolve-EvidenceFile $OperatorToControllerHandoffProcedureArtifact 'operator-to-controller handoff procedure artifact'
$communication = Resolve-EvidenceFile $AnpdDataSubjectCommunicationDecisionProcedureArtifact 'ANPD/data-subject communication decision procedure artifact'
$retention = Resolve-EvidenceFile $IncidentRegistryRetentionControlArtifact 'incident registry retention control artifact'
$crossTenant = Resolve-EvidenceFile $CrossTenantExposureTabletopReceipt 'cross-tenant exposure tabletop receipt'
$credential = Resolve-EvidenceFile $CredentialCompromiseTabletopReceipt 'credential compromise tabletop receipt'
$sensitive = Resolve-EvidenceFile $PotentiallySensitiveStudentDataTabletopReceipt 'potentially sensitive student-data tabletop receipt'
$postmortem = Resolve-EvidenceFile $FinalDrillPostmortemArtifact 'final drill/postmortem artifact'

$receipt = [ordered]@{
    schema_version = 1
    stage = 'STAGE45_INCIDENT_RESPONSE_EXTERNAL_EVIDENCE_PREPARATION'
    output_kind = 'DIGEST_ONLY_INCIDENT_RESPONSE_EVIDENCE_INTAKE_CANDIDATE'
    gate_code = 'incident_response'
    candidate_state = 'AWAITING_INDEPENDENT_REVIEW_NOT_ATTESTATION'
    collected_at_utc = (Get-Date).ToUniversalTime().ToString('o')
    incident_commander_privacy_owner_technical_owner_assignment_digest = Get-Sha256 $owners
    risk_classification_matrix_digest = Get-Sha256 $risk
    operator_to_controller_handoff_procedure_digest = Get-Sha256 $handoff
    anpd_data_subject_communication_decision_procedure_digest = Get-Sha256 $communication
    incident_registry_retention_control_digest = Get-Sha256 $retention
    cross_tenant_exposure_tabletop_receipt_digest = Get-Sha256 $crossTenant
    credential_compromise_tabletop_receipt_digest = Get-Sha256 $credential
    potentially_sensitive_student_data_tabletop_receipt_digest = Get-Sha256 $sensitive
    final_drill_postmortem_digest = Get-Sha256 $postmortem
    synthetic_or_non_customer_tabletop_fixture_confirmation = 'CONFIRMED'
    redaction_confirmation = 'CONFIRMED'
    raw_artifact_content_copied_to_receipt = $false
    artifact_path_or_filename_copied_to_receipt = $false
    personal_or_secret_material_collected = $false
    real_customer_data_used_in_tabletops = $false
    live_incident_required = $false
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
Write-Output 'STAGE45_INCIDENT_RESPONSE_EVIDENCE_COLLECTION=PASS_CANDIDATE_ONLY'
Write-Output "RECEIPT=$out"
Write-Output 'GATE_READY=false'
Write-Output 'REAL_CUSTOMER_DATA_USED=false'
Write-Output 'LIVE_INCIDENT_REQUIRED=false'
Write-Output 'INDEPENDENT_REVIEW_REQUIRED=true'
