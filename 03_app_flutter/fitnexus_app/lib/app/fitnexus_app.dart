import 'package:flutter/material.dart';

import '../features/auth/auth_preview_page.dart';
import '../features/demo/demo_home_page.dart';
import '../features/landing/ecosystem_links_page.dart';
import '../features/landing/landing_page.dart';
import '../features/professor/professor_dashboard_page.dart';
import '../features/student/student_workout_page.dart';

class FitNexusApp extends StatelessWidget {
  const FitNexusApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'FitNexus Coach BlackGold',
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
      routes: <String, WidgetBuilder>{
        '/': (_) => const LandingPage(),
        '/links': (_) => const EcosystemLinksPage(),
        '/demo': (_) => const DemoHomePage(),
        '/auth': (_) => const AuthPreviewPage(),
        '/professor': (_) => const ProfessorDashboardPage(),
        '/student': (_) => const StudentWorkoutPage(),
      },
    );
  }
}
