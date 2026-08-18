import 'package:flutter/material.dart';

import '../auth/auth_service.dart';
import 'professor_data_repository.dart';

class ProfessorLiveDashboardPage extends StatefulWidget {
  const ProfessorLiveDashboardPage({super.key});

  @override
  State<ProfessorLiveDashboardPage> createState() => _ProfessorLiveDashboardPageState();
}

class _ProfessorLiveDashboardPageState extends State<ProfessorLiveDashboardPage> {
  final ProfessorDataRepository _repository = ProfessorDataRepository.instance;

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
        _repository.fetchStudents(),
        _repository.fetchTrainingPlans(),
      ]);

      if (!mounted) return;
      setState(() {
        _students = result[0] as List<StudentRecord>;
        _plans = result[1] as List<TrainingPlanRecord>;
      });
    } catch (error) {
      if (!mounted) return;
      setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _createStudent() async {
    final _NewStudentInput? input = await showDialog<_NewStudentInput>(
      context: context,
      barrierColor: Colors.black.withValues(alpha: 0.72),
      builder: (BuildContext context) => const _NewStudentDialog(),
    );

    if (input == null || !mounted) return;

    try {
      await _repository.createStudent(
        name: input.name,
        email: input.email,
        objective: input.objective,
        level: input.level,
        nextSession: input.nextSession,
      );
      await _reload();
      if (!mounted) return;
      _toast('${input.name} foi adicionado ao seu espaço.');
    } catch (error) {
      if (!mounted) return;
      _toast('Não foi possível cadastrar o aluno: $error', error: true);
    }
  }

  Future<void> _createTraining() async {
    if (_students.isEmpty) {
      _toast('Cadastre um aluno antes de criar um treino.');
      return;
    }

    final _TrainingInput? input = await showDialog<_TrainingInput>(
      context: context,
      barrierColor: Colors.black.withValues(alpha: 0.72),
      builder: (BuildContext context) => _TrainingDialog(students: _students),
    );

    if (input == null || !mounted) return;

    try {
      await _repository.createTrainingPlan(
        studentId: input.studentId,
        name: input.name,
        nextSession: input.nextSession,
        notes: input.notes,
        exercises: input.exercises,
      );
      await _reload();
      if (!mounted) return;
      _toast('Treino criado e salvo no FitNexus.');
    } catch (error) {
      if (!mounted) return;
      _toast('Não foi possível criar o treino: $error', error: true);
    }
  }

  void _toast(String message, {bool error = false}) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        behavior: SnackBarBehavior.floating,
        backgroundColor: error ? const Color(0xFF5A1919) : _LiveColors.card,
        content: Text(message),
      ),
    );
  }

  int get _averageAdherence {
    if (_students.isEmpty) return 0;
    final int total = _students.fold<int>(0, (int sum, StudentRecord student) => sum + student.adherence);
    return (total / _students.length).round();
  }

  @override
  Widget build(BuildContext context) {
    final String professorEmail = AuthService.instance.currentUser?.email ?? 'Professor';

    return Scaffold(
      backgroundColor: _LiveColors.black,
      body: SafeArea(
        child: RefreshIndicator(
          color: _LiveColors.gold,
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
                    _DashboardHeader(
                      email: professorEmail,
                      loading: _loading,
                      onRefresh: _reload,
                    ),
                    const SizedBox(height: 24),
                    _HeroActions(
                      onNewStudent: _createStudent,
                      onNewTraining: _createTraining,
                    ),
                    const SizedBox(height: 20),
                    _StatsRow(
                      students: _students.length,
                      plans: _plans.where((TrainingPlanRecord plan) => plan.isActive).length,
                      adherence: _averageAdherence,
                    ),
                    if (_error != null) ...<Widget>[
                      const SizedBox(height: 18),
                      _ErrorPanel(message: _error!, onRetry: _reload),
                    ],
                    const SizedBox(height: 22),
                    _StudentsPanel(
                      students: _students,
                      loading: _loading,
                      onNewStudent: _createStudent,
                    ),
                    const SizedBox(height: 22),
                    _PlansPanel(plans: _plans, students: _students),
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

class _DashboardHeader extends StatelessWidget {
  const _DashboardHeader({
    required this.email,
    required this.loading,
    required this.onRefresh,
  });

  final String email;
  final bool loading;
  final Future<void> Function() onRefresh;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 18,
      runSpacing: 16,
      alignment: WrapAlignment.spaceBetween,
      crossAxisAlignment: WrapCrossAlignment.center,
      children: <Widget>[
        Row(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            Container(
              width: 52,
              height: 52,
              decoration: BoxDecoration(
                gradient: _LiveColors.goldGradient,
                borderRadius: BorderRadius.circular(15),
                boxShadow: <BoxShadow>[
                  BoxShadow(
                    color: _LiveColors.gold.withValues(alpha: 0.25),
                    blurRadius: 26,
                  ),
                ],
              ),
              child: const Icon(Icons.fitness_center_rounded, color: Colors.black),
            ),
            const SizedBox(width: 14),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                const Text(
                  'FitNexus Coach',
                  style: TextStyle(
                    color: _LiveColors.text,
                    fontSize: 23,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  email,
                  style: const TextStyle(color: _LiveColors.muted, fontSize: 12),
                ),
              ],
            ),
          ],
        ),
        IconButton.filledTonal(
          tooltip: 'Atualizar dados',
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

class _HeroActions extends StatelessWidget {
  const _HeroActions({
    required this.onNewStudent,
    required this.onNewTraining,
  });

  final VoidCallback onNewStudent;
  final VoidCallback onNewTraining;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(28),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(28),
        gradient: const LinearGradient(
          colors: <Color>[Color(0xFF171205), Color(0xFF0D0D0D)],
        ),
        border: Border.all(color: _LiveColors.border),
      ),
      child: LayoutBuilder(
        builder: (BuildContext context, BoxConstraints constraints) {
          final bool narrow = constraints.maxWidth < 760;
          final Widget copy = const Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(
                'PAINEL AO VIVO',
                style: TextStyle(
                  color: _LiveColors.goldSoft,
                  fontWeight: FontWeight.w900,
                  fontSize: 12,
                  letterSpacing: 1,
                ),
              ),
              SizedBox(height: 10),
              Text(
                'Alunos e treinos agora vivem no seu banco FitNexus.',
                style: TextStyle(
                  color: _LiveColors.text,
                  fontSize: 28,
                  height: 1.12,
                  fontWeight: FontWeight.w900,
                ),
              ),
              SizedBox(height: 8),
              Text(
                'Cada registro é isolado pela sua organização e protegido por RLS no Postgres.',
                style: TextStyle(color: _LiveColors.muted, height: 1.45),
              ),
            ],
          );

          final Widget actions = Wrap(
            spacing: 10,
            runSpacing: 10,
            children: <Widget>[
              _GoldAction(
                label: 'Novo aluno',
                icon: Icons.person_add_alt_1_rounded,
                onPressed: onNewStudent,
              ),
              OutlinedButton.icon(
                onPressed: onNewTraining,
                icon: const Icon(Icons.assignment_add),
                label: const Text('Criar treino'),
                style: OutlinedButton.styleFrom(
                  foregroundColor: _LiveColors.text,
                  side: const BorderSide(color: _LiveColors.border),
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                ),
              ),
            ],
          );

          if (narrow) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[copy, const SizedBox(height: 20), actions],
            );
          }

          return Row(
            children: <Widget>[
              Expanded(child: copy),
              const SizedBox(width: 26),
              actions,
            ],
          );
        },
      ),
    );
  }
}

