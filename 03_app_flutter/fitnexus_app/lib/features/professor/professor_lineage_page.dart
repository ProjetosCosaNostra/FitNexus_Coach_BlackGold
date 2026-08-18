import 'package:flutter/material.dart';

import 'professor_data_repository.dart';
import 'professor_lineage_repository.dart';

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
  String? _error;

  @override
  void initState() {
    super.initState();
    _bootstrap();
  }

  Future<void> _bootstrap() async {
    setState(() {
      _loading = true;
      _error = null;
    });
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
      final TrainingLineageSnapshot snapshot = await _lineage.fetchLineage(studentId);
      if (!mounted) return;
      setState(() => _snapshot = snapshot);
    } catch (error) {
      if (!mounted) return;
      setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF050505),
      appBar: AppBar(
        backgroundColor: const Color(0xFF090909),
        foregroundColor: Colors.white,
        title: const Text(
          'Training Lineage',
          style: TextStyle(fontWeight: FontWeight.w900),
        ),
      ),
      body: SafeArea(
        child: RefreshIndicator(
          color: const Color(0xFFE1B92F),
          onRefresh: () async {
            final String? studentId = _studentId;
            if (studentId == null) {
              await _bootstrap();
            } else {
              await _loadLineage(studentId);
            }
          },
          child: ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.fromLTRB(20, 22, 20, 80),
            children: <Widget>[
              const Text(
                'DECISÕES EXPLICÁVEIS',
                style: TextStyle(
                  color: Color(0xFFFFD45A),
                  fontSize: 12,
                  fontWeight: FontWeight.w900,
                  letterSpacing: 1.1,
                ),
              ),
              const SizedBox(height: 8),
              const Text(
                'Veja de onde cada treino veio e o que mudou',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 28,
                  height: 1.1,
                  fontWeight: FontWeight.w900,
                ),
              ),
              const SizedBox(height: 7),
              const Text(
                'O FitNexus preserva a cadeia de prescrições. Nenhuma revisão apaga a anterior.',
                style: TextStyle(color: Color(0xFFAAAAAA), height: 1.45),
              ),
              const SizedBox(height: 20),
              if (_students.isNotEmpty)
                DropdownButtonFormField<String>(
                  initialValue: _studentId,
                  decoration: const InputDecoration(
                    labelText: 'Aluno',
                    border: OutlineInputBorder(),
                  ),
                  items: _students
                      .map(
                        (StudentRecord student) => DropdownMenuItem<String>(
                          value: student.id,
                          child: Text(student.name),
                        ),
                      )
                      .toList(growable: false),
                  onChanged: _loading
                      ? null
                      : (String? value) {
                          if (value == null) return;
                          setState(() => _studentId = value);
                          _loadLineage(value);
                        },
                ),
              const SizedBox(height: 18),
              if (_error != null)
                _Message(
                  icon: Icons.error_outline_rounded,
                  title: 'Não foi possível carregar a linhagem',
                  text: _error!,
                )
              else if (_loading && _snapshot == null)
                const SizedBox(
                  height: 280,
                  child: Center(child: CircularProgressIndicator()),
                )
              else if (_students.isEmpty)
                const _Message(
                  icon: Icons.groups_outlined,
                  title: 'Nenhum aluno cadastrado',
                  text: 'Cadastre um aluno e crie a primeira prescrição para iniciar a linhagem.',
                )
              else if ((_snapshot?.items ?? const <TrainingLineageRecord>[]).isEmpty)
                const _Message(
                  icon: Icons.account_tree_outlined,
                  title: 'Nenhuma prescrição registrada',
                  text: 'A primeira criação de treino aparecerá aqui como origem da linhagem.',
                )
              else
                ..._snapshot!.items.map(
                  (TrainingLineageRecord record) => Padding(
                    padding: const EdgeInsets.only(bottom: 14),
                    child: _LineageCard(record: record),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

class _LineageCard extends StatelessWidget {
  const _LineageCard({required this.record});

  final TrainingLineageRecord record;

  @override
  Widget build(BuildContext context) {
    final Color accent = record.isActive
        ? const Color(0xFF75E39B)
        : const Color(0xFFE1B92F);

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFF111111),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: accent.withValues(alpha: 0.38)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            children: <Widget>[
              Container(
                width: 42,
                height: 42,
                decoration: BoxDecoration(
                  color: accent.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(Icons.account_tree_rounded, color: accent),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      record.planName,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 17,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      '${record.decisionLabel} • ${_formatDate(record.createdAt)}',
                      style: const TextStyle(color: Color(0xFFAAAAAA), fontSize: 12),
                    ),
                  ],
                ),
              ),
              if (record.isActive)
                const _Tag(label: 'ATIVO', color: Color(0xFF75E39B)),
            ],
          ),
          const SizedBox(height: 14),
          Text(
            record.decisionReason,
            style: const TextStyle(
              color: Color(0xFFE6E6E6),
              height: 1.45,
              fontWeight: FontWeight.w700,
            ),
          ),
          if ((record.sourceTemplateName ?? '').isNotEmpty) ...<Widget>[
            const SizedBox(height: 10),
            Text(
              'Origem: Smart Template “${record.sourceTemplateName}”',
              style: const TextStyle(
                color: Color(0xFFFFD45A),
                fontSize: 12,
                fontWeight: FontWeight.w800,
              ),
            ),
          ],
          if ((record.predecessorPlanName ?? '').isNotEmpty) ...<Widget>[
            const SizedBox(height: 8),
            Text(
              'Substituiu: ${record.predecessorPlanName}',
              style: const TextStyle(color: Color(0xFFAAAAAA), fontSize: 12),
            ),
          ],
          const SizedBox(height: 14),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: <Widget>[
              _Tag(label: '${record.exerciseCount} exercícios', color: const Color(0xFFE1B92F)),
              if (record.diff.addedCount > 0)
                _Tag(label: '+${record.diff.addedCount} adicionados', color: const Color(0xFF75E39B)),
              if (record.diff.removedCount > 0)
                _Tag(label: '-${record.diff.removedCount} removidos', color: const Color(0xFFFF7474)),
              if (record.diff.changedCount > 0)
                _Tag(label: '${record.diff.changedCount} alterados', color: const Color(0xFFFFC85A)),
            ],
          ),
          if (record.diff.hasChanges) ...<Widget>[
            const SizedBox(height: 14),
            ExpansionTile(
              tilePadding: EdgeInsets.zero,
              childrenPadding: EdgeInsets.zero,
              collapsedIconColor: const Color(0xFFFFD45A),
              iconColor: const Color(0xFFFFD45A),
              title: const Text(
                'Ver diferença da versão anterior',
                style: TextStyle(
                  color: Color(0xFFFFD45A),
                  fontWeight: FontWeight.w800,
                  fontSize: 13,
                ),
              ),
              children: <Widget>[
                _DiffSection(title: 'Adicionados', items: record.diff.added),
                _DiffSection(title: 'Removidos', items: record.diff.removed),
                _DiffSection(title: 'Alterados', items: record.diff.changed),
              ],
            ),
          ],
        ],
      ),
    );
  }
}

class _DiffSection extends StatelessWidget {
  const _DiffSection({required this.title, required this.items});

  final String title;
  final List<String> items;

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Text(
            title,
            style: const TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.w900,
              fontSize: 12,
            ),
          ),
          const SizedBox(height: 5),
          ...items.map(
            (String item) => Padding(
              padding: const EdgeInsets.only(bottom: 3),
              child: Text(
                '• $item',
                style: const TextStyle(color: Color(0xFFBBBBBB), fontSize: 12),
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
        color: color.withValues(alpha: 0.10),
        borderRadius: BorderRadius.circular(999),
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

class _Message extends StatelessWidget {
  const _Message({required this.icon, required this.title, required this.text});

  final IconData icon;
  final String title;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(28),
      decoration: BoxDecoration(
        color: const Color(0xFF111111),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFF2C2A22)),
      ),
      child: Column(
        children: <Widget>[
          Icon(icon, color: const Color(0xFFE1B92F), size: 40),
          const SizedBox(height: 12),
          Text(
            title,
            textAlign: TextAlign.center,
            style: const TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.w900,
              fontSize: 19,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            text,
            textAlign: TextAlign.center,
            style: const TextStyle(color: Color(0xFFAAAAAA), height: 1.4),
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
