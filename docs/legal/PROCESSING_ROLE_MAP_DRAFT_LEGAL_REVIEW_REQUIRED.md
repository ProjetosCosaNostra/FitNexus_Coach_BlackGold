# FitNexus Coach BlackGold — Mapa de Papéis de Tratamento

> **STATUS: DRAFT — LEGAL REVIEW REQUIRED — NOT APPROVED FOR PRODUCTION**
>
> Este mapa organiza hipóteses de controlador/operador para revisão. Ele não satisfaz o gate `legal_role_mapping`.

## Princípio

A LGPD define controlador como quem toma decisões referentes ao tratamento e operador como quem realiza tratamento em nome do controlador. O papel depende da operação concreta; uma mesma organização pode ocupar papéis diferentes em tratamentos diferentes.

## Matriz preliminar

| Contexto | Dados principais | Papel FitNexus — hipótese | Papel coach/organização — hipótese | Ponto de revisão |
| --- | --- | --- | --- | --- |
| Conta/autenticação do profissional | nome, e-mail, sessão, segurança | controlador para finalidades próprias do SaaS | titular/cliente | confirmar bases legais e retenção |
| Assinatura/faturamento | plano, estado, IDs de cobrança, eventos | controlador para operação comercial própria | cliente | mapear provedor como operador/controlador independente conforme contrato |
| Segurança/antifraude | logs, evidência técnica, incidentes | controlador para segurança própria | cliente impactado | retenção e compartilhamento |
| Cadastro de aluno pelo coach | identidade/contato/objetivo | potencial operador em nome do cliente | potencial controlador | contrato e instruções devem refletir realidade |
| Prescrição/treino do aluno | treino, exercícios, observações | potencial operador | potencial controlador/profissional responsável | confirmar finalidade e responsabilidade profissional |
| Feedback físico do aluno | esforço, energia, dor/localização, notas | potencial operador; dado pode ser sensível | potencial controlador | base legal de dado sensível + minimização |
| Telemetria de produto autenticada | eventos de ativação sem payload de saúde | controlador para melhoria/segurança/negócio próprio | cliente/titular conforme evento | definir base legal e retenção |
| Aquisição anônima | visitante hash, UTM, caminho relativo | controlador para medição de aquisição | não aplicável | revisar cookies/storage e transparência |
| IA futura | contexto autorizado, sugestão, aceite/rejeição | depende do desenho e fornecedor | profissional mantém decisão | DPA, transferência, minimização, não diagnóstico |

## Regras técnicas já alinhadas ao mapa

- RLS isola organizações.
- Segredos do provedor não ficam no Flutter.
- Telemetria de crescimento não aceita payload arbitrário de saúde.
- Eventos de aquisição não guardam e-mail, nome, telefone, IP ou query string no ledger público.
- IA não altera prescrição silenciosamente.
- Billing/entitlements são autoridade do servidor.

## Questões obrigatórias antes de promover o gate

1. Para dados de alunos, o contrato realmente coloca o FitNexus sob instruções documentadas do cliente?
2. Quais decisões de finalidade/meios o FitNexus toma por conta própria em segurança, produto, suporte e analytics?
3. Há tratamentos em que ambas as partes determinam conjuntamente finalidades/meios?
4. Quais bases legais sustentam cada finalidade, sobretudo dados de saúde?
5. Quais fornecedores são operadores/suboperadores e quais atuam como controladores independentes?
6. Há transferência internacional e qual mecanismo jurídico se aplica?
7. Como pedidos do aluno titular chegam ao coach e ao FitNexus e quem responde em cada cenário?
8. Como exclusão, retenção, backup e obrigação legal são coordenados?

## Fontes oficiais para revisão

- LGPD — definições de controlador e operador: https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm
- ANPD — Guia Orientativo para Definições dos Agentes de Tratamento de Dados Pessoais e do Encarregado: https://www.gov.br/anpd/pt-br/documentos-e-publicacoes/2021.05.27GuiaAgentesdeTratamento_Final.pdf
- ANPD — Direitos dos titulares: https://www.gov.br/anpd/pt-br/assuntos/direitos-dos-titulares

## Gate

`legal_role_mapping = BLOCKED`

A promoção exige revisão jurídica e evidence migration com versão/digest do mapa aprovado.
