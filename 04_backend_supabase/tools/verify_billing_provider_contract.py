from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS = ROOT / "04_backend_supabase" / "migrations"
PROFESSOR = ROOT / "03_app_flutter" / "fitnexus_app" / "lib" / "features" / "professor"

BASE = MIGRATIONS / "20260818225500_stage16_billing_provider_gate.sql"
HARDENING = MIGRATIONS / "20260818230000_stage16_billing_authority_hardening.sql"


def fail(code: str, detail: str) -> None:
    print("BILLING_PROVIDER_CONTRACT_GATE=FAIL")
    print(f"FAILURE_CLASS={code}")
    print(f"DETAIL={detail}")
    raise SystemExit(1)


def read(path: Path, code: str) -> str:
    if not path.exists():
        fail(code, f"required file missing: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def require(text: str, needle: str, code: str, detail: str) -> None:
    if needle not in text:
        fail(code, detail)


def forbid(text: str, needle: str, code: str, detail: str) -> None:
    if needle in text:
        fail(code, detail)


def require_regex(text: str, pattern: str, code: str, detail: str) -> None:
    if re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL) is None:
        fail(code, detail)


def main() -> int:
    base = read(BASE, "BGF-BILLING-FILE-MISSING-082")
    hardening = read(HARDENING, "BGF-BILLING-FILE-MISSING-082")
    billing_repo = read(
        PROFESSOR / "professor_billing_repository.dart",
        "BGF-BILLING-FLUTTER-READINESS-081",
    )
    subscription_page = read(
        PROFESSOR / "professor_subscription_page.dart",
        "BGF-BILLING-FLUTTER-READINESS-081",
    )

    require_regex(
        base,
        r"\(\s*'asaas'\s*,\s*'Asaas'\s*,\s*'selected'\s*,\s*'BR_V1'",
        "BGF-BILLING-PROVIDER-EVIDENCE-070",
        "Brazil V1 provider selection is no longer Asaas",
    )
    require(
        base,
        "2026-08-18-official-docs-v1",
        "BGF-BILLING-PROVIDER-EVIDENCE-070",
        "provider evidence version disappeared",
    )
    require_regex(
        base,
        r"values\s*\(\s*'BR_V1'\s*,\s*'asaas'\s*,\s*'selected_pending_credentials'",
        "BGF-BILLING-CREDENTIAL-BOUNDARY-072",
        "provider must start pending external credential verification",
    )

    forbid(
        base,
        "insert into public.subscription_plan_prices",
        "BGF-BILLING-PRICE-AUTHORITY-071",
        "Stage 16 must not silently freeze a FitNexus commercial price",
    )
    require(
        base,
        "COMMERCIAL_PRICE_NOT_PROMOTED",
        "BGF-BILLING-PRICE-AUTHORITY-071",
        "checkout no longer fails closed without a promoted price",
    )
    require(
        base,
        "BILLING_PROVIDER_CREDENTIALS_NOT_READY",
        "BGF-BILLING-CREDENTIAL-BOUNDARY-072",
        "checkout no longer fails closed before provider credential authority",
    )
    for guardrail in (
        "'server_amount_authority', true",
        "'client_amount_allowed', false",
        "'silent_provider_fallback', false",
        "'secret_exposed_to_flutter', false",
    ):
        require(
            base,
            guardrail,
            "BGF-BILLING-PRICE-AUTHORITY-071",
            f"billing readiness guardrail disappeared: {guardrail}",
        )

    require(
        base,
        "WEBHOOK_AUTH_NOT_VERIFIED",
        "BGF-BILLING-WEBHOOK-AUTH-073",
        "webhook authentication fail-closed guard disappeared",
    )
    require(
        base,
        "unique (provider_code, provider_event_id)",
        "BGF-BILLING-WEBHOOK-IDEMPOTENCY-074",
        "provider-event deduplication constraint disappeared",
    )
    require(
        base,
        "idempotency_key uuid not null unique",
        "BGF-BILLING-CHECKOUT-IDEMPOTENCY-075",
        "checkout intent idempotency authority disappeared",
    )
    require(
        base,
        "CHECKOUT_IDEMPOTENCY_KEY_CONFLICT",
        "BGF-BILLING-CHECKOUT-IDEMPOTENCY-075",
        "conflicting checkout idempotency reuse no longer fails closed",
    )
    require(
        hardening,
        "SILENT_PROVIDER_FALLBACK_FORBIDDEN",
        "BGF-BILLING-NO-SILENT-FALLBACK-076",
        "provider activation can silently replace the selected provider",
    )
    require(
        base,
        "HTTPS_CHECKOUT_URL_REQUIRED",
        "BGF-BILLING-CHECKOUT-URL-AUTHORITY-077",
        "HTTPS checkout redirect validation disappeared",
    )

    for table in (
        "public.billing_provider_registry",
        "public.billing_provider_selections",
        "public.subscription_plan_prices",
        "public.billing_checkout_intents",
        "public.billing_webhook_receipts",
    ):
        require(
            base,
            f"alter table {table} enable row level security;",
            "BGF-BILLING-RLS-083",
            f"RLS missing for {table}",
        )
        require(
            hardening,
            f"revoke all on {table} from service_role;",
            "BGF-BILLING-SERVICE-DIRECT-MUTATION-079",
            f"service-role direct privileges were not reset for {table}",
        )
        require(
            hardening,
            f"grant select on {table} to service_role;",
            "BGF-BILLING-SERVICE-DIRECT-MUTATION-079",
            f"service worker lost required read-only access to {table}",
        )

    forbid(
        hardening,
        "grant update on public.billing_",
        "BGF-BILLING-SERVICE-DIRECT-MUTATION-079",
        "service worker received direct UPDATE on a Stage 16 billing table",
    )
    forbid(
        hardening,
        "grant insert on public.billing_",
        "BGF-BILLING-SERVICE-DIRECT-MUTATION-079",
        "service worker received direct INSERT on a Stage 16 billing table",
    )
    forbid(
        hardening,
        "grant delete on public.billing_",
        "BGF-BILLING-SERVICE-DIRECT-MUTATION-079",
        "service worker received direct DELETE on a Stage 16 billing table",
    )

    for signature in (
        "public.activate_billing_provider_selection(text,text,text)",
        "public.attach_billing_provider_checkout(uuid,text,text,timestamptz)",
        "public.record_billing_webhook_receipt(text,text,text,text,boolean,uuid,text)",
        "public.mark_billing_webhook_receipt(text,text,text,uuid,text)",
    ):
        require(
            hardening,
            f"revoke execute on function {signature} from public, anon, authenticated;",
            "BGF-BILLING-SERVICE-COMMAND-AUTHORITY-084",
            f"normal clients can execute service billing command {signature}",
        )
        require(
            hardening,
            f"grant execute on function {signature} to service_role;",
            "BGF-BILLING-SERVICE-COMMAND-AUTHORITY-084",
            f"service billing command authority missing for {signature}",
        )

    for index_name in (
        "billing_checkout_intents_created_by_idx",
        "billing_checkout_intents_plan_code_idx",
        "billing_checkout_intents_price_id_idx",
        "billing_provider_selections_provider_code_idx",
    ):
        require(
            hardening,
            index_name,
            "BGF-BILLING-FK-INDEX-080",
            f"Stage 16 foreign-key covering index missing: {index_name}",
        )

    require(
        billing_repo,
        "get_billing_provider_readiness",
        "BGF-BILLING-FLUTTER-READINESS-081",
        "Flutter readiness RPC binding disappeared",
    )
    require(
        billing_repo,
        "externalBoundaryPending",
        "BGF-BILLING-FLUTTER-READINESS-081",
        "Flutter readiness model no longer represents blocked external boundary",
    )
    require(
        subscription_page,
        "AINDA BLOQUEADO",
        "BGF-BILLING-FLUTTER-READINESS-081",
        "blocked checkout state disappeared from Plan workspace",
    )
    require(
        subscription_page,
        "UNFROZEN",
        "BGF-BILLING-PRICE-AUTHORITY-071",
        "Plan workspace no longer exposes unfrozen price state",
    )
    forbid(
        subscription_page,
        "Comprar agora",
        "BGF-BILLING-FLUTTER-READINESS-081",
        "fake live checkout CTA appeared before credential/price gates are promoted",
    )

    print("BILLING_PROVIDER_CONTRACT_GATE=PASS")
    print("BRAZIL_V1_PROVIDER=ASAAS")
    print("PROVIDER_EVIDENCE_VERSION=PASS")
    print("CREDENTIAL_BOUNDARY=PASS")
    print("PRICE_AUTHORITY=SERVER_ONLY")
    print("PRICING_STAGE16=UNFROZEN")
    print("WEBHOOK_AUTH=PASS")
    print("WEBHOOK_IDEMPOTENCY=PASS")
    print("CHECKOUT_IDEMPOTENCY=PASS")
    print("NO_SILENT_FALLBACK=PASS")
    print("SERVICE_DIRECT_MUTATION=DENIED")
    print("SERVICE_COMMAND_AUTHORITY=PASS")
    print("FOREIGN_KEY_INDEX_COVERAGE=PASS")
    print("FLUTTER_READINESS=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
