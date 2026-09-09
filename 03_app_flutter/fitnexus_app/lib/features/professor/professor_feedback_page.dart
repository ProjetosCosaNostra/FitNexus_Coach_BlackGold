import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/blackgold_tokens.dart';
import '../shared/fitnexus_ui.dart';
import 'professor_feedback_repository.dart';

class ProfessorFeedbackPage extends StatefulWidget {
  const ProfessorFeedbackPage({super.key});

  @override
  State<ProfessorFeedbackPage> createState() => _ProfessorFeedbackPageState();
}

class _ProfessorFeedbackPageState extends State<ProfessorFeedbackPage> {
  final ProfessorFeedbackRepository _repository =
      ProfessorFeedbackRepository.instance;

  ProfessorFeedbackSnapshot? _snapshot;
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
      final ProfessorFeedbackSnapshot snapshot = await _repository.fetchFeed();
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
    final ProfessorFeedbackSnapshot? snapshot = _snapshot;

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
                      constraints: const BoxConstraints(maxWidth: 1260),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: <Widget>[
                          FitPageTitle(
                            eyebrow: 'Feedback pós-treino',
                            title: 'O que o aluno sentiu vira sinal de decisão',
                            description:
                                'Esforço, desconforto e energia alimentam o acompanhamento sem alterar prescrições automaticamente.',
                            trailing: OutlinedButton.icon(
                              onPressed: _loading ? null : _reload,
                              icon: _loading
                                  ? const SizedBox(
                                      width: 16,
                                      height: 16,
                                      child: CircularProgressIndicator(
                                        strokeWidth: 2,
                                        color: AppColors.goldSoft,
                                      ),
                                    )
                                  : const Icon(Icons.refresh_rounded, size: 18),
                              label: const Text('Atualizar'),
                            ),
                          ),
                          const SizedBox(height: BlackGoldSpace.xl),
                          if (_error != null && snapshot == null)
                            _Message(
                              icon: Icons.error_outline_rounded,
                              title: 'Não foi possível carregar os feedbacks',
                              text: _error!,
                              error: true,
                            )
                          else if (_loading && snapshot == null)
                            const _LoadingPanel()
                          else if (snapshot != null) ...<Widget>[
                            _Summary(snapshot: snapshot),
                            const SizedBox(height: BlackGoldSpace.xl),
                            if (snapshot.items.isEmpty)
                              const _Message(
                                icon: Icons.forum_outlined,
                                title: 'Nenhum feedback recebido ainda',
                                text:
                                    'Depois que um aluno concluir o treino e responder “Como foi o treino?”, os sinais aparecerão aqui.',
                              )
                            else
                              ...snapshot.items.map(
                                (ProfessorFeedbackRecord item) => Padding(
                                  padding: const EdgeInsets.only(
                                    bottom: BlackGoldSpace.sm,
                                  ),
                                  child: _FeedbackCard(item: item),
                                ),
                              ),
                            const SizedBox(height: BlackGoldSpace.sm),
                            Text(
                              'Atualizado em ${_formatDate(snapshot.generatedAt)}',
                              textAlign: TextAlign.right,
                              style: const TextStyle(
                                color: AppColors.mutedSoft,
                                fontSize: 10.5,
                              ),
                            ),
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

class _Summary extends StatelessWidget {
  const _Summary({required this.snapshot});

  final ProfessorFeedbackSnapshot snapshot;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (BuildContext context, BoxConstraints constraints) {
        final int columns = constraints.maxWidth >= 840
            ? 3
            : constraints.maxWidth >= 560
                ? 2
                : 1;
        const double gap = BlackGoldSpace.sm;
        final double width =
            (constraints.maxWidth - gap * (columns - 1)) / columns;

        final List<Widget> metrics = <Widget>[
          FitMetricCard(
            icon: Icons.forum_rounded,
            label: 'Feedbacks recebidos',
            value: '${snapshot.items.length}',
            detail: 'Sinais registrados pelos alunos',
          ),
          FitMetricCard(
            icon: Icons.warning_amber_rounded,
            label: 'Sinais altos',
            value: '${snapshot.highSignals}',
            detail: 'Pedem revisão humana',
          ),
          FitMetricCard(
            icon: Icons.healing_rounded,
            label: 'Dor ≥ 7',
            value: '${snapshot.painAlerts}',
            detail: 'Alertas de desconforto elevado',
          ),
        ];

        return Wrap(
          spacing: gap,
          runSpacing: gap,
          children: metrics
              .map((Widget metric) => SizedBox(width: width, child: metric))
              .toList(growable: false),
        );
      },
    );
  }
}

class _FeedbackCard extends StatelessWidget {
  const _FeedbackCard({required this.item});

