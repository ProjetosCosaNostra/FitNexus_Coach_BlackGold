import 'package:flutter/material.dart';

const Color _canvasColor = Color(0xFF050505);
const Color surface = Color(0xFF0E0E0E);
const Color surfaceRaised = Color(0xFF151515);
const Color line = Color(0xFF4A3510);
const Color muted = Color(0xFFB8B8B8);
const Color gold = Color(0xFFE5A91B);
const Color goldSoft = Color(0xFFFFD261);
const Color success = Color(0xFF21D07A);

class LandingPage extends StatelessWidget {
  const LandingPage({super.key});

  static const Color canvas = _canvasColor;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: canvas,
      body: SafeArea(
        bottom: false,
        child: LayoutBuilder(
          builder: (BuildContext context, BoxConstraints constraints) {
            final double width = constraints.maxWidth;
            final double horizontal = width < 520 ? 14 : 24;

            return SingleChildScrollView(
              child: Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 920),
                  child: Padding(
                    padding: EdgeInsets.fromLTRB(horizontal, 14, horizontal, 22),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: const <Widget>[
                        _TopBar(),
                        SizedBox(height: 18),
                        _GreetingRow(),
                        SizedBox(height: 18),
                        _HeroPanel(),
                        SizedBox(height: 14),
                        _MetricsSection(),
                        SizedBox(height: 14),
                        _ModulesSection(),
                        SizedBox(height: 14),
                        _WeeklyProgress(),
                        SizedBox(height: 14),
                        _BottomNavigation(),
                      ],
                    ),
                  ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}

class _TopBar extends StatelessWidget {
  const _TopBar();

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (BuildContext context, BoxConstraints constraints) {
        final bool compact = constraints.maxWidth < 430;
        return Row(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: <Widget>[
            const Expanded(child: _Brand()),
            SizedBox(width: compact ? 6 : 10),
            OutlinedButton.icon(
              onPressed: () => Navigator.of(context).pushNamed('/links'),
              icon: const Icon(Icons.hub_outlined, size: 17),
              label: const Text('Ecossistema'),
              style: OutlinedButton.styleFrom(
                foregroundColor: goldSoft,
                side: const BorderSide(color: gold, width: 1.1),
                padding: EdgeInsets.symmetric(
                  horizontal: compact ? 9 : 14,
                  vertical: 12,
                ),
                textStyle: TextStyle(
                  fontSize: compact ? 10 : 12,
                  fontWeight: FontWeight.w800,
                ),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
            ),
            SizedBox(width: compact ? 6 : 10),
            FilledButton(
              key: const ValueKey<String>('public-signup-entry'),
              onPressed: () => Navigator.of(context).pushNamed('/start'),
              style: FilledButton.styleFrom(
                backgroundColor: goldSoft,
                foregroundColor: Colors.black,
                padding: EdgeInsets.symmetric(
                  horizontal: compact ? 10 : 16,
                  vertical: 13,
                ),
                textStyle: TextStyle(
                  fontSize: compact ? 10 : 12,
                  fontWeight: FontWeight.w900,
                ),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              child: const Text('Criar conta'),
            ),
          ],
        );
      },
    );
  }
}

class _Brand extends StatelessWidget {
  const _Brand();

  @override
  Widget build(BuildContext context) {
    return FittedBox(
      fit: BoxFit.scaleDown,
      alignment: Alignment.centerLeft,
      child: const Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text.rich(
            TextSpan(
              children: <InlineSpan>[
                TextSpan(
                  text: 'FIT',
                  style: TextStyle(color: Colors.white),
                ),
                TextSpan(
                  text: 'NEXUS',
                  style: TextStyle(color: goldSoft),
                ),
              ],
            ),
            style: TextStyle(
              fontSize: 26,
              fontWeight: FontWeight.w500,
              letterSpacing: 0.8,
              height: 1,
            ),
          ),
          SizedBox(height: 5),
          Text(
            'COACH  BLACKGOLD',
            style: TextStyle(
              color: Colors.white,
              fontSize: 8.5,
              fontWeight: FontWeight.w600,
              letterSpacing: 2.2,
            ),
          ),
        ],
      ),
    );
  }
}

class _GreetingRow extends StatelessWidget {
  const _GreetingRow();

