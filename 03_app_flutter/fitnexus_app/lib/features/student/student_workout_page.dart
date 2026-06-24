import 'package:flutter/material.dart';

import '../shared/fitnexus_ui.dart';

class StudentWorkoutPage extends StatefulWidget {
  const StudentWorkoutPage({super.key});

  @override
  State<StudentWorkoutPage> createState() => _StudentWorkoutPageState();
}

class _StudentWorkoutPageState extends State<StudentWorkoutPage> {
  final List<bool> _done = <bool>[true, false, false];

  int get completed => _done.where((bool item) => item).length;

  @override
  Widget build(BuildContext context) {
    final int percent = ((completed / _done.length) * 100).round();

    return FitShell(
      maxWidth: 760,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const SectionLabel('App do aluno'),
          const SizedBox(height: 12),
          const Text(
            'Treino A — Inferiores',
            style: TextStyle(
              color: FitColors.text,
              fontSize: 38,
              height: 1.08,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 12),
          const Text(
            'Mariana Alves recebe o treino no celular, executa e marca cada exercício concluído.',
            style: TextStyle(
              color: FitColors.muted,
              fontSize: 16,
              height: 1.45,
            ),
          ),
          const SizedBox(height: 26),
          FitCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Wrap(
                  spacing: 12,
                  runSpacing: 12,
                  children: <Widget>[
                    const _Metric(label: 'Treinos', value: '12'),
                    _Metric(label: 'Conclusão', value: '$percent%'),
                    const _Metric(label: 'Carga', value: '+8kg'),
                  ],
                ),
                const SizedBox(height: 20),
                _ExerciseItem(
                  done: _done[0],
                  title: 'Agachamento livre',
                  detail: '4 séries • 10 a 12 repetições • descanso 60s',
                  onChanged: (bool value) => setState(() => _done[0] = value),
                ),
                _ExerciseItem(
                  done: _done[1],
                  title: 'Leg press',
                  detail: '4 séries • 12 repetições • carga moderada',
                  onChanged: (bool value) => setState(() => _done[1] = value),
                ),
                _ExerciseItem(
                  done: _done[2],
                  title: 'Cadeira extensora',
                  detail: '3 séries • 12 a 15 repetições • controle total',
                  onChanged: (bool value) => setState(() => _done[2] = value),
                ),
                const SizedBox(height: 16),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(18),
                  decoration: BoxDecoration(
                    color: FitColors.gold.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(18),
                    border: Border.all(
                      color: FitColors.gold.withValues(alpha: 0.35),
                    ),
                  ),
                  child: const Row(
                    children: <Widget>[
                      Icon(Icons.timer, color: FitColors.goldSoft),
                      SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          'Cronômetro de descanso pronto para o próximo exercício.',
                          style: TextStyle(
                            color: FitColors.text,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                      ),
                    ],
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

class _Metric extends StatelessWidget {
  const _Metric({
    required this.label,
    required this.value,
  });

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 150,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: FitColors.cardSoft,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: FitColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(
            value,
            style: const TextStyle(
              color: FitColors.goldSoft,
              fontSize: 26,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            label,
            style: const TextStyle(color: FitColors.muted),
          ),
        ],
      ),
    );
  }
}

class _ExerciseItem extends StatelessWidget {
  const _ExerciseItem({
    required this.done,
    required this.title,
    required this.detail,
    required this.onChanged,
  });

  final bool done;
  final String title;
  final String detail;
  final ValueChanged<bool> onChanged;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        borderRadius: BorderRadius.circular(18),
        onTap: () => onChanged(!done),
        child: Container(
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(
            color: FitColors.cardSoft,
            borderRadius: BorderRadius.circular(18),
            border: Border.all(
              color: done
                  ? FitColors.gold.withValues(alpha: 0.8)
                  : FitColors.border,
            ),
          ),
          child: Row(
            children: <Widget>[
              Icon(
                done ? Icons.check_circle : Icons.circle_outlined,
                color: done ? FitColors.goldSoft : FitColors.muted,
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
        ),
      ),
    );
  }
}
