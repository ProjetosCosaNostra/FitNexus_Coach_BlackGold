import 'package:flutter/material.dart';

import '../auth/auth_gate.dart';
import '../auth/auth_service.dart';
import 'professor_live_dashboard_page.dart';
import 'professor_progress_page.dart';
import 'student_access_management_page.dart';

class AuthenticatedProfessorPage extends StatefulWidget {
  const AuthenticatedProfessorPage({super.key});

  @override
  State<AuthenticatedProfessorPage> createState() =>
      _AuthenticatedProfessorPageState();
}

class _AuthenticatedProfessorPageState
    extends State<AuthenticatedProfessorPage> {
  int _index = 0;

  static const List<Widget> _pages = <Widget>[
    ProfessorLiveDashboardPage(),
    ProfessorProgressPage(),
    StudentAccessManagementPage(),
  ];

  Future<void> _signOut(BuildContext context) async {
    final NavigatorState navigator = Navigator.of(context);
    await AuthService.instance.signOut();
    navigator.pushNamedAndRemoveUntil('/auth', (Route<dynamic> route) => false);
  }

  @override
  Widget build(BuildContext context) {
    return AuthGate(
      child: LayoutBuilder(
        builder: (BuildContext context, BoxConstraints constraints) {
          final bool wide = constraints.maxWidth >= 980;
          final Widget body = IndexedStack(index: _index, children: _pages);

          final Widget workspace = wide
              ? Row(
                  children: <Widget>[
                    NavigationRail(
                      backgroundColor: const Color(0xFF0B0B0B),
                      selectedIndex: _index,
                      onDestinationSelected: (int value) {
                        setState(() => _index = value);
                      },
                      labelType: NavigationRailLabelType.all,
                      selectedIconTheme:
                          const IconThemeData(color: Color(0xFFFFD45A)),
                      selectedLabelTextStyle: const TextStyle(
                        color: Color(0xFFFFD45A),
                        fontWeight: FontWeight.w900,
                      ),
                      unselectedIconTheme:
                          const IconThemeData(color: Color(0xFFB7B7B7)),
                      unselectedLabelTextStyle:
                          const TextStyle(color: Color(0xFFB7B7B7)),
                      destinations: const <NavigationRailDestination>[
                        NavigationRailDestination(
                          icon: Icon(Icons.dashboard_rounded),
                          label: Text('Painel'),
                        ),
                        NavigationRailDestination(
                          icon: Icon(Icons.monitor_heart_rounded),
                          label: Text('Acompanhamento'),
                        ),
                        NavigationRailDestination(
                          icon: Icon(Icons.qr_code_2_rounded),
                          label: Text('Acessos'),
                        ),
                      ],
                    ),
                    const VerticalDivider(width: 1, color: Color(0xFF2C2A22)),
                    Expanded(child: body),
                  ],
                )
              : Column(
                  children: <Widget>[
                    Expanded(child: body),
                    NavigationBar(
                      selectedIndex: _index,
                      onDestinationSelected: (int value) {
                        setState(() => _index = value);
                      },
                      backgroundColor: const Color(0xFF0B0B0B),
                      indicatorColor:
                          const Color(0xFFE1B92F).withValues(alpha: 0.18),
                      destinations: const <NavigationDestination>[
                        NavigationDestination(
                          icon: Icon(Icons.dashboard_rounded),
                          label: 'Painel',
                        ),
                        NavigationDestination(
                          icon: Icon(Icons.monitor_heart_rounded),
                          label: 'Progresso',
                        ),
                        NavigationDestination(
                          icon: Icon(Icons.qr_code_2_rounded),
                          label: 'Acessos',
                        ),
                      ],
                    ),
                  ],
                );

          return Stack(
            children: <Widget>[
              workspace,
              Positioned(
                right: 22,
                bottom: wide ? 22 : 92,
                child: SafeArea(
                  child: FloatingActionButton.extended(
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
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}
