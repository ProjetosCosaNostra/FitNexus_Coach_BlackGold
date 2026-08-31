import 'package:flutter/material.dart';

import 'features/professor/professor_coach_action_center_page.dart';
import 'features/professor/professor_coach_action_repository.dart';
import 'features/professor/student_access_management_page.dart';

const String fitNexusStoreCaptureShot = String.fromEnvironment(
  'FITNEXUS_STORE_CAPTURE_SHOT',
  defaultValue: '01',
);

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  if (!fitNexusStoreCaptureMode) {
    throw StateError(
      'FITNEXUS_STORE_CAPTURE must be enabled only for controlled store asset builds.',
    );
  }
  if (fitNexusStoreCaptureShot != '01' && fitNexusStoreCaptureShot != '02') {
    throw StateError('Unsupported FITNEXUS_STORE_CAPTURE_SHOT.');
  }
  runApp(const _FitNexusStoreCaptureApp());
}

class _FitNexusStoreCaptureApp extends StatelessWidget {
  const _FitNexusStoreCaptureApp();

  Widget _home() {
    if (fitNexusStoreCaptureShot == '02') {
      return const StudentAccessManagementPage();
    }
    return const ProfessorCoachActionCenterPage();
  }

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
      home: _home(),
    );
  }
}
