import 'dart:math' as math;

import 'package:flutter/material.dart';

class ProfessorDashboardPage extends StatelessWidget {
  const ProfessorDashboardPage({super.key});

  static const List<_StatData> _stats = <_StatData>[
    _StatData(Icons.groups_rounded, '18', 'Alunos ativos', '+4 este mês'),
    _StatData(Icons.assignment_turned_in_rounded, '42', 'Treinos criados', '12 atualizados'),
    _StatData(Icons.check_circle_rounded, '126', 'Execuções feitas', 'semana atual'),
    _StatData(Icons.trending_up_rounded, '23%', 'Evolução média', 'carga e presença'),
    _StatData(Icons.local_fire_department_rounded, '74%', 'Constância semanal', 'aderência média'),
  ];

  static const List<_StudentData> _students = <_StudentData>[
    _StudentData(
      name: 'Mariana Costa',
      initials: 'MC',
      objective: 'Hipertrofia',
      level: 'Intermediário',
      lastWorkout: 'Inferiores A',
      lastDate: '25/06/2026',
      adherence: 82,
      next: 'Hoje 18:00',
      status: 'Em evolução',
      tone: _StatusTone.green,
    ),
    _StudentData(
      name: 'Carlos Menezes',
      initials: 'CM',
      objective: 'Emagrecimento',
      level: 'Iniciante',
      lastWorkout: 'Full Body + Cardio',
      lastDate: '28/06/2026',
      adherence: 54,
      next: 'Amanhã 08:30',
      status: 'Revisar rotina',
      tone: _StatusTone.gold,
    ),
    _StudentData(
      name: 'Ana Ribeiro',
      initials: 'AR',
      objective: 'Condicionamento',
      level: 'Intermediário',
      lastWorkout: 'Superiores B',
      lastDate: '27/06/2026',
      adherence: 71,
      next: 'Hoje 15:00',
      status: 'No caminho',
      tone: _StatusTone.blue,
    ),
    _StudentData(
      name: 'Lucas Almeida',
      initials: 'LA',
      objective: 'Definição',
      level: 'Iniciante',
      lastWorkout: 'Peito e tríceps',
      lastDate: '26/06/2026',
      adherence: 68,
      next: 'Amanhã 19:00',
      status: 'Em evolução',
      tone: _StatusTone.green,
    ),
    _StudentData(
      name: 'Beatriz Lima',
      initials: 'BL',
      objective: 'Hipertrofia',
      level: 'Intermediário',
      lastWorkout: 'Inferiores B',
      lastDate: '27/06/2026',
      adherence: 90,
      next: 'Sexta 17:00',
      status: 'Excelente',
      tone: _StatusTone.purple,
    ),
  ];

  static const List<_ScheduleData> _schedule = <_ScheduleData>[
    _ScheduleData('08:00', 'Carlos Menezes', 'Full Body + Cardio'),
    _ScheduleData('15:00', 'Ana Ribeiro', 'Superiores B'),
    _ScheduleData('18:00', 'Mariana Costa', 'Inferiores A'),
    _ScheduleData('19:00', 'Lucas Almeida', 'Peito e tríceps'),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _P.black,
      body: Stack(
        children: <Widget>[
          _BackgroundGlow(),
          SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.fromLTRB(20, 0, 20, 44),
              child: Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 1510),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: <Widget>[
                      _TopBar(),
                      _HeroShowcase(),
                      _StatsStrip(),
                      const SizedBox(height: 12),
                      const _DashboardBody(),
                    ],
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

class _TopBar extends StatelessWidget {
  const _TopBar();

  @override
  Widget build(BuildContext context) {
    final bool compact = MediaQuery.sizeOf(context).width < 860;

    return Container(
      height: compact ? 76 : 86,
      decoration: const BoxDecoration(
        border: Border(bottom: BorderSide(color: _P.borderSoft)),
      ),
      child: Row(
        children: <Widget>[
          const _LogoMark(),
          const SizedBox(width: 14),
          const Expanded(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  'FitNexus Coach',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    color: _P.text,
                    fontSize: 23,
                    height: 1,
                    fontWeight: FontWeight.w900,
                    letterSpacing: -0.7,
                  ),
                ),
                SizedBox(height: 5),
                Text(
                  'BlackGold SaaS Fitness',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(color: _P.mutedLight, fontSize: 13, fontWeight: FontWeight.w700),
                ),
              ],
            ),
          ),
          if (!compact) ...const <Widget>[
            _NavPill(label: 'Landing', route: '/', filled: false),
            SizedBox(width: 10),
            _NavPill(label: 'Demonstração', route: '/demo', filled: false),
            SizedBox(width: 10),
            _NavPill(label: 'Ecossistema', route: '/links', filled: true),
            SizedBox(width: 28),
            _HeaderIcon(Icons.notifications_none_rounded),
            SizedBox(width: 16),
            _HeaderIcon(Icons.help_outline_rounded),
            SizedBox(width: 16),
            _ProfileChip(),
          ],
        ],
      ),
    );
  }
}

