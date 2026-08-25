# FitNexus Coach BlackGold — Incident Response Runbook — CANDIDATO NÃO OPERACIONAL

> **STATUS OBRIGATÓRIO:** DRAFT_UNREVIEWED_NOT_OPERATIONAL_EVIDENCE  
> Este runbook prepara o gate `incident_response`. Ele não prova owner assignment, não substitui tabletop, não conclui comunicação à ANPD/titulares e não fecha nenhum gate.

## 1. Papéis exigidos antes de produção

- Incident Commander: **PENDENTE DE ATRIBUIÇÃO REAL**.
- Privacy/Legal Owner: **PENDENTE DE ATRIBUIÇÃO REAL**.
- Technical Owner: **PENDENTE DE ATRIBUIÇÃO REAL**.
- Backup owner(s): **PENDENTE**.
- Canal de escalonamento fora de banda: **PENDENTE**.

O mesmo indivíduo pode acumular papéis somente se a revisão de capacidade e conflito aceitar; o candidato não presume isso.

## 2. Objetivos

1. Detectar e conter impacto sem destruir evidência.
2. Proteger tenants e dados potencialmente sensíveis.
3. Preservar logs/receipts suficientes para investigação.
4. Diferenciar incidente técnico, incidente de segurança e incidente de dados pessoais.
5. Acionar controlador/operador correto conforme matriz aprovada.
6. Tomar decisão regulatória com evidência e revisão, não por automação cega.
7. Produzir postmortem e converter recorrência em guard/regressão.

## 3. Severidade — matriz candidata

A severidade final precisa de revisão, mas o tabletop deve avaliar pelo menos:

- alcance: uma conta, um tenant, vários tenants, plataforma;
- confidencialidade: houve exposição ou somente tentativa;
- integridade: houve alteração não autorizada;
- disponibilidade: indisponibilidade ou degradação;
- tipo de dado: técnico, cadastral, financeiro, potencialmente sensível;
- duração e persistência;
- exploitability/replay;
- capacidade de contenção;
- impacto ao titular e ao negócio.

Nenhum rótulo de severidade deve, sozinho, decidir notificação regulatória.

## 4. Fluxo operacional candidato

### 4.1 Detectar

Fontes possíveis: logs de segurança, alertas, suporte, CI/deploy, provider, relato de usuário ou análise manual.

Capturar: timestamp, sistema afetado, first observer, sintomas, tenant(s) potencialmente envolvidos e evidência técnica mínima. Não copiar secrets para o ticket.

### 4.2 Triage

- verificar se é falso positivo;
- identificar blast radius sem consultar dados além do necessário;
- preservar evidence refs/digests;
- classificar necessidade de contenção imediata;
- registrar hipótese e confiança separadas de fatos confirmados.

### 4.3 Conter

Ações dependem do incidente e da autoridade disponível. Exemplos técnicos possíveis, sempre com rollback/receipt quando aplicável:

- revogar/rotacionar credencial comprometida;
- bloquear rota ou token abusado;
- reduzir autoridade temporariamente;
- pausar deploy/campanha/provider afetado;
- isolar tenant/feature somente quando necessário;
- ativar modo read-only quando a arquitetura suportar.

Não apagar logs/evidências para “limpar” o incidente.

### 4.4 Erradicar e recuperar

- corrigir causa raiz, não apenas sintoma;
- provar regressão automatizada;
- restaurar por caminho conhecido;
- executar smoke e validar ausência de cross-tenant drift;
- monitorar reincidência;
- registrar exact commit/config/recovery evidence.

### 4.5 Avaliar dados pessoais e obrigações

Privacy/Legal Owner deve revisar, com base em fatos:

- categorias e titulares potencialmente afetados;
- natureza, extensão, duração e consequências;
- papel FitNexus/controlador/operador no fluxo;
- medidas de contenção e risco residual;
- obrigações contratuais e regulatórias vigentes;
- necessidade, conteúdo, destinatário e prazo de comunicação.

**O script/CI não pode auto-concluir “notificar” ou “não notificar”.** A decisão deve citar regra vigente e evidence refs revisadas.

### 4.6 Comunicar

Somente depois de decisão autorizada. Mensagens devem evitar especulação, não expor outros tenants, descrever medidas reais e preservar consistência entre controlador, operador, titulares e autoridade aplicável.

### 4.7 Encerrar

Encerramento exige:

- causa raiz;
- impacto confirmado vs descartado;
- timeline;
- contenção/recuperação;
- decisão regulatória e responsável;
- backlog de prevenção;
- regressão/gate criado quando cabível;
- postmortem aprovado.

## 5. Registro e retenção

O registro de incidentes deve possuir política de retenção revisada e acesso restrito. Campos candidatos:

- incident_id;
- opened/contained/recovered/closed timestamps;
- owner assignments;
- severity working/final;
- affected systems/tenants em referência minimizada;
- evidence digests;
- decisions e approvers;
- communication refs;
- root cause/failure class;
- remediation commits/tests;
- postmortem digest.

Prazo de retenção: **PENDENTE DE REVISÃO JURÍDICA/OPERACIONAL**.

## 6. Handoff operador → controlador

Quando o coach/organização for controlador do dado de aluno e FitNexus atuar como operador no fluxo:

1. validar tenant/controlador correto;
2. fornecer fatos necessários e minimizados;
3. não contatar aluno em nome do controlador sem autoridade adequada, salvo obrigação própria aplicável;
4. registrar horário, escopo e conteúdo do handoff;
5. coordenar updates e preservar evidence trail.

## 7. Três tabletops obrigatórios do Stage45

### A. Cross-tenant exposure

Simular, com fixture sintética, suspeita de leitura entre organizações. Exercitar detecção, blast radius, containment, tenant isolation proof, owner handoff, decisão de dados pessoais e recuperação.

### B. Credential compromise

Simular comprometimento de credencial de serviço/provider sem usar segredo real. Exercitar revogação/rotação hipotética, inventory de dependências, containment, audit trail, recovery e prevenção de secret leakage.

### C. Potentially sensitive student data

Simular exposição de dado de aluno que possa conter saúde/lesão/dor. Exercitar minimização, classificação, controller/operator handoff, risk assessment e processo de decisão de comunicação.

Cada tabletop deve produzir receipt próprio e usar **somente dados sintéticos/non-customer**.

## 8. Postmortem obrigatório

O postmortem final do drill deve registrar:

- cenário e objetivos;
- participantes/papéis reais;
- o que funcionou/falhou;
- tempos de decisão e pontos cegos;
- gaps de tooling/processo;
- actions com owner e prioridade;
- regressões/guards criados;
- decisão se o runbook está pronto para nova revisão.

## 9. O que ainda bloqueia o gate

- owners reais;
- matriz de severidade revisada;
- handoff controller/operator aprovado;
- procedimento de comunicação ANPD/titulares revisado conforme regra vigente;
- controle de retenção do registry;
- três tabletop receipts reais de exercício;
- postmortem final;
- independent review.

**GATE:** `incident_response = BLOCKED` até todos os requisitos reais serem evidenciados e promovidos por migration dedicada após review.
