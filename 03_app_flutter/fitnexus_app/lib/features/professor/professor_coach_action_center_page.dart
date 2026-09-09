import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/blackgold_tokens.dart';
import '../shared/fitnexus_ui.dart';
import 'professor_coach_action_repository.dart';
import 'professor_decision_intelligence_page.dart';
import 'professor_feedback_page.dart';
import 'professor_live_dashboard_page.dart';
import 'professor_progress_page.dart';
import 'student_access_management_page.dart';

class ProfessorCoachActionCenterPage extends StatefulWidget {
  const ProfessorCoachActionCenterPage({super.key});

  @override
  State<ProfessorCoachActionCenterPage> createState() =>
      _ProfessorCoachActionCenterPageState();
}

class _ProfessorCoachActionCenterPageState
    extends State<ProfessorCoachActionCenterPage> {
  final ProfessorCoachActionRepository _repository =
      ProfessorCoachActionRepository.instance;

  CoachActionSnapshot? _snapshot;
  bool _loading = true;
  String? _error;
  String? _busyFingerprint;

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
      final CoachActionSnapshot snapshot =
          await _repository.fetchActionCenter();
      if (!mounted) return;
      setState(() => _snapshot = snapshot);
    } catch (error) {
      if (!mounted) return;
      setState(() => _error = _friendlyError(error));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _complete(CoachActionItem action) async {
    if (_busyFingerprint != null) return;
    setState(() => _busyFingerprint = action.actionFingerprint);
    try {
      await _repository.completeForToday(action);
      if (!mounted) return;
      _toast('Ação concluída por hoje.');
      await _reload();
    } catch (error) {
      if (!mounted) return;
      _toast(_friendlyError(error), error: true);
    } finally {
      if (mounted) setState(() => _busyFingerprint = null);
    }
  }

  Future<void> _snooze(CoachActionItem action) async {
    if (_busyFingerprint != null) return;
    setState(() => _busyFingerprint = action.actionFingerprint);
    try {
      await _repository.snooze(action);
      if (!mounted) return;
      _toast('Ação lembrada novamente em 24 horas.');
      await _reload();
    } catch (error) {
      if (!mounted) return;
      _toast(_friendlyError(error), error: true);
    } finally {
      if (mounted) setState(() => _busyFingerprint = null);
    }
  }

  void _openContext(CoachActionItem action) {
    final Widget page = switch (action.target) {
      'feedback' => const ProfessorFeedbackPage(),
      'access' => const StudentAccessManagementPage(),
      'intelligence' => const ProfessorDecisionIntelligencePage(),
      'training' => const ProfessorLiveDashboardPage(),
      _ => const ProfessorProgressPage(),
    };
    Navigator.of(context).push(
      MaterialPageRoute<void>(builder: (_) => page),
    );
  }

  void _openOperationalPanel() {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => const ProfessorLiveDashboardPage(),
      ),
    );
  }

  String _friendlyError(Object error) {
    final String text = error.toString();
    if (text.contains('STALE_ACTION_CONTEXT')) {
      return 'Os sinais deste aluno mudaram. Atualizei a prioridade para evitar registrar uma ação antiga.';
    }
    if (text.contains('ORG_MANAGER_REQUIRED')) {
      return 'Somente owner/admin pode concluir ou adiar ações do Coach Action Center.';
    }
    return 'Não foi possível concluir a operação agora.';
  }

  void _toast(String message, {bool error = false}) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: error ? AppColors.danger : AppColors.cardRaised,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final CoachActionSnapshot? snapshot = _snapshot;

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
                            eyebrow: 'Coach Action Center',
                            title: 'O que precisa da sua atenção hoje',
                            description:
                                'O FitNexus cruza execução, aderência, feedback, acesso e decisões pendentes para priorizar a próxima ação sem tirar o professor do controle.',
                            trailing: Wrap(
                              spacing: BlackGoldSpace.xs,
                              runSpacing: BlackGoldSpace.xs,
                              children: <Widget>[
                                OutlinedButton.icon(
                                  onPressed:
                                      _loading ? null : _openOperationalPanel,
                                  icon: const Icon(
                                    Icons.dashboard_customize_rounded,
                                    size: 18,
                                  ),
                                  label: const Text('Painel'),
                                ),
                                OutlinedButton.icon(
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
                                      : const Icon(
                                          Icons.refresh_rounded,
                                          size: 18,
                                        ),
                                  label: const Text('Atualizar'),
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(height: BlackGoldSpace.xl),
                          if (_loading && snapshot == null)
                            const _LoadingPanel()
                          else if (_error != null && snapshot == null)
                            _Notice(
                              icon: Icons.error_outline_rounded,
                              title: 'Coach Action Center indisponível',
                              text: _error!,
                              error: true,
                            )
                          else if (snapshot != null) ...<Widget>[
                            _SummaryGrid(summary: snapshot.summary),
                            const SizedBox(height: BlackGoldSpace.lg),
                            _Principle(text: snapshot.principle),
                            if (_error != null) ...<Widget>[
                              const SizedBox(height: BlackGoldSpace.md),
                              _Notice(
                                icon: Icons.sync_problem_rounded,
                                title: 'Não foi possível atualizar agora',
                                text: _error!,
                                error: true,
                              ),
                            ],
                            const SizedBox(height: BlackGoldSpace.xl),
                            if (snapshot.actions.isEmpty)
                              const _Notice(
                                icon: Icons.task_alt_rounded,
                                title: 'Fila limpa por agora',
                                text:
                                    'Não há nenhuma próxima ação ativa. O FitNexus continua acompanhando os sinais e trará uma ação quando houver contexto suficiente.',
                              )
                            else ...<Widget>[
                              _QueueHeader(count: snapshot.actions.length),
                              const SizedBox(height: BlackGoldSpace.md),
                              ...snapshot.actions.map(
                                (CoachActionItem action) => Padding(
                                  padding: const EdgeInsets.only(
                                    bottom: BlackGoldSpace.sm,
                                  ),
                                  child: _ActionCard(
                                    action: action,
                                    busy: _busyFingerprint ==
                                        action.actionFingerprint,
                                    onOpen: () => _openContext(action),
                                    onComplete: () => _complete(action),
                                    onSnooze: () => _snooze(action),
                                  ),
                                ),
                              ),
                            ],
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

class _SummaryGrid extends StatelessWidget {
  const _SummaryGrid({required this.summary});

  final CoachActionSummary summary;

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
            icon: Icons.auto_awesome_rounded,
            label: 'Ações ativas',
            value: '${summary.activeActions}',
            detail: '${summary.attention} pedem atenção',
          ),
          FitMetricCard(
            icon: Icons.priority_high_rounded,
            label: 'Urgentes',
            value: '${summary.urgent}',
            detail: 'Prioridade máxima hoje',
          ),
          FitMetricCard(
            icon: Icons.task_alt_rounded,
            label: 'Concluídas hoje',
            value: '${summary.completedToday}',
            detail: 'Ações registradas pelo professor',
            positive: true,
          ),
          FitMetricCard(
            icon: Icons.schedule_rounded,
            label: 'Adiados',
            value: '${summary.snoozed}',
            detail: '${summary.monitor} em monitoramento',
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

class _Principle extends StatelessWidget {
  const _Principle({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return FitCard(
      highlight: true,
      padding: const EdgeInsets.all(BlackGoldSpace.md),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Container(
            width: 38,
            height: 38,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: AppColors.gold.withValues(alpha: 0.09),
              borderRadius: BorderRadius.circular(BlackGoldRadius.control),
            ),
            child: const Icon(
              Icons.psychology_alt_rounded,
              color: AppColors.goldSoft,
              size: 20,
            ),
          ),
          const SizedBox(width: BlackGoldSpace.sm),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                const Text(
                  'PRINCÍPIO DE DECISÃO',
                  style: TextStyle(
                    color: AppColors.goldSoft,
                    fontSize: 10.5,
                    fontWeight: FontWeight.w900,
                    letterSpacing: 1.05,
                  ),
                ),
                const SizedBox(height: 5),
                Text(
                  text,
                  style: const TextStyle(
                    color: AppColors.text,
                    fontSize: 13,
                    height: 1.4,
                    fontWeight: FontWeight.w700,
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

class _QueueHeader extends StatelessWidget {
  const _QueueHeader({required this.count});

  final int count;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: <Widget>[
        const Icon(
          Icons.view_agenda_outlined,
          color: AppColors.goldSoft,
          size: 20,
        ),
        const SizedBox(width: BlackGoldSpace.xs),
        Expanded(
          child: Text(
            '$count próximas ações priorizadas',
            style: Theme.of(context).textTheme.titleLarge,
          ),
        ),
      ],
    );
  }
}

class _ActionCard extends StatelessWidget {
  const _ActionCard({
    required this.action,
    required this.busy,
    required this.onOpen,
    required this.onComplete,
    required this.onSnooze,
  });

  final CoachActionItem action;
  final bool busy;
  final VoidCallback onOpen;
  final VoidCallback onComplete;
  final VoidCallback onSnooze;

  @override
  Widget build(BuildContext context) {
    final _PriorityMeta priority = _priorityMeta(action.priorityLabel);
    final List<String> evidence = _evidenceLabels(action);

    return FitCard(
      highlight: action.urgent,
      padding: const EdgeInsets.all(BlackGoldSpace.lg),
      child: LayoutBuilder(
        builder: (BuildContext context, BoxConstraints constraints) {
          final bool compact = constraints.maxWidth < 760;
          final Widget identity = Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  CircleAvatar(
                    radius: 22,
                    backgroundColor: AppColors.gold.withValues(alpha: 0.10),
                    foregroundColor: AppColors.goldSoft,
                    child: Text(
                      _initials(action.studentName),
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
                                action.studentName,
                                style: const TextStyle(
                                  color: AppColors.text,
                                  fontSize: 16,
                                  fontWeight: FontWeight.w900,
                                ),
                              ),
                            ),
                            _PriorityPill(meta: priority),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Text(
                          '${action.objective} • ${action.level} • ${action.adherence}% aderência',
                          style: const TextStyle(
                            color: AppColors.muted,
                            fontSize: 11.5,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: BlackGoldSpace.md),
              Text(
                action.actionTitle,
                style: const TextStyle(
                  color: AppColors.text,
                  fontSize: 17,
                  height: 1.2,
                  fontWeight: FontWeight.w900,
                ),
              ),
              const SizedBox(height: BlackGoldSpace.xs),
              Text(
                action.actionReason,
                style: const TextStyle(
                  color: AppColors.muted,
                  fontSize: 12.5,
                  height: 1.45,
                ),
              ),
              if (evidence.isNotEmpty) ...<Widget>[
                const SizedBox(height: BlackGoldSpace.md),
                Wrap(
                  spacing: BlackGoldSpace.xs,
                  runSpacing: BlackGoldSpace.xs,
                  children: evidence
                      .map((String item) => _EvidenceChip(text: item))
                      .toList(growable: false),
                ),
              ],
              if (action.humanActionRequired) ...<Widget>[
                const SizedBox(height: BlackGoldSpace.md),
                const Row(
                  children: <Widget>[
                    Icon(
                      Icons.person_pin_circle_outlined,
                      color: AppColors.goldSoft,
                      size: 16,
                    ),
                    SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        'Decisão humana obrigatória — o FitNexus não executa esta ação sozinho.',
                        style: TextStyle(
                          color: AppColors.goldSoft,
                          fontSize: 10.5,
                          height: 1.3,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ],
          );

          final Widget actions = Wrap(
            spacing: BlackGoldSpace.xs,
            runSpacing: BlackGoldSpace.xs,
            alignment: compact ? WrapAlignment.start : WrapAlignment.end,
            children: <Widget>[
              OutlinedButton.icon(
                onPressed: busy ? null : onOpen,
                icon: const Icon(Icons.open_in_new_rounded, size: 17),
                label: const Text('Ver contexto'),
              ),
              OutlinedButton.icon(
                onPressed: busy ? null : onSnooze,
                icon: const Icon(Icons.schedule_rounded, size: 17),
                label: const Text('Lembrar em 24h'),
              ),
              GoldButton(
                label: busy ? 'Processando' : 'Concluir hoje',
                icon: busy
                    ? Icons.hourglass_top_rounded
                    : Icons.check_rounded,
                onTap: busy ? null : onComplete,
              ),
            ],
          );

          if (compact) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: <Widget>[
                identity,
                const SizedBox(height: BlackGoldSpace.lg),
                actions,
              ],
            );
          }

          return Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: <Widget>[
              Expanded(child: identity),
              const SizedBox(width: BlackGoldSpace.lg),
              ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 430),
                child: actions,
              ),
            ],
          );
        },
      ),
    );
  }
}

class _PriorityPill extends StatelessWidget {
  const _PriorityPill({required this.meta});

  final _PriorityMeta meta;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      decoration: BoxDecoration(
        color: meta.color.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(BlackGoldRadius.pill),
        border: Border.all(
          color: meta.color.withValues(alpha: 0.45),
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
              letterSpacing: 0.3,
            ),
          ),
        ],
      ),
    );
  }
}

class _EvidenceChip extends StatelessWidget {
  const _EvidenceChip({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: const BoxConstraints(minHeight: 30),
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: AppColors.cardRaised,
        borderRadius: BorderRadius.circular(BlackGoldRadius.pill),
        border: Border.all(
          color: AppColors.borderGold.withValues(alpha: 0.56),
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

class _Notice extends StatelessWidget {
  const _Notice({
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
          Icon(icon, color: accent, size: 23),
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
        height: 280,
        child: Center(
          child: CircularProgressIndicator(color: AppColors.gold),
        ),
      ),
    );
  }
}

class _PriorityMeta {
  const _PriorityMeta(this.label, this.icon, this.color);

  final String label;
  final IconData icon;
  final Color color;
}

_PriorityMeta _priorityMeta(String priority) {
  switch (priority.toLowerCase()) {
    case 'urgent':
      return const _PriorityMeta(
        'URGENTE',
        Icons.priority_high_rounded,
        AppColors.danger,
      );
    case 'attention':
      return const _PriorityMeta(
        'ATENÇÃO',
        Icons.warning_amber_rounded,
        AppColors.warning,
      );
    case 'setup':
      return const _PriorityMeta(
        'CONFIGURAR',
        Icons.tune_rounded,
        AppColors.goldSoft,
      );
    default:
      return const _PriorityMeta(
        'MONITORAR',
        Icons.visibility_outlined,
        AppColors.success,
      );
  }
}

List<String> _evidenceLabels(CoachActionItem action) {
  final List<String> labels = <String>[
    '${action.sessions30d} sessões / 30d',
    '${action.completed30d} concluídas',
  ];
  final CoachActionEvidence evidence = action.evidence;
  if (evidence.perceivedExertion != null) {
    labels.add('Esforço ${evidence.perceivedExertion}/10');
  }
  if (evidence.energyScore != null) {
    labels.add('Energia ${evidence.energyScore}/5');
  }
  if (evidence.painScore != null && evidence.painScore! > 0) {
    labels.add('Dor ${evidence.painScore}/10');
  }
  if (evidence.activePlanName != null &&
      evidence.activePlanName!.trim().isNotEmpty) {
    labels.add(evidence.activePlanName!);
  }
  if (evidence.hasActiveAccess == false) {
    labels.add('Acesso inativo');
  }
  return labels;
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
