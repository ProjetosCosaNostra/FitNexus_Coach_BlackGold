import 'package:flutter/material.dart';

import 'professor_data_repository.dart';
import 'professor_template_repository.dart';

class ProfessorTemplatesPage extends StatefulWidget {
  const ProfessorTemplatesPage({super.key});

  @override
  State<ProfessorTemplatesPage> createState() => _ProfessorTemplatesPageState();
}

class _ProfessorTemplatesPageState extends State<ProfessorTemplatesPage> {
  final ProfessorTemplateRepository _templates =
      ProfessorTemplateRepository.instance;
  final ProfessorDataRepository _data = ProfessorDataRepository.instance;

  List<TrainingTemplateRecord> _items = const <TrainingTemplateRecord>[];
  List<StudentRecord> _students = const <StudentRecord>[];
  List<TrainingPlanRecord> _plans = const <TrainingPlanRecord>[];
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
      final List<Object> result = await Future.wait<Object>(<Future<Object>>[
        _templates.fetchTemplates(),
        _data.fetchStudents(),
        _data.fetchTrainingPlans(),
      ]);

      if (!mounted) return;
      setState(() {
        _items = result[0] as List<TrainingTemplateRecord>;
        _students = result[1] as List<StudentRecord>;
        _plans = result[2] as List<TrainingPlanRecord>;
      });
    } catch (error) {
      if (!mounted) return;
      setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _createTemplate() async {
    final _TemplateInput? input = await showDialog<_TemplateInput>(
      context: context,
      barrierColor: Colors.black.withValues(alpha: 0.72),
      builder: (_) => const _TemplateDialog(),
    );

    if (input == null || !mounted) return;

    try {
      await _templates.createTemplate(
        name: input.name,
        objective: input.objective,
        level: input.level,
        notes: input.notes,
        exercises: input.exercises,
      );
      await _reload();
      if (!mounted) return;
      _toast('Modelo ${input.name} criado e pronto para reutilizar.');
    } catch (error) {
      if (!mounted) return;
      _toast('Não foi possível criar o modelo: $error', error: true);
    }
  }

  Future<void> _assignTemplate(TrainingTemplateRecord template) async {
    if (_students.isEmpty) {
      _toast('Cadastre um aluno antes de aplicar um modelo.');
      return;
    }

    final _AssignmentInput? input = await showDialog<_AssignmentInput>(
      context: context,
      barrierColor: Colors.black.withValues(alpha: 0.72),
      builder: (_) => _AssignmentDialog(
        template: template,
        students: _students,
      ),
    );

    if (input == null || !mounted) return;

    try {
      await _templates.assignTemplate(
        templateId: template.id,
        studentId: input.studentId,
        nextSession: input.nextSession,
      );
      await _reload();
      if (!mounted) return;
      final String studentName = _studentName(input.studentId);
      _toast('${template.name} aplicado para $studentName.');
    } catch (error) {
      if (!mounted) return;
      _toast('Não foi possível aplicar o modelo: $error', error: true);
    }
  }

  Future<void> _createFromPlan() async {
    if (_plans.isEmpty) {
      _toast('Crie um treino antes de transformá-lo em modelo.');
      return;
    }

    final _PlanTemplateInput? input = await showDialog<_PlanTemplateInput>(
      context: context,
      barrierColor: Colors.black.withValues(alpha: 0.72),
      builder: (_) => _PlanTemplateDialog(
        plans: _plans,
        students: _students,
      ),
    );

    if (input == null || !mounted) return;

    try {
      await _templates.createFromPlan(
        planId: input.planId,
        name: input.name,
      );
      await _reload();
      if (!mounted) return;
      _toast('Treino salvo como modelo inteligente.');
    } catch (error) {
      if (!mounted) return;
      _toast('Não foi possível salvar o treino como modelo: $error', error: true);
    }
  }

  String _studentName(String id) {
    for (final StudentRecord student in _students) {
      if (student.id == id) return student.name;
    }
    return 'Aluno';
  }

  void _toast(String message, {bool error = false}) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        behavior: SnackBarBehavior.floating,
        backgroundColor: error ? const Color(0xFF5A1919) : _TemplateColors.card,
        content: Text(message),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _TemplateColors.black,
      body: SafeArea(
        child: RefreshIndicator(
          color: _TemplateColors.gold,
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
                    _Header(
                      loading: _loading,
                      onRefresh: _reload,
                      onCreate: _createTemplate,
                      onCreateFromPlan: _createFromPlan,
                    ),
                    const SizedBox(height: 22),
                    if (_error != null)
                      _ErrorPanel(message: _error!, onRetry: _reload)
                    else if (_loading && _items.isEmpty)
                      const _LoadingPanel()
                    else if (_items.isEmpty)
                      _EmptyTemplates(onCreate: _createTemplate)
                    else
                      _TemplateGrid(
                        templates: _items,
                        onAssign: _assignTemplate,
                      ),
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
  const _Header({
    required this.loading,
    required this.onRefresh,
    required this.onCreate,
    required this.onCreateFromPlan,
  });

  final bool loading;
  final Future<void> Function() onRefresh;
  final VoidCallback onCreate;
  final VoidCallback onCreateFromPlan;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(26),
      decoration: BoxDecoration(
        color: _TemplateColors.card,
        borderRadius: BorderRadius.circular(26),
        border: Border.all(color: _TemplateColors.border),
      ),
      child: LayoutBuilder(
        builder: (BuildContext context, BoxConstraints constraints) {
          final Widget copy = const Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(
                'SMART TEMPLATES',
                style: TextStyle(
                  color: _TemplateColors.goldSoft,
                  fontWeight: FontWeight.w900,
                  letterSpacing: 1.1,
                  fontSize: 12,
                ),
              ),
              SizedBox(height: 9),
              Text(
                'Prescreva rápido sem transformar o treino em receita cega.',
                style: TextStyle(
                  color: _TemplateColors.text,
                  fontWeight: FontWeight.w900,
                  fontSize: 28,
                  height: 1.1,
                ),
              ),
              SizedBox(height: 8),
              Text(
                'Crie modelos reutilizáveis ou transforme um treino já validado em template. Ao aplicar, o FitNexus cria um novo treino individual e preserva o histórico anterior.',
                style: TextStyle(
                  color: _TemplateColors.muted,
                  height: 1.45,
                ),
              ),
            ],
          );

          final Widget actions = Wrap(
            spacing: 10,
            runSpacing: 10,
            children: <Widget>[
              FilledButton.icon(
                onPressed: onCreate,
                icon: const Icon(Icons.add_rounded),
                label: const Text('Novo modelo'),
                style: FilledButton.styleFrom(
                  backgroundColor: _TemplateColors.gold,
                  foregroundColor: Colors.black,
                  padding:
                      const EdgeInsets.symmetric(horizontal: 18, vertical: 15),
                  textStyle: const TextStyle(fontWeight: FontWeight.w900),
                ),
              ),
              OutlinedButton.icon(
                onPressed: onCreateFromPlan,
                icon: const Icon(Icons.bookmark_add_rounded),
                label: const Text('Salvar treino como modelo'),
                style: OutlinedButton.styleFrom(
                  foregroundColor: _TemplateColors.text,
                  side: const BorderSide(color: _TemplateColors.border),
                  padding:
                      const EdgeInsets.symmetric(horizontal: 18, vertical: 15),
                ),
              ),
              IconButton.filledTonal(
                tooltip: 'Atualizar modelos',
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

          if (constraints.maxWidth < 820) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                copy,
                const SizedBox(height: 20),
                actions,
              ],
            );
          }

          return Row(
            children: <Widget>[
              Expanded(child: copy),
              const SizedBox(width: 24),
              actions,
            ],
          );
        },
      ),
    );
  }
}