class _LogoMark extends StatelessWidget {
  const _LogoMark();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 52,
      height: 52,
      decoration: BoxDecoration(
        gradient: _P.goldGradient,
        borderRadius: BorderRadius.circular(14),
        boxShadow: const <BoxShadow>[BoxShadow(color: _P.goldGlow, blurRadius: 30, offset: Offset(0, 10))],
      ),
      child: const Icon(Icons.fitness_center_rounded, color: _P.black, size: 27),
    );
  }
}

class _NavPill extends StatelessWidget {
  const _NavPill({required this.label, required this.route, required this.filled});

  final String label;
  final String route;
  final bool filled;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      borderRadius: BorderRadius.circular(999),
      onTap: () {
        if (ModalRoute.of(context)?.settings.name != route) {
          Navigator.of(context).pushNamed(route);
        }
      },
      child: Container(
        height: 34,
        padding: const EdgeInsets.symmetric(horizontal: 24),
        alignment: Alignment.center,
        decoration: BoxDecoration(
          gradient: filled ? _P.goldGradient : null,
          color: filled ? null : _P.blackGlass,
          borderRadius: BorderRadius.circular(999),
          border: Border.all(color: filled ? Colors.transparent : _P.borderSoft),
          boxShadow: filled ? const <BoxShadow>[BoxShadow(color: _P.goldGlow, blurRadius: 18, offset: Offset(0, 7))] : null,
        ),
        child: Text(
          label,
          style: TextStyle(color: filled ? _P.black : _P.text, fontSize: 12, fontWeight: FontWeight.w900),
        ),
      ),
    );
  }
}

class _HeaderIcon extends StatelessWidget {
  const _HeaderIcon(this.icon);

  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Icon(icon, color: _P.gold, size: 22);
  }
}

class _ProfileChip extends StatelessWidget {
  const _ProfileChip();

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: <Widget>[
        Container(
          width: 36,
          height: 36,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: _P.card,
            border: Border.all(color: _P.border),
          ),
          child: const Icon(Icons.person_rounded, color: _P.gold, size: 20),
        ),
        const SizedBox(width: 8),
        const Icon(Icons.keyboard_arrow_down_rounded, color: _P.gold, size: 20),
      ],
    );
  }
}

class _HeroShowcase extends StatelessWidget {
  const _HeroShowcase();

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (BuildContext context, BoxConstraints constraints) {
        final bool compact = constraints.maxWidth < 900;
        final double heroHeight = compact ? 740 : 360;

        if (compact) {
          return Container(
            margin: const EdgeInsets.only(top: 20),
            padding: const EdgeInsets.all(18),
            decoration: _P.premiumDecoration(radius: 24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                const _HeroCopy(compact: true),
                const SizedBox(height: 22),
                ClipRRect(
                  borderRadius: BorderRadius.circular(20),
                  child: const AspectRatio(
                    aspectRatio: 16 / 9,
                    child: Image(
                      image: AssetImage('assets/images/professor_dashboard_hero.webp'),
                      fit: BoxFit.cover,
                      filterQuality: FilterQuality.high,
                    ),
                  ),
                ),
              ],
            ),
          );
        }

        return Container(
          height: heroHeight,
          margin: const EdgeInsets.only(top: 0),
          clipBehavior: Clip.antiAlias,
          decoration: const BoxDecoration(border: Border(bottom: BorderSide(color: _P.borderSoft))),
          child: Stack(
            fit: StackFit.expand,
            children: <Widget>[
              Positioned.fill(
                left: constraints.maxWidth * 0.36,
                child: Image.asset(
                  'assets/images/professor_dashboard_hero.webp',
                  fit: BoxFit.cover,
                  alignment: Alignment.centerRight,
                  filterQuality: FilterQuality.high,
                ),
              ),
              const Positioned.fill(
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.centerLeft,
                      end: Alignment.centerRight,
                      stops: <double>[0.0, 0.30, 0.47, 0.72, 1.0],
                      colors: <Color>[
                        _P.black,
                        _P.black,
                        _P.blackAlpha72,
                        _P.blackAlpha16,
                        _P.blackAlpha08,
                      ],
                    ),
                  ),
                ),
              ),
              const Positioned.fill(
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    gradient: RadialGradient(
                      center: Alignment(-0.78, -0.05),
                      radius: 0.74,
                      colors: <Color>[_P.heroGoldWash, Colors.transparent],
                    ),
                  ),
                ),
              ),
              const Align(
                alignment: Alignment.centerLeft,
                child: Padding(
                  padding: EdgeInsets.only(left: 56),
                  child: SizedBox(width: 635, child: _HeroCopy(compact: false)),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _HeroCopy extends StatelessWidget {
  const _HeroCopy({required this.compact});

  final bool compact;

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        const _SectionBadge(label: 'PAINEL DO PROFESSOR'),
        SizedBox(height: compact ? 16 : 20),
        RichText(
          text: TextSpan(
            style: TextStyle(
              color: _P.text,
              fontSize: compact ? 40 : 52,
              height: 0.96,
              fontWeight: FontWeight.w900,
              letterSpacing: compact ? -1.5 : -2.2,
            ),
            children: const <InlineSpan>[
              TextSpan(text: 'Gestão premium para\nalunos, treinos e '),
              TextSpan(text: 'evolução.', style: TextStyle(color: _P.gold)),
            ],
          ),
        ),
        SizedBox(height: compact ? 16 : 20),
        Text(
          'Organize rotina, acompanhe aderência, registre progresso e entregue\ntreino digital com aparência de produto profissional.',
          style: TextStyle(
            color: _P.mutedLight,
            fontSize: compact ? 14 : 16,
            height: 1.38,
            fontWeight: FontWeight.w600,
          ),
        ),
        SizedBox(height: compact ? 22 : 28),
        const Wrap(
          spacing: 14,
          runSpacing: 12,
          children: <Widget>[
            _HeroButton(label: 'Novo aluno', icon: Icons.person_add_alt_1_rounded, filled: true),
            _HeroButton(label: 'Criar treino', icon: Icons.add_task_rounded),
            _HeroButton(label: 'Relatório', icon: Icons.show_chart_rounded),
          ],
        ),
      ],
    );
  }
}

