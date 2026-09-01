# Asaas boundary for Play launch

Existing Asaas checkout/webhook infrastructure is retained as optional backend capability, but it is explicitly removed from the Android publication critical path.

It must not block:
- Google Play Billing integration;
- AAB generation;
- internal/closed testing;
- Play listing completion;
- production publication.

Android subscription purchase UX must prefer Google Play Billing when the app is installed from Google Play.
