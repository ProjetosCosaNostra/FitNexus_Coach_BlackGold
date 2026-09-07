import 'package:flutter/material.dart';

/// Frozen visual primitives for the FitNexus Coach BlackGold product family.
///
/// Pages may compose these tokens, but must not invent local palettes, radii or
/// spacing scales. The approved Home is the visual authority for this file.
class BlackGoldPalette {
  const BlackGoldPalette._();

  static const Color canvas = Color(0xFF000000);
  static const Color canvasSoft = Color(0xFF050505);
  static const Color surface = Color(0xFF0B0B0A);
  static const Color surfaceRaised = Color(0xFF10100E);
  static const Color surfaceMuted = Color(0xFF15130E);

  static const Color gold = Color(0xFFF2C14E);
  static const Color goldBright = Color(0xFFFFD76A);
  static const Color goldDeep = Color(0xFF9F7312);
  static const Color goldBorder = Color(0xFF5C4514);
  static const Color goldBorderSoft = Color(0xFF30270F);

  static const Color textPrimary = Color(0xFFF8F6F0);
  static const Color textSecondary = Color(0xFFB7B2A7);
  static const Color textTertiary = Color(0xFF7F7B72);

  static const Color success = Color(0xFF42D790);
  static const Color warning = Color(0xFFFFC857);
  static const Color danger = Color(0xFFFF6B6B);
}

class BlackGoldSpace {
  const BlackGoldSpace._();

  static const double xxs = 4;
  static const double xs = 8;
  static const double sm = 12;
  static const double md = 16;
  static const double lg = 20;
  static const double xl = 24;
  static const double xxl = 32;
  static const double xxxl = 40;
  static const double section = 48;
}

class BlackGoldRadius {
  const BlackGoldRadius._();

  static const double control = 10;
  static const double card = 14;
  static const double panel = 18;
  static const double hero = 20;
  static const double pill = 999;
}

class BlackGoldStroke {
  const BlackGoldStroke._();

  static const double hairline = 0.75;
  static const double regular = 1;
  static const double emphasis = 1.35;
}

class BlackGoldBreakpoints {
  const BlackGoldBreakpoints._();

  static const double mobile = 600;
  static const double tablet = 900;
  static const double desktop = 1180;
}

class BlackGoldEffects {
  const BlackGoldEffects._();

  static List<BoxShadow> get cardShadow => <BoxShadow>[
        BoxShadow(
          color: Colors.black.withValues(alpha: 0.48),
          blurRadius: 28,
          offset: const Offset(0, 14),
        ),
        BoxShadow(
          color: BlackGoldPalette.gold.withValues(alpha: 0.055),
          blurRadius: 22,
          spreadRadius: -8,
        ),
      ];

  static List<BoxShadow> get goldGlow => <BoxShadow>[
        BoxShadow(
          color: BlackGoldPalette.gold.withValues(alpha: 0.20),
          blurRadius: 24,
          spreadRadius: -5,
        ),
      ];

  static const LinearGradient panelGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: <Color>[
      Color(0xFF12110D),
      Color(0xFF080808),
    ],
  );

  static const LinearGradient goldGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: <Color>[
      Color(0xFFFFD86A),
      Color(0xFFE7AE32),
    ],
  );
}
