#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "10_financeiro/autopilot/FINANCE_TAX_AUTOPILOT_V1_CONTRACT.json"
MARKER_NAME = ".fitnexus_finance_tax_autopilot_v1"
MARKER_VALUE = "FITNEXUS_FINANCE_TAX_AUTOPILOT_V1\n"


def fail(message: str) -> None:
    raise SystemExit(f"FINANCE_TAX_AUTOPILOT_V1=FAIL::{message}")


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def default_output_root() -> Path:
    return Path.home() / "Documents" / "FitNexus_Coach_BlackGold_EXTERNAL" / "finance_tax" / "current"


def prepare_current_only_output(output_root: Path) -> None:
    if output_root.exists():
        marker = output_root / MARKER_NAME
        if not marker.is_file() or marker.read_text(encoding="utf-8") != MARKER_VALUE:
            fail(f"refusing to replace unmarked directory: {output_root}")
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=False)
    (output_root / MARKER_NAME).write_text(MARKER_VALUE, encoding="utf-8", newline="\n")
    (output_root / "evidence").mkdir()


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def build_workspace(output_root: Path, contract: dict) -> None:
    operator = contract["operator_profile"]
    write_json(
        output_root / "OPERATOR_PROFILE.json",
        {
            "schema_version": 1,
            "operator_legal_form": operator["legal_form"],
            "commercial_brand": operator["commercial_brand"],
            "mei_or_cnpj_present": operator["mei_or_cnpj_present"],
            "cpf_or_other_sensitive_identifier_present": False,
            "status": "PRE_REVENUE_PROFILE_NON_ATTESTING",
        },
    )

    write_json(
        output_root / "TAX_RULE_AUTHORITY_TEMPLATE.json",
        {
            "schema_version": 1,
            "status": "PLACEHOLDER_NOT_REVIEWED_NOT_VALID_FOR_TAX_CALCULATION",
            "jurisdiction": "BR",
            "calendar_year": None,
            "operator_legal_form": "PESSOA_FISICA",
            "revenue_source_classification": None,
            "official_source_urls": [],
            "reviewed_rules": [],
            "effective_dates": [],
            "review_status": "NOT_REVIEWED",
            "review_reference": None,
            "contains_secret_values": False,
        },
    )

    write_json(
        output_root / "MONTHLY_CLOSE_TEMPLATE.json",
        {
            "schema_version": 1,
            "status": "PLACEHOLDER_NO_REAL_MONTHLY_CLOSE",
            "period": "YYYY-MM",
            "currency": "BRL",
            "reconciled_totals": {
                "gross_receipts": None,
                "refunds": None,
                "chargebacks": None,
                "provider_fees": None,
                "operating_costs": None,
                "owner_contributions": None,
                "owner_withdrawals": None,
                "net_cash_movement": None,
            },
            "tax_reserve": {
                "authority_pack_validated": False,
                "provisional_reserve_amount": None,
                "final_tax_due_attested": False,
            },
            "unresolved_exceptions": [],
            "candidate_due_dates": [],
            "human_actions_required": [],
            "evidence_manifest_path": "evidence/MANIFEST.json",
        },
    )

    write_json(
        output_root / "FORMALIZATION_GATE_TEMPLATE.json",
        {
            "schema_version": 1,
            "status": "PRE_REVENUE_NOT_TRIGGERED",
            "current_legal_form": "PESSOA_FISICA",
            "candidate_forms": ["PESSOA_FISICA", "MEI_IF_LEGALLY_ELIGIBLE", "OTHER_CNPJ_REGIME"],
            "inputs": {
                "average_monthly_gross_revenue": None,
                "average_monthly_net_cash": None,
                "revenue_stability_months": None,
                "estimated_pf_compliance_cost": None,
                "estimated_mei_compliance_cost_if_eligible": None,
                "estimated_other_cnpj_compliance_cost": None,
                "billing_or_invoice_requirement": None,
                "safety_margin_months": None,
            },
            "mei_eligibility_reviewed": False,
            "recommended_action": "NO_AUTOMATIC_FORMALIZATION",
            "human_authorization_required": True,
        },
    )

    write_json(
        output_root / "STATUS.json",
        {
            "schema_version": 1,
            "kind": "NON_ATTESTING_FINANCE_TAX_AUTOPILOT_STATUS",
            "state": contract["state"],
            "operator_legal_form": "PESSOA_FISICA",
            "commercial_brand": operator["commercial_brand"],
            "real_revenue_ingested": False,
            "reviewed_tax_rule_pack_present": False,
            "tax_filing_authorized": False,
            "tax_payment_authorized": False,
            "formalization_triggered": False,
            "commercial_publication_progress_credit": 0,
        },
    )

    ledger = output_root / "TRANSACTION_LEDGER_TEMPLATE.csv"
    with ledger.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow([
            "event_id",
            "event_date",
            "event_type",
            "gross_amount_brl",
            "fee_amount_brl",
            "net_amount_brl",
            "provider_reference",
            "category",
            "evidence_reference",
            "reconciled",
            "notes",
        ])

    (output_root / "evidence" / "MANIFEST.json").write_text(
        json.dumps({
            "schema_version": 1,
            "status": "EMPTY_PRE_REVENUE_MANIFEST",
            "entries": [],
            "contains_secrets": False,
        }, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    readme = """# Finance & Tax Autopilot V1 — External Workspace\n\nThis is the private current-only workspace for future FitNexus finance/tax operations.\n\nDo not place CPF, bank passwords, API secrets or government credentials here unless a later encrypted/approved mechanism explicitly requires it. Never commit this completed workspace to Git.\n\nThe system is currently pre-revenue. Templates are not tax advice, a filing, a payment instruction or proof of compliance. Tax calculations may only use a reviewed authority pack with dated official sources.\n\nWorkflow when revenue starts: ingest and reconcile receipts/fees/refunds/costs -> review exceptions -> load current tax authority pack -> calculate provisional reserve -> prepare monthly close -> present only unavoidable human filing/payment actions.\n\nFormalization is a separate economic/legal gate. MEI eligibility must be reviewed rather than assumed.\n"""
    (output_root / "README_FIRST.md").write_text(readme, encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=default_output_root())
    args = parser.parse_args()

    contract = load_json(CONTRACT)
    require(contract.get("kind") == "NON_ATTESTING_FINANCE_TAX_AUTOPILOT_FOUNDATION", "contract kind drift")
    require(contract.get("operator_profile", {}).get("legal_form") == "PESSOA_FISICA", "operator legal form drift")
    require(contract.get("hard_boundaries", {}).get("can_file_tax_return") is False, "tax filing boundary drift")
    require(contract.get("hard_boundaries", {}).get("can_pay_tax") is False, "tax payment boundary drift")
    require(contract.get("progress_semantics", {}).get("foundation_progress_credit_to_commercial_publication_percent") == 0, "foundation cannot grant commercial progress")

    output_root = args.output_root.expanduser().resolve()
    require(output_root != ROOT and ROOT not in output_root.parents, "output root must remain outside repository")
    prepare_current_only_output(output_root)
    build_workspace(output_root, contract)

    required = {
        "OPERATOR_PROFILE.json",
        "TAX_RULE_AUTHORITY_TEMPLATE.json",
        "MONTHLY_CLOSE_TEMPLATE.json",
        "FORMALIZATION_GATE_TEMPLATE.json",
        "STATUS.json",
        "TRANSACTION_LEDGER_TEMPLATE.csv",
        "README_FIRST.md",
        MARKER_NAME,
        "evidence",
    }
    require(required.issubset({p.name for p in output_root.iterdir()}), "workspace completeness failure")
    require(load_json(output_root / "STATUS.json")["commercial_publication_progress_credit"] == 0, "status progress boundary drift")

    print("FINANCE_TAX_AUTOPILOT_V1=PASS")
    print(f"OUTPUT_ROOT={output_root}")
    print("OPERATOR_LEGAL_FORM=PESSOA_FISICA")
    print("REAL_REVENUE_INGESTED=false")
    print("TAX_FILING_AUTHORIZED=false")
    print("TAX_PAYMENT_AUTHORIZED=false")
    print("FOUNDATION_PROGRESS_CREDIT=0")


if __name__ == "__main__":
    main()