class _TemplateGrid extends StatelessWidget {
  const _TemplateGrid({
    required this.templates,
    required this.onAssign,
  });

  final List<TrainingTemplateRecord> templates;
  final Future<void> Function(TrainingTemplateRecord template) onAssign;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (BuildContext context, BoxConstraints constraints) {
        final int columns = constraints.maxWidth >= 1120
            ? 3
            : constraints.maxWidth >= 700
                ? 2
                : 1;
        const double gap = 14;
        final double width =
            (constraints.maxWidth - gap * (columns - 1)) / columns;

        return Wrap(
          spacing: gap,
          runSpacing: gap,
          children: templates
              .map(
                (TrainingTemplateRecord template) => SizedBox(
                  width: width,
                  child: _TemplateCard(
                    template: template,
                    onAssign: () => onAssign(template),
                  ),
                ),
              )
              .toList(growable: false),
        );
      },
    );
  }
}

class _TemplateCard extends StatelessWidget {
  const _TemplateCard({required this.template, required this.onAssign});

  final TrainingTemplateRecord template;
  final VoidCallback onAssign;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: _TemplateColors.card,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: _TemplateColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            children: <Widget>[
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: _TemplateColors.gold.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(13),
                ),
                child: const Icon(
                  Icons.auto_awesome_rounded,
                  color: _TemplateColors.goldSoft,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      template.name,
                      style: const TextStyle(
                        color: _TemplateColors.text,
                        fontWeight: FontWeight.w900,
                        fontSize: 18,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      '${template.objective} • ${template.level}',
                      style: const TextStyle(
                        color: _TemplateColors.muted,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          ...template.exercises.take(5).map(
                (TrainingTemplateExerciseRecord exercise) => Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      const Icon(
                        Icons.check_circle_outline_rounded,
                        color: _TemplateColors.goldSoft,
                        size: 16,
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          exercise.prescription.isEmpty
                              ? exercise.name
                              : '${exercise.name} — ${exercise.prescription}',
                          style: const TextStyle(
                            color: _TemplateColors.muted,
                            fontSize: 12,
                            height: 1.35,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
          if (template.exercises.length > 5)
            Text(
              '+ ${template.exercises.length - 5} exercícios',
              style: const TextStyle(
                color: _TemplateColors.goldSoft,
                fontSize: 11,
                fontWeight: FontWeight.w800,
              ),
            ),
          if ((template.notes ?? '').isNotEmpty) ...<Widget>[
            const SizedBox(height: 10),
            Text(
              template.notes!,
              maxLines: 3,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                color: _TemplateColors.muted,
                fontSize: 11,
                height: 1.35,
              ),
            ),
          ],
          const SizedBox(height: 18),
          SizedBox(
            width: double.infinity,
            child: FilledButton.icon(
              onPressed: onAssign,
              icon: const Icon(Icons.person_add_alt_1_rounded),
              label: const Text('Aplicar a um aluno'),
              style: FilledButton.styleFrom(
                backgroundColor: _TemplateColors.gold,
                foregroundColor: Colors.black,
                textStyle: const TextStyle(fontWeight: FontWeight.w900),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _EmptyTemplates extends StatelessWidget {
  const _EmptyTemplates({required this.onCreate});

  final VoidCallback onCreate;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 55, horizontal: 20),
      decoration: BoxDecoration(
        color: _TemplateColors.card,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: _TemplateColors.border),
      ),
      child: Column(
        children: <Widget>[
          const Icon(
            Icons.auto_awesome_rounded,
            color: _TemplateColors.goldSoft,
            size: 46,
          ),
          const SizedBox(height: 14),
          const Text(
            'Nenhum modelo criado ainda',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: _TemplateColors.text,
              fontSize: 20,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 7),
          const Text(
            'Transforme seus melhores treinos em uma biblioteca reutilizável sem perder a individualização do aluno.',
            textAlign: TextAlign.center,
            style: TextStyle(color: _TemplateColors.muted, height: 1.4),
          ),
          const SizedBox(height: 18),
          FilledButton.icon(
            onPressed: onCreate,
            icon: const Icon(Icons.add_rounded),
            label: const Text('Criar primeiro modelo'),
          ),
        ],
      ),
    );
  }
}

class _TemplateInput {
  const _TemplateInput({
    required this.name,
    required this.objective,
    required this.level,
    required this.notes,
    required this.exercises,
  });

  final String name;
  final String objective;
  final String level;
  final String notes;
  final List<TrainingExerciseDraft> exercises;
}

class _TemplateDialog extends StatefulWidget {
  const _TemplateDialog();

  @override
  State<_TemplateDialog> createState() => _TemplateDialogState();
}

class _TemplateDialogState extends State<_TemplateDialog> {
  final GlobalKey<FormState> _formKey = GlobalKey<FormState>();
  final TextEditingController _name = TextEditingController();
  final TextEditingController _objective =
      TextEditingController(text: 'Hipertrofia');
  final TextEditingController _level = TextEditingController(text: 'Iniciante');
  final TextEditingController _notes = TextEditingController();
  final TextEditingController _exercises = TextEditingController(
    text: 'Agachamento livre | 4x10 • descanso 90s\nSupino reto | 3x10 • descanso 75s\nRemada baixa | 3x12 • descanso 60s',
  );

  @override
  void dispose() {
    _name.dispose();
    _objective.dispose();
    _level.dispose();
    _notes.dispose();
    _exercises.dispose();
    super.dispose();
  }

  List<TrainingExerciseDraft> _parseExercises() {
    return _exercises.text
        .split('\n')
        .map((String line) => line.trim())
        .where((String line) => line.isNotEmpty)
        .map((String line) {
          final List<String> parts = line.split('|');
          return TrainingExerciseDraft(
            name: parts.first.trim(),
            prescription:
                parts.length > 1 ? parts.sublist(1).join('|').trim() : '',
          );
        })
        .toList(growable: false);
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      backgroundColor: _TemplateColors.card,
      title: const Text('Novo Smart Template'),
      content: SizedBox(
        width: 620,
        child: Form(
          key: _formKey,
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                _Field(controller: _name, label: 'Nome do modelo *', validator: _required),
                const SizedBox(height: 10),
                _Field(controller: _objective, label: 'Objetivo *', validator: _required),
                const SizedBox(height: 10),
                _Field(controller: _level, label: 'Nível *', validator: _required),
                const SizedBox(height: 10),
                _Field(controller: _notes, label: 'Orientações do modelo', maxLines: 2),
                const SizedBox(height: 10),
                _Field(
                  controller: _exercises,
                  label: 'Exercícios — nome | prescrição *',
                  maxLines: 8,
                  validator: (String? value) {
                    if (value == null || value.trim().isEmpty) {
                      return 'Informe pelo menos um exercício.';
                    }
                    if (_parseExercises().any(
                      (TrainingExerciseDraft item) => item.name.length < 2,
                    )) {
                      return 'Revise os nomes dos exercícios.';
                    }
                    return null;
                  },
                ),
              ],
            ),
          ),
        ),
      ),
      actions: <Widget>[
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Cancelar'),
        ),
        FilledButton(
          onPressed: () {
            if (!(_formKey.currentState?.validate() ?? false)) return;
            Navigator.pop(
              context,
              _TemplateInput(
                name: _name.text.trim(),
                objective: _objective.text.trim(),
                level: _level.text.trim(),
                notes: _notes.text.trim(),
                exercises: _parseExercises(),
              ),
            );
          },
          child: const Text('Criar modelo'),
        ),
      ],
    );
  }

