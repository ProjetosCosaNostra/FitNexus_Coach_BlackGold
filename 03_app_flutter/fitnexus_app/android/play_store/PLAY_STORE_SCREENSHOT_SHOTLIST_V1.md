# FitNexus Coach BlackGold — Google Play Screenshot Shotlist V1

Status: **CAPTURE PLAN — NOT STORE EVIDENCE**

Purpose: define the exact real-app screenshots required for the first Google Play listing without fabricating UI, testimonials, rankings or promotional claims.

## Capture standard

- Target: Android phone, portrait 9:16.
- Preferred export: 1080 x 1920 PNG/JPEG, no alpha.
- Minimum publication requirement from current Google Play guidance: 2 screenshots.
- FitNexus launch target: 6 screenshots.
- First four must prioritize real product UI because they carry most discovery value.
- No device frame, fake notification bar, invented metrics or features not visible in the running app.
- Remove test-only personal data before capture. Use synthetic users only.
- Do not include prices, rankings, awards, download claims or calls such as “baixe agora”.
- Localized overlay text is optional; if used, it must stay secondary to the real UI and be localized per store language.

## Required shot sequence

### 01 — Coach Action Center
**Goal:** show the professional’s daily command center and immediate priorities.

Capture only when the screen contains realistic synthetic data and no debug/demo residue. The viewer should understand that FitNexus centralizes attention, follow-up and operational decisions.

Suggested alt text PT-BR: `Painel do personal com prioridades, alunos e ações de acompanhamento.`

### 02 — Student management
**Goal:** show a coach managing the student roster and opening a student context.

The image should make clear that the product is designed for multiple clients rather than a single personal workout diary.

Suggested alt text PT-BR: `Lista de alunos com contexto de acompanhamento profissional.`

### 03 — Workout prescription / template flow
**Goal:** show creation or management of a structured workout plan.

Prefer a screen that demonstrates reusable professional structure without exposing private data.

Suggested alt text PT-BR: `Plano de treino estruturado criado pelo personal para um aluno.`

### 04 — Feedback and attention signals
**Goal:** show the closed loop after workout execution: feedback arrives and the coach can identify what needs attention.

Do not claim medical diagnosis or guaranteed results.

Suggested alt text PT-BR: `Feedback de treino e sinais de atenção para acompanhamento do personal.`

### 05 — Student experience
**Goal:** show the authenticated student-side experience used to consult assigned training and return feedback.

This is important because FitNexus is not only an admin dashboard; the student participates in the same coaching loop.

Suggested alt text PT-BR: `Área do aluno com treino atribuído e envio de feedback.`

### 06 — Plan / limits / support
**Goal:** close the story with account status, plan limits or support, using whichever screen is most production-ready at capture time.

Do not show live prices unless the customer-facing pricing authority has already been promoted and reviewed.

Suggested alt text PT-BR: `Área de conta do FitNexus com limites do plano e acesso ao suporte.`

## Capture gate

The six screenshots are considered READY only when all of the following are true:

1. Flutter production sweep has removed obsolete demo/local-only surfaces from the capture path.
2. Synthetic data is realistic but contains no real client information.
3. The tested build uses the canonical application ID `br.com.lafamigliaplayworks.fitnexuscoach`.
4. Screenshot dimensions and formats satisfy the current Play asset contract.
5. The screenshot matches the current version of the app.
6. The asset was visually reviewed for clipping, overflow, placeholder text and debug artifacts.

Until then: `PLAY_SCREENSHOT_EVIDENCE=NOT_PROVEN`.
