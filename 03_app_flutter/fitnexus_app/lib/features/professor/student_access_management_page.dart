import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:qr_flutter/qr_flutter.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/blackgold_tokens.dart';
import '../shared/fitnexus_ui.dart';
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
    if (mounted) {
      setState(() {
        _loading = true;
        _error = null;
      });
    }

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
        barrierColor: Colors.black.withValues(alpha: 0.78),
        builder: (BuildContext context) => _AccessDialog(
          studentName: student.name,
          link: link,
        ),
      );
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          backgroundColor: AppColors.danger,
          content: Text('Não foi possível gerar o acesso: $error'),
        ),
      );
    } finally {
      if (mounted) setState(() => _issuingStudentId = null);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.black,
      child: SafeArea(
        bottom: false,
        child: RefreshIndicator(
          color: AppColors.gold,
          backgroundColor: AppColors.cardRaised,
          onRefresh: _load,
          child: CustomScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            slivers: <Widget>[
              SliverPadding(
                padding: const EdgeInsets.fromLTRB(
                  BlackGoldSpace.lg,
                  BlackGoldSpace.lg,
                  BlackGoldSpace.lg,
                  120,
                ),
                sliver: SliverToBoxAdapter(
                  child: Center(
                    child: ConstrainedBox(
                      constraints: const BoxConstraints(maxWidth: 1080),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: <Widget>[
                          FitPageTitle(
                            eyebrow: 'Acesso individual',
                            title: 'Link + QR privado para cada aluno',
                            description:
                                'Cada acesso pertence a um único aluno, expira em 30 dias e revoga o anterior quando uma nova chave é emitida.',
                            trailing: OutlinedButton.icon(
                              onPressed: _loading ? null : _load,
                              icon: _loading
                                  ? const SizedBox(
                                      width: 16,
                                      height: 16,
                                      child: CircularProgressIndicator(
                                        strokeWidth: 2,
                                        color: AppColors.goldSoft,
                                      ),
                                    )
                                  : const Icon(Icons.refresh_rounded, size: 18),
                              label: const Text('Atualizar'),
                            ),
                          ),
                          const SizedBox(height: BlackGoldSpace.xl),
                          const _SecurityCallout(),
                          const SizedBox(height: BlackGoldSpace.lg),
                          if (_loading && _students.isEmpty)
                            const _LoadingPanel()
                          else if (_error != null)
                            _MessageCard(
                              icon: Icons.error_outline_rounded,
                              title: 'Não foi possível carregar os alunos',
                              text: _error!,
                              action: OutlinedButton.icon(
                                onPressed: _load,
                                icon: const Icon(Icons.refresh_rounded),
                                label: const Text('Tentar novamente'),
                              ),
                              error: true,
                            )
                          else if (_students.isEmpty)
                            const _MessageCard(
                              icon: Icons.group_off_rounded,
                              title: 'Nenhum aluno disponível',
                              text:
                                  'Cadastre um aluno no painel antes de gerar um acesso individual.',
                            )
                          else ...<Widget>[
                            _StudentCount(count: _students.length),
                            const SizedBox(height: BlackGoldSpace.md),
                            ..._students.map(
                              (StudentRecord student) => Padding(
                                padding: const EdgeInsets.only(
                                  bottom: BlackGoldSpace.sm,
                                ),
                                child: _StudentAccessRow(
                                  student: student,
                                  busy: _issuingStudentId == student.id,
                                  onGenerate: () => _issue(student),
                                ),
                              ),
                            ),
                          ],
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _SecurityCallout extends StatelessWidget {
  const _SecurityCallout();

  @override
  Widget build(BuildContext context) {
    return FitCard(
      highlight: true,
      padding: const EdgeInsets.all(BlackGoldSpace.md),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Container(
            width: 40,
            height: 40,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: AppColors.gold.withValues(alpha: 0.09),
              borderRadius: BorderRadius.circular(BlackGoldRadius.control),
            ),
            child: const Icon(
              Icons.shield_outlined,
              color: AppColors.goldSoft,
              size: 21,
            ),
          ),
          const SizedBox(width: BlackGoldSpace.sm),
          const Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  'ACESSO PRIVADO E REVOGÁVEL',
                  style: TextStyle(
                    color: AppColors.goldSoft,
                    fontSize: 10.5,
                    fontWeight: FontWeight.w900,
                    letterSpacing: 1.0,
                  ),
                ),
                SizedBox(height: 5),
                Text(
                  'O token bruto não fica salvo no banco. Gere uma nova chave somente quando necessário e compartilhe o endereço exclusivamente com o aluno correspondente.',
                  style: TextStyle(
                    color: AppColors.muted,
                    fontSize: 12.5,
                    height: 1.42,
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

class _StudentCount extends StatelessWidget {
  const _StudentCount({required this.count});

  final int count;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: <Widget>[
        const Icon(Icons.groups_rounded, color: AppColors.goldSoft, size: 20),
        const SizedBox(width: BlackGoldSpace.xs),
        Text(
          '$count alunos disponíveis',
          style: Theme.of(context).textTheme.titleLarge,
        ),
      ],
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
    return FitCard(
      padding: const EdgeInsets.all(BlackGoldSpace.md),
      child: LayoutBuilder(
        builder: (BuildContext context, BoxConstraints constraints) {
          final Widget identity = Row(
            children: <Widget>[
              CircleAvatar(
                radius: 21,
                backgroundColor: AppColors.gold.withValues(alpha: 0.10),
                foregroundColor: AppColors.goldSoft,
                child: Text(
                  _initials(student.name),
                  style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w900,
                  ),
                ),
              ),
              const SizedBox(width: BlackGoldSpace.sm),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      student.name,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: AppColors.text,
                        fontSize: 15,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${student.objective} • ${student.level} • ${student.status}',
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: AppColors.muted,
                        fontSize: 11.5,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          );

          final Widget action = GoldButton(
            label: busy ? 'Gerando...' : 'Gerar link + QR',
            icon: busy ? Icons.hourglass_top_rounded : Icons.qr_code_2_rounded,
            onTap: busy ? null : onGenerate,
          );

          if (constraints.maxWidth < 620) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: <Widget>[
                identity,
                const SizedBox(height: BlackGoldSpace.md),
                action,
              ],
            );
          }

          return Row(
            children: <Widget>[
              Expanded(child: identity),
              const SizedBox(width: BlackGoldSpace.md),
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
      const SnackBar(content: Text('Link do aluno copiado.')),
    );
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const SectionLabel('Acesso privado'),
          const SizedBox(height: BlackGoldSpace.xs),
          Text('Acesso de $studentName'),
        ],
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
                  borderRadius: BorderRadius.circular(BlackGoldRadius.card),
                ),
                child: QrImageView(
                  data: link,
                  version: QrVersions.auto,
                  size: 230,
                ),
              ),
              const SizedBox(height: BlackGoldSpace.lg),
              SelectableText(
                link,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  color: AppColors.muted,
                  fontSize: 11.5,
                  height: 1.45,
                ),
              ),
              const SizedBox(height: BlackGoldSpace.md),
              const Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Icon(
                    Icons.lock_outline_rounded,
                    color: AppColors.goldSoft,
                    size: 17,
                  ),
                  SizedBox(width: BlackGoldSpace.xs),
                  Expanded(
                    child: Text(
                      'Este endereço funciona como uma chave privada e expira em 30 dias. Compartilhe somente com o aluno correspondente.',
                      style: TextStyle(
                        color: AppColors.text,
                        fontSize: 11.5,
                        height: 1.4,
                      ),
                    ),
                  ),
                ],
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
  const _MessageCard({
    required this.icon,
    required this.title,
    required this.text,
    this.action,
    this.error = false,
  });

  final IconData icon;
  final String title;
  final String text;
  final Widget? action;
  final bool error;

  @override
  Widget build(BuildContext context) {
    final Color accent = error ? AppColors.danger : AppColors.goldSoft;
    return FitCard(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Icon(icon, color: accent, size: 24),
          const SizedBox(width: BlackGoldSpace.sm),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  title,
                  style: const TextStyle(
                    color: AppColors.text,
                    fontSize: 15,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const SizedBox(height: 5),
                Text(
                  text,
                  style: const TextStyle(
                    color: AppColors.muted,
                    fontSize: 12.5,
                    height: 1.42,
                  ),
                ),
                if (action != null) ...<Widget>[
                  const SizedBox(height: BlackGoldSpace.sm),
                  action!,
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _LoadingPanel extends StatelessWidget {
  const _LoadingPanel();

  @override
  Widget build(BuildContext context) {
    return const FitCard(
      child: SizedBox(
        height: 240,
        child: Center(
          child: CircularProgressIndicator(color: AppColors.gold),
        ),
      ),
    );
  }
}

String _initials(String name) {
  final List<String> parts = name
      .trim()
      .split(RegExp(r'\s+'))
      .where((String part) => part.isNotEmpty)
      .toList(growable: false);
  if (parts.isEmpty) return 'AL';
  if (parts.length == 1) {
    final int end = parts.first.length >= 2 ? 2 : 1;
    return parts.first.substring(0, end).toUpperCase();
  }
  return '${parts.first[0]}${parts.last[0]}'.toUpperCase();
}
