import 'package:flutter/material.dart';

import 'professor_progress_repository.dart';

class ProfessorProgressPage extends StatefulWidget {
  const ProfessorProgressPage({super.key});

  @override
  State<ProfessorProgressPage> createState() => _ProfessorProgressPageState();
}

class _ProfessorProgressPageState extends State<ProfessorProgressPage> {
  final ProfessorProgressRepository _repository =
      ProfessorProgressRepository.instance;

  ProfessorProgressSnapshot? _snapshot;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _reload();
  }

  Future<void> _reload() async {
    if (mounted) {
      setState(() {
        _loading = true;
        _error = null;
      });
    }

    try {
      final ProfessorProgressSnapshot snapshot =
          await _repository.fetchDashboard();
      if (!mounted) return;
      setState(() => _snapshot = snapshot);
    } catch (error) {
      if (!mounted) return;
      setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final ProfessorProgressSnapshot? snapshot = _snapshot;

    return Scaffold(
      backgroundColor: _ProgressColors.black,
      body: SafeArea(
        child: RefreshIndicator(
          color: _ProgressColors.gold,
          onRefresh: _reload,
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.fromLTRB(20, 22, 20, 120),
            child: Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 1420),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: <Widget>[
                    _Header(loading: _loading, onRefresh: _reload),
                    const SizedBox(height: 22),
                    if (_error != null)
                      _ErrorPanel(message: _error!, onRetry: _reload)
                    else if (_loading && snapshot == null)
                      const _LoadingPanel()
                    else if (snapshot != null) ...<Widget>[
                      _SummaryGrid(summary: snapshot.summary),
                      const SizedBox(height: 22),
                      _RiskRadar(students: snapshot.students),
                      const SizedBox(height: 22),
                      _RecentSessions(sessions: snapshot.recentSessions),
                    ],
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.loading, required this.onRefresh});

  final bool loading;
  final Future<void> Function() onRefresh;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 16,
      runSpacing: 14,
      alignment: WrapAlignment.spaceBetween,
      crossAxisAlignment: WrapCrossAlignment.center,
      children: <Widget>[
        const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(
              'ACOMPANHAMENTO INTELIGENTE',
              style: TextStyle(
                color: _ProgressColors.goldSoft,
                fontWeight: FontWeight.w900,
                fontSize: 12,
                letterSpacing: 1.1,
              ),
            ),
            SizedBox(height: 8),
            Text(
              'Progresso, risco e próxima ação',
              style: TextStyle(
                color: _ProgressColors.text,
                fontSize: 30,
                height: 1.08,
                fontWeight: FontWeight.w900,
              ),
            ),
            SizedBox(height: 7),
            Text(
              'O FitNexus transforma as execuções dos alunos em sinais claros para o professor agir.',
              style: TextStyle(
                color: _ProgressColors.muted,
                height: 1.4,
              ),
            ),
          ],
        ),
        IconButton.filledTonal(
          tooltip: 'Atualizar acompanhamento',
          onPressed: loading ? null : onRefresh,
          icon: loading
              ? const SizedBox(
                  width: 18,
                  height: 18,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Icon(Icons.refresh_rounded),
        ),
      ],
    );
  }
}

class _SummaryGrid extends StatelessWidget {
  const _SummaryGrid({required this.summary});

  final ProfessorProgressSummary summary;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (BuildContext context, BoxConstraints constraints) {
        final int columns = constraints.maxWidth >= 1080
            ? 4
            : constraints.maxWidth >= 620
                ? 2
                : 1;
        const double gap = 12;
        final double width =
            (constraints.maxWidth - (gap * (columns - 1))) / columns;

        final List<Widget> cards = <Widget>[
          _SummaryCard(
            icon: Icons.groups_rounded,
            label: 'Alunos',
            value: '${summary.students}',
            caption: '${summary.activePlans} com treino ativo',
          ),
          _SummaryCard(
            icon: Icons.monitor_heart_rounded,
            label: 'Aderência média',
            value: '${summary.averageAdherence}%',
            caption: 'Baseada nas execuções registradas',
          ),
          _SummaryCard(
            icon: Icons.check_circle_rounded,
            label: 'Conclusão — 7 dias',
            value: '${summary.completionRate7d}%',
            caption:
                '${summary.completed7d} concluídos de ${summary.sessions7d} iniciados',
          ),
          _SummaryCard(
            icon: Icons.radar_rounded,
            label: 'Radar',
            value: '${summary.highRisk + summary.mediumRisk}',
            caption:
                '${summary.highRisk} alto • ${summary.mediumRisk} médio • ${summary.newStudents} novos',
          ),
        ];

        return Wrap(
          spacing: gap,
          runSpacing: gap,
          children: cards
              .map((Widget card) => SizedBox(width: width, child: card))
              .toList(growable: false),
        );
      },
    );
  }
}

