import 'dart:async';

import 'package:flutter/material.dart';

import '../shared/fitnexus_ui.dart';
import 'student_workout_repository.dart';

class StudentWorkoutPage extends StatefulWidget {
  const StudentWorkoutPage({super.key, this.token});

  final String? token;

  @override
  State<StudentWorkoutPage> createState() => _StudentWorkoutPageState();
}

class _StudentWorkoutPageState extends State<StudentWorkoutPage> {
  final StudentWorkoutRepository _repository = StudentWorkoutRepository.instance;
  final Set<String> _busyExercises = <String>{};

  late final String _token;
  StudentWorkoutSnapshot? _snapshot;
  bool _loading = true;
  bool _starting = false;
  String? _error;
  Timer? _restTimer;
  int _restSeconds = 0;
  int _restInitialSeconds = 0;

  @override
  void initState() {
    super.initState();
    _token = _resolveToken();
    if (_token.isEmpty) {
      _loading = false;
    } else {
      _load();
    }
  }

  @override
  void dispose() {
    _restTimer?.cancel();
    super.dispose();
  }

  String _resolveToken() {
    final String direct = (widget.token ?? '').trim();
    if (direct.isNotEmpty) return direct;

    final String queryToken = (Uri.base.queryParameters['token'] ?? '').trim();
    if (queryToken.isNotEmpty) return queryToken;

    final String fragment = Uri.base.fragment;
    if (fragment.isEmpty) return '';
    final Uri? fragmentUri = Uri.tryParse(
      fragment.startsWith('/') ? fragment : '/$fragment',
    );
    return (fragmentUri?.queryParameters['token'] ?? '').trim();
  }

