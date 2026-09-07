import 'package:flutter/material.dart';

const Color _canvasColor = Color(0xFF050505);
const Color surface = Color(0xFF0E0E0E);
const Color surfaceRaised = Color(0xFF151515);
const Color line = Color(0xFF5A3D0D);
const Color lineSoft = Color(0xFF2C2418);
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
            if (constraints.maxWidth >= 900) {
              return _DesktopHome(viewportHeight: constraints.maxHeight);
            }
            return const _MobileHome();
          },
        ),
      ),
    );
  }
}

class _MobileHome extends StatelessWidget {
  const _MobileHome();

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 520),
          child: const Padding(
            padding: EdgeInsets.fromLTRB(14, 14, 14, 22),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: <Widget>[
                _MobileTopBar(),
                SizedBox(height: 18),
                _GreetingRow(),
                SizedBox(height: 18),
                _MobileHero(),
                SizedBox(height: 14),
                _MetricsSection(),
                SizedBox(height: 14),
                _MobileModules(),
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
  }
}

class _MobileTopBar extends StatelessWidget {
  const _MobileTopBar();

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (BuildContext context, BoxConstraints constraints) {
        final bool compact = constraints.maxWidth < 400;
        return Row(
          children: <Widget>[
            const Expanded(child: _Brand(compact: true)),
            SizedBox(width: compact ? 6 : 9),
            OutlinedButton.icon(
              onPressed: () => Navigator.of(context).pushNamed('/links'),
              icon: Icon(Icons.hub_outlined, size: compact ? 15 : 17),
              label: const Text('Ecossistema'),
              style: OutlinedButton.styleFrom(
                foregroundColor: goldSoft,
                side: const BorderSide(color: gold, width: 1.1),
                padding: EdgeInsets.symmetric(
                  horizontal: compact ? 8 : 12,
                  vertical: 12,
                ),
                textStyle: TextStyle(
                  fontSize: compact ? 9.5 : 11,
                  fontWeight: FontWeight.w800,
                ),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
            ),
            SizedBox(width: compact ? 6 : 9),
            FilledButton(
              key: const ValueKey<String>('public-signup-entry'),
              onPressed: () => Navigator.of(context).pushNamed('/start'),
              style: FilledButton.styleFrom(
                backgroundColor: goldSoft,
                foregroundColor: Colors.black,
                padding: EdgeInsets.symmetric(
                  horizontal: compact ? 9 : 13,
                  vertical: 13,
                ),
                textStyle: TextStyle(
                  fontSize: compact ? 9.5 : 11,
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
  const _Brand({this.compact = false});

  final bool compact;

  @override
  Widget build(BuildContext context) {
    return FittedBox(
      fit: BoxFit.scaleDown,
      alignment: Alignment.centerLeft,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text.rich(
            const TextSpan(
              children: <InlineSpan>[
                TextSpan(text: 'FIT', style: TextStyle(color: Colors.white)),
                TextSpan(text: 'NEXUS', style: TextStyle(color: goldSoft)),
              ],
            ),
            style: TextStyle(
              fontSize: compact ? 25 : 27,
              fontWeight: FontWeight.w500,
              letterSpacing: 0.8,
              height: 1,
            ),
          ),
          const SizedBox(height: 5),
          Text(
            'COACH  BLACKGOLD',
            style: TextStyle(
              color: Colors.white,
              fontSize: compact ? 8.1 : 8.8,
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
                  _Avatar(size: 52),
                  SizedBox(width: 12),
                  Flexible(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text(
                          'Bom dia,',
                          style: TextStyle(color: muted, fontSize: 14, height: 1.1),
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
        const _StatusCard(compact: true),
      ],
    );
  }
}

class _Avatar extends StatelessWidget {
  const _Avatar({required this.size});

  final double size;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      padding: const EdgeInsets.all(2),
      decoration: const BoxDecoration(
        shape: BoxShape.circle,
        gradient: LinearGradient(colors: <Color>[goldSoft, Color(0xFF9C6500)]),
      ),
      child: Container(
        decoration: const BoxDecoration(color: Color(0xFF171717), shape: BoxShape.circle),
        child: Icon(Icons.person_rounded, color: const Color(0xFFE5E5E5), size: size * .56),
      ),
    );
  }
}

class _StatusCard extends StatelessWidget {
  const _StatusCard({this.compact = false});

  final bool compact;

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: BoxConstraints(minWidth: compact ? 112 : 150),
      padding: EdgeInsets.symmetric(
        horizontal: compact ? 12 : 15,
        vertical: compact ? 10 : 12,
      ),
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
                style: TextStyle(color: goldSoft, fontSize: 12, fontWeight: FontWeight.w800),
              ),
            ],
          ),
          SizedBox(height: 3),
          Text('Continue assim!', style: TextStyle(color: muted, fontSize: 10.5)),
        ],
      ),
    );
  }
}

class _MobileHero extends StatelessWidget {
  const _MobileHero();

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (BuildContext context, BoxConstraints constraints) {
        final bool narrow = constraints.maxWidth < 390;
        return Container(
          height: narrow ? 500 : 455,
          clipBehavior: Clip.antiAlias,
          decoration: _panelDecoration(radius: 20),
          child: Stack(
            fit: StackFit.expand,
            children: <Widget>[
              Image.asset(
                'assets/images/professor_dashboard_hero.webp',
                fit: BoxFit.cover,
                alignment: Alignment.centerRight,
                errorBuilder: (_, __, ___) => const ColoredBox(color: surface),
              ),
              const DecoratedBox(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.centerLeft,
                    end: Alignment.centerRight,
                    stops: <double>[0, .48, .78, 1],
                    colors: <Color>[
                      Color(0xFF070707),
                      Color(0xF2070707),
                      Color(0x66070707),
                      Color(0x11070707),
                    ],
                  ),
                ),
              ),
              Positioned(
                right: 18,
                top: 24,
                child: Text(
                  'X',
                  style: TextStyle(
                    color: goldSoft.withValues(alpha: .34),
                    fontSize: narrow ? 76 : 94,
                    fontWeight: FontWeight.w200,
                    shadows: const <Shadow>[Shadow(color: gold, blurRadius: 22)],
                  ),
                ),
              ),
              Padding(
                padding: EdgeInsets.fromLTRB(narrow ? 18 : 22, 24, 14, 20),
                child: Align(
                  alignment: Alignment.centerLeft,
                  child: FractionallySizedBox(
                    widthFactor: narrow ? .72 : .66,
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: <Widget>[
                        Text.rich(
                          const TextSpan(
                            children: <InlineSpan>[
                              TextSpan(text: 'Sua evolução\n', style: TextStyle(color: Colors.white)),
                              TextSpan(text: 'sob controle.', style: TextStyle(color: goldSoft)),
                            ],
                          ),
                          style: TextStyle(
                            fontSize: narrow ? 28 : 34,
                            height: 1.02,
                            fontWeight: FontWeight.w900,
                            letterSpacing: -1,
                          ),
                        ),
                        const SizedBox(height: 13),
                        Text(
                          'Treino, alimentação, progresso e acompanhamento em um só lugar para transformar sua rotina.',
                          style: TextStyle(
                            color: const Color(0xFFE0E0E0),
                            fontSize: narrow ? 11.8 : 13.4,
                            height: 1.42,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                        const SizedBox(height: 18),
                        _GoldPrimaryButton(
                          label: 'Começar treino',
                          icon: Icons.play_arrow_rounded,
                          onPressed: () => Navigator.of(context).pushNamed('/start'),
                        ),
                        const SizedBox(height: 9),
                        _OutlineAction(
                          label: 'Plano alimentar',
                          icon: Icons.restaurant_menu_rounded,
                          onPressed: () => Navigator.of(context).pushNamed('/start'),
                        ),
                        const SizedBox(height: 9),
                        _OutlineAction(
                          label: 'Falar com coach',
                          icon: Icons.chat_bubble_outline_rounded,
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

class _GoldPrimaryButton extends StatelessWidget {
  const _GoldPrimaryButton({required this.label, required this.icon, required this.onPressed});

  final String label;
  final IconData icon;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return FilledButton.icon(
      onPressed: onPressed,
      icon: Icon(icon),
      label: Text(label),
      style: FilledButton.styleFrom(
        backgroundColor: goldSoft,
        foregroundColor: Colors.black,
        minimumSize: const Size(0, 50),
        textStyle: const TextStyle(fontWeight: FontWeight.w900, fontSize: 14),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    );
  }
}

class _OutlineAction extends StatelessWidget {
  const _OutlineAction({required this.label, required this.icon, required this.onPressed});

  final String label;
  final IconData icon;
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

const List<_MetricData> _metrics = <_MetricData>[
  _MetricData(
    icon: Icons.fitness_center_rounded,
    label: 'Treinos da semana',
    value: '5/6',
    detail: '83%',
    progress: .83,
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

class _MetricsSection extends StatelessWidget {
  const _MetricsSection();

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (BuildContext context, BoxConstraints constraints) {
        final int columns = constraints.maxWidth >= 350 ? 4 : 2;
        const double gap = 9;
        final double width = (constraints.maxWidth - gap * (columns - 1)) / columns;
        return Wrap(
          spacing: gap,
          runSpacing: gap,
          children: _metrics
              .map((item) => SizedBox(width: width, child: _MetricCard(data: item)))
              .toList(),
        );
      },
    );
  }
}

class _MetricCard extends StatelessWidget {
  const _MetricCard({required this.data});

  final _MetricData data;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 126,
      padding: const EdgeInsets.all(11),
      decoration: _panelDecoration(radius: 15),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            children: <Widget>[
              Icon(data.icon, color: goldSoft, size: 18),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  data.label,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(color: Color(0xFFD8D8D8), fontSize: 10, height: 1.1),
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
                    fontSize: 24,
                    fontWeight: FontWeight.w900,
                    height: 1,
                  ),
                ),
                if (data.unit != null) ...<Widget>[
                  const SizedBox(width: 4),
                  Text(data.unit!, style: const TextStyle(color: muted, fontSize: 9.5)),
                ],
              ],
            ),
          ),
          const SizedBox(height: 6),
          if (data.progress != null) ...<Widget>[
            ClipRRect(
              borderRadius: BorderRadius.circular(99),
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
              fontSize: 9.8,
              fontWeight: FontWeight.w800,
            ),
          ),
        ],
      ),
    );
  }
}

class _ModuleData {
  const _ModuleData(this.icon, this.title, this.subtitle, this.alignment);

  final IconData icon;
  final String title;
  final String subtitle;
  final Alignment alignment;
}

const List<_ModuleData> _modules = <_ModuleData>[
  _ModuleData(Icons.fitness_center_rounded, 'Treinos', 'Planos personalizados', Alignment.centerLeft),
  _ModuleData(Icons.ramen_dining_outlined, 'Nutrição', 'Alimentação inteligente', Alignment.center),
  _ModuleData(Icons.calendar_month_outlined, 'Agenda', 'Compromissos e treinos', Alignment.centerRight),
  _ModuleData(Icons.bar_chart_rounded, 'Resultados', 'Acompanhe sua evolução', Alignment.bottomLeft),
  _ModuleData(Icons.spa_outlined, 'Hábitos', 'Constância que transforma', Alignment.bottomCenter),
  _ModuleData(Icons.groups_2_outlined, 'Comunidade', 'Conecte-se e evolua', Alignment.bottomRight),
];

class _MobileModules extends StatelessWidget {
  const _MobileModules();

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (BuildContext context, BoxConstraints constraints) {
        final int columns = constraints.maxWidth < 330 ? 2 : 3;
        const double gap = 10;
        final double width = (constraints.maxWidth - gap * (columns - 1)) / columns;
        return Wrap(
          spacing: gap,
          runSpacing: gap,
          children: _modules
              .map((item) => SizedBox(width: width, height: 128, child: _ModuleCard(data: item)))
              .toList(),
        );
      },
    );
  }
}

class _ModuleCard extends StatelessWidget {
  const _ModuleCard({required this.data, this.desktop = false});

