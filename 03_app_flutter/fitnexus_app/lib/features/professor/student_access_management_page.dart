import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:qr_flutter/qr_flutter.dart';

import 'professor_data_repository.dart';

class StudentAccessManagementPage extends StatefulWidget {
  const StudentAccessManagementPage({super.key});

  @override
  State<StudentAccessManagementPage> createState() =>
      _StudentAccessManagementPageState();
}

class _StudentAccessManagementPageState
    extends State<StudentAccessManagementPage> {
  final ProfessorDataRepository _repository = ProfessorDataRepository.instance;

  List<StudentRecord> _students = const <StudentRecord>[];
  bool _loading = true;
  String? _error;
  String? _issuingStudentId;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final List<StudentRecord> students = await _repository.fetchStudents();
      if (!mounted) return;
      setState(() => _students = students);
    } catch (error) {
      if (!mounted) return;
      setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  String _studentLink(String token) {
    final String base = Uri.base.toString().split('#').first;
    return '$base#/student?token=${Uri.encodeQueryComponent(token)}';
  }

  Future<void> _issue(StudentRecord student) async {
    if (_issuingStudentId != null) return;
    setState(() => _issuingStudentId = student.id);

    try {
      final String token = await _repository.issueStudentAccessToken(student.id);
      if (!mounted) return;
      final String link = _studentLink(token);
      await showDialog<void>(
        context: context,
        barrierColor: Colors.black.withValues(alpha: 0.76),
        builder: (BuildContext context) => _AccessDialog(
          studentName: student.name,
          link: link,
        ),
      );
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          behavior: SnackBarBehavior.floating,
          backgroundColor: const Color(0xFF5A1919),
          content: Text('Não foi possível gerar o acesso: $error'),
        ),
      );
    } finally {
      if (mounted) setState(() => _issuingStudentId = null);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _AccessColors.black,
      appBar: AppBar(
        backgroundColor: _AccessColors.black,
        foregroundColor: _AccessColors.text,
        title: const Text(
          'Acesso dos alunos',
          style: TextStyle(fontWeight: FontWeight.w900),
        ),
        actions: <Widget>[
          IconButton(
            tooltip: 'Atualizar',
            onPressed: _loading ? null : _load,
            icon: const Icon(Icons.refresh_rounded),
          ),
        ],
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(20, 18, 20, 60),
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 960),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: <Widget>[
                  Container(
                    padding: const EdgeInsets.all(22),
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: <Color>[Color(0xFF1A1507), Color(0xFF101010)],
                      ),
                      borderRadius: BorderRadius.circular(24),
                      border: Border.all(color: _AccessColors.border),
                    ),
                    child: const Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text(
                          'LINK + QR INDIVIDUAL',
                          style: TextStyle(
                            color: _AccessColors.goldSoft,
                            fontSize: 12,
                            fontWeight: FontWeight.w900,
                            letterSpacing: 0.8,
                          ),
                        ),
                        SizedBox(height: 10),
                        Text(
                          'Cada aluno recebe um acesso privado ao treino.',
                          style: TextStyle(
                            color: _AccessColors.text,
                            fontSize: 25,
                            height: 1.12,
                            fontWeight: FontWeight.w900,
                          ),
                        ),
                        SizedBox(height: 8),
                        Text(
                          'Ao gerar novamente, o link anterior é invalidado automaticamente. O token bruto não fica salvo no banco.',
                          style: TextStyle(
                            color: _AccessColors.muted,
                            height: 1.45,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 18),
                  if (_loading && _students.isEmpty)
                    const Padding(
                      padding: EdgeInsets.all(40),
                      child: Center(
                        child: CircularProgressIndicator(color: _AccessColors.gold),
                      ),
                    )
                  else if (_error != null)
                    _MessageCard(
                      icon: Icons.error_outline_rounded,
                      text: _error!,
                      action: TextButton(
                        onPressed: _load,
                        child: const Text('Tentar novamente'),
                      ),
                    )
                  else if (_students.isEmpty)
                    const _MessageCard(
                      icon: Icons.group_off_rounded,
                      text: 'Cadastre um aluno no painel antes de gerar o acesso.',
                    )
                  else
                    ..._students.map(
                      (StudentRecord student) => Padding(
                        padding: const EdgeInsets.only(bottom: 10),
                        child: _StudentAccessRow(
                          student: student,
                          busy: _issuingStudentId == student.id,
                          onGenerate: () => _issue(student),
                        ),
                      ),
                    ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _StudentAccessRow extends StatelessWidget {
  const _StudentAccessRow({
    required this.student,
    required this.busy,
    required this.onGenerate,
  });

  final StudentRecord student;
  final bool busy;
  final VoidCallback onGenerate;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: _AccessColors.card,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: _AccessColors.border),
      ),
      child: LayoutBuilder(
        builder: (BuildContext context, BoxConstraints constraints) {
          final Widget identity = Row(
            mainAxisSize: MainAxisSize.min,
            children: <Widget>[
              const CircleAvatar(
                backgroundColor: _AccessColors.gold,
                foregroundColor: Colors.black,
                child: Icon(Icons.person_rounded),
              ),
              const SizedBox(width: 12),
              Flexible(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      student.name,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: _AccessColors.text,
                        fontWeight: FontWeight.w900,
                        fontSize: 16,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${student.objective} • ${student.status}',
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: _AccessColors.muted,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          );

          final Widget action = FilledButton.icon(
            onPressed: busy ? null : onGenerate,
            icon: busy
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.qr_code_2_rounded),
            label: Text(busy ? 'Gerando...' : 'Gerar link + QR'),
            style: FilledButton.styleFrom(
              backgroundColor: _AccessColors.gold,
              foregroundColor: Colors.black,
              textStyle: const TextStyle(fontWeight: FontWeight.w900),
            ),
          );

          if (constraints.maxWidth < 620) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: <Widget>[
                identity,
                const SizedBox(height: 14),
                action,
              ],
            );
          }

          return Row(
            children: <Widget>[
              Expanded(child: identity),
              const SizedBox(width: 16),
              action,
            ],
          );
        },
      ),
    );
  }
}

