#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "10_compliance/review/COMMERCIAL_READINESS_EXTERNAL_FACT_PACK_V1_CONTRACT.json"
MARKER_NAME = ".fitnexus_external_fact_pack_v1"
MARKER_VALUE = "FITNEXUS_COMMERCIAL_READINESS_EXTERNAL_FACT_PACK_V1\n"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(message: str) -> None:
    raise SystemExit(f"COMMERCIAL_READINESS_EXTERNAL_FACT_PACK_V1=FAIL::{message}")


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def default_output_root() -> Path:
    return Path.home() / "Documents" / "FitNexus_Coach_BlackGold_EXTERNAL" / "commercial_readiness" / "current"


def prepare_current_only_output(output_root: Path) -> None:
    if output_root.exists():
        marker = output_root / MARKER_NAME
        if not marker.is_file() or marker.read_text(encoding="utf-8") != MARKER_VALUE:
            fail(f"refusing to replace unmarked directory: {output_root}")
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=False)
    (output_root / MARKER_NAME).write_text(MARKER_VALUE, encoding="utf-8", newline="\n")
    (output_root / "sources").mkdir()


def validate_bound_sources(contract: dict) -> list[dict]:
    manifest_entries: list[dict] = []
    seen_names: set[str] = set()
    for item in contract["bound_sources"]:
        source = ROOT / item["path"]
        require(source.is_file(), f"missing bound source {item['path']}")
        actual_blob = git_blob_sha(source)
        require(actual_blob == item["git_blob_sha"], f"git blob drift for {item['path']}: {actual_blob}")
        name = source.name
        require(name not in seen_names, f"duplicate output basename {name}")
        seen_names.add(name)
        manifest_entries.append(
            {
                "source_path": item["path"],
                "role": item["role"],
                "git_blob_sha": actual_blob,
                "sha256": sha256(source),
                "copied_relative_path": f"sources/{name}",
            }
        )
    return manifest_entries


def validate_fail_closed_source_state() -> dict:
    decisions = load_json(ROOT / "10_compliance/drafts/COMPLIANCE_OPEN_DECISIONS.json")
    unresolved = decisions.get("unresolved", [])
    require(len(unresolved) == 14, f"expected 14 canonical open decisions, got {len(unresolved)}")
    require(all(x.get("state") == "OPEN" for x in unresolved), "a canonical decision is no longer OPEN; rebuild strategy before generating pack")

    terms_text = (ROOT / "10_compliance/drafts/TERMS_OF_USE_CANDIDATE_PTBR.md").read_text(encoding="utf-8")
    require("DRAFT_UNREVIEWED_NOT_PUBLISHED_NOT_LEGAL_EVIDENCE" in terms_text, "Terms candidate status marker drift")
    require("legal_terms_of_use = BLOCKED" in terms_text, "Terms legal gate marker drift")

    stage69 = load_json(ROOT / "10_compliance/rehearsals/STAGE69_REAL_OWNER_ASSIGNMENT_INPUT_TEMPLATE.json")
    require(stage69.get("test_fixture") is True and stage69.get("contains_placeholders") is True, "Stage69 template is not a placeholder fixture")

    stage91 = load_json(ROOT / "10_compliance/rehearsals/STAGE91_REAL_CONTROLLED_EXERCISE_REVIEW_INPUT_TEMPLATE.json")
    require(stage91.get("test_fixture") is True and stage91.get("contains_placeholders") is True, "Stage91 template is not a placeholder fixture")

    predeploy = load_json(ROOT / "10_compliance/deployment/STAGE70_PRODUCTION_PREDEPLOY_PREREQUISITE_INPUT_TEMPLATE.json")
    require(predeploy.get("test_fixture") is True and predeploy.get("contains_placeholders") is True, "Stage70 predeploy template is not a placeholder fixture")
    require(predeploy.get("operator_acknowledged") is False, "Stage70 operator acknowledgement unexpectedly true")

    postdeploy = load_json(ROOT / "10_compliance/deployment/STAGE71_POSTDEPLOY_EVIDENCE_INPUT_TEMPLATE.json")
    require(postdeploy.get("test_fixture") is True and postdeploy.get("contains_placeholders") is True, "Stage71 postdeploy template is not a placeholder fixture")
    require(postdeploy.get("operator_acknowledged") is False, "Stage71 operator acknowledgement unexpectedly true")

    return decisions


def copy_sources(entries: list[dict], output_root: Path) -> None:
    for entry in entries:
        src = ROOT / entry["source_path"]
        dst = output_root / entry["copied_relative_path"]
        shutil.copyfile(src, dst)
        require(sha256(dst) == entry["sha256"], f"copy hash mismatch for {entry['source_path']}")


