import 'package:flutter/material.dart';

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
        behavior: SnackBarBehavior.floating,
        backgroundColor:
            error ? const Color(0xFF5A1919) : const Color(0xFF171717),
        content: Text(message),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final CoachActionSnapshot? snapshot = _snapshot;
    return Scaffold(
      backgroundColor: const Color(0xFF050505),
      body: SafeArea(
        child: RefreshIndicator(
          color: const Color(0xFFE1B92F),
          onRefresh: _reload,
          child: ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.fromLTRB(20, 22, 20, 120),
            children: <Widget>[
              _Header(
                loading: _loading,
                onRefresh: _reload,
                onOpenPanel: _openOperationalPanel,
              ),
              const SizedBox(height: 20),
              if (_loading && snapshot == null)
                const SizedBox(
                  height: 280,
                  child: Center(
                    child: CircularProgressIndicator(
                      color: Color(0xFFE1B92F),
                    ),
                  ),
                )
              else if (_error != null && snapshot == null)
                _Notice(
                  icon: Icons.error_outline_rounded,
                  title: 'Coach Action Center indisponível',
                  text: _error!,
                  error: true,
                )
              else if (snapshot != null) ...<Widget>[
                _SummaryGrid(summary: snapshot.summary),
                const SizedBox(height: 18),
                _Principle(text: snapshot.principle),
                const SizedBox(height: 18),
                if (_error != null) ...<Widget>[
                  _Notice(
                    icon: Icons.sync_problem_rounded,
                    title: 'Não foi possível atualizar agora',
                    text: _error!,
                    error: true,
                  ),
                  const SizedBox(height: 14),
                ],
                if (snapshot.actions.isEmpty)
                  const _Notice(
                    icon: Icons.task_alt_rounded,
                    title: 'Fila limpa por agora',
                    text:
                        'Não há nenhuma próxima ação ativa. Itens concluídos reaparecem somente se o sinal persistir depois da janela de 24 horas ou se o contexto mudar.',
                  )
                else ...<Widget>[
                  Text(
                    '${snapshot.actions.length} próximas ações priorizadas',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 18,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                  const SizedBox(height: 12),
                  ...snapshot.actions.map(
                    (CoachActionItem action) => Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: _ActionCard(
                        action: action,
                        busy: _busyFingerprint == action.actionFingerprint,
                        onOpen: () => _openContext(action),
                        onComplete: () => _complete(action),
                        onSnooze: () => _snooze(action),
                      ),
                    ),
                  ),
                ],
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({
    required this.loading,
    required this.onRefresh,
    required this.onOpenPanel,
  });

  final bool loading;
  final Future<void> Function() onRefresh;
  final VoidCallback onOpenPanel;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (BuildContext context, BoxConstraints constraints) {
        final Widget copy = const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(
              'COACH ACTION CENTER',
              style: TextStyle(
                color: Color(0xFFFFD45A),
                fontSize: 12,
                fontWeight: FontWeight.w900,
                letterSpacing: 1.1,
              ),
            ),
            SizedBox(height: 7),
            Text(
              'O que precisa da sua atenção hoje',
              style: TextStyle(
                color: Colors.white,
                fontSize: 29,
                height: 1.06,
                fontWeight: FontWeight.w900,
              ),
            ),
            SizedBox(height: 7),
            Text(
              'O FitNexus cruza execução, aderência, feedback, acesso, prescrição e decisões pendentes para entregar uma única próxima ação por aluno — sempre explicada e sempre humana.',
              style: TextStyle(color: Color(0xFFAAAAAA), height: 1.45),
            ),
          ],
        );

        final Widget actions = Wrap(
          spacing: 9,
          runSpacing: 9,
          children: <Widget>[
            OutlinedButton.icon(
              onPressed: onOpenPanel,
              icon: const Icon(Icons.dashboard_rounded),
              label: const Text('Painel operacional'),
            ),
            IconButton.filledTonal(
              tooltip: 'Atualizar prioridades',
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

        if (constraints.maxWidth < 760) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[copy, const SizedBox(height: 15), actions],
          );
        }
        return Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: <Widget>[
            Expanded(child: copy),
            const SizedBox(width: 24),
            actions,
          ],
        );
      },
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
        final int columns = constraints.maxWidth >= 1100
            ? 4
            : constraints.maxWidth >= 620
                ? 2
                : 1;
        const double gap = 10;
        final double width =
            (constraints.maxWidth - gap * (columns - 1)) / columns;
        return Wrap(
          spacing: gap,
          runSpacing: gap,
          children: <Widget>[
            SizedBox(
              width: width,
              child: _Metric(
                value: '${summary.activeActions}',
                label: 'ações ativas',
                icon: Icons.bolt_rounded,
                color: const Color(0xFFFFD45A),
              ),
            ),
            SizedBox(
              width: width,
              child: _Metric(
                value: '${summary.urgent}',
                label: 'prioridade agora',
                icon: Icons.priority_high_rounded,
                color: const Color(0xFFFF7474),
              ),
            ),
            SizedBox(
              width: width,
              child: _Metric(
                value: '${summary.completedToday}',
                label: 'concluídas hoje',
                icon: Icons.task_alt_rounded,
                color: const Color(0xFF75E39B),
              ),
            ),
            SizedBox(
              width: width,
              child: _Metric(
                value: '${summary.snoozed}',
                label: 'lembrar depois',
                icon: Icons.schedule_rounded,
                color: const Color(0xFF8EBBFF),
              ),
            ),
          ],
        );
      },
    );
  }
}

