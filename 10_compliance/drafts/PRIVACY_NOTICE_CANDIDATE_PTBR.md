# FitNexus Coach BlackGold — Aviso de Privacidade — CANDIDATO NÃO REVISADO

> **STATUS OBRIGATÓRIO:** DRAFT_UNREVIEWED_NOT_PUBLISHED_NOT_LEGAL_EVIDENCE  
> Este documento é material de preparação. Não está aprovado por revisor jurídico, não possui data de vigência, não deve ser publicado como aviso oficial e não fecha o gate `legal_privacy_notice`.

## 1. Identificação ainda aberta

- Produto: **FitNexus Coach BlackGold**.
- Operador do projeto/ecossistema: **PREENCHER APÓS REVISÃO JURÍDICA: razão social/nome empresarial, CNPJ quando aplicável e endereço oficial**.
- Contato candidato para privacidade e direitos: **projetoscosanostra@gmail.com**.
- Encarregado/DPO ou hipótese legal de dispensa: **PENDENTE DE REVISÃO JURÍDICA**.
- Versão aprovada, data de vigência e URL pública estável: **NÃO EXISTEM NESTE CANDIDATO**.

## 2. Escopo do serviço

O FitNexus Coach BlackGold é um SaaS coach-first para organização de alunos, treinos, entrega de prescrições, execução/feedback, acompanhamento operacional e recursos de Decision Intelligence sob controle do profissional. A arquitetura atual usa conta/organização com isolamento multi-tenant e acesso de aluno por fluxo controlado de link/token.

## 3. Categorias de dados previstas

A depender do uso efetivo do produto, podem ser tratados:

- dados de conta e autenticação do coach/usuário;
- dados da organização, papéis e associação de membros;
- dados cadastrais mínimos de alunos;
- objetivos, prescrições de treino, histórico de versões, execução e feedback;
- informações que, conforme seu conteúdo, podem revelar saúde, lesão, dor, limitações ou outras informações potencialmente sensíveis;
- eventos de segurança, auditoria, prevenção de abuso, idempotência e telemetria operacional;
- dados de assinatura, plano, cobrança e referências de transação quando billing for ativado;
- dados de suporte e solicitações de direitos.

**Regra de minimização:** dados sensíveis não devem ser enviados em UTMs, payloads de advertising, logs desnecessários ou recibos de engenharia.

## 4. Finalidades candidatas

- fornecer autenticação, tenancy e controle de acesso;
- cadastrar e gerenciar alunos e prescrições;
- entregar treino e registrar execução/feedback;
- preservar histórico, lineage, auditoria e restauração segura;
- apresentar prioridades e sugestões operacionais explicáveis ao coach;
- prevenir abuso, fraude, replay, acesso cross-tenant e incidentes;
- operar suporte, continuidade, backup e recuperação quando habilitados;
- operar trial, assinatura e cobrança quando o provider de billing estiver legitimamente ativado;
- cumprir obrigações legais e responder solicitações de titulares.

## 5. Papéis de tratamento — hipótese, não conclusão jurídica

A matriz final de controlador/operador ainda depende de revisão jurídica. Hipótese de trabalho:

- para dados que o coach/organização insere para prestar acompanhamento ao aluno, o coach/organização pode exercer papel de controlador e o FitNexus pode atuar como operador em parte do fluxo;
- para segurança da própria plataforma, gestão de conta, billing, prevenção de fraude e obrigações próprias, o FitNexus pode possuir finalidades e responsabilidades próprias.

Esta hipótese **não deve ser publicada como conclusão jurídica** antes da aprovação da matriz de papéis.

## 6. Compartilhamentos e subprocessadores

- **Supabase/Postgres** integra o backend atual e deve constar do inventário de subprocessadores após revisão de contrato, localização, retenção e transferência internacional quando aplicável.
- **Asaas** está selecionado para BR V1, porém permanece `selected_pending_credentials`; não deve ser descrito como provider de produção ativo antes de ativação real e evidência correspondente.
- Outros provedores de hosting, observabilidade, e-mail, IA ou mídia só entram na versão oficial depois de inventário real, finalidade, minimização, contrato e revisão aplicáveis.

## 7. Decision Intelligence e IA

O contrato do produto é human-in-the-loop: IA/regras podem sugerir, resumir ou priorizar, mas o profissional mantém a decisão sobre prescrições e ações relevantes. Dados de saúde/sensíveis não devem ser reutilizados para segmentação publicitária. Qualquer provedor externo de IA exige avaliação de privacidade, minimização, isolamento de tenant, custo e segurança antes de produção.

## 8. Retenção e eliminação

A matriz de retenção definitiva ainda está aberta. A versão oficial deve definir por categoria:

- período ou critério de retenção;
- finalidade e base revisada;
- efeito de cancelamento/inadimplência;
- backups e janela de expurgo;
- legal hold quando necessário;
- anonimização, bloqueio ou eliminação aplicável.

Nenhum prazo deve ser inventado neste candidato.

## 9. Segurança

Controles já presentes no projeto incluem RLS/tenant isolation, funções de autoridade, trilhas de segurança, rate limiting/idempotência em fronteiras críticas, CI fail-closed e reconciliação de migrations/receipts. A versão pública não deve prometer segurança absoluta. Incidentes devem seguir runbook e decisão regulatória revisados.

## 10. Direitos dos titulares

O canal candidato é `projetoscosanostra@gmail.com`, sujeito a teste operacional e revisão. A versão oficial deve explicar como solicitar acesso, confirmação, correção, informação, portabilidade quando aplicável, anonimização/bloqueio/eliminação quando cabível, revogação/objeção e demais direitos previstos pela legislação vigente, com verificação proporcional de identidade e preservação de segregação por tenant.

## 11. Transferências internacionais

**PENDENTE:** mapear regiões e mecanismos aplicáveis de Supabase e de qualquer futuro subprocessor. Não declarar ausência ou presença de transferência internacional sem evidência contratual/técnica atual.

## 12. Cookies, analytics e marketing

Nenhum advertising/analytics deve coletar dado sensível ou tornar a mídia paga autoridade sobre fatos do produto. Consentimento/base legal, disclosure e conversion measurement devem ser revisados antes de paid media. `paid_ads_auto_launch=false` permanece.

## 13. Mudanças deste aviso

A futura versão oficial deve possuir versão, digest SHA-256, data de vigência, histórico e URL estável. Alterações materiais devem seguir o processo de governança aprovado.

## 14. Itens que impedem publicação

1. Identidade jurídica/contato institucional final.
2. Revisor jurídico e referência de aprovação.
3. Matriz controlador/operador aprovada.
4. Base/finalidade revisada por categoria.
5. Inventário de subprocessadores e retenção.
6. Transferência internacional quando aplicável.
7. Canal de direitos testado.
8. Versão/data/digest/URL estável.

**GATE:** `legal_privacy_notice = BLOCKED` até evidência independente real e migration dedicada aprovada.
