import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../core/theme/app_theme.dart';
import '../features/auth/auth_preview_page.dart';
import '../features/demo/demo_home_page.dart';
import '../features/landing/ecosystem_links_page.dart';
import '../features/landing/landing_page.dart';
import '../features/landing/public_contact_page.dart';
import '../features/professor/authenticated_professor_page.dart';
import '../features/student/student_experience_page.dart';

Map<String, WidgetBuilder> buildFitNexusRoutes({required bool includeDemo}) {
  return <String, WidgetBuilder>{
    '/landing': (_) => const LandingPage(),
    '/': (_) => const LandingPage(),
    '/links': (_) => const EcosystemLinksPage(),
    '/support': (_) => const PublicContactPage(),
    if (includeDemo) '/demo': (_) => const DemoHomePage(),
    '/auth': (_) => const AuthPreviewPage(),
    '/start': (_) => const AuthPreviewPage(initialRegisterMode: true),
    '/professor': (_) => const AuthenticatedProfessorPage(),
    '/student': (_) => const StudentExperiencePage(),
  };
}

class FitNexusApp extends StatelessWidget {
  const FitNexusApp({super.key});

  Route<dynamic>? _onGenerateRoute(RouteSettings settings) {
    final Uri uri = Uri.tryParse(settings.name ?? '') ?? Uri();
    if (uri.path == '/student') {
      return MaterialPageRoute<void>(
        settings: settings,
        builder: (_) => StudentExperiencePage(token: uri.queryParameters['token']),
      );
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'FitNexus Coach BlackGold',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.dark,
      routes: buildFitNexusRoutes(includeDemo: !kReleaseMode),
      onGenerateRoute: _onGenerateRoute,
    );
  }
}
