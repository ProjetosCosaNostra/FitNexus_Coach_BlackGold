import 'package:fitnexus_app/features/landing/public_contact_page.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('public contact page exposes authorized channel and boundary',
      (WidgetTester tester) async {
    await tester.pumpWidget(
      const MaterialApp(home: PublicContactPage()),
    );

    expect(find.byKey(const ValueKey<String>('public-contact-title')), findsOneWidget);
    expect(find.byKey(const ValueKey<String>('public-contact-email')), findsOneWidget);
    expect(find.text('projetoscosanostra@gmail.com'), findsOneWidget);
    expect(
      find.byKey(const ValueKey<String>('public-contact-protocol-boundary')),
      findsOneWidget,
    );
  });
}
