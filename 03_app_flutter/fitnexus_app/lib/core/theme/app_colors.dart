import 'package:flutter/material.dart';

import 'blackgold_tokens.dart';

/// Backwards-compatible color facade.
///
/// Existing screens may keep importing [AppColors], but every value now comes
/// from the single BlackGold visual authority. New code should prefer the
/// semantic names exposed here or [BlackGoldPalette] directly.
class AppColors {
  const AppColors._();

  static const Color black = BlackGoldPalette.canvas;
  static const Color blackSoft = BlackGoldPalette.canvasSoft;
  static const Color card = BlackGoldPalette.surface;
  static const Color cardRaised = BlackGoldPalette.surfaceRaised;
  static const Color cardSoft = BlackGoldPalette.surfaceMuted;

  static const Color gold = BlackGoldPalette.gold;
  static const Color goldSoft = BlackGoldPalette.goldBright;
  static const Color goldDeep = BlackGoldPalette.goldDeep;

  static const Color text = BlackGoldPalette.textPrimary;
  static const Color muted = BlackGoldPalette.textSecondary;
  static const Color mutedSoft = BlackGoldPalette.textTertiary;

  static const Color border = BlackGoldPalette.goldBorderSoft;
  static const Color borderGold = BlackGoldPalette.goldBorder;

  static const Color success = BlackGoldPalette.success;
  static const Color warning = BlackGoldPalette.warning;
  static const Color danger = BlackGoldPalette.danger;
}
