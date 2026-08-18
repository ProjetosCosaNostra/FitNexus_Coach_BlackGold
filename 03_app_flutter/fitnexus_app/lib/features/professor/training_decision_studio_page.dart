import 'package:flutter/material.dart';

import 'professor_data_repository.dart';
import 'professor_lineage_repository.dart';

class TrainingDecisionStudioPage extends StatefulWidget {
  const TrainingDecisionStudioPage({super.key, this.initialStudentId});

  final String? initialStudentId;

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
      final String name = (divider < 0 ? line : line.substring(0, divider)).trim();
      final String prescription =
          (divider < 0 ? '' : line.substring(divider + 1)).trim();
      if (name.length < 2) {
        throw const FormatException('Cada exercício precisa ter um nome válido.');
      }
      items.add(TrainingExerciseDraft(name: name, prescription: prescription));
    }
    if (items.isEmpty) {
      throw const FormatException('Informe pelo menos um exercício.');
    }
    return items;
  }

  String _fingerprint(String studentId, List<TrainingExerciseDraft> exercises) {
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
        throw const FormatException('Registre o motivo da decisão antes de confirmar.');
      }

      await _data.createTrainingPlan(
        studentId: studentId,
        name: _nameController.text,
        exercises: exercises,
        nextSession: _nextSessionController.text,
        notes: _notesController.text,
        decisionReason: _reasonController.text,
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
    return text.replaceFirst('FormatException: ', '').replaceFirst('Bad state: ', '');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF050505),
      appBar: AppBar(
        backgroundColor: const Color(0xFF090909),
        title: const Text(
          'Decision Studio',
          style: TextStyle(fontWeight: FontWeight.w900),
        ),
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 22, 20, 80),
          children: <Widget>[
            const Text(
              'PREVIEW → DIFF → CONFIRM',
              style: TextStyle(
                color: Color(0xFFFFD45A),
                fontSize: 12,
                fontWeight: FontWeight.w900,
                letterSpacing: 1.0,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'A decisão fica explicada antes de substituir o treino ativo',
              style: TextStyle(
                color: Colors.white,
                fontSize: 27,
                height: 1.1,
                fontWeight: FontWeight.w900,
              ),
            ),
            const SizedBox(height: 7),
            const Text(
              'O banco só recebe a nova versão depois de uma prévia válida e de uma confirmação humana explícita.',
              style: TextStyle(color: Color(0xFFAAAAAA), height: 1.45),
            ),
            const SizedBox(height: 20),
            if (_loading)
              const Center(child: CircularProgressIndicator())
            else if (_students.isEmpty)
              const _Notice(
                text: 'Cadastre um aluno antes de abrir uma decisão de treino.',
              )
            else ...<Widget>[
              DropdownButtonFormField<String>(
                initialValue: _studentId,
                decoration: const InputDecoration(
                  labelText: 'Aluno',
                  border: OutlineInputBorder(),
                ),
                items: _students
                    .map(
                      (StudentRecord item) => DropdownMenuItem<String>(
                        value: item.id,
                        child: Text(item.name),
                      ),
                    )
                    .toList(growable: false),
                onChanged: _saving
                    ? null
                    : (String? value) {
                        setState(() {
                          _studentId = value;
                          _preview = null;
                          _previewFingerprint = null;
                        });
                      },
              ),
              const SizedBox(height: 14),
              TextField(
                controller: _nameController,
                decoration: const InputDecoration(
                  labelText: 'Nome da nova prescrição',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 14),
              TextField(
                controller: _reasonController,
                maxLength: 500,
                minLines: 2,
                maxLines: 4,
                decoration: const InputDecoration(
                  labelText: 'Por que esta mudança está sendo feita?',
                  hintText: 'Ex.: reduzir volume após feedback de recuperação baixa.',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 14),
              TextField(
                controller: _nextSessionController,
                decoration: const InputDecoration(
                  labelText: 'Próxima sessão (opcional)',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 14),
              TextField(
                controller: _notesController,
                minLines: 2,
                maxLines: 4,
                decoration: const InputDecoration(
                  labelText: 'Notas da prescrição (opcional)',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 14),
              TextField(
                controller: _exercisesController,
                minLines: 6,
                maxLines: 12,
                decoration: const InputDecoration(
                  labelText: 'Exercícios — um por linha',
                  hintText: 'Agachamento | 4x8 • descanso 90s\nRemada | 4x10 • descanso 60s',
                  helperText: 'Formato: exercício | prescrição',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 14),
              OutlinedButton.icon(
                onPressed: _previewing || _saving ? null : _previewDecision,
                icon: _previewing
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.compare_arrows_rounded),
                label: Text(_previewing ? 'Comparando...' : 'Gerar prévia e diferenças'),
              ),
              if (_error != null) ...<Widget>[
                const SizedBox(height: 12),
                _Notice(text: _error!, error: true),
              ],
              if (_preview != null) ...<Widget>[
                const SizedBox(height: 16),
                _PreviewCard(preview: _preview!),
                const SizedBox(height: 14),
                FilledButton.icon(
                  onPressed: _saving ? null : _commitDecision,
                  style: FilledButton.styleFrom(
                    backgroundColor: const Color(0xFFE1B92F),
                    foregroundColor: Colors.black,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    textStyle: const TextStyle(fontWeight: FontWeight.w900),
                  ),
                  icon: _saving
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.verified_rounded),
                  label: Text(_saving ? 'Confirmando...' : 'Confirmar nova versão'),
                ),
              ],
            ],
          ],
        ),
      ),
    );
  }
}

