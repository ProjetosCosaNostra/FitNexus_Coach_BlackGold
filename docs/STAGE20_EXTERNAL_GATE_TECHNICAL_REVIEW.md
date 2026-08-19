# FitNexus Coach BlackGold — Stage 20 External-Gate Technical Review

> **STATUS: TECHNICAL PRE-REVIEW ONLY — NO LEGAL/EXTERNAL GATE PROMOTED**
>
> This document reviews technical completeness of the five Stage 20 legal/privacy/security drafts and prepares the evidence shape needed later. It is not legal advice, does not attest compliance, and cannot change any controlled-launch gate to `ready`.

## 1. Scope reviewed

- `docs/legal/PRIVACY_NOTICE_DRAFT_LEGAL_REVIEW_REQUIRED.md`
- `docs/legal/TERMS_OF_USE_DRAFT_LEGAL_REVIEW_REQUIRED.md`
- `docs/legal/PROCESSING_ROLE_MAP_DRAFT_LEGAL_REVIEW_REQUIRED.md`
- `docs/privacy/DATA_SUBJECT_REQUEST_RUNBOOK_DRAFT.md`
- `docs/security/PERSONAL_DATA_INCIDENT_RESPONSE_RUNBOOK_DRAFT.md`

All five drafts remain useful and directionally consistent with the current FitNexus architecture, but each still depends on facts that code cannot self-grant: legal review, final processor/vendor inventory, actual production routes, named operational owners, tested workflows and stable deployment evidence.

## 2. Current official-source checkpoints

Technical review refreshed against current official Brazilian sources on 2026-08-19:

- LGPD — Lei 13.709/2018: https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709compilado.htm
- ANPD — Direitos dos Titulares: https://www.gov.br/anpd/pt-br/assuntos/titular-de-dados-1/direito-dos-titulares
- ANPD — Regulamentações vigentes: https://www.gov.br/anpd/pt-br/acesso-a-informacao/institucional/atos-normativos/regulamentacoes_anpd
- ANPD — Comunicação de Incidente de Segurança: https://www.gov.br/anpd/pt-br/canais_atendimento/agente-de-tratamento/comunicado-de-incidente-de-seguranca-cis
- Resolução CD/ANPD nº 15/2024 — comunicação de incidentes.
- Resolução CD/ANPD nº 18/2024 — atuação do encarregado.
- Resolução CD/ANPD nº 19/2024 — transferência internacional de dados e cláusulas-padrão contratuais.

These sources are review anchors, not automatic legal conclusions for FitNexus.

## 3. Privacy notice — technical completeness

Already strong:

- identifies account, coach, student, feedback, billing and growth data categories;
- explicitly treats health-related information as potentially sensitive;
- separates operational purpose from marketing reuse;
- describes tenant isolation, RLS, minimization and no service-role secret in Flutter;
- keeps legal bases and controller/operator roles open instead of fabricating them.

Still required before production review can close:

1. **Processor/subprocessor inventory**: actual provider, service, purpose, data categories, data location, contractual role and retention.
2. **International-transfer inventory**: determine whether any active provider causes transfer outside Brazil. If yes, record destination, purpose, mechanism and the transparency information required by the current ANPD transfer regulation. Do not infer transfer merely from a vendor brand.
3. **Retention matrix**: operational retention, financial/security holds, backup expiry and deletion/anonymization behavior by data class.
4. **Published privacy route**: stable production URL, effective version, publication date and digest.
5. **Contact/encarregado decision**: document whether a formal encarregado is required/designated or whether a lawful small-agent exemption is relied upon. In either case, the titular contact channel must be stable and operational.
6. **Cookie/local-storage inventory**: verify actual browser/PWA storage and analytics behavior before making any cookie/storage statement.
7. **Purpose → legal-basis map**: must be reviewed outside code, especially for potentially sensitive health data.

`legal_privacy_notice` remains `BLOCKED`.

## 4. Terms of Use — technical completeness

Already strong:

- preserves professional human authority over prescription;
- avoids claiming medical diagnosis or guaranteed physical outcome;
- keeps payment, liability, consumer-law and forum clauses open for legal review;
- aligns plan/entitlement behavior with backend authority instead of UI-only promises.

Still required before production review can close:

1. Final contracting party identification and business details.
2. Who may create an account, including age/capacity and any professional-qualification requirement.
3. Actual billing provider/payment methods and commercial rules for renewal, cancellation, refund, chargeback, delinquency and grace/read-only behavior.
4. Price-change/grandfathering policy for existing customers.
5. Support scope, service availability language and any SLA only if one is actually offered.
6. Data export/termination window and backup-expiry behavior synchronized with the retention matrix.
7. Contract acceptance/version evidence and stable public route.