class _AccessDialog extends StatelessWidget {
  const _AccessDialog({required this.studentName, required this.link});

  final String studentName;
  final String link;

  Future<void> _copy(BuildContext context) async {
    await Clipboard.setData(ClipboardData(text: link));
    if (!context.mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        behavior: SnackBarBehavior.floating,
        content: Text('Link do aluno copiado.'),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      backgroundColor: _AccessColors.card,
      title: Text(
        'Acesso de $studentName',
        style: const TextStyle(fontWeight: FontWeight.w900),
      ),
      content: SizedBox(
        width: 520,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: <Widget>[
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: QrImageView(
                  data: link,
                  version: QrVersions.auto,
                  size: 230,
                ),
              ),
              const SizedBox(height: 18),
              SelectableText(
                link,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  color: _AccessColors.muted,
                  fontSize: 12,
                  height: 1.45,
                ),
              ),
              const SizedBox(height: 14),
              const Text(
                'Este endereço funciona como uma chave privada. Compartilhe somente com o aluno correspondente.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: _AccessColors.text,
                  fontSize: 12,
                  height: 1.4,
                ),
              ),
            ],
          ),
        ),
      ),
      actions: <Widget>[
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Fechar'),
        ),
        FilledButton.icon(
          onPressed: () => _copy(context),
          icon: const Icon(Icons.copy_rounded),
          label: const Text('Copiar link'),
        ),
      ],
    );
  }
}

class _MessageCard extends StatelessWidget {
  const _MessageCard({required this.icon, required this.text, this.action});

  final IconData icon;
  final String text;
  final Widget? action;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        color: _AccessColors.card,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: _AccessColors.border),
      ),
      child: Row(
        children: <Widget>[
          Icon(icon, color: _AccessColors.goldSoft),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(color: _AccessColors.text, height: 1.4),
            ),
          ),
          if (action != null) action!,
        ],
      ),
    );
  }
}

class _AccessColors {
  static const Color black = Color(0xFF050505);
  static const Color card = Color(0xFF111111);
  static const Color border = Color(0xFF302B1D);
  static const Color gold = Color(0xFFE1B92F);
  static const Color goldSoft = Color(0xFFFFD45A);
  static const Color text = Color(0xFFF7F7F7);
  static const Color muted = Color(0xFFB7B7B7);
}
