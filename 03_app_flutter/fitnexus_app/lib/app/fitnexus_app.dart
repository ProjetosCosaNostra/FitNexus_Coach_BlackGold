import 'package:flutter/material.dart';

import '../core/theme/app_theme.dart';
import '../features/landing/landing_page.dart';

class FitNexusApp extends StatelessWidget {
  const FitNexusApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'FitNexus Coach BlackGold',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.dark,
      home: const LandingPage(),
    );
  }
}
