import 'package:flutter/material.dart';

import '../shared/fitnexus_ui.dart';

class DemoHomePage extends StatelessWidget {
  const DemoHomePage({super.key});

  @override
  Widget build(BuildContext context) {
    return FitShell(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const SectionLabel('MVP Core 01'),
          const SizedBox(height: 12),
          const Text(
            'Demonstração navegável do FitNexus.',
            style: TextStyle(
              color: FitColors.text,
              fontSize: 44,
              height: 1.05,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 14),
          const Text(
            'Veja o fluxo completo: o professor monta o treino, o aluno acessa pelo celular e o sistema acompanha a execução.',
            style: TextStyle(
              color: FitColors.muted,
              fontSize: 18,
              height: 1.5,
            ),
          ),
          const SizedBox(height: 28),
          Wrap(
            spacing: 14,
            runSpacing: 14,
            children: <Widget>[
              GoldButton(
                label: 'Abrir painel do professor',
                icon: Icons.dashboard_customize,
                onTap: () => Navigator.pushNamed(context, '/professor'),
              ),
              GhostButton(
                label: 'Ver tela do aluno',
                icon: Icons.phone_iphone,
                onTap: () => Navigator.pushNamed(context, '/student'),
              ),
              GhostButton(
                label: 'Tela de acesso',
                icon: Icons.lock_outline,
                onTap: () => Navigator.pushNamed(context, '/auth'),
              ),
            ],
          ),
          const SizedBox(height: 36),
          LayoutBuilder(
            builder: (BuildContext context, BoxConstraints constraints) {
              final bool narrow = constraints.maxWidth < 840;
              final List<FeatureTile> cards = <FeatureTile>[
                const FeatureTile(
                  icon: Icons.people_alt,
                  title: 'Professor',
                  text: 'Cadastra aluno, monta treino e acompanha execução.',
                ),
                const FeatureTile(
                  icon: Icons.qr_code_2,
                  title: 'Aluno',
                  text: 'Acessa o treino no celular e marca exercícios concluídos.',
                ),
                const FeatureTile(
                  icon: Icons.insights,
                  title: 'Evolução',
                  text: 'Base pronta para histórico, carga, conclusão e relatórios.',
                ),
              ];

              if (narrow) {
                return Column(
                  children: cards
                      .map(
                        (FeatureTile card) => Padding(
                          padding: const EdgeInsets.only(bottom: 14),
                          child: card,
                        ),
                      )
                      .toList(),
                );
              }

              return Row(
                children: cards
                    .map(
                      (FeatureTile card) => Expanded(
                        child: Padding(
                          padding: const EdgeInsets.only(right: 14),
                          child: card,
                        ),
                      ),
                    )
                    .toList(),
              );
            },
          ),
        ],
      ),
    );
  }
}
