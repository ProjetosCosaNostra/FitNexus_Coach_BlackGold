from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS = ROOT / "04_backend_supabase" / "migrations"
BILLING = ROOT / "03_app_flutter" / "fitnexus_app" / "lib" / "features" / "professor" / "professor_billing_repository.dart"


def fail(code: str, detail: str) -> None:
    print("PRICING_AUTHORITY_CONTRACT_GATE=FAIL")
    print(f"FAILURE_CLASS={code}")
    print(f"DETAIL={detail}")
    raise SystemExit(1)


def require(text: str, needle: str, code: str, detail: str) -> None:
    if needle not in text:
        fail(code, detail)


def forbid(text: str, needle: str, code: str, detail: str) -> None:
    if needle in text:
        fail(code, detail)


def main() -> int:
    migrations = "\n".join(p.read_text(encoding="utf-8") for p in sorted(MIGRATIONS.glob("*.sql")))
    billing = BILLING.read_text(encoding="utf-8")

    checks = [
        ("BR_V1_PRICING_EXPERIMENT_001", "BGF-PRICING-UNVERSIONED-083", "pricing experiment lost versioned identity"),
        ("'solo','billing_interval','month','amount_minor',3990", "BGF-PRICING-DECISION-DRIFT-084", "Solo monthly experiment price drifted without a new decision version"),
        ("'pro','billing_interval','month','amount_minor',7990", "BGF-PRICING-DECISION-DRIFT-084", "Pro monthly experiment price drifted without a new decision version"),
        ("'studio','billing_interval','month','amount_minor',17990", "BGF-PRICING-DECISION-DRIFT-084", "Studio monthly experiment price drifted without a new decision version"),
        ("TEN_MONTHS_FOR_TWELVE", "BGF-PRICING-ANNUAL-STRATEGY-085", "ten-month annual experiment strategy disappeared"),
        ("PRICING_SET_MUST_HAVE_SIX_OFFERS", "BGF-PRICING-PARTIAL-PROMOTION-086", "partial price-set prevention disappeared"),
        ("PRICING_DECISION_VERSION_CONFLICT", "BGF-PRICING-IDEMPOTENCY-087", "pricing decision replay/conflict guard disappeared"),
        ("provider_fee_assumptions_contractual', false", "BGF-PRICING-FEE-EVIDENCE-088", "public provider fees must not be treated as contractual account rates"),
        ("pricing_decision_version", "BGF-PRICING-CHECKOUT-BINDING-089", "checkout intent lost pricing decision binding"),
        ("security definer", "BGF-BILLING-RPC-PRIVILEGE-DEADPATH-082", "billing mutation RPC must close underlying table privilege path"),
        ("get_pricing_catalog", "BGF-PRICING-CATALOG-090", "authoritative pricing catalog RPC disappeared"),
        ("expected_price_count', 6", "BGF-PRICING-COMPLETE-SET-091", "readiness no longer requires the complete six-offer set"),
        ("PricingCatalogSnapshot", "BGF-PRICING-FLUTTER-BINDING-092", "Flutter pricing authority model disappeared"),
    ]
    for needle, code, detail in checks:
        require(migrations + "\n" + billing, needle, code, detail)

    forbid(migrations, "grant insert on public.subscription_plan_prices to authenticated", "BGF-PRICING-CLIENT-MUTATION-093", "client must not insert prices")
    forbid(migrations, "grant update on public.subscription_plan_prices to authenticated", "BGF-PRICING-CLIENT-MUTATION-093", "client must not update prices")
    forbid(migrations, "grant execute on function public.promote_subscription_pricing(text,text,text,text,text,jsonb,text,timestamptz,jsonb) to authenticated", "BGF-PRICING-PROMOTION-AUTHORITY-094", "normal users must not promote pricing")

    print("PRICING_AUTHORITY_CONTRACT_GATE=PASS")
    print("DECISION_VERSION=BR_V1_PRICING_EXPERIMENT_001")
    print("PRICE_SET=6_OFFERS")
    print("ANNUAL_STRATEGY=TEN_MONTHS_FOR_TWELVE")
    print("CHECKOUT_DECISION_BINDING=PASS")
    print("PUBLIC_FEE_ASSUMPTIONS=NON_CONTRACTUAL")
    print("CLIENT_PRICE_MUTATION=DENIED")
    print("FLUTTER_PRICING_BINDING=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
