import 'package:flutter/material.dart';

import '../auth/auth_gate.dart';
import '../auth/auth_service.dart';
import 'professor_live_dashboard_page.dart';
import 'student_access_management_page.dart';

class AuthenticatedProfessorPage extends StatelessWidget {
  const AuthenticatedProfessorPage({super.key});

  Future<void> _signOut(BuildContext context) async {
    final NavigatorState navigator = Navigator.of(context);
    await AuthService.instance.signOut();
    navigator.pushNamedAndRemoveUntil('/auth', (Route<dynamic> route) => false);
  }

  void _openStudentAccess(BuildContext context) {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => const StudentAccessManagementPage(),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return AuthGate(
      child: Stack(
        children: <Widget>[
          const ProfessorLiveDashboardPage(),
          Positioned(
            right: 22,
            bottom: 22,
            child: SafeArea(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.end,
                children: <Widget>[
                  FloatingActionButton.extended(
                    heroTag: 'fitnexus_student_access',
                    onPressed: () => _openStudentAccess(context),
                    backgroundColor: const Color(0xFF171717),
                    foregroundColor: const Color(0xFFFFD45A),
                    icon: const Icon(Icons.qr_code_2_rounded),
                    label: const Text(
                      'Acesso do aluno',
                      style: TextStyle(fontWeight: FontWeight.w900),
                    ),
                  ),
                  const SizedBox(height: 10),
                  FloatingActionButton.extended(
                    heroTag: 'fitnexus_logout',
                    onPressed: () => _signOut(context),
                    backgroundColor: const Color(0xFFE1B92F),
                    foregroundColor: Colors.black,
                    icon: const Icon(Icons.logout_rounded),
                    label: const Text(
                      'Sair',
                      style: TextStyle(fontWeight: FontWeight.w900),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
