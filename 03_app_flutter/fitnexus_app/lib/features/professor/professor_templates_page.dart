import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/blackgold_tokens.dart';
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
      barrierColor: Colors.black.withValues(alpha: 0.78),
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
      barrierColor: Colors.black.withValues(alpha: 0.78),
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
      _toast('${template.name} aplicado para ${_studentName(input.studentId)}.');
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
      barrierColor: Colors.black.withValues(alpha: 0.78),
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
        backgroundColor: error
            ? AppColors.danger.withValues(alpha: 0.24)
            : AppColors.cardRaised,
        content: Text(message),
      ),
    );
  }

  int get _exerciseCount => _items.fold<int>(
        0,
        (int total, TrainingTemplateRecord item) =>
            total + item.exercises.length,
      );

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.black,
      body: Stack(
        children: <Widget>[
          const Positioned.fill(child: _PageAtmosphere()),
          SafeArea(
            child: RefreshIndicator(
              color: AppColors.gold,
              onRefresh: _reload,
              child: SingleChildScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.fromLTRB(
                  BlackGoldSpace.lg,
                  BlackGoldSpace.xl,
                  BlackGoldSpace.lg,
                  132,
                ),
                child: Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 1420),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: <Widget>[
                        _HeroHeader(
                          loading: _loading,
                          onRefresh: _reload,
                          onCreate: _createTemplate,
                          onCreateFromPlan: _createFromPlan,
                        ),
                        const SizedBox(height: BlackGoldSpace.lg),
                        _LibrarySummary(
                          templates: _items.length,
                          exercises: _exerciseCount,
                          students: _students.length,
                          activePlans: _plans.where((plan) => plan.isActive).length,
                        ),
                        const SizedBox(height: BlackGoldSpace.lg),
                        if (_error != null)
                          _ErrorPanel(message: _error!, onRetry: _reload)
                        else if (_loading && _items.isEmpty)
                          const _LoadingPanel()
                        else if (_items.isEmpty)
                          _EmptyTemplates(onCreate: _createTemplate)
                        else ...<Widget>[
                          const _SectionHeading(
                            eyebrow: 'BIBLIOTECA PROFISSIONAL',
                            title: 'Modelos prontos para individualizar',
                            subtitle:
                                'Reutilize a estrutura, preserve a decisão do professor e gere uma nova prescrição para cada aluno.',
                          ),
                          const SizedBox(height: BlackGoldSpace.md),
                          _TemplateGrid(
                            templates: _items,
                            onAssign: _assignTemplate,
                          ),
                        ],
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _PageAtmosphere extends StatelessWidget {
  const _PageAtmosphere();

  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      child: DecoratedBox(
        decoration: BoxDecoration(
          gradient: RadialGradient(
            center: const Alignment(0.82, -0.92),
            radius: 1.15,
            colors: <Color>[
              AppColors.gold.withValues(alpha: 0.08),
              Colors.transparent,
            ],
          ),
        ),
      ),
    );
  }
}

class _HeroHeader extends StatelessWidget {
  const _HeroHeader({
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
      padding: const EdgeInsets.all(BlackGoldSpace.xl),
      decoration: BoxDecoration(
        gradient: BlackGoldEffects.panelGradient,
        borderRadius: BorderRadius.circular(BlackGoldRadius.hero),
        border: Border.all(
          color: AppColors.borderGold,
          width: BlackGoldStroke.hairline,
        ),
        boxShadow: BlackGoldEffects.cardShadow,
      ),
      child: LayoutBuilder(
        builder: (BuildContext context, BoxConstraints constraints) {
          final bool compact = constraints.maxWidth < BlackGoldBreakpoints.tablet;

          final Widget copy = Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Row(
                children: <Widget>[
                  Container(
                    width: 46,
                    height: 46,
                    decoration: BoxDecoration(
                      gradient: BlackGoldEffects.goldGradient,
                      borderRadius:
                          BorderRadius.circular(BlackGoldRadius.card),
                      boxShadow: BlackGoldEffects.goldGlow,
                    ),
                    child: const Icon(
                      Icons.auto_awesome_rounded,
                      color: Colors.black,
                    ),
                  ),
                  const SizedBox(width: BlackGoldSpace.md),
                  const Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text(
                          'SMART TEMPLATES',
                          style: TextStyle(
                            color: AppColors.goldSoft,
                            fontSize: 12,
                            fontWeight: FontWeight.w900,
                            letterSpacing: 1.25,
                          ),
                        ),
                        SizedBox(height: BlackGoldSpace.xs),
                        Text(
                          'Biblioteca inteligente de prescrição',
                          style: TextStyle(
                            color: AppColors.text,
                            fontSize: 30,
                            height: 1.05,
                            fontWeight: FontWeight.w900,
                            letterSpacing: -0.7,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: BlackGoldSpace.md),
              const Text(
                'Transforme treinos já validados em modelos reutilizáveis, aplique com contexto e mantenha o histórico individual do aluno intacto.',
                style: TextStyle(
                  color: AppColors.muted,
                  height: 1.5,
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                ),
              ),
              const SizedBox(height: BlackGoldSpace.md),
              const _PrincipleStrip(),
            ],
          );

          final Widget actions = Wrap(
            spacing: BlackGoldSpace.sm,
            runSpacing: BlackGoldSpace.sm,
            children: <Widget>[
              FilledButton.icon(
                key: const ValueKey<String>('templates-create-primary'),
                onPressed: onCreate,
                icon: const Icon(Icons.add_rounded),
                label: const Text('Novo modelo'),
              ),
              OutlinedButton.icon(
                key: const ValueKey<String>('templates-create-from-plan'),
                onPressed: onCreateFromPlan,
                icon: const Icon(Icons.bookmark_add_rounded),
                label: const Text('Salvar treino como modelo'),
              ),
              IconButton.outlined(
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

          if (compact) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: <Widget>[
                copy,
                const SizedBox(height: BlackGoldSpace.lg),
                actions,
              ],
            );
          }

          return Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: <Widget>[
              Expanded(flex: 7, child: copy),
              const SizedBox(width: BlackGoldSpace.xxl),
              Flexible(flex: 5, child: actions),
            ],
          );
        },
      ),
    );
  }
}

class _PrincipleStrip extends StatelessWidget {
  const _PrincipleStrip();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: BlackGoldSpace.md,
        vertical: BlackGoldSpace.sm,
      ),
      decoration: BoxDecoration(
        color: AppColors.gold.withValues(alpha: 0.07),
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
              'O modelo acelera o trabalho; a decisão final continua sendo do professor.',
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

class _LibrarySummary extends StatelessWidget {
  const _LibrarySummary({
    required this.templates,
    required this.exercises,
    required this.students,
    required this.activePlans,
  });

  final int templates;
  final int exercises;
  final int students;
  final int activePlans;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (BuildContext context, BoxConstraints constraints) {
        final int columns = constraints.maxWidth >= 1040
            ? 4
            : constraints.maxWidth >= BlackGoldBreakpoints.mobile
                ? 2
                : 1;
        const double gap = BlackGoldSpace.sm;
        final double width =
            (constraints.maxWidth - (gap * (columns - 1))) / columns;

        final List<_MetricData> metrics = <_MetricData>[
          _MetricData(Icons.auto_awesome_rounded, '$templates', 'Modelos', 'na biblioteca'),
          _MetricData(Icons.fitness_center_rounded, '$exercises', 'Exercícios', 'catalogados'),
          _MetricData(Icons.groups_rounded, '$students', 'Alunos', 'disponíveis'),
          _MetricData(Icons.assignment_turned_in_rounded, '$activePlans', 'Treinos ativos', 'em acompanhamento'),
        ];

        return Wrap(
          spacing: gap,
          runSpacing: gap,
          children: metrics
              .map((metric) => SizedBox(width: width, child: _MetricCard(data: metric)))
              .toList(growable: false),
        );
      },
    );
  }
}

class _MetricData {
  const _MetricData(this.icon, this.value, this.label, this.caption);

  final IconData icon;
  final String value;
  final String label;
  final String caption;
}

class _MetricCard extends StatelessWidget {
  const _MetricCard({required this.data});

  final _MetricData data;

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
              color: AppColors.gold.withValues(alpha: 0.10),
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
                    fontSize: 24,
                    height: 1,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const SizedBox(height: BlackGoldSpace.xxs),
                Text(
                  data.label,
                  style: const TextStyle(
                    color: AppColors.goldSoft,
                    fontSize: 12,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  data.caption,
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
            letterSpacing: 1.2,
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
        const double gap = BlackGoldSpace.sm;
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
      padding: const EdgeInsets.all(BlackGoldSpace.lg),
      decoration: BoxDecoration(
        gradient: BlackGoldEffects.panelGradient,
        borderRadius: BorderRadius.circular(BlackGoldRadius.panel),
        border: Border.all(color: AppColors.borderGold),
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
                  gradient: BlackGoldEffects.goldGradient,
                  borderRadius: BorderRadius.circular(BlackGoldRadius.card),
                  boxShadow: BlackGoldEffects.goldGlow,
                ),
                child: const Icon(
                  Icons.auto_awesome_rounded,
                  color: Colors.black,
                ),
              ),
              const SizedBox(width: BlackGoldSpace.sm),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      template.name,
                      style: const TextStyle(
                        color: AppColors.text,
                        fontWeight: FontWeight.w900,
                        fontSize: 18,
                        height: 1.12,
                      ),
                    ),
                    const SizedBox(height: BlackGoldSpace.xxs),
                    Text(
                      '${template.objective} • ${template.level}',
                      style: const TextStyle(
                        color: AppColors.muted,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ),
              _CountPill(count: template.exercises.length),
            ],
          ),
          const SizedBox(height: BlackGoldSpace.md),
          const Divider(height: 1),
          const SizedBox(height: BlackGoldSpace.md),
          ...template.exercises.take(5).map(
                (TrainingTemplateExerciseRecord exercise) => Padding(
                  padding: const EdgeInsets.only(bottom: BlackGoldSpace.xs),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      const Padding(
                        padding: EdgeInsets.only(top: 1),
                        child: Icon(
                          Icons.check_circle_outline_rounded,
                          color: AppColors.goldSoft,
                          size: 16,
                        ),
                      ),
                      const SizedBox(width: BlackGoldSpace.xs),
                      Expanded(
                        child: Text(
                          exercise.prescription.isEmpty
                              ? exercise.name
                              : '${exercise.name} — ${exercise.prescription}',
                          style: const TextStyle(
                            color: AppColors.muted,
                            fontSize: 12,
                            height: 1.4,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
          if (template.exercises.length > 5)
            Text(
              '+ ${template.exercises.length - 5} exercícios adicionais',
              style: const TextStyle(
                color: AppColors.goldSoft,
                fontSize: 11,
                fontWeight: FontWeight.w800,
              ),
            ),
          if ((template.notes ?? '').trim().isNotEmpty) ...<Widget>[
            const SizedBox(height: BlackGoldSpace.sm),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(BlackGoldSpace.sm),
              decoration: BoxDecoration(
                color: AppColors.blackSoft,
                borderRadius: BorderRadius.circular(BlackGoldRadius.control),
                border: Border.all(color: AppColors.border),
              ),
              child: Text(
                template.notes!,
                maxLines: 3,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  color: AppColors.muted,
                  fontSize: 11,
                  height: 1.4,
                ),
              ),
            ),
          ],
          const SizedBox(height: BlackGoldSpace.lg),
          SizedBox(
            width: double.infinity,
            child: FilledButton.icon(
              onPressed: onAssign,
              icon: const Icon(Icons.person_add_alt_1_rounded),
              label: const Text('Aplicar a um aluno'),
            ),
          ),
        ],
      ),
    );
  }
}