`legal_terms_of_use` remains `BLOCKED`.

## 5. Processing-role map — technical completeness

Already strong:

- correctly treats controller/operator role as processing-specific rather than one global label;
- separates FitNexus own-account/security/billing purposes from student data managed by the coach;
- flags sensitive data, AI and international-transfer questions instead of pre-deciding them.

Required structured record before legal review can close:

For every processing purpose, maintain at least:

- purpose identifier;
- data-subject category;
- personal-data categories and whether sensitive;
- source of data;
- FitNexus role hypothesis;
- coach/organization role hypothesis;
- legal-basis candidate for legal review;
- processor/subprocessor recipients;
- international-transfer destination/mechanism if any;
- retention rule;
- security controls;
- DSR owner/routing;
- incident owner/routing.

For student data where FitNexus is intended to act as operator, the production contract must match the actual instructions and technical behavior. A label in a document cannot override real decision-making authority.

`legal_role_mapping` remains `BLOCKED`.

## 6. Data-subject request runbook — technical completeness

The draft already protects tenant isolation, proportionate identity verification, immutable evidence and non-universal deletion.

Technical work still required:

1. Stable public intake channel and named owner/backup owner.
2. Request ID, timestamps, status and immutable receipt model.
3. Identity-verification procedure proportionate to the requested action.
4. Tenant-scoped authoritative export path.
5. Controlled correction path.
6. Deletion/anonymization/blocking workflow with retention holds and backup semantics.
7. Secure controller/operator handoff with evidence.
8. Configurable deadline/SLA policy reviewed against the current law rather than scattered hard-coded timers.
9. One tabletop request covering access plus one destructive request scenario.

Current ANPD material distinguishes immediate confirmation/access from a more complete statement within the applicable statutory period (including the 15-day framework for specified information). Automation should therefore use a reviewed policy/configuration, not an unreviewed magic number in UI code.

`data_subject_request_channel` remains `BLOCKED`.

## 7. Personal-data incident response — technical completeness

The current runbook already contains the essential separation between operator and controller, evidence preservation, relevant-risk assessment, three-business-day controller communication checkpoint and five-year incident-record retention checkpoint.

Add to the operational implementation before promotion:

1. Named incident commander, privacy/legal owner and technical owner plus backups.
2. Severity/risk decision matrix with explicit `confirmed / unknown / not-applicable` evidence fields.
3. Operator → controller handoff receipt without unjustified delay when FitNexus is operator.
4. Controller communication timer based on the current three-business-day rule when communication is required.
5. Preliminary + complementary communication path when complete facts are unavailable, including the current complementary-information window.
6. Immutable incident registry retained for the applicable regulatory period, including incidents that are not communicated.
7. Evidence pack: timeline, impacted tenants/data categories, containment actions, decision rationale, communications, recovery and postmortem.
8. Tabletop drills for cross-tenant exposure, credential compromise and potentially sensitive student data.

`incident_response` remains `BLOCKED`.

## 8. International transfer and encarregado are cross-cutting gates

Two items must not remain implicit:

### International transfer

If actual production processing transfers personal data internationally, the approved role/privacy/vendor map must record the lawful transfer mechanism and required transparency. Resolução CD/ANPD nº 19/2024 is the current technical/legal review anchor. No transfer should be invented from assumptions about a provider; resolve it from the contracted production architecture.

### Encarregado / titular contact channel

The production posture must explicitly document either:

- formal indication/contact of the encarregado when applicable; or
- the legal basis for a valid exemption when applicable, while still maintaining the required titular communication channel.

This is an external/legal decision, not a code-generated attestation.

## 9. Evidence placeholders prepared

The machine-readable template is:

`04_backend_supabase/external_gate_evidence_placeholders.json`

It intentionally contains **no evidence refs, no digests and no `ready` state**. It only declares what future reviewers/operators must supply before a dedicated evidence migration can promote a gate.

CI validates that this template cannot silently become self-attestation through:

`04_backend_supabase/tools/verify_external_gate_evidence_placeholders.py`

## 10. Exit condition for this pre-review

This technical pre-review is complete when:

- all five drafts are structurally reviewable;
- required missing operational facts are explicit;
- evidence fields exist as placeholders only;
- CI proves the placeholder template contains no attestation;
- all controlled-launch gates remain unchanged.

No evidence migration is created in this step.
