import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';

class LandingPage extends StatelessWidget {
  const LandingPage({super.key});

  static const Color _canvas = Color(0xFF070707);
  static const Color _surface = Color(0xFF101010);
  static const Color _surfaceRaised = Color(0xFF151515);
  static const Color _line = Color(0xFF292929);
  static const Color _muted = Color(0xFFA8A8A8);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _canvas,
      body: SafeArea(
        bottom: false,
        child: SelectionArea(
          child: SingleChildScrollView(
            child: Column(
              children: const <Widget>[
                _HeroSection(),
                _BenefitStrip(),
                _ExperienceSection(),
                _WorkflowSection(),
                _PlanSection(),
                _FinalSection(),
                _Footer(),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _Shell extends StatelessWidget {
  const _Shell({required this.child, this.maxWidth = 1180});

  final Widget child;
  final double maxWidth;

  @override
  Widget build(BuildContext context) {
    final double width = MediaQuery.sizeOf(context).width;
    final double horizontal = width < 560 ? 20 : width < 900 ? 36 : 56;
    return Center(
      child: ConstrainedBox(
        constraints: BoxConstraints(maxWidth: maxWidth),
        child: Padding(
          padding: EdgeInsets.symmetric(horizontal: horizontal),
          child: child,
        ),
      ),
    );
  }
}

class _HeroSection extends StatelessWidget {
  const _HeroSection();

  @override
  Widget build(BuildContext context) {
    final double width = MediaQuery.sizeOf(context).width;
    final bool mobile = width < 760;

    return DecoratedBox(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: <Color>[Color(0xFF0B0B0B), Color(0xFF070707)],
        ),
      ),
      child: _Shell(
        child: Padding(
          padding: EdgeInsets.only(
            top: mobile ? 16 : 24,
            bottom: mobile ? 34 : 64,
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              const _TopBar(),
              SizedBox(height: mobile ? 38 : 70),
              if (mobile)
                const Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    _HeroCopy(),
                    SizedBox(height: 30),
                    _ProductPreview(),
                  ],
                )
              else
                const Row(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: <Widget>[
                    Expanded(flex: 11, child: _HeroCopy()),
                    SizedBox(width: 52),
                    Expanded(flex: 9, child: _ProductPreview()),
                  ],
                ),
            ],
          ),
        ),
      ),
    );
  }
}

class _TopBar extends StatelessWidget {
  const _TopBar();

  @override
  Widget build(BuildContext context) {
    final bool compact = MediaQuery.sizeOf(context).width < 520;
    return Row(
      children: <Widget>[
        Container(
          width: 44,
          height: 44,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(14),
            gradient: const LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: <Color>[AppColors.goldSoft, AppColors.gold],
            ),
          ),
          alignment: Alignment.center,
          child: const Icon(Icons.fitness_center_rounded, color: Colors.black, size: 22),
        ),
        const SizedBox(width: 12),
        const Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(
                'FitNexus Coach',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 17,
                  fontWeight: FontWeight.w900,
                  letterSpacing: -0.2,
                ),
              ),
              SizedBox(height: 1),
              Text(
                'COACH OPERATING SYSTEM',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  color: Color(0xFF858585),
                  fontSize: 9,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 1.2,
                ),
              ),
            ],
          ),
        ),
        if (!compact) ...<Widget>[
          TextButton(
            onPressed: () => Navigator.of(context).pushNamed('/links'),
            child: const Text('Ecossistema'),
          ),
          const SizedBox(width: 4),
        ],
        OutlinedButton(
          onPressed: () => Navigator.of(context).pushNamed('/auth'),
          style: OutlinedButton.styleFrom(
            foregroundColor: Colors.white,
            side: const BorderSide(color: Color(0xFF343434)),
            padding: EdgeInsets.symmetric(horizontal: compact ? 14 : 18, vertical: 12),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          ),
          child: const Text('Entrar', style: TextStyle(fontWeight: FontWeight.w800)),
        ),
      ],
    );
  }
}

class _HeroCopy extends StatelessWidget {
  const _HeroCopy();

