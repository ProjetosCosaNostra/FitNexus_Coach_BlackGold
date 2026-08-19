# FitNexus Coach BlackGold — Termos de Uso

> **STATUS: DRAFT — LEGAL REVIEW REQUIRED — NOT APPROVED FOR PRODUCTION**
>
> Este texto é uma minuta operacional para revisão. Não satisfaz o gate `legal_terms_of_use` e não deve ser apresentado como contrato final antes da revisão jurídica.

## 1. Objeto

O FitNexus Coach BlackGold é um SaaS de apoio à gestão profissional de alunos, treinos, execução, feedback, aderência, templates, decisões operacionais e recursos comerciais relacionados ao serviço.

## 2. Público profissional

A oferta principal é direcionada a profissionais/organizações que utilizam o sistema na condução de sua própria atividade. A versão final deve definir requisitos de capacidade civil, eventual qualificação profissional e regras para contas de equipe.

## 3. O FitNexus não substitui decisão profissional ou assistência médica

O software organiza informações e pode apresentar alertas, métricas, automações e sugestões. O profissional continua responsável por revisar e decidir prescrições e orientações.

Recursos de IA, quando liberados, seguem o princípio: **IA sugere; profissional decide**. O sistema não deve alterar prescrições silenciosamente.

O FitNexus não deve ser descrito como serviço médico, diagnóstico ou promessa de resultado físico garantido.

## 4. Conta e segurança

O usuário deve:

- fornecer informações corretas;
- proteger credenciais;
- não compartilhar conta de forma incompatível com o plano;
- comunicar uso não autorizado conhecido;
- respeitar permissões e limites da organização.

Tentativas de contornar RLS, limites de plano, checkout, cobrança ou controles de segurança podem gerar bloqueio conforme política final.

## 5. Dados de alunos

O profissional/organização que insere dados de alunos deve possuir fundamento e autoridade adequados para usar o serviço e fornecer instruções compatíveis com a legislação aplicável.

Os papéis exatos de controlador/operador e obrigações de cada parte permanecem sujeitos ao gate `legal_role_mapping`.

## 6. Trial, planos e limites

A arquitetura comercial atual suporta:

- trial;
- planos recorrentes;
- limites de alunos/equipe;
- recursos por entitlement;
- cobrança mensal/anual;
- preservação de dados quando novos writes comerciais forem bloqueados.

Os valores atuais são um experimento comercial versionado e podem ser alterados para novas contratações mediante nova decisão de preço e comunicação adequada. A versão contratual final deve definir tratamento de preço vigente, renovação, reajuste, impostos e efeitos para clientes existentes.

## 7. Pagamento e inadimplência

O desenho do produto prevê provedor externo de pagamento, eventos idempotentes, estados de assinatura e possibilidade de período de tolerância/read-only antes de medidas mais restritivas.

O contrato final deve definir:

- periodicidade;
- renovação;
- vencimento;
- cancelamento;
- reembolso quando aplicável;
- tratamento de chargeback/fraude;
- efeitos da inadimplência;
- eventual prazo de exportação antes de exclusão.

Nenhuma cláusula financeira deve ser promovida antes de o provedor real e a política comercial estarem ativos.

## 8. Uso aceitável

Deve ser proibido, entre outros:

- uso ilegal ou fraudulento;
- tentativa de acesso a outra organização;
- exploração de vulnerabilidades;
- engenharia para contornar limites comerciais;
- inserção de conteúdo para o qual o usuário não possua direito/autorização;
- uso do sistema para diagnóstico/promessas médicas indevidas em nome do FitNexus.

## 9. Disponibilidade, manutenção e evolução

O serviço pode evoluir, receber manutenção e corrigir falhas. A versão final não deve prometer disponibilidade absoluta sem SLA contratado.

Mudanças que afetem materialmente contrato, preço ou tratamento de dados devem seguir versionamento e comunicação apropriados.

## 10. Propriedade intelectual

A versão final deve separar:

- software, marca, design e componentes do FitNexus;
- conteúdo/dados inseridos pelo cliente;
- licenças necessárias para processar esse conteúdo durante a prestação do serviço;
- materiais de terceiros e open source.

## 11. Exportação, encerramento e preservação

O encerramento não deve apagar dados imediatamente quando houver obrigação legal, necessidade de segurança, retenção financeira ou política de backup aplicável.

O produto deve buscar permitir portabilidade/exportação coerente com o contrato e a legislação antes de exclusões definitivas.

## 12. Responsabilidade

Limitações de responsabilidade, indenização e exclusões dependem da legislação aplicável e do perfil contratual do cliente. Nenhuma limitação deve ser inserida como definitiva sem revisão jurídica, especialmente quando puder conflitar com normas de proteção do consumidor ou deveres legais.

## 13. Privacidade

O tratamento de dados pessoais será regido pelo Aviso de Privacidade aprovado e pelos instrumentos contratuais aplicáveis. A aceitação destes Termos não deve ser usada como “consentimento genérico” para todo tratamento de dados.

## 14. Lei aplicável e foro

**PENDENTE DE REVISÃO JURÍDICA.** Não congelar foro ou regra de resolução de conflito sem avaliar relação B2B/B2C, local de contratação e normas cogentes aplicáveis.

## 15. Versionamento

A versão de produção deve possuir:

- identificador;
- data de publicação;
- data de vigência;
- histórico de alterações materiais;
- mecanismo de aceite quando contratualmente necessário.

## Fontes oficiais mínimas para revisão

- Lei 13.709/2018 (LGPD): https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm
- Código de Defesa do Consumidor, quando aplicável: https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm
- Marco Civil da Internet, quando aplicável: https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2014/lei/l12965.htm

## Gate

`legal_terms_of_use = BLOCKED`

Somente evidence migration após revisão jurídica e publicação estável pode promover este gate.
