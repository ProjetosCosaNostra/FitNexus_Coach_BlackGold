import 'package:flutter/material.dart';

import 'app_colors.dart';
import 'blackgold_tokens.dart';

/// Product-wide FitNexus Coach BlackGold theme.
///
/// This is the only Material theme authority. Feature pages must consume this
/// theme/shared components instead of creating independent palettes.
class AppTheme {
  const AppTheme._();

  static ThemeData get dark {
    const ColorScheme scheme = ColorScheme.dark(
      primary: AppColors.gold,
      onPrimary: Colors.black,
      secondary: AppColors.goldSoft,
      onSecondary: Colors.black,
      surface: AppColors.card,
      onSurface: AppColors.text,
      error: AppColors.danger,
      onError: Colors.black,
    );

    const TextTheme typography = TextTheme(
      displayLarge: TextStyle(
        color: AppColors.text,
        fontSize: 48,
        height: 1.03,
        fontWeight: FontWeight.w900,
        letterSpacing: -1.6,
      ),
      displayMedium: TextStyle(
        color: AppColors.text,
        fontSize: 40,
        height: 1.06,
        fontWeight: FontWeight.w900,
        letterSpacing: -1.2,
      ),
      headlineLarge: TextStyle(
        color: AppColors.text,
        fontSize: 32,
        height: 1.08,
        fontWeight: FontWeight.w900,
        letterSpacing: -0.7,
      ),
      headlineMedium: TextStyle(
        color: AppColors.text,
        fontSize: 26,
        height: 1.10,
        fontWeight: FontWeight.w800,
        letterSpacing: -0.4,
      ),
      titleLarge: TextStyle(
        color: AppColors.text,
        fontSize: 20,
        height: 1.15,
        fontWeight: FontWeight.w800,
      ),
      titleMedium: TextStyle(
        color: AppColors.text,
        fontSize: 16,
        height: 1.20,
        fontWeight: FontWeight.w700,
      ),
      bodyLarge: TextStyle(
        color: AppColors.text,
        fontSize: 16,
        height: 1.45,
        fontWeight: FontWeight.w500,
      ),
      bodyMedium: TextStyle(
        color: AppColors.muted,
        fontSize: 14,
        height: 1.45,
        fontWeight: FontWeight.w400,
      ),
      bodySmall: TextStyle(
        color: AppColors.muted,
        fontSize: 12,
        height: 1.35,
        fontWeight: FontWeight.w400,
      ),
      labelLarge: TextStyle(
        color: AppColors.text,
        fontSize: 14,
        height: 1.15,
        fontWeight: FontWeight.w800,
      ),
      labelMedium: TextStyle(
        color: AppColors.muted,
        fontSize: 12,
        height: 1.15,
        fontWeight: FontWeight.w700,
      ),
    );

    final OutlineInputBorder inputBorder = OutlineInputBorder(
      borderRadius: BorderRadius.circular(BlackGoldRadius.control),
      borderSide: const BorderSide(
        color: AppColors.borderGold,
        width: BlackGoldStroke.hairline,
      ),
    );

    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      fontFamily: 'Arial',
      scaffoldBackgroundColor: AppColors.black,
      canvasColor: AppColors.black,
      cardColor: AppColors.card,
      dividerColor: AppColors.border,
      colorScheme: scheme,
      textTheme: typography,
      iconTheme: const IconThemeData(color: AppColors.goldSoft, size: 21),
      dividerTheme: const DividerThemeData(
        color: AppColors.border,
        thickness: BlackGoldStroke.hairline,
        space: BlackGoldSpace.xl,
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: AppColors.gold,
          foregroundColor: Colors.black,
          disabledBackgroundColor: AppColors.goldDeep,
          disabledForegroundColor: Colors.black54,
          elevation: 0,
          padding: const EdgeInsets.symmetric(
            horizontal: BlackGoldSpace.lg,
            vertical: 15,
          ),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(BlackGoldRadius.control),
          ),
          textStyle: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w900,
          ),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: AppColors.text,
          side: const BorderSide(
            color: AppColors.borderGold,
            width: BlackGoldStroke.regular,
          ),
          padding: const EdgeInsets.symmetric(
            horizontal: BlackGoldSpace.lg,
            vertical: 15,
          ),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(BlackGoldRadius.control),
          ),
          textStyle: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w800,
          ),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: AppColors.goldSoft,
          textStyle: const TextStyle(fontWeight: FontWeight.w800),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(BlackGoldRadius.control),
          ),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColors.cardRaised,
        labelStyle: const TextStyle(color: AppColors.muted),
        hintStyle: const TextStyle(color: AppColors.mutedSoft),
        helperStyle: const TextStyle(color: AppColors.muted),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: BlackGoldSpace.md,
          vertical: 15,
        ),
        enabledBorder: inputBorder,
        border: inputBorder,
        focusedBorder: inputBorder.copyWith(
          borderSide: const BorderSide(
            color: AppColors.gold,
            width: BlackGoldStroke.emphasis,
          ),
        ),
        errorBorder: inputBorder.copyWith(
          borderSide: const BorderSide(color: AppColors.danger),
        ),
        focusedErrorBorder: inputBorder.copyWith(
          borderSide: const BorderSide(
            color: AppColors.danger,
            width: BlackGoldStroke.emphasis,
          ),
        ),
      ),
      snackBarTheme: SnackBarThemeData(
        backgroundColor: AppColors.cardRaised,
        contentTextStyle: const TextStyle(color: AppColors.text),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(BlackGoldRadius.control),
          side: const BorderSide(color: AppColors.borderGold),
        ),
        behavior: SnackBarBehavior.floating,
      ),
      dialogTheme: DialogThemeData(
        backgroundColor: AppColors.cardRaised,
        surfaceTintColor: Colors.transparent,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(BlackGoldRadius.panel),
          side: const BorderSide(color: AppColors.borderGold),
        ),
      ),
      bottomSheetTheme: const BottomSheetThemeData(
        backgroundColor: AppColors.cardRaised,
        surfaceTintColor: Colors.transparent,
        modalBackgroundColor: AppColors.cardRaised,
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: const Color(0xFF080808),
        indicatorColor: AppColors.gold.withValues(alpha: 0.16),
        iconTheme: WidgetStateProperty.resolveWith<IconThemeData>(
          (Set<WidgetState> states) => IconThemeData(
            color: states.contains(WidgetState.selected)
                ? AppColors.goldSoft
                : AppColors.muted,
          ),
        ),
        labelTextStyle: WidgetStateProperty.resolveWith<TextStyle>(
          (Set<WidgetState> states) => TextStyle(
            color: states.contains(WidgetState.selected)
                ? AppColors.goldSoft
                : AppColors.muted,
            fontSize: 11,
            fontWeight: states.contains(WidgetState.selected)
                ? FontWeight.w800
                : FontWeight.w500,
          ),
        ),
      ),
    );
  }
}