  Future<void> _load() async {
    if (_token.isEmpty) return;
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final StudentWorkoutSnapshot snapshot =
          await _repository.fetchSnapshot(_token);
      if (!mounted) return;
      setState(() => _snapshot = snapshot);
    } catch (error) {
      if (!mounted) return;
      setState(() => _error = _friendlyError(error));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _startWorkout() async {
    if (_starting || _token.isEmpty) return;
    setState(() => _starting = true);
    try {
      await _repository.startWorkout(_token);
      await _load();
    } catch (error) {
      if (!mounted) return;
      _toast(_friendlyError(error), error: true);
    } finally {
      if (mounted) setState(() => _starting = false);
    }
  }

  Future<void> _toggleExercise(StudentWorkoutExercise exercise) async {
    final StudentWorkoutSnapshot? snapshot = _snapshot;
    final String sessionId = snapshot?.sessionId ?? '';
    if (sessionId.isEmpty || !snapshot!.inProgress) return;
    if (_busyExercises.contains(exercise.id)) return;

    final bool nextValue = !exercise.completed;
    setState(() => _busyExercises.add(exercise.id));

    try {
      await _repository.setExerciseCompletion(
        token: _token,
        sessionId: sessionId,
        exerciseId: exercise.id,
        completed: nextValue,
      );

      if (nextValue) {
        _startRestTimer(exercise.restSeconds);
      }
      await _load();
    } catch (error) {
      if (!mounted) return;
      _toast(_friendlyError(error), error: true);
    } finally {
      if (mounted) {
        setState(() => _busyExercises.remove(exercise.id));
      }
    }
  }

  void _startRestTimer(int seconds) {
    _restTimer?.cancel();
    final int safeSeconds = seconds.clamp(10, 600).toInt();
    setState(() {
      _restInitialSeconds = safeSeconds;
      _restSeconds = safeSeconds;
    });

    _restTimer = Timer.periodic(const Duration(seconds: 1), (Timer timer) {
      if (!mounted) {
        timer.cancel();
        return;
      }
      if (_restSeconds <= 1) {
        timer.cancel();
        setState(() => _restSeconds = 0);
        _toast('Descanso concluído. Próximo exercício!');
        return;
      }
      setState(() => _restSeconds -= 1);
    });
  }

  void _cancelTimer() {
    _restTimer?.cancel();
    setState(() => _restSeconds = 0);
  }

  void _toast(String message, {bool error = false}) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        behavior: SnackBarBehavior.floating,
        backgroundColor: error ? const Color(0xFF5A1919) : FitColors.card,
        content: Text(message),
      ),
    );
  }

  String _friendlyError(Object error) {
    final String text = error.toString();
    if (text.contains('STUDENT_ACCESS_INVALID')) {
      return 'Este link de aluno é inválido, expirou ou foi substituído.';
    }
    if (text.contains('ACTIVE_TRAINING_NOT_FOUND')) {
      return 'Seu professor ainda não publicou um treino ativo.';
    }
    return 'Não foi possível carregar o treino agora. Tente novamente.';
  }

  String _clock(int seconds) {
    final int minutes = seconds ~/ 60;
    final int rest = seconds % 60;
    return '${minutes.toString().padLeft(2, '0')}:${rest.toString().padLeft(2, '0')}';
  }

  @override
  Widget build(BuildContext context) {
    if (_token.isEmpty) {
      return const _StudentMessagePage(
        icon: Icons.link_off_rounded,
        title: 'Link de aluno necessário',
        text: 'Abra o link ou QR Code enviado pelo seu professor para acessar o treino.',
      );
    }

    if (_loading && _snapshot == null) {
      return const _StudentMessagePage(
        loading: true,
        icon: Icons.fitness_center_rounded,
        title: 'Carregando seu treino',
        text: 'Conectando ao FitNexus com seu acesso privado.',
      );
    }

    if (_error != null && _snapshot == null) {
      return _StudentMessagePage(
        icon: Icons.error_outline_rounded,
        title: 'Não foi possível abrir o treino',
        text: _error!,
        action: FilledButton.icon(
          onPressed: _load,
          icon: const Icon(Icons.refresh_rounded),
          label: const Text('Tentar novamente'),
        ),
      );
    }

    final StudentWorkoutSnapshot snapshot = _snapshot!;

    return Scaffold(
      backgroundColor: FitColors.bg,
      body: SafeArea(
        child: RefreshIndicator(
          color: FitColors.gold,
          onRefresh: _load,
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.fromLTRB(18, 18, 18, 54),
            child: Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 820),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: <Widget>[
                    _StudentHeader(
                      name: snapshot.studentName,
                      status: snapshot.studentStatus,
                      onRefresh: _loading ? null : _load,
                    ),
                    const SizedBox(height: 18),
                    _WorkoutHero(snapshot: snapshot),
                    const SizedBox(height: 16),
                    if (!snapshot.hasPlan)
                      const _InfoCard(
                        icon: Icons.assignment_late_outlined,
                        title: 'Nenhum treino ativo ainda',
                        text: 'Seu professor ainda não publicou um treino para este acesso.',
                      )
                    else ...<Widget>[
                      _SessionActionCard(
                        snapshot: snapshot,
                        starting: _starting,
                        onStart: _startWorkout,
                      ),
                      const SizedBox(height: 16),
                      if (_restSeconds > 0) ...<Widget>[
                        _RestTimerCard(
                          time: _clock(_restSeconds),
                          initialSeconds: _restInitialSeconds,
                          remainingSeconds: _restSeconds,
                          onCancel: _cancelTimer,
                        ),
                        const SizedBox(height: 16),
                      ],
                      _ExercisesCard(
                        snapshot: snapshot,
                        busyExercises: _busyExercises,
                        onToggle: _toggleExercise,
                      ),
                      const SizedBox(height: 16),
                      _HistoryCard(history: snapshot.history),
                    ],
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

class _StudentHeader extends StatelessWidget {
  const _StudentHeader({
    required this.name,
    required this.status,
    required this.onRefresh,
  });

  final String name;
  final String status;
  final Future<void> Function()? onRefresh;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: <Widget>[
        Container(
          width: 48,
          height: 48,
          decoration: BoxDecoration(
            color: FitColors.gold,
            borderRadius: BorderRadius.circular(14),
          ),
          child: const Icon(Icons.fitness_center_rounded, color: Colors.black),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              const Text(
                'FitNexus Coach',
                style: TextStyle(
                  color: FitColors.text,
                  fontWeight: FontWeight.w900,
                  fontSize: 19,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                '$name • $status',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(color: FitColors.muted, fontSize: 12),
              ),
            ],
          ),
        ),
        IconButton.filledTonal(
          tooltip: 'Atualizar treino',
          onPressed: onRefresh,
          icon: const Icon(Icons.refresh_rounded),
        ),
      ],
    );
  }
}

class _WorkoutHero extends StatelessWidget {
  const _WorkoutHero({required this.snapshot});

  final StudentWorkoutSnapshot snapshot;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: <Color>[Color(0xFF1C1606), Color(0xFF101010)],
        ),
        borderRadius: BorderRadius.circular(26),
        border: Border.all(color: FitColors.gold.withValues(alpha: 0.30)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const SectionLabel('App do aluno • acesso privado'),
          const SizedBox(height: 10),
          Text(
            snapshot.planName ?? 'Seu espaço de treino',
            style: const TextStyle(
              color: FitColors.text,
              fontSize: 32,
              height: 1.08,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            '${snapshot.objective} • ${snapshot.level}',
            style: const TextStyle(color: FitColors.muted, fontSize: 14),
          ),
          if ((snapshot.planNotes ?? '').isNotEmpty) ...<Widget>[
            const SizedBox(height: 12),
            Text(
              snapshot.planNotes!,
              style: const TextStyle(color: FitColors.muted, height: 1.45),
            ),
          ],
          const SizedBox(height: 20),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: <Widget>[
              _Metric(label: 'Conclusão', value: '${snapshot.completionPercent}%'),
              _Metric(label: 'Aderência', value: '${snapshot.adherence}%'),
              _Metric(label: 'Exercícios', value: '${snapshot.exercises.length}'),
            ],
          ),
        ],
      ),
    );
  }
}

