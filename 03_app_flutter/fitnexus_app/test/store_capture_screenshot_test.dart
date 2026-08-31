import 'dart:io';
import 'dart:ui' as ui;

import 'package:fitnexus_app/features/professor/professor_decision_intelligence_page.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('renders Play screenshot 03 at 1080x1920 without emulator',
      (WidgetTester tester) async {
    await tester.binding.setSurfaceSize(const Size(360, 640));
    addTearDown(() => tester.binding.setSurfaceSize(null));

    const Key captureKey = ValueKey<String>('fitnexus_store_capture_root');

    await tester.pumpWidget(
      MaterialApp(
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          useMaterial3: true,
          brightness: Brightness.dark,
          scaffoldBackgroundColor: const Color(0xFF050505),
          colorScheme: const ColorScheme.dark(
            primary: Color(0xFFE1B92F),
            secondary: Color(0xFFFFD45A),
            surface: Color(0xFF101010),
          ),
        ),
        home: const RepaintBoundary(
          key: captureKey,
          child: ProfessorDecisionIntelligencePage(),
        ),
      ),
    );

    await tester.pumpAndSettle(const Duration(milliseconds: 100));

    final Finder target = find.byKey(captureKey);
    expect(target, findsOneWidget);
    expect(find.text('DECISION INTELLIGENCE'), findsOneWidget);

    final RenderRepaintBoundary boundary =
        tester.renderObject<RenderRepaintBoundary>(target);
    final ui.Image image = await boundary.toImage(pixelRatio: 3.0);
    expect(image.width, 1080);
    expect(image.height, 1920);

    final ByteData? byteData =
        await image.toByteData(format: ui.ImageByteFormat.png);
    expect(byteData, isNotNull);

    final String output = Platform.environment['FNX_STORE_SCREENSHOT_OUTPUT'] ?? '';
    expect(output, isNotEmpty,
        reason: 'FNX_STORE_SCREENSHOT_OUTPUT must be provided by the runner.');

    final File file = File(output);
    await file.parent.create(recursive: true);
    await file.writeAsBytes(byteData!.buffer.asUint8List(), flush: true);

    image.dispose();

    expect(await file.exists(), isTrue);
    expect(await file.length(), greaterThan(20000));
  });
}
