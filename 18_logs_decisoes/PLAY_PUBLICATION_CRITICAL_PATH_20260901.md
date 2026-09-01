# FitNexus — publication critical path

The release train is now optimized for first revenue through Google Play.

- Android package: `br.com.lafamigliaplayworks.fitnexuscoach`
- Android monetization: Google Play Billing subscriptions
- Shared product: Flutter codebase for Android, Web and Windows
- Cross-platform entitlement: server account state; Android Play purchases are synchronized to the account
- Web/Windows must remain usable/installable without importing an Android-only payment runtime at execution time
- Asaas is non-blocking and not part of the Play publication critical path
- Marketing screenshots/assets are deferred until the Play Console listing step
