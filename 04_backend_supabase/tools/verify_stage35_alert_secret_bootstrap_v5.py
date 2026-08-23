from pathlib import Path

root = Path(__file__).resolve().parents[2]
ps = root / '04_backend_supabase/tools/Invoke-Stage35AlertSecretBootstrapV5.ps1'
text = ps.read_text(encoding='utf-8')
lower = text.lower()

required = [
    'stage35_alert_secret_bootstrap_v5=disabled',
    'bgf-stage35-alert-management-secret-readback-plaintext-assumption-303',
    'do_not_execute_v5=true',
    'run 32647288419',
    'http 401',
    'secret_values_read=false',
    'secret_values_written=false',
    'telegram_provider_called=false',
    'stage35-dispatch-secret-parity-recovery',
    'exit 1',
]
missing = [fragment for fragment in required if fragment not in lower]
assert not missing, f'missing V5 fail-closed deprecation invariants: {missing}'

for forbidden in [
    'invoke-webrequest',
    'invoke-restmethod',
    'read-host',
    'secret set',
    'api.supabase.com',
    'supabase secrets set',
    'functions deploy',
    'apply_migration',
    'api.telegram.org/bot',
]:
    assert forbidden not in lower, f'deprecated V5 still contains secret/provider mutation path: {forbidden}'

print('STAGE35_ALERT_SECRET_BOOTSTRAP_V5_GUARD=PASS')
print('V5_DEPRECATED_FAIL_CLOSED=PASS')
print('V5_SECRET_IO_SURFACE_PRESENT=false')
print('V5_EXECUTION_ALLOWED=false')
