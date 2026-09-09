import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/blackgold_tokens.dart';
import '../auth/auth_service.dart';
import 'professor_data_repository.dart';

class ProfessorLiveDashboardPage extends StatefulWidget {
  const ProfessorLiveDashboardPage({super.key});

  @override
  State<ProfessorLiveDashboardPage> createState() =>
      _ProfessorLiveDashboardPageState();
}

class _ProfessorLiveDashboardPageState
    extends State<ProfessorLiveDashboardPage> {
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
      barrierColor: Colors.black.withValues(alpha: 0.78),
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
      barrierColor: Colors.black.withValues(alpha: 0.78),
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
        backgroundColor: error
            ? AppColors.danger.withValues(alpha: 0.24)
            : AppColors.cardRaised,
        content: Text(message),
      ),
    );
  }

  int get _averageAdherence {
    if (_students.isEmpty) return 0;
    final int total = _students.fold<int>(
      0,
      (int sum, StudentRecord student) => sum + student.adherence,
    );
    return (total / _students.length).round();
  }

  String _studentName(String studentId) {
    for (final StudentRecord student in _students) {
      if (student.id == studentId) return student.name;
    }
    return 'Aluno';
  }

  @override
  Widget build(BuildContext context) {
    final String professorEmail =
        AuthService.instance.currentUser?.email ?? 'Professor';
    final List<TrainingPlanRecord> activePlans =
        _plans.where((TrainingPlanRecord plan) => plan.isActive).toList();

    return Scaffold(
      backgroundColor: AppColors.black,
      body: Stack(
        children: <Widget>[
          const Positioned.fill(child: _DashboardAtmosphere()),
          SafeArea(
            child: RefreshIndicator(
              color: AppColors.gold,
              backgroundColor: AppColors.cardRaised,
              onRefresh: _reload,
              child: SingleChildScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.fromLTRB(
                  BlackGoldSpace.lg,
                  BlackGoldSpace.xl,
                  BlackGoldSpace.lg,
                  120,
                ),
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
                          onNewStudent: _createStudent,
                          onNewTraining: _createTraining,
                        ),
                        const SizedBox(height: BlackGoldSpace.lg),
                        _StatsRow(
                          students: _students.length,
                          plans: activePlans.length,
                          adherence: _averageAdherence,
                          scheduled: _students
                              .where((student) =>
                                  (student.nextSession ?? '').trim().isNotEmpty)
                              .length,
                        ),
                        if (_error != null) ...<Widget>[
                          const SizedBox(height: BlackGoldSpace.sm),
                          _ErrorPanel(message: _error!, onRetry: _reload),
                        ],
                        const SizedBox(height: BlackGoldSpace.lg),
                        LayoutBuilder(
                          builder: (
                            BuildContext context,
                            BoxConstraints constraints,
                          ) {
                            if (constraints.maxWidth < 980) {
                              return Column(
                                children: <Widget>[
                                  _StudentsPanel(
                                    students: _students,
                                    loading: _loading,
                                    onNewStudent: _createStudent,
                                  ),
                                  const SizedBox(height: BlackGoldSpace.lg),
                                  _PlansPanel(
                                    plans: _plans,
                                    studentName: _studentName,
                                    onNewTraining: _createTraining,
                                  ),
                                ],
                              );
                            }

                            return Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: <Widget>[
                                Expanded(
                                  flex: 6,
                                  child: _StudentsPanel(
                                    students: _students,
                                    loading: _loading,
                                    onNewStudent: _createStudent,
                                  ),
                                ),
                                const SizedBox(width: BlackGoldSpace.lg),
                                Expanded(
                                  flex: 5,
                                  child: _PlansPanel(
                                    plans: _plans,
                                    studentName: _studentName,
                                    onNewTraining: _createTraining,
                                  ),
                                ),
                              ],
                            );
                          },
                        ),
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

class _DashboardAtmosphere extends StatelessWidget {
  const _DashboardAtmosphere();

  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      child: DecoratedBox(
        decoration: BoxDecoration(
          gradient: RadialGradient(
            center: const Alignment(0.75, -0.95),
            radius: 1.2,
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

class _DashboardHeader extends StatelessWidget {
  const _DashboardHeader({
    required this.email,
    required this.loading,
    required this.onRefresh,
    required this.onNewStudent,
    required this.onNewTraining,
  });

  final String email;
  final bool loading;
  final Future<void> Function() onRefresh;
  final VoidCallback onNewStudent;
  final VoidCallback onNewTraining;

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
          final Widget copy = Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Row(
                children: <Widget>[
                  Container(
                    width: 48,
                    height: 48,
                    decoration: BoxDecoration(
                      gradient: BlackGoldEffects.goldGradient,
                      borderRadius: BorderRadius.circular(BlackGoldRadius.card),
                      boxShadow: BlackGoldEffects.goldGlow,
                    ),
                    child: const Icon(
                      Icons.fitness_center_rounded,
                      color: Colors.black,
                    ),
                  ),
                  const SizedBox(width: BlackGoldSpace.sm),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        const Text(
                          'PAINEL OPERACIONAL',
                          style: TextStyle(
                            color: AppColors.goldSoft,
                            fontSize: 11,
                            fontWeight: FontWeight.w900,
                            letterSpacing: 1.2,
                          ),
                        ),
                        const SizedBox(height: BlackGoldSpace.xxs),
                        const Text(
                          'Alunos e treinos no mesmo centro de comando',
                          style: TextStyle(
                            color: AppColors.text,
                            fontSize: 28,
                            height: 1.06,
                            fontWeight: FontWeight.w900,
                            letterSpacing: -0.6,
                          ),
                        ),
                        const SizedBox(height: BlackGoldSpace.xxs),
                        Text(
                          email,
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
              const SizedBox(height: BlackGoldSpace.md),
              const Text(
                'Cada registro é isolado por organização e protegido por RLS no Postgres. Use este painel para cadastrar alunos e criar prescrições reais.',
                style: TextStyle(
                  color: AppColors.muted,
                  fontSize: 14,
                  height: 1.5,
                ),
              ),
            ],
          );

          final Widget actions = Wrap(
            spacing: BlackGoldSpace.xs,
            runSpacing: BlackGoldSpace.xs,
            children: <Widget>[
              FilledButton.icon(
                key: const ValueKey<String>('live-dashboard-new-student'),
                onPressed: onNewStudent,
                icon: const Icon(Icons.person_add_alt_1_rounded),
                label: const Text('Novo aluno'),
              ),
              OutlinedButton.icon(
                key: const ValueKey<String>('live-dashboard-new-training'),
                onPressed: onNewTraining,
                icon: const Icon(Icons.assignment_add),
                label: const Text('Criar treino'),
              ),
              IconButton.outlined(
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

          if (constraints.maxWidth < BlackGoldBreakpoints.tablet) {
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

class _StatsRow extends StatelessWidget {
  const _StatsRow({
    required this.students,
    required this.plans,
    required this.adherence,
    required this.scheduled,
  });

  final int students;
  final int plans;
  final int adherence;
  final int scheduled;

  @override
  Widget build(BuildContext context) {
    final List<_StatData> data = <_StatData>[
      _StatData(Icons.groups_rounded, '$students', 'Alunos', 'cadastrados'),
      _StatData(
        Icons.assignment_turned_in_rounded,
        '$plans',
        'Treinos ativos',
        'em acompanhamento',
      ),
      _StatData(
        Icons.trending_up_rounded,
        '$adherence%',
        'Aderência média',
        'da base atual',
      ),
      _StatData(
        Icons.event_available_rounded,
        '$scheduled',
        'Próximas sessões',
        'com agenda definida',
      ),
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
              .map((item) => SizedBox(width: width, child: _StatCard(data: item)))
              .toList(growable: false),
        );
      },
    );
  }
}

class _StatData {
  const _StatData(this.icon, this.value, this.label, this.detail);

  final IconData icon;
  final String value;
  final String label;
  final String detail;
}

class _StatCard extends StatelessWidget {
  const _StatCard({required this.data});

  final _StatData data;

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
                  data.detail,
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
      icon: Icons.groups_rounded,
      eyebrow: 'BASE DE ALUNOS',
      title: 'Alunos',
      action: TextButton.icon(
        onPressed: onNewStudent,
        icon: const Icon(Icons.add_rounded),
        label: const Text('Adicionar'),
      ),
      child: loading && students.isEmpty
          ? const _InlineLoading(text: 'Carregando alunos…')
          : students.isEmpty
              ? _EmptyState(
                  icon: Icons.group_add_rounded,
                  title: 'Nenhum aluno cadastrado ainda',
                  text:
                      'Crie o primeiro aluno e o FitNexus começa a montar sua base real.',
                  action: FilledButton.icon(
                    onPressed: onNewStudent,
                    icon: const Icon(Icons.add_rounded),
                    label: const Text('Cadastrar primeiro aluno'),
                  ),
                )
              : Column(
                  children: students
                      .map(
                        (StudentRecord student) => Padding(
                          padding:
                              const EdgeInsets.only(bottom: BlackGoldSpace.xs),
                          child: _StudentRow(student: student),
                        ),
                      )
                      .toList(growable: false),
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
      padding: const EdgeInsets.all(BlackGoldSpace.sm),
      decoration: BoxDecoration(
        color: AppColors.cardRaised,
        borderRadius: BorderRadius.circular(BlackGoldRadius.card),
        border: Border.all(color: AppColors.border),
      ),
      child: LayoutBuilder(
        builder: (BuildContext context, BoxConstraints constraints) {
          final Widget identity = Row(
            children: <Widget>[
              CircleAvatar(
                backgroundColor: AppColors.gold,
                foregroundColor: Colors.black,
                child: Text(
                  initials,
                  style: const TextStyle(fontWeight: FontWeight.w900),
                ),
              ),
              const SizedBox(width: BlackGoldSpace.sm),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      student.name,
                      style: const TextStyle(
                        color: AppColors.text,
                        fontSize: 15,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(height: BlackGoldSpace.xxs),
                    Text(
                      '${student.objective} • ${student.level}',
                      style: const TextStyle(
                        color: AppColors.muted,
                        fontSize: 11,
                      ),
                    ),
                    if ((student.lastWorkout ?? '').trim().isNotEmpty) ...<Widget>[
                      const SizedBox(height: BlackGoldSpace.xxs),
                      Text(
                        'Último treino: ${student.lastWorkout}',
                        style: const TextStyle(
                          color: AppColors.mutedSoft,
                          fontSize: 10.5,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ],
          );

          final Widget status = Wrap(
            spacing: BlackGoldSpace.xs,
            runSpacing: BlackGoldSpace.xs,
            children: <Widget>[
              _Pill(
                label: '${student.adherence}% aderência',
                color: student.adherence >= 75
                    ? AppColors.success
                    : AppColors.warning,
              ),
              _Pill(label: student.status, color: AppColors.goldSoft),
            ],
          );

          if (constraints.maxWidth < 620) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: <Widget>[
                identity,
                const SizedBox(height: BlackGoldSpace.sm),
                status,
              ],
            );
          }

          return Row(
            children: <Widget>[
              Expanded(child: identity),
              const SizedBox(width: BlackGoldSpace.sm),
              status,
            ],
          );
        },
      ),
    );
  }
}

class _PlansPanel extends StatelessWidget {
  const _PlansPanel({
    required this.plans,
    required this.studentName,
    required this.onNewTraining,
  });

  final List<TrainingPlanRecord> plans;
  final String Function(String studentId) studentName;
  final VoidCallback onNewTraining;

  @override
  Widget build(BuildContext context) {
    return _Panel(
      icon: Icons.assignment_turned_in_rounded,
      eyebrow: 'PRESCRIÇÕES',
      title: 'Treinos',
      action: TextButton.icon(
        onPressed: onNewTraining,
        icon: const Icon(Icons.add_rounded),
        label: const Text('Criar'),
      ),
      child: plans.isEmpty
          ? _EmptyState(
              icon: Icons.assignment_add,
              title: 'Nenhum treino criado ainda',
              text:
                  'Crie a primeira prescrição para conectar um aluno a um treino real.',
              action: FilledButton.icon(
                onPressed: onNewTraining,
                icon: const Icon(Icons.assignment_add),
                label: const Text('Criar primeiro treino'),
              ),
            )
          : Column(
              children: plans
                  .map(
                    (TrainingPlanRecord plan) => Padding(
                      padding:
                          const EdgeInsets.only(bottom: BlackGoldSpace.xs),
                      child: _PlanRow(
                        plan: plan,
                        studentName: studentName(plan.studentId),
                      ),
                    ),
                  )
                  .toList(growable: false),
            ),
    );
  }
}

class _PlanRow extends StatelessWidget {
  const _PlanRow({required this.plan, required this.studentName});

  final TrainingPlanRecord plan;
  final String studentName;

  @override
  Widget build(BuildContext context) {
    final Color accent = plan.isActive ? AppColors.success : AppColors.mutedSoft;
    return Container(
      padding: const EdgeInsets.all(BlackGoldSpace.sm),
      decoration: BoxDecoration(
        color: AppColors.cardRaised,
        borderRadius: BorderRadius.circular(BlackGoldRadius.card),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            children: <Widget>[
              Container(
                width: 38,
                height: 38,
                decoration: BoxDecoration(
                  color: accent.withValues(alpha: 0.08),
                  borderRadius: BorderRadius.circular(BlackGoldRadius.control),
                ),
                child: Icon(
                  Icons.fitness_center_rounded,
                  color: accent,
                  size: 19,
                ),
              ),
              const SizedBox(width: BlackGoldSpace.sm),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      plan.name,
                      style: const TextStyle(
                        color: AppColors.text,
                        fontWeight: FontWeight.w900,
                        fontSize: 14,
                      ),
                    ),
                    const SizedBox(height: BlackGoldSpace.xxs),
                    Text(
                      studentName,
                      style: const TextStyle(
                        color: AppColors.muted,
                        fontSize: 11,
                      ),
                    ),
                  ],
                ),
              ),
              _Pill(
                label: plan.isActive ? 'ATIVO' : 'ARQUIVADO',
                color: accent,
              ),
            ],
          ),
          if ((plan.nextSession ?? '').trim().isNotEmpty) ...<Widget>[
            const SizedBox(height: BlackGoldSpace.sm),
            Row(
              children: <Widget>[
                const Icon(
                  Icons.event_rounded,
                  color: AppColors.goldSoft,
                  size: 15,
                ),
                const SizedBox(width: BlackGoldSpace.xs),
                Expanded(
                  child: Text(
                    'Próxima sessão: ${plan.nextSession}',
                    style: const TextStyle(
                      color: AppColors.muted,
                      fontSize: 11,
                    ),
                  ),
                ),
              ],
            ),
          ],
          if ((plan.notes ?? '').trim().isNotEmpty) ...<Widget>[
            const SizedBox(height: BlackGoldSpace.xs),
            Text(
              plan.notes!,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                color: AppColors.mutedSoft,
                fontSize: 10.5,
                height: 1.35,
              ),
            ),
          ],
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
    this.action,
  });

  final IconData icon;
  final String eyebrow;
  final String title;
  final Widget child;
  final Widget? action;

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
              if (action != null) action!,
            ],
          ),
          const SizedBox(height: BlackGoldSpace.md),
          child,
        ],
      ),
    );
  }
}

class _Pill extends StatelessWidget {
  const _Pill({required this.label, required this.color});

  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 6),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.09),
        borderRadius: BorderRadius.circular(BlackGoldRadius.pill),
        border: Border.all(color: color.withValues(alpha: 0.24)),
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

class _EmptyState extends StatelessWidget {
  const _EmptyState({
    required this.icon,
    required this.title,
    required this.text,
    required this.action,
  });

  final IconData icon;
  final String title;
  final String text;
  final Widget action;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: BlackGoldSpace.xl),
      child: Column(
        children: <Widget>[
          Container(
            width: 54,
            height: 54,
            decoration: BoxDecoration(
              color: AppColors.gold.withValues(alpha: 0.08),
              borderRadius: BorderRadius.circular(BlackGoldRadius.panel),
              border: Border.all(color: AppColors.border),
            ),
            child: Icon(icon, color: AppColors.goldSoft, size: 28),
          ),
          const SizedBox(height: BlackGoldSpace.sm),
          Text(
            title,
            textAlign: TextAlign.center,
            style: const TextStyle(
              color: AppColors.text,
              fontSize: 17,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: BlackGoldSpace.xs),
          Text(
            text,
            textAlign: TextAlign.center,
            style: const TextStyle(color: AppColors.muted, height: 1.4),
          ),
          const SizedBox(height: BlackGoldSpace.md),
          action,
        ],
      ),
    );
  }
}

