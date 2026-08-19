# FitNexus Coach BlackGold — Personal Data Incident Response Runbook

> **STATUS: DRAFT / NOT YET TABLETOP-TESTED — GATE REMAINS BLOCKED**

## Purpose

Contain, investigate and document security incidents involving personal data without improvising legal decisions during an emergency.

This runbook is operational preparation, not legal advice. Notification decisions must follow the current LGPD/ANPD rules and the approved controller/operator role map.

## Trigger examples

Open an incident when there is credible evidence of, for example:

- unauthorized tenant/data access;
- leaked credentials/tokens/secrets;
- accidental public exposure;
- unauthorized alteration/deletion;
- compromised admin/service account;
- payment/webhook authority abuse;
- backup exposure;
- vulnerability exploited against personal-data systems;
- loss of confidentiality, integrity or availability with personal-data impact.

## Immediate actions

1. Create incident ID and UTC/BRT timestamps.
2. Preserve logs/evidence before destructive remediation when safe.
3. Contain credentials, routes, keys or accounts involved.
4. Protect other tenants and stop active exfiltration/abuse.
5. Record every high-impact action and operator.
6. Do not notify publicly before facts/risk/role ownership are sufficiently established unless required by law/emergency.
7. Do not erase evidence to make a dashboard look clean.

## Initial classification

Capture only confirmed or explicitly uncertain facts:

- systems affected;
- controller/operator role for the affected processing;
- categories of personal data;
- whether sensitive data may be involved;
- approximate number of affected data subjects/records if known;
- confidentiality/integrity/availability impact;
- malicious vs accidental evidence;
- containment status;
- likely consequences;
- cross-border/vendor involvement;
- whether children/adolescents or vulnerable groups are implicated.

## Controller/operator handoff

The current ANPD incident regulation requires operators to inform the controller without undue delay and provide information necessary for the controller to meet legal obligations.

If FitNexus is acting as operator for customer-controlled student data, the incident workflow must therefore identify the customer/controller quickly and preserve evidence of the notification/handoff.

If FitNexus is controller for the affected processing, it owns the controller-side assessment/communication workflow.

The definitive role mapping remains a legal gate.

## ANPD communication decision

Under the current ANPD regulation, a controller must communicate a security incident to the ANPD and affected data subjects when the incident may cause relevant risk or damage, subject to the regulation and other applicable rules.

Current ANPD guidance/regulation uses a **three-business-day** communication period counted under the applicable rule, except where specific legislation provides another period. Do not hard-code a countdown into product automation until legal review confirms how the rule applies to the actual incident and controller role.

When required, prepare the information requested by the regulation/guidance, including as applicable:

- nature/categories of affected personal data;
- affected data subjects/approximate quantity;
- technical/security measures used, respecting legitimate secrecy;
- risks/consequences;
- reasons for any delayed communication;
- measures taken or planned to reverse/mitigate effects;
- incident date/time and discovery timeline;
- controller/contact information required by the regulator.

Use the current ANPD electronic communication channel and current official form/instructions at incident time.

## Data-subject communication

If notification to affected data subjects is required:

- use clear/plain language;
- identify material risks and protective actions;
- do not expose another person's data in the notice;
- provide a trustworthy contact channel;
- coordinate timing/content with regulator requirements and incident containment.

## Evidence retention

The current ANPD incident regulation requires controllers to maintain a record of security incidents, including incidents not communicated, for at least the regulatory period (currently five years under Resolution CD/ANPD 15/2024), subject to applicable rules.

The production runbook must map this requirement to an immutable/controlled incident-evidence store and backup policy.

## Post-incident

1. Confirm containment and recovery.
2. Validate tenant isolation and credential rotation.
3. Identify root cause and failure class.
4. Fix the immediate defect.
5. Add permanent prevention/static/runtime regression.
6. Record monitoring/alerting improvements.
7. Review whether processors/subprocessors/contracts need updates.
8. Update legal/privacy notices only if materially necessary.
9. Conduct postmortem without hiding contributing failures.
10. Verify restored service and rollback path.

## BlackGold construction rule

Every incident-class defect must become a permanent engineering mechanism when feasible: prevention, detection, test, recovery, evidence and observability.

## Tabletop drill required before gate promotion

`incident_response` remains blocked until a tabletop drill produces evidence for at least:

- cross-tenant exposure scenario;
- service credential compromise;
- potentially sensitive student-data exposure;
- controller/operator routing decision;
- ANPD/data-subject notification decision tree;
- evidence-preservation/rollback steps;
- final receipt and digest.

## Official sources for review

- LGPD: https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm
- ANPD — Comunicação de Incidente de Segurança: https://www.gov.br/anpd/pt-br/assuntos/incidente-de-seguranca
- Resolução CD/ANPD nº 15/2024: https://www.in.gov.br/en/web/dou/-/resolucao-cd/anpd-n-15-de-24-de-abril-de-2024-556243024

## Gate

`incident_response = BLOCKED`
