# FitNexus Coach BlackGold — Google Play Data Safety Inventory V1

Status: **NON-ATTESTING INVENTORY — NOT A PLAY CONSOLE SUBMISSION**

Google Play requires developers to declare how the app collects, shares and protects user data. This file is a working inventory only. It must be reconciled with the real production data flows, final SDK inventory, independent privacy review and the Play Console form before submission.

## Current source observations

The current Flutter dependency surface includes `supabase_flutter`, `shared_preferences`, `url_launcher` and `qr_flutter`. No advertising SDK is present in the current Flutter `pubspec.yaml`; this does **not** by itself prove the final Play ads declaration because native dependencies and runtime behavior must still be checked.

The product requires authenticated professional and student experiences and supports student management, workout assignment, workout feedback, subscription entitlement/status and operational follow-up. Because of that product scope, the data categories below must be explicitly reviewed rather than defaulted to “not collected”.

## Data category review matrix

| Google Play area | FitNexus candidate surface | Current state |
| --- | --- | --- |
| Personal info | account identity, email/profile information needed for authenticated access | REVIEW_REQUIRED |
| Health and fitness | workout plans, execution/feedback and fitness-related coaching context may fall within this category | REVIEW_REQUIRED_SENSITIVE |
| App activity | actions used for product operation, audit, support or security may qualify depending on final telemetry | REVIEW_REQUIRED |
| User-generated content | coach/student feedback, notes or other content entered into the service may qualify | REVIEW_REQUIRED |
| Device or other identifiers | Supabase/session/runtime libraries may use identifiers; final SDK/runtime analysis required | REVIEW_REQUIRED |
| Financial info | FitNexus Play app must not collect external billing credentials directly; provider/server flows still require review | REVIEW_REQUIRED_SERVER_SIDE |
| Location | no location feature is asserted by this inventory | NOT_EVIDENCED_RECONFIRM_BEFORE_SUBMISSION |
| Contacts | no contacts permission/feature is asserted by this inventory | NOT_EVIDENCED_RECONFIRM_BEFORE_SUBMISSION |
| Photos/videos/files | no final collection declaration is made; future exercise/media features would require reassessment | NOT_EVIDENCED_RECONFIRM_BEFORE_SUBMISSION |

## Required questions before Play submission

For every category confirmed as collected, determine from production evidence:

1. Is it collected by the app, the backend, an SDK, or more than one?
2. Is it shared with any third party under Google Play's definition?
3. Is collection required or optional for the user?
4. What is the purpose: app functionality, account management, analytics, fraud/security, developer communications, personalization, advertising/marketing, or another allowed purpose?
5. Is data encrypted in transit?
6. Can users request deletion of their data and/or account through the stable public route required by the project compliance gate?
7. Do privacy policy statements match actual retention and deletion behavior?
8. Does any processor/subprocessor receive data outside the primary production environment?

## Android permissions and SDK gate

Before the final declaration, generate evidence from the exact release candidate:

- merged Android manifest and requested permissions;
- complete Gradle dependency inventory;
- Flutter dependency lockfile;
- SDK/provider inventory;
- network destinations observed in controlled testing where appropriate;
- production Supabase/data-flow inventory;
- final privacy policy and retention matrix references.

No Play Data Safety answer may be inferred solely from this document.

## FitNexus-specific fail-closed rules

- Fitness/health-related information must be treated conservatively until independent privacy review resolves classification and treatment.
- A free download does not remove Data Safety obligations.
- Absence of an advertising SDK in current Flutter dependencies does not automatically close the Ads declaration.
- The Android app must not expose Asaas credentials, payment secrets or raw billing credentials.
- Play reviewer credentials, user credentials and personal documents must never be committed to GitHub.
- A completed form in the Play Console is an external fact and must be recorded only after real submission/readback evidence exists.

Until final reconciliation: `PLAY_DATA_SAFETY=NOT_READY_FOR_SUBMISSION`.
