# BGF-FLUTTER-RESPONSIVE-HERO-OVERFLOW-011

## Symptom

The autonomous Flutter quality gate detected a `RenderFlex` overflow in the landing hero at an 800×600 logical viewport. The hero used a fixed-height section derived from viewport height while its tablet panel could require more vertical space than the remaining `Expanded` area.

## Root cause

A responsive breakpoint changed the amount of content shown (`_HeroMiniGrid`) without guaranteeing that the hero's vertical sizing contract grew with that content. A short desktop/tablet browser window therefore produced a valid width breakpoint with an invalid height budget.

## Permanent prevention

- Landing startup tests MUST include a short desktop/tablet viewport (800×600).
- Mobile startup tests MUST include a representative phone viewport.
- Responsive fixes MUST preserve scrollability and MUST NOT hide overflow with clipping.
- CI runs `flutter analyze` and `flutter test` on every relevant PR/push.
- A layout regression blocks promotion/merge.

## Recovery implemented

`ResponsiveLandingPage` establishes a minimum logical height only when the physical viewport is too short for the content contract. The underlying landing remains scrollable; the content is not clipped or removed.

## Promotion rule

This failure class is considered closed only after the GitHub Flutter Quality Gate passes both static analysis and widget tests on the repaired branch.