class _CountPill extends StatelessWidget {
  const _CountPill({required this.count});

  final int count;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 6),
      decoration: BoxDecoration(
        color: AppColors.gold.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(BlackGoldRadius.pill),
        border: Border.all(color: AppColors.border),
      ),
      child: Text(
        '$count EX.',
        style: const TextStyle(
          color: AppColors.goldSoft,
          fontSize: 10,
          fontWeight: FontWeight.w900,
          letterSpacing: 0.5,
        ),
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
      padding: const EdgeInsets.symmetric(
        vertical: BlackGoldSpace.section,
        horizontal: BlackGoldSpace.lg,
      ),
      decoration: BoxDecoration(
        gradient: BlackGoldEffects.panelGradient,
        borderRadius: BorderRadius.circular(BlackGoldRadius.panel),
        border: Border.all(color: AppColors.borderGold),
        boxShadow: BlackGoldEffects.cardShadow,
      ),
      child: Column(
        children: <Widget>[
          Container(
            width: 58,
            height: 58,
            decoration: BoxDecoration(
              gradient: BlackGoldEffects.goldGradient,
              borderRadius: BorderRadius.circular(BlackGoldRadius.panel),
              boxShadow: BlackGoldEffects.goldGlow,
            ),
            child: const Icon(
              Icons.auto_awesome_rounded,
              color: Colors.black,
              size: 30,
            ),
          ),
          const SizedBox(height: BlackGoldSpace.md),
          const Text(
            'Nenhum modelo criado ainda',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: AppColors.text,
              fontSize: 21,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: BlackGoldSpace.xs),
          ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 620),
            child: const Text(
              'Transforme seus melhores treinos em uma biblioteca reutilizável sem perder a individualização do aluno.',
              textAlign: TextAlign.center,
              style: TextStyle(color: AppColors.muted, height: 1.45),
            ),
          ),
          const SizedBox(height: BlackGoldSpace.lg),
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
      title: const _DialogTitle(
        icon: Icons.auto_awesome_rounded,
        eyebrow: 'SMART TEMPLATE',
        title: 'Novo modelo profissional',
      ),
      content: SizedBox(
        width: 650,
        child: Form(
          key: _formKey,
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                _Field(
                  controller: _name,
                  label: 'Nome do modelo *',
                  validator: _required,
                ),
                const SizedBox(height: BlackGoldSpace.sm),
                _Field(
                  controller: _objective,
                  label: 'Objetivo *',
                  validator: _required,
                ),
                const SizedBox(height: BlackGoldSpace.sm),
                _Field(
                  controller: _level,
                  label: 'Nível *',
                  validator: _required,
                ),
                const SizedBox(height: BlackGoldSpace.sm),
                _Field(
                  controller: _notes,
                  label: 'Orientações do modelo',
                  maxLines: 2,
                ),
                const SizedBox(height: BlackGoldSpace.sm),
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
        FilledButton.icon(
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
          icon: const Icon(Icons.check_rounded),
          label: const Text('Criar modelo'),
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
      title: _DialogTitle(
        icon: Icons.person_add_alt_1_rounded,
        eyebrow: 'INDIVIDUALIZAÇÃO',
        title: 'Aplicar ${widget.template.name}',
      ),
      content: SizedBox(
        width: 540,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            DropdownButtonFormField<String>(
              initialValue: _studentId,
              dropdownColor: AppColors.cardRaised,
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
            const SizedBox(height: BlackGoldSpace.sm),
            _Field(controller: _next, label: 'Próxima sessão'),
            const SizedBox(height: BlackGoldSpace.md),
            const _SafetyNote(
              text:
                  'O treino ativo anterior será preservado no histórico. Este modelo cria uma nova prescrição individual para o aluno selecionado.',
            ),
          ],
        ),
      ),
      actions: <Widget>[
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Cancelar'),
        ),
        FilledButton.icon(
          onPressed: () => Navigator.pop(
            context,
            _AssignmentInput(
              studentId: _studentId,
              nextSession: _next.text.trim(),
            ),
          ),
          icon: const Icon(Icons.person_add_alt_1_rounded),
          label: const Text('Aplicar modelo'),
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
      title: const _DialogTitle(
        icon: Icons.bookmark_add_rounded,
        eyebrow: 'REAPROVEITAR COM CONTROLE',
        title: 'Salvar treino como modelo',
      ),
      content: SizedBox(
        width: 590,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            DropdownButtonFormField<String>(
              initialValue: _planId,
              dropdownColor: AppColors.cardRaised,
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
            const SizedBox(height: BlackGoldSpace.sm),
            _Field(
              controller: _name,
              label: 'Novo nome do modelo (opcional)',
            ),
            const SizedBox(height: BlackGoldSpace.md),
            const _SafetyNote(
              text:
                  'A cópia vira um modelo reutilizável; o treino original e seu histórico continuam preservados.',
            ),
          ],
        ),
      ),
      actions: <Widget>[
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Cancelar'),
        ),
        FilledButton.icon(
          onPressed: () => Navigator.pop(
            context,
            _PlanTemplateInput(
              planId: _planId,
              name: _name.text.trim(),
            ),
          ),
          icon: const Icon(Icons.bookmark_added_rounded),
          label: const Text('Salvar modelo'),
        ),
      ],
    );
  }
}