class _StatsRow extends StatelessWidget {
  const _StatsRow({required this.students, required this.plans, required this.adherence});

  final int students;
  final int plans;
  final int adherence;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (BuildContext context, BoxConstraints constraints) {
        final int columns = constraints.maxWidth < 680 ? 1 : 3;
        const double gap = 12;
        final double width = (constraints.maxWidth - gap * (columns - 1)) / columns;

        return Wrap(
          spacing: gap,
          runSpacing: gap,
          children: <Widget>[
            SizedBox(width: width, child: _StatCard(icon: Icons.groups_rounded, value: '$students', label: 'Alunos cadastrados')),
            SizedBox(width: width, child: _StatCard(icon: Icons.assignment_turned_in_rounded, value: '$plans', label: 'Treinos ativos')),
            SizedBox(width: width, child: _StatCard(icon: Icons.trending_up_rounded, value: '$adherence%', label: 'Aderência média')),
          ],
        );
      },
    );
  }
}

class _StatCard extends StatelessWidget {
  const _StatCard({required this.icon, required this.value, required this.label});

  final IconData icon;
  final String value;
  final String label;

  @override
  Widget build(BuildContext context) {
    return _Panel(
      child: Row(
        children: <Widget>[
          Icon(icon, color: _LiveColors.goldSoft, size: 28),
          const SizedBox(width: 14),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(value, style: const TextStyle(color: _LiveColors.text, fontSize: 25, fontWeight: FontWeight.w900)),
              Text(label, style: const TextStyle(color: _LiveColors.muted, fontSize: 12)),
            ],
          ),
        ],
      ),
    );
  }
}

