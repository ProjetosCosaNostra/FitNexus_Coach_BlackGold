# FitNexus Coach BlackGold — Stage81 Sensitive Data Treatment Review Questionnaire

> **STATUS:** REVIEW_INTAKE_ONLY_NOT_LEGAL_ADVICE_NOT_POLICY_NOT_GATE_EVIDENCE  
> **DO NOT PREPOPULATE OR RECOMMEND A LEGAL CLASSIFICATION.**  
> Este questionário existe para uma revisão independente real por **legal** e **privacy**. Ele não deve ser preenchido por CI, automação, engenharia ou IA em nome dos revisores.

## 1. Objetivo e fronteira

O Stage80 identificou superfícies técnicas que podem conter, herdar, referenciar ou receber informação potencialmente sensível. O Stage81 apenas estrutura a coleta de uma futura revisão humana independente. Nenhuma pergunta abaixo contém resposta jurídica sugerida, prazo recomendado, base legal presumida, regra de consentimento presumida, conclusão controlador/operador, autorização de IA externa, autorização de marketing ou decisão de notificação de incidente.

Uma revisão concluída ainda produz somente material para **aceitação canônica independente posterior**. O digest do coletor não é, por si só, classificação jurídica, política aprovada, evidência de gate nem autorização de lançamento.

## 2. Fontes técnicas vinculadas

- Stage80R1 reconciliation addendum: preserva o histórico e aponta o registry Stage80 corrente.
- Stage80 technical sensitive-data registry: 7 superfícies table-backed + 2 superfícies non-table.
- Open decision: `SENSITIVE_DATA_TREATMENT`, que permanece `OPEN` e depende de `independent legal/privacy review`.

## 3. Participantes mínimos da sessão real

A sessão deve ter exatamente estes papéis de revisão, com referências rastreáveis mantidas fora do repositório:

1. `legal_review`
2. `privacy_review`

O mesmo indivíduo não deve ser assumido automaticamente para ambos os papéis. Qualquer acumulação precisa ser uma decisão operacional real, documentada fora do repositório. O coletor não valida qualificação profissional; ele apenas prova que materiais e referências foram fornecidos.

## 4. Perguntas obrigatórias para cada superfície

Para **cada uma das nove superfícies**, os revisores devem registrar respostas próprias, sem copiar uma conclusão padrão entre superfícies:

1. **legal_classification_review** — qual classificação jurídica os revisores entendem aplicável ao conteúdo/fluxo real e quais incertezas permanecem?
2. **processing_purpose_review** — quais finalidades reais são permitidas, necessárias ou devem ser limitadas?
3. **minimization_rule_review** — quais regras técnicas de minimização do Stage80 são aceitas, modificadas ou rejeitadas e por quê?
4. **legal_basis_or_consent_review** — qual análise de base legal, consentimento ou outra condição aplicável foi feita? Não presumir que consentimento é sempre necessário ou sempre suficiente.
5. **disclosure_recipient_review** — quais destinatários/compartilhamentos são aceitáveis, proibidos ou condicionados?
6. **external_ai_review** — IA externa pode receber algum conteúdo dessa superfície? Sob quais condições, se houver? Ausência de resposta não autoriza uso.
7. **marketing_review** — algum conteúdo ou derivado pode ser usado em analytics, attribution, targeting ou advertising? Ausência de resposta não autoriza uso.
8. **controller_processor_dependency_ref** — referência para a conclusão/dependência da matriz controlador↔operador; não repetir a conclusão jurídica no receipt técnico.
9. **retention_dependency_ref** — referência para a decisão de retenção/legal hold aplicável; Stage81 não define prazo.
10. **incident_dependency_ref** — referência para obrigações de incident handling/communication aplicáveis; Stage81 não decide notificação.
11. **review_material_ref** — referência do material real que sustenta a resposta desta superfície.

Também deve ser registrado `review_alignment_state` como uma das duas condições factuais da sessão:
- `CONSENSUS_RECORDED`
- `UNRESOLVED_DIFFERENCE_RECORDED`

`UNRESOLVED_DIFFERENCE_RECORDED` é permitido como resultado de uma revisão real, porém confirma que a matéria continua sem conclusão canônica.

## 5. Superfícies Stage80 a revisar

### 5.1 `student_profile_objective_and_context`

**Fonte técnica:** `public.students` — campos como `name`, `email`, `objective`, `level`, `last_workout`, `next_session`, `status`.

**Risco técnico observado:** campos de objetivo/contexto podem revelar limitações, saúde ou outra informação sensível conforme o conteúdo real.

**Minimização técnica candidata para revisão:** coletar apenas o necessário; evitar narrativa de saúde/lesão em campo genérico quando um campo mais restrito bastar; preservar tenant/purpose boundaries; não copiar conteúdo de perfil para growth, advertising ou engineering receipts.

### 5.2 `training_prescription_notes_and_lineage`

**Fonte técnica:** `public.training_plans`, `public.training_plan_lineage` — `student_id`, `notes`, `next_session`, `decision_reason`, `trigger_context`.

**Risco técnico observado:** notas de prescrição, motivos e contexto de lineage podem codificar lesão, dor, limitação ou outro contexto sensível.

