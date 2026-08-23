from pathlib import Path

root = Path(__file__).resolve().parents[2]
ps = root / '04_backend_supabase/tools/Invoke-Stage35AlertSecretBootstrapV5.ps1'
text = ps.read_text(encoding='utf-8')
required = [
    "Invoke-WebRequest -Method Get -Uri \"https://api.supabase.com/v1/projects/$ProjectRef/secrets\"",
    "if (-not ($decoded -is [array]))",
    "$items = @($decoded)",
    "STUDENT_ACCESS_ALERT_DISPATCH_TOKEN",
    "STUDENT_ACCESS_ALERT_TELEGRAM_BOT_TOKEN",
    "STUDENT_ACCESS_ALERT_TELEGRAM_CHAT_ID",
    "secret set $Name --repo $Repository",
    "RUNTIME_SECRET_ROTATED=false",
    "TELEGRAM_PROVIDER_CALLED=false",
    "ONE_SHOT_EXTERNAL_DELIVERY_PROOF_CONSUMED=false",
]
missing = [s for s in required if s not in text]
assert not missing, f'missing required V5 invariants: {missing}'
for forbidden in [
    'Invoke-RestMethod -Method Post -Uri "https://api.supabase.com/v1/projects/$ProjectRef/secrets"',
    'supabase secrets set',
    'functions deploy',
    'apply_migration',
    'api.telegram.org/bot',
]:
    assert forbidden not in text, f'forbidden mutating/provider path in V5: {forbidden}'
print('STAGE35_ALERT_SECRET_BOOTSTRAP_V5_GUARD=PASS')
