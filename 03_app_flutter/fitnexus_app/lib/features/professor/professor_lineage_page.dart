import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/blackgold_tokens.dart';
import 'professor_data_repository.dart';
import 'professor_lineage_repository.dart';
import 'training_decision_studio_page.dart';

class ProfessorLineagePage extends StatefulWidget {
  const ProfessorLineagePage({super.key});

  @override
  State<ProfessorLineagePage> createState() => _ProfessorLineagePageState();
}

class _ProfessorLineagePageState extends State<ProfessorLineagePage> {
  final ProfessorDataRepository _data = ProfessorDataRepository.instance;
  final ProfessorLineageRepository _lineage = ProfessorLineageRepository.instance;

  List<StudentRecord> _students = const <StudentRecord>[];
  String? _studentId;
  TrainingLineageSnapshot? _snapshot;
  bool _loading = true;
  bool _restoring = false;
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
      if (selected != null) {
        await _loadLineage(selected);
      }
    } catch (error) {
      if (!mounted) return;
      setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _loadLineage(String studentId) async {
    if (mounted) {
      setState(() {
        _loading = true;
        _error = null;
      });
    }
    try {
      final TrainingLineageSnapshot snapshot =
          await _lineage.fetchLineage(studentId);
      if (!mounted) return;
      setState(() => _snapshot = snapshot);
    } catch (error) {
      if (!mounted) return;
      setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _openDecisionStudio() async {
    final bool? changed = await Navigator.of(context).push<bool>(
      MaterialPageRoute<bool>(
        builder: (_) => TrainingDecisionStudioPage(initialStudentId: _studentId),
      ),
    );
    if (!mounted || changed != true) return;
    final String? studentId = _studentId;
    if (studentId != null) await _loadLineage(studentId);
  }

  Future<void> _restoreVersion(TrainingLineageRecord record) async {
    if (_restoring || record.isActive) return;

    final TextEditingController reasonController = TextEditingController(
      text: 'Restaurar ${record.planName} após revisão do histórico',
    );

    final String? reason = await showDialog<String>(
      context: context,
      barrierColor: Colors.black.withValues(alpha: 0.78),
      builder: (BuildContext dialogContext) => AlertDialog(
        title: const _RestoreDialogTitle(),
        content: SizedBox(
          width: 620,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              Text(
                'A versão “${record.planName}” não será reativada diretamente. O FitNexus criará uma nova cópia, preservando a versão ativa atual como predecessora.',
                style: const TextStyle(
                  color: AppColors.muted,
                  height: 1.45,
                ),
              ),
              const SizedBox(height: BlackGoldSpace.md),
              const _AuditSafetyNote(),
              const SizedBox(height: BlackGoldSpace.md),
              TextField(
                controller: reasonController,
                maxLength: 500,
                minLines: 2,
                maxLines: 4,
                decoration: const InputDecoration(
                  labelText: 'Motivo da restauração',
                ),
              ),
            ],
          ),
        ),
        actions: <Widget>[
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(),
            child: const Text('Cancelar'),
          ),
          FilledButton.icon(
            onPressed: () {
              final String normalized = reasonController.text.trim();
              if (normalized.length < 2) return;
              Navigator.of(dialogContext).pop(normalized);
            },
            icon: const Icon(Icons.restore_rounded),
            label: const Text('Confirmar restauração'),
          ),
        ],
      ),
    );

    reasonController.dispose();
    if (reason == null || !mounted) return;

    setState(() {
      _restoring = true;
      _error = null;
    });

    try {
      await _lineage.restoreVersion(
        planId: record.planId,
        decisionReason: reason,
      );
      final String? studentId = _studentId;
      if (studentId != null) await _loadLineage(studentId);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Versão restaurada como uma nova decisão auditável.'),
        ),
      );
    } catch (error) {
      if (!mounted) return;
      setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _restoring = false);
    }
  }

  Future<void> _refresh() async {
    final String? studentId = _studentId;
    if (studentId == null) {
      await _bootstrap();
    } else {
      await _loadLineage(studentId);
    }
  }

  @override
  Widget build(BuildContext context) {
    final List<TrainingLineageRecord> items =
        _snapshot?.items ?? const <TrainingLineageRecord>[];

    return Scaffold(
      backgroundColor: AppColors.black,
      body: Stack(
        children: <Widget>[
          const Positioned.fill(child: _LineageAtmosphere()),
          SafeArea(
            child: RefreshIndicator(
              color: AppColors.gold,
              backgroundColor: AppColors.cardRaised,
              onRefresh: _refresh,
              child: ListView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.fromLTRB(
                  BlackGoldSpace.lg,
                  BlackGoldSpace.xl,
                  BlackGoldSpace.lg,
                  110,
                ),
                children: <Widget>[
                  _LineageHeader(
                    canCreate: _students.isNotEmpty && !_loading && !_restoring,
                    onCreate: _openDecisionStudio,
                  ),
                  const SizedBox(height: BlackGoldSpace.lg),
                  if (_students.isNotEmpty)
                    _StudentSelector(
                      students: _students,
                      studentId: _studentId,
                      enabled: !_loading && !_restoring,
                      onChanged: (String? value) {
                        if (value == null) return;
                        setState(() => _studentId = value);
                        _loadLineage(value);
                      },
                    ),
                  if (_students.isNotEmpty)
                    const SizedBox(height: BlackGoldSpace.lg),
                  if (_error != null)
                    _Message(
                      icon: Icons.error_outline_rounded,
                      title: 'Não foi possível carregar a linhagem',
                      text: _error!,
                      error: true,
                    )
                  else if ((_loading || _restoring) && _snapshot == null)
                    const _LoadingPanel()
                  else if (_students.isEmpty)
                    const _Message(
                      icon: Icons.groups_outlined,
                      title: 'Nenhum aluno cadastrado',
                      text:
                          'Cadastre um aluno e crie a primeira prescrição para iniciar a linhagem.',
                    )
                  else if (items.isEmpty)
                    const _Message(
                      icon: Icons.account_tree_outlined,
                      title: 'Nenhuma prescrição registrada',
                      text:
                          'A primeira criação de treino aparecerá aqui como origem da linhagem.',
                    )
                  else ...<Widget>[
                    _LineageSummary(items: items),
                    const SizedBox(height: BlackGoldSpace.lg),
                    const _SectionHeading(
                      eyebrow: 'CADEIA DE DECISÕES',
                      title: 'Histórico preservado, versão por versão',
                      subtitle:
                          'Cada cartão representa uma prescrição auditável. Mudanças, origem e predecessor permanecem visíveis mesmo depois de novas revisões.',
                    ),
                    const SizedBox(height: BlackGoldSpace.md),
                    ...items.asMap().entries.map(
                          (MapEntry<int, TrainingLineageRecord> entry) =>
                              _TimelineItem(
                            record: entry.value,
                            isFirst: entry.key == 0,
                            isLast: entry.key == items.length - 1,
                            restoring: _restoring,
                            onRestore: _restoreVersion,
                          ),
                        ),
                    if (_snapshot != null) ...<Widget>[
                      const SizedBox(height: BlackGoldSpace.xs),
                      Text(
                        'Linhagem atualizada em ${_formatDate(_snapshot!.generatedAt)}',
                        textAlign: TextAlign.right,
                        style: const TextStyle(
                          color: AppColors.mutedSoft,
                          fontSize: 10.5,
                        ),
                      ),
                    ],
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

class _LineageAtmosphere extends StatelessWidget {
  const _LineageAtmosphere();

  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      child: DecoratedBox(
        decoration: BoxDecoration(
          gradient: RadialGradient(
            center: const Alignment(0.76, -0.96),
            radius: 1.18,
            colors: <Color>[
              AppColors.gold.withValues(alpha: 0.075),
              Colors.transparent,
            ],
          ),
        ),
      ),
    );
  }
}

class _LineageHeader extends StatelessWidget {
  const _LineageHeader({required this.canCreate, required this.onCreate});

  final bool canCreate;
  final VoidCallback onCreate;

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
      child: LayoutBuilder(
        builder: (BuildContext context, BoxConstraints constraints) {
          final Widget copy = const Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(
                'TRAINING LINEAGE',
                style: TextStyle(
                  color: AppColors.goldSoft,
                  fontSize: 11,
                  fontWeight: FontWeight.w900,
                  letterSpacing: 1.25,
                ),
              ),
              SizedBox(height: BlackGoldSpace.xs),
              Text(
                'Veja de onde cada treino veio e o que mudou',
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
                'O FitNexus preserva a cadeia de prescrições. Nenhuma revisão apaga a anterior e nenhuma restauração sobrescreve o histórico.',
                style: TextStyle(
                  color: AppColors.muted,
                  height: 1.5,
                  fontSize: 14,
                ),
              ),
            ],
          );

          final Widget action = FilledButton.icon(
            key: const ValueKey<String>('lineage-new-decision'),
            onPressed: canCreate ? onCreate : null,
            icon: const Icon(Icons.add_task_rounded),
            label: const Text('Nova decisão'),
          );

          if (constraints.maxWidth < BlackGoldBreakpoints.tablet) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: <Widget>[
                copy,
                const SizedBox(height: BlackGoldSpace.lg),
                action,
              ],
            );
          }

          return Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: <Widget>[
              Expanded(child: copy),
              const SizedBox(width: BlackGoldSpace.xxl),
              action,
            ],
          );
        },
      ),
    );
  }
}