class _StatsStrip extends StatelessWidget {
  const _StatsStrip();

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (BuildContext context, BoxConstraints constraints) {
        final bool compact = constraints.maxWidth < 980;
        if (compact) {
          return Padding(
            padding: const EdgeInsets.only(top: 14),
            child: Wrap(
              spacing: 12,
              runSpacing: 12,
              children: ProfessorDashboardPage._stats
                  .map(
                    (stat) => SizedBox(
                      width: constraints.maxWidth < 620 ? constraints.maxWidth : (constraints.maxWidth - 12) / 2,
                      child: _StatCard(data: stat),
                    ),
                  )
                  .toList(),
            ),
          );
        }

        return Container(
          height: 108,
          padding: const EdgeInsets.symmetric(horizontal: 18),
          decoration: _P.premiumDecoration(radius: 18),
          child: Row(
            children: <Widget>[
              for (int i = 0; i < ProfessorDashboardPage._stats.length; i++) ...<Widget>[
                Expanded(child: _StatCard(data: ProfessorDashboardPage._stats[i], flat: true)),
                if (i < ProfessorDashboardPage._stats.length - 1) const _VerticalRule(),
              ],
            ],
          ),
        );
      },
    );
  }
}

class _DashboardBody extends StatelessWidget {
  const _DashboardBody();

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (BuildContext context, BoxConstraints constraints) {
        final bool compact = constraints.maxWidth < 1180;
        if (compact) {
          return const Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              _StudentsPanel(),
              SizedBox(height: 14),
              _AgendaPanel(),
              SizedBox(height: 14),
              _AnalyticsCards(compact: true),
            ],
          );
        }

        return const Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Expanded(child: _StudentsPanel()),
            SizedBox(width: 20),
            SizedBox(
              width: 364,
              child: Column(
                children: <Widget>[
                  _AgendaPanel(),
                  SizedBox(height: 14),
                  _AnalyticsCards(compact: false),
                ],
              ),
            ),
          ],
        );
      },
    );
  }
}

class _StudentsPanel extends StatelessWidget {
  const _StudentsPanel();

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (BuildContext context, BoxConstraints constraints) {
        final bool compact = constraints.maxWidth < 760;
        return _PremiumPanel(
          padding: EdgeInsets.zero,
          child: Column(
            children: <Widget>[
              _StudentsHeader(compact: compact),
              const Divider(height: 1, color: _P.borderSoft),
              if (!compact)
                SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  clipBehavior: Clip.hardEdge,
                  child: ConstrainedBox(
                    constraints: BoxConstraints(minWidth: constraints.maxWidth),
                    child: SizedBox(
                      width: math.max(constraints.maxWidth, 1080),
                      child: Column(
                        children: <Widget>[
                          const _StudentsTableHeader(),
                          for (final _StudentData student in ProfessorDashboardPage._students) _StudentTableRow(student: student),
                          const _PaginationFooter(),
                        ],
                      ),
                    ),
                  ),
                )
              else ...<Widget>[
                Padding(
                  padding: const EdgeInsets.all(14),
                  child: Column(
                    children: <Widget>[
                      for (final _StudentData student in ProfessorDashboardPage._students) ...<Widget>[
                        _StudentMobileCard(student: student),
                        if (student != ProfessorDashboardPage._students.last) const SizedBox(height: 10),
                      ],
                    ],
                  ),
                ),
                const _PaginationFooter(),
              ],
            ],
          ),
        );
      },
    );
  }
}

class _StudentsHeader extends StatelessWidget {
  const _StudentsHeader({required this.compact});

  final bool compact;