  final _ModuleData data;
  final bool desktop;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: surface,
      borderRadius: BorderRadius.circular(16),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: () => Navigator.of(context).pushNamed('/start'),
        child: Ink(
          decoration: _panelDecoration(radius: 16),
          child: Stack(
            fit: StackFit.expand,
            children: <Widget>[
              Opacity(
                opacity: desktop ? .20 : .14,
                child: Image.asset(
                  'assets/images/hero_bg.webp',
                  fit: BoxFit.cover,
                  alignment: data.alignment,
                  errorBuilder: (_, __, ___) => const SizedBox.shrink(),
                ),
              ),
              const DecoratedBox(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: <Color>[Color(0x11000000), Color(0xF2090909)],
                  ),
                ),
              ),
              Positioned(
                right: 5,
                top: 5,
                child: Icon(
                  data.icon,
                  size: desktop ? 62 : 54,
                  color: goldSoft.withValues(alpha: .10),
                ),
              ),
              Padding(
                padding: EdgeInsets.all(desktop ? 15 : 12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: <Widget>[
                    Icon(data.icon, color: goldSoft, size: desktop ? 24 : 22),
                    const Spacer(),
                    Text(
                      data.title,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: desktop ? 15 : 13.5,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      data.subtitle,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(color: muted, fontSize: desktop ? 10.5 : 9.5, height: 1.15),
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
      decoration: _panelDecoration(radius: 18),
      child: Column(
        children: <Widget>[
          const Row(
            children: <Widget>[
              Icon(Icons.multiline_chart_rounded, color: goldSoft, size: 20),
              SizedBox(width: 9),
              Expanded(
                child: Text(
                  'Seu progresso semanal',
                  style: TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w800),
                ),
              ),
              Text('Ver detalhes', style: TextStyle(color: muted, fontSize: 10.5)),
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
          child: done ? const Icon(Icons.check_rounded, color: goldSoft, size: 19) : null,
        ),
        const SizedBox(height: 6),
        Text(day, style: const TextStyle(color: muted, fontSize: 9.5)),
      ],
    );
  }
}

class _BottomNavigation extends StatelessWidget {
  const _BottomNavigation();

  @override
  Widget build(BuildContext context) {
    const items = <(IconData, String)>[
      (Icons.home_rounded, 'Início'),
      (Icons.fitness_center_rounded, 'Treinos'),
      (Icons.assignment_turned_in_outlined, 'Plano'),
      (Icons.stacked_line_chart_rounded, 'Progresso'),
      (Icons.grid_view_rounded, 'Mais'),
    ];
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
        children: List<Widget>.generate(items.length, (int index) {
          final bool active = index == 0;
          return Expanded(
            child: InkWell(
              onTap: active ? null : () => Navigator.of(context).pushNamed('/start'),
              borderRadius: BorderRadius.circular(12),
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: <Widget>[
                    Icon(items[index].$1, size: 22, color: active ? goldSoft : const Color(0xFFB0B0B0)),
                    const SizedBox(height: 4),
                    FittedBox(
                      child: Text(
                        items[index].$2,
                        style: TextStyle(
                          color: active ? goldSoft : const Color(0xFFB0B0B0),
                          fontSize: 9.5,
                          fontWeight: active ? FontWeight.w800 : FontWeight.w500,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          );
        }),
      ),
    );
  }
}

class _DesktopHome extends StatelessWidget {
  const _DesktopHome({required this.viewportHeight});

  final double viewportHeight;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 1480),
          child: Padding(
            padding: const EdgeInsets.fromLTRB(22, 20, 22, 28),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                const SizedBox(width: 196, child: _DesktopSidebar()),
                const SizedBox(width: 18),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: <Widget>[
                      const _DesktopTopBar(),
                      const SizedBox(height: 18),
                      const _DesktopHeroAndSummary(),
                      const SizedBox(height: 14),
                      const _DesktopModuleGrid(),
                      const SizedBox(height: 14),
                      const _DesktopAnalytics(),
                      SizedBox(height: viewportHeight > 900 ? 16 : 8),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _DesktopSidebar extends StatelessWidget {
  const _DesktopSidebar();

  static const List<(IconData, String)> _nav = <(IconData, String)>[
    (Icons.home_rounded, 'Início'),
    (Icons.people_alt_outlined, 'Alunos'),
    (Icons.fitness_center_rounded, 'Treinos'),
    (Icons.ramen_dining_outlined, 'Nutrição'),
    (Icons.calendar_month_outlined, 'Agenda'),
    (Icons.trending_up_rounded, 'Progressos'),
    (Icons.groups_2_outlined, 'Comunidade'),
    (Icons.analytics_outlined, 'Relatórios'),
    (Icons.hub_outlined, 'Ecossistema'),
    (Icons.psychology_alt_outlined, 'IA Coach'),
    (Icons.settings_outlined, 'Configurações'),
  ];

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(14, 18, 14, 16),
      decoration: _panelDecoration(radius: 18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          const Padding(padding: EdgeInsets.symmetric(horizontal: 8), child: _Brand()),
          const SizedBox(height: 22),
          ...List<Widget>.generate(_nav.length, (int index) {
            final bool active = index == 0;
            final bool ecosystem = _nav[index].$2 == 'Ecossistema';
            return Padding(
              padding: const EdgeInsets.only(bottom: 5),
              child: Material(
                color: active ? goldSoft : Colors.transparent,
                borderRadius: BorderRadius.circular(10),
                child: InkWell(
                  onTap: () {
                    if (ecosystem) {
                      Navigator.of(context).pushNamed('/links');
                    } else if (!active) {
                      Navigator.of(context).pushNamed('/start');
                    }
                  },
                  borderRadius: BorderRadius.circular(10),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 10),
                    child: Row(
                      children: <Widget>[
                        Icon(_nav[index].$1, size: 18, color: active ? Colors.black : const Color(0xFFD2D2D2)),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            _nav[index].$2,
                            style: TextStyle(
                              color: active ? Colors.black : const Color(0xFFD2D2D2),
                              fontSize: 11.5,
                              fontWeight: active ? FontWeight.w900 : FontWeight.w600,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            );
          }),
          const SizedBox(height: 18),
          const Divider(color: Color(0xFF292929)),
          const SizedBox(height: 12),
          InkWell(
            key: const ValueKey<String>('public-login-entry'),
            onTap: () => Navigator.of(context).pushNamed('/auth'),
            borderRadius: BorderRadius.circular(12),
            child: const Padding(
              padding: EdgeInsets.all(7),
              child: Row(
                children: <Widget>[
                  _Avatar(size: 38),
                  SizedBox(width: 9),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text('Felipe', style: TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w800)),
                        Text('Personal Trainer', style: TextStyle(color: muted, fontSize: 9.5)),
                      ],
                    ),
                  ),
                  Icon(Icons.chevron_right_rounded, color: muted, size: 18),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _DesktopTopBar extends StatelessWidget {
  const _DesktopTopBar();

  @override
  Widget build(BuildContext context) {
    return Row(
      children: <Widget>[
        Expanded(
          child: Container(
            height: 46,
            padding: const EdgeInsets.symmetric(horizontal: 14),
            decoration: BoxDecoration(
              color: surface,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: const Color(0xFF333333)),
            ),
            child: const Row(
              children: <Widget>[
                Icon(Icons.search_rounded, color: muted, size: 20),
                SizedBox(width: 9),
                Expanded(
                  child: Text(
                    'Buscar alunos, treinos, alimentos...  (Ctrl + K)',
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(color: muted, fontSize: 11.5),
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(width: 12),
        OutlinedButton.icon(
          onPressed: () => Navigator.of(context).pushNamed('/links'),
          icon: const Icon(Icons.hub_outlined, size: 17),
          label: const Text('Ecossistema'),
          style: OutlinedButton.styleFrom(
            foregroundColor: goldSoft,
            side: const BorderSide(color: gold),
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 13),
            textStyle: const TextStyle(fontSize: 11, fontWeight: FontWeight.w800),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(11)),
          ),
        ),
        const SizedBox(width: 10),
        FilledButton(
          key: const ValueKey<String>('public-signup-entry'),
          onPressed: () => Navigator.of(context).pushNamed('/start'),
          style: FilledButton.styleFrom(
            backgroundColor: goldSoft,
            foregroundColor: Colors.black,
            padding: const EdgeInsets.symmetric(horizontal: 15, vertical: 14),
            textStyle: const TextStyle(fontSize: 11, fontWeight: FontWeight.w900),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(11)),
          ),
          child: const Text('Criar conta'),
        ),
        const SizedBox(width: 12),
        const _TopIcon(icon: Icons.notifications_none_rounded),
        const SizedBox(width: 7),
        const _TopIcon(icon: Icons.chat_bubble_outline_rounded),
        const SizedBox(width: 9),
        const _Avatar(size: 38),
      ],
    );
  }
}

class _TopIcon extends StatelessWidget {
  const _TopIcon({required this.icon});

  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 38,
      height: 38,
      decoration: BoxDecoration(
        color: surface,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: const Color(0xFF303030)),
      ),
      child: Icon(icon, color: const Color(0xFFD4D4D4), size: 19),
    );
  }
}

class _DesktopHeroAndSummary extends StatelessWidget {
  const _DesktopHeroAndSummary();

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (BuildContext context, BoxConstraints constraints) {
        if (constraints.maxWidth < 820) {
          return const Column(
            children: <Widget>[
              _DesktopHero(),
              SizedBox(height: 12),
              _DesktopSummary(),
            ],
          );
        }
        return const Row(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            Expanded(child: _DesktopHero()),
            SizedBox(width: 14),
            SizedBox(width: 290, child: _DesktopSummary()),
          ],
        );
      },
    );
  }
}

class _DesktopHero extends StatelessWidget {
  const _DesktopHero();

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 300,
      clipBehavior: Clip.antiAlias,
      decoration: _panelDecoration(radius: 18),
      child: Stack(
        fit: StackFit.expand,
        children: <Widget>[
          Image.asset(
            'assets/images/professor_dashboard_hero.webp',
            fit: BoxFit.cover,
            alignment: Alignment.centerRight,
            errorBuilder: (_, __, ___) => const ColoredBox(color: surface),
          ),
          const DecoratedBox(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.centerLeft,
                end: Alignment.centerRight,
                colors: <Color>[Color(0xFF080808), Color(0xE6080808), Color(0x22080808)],
                stops: <double>[0, .50, 1],
              ),
            ),
          ),
          Positioned(
            right: 28,
            top: 24,
            child: Text(
              'X',
              style: TextStyle(
                color: goldSoft.withValues(alpha: .38),
                fontSize: 118,
                fontWeight: FontWeight.w200,
                shadows: const <Shadow>[Shadow(color: gold, blurRadius: 28)],
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(28, 24, 22, 24),
            child: Align(
              alignment: Alignment.centerLeft,
              child: FractionallySizedBox(
                widthFactor: .58,
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    const Text.rich(
                      TextSpan(
                        children: <InlineSpan>[
                          TextSpan(text: 'Sua evolução\n', style: TextStyle(color: Colors.white)),
                          TextSpan(text: 'sob controle.', style: TextStyle(color: goldSoft)),
                        ],
                      ),
                      style: TextStyle(fontSize: 34, height: 1.02, fontWeight: FontWeight.w900, letterSpacing: -1),
                    ),
                    const SizedBox(height: 12),
                    const Text(
                      'Alunos mais ativos, treinos entregues e resultados reais. Continue assim!',
                      style: TextStyle(color: Color(0xFFE0E0E0), fontSize: 12.5, height: 1.35),
                    ),
                    const SizedBox(height: 18),
                    Row(
                      children: <Widget>[
                        SizedBox(
                          width: 156,
                          child: _GoldPrimaryButton(
                            label: 'Começar treino',
                            icon: Icons.play_arrow_rounded,
                            onPressed: () => Navigator.of(context).pushNamed('/start'),
                          ),
                        ),
                        const SizedBox(width: 10),
                        OutlinedButton.icon(
                          onPressed: () => Navigator.of(context).pushNamed('/start'),
                          icon: const Icon(Icons.add_rounded, size: 18),
                          label: const Text('Novo aluno'),
                          style: OutlinedButton.styleFrom(
                            foregroundColor: Colors.white,
                            side: const BorderSide(color: Color(0xFF777777)),
                            padding: const EdgeInsets.symmetric(horizontal: 15, vertical: 14),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(11)),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _DesktopSummary extends StatelessWidget {
  const _DesktopSummary();

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 300,
      padding: const EdgeInsets.all(16),
      decoration: _panelDecoration(radius: 18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const Text('Resumo da semana', style: TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w800)),
          const SizedBox(height: 14),
          Row(
            children: <Widget>[
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text('5/6', style: TextStyle(color: Colors.white, fontSize: 28, fontWeight: FontWeight.w900)),
                    Text('treinos concluídos', style: TextStyle(color: muted, fontSize: 10.5)),
                  ],
                ),
              ),
              SizedBox(
                width: 66,
                height: 66,
                child: Stack(
                  fit: StackFit.expand,
                  children: <Widget>[
                    CircularProgressIndicator(
                      value: .83,
                      strokeWidth: 7,
                      backgroundColor: Color(0xFF2A2418),
                      valueColor: AlwaysStoppedAnimation<Color>(goldSoft),
                    ),
                    Center(child: Text('83%', style: TextStyle(color: goldSoft, fontSize: 12, fontWeight: FontWeight.w900))),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          const Divider(color: Color(0xFF2A2A2A), height: 1),
          const SizedBox(height: 10),
          const _SummaryLine(icon: Icons.local_fire_department_outlined, value: '2.450 kcal', label: 'ingestão média', trend: '▲ 12%'),
          const SizedBox(height: 9),
          const _SummaryLine(icon: Icons.monitor_weight_outlined, value: '78,4 kg', label: 'peso atual', trend: '▼ 0,6 kg'),
          const SizedBox(height: 9),
          const _SummaryLine(icon: Icons.spa_outlined, value: '72%', label: 'progresso geral', trend: '▲ 8%'),
        ],
      ),
    );
  }
}

class _SummaryLine extends StatelessWidget {
  const _SummaryLine({required this.icon, required this.value, required this.label, required this.trend});

  final IconData icon;
  final String value;
  final String label;
  final String trend;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: <Widget>[
        Icon(icon, color: goldSoft, size: 19),
        const SizedBox(width: 9),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(value, style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.w800)),
              Text(label, style: const TextStyle(color: muted, fontSize: 9.5)),
            ],
          ),
        ),
        Text(trend, style: const TextStyle(color: success, fontSize: 9.5, fontWeight: FontWeight.w800)),
      ],
    );
  }
}

class _DesktopModuleGrid extends StatelessWidget {
  const _DesktopModuleGrid();

  @override
  Widget build(BuildContext context) {
    const desktopModules = <_ModuleData>[
      _ModuleData(Icons.people_alt_outlined, 'Alunos', '24 ativos', Alignment.centerLeft),
      _ModuleData(Icons.fitness_center_rounded, 'Treinos', 'Planos e templates', Alignment.centerLeft),
      _ModuleData(Icons.ramen_dining_outlined, 'Nutrição', 'Planos alimentares', Alignment.center),
      _ModuleData(Icons.calendar_month_outlined, 'Agenda', 'Compromissos e treinos', Alignment.centerRight),
    ];
    return LayoutBuilder(
      builder: (BuildContext context, BoxConstraints constraints) {
        final int columns = constraints.maxWidth >= 760 ? 4 : 2;
        const double gap = 12;
        final double width = (constraints.maxWidth - gap * (columns - 1)) / columns;
        return Wrap(
          spacing: gap,
          runSpacing: gap,
          children: desktopModules
              .map((item) => SizedBox(width: width, height: 150, child: _ModuleCard(data: item, desktop: true)))
              .toList(),
        );
      },
    );
  }
}

class _DesktopAnalytics extends StatelessWidget {
  const _DesktopAnalytics();

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (BuildContext context, BoxConstraints constraints) {
        final widgets = <Widget>[
          const _TrendPanel(),
          const _DistributionPanel(),
          const _ActionsPanel(),
        ];
        if (constraints.maxWidth >= 930) {
          return Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Expanded(flex: 5, child: widgets[0]),
              const SizedBox(width: 12),
              Expanded(flex: 4, child: widgets[1]),
              const SizedBox(width: 12),
              Expanded(flex: 5, child: widgets[2]),
            ],
          );
        }
        return Column(
          children: <Widget>[
            widgets[0],
            const SizedBox(height: 12),
            widgets[1],
            const SizedBox(height: 12),
            widgets[2],
          ],
        );
      },
    );
  }
}

class _TrendPanel extends StatelessWidget {
  const _TrendPanel();

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 260,
      padding: const EdgeInsets.all(16),
      decoration: _panelDecoration(radius: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const Row(
            children: <Widget>[
              Expanded(child: Text('Evolução dos alunos', style: TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w800))),
              Text('Últimos 30 dias', style: TextStyle(color: muted, fontSize: 9.5)),
            ],
          ),
          const SizedBox(height: 12),
          const Row(
            children: <Widget>[
              _LegendDot(color: goldSoft, label: 'Peso'),
              SizedBox(width: 12),
              _LegendDot(color: Color(0xFF44A9FF), label: 'Treinos'),
              SizedBox(width: 12),
              _LegendDot(color: success, label: 'Aderência'),
            ],
          ),
          const SizedBox(height: 14),
          const Expanded(child: CustomPaint(painter: _TrendPainter(), child: SizedBox.expand())),
          const SizedBox(height: 6),
          const Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: <Widget>[
              Text('04/08', style: TextStyle(color: muted, fontSize: 9)),
              Text('11/08', style: TextStyle(color: muted, fontSize: 9)),
              Text('18/08', style: TextStyle(color: muted, fontSize: 9)),
              Text('25/08', style: TextStyle(color: muted, fontSize: 9)),
              Text('01/09', style: TextStyle(color: muted, fontSize: 9)),
            ],
          ),
        ],
      ),
    );
  }
}

class _LegendDot extends StatelessWidget {
  const _LegendDot({required this.color, required this.label});

  final Color color;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: <Widget>[
        Container(width: 7, height: 7, decoration: BoxDecoration(color: color, shape: BoxShape.circle)),
        const SizedBox(width: 5),
        Text(label, style: const TextStyle(color: muted, fontSize: 9)),
      ],
    );
  }
}

class _TrendPainter extends CustomPainter {
  const _TrendPainter();

