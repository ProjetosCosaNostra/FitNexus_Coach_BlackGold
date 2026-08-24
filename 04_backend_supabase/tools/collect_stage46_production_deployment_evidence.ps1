[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$StableProductionDomain,
    [Parameter(Mandatory=$true)][string]$TlsEvidenceArtifact,
    [Parameter(Mandatory=$true)][string]$EnvironmentConfigurationReceiptWithoutSecrets,
    [Parameter(Mandatory=$true)][string]$ReleaseCommitSha,
    [Parameter(Mandatory=$true)][string]$ProductionSmokeTestReceipt,
    [Parameter(Mandatory=$true)][string]$RollbackTestReceipt,
    [Parameter(Mandatory=$true)][string]$MonitoringAlertingReadinessReceipt,
    [Parameter(Mandatory=$true)][string]$BackupRestoreReadinessReferenceArtifact,
    [Parameter(Mandatory=$true)][string]$ReleaseEvidenceManifestArtifact,
    [Parameter(Mandatory=$true)][ValidateSet('I_CONFIRM_ENVIRONMENT_RECEIPT_AND_ARTIFACTS_REDACTED_NO_SECRET_VALUES')][string]$SecretRedactionConfirmation,
    [Parameter(Mandatory=$true)][ValidateSet('I_CONFIRM_MONITORING_ALERTING_EVIDENCE_IS_NOT_STAGE35_ALERT_PROOF_ALONE')][string]$MonitoringCompletenessConfirmation,
    [Parameter(Mandatory=$true)][string]$OutputPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Fail([string]$Message) { throw "STAGE46_PRODUCTION_DEPLOYMENT_EVIDENCE_COLLECTION_BLOCKED: $Message" }
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
if (-not [Uri]::TryCreate($StableProductionDomain, [UriKind]::Absolute, [ref]$uri)) { Fail 'stable production domain is not an absolute URL' }
if ($uri.Scheme -ne 'https') { Fail 'stable production domain must use https' }
$hostValue = $uri.Host.ToLowerInvariant()
if ($hostValue -in @('localhost','127.0.0.1','::1','example.com','www.example.com')) { Fail 'stable production domain is placeholder/local' }
if ($hostValue -match '(^|\.)(test|staging|preview|dev)(\.|$)') { Fail 'stable production domain appears non-production' }
if ($StableProductionDomain -match '(?i)(example|placeholder|localhost|preview)') { Fail 'stable production domain contains placeholder marker' }
if ($ReleaseCommitSha -notmatch '^[0-9a-f]{40}$') { Fail 'release commit SHA must be lowercase 40-character git SHA-1 hex' }
if ($SecretRedactionConfirmation -ne 'I_CONFIRM_ENVIRONMENT_RECEIPT_AND_ARTIFACTS_REDACTED_NO_SECRET_VALUES') { Fail 'secret-redaction confirmation missing' }
if ($MonitoringCompletenessConfirmation -ne 'I_CONFIRM_MONITORING_ALERTING_EVIDENCE_IS_NOT_STAGE35_ALERT_PROOF_ALONE') { Fail 'monitoring/alerting completeness confirmation missing' }

$tls = Resolve-EvidenceFile $TlsEvidenceArtifact 'TLS evidence artifact'
$envReceipt = Resolve-EvidenceFile $EnvironmentConfigurationReceiptWithoutSecrets 'environment configuration receipt without secrets'
$smoke = Resolve-EvidenceFile $ProductionSmokeTestReceipt 'production smoke-test receipt'
$rollback = Resolve-EvidenceFile $RollbackTestReceipt 'rollback test receipt'
$monitoring = Resolve-EvidenceFile $MonitoringAlertingReadinessReceipt 'monitoring/alerting readiness receipt'
$backup = Resolve-EvidenceFile $BackupRestoreReadinessReferenceArtifact 'backup/restore readiness reference artifact'
$manifest = Resolve-EvidenceFile $ReleaseEvidenceManifestArtifact 'release evidence manifest artifact'

$receipt = [ordered]@{
    schema_version = 1
    stage = 'STAGE46_PRODUCTION_DEPLOYMENT_EXTERNAL_EVIDENCE_PREPARATION'
    output_kind = 'DIGEST_ONLY_PRODUCTION_DEPLOYMENT_EVIDENCE_INTAKE_CANDIDATE'
    gate_code = 'production_deployment'
    candidate_state = 'AWAITING_INDEPENDENT_REVIEW_NOT_ATTESTATION'
    collected_at_utc = (Get-Date).ToUniversalTime().ToString('o')
    stable_production_domain = $uri.AbsoluteUri
    tls_evidence_digest = Get-Sha256 $tls
    environment_configuration_receipt_digest = Get-Sha256 $envReceipt
    release_commit_sha = $ReleaseCommitSha
    production_smoke_test_receipt_digest = Get-Sha256 $smoke
    rollback_test_receipt_digest = Get-Sha256 $rollback
    monitoring_alerting_readiness_receipt_digest = Get-Sha256 $monitoring
    backup_restore_readiness_reference_digest = Get-Sha256 $backup
    release_evidence_manifest_digest = Get-Sha256 $manifest
    secret_redaction_confirmation = 'CONFIRMED'
    monitoring_alerting_not_stage35_only_confirmation = 'CONFIRMED'
    raw_artifact_content_copied_to_receipt = $false
    artifact_path_or_filename_copied_to_receipt = $false
    secret_values_collected = $false
    network_call_performed = $false
    deployment_action_performed = $false
    supabase_mutation_performed = $false
    evidence_migration_created = $false
    operations_self_attested = $false
    stage35_alert_proof_alone_used_for_monitoring_alerting = $false
    gate_ready_attested = $false
    controlled_launch_promoted = $false
    next_action = 'INDEPENDENT_REVIEW_REQUIRED_BEFORE_ANY_EVIDENCE_MIGRATION'
}

$out = [System.IO.Path]::GetFullPath($OutputPath)
$parent = Split-Path -Parent $out
if ($parent -and -not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
$receipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $out -Encoding UTF8
Write-Output 'STAGE46_PRODUCTION_DEPLOYMENT_EVIDENCE_COLLECTION=PASS_CANDIDATE_ONLY'
Write-Output "RECEIPT=$out"
Write-Output 'GATE_READY=false'
Write-Output 'DEPLOYMENT_ACTION_PERFORMED=false'
Write-Output 'SECRET_VALUES_COLLECTED=false'
Write-Output 'INDEPENDENT_REVIEW_REQUIRED=true'
