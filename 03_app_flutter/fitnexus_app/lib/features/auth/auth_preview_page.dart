import 'package:flutter/material.dart';

import '../shared/fitnexus_ui.dart';

class AuthPreviewPage extends StatelessWidget {
  const AuthPreviewPage({super.key});

  @override
  Widget build(BuildContext context) {
    return FitShell(
      maxWidth: 640,
      child: FitCard(
        padding: const EdgeInsets.all(30),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            const SectionLabel('Acesso'),
            const SizedBox(height: 12),
            const Text(
              'Entrada do sistema',
              style: TextStyle(
                color: FitColors.text,
                fontSize: 34,
                fontWeight: FontWeight.w900,
              ),
            ),
            const SizedBox(height: 10),
            const Text(
              'Entre no sistema para acessar o painel e gerenciar alunos, treinos e evolução.',
              style: TextStyle(
                color: FitColors.muted,
                height: 1.45,
              ),
            ),
            const SizedBox(height: 24),
            const _FakeInput(label: 'E-mail', value: 'professor@fitnexus.app'),
            const SizedBox(height: 12),
            const _FakeInput(label: 'Senha', value: '••••••••••'),
            const SizedBox(height: 22),
            GoldButton(
              label: 'Entrar no painel',
              icon: Icons.login,
              onTap: () => Navigator.pushNamed(context, '/professor'),
            ),
          ],
        ),
      ),
    );
  }
}

class _FakeInput extends StatelessWidget {
  const _FakeInput({
    required this.label,
    required this.value,
  });

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: FitColors.cardSoft,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: FitColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(label, style: const TextStyle(color: FitColors.muted)),
          const SizedBox(height: 8),
          Text(
            value,
            style: const TextStyle(
              color: FitColors.text,
              fontWeight: FontWeight.w800,
            ),
          ),
        ],
      ),
    );
  }
}
