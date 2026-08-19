from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "04_backend_supabase" / "migrations" / "20260819062000_stage20_controlled_launch_admission.sql"


def fail(code: str, detail: str) -> None:
    print("CONTROLLED_LAUNCH_ADMISSION_CONTRACT_GATE=FAIL")
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
    if not MIGRATION.exists():
        fail("BGF-LAUNCH-ADMISSION-FILE-MISSING-130", "Stage 20 launch admission migration is missing")

    text = MIGRATION.read_text(encoding="utf-8").lower()

    mandatory_gates = (
        "tracking_core",
        "pricing_experiment",
        "billing_provider_credentials",
        "legal_privacy_notice",
        "legal_terms_of_use",
        "legal_role_mapping",
        "data_subject_request_channel",
        "incident_response",
        "production_deployment",
    )
    for gate in mandatory_gates:
        require(
            text,
            f"('{gate}'",
            "BGF-LAUNCH-GATE-MISSING-131",
            f"mandatory controlled-launch gate disappeared: {gate}",
        )

    checks = [
        ("authority_mode in ('automatic','evidence_migration','external_authorization')", "BGF-LAUNCH-EVIDENCE-AUTHORITY-132", "launch gate authority modes drifted"),
        ("where c.authority_mode='evidence_migration'", "BGF-LAUNCH-EVIDENCE-AUTHORITY-132", "manual evidence gates no longer bootstrap blocked"),
        ("state = 'blocked' or (evidence_ref is not null and evidence_digest is not null)", "BGF-LAUNCH-READY-WITHOUT-EVIDENCE-133", "ready evidence gate lost evidence requirement"),
        ("c.capture_authority='public_capture'", "BGF-LAUNCH-TRACKING-AUTHORITY-134", "tracking gate no longer derives from real public capture authority"),
        ("c.capture_status='active'", "BGF-LAUNCH-TRACKING-AUTHORITY-134", "tracking gate no longer requires active public capture"),
        ("p.pricing_decision_version=d.decision_version", "BGF-LAUNCH-PRICING-AUTHORITY-135", "pricing gate lost decision lineage"),
        ("p.billing_interval in ('month','year')", "BGF-LAUNCH-PRICING-AUTHORITY-135", "pricing gate lost monthly/annual completeness"),
        ("s.provider_code='asaas'", "BGF-LAUNCH-BILLING-AUTHORITY-136", "billing gate no longer targets selected BR V1 provider"),
        ("s.state='active'", "BGF-LAUNCH-BILLING-AUTHORITY-136", "billing gate no longer requires active provider authority"),
        ("s.activated_at is not null", "BGF-LAUNCH-BILLING-AUTHORITY-136", "billing gate lost activation evidence timestamp"),
        ("'tracking_readiness_is_not_launch_authority',true", "BGF-LAUNCH-AUTHORITY-SEPARATION-137", "tracking readiness is being conflated with launch authority"),
        ("'pricing_readiness_is_not_checkout_authority',true", "BGF-LAUNCH-AUTHORITY-SEPARATION-137", "pricing readiness is being conflated with checkout authority"),
        ("'external_billing_authorization_required',true", "BGF-LAUNCH-AUTHORITY-SEPARATION-137", "external billing boundary disappeared"),
        ("'legal_review_evidence_is_migration_owned',true", "BGF-LAUNCH-LEGAL-SELF-ATTESTATION-138", "legal evidence is no longer evidence-as-code"),
        ("'paid_ads_auto_launch',false", "BGF-LAUNCH-PAID-ADS-AUTO-139", "paid ads must never auto-launch from readiness"),
        ("ready_for_controlled_launch", "BGF-LAUNCH-STATE-SEMANTICS-140", "controlled launch state disappeared"),
        ("ready_for_controlled_admission", "BGF-LAUNCH-STATE-SEMANTICS-140", "ads admission state disappeared"),
    ]
    for needle, code, detail in checks:
        require(text, needle, code, detail)

    # Evidence must be changed by an auditable migration, not a client/service RPC.
    forbid(
        text,
        "create or replace function public.attest_controlled_launch_gate",
        "BGF-LAUNCH-LEGAL-SELF-ATTESTATION-138",
        "runtime public RPC must not self-attest launch evidence",
    )
    forbid(
        text,
        "grant insert on private.controlled_launch_gate_evidence",
        "BGF-LAUNCH-EVIDENCE-AUTHORITY-132",
        "runtime roles must not directly insert launch evidence",
    )
    forbid(
        text,
        "grant update on private.controlled_launch_gate_evidence",
        "BGF-LAUNCH-EVIDENCE-AUTHORITY-132",
        "runtime roles must not directly update launch evidence",
    )

    wrapper = re.search(
        r"create or replace function public\.get_controlled_launch_readiness\(\).*?\$\$;",
        text,
        flags=re.DOTALL,
    )
    if wrapper is None or "security invoker" not in wrapper.group(0):
        fail(
            "BGF-LAUNCH-RPC-AUTHORITY-141",
            "public readiness wrapper must remain SECURITY INVOKER",
        )

    require(
        text,
        "revoke execute on function public.get_controlled_launch_readiness() from public,anon,authenticated",
        "BGF-LAUNCH-RPC-AUTHORITY-141",
        "launch readiness must not be exposed to browser roles",
    )
    require(
        text,
        "grant execute on function public.get_controlled_launch_readiness() to service_role",
        "BGF-LAUNCH-RPC-AUTHORITY-141",
        "launch automation lost its service authority read path",
    )

    print("CONTROLLED_LAUNCH_ADMISSION_CONTRACT_GATE=PASS")
    print("MANDATORY_GATES=9")
    print("TRACKING_AUTHORITY=SERVER_DERIVED")
    print("PRICING_AUTHORITY=SERVER_DERIVED")
    print("BILLING_CREDENTIAL_AUTHORITY=EXTERNAL")
    print("LEGAL_AND_OPERATIONS_EVIDENCE=MIGRATION_OWNED")
    print("RUNTIME_SELF_ATTESTATION=DENIED")
    print("PAID_ADS_AUTO_LAUNCH=DENIED")
    print("READINESS_RPC=SERVICE_ROLE_ONLY")
    return 0


if __name__ == "__main__":
    sys.exit(main())
