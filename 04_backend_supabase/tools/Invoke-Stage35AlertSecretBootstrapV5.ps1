[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$FailureClass = 'BGF-STAGE35-ALERT-MANAGEMENT-SECRET-READBACK-PLAINTEXT-ASSUMPTION-303'

Write-Host 'STAGE35_ALERT_SECRET_BOOTSTRAP_V5=DISABLED'
Write-Host "FAILURE_CLASS=$FailureClass"
Write-Host 'DO_NOT_EXECUTE_V5=true'
Write-Host 'REASON=Management secret readback plaintext reusability was not proven; Stage35 external proof run 32647288419 empirically failed the custom dispatch auth gate with HTTP 401.'
Write-Host 'SECRET_VALUES_PRINTED=false'
Write-Host 'SECRET_VALUES_READ=false'
Write-Host 'SECRET_VALUES_WRITTEN=false'
Write-Host 'DATABASE_MUTATION=false'
Write-Host 'EDGE_FUNCTION_DEPLOYMENT=false'
Write-Host 'TELEGRAM_PROVIDER_CALLED=false'
Write-Host 'NEXT_ACTION=stage35-dispatch-secret-parity-recovery'
Write-Error 'STAGE35_ALERT_SECRET_BOOTSTRAP_V5_DISABLED_FAIL_CLOSED'
exit 1
