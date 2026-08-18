import 'package:flutter/material.dart';

import '../shared/fitnexus_ui.dart';
import 'student_feedback_repository.dart';

class StudentFeedbackSheet extends StatefulWidget {
  const StudentFeedbackSheet({
    super.key,
    required this.token,
  });

  final String token;

  @override
  State<StudentFeedbackSheet> createState() => _StudentFeedbackSheetState();
}

class _StudentFeedbackSheetState extends State<StudentFeedbackSheet> {
  final StudentFeedbackRepository _repository = StudentFeedbackRepository.instance;
  final TextEditingController _painLocationController = TextEditingController();
  final TextEditingController _noteController = TextEditingController();

  StudentFeedbackContext? _context;
  bool _loading = true;
  bool _saving = false;
  String? _error;
  int _exertion = 6;
  int _pain = 0;
  int _energy = 3;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _painLocationController.dispose();
    _noteController.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final StudentFeedbackContext context =
          await _repository.fetchContext(widget.token);
      if (!mounted) return;
      _context = context;
      if (context.submitted) {
        _exertion = context.perceivedExertion ?? _exertion;
        _pain = context.painScore ?? _pain;
        _energy = context.energyScore ?? _energy;
        _painLocationController.text = context.painLocation ?? '';
        _noteController.text = context.note ?? '';
      }
      setState(() {});
    } catch (error) {
      if (!mounted) return;
      setState(() => _error = _friendlyError(error));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _submit() async {
    final StudentFeedbackContext? context = _context;
    final String sessionId = context?.sessionId ?? '';
    if (_saving || sessionId.isEmpty) return;

    setState(() {
      _saving = true;
      _error = null;
    });

    try {
      final StudentFeedbackResult result = await _repository.submit(
        token: widget.token,
        sessionId: sessionId,
        perceivedExertion: _exertion,
        painScore: _pain,
        energyScore: _energy,
        painLocation: _painLocationController.text,
        note: _noteController.text,
      );
      if (!mounted) return;
      await _load();
      if (!mounted) return;
      final String message = result.riskSignal == 'high'
          ? 'Feedback salvo. Seu professor verá este sinal com prioridade.'
          : 'Feedback salvo e enviado ao acompanhamento do seu professor.';
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          behavior: SnackBarBehavior.floating,
          backgroundColor: FitColors.card,
          content: Text(message),
        ),
      );
    } catch (error) {
      if (!mounted) return;
      setState(() => _error = _friendlyError(error));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  String _friendlyError(Object error) {
    final String text = error.toString();
    if (text.contains('STUDENT_ACCESS_INVALID')) {
      return 'Este acesso de aluno não é mais válido.';
    }
    if (text.contains('COMPLETED_SESSION_NOT_FOUND')) {
      return 'Conclua o treino antes de enviar o feedback.';
    }
    return 'Não foi possível salvar o feedback agora. Tente novamente.';
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: EdgeInsets.fromLTRB(
          18,
          18,
          18,
          18 + MediaQuery.viewInsetsOf(context).bottom,
        ),
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 760),
          child: _loading
              ? const SizedBox(
                  height: 260,
                  child: Center(child: CircularProgressIndicator()),
                )
              : _buildContent(context),
        ),
      ),
    );
  }

  Widget _buildContent(BuildContext context) {
    final StudentFeedbackContext? feedbackContext = _context;
    if (_error != null && feedbackContext == null) {
      return _Message(
        icon: Icons.error_outline_rounded,
        title: 'Não foi possível abrir o feedback',
        text: _error!,
        action: FilledButton.icon(
          onPressed: _load,
          icon: const Icon(Icons.refresh_rounded),
          label: const Text('Tentar novamente'),
        ),
      );
    }

    if (feedbackContext == null || !feedbackContext.eligible) {
      return const _Message(
        icon: Icons.hourglass_bottom_rounded,
        title: 'Feedback disponível após concluir',
        text: 'Finalize pelo menos uma sessão de treino para contar ao professor como foi a execução.',
      );
    }

    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Row(
            children: <Widget>[
              Container(
                width: 46,
                height: 46,
                decoration: BoxDecoration(
                  color: FitColors.gold,
                  borderRadius: BorderRadius.circular(14),
                ),
                child: const Icon(Icons.forum_rounded, color: Colors.black),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    const Text(
                      'Como foi o treino?',
                      style: TextStyle(
                        color: FitColors.text,
                        fontWeight: FontWeight.w900,
                        fontSize: 22,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      feedbackContext.planName ?? 'Última sessão concluída',
                      style: const TextStyle(color: FitColors.muted),
                    ),
                  ],
                ),
              ),
              IconButton(
                tooltip: 'Fechar',
                onPressed: () => Navigator.of(context).pop(),
                icon: const Icon(Icons.close_rounded),
              ),
            ],
          ),
          const SizedBox(height: 18),
          if (feedbackContext.submitted)
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: const Color(0xFF173221),
                borderRadius: BorderRadius.circular(14),
              ),
              child: const Text(
                'Você já enviou feedback desta sessão. Pode atualizar as respostas se algo precisar ser corrigido.',
                style: TextStyle(color: Color(0xFF9DE6B4), height: 1.4),
              ),
            ),
          if (_error != null) ...<Widget>[
            const SizedBox(height: 12),
            Text(_error!, style: const TextStyle(color: Color(0xFFFF8A8A))),
          ],
          const SizedBox(height: 18),
          _ScoreControl(
            title: 'Esforço percebido',
            subtitle: '1 = muito leve • 10 = máximo',
            value: _exertion,
            min: 1,
            max: 10,
            onChanged: (int value) => setState(() => _exertion = value),
          ),
          const SizedBox(height: 14),
          _ScoreControl(
            title: 'Dor ou desconforto',
            subtitle: '0 = nenhum • 10 = muito forte',
            value: _pain,
            min: 0,
            max: 10,
            onChanged: (int value) => setState(() => _pain = value),
          ),
          if (_pain > 0) ...<Widget>[
            const SizedBox(height: 12),
            TextField(
              controller: _painLocationController,
              maxLength: 120,
              decoration: const InputDecoration(
                labelText: 'Onde sentiu desconforto? (opcional)',
                border: OutlineInputBorder(),
              ),
            ),
          ],
          const SizedBox(height: 14),
          _ScoreControl(
            title: 'Energia durante o treino',
            subtitle: '1 = muito baixa • 5 = excelente',
            value: _energy,
            min: 1,
            max: 5,
            onChanged: (int value) => setState(() => _energy = value),
          ),
          const SizedBox(height: 14),
          TextField(
            controller: _noteController,
            maxLength: 500,
            minLines: 3,
            maxLines: 5,
            decoration: const InputDecoration(
              labelText: 'Observação para o professor (opcional)',
              hintText: 'Ex.: senti a perna pesada no final, mas consegui concluir.',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 6),
          FilledButton.icon(
            onPressed: _saving ? null : _submit,
            style: FilledButton.styleFrom(
              backgroundColor: FitColors.gold,
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
                : const Icon(Icons.send_rounded),
            label: Text(_saving ? 'Salvando...' : 'Enviar feedback'),
          ),
          const SizedBox(height: 10),
          const Text(
            'O feedback vira um sinal de acompanhamento para o professor. O FitNexus não altera seu treino automaticamente.',
            textAlign: TextAlign.center,
            style: TextStyle(color: FitColors.muted, fontSize: 11, height: 1.4),
          ),
        ],
      ),
    );
  }
}