def build_status(decisions: dict) -> dict:
    return {
        "schema_version": 1,
        "kind": "NON_ATTESTING_COMMERCIAL_READINESS_EXTERNAL_WORK_STATUS",
        "commercial_publication_management_percent": 74,
        "technical_product_management_percent": 92,
        "progress_credit_from_pack_generation": 0,
        "macroblock": "COMMERCIAL_READINESS",
        "macroblock_state": "ACTIVE_EXTERNAL_FACT_COLLECTION",
        "canonical_open_decision_count": 14,
        "canonical_open_decisions": [
            {
                "id": item["id"],
                "required": item["required"],
                "resolution_authority": item["resolution_authority"],
                "state": item["state"],
            }
            for item in decisions["unresolved"]
        ],
        "working_sequence": [
            "1_REAL_PROVIDER_AND_LEGAL_IDENTITY",
            "2_REAL_INDEPENDENT_LEGAL_PRIVACY_BUSINESS_REVIEW",
            "3_REAL_DSR_AND_INCIDENT_OWNER_ASSIGNMENTS",
            "4_HUMAN_SYNTHETIC_EXERCISE_AND_INDEPENDENT_REVIEW",
            "5_REAL_BILLING_AUTHORITY_AND_BILLING_POLICY_REVIEW",
            "6_APPROVED_PUBLISHED_TERMS_AND_VERSIONING_REVIEW",
            "7_PRODUCTION_PREDEPLOY_AUTHORITY",
            "8_LATER_POSTDEPLOY_EVIDENCE_ONLY_AFTER_AUTHORIZED_DEPLOYMENT",
        ],
        "hard_boundaries": {
            "legal_review_attested": False,
            "owner_assignments_attested": False,
            "human_exercise_execution_attested": False,
            "billing_authority_attested": False,
            "provider_credentials_collected": False,
            "deployment_authorized": False,
            "controlled_launch_authorized": False,
            "paid_media_authorized": False,
        },
    }


def build_readme() -> str:
    return """# FitNexus Coach BlackGold — Commercial Readiness External Fact Pack V1

Este diretório é uma **cópia de trabalho externa e current-only**. Ele existe para evitar procurar vários arquivos no repositório e para concentrar, em um único lugar, as entradas reais que ainda faltam para a publicação comercial.

## Regra principal

Gerar este pacote **não aumenta os 74% de prontidão comercial**. O percentual só muda quando fatos reais removem bloqueios. Nenhum arquivo preenchido com nomes reais, dados de revisores, caminhos de evidências, credenciais ou segredos deve ser commitado no repositório.

## Ordem de trabalho

1. Definir a identidade real do prestador/entidade e reunir a referência documental correspondente.
2. Levar os questionários e o candidato exato de Termos para revisão jurídica/privacidade/business real e rastreável.
3. Preencher externamente o template Stage69 com os seis papéis reais e os artefatos de designação.
4. Executar os oito cenários sintéticos com pessoas reais responsáveis e produzir o registro de exercício + revisão independente; depois preencher o template Stage91.
5. Somente quando existir autoridade real do provedor de cobrança, revisar a política de trial, renovação, cancelamento, reembolso/arrependimento, inadimplência e reativação.
6. Após revisão independente, produzir Termos aprovados/publicados com versão, vigência, digest e URL HTTPS estável; só então o mecanismo técnico de aceite pode ser ligado ao documento aprovado.
7. Preencher o Stage70 apenas quando domínio, TLS, rollback, monitoramento, backup e destino de produção forem reais e revisados.
8. O Stage71 fica reservado para **depois** de um deploy real separadamente autorizado.

## Pastas e arquivos

- `STATUS.json`: estado consolidado dos 14 bloqueios canônicos.
- `MANIFEST.json`: hashes e proveniência das cópias.
- `sources/`: cópias exatas dos templates, questionários e contexto necessários.

## Proibições

Não inventar revisão, nomes, aprovações, URLs de publicação, credenciais, evidências, execução humana, deploy ou autorização de lançamento. Não colocar segredo de Asaas/Supabase/Cloudflare/GitHub neste pacote. O conteúdo real preenchido deve permanecer fora do repositório.
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=default_output_root())
    args = parser.parse_args()

    contract = load_json(CONTRACT)
    require(contract.get("kind") == "NON_ATTESTING_EXTERNAL_FACT_PACK_CONTRACT", "contract kind drift")
    require(contract.get("status_semantics", {}).get("pack_generation_progress_credit") == 0, "pack must not grant progress credit")
    require(contract.get("hard_boundaries", {}).get("paid_media_allowed") is False, "paid media boundary drift")

    entries = validate_bound_sources(contract)
    decisions = validate_fail_closed_source_state()

    output_root = args.output_root.expanduser().resolve()
    require(output_root != ROOT and ROOT not in output_root.parents, "output root must remain outside repository")
    prepare_current_only_output(output_root)
    copy_sources(entries, output_root)

    status = build_status(decisions)
    (output_root / "STATUS.json").write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

    manifest = {
        "schema_version": 1,
        "kind": "NON_ATTESTING_EXTERNAL_FACT_PACK_MANIFEST",
        "source_baseline_main_sha": contract["baseline_main_sha"],
        "entry_count": len(entries),
        "entries": entries,
        "contains_real_owner_identity": False,
        "contains_real_reviewer_identity": False,
        "contains_provider_secret": False,
        "contains_real_operational_evidence": False,
        "commercial_progress_credit": 0,
    }
    (output_root / "MANIFEST.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    (output_root / "README_FIRST.md").write_text(build_readme(), encoding="utf-8", newline="\n")

    require(len(list((output_root / "sources").iterdir())) == len(entries), "copied source count mismatch")
    require(load_json(output_root / "STATUS.json")["canonical_open_decision_count"] == 14, "generated status decision count drift")
    require(load_json(output_root / "MANIFEST.json")["commercial_progress_credit"] == 0, "generated manifest progress-credit drift")

    print("COMMERCIAL_READINESS_EXTERNAL_FACT_PACK_V1=PASS")
    print(f"OUTPUT_ROOT={output_root}")
    print(f"BOUND_SOURCE_COUNT={len(entries)}")
    print("COMMERCIAL_PUBLICATION_MANAGEMENT_ESTIMATE=74%")
    print("PACK_GENERATION_PROGRESS_CREDIT=0")
    print("REAL_EXTERNAL_FACTS_STILL_REQUIRED=true")


if __name__ == "__main__":
    main()
