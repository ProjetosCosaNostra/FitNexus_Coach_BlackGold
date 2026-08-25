# FitNexus Coach BlackGold — Processing Role Matrix — CANDIDATO NÃO REVISADO

> **STATUS OBRIGATÓRIO:** DRAFT_UNREVIEWED_NOT_LEGAL_EVIDENCE  
> Matriz técnica para orientar revisão jurídica. Nenhuma linha abaixo congela controlador, operador, base legal, transferência internacional ou retenção.

| Fluxo | Dados previstos | Finalidade técnica | Hipótese de papel FitNexus | Hipótese de papel coach/organização | Sensível possível? | Subprocessor atual/candidato | Decisão jurídica pendente |
|---|---|---|---|---|---|---|---|
| Conta/autenticação do coach | identificadores, auth metadata | criar conta e autenticar | finalidade própria e/ou controladoria própria | titular/usuário | baixo em regra | Supabase | base legal, retenção, registros de auth |
| Tenancy/organização | organização, membros, roles | isolamento e autorização | operador da infraestrutura e possível finalidade própria de segurança | controlador da equipe/carteira, hipótese | não por natureza | Supabase | divisão exata de papéis |
| Cadastro do aluno | perfil mínimo, vínculo com organização | permitir acompanhamento | operador, hipótese | controlador, hipótese | pode tornar-se sensível pelo conteúdo | Supabase | minimização e campos permitidos |
| Prescrição/treino | exercícios, objetivos, notas, versões | montar/entregar treino | operador, hipótese | controlador/profissional, hipótese | sim, dependendo de notas/objetivos | Supabase | tratamento de saúde/sensível |
| Execução/feedback | sessão, conclusão, feedback, dor/energia quando houver | acompanhar aderência e evolução | operador, hipótese | controlador/profissional, hipótese | sim | Supabase | finalidade/base e minimização |
| Student access link/token | token/identificador técnico, eventos de segurança | acesso controlado sem conta completa | finalidade técnica de segurança + operação | controlador da relação com aluno, hipótese | token é credencial; não é dado para marketing | Supabase | transparência ao titular e retenção |
| Security/audit | eventos, rate limit, idempotência, incident metadata | prevenir abuso e investigar incidentes | possível controladoria própria de segurança | cooperação operacional | pode conter identificadores | Supabase | retenção e acesso aos logs |
| Decision Intelligence | sinais operacionais, evidência, confidence, decisão humana | priorizar trabalho do coach | operador/fornecedor da ferramenta, hipótese | controlador da decisão profissional, hipótese | pode usar contexto sensível autorizado | Supabase; LLM futuro somente após gate | limites de finalidade e IA |
| Billing/trial | plano, status, refs de cobrança | operar assinatura | possível controladoria própria comercial | cliente/contratante | não esperado | Asaas somente após ativação real | provider, impostos, retenção financeira |
| Suporte | mensagens e evidências fornecidas pelo usuário | resolver problema | possível controladoria própria de suporte | titular/cliente | pode conter sensível se usuário enviar | canal a definir | orientação para não enviar excesso |
| Growth/analytics | eventos de aquisição/ativação/receita | medir produto e aquisição | possível controladoria própria de analytics | n/a | **não permitido** enviar sensível | ferramenta futura sob gate | consentimento/base/disclosure |
| Ads/conversion | identificadores mínimos aprovados, eventos de conversão | atribuição de mídia | possível controladoria própria de marketing | n/a | **proibido** usar sensível para targeting | Google/Meta somente após gates | consent/privacy/ad terms |
| DSR | identidade de solicitante, protocolo, resultado | atender direitos | papel depende do pedido; coordena com controlador quando operador | controlador em pedidos de aluno, hipótese | pode envolver qualquer categoria | canal operacional | SLA, autenticação, handoff |
| Incidente | escopo, categorias afetadas, decisões, comunicações | resposta e obrigação regulatória | papel depende da causa/fluxo | cooperação controlador-operador | sim | providers afetados | comunicação ANPD/titulares e responsabilidades |

## Decisões obrigatórias antes de aprovação

1. Identificar entidade jurídica do FitNexus e contratos aplicáveis.
2. Aprovar papel por fluxo, não por slogan global.
3. Vincular cada finalidade à base jurídica revisada.
4. Definir tratamento de dados potencialmente sensíveis de treino/feedback.
5. Aprovar inventário real de subprocessadores, regiões e transferências internacionais.
6. Aprovar retenção e legal hold por categoria.
7. Definir responsabilidades controller↔processor para DSR e incidentes.
8. Confirmar se e quando Asaas, analytics, ads ou LLM realmente entram em produção.

## Guardrails técnicos já existentes que a revisão deve preservar

- RLS e isolamento por organização.
- Sem CRUD direto `authenticated` em `student_access_links` e eventos privados de segurança.
- Student access com fronteiras de rate limit/idempotência/rotação.
- Decision Intelligence human-in-the-loop.
- Growth events não são autoridade para readiness externa.
- Dados sensíveis não entram em UTMs/advertising payloads.
- `paid_ads_auto_launch=false`.

**GATE:** `legal_role_mapping = BLOCKED` até revisão jurídica real, versão aprovada e digest independente.