**Minimização técnica candidata para revisão:** evitar narrativa diagnóstica desnecessária; limitar lineage ao necessário para explicar a decisão; não reutilizar contexto para advertising/unrelated analytics; manter human review para mudanças consequenciais.

### 5.3 `workout_feedback_pain_energy_and_notes`

**Fonte técnica:** `public.workout_feedback` — `perceived_exertion`, `pain_score`, `energy_score`, `pain_location`, `note`.

**Risco técnico observado:** dor/localização, esforço, energia e texto livre são candidatos de alta sensibilidade no contexto do produto.

**Minimização técnica candidata para revisão:** coletar somente feedback necessário; não inferir diagnóstico; não enviar feedback a UTM/advertising/log desnecessário; separar feedback de growth e billing.

### 5.4 `decision_intelligence_context_and_outcomes`

**Fonte técnica:** `public.decision_intelligence_runs`, `public.decision_intelligence_outcomes` — `brief`, `outcome`, `note` e referências de estudante/decisor.

**Risco técnico observado:** entradas/saídas podem herdar contexto sensível mesmo sem coluna explicitamente médica.

**Minimização técnica candidata para revisão:** usar somente contexto necessário; preservar human-in-the-loop; não enviar contexto sensível a IA externa antes de gates apropriados; preferir resumo/sinal limitado a cópia integral de registros.

### 5.5 `coach_action_notes`

**Fonte técnica:** `public.coach_action_events` — `student_id`, `resolution`, `note`, `created_by`.

**Risco técnico observado:** notas de ação podem duplicar contexto sensível originado em outra superfície.

**Minimização técnica candidata para revisão:** armazenar somente contexto necessário; evitar duplicar narrativas completas de dor/lesão; não usar notas como atributo de marketing; manter tenant-scoped access.

### 5.6 `student_access_security_identifiers_and_alerts`

**Fonte técnica:** `public.student_access_links` e tabelas privadas de security events/signals/alert receipts.

**Risco técnico observado:** security telemetry pode identificar/vincular estudante e criar vazamento se payloads carregarem narrativa de coaching/saúde.

**Minimização técnica candidata para revisão:** usar identificadores/fingerprints e metadata limitada; não colocar raw token/secret em receipt; não incluir dor/lesão/workout note em alerta externo; manter somente campos necessários para detecção/investigação e retenção revisada.

### 5.7 `growth_attribution_and_marketing_boundary`

**Fonte técnica:** `private.growth_events`, `private.growth_attribution`, `private.growth_capture_failures`.

**Risco técnico observado:** source/term/content ou eventos podem receber indevidamente texto sensível ou health/fitness targeting derivado.

**Minimização técnica candidata para revisão:** nunca codificar dor, lesão, saúde ou workout notes em UTM/source/term/content; não usar informação sensível de estudante para ad targeting; growth events não são autoridade de external readiness; usar somente identificadores/eventos mínimos após revisão aplicável.

### 5.8 `support_and_dsr_free_form_ingress`

**Fonte documental:** drafts de privacy/role mapping que tratam suporte, solicitações de direitos e orientação para não enviar excesso.

**Risco técnico observado:** usuário pode enviar voluntariamente conteúdo sensível em canal de suporte ou direitos mesmo sem solicitação do produto.

**Minimização técnica candidata para revisão:** pedir só o necessário para autenticar/resolver; orientar a não enviar detalhe excessivo de saúde/treino; separar prova de identidade de conteúdo de suporte; evitar copiar submissão sensível bruta para engineering receipts.

### 5.9 `incident_response_sensitive_data_handling`

**Fonte documental:** incident-response draft, incluindo proteção de dados potencialmente sensíveis, blast radius e cenário sintético de dados de estudante.

**Risco técnico observado:** investigação pode ampliar acesso/cópia de conteúdo sensível se blast-radius e evidence collection não forem minimizados.

**Minimização técnica candidata para revisão:** inspecionar apenas o necessário para estabelecer fatos; preferir referências/digests minimizados; não copiar secrets ou dados de tenant não relacionado; exercícios permanecem synthetic/non-customer até autoridade real.

## 6. Conclusão global da sessão

Ao final, registrar fora do repositório:

- referência rastreável da sessão;
- data/hora timezone-aware;
- materiais dos dois participantes;
- estado de conclusão (`COMPLETED_WITH_CONCLUSIONS` ou `COMPLETED_WITH_UNRESOLVED_ITEMS`);
- referência para itens não resolvidos, mesmo quando vazia por decisão real documentada;
- referência para material global da revisão.

## 7. O que esta revisão NÃO faz automaticamente

Mesmo uma sessão real completa não deve, por automação:

- fechar `SENSITIVE_DATA_TREATMENT`;
- aprovar o Aviso de Privacidade;
- aprovar a Processing Role Matrix;
- aprovar Incident Response;
- selecionar política de retenção;
- autorizar IA externa com dados sensíveis;
- autorizar marketing/ads com dados sensíveis;
- criar evidence ref/digest oficial de gate;
- criar migration de evidência;
- autorizar controlled launch, paid media ou production deployment.

A etapa seguinte, caso exista material real, é **aceitação canônica independente** em fronteira separada e fail-closed.
