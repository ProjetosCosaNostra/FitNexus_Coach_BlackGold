# FitNexus Coach BlackGold — Stage 20 Controlled Launch Admission

## Purpose

Stage 20 prevents technical progress from being mistaken for permission to launch commercially or spend on ads.

Stage 19 made the tracking core real. Stage 17 made pricing experiment authority real. Neither of those facts is sufficient for public launch. The controlled-launch admission layer now evaluates independent authorities and remains fail-closed until every mandatory gate is evidenced.

## Mandatory gates

The initial controlled-launch contract contains nine mandatory gates:

1. `tracking_core` — automatic;
2. `pricing_experiment` — automatic;
3. `billing_provider_credentials` — external authorization;
4. `legal_privacy_notice` — evidence migration;
5. `legal_terms_of_use` — evidence migration;
6. `legal_role_mapping` — evidence migration;
7. `data_subject_request_channel` — evidence migration;
8. `incident_response` — evidence migration;
9. `production_deployment` — evidence migration.

## Authority separation

Automatic gates are derived from authoritative runtime state:

- tracking requires both `landing_view` and `signup_started` to be `public_capture / active`;
- pricing requires one current BRL decision with all six monthly/annual Solo/Pro/Studio offers;
- billing credentials require the selected BR V1 Asaas authority to be `active` with an activation timestamp.

Legal, privacy, security and deployment gates are **not runtime self-attestable**. They are represented by `private.controlled_launch_gate_evidence` and can move to `ready` only through a deliberate versioned migration containing an evidence reference and digest.

That evidence-as-code rule makes legal/release admission changes reviewable in Git history and prevents a normal client or runtime service from granting itself launch permission.

## Current remote state

At Stage 20 bootstrap:

- tracking core: **READY**;
- pricing experiment: **READY**;
- Asaas credential authority: **BLOCKED** (`selected_pending_credentials`);
- privacy notice legal review: **BLOCKED**;
- terms legal review: **BLOCKED**;
- processing-role mapping legal review: **BLOCKED**;
- data-subject request channel: **BLOCKED**;
- incident-response drill/evidence: **BLOCKED**;
- production deployment attestation: **BLOCKED**.

Therefore the current launch posture is **2 of 9 mandatory gates ready** and the product remains **BLOCKED** for controlled public launch/ad admission.

## Ads remain a separate authority

The evaluator carries explicit guardrails:

- tracking readiness is not launch authority;
- pricing readiness is not checkout authority;
- external billing authorization remains mandatory;
- legal review evidence is migration-owned;
- paid ads never auto-launch.

Even when the nine launch gates eventually become ready, `READY_FOR_CONTROLLED_ADMISSION` means the system is eligible for a deliberate human-controlled launch/admission decision. It is not an automatic campaign creation instruction.

## Legal preparation posture

Stage 20 also prepares draft operational/legal artifacts from current official Brazilian sources, but they remain visibly marked **DRAFT — LEGAL REVIEW REQUIRED**.

They do not move a legal gate to `ready` merely by existing in the repository.

Current official source anchors used for preparation include:

- LGPD, Law 13.709/2018: https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm
- ANPD data-subject rights guidance: https://www.gov.br/anpd/pt-br/assuntos/direitos-dos-titulares
- ANPD security incident communication guidance: https://www.gov.br/anpd/pt-br/assuntos/incidente-de-seguranca
- ANPD Resolution CD/ANPD 15/2024: https://www.in.gov.br/en/web/dou/-/resolucao-cd/anpd-n-15-de-24-de-abril-de-2024-556243024

## Evidence ownership

`private.controlled_launch_gate_catalog` defines what must be true.

`private.controlled_launch_gate_evidence` stores only reviewed evidence state for non-automatic gates.

The service-role readiness RPC is read-only. No public attestation RPC exists. This is deliberate: the runtime cannot mark legal/privacy/security/deployment gates ready by itself.

## Permanent prevention classes

- `BGF-LAUNCH-ADMISSION-FILE-MISSING-130`: controlled-launch authority artifacts cannot disappear silently.
- `BGF-LAUNCH-GATE-MISSING-131`: the mandatory release-gate set cannot shrink accidentally.
- `BGF-LAUNCH-EVIDENCE-AUTHORITY-132`: legal/privacy/security/deployment evidence remains migration-owned and runtime roles cannot write it directly.
- `BGF-LAUNCH-READY-WITHOUT-EVIDENCE-133`: an evidence gate cannot be `ready` without evidence reference + digest.
- `BGF-LAUNCH-TRACKING-AUTHORITY-134`: tracking readiness derives from actual active public capture authority.
- `BGF-LAUNCH-PRICING-AUTHORITY-135`: pricing readiness derives from complete current decision lineage.
- `BGF-LAUNCH-BILLING-AUTHORITY-136`: billing readiness requires externally activated Asaas authority, not provider selection alone.
- `BGF-LAUNCH-AUTHORITY-SEPARATION-137`: tracking, pricing, billing and launch authority cannot collapse into one boolean.
- `BGF-LAUNCH-LEGAL-SELF-ATTESTATION-138`: runtime/client code cannot self-attest legal review.
- `BGF-LAUNCH-PAID-ADS-AUTO-139`: readiness never auto-creates or auto-launches paid advertising.
- `BGF-LAUNCH-STATE-SEMANTICS-140`: controlled-launch readiness and controlled-admission readiness retain explicit semantics.
- `BGF-LAUNCH-RPC-AUTHORITY-141`: launch-readiness RPC remains service-role-only and read-only.

## Next gate work

The next internal work is to prepare privacy notice, terms, processing-role map, data-subject request workflow and incident-response runbook as reviewable drafts. Those artifacts must remain blocked until actual legal/operational review evidence is available.

The Asaas credential boundary is a separate external authorization and cannot be fabricated by code or database migration.
