# FitNexus — Screenshot 02 black-frame evidence and V7 render readiness

Date: 2026-08-31

## Human evidence
Windows inspection of `02_student_management_1080x1920.png` from the V6 run showed a fully black 1080x1920 frame. The file size reported by the runner was 12,504 bytes and the production release was restored successfully.

## What this proves
V6 materially advanced beyond foreground ownership: it reached `screencap`, but foreground Activity/window ownership alone is not proof that Flutter has presented a usable frame. The production capture entrypoint routes shot 02 to `StudentAccessManagementPage`, whose UI contains visible text, cards and BlackGold elements, so a fully black image cannot be accepted as the intended store asset.

Stable prevention class: `FNX-PLAY-SCREENSHOT-02-FOREGROUND-BEFORE-FLUTTER-RENDER-READY-010`.

## V7 strategy
`FITNEXUS_PLAY_STORE_SCREENSHOT_02_RENDER_READY_AUTHORITY_V7.ps1` adds two authorities before final screencap:

1. Device display authority
   - send Android wake key event;
   - request keyguard dismissal;
   - emit power-state evidence.

2. Rendered-frame authority
   - preserve V6 explicit MainActivity launch and foreground ownership checks;
   - repeatedly capture temporary probe PNGs;
   - require 1080x1920 plus visible-content samples and BlackGold-like samples before allowing the final screenshot;
   - if readiness never appears, emit power and filtered logcat diagnostics and fail closed.

V7 does not lower the final human/visual acceptance requirement, does not mutate Supabase or Play Console, and keeps the existing production APK restoration path.

## Next gate
Run the V7 exact-head proof on Windows. If GREEN, open the resulting Screenshot 02 and perform human visual review before PR promotion. If V7 fails, use its power/render/logcat diagnostics as the next cause authority instead of creating another blind capture loop.