  @override
  Widget build(BuildContext context) {
    final double width = MediaQuery.sizeOf(context).width;
    final bool mobile = width < 760;
    final double titleSize = width < 370 ? 36 : mobile ? 42 : 58;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        const _Eyebrow(text: 'TREINO • GESTÃO • EVOLUÇÃO'),
        const SizedBox(height: 18),
        Text(
          'Treinos, alunos e evolução.\nEm um só lugar.',
          style: TextStyle(
            color: Colors.white,
            fontSize: titleSize,
            height: 0.98,
            fontWeight: FontWeight.w900,
            letterSpacing: mobile ? -1.2 : -2.2,
          ),
        ),
        const SizedBox(height: 18),
        ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 600),
          child: const Text(
            'Organize sua rotina de coaching, entregue treinos pelo celular e acompanhe cada aluno com mais clareza.',
            style: TextStyle(
              color: LandingPage._muted,
              fontSize: 16,
              height: 1.5,
              fontWeight: FontWeight.w500,
            ),
          ),
        ),
        const SizedBox(height: 26),
        _HeroActions(mobile: mobile),
        const SizedBox(height: 22),
        const Wrap(
          spacing: 18,
          runSpacing: 10,
          children: <Widget>[
            _MicroProof(icon: Icons.check_circle_outline_rounded, text: 'Professor e aluno conectados'),
            _MicroProof(icon: Icons.lock_outline_rounded, text: 'Acesso autenticado'),
          ],
        ),
      ],
    );
  }
}

class _HeroActions extends StatelessWidget {
  const _HeroActions({required this.mobile});

  final bool mobile;

  @override
  Widget build(BuildContext context) {
    final Widget primary = FilledButton.icon(
      key: const ValueKey<String>('public-signup-entry'),
      onPressed: () => Navigator.of(context).pushNamed('/start'),
      icon: const Icon(Icons.arrow_forward_rounded, size: 20),
      label: const Text('Começar grátis'),
      style: FilledButton.styleFrom(
        backgroundColor: AppColors.gold,
        foregroundColor: Colors.black,
        minimumSize: Size(mobile ? double.infinity : 0, 54),
        padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 16),
        textStyle: const TextStyle(fontSize: 15, fontWeight: FontWeight.w900),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      ),
    );
    final Widget secondary = OutlinedButton.icon(
      onPressed: () => Navigator.of(context).pushNamed('/auth'),
      icon: const Icon(Icons.login_rounded, size: 19),
      label: const Text('Já tenho conta'),
      style: OutlinedButton.styleFrom(
        foregroundColor: Colors.white,
        side: const BorderSide(color: Color(0xFF343434)),
        minimumSize: Size(mobile ? double.infinity : 0, 54),
        padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 16),
        textStyle: const TextStyle(fontSize: 15, fontWeight: FontWeight.w800),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      ),
    );

    if (mobile) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          primary,
          const SizedBox(height: 10),
          secondary,
        ],
      );
    }
    return Wrap(spacing: 12, runSpacing: 12, children: <Widget>[primary, secondary]);
  }
}

class _ProductPreview extends StatelessWidget {
  const _ProductPreview();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: LandingPage._surface,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: LandingPage._line),
        boxShadow: const <BoxShadow>[
          BoxShadow(color: Color(0x66000000), blurRadius: 32, offset: Offset(0, 18)),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Row(
            children: <Widget>[
              Container(
                width: 38,
                height: 38,
                decoration: BoxDecoration(
                  color: AppColors.gold.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Icon(Icons.dashboard_rounded, color: AppColors.goldSoft, size: 20),
              ),
              const SizedBox(width: 11),
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text('Painel do professor', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w900)),
                    SizedBox(height: 2),
                    Text('Visão rápida da operação', style: TextStyle(color: Color(0xFF858585), fontSize: 11)),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
                decoration: BoxDecoration(
                  color: const Color(0xFF16301F),
                  borderRadius: BorderRadius.circular(999),
                ),
                child: const Text(
                  'ONLINE',
                  style: TextStyle(color: Color(0xFF7DE3A1), fontSize: 9, fontWeight: FontWeight.w900, letterSpacing: 0.8),
                ),
              ),
            ],
          ),
          const SizedBox(height: 18),
          const _PreviewMetric(label: 'Alunos ativos', value: '24', icon: Icons.groups_2_rounded),
          const SizedBox(height: 9),
          const _PreviewMetric(label: 'Treinos para revisar', value: '3', icon: Icons.assignment_turned_in_rounded),
          const SizedBox(height: 9),
          const _PreviewMetric(label: 'Feedbacks recentes', value: '8', icon: Icons.forum_rounded),
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: LandingPage._surfaceRaised,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: const Color(0xFF282828)),
            ),
            child: const Row(
              children: <Widget>[
                Icon(Icons.insights_rounded, color: AppColors.goldSoft, size: 20),
                SizedBox(width: 10),
                Expanded(
                  child: Text(
                    'Acompanhe treino, feedback e evolução sem espalhar o trabalho em várias ferramentas.',
                    style: TextStyle(color: Color(0xFFBDBDBD), fontSize: 12, height: 1.4),
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

class _PreviewMetric extends StatelessWidget {
  const _PreviewMetric({required this.label, required this.value, required this.icon});

  final String label;
  final String value;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 12),
      decoration: BoxDecoration(
        color: const Color(0xFF131313),
        borderRadius: BorderRadius.circular(14),
      ),
      child: Row(
        children: <Widget>[
          Icon(icon, color: const Color(0xFF8E8E8E), size: 18),
          const SizedBox(width: 10),
          Expanded(child: Text(label, style: const TextStyle(color: Color(0xFFAAAAAA), fontSize: 12))),
          Text(value, style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w900)),
        ],
      ),
    );
  }
}