class _ScoreControl extends StatelessWidget {
  const _ScoreControl({
    required this.title,
    required this.subtitle,
    required this.value,
    required this.min,
    required this.max,
    required this.onChanged,
  });

  final String title;
  final String subtitle;
  final int value;
  final int min;
  final int max;
  final ValueChanged<int> onChanged;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFF111111),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF2C2A22)),
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
                      title,
                      style: const TextStyle(
                        color: FitColors.text,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    Text(
                      subtitle,
                      style: const TextStyle(color: FitColors.muted, fontSize: 11),
                    ),
                  ],
                ),
              ),
              Container(
                width: 42,
                height: 42,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: FitColors.gold.withValues(alpha: 0.14),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  '$value',
                  style: const TextStyle(
                    color: FitColors.gold,
                    fontWeight: FontWeight.w900,
                    fontSize: 18,
                  ),
                ),
              ),
            ],
          ),
          Slider(
            value: value.toDouble(),
            min: min.toDouble(),
            max: max.toDouble(),
            divisions: max - min,
            label: '$value',
            onChanged: (double next) => onChanged(next.round()),
          ),
        ],
      ),
    );
  }
}

class _Message extends StatelessWidget {
  const _Message({
    required this.icon,
    required this.title,
    required this.text,
    this.action,
  });

  final IconData icon;
  final String title;
  final String text;
  final Widget? action;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 270,
      child: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            Icon(icon, size: 42, color: FitColors.gold),
            const SizedBox(height: 12),
            Text(
              title,
              textAlign: TextAlign.center,
              style: const TextStyle(
                color: FitColors.text,
                fontWeight: FontWeight.w900,
                fontSize: 20,
              ),
            ),
            const SizedBox(height: 7),
            Text(
              text,
              textAlign: TextAlign.center,
              style: const TextStyle(color: FitColors.muted, height: 1.4),
            ),
            if (action != null) ...<Widget>[
              const SizedBox(height: 14),
              action!,
            ],
          ],
        ),
      ),
    );
  }
}