  final ProfessorFeedbackRecord item;

  @override
  Widget build(BuildContext context) {
    final _SignalMeta signal = _signalMeta(item.riskSignal);

    return FitCard(
      highlight: item.riskSignal == 'high',
      padding: const EdgeInsets.all(BlackGoldSpace.lg),
      child: LayoutBuilder(
        builder: (BuildContext context, BoxConstraints constraints) {
          final bool compact = constraints.maxWidth < 760;
          final Widget identity = Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              CircleAvatar(
                radius: 22,
                backgroundColor: AppColors.gold.withValues(alpha: 0.10),
                foregroundColor: AppColors.goldSoft,
                child: Text(
                  _initials(item.studentName),
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
                    Row(
                      children: <Widget>[
                        Expanded(
                          child: Text(
                            item.studentName,
                            style: const TextStyle(
                              color: AppColors.text,
                              fontSize: 16,
                              fontWeight: FontWeight.w900,
                            ),
                          ),
                        ),
                        _SignalPill(meta: signal),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(
                      item.planName,
                      style: const TextStyle(
                        color: AppColors.muted,
                        fontSize: 11.5,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      _formatDate(item.submittedAt),
                      style: const TextStyle(
                        color: AppColors.mutedSoft,
                        fontSize: 10.5,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          );

          final Widget scores = Wrap(
            spacing: BlackGoldSpace.xs,
            runSpacing: BlackGoldSpace.xs,
            children: <Widget>[
              _ScoreTile(
                icon: Icons.speed_rounded,
                label: 'Esforço',
                value: '${item.perceivedExertion}/10',
                color: item.perceivedExertion >= 8
                    ? AppColors.warning
                    : AppColors.goldSoft,
              ),
              _ScoreTile(
                icon: Icons.healing_rounded,
                label: 'Dor',
                value: '${item.painScore}/10',
                color: item.painScore >= 7
                    ? AppColors.danger
                    : AppColors.goldSoft,
              ),
              _ScoreTile(
                icon: Icons.bolt_rounded,
                label: 'Energia',
                value: '${item.energyScore}/5',
                color: item.energyScore <= 2
                    ? AppColors.warning
                    : AppColors.success,
              ),
            ],
          );

          final Widget details = Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              if (item.painLocation != null &&
                  item.painLocation!.trim().isNotEmpty) ...<Widget>[
                _DetailLine(
                  icon: Icons.my_location_rounded,
                  label: 'Local da dor',
                  value: item.painLocation!,
                ),
                const SizedBox(height: BlackGoldSpace.xs),
              ],
              if (item.note != null && item.note!.trim().isNotEmpty)
                _DetailLine(
                  icon: Icons.chat_bubble_outline_rounded,
                  label: 'Observação',
                  value: item.note!,
                )
              else
                const _DetailLine(
                  icon: Icons.chat_bubble_outline_rounded,
                  label: 'Observação',
                  value: 'Aluno não deixou comentário adicional.',
                ),
            ],
          );

          if (compact) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: <Widget>[
                identity,
                const SizedBox(height: BlackGoldSpace.md),
                scores,
                const SizedBox(height: BlackGoldSpace.md),
                details,
              ],
            );
          }

          return Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Expanded(flex: 4, child: identity),
              const SizedBox(width: BlackGoldSpace.lg),
              Expanded(flex: 4, child: scores),
              const SizedBox(width: BlackGoldSpace.lg),
              Expanded(flex: 5, child: details),
            ],
          );
        },
      ),
    );
  }
}

class _ScoreTile extends StatelessWidget {
  const _ScoreTile({
    required this.icon,
    required this.label,
    required this.value,
    required this.color,
  });