class _BenefitStrip extends StatelessWidget {
  const _BenefitStrip();

  @override
  Widget build(BuildContext context) {
    return _Shell(
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 28),
        child: LayoutBuilder(
          builder: (BuildContext context, BoxConstraints constraints) {
            final bool stack = constraints.maxWidth < 700;
            const List<Widget> cards = <Widget>[
              _Benefit(icon: Icons.fitness_center_rounded, title: 'Treinos', text: 'Prescrição organizada e acessível no celular.'),
              _Benefit(icon: Icons.monitor_heart_rounded, title: 'Acompanhamento', text: 'Feedback e evolução no mesmo fluxo.'),
              _Benefit(icon: Icons.psychology_alt_rounded, title: 'Decisão', text: 'Sinais claros para o professor agir melhor.'),
            ];
            if (stack) {
              return const Column(
                children: <Widget>[
                  cards[0],
                  SizedBox(height: 10),
                  cards[1],
                  SizedBox(height: 10),
                  cards[2],
                ],
              );
            }
            return const Row(
              children: <Widget>[
                Expanded(child: cards[0]),
                SizedBox(width: 12),
                Expanded(child: cards[1]),
                SizedBox(width: 12),
                Expanded(child: cards[2]),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _Benefit extends StatelessWidget {
  const _Benefit({required this.icon, required this.title, required this.text});

  final IconData icon;
  final String title;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: LandingPage._surface,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: LandingPage._line),
      ),
      child: Row(
        children: <Widget>[
          Container(
            width: 42,
            height: 42,
            decoration: BoxDecoration(
              color: AppColors.gold.withValues(alpha: 0.10),
              borderRadius: BorderRadius.circular(13),
            ),
            child: Icon(icon, color: AppColors.goldSoft, size: 20),
          ),
          const SizedBox(width: 13),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(title, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900)),
                const SizedBox(height: 3),
                Text(text, style: const TextStyle(color: LandingPage._muted, fontSize: 12, height: 1.35)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ExperienceSection extends StatelessWidget {
  const _ExperienceSection();

  @override
  Widget build(BuildContext context) {
    return _Section(
      eyebrow: 'UMA EXPERIÊNCIA, DOIS LADOS',
      title: 'Professor no controle. Aluno focado no treino.',
      subtitle: 'Cada perfil vê o que precisa, sem misturar operação profissional com execução do aluno.',
      child: LayoutBuilder(
        builder: (BuildContext context, BoxConstraints constraints) {
          final bool stack = constraints.maxWidth < 760;
          const Widget professor = _RoleCard(
            icon: Icons.co_present_rounded,
            title: 'Para o professor',
            text: 'Organize alunos, monte treinos, acompanhe feedbacks e identifique prioridades de acompanhamento.',
            bullets: <String>['Alunos e acessos', 'Planos de treino', 'Feedback e evolução'],
          );
          const Widget student = _RoleCard(
            icon: Icons.directions_run_rounded,
            title: 'Para o aluno',
            text: 'Abra o treino no celular, registre a execução e mantenha o histórico conectado ao professor.',
            bullets: <String>['Treino no celular', 'Registro de execução', 'Histórico conectado'],
          );
          if (stack) {
            return const Column(children: <Widget>[professor, SizedBox(height: 12), student]);
          }
          return const Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[Expanded(child: professor), SizedBox(width: 14), Expanded(child: student)],
          );
        },
      ),
    );
  }
}

class _RoleCard extends StatelessWidget {
  const _RoleCard({required this.icon, required this.title, required this.text, required this.bullets});

  final IconData icon;
  final String title;
  final String text;
  final List<String> bullets;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        color: LandingPage._surface,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: LandingPage._line),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Icon(icon, color: AppColors.goldSoft, size: 27),
          const SizedBox(height: 16),
          Text(title, style: const TextStyle(color: Colors.white, fontSize: 21, fontWeight: FontWeight.w900)),
          const SizedBox(height: 8),
          Text(text, style: const TextStyle(color: LandingPage._muted, height: 1.5)),
          const SizedBox(height: 18),
          ...bullets.map(
            (String value) => Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Row(
                children: <Widget>[
                  const Icon(Icons.check_rounded, color: AppColors.gold, size: 18),
                  const SizedBox(width: 9),
                  Expanded(child: Text(value, style: const TextStyle(color: Color(0xFFD7D7D7), fontWeight: FontWeight.w700))),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _WorkflowSection extends StatelessWidget {
  const _WorkflowSection();

  @override
  Widget build(BuildContext context) {
    return const _Section(
      eyebrow: 'FLUXO SIMPLES',
      title: 'Do cadastro ao acompanhamento.',
      subtitle: 'Menos etapas soltas. Mais continuidade entre o que o professor prescreve e o que o aluno executa.',
      child: _WorkflowGrid(),
    );
  }
}

class _WorkflowGrid extends StatelessWidget {
  const _WorkflowGrid();

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (BuildContext context, BoxConstraints constraints) {
        final bool stack = constraints.maxWidth < 700;
        const List<Widget> steps = <Widget>[
          _Step(number: '01', title: 'Cadastre', text: 'Organize aluno e acesso em um único lugar.'),
          _Step(number: '02', title: 'Prescreva', text: 'Monte o treino e deixe a execução clara.'),
          _Step(number: '03', title: 'Acompanhe', text: 'Use feedback e evolução para decidir o próximo passo.'),
        ];
        if (stack) {
          return const Column(children: <Widget>[steps[0], SizedBox(height: 10), steps[1], SizedBox(height: 10), steps[2]]);
        }
        return const Row(
          children: <Widget>[
            Expanded(child: steps[0]),
            SizedBox(width: 12),
            Expanded(child: steps[1]),
            SizedBox(width: 12),
            Expanded(child: steps[2]),
          ],
        );
      },
    );
  }
}

class _Step extends StatelessWidget {
  const _Step({required this.number, required this.title, required this.text});

  final String number;
  final String title;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: LandingPage._surface,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: LandingPage._line),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(number, style: const TextStyle(color: AppColors.gold, fontSize: 11, fontWeight: FontWeight.w900, letterSpacing: 1.4)),
          const SizedBox(height: 14),
          Text(title, style: const TextStyle(color: Colors.white, fontSize: 19, fontWeight: FontWeight.w900)),
          const SizedBox(height: 7),
          Text(text, style: const TextStyle(color: LandingPage._muted, height: 1.45)),
        ],
      ),
    );
  }
}

class _PlanSection extends StatelessWidget {
  const _PlanSection();

  @override
  Widget build(BuildContext context) {
    return _Shell(
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 42),
        child: Container(
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            gradient: const LinearGradient(colors: <Color>[Color(0xFF17140B), Color(0xFF101010)]),
            borderRadius: BorderRadius.circular(24),
            border: Border.all(color: const Color(0xFF4B3D18)),
          ),
          child: LayoutBuilder(
            builder: (BuildContext context, BoxConstraints constraints) {
              final bool stack = constraints.maxWidth < 700;
              final Widget copy = const Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  _Eyebrow(text: 'PLANOS QUE CRESCEM COM VOCÊ'),
                  SizedBox(height: 12),
                  Text('Comece simples. Evolua quando precisar.', style: TextStyle(color: Colors.white, fontSize: 24, height: 1.08, fontWeight: FontWeight.w900)),
                  SizedBox(height: 8),
                  Text('Opções para personal individual, equipe e estúdio. No Android, assinaturas elegíveis são gerenciadas pelo Google Play.', style: TextStyle(color: LandingPage._muted, height: 1.45)),
                ],
              );
              final Widget action = FilledButton(
                onPressed: () => Navigator.of(context).pushNamed('/start'),
                style: FilledButton.styleFrom(
                  backgroundColor: AppColors.gold,
                  foregroundColor: Colors.black,
                  minimumSize: const Size(170, 52),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                ),
                child: const Text('Criar minha conta', style: TextStyle(fontWeight: FontWeight.w900)),
              );
              if (stack) {
                return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: <Widget>[copy, const SizedBox(height: 20), action]);
              }
              return Row(children: <Widget>[Expanded(child: copy), const SizedBox(width: 30), action]);
            },
          ),
        ),
      ),
    );
  }
}