  String? _required(String? value) {
    return value == null || value.trim().isEmpty ? 'Campo obrigatório.' : null;
  }
}

class _AssignmentInput {
  const _AssignmentInput({required this.studentId, required this.nextSession});

  final String studentId;
  final String nextSession;
}

class _AssignmentDialog extends StatefulWidget {
  const _AssignmentDialog({required this.template, required this.students});

  final TrainingTemplateRecord template;
  final List<StudentRecord> students;

  @override
  State<_AssignmentDialog> createState() => _AssignmentDialogState();
}

class _AssignmentDialogState extends State<_AssignmentDialog> {
  late String _studentId = widget.students.first.id;
  final TextEditingController _next = TextEditingController();

  @override
  void dispose() {
    _next.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      backgroundColor: _TemplateColors.card,
      title: Text('Aplicar ${widget.template.name}'),
      content: SizedBox(
        width: 520,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            DropdownButtonFormField<String>(
              initialValue: _studentId,
              dropdownColor: _TemplateColors.card,
              decoration: const InputDecoration(labelText: 'Aluno'),
              items: widget.students
                  .map(
                    (StudentRecord student) => DropdownMenuItem<String>(
                      value: student.id,
                      child: Text(student.name),
                    ),
                  )
                  .toList(growable: false),
              onChanged: (String? value) {
                if (value != null) setState(() => _studentId = value);
              },
            ),
            const SizedBox(height: 12),
            _Field(controller: _next, label: 'Próxima sessão'),
            const SizedBox(height: 12),
            const Text(
              'O treino ativo anterior será preservado no histórico e este modelo criará uma nova prescrição individual.',
              style: TextStyle(color: _TemplateColors.muted, height: 1.4),
            ),
          ],
        ),
      ),
      actions: <Widget>[
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Cancelar'),
        ),
        FilledButton(
          onPressed: () => Navigator.pop(
            context,
            _AssignmentInput(
              studentId: _studentId,
              nextSession: _next.text.trim(),
            ),
          ),
          child: const Text('Aplicar modelo'),
        ),
      ],
    );
  }
}

