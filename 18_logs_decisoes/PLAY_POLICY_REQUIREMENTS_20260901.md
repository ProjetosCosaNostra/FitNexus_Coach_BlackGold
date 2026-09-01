# Google Play publication requirements — 2026-09-01

Publication-critical facts verified against current Google Play / Android documentation:

- New apps and app updates submitted from 2026-08-31 must target Android 16 / API 36 or higher (unless an extension applies).
- Play Billing Library 7 reached its normal new-app/update deadline on 2026-08-31; supported releases should use Play Billing Library 8 or later.
- Digital subscriptions sold inside an Android app distributed through Google Play must use Google Play Billing unless a specific policy exception/program applies.
- Play subscription products are configured as subscription -> base plans -> offers in Play Console.

FitNexus publication train therefore targets API 36 and a current Flutter `in_app_purchase` implementation backed by a supported Play Billing Library.