class _DialogTitle extends StatelessWidget {
  const _DialogTitle({
    required this.icon,
    required this.eyebrow,
    required this.title,
  });

  final IconData icon;
  final String eyebrow;
  final String title;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Container(
          width: 42,
          height: 42,
          decoration: BoxDecoration(
            gradient: BlackGoldEffects.goldGradient,
            borderRadius: BorderRadius.circular(BlackGoldRadius.card),
          ),
          child: Icon(icon, color: Colors.black, size: 21),
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
                  letterSpacing: 1,
                ),
              ),
              const SizedBox(height: BlackGoldSpace.xxs),
              Text(
                title,
                style: const TextStyle(
                  color: AppColors.text,
                  fontSize: 20,
                  fontWeight: FontWeight.w900,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _SafetyNote extends StatelessWidget {
  const _SafetyNote({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(BlackGoldSpace.sm),
      decoration: BoxDecoration(
        color: AppColors.gold.withValues(alpha: 0.07),
        borderRadius: BorderRadius.circular(BlackGoldRadius.control),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const Icon(Icons.shield_outlined, color: AppColors.goldSoft, size: 18),
          const SizedBox(width: BlackGoldSpace.sm),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(
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
      style: const TextStyle(color: AppColors.text),
      decoration: InputDecoration(labelText: label),
    );
  }
}

class _LoadingPanel extends StatelessWidget {
  const _LoadingPanel();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(BlackGoldSpace.section),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(BlackGoldRadius.panel),
        border: Border.all(color: AppColors.border),
      ),
      child: const Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            CircularProgressIndicator(color: AppColors.gold),
            SizedBox(height: BlackGoldSpace.md),
            Text(
              'Atualizando biblioteca inteligente…',
              style: TextStyle(color: AppColors.muted),
            ),
          ],
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
      padding: const EdgeInsets.all(BlackGoldSpace.md),
      decoration: BoxDecoration(
        color: AppColors.danger.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(BlackGoldRadius.panel),
        border: Border.all(color: AppColors.danger.withValues(alpha: 0.48)),
      ),
      child: LayoutBuilder(
        builder: (BuildContext context, BoxConstraints constraints) {
          final Widget messageBlock = Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              const Icon(Icons.error_outline_rounded, color: AppColors.danger),
              const SizedBox(width: BlackGoldSpace.sm),
              Expanded(
                child: Text(
                  message,
                  style: const TextStyle(color: AppColors.text, height: 1.4),
                ),
              ),
            ],
          );

          final Widget action = TextButton.icon(
            onPressed: onRetry,
            icon: const Icon(Icons.refresh_rounded),
            label: const Text('Tentar novamente'),
          );

          if (constraints.maxWidth < BlackGoldBreakpoints.mobile) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: <Widget>[
                messageBlock,
                const SizedBox(height: BlackGoldSpace.sm),
                action,
              ],
            );
          }

          return Row(
            children: <Widget>[
              Expanded(child: messageBlock),
              const SizedBox(width: BlackGoldSpace.md),
              action,
            ],
          );
        },
      ),
    );
  }
}