  @override
  Widget build(BuildContext context) {
    final Widget title = const Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        _SectionLabel('GESTÃO DE ALUNOS'),
        SizedBox(height: 10),
        Text(
          'Alunos acompanhados',
          style: TextStyle(color: _P.text, fontSize: 28, height: 1, fontWeight: FontWeight.w900, letterSpacing: -0.7),
        ),
        SizedBox(height: 8),
        Text(
          'Status, último treino, aderência e ação rápida.',
          style: TextStyle(color: _P.muted, fontSize: 13, fontWeight: FontWeight.w600),
        ),
      ],
    );

    final Widget actions = const Wrap(
      spacing: 8,
      runSpacing: 8,
      children: <Widget>[
        _SmallButton(label: 'Buscar', icon: Icons.search_rounded),
        _SmallButton(label: 'Filtrar', icon: Icons.tune_rounded),
        _SmallButton(label: 'Novo aluno', icon: Icons.add_rounded, filled: true),
      ],
    );

    return Padding(
      padding: const EdgeInsets.fromLTRB(18, 20, 18, 18),
      child: compact
          ? Column(crossAxisAlignment: CrossAxisAlignment.start, children: <Widget>[title, const SizedBox(height: 16), actions])
          : Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: <Widget>[
                Expanded(child: title),
                const SizedBox(width: 16),
                actions,
              ],
            ),
    );
  }
}

class _StudentsTableHeader extends StatelessWidget {
  const _StudentsTableHeader();

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.fromLTRB(18, 12, 18, 8),
      child: Row(
        children: <Widget>[
          SizedBox(width: 210, child: _HeaderText('ALUNO')),
          SizedBox(width: 130, child: _HeaderText('OBJETIVO')),
          SizedBox(width: 160, child: _HeaderText('ÚLTIMO TREINO')),
          SizedBox(width: 150, child: _HeaderText('ADERÊNCIA')),
          SizedBox(width: 135, child: _HeaderText('PRÓXIMO')),
          SizedBox(width: 150, child: _HeaderText('STATUS')),
          SizedBox(width: 92, child: _HeaderText('AÇÕES')),
        ],
      ),
    );
  }
}

class _StudentTableRow extends StatelessWidget {
  const _StudentTableRow({required this.student});

  final _StudentData student;

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: const BoxConstraints(minHeight: 88),
      padding: const EdgeInsets.fromLTRB(18, 14, 18, 14),
      decoration: const BoxDecoration(border: Border(top: BorderSide(color: _P.line))),
      child: Row(
        children: <Widget>[
          SizedBox(
            width: 210,
            child: Row(
              children: <Widget>[
                _Avatar(initials: student.initials),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      Text(student.name, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(color: _P.text, fontSize: 14, fontWeight: FontWeight.w900)),
                      const SizedBox(height: 5),
                      _TinyBadge(student.level),
                    ],
                  ),
                ),
              ],
            ),
          ),
          SizedBox(width: 130, child: _BodyText(student.objective)),
          SizedBox(width: 160, child: _TwoLineText(student.lastWorkout, student.lastDate)),
          SizedBox(width: 150, child: _ProgressCell(value: student.adherence)),
          SizedBox(width: 135, child: _BodyText(student.next)),
          SizedBox(width: 150, child: Align(alignment: Alignment.centerLeft, child: _StatusBadge(label: student.status, tone: student.tone))),
          SizedBox(
            width: 92,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: const <Widget>[
                _IconBox(Icons.visibility_outlined),
                SizedBox(width: 8),
                _IconBox(Icons.edit_outlined),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _StudentMobileCard extends StatelessWidget {
  const _StudentMobileCard({required this.student});

  final _StudentData student;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(color: _P.card, borderRadius: BorderRadius.circular(16), border: Border.all(color: _P.borderSoft)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            children: <Widget>[
              _Avatar(initials: student.initials),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(student.name, style: const TextStyle(color: _P.text, fontSize: 15, fontWeight: FontWeight.w900)),
                    const SizedBox(height: 5),
                    Wrap(spacing: 6, runSpacing: 6, children: <Widget>[_TinyBadge(student.objective), _TinyBadge(student.level)]),
                  ],
                ),
              ),
              _StatusBadge(label: student.status, tone: student.tone),
            ],
          ),
          const SizedBox(height: 14),
          Row(
            children: <Widget>[
              Expanded(child: _TwoLineText('Último treino', student.lastWorkout)),
              Expanded(child: _TwoLineText('Próximo', student.next)),
            ],
          ),
          const SizedBox(height: 12),
          _ProgressCell(value: student.adherence),
        ],
      ),
    );
  }
}

class _AgendaPanel extends StatelessWidget {
  const _AgendaPanel();

