import 'package:fitnexus_app/app/fitnexus_app.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  Future<void> pumpAtSize(
    WidgetTester tester,
    Size size,
  ) async {
    tester.view.devicePixelRatio = 1.0;
    tester.view.physicalSize = size;

    await tester.pumpWidget(const FitNexusApp());
    await tester.pump();
  }

  tearDown(() {
    TestWidgetsFlutterBinding.ensureInitialized();
  });

  testWidgets('FitNexus landing renders without overflow at 800x600',
      (WidgetTester tester) async {
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await pumpAtSize(tester, const Size(800, 600));

    expect(tester.takeException(), isNull);
    expect(find.text('FitNexus Coach'), findsOneWidget);
    expect(
      find.text('Treinos digitais profissionais para personal, professor e academia.'),
      findsOneWidget,
    );
    expect(find.text('Ver painel do professor'), findsWidgets);
  });

  testWidgets('FitNexus landing renders without overflow on mobile',
      (WidgetTester tester) async {
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await pumpAtSize(tester, const Size(390, 844));

    expect(tester.takeException(), isNull);
    expect(find.text('FitNexus Coach'), findsOneWidget);
    expect(find.text('Como funciona'), findsOneWidget);
  });
}