  final IconData icon;
  final String label;
  final String value;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: const BoxConstraints(minWidth: 104, minHeight: 70),
      padding: const EdgeInsets.all(BlackGoldSpace.sm),
      decoration: BoxDecoration(
        color: AppColors.cardRaised,
        borderRadius: BorderRadius.circular(BlackGoldRadius.control),
        border: Border.all(
          color: color.withValues(alpha: 0.36),
          width: BlackGoldStroke.hairline,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            mainAxisSize: MainAxisSize.min,
            children: <Widget>[
              Icon(icon, color: color, size: 15),
              const SizedBox(width: 5),
              Text(
                label,
                style: const TextStyle(
                  color: AppColors.muted,
                  fontSize: 10.5,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            value,
            style: TextStyle(
              color: color,
              fontSize: 17,
              fontWeight: FontWeight.w900,
            ),
          ),
        ],
      ),
    );
  }
}

class _DetailLine extends StatelessWidget {
  const _DetailLine({
    required this.icon,
    required this.label,
    required this.value,
  });

  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Icon(icon, color: AppColors.goldSoft, size: 16),
        const SizedBox(width: BlackGoldSpace.xs),
        Expanded(
          child: Text.rich(
            TextSpan(
              children: <InlineSpan>[
                TextSpan(
                  text: '$label: ',
                  style: const TextStyle(
                    color: AppColors.goldSoft,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                TextSpan(text: value),
              ],
            ),
            style: const TextStyle(
              color: AppColors.muted,
              fontSize: 11.5,
              height: 1.4,
            ),
          ),
        ),
      ],
    );
  }
}

class _SignalPill extends StatelessWidget {
  const _SignalPill({required this.meta});

  final _SignalMeta meta;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      decoration: BoxDecoration(
        color: meta.color.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(BlackGoldRadius.pill),
        border: Border.all(
          color: meta.color.withValues(alpha: 0.42),
          width: BlackGoldStroke.hairline,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          Icon(meta.icon, color: meta.color, size: 13),
          const SizedBox(width: 4),
          Text(
            meta.label,
            style: TextStyle(
              color: meta.color,
              fontSize: 9.5,
              fontWeight: FontWeight.w900,
            ),
          ),
        ],
      ),
    );
  }
}

class _Message extends StatelessWidget {
  const _Message({
    required this.icon,
    required this.title,
    required this.text,
    this.error = false,
  });

  final IconData icon;
  final String title;
  final String text;
  final bool error;

  @override
  Widget build(BuildContext context) {
    final Color accent = error ? AppColors.danger : AppColors.goldSoft;
    return FitCard(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Icon(icon, color: accent, size: 24),
          const SizedBox(width: BlackGoldSpace.sm),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  title,
                  style: const TextStyle(
                    color: AppColors.text,
                    fontSize: 15,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const SizedBox(height: 5),
                Text(
                  text,
                  style: const TextStyle(
                    color: AppColors.muted,
                    fontSize: 12.5,
                    height: 1.42,
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

class _SignalMeta {
  const _SignalMeta(this.label, this.icon, this.color);

  final String label;
  final IconData icon;
  final Color color;
}

_SignalMeta _signalMeta(String signal) {
  switch (signal.toLowerCase()) {
    case 'high':
      return const _SignalMeta(
        'SINAL ALTO',
        Icons.priority_high_rounded,
        AppColors.danger,
      );
    case 'medium':
      return const _SignalMeta(
        'ATENÇÃO',
        Icons.warning_amber_rounded,
        AppColors.warning,
      );
    default:
      return const _SignalMeta(
        'ESTÁVEL',
        Icons.check_circle_outline_rounded,
        AppColors.success,
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
    final int end = parts.first.length >= 2 ? 2 : 1;
    return parts.first.substring(0, end).toUpperCase();
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