  @override
  Widget build(BuildContext context) {
    return _PremiumPanel(
      padding: const EdgeInsets.fromLTRB(18, 18, 18, 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            children: <Widget>[
              const Icon(Icons.calendar_month_rounded, color: _P.gold, size: 22),
              const SizedBox(width: 10),
              const Expanded(child: Text('AGENDA DE HOJE', style: TextStyle(color: _P.gold, fontSize: 14, fontWeight: FontWeight.w900, letterSpacing: 0.6))),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 8),
                decoration: BoxDecoration(borderRadius: BorderRadius.circular(999), border: Border.all(color: _P.borderSoft), color: _P.blackAlpha25),
                child: const Text('Ver agenda', style: TextStyle(color: _P.text, fontSize: 11, fontWeight: FontWeight.w900)),
              ),
            ],
          ),
          const SizedBox(height: 14),
          Container(
            decoration: BoxDecoration(color: _P.card, borderRadius: BorderRadius.circular(14), border: Border.all(color: _P.borderSoft)),
            child: Column(
              children: <Widget>[
                for (int i = 0; i < ProfessorDashboardPage._schedule.length; i++)
                  _AgendaItem(item: ProfessorDashboardPage._schedule[i], showBorder: i != ProfessorDashboardPage._schedule.length - 1),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _AnalyticsCards extends StatelessWidget {
  const _AnalyticsCards({required this.compact});

  final bool compact;

  @override
  Widget build(BuildContext context) {
    if (compact) {
      return const Column(
        children: <Widget>[
          SizedBox(height: 236, child: _AdherenceCard()),
          SizedBox(height: 12),
          SizedBox(height: 236, child: _EvolutionCard()),
        ],
      );
    }

    return const SizedBox(
      height: 260,
      child: Row(
        children: <Widget>[
          Expanded(child: _AdherenceCard()),
          SizedBox(width: 12),
          Expanded(child: _EvolutionCard()),
        ],
      ),
    );
  }
}

class _AdherenceCard extends StatelessWidget {
  const _AdherenceCard();

  @override
  Widget build(BuildContext context) {
    return _PremiumPanel(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const Text(
            'ADERÊNCIA DA SEMANA',
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(color: _P.gold, fontSize: 12, height: 1.12, fontWeight: FontWeight.w900, letterSpacing: 0.45),
          ),
          Expanded(
            child: Center(
              child: SizedBox(
                width: 104,
                height: 104,
                child: Stack(
                  alignment: Alignment.center,
                  children: const <Widget>[
                    CustomPaint(size: Size(104, 104), painter: _RingPainter(progress: 0.74)),
                    Column(
                      mainAxisSize: MainAxisSize.min,
                      children: <Widget>[
                        Text('74%', style: TextStyle(color: _P.text, fontSize: 27, height: 1, fontWeight: FontWeight.w900)),
                        SizedBox(height: 3),
                        Text('Média geral', style: TextStyle(color: _P.muted, fontSize: 10.5, fontWeight: FontWeight.w700)),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ),
          const Text(
            '↗ 6%  vs. semana passada',
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(color: _P.green, fontSize: 11.5, fontWeight: FontWeight.w800),
          ),
        ],
      ),
    );
  }
}

class _EvolutionCard extends StatelessWidget {
  const _EvolutionCard();

  @override
  Widget build(BuildContext context) {
    return _PremiumPanel(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: const <Widget>[
          Text(
            'EVOLUÇÃO MÉDIA',
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(color: _P.gold, fontSize: 12, height: 1.12, fontWeight: FontWeight.w900, letterSpacing: 0.45),
          ),
          Expanded(
            child: Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: <Widget>[
                  Text('23%', style: TextStyle(color: _P.text, fontSize: 29, height: 1, fontWeight: FontWeight.w900)),
                  SizedBox(height: 5),
                  Text('Carga e presença', style: TextStyle(color: _P.muted, fontSize: 10.5, fontWeight: FontWeight.w700)),
                  SizedBox(height: 16),
                  SizedBox(height: 50, child: CustomPaint(painter: _LineChartPainter())),
                ],
              ),
            ),
          ),
          Text(
            '↗ 4%  vs. mês passado',
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(color: _P.green, fontSize: 11.5, fontWeight: FontWeight.w800),
          ),
        ],
      ),
    );
  }
}

class _HeroButton extends StatelessWidget {
  const _HeroButton({required this.label, required this.icon, this.filled = false});

  final String label;
  final IconData icon;
  final bool filled;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 42,
      padding: const EdgeInsets.symmetric(horizontal: 24),
      decoration: BoxDecoration(
        gradient: filled ? _P.goldGradient : null,
        color: filled ? null : _P.blackGlass,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: filled ? Colors.transparent : _P.border),
        boxShadow: filled ? const <BoxShadow>[BoxShadow(color: _P.goldGlow, blurRadius: 24, offset: Offset(0, 9))] : null,
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          Icon(icon, size: 17, color: filled ? _P.black : _P.gold),
          const SizedBox(width: 9),
          Text(label, style: TextStyle(color: filled ? _P.black : _P.text, fontSize: 13, fontWeight: FontWeight.w900)),
        ],
      ),
    );
  }
}

class _SmallButton extends StatelessWidget {
  const _SmallButton({required this.label, required this.icon, this.filled = false});

  final String label;
  final IconData icon;
  final bool filled;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 38,
      padding: const EdgeInsets.symmetric(horizontal: 14),
      decoration: BoxDecoration(
        gradient: filled ? _P.goldGradient : null,
        color: filled ? null : _P.blackGlass,
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: filled ? Colors.transparent : _P.borderSoft),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          Icon(icon, size: 16, color: filled ? _P.black : _P.gold),
          const SizedBox(width: 8),
          Text(label, style: TextStyle(color: filled ? _P.black : _P.text, fontSize: 11, fontWeight: FontWeight.w900)),
        ],
      ),
    );
  }
}