class _PreviewCard extends StatelessWidget {
  const _PreviewCard({required this.preview});

  final TrainingChangePreview preview;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFF111111),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFFE1B92F).withValues(alpha: 0.45)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Text(
            preview.hasPreviousPlan
                ? 'Comparado com: ${preview.activePlanName ?? 'treino ativo'}'
                : 'Primeira prescrição deste aluno',
            style: const TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 12),
          if (!preview.hasChanges)
            const Text(
              'Nenhuma diferença de exercício/prescrição detectada. O motivo ainda ficará registrado se você confirmar.',
              style: TextStyle(color: Color(0xFFAAAAAA), height: 1.4),
            )
          else ...<Widget>[
            _Diff(title: 'Adicionados', items: preview.added, color: const Color(0xFF75E39B)),
            _Diff(title: 'Removidos', items: preview.removed, color: const Color(0xFFFF7474)),
            _Diff(title: 'Alterados', items: preview.changed, color: const Color(0xFFFFC85A)),
          ],
          const SizedBox(height: 10),
          const Text(
            'A prévia não altera o banco. Confirmar cria uma nova versão e preserva a anterior no Training Lineage.',
            style: TextStyle(color: Color(0xFF888888), fontSize: 11, height: 1.4),
          ),
        ],
      ),
    );
  }
}

class _Diff extends StatelessWidget {
  const _Diff({required this.title, required this.items, required this.color});

  final String title;
  final List<String> items;
  final Color color;

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(title, style: TextStyle(color: color, fontWeight: FontWeight.w900)),
          const SizedBox(height: 4),
          ...items.map(
            (String item) => Text(
              '• $item',
              style: const TextStyle(color: Color(0xFFCCCCCC), height: 1.4),
            ),
          ),
        ],
      ),
    );
  }
}

class _Notice extends StatelessWidget {
  const _Notice({required this.text, this.error = false});

  final String text;
  final bool error;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: error ? const Color(0xFF351515) : const Color(0xFF111111),
        borderRadius: BorderRadius.circular(14),
      ),
      child: Text(
        text,
        style: TextStyle(
          color: error ? const Color(0xFFFF9A9A) : const Color(0xFFBBBBBB),
          height: 1.4,
        ),
      ),
    );
  }
}
