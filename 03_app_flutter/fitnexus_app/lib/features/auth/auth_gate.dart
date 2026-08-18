import 'dart:async';

import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../shared/fitnexus_ui.dart';
import 'auth_preview_page.dart';
import 'auth_service.dart';

class AuthGate extends StatefulWidget {
  const AuthGate({
    super.key,
    required this.child,
  });

  final Widget child;

  @override
  State<AuthGate> createState() => _AuthGateState();
}

class _AuthGateState extends State<AuthGate> {
  StreamSubscription<AuthState>? _subscription;
  Session? _session;
  Future<String>? _tenantFuture;

  @override
  void initState() {
    super.initState();
    _applySession(AuthService.instance.currentSession, notify: false);
    _subscription = AuthService.instance.authStateChanges.listen((AuthState state) {
      if (!mounted) return;
      _applySession(state.session);
    });
  }

  void _applySession(Session? session, {bool notify = true}) {
    void update() {
      _session = session;
      _tenantFuture = session == null
          ? null
          : AuthService.instance.ensureProfessorOrganization();
    }

    if (notify) {
      setState(update);
    } else {
      update();
    }
  }

  Future<void> _recoverToLogin() async {
    await AuthService.instance.signOut();
    if (!mounted) return;
    Navigator.of(context).pushNamedAndRemoveUntil('/auth', (Route<dynamic> route) => false);
  }

  @override
  void dispose() {
    _subscription?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_session == null) {
      return const AuthPreviewPage();
    }

    final Future<String>? tenantFuture = _tenantFuture;
    if (tenantFuture == null) {
      return const AuthPreviewPage();
    }

    return FutureBuilder<String>(
      future: tenantFuture,
      builder: (BuildContext context, AsyncSnapshot<String> snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return const Scaffold(
            backgroundColor: Color(0xFF050505),
            body: Center(
              child: CircularProgressIndicator(color: FitColors.gold),
            ),
          );
        }

        if (snapshot.hasError) {
          return Scaffold(
            backgroundColor: const Color(0xFF050505),
            body: FitShell(
              maxWidth: 620,
              child: FitCard(
                padding: const EdgeInsets.all(30),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    const SectionLabel('Segurança'),
                    const SizedBox(height: 14),
                    const Text(
                      'Não foi possível preparar seu espaço.',
                      style: TextStyle(
                        color: FitColors.text,
                        fontSize: 28,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(height: 10),
                    Text(
                      '${snapshot.error}',
                      style: const TextStyle(color: FitColors.muted, height: 1.45),
                    ),
                    const SizedBox(height: 22),
                    GoldButton(
                      label: 'Voltar ao acesso',
                      icon: Icons.logout_rounded,
                      onTap: _recoverToLogin,
                    ),
                  ],
                ),
              ),
            ),
          );
        }

        return widget.child;
      },
    );
  }
}