class _StatCard extends StatelessWidget {
  const _StatCard({required this.data, this.flat = false});

  final _StatData data;
  final bool flat;

  @override
  Widget build(BuildContext context) {
    final Widget content = Row(
      children: <Widget>[
        Container(
          width: 48,
          height: 48,
          decoration: BoxDecoration(
            gradient: _P.goldGradient,
            borderRadius: BorderRadius.circular(13),
            boxShadow: const <BoxShadow>[BoxShadow(color: _P.goldGlow, blurRadius: 22, offset: Offset(0, 8))],
          ),
          child: Icon(data.icon, color: _P.black, size: 22),
        ),
        const SizedBox(width: 14),
        Expanded(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(data.value, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(color: _P.text, fontSize: 28, height: 1, fontWeight: FontWeight.w900, letterSpacing: -0.8)),
              const SizedBox(height: 4),
              Text(data.title, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(color: _P.text, fontSize: 13, fontWeight: FontWeight.w900)),
              const SizedBox(height: 2),
              Text(data.subtitle, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(color: _P.muted, fontSize: 12, fontWeight: FontWeight.w600)),
            ],
          ),
        ),
      ],
    );

    if (flat) return content;
    return _PremiumPanel(padding: const EdgeInsets.all(18), child: content);
  }
}

class _PremiumPanel extends StatelessWidget {
  const _PremiumPanel({required this.child, this.padding = const EdgeInsets.all(18)});

  final Widget child;
  final EdgeInsetsGeometry padding;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: padding,
      decoration: _P.premiumDecoration(radius: 18),
      child: child,
    );
  }
}

class _AgendaItem extends StatelessWidget {
  const _AgendaItem({required this.item, required this.showBorder});

  final _ScheduleData item;
  final bool showBorder;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 58,
      padding: const EdgeInsets.symmetric(horizontal: 12),
      decoration: BoxDecoration(border: showBorder ? const Border(bottom: BorderSide(color: _P.line)) : null),
      child: Row(
        children: <Widget>[
          SizedBox(width: 50, child: Text(item.time, style: const TextStyle(color: _P.gold, fontSize: 13, fontWeight: FontWeight.w900))),
          Container(width: 7, height: 7, decoration: const BoxDecoration(color: _P.gold, shape: BoxShape.circle, boxShadow: <BoxShadow>[BoxShadow(color: _P.goldGlow, blurRadius: 12)])),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(item.name, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(color: _P.text, fontSize: 13, fontWeight: FontWeight.w900)),
                const SizedBox(height: 2),
                Text(item.training, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(color: _P.muted, fontSize: 12, fontWeight: FontWeight.w600)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _Avatar extends StatelessWidget {
  const _Avatar({required this.initials});

  final String initials;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 40,
      height: 40,
      alignment: Alignment.center,
      decoration: BoxDecoration(shape: BoxShape.circle, gradient: _P.goldGradient, border: Border.all(color: _P.goldDeep), boxShadow: const <BoxShadow>[BoxShadow(color: _P.goldGlow, blurRadius: 18, offset: Offset(0, 6))]),
      child: Text(initials, style: const TextStyle(color: _P.black, fontSize: 11, fontWeight: FontWeight.w900)),
    );
  }
}

class _ProgressCell extends StatelessWidget {
  const _ProgressCell({required this.value});

  final int value;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: <Widget>[
        SizedBox(width: 38, child: Text('$value%', style: const TextStyle(color: _P.text, fontSize: 13, fontWeight: FontWeight.w900))),
        const SizedBox(width: 9),
        Expanded(
          child: ClipRRect(
            borderRadius: BorderRadius.circular(999),
            child: LinearProgressIndicator(
              minHeight: 7,
              value: value / 100,
              backgroundColor: _P.line,
              valueColor: const AlwaysStoppedAnimation<Color>(_P.gold),
            ),
          ),
        ),
      ],
    );
  }
}

class _PaginationFooter extends StatelessWidget {
  const _PaginationFooter();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(18, 14, 18, 16),
      child: Row(
        children: <Widget>[
          const Expanded(child: Text('Mostrando 1 a 5 de 18 alunos', style: TextStyle(color: _P.muted, fontSize: 12, fontWeight: FontWeight.w600))),
          const _PageBox(Icons.chevron_left_rounded),
          const SizedBox(width: 8),
          Container(width: 28, height: 28, alignment: Alignment.center, decoration: BoxDecoration(gradient: _P.goldGradient, borderRadius: BorderRadius.circular(7)), child: const Text('1', style: TextStyle(color: _P.black, fontSize: 12, fontWeight: FontWeight.w900))),
          const SizedBox(width: 14),
          const Text('2', style: TextStyle(color: _P.muted, fontSize: 11, fontWeight: FontWeight.w900)),
          const SizedBox(width: 22),
          const Text('3', style: TextStyle(color: _P.muted, fontSize: 11, fontWeight: FontWeight.w900)),
          const SizedBox(width: 22),
          const Text('4', style: TextStyle(color: _P.muted, fontSize: 11, fontWeight: FontWeight.w900)),
          const SizedBox(width: 8),
          const _PageBox(Icons.chevron_right_rounded),
        ],
      ),
    );
  }
}

