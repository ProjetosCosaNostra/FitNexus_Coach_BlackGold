import 'package:fitnexus_app/app/fitnexus_app.dart';
import 'package:fitnexus_app/features/student/student_workout_page.dart';
import 'package:fitnexus_app/features/student/student_workout_repository.dart';
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
    expect(find.textContaining('Treinos, alunos e evolução.'), findsOneWidget);
    expect(
      find.byKey(const ValueKey<String>('public-signup-entry')),
      findsOneWidget,
    );
    expect(
      find.byKey(const ValueKey<String>('public-login-entry')),
      findsOneWidget,
    );
  });

  testWidgets('FitNexus landing renders without overflow on mobile',
      (WidgetTester tester) async {
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await pumpAtSize(tester, const Size(390, 844));

    expect(tester.takeException(), isNull);
    expect(find.text('FitNexus Coach'), findsOneWidget);
    expect(find.textContaining('Treinos, alunos e evolução.'), findsOneWidget);
    expect(find.text('Começar grátis'), findsOneWidget);
    expect(find.text('Já tenho conta'), findsOneWidget);
  });

  testWidgets('Student screen fails closed when access token is missing',
      (WidgetTester tester) async {
    await tester.pumpWidget(
      const MaterialApp(home: StudentWorkoutPage(token: '')),
    );
    await tester.pump();

    expect(tester.takeException(), isNull);
    expect(find.text('Link de aluno necessário'), findsOneWidget);
    expect(
      find.textContaining('link ou QR Code enviado pelo seu professor'),
      findsOneWidget,
    );
  });

  test('Rest timer derives seconds from exercise prescription', () {
    const StudentWorkoutExercise withRest = StudentWorkoutExercise(
      id: '1',
      position: 0,
      name: 'Agachamento',
      prescription: '4x10 • descanso 90s',
      completed: false,
    );
    const StudentWorkoutExercise withoutRest = StudentWorkoutExercise(
      id: '2',
      position: 1,
      name: 'Remada',
      prescription: '3x12',
      completed: false,
    );

    expect(withRest.restSeconds, 90);
    expect(withoutRest.restSeconds, 60);
  });
}
