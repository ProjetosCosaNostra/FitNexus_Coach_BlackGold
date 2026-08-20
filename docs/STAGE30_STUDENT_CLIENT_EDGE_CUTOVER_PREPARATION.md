# Stage 30 — Student Client Edge Cutover Preparation

## Estado de entrada

O Edge `student-access-gateway` v3 já possui prova live de origem de rede confiável, resistência a spoof, rate limit pré-token e threshold exato HTTP 429. O Stage 29 também comprovou uma rota válida `get_workout` com token sintético e resposta exata da fixture, seguido de cleanup transacional completo e reconciliação do ledger.

Isso não autoriza automaticamente o Flutter a trocar de transporte nem autoriza revogar os cinco RPCs públicos atuais.

## Estado deste estágio

`CLIENT_EDGE_CUTOVER_PREPARATION_DIRECT_PATH_ACTIVE`

O comportamento do aplicativo continua inalterado: os cinco caminhos estudantis permanecem em RPC direto. O arquivo `student_access_transport_contract.dart` é apenas uma autoridade compilável de preparação e mantém `activeMode = directRpc`.

## Inventário indivisível

As cinco ações formam uma única fronteira de segurança e devem migrar juntas:

- `get_workout` → `get_student_workout_v2`
- `start_workout` → `start_student_workout_v2`
- `set_completion` → `set_student_exercise_completion_v2`
- `get_feedback_context` → `get_student_feedback_context_v2`
- `submit_feedback` → `submit_student_workout_feedback_v2`

Uma migração parcial é proibida.

## Regra de fail-closed

Depois que o Edge for selecionado como transporte ativo, erro do Edge não poderá causar fallback automático por requisição para os RPCs diretos. Esse comportamento furaria os controles de origem de rede e rate limit pré-token.

Rollback é uma transição explícita, controlada e comprovada. Não é fallback automático.

## Ordem obrigatória para futura promoção

1. Centralizar os cinco call sites em um único transporte sem alterar o modo ativo.
2. Implementar o transporte Edge e mapear erros sem alterar o modo ativo.
3. Compilar/testar e executar smoke read-only.
4. Executar prova sintética controlada também para rotas de comando.
5. Provar rollback explícito.
6. Somente então selecionar Edge no cliente.
7. Observar o cliente em runtime e comprovar as cinco rotas.
8. Reavaliar advisors.
9. Revogar os RPCs diretos somente após rollback e cutover estarem comprovados.

## Falhas permanentes registradas

- `BGF-CLIENT-EDGE-CUTOVER-PREMATURE-195`
- `BGF-CLIENT-TRANSPORT-PARTIAL-CUTOVER-196`
- `BGF-EDGE-FAILOPEN-DIRECT-FALLBACK-197`
- `BGF-DIRECT-RPC-REVOCATION-BEFORE-ROLLBACK-198`
- `BGF-CLIENT-CUTOVER-SELF-ATTESTATION-199`

Nenhuma dessas mudanças promove gate de incident response, deployment, billing, legal ou mídia paga.