class _SummaryCard extends StatelessWidget {
  const _SummaryCard({
    required this.icon,
    required this.label,
    required this.value,
    required this.caption,
  });

  final IconData icon;
  final String label;
  final String value;
  final String caption;

  @override
  Widget build(BuildContext context) {
    return _Panel(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Container(
            width: 46,
            height: 46,
            decoration: BoxDecoration(
              color: _ProgressColors.gold.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(14),
            ),
            child: Icon(icon, color: _ProgressColors.goldSoft),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  value,
                  style: const TextStyle(
                    color: _ProgressColors.text,
                    fontSize: 27,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  label,
                  style: const TextStyle(
                    color: _ProgressColors.goldSoft,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  caption,
                  style: const TextStyle(
                    color: _ProgressColors.muted,
                    fontSize: 12,
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

class _RiskRadar extends StatelessWidget {
  const _RiskRadar({required this.students});

  final List<StudentProgressRecord> students;

  @override
  Widget build(BuildContext context) {
    return _Panel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const _PanelTitle(
            title: 'Risk Radar',
            subtitle:
                'Priorização determinística e explicável — o professor continua decidindo.',
          ),
          const SizedBox(height: 18),
          if (students.isEmpty)
            const _EmptyState(
              icon: Icons.radar_rounded,
              title: 'Sem alunos para analisar',
              text: 'Cadastre alunos e as primeiras execuções aparecerão aqui.',
            )
          else
            Column(
              children: students
                  .map(
                    (StudentProgressRecord student) => Padding(
                      padding: const EdgeInsets.only(bottom: 10),
                      child: _RiskRow(student: student),
                    ),
                  )
                  .toList(growable: false),
            ),
        ],
      ),
    );
  }
}

class _RiskRow extends StatelessWidget {
  const _RiskRow({required this.student});

  final StudentProgressRecord student;

  @override
  Widget build(BuildContext context) {
    final _RiskVisual visual = _riskVisual(student.riskLevel);

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: _ProgressColors.cardSoft,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: visual.color.withValues(alpha: 0.45)),
      ),
      child: LayoutBuilder(
        builder: (BuildContext context, BoxConstraints constraints) {
          final Widget identity = Row(
            children: <Widget>[
              CircleAvatar(
                backgroundColor: visual.color.withValues(alpha: 0.16),
                foregroundColor: visual.color,
                child: Text(
                  _initials(student.name),
                  style: const TextStyle(fontWeight: FontWeight.w900),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      student.name,
                      style: const TextStyle(
                        color: _ProgressColors.text,
                        fontWeight: FontWeight.w900,
                        fontSize: 16,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      '${student.objective} • ${student.level}',
                      style: const TextStyle(
                        color: _ProgressColors.muted,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          );

          final Widget metrics = Wrap(
            spacing: 8,
            runSpacing: 8,
            children: <Widget>[
              _Chip(label: '${student.adherence}% aderência'),
              _Chip(label: '${student.sessions30d} sessões / 30d'),
              _Chip(label: '${student.completionRate30d}% conclusão'),
            ],
          );

          final Widget action = Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: visual.color.withValues(alpha: 0.08),
              borderRadius: BorderRadius.circular(14),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Row(
                  children: <Widget>[
                    Icon(visual.icon, size: 17, color: visual.color),
                    const SizedBox(width: 7),
                    Text(
                      visual.label,
                      style: TextStyle(
                        color: visual.color,
                        fontWeight: FontWeight.w900,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 6),
                Text(
                  student.riskReason,
                  style: const TextStyle(
                    color: _ProgressColors.text,
                    fontWeight: FontWeight.w700,
                    fontSize: 12,
                  ),
                ),
                const SizedBox(height: 5),
                Text(
                  'Próxima ação: ${student.nextBestAction}',
                  style: const TextStyle(
                    color: _ProgressColors.muted,
                    fontSize: 12,
                    height: 1.35,
                  ),
                ),
              ],
            ),
          );

          if (constraints.maxWidth < 760) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: <Widget>[
                identity,
                const SizedBox(height: 12),
                metrics,
                const SizedBox(height: 12),
                action,
              ],
            );
          }

          return Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: <Widget>[
              Expanded(flex: 3, child: identity),
              const SizedBox(width: 16),
              Expanded(flex: 3, child: metrics),
              const SizedBox(width: 16),
              Expanded(flex: 4, child: action),
            ],
          );
        },
      ),
    );
  }
}

class _RecentSessions extends StatelessWidget {
  const _RecentSessions({required this.sessions});

  final List<RecentWorkoutSessionRecord> sessions;

  @override
  Widget build(BuildContext context) {
    return _Panel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const _PanelTitle(
            title: 'Execuções recentes',
            subtitle: 'O que realmente aconteceu nos treinos mais recentes.',
          ),
          const SizedBox(height: 18),
          if (sessions.isEmpty)
            const _EmptyState(
              icon: Icons.history_rounded,
              title: 'Nenhuma execução registrada',
              text: 'Quando um aluno iniciar um treino pelo link/QR, ele aparecerá aqui.',
            )
          else
            Column(
              children: sessions
                  .map(
                    (RecentWorkoutSessionRecord session) => Padding(
                      padding: const EdgeInsets.only(bottom: 10),
                      child: _SessionRow(session: session),
                    ),
                  )
                  .toList(growable: false),
            ),
        ],
      ),
    );
  }
}