class _SessionActionCard extends StatelessWidget {
  const _SessionActionCard({
    required this.snapshot,
    required this.starting,
    required this.onStart,
  });

  final StudentWorkoutSnapshot snapshot;
  final bool starting;
  final VoidCallback onStart;

  @override
  Widget build(BuildContext context) {
    if (snapshot.inProgress) {
      return const _InfoCard(
        icon: Icons.play_circle_fill_rounded,
        title: 'Treino em andamento',
        text: 'Marque cada exercício conforme concluir. O progresso é salvo no FitNexus.',
      );
    }

    final bool completed = snapshot.completed;
    return FitCard(
      child: LayoutBuilder(
        builder: (BuildContext context, BoxConstraints constraints) {
          final Widget copy = Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(
                completed ? 'Treino concluído' : 'Pronto para começar?',
                style: const TextStyle(
                  color: FitColors.text,
                  fontSize: 20,
                  fontWeight: FontWeight.w900,
                ),
              ),
              const SizedBox(height: 6),
              Text(
                completed
                    ? 'Sua última execução foi salva. Você pode iniciar uma nova sessão quando quiser.'
                    : 'Inicie a sessão para liberar a marcação dos exercícios e registrar seu histórico.',
                style: const TextStyle(color: FitColors.muted, height: 1.4),
              ),
            ],
          );

          final Widget button = GoldButton(
            label: starting
                ? 'Iniciando...'
                : completed
                    ? 'Iniciar novo treino'
                    : 'Iniciar treino',
            icon: Icons.play_arrow_rounded,
            onTap: starting ? () {} : onStart,
          );

          if (constraints.maxWidth < 590) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: <Widget>[copy, const SizedBox(height: 16), button],
            );
          }

          return Row(
            children: <Widget>[
              Expanded(child: copy),
              const SizedBox(width: 16),
              button,
            ],
          );
        },
      ),
    );
  }
}

