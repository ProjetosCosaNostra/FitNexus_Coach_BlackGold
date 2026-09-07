import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/blackgold_tokens.dart';
import 'professor_data_repository.dart';
import 'professor_decision_intelligence_repository.dart';
import 'professor_lineage_repository.dart';
import 'training_decision_studio_page.dart';

class ProfessorDecisionIntelligencePage extends StatefulWidget {
  const ProfessorDecisionIntelligencePage({super.key});

  @override
  State<ProfessorDecisionIntelligencePage> createState() =>
      _ProfessorDecisionIntelligencePageState();
}

class _ProfessorDecisionIntelligencePageState
    extends State<ProfessorDecisionIntelligencePage> {
  final ProfessorDataRepository _data = ProfessorDataRepository.instance;
  final ProfessorDecisionIntelligenceRepository _intelligence =
      ProfessorDecisionIntelligenceRepository.instance;

  List<StudentRecord> _students = const <StudentRecord>[];
  List<DecisionIntelligenceHistoryItem> _history =
      const <DecisionIntelligenceHistoryItem>[];
  DecisionCalibrationSnapshot? _calibration;
  String? _studentId;
  DecisionIntelligenceBrief? _brief;
  bool _loading = true;
  bool _generating = false;
  bool _resolving = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _bootstrap();
  }

  Future<void> _bootstrap() async {
    if (mounted) {
      setState(() {
        _loading = true;
        _error = null;
      });
    }
    try {
      final List<StudentRecord> students = await _data.fetchStudents();
      if (!mounted) return;
      final String? selected = students.isEmpty ? null : students.first.id;
      setState(() {
        _students = students;
        _studentId = selected;
      });
      if (selected != null) await _loadHistory(selected);
      await _loadCalibration();
    } catch (error) {
      if (!mounted) return;
      setState(() => _error = _friendlyError(error));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _loadHistory(String studentId) async {
    try {
      final List<DecisionIntelligenceHistoryItem> history =
          await _intelligence.fetchHistory(studentId, limit: 6);
      if (!mounted) return;
      setState(() => _history = history);
    } catch (_) {
      if (!mounted) return;
      setState(() => _history = const <DecisionIntelligenceHistoryItem>[]);
    }
  }

  Future<void> _loadCalibration() async {
    try {
      final DecisionCalibrationSnapshot calibration =
          await _intelligence.fetchCalibration();
      if (!mounted) return;
      setState(() => _calibration = calibration);
    } catch (_) {
      if (!mounted) return;
      setState(() => _calibration = null);
    }
  }

  Future<void> _refreshCurrent() async {
    final String? studentId = _studentId;
    if (studentId != null) await _loadHistory(studentId);
    await _loadCalibration();
  }

  Future<void> _generate() async {
    final String studentId = _studentId ?? '';
    if (studentId.isEmpty || _generating || _resolving) return;
    setState(() {
      _generating = true;
      _error = null;
    });
    try {
      final DecisionIntelligenceBrief brief =
          await _intelligence.generateBrief(studentId);
      if (!mounted) return;
      setState(() => _brief = brief);
      await _refreshCurrent();
    } catch (error) {
      if (!mounted) return;
      setState(() => _error = _friendlyError(error));
    } finally {
      if (mounted) setState(() => _generating = false);
    }
  }

  Future<void> _openStudio(DecisionIntelligenceBrief brief) async {
    final DecisionCandidate? candidate = brief.candidate;
    if (candidate == null) return;

    final bool? changed = await Navigator.of(context).push<bool>(
      MaterialPageRoute<bool>(
        builder: (_) => TrainingDecisionStudioPage(
          initialStudentId: brief.studentId,
          initialName: '${candidate.templateName} — revisão',
          initialDecisionReason:
              'Decision Intelligence ${brief.runId}: ${brief.recommendationTitle}. ${brief.recommendationReason}',
          initialNotes:
              'Candidato profissional originado do Smart Template “${candidate.templateName}”. Revisado pelo professor antes do commit.',
          initialExercises: candidate.exercises,
          initialDecisionIntelligenceRunId: brief.runId,
          initialSourceTemplateId: candidate.templateId,
        ),
      ),
    );

    if (!mounted || changed != true) return;
    setState(() => _brief = null);
    await _refreshCurrent();
  }

  Future<void> _recordOutcome(
    DecisionIntelligenceBrief brief,
    String outcome,
  ) async {
    if (_resolving) return;
    final bool confirmed = await _confirmOutcome(outcome);
    if (!confirmed || !mounted) return;

    setState(() {
      _resolving = true;
      _error = null;
    });
    try {
      await _intelligence.recordOutcome(
        runId: brief.runId,
        outcome: outcome,
        note: outcome == 'rejected'
            ? 'Sugestão descartada conscientemente pelo professor'
            : 'Professor decidiu manter a prescrição sem alteração neste momento',
      );
      if (!mounted) return;
      setState(() => _brief = null);
      await _refreshCurrent();
    } catch (error) {
      if (!mounted) return;
      setState(() => _error = _friendlyError(error));
    } finally {
      if (mounted) setState(() => _resolving = false);
    }
  }

  Future<bool> _confirmOutcome(String outcome) async {
    final bool rejected = outcome == 'rejected';
    return await showDialog<bool>(
          context: context,
          barrierColor: Colors.black.withValues(alpha: 0.78),
          builder: (BuildContext dialogContext) => AlertDialog(
            title: Row(
              children: <Widget>[
                Container(
                  width: 40,
                  height: 40,
                  decoration: BoxDecoration(
                    gradient: BlackGoldEffects.goldGradient,
                    borderRadius: BorderRadius.circular(BlackGoldRadius.card),
                  ),
                  child: Icon(
                    rejected
                        ? Icons.close_rounded
                        : Icons.pause_circle_outline_rounded,
                    color: Colors.black,
                  ),
                ),
                const SizedBox(width: BlackGoldSpace.sm),
                Expanded(
                  child: Text(
                    rejected ? 'Descartar sugestão?' : 'Manter treino atual?',
                    style: const TextStyle(
                      color: AppColors.text,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                ),
              ],
            ),
            content: Text(
              rejected
                  ? 'A análise ficará registrada como rejeitada. Nenhuma prescrição será alterada.'
                  : 'A análise ficará registrada como “sem ação”. O treino atual será preservado.',
              style: const TextStyle(color: AppColors.muted, height: 1.45),
            ),
            actions: <Widget>[
              TextButton(
                onPressed: () => Navigator.of(dialogContext).pop(false),
                child: const Text('Cancelar'),
              ),
              FilledButton(
                onPressed: () => Navigator.of(dialogContext).pop(true),
                child: const Text('Confirmar decisão'),
              ),
            ],
          ),
        ) ??
        false;
  }

  String _friendlyError(Object error) {
    final String text = error.toString();
    if (text.contains('ORG_MANAGER_REQUIRED')) {
      return 'Somente owner/admin pode registrar esta decisão.';
    }
    if (text.contains('DECISION_INTELLIGENCE_RUN_ALREADY_RESOLVED')) {
      return 'Este Decision Brief já recebeu uma decisão e não pode ser resolvido novamente.';
    }
    return 'Não foi possível concluir a operação agora. ${text.replaceFirst('Exception: ', '')}';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.black,
      body: Stack(
        children: <Widget>[
          const Positioned.fill(child: _DecisionAtmosphere()),
          SafeArea(
            child: RefreshIndicator(
              color: AppColors.gold,
              onRefresh: _refreshCurrent,
              child: ListView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.fromLTRB(
                  BlackGoldSpace.lg,
                  BlackGoldSpace.xl,
                  BlackGoldSpace.lg,
                  120,
                ),
                children: <Widget>[
                  const _DecisionHeader(),
                  const SizedBox(height: BlackGoldSpace.lg),
                  if (_loading)
                    const _LoadingPanel()
                  else if (_students.isEmpty)
                    const _Notice(
                      icon: Icons.groups_outlined,
                      title: 'Nenhum aluno cadastrado',
                      text:
                          'Cadastre um aluno para gerar o primeiro Decision Brief.',
                    )
                  else ...<Widget>[
                    if (_calibration != null) ...<Widget>[
                      _CalibrationCard(snapshot: _calibration!),
                      const SizedBox(height: BlackGoldSpace.lg),
                    ],
                    _Controls(
                      students: _students,
                      studentId: _studentId,
                      generating: _generating || _resolving,
                      onStudentChanged: (String? value) async {
                        if (value == null) return;
                        setState(() {
                          _studentId = value;
                          _brief = null;
                          _error = null;
                        });
                        await _loadHistory(value);
                      },
                      onGenerate: _generate,
                    ),
                    if (_error != null) ...<Widget>[
                      const SizedBox(height: BlackGoldSpace.sm),
                      _Notice(
                        icon: Icons.error_outline_rounded,
                        title: 'Operação indisponível',
                        text: _error!,
                        error: true,
                      ),
                    ],
                    if (_brief != null) ...<Widget>[
                      const SizedBox(height: BlackGoldSpace.lg),
                      _BriefCard(
                        brief: _brief!,
                        busy: _resolving,
                        onOpenStudio: () => _openStudio(_brief!),
                        onReject: () => _recordOutcome(_brief!, 'rejected'),
                        onNoAction: () => _recordOutcome(_brief!, 'no_action'),
                      ),
                    ],
                    const SizedBox(height: BlackGoldSpace.lg),
                    _HistoryCard(history: _history),
                  ],
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _DecisionAtmosphere extends StatelessWidget {
  const _DecisionAtmosphere();

  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      child: DecoratedBox(
        decoration: BoxDecoration(
          gradient: RadialGradient(
            center: const Alignment(0.7, -0.95),
            radius: 1.2,
            colors: <Color>[
              AppColors.gold.withValues(alpha: 0.07),
              Colors.transparent,
            ],
          ),
        ),
      ),
    );
  }
}

class _DecisionHeader extends StatelessWidget {
  const _DecisionHeader();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(BlackGoldSpace.xl),
      decoration: BoxDecoration(
        gradient: BlackGoldEffects.panelGradient,
        borderRadius: BorderRadius.circular(BlackGoldRadius.hero),
        border: Border.all(color: AppColors.borderGold),
        boxShadow: BlackGoldEffects.cardShadow,
      ),
      child: const Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(
            'DECISION INTELLIGENCE',
            style: TextStyle(
              color: AppColors.goldSoft,
              fontSize: 12,
              fontWeight: FontWeight.w900,
              letterSpacing: 1.15,
            ),
          ),
          SizedBox(height: BlackGoldSpace.xs),
          Text(
            'Sinais viram recomendações explicáveis',
            style: TextStyle(
              color: AppColors.text,
              fontSize: 30,
              height: 1.06,
              fontWeight: FontWeight.w900,
              letterSpacing: -0.7,
            ),
          ),
          SizedBox(height: BlackGoldSpace.sm),
          Text(
            'Aderência, execuções, feedback, treino ativo e Smart Templates entram na análise. A decisão humana continua sendo a autoridade final — e também vira evidência de calibração.',
            style: TextStyle(
              color: AppColors.muted,
              height: 1.5,
              fontSize: 14,
            ),
          ),
          SizedBox(height: BlackGoldSpace.md),
          _HumanAuthorityStrip(),
        ],
      ),
    );
  }
}

class _HumanAuthorityStrip extends StatelessWidget {
  const _HumanAuthorityStrip();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(BlackGoldSpace.sm),
      decoration: BoxDecoration(
        color: AppColors.gold.withValues(alpha: 0.06),
        borderRadius: BorderRadius.circular(BlackGoldRadius.control),
        border: Border.all(color: AppColors.border),
      ),
      child: const Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Icon(Icons.verified_user_rounded, color: AppColors.goldSoft, size: 18),
          SizedBox(width: BlackGoldSpace.sm),
          Expanded(
            child: Text(
              'O motor explica e propõe; o professor decide. Nenhuma prescrição é alterada automaticamente.',
              style: TextStyle(
                color: AppColors.text,
                fontSize: 12,
                height: 1.4,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _CalibrationCard extends StatelessWidget {
  const _CalibrationCard({required this.snapshot});

  final DecisionCalibrationSnapshot snapshot;

  @override
  Widget build(BuildContext context) {
    final DecisionCalibrationSummary summary = snapshot.summary;
    final List<_MetricData> metrics = <_MetricData>[
      _MetricData('Briefs', '${summary.totalRuns}'),
      _MetricData('Resolvidos', '${summary.resolvedRuns}'),
      _MetricData('Pendentes', '${summary.unresolvedRuns}'),
      _MetricData('Adoção', '${summary.adoptionRate}%'),
      _MetricData('Aceitos', '${summary.exactAcceptanceRate}%'),
      _MetricData('Modificados', '${summary.modificationRate}%'),
    ];

    return _Panel(
      icon: Icons.tune_rounded,
      eyebrow: 'CALIBRAÇÃO HUMANA',
      title: 'Como as recomendações estão sendo usadas',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Wrap(
            spacing: BlackGoldSpace.xs,
            runSpacing: BlackGoldSpace.xs,
            children: metrics
                .map((metric) => _Metric(data: metric))
                .toList(growable: false),
          ),
          const SizedBox(height: BlackGoldSpace.sm),
          Text(
            'Aceitos ${summary.accepted} • modificados ${summary.modified} • rejeitados ${summary.rejected} • sem ação ${summary.noAction}',
            style: const TextStyle(
              color: AppColors.muted,
              fontSize: 12,
            ),
          ),
          const SizedBox(height: BlackGoldSpace.xs),
          Text(
            snapshot.interpretation,
            style: const TextStyle(
              color: AppColors.mutedSoft,
              fontSize: 11,
              height: 1.4,
            ),
          ),
        ],
      ),
    );
  }
}

class _MetricData {
  const _MetricData(this.label, this.value);

  final String label;
  final String value;
}

class _Metric extends StatelessWidget {
  const _Metric({required this.data});

  final _MetricData data;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 9),
      decoration: BoxDecoration(
        color: AppColors.cardRaised,
        borderRadius: BorderRadius.circular(BlackGoldRadius.control),
        border: Border.all(color: AppColors.border),
      ),
      child: Text.rich(
        TextSpan(
          children: <InlineSpan>[
            TextSpan(
              text: '${data.value} ',
              style: const TextStyle(
                color: AppColors.text,
                fontWeight: FontWeight.w900,
              ),
            ),
            TextSpan(
              text: data.label,
              style: const TextStyle(
                color: AppColors.muted,
                fontSize: 11,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Controls extends StatelessWidget {
  const _Controls({
    required this.students,
    required this.studentId,
    required this.generating,
    required this.onStudentChanged,
    required this.onGenerate,
  });

  final List<StudentRecord> students;
  final String? studentId;
  final bool generating;
  final ValueChanged<String?> onStudentChanged;
  final VoidCallback onGenerate;

  @override
  Widget build(BuildContext context) {
    return _Panel(
      icon: Icons.psychology_alt_rounded,
      eyebrow: 'NOVO BRIEF',
      title: 'Escolha o aluno e gere uma análise',
      child: LayoutBuilder(
        builder: (BuildContext buildContext, BoxConstraints constraints) {
          final Widget selector = DropdownButtonFormField<String>(
            initialValue: studentId,
            dropdownColor: AppColors.cardRaised,
            decoration: const InputDecoration(labelText: 'Aluno'),
            items: students
                .map(
                  (StudentRecord student) => DropdownMenuItem<String>(
                    value: student.id,
                    child: Text(student.name),
                  ),
                )
                .toList(growable: false),
            onChanged: generating ? null : onStudentChanged,
          );

          final Widget button = FilledButton.icon(
            onPressed: generating ? null : onGenerate,
            icon: generating
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.psychology_alt_rounded),
            label: Text(generating ? 'Processando...' : 'Gerar Decision Brief'),
          );

          if (constraints.maxWidth < 720) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: <Widget>[
                selector,
                const SizedBox(height: BlackGoldSpace.sm),
                button,
              ],
            );
          }

          return Row(
            children: <Widget>[
              Expanded(child: selector),
              const SizedBox(width: BlackGoldSpace.sm),
              button,
            ],
          );
        },
      ),
    );
  }
}

class _BriefCard extends StatelessWidget {
  const _BriefCard({
    required this.brief,
    required this.busy,
    required this.onOpenStudio,
    required this.onReject,
    required this.onNoAction,
  });

  final DecisionIntelligenceBrief brief;
  final bool busy;
  final VoidCallback onOpenStudio;
  final VoidCallback onReject;
  final VoidCallback onNoAction;

  @override
  Widget build(BuildContext context) {
    final _RiskVisual risk = _riskVisual(brief.riskLevel);
    final DecisionCandidate? candidate = brief.candidate;

    return Container(
      padding: const EdgeInsets.all(BlackGoldSpace.lg),
      decoration: BoxDecoration(
        gradient: BlackGoldEffects.panelGradient,
        borderRadius: BorderRadius.circular(BlackGoldRadius.panel),
        border: Border.all(color: risk.color.withValues(alpha: 0.48)),
        boxShadow: <BoxShadow>[
          ...BlackGoldEffects.cardShadow,
          BoxShadow(
            color: risk.color.withValues(alpha: 0.07),
            blurRadius: 30,
            spreadRadius: -8,
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Wrap(
            spacing: BlackGoldSpace.xs,
            runSpacing: BlackGoldSpace.xs,
            children: <Widget>[
              _Tag(label: risk.label, color: risk.color),
              _Tag(
                label: 'Confiança ${brief.confidenceScore}%',
                color: AppColors.goldSoft,
              ),
              _Tag(
                label: brief.engineMode == 'deterministic_fallback'
                    ? 'Motor determinístico'
                    : brief.engineMode,
                color: AppColors.gold,
              ),
            ],
          ),
          const SizedBox(height: BlackGoldSpace.md),
          Text(
            brief.recommendationTitle,
            style: const TextStyle(
              color: AppColors.text,
              fontSize: 24,
              fontWeight: FontWeight.w900,
              height: 1.08,
            ),
          ),
          const SizedBox(height: BlackGoldSpace.xs),
          Text(
            brief.recommendationReason,
            style: const TextStyle(color: AppColors.muted, height: 1.45),
          ),
          const SizedBox(height: BlackGoldSpace.md),
          const Text(
            'EVIDÊNCIAS USADAS',
            style: TextStyle(
              color: AppColors.goldSoft,
              fontSize: 11,
              fontWeight: FontWeight.w900,
              letterSpacing: 0.8,
            ),
          ),
          const SizedBox(height: BlackGoldSpace.xs),
          Wrap(
            spacing: BlackGoldSpace.xs,
            runSpacing: BlackGoldSpace.xs,
            children: brief.evidence
                .map(
                  (DecisionEvidence item) => _EvidenceChip(
                    label: item.label,
                    value: item.displayValue,
                  ),
                )
                .toList(growable: false),
          ),
          const SizedBox(height: BlackGoldSpace.lg),
          if (candidate != null) ...<Widget>[
            Container(
              padding: const EdgeInsets.all(BlackGoldSpace.md),
              decoration: BoxDecoration(
                color: AppColors.gold.withValues(alpha: 0.06),
                borderRadius: BorderRadius.circular(BlackGoldRadius.card),
                border: Border.all(color: AppColors.borderGold),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: <Widget>[
                  Text(
                    'Candidato: ${candidate.templateName}',
                    style: const TextStyle(
                      color: AppColors.text,
                      fontWeight: FontWeight.w900,
                      fontSize: 18,
                    ),
                  ),
                  const SizedBox(height: BlackGoldSpace.xxs),
                  Text(
                    '${candidate.objective} • ${candidate.level} • ${candidate.exercises.length} exercícios',
                    style: const TextStyle(color: AppColors.muted),
                  ),
                  const SizedBox(height: BlackGoldSpace.sm),
                  _DiffSummary(diff: candidate.diff),
                  const SizedBox(height: BlackGoldSpace.md),
                  FilledButton.icon(
                    onPressed: busy ? null : onOpenStudio,
                    icon: const Icon(Icons.rule_rounded),
                    label: const Text('Levar candidato ao Decision Studio'),
                  ),
                  const SizedBox(height: BlackGoldSpace.xs),
                  OutlinedButton.icon(
                    onPressed: busy ? null : onReject,
                    icon: const Icon(Icons.close_rounded),
                    label: const Text('Descartar sugestão'),
                  ),
                ],
              ),
            ),
          ] else ...<Widget>[
            _Notice(
              icon: Icons.shield_outlined,
              title: 'Sem candidato automático',
              text: _blockReason(brief.candidateBlockReason),
            ),
            const SizedBox(height: BlackGoldSpace.sm),
            OutlinedButton.icon(
              onPressed: busy ? null : onNoAction,
              icon: const Icon(Icons.pause_circle_outline_rounded),
              label: const Text('Registrar sem mudança de treino'),
            ),
          ],
          const SizedBox(height: BlackGoldSpace.md),
          const _LearningLoopNote(),
        ],
      ),
    );
  }
}

class _LearningLoopNote extends StatelessWidget {
  const _LearningLoopNote();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(BlackGoldSpace.sm),
      decoration: BoxDecoration(
        color: AppColors.blackSoft,
        borderRadius: BorderRadius.circular(BlackGoldRadius.control),
        border: Border.all(color: AppColors.border),
      ),
      child: const Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Icon(Icons.loop_rounded, color: AppColors.goldSoft, size: 18),
          SizedBox(width: BlackGoldSpace.sm),
          Expanded(
            child: Text(
              'Learning Loop BlackGold: a decisão humana vira evidência de calibração, nunca permissão para o motor editar regras ou prescrições sozinho.',
              style: TextStyle(
                color: AppColors.muted,
                fontSize: 11,
                height: 1.4,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _DiffSummary extends StatelessWidget {
  const _DiffSummary({required this.diff});

  final TrainingChangePreview diff;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: <Widget>[
        Wrap(
          spacing: BlackGoldSpace.xs,
          runSpacing: BlackGoldSpace.xs,
          children: <Widget>[
            _Tag(
              label: '+${diff.added.length} adicionados',
              color: AppColors.success,
            ),
            _Tag(
              label: '-${diff.removed.length} removidos',
              color: AppColors.danger,
            ),
            _Tag(
              label: '${diff.changed.length} alterados',
              color: AppColors.warning,
            ),
          ],
        ),
        if (diff.hasChanges) ...<Widget>[
          const SizedBox(height: BlackGoldSpace.sm),
          ...diff.added.take(3).map(
                (String item) => Text(
                  '+ $item',
                  style: const TextStyle(color: AppColors.success),
                ),
              ),
          ...diff.removed.take(3).map(
                (String item) => Text(
                  '- $item',
                  style: const TextStyle(color: AppColors.danger),
                ),
              ),
          ...diff.changed.take(3).map(
                (String item) => Text(
                  '~ $item',
                  style: const TextStyle(color: AppColors.warning),
                ),
              ),
        ],
      ],
    );
  }
}

class _HistoryCard extends StatelessWidget {
  const _HistoryCard({required this.history});

  final List<DecisionIntelligenceHistoryItem> history;

  @override
  Widget build(BuildContext context) {
    return _Panel(
      icon: Icons.history_rounded,
      eyebrow: 'AUDITORIA',
      title: 'Histórico de análises',
      child: history.isEmpty
          ? const Text(
              'Nenhum Decision Brief gerado ainda.',
              style: TextStyle(color: AppColors.muted),
            )
          : Column(
              children: history
                  .map(
                    (DecisionIntelligenceHistoryItem item) => Padding(
                      padding:
                          const EdgeInsets.only(bottom: BlackGoldSpace.xs),
                      child: Container(
                        padding: const EdgeInsets.all(BlackGoldSpace.sm),
                        decoration: BoxDecoration(
                          color: AppColors.cardRaised,
                          borderRadius:
                              BorderRadius.circular(BlackGoldRadius.control),
                          border: Border.all(color: AppColors.border),
                        ),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: <Widget>[
                            Icon(
                              _riskVisual(item.brief.riskLevel).icon,
                              color: _riskVisual(item.brief.riskLevel).color,
                              size: 18,
                            ),
                            const SizedBox(width: BlackGoldSpace.sm),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: <Widget>[
                                  Text(
                                    item.brief.recommendationTitle,
                                    style: const TextStyle(
                                      color: AppColors.text,
                                      fontWeight: FontWeight.w800,
                                      fontSize: 12,
                                    ),
                                  ),
                                  const SizedBox(height: 2),
                                  Text(
                                    '${_formatDate(item.createdAt)} • confiança ${item.brief.confidenceScore}% • run ${_short(item.runId)}',
                                    style: const TextStyle(
                                      color: AppColors.mutedSoft,
                                      fontSize: 11,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  )
                  .toList(growable: false),
            ),
    );
  }
}

class _EvidenceChip extends StatelessWidget {
  const _EvidenceChip({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 8),
      decoration: BoxDecoration(
        color: AppColors.cardRaised,
        borderRadius: BorderRadius.circular(BlackGoldRadius.control),
        border: Border.all(color: AppColors.border),
      ),
      child: Text(
        '$label: $value',
        style: const TextStyle(
          color: AppColors.text,
          fontSize: 11,
          fontWeight: FontWeight.w600,
        ),
      ),
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
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.10),
        borderRadius: BorderRadius.circular(BlackGoldRadius.pill),
        border: Border.all(color: color.withValues(alpha: 0.28)),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: color,
          fontSize: 11,
          fontWeight: FontWeight.w900,
        ),
      ),
    );
  }
}

class _Panel extends StatelessWidget {
  const _Panel({
    required this.icon,
    required this.eyebrow,
    required this.title,
    required this.child,
  });

  final IconData icon;
  final String eyebrow;
  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(BlackGoldSpace.lg),
      decoration: BoxDecoration(
        gradient: BlackGoldEffects.panelGradient,
        borderRadius: BorderRadius.circular(BlackGoldRadius.panel),
        border: Border.all(color: AppColors.borderGold),
        boxShadow: BlackGoldEffects.cardShadow,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Container(
                width: 42,
                height: 42,
                decoration: BoxDecoration(
                  color: AppColors.gold.withValues(alpha: 0.09),
                  borderRadius: BorderRadius.circular(BlackGoldRadius.control),
                  border: Border.all(color: AppColors.border),
                ),
                child: Icon(icon, color: AppColors.goldSoft, size: 20),
              ),
              const SizedBox(width: BlackGoldSpace.sm),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      eyebrow,
                      style: const TextStyle(
                        color: AppColors.goldSoft,
                        fontSize: 10,
                        fontWeight: FontWeight.w900,
                        letterSpacing: 0.9,
                      ),
                    ),
                    const SizedBox(height: BlackGoldSpace.xxs),
                    Text(
                      title,
                      style: const TextStyle(
                        color: AppColors.text,
                        fontSize: 18,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: BlackGoldSpace.md),
          child,
        ],
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
    final Color color = error ? AppColors.danger : AppColors.gold;
    return Container(
      padding: const EdgeInsets.all(BlackGoldSpace.md),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.07),
        borderRadius: BorderRadius.circular(BlackGoldRadius.panel),
        border: Border.all(color: color.withValues(alpha: 0.30)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Icon(icon, color: color),
          const SizedBox(width: BlackGoldSpace.sm),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  title,
                  style: const TextStyle(
                    color: AppColors.text,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const SizedBox(height: BlackGoldSpace.xxs),
                Text(
                  text,
                  style: const TextStyle(
                    color: AppColors.muted,
                    height: 1.4,
                    fontSize: 12,
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
    return Container(
      height: 260,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(BlackGoldRadius.panel),
        border: Border.all(color: AppColors.border),
      ),
      child: const Column(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          CircularProgressIndicator(color: AppColors.gold),
          SizedBox(height: BlackGoldSpace.md),
          Text(
            'Carregando sinais e calibração…',
            style: TextStyle(color: AppColors.muted),
          ),
        ],
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
  return switch (level) {
    'high' => const _RiskVisual(
        'PRIORIDADE ALTA', AppColors.danger, Icons.priority_high_rounded),
    'medium' => const _RiskVisual(
        'ATENÇÃO', AppColors.warning, Icons.visibility_rounded),
    'low' => const _RiskVisual('SINAL SAUDÁVEL', AppColors.success,
        Icons.check_circle_outline_rounded),
    _ => const _RiskVisual(
        'NOVO', AppColors.goldSoft, Icons.fiber_new_rounded),
  };
}

String _blockReason(String? reason) {
  return switch (reason) {
    'HIGH_PAIN_REQUIRES_HUMAN_REVIEW' =>
      'Há um sinal de dor/desconforto alto. O sistema bloqueou candidato de progressão e exige revisão humana antes de qualquer troca.',
    'RECOVERY_SIGNAL_REQUIRES_HUMAN_REVIEW' =>
      'Esforço muito alto e energia baixa pedem revisão do contexto antes de qualquer proposta de nova prescrição.',
    'ENGAGEMENT_SIGNAL_REQUIRES_CONTEXT' || 'ENGAGEMENT_CHECK_REQUIRED' =>
      'O principal problema parece ser aderência/continuidade. Trocar exercícios sem entender a barreira poderia mascarar a causa real.',
    'MODERATE_PAIN_REQUIRES_REVIEW' || 'RECOVERY_CHECK_REQUIRED' =>
      'Existe um sinal de desconforto ou recuperação que precisa ser validado pelo professor antes da progressão.',
    'NO_MATCHING_PROFESSIONAL_TEMPLATE' =>
      'Não existe Smart Template profissional compatível com objetivo e nível para propor um diff seguro.',
    'NO_CHANGE_SIGNAL' =>
      'Os dados atuais favorecem manutenção e acompanhamento, sem motivo suficiente para propor mudança.',
    _ =>
      'Nenhum candidato de alteração foi liberado pelos guardrails desta análise.',
  };
}

String _formatDate(DateTime value) {
  final DateTime local = value.toLocal();
  String two(int number) => number.toString().padLeft(2, '0');
  return '${two(local.day)}/${two(local.month)} ${two(local.hour)}:${two(local.minute)}';
}

String _short(String value) {
  if (value.length <= 8) return value;
  return value.substring(0, 8);
}