class _PageBox extends StatelessWidget {
  const _PageBox(this.icon);

  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Container(width: 28, height: 28, decoration: BoxDecoration(color: _P.blackGlass, borderRadius: BorderRadius.circular(7), border: Border.all(color: _P.borderSoft)), child: Icon(icon, color: _P.gold, size: 18));
  }
}

class _StatusBadge extends StatelessWidget {
  const _StatusBadge({required this.label, required this.tone});

  final String label;
  final _StatusTone tone;

  Color get color => switch (tone) {
        _StatusTone.green => _P.green,
        _StatusTone.gold => _P.gold,
        _StatusTone.blue => _P.blue,
        _StatusTone.purple => _P.purple,
      };

  Color get bg => switch (tone) {
        _StatusTone.green => _P.greenBg,
        _StatusTone.gold => _P.goldBadgeBg,
        _StatusTone.blue => _P.blueBg,
        _StatusTone.purple => _P.purpleBg,
      };

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
      decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(8), border: Border.all(color: color.withValues(alpha: 0.18))),
      child: Text(label, maxLines: 1, overflow: TextOverflow.ellipsis, style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.w900)),
    );
  }
}

class _TinyBadge extends StatelessWidget {
  const _TinyBadge(this.text);

  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: const BoxConstraints(minHeight: 20),
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      alignment: Alignment.center,
      decoration: BoxDecoration(color: _P.goldBadgeBg, borderRadius: BorderRadius.circular(999), border: Border.all(color: _P.borderSoft)),
      child: Text(text, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(color: _P.gold, fontSize: 10, height: 1, fontWeight: FontWeight.w900)),
    );
  }
}

class _IconBox extends StatelessWidget {
  const _IconBox(this.icon);

  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Container(width: 30, height: 30, decoration: BoxDecoration(color: _P.blackGlass, borderRadius: BorderRadius.circular(8), border: Border.all(color: _P.border)), child: Icon(icon, color: _P.gold, size: 16));
  }
}

class _HeaderText extends StatelessWidget {
  const _HeaderText(this.text);

  final String text;

  @override
  Widget build(BuildContext context) {
    return Text(text, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(color: _P.gold, fontSize: 11, fontWeight: FontWeight.w900, letterSpacing: 0.7));
  }
}

class _BodyText extends StatelessWidget {
  const _BodyText(this.text);

  final String text;

  @override
  Widget build(BuildContext context) {
    return Text(text, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(color: _P.text, fontSize: 13, fontWeight: FontWeight.w700, height: 1.18));
  }
}

class _TwoLineText extends StatelessWidget {
  const _TwoLineText(this.main, this.sub);

  final String main;
  final String sub;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisAlignment: MainAxisAlignment.center,
      children: <Widget>[
        Text(main, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(color: _P.text, fontSize: 13, fontWeight: FontWeight.w900)),
        const SizedBox(height: 3),
        Text(sub, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(color: _P.muted, fontSize: 12, fontWeight: FontWeight.w600)),
      ],
    );
  }
}

class _SectionBadge extends StatelessWidget {
  const _SectionBadge({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 15, vertical: 9),
      decoration: BoxDecoration(color: _P.goldBadgeBg, borderRadius: BorderRadius.circular(999), border: Border.all(color: _P.border)),
      child: Text(label, style: const TextStyle(color: _P.gold, fontSize: 12, fontWeight: FontWeight.w900, letterSpacing: 1.0)),
    );
  }
}

class _SectionLabel extends StatelessWidget {
  const _SectionLabel(this.text);

  final String text;

  @override
  Widget build(BuildContext context) {
    return Text(text, style: const TextStyle(color: _P.gold, fontSize: 12, fontWeight: FontWeight.w900, letterSpacing: 1.2));
  }
}

class _VerticalRule extends StatelessWidget {
  const _VerticalRule();

  @override
  Widget build(BuildContext context) {
    return Container(width: 1, height: 58, margin: const EdgeInsets.symmetric(horizontal: 10), color: _P.line);
  }
}

class _BackgroundGlow extends StatelessWidget {
  const _BackgroundGlow();

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: const <Widget>[
        Positioned.fill(child: ColoredBox(color: _P.black)),
        Positioned(top: -170, left: -150, child: _BlurCircle(size: 430, color: _P.goldSoftGlow)),
        Positioned(top: 40, right: -180, child: _BlurCircle(size: 560, color: _P.goldSoftGlow2)),
        Positioned(bottom: -260, right: 80, child: _BlurCircle(size: 600, color: _P.goldSoftGlow3)),
      ],
    );
  }
}

class _BlurCircle extends StatelessWidget {
  const _BlurCircle({required this.size, required this.color});

  final double size;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(width: size, height: size, decoration: BoxDecoration(shape: BoxShape.circle, color: color));
  }
}

