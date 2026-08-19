# FitNexus Coach BlackGold — Data Subject Request Runbook

> **STATUS: DRAFT / NOT YET TESTED — GATE REMAINS BLOCKED**

## Objective

Provide an auditable workflow for requests involving personal data while preventing disclosure to the wrong person, accidental destruction of evidence, or silent loss of deadlines.

Provisional privacy contact:

`projetoscosanostra@gmail.com`

The production channel must be deliberately published and tested before `data_subject_request_channel` can become `ready`.

## Request classes to route

Examples include:

- confirmation that processing exists;
- access;
- correction;
- information about processing/sharing;
- portability where applicable and regulated;
- anonymization, blocking or deletion where legally applicable;
- objection/review requests where applicable;
- revocation of consent when consent is actually the lawful basis;
- questions about how a coach/organization and FitNexus divide responsibility for student data.

## Intake workflow

1. Create an internal request ID and timestamp.
2. Record only the minimum information necessary to route the request.
3. Identify whether the requester is a coach/account holder, organization member, student, former user or other data subject.
4. Verify identity proportionately before disclosing or changing personal data.
5. Identify the relevant organization/tenant without exposing another tenant.
6. Classify which party is expected to answer the request under the approved controller/operator role map.
7. Preserve any data subject to legal/security/financial hold before deletion or alteration.
8. Gather authoritative data from backend sources, not screenshots/local browser state.
9. Record response, legal/operational rationale, actions performed and completion timestamp.
10. If another controller/operator must act, route securely and retain evidence of the handoff.

## Access requests

The production workflow should support:

- a simplified confirmation/access response when legally appropriate;
- a complete statement when required;
- tenant-scoped export only;
- no service-role secrets, password hashes, security-sensitive tokens, other tenants' identifiers or internal anti-abuse rules in the export.

The LGPD/ANPD materials should be reviewed for applicable response timing before production automation is frozen. Current official guidance references immediate simplified confirmation/access and a complete statement within the statutory framework, but product timers must be validated by legal review rather than hard-coded from this draft.

## Correction requests

- validate the target field and tenant;
- distinguish editable business data from immutable audit/billing evidence;
- record old/new value only where audit policy permits;
- propagate corrections to processors when legally/contractually required.

## Deletion / anonymization / blocking

Never implement “delete everything” as an automatic universal response.

Before action, evaluate:

- whether the requester/organization has authority;
- whether a legal basis/retention obligation requires preservation;
- whether financial/security/audit evidence must remain;
- backup retention/expiry;
- whether data can be anonymized instead;
- operator/controller instructions for student data.

## Sensitive data

Requests touching pain, injury/health context or other potentially sensitive fields receive elevated privacy review. Do not include these fields in generic analytics exports.

## Security safeguards

- no response based solely on possession of an unverified e-mail address;
- no cross-tenant search result disclosure;
- no raw database dumps to users;
- no secrets/API keys/service-role material in exports;
- actions must be logged and reversible where appropriate;
- suspicious requests may be escalated to security review before disclosure.

## Evidence required to promote the gate

Before `data_subject_request_channel = ready`:

- stable published contact route;
- role ownership assigned;
- identity-verification procedure approved;
- tenant-scoped export/correction/deletion paths tested;
- retention exceptions documented;
- one tabletop/test request completed with receipt;
- reviewed response-time rules documented;
- evidence digest recorded by a dedicated migration.

## Official review sources

- LGPD, especially data-subject rights: https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm
- ANPD — Direitos dos Titulares: https://www.gov.br/anpd/pt-br/assuntos/direitos-dos-titulares

## Gate

`data_subject_request_channel = BLOCKED`
