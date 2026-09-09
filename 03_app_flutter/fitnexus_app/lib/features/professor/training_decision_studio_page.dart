import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/blackgold_tokens.dart';
import 'professor_data_repository.dart';
import 'professor_lineage_repository.dart';

class TrainingDecisionStudioPage extends StatefulWidget {
  const TrainingDecisionStudioPage({
    super.key,
    this.initialStudentId,
    this.initialName,
    this.initialDecisionReason,
    this.initialNotes,
    this.initialExercises = const <TrainingExerciseDraft>[],
    this.initialDecisionIntelligenceRunId,
    this.initialSourceTemplateId,
  });

  final String? initialStudentId;
  final String? initialName;
  final String? initialDecisionReason;
  final String? initialNotes;
  final List<TrainingExerciseDraft> initialExercises;
  final String? initialDecisionIntelligenceRunId;
  final String? initialSourceTemplateId;

  @override
  State<TrainingDecisionStudioPage> createState() =>
      _TrainingDecisionStudioPageState();
}

class _TrainingDecisionStudioPageState
    extends State<TrainingDecisionStudioPage> {
  final ProfessorDataRepository _data = ProfessorDataRepository.instance;
  final ProfessorLineageRepository _lineage = ProfessorLineageRepository.instance;

  final TextEditingController _nameController = TextEditingController();
  final TextEditingController _nextSessionController = TextEditingController();
  final TextEditingController _reasonController = TextEditingController();
  final TextEditingController _notesController = TextEditingController();
  final TextEditingController _exercisesController = TextEditingController();

  List<StudentRecord> _students = const <StudentRecord>[];
  String? _studentId;
  TrainingChangePreview? _preview;
  String? _previewFingerprint;
  bool _loading = true;
  bool _previewing = false;
  bool _saving = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _nameController.text = widget.initialName ?? '';
    _reasonController.text = widget.initialDecisionReason ?? '';
    _notesController.text = widget.initialNotes ?? '';
    _exercisesController.text = widget.initialExercises
        .map(
          (TrainingExerciseDraft item) =>
              '${item.name.trim()} | ${item.prescription.trim()}',
        )
        .join('\n');
    _loadStudents();
  }

  @override
  void dispose() {
    _nameController.dispose();
    _nextSessionController.dispose();
    _reasonController.dispose();
    _notesController.dispose();
    _exercisesController.dispose();
    super.dispose();
  }

  Future<void> _loadStudents() async {
    try {
      final List<StudentRecord> students = await _data.fetchStudents();
      if (!mounted) return;
      String? selected = widget.initialStudentId;
      if (selected == null ||
          !students.any((StudentRecord item) => item.id == selected)) {
        selected = students.isEmpty ? null : students.first.id;
      }
      setState(() {
        _students = students;
        _studentId = selected;
      });
    } catch (error) {
      if (!mounted) return;
      setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  List<TrainingExerciseDraft> _parseExercises() {
    final List<TrainingExerciseDraft> items = <TrainingExerciseDraft>[];
    final List<String> lines = _exercisesController.text.split('\n');
    for (final String raw in lines) {
      final String line = raw.trim();
      if (line.isEmpty) continue;
      final int divider = line.indexOf('|');
      final String name =
          (divider < 0 ? line : line.substring(0, divider)).trim();
      final String prescription =
          (divider < 0 ? '' : line.substring(divider + 1)).trim();
      if (name.length < 2) {
        throw const FormatException(
          'Cada exercício precisa ter um nome válido.',
        );
      }
      items.add(
        TrainingExerciseDraft(name: name, prescription: prescription),
      );
    }
    if (items.isEmpty) {
      throw const FormatException('Informe pelo menos um exercício.');
    }
    return items;
  }

  String _fingerprint(
    String studentId,
    List<TrainingExerciseDraft> exercises,
  ) {
    return <String>[
      studentId,
      _nameController.text.trim(),
      _nextSessionController.text.trim(),
      _reasonController.text.trim(),
      _notesController.text.trim(),
      ...exercises.map(
        (TrainingExerciseDraft item) =>
            '${item.name.trim()}|${item.prescription.trim()}',
      ),
    ].join('\u001f');
  }

  void _invalidatePreview() {
    if (_preview == null && _previewFingerprint == null) return;
    setState(() {
      _preview = null;
      _previewFingerprint = null;
    });
  }

  Future<void> _previewDecision() async {
    final String studentId = _studentId ?? '';
    if (studentId.isEmpty) return;

    setState(() {
      _previewing = true;
      _error = null;
    });

    try {
      final List<TrainingExerciseDraft> exercises = _parseExercises();
      final TrainingChangePreview preview = await _lineage.previewChange(
        studentId: studentId,
        exercises: exercises
            .map((TrainingExerciseDraft item) => item.toJson())
            .toList(growable: false),
      );
      if (!mounted) return;
      setState(() {
        _preview = preview;
        _previewFingerprint = _fingerprint(studentId, exercises);
      });
    } catch (error) {
      if (!mounted) return;
      setState(() => _error = _friendlyError(error));
    } finally {
      if (mounted) setState(() => _previewing = false);
    }
  }

  Future<void> _commitDecision() async {
    final String studentId = _studentId ?? '';
    if (studentId.isEmpty || _saving) return;

    setState(() {
      _saving = true;
      _error = null;
    });

    try {
      final List<TrainingExerciseDraft> exercises = _parseExercises();
      final String currentFingerprint = _fingerprint(studentId, exercises);
      if (_preview == null || _previewFingerprint != currentFingerprint) {
        throw StateError(
          'A prescrição mudou depois da prévia. Gere uma nova comparação antes de confirmar.',
        );
      }
      if (_nameController.text.trim().length < 2) {
        throw const FormatException('Informe um nome para o treino.');
      }
      if (_reasonController.text.trim().length < 2) {
        throw const FormatException(
          'Registre o motivo da decisão antes de confirmar.',
        );
      }

      await _data.createTrainingPlan(
        studentId: studentId,
        name: _nameController.text,
        exercises: exercises,
        nextSession: _nextSessionController.text,
        notes: _notesController.text,
        decisionReason: _reasonController.text,
        decisionIntelligenceRunId: widget.initialDecisionIntelligenceRunId,
        sourceTemplateId: widget.initialSourceTemplateId,
      );

      if (!mounted) return;
      Navigator.of(context).pop(true);
    } catch (error) {
      if (!mounted) return;
      setState(() => _error = _friendlyError(error));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  String _friendlyError(Object error) {
    final String text = error.toString();
    if (text.contains('ORG_MANAGER_REQUIRED')) {
      return 'Somente owner/admin pode confirmar uma nova prescrição.';
    }
    return text
        .replaceFirst('FormatException: ', '')
        .replaceFirst('Bad state: ', '');
  }

  @override
  Widget build(BuildContext context) {
    final bool intelligenceCandidate =
        (widget.initialDecisionIntelligenceRunId ?? '').isNotEmpty;

    return Scaffold(
      backgroundColor: AppColors.black,
      body: Stack(
        children: <Widget>[
          const Positioned.fill(child: _StudioAtmosphere()),
          SafeArea(
            child: ListView(
              padding: const EdgeInsets.fromLTRB(
                BlackGoldSpace.lg,
                BlackGoldSpace.xl,
                BlackGoldSpace.lg,
                90,
              ),
              children: <Widget>[
                _StudioHeader(intelligenceCandidate: intelligenceCandidate),
                if (intelligenceCandidate) ...<Widget>[
                  const SizedBox(height: BlackGoldSpace.sm),
                  const _Notice(
                    icon: Icons.psychology_alt_rounded,
                    title: 'Candidato recebido do Decision Intelligence',
                    text:
                        'Revise todos os campos: a análise é apenas uma sugestão e não tem permissão para confirmar a prescrição.',
                  ),
                ],
                const SizedBox(height: BlackGoldSpace.lg),
                if (_loading)
                  const _LoadingPanel()
                else if (_students.isEmpty)
                  const _Notice(
                    icon: Icons.groups_outlined,
                    title: 'Nenhum aluno cadastrado',
                    text:
                        'Cadastre um aluno antes de abrir uma decisão de treino.',
                  )
                else ...<Widget>[
                  _DecisionForm(
                    students: _students,
                    studentId: _studentId,
                    saving: _saving,
                    nameController: _nameController,
                    reasonController: _reasonController,
                    nextSessionController: _nextSessionController,
                    notesController: _notesController,
                    exercisesController: _exercisesController,
                    onStudentChanged: (String? value) {
                      setState(() {
                        _studentId = value;
                        _preview = null;
                        _previewFingerprint = null;
                      });
                    },
                    onChanged: _invalidatePreview,
                  ),
                  const SizedBox(height: BlackGoldSpace.sm),
                  _PreviewAction(
                    previewing: _previewing,
                    saving: _saving,
                    onPreview: _previewDecision,
                  ),
                  if (_error != null) ...<Widget>[
                    const SizedBox(height: BlackGoldSpace.sm),
                    _Notice(
                      icon: Icons.error_outline_rounded,
                      title: 'Revise antes de continuar',
                      text: _error!,
                      error: true,
                    ),
                  ],
                  if (_preview != null) ...<Widget>[
                    const SizedBox(height: BlackGoldSpace.lg),
                    _PreviewCard(preview: _preview!),
                    const SizedBox(height: BlackGoldSpace.sm),
                    _CommitPanel(
                      saving: _saving,
                      onCommit: _commitDecision,
                    ),
                  ],
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _StudioAtmosphere extends StatelessWidget {
  const _StudioAtmosphere();

  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      child: DecoratedBox(
        decoration: BoxDecoration(
          gradient: RadialGradient(
            center: const Alignment(0.75, -0.96),
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

class _StudioHeader extends StatelessWidget {
  const _StudioHeader({required this.intelligenceCandidate});

  final bool intelligenceCandidate;

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
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            children: <Widget>[
              Container(
                width: 46,
                height: 46,
                decoration: BoxDecoration(
                  gradient: BlackGoldEffects.goldGradient,
                  borderRadius: BorderRadius.circular(BlackGoldRadius.card),
                  boxShadow: BlackGoldEffects.goldGlow,
                ),
                child: const Icon(Icons.rule_rounded, color: Colors.black),
              ),
              const SizedBox(width: BlackGoldSpace.sm),
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      'DECISION STUDIO',
                      style: TextStyle(
                        color: AppColors.goldSoft,
                        fontSize: 11,
                        fontWeight: FontWeight.w900,
                        letterSpacing: 1.2,
                      ),
                    ),
                    SizedBox(height: BlackGoldSpace.xs),
                    Text(
                      'Prévia → diferença → confirmação humana',
                      style: TextStyle(
                        color: AppColors.text,
                        fontSize: 28,
                        height: 1.06,
                        fontWeight: FontWeight.w900,
                        letterSpacing: -0.6,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: BlackGoldSpace.md),
          const Text(
            'A decisão fica explicada antes de substituir o treino ativo. O banco só recebe a nova versão depois de uma prévia válida e de uma confirmação humana explícita.',
            style: TextStyle(
              color: AppColors.muted,
              height: 1.5,
              fontSize: 14,
            ),
          ),
          const SizedBox(height: BlackGoldSpace.md),
          const _AuthorityStrip(),
        ],
      ),
    );
  }
}

class _AuthorityStrip extends StatelessWidget {
  const _AuthorityStrip();

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
              'Pré-visualizar não altera dados. Confirmar cria uma nova versão e preserva a anterior no Training Lineage.',
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

class _DecisionForm extends StatelessWidget {
  const _DecisionForm({
    required this.students,
    required this.studentId,
    required this.saving,
    required this.nameController,
    required this.reasonController,
    required this.nextSessionController,
    required this.notesController,
    required this.exercisesController,
    required this.onStudentChanged,
    required this.onChanged,
  });

  final List<StudentRecord> students;
  final String? studentId;
  final bool saving;
  final TextEditingController nameController;
  final TextEditingController reasonController;
  final TextEditingController nextSessionController;
  final TextEditingController notesController;
  final TextEditingController exercisesController;
  final ValueChanged<String?> onStudentChanged;
  final VoidCallback onChanged;

  @override
  Widget build(BuildContext context) {
    return _Panel(
      icon: Icons.edit_note_rounded,
      eyebrow: 'NOVA VERSÃO',
      title: 'Defina o contexto da decisão',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          DropdownButtonFormField<String>(
            initialValue: studentId,
            dropdownColor: AppColors.cardRaised,
            decoration: const InputDecoration(labelText: 'Aluno'),
            items: students
                .map(
                  (StudentRecord item) => DropdownMenuItem<String>(
                    value: item.id,
                    child: Text(item.name),
                  ),
                )
                .toList(growable: false),
            onChanged: saving ? null : onStudentChanged,
          ),
          const SizedBox(height: BlackGoldSpace.sm),
          TextField(
            controller: nameController,
            onChanged: (_) => onChanged(),
            decoration: const InputDecoration(
              labelText: 'Nome da nova prescrição',
            ),
          ),
          const SizedBox(height: BlackGoldSpace.sm),
          TextField(
            controller: reasonController,
            onChanged: (_) => onChanged(),
            maxLength: 500,
            minLines: 2,
            maxLines: 4,
            decoration: const InputDecoration(
              labelText: 'Por que esta mudança está sendo feita?',
              hintText:
                  'Ex.: reduzir volume após feedback de recuperação baixa.',
            ),
          ),
          const SizedBox(height: BlackGoldSpace.sm),
          TextField(
            controller: nextSessionController,
            onChanged: (_) => onChanged(),
            decoration: const InputDecoration(
              labelText: 'Próxima sessão (opcional)',
            ),
          ),
          const SizedBox(height: BlackGoldSpace.sm),
          TextField(
            controller: notesController,
            onChanged: (_) => onChanged(),
            minLines: 2,
            maxLines: 4,
            decoration: const InputDecoration(
              labelText: 'Notas da prescrição (opcional)',
            ),
          ),
          const SizedBox(height: BlackGoldSpace.sm),
          TextField(
            controller: exercisesController,
            onChanged: (_) => onChanged(),
            minLines: 6,
            maxLines: 12,
            decoration: const InputDecoration(
              labelText: 'Exercícios — um por linha',
              hintText:
                  'Agachamento | 4x8 • descanso 90s\nRemada | 4x10 • descanso 60s',
              helperText: 'Formato: exercício | prescrição',
            ),
          ),
        ],
      ),
    );
  }
}

class _PreviewAction extends StatelessWidget {
  const _PreviewAction({
    required this.previewing,
    required this.saving,
    required this.onPreview,
  });

  final bool previewing;
  final bool saving;
  final VoidCallback onPreview;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(BlackGoldSpace.md),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(BlackGoldRadius.panel),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          const Text(
            '1. Gere a comparação antes de confirmar',
            style: TextStyle(
              color: AppColors.text,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: BlackGoldSpace.xs),
          const Text(
            'A prévia mostra exatamente o que será adicionado, removido ou alterado em relação ao treino ativo.',
            style: TextStyle(
              color: AppColors.muted,
              fontSize: 12,
              height: 1.4,
            ),
          ),
          const SizedBox(height: BlackGoldSpace.sm),
          OutlinedButton.icon(
            onPressed: previewing || saving ? null : onPreview,
            icon: previewing
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.compare_arrows_rounded),
            label: Text(
              previewing ? 'Comparando...' : 'Gerar prévia e diferenças',
            ),
          ),
        ],
      ),
    );
  }
}

class _PreviewCard extends StatelessWidget {
  const _PreviewCard({required this.preview});

  final TrainingChangePreview preview;

  @override
  Widget build(BuildContext context) {
    return _Panel(
      icon: Icons.compare_arrows_rounded,
      eyebrow: 'PRÉVIA VALIDADA',
      title: preview.hasPreviousPlan
          ? 'Comparado com ${preview.activePlanName ?? 'treino ativo'}'
          : 'Primeira prescrição deste aluno',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          if (!preview.hasChanges)
            const _NoChangeNote()
          else ...<Widget>[
            _Diff(
              title: 'Adicionados',
              items: preview.added,
              color: AppColors.success,
            ),
            _Diff(
              title: 'Removidos',
              items: preview.removed,
              color: AppColors.danger,
            ),
            _Diff(
              title: 'Alterados',
              items: preview.changed,
              color: AppColors.warning,
            ),
          ],
          const SizedBox(height: BlackGoldSpace.sm),
          const _PreviewSafetyNote(),
        ],
      ),
    );
  }
}

class _NoChangeNote extends StatelessWidget {
  const _NoChangeNote();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(BlackGoldSpace.sm),
      decoration: BoxDecoration(
        color: AppColors.gold.withValues(alpha: 0.05),
        borderRadius: BorderRadius.circular(BlackGoldRadius.control),
        border: Border.all(color: AppColors.border),
      ),
      child: const Text(
        'Nenhuma diferença de exercício/prescrição detectada. O motivo ainda ficará registrado se você confirmar.',
        style: TextStyle(color: AppColors.muted, height: 1.4),
      ),
    );
  }
}

class _PreviewSafetyNote extends StatelessWidget {
  const _PreviewSafetyNote();

  @override
  Widget build(BuildContext context) {
    return const Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Icon(Icons.shield_outlined, color: AppColors.goldSoft, size: 18),
        SizedBox(width: BlackGoldSpace.sm),
        Expanded(
          child: Text(
            'A prévia não altera o banco. Confirmar cria uma nova versão e preserva a anterior no Training Lineage.',
            style: TextStyle(
              color: AppColors.muted,
              fontSize: 11,
              height: 1.4,
            ),
          ),
        ),
      ],
    );
  }
}

class _Diff extends StatelessWidget {
  const _Diff({
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
      margin: const EdgeInsets.only(bottom: BlackGoldSpace.xs),
      padding: const EdgeInsets.all(BlackGoldSpace.sm),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.045),
        borderRadius: BorderRadius.circular(BlackGoldRadius.control),
        border: Border.all(color: color.withValues(alpha: 0.20)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(
            title,
            style: TextStyle(color: color, fontWeight: FontWeight.w900),
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

class _CommitPanel extends StatelessWidget {
  const _CommitPanel({required this.saving, required this.onCommit});

  final bool saving;
  final VoidCallback onCommit;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(BlackGoldSpace.md),
      decoration: BoxDecoration(
        color: AppColors.gold.withValues(alpha: 0.065),
        borderRadius: BorderRadius.circular(BlackGoldRadius.panel),
        border: Border.all(color: AppColors.borderGold),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          const Text(
            '2. Confirmação humana',
            style: TextStyle(
              color: AppColors.text,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: BlackGoldSpace.xs),
          const Text(
            'Ao confirmar, uma nova versão será criada. A versão anterior continuará disponível para auditoria e restauração controlada.',
            style: TextStyle(
              color: AppColors.muted,
              fontSize: 12,
              height: 1.4,
            ),
          ),
          const SizedBox(height: BlackGoldSpace.sm),
          FilledButton.icon(
            key: const ValueKey<String>('decision-studio-confirm-version'),
            onPressed: saving ? null : onCommit,
            icon: saving
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.verified_rounded),
            label: Text(saving ? 'Confirmando...' : 'Confirmar nova versão'),
          ),
        ],
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
                    fontSize: 12,
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

class _LoadingPanel extends StatelessWidget {
  const _LoadingPanel();

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 240,
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
            'Carregando contexto de prescrição…',
            style: TextStyle(color: AppColors.muted),
          ),
        ],
      ),
    );
  }
}
