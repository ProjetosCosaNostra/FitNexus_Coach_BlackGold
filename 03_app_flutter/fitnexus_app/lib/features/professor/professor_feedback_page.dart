import 'package:flutter/material.dart';

import 'professor_feedback_repository.dart';

class ProfessorFeedbackPage extends StatefulWidget {
  const ProfessorFeedbackPage({super.key});

  @override
  State<ProfessorFeedbackPage> createState() => _ProfessorFeedbackPageState();
}

class _ProfessorFeedbackPageState extends State<ProfessorFeedbackPage> {
  final ProfessorFeedbackRepository _repository = ProfessorFeedbackRepository.instance;

  ProfessorFeedbackSnapshot? _snapshot;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _reload();
  }

  Future<void> _reload() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final ProfessorFeedbackSnapshot snapshot = await _repository.fetchFeed();
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
    final ProfessorFeedbackSnapshot? snapshot = _snapshot;

    return Scaffold(
      backgroundColor: const Color(0xFF050505),
      body: SafeArea(
        child: RefreshIndicator(
          color: const Color(0xFFE1B92F),
          onRefresh: _reload,
          child: ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.fromLTRB(20, 22, 20, 120),
            children: <Widget>[
              _Header(loading: _loading, onRefresh: _reload),
              const SizedBox(height: 20),
              if (_error != null)
                _Message(
                  icon: Icons.error_outline_rounded,
                  title: 'Não foi possível carregar os feedbacks',
                  text: _error!,
                )
              else if (_loading && snapshot == null)
                const SizedBox(
                  height: 260,
                  child: Center(child: CircularProgressIndicator()),
                )
              else if (snapshot != null) ...<Widget>[
                _Summary(snapshot: snapshot),
                const SizedBox(height: 18),
                if (snapshot.items.isEmpty)
                  const _Message(
                    icon: Icons.forum_outlined,
                    title: 'Nenhum feedback recebido ainda',
                    text: 'Depois que um aluno concluir o treino e responder “Como foi o treino?”, os sinais aparecerão aqui.',
                  )
                else
                  ...snapshot.items.map(
                    (ProfessorFeedbackRecord item) => Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: _FeedbackCard(item: item),
                    ),
                  ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.loading, required this.onRefresh});

  final bool loading;
  final Future<void> Function() onRefresh;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 14,
      runSpacing: 12,
      alignment: WrapAlignment.spaceBetween,
      crossAxisAlignment: WrapCrossAlignment.center,
      children: <Widget>[
        const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(
              'FEEDBACK PÓS-TREINO',
              style: TextStyle(
                color: Color(0xFFFFD45A),
                fontWeight: FontWeight.w900,
                fontSize: 12,
                letterSpacing: 1.0,
              ),
            ),
            SizedBox(height: 7),
            Text(
              'O que o aluno sentiu vira sinal de decisão',
              style: TextStyle(
                color: Colors.white,
                fontSize: 28,
                fontWeight: FontWeight.w900,
              ),
            ),
            SizedBox(height: 6),
            Text(
              'Esforço, desconforto e energia alimentam o Risk Radar sem alterar prescrições automaticamente.',
              style: TextStyle(color: Color(0xFFAAAAAA), height: 1.4),
            ),
          ],
        ),
        IconButton.filledTonal(
          tooltip: 'Atualizar feedbacks',
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

class _Summary extends StatelessWidget {
  const _Summary({required this.snapshot});

  final ProfessorFeedbackSnapshot snapshot;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 12,
      runSpacing: 12,
      children: <Widget>[
        _Metric(label: 'Feedbacks', value: '${snapshot.items.length}'),
        _Metric(label: 'Sinais altos', value: '${snapshot.highSignals}'),
        _Metric(label: 'Dor ≥ 7', value: '${snapshot.painAlerts}'),
      ],
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
      width: 180,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF111111),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFF2C2A22)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(
            value,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 26,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 3),
          Text(
            label,
            style: const TextStyle(
              color: Color(0xFFFFD45A),
              fontWeight: FontWeight.w800,
            ),
          ),
        ],
      ),
    );
  }
}

class _FeedbackCard extends StatelessWidget {
  const _FeedbackCard({required this.item});

  final ProfessorFeedbackRecord item;

  @override
  Widget build(BuildContext context) {
    final Color signalColor = switch (item.riskSignal) {
      'high' => const Color(0xFFFF7474),
      'medium' => const Color(0xFFFFC85A),
      _ => const Color(0xFF75E39B),
    };

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFF111111),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: signalColor.withValues(alpha: 0.42)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            children: <Widget>[
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      item.studentName,
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.w900,
                        fontSize: 17,
                      ),
                    ),
                    Text(
                      item.planName,
                      style: const TextStyle(color: Color(0xFFAAAAAA)),
                    ),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                decoration: BoxDecoration(
                  color: signalColor.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(999),
                ),
                child: Text(
                  item.riskSignal == 'high'
                      ? 'PRIORIDADE ALTA'
                      : item.riskSignal == 'medium'
                          ? 'ATENÇÃO'
                          : 'SEM ALERTA',
                  style: TextStyle(
                    color: signalColor,
                    fontSize: 11,
                    fontWeight: FontWeight.w900,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: <Widget>[
              _Chip(label: 'Esforço ${item.perceivedExertion}/10'),
              _Chip(label: 'Dor ${item.painScore}/10'),
              _Chip(label: 'Energia ${item.energyScore}/5'),
            ],
          ),
          if ((item.painLocation ?? '').isNotEmpty) ...<Widget>[
            const SizedBox(height: 12),
            Text(
              'Local do desconforto: ${item.painLocation}',
              style: const TextStyle(
                color: Color(0xFFFFC85A),
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
          if ((item.note ?? '').isNotEmpty) ...<Widget>[
            const SizedBox(height: 10),
            Text(
              item.note!,
              style: const TextStyle(color: Color(0xFFD5D5D5), height: 1.45),
            ),
          ],
          const SizedBox(height: 12),
          Text(
            _formatDate(item.submittedAt),
            style: const TextStyle(color: Color(0xFF888888), fontSize: 11),
          ),
        ],
      ),
    );
  }
}

class _Chip extends StatelessWidget {
  const _Chip({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
      decoration: BoxDecoration(
        color: const Color(0xFF1A1A1A),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        label,
        style: const TextStyle(color: Color(0xFFDDDDDD), fontSize: 12),
      ),
    );
  }
}

class _Message extends StatelessWidget {
  const _Message({
    required this.icon,
    required this.title,
    required this.text,
  });

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
          Icon(icon, color: const Color(0xFFE1B92F), size: 38),
          const SizedBox(height: 12),
          Text(
            title,
            textAlign: TextAlign.center,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 19,
              fontWeight: FontWeight.w900,
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
  String two(int n) => n.toString().padLeft(2, '0');
  return '${two(local.day)}/${two(local.month)}/${local.year} • ${two(local.hour)}:${two(local.minute)}';
}