class _PlanTemplateInput {
  const _PlanTemplateInput({required this.planId, required this.name});

  final String planId;
  final String name;
}

class _PlanTemplateDialog extends StatefulWidget {
  const _PlanTemplateDialog({required this.plans, required this.students});

  final List<TrainingPlanRecord> plans;
  final List<StudentRecord> students;

  @override
  State<_PlanTemplateDialog> createState() => _PlanTemplateDialogState();
}

class _PlanTemplateDialogState extends State<_PlanTemplateDialog> {
  late String _planId = widget.plans.first.id;
  final TextEditingController _name = TextEditingController();

  @override
  void dispose() {
    _name.dispose();
    super.dispose();
  }

  String _studentName(String id) {
    for (final StudentRecord student in widget.students) {
      if (student.id == id) return student.name;
    }
    return 'Aluno';
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      backgroundColor: _TemplateColors.card,
      title: const Text('Salvar treino como modelo'),
      content: SizedBox(
        width: 560,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            DropdownButtonFormField<String>(
              initialValue: _planId,
              dropdownColor: _TemplateColors.card,
              decoration: const InputDecoration(labelText: 'Treino existente'),
              items: widget.plans
                  .map(
                    (TrainingPlanRecord plan) => DropdownMenuItem<String>(
                      value: plan.id,
                      child: Text('${plan.name} — ${_studentName(plan.studentId)}'),
                    ),
                  )
                  .toList(growable: false),
              onChanged: (String? value) {
                if (value != null) setState(() => _planId = value);
              },
            ),
            const SizedBox(height: 12),
            _Field(
              controller: _name,
              label: 'Novo nome do modelo (opcional)',
            ),
          ],
        ),
      ),
      actions: <Widget>[
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Cancelar'),
        ),
        FilledButton(
          onPressed: () => Navigator.pop(
            context,
            _PlanTemplateInput(
              planId: _planId,
              name: _name.text.trim(),
            ),
          ),
          child: const Text('Salvar modelo'),
        ),
      ],
    );
  }
}