  @override
  Widget build(BuildContext context) {
    return Row(
      children: <Widget>[
        Expanded(
          child: InkWell(
            key: const ValueKey<String>('public-login-entry'),
            onTap: () => Navigator.of(context).pushNamed('/auth'),
            borderRadius: BorderRadius.circular(18),
            child: const Padding(
              padding: EdgeInsets.symmetric(vertical: 2),
              child: Row(
                children: <Widget>[
                  _Avatar(),
                  SizedBox(width: 12),
                  Flexible(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text(
                          'Bom dia,',
                          style: TextStyle(
                            color: muted,
                            fontSize: 14,
                            height: 1.1,
                          ),
                        ),
                        SizedBox(height: 2),
                        Text(
                          'Felipe',
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 24,
                            fontWeight: FontWeight.w800,
                            height: 1.05,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
        const SizedBox(width: 10),
        Container(
          constraints: const BoxConstraints(minWidth: 116),
          padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 10),
          decoration: BoxDecoration(
            color: surface,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: const Color(0xFF292929)),
          ),
          child: const Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Row(
                mainAxisSize: MainAxisSize.min,
                children: <Widget>[
                  Icon(Icons.circle, size: 10, color: goldSoft),
                  SizedBox(width: 7),
                  Text(
                    'Em dia',
                    style: TextStyle(
                      color: goldSoft,
                      fontSize: 12,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ],
              ),
              SizedBox(height: 3),
              Text(
                'Continue assim!',
                style: TextStyle(color: muted, fontSize: 10.5),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _Avatar extends StatelessWidget {
  const _Avatar();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 52,
      height: 52,
      padding: const EdgeInsets.all(2),
      decoration: const BoxDecoration(
        shape: BoxShape.circle,
        gradient: LinearGradient(
          colors: <Color>[goldSoft, Color(0xFF9C6500)],
        ),
      ),
      child: Container(
        decoration: const BoxDecoration(
          color: Color(0xFF171717),
          shape: BoxShape.circle,
        ),
        child: const Icon(
          Icons.person_rounded,
          color: Color(0xFFE5E5E5),
          size: 29,
        ),
      ),
    );
  }
}

class _HeroPanel extends StatelessWidget {
  const _HeroPanel();

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (BuildContext context, BoxConstraints constraints) {
        final bool narrow = constraints.maxWidth < 410;
        final double height = narrow ? 385 : constraints.maxWidth < 620 ? 410 : 445;

        return Container(
          height: height,
          clipBehavior: Clip.antiAlias,
          decoration: BoxDecoration(
            color: surface,
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: line, width: 1.1),
          ),
          child: Stack(
            fit: StackFit.expand,
            children: <Widget>[
              Positioned.fill(
                child: Image.asset(
                  'assets/images/professor_dashboard_hero.webp',
                  fit: BoxFit.cover,
                  alignment: Alignment.centerRight,
                  errorBuilder: (_, __, ___) => const ColoredBox(color: surface),
                ),
              ),
              const DecoratedBox(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.centerLeft,
                    end: Alignment.centerRight,
                    stops: <double>[0, 0.52, 1],
                    colors: <Color>[
                      Color(0xFF080808),
                      Color(0xE6080808),
                      Color(0x25080808),
                    ],
                  ),
                ),
              ),
              Positioned(
                right: 22,
                top: 26,
                child: IgnorePointer(
                  child: Text(
                    'X',
                    style: TextStyle(
                      color: goldSoft.withValues(alpha: 0.34),
                      fontSize: narrow ? 76 : 106,
                      fontWeight: FontWeight.w200,
                      shadows: const <Shadow>[
                        Shadow(color: gold, blurRadius: 22),
                      ],
                    ),
                  ),
                ),
              ),
              Padding(
                padding: EdgeInsets.fromLTRB(
                  narrow ? 18 : 22,
                  narrow ? 22 : 28,
                  narrow ? 14 : 22,
                  20,
                ),
                child: Align(
                  alignment: Alignment.centerLeft,
                  child: FractionallySizedBox(
                    widthFactor: narrow ? 0.72 : 0.62,
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: <Widget>[
                        Text.rich(
                          TextSpan(
                            children: <InlineSpan>[
                              const TextSpan(
                                text: 'Sua evolução\n',
                                style: TextStyle(color: Colors.white),
                              ),
                              const TextSpan(
                                text: 'sob controle.',
                                style: TextStyle(color: goldSoft),
                              ),
                            ],
                          ),
                          style: TextStyle(
                            fontSize: narrow ? 29 : 35,
                            height: 1.02,
                            fontWeight: FontWeight.w900,
                            letterSpacing: -1.0,
                          ),
                        ),
                        const SizedBox(height: 13),
                        Text(
                          'Treino, alimentação, progresso e acompanhamento em um só lugar para transformar sua rotina.',
                          style: TextStyle(
                            color: const Color(0xFFE0E0E0),
                            fontSize: narrow ? 12.2 : 14,
                            height: 1.42,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                        const SizedBox(height: 18),
                        FilledButton.icon(
                          onPressed: () => Navigator.of(context).pushNamed('/start'),
                          icon: const Icon(Icons.play_arrow_rounded),
                          label: const Text('Começar treino'),
                          style: FilledButton.styleFrom(
                            backgroundColor: goldSoft,
                            foregroundColor: Colors.black,
                            minimumSize: const Size(0, 50),
                            textStyle: const TextStyle(
                              fontWeight: FontWeight.w900,
                              fontSize: 14,
                            ),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                            ),
                          ),
                        ),
                        const SizedBox(height: 9),
                        _HeroOutlineAction(
                          icon: Icons.restaurant_menu_rounded,
                          label: 'Plano alimentar',
                          onPressed: () => Navigator.of(context).pushNamed('/start'),
                        ),
                        const SizedBox(height: 9),
                        _HeroOutlineAction(
                          icon: Icons.chat_bubble_outline_rounded,
                          label: 'Falar com coach',
                          onPressed: () => Navigator.of(context).pushNamed('/support'),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _HeroOutlineAction extends StatelessWidget {
  const _HeroOutlineAction({
    required this.icon,
    required this.label,
    required this.onPressed,
  });

  final IconData icon;
  final String label;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return OutlinedButton.icon(
      onPressed: onPressed,
      icon: Icon(icon, size: 18),
      label: Text(label),
      style: OutlinedButton.styleFrom(
        foregroundColor: Colors.white,
        alignment: Alignment.centerLeft,
        minimumSize: const Size(0, 43),
        side: const BorderSide(color: gold),
        textStyle: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.w700),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(11)),
      ),
    );
  }
}

class _MetricsSection extends StatelessWidget {
  const _MetricsSection();

  static const List<_MetricData> _metrics = <_MetricData>[
    _MetricData(
      icon: Icons.fitness_center_rounded,
      label: 'Treinos da semana',
      value: '5/6',
      detail: '83%',
      progress: 0.83,
    ),
    _MetricData(
      icon: Icons.local_fire_department_outlined,
      label: 'Calorias',
      value: '2.450',
      detail: '▲ 12%',
      unit: 'kcal',
      positive: true,
    ),
    _MetricData(
      icon: Icons.monitor_weight_outlined,
      label: 'Peso',
      value: '78,4',
      detail: '▼ 0,6 kg',
      unit: 'kg',
      positive: true,
    ),
    _MetricData(
      icon: Icons.trending_up_rounded,
      label: 'Progresso',
      value: '72%',
      detail: '↗ evolução',
      positive: true,
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (BuildContext context, BoxConstraints constraints) {
        final int columns = constraints.maxWidth >= 350 ? 4 : 2;
        const double gap = 9;
        final double cardWidth =
            (constraints.maxWidth - gap * (columns - 1)) / columns;

        return Wrap(
          spacing: gap,
          runSpacing: gap,
          children: _metrics
              .map(
                (_MetricData item) => SizedBox(
                  width: cardWidth,
                  child: _MetricCard(data: item),
                ),
              )
              .toList(),
        );
      },
    );
  }
}

class _MetricData {
  const _MetricData({
    required this.icon,
    required this.label,
    required this.value,
    required this.detail,
    this.unit,
    this.progress,
    this.positive = false,
  });

  final IconData icon;
  final String label;
  final String value;
  final String detail;
  final String? unit;
  final double? progress;
  final bool positive;
}

class _MetricCard extends StatelessWidget {
  const _MetricCard({required this.data});

  final _MetricData data;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 132,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: line),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Icon(data.icon, color: goldSoft, size: 19),
              const SizedBox(width: 7),
              Expanded(
                child: Text(
                  data.label,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    color: Color(0xFFD8D8D8),
                    fontSize: 10.5,
                    height: 1.15,
                  ),
                ),
              ),
            ],
          ),
          const Spacer(),
          FittedBox(
            fit: BoxFit.scaleDown,
            alignment: Alignment.centerLeft,
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: <Widget>[
                Text(
                  data.value,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 25,
                    fontWeight: FontWeight.w900,
                    height: 1,
                  ),
                ),
                if (data.unit != null) ...<Widget>[
                  const SizedBox(width: 4),
                  Text(
                    data.unit!,
                    style: const TextStyle(color: muted, fontSize: 10),
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(height: 7),
          if (data.progress != null) ...<Widget>[
            ClipRRect(
              borderRadius: BorderRadius.circular(999),
              child: LinearProgressIndicator(
                minHeight: 5,
                value: data.progress,
                backgroundColor: const Color(0xFF2B2418),
                valueColor: const AlwaysStoppedAnimation<Color>(goldSoft),
              ),
            ),
            const SizedBox(height: 5),
          ],
          Text(
            data.detail,
            style: TextStyle(
              color: data.positive ? success : goldSoft,
              fontSize: 10,
              fontWeight: FontWeight.w800,
            ),
          ),
        ],
      ),
    );
  }
}

class _ModulesSection extends StatelessWidget {
  const _ModulesSection();

  static const List<_ModuleData> _modules = <_ModuleData>[
    _ModuleData(
      icon: Icons.fitness_center_rounded,
      title: 'Treinos',
      subtitle: 'Planos personalizados',
    ),
    _ModuleData(
      icon: Icons.ramen_dining_outlined,
      title: 'Nutrição',
      subtitle: 'Alimentação inteligente',
    ),
    _ModuleData(
      icon: Icons.calendar_month_outlined,
      title: 'Agenda',
      subtitle: 'Compromissos e treinos',
    ),
    _ModuleData(
      icon: Icons.bar_chart_rounded,
      title: 'Resultados',
      subtitle: 'Acompanhe sua evolução',
    ),
    _ModuleData(
      icon: Icons.spa_outlined,
      title: 'Hábitos',
      subtitle: 'Constância que transforma',
    ),
    _ModuleData(
      icon: Icons.groups_2_outlined,
      title: 'Comunidade',
      subtitle: 'Conecte-se e evolua',
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (BuildContext context, BoxConstraints constraints) {
        final int columns = constraints.maxWidth < 330 ? 2 : 3;
        const double gap = 10;
        final double width =
            (constraints.maxWidth - gap * (columns - 1)) / columns;

        return Wrap(
          spacing: gap,
          runSpacing: gap,
          children: _modules
              .map(
                (_ModuleData item) => SizedBox(
                  width: width,
                  height: 126,
                  child: _ModuleCard(data: item),
                ),
              )
              .toList(),
        );
      },
    );
  }
}

class _ModuleData {
  const _ModuleData({
    required this.icon,
    required this.title,
    required this.subtitle,
  });

  final IconData icon;
  final String title;
  final String subtitle;
}

class _ModuleCard extends StatelessWidget {
  const _ModuleCard({required this.data});

  final _ModuleData data;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: surface,
      borderRadius: BorderRadius.circular(16),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: () => Navigator.of(context).pushNamed('/start'),
        child: Ink(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: line),
            gradient: const LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: <Color>[Color(0xFF17120B), Color(0xFF090909)],
            ),
          ),
          child: Stack(
            children: <Widget>[
              Positioned(
                right: -4,
                top: 8,
                child: Icon(
                  data.icon,
                  size: 70,
                  color: goldSoft.withValues(alpha: 0.09),
                ),
              ),
              Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: <Widget>[
                    Icon(data.icon, color: goldSoft, size: 24),
                    const Spacer(),
                    Text(
                      data.title,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 13.5,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      data.subtitle,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: muted,
                        fontSize: 9.5,
                        height: 1.15,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _WeeklyProgress extends StatelessWidget {
  const _WeeklyProgress();

  static const List<String> _days = <String>['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'];

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(14, 14, 14, 12),
      decoration: BoxDecoration(
        color: surface,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: line),
      ),
      child: Column(
        children: <Widget>[
          const Row(
            children: <Widget>[
              Icon(Icons.multiline_chart_rounded, color: goldSoft, size: 20),
              SizedBox(width: 9),
              Expanded(
                child: Text(
                  'Seu progresso semanal',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 14,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),
              Text(
                'Ver detalhes',
                style: TextStyle(color: muted, fontSize: 10.5),
              ),
              SizedBox(width: 4),
              Icon(Icons.chevron_right_rounded, color: goldSoft, size: 18),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: List<Widget>.generate(
              _days.length,
              (int index) => Expanded(
                child: _DayProgress(
                  day: _days[index],
                  state: index < 3
                      ? _DayState.done
                      : index == 3
                          ? _DayState.partial
                          : _DayState.pending,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

enum _DayState { done, partial, pending }

class _DayProgress extends StatelessWidget {
  const _DayProgress({required this.day, required this.state});

  final String day;
  final _DayState state;

  @override
  Widget build(BuildContext context) {
    final bool done = state == _DayState.done;
    final bool partial = state == _DayState.partial;

    return Column(
      children: <Widget>[
        Container(
          width: 34,
          height: 34,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            border: Border.all(
              color: done || partial ? goldSoft : const Color(0xFF6C6C6C),
              width: done ? 2.3 : 1.5,
            ),
            gradient: partial
                ? const LinearGradient(
                    begin: Alignment.centerLeft,
                    end: Alignment.centerRight,
                    colors: <Color>[Color(0xB3E5A91B), Color(0x00101010)],
                  )
                : null,
          ),
          child: done
              ? const Icon(Icons.check_rounded, color: goldSoft, size: 19)
              : null,
        ),
        const SizedBox(height: 6),
        Text(
          day,
          style: const TextStyle(color: muted, fontSize: 9.5),
        ),
      ],
    );
  }
}

class _BottomNavigation extends StatelessWidget {
  const _BottomNavigation();

  static const List<_NavData> _items = <_NavData>[
    _NavData(icon: Icons.home_rounded, label: 'Início', active: true),
    _NavData(icon: Icons.fitness_center_rounded, label: 'Treinos'),
    _NavData(icon: Icons.assignment_turned_in_outlined, label: 'Plano'),
    _NavData(icon: Icons.stacked_line_chart_rounded, label: 'Progresso'),
    _NavData(icon: Icons.grid_view_rounded, label: 'Mais'),
  ];

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 9),
      decoration: BoxDecoration(
        color: const Color(0xFF0C0C0C),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFF303030)),
        boxShadow: const <BoxShadow>[
          BoxShadow(color: Color(0x66000000), blurRadius: 20, offset: Offset(0, 8)),
        ],
      ),
      child: Row(
        children: _items
            .map(
              (_NavData item) => Expanded(
                child: InkWell(
                  onTap: item.active
                      ? null
                      : () => Navigator.of(context).pushNamed('/start'),
                  borderRadius: BorderRadius.circular(12),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(vertical: 4),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: <Widget>[
                        Icon(
                          item.icon,
                          size: 22,
                          color: item.active ? goldSoft : const Color(0xFFB0B0B0),
                        ),
                        const SizedBox(height: 4),
                        FittedBox(
                          fit: BoxFit.scaleDown,
                          child: Text(
                            item.label,
                            style: TextStyle(
                              color: item.active ? goldSoft : const Color(0xFFB0B0B0),
                              fontSize: 9.5,
                              fontWeight: item.active ? FontWeight.w800 : FontWeight.w500,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            )
            .toList(),
      ),
    );
  }
}

class _NavData {
  const _NavData({required this.icon, required this.label, this.active = false});

  final IconData icon;
  final String label;
  final bool active;
}