class _InlineLoading extends StatelessWidget {
  const _InlineLoading({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(BlackGoldSpace.xl),
      child: Column(
        children: <Widget>[
          const CircularProgressIndicator(color: AppColors.gold),
          const SizedBox(height: BlackGoldSpace.sm),
          Text(text, style: const TextStyle(color: AppColors.muted)),
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
      padding: const EdgeInsets.all(BlackGoldSpace.md),
      decoration: BoxDecoration(
        color: AppColors.danger.withValues(alpha: 0.07),
        borderRadius: BorderRadius.circular(BlackGoldRadius.panel),
        border: Border.all(color: AppColors.danger.withValues(alpha: 0.35)),
      ),
      child: Row(
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
          TextButton(onPressed: onRetry, child: const Text('Tentar novamente')),
        ],
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
  final TextEditingController _objective =
      TextEditingController(text: 'Hipertrofia');
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
      title: const _DialogTitle(
        icon: Icons.person_add_alt_1_rounded,
        eyebrow: 'BASE DE ALUNOS',
        title: 'Novo aluno',
      ),
      content: SizedBox(
        width: 520,
        child: Form(
          key: _formKey,
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                _Field(
                  controller: _name,
                  label: 'Nome *',
                  validator: _required,
                ),
                const SizedBox(height: BlackGoldSpace.sm),
                _Field(controller: _email, label: 'E-mail'),
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
                _Field(controller: _next, label: 'Próxima sessão'),
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
              _NewStudentInput(
                name: _name.text.trim(),
                email: _email.text.trim(),
                objective: _objective.text.trim(),
                level: _level.text.trim(),
                nextSession: _next.text.trim(),
              ),
            );
          },
          icon: const Icon(Icons.check_rounded),
          label: const Text('Salvar aluno'),
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
    text:
        'Agachamento livre | 3x10\nSupino reto | 3x10\nRemada baixa | 3x12',
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
        icon: Icons.assignment_add,
        eyebrow: 'PRESCRIÇÃO',
        title: 'Criar treino',
      ),
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
                _Field(
                  controller: _name,
                  label: 'Nome do treino *',
                  validator: _required,
                ),
                const SizedBox(height: BlackGoldSpace.sm),
                _Field(controller: _next, label: 'Próxima sessão'),
                const SizedBox(height: BlackGoldSpace.sm),
                _Field(
                  controller: _notes,
                  label: 'Observações',
                  maxLines: 2,
                ),
                const SizedBox(height: BlackGoldSpace.sm),
                _Field(
                  controller: _exercises,
                  label: 'Exercícios — um por linha: nome | prescrição *',
                  maxLines: 7,
                  validator: (String? value) {
                    if (value == null || value.trim().isEmpty) {
                      return 'Informe pelo menos um exercício.';
                    }
                    if (_parseExercises().any(
                      (TrainingExerciseDraft exercise) =>
                          exercise.name.length < 2,
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
              _TrainingInput(
                studentId: _studentId,
                name: _name.text.trim(),
                nextSession: _next.text.trim(),
                notes: _notes.text.trim(),
                exercises: _parseExercises(),
              ),
            );
          },
          icon: const Icon(Icons.check_rounded),
          label: const Text('Criar treino'),
        ),
      ],
    );
  }

  String? _required(String? value) {
    return value == null || value.trim().isEmpty ? 'Campo obrigatório.' : null;
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
      children: <Widget>[
        Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(
            gradient: BlackGoldEffects.goldGradient,
            borderRadius: BorderRadius.circular(BlackGoldRadius.card),
          ),
          child: Icon(icon, color: Colors.black, size: 20),
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
                  fontSize: 19,
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
