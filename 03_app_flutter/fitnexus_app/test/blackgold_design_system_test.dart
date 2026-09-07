import 'package:fitnexus_app/core/theme/app_colors.dart';
import 'package:fitnexus_app/core/theme/app_theme.dart';
import 'package:fitnexus_app/core/theme/blackgold_tokens.dart';
import 'package:fitnexus_app/features/shared/fitnexus_ui.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('approved BlackGold palette stays frozen', () {
    expect(AppColors.black, const Color(0xFF000000));
    expect(AppColors.gold, const Color(0xFFF2C14E));
    expect(AppColors.goldSoft, const Color(0xFFFFD76A));
    expect(AppColors.text, const Color(0xFFF8F6F0));
    expect(AppColors.borderGold, const Color(0xFF5C4514));
  });

  test('product theme uses the same BlackGold authority', () {
    final ThemeData theme = AppTheme.dark;

    expect(theme.brightness, Brightness.dark);
    expect(theme.scaffoldBackgroundColor, AppColors.black);
    expect(theme.colorScheme.primary, AppColors.gold);
    expect(theme.colorScheme.secondary, AppColors.goldSoft);
    expect(theme.colorScheme.surface, AppColors.card);
  });

  test('spacing and radius scales remain shared instead of page-local', () {
    expect(BlackGoldSpace.xs, 8);
    expect(BlackGoldSpace.md, 16);
    expect(BlackGoldSpace.xl, 24);
    expect(BlackGoldRadius.control, 10);
    expect(BlackGoldRadius.panel, 18);
  });

  testWidgets('shared shell exposes the official product brand',
      (WidgetTester tester) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.dark,
        home: const FitShell(
          child: FitCard(
            child: Text('Conteúdo'),
          ),
        ),
      ),
    );

    expect(find.byType(FitHeader), findsOneWidget);
    expect(find.text('C O A C H   B L A C K G O L D'), findsOneWidget);
    expect(find.text('Ecossistema'), findsOneWidget);
    expect(find.text('Início'), findsOneWidget);
    expect(find.text('Conteúdo'), findsOneWidget);
  });
}
