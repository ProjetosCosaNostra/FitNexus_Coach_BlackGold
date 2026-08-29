# FitNexus Play Store Device Bootstrap V1

This local-only bootstrap exists to remove the `CANONICAL_PACKAGE_NOT_INSTALLED` blocker without asking the operator to install APKs manually.

It discovers ADB, requires exactly one authorized Android device/emulator, reuses the existing external DPAPI-protected upload signing authority, materializes `android/key.properties` only temporarily, builds the current release APK, installs/replaces the canonical package with ADB, verifies version `0.9.0+2`, writes current-only evidence, and removes runner-owned key properties.

It does not create accounts, mutate Supabase or Play Console, upload an AAB, publish assets, capture screenshots, or activate billing.
