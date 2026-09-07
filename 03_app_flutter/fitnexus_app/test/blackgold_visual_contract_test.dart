import 'package:fitnexus_app/features/landing/landing_page.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

MaterialApp _app() {
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

void main() {
  testWidgets('mobile keeps the approved frozen visual hierarchy', (
    WidgetTester tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(390, 844));
    addTearDown(() => tester.binding.setSurfaceSize(null));

    await tester.pumpWidget(_app());
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
    expect(find.text('Nutrição'), findsOneWidget);
    expect(find.text('Agenda'), findsOneWidget);
    expect(find.text('Resultados'), findsOneWidget);
    expect(find.text('Hábitos'), findsOneWidget);
    expect(find.text('Comunidade'), findsOneWidget);
    expect(find.text('Seu progresso semanal'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('desktop renders the BlackGold cockpit instead of a narrow landing rail', (
    WidgetTester tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(1440, 1000));
    addTearDown(() => tester.binding.setSurfaceSize(null));

    await tester.pumpWidget(_app());
    await tester.pump();

    expect(find.text('COACH  BLACKGOLD'), findsOneWidget);
    expect(find.text('Alunos'), findsWidgets);
    expect(find.text('IA Coach'), findsOneWidget);
    expect(find.text('Resumo da semana'), findsOneWidget);
    expect(find.text('Evolução dos alunos'), findsOneWidget);
    expect(find.text('Distribuição de treinos'), findsOneWidget);
    expect(find.text('Ações sugeridas (IA Coach)'), findsOneWidget);
    expect(find.text('Ecossistema'), findsWidgets);
    expect(find.text('Criar conta'), findsOneWidget);
    expect(find.byKey(const ValueKey<String>('public-login-entry')), findsOneWidget);
    expect(find.byKey(const ValueKey<String>('public-signup-entry')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
