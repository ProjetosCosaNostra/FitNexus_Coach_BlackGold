import 'package:fitnexus_app/features/landing/landing_page.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

MaterialApp _testApp() {
  return MaterialApp(
    theme: ThemeData.dark(useMaterial3: true),
    routes: <String, WidgetBuilder>{
      '/auth': (_) => const Scaffold(body: Text('auth')),
      '/start': (_) => const Scaffold(body: Text('start')),
      '/links': (_) => const Scaffold(body: Text('links')),
      '/support': (_) => const Scaffold(body: Text('support')),
    },
    home: const LandingPage(),
  );
}

Future<void> _systemBack(WidgetTester tester) async {
  await tester.binding.handlePopRoute();
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('approved BlackGold home fits 360x800 without render errors', (
    WidgetTester tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(360, 800));
    addTearDown(() => tester.binding.setSurfaceSize(null));

    await tester.pumpWidget(_testApp());
    await tester.pump();

    expect(find.text('COACH  BLACKGOLD'), findsOneWidget);
    expect(find.textContaining('Sua evolução'), findsOneWidget);
    expect(find.textContaining('sob controle.'), findsOneWidget);
    expect(find.text('Ecossistema'), findsOneWidget);
    expect(find.text('Criar conta'), findsOneWidget);
    expect(find.text('Começar treino'), findsOneWidget);
    expect(find.text('Plano alimentar'), findsOneWidget);
    expect(find.text('Falar com coach'), findsOneWidget);
    expect(find.text('Treinos da semana'), findsOneWidget);
    expect(find.text('2.450'), findsOneWidget);
    expect(find.text('78,4'), findsOneWidget);
    expect(find.text('72%'), findsOneWidget);
    expect(find.byKey(const ValueKey<String>('public-signup-entry')), findsOneWidget);
    expect(find.byKey(const ValueKey<String>('public-login-entry')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('approved home preserves public entry routes', (
    WidgetTester tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(390, 844));
    addTearDown(() => tester.binding.setSurfaceSize(null));

    await tester.pumpWidget(_testApp());
    await tester.pump();

    await tester.tap(find.text('Ecossistema'));
    await tester.pumpAndSettle();
    expect(find.text('links'), findsOneWidget);

    await _systemBack(tester);
    await tester.tap(find.byKey(const ValueKey<String>('public-signup-entry')));
    await tester.pumpAndSettle();
    expect(find.text('start'), findsOneWidget);

    await _systemBack(tester);
    await tester.tap(find.byKey(const ValueKey<String>('public-login-entry')));
    await tester.pumpAndSettle();
    expect(find.text('auth'), findsOneWidget);

    await _systemBack(tester);
    await tester.ensureVisible(find.text('Falar com coach'));
    await tester.tap(find.text('Falar com coach'));
    await tester.pumpAndSettle();
    expect(find.text('support'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
