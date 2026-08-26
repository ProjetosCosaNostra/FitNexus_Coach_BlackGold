# FitNexus Coach BlackGold — Stage79 Retention Decision Review Questionnaire

> **STATUS:** REVIEW_INTAKE_QUESTIONNAIRE_NOT_POLICY_NOT_LEGAL_EVIDENCE  
> Este material organiza perguntas para revisão real de legal/privacy/operations. Ele não aprova prazo, base legal, legal hold, janela de backup, regra de cancelamento ou eliminação e não fecha `RETENTION_MATRIX`.

## 1. Regra central

A Stage78 inventariou superfícies técnicas e marcadores de ciclo de vida. Campos como `created_at`, `expires_at`, `revoked_at`, `status`, `is_active` e timestamps de eventos **não são política de retenção por si só**.

**DO NOT PREPOPULATE OR RECOMMEND A DURATION.**  
Nenhum prazo em dias/meses/anos deve ser sugerido por este questionário. Cada critério precisa vir de revisão real e rastreável.

## 2. Referências obrigatórias da revisão

A cópia preenchida deve permanecer fora do repositório e registrar referências rastreáveis para:

- revisão jurídica;
- revisão de privacidade/proteção de dados;
- revisão operacional;
- artefato(s) fonte usados para fundamentar cada decisão;
- data/hora da sessão de revisão;
- referência da sessão/review package.

Nomes, caminhos de arquivos e conteúdo bruto não devem ser copiados para receipts de engenharia; o intake Stage79 aceita somente bindings SHA-256 desses materiais.

## 3. Perguntas obrigatórias por categoria Stage78

Responder para **cada** uma das dez categorias abaixo:

1. `account_and_tenancy`
2. `student_identity_and_coaching_profile`
3. `training_prescription_templates_and_lineage`
4. `workout_execution_history`
5. `potentially_sensitive_workout_feedback`
6. `decision_intelligence_and_coach_action_history`
7. `student_access_security_and_abuse_telemetry`
8. `growth_attribution_and_funnel_telemetry`
9. `billing_subscription_and_webhook_history`
10. `governance_and_gate_evidence_metadata`

Para cada categoria, a revisão deve fornecer, sem deixar implícito:

- critério de retenção aprovado para futura redação de política;
- referência da finalidade/autoridade que sustenta o critério;
- efeito de encerramento/cancelamento da conta ou relação;
- efeito de inadimplência quando aplicável;
- regra de backup/expurgo aplicável ou declaração revisada de não aplicabilidade;
- regra de legal hold/preservação aplicável ou declaração revisada de não aplicabilidade;
- ação ao fim do critério: eliminação, anonimização, bloqueio, preservação justificada ou outra decisão revisada;
- exceção própria para segurança/auditoria, quando houver, ou declaração revisada de não aplicabilidade;
- referência do material de revisão que suporta a decisão;
- confirmação de que a decisão está completa para **drafting**, não para promoção automática de gate.

## 4. Superfícies não tabulares obrigatórias

A revisão também deve decidir explicitamente sobre:

- `backup_restore_and_expiration` — janela/critério de backup e expurgo, responsabilidades e dependências de provider/infra;
- `scheduled_cleanup_or_purge` — mecanismo operacional esperado para aplicar decisões de retenção, inclusive quando não houver `pg_cron` ou rotina SQL nomeada.

A ausência atual de buckets de Storage, de `pg_cron` ou de rotinas com nomes `delete/cleanup/purge/prune/expire/retention` **não** responde essas perguntas.

## 5. Pontos sensíveis que exigem decisão explícita

A revisão deve tratar separadamente, quando aplicável:

- dor, lesão, localização de dor, feedback e notas potencialmente sensíveis;
- histórico/lineage de prescrições e decisões do coach;
- trilhas de segurança, antiabuso, idempotência e auditoria;
- growth/attribution, com a regra de não transportar conteúdo sensível para marketing;
- referências de billing/webhooks após ativação real do provider;
- dados necessários para DSR, disputa, segurança, obrigação própria ou legal hold.

## 6. Condições de fail-closed

A revisão deve permanecer **incompleta** se qualquer categoria/superfície não possuir referência rastreável. Não inferir prazo a partir de lifecycle markers técnicos. Não usar ausência atual de clientes como justificativa para omitir política futura. Não tratar um review packet ou digest como `legal_privacy_notice`, `data_subject_request_channel` ou `incident_response` evidence.

## 7. Resultado permitido nesta etapa

Um input Stage79 real pode gerar apenas um candidato digest-only com estado:

`REAL_EXTERNAL_RETENTION_REVIEW_MATERIAL_DIGESTS_BOUND_AWAITING_CANONICAL_INDEPENDENT_ACCEPTANCE_NOT_POLICY_EVIDENCE`

Mesmo nesse estado:

- `RETENTION_MATRIX` continua OPEN;
- nenhum documento de privacidade é promovido automaticamente;
- nenhuma migration de evidence é criada;
- nenhum gate é marcado READY;
- nenhuma ação de produção, provider, Supabase mutation, controlled launch ou paid media é autorizada.