class _ExercisesCard extends StatelessWidget {
  const _ExercisesCard({
    required this.snapshot,
    required this.busyExercises,
    required this.onToggle,
  });

  final StudentWorkoutSnapshot snapshot;
  final Set<String> busyExercises;
  final ValueChanged<StudentWorkoutExercise> onToggle;

  @override
  Widget build(BuildContext context) {
    return FitCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const Text(
            'Exercícios',
            style: TextStyle(
              color: FitColors.text,
              fontSize: 21,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            snapshot.inProgress
                ? 'Toque para marcar ou desmarcar. Cada alteração é salva.'
                : 'Inicie um treino para registrar sua execução.',
            style: const TextStyle(color: FitColors.muted, fontSize: 12),
          ),
          const SizedBox(height: 16),
          if (snapshot.exercises.isEmpty)
            const Text(
              'Nenhum exercício publicado neste treino.',
              style: TextStyle(color: FitColors.muted),
            )
          else
            ...snapshot.exercises.map(
              (StudentWorkoutExercise exercise) => Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: _ExerciseItem(
                  exercise: exercise,
                  enabled: snapshot.inProgress,
                  busy: busyExercises.contains(exercise.id),
                  onTap: () => onToggle(exercise),
                ),
              ),
            ),
        ],
      ),
    );
  }
}

class _ExerciseItem extends StatelessWidget {
  const _ExerciseItem({
    required this.exercise,
    required this.enabled,
    required this.busy,
    required this.onTap,
  });

  final StudentWorkoutExercise exercise;
  final bool enabled;
  final bool busy;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      borderRadius: BorderRadius.circular(18),
      onTap: enabled && !busy ? onTap : null,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: FitColors.cardSoft,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(
            color: exercise.completed
                ? FitColors.gold.withValues(alpha: 0.75)
                : FitColors.border,
          ),
        ),
        child: Row(
          children: <Widget>[
            if (busy)
              const SizedBox(
                width: 24,
                height: 24,
                child: CircularProgressIndicator(strokeWidth: 2),
              )
            else
              Icon(
                exercise.completed
                    ? Icons.check_circle_rounded
                    : Icons.circle_outlined,
                color: exercise.completed ? FitColors.goldSoft : FitColors.muted,
              ),
            const SizedBox(width: 13),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text(
                    exercise.name,
                    style: const TextStyle(
                      color: FitColors.text,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                  if (exercise.prescription.isNotEmpty) ...<Widget>[
                    const SizedBox(height: 5),
                    Text(
                      exercise.prescription,
                      style: const TextStyle(
                        color: FitColors.muted,
                        height: 1.35,
                      ),
                    ),
                  ],
                ],
              ),
            ),
            if (!enabled)
              const Icon(Icons.lock_outline_rounded, color: FitColors.muted, size: 18),
          ],
        ),
      ),
    );
  }
}

class _RestTimerCard extends StatelessWidget {
  const _RestTimerCard({
    required this.time,
    required this.initialSeconds,
    required this.remainingSeconds,
    required this.onCancel,
  });

  final String time;
  final int initialSeconds;
  final int remainingSeconds;
  final VoidCallback onCancel;

  @override
  Widget build(BuildContext context) {
    final double progress = initialSeconds <= 0
        ? 0
        : remainingSeconds / initialSeconds;

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: FitColors.gold.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: FitColors.gold.withValues(alpha: 0.35)),
      ),
      child: Row(
        children: <Widget>[
          const Icon(Icons.timer_rounded, color: FitColors.goldSoft, size: 30),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  time,
                  style: const TextStyle(
                    color: FitColors.text,
                    fontSize: 25,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const SizedBox(height: 7),
                LinearProgressIndicator(
                  value: progress.clamp(0.0, 1.0).toDouble(),
                  color: FitColors.goldSoft,
                  backgroundColor: FitColors.border,
                ),
              ],
            ),
          ),
          const SizedBox(width: 10),
          IconButton(
            tooltip: 'Encerrar descanso',
            onPressed: onCancel,
            icon: const Icon(Icons.close_rounded, color: FitColors.text),
          ),
        ],
      ),
    );
  }
}