class _StudentsPanel extends StatelessWidget {
  const _StudentsPanel({
    required this.students,
    required this.loading,
    required this.onNewStudent,
  });

  final List<StudentRecord> students;
  final bool loading;
  final VoidCallback onNewStudent;

  @override
  Widget build(BuildContext context) {
    return _Panel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const _PanelTitle(title: 'Alunos', subtitle: 'Dados reais da sua organização'),
          const SizedBox(height: 18),
          if (loading && students.isEmpty)
            const Center(child: Padding(padding: EdgeInsets.all(32), child: CircularProgressIndicator(color: _LiveColors.gold)))
          else if (students.isEmpty)
            _EmptyState(
              icon: Icons.group_add_rounded,
              title: 'Nenhum aluno cadastrado ainda',
              text: 'Crie o primeiro aluno e o FitNexus começa a montar sua base real.',
              action: _GoldAction(label: 'Cadastrar primeiro aluno', icon: Icons.add_rounded, onPressed: onNewStudent),
            )
          else
            Column(
              children: students
                  .map((StudentRecord student) => Padding(
                        padding: const EdgeInsets.only(bottom: 10),
                        child: _StudentRow(student: student),
                      ))
                  .toList(growable: false),
            ),
        ],
      ),
    );
  }
}

class _StudentRow extends StatelessWidget {
  const _StudentRow({required this.student});

  final StudentRecord student;

  @override
  Widget build(BuildContext context) {
    final String initials = student.name
        .split(RegExp(r'\s+'))
        .where((String part) => part.isNotEmpty)
        .take(2)
        .map((String part) => part[0].toUpperCase())
        .join();

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: _LiveColors.cardSoft,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: _LiveColors.border),
      ),
      child: Row(
        children: <Widget>[
          CircleAvatar(
            backgroundColor: _LiveColors.gold,
            foregroundColor: Colors.black,
            child: Text(initials, style: const TextStyle(fontWeight: FontWeight.w900)),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(student.name, style: const TextStyle(color: _LiveColors.text, fontSize: 16, fontWeight: FontWeight.w900)),
                const SizedBox(height: 4),
                Text('${student.objective} • ${student.level}', style: const TextStyle(color: _LiveColors.muted, fontSize: 12)),
                if ((student.lastWorkout ?? '').isNotEmpty) ...<Widget>[
                  const SizedBox(height: 4),
                  Text('Último treino: ${student.lastWorkout}', style: const TextStyle(color: _LiveColors.muted, fontSize: 12)),
                ],
              ],
            ),
          ),
          const SizedBox(width: 10),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: <Widget>[
              Text('${student.adherence}%', style: const TextStyle(color: _LiveColors.goldSoft, fontWeight: FontWeight.w900)),
              const SizedBox(height: 3),
              Text(student.status, style: const TextStyle(color: _LiveColors.muted, fontSize: 11)),
            ],
          ),
        ],
      ),
    );
  }
}

class _PlansPanel extends StatelessWidget {
  const _PlansPanel({required this.plans, required this.students});

  final List<TrainingPlanRecord> plans;
  final List<StudentRecord> students;

  String _studentName(String id) {
    for (final StudentRecord student in students) {
      if (student.id == id) return student.name;
    }
    return 'Aluno';
  }

