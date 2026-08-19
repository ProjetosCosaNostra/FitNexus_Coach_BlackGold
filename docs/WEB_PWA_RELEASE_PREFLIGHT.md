# FitNexus Coach BlackGold — Web/PWA Release Preflight

> **STATUS: BUILD PREFLIGHT ONLY — NOT A PRODUCTION DEPLOYMENT ATTESTATION**

## Why this exists

The Web/PWA distribution path is the preferred low-cost FitNexus entry point, but `production_deployment` is still a controlled-launch gate. This preflight makes the web artifact buildable and testable without publishing it or pretending that domain/TLS/legal/rollback evidence already exists.

## Defect found and repaired

`web/index.html` referenced `manifest.json`, but that file was not present in the tracked web directory. The shell also still carried default Flutter metadata (`A new Flutter project`, `fitnexus_app`) and referenced a favicon file that was not tracked.

The repair:

- adds a branded PWA manifest;
- uses the existing tracked 192/512 regular and maskable icons;
- points favicon to an existing tracked icon;
- brands title/description/apple metadata;
- preserves `$FLUTTER_BASE_HREF` for non-root hosting;
- keeps `noindex` while controlled launch is blocked.

## Permanent guard

`04_backend_supabase/tools/verify_web_release_contract.py` fails CI if:

- the PWA manifest disappears;
- tracked manifest icons disappear or drift;
- the Flutter base-href placeholder disappears;
- default Flutter placeholder metadata returns;
- the app becomes indexable before launch admission is deliberately changed;
- the favicon again points at a missing asset.

Failure class: `BGF-WEB-PWA-RELEASE-CONTRACT-146`.

## Build proof

The normal Flutter Quality Gate now runs:

```text
flutter build web --release --base-href /FitNexus_Coach_BlackGold/
```

This proves that the current repository can produce a release-mode web artifact for the intended project subpath. It does **not** publish that artifact.

## What still blocks `production_deployment`

The production gate remains blocked until real evidence exists for:

- stable production hosting/domain decision;
- live TLS/route check;
- production environment configuration without leaked secrets;
- deployed release commit identity;
- smoke-test receipt against the live route;
- monitoring/alerting readiness;
- backup/restore references where applicable;
- tested rollback or previous-release restore;
- final release evidence digest through a dedicated evidence migration.

Legal/privacy/payment gates remain independent and are not bypassed by a successful web build.
