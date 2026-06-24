import 'package:fitnexus_app/app/fitnexus_app.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('FitNexus app starts', (WidgetTester tester) async {
    await tester.pumpWidget(const FitNexusApp());

    expect(find.text('FitNexus Coach'), findsOneWidget);
    expect(find.text('Começar teste grátis'), findsOneWidget);
  });
}