  @override
  Widget build(BuildContext context) {
    return _Panel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const _PanelTitle(title: 'Treinos', subtitle: 'Planos persistidos no Supabase'),
          const SizedBox(height: 18),
          if (plans.isEmpty)
            const Text('Nenhum treino criado ainda.', style: TextStyle(color: _LiveColors.muted))
          else
            Wrap(
              spacing: 12,
              runSpacing: 12,
              children: plans
                  .map((TrainingPlanRecord plan) => ConstrainedBox(
                        constraints: const BoxConstraints(minWidth: 250, maxWidth: 390),
                        child: Container(
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: _LiveColors.cardSoft,
                            borderRadius: BorderRadius.circular(18),
                            border: Border.all(color: _LiveColors.border),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: <Widget>[
                              Text(plan.name, style: const TextStyle(color: _LiveColors.text, fontWeight: FontWeight.w900, fontSize: 16)),
                              const SizedBox(height: 6),
                              Text(_studentName(plan.studentId), style: const TextStyle(color: _LiveColors.goldSoft, fontSize: 12)),
                              if ((plan.nextSession ?? '').isNotEmpty) ...<Widget>[
                                const SizedBox(height: 8),
                                Text('Próxima sessão: ${plan.nextSession}', style: const TextStyle(color: _LiveColors.muted, fontSize: 12)),
                              ],
                            ],
                          ),
                        ),
                      ))
                  .toList(growable: false),
            ),
        ],
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
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF351313),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: Colors.redAccent.withValues(alpha: 0.5)),
      ),
      child: Row(
        children: <Widget>[
          const Icon(Icons.error_outline_rounded, color: Colors.redAccent),
          const SizedBox(width: 12),
          Expanded(child: Text(message, style: const TextStyle(color: _LiveColors.text))),
          TextButton(onPressed: onRetry, child: const Text('Tentar novamente')),
        ],
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
        color: _LiveColors.card,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: _LiveColors.border),
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
        Text(title, style: const TextStyle(color: _LiveColors.text, fontSize: 21, fontWeight: FontWeight.w900)),
        const SizedBox(height: 4),
        Text(subtitle, style: const TextStyle(color: _LiveColors.muted, fontSize: 12)),
      ],
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({required this.icon, required this.title, required this.text, required this.action});

  final IconData icon;
  final String title;
  final String text;
  final Widget action;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 30),
        child: Column(
          children: <Widget>[
            Icon(icon, color: _LiveColors.goldSoft, size: 42),
            const SizedBox(height: 12),
            Text(title, textAlign: TextAlign.center, style: const TextStyle(color: _LiveColors.text, fontSize: 18, fontWeight: FontWeight.w900)),
            const SizedBox(height: 6),
            ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 520),
              child: Text(text, textAlign: TextAlign.center, style: const TextStyle(color: _LiveColors.muted, height: 1.4)),
            ),
            const SizedBox(height: 18),
            action,
          ],
        ),
      ),
    );
  }
}

class _GoldAction extends StatelessWidget {
  const _GoldAction({required this.label, required this.icon, required this.onPressed});

  final String label;
  final IconData icon;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return FilledButton.icon(
      onPressed: onPressed,
      icon: Icon(icon),
      label: Text(label),
      style: FilledButton.styleFrom(
        backgroundColor: _LiveColors.gold,
        foregroundColor: Colors.black,
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        textStyle: const TextStyle(fontWeight: FontWeight.w900),
      ),
    );
  }
}

class _NewStudentInput {
  const _NewStudentInput({
    required this.name,
    required this.email,
    required this.objective,
    required this.level,
    required this.nextSession,
  });

  final String name;
  final String email;
  final String objective;
  final String level;
  final String nextSession;
}

class _NewStudentDialog extends StatefulWidget {
  const _NewStudentDialog();

  @override
  State<_NewStudentDialog> createState() => _NewStudentDialogState();
}

class _NewStudentDialogState extends State<_NewStudentDialog> {
  final GlobalKey<FormState> _formKey = GlobalKey<FormState>();
  final TextEditingController _name = TextEditingController();
  final TextEditingController _email = TextEditingController();
  final TextEditingController _objective = TextEditingController(text: 'Hipertrofia');
  final TextEditingController _level = TextEditingController(text: 'Iniciante');
  final TextEditingController _next = TextEditingController();

  @override
  void dispose() {
    _name.dispose();
    _email.dispose();
    _objective.dispose();
    _level.dispose();
    _next.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      backgroundColor: _LiveColors.card,
      title: const Text('Novo aluno'),
      content: SizedBox(
        width: 520,
        child: Form(
          key: _formKey,
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                _Field(controller: _name, label: 'Nome *', validator: _required),
                const SizedBox(height: 10),
                _Field(controller: _email, label: 'E-mail'),
                const SizedBox(height: 10),
                _Field(controller: _objective, label: 'Objetivo *', validator: _required),
                const SizedBox(height: 10),
                _Field(controller: _level, label: 'Nível *', validator: _required),
                const SizedBox(height: 10),
                _Field(controller: _next, label: 'Próxima sessão'),
              ],
            ),
          ),
        ),
      ),
      actions: <Widget>[
        TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancelar')),
        FilledButton(
          onPressed: () {
            if (!(_formKey.currentState?.validate() ?? false)) return;
            Navigator.pop(
              context,
              _NewStudentInput(
                name: _name.text.trim(),
                email: _email.text.trim(),
                objective: _objective.text.trim(),
                level: _level.text.trim(),
                nextSession: _next.text.trim(),
              ),
            );
          },
          child: const Text('Salvar'),
        ),
      ],
    );
  }

  String? _required(String? value) {
    return value == null || value.trim().isEmpty ? 'Campo obrigatório.' : null;
  }
}