class _FinalSection extends StatelessWidget {
  const _FinalSection();

  @override
  Widget build(BuildContext context) {
    return _Shell(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(0, 32, 0, 54),
        child: Column(
          children: <Widget>[
            const Text(
              'Seu coaching merece uma operação à altura.',
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.white, fontSize: 30, height: 1.05, fontWeight: FontWeight.w900, letterSpacing: -0.7),
            ),
            const SizedBox(height: 12),
            const Text(
              'Entre, organize seu primeiro aluno e conheça o fluxo completo do FitNexus.',
              textAlign: TextAlign.center,
              style: TextStyle(color: LandingPage._muted, fontSize: 15, height: 1.45),
            ),
            const SizedBox(height: 22),
            FilledButton.icon(
              onPressed: () => Navigator.of(context).pushNamed('/start'),
              icon: const Icon(Icons.arrow_forward_rounded),
              label: const Text('Começar grátis'),
              style: FilledButton.styleFrom(
                backgroundColor: AppColors.gold,
                foregroundColor: Colors.black,
                padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                textStyle: const TextStyle(fontWeight: FontWeight.w900),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Footer extends StatelessWidget {
  const _Footer();

  @override
  Widget build(BuildContext context) {
    final bool compact = MediaQuery.sizeOf(context).width < 620;
    final Widget brand = const Text(
      'FitNexus Coach BlackGold',
      style: TextStyle(color: Color(0xFF8D8D8D), fontSize: 12, fontWeight: FontWeight.w700),
    );
    final Widget links = Wrap(
      spacing: 8,
      runSpacing: 8,
      alignment: WrapAlignment.center,
      children: <Widget>[
        TextButton(onPressed: () => Navigator.of(context).pushNamed('/support'), child: const Text('Atendimento')),
        TextButton(onPressed: () => Navigator.of(context).pushNamed('/links'), child: const Text('Ecossistema')),
      ],
    );

    return DecoratedBox(
      decoration: const BoxDecoration(border: Border(top: BorderSide(color: LandingPage._line))),
      child: _Shell(
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 18),
          child: compact
              ? Column(children: <Widget>[brand, const SizedBox(height: 8), links])
              : Row(children: <Widget>[Expanded(child: brand), links]),
        ),
      ),
    );
  }
}

class _Section extends StatelessWidget {
  const _Section({required this.eyebrow, required this.title, required this.subtitle, required this.child});

  final String eyebrow;
  final String title;
  final String subtitle;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final bool mobile = MediaQuery.sizeOf(context).width < 760;
    return _Shell(
      child: Padding(
        padding: EdgeInsets.symmetric(vertical: mobile ? 38 : 54),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            _Eyebrow(text: eyebrow),
            const SizedBox(height: 12),
            ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 740),
              child: Text(
                title,
                style: TextStyle(color: Colors.white, fontSize: mobile ? 27 : 34, height: 1.06, fontWeight: FontWeight.w900, letterSpacing: -0.6),
              ),
            ),
            const SizedBox(height: 10),
            ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 760),
              child: Text(subtitle, style: const TextStyle(color: LandingPage._muted, height: 1.5, fontSize: 15)),
            ),
            const SizedBox(height: 24),
            child,
          ],
        ),
      ),
    );
  }
}

class _Eyebrow extends StatelessWidget {
  const _Eyebrow({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Text(
      text,
      style: const TextStyle(
        color: AppColors.goldSoft,
        fontSize: 10,
        fontWeight: FontWeight.w900,
        letterSpacing: 1.5,
      ),
    );
  }
}

class _MicroProof extends StatelessWidget {
  const _MicroProof({required this.icon, required this.text});

  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: <Widget>[
        Icon(icon, color: const Color(0xFF898989), size: 15),
        const SizedBox(width: 6),
        Text(text, style: const TextStyle(color: Color(0xFF9B9B9B), fontSize: 11, fontWeight: FontWeight.w700)),
      ],
    );
  }
}