class _SessionRow extends StatelessWidget {
  const _SessionRow({required this.session});

  final RecentWorkoutSessionRecord session;

  @override
  Widget build(BuildContext context) {
    final bool completed = session.status == 'completed';
    final Color stateColor =
        completed ? const Color(0xFF6FE39A) : _ProgressColors.goldSoft;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: _ProgressColors.cardSoft,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: _ProgressColors.border),
      ),
      child: LayoutBuilder(
        builder: (BuildContext context, BoxConstraints constraints) {
          final Widget description = Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(
                session.studentName,
                style: const TextStyle(
                  color: _ProgressColors.text,
                  fontWeight: FontWeight.w900,
                  fontSize: 15,
                ),
              ),
              const SizedBox(height: 3),
              Text(
                session.planName,
                style: const TextStyle(
                  color: _ProgressColors.muted,
                  fontSize: 12,
                ),
              ),
              const SizedBox(height: 5),
              Text(
                _formatDate(session.startedAt),
                style: const TextStyle(
                  color: _ProgressColors.muted,
                  fontSize: 11,
                ),
              ),
            ],
          );

          final Widget progress = Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Row(
                children: <Widget>[
                  Expanded(
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(999),
                      child: LinearProgressIndicator(
                        value: session.completionPercent / 100,
                        minHeight: 8,
                        backgroundColor: _ProgressColors.border,
                        valueColor: AlwaysStoppedAnimation<Color>(stateColor),
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Text(
                    '${session.completionPercent}%',
                    style: TextStyle(
                      color: stateColor,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 6),
              Text(
                '${session.completedExercises}/${session.totalExercises} exercícios • ${completed ? 'Concluído' : 'Em andamento'}',
                style: const TextStyle(
                  color: _ProgressColors.muted,
                  fontSize: 11,
                ),
              ),
            ],
          );

          if (constraints.maxWidth < 620) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: <Widget>[
                description,
                const SizedBox(height: 12),
                progress,
              ],
            );
          }

          return Row(
            children: <Widget>[
              Expanded(flex: 4, child: description),
              const SizedBox(width: 18),
              Expanded(flex: 6, child: progress),
            ],
          );
        },
      ),
    );
  }
}

