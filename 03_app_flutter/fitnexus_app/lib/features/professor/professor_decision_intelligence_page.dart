import 'package:flutter/material.dart';

import 'professor_data_repository.dart';
import 'professor_decision_intelligence_repository.dart';
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
  String? _studentId;
  DecisionIntelligenceBrief? _brief;
  bool _loading = true;
  bool _generating = false;
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
      if (selected != null) await _loadHistory(selected);
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

  Future<void> _generate() async {
    final String studentId = _studentId ?? '';
    if (studentId.isEmpty || _generating) return;
    setState(() {
      _generating = true;
      _error = null;
    });
    try {
      final DecisionIntelligenceBrief brief =
          await _intelligence.generateBrief(studentId);
      if (!mounted) return;
      setState(() => _brief = brief);
      await _loadHistory(studentId);
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
        ),
      ),
    );

    if (!mounted || changed != true) return;
    await _generate();
  }

  String _friendlyError(Object error) {
    final String text = error.toString();
    if (text.contains('ORG_MANAGER_REQUIRED')) {
      return 'Somente owner/admin pode gerar um Decision Brief.';
    }
    return 'Não foi possível gerar a análise agora. ${text.replaceFirst('Exception: ', '')}';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF050505),
      body: SafeArea(
        child: RefreshIndicator(
          color: const Color(0xFFE1B92F),
          onRefresh: () async {
            final String? studentId = _studentId;
            if (studentId == null) {
              await _bootstrap();
            } else {
              await _loadHistory(studentId);
            }
          },
          child: ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.fromLTRB(20, 22, 20, 120),
            children: <Widget>[
              const Text(
                'DECISION INTELLIGENCE',
                style: TextStyle(
                  color: Color(0xFFFFD45A),
                  fontSize: 12,
                  fontWeight: FontWeight.w900,
                  letterSpacing: 1.1,
                ),
              ),
              const SizedBox(height: 8),
              const Text(
                'Sinais viram recomendações explicáveis — nunca alterações silenciosas',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 28,
                  height: 1.08,
                  fontWeight: FontWeight.w900,
                ),
              ),
              const SizedBox(height: 7),
              const Text(
                'O motor cruza aderência, execuções, feedback, treino ativo e Smart Templates. Se houver um candidato seguro, ele mostra o diff antes de levar a proposta ao Decision Studio.',
                style: TextStyle(color: Color(0xFFAAAAAA), height: 1.45),
              ),
              const SizedBox(height: 20),
              if (_loading)
                const SizedBox(
                  height: 260,
                  child: Center(child: CircularProgressIndicator()),
                )
              else if (_students.isEmpty)
                const _Notice(
                  icon: Icons.groups_outlined,
                  title: 'Nenhum aluno cadastrado',
                  text: 'Cadastre um aluno para gerar o primeiro Decision Brief.',
                )
              else ...<Widget>[
                _Controls(
                  students: _students,
                  studentId: _studentId,
                  generating: _generating,
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
                  const SizedBox(height: 14),
                  _Notice(
                    icon: Icons.error_outline_rounded,
                    title: 'Análise indisponível',
                    text: _error!,
                    error: true,
                  ),
                ],
                if (_brief != null) ...<Widget>[
                  const SizedBox(height: 18),
                  _BriefCard(
                    brief: _brief!,
                    onOpenStudio: () => _openStudio(_brief!),
                  ),
                ],
                const SizedBox(height: 18),
                _HistoryCard(history: _history),
              ],
            ],
          ),
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
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF111111),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFF2C2A22)),
      ),
      child: LayoutBuilder(
        builder: (BuildContext buildContext, BoxConstraints constraints) {
          final Widget selector = DropdownButtonFormField<String>(
            initialValue: studentId,
            decoration: const InputDecoration(
              labelText: 'Aluno',
              border: OutlineInputBorder(),
            ),
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
            style: FilledButton.styleFrom(
              backgroundColor: const Color(0xFFE1B92F),
              foregroundColor: Colors.black,
              padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 17),
              textStyle: const TextStyle(fontWeight: FontWeight.w900),
            ),
            icon: generating
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.psychology_alt_rounded),
            label: Text(generating ? 'Analisando...' : 'Gerar Decision Brief'),
          );

          if (constraints.maxWidth < 720) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: <Widget>[selector, const SizedBox(height: 12), button],
            );
          }
          return Row(
            children: <Widget>[
              Expanded(child: selector),
              const SizedBox(width: 12),
              button,
            ],
          );
        },
      ),
    );
  }
}