class _HistoryCard extends StatelessWidget {
  const _HistoryCard({required this.history});

  final List<StudentWorkoutHistoryItem> history;

  String _date(DateTime value) {
    final DateTime local = value.toLocal();
    return '${local.day.toString().padLeft(2, '0')}/${local.month.toString().padLeft(2, '0')}/${local.year}';
  }

  @override
  Widget build(BuildContext context) {
    return FitCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const Text(
            'Histórico',
            style: TextStyle(
              color: FitColors.text,
              fontSize: 21,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 14),
          if (history.isEmpty)
            const Text(
              'Seu histórico aparecerá aqui depois que você iniciar o primeiro treino.',
              style: TextStyle(color: FitColors.muted, height: 1.4),
            )
          else
            ...history.take(6).map(
              (StudentWorkoutHistoryItem item) => Container(
                margin: const EdgeInsets.only(bottom: 9),
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: FitColors.cardSoft,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: FitColors.border),
                ),
                child: Row(
                  children: <Widget>[
                    Icon(
                      item.status == 'completed'
                          ? Icons.check_circle_rounded
                          : Icons.timelapse_rounded,
                      color: item.status == 'completed'
                          ? FitColors.goldSoft
                          : FitColors.muted,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: <Widget>[
                          Text(
                            item.planName,
                            style: const TextStyle(
                              color: FitColors.text,
                              fontWeight: FontWeight.w900,
                            ),
                          ),
                          const SizedBox(height: 3),
                          Text(
                            '${_date(item.startedAt)} • ${item.completedExercises}/${item.totalExercises} exercícios',
                            style: const TextStyle(
                              color: FitColors.muted,
                              fontSize: 12,
                            ),
                          ),
                        ],
                      ),
                    ),
                    Text(
                      '${item.percent}%',
                      style: const TextStyle(
                        color: FitColors.goldSoft,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }
}

class _Metric extends StatelessWidget {
  const _Metric({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 150,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: FitColors.cardSoft,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: FitColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(
            value,
            style: const TextStyle(
              color: FitColors.goldSoft,
              fontSize: 24,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 4),
          Text(label, style: const TextStyle(color: FitColors.muted, fontSize: 12)),
        ],
      ),
    );
  }
}

class _InfoCard extends StatelessWidget {
  const _InfoCard({
    required this.icon,
    required this.title,
    required this.text,
  });

  final IconData icon;
  final String title;
  final String text;

  @override
  Widget build(BuildContext context) {
    return FitCard(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Icon(icon, color: FitColors.goldSoft, size: 28),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  title,
                  style: const TextStyle(
                    color: FitColors.text,
                    fontSize: 17,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const SizedBox(height: 6),
                Text(text, style: const TextStyle(color: FitColors.muted, height: 1.4)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _StudentMessagePage extends StatelessWidget {
  const _StudentMessagePage({
    required this.icon,
    required this.title,
    required this.text,
    this.loading = false,
    this.action,
  });

  final IconData icon;
  final String title;
  final String text;
  final bool loading;
  final Widget? action;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: FitColors.bg,
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(22),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 580),
              child: FitCard(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: <Widget>[
                    if (loading)
                      const CircularProgressIndicator(color: FitColors.gold)
                    else
                      Icon(icon, color: FitColors.goldSoft, size: 46),
                    const SizedBox(height: 18),
                    Text(
                      title,
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        color: FitColors.text,
                        fontSize: 24,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      text,
                      textAlign: TextAlign.center,
                      style: const TextStyle(color: FitColors.muted, height: 1.45),
                    ),
                    if (action != null) ...<Widget>[
                      const SizedBox(height: 18),
                      action!,
                    ],
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
