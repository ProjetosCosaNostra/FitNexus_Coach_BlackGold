import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/blackgold_tokens.dart';
import '../shared/fitnexus_ui.dart';
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

    return Material(
      color: AppColors.black,
      child: SafeArea(
        bottom: false,
        child: RefreshIndicator(
          color: AppColors.gold,
          backgroundColor: AppColors.cardRaised,
          onRefresh: _reload,
          child: CustomScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            slivers: <Widget>[
              SliverPadding(
                padding: const EdgeInsets.fromLTRB(
                  BlackGoldSpace.lg,
                  BlackGoldSpace.lg,
                  BlackGoldSpace.lg,
                  120,
                ),
                sliver: SliverToBoxAdapter(
                  child: Center(
                    child: ConstrainedBox(
                      constraints: const BoxConstraints(maxWidth: 1360),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: <Widget>[
                          FitPageTitle(
                            eyebrow: 'Acompanhamento inteligente',
                            title: 'Progresso, risco e próxima ação',
                            description:
                                'O FitNexus transforma as execuções dos alunos em sinais claros para o professor agir.',
                            trailing: _RefreshButton(
                              loading: _loading,
                              onRefresh: _reload,
                            ),
                          ),
                          const SizedBox(height: BlackGoldSpace.xl),
                          if (_error != null && snapshot == null)
                            _ErrorPanel(message: _error!, onRetry: _reload)
                          else if (_loading && snapshot == null)
                            const _LoadingPanel()
                          else if (snapshot != null) ...<Widget>[
                            _SummaryGrid(summary: snapshot.summary),
                            const SizedBox(height: BlackGoldSpace.xl),
                            _RiskRadar(students: snapshot.students),
                            const SizedBox(height: BlackGoldSpace.xl),
                            _RecentSessions(sessions: snapshot.recentSessions),
                            const SizedBox(height: BlackGoldSpace.md),
                            _GeneratedAt(generatedAt: snapshot.generatedAt),
                          ],
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _RefreshButton extends StatelessWidget {
  const _RefreshButton({required this.loading, required this.onRefresh});

  final bool loading;
  final Future<void> Function() onRefresh;

  @override
  Widget build(BuildContext context) {
    return OutlinedButton.icon(
      onPressed: loading ? null : onRefresh,
      icon: loading
          ? const SizedBox(
              width: 16,
              height: 16,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                color: AppColors.goldSoft,
              ),
            )
          : const Icon(Icons.refresh_rounded, size: 18),
      label: Text(loading ? 'Atualizando' : 'Atualizar'),
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
        final int columns = constraints.maxWidth >= 1050
            ? 4
            : constraints.maxWidth >= 620
                ? 2
                : 1;
        const double gap = BlackGoldSpace.sm;
        final double width =
            (constraints.maxWidth - gap * (columns - 1)) / columns;

        final List<Widget> cards = <Widget>[
          FitMetricCard(
            icon: Icons.groups_rounded,
            label: 'Alunos ativos',
            value: '${summary.students}',
            detail: '${summary.activePlans} com treino ativo',
          ),
          FitMetricCard(
            icon: Icons.monitor_heart_rounded,
            label: 'Aderência média',
            value: '${summary.averageAdherence}%',
            detail: 'Baseada nas execuções registradas',
          ),
          FitMetricCard(
            icon: Icons.check_circle_outline_rounded,
            label: 'Conclusão — 7 dias',
            value: '${summary.completionRate7d}%',
            detail:
                '${summary.completed7d} concluídos de ${summary.sessions7d} iniciados',
          ),
          FitMetricCard(
            icon: Icons.radar_rounded,
            label: 'Radar de atenção',
            value: '${summary.highRisk + summary.mediumRisk}',
            detail:
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

class _RiskRadar extends StatelessWidget {
  const _RiskRadar({required this.students});

  final List<StudentProgressRecord> students;

  @override
  Widget build(BuildContext context) {
    return FitCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const _PanelHeading(
            icon: Icons.radar_rounded,
            title: 'Radar de atenção',
            subtitle:
                'Priorização explicável. O sistema organiza os sinais; a decisão continua sendo do professor.',
          ),
          const SizedBox(height: BlackGoldSpace.lg),
          if (students.isEmpty)
            const _EmptyState(
              icon: Icons.radar_rounded,
              title: 'Sem alunos para analisar',
              text:
                  'Cadastre alunos e as primeiras execuções aparecerão neste radar.',
            )
          else
            Column(
              children: students
                  .map(
                    (StudentProgressRecord student) => Padding(
                      padding: const EdgeInsets.only(
                        bottom: BlackGoldSpace.sm,
                      ),
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
    final _RiskMeta meta = _riskMeta(student.riskLevel);

    return Container(
      padding: const EdgeInsets.all(BlackGoldSpace.md),
      decoration: BoxDecoration(
        color: AppColors.cardRaised,
        borderRadius: BorderRadius.circular(BlackGoldRadius.card),
        border: Border.all(
          color: meta.color.withValues(alpha: 0.42),
          width: BlackGoldStroke.hairline,
        ),
      ),
      child: LayoutBuilder(
        builder: (BuildContext context, BoxConstraints constraints) {
          final Widget identity = Row(
            children: <Widget>[
              CircleAvatar(
                radius: 21,
                backgroundColor: AppColors.gold.withValues(alpha: 0.10),
                foregroundColor: AppColors.goldSoft,
                child: Text(
                  _initials(student.name),
                  style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w900,
                  ),
                ),
              ),
              const SizedBox(width: BlackGoldSpace.sm),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      student.name,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: AppColors.text,
                        fontSize: 15,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      '${student.objective} • ${student.level}',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: AppColors.muted,
                        fontSize: 11.5,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          );

          final Widget metrics = Wrap(
            spacing: BlackGoldSpace.xs,
            runSpacing: BlackGoldSpace.xs,
            children: <Widget>[
              _MetricChip('${student.adherence}% aderência'),
              _MetricChip('${student.sessions30d} sessões / 30d'),
              _MetricChip('${student.completionRate30d}% conclusão'),
            ],
          );

          final Widget action = Container(
            padding: const EdgeInsets.all(BlackGoldSpace.sm),
            decoration: BoxDecoration(
              color: meta.color.withValues(alpha: 0.07),
              borderRadius: BorderRadius.circular(BlackGoldRadius.control),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Row(
                  children: <Widget>[
                    Icon(meta.icon, size: 16, color: meta.color),
                    const SizedBox(width: 6),
                    Text(
                      meta.label,
                      style: TextStyle(
                        color: meta.color,
                        fontSize: 11,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 6),
                Text(
                  student.riskReason,
                  style: const TextStyle(
                    color: AppColors.text,
                    fontSize: 12,
                    height: 1.35,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  'Próxima ação: ${student.nextBestAction}',
                  style: const TextStyle(
                    color: AppColors.muted,
                    fontSize: 11.5,
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
                const SizedBox(height: BlackGoldSpace.sm),
                metrics,
                const SizedBox(height: BlackGoldSpace.sm),
                action,
              ],
            );
          }

          return Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: <Widget>[
              Expanded(flex: 3, child: identity),
              const SizedBox(width: BlackGoldSpace.md),
              Expanded(flex: 3, child: metrics),
              const SizedBox(width: BlackGoldSpace.md),
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
    return FitCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const _PanelHeading(
            icon: Icons.history_rounded,
            title: 'Execuções recentes',
            subtitle: 'O que realmente aconteceu nos treinos mais recentes.',
          ),
          const SizedBox(height: BlackGoldSpace.lg),
          if (sessions.isEmpty)
            const _EmptyState(
              icon: Icons.history_rounded,
              title: 'Nenhuma execução registrada',
              text:
                  'Quando um aluno iniciar um treino pelo link ou QR, ele aparecerá aqui.',
            )
          else
            Column(
              children: sessions
                  .map(
                    (RecentWorkoutSessionRecord session) => Padding(
                      padding: const EdgeInsets.only(
                        bottom: BlackGoldSpace.sm,
                      ),
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
    final Color stateColor = completed ? AppColors.success : AppColors.goldSoft;

    return Container(
      padding: const EdgeInsets.all(BlackGoldSpace.md),
      decoration: BoxDecoration(
        color: AppColors.cardRaised,
        borderRadius: BorderRadius.circular(BlackGoldRadius.card),
        border: Border.all(
          color: AppColors.borderGold.withValues(alpha: 0.56),
          width: BlackGoldStroke.hairline,
        ),
      ),
      child: LayoutBuilder(
        builder: (BuildContext context, BoxConstraints constraints) {
          final Widget description = Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(
                session.studentName,
                style: const TextStyle(
                  color: AppColors.text,
                  fontSize: 14,
                  fontWeight: FontWeight.w900,
                ),
              ),
              const SizedBox(height: 3),
              Text(
                session.planName,
                style: const TextStyle(
                  color: AppColors.muted,
                  fontSize: 11.5,
                ),
              ),
              const SizedBox(height: 5),
              Text(
                _formatDate(session.startedAt),
                style: const TextStyle(
                  color: AppColors.mutedSoft,
                  fontSize: 10.5,
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
                      borderRadius: BorderRadius.circular(
                        BlackGoldRadius.pill,
                      ),
                      child: LinearProgressIndicator(
                        value: session.completionPercent / 100,
                        minHeight: 7,
                        backgroundColor: AppColors.border,
                        valueColor: AlwaysStoppedAnimation<Color>(stateColor),
                      ),
                    ),
                  ),
                  const SizedBox(width: BlackGoldSpace.sm),
                  Text(
                    '${session.completionPercent}%',
                    style: TextStyle(
                      color: stateColor,
                      fontSize: 12,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 6),
              Text(
                '${session.completedExercises}/${session.totalExercises} exercícios',
                style: const TextStyle(
                  color: AppColors.muted,
                  fontSize: 11,
                ),
              ),
            ],
          );

          final Widget status = _StatusPill(
            text: completed ? 'Concluído' : 'Em andamento',
            color: stateColor,
          );

          if (constraints.maxWidth < 680) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: <Widget>[
                description,
                const SizedBox(height: BlackGoldSpace.sm),
                progress,
                const SizedBox(height: BlackGoldSpace.sm),
                Align(alignment: Alignment.centerLeft, child: status),
              ],
            );
          }

          return Row(
            children: <Widget>[
              Expanded(flex: 3, child: description),
              const SizedBox(width: BlackGoldSpace.lg),
              Expanded(flex: 4, child: progress),
              const SizedBox(width: BlackGoldSpace.lg),
              status,
            ],
          );
        },
      ),
    );
  }
}

class _PanelHeading extends StatelessWidget {
  const _PanelHeading({
    required this.icon,
    required this.title,
    required this.subtitle,
  });

  final IconData icon;
  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Container(
          width: 38,
          height: 38,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: AppColors.gold.withValues(alpha: 0.08),
            borderRadius: BorderRadius.circular(BlackGoldRadius.control),
            border: Border.all(
              color: AppColors.gold.withValues(alpha: 0.35),
              width: BlackGoldStroke.hairline,
            ),
          ),
          child: Icon(icon, color: AppColors.goldSoft, size: 19),
        ),
        const SizedBox(width: BlackGoldSpace.sm),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(
                title,
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: 4),
              Text(
                subtitle,
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _MetricChip extends StatelessWidget {
  const _MetricChip(this.text);

  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: const BoxConstraints(minHeight: 32),
      padding: const EdgeInsets.symmetric(
        horizontal: BlackGoldSpace.sm,
        vertical: 7,
      ),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(BlackGoldRadius.pill),
        border: Border.all(
          color: AppColors.borderGold.withValues(alpha: 0.55),
          width: BlackGoldStroke.hairline,
        ),
      ),
      child: Text(
        text,
        style: const TextStyle(
          color: AppColors.muted,
          fontSize: 10.5,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}

class _StatusPill extends StatelessWidget {
  const _StatusPill({required this.text, required this.color});

  final String text;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: const BoxConstraints(minHeight: 32),
      padding: const EdgeInsets.symmetric(
        horizontal: BlackGoldSpace.sm,
        vertical: 7,
      ),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(BlackGoldRadius.pill),
        border: Border.all(
          color: color.withValues(alpha: 0.42),
          width: BlackGoldStroke.hairline,
        ),
      ),
      child: Text(
        text,
        style: TextStyle(
          color: color,
          fontSize: 10.5,
          fontWeight: FontWeight.w900,
        ),
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
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(BlackGoldSpace.xl),
      decoration: BoxDecoration(
        color: AppColors.cardRaised,
        borderRadius: BorderRadius.circular(BlackGoldRadius.card),
        border: Border.all(
          color: AppColors.borderGold.withValues(alpha: 0.44),
          width: BlackGoldStroke.hairline,
        ),
      ),
      child: Column(
        children: <Widget>[
          Icon(icon, color: AppColors.goldSoft, size: 30),
          const SizedBox(height: BlackGoldSpace.sm),
          Text(
            title,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: BlackGoldSpace.xs),
          Text(
            text,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
      ),
    );
  }
}

class _LoadingPanel extends StatelessWidget {
  const _LoadingPanel();

  @override
  Widget build(BuildContext context) {
    return const FitCard(
      child: SizedBox(
        height: 260,
        child: Center(
          child: CircularProgressIndicator(color: AppColors.gold),
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
    return FitCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const Row(
            children: <Widget>[
              Icon(Icons.error_outline_rounded, color: AppColors.danger),
              SizedBox(width: BlackGoldSpace.sm),
              Text(
                'Não foi possível carregar o acompanhamento',
                style: TextStyle(
                  color: AppColors.text,
                  fontSize: 16,
                  fontWeight: FontWeight.w900,
                ),
              ),
            ],
          ),
          const SizedBox(height: BlackGoldSpace.sm),
          Text(
            message,
            style: Theme.of(context).textTheme.bodyMedium,
          ),
          const SizedBox(height: BlackGoldSpace.md),
          OutlinedButton.icon(
            onPressed: onRetry,
            icon: const Icon(Icons.refresh_rounded),
            label: const Text('Tentar novamente'),
          ),
        ],
      ),
    );
  }
}

class _GeneratedAt extends StatelessWidget {
  const _GeneratedAt({required this.generatedAt});

  final DateTime generatedAt;

  @override
  Widget build(BuildContext context) {
    return Text(
      'Atualizado em ${_formatDate(generatedAt)}',
      textAlign: TextAlign.right,
      style: const TextStyle(
        color: AppColors.mutedSoft,
        fontSize: 10.5,
      ),
    );
  }
}

class _RiskMeta {
  const _RiskMeta(this.label, this.icon, this.color);

  final String label;
  final IconData icon;
  final Color color;
}

_RiskMeta _riskMeta(String level) {
  switch (level.toLowerCase()) {
    case 'high':
      return const _RiskMeta(
        'ATENÇÃO ALTA',
        Icons.priority_high_rounded,
        AppColors.danger,
      );
    case 'medium':
      return const _RiskMeta(
        'ATENÇÃO',
        Icons.warning_amber_rounded,
        AppColors.warning,
      );
    case 'low':
      return const _RiskMeta(
        'EM EVOLUÇÃO',
        Icons.trending_up_rounded,
        AppColors.success,
      );
    default:
      return const _RiskMeta(
        'NOVO SINAL',
        Icons.auto_awesome_rounded,
        AppColors.goldSoft,
      );
  }
}

String _initials(String name) {
  final List<String> parts = name
      .trim()
      .split(RegExp(r'\s+'))
      .where((String part) => part.isNotEmpty)
      .toList(growable: false);
  if (parts.isEmpty) return 'AL';
  if (parts.length == 1) {
    return parts.first.substring(0, parts.first.length.clamp(1, 2)).toUpperCase();
  }
  return '${parts.first[0]}${parts.last[0]}'.toUpperCase();
}

String _formatDate(DateTime date) {
  final String day = date.day.toString().padLeft(2, '0');
  final String month = date.month.toString().padLeft(2, '0');
  final String hour = date.hour.toString().padLeft(2, '0');
  final String minute = date.minute.toString().padLeft(2, '0');
  return '$day/$month/${date.year} • $hour:$minute';
}