class _RingPainter extends CustomPainter {
  const _RingPainter({required this.progress});

  final double progress;

  @override
  void paint(Canvas canvas, Size size) {
    final Offset center = Offset(size.width / 2, size.height / 2);
    final double radius = math.min(size.width, size.height) / 2 - 8;
    final Paint track = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 10
      ..strokeCap = StrokeCap.round
      ..color = _P.line;
    final Paint active = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 10
      ..strokeCap = StrokeCap.round
      ..shader = const SweepGradient(colors: <Color>[_P.gold, _P.goldDeep, _P.gold]).createShader(Rect.fromCircle(center: center, radius: radius));

    canvas.drawCircle(center, radius, track);
    canvas.drawArc(Rect.fromCircle(center: center, radius: radius), -math.pi / 2, progress * math.pi * 2, false, active);
  }

  @override
  bool shouldRepaint(covariant _RingPainter oldDelegate) => oldDelegate.progress != progress;
}

class _LineChartPainter extends CustomPainter {
  const _LineChartPainter();

  @override
  void paint(Canvas canvas, Size size) {
    final List<double> points = <double>[0.18, 0.32, 0.45, 0.58, 0.43, 0.52, 0.39, 0.55, 0.68, 0.82];
    final Paint grid = Paint()
      ..color = _P.line
      ..strokeWidth = 1;
    final Paint line = Paint()
      ..color = _P.gold
      ..strokeWidth = 2.2
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round;
    final Paint dot = Paint()..color = _P.gold;

    for (int i = 1; i < 4; i++) {
      final double y = size.height * i / 4;
      canvas.drawLine(Offset(0, y), Offset(size.width, y), grid);
    }

    final Path path = Path();
    for (int i = 0; i < points.length; i++) {
      final double x = size.width * i / (points.length - 1);
      final double y = size.height * (1 - points[i]);
      if (i == 0) {
        path.moveTo(x, y);
      } else {
        path.lineTo(x, y);
      }
      canvas.drawCircle(Offset(x, y), 3.2, dot);
    }
    canvas.drawPath(path, line);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _P {
  static const Color black = Color(0xFF050505);
  static const Color panel = Color(0xF20F0F0F);
  static const Color card = Color(0xFF151515);
  static const Color blackGlass = Color(0x73000000);
  static const Color blackAlpha72 = Color(0xB8050505);
  static const Color blackAlpha25 = Color(0x40050505);
  static const Color blackAlpha16 = Color(0x29050505);
  static const Color blackAlpha08 = Color(0x14050505);

  static const Color gold = Color(0xFFFFD33D);
  static const Color gold2 = Color(0xFFC79416);
  static const Color goldDeep = Color(0xFF7C5A0A);
  static const Color goldGlow = Color(0x57FFD33D);
  static const Color goldSoftGlow = Color(0x302D2205);
  static const Color goldSoftGlow2 = Color(0x402C2107);
  static const Color goldSoftGlow3 = Color(0x261F1705);
  static const Color heroGoldWash = Color(0x4E55420B);
  static const Color goldBadgeBg = Color(0x332A2207);

  static const Color text = Color(0xFFF8F5EC);
  static const Color mutedLight = Color(0xFFCCC5B6);
  static const Color muted = Color(0xFFA9A292);
  static const Color border = Color(0x8A7D5D12);
  static const Color borderSoft = Color(0x4D806012);
  static const Color line = Color(0x1FFFFFFF);
  static const Color shadow = Color(0x99000000);

  static const Color green = Color(0xFF77D85A);
  static const Color greenBg = Color(0x241CB329);
  static const Color blue = Color(0xFF57B7FF);
  static const Color blueBg = Color(0x1F1976D2);
  static const Color purple = Color(0xFFD287FF);
  static const Color purpleBg = Color(0x242A0A45);

  static const LinearGradient goldGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: <Color>[gold, gold2],
  );

  static BoxDecoration premiumDecoration({required double radius}) {
    return BoxDecoration(
      color: panel,
      borderRadius: BorderRadius.circular(radius),
      border: Border.all(color: borderSoft),
      boxShadow: const <BoxShadow>[BoxShadow(color: shadow, blurRadius: 34, offset: Offset(0, 18))],
    );
  }
}

class _StatData {
  const _StatData(this.icon, this.value, this.title, this.subtitle);

  final IconData icon;
  final String value;
  final String title;
  final String subtitle;
}

class _StudentData {
  const _StudentData({
    required this.name,
    required this.initials,
    required this.objective,
    required this.level,
    required this.lastWorkout,
    required this.lastDate,
    required this.adherence,
    required this.next,
    required this.status,
    required this.tone,
  });

  final String name;
  final String initials;
  final String objective;
  final String level;
  final String lastWorkout;
  final String lastDate;
  final int adherence;
  final String next;
  final String status;
  final _StatusTone tone;
}

class _ScheduleData {
  const _ScheduleData(this.time, this.name, this.training);

  final String time;
  final String name;
  final String training;
}

enum _StatusTone { green, gold, blue, purple }