class _Metric extends StatelessWidget {
  const _Metric({
    required this.value,
    required this.label,
    required this.icon,
    required this.color,
  });

  final String value;
  final String label;
  final IconData icon;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(15),
      decoration: BoxDecoration(
        color: const Color(0xFF111111),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: color.withValues(alpha: 0.22)),
      ),
      child: Row(
        children: <Widget>[
          Icon(icon, color: color, size: 25),
          const SizedBox(width: 11),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(
                value,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 23,
                  fontWeight: FontWeight.w900,
                ),
              ),
              Text(
                label,
                style: const TextStyle(color: Color(0xFF999999), fontSize: 11),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _Principle extends StatelessWidget {
  const _Principle({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 15, vertical: 12),
      decoration: BoxDecoration(
        color: const Color(0xFF10141A),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: const Color(0xFF8EBBFF).withValues(alpha: 0.24),
        ),
      ),
      child: Row(
        children: <Widget>[
          const Icon(Icons.shield_outlined, color: Color(0xFF8EBBFF)),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(
                color: Color(0xFFB8C7DB),
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ],
      ),
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
    final _PriorityVisual visual = _priority(action.priorityLabel);
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFF101010),
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: visual.color.withValues(alpha: 0.34)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Wrap(
            spacing: 8,
            runSpacing: 8,
            crossAxisAlignment: WrapCrossAlignment.center,
            children: <Widget>[
              _Tag(label: visual.label, color: visual.color),
              _Tag(
                label: 'score ${action.priorityScore}',
                color: const Color(0xFF8EBBFF),
              ),
              _Tag(
                label: '${action.adherence}% aderência',
                color: const Color(0xFFFFD45A),
              ),
            ],
          ),
          const SizedBox(height: 13),
          Text(
            action.studentName,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 20,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 3),
          Text(
            '${action.objective} • ${action.level}',
            style: const TextStyle(color: Color(0xFF999999), fontSize: 12),
          ),
          const SizedBox(height: 13),
          Text(
            action.actionTitle,
            style: TextStyle(
              color: visual.color,
              fontSize: 18,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            action.actionReason,
            style: const TextStyle(color: Color(0xFFCCCCCC), height: 1.45),
          ),
          const SizedBox(height: 13),
          _Evidence(action: action),
          const SizedBox(height: 15),
          LayoutBuilder(
            builder: (BuildContext context, BoxConstraints constraints) {
              final List<Widget> buttons = <Widget>[
                FilledButton.icon(
                  onPressed: busy ? null : onOpen,
                  style: FilledButton.styleFrom(
                    backgroundColor: const Color(0xFFE1B92F),
                    foregroundColor: Colors.black,
                  ),
                  icon: const Icon(Icons.open_in_new_rounded),
                  label: const Text('Abrir contexto'),
                ),
                OutlinedButton.icon(
                  onPressed: busy ? null : onComplete,
                  icon: const Icon(Icons.task_alt_rounded),
                  label: const Text('Concluir por hoje'),
                ),
                TextButton.icon(
                  onPressed: busy ? null : onSnooze,
                  icon: const Icon(Icons.schedule_rounded),
                  label: const Text('Lembrar amanhã'),
                ),
              ];
              if (constraints.maxWidth < 650) {
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: buttons
                      .expand(
                        (Widget button) => <Widget>[
                          button,
                          const SizedBox(height: 8),
                        ],
                      )
                      .toList(growable: false),
                );
              }
              return Wrap(spacing: 9, runSpacing: 9, children: buttons);
            },
          ),
          const SizedBox(height: 9),
          Row(
            children: <Widget>[
              const Icon(
                Icons.person_outline_rounded,
                size: 15,
                color: Color(0xFF777777),
              ),
              const SizedBox(width: 5),
              Expanded(
                child: Text(
                  action.humanActionRequired
                      ? 'Nenhuma ação é executada automaticamente.'
                      : 'Revisão humana continua obrigatória.',
                  style: const TextStyle(
                    color: Color(0xFF777777),
                    fontSize: 10,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _Evidence extends StatelessWidget {
  const _Evidence({required this.action});

  final CoachActionItem action;

  @override
  Widget build(BuildContext context) {
    final CoachActionEvidence evidence = action.evidence;
    final List<String> items = <String>[
      '${action.sessions30d} sessões/30d',
      '${action.completed30d} concluídas',
      if (evidence.painScore != null) 'dor ${evidence.painScore}/10',
      if (evidence.perceivedExertion != null)
        'esforço ${evidence.perceivedExertion}/10',
      if (evidence.energyScore != null) 'energia ${evidence.energyScore}/5',
      if ((evidence.activePlanName ?? '').isNotEmpty)
        'treino: ${evidence.activePlanName}',
      if (evidence.hasActiveAccess != null)
        evidence.hasActiveAccess! ? 'acesso ativo' : 'sem acesso ativo',
      if ((evidence.unresolvedDecisionRunId ?? '').isNotEmpty)
        'Decision Brief pendente',
    ];
    return Wrap(
      spacing: 7,
      runSpacing: 7,
      children: items
          .map(
            (String item) => Container(
              padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 6),
              decoration: BoxDecoration(
                color: const Color(0xFF191919),
                borderRadius: BorderRadius.circular(999),
              ),
              child: Text(
                item,
                style: const TextStyle(
                  color: Color(0xFFB8B8B8),
                  fontSize: 11,
                ),
              ),
            ),
          )
          .toList(growable: false),
    );
  }
}

class _Tag extends StatelessWidget {
  const _Tag({required this.label, required this.color});

  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.10),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: color.withValues(alpha: 0.30)),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: color,
          fontSize: 10,
          fontWeight: FontWeight.w900,
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
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: error ? const Color(0xFF351515) : const Color(0xFF111111),
        borderRadius: BorderRadius.circular(18),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Icon(
            icon,
            color: error ? const Color(0xFFFF9A9A) : const Color(0xFFFFD45A),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  title,
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  text,
                  style: const TextStyle(
                    color: Color(0xFFBBBBBB),
                    height: 1.4,
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

class _PriorityVisual {
  const _PriorityVisual(this.label, this.color);

  final String label;
  final Color color;
}

_PriorityVisual _priority(String value) {
  return switch (value) {
    'urgent' => const _PriorityVisual('AGORA', Color(0xFFFF7474)),
    'attention' => const _PriorityVisual('ATENÇÃO', Color(0xFFFFC85A)),
    'setup' => const _PriorityVisual('CONFIGURAR', Color(0xFF8EBBFF)),
    _ => const _PriorityVisual('ACOMPANHAR', Color(0xFF75E39B)),
  };
}
