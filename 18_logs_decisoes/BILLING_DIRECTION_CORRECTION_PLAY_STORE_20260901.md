# Monetization direction correction — Google Play first

Effective immediately, the publication-critical monetization path for Android is Google Play Billing.

## Authority
- Android distributed through Google Play: subscription purchase UI and payment must use Google Play Billing for FitNexus digital subscription access.
- Flutter Web / Windows remain the same FitNexus SaaS surfaces and consume account entitlements; they must not depend on Android-only Billing APIs to render or run.
- Existing Asaas server work is retained as non-publication-critical infrastructure and must not block Android publication.

## Publication priority
1. Android target/API compliance.
2. Google Play Billing client integration.
3. Play subscription product/base-plan contract.
4. Purchase verification/entitlement synchronization.
5. AAB build + internal track.
6. Emulator/device review from Play-distributed build.
7. Store listing/publication.

No screenshot-generation workflow is a publication blocker before the final Play Console listing step.