  @override
  void paint(Canvas canvas, Size size) {
    final grid = Paint()..color = const Color(0xFF262626)..strokeWidth = 1;
    for (int i = 1; i < 4; i++) {
      final y = size.height * i / 4;
      canvas.drawLine(Offset(0, y), Offset(size.width, y), grid);
    }
    final goldPaint = Paint()..color = goldSoft..strokeWidth = 2.2..style = PaintingStyle.stroke;
    final bluePaint = Paint()..color = const Color(0xFF44A9FF)..strokeWidth = 2.0..style = PaintingStyle.stroke;
    final greenPaint = Paint()..color = success..strokeWidth = 1.8..style = PaintingStyle.stroke;
    final goldPath = Path();
    final bluePath = Path();
    final greenPath = Path();
    const goldValues = <double>[.69, .61, .67, .54, .49, .43, .48, .36, .31];
    const blueValues = <double>[.83, .78, .72, .68, .60, .55, .48, .44, .39];
    const greenValues = <double>[.76, .74, .69, .65, .61, .57, .52, .49, .43];
    for (int i = 0; i < goldValues.length; i++) {
      final x = size.width * i / (goldValues.length - 1);
      final pg = Offset(x, size.height * goldValues[i]);
      final pb = Offset(x, size.height * blueValues[i]);
      final pr = Offset(x, size.height * greenValues[i]);
      if (i == 0) {
        goldPath.moveTo(pg.dx, pg.dy);
        bluePath.moveTo(pb.dx, pb.dy);
        greenPath.moveTo(pr.dx, pr.dy);
      } else {
        goldPath.lineTo(pg.dx, pg.dy);
        bluePath.lineTo(pb.dx, pb.dy);
        greenPath.lineTo(pr.dx, pr.dy);
      }
    }
    canvas.drawPath(goldPath, goldPaint);
    canvas.drawPath(bluePath, bluePaint);
    canvas.drawPath(greenPath, greenPaint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _DistributionPanel extends StatelessWidget {
  const _DistributionPanel();

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 260,
      padding: const EdgeInsets.all(16),
      decoration: _panelDecoration(radius: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const Text('Distribuição de treinos', style: TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w800)),
          const SizedBox(height: 18),
          Expanded(
            child: Row(
              children: <Widget>[
                const Expanded(
                  child: Center(
                    child: SizedBox(
                      width: 132,
                      height: 132,
                      child: CustomPaint(
                        painter: _DonutPainter(),
                        child: Center(
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            children: <Widget>[
                              Text('186', style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.w900)),
                              Text('treinos', style: TextStyle(color: muted, fontSize: 9.5)),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                const Expanded(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      _LegendDot(color: goldSoft, label: 'Força 42%'),
                      SizedBox(height: 8),
                      _LegendDot(color: Color(0xFF44A9FF), label: 'Hipertrofia 30%'),
                      SizedBox(height: 8),
                      _LegendDot(color: success, label: 'Funcional 15%'),
                      SizedBox(height: 8),
                      _LegendDot(color: Color(0xFF9A77FF), label: 'Mobilidade 8%'),
                      SizedBox(height: 8),
                      _LegendDot(color: Color(0xFF777777), label: 'Outros 5%'),
                    ],
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

class _DonutPainter extends CustomPainter {
  const _DonutPainter();

  @override
  void paint(Canvas canvas, Size size) {
    final rect = Offset.zero & size;
    const segments = <(double, Color)>[
      (.42, goldSoft),
      (.30, Color(0xFF44A9FF)),
      (.15, success),
      (.08, Color(0xFF9A77FF)),
      (.05, Color(0xFF777777)),
    ];
    double start = -1.5708;
    for (final segment in segments) {
      final sweep = 6.28318 * segment.$1;
      canvas.drawArc(
        rect.deflate(14),
        start,
        sweep - .025,
        false,
        Paint()..color = segment.$2..style = PaintingStyle.stroke..strokeWidth = 18,
      );
      start += sweep;
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _ActionsPanel extends StatelessWidget {
  const _ActionsPanel();

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 260,
      padding: const EdgeInsets.all(16),
      decoration: _panelDecoration(radius: 16),
      child: const Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            children: <Widget>[
              Expanded(child: Text('Ações sugeridas (IA Coach)', style: TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w800))),
              CircleAvatar(radius: 11, backgroundColor: goldSoft, child: Text('3', style: TextStyle(color: Colors.black, fontSize: 10, fontWeight: FontWeight.w900))),
            ],
          ),
          SizedBox(height: 13),
          _ActionRow(icon: Icons.hourglass_bottom_rounded, color: Color(0xFF8B7CFF), title: 'João está há 5 dias sem registrar treino', subtitle: 'Sugerir nova prescrição'),
          SizedBox(height: 8),
          _ActionRow(icon: Icons.person_outline_rounded, color: success, title: 'Ana evoluiu 12% na carga', subtitle: 'Considerar ajuste de volume'),
          SizedBox(height: 8),
          _ActionRow(icon: Icons.warning_amber_rounded, color: Color(0xFFFF9E42), title: 'Lucas relatou fadiga alta', subtitle: 'Revisar intensidade da semana'),
          Spacer(),
          Text('IA sugere. O profissional decide.', style: TextStyle(color: goldSoft, fontSize: 9.5, fontWeight: FontWeight.w700)),
        ],
      ),
    );
  }
}

class _ActionRow extends StatelessWidget {
  const _ActionRow({required this.icon, required this.color, required this.title, required this.subtitle});

  final IconData icon;
  final Color color;
  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: const Color(0xFF121212),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: const Color(0xFF2A2A2A)),
      ),
      child: Row(
        children: <Widget>[
          Icon(icon, color: color, size: 19),
          const SizedBox(width: 9),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(title, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(color: Colors.white, fontSize: 10.2, fontWeight: FontWeight.w700)),
                const SizedBox(height: 2),
                Text(subtitle, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(color: muted, fontSize: 9)),
              ],
            ),
          ),
          const Icon(Icons.chevron_right_rounded, color: muted, size: 17),
        ],
      ),
    );
  }
}

BoxDecoration _panelDecoration({required double radius}) {
  return BoxDecoration(
    color: surface,
    borderRadius: BorderRadius.circular(radius),
    border: Border.all(color: line, width: 1),
    boxShadow: const <BoxShadow>[
      BoxShadow(color: Color(0x55000000), blurRadius: 18, offset: Offset(0, 8)),
    ],
  );
}
