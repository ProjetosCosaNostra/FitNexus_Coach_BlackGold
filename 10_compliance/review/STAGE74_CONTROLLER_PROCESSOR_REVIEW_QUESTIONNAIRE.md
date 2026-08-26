# FitNexus Coach BlackGold — Questionário de Revisão Independente — Controller / Processor

> **STATUS:** NON_ATTESTING_REVIEW_INTAKE_QUESTIONNAIRE_NOT_LEGAL_EVIDENCE  
> Este material organiza perguntas para revisão jurídica/privacidade independente. Ele não contém conclusão jurídica, não aprova documentos, não cria versão vigente e não fecha gates.

## Escopo desta revisão

Decisão aberta autoritativa: `CONTROLLER_PROCESSOR_ROLE_MATRIX`.

A decisão aparece em quatro gates ainda bloqueados:

- `legal_privacy_notice`
- `legal_role_mapping`
- `data_subject_request_channel`
- `incident_response`

A revisão deve considerar conjuntamente, pelos bytes exatos apresentados ao revisor:

1. `PRIVACY_NOTICE_CANDIDATE_PTBR.md`
2. `PROCESSING_ROLE_MATRIX_CANDIDATE.md`
3. `DATA_SUBJECT_REQUEST_RUNBOOK_CANDIDATE.md`
4. `INCIDENT_RESPONSE_RUNBOOK_CANDIDATE.md`
5. `COMPLIANCE_OPEN_DECISIONS.json`

## Perguntas obrigatórias ao revisor independente

### A. Papéis por fluxo e finalidade

1. Para cada fluxo listado na matriz candidata, qual papel jurídico do FitNexus deve ser adotado: controlador, operador/processador, controlador independente, controladoria conjunta ou outra classificação aplicável?
2. Qual papel deve ser atribuído ao coach/organização em cada um desses mesmos fluxos?
3. Há algum fluxo em que o papel varie conforme configuração, contrato, origem do dado ou finalidade concreta? Se sim, quais condições precisam ficar explícitas?
4. Quais finalidades não podem compartilhar uma classificação global e exigem análise separada?

### B. Base jurídica e dados potencialmente sensíveis

5. Para cada finalidade material, qual base jurídica deve ser documentada após análise do contexto real?
6. Quais campos de treino, feedback, dor, lesão, saúde ou contexto do aluno devem ser classificados como potencialmente sensíveis e quais regras de minimização devem ser obrigatórias?
7. Há campos ou usos que devem ser proibidos, reduzidos ou separados antes de produção?
8. Quais salvaguardas adicionais devem aparecer na matriz, no aviso de privacidade ou nos runbooks para esses dados?

### C. Controller ↔ processor em direitos dos titulares

9. Quando o pedido de direito vier de um aluno ligado a um coach/organização, quem deve receber, autenticar, decidir, executar e responder ao pedido?
10. Em quais casos o FitNexus responde diretamente e em quais casos deve encaminhar ou cooperar com o controlador identificado?
11. Quais elementos mínimos o procedimento de handoff deve registrar sem revelar dados de outro tenant?
12. Quais pontos do DSR runbook candidato precisam mudar para refletir a classificação aprovada?

### D. Controller ↔ processor em incidentes

13. Em um incidente de exposição entre tenants, comprometimento de credencial ou dado potencialmente sensível, quem conduz contenção, avaliação de risco, decisão regulatória e comunicação?
14. Quais obrigações de cooperação e prazos contratuais/operacionais devem ser definidos entre FitNexus e coach/organização, sem presumir automaticamente obrigação legal não revisada?
15. Quais pontos do Incident Response runbook candidato precisam mudar para refletir a classificação aprovada?

### E. Subprocessadores, transferências e infraestrutura

16. Quais fornecedores atualmente previstos devem ser tratados como subprocessadores, operadores ou controladores independentes em cada fluxo relevante?
17. Que informações de região, contrato, retenção e transferência internacional precisam estar documentadas antes da aprovação do aviso/matriz?
18. A classificação dos eventos de segurança, logs, autenticação e prevenção de fraude exige finalidade própria do FitNexus? Se sim, quais limites devem ser formalizados?

### F. Retenção, produto e comunicação ao usuário

19. Que responsabilidades de retenção, exclusão, backup e legal hold decorrem da classificação aprovada por fluxo?
20. Que alterações exatas são necessárias no Aviso de Privacidade candidato para explicar os papéis sem induzir o titular a uma classificação simplificada ou incorreta?
21. Há alterações correspondentes necessárias nos Termos de Uso, mesmo que `legal_terms_of_use` não esteja no fanout direto desta decisão?
22. Quais decisões relacionadas devem permanecer explicitamente abertas após esta revisão por dependerem de entidade legal, contratos, billing, subprocessadores, retenção ou outras evidências ainda inexistentes?

## Resultado esperado do revisor

O revisor deve produzir um artefato externo rastreável que:

- identifique a referência da revisão e sua data;
- declare quais bytes/digests dos candidatos foram revisados;
- responda ou referencie as respostas às perguntas acima;
- escolha um resultado entre `APPROVED_WITHOUT_CHANGES`, `APPROVED_WITH_REQUIRED_CHANGES` ou `NOT_APPROVED_REQUIRES_REVISION`;
- liste alterações obrigatórias quando aplicável;
- não inclua segredos operacionais ou credenciais.

## Limites do resultado

Mesmo `APPROVED_WITHOUT_CHANGES` não fecha automaticamente nenhum gate. A revisão ainda precisa ser vinculada às versões finais correspondentes e passar pelos revisores canônicos de cada gate antes de qualquer evidence migration. Se houver mudança nos bytes candidatos, os novos bytes precisam de novo vínculo/revisão; este questionário não autoriza autopromoção de documentos ou gates.