class _BriefCard extends StatelessWidget {
  const _BriefCard({required this.brief, required this.onOpenStudio});

  final DecisionIntelligenceBrief brief;
  final VoidCallback onOpenStudio;

  @override
  Widget build(BuildContext context) {
    final _RiskVisual risk = _riskVisual(brief.riskLevel);
    final DecisionCandidate? candidate = brief.candidate;

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFF0F0F0F),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: risk.color.withValues(alpha: 0.45)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Wrap(
            spacing: 10,
            runSpacing: 10,
            crossAxisAlignment: WrapCrossAlignment.center,
            children: <Widget>[
              _Tag(label: risk.label, color: risk.color),
              _Tag(
                label: 'Confiança ${brief.confidenceScore}%',
                color: const Color(0xFFFFD45A),
              ),
              _Tag(
                label: brief.engineMode == 'deterministic_fallback'
                    ? 'Motor determinístico'
                    : brief.engineMode,
                color: const Color(0xFF8EBBFF),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Text(
            brief.recommendationTitle,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 24,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 7),
          Text(
            brief.recommendationReason,
            style: const TextStyle(color: Color(0xFFCCCCCC), height: 1.45),
          ),
          const SizedBox(height: 16),
          const Text(
            'Evidências usadas',
            style: TextStyle(
              color: Color(0xFFFFD45A),
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 9),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: brief.evidence
                .map(
                  (DecisionEvidence item) => _EvidenceChip(
                    label: item.label,
                    value: item.displayValue,
                  ),
                )
                .toList(growable: false),
          ),
          const SizedBox(height: 18),
          if (candidate != null) ...<Widget>[
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFF161306),
                borderRadius: BorderRadius.circular(18),
                border: Border.all(
                  color: const Color(0xFFE1B92F).withValues(alpha: 0.35),
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: <Widget>[
                  Text(
                    'Candidato: ${candidate.templateName}',
                    style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.w900,
                      fontSize: 18,
                    ),
                  ),
                  const SizedBox(height: 5),
                  Text(
                    '${candidate.objective} • ${candidate.level} • ${candidate.exercises.length} exercícios',
                    style: const TextStyle(color: Color(0xFFAAAAAA)),
                  ),
                  const SizedBox(height: 12),
                  _DiffSummary(diff: candidate.diff),
                  const SizedBox(height: 14),
                  FilledButton.icon(
                    onPressed: onOpenStudio,
                    style: FilledButton.styleFrom(
                      backgroundColor: const Color(0xFFE1B92F),
                      foregroundColor: Colors.black,
                      padding: const EdgeInsets.symmetric(vertical: 15),
                      textStyle: const TextStyle(fontWeight: FontWeight.w900),
                    ),
                    icon: const Icon(Icons.rule_rounded),
                    label: const Text('Levar candidato ao Decision Studio'),
                  ),
                ],
              ),
            ),
          ] else
            _Notice(
              icon: Icons.shield_outlined,
              title: 'Sem candidato automático',
              text: _blockReason(brief.candidateBlockReason),
            ),
          const SizedBox(height: 14),
          const Text(
            'Guardrail BlackGold: esta análise nunca aplica treino, nunca diagnostica e nunca substitui a decisão profissional. Qualquer commit exige preview, diff e confirmação humana.',
            style: TextStyle(color: Color(0xFF888888), fontSize: 11, height: 1.4),
          ),
        ],
      ),
    );
  }
}

class _DiffSummary extends StatelessWidget {
  const _DiffSummary({required this.diff});

  final dynamic diff;

