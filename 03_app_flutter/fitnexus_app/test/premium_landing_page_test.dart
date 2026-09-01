import 'package:fitnexus_app/features/landing/landing_page.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('premium landing fits a mobile viewport without render errors', (
    WidgetTester tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(360, 800));
    addTearDown(() => tester.binding.setSurfaceSize(null));

    await tester.pumpWidget(
      MaterialApp(
        theme: ThemeData.dark(useMaterial3: true),
        routes: <String, WidgetBuilder>{
          '/auth': (_) => const Scaffold(body: Text('auth')),
          '/start': (_) => const Scaffold(body: Text('start')),
          '/links': (_) => const Scaffold(body: Text('links')),
          '/support': (_) => const Scaffold(body: Text('support')),
        },
        home: const LandingPage(),
      ),
    );
    await tester.pump();

    expect(find.text('FitNexus Coach'), findsOneWidget);
    expect(find.textContaining('Treinos, alunos e evolução.'), findsOneWidget);
    expect(find.byKey(const ValueKey<String>('public-signup-entry')), findsOneWidget);
    expect(find.byKey(const ValueKey<String>('public-login-entry')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
