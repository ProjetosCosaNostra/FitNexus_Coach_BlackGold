# FitNexus Coach BlackGold — Aviso de Privacidade

> **STATUS: DRAFT — LEGAL REVIEW REQUIRED — NOT APPROVED FOR PRODUCTION**
>
> Este documento prepara o conteúdo operacional do aviso de privacidade, mas **não** satisfaz o gate `legal_privacy_notice`. Publicação e promoção para produção exigem revisão jurídica específica do produto, das bases legais e dos papéis controlador/operador.

## 1. Quem é o FitNexus

FitNexus Coach BlackGold é um SaaS para profissionais de treino organizarem alunos, prescrições, execução, feedback, acompanhamento e operação comercial.

Canal provisório de contato do projeto:

`projetoscosanostra@gmail.com`

O canal definitivo para direitos de titulares e questões de privacidade deve ser validado antes do lançamento.

## 2. Que dados o sistema atualmente pode tratar

### Conta e autenticação do profissional

- nome informado no cadastro;
- e-mail;
- identificadores técnicos da conta e sessão;
- organização/espaço profissional;
- papéis e vínculo com a organização.

### Operação do coach

- cadastro de alunos;
- dados de contato do aluno quando registrados pelo profissional;
- objetivo operacional do aluno;
- treinos, exercícios, séries, repetições, observações e agenda;
- links/tokens de acesso do aluno;
- histórico de execução.

### Feedback e contexto potencialmente sensível

O produto pode registrar informações relacionadas à execução física, incluindo esforço percebido, energia, dor, localização de dor e observações. Dependendo do conteúdo, informações sobre saúde podem constituir **dados pessoais sensíveis** sob a LGPD.

A arquitetura deve aplicar minimização, isolamento por organização, controle de acesso e finalidade compatível. O marketing não deve usar dados de saúde para segmentação sem análise jurídica específica.

### Assinatura e cobrança

- plano, limites e estado da assinatura;
- identificadores do provedor de cobrança;
- referências de checkout/evento;
- evidência técnica/idempotência de eventos financeiros.

O desenho atual não exige que o Flutter receba segredo do provedor ou dados brutos de cartão.

### Telemetria de produto e aquisição

A telemetria de crescimento foi desenhada para minimizar dados:

- eventos operacionais de ativação/retenção/receita sem copiar conteúdo de saúde;
- UTM source/medium/campaign/term/content com tamanho limitado;
- caminho relativo da landing, sem query string;
- para visitante anônimo, chave aleatória transformada em SHA-256 no servidor;
- sem armazenamento intencional de IP, e-mail, nome, telefone ou payload arbitrário na tabela de aquisição pública.

## 3. Para que os dados podem ser usados

Finalidades operacionais preparadas para revisão:

- criar e proteger a conta;
- isolar organizações e aplicar permissões;
- permitir cadastro e acompanhamento de alunos;
- criar, entregar e registrar treinos;
- receber feedback do aluno e permitir acompanhamento pelo profissional;
- manter histórico, evidência e recuperação do produto;
- controlar trial, planos, limites e cobrança;
- prevenir abuso, fraude e falhas de segurança;
- medir aquisição, ativação, retenção e qualidade do produto;
- cumprir obrigações legais/regulatórias aplicáveis e responder a solicitações válidas de titulares.

**Bases legais não estão congeladas neste draft.** O mapeamento finalidade → base legal deve ser aprovado no gate `legal_role_mapping` antes da produção.

## 4. Papéis de tratamento — ainda em revisão

O desenho de trabalho considera que os papéis podem variar por contexto:

- para conta, segurança, faturamento e operação do próprio SaaS, o FitNexus pode possuir decisões próprias de finalidade/meios;
- para dados de alunos inseridos e gerenciados por um coach/organização, a relação controlador/operador precisa considerar contrato, instruções do cliente e decisões efetivamente tomadas pelo produto;
- integrações futuras podem criar novos papéis ou controladoria conjunta e exigem nova análise.

Nenhum papel é declarado definitivo neste draft. Ver `PROCESSING_ROLE_MAP_DRAFT_LEGAL_REVIEW_REQUIRED.md`.

## 5. Compartilhamentos e operadores

Antes do lançamento, a versão final deve listar categorias de fornecedores efetivamente usados, por exemplo:

- infraestrutura/backend;
- autenticação;
- hospedagem/deploy;
- provedor de pagamento;
- e-mail/transacional, quando existir;
- observabilidade, quando existir.

O produto não deve prometer fornecedor ou transferência internacional que ainda não esteja tecnicamente configurado e contratualmente revisado.

## 6. Retenção e exclusão

A política final deve diferenciar:

- dados necessários enquanto a conta/contrato estiver ativo;
- evidências financeiras e de segurança que possam exigir retenção;
- dados de aluno sob instrução do cliente/controlador;
- backups e prazos de expurgo;
- pedidos de eliminação sujeitos a hipóteses legais de conservação.

O estado atual de assinatura já preserva histórico em bloqueios/inadimplência em vez de apagar dados automaticamente.

## 7. Direitos dos titulares

A LGPD prevê direitos como confirmação do tratamento, acesso, correção, anonimização/bloqueio/eliminação em hipóteses aplicáveis, portabilidade conforme regulamentação, informação sobre compartilhamento, revogação de consentimento quando essa for a base utilizada e revisão/explicação em situações aplicáveis.

O procedimento operacional preliminar está em `docs/privacy/DATA_SUBJECT_REQUEST_RUNBOOK_DRAFT.md`.

## 8. Segurança

Controles técnicos já presentes ou em evolução incluem:

- autenticação Supabase;
- isolamento por organização;
- RLS e menor privilégio;
- funções privadas para autoridade elevada;
- segredos fora do Flutter;
- trilhas de eventos e idempotência;
- gates de CI;
- telemetria sem payload sensível arbitrário;
- prevenção contra mudanças silenciosas de assinatura/preço/prescrição.

Nenhum sistema é infalível. A versão final do aviso deve descrever medidas de forma verdadeira, sem garantia absoluta de segurança.

## 9. Incidentes

Existe runbook técnico em preparação em `docs/security/PERSONAL_DATA_INCIDENT_RESPONSE_RUNBOOK_DRAFT.md`.

A versão de produção precisa estar alinhada ao Regulamento de Comunicação de Incidente de Segurança da ANPD e à operação real do FitNexus.

## 10. Alterações deste aviso

A versão final deve possuir identificador/versionamento e data de vigência. Mudanças materiais devem gerar nova versão e, quando necessário, comunicação apropriada.

## 11. Fontes oficiais para revisão jurídica

- Lei Geral de Proteção de Dados — Lei 13.709/2018: https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm
- ANPD — Direitos dos titulares: https://www.gov.br/anpd/pt-br/assuntos/direitos-dos-titulares
- ANPD — Incidente de segurança: https://www.gov.br/anpd/pt-br/assuntos/incidente-de-seguranca

## Gate

`legal_privacy_notice = BLOCKED`

Este gate somente pode mudar por evidence migration após revisão jurídica, publicação em rota estável e registro do digest da versão aprovada.
