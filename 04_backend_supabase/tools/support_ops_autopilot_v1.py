#!/usr/bin/env python3
"""FitNexus Support Ops Autopilot V1.

Consumes one externally supplied email-envelope JSON and produces a minimized,
non-sending triage candidate. It never connects to Gmail, Supabase or any
network service. The full body is used only for classification and is not
copied into the output.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

CATEGORIES = ("SUPPORT", "BILLING", "PRIVACY_DATA", "SECURITY", "OTHER")

RULES: dict[str, tuple[str, ...]] = {
    "SECURITY": (
        "security", "seguranca", "segurança", "vazamento", "breach", "hack",
        "hacked", "invasao", "invasão", "token exposed", "senha vazou",
        "fraude", "fraud", "phishing",
    ),
    "PRIVACY_DATA": (
        "privacidade", "privacy", "dados pessoais", "personal data", "lgpd",
        "acesso aos dados", "exportar dados", "export my data", "excluir dados",
        "delete my data", "corrigir dados", "rectification", "data request",
    ),
    "BILLING": (
        "cobranca", "cobrança", "billing", "pagamento", "payment", "refund",
        "reembolso", "assinatura", "subscription", "cartao", "cartão", "pix",
        "chargeback", "cancelamento", "cancel subscription",
    ),
    "SUPPORT": (
        "suporte", "support", "erro", "error", "bug", "nao funciona",
        "não funciona", "problema", "problem", "login", "acesso", "treino",
        "aluno", "professor", "app", "aplicativo",
    ),
}

PREFIX_RULES = {
    "[FITNEXUS][SEGURANCA]": "SECURITY",
    "[FITNEXUS][SEGURANÇA]": "SECURITY",
    "[FITNEXUS][SECURITY]": "SECURITY",
    "[FITNEXUS][DADOS]": "PRIVACY_DATA",
    "[FITNEXUS][PRIVACIDADE]": "PRIVACY_DATA",
    "[FITNEXUS][PRIVACY]": "PRIVACY_DATA",
    "[FITNEXUS][COBRANCA]": "BILLING",
    "[FITNEXUS][COBRANÇA]": "BILLING",
    "[FITNEXUS][BILLING]": "BILLING",
    "[FITNEXUS][SUPORTE]": "SUPPORT",
    "[FITNEXUS][SUPPORT]": "SUPPORT",
}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()).lower()


def classify(subject: str, body: str) -> tuple[str, list[str]]:
    upper_subject = subject.strip().upper()
    for prefix, category in PREFIX_RULES.items():
        if upper_subject.startswith(prefix):
            return category, [f"subject_prefix:{prefix}"]

    haystack = _normalize(f"{subject} {body}")
    scores: dict[str, int] = {category: 0 for category in RULES}
    hits: dict[str, list[str]] = {category: [] for category in RULES}
    for category, keywords in RULES.items():
        for keyword in keywords:
            if _normalize(keyword) in haystack:
                scores[category] += 1
                hits[category].append(keyword)

    # Security and privacy win ties because they demand attention, not because
    # the engine is making a legal classification.
    priority = ("SECURITY", "PRIVACY_DATA", "BILLING", "SUPPORT")
    best = max(scores.values(), default=0)
    if best == 0:
        return "OTHER", []
    for category in priority:
        if scores[category] == best:
            return category, [f"keyword:{item}" for item in hits[category]]
    return "OTHER", []


def build_candidate(payload: dict[str, Any]) -> dict[str, Any]:
    message_id = str(payload.get("source_message_id") or "").strip()
    requester_email = str(payload.get("requester_email") or "").strip().lower()
    subject = str(payload.get("subject") or "").strip()
    body = str(payload.get("body") or "")
    received_at = str(payload.get("received_at") or "").strip()

    if not message_id:
        raise ValueError("source_message_id_required")
    if "@" not in requester_email or len(requester_email) < 5:
        raise ValueError("requester_email_invalid")
    if not received_at:
        raise ValueError("received_at_required")

    category, reasons = classify(subject, body)
    security = category == "SECURITY"
    privacy = category == "PRIVACY_DATA"

    summary_parts = [f"Categoria candidata: {category}."]
    if reasons:
        summary_parts.append("Sinais: " + ", ".join(reasons[:5]) + ".")
    summary_parts.append("Revisar a mensagem-fonte antes de qualquer resposta externa.")

    return {
        "schema_version": 1,
        "kind": "SUPPORT_TRIAGE_CANDIDATE_NOT_SENT_NOT_FILED",
        "source_message_id": message_id,
        "requester_email": requester_email,
        "subject": subject,
        "received_at": received_at,
        "category": category,
        "attention_security": security,
        "attention_privacy": privacy,
        "triage_summary": " ".join(summary_parts),
        "protocol_number": "PENDING_DATABASE_ASSIGNMENT",
        "database_status": "NOT_INGESTED",
        "full_message_body_persisted": False,
        "draft_ack": {
            "subject": f"[FitNexus] Solicitação recebida — protocolo pendente ({category})",
            "body": (
                "Recebemos sua mensagem no canal oficial do FitNexus Coach BlackGold. "
                "A solicitação será vinculada a um protocolo quando a operação automática "
                "estiver ativa. Não envie senhas, tokens ou códigos de autenticação."
            ),
            "send_authorized": False,
        },
    }


def _self_test() -> None:
    cases = [
        ("[FITNEXUS][DADOS] Quero exportar", "", "PRIVACY_DATA"),
        ("Cobrança duplicada", "pagamento no cartão", "BILLING"),
        ("Possível vazamento", "minha senha vazou", "SECURITY"),
        ("Erro no treino", "o app não funciona", "SUPPORT"),
        ("Assunto geral", "mensagem sem palavras conhecidas", "OTHER"),
    ]
    for subject, body, expected in cases:
        actual, _ = classify(subject, body)
        if actual != expected:
            raise AssertionError(f"classification mismatch: {actual} != {expected}")

    candidate = build_candidate(
        {
            "source_message_id": "gmail:test-1",
            "requester_email": "Pessoa@Example.com",
            "subject": "[FITNEXUS][DADOS] acesso",
            "body": "quero acesso aos dados",
            "received_at": "2026-08-27T18:00:00Z",
        }
    )
    assert candidate["requester_email"] == "pessoa@example.com"
    assert candidate["category"] == "PRIVACY_DATA"
    assert candidate["full_message_body_persisted"] is False
    assert candidate["draft_ack"]["send_authorized"] is False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        _self_test()
        print("SUPPORT_OPS_AUTOPILOT_V1_SELF_TEST=PASS")
        return 0

    if not args.input or not args.output:
        parser.error("--input and --output are required unless --self-test is used")

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    candidate = build_candidate(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("SUPPORT_OPS_AUTOPILOT_V1=PASS")
    print(f"OUTPUT={args.output}")
    print(f"CATEGORY={candidate['category']}")
    print("SEND_AUTHORIZED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
