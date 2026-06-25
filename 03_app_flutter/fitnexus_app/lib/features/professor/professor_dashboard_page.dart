import 'package:flutter/material.dart';

import '../shared/fitnexus_ui.dart';

class ProfessorDashboardPage extends StatelessWidget {
  const ProfessorDashboardPage({super.key});

  @override
  Widget build(BuildContext context) {
    return FitShell(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const SectionLabel('Painel do professor'),
          const SizedBox(height: 12),
          const Text(
            'Organize alunos e treinos em poucos minutos.',
            style: TextStyle(
              color: FitColors.text,
              fontSize: 38,
              height: 1.08,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 16),
          const Text(
            'Cadastre alunos, monte treinos e envie uma rotina organizada para o aluno.',
            style: TextStyle(
              color: FitColors.muted,
              fontSize: 16,
              height: 1.45,
            ),
          ),
          const SizedBox(height: 28),
          LayoutBuilder(
            builder: (BuildContext context, BoxConstraints constraints) {
              final bool narrow = constraints.maxWidth < 900;

              final FitCard left = FitCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    const Text(
                      'Alunos',
                      style: TextStyle(
                        color: FitColors.text,
                        fontSize: 24,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(height: 18),
                    _StudentRow(
                      name: 'Mariana Alves',
                      goal: 'Inferiores • 3x por semana',
                      progress: '86%',
                      onTap: () => Navigator.pushNamed(context, '/student'),
                    ),
                    const SizedBox(height: 12),
                    _StudentRow(
                      name: 'Carlos Lima',
                      goal: 'Hipertrofia • Peito e tríceps',
                      progress: '62%',
                      onTap: () => Navigator.pushNamed(context, '/student'),
                    ),
                    const SizedBox(height: 12),
                    _StudentRow(
                      name: 'Renata Costa',
                      goal: 'Condicionamento • Iniciante',
                      progress: '44%',
                      onTap: () => Navigator.pushNamed(context, '/student'),
                    ),
                  ],
                ),
              );

              final FitCard right = FitCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    const Text(
                      'Treino modelo',
                      style: TextStyle(
                        color: FitColors.text,
                        fontSize: 24,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(height: 18),
                    const _WorkoutBuilderItem(
                      number: '01',
                      title: 'Agachamento livre',
                      detail: '4 séries • 10 a 12 repetições • descanso 60s',
                    ),
                    const _WorkoutBuilderItem(
                      number: '02',
                      title: 'Leg press',
                      detail: '4 séries • 12 repetições • carga moderada',
                    ),
                    const _WorkoutBuilderItem(
                      number: '03',
                      title: 'Cadeira extensora',
                      detail: '3 séries • 12 a 15 repetições • controle total',
                    ),
                    const SizedBox(height: 18),
                    GoldButton(
                      label: 'Enviar para o aluno',
                      icon: Icons.send,
                      onTap: () => Navigator.pushNamed(context, '/student'),
                    ),
                  ],
                ),
              );

              if (narrow) {
                return Column(
                  children: <Widget>[
                    left,
                    const SizedBox(height: 18),
                    right,
                  ],
                );
              }

              return Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Expanded(child: left),
                  const SizedBox(width: 18),
                  Expanded(child: right),
                ],
              );
            },
          ),
        ],
      ),
    );
  }
}

class _StudentRow extends StatelessWidget {
  const _StudentRow({
    required this.name,
    required this.goal,
    required this.progress,
    required this.onTap,
  });

  final String name;
  final String goal;
  final String progress;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      borderRadius: BorderRadius.circular(18),
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: FitColors.cardSoft,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: FitColors.border),
        ),
        child: Row(
          children: <Widget>[
            const CircleAvatar(
              backgroundColor: FitColors.gold,
              foregroundColor: Colors.black,
              child: Icon(Icons.person),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text(
                    name,
                    style: const TextStyle(
                      color: FitColors.text,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    goal,
                    style: const TextStyle(color: FitColors.muted),
                  ),
                ],
              ),
            ),
            Text(
              progress,
              style: const TextStyle(
                color: FitColors.goldSoft,
                fontWeight: FontWeight.w900,
                fontSize: 18,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _WorkoutBuilderItem extends StatelessWidget {
  const _WorkoutBuilderItem({
    required this.number,
    required this.title,
    required this.detail,
  });

  final String number;
  final String title;
  final String detail;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          CircleAvatar(
            radius: 22,
            backgroundColor: FitColors.gold.withValues(alpha: 0.18),
            child: Text(
              number,
              style: const TextStyle(
                color: FitColors.goldSoft,
                fontWeight: FontWeight.w900,
              ),
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  title,
                  style: const TextStyle(
                    color: FitColors.text,
                    fontWeight: FontWeight.w900,
                    fontSize: 16,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  detail,
                  style: const TextStyle(
                    color: FitColors.muted,
                    height: 1.35,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