class _StudentSelector extends StatelessWidget {
  const _StudentSelector({
    required this.students,
    required this.studentId,
    required this.enabled,
    required this.onChanged,
  });

  final List<StudentRecord> students;
  final String? studentId;
  final bool enabled;
  final ValueChanged<String?> onChanged;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(BlackGoldSpace.md),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(BlackGoldRadius.panel),
        border: Border.all(color: AppColors.border),
        boxShadow: BlackGoldEffects.cardShadow,
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: <Widget>[
          Container(
            width: 42,
            height: 42,
            decoration: BoxDecoration(
              color: AppColors.gold.withValues(alpha: 0.09),
              borderRadius: BorderRadius.circular(BlackGoldRadius.control),
              border: Border.all(color: AppColors.border),
            ),
            child: const Icon(Icons.person_search_rounded),
          ),
          const SizedBox(width: BlackGoldSpace.sm),
          Expanded(
            child: DropdownButtonFormField<String>(
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
              onChanged: enabled ? onChanged : null,
            ),
          ),
        ],
      ),
    );
  }
}

class _LineageSummary extends StatelessWidget {
  const _LineageSummary({required this.items});

  final List<TrainingLineageRecord> items;

  @override
  Widget build(BuildContext context) {
    final int restorations = items
        .where((TrainingLineageRecord item) => item.decisionType == 'restoration')
        .length;
    final int templateOrigins = items
        .where((TrainingLineageRecord item) =>
            (item.sourceTemplateName ?? '').trim().isNotEmpty)
        .length;
    final int changes = items.fold<int>(
      0,
      (int total, TrainingLineageRecord item) =>
          total +
          item.diff.addedCount +
          item.diff.removedCount +
          item.diff.changedCount,
    );

    final List<_SummaryData> data = <_SummaryData>[
      _SummaryData(Icons.account_tree_rounded, '${items.length}', 'Versões', 'preservadas'),
      _SummaryData(Icons.auto_awesome_rounded, '$templateOrigins', 'Smart Templates', 'na origem'),
      _SummaryData(Icons.change_circle_outlined, '$changes', 'Mudanças', 'auditadas'),
      _SummaryData(Icons.restore_rounded, '$restorations', 'Restaurações', 'controladas'),
    ];

    return LayoutBuilder(
      builder: (BuildContext context, BoxConstraints constraints) {
        final int columns = constraints.maxWidth >= 1040
            ? 4
            : constraints.maxWidth >= BlackGoldBreakpoints.mobile
                ? 2
                : 1;
        const double gap = BlackGoldSpace.sm;
        final double width =
            (constraints.maxWidth - gap * (columns - 1)) / columns;
        return Wrap(
          spacing: gap,
          runSpacing: gap,
          children: data
              .map((item) => SizedBox(width: width, child: _SummaryCard(data: item)))
              .toList(growable: false),
        );
      },
    );
  }
}