class _Field extends StatelessWidget {
  const _Field({
    required this.controller,
    required this.label,
    this.validator,
    this.maxLines = 1,
  });

  final TextEditingController controller;
  final String label;
  final String? Function(String?)? validator;
  final int maxLines;

  @override
  Widget build(BuildContext context) {
    return TextFormField(
      controller: controller,
      validator: validator,
      maxLines: maxLines,
      style: const TextStyle(color: _TemplateColors.text),
      decoration: InputDecoration(
        labelText: label,
        filled: true,
        fillColor: _TemplateColors.cardSoft,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(14)),
      ),
    );
  }
}

class _LoadingPanel extends StatelessWidget {
  const _LoadingPanel();

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.all(50),
      child: Center(
        child: CircularProgressIndicator(color: _TemplateColors.gold),
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
              style: const TextStyle(color: _TemplateColors.text),
            ),
          ),
          TextButton(onPressed: onRetry, child: const Text('Tentar novamente')),
        ],
      ),
    );
  }
}

class _TemplateColors {
  static const Color black = Color(0xFF050505);
  static const Color card = Color(0xFF101010);
  static const Color cardSoft = Color(0xFF171717);
  static const Color border = Color(0xFF2C2A22);
  static const Color gold = Color(0xFFE1B92F);
  static const Color goldSoft = Color(0xFFFFD45A);
  static const Color text = Color(0xFFF7F7F7);
  static const Color muted = Color(0xFFB7B7B7);
}
