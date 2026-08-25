# FitNexus Coach BlackGold — Data Subject Request Runbook — CANDIDATO NÃO OPERACIONAL

> **STATUS OBRIGATÓRIO:** DRAFT_UNREVIEWED_NOT_OPERATIONAL_EVIDENCE  
> Este runbook prepara o gate `data_subject_request_channel`, mas não prova que o canal foi testado, não define SLA jurídico final e não substitui revisão de controlador/operador.

## 1. Canal candidato

- Contato candidato: **projetoscosanostra@gmail.com**.
- URL/formulário público estável: **PENDENTE**.
- Owner primário e owner substituto: **PENDENTES DE ATRIBUIÇÃO REAL**.
- Ferramenta de protocolo/ticket: **PENDENTE**.

## 2. Princípios fail-closed

1. Não revelar se uma pessoa/aluno existe antes de verificação adequada.
2. Não usar customer data em testes/tabletops; usar fixture sintética.
3. Não exportar dados de tenant diferente do tenant autorizado.
4. Não executar exclusão irreversível se existir legal hold, obrigação de retenção ou incerteza de identidade.
5. Não copiar secrets, tokens de acesso ou material de segurança desnecessário para o protocolo.
6. Toda ação material precisa de receipt com escopo, decisão, executor autorizado e resultado.

## 3. Intake mínimo

Registrar somente o necessário para processar a solicitação:

- protocolo interno;
- data/hora de recebimento;
- categoria do pedido;
- identidade declarada do solicitante;
- relação declarada com conta/organização/aluno;
- canal de resposta;
- estado da verificação de identidade;
- controlador/operador envolvido, quando conhecido;
- prazo aplicável **a confirmar juridicamente**.

## 4. Verificação de identidade — procedimento candidato

- Coach/account owner autenticado: preferir challenge dentro da conta ou confirmação por canal já vinculado.
- Membro de organização: confirmar membership/role e escopo do tenant.
- Aluno sem conta completa: usar mecanismo proporcional que não dependa apenas de informação facilmente obtida; nunca pedir que envie token/segredo completo em e-mail.
- Terceiro/representante: exigir autoridade adequada antes de liberar dado.
- Em caso de dúvida material: pausar execução, não negar silenciosamente, registrar necessidade de revisão.

## 5. Classificação do pedido

Categorias candidatas:

- confirmação/acesso;
- correção;
- informação sobre compartilhamento/processamento;
- portabilidade quando aplicável;
- anonimização/bloqueio/eliminação quando cabível;
- oposição/revisão/revogação quando aplicável;
- reclamação sobre tratamento;
- pedido relacionado a aluno cujo controlador principal pode ser o coach/organização.

A classificação jurídica final depende da matriz de papéis aprovada.

## 6. Handoff controlador ↔ operador

Quando FitNexus estiver atuando como operador para dado controlado pelo coach/organização:

1. identificar tenant e controlador sem revelar dados a outro tenant;
2. registrar o pedido e o escopo técnico disponível;
3. encaminhar ao controlador pelo canal aprovado;
4. preservar trilha de recebimento, handoff e decisão;
5. executar apenas instrução válida/autorizada, salvo obrigação legal própria;
6. devolver receipt técnico sem conteúdo excessivo.

## 7. Access/export — teste sintético exigido

Antes do gate:

- criar fixture sintética isolada e autorizada;
- provar que o export contém apenas o titular/tenant correto;
- validar campos esperados e exclusão de secrets/credenciais internas;
- registrar SHA-256 do artefato de teste e cleanup;
- review independente do receipt.

## 8. Correção — teste sintético exigido

- corrigir fixture sintética em fluxo autorizado;
- confirmar before/after, audit trail e ausência de alteração cross-tenant;
- provar que a mudança não quebra lineage/histórico quando histórico for necessário;
- limpar fixture e registrar receipt.

## 9. Eliminação, anonimização, bloqueio e retention hold — teste exigido

O procedimento final precisa separar:

- dado que pode ser eliminado imediatamente;
- dado sujeito a retenção obrigatória/contratual revisada;
- backup ainda em janela de retenção;
- dado a anonimizar/bloquear;
- eventos de segurança/auditoria que possuam fundamento próprio de retenção.

Nenhum prazo ou obrigação é congelado por este candidato.

## 10. Resposta ao titular

A resposta final deve ser clara, registrar o que foi feito/não feito e por quê, sem expor segurança interna, dados de terceiros ou outros tenants. Prazos e linguagem obrigatória dependem de revisão jurídica vigente.

## 11. Tabletop obrigatório antes do gate

Cenário mínimo candidato:

1. pedido de acesso de coach autenticado;
2. pedido de aluno ligado a organização;
3. tentativa de requester de outro tenant;
4. pedido de eliminação com retention hold hipotético;
5. pedido incompleto com identidade insuficiente.

O tabletop deve produzir receipt real do exercício e postmortem; este documento não é esse receipt.

## 12. Critérios de prontidão que ainda faltam

- rota pública estável de contato;
- owner + backup owner reais;
- política de prazo revisada;
- matriz de papéis aprovada;
- procedimentos de identidade aprovados;
- três testes técnicos de access/export, correction e deletion/hold;
- tabletop request receipt;
- independent review.

**GATE:** `data_subject_request_channel = BLOCKED` até evidência operacional real e migration dedicada aprovada.