class _TrainingInput {
  const _TrainingInput({
    required this.studentId,
    required this.name,
    required this.nextSession,
    required this.notes,
    required this.exercises,
  });

  final String studentId;
  final String name;
  final String nextSession;
  final String notes;
  final List<TrainingExerciseDraft> exercises;
}

class _TrainingDialog extends StatefulWidget {
  const _TrainingDialog({required this.students});

  final List<StudentRecord> students;

  @override
  State<_TrainingDialog> createState() => _TrainingDialogState();
}

class _TrainingDialogState extends State<_TrainingDialog> {
  final GlobalKey<FormState> _formKey = GlobalKey<FormState>();
  late String _studentId = widget.students.first.id;
  final TextEditingController _name = TextEditingController(text: 'Treino A');
  final TextEditingController _next = TextEditingController();
  final TextEditingController _notes = TextEditingController();
  final TextEditingController _exercises = TextEditingController(
    text: 'Agachamento livre | 3x10\nSupino reto | 3x10\nRemada baixa | 3x12',
  );

  @override
  void dispose() {
    _name.dispose();
    _next.dispose();
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
            prescription: parts.length > 1 ? parts.sublist(1).join('|').trim() : '',
          );
        })
        .toList(growable: false);
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      backgroundColor: _LiveColors.card,
      title: const Text('Criar treino'),
      content: SizedBox(
        width: 600,
        child: Form(
          key: _formKey,
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                DropdownButtonFormField<String>(
                  initialValue: _studentId,
                  dropdownColor: _LiveColors.card,
                  decoration: const InputDecoration(labelText: 'Aluno'),
                  items: widget.students
                      .map((StudentRecord student) => DropdownMenuItem<String>(value: student.id, child: Text(student.name)))
                      .toList(growable: false),
                  onChanged: (String? value) {
                    if (value != null) setState(() => _studentId = value);
                  },
                ),
                const SizedBox(height: 10),
                _Field(controller: _name, label: 'Nome do treino *', validator: _required),
                const SizedBox(height: 10),
                _Field(controller: _next, label: 'Próxima sessão'),
                const SizedBox(height: 10),
                _Field(controller: _notes, label: 'Observações', maxLines: 2),
                const SizedBox(height: 10),
                _Field(
                  controller: _exercises,
                  label: 'Exercícios — um por linha: nome | prescrição *',
                  maxLines: 7,
                  validator: (String? value) {
                    if (value == null || value.trim().isEmpty) return 'Informe pelo menos um exercício.';
                    if (_parseExercises().any((TrainingExerciseDraft exercise) => exercise.name.length < 2)) {
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
        TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancelar')),
        FilledButton(
          onPressed: () {
            if (!(_formKey.currentState?.validate() ?? false)) return;
            Navigator.pop(
              context,
              _TrainingInput(
                studentId: _studentId,
                name: _name.text.trim(),
                nextSession: _next.text.trim(),
                notes: _notes.text.trim(),
                exercises: _parseExercises(),
              ),
            );
          },
          child: const Text('Criar treino'),
        ),
      ],
    );
  }

  String? _required(String? value) {
    return value == null || value.trim().isEmpty ? 'Campo obrigatório.' : null;
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
      style: const TextStyle(color: _LiveColors.text),
      decoration: InputDecoration(
        labelText: label,
        filled: true,
        fillColor: _LiveColors.cardSoft,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(14)),
      ),
    );
  }
}

class _LiveColors {
  static const Color black = Color(0xFF050505);
  static const Color card = Color(0xFF101010);
  static const Color cardSoft = Color(0xFF171717);
  static const Color border = Color(0xFF2C2A22);
  static const Color gold = Color(0xFFE1B92F);
  static const Color goldSoft = Color(0xFFFFD45A);
  static const Color text = Color(0xFFF7F7F7);
  static const Color muted = Color(0xFFB7B7B7);

  static const LinearGradient goldGradient = LinearGradient(
    colors: <Color>[goldSoft, gold],
  );
}