class _SummaryData {
  const _SummaryData(this.icon, this.value, this.label, this.caption);

  final IconData icon;
  final String value;
  final String label;
  final String caption;
}

class _SummaryCard extends StatelessWidget {
  const _SummaryCard({required this.data});

  final _SummaryData data;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(BlackGoldSpace.md),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(BlackGoldRadius.card),
        border: Border.all(color: AppColors.border),
        boxShadow: BlackGoldEffects.cardShadow,
      ),
      child: Row(
        children: <Widget>[
          Container(
            width: 42,
            height: 42,
            decoration: BoxDecoration(
              color: AppColors.gold.withValues(alpha: 0.09),
              borderRadius: BorderRadius.circular(BlackGoldRadius.control),
              border: Border.all(color: AppColors.border),
            ),
            child: Icon(data.icon, color: AppColors.goldSoft),
          ),
          const SizedBox(width: BlackGoldSpace.sm),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  data.value,
                  style: const TextStyle(
                    color: AppColors.text,
                    fontSize: 22,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                Text(
                  data.label,
                  style: const TextStyle(
                    color: AppColors.goldSoft,
                    fontSize: 11,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  data.caption,
                  style: const TextStyle(
                    color: AppColors.mutedSoft,
                    fontSize: 10,
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

class _SectionHeading extends StatelessWidget {
  const _SectionHeading({
    required this.eyebrow,
    required this.title,
    required this.subtitle,
  });

  final String eyebrow;
  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Text(
          eyebrow,
          style: const TextStyle(
            color: AppColors.goldSoft,
            fontSize: 11,
            fontWeight: FontWeight.w900,
            letterSpacing: 1.1,
          ),
        ),
        const SizedBox(height: BlackGoldSpace.xs),
        Text(
          title,
          style: const TextStyle(
            color: AppColors.text,
            fontSize: 24,
            height: 1.08,
            fontWeight: FontWeight.w900,
          ),
        ),
        const SizedBox(height: BlackGoldSpace.xs),
        Text(
          subtitle,
          style: const TextStyle(color: AppColors.muted, height: 1.45),
        ),
      ],
    );
  }
}

class _TimelineItem extends StatelessWidget {
  const _TimelineItem({
    required this.record,
    required this.isFirst,
    required this.isLast,
    required this.restoring,
    required this.onRestore,
  });

  final TrainingLineageRecord record;
  final bool isFirst;
  final bool isLast;
  final bool restoring;
  final Future<void> Function(TrainingLineageRecord record) onRestore;

  @override
  Widget build(BuildContext context) {
    final Color accent = record.isActive ? AppColors.success : AppColors.gold;

    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          SizedBox(
            width: 38,
            child: Column(
              children: <Widget>[
                if (!isFirst)
                  Expanded(
                    child: Container(width: 1, color: AppColors.borderGold),
                  )
                else
                  const Spacer(),
                Container(
                  width: 18,
                  height: 18,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: AppColors.black,
                    border: Border.all(color: accent, width: 3),
                    boxShadow: <BoxShadow>[
                      BoxShadow(
                        color: accent.withValues(alpha: 0.22),
                        blurRadius: 12,
                      ),
                    ],
                  ),
                ),
                if (!isLast)
                  Expanded(
                    child: Container(width: 1, color: AppColors.borderGold),
                  )
                else
                  const Spacer(),
              ],
            ),
          ),
          const SizedBox(width: BlackGoldSpace.xs),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.only(bottom: BlackGoldSpace.sm),
              child: _LineageCard(
                record: record,
                restoring: restoring,
                onRestore: onRestore,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _LineageCard extends StatelessWidget {
  const _LineageCard({
    required this.record,
    required this.restoring,
    required this.onRestore,
  });

  final TrainingLineageRecord record;
  final bool restoring;
  final Future<void> Function(TrainingLineageRecord record) onRestore;

  @override
  Widget build(BuildContext context) {
    final Color accent = record.isActive ? AppColors.success : AppColors.gold;

    return Container(
      padding: const EdgeInsets.all(BlackGoldSpace.lg),
      decoration: BoxDecoration(
        gradient: BlackGoldEffects.panelGradient,
        borderRadius: BorderRadius.circular(BlackGoldRadius.panel),
        border: Border.all(color: accent.withValues(alpha: 0.42)),
        boxShadow: BlackGoldEffects.cardShadow,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: accent.withValues(alpha: 0.09),
                  borderRadius: BorderRadius.circular(BlackGoldRadius.card),
                  border: Border.all(color: accent.withValues(alpha: 0.25)),
                ),
                child: Icon(Icons.account_tree_rounded, color: accent),
              ),
              const SizedBox(width: BlackGoldSpace.sm),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      record.planName,
                      style: const TextStyle(
                        color: AppColors.text,
                        fontSize: 18,
                        height: 1.12,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(height: BlackGoldSpace.xxs),
                    Text(
                      '${record.decisionLabel} • ${_formatDate(record.createdAt)}',
                      style: const TextStyle(
                        color: AppColors.muted,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ),
              if (record.isActive)
                const _Tag(label: 'ATIVO', color: AppColors.success),
            ],
          ),
          const SizedBox(height: BlackGoldSpace.md),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(BlackGoldSpace.sm),
            decoration: BoxDecoration(
              color: AppColors.blackSoft,
              borderRadius: BorderRadius.circular(BlackGoldRadius.control),
              border: Border.all(color: AppColors.border),
            ),
            child: Text(
              record.decisionReason,
              style: const TextStyle(
                color: AppColors.text,
                height: 1.45,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
          if ((record.sourceTemplateName ?? '').trim().isNotEmpty ||
              (record.predecessorPlanName ?? '').trim().isNotEmpty) ...<Widget>[
            const SizedBox(height: BlackGoldSpace.sm),
            _OriginStrip(record: record),
          ],
          const SizedBox(height: BlackGoldSpace.md),
          Wrap(
            spacing: BlackGoldSpace.xs,
            runSpacing: BlackGoldSpace.xs,
            children: <Widget>[
              _Tag(
                label: '${record.exerciseCount} exercícios',
                color: AppColors.goldSoft,
              ),
              if (record.diff.addedCount > 0)
                _Tag(
                  label: '+${record.diff.addedCount} adicionados',
                  color: AppColors.success,
                ),
              if (record.diff.removedCount > 0)
                _Tag(
                  label: '-${record.diff.removedCount} removidos',
                  color: AppColors.danger,
                ),
              if (record.diff.changedCount > 0)
                _Tag(
                  label: '${record.diff.changedCount} alterados',
                  color: AppColors.warning,
                ),
            ],
          ),
          if (record.diff.hasChanges) ...<Widget>[
            const SizedBox(height: BlackGoldSpace.sm),
            Theme(
              data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
              child: ExpansionTile(
                tilePadding: EdgeInsets.zero,
                childrenPadding: EdgeInsets.zero,
                collapsedIconColor: AppColors.goldSoft,
                iconColor: AppColors.goldSoft,
                title: const Text(
                  'Ver diferença da versão anterior',
                  style: TextStyle(
                    color: AppColors.goldSoft,
                    fontWeight: FontWeight.w800,
                    fontSize: 13,
                  ),
                ),
                children: <Widget>[
                  _DiffSection(
                    title: 'Adicionados',
                    items: record.diff.added,
                    color: AppColors.success,
                  ),
                  _DiffSection(
                    title: 'Removidos',
                    items: record.diff.removed,
                    color: AppColors.danger,
                  ),
                  _DiffSection(
                    title: 'Alterados',
                    items: record.diff.changed,
                    color: AppColors.warning,
                  ),
                ],
              ),
            ),
          ],
          if (!record.isActive) ...<Widget>[
            const SizedBox(height: BlackGoldSpace.sm),
            OutlinedButton.icon(
              onPressed: restoring ? null : () => onRestore(record),
              icon: const Icon(Icons.restore_rounded),
              label: const Text('Restaurar como nova versão'),
            ),
          ],
        ],
      ),
    );
  }
}

class _OriginStrip extends StatelessWidget {
  const _OriginStrip({required this.record});

  final TrainingLineageRecord record;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(BlackGoldSpace.sm),
      decoration: BoxDecoration(
        color: AppColors.gold.withValues(alpha: 0.055),
        borderRadius: BorderRadius.circular(BlackGoldRadius.control),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          if ((record.sourceTemplateName ?? '').trim().isNotEmpty)
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                const Icon(
                  Icons.auto_awesome_rounded,
                  color: AppColors.goldSoft,
                  size: 16,
                ),
                const SizedBox(width: BlackGoldSpace.xs),
                Expanded(
                  child: Text(
                    'Origem: Smart Template “${record.sourceTemplateName}”',
                    style: const TextStyle(
                      color: AppColors.goldSoft,
                      fontSize: 12,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
              ],
            ),
          if ((record.sourceTemplateName ?? '').trim().isNotEmpty &&
              (record.predecessorPlanName ?? '').trim().isNotEmpty)
            const SizedBox(height: BlackGoldSpace.xs),
          if ((record.predecessorPlanName ?? '').trim().isNotEmpty)
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                const Icon(
                  Icons.subdirectory_arrow_right_rounded,
                  color: AppColors.muted,
                  size: 16,
                ),
                const SizedBox(width: BlackGoldSpace.xs),
                Expanded(
                  child: Text(
                    'Substituiu: ${record.predecessorPlanName}',
                    style: const TextStyle(
                      color: AppColors.muted,
                      fontSize: 12,
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

class _DiffSection extends StatelessWidget {
  const _DiffSection({
    required this.title,
    required this.items,
    required this.color,
  });

  final String title;
  final List<String> items;
  final Color color;

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) return const SizedBox.shrink();

    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: BlackGoldSpace.xs),
      padding: const EdgeInsets.all(BlackGoldSpace.sm),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.045),
        borderRadius: BorderRadius.circular(BlackGoldRadius.control),
        border: Border.all(color: color.withValues(alpha: 0.18)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Text(
            title,
            style: TextStyle(
              color: color,
              fontWeight: FontWeight.w900,
              fontSize: 12,
            ),
          ),
          const SizedBox(height: BlackGoldSpace.xs),
          ...items.map(
            (String item) => Padding(
              padding: const EdgeInsets.only(bottom: BlackGoldSpace.xxs),
              child: Text(
                '• $item',
                style: const TextStyle(
                  color: AppColors.muted,
                  fontSize: 12,
                  height: 1.35,
                ),
              ),
            ),
          ),
        ],
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
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 6),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.09),
        borderRadius: BorderRadius.circular(BlackGoldRadius.pill),
        border: Border.all(color: color.withValues(alpha: 0.25)),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: color,
          fontSize: 10.5,
          fontWeight: FontWeight.w900,
        ),
      ),
    );
  }
}

class _RestoreDialogTitle extends StatelessWidget {
  const _RestoreDialogTitle();

  @override
  Widget build(BuildContext context) {
    return Row(
      children: <Widget>[
        Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(
            gradient: BlackGoldEffects.goldGradient,
            borderRadius: BorderRadius.circular(BlackGoldRadius.card),
          ),
          child: const Icon(Icons.restore_rounded, color: Colors.black),
        ),
        const SizedBox(width: BlackGoldSpace.sm),
        const Expanded(
          child: Text(
            'Restaurar como nova versão?',
            style: TextStyle(
              color: AppColors.text,
              fontWeight: FontWeight.w900,
            ),
          ),
        ),
      ],
    );
  }
}