  @override
  Widget build(BuildContext context) {
    final List<String> added = diff.added as List<String>;
    final List<String> removed = diff.removed as List<String>;
    final List<String> changed = diff.changed as List<String>;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: <Widget>[
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: <Widget>[
            _Tag(label: '+${added.length} adicionados', color: const Color(0xFF75E39B)),
            _Tag(label: '-${removed.length} removidos', color: const Color(0xFFFF7474)),
            _Tag(label: '${changed.length} alterados', color: const Color(0xFFFFC85A)),
          ],
        ),
        if (added.isNotEmpty || removed.isNotEmpty || changed.isNotEmpty) ...<Widget>[
          const SizedBox(height: 10),
          ...added.take(3).map((String item) => Text('+ $item', style: const TextStyle(color: Color(0xFF9DE6B4)))),
          ...removed.take(3).map((String item) => Text('- $item', style: const TextStyle(color: Color(0xFFFF9A9A)))),
          ...changed.take(3).map((String item) => Text('~ $item', style: const TextStyle(color: Color(0xFFFFD58A)))),
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
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFF111111),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFF2C2A22)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          const Text(
            'Histórico de análises',
            style: TextStyle(
              color: Colors.white,
              fontSize: 18,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 5),
          const Text(
            'Cada geração fica registrada como evidência de decisão; nenhuma delas altera a prescrição.',
            style: TextStyle(color: Color(0xFF999999), fontSize: 12),
          ),
          const SizedBox(height: 14),
          if (history.isEmpty)
            const Text(
              'Nenhum Decision Brief gerado ainda.',
              style: TextStyle(color: Color(0xFF888888)),
            )
          else
            ...history.map(
              (DecisionIntelligenceHistoryItem item) => Padding(
                padding: const EdgeInsets.only(bottom: 9),
                child: Row(
                  children: <Widget>[
                    Icon(
                      _riskVisual(item.brief.riskLevel).icon,
                      color: _riskVisual(item.brief.riskLevel).color,
                      size: 18,
                    ),
                    const SizedBox(width: 9),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: <Widget>[
                          Text(
                            item.brief.recommendationTitle,
                            style: const TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.w800,
                              fontSize: 12,
                            ),
                          ),
                          Text(
                            '${_formatDate(item.createdAt)} • confiança ${item.brief.confidenceScore}% • run ${_short(item.runId)}',
                            style: const TextStyle(
                              color: Color(0xFF888888),
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
        ],
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
        color: const Color(0xFF191919),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text.rich(
        TextSpan(
          children: <InlineSpan>[
            TextSpan(
              text: '$label: ',
              style: const TextStyle(
                color: Color(0xFF888888),
                fontSize: 11,
              ),
            ),
            TextSpan(
              text: value,
              style: const TextStyle(
                color: Color(0xFFE6E6E6),
                fontSize: 11,
                fontWeight: FontWeight.w800,
              ),
            ),
          ],
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
        borderRadius: BorderRadius.circular(999),
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
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: error ? const Color(0xFF351515) : const Color(0xFF111111),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Icon(
            icon,
            color: error ? const Color(0xFFFF9A9A) : const Color(0xFFFFD45A),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  title,
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  text,
                  style: const TextStyle(
                    color: Color(0xFFBBBBBB),
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

class _RiskVisual {
  const _RiskVisual(this.label, this.color, this.icon);

  final String label;
  final Color color;
  final IconData icon;
}

_RiskVisual _riskVisual(String level) {
  return switch (level) {
    'high' => const _RiskVisual('PRIORIDADE ALTA', Color(0xFFFF7474), Icons.priority_high_rounded),
    'medium' => const _RiskVisual('ATENÇÃO', Color(0xFFFFC85A), Icons.visibility_rounded),
    'low' => const _RiskVisual('SINAL SAUDÁVEL', Color(0xFF75E39B), Icons.check_circle_outline_rounded),
    _ => const _RiskVisual('NOVO', Color(0xFF8EBBFF), Icons.fiber_new_rounded),
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
    _ => 'Nenhum candidato de alteração foi liberado pelos guardrails desta análise.',
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