class _Chip extends StatelessWidget {
  const _Chip({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
      decoration: BoxDecoration(
        color: _ProgressColors.black,
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: _ProgressColors.border),
      ),
      child: Text(
        label,
        style: const TextStyle(
          color: _ProgressColors.muted,
          fontSize: 11,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}

class _Panel extends StatelessWidget {
  const _Panel({required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: _ProgressColors.card,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: _ProgressColors.border),
      ),
      child: child,
    );
  }
}

class _PanelTitle extends StatelessWidget {
  const _PanelTitle({required this.title, required this.subtitle});

  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Text(
          title,
          style: const TextStyle(
            color: _ProgressColors.text,
            fontSize: 21,
            fontWeight: FontWeight.w900,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          subtitle,
          style: const TextStyle(
            color: _ProgressColors.muted,
            fontSize: 12,
            height: 1.35,
          ),
        ),
      ],
    );
  }
}

class _LoadingPanel extends StatelessWidget {
  const _LoadingPanel();

  @override
  Widget build(BuildContext context) {
    return const _Panel(
      child: Padding(
        padding: EdgeInsets.all(38),
        child: Center(
          child: CircularProgressIndicator(color: _ProgressColors.gold),
        ),
      ),
    );
  }
}

class _ErrorPanel extends StatelessWidget {
  const _ErrorPanel({required this.message, required this.onRetry});

  final String message;
  final Future<void> Function() onRetry;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFF351313),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: Colors.redAccent.withValues(alpha: 0.5)),
      ),
      child: Row(
        children: <Widget>[
          const Icon(Icons.error_outline_rounded, color: Colors.redAccent),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              message,
              style: const TextStyle(color: _ProgressColors.text),
            ),
          ),
          TextButton(onPressed: onRetry, child: const Text('Tentar novamente')),
        ],
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({
    required this.icon,
    required this.title,
    required this.text,
  });

  final IconData icon;
  final String title;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 30),
        child: Column(
          children: <Widget>[
            Icon(icon, color: _ProgressColors.goldSoft, size: 42),
            const SizedBox(height: 12),
            Text(
              title,
              textAlign: TextAlign.center,
              style: const TextStyle(
                color: _ProgressColors.text,
                fontSize: 18,
                fontWeight: FontWeight.w900,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              text,
              textAlign: TextAlign.center,
              style: const TextStyle(
                color: _ProgressColors.muted,
                height: 1.4,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _RiskVisual {
  const _RiskVisual(this.label, this.color, this.icon);

  final String label;
  final Color color;
  final IconData icon;
}

_RiskVisual _riskVisual(String level) {
  switch (level) {
    case 'high':
      return const _RiskVisual(
        'RISCO ALTO',
        Color(0xFFFF6B6B),
        Icons.priority_high_rounded,
      );
    case 'medium':
      return const _RiskVisual(
        'ATENÇÃO',
        Color(0xFFFFC857),
        Icons.warning_amber_rounded,
      );
    case 'low':
      return const _RiskVisual(
        'SAUDÁVEL',
        Color(0xFF6FE39A),
        Icons.check_circle_outline_rounded,
      );
    default:
      return const _RiskVisual(
        'NOVO',
        Color(0xFF8DB7FF),
        Icons.auto_awesome_rounded,
      );
  }
}

String _initials(String name) {
  return name
      .split(RegExp(r'\s+'))
      .where((String part) => part.isNotEmpty)
      .take(2)
      .map((String part) => part[0].toUpperCase())
      .join();
}

String _formatDate(DateTime date) {
  final DateTime local = date.toLocal();
  String two(int value) => value.toString().padLeft(2, '0');
  return '${two(local.day)}/${two(local.month)} • ${two(local.hour)}:${two(local.minute)}';
}

class _ProgressColors {
  static const Color black = Color(0xFF050505);
  static const Color card = Color(0xFF101010);
  static const Color cardSoft = Color(0xFF171717);
  static const Color border = Color(0xFF2C2A22);
  static const Color gold = Color(0xFFE1B92F);
  static const Color goldSoft = Color(0xFFFFD45A);
  static const Color text = Color(0xFFF7F7F7);
  static const Color muted = Color(0xFFB7B7B7);
}