class _AuditSafetyNote extends StatelessWidget {
  const _AuditSafetyNote();

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
              'A restauração é uma nova decisão auditável. A versão ativa atual continua registrada e a versão antiga não é sobrescrita.',
              style: TextStyle(
                color: AppColors.muted,
                fontSize: 12,
                height: 1.4,
              ),
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
    final Color accent = error ? AppColors.danger : AppColors.gold;
    return Container(
      padding: const EdgeInsets.all(BlackGoldSpace.lg),
      decoration: BoxDecoration(
        gradient: BlackGoldEffects.panelGradient,
        borderRadius: BorderRadius.circular(BlackGoldRadius.panel),
        border: Border.all(color: accent.withValues(alpha: 0.35)),
        boxShadow: BlackGoldEffects.cardShadow,
      ),
      child: Column(
        children: <Widget>[
          Container(
            width: 52,
            height: 52,
            decoration: BoxDecoration(
              color: accent.withValues(alpha: 0.08),
              borderRadius: BorderRadius.circular(BlackGoldRadius.panel),
              border: Border.all(color: accent.withValues(alpha: 0.24)),
            ),
            child: Icon(icon, color: accent, size: 27),
          ),
          const SizedBox(height: BlackGoldSpace.md),
          Text(
            title,
            textAlign: TextAlign.center,
            style: const TextStyle(
              color: AppColors.text,
              fontSize: 18,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: BlackGoldSpace.xs),
          Text(
            text,
            textAlign: TextAlign.center,
            style: const TextStyle(color: AppColors.muted, height: 1.45),
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
      height: 280,
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
            'Carregando cadeia de decisões…',
            style: TextStyle(color: AppColors.muted),
          ),
        ],
      ),
    );
  }
}

String _formatDate(DateTime value) {
  final DateTime local = value.toLocal();
  String two(int value) => value.toString().padLeft(2, '0');
  return '${two(local.day)}/${two(local.month)}/${local.year} ${two(local.hour)}:${two(local.minute)}';
}
