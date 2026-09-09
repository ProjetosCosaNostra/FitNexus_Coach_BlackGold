import 'package:flutter/material.dart';

const Color _black = Color(0xFF050505);
const Color _surface = Color(0xFF0F0F0F);
const Color _surface2 = Color(0xFF151515);
const Color _gold = Color(0xFFE4AA25);
const Color _goldSoft = Color(0xFFFFD261);
const Color _muted = Color(0xFFB8B8B8);
const Color _green = Color(0xFF20D37A);

class BlackGoldDesktopHome extends StatelessWidget {
  const BlackGoldDesktopHome({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _black,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(20, 18, 20, 28),
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 1480),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  const SizedBox(width: 205, child: _Sidebar()),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: const <Widget>[
                        _TopBar(),
                        SizedBox(height: 16),
                        _HeroRow(),
                        SizedBox(height: 14),
                        _ModuleRow(),
                        SizedBox(height: 14),
                        _AnalyticsRow(),
                      ],
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

class _Sidebar extends StatelessWidget {
  const _Sidebar();

  static const List<(IconData, String)> _items = <(IconData, String)>[
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
    return _Panel(
      padding: const EdgeInsets.fromLTRB(14, 18, 14, 14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          const _Brand(),
          const SizedBox(height: 20),
          ...List<Widget>.generate(_items.length, (int index) {
            final bool active = index == 0;
            final bool ecosystem = _items[index].$2 == 'Ecossistema';
            return Padding(
              padding: const EdgeInsets.only(bottom: 5),
              child: Material(
                color: active ? _goldSoft : Colors.transparent,
                borderRadius: BorderRadius.circular(10),
                child: InkWell(
                  borderRadius: BorderRadius.circular(10),
                  onTap: active
                      ? null
                      : () => Navigator.of(context).pushNamed(
                            ecosystem ? '/links' : '/start',
                          ),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 10,
                      vertical: 10,
                    ),
                    child: Row(
                      children: <Widget>[
                        Icon(
                          _items[index].$1,
                          size: 18,
                          color: active ? Colors.black : const Color(0xFFD0D0D0),
                        ),
                        const SizedBox(width: 9),
                        Expanded(
                          child: Text(
                            _items[index].$2,
                            style: TextStyle(
                              color: active ? Colors.black : const Color(0xFFD0D0D0),
                              fontSize: 11.3,
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
          const SizedBox(height: 10),
          const Divider(color: Color(0xFF2B2B2B)),
          const SizedBox(height: 8),
          InkWell(
            key: const ValueKey<String>('public-login-entry'),
            onTap: () => Navigator.of(context).pushNamed('/auth'),
            borderRadius: BorderRadius.circular(12),
            child: const Padding(
              padding: EdgeInsets.all(6),
              child: Row(
                children: <Widget>[
                  _Avatar(size: 36),
                  SizedBox(width: 9),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text(
                          'Felipe',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 11.5,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                        Text(
                          'Personal Trainer',
                          style: TextStyle(color: _muted, fontSize: 9),
                        ),
                      ],
                    ),
                  ),
                  Icon(Icons.chevron_right_rounded, color: _muted, size: 17),
                ],
              ),
            ),
          ),
        ],
      ),
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
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: const <Widget>[
          Text.rich(
            TextSpan(
              children: <InlineSpan>[
                TextSpan(text: 'FIT', style: TextStyle(color: Colors.white)),
                TextSpan(text: 'NEXUS', style: TextStyle(color: _goldSoft)),
              ],
            ),
            style: TextStyle(
              fontSize: 25,
              height: 1,
              fontWeight: FontWeight.w500,
              letterSpacing: .8,
            ),
          ),
          SizedBox(height: 5),
          Text(
            'COACH  BLACKGOLD',
            style: TextStyle(
              color: Colors.white,
              fontSize: 8,
              fontWeight: FontWeight.w600,
              letterSpacing: 2.1,
            ),
          ),
        ],
      ),
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
        gradient: LinearGradient(colors: <Color>[_goldSoft, Color(0xFF996300)]),
      ),
      child: Container(
        decoration: const BoxDecoration(shape: BoxShape.circle, color: Color(0xFF1A1A1A)),
        child: Icon(Icons.person_rounded, color: Colors.white, size: size * .55),
      ),
    );
  }
}

class _TopBar extends StatelessWidget {
  const _TopBar();

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 48,
      child: Row(
        children: <Widget>[
          Expanded(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14),
              decoration: BoxDecoration(
                color: _surface,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFF343434)),
              ),
              child: const Row(
                children: <Widget>[
                  Icon(Icons.search_rounded, color: _muted, size: 19),
                  SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Buscar alunos, treinos, alimentos...  (Ctrl + K)',
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(color: _muted, fontSize: 11.5),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(width: 10),
          OutlinedButton.icon(
            onPressed: () => Navigator.of(context).pushNamed('/links'),
            icon: const Icon(Icons.hub_outlined, size: 17),
            label: const Text('Ecossistema'),
            style: OutlinedButton.styleFrom(
              foregroundColor: _goldSoft,
              side: const BorderSide(color: _gold),
              padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 13),
              textStyle: const TextStyle(fontSize: 10.5, fontWeight: FontWeight.w800),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(11)),
            ),
          ),
          const SizedBox(width: 9),
          FilledButton(
            key: const ValueKey<String>('public-signup-entry'),
            onPressed: () => Navigator.of(context).pushNamed('/start'),
            style: FilledButton.styleFrom(
              backgroundColor: _goldSoft,
              foregroundColor: Colors.black,
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
              textStyle: const TextStyle(fontSize: 10.5, fontWeight: FontWeight.w900),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(11)),
            ),
            child: const Text('Criar conta'),
          ),
          const SizedBox(width: 10),
          const Icon(Icons.notifications_none_rounded, color: Color(0xFFD4D4D4), size: 21),
          const SizedBox(width: 10),
          const Icon(Icons.chat_bubble_outline_rounded, color: Color(0xFFD4D4D4), size: 19),
          const SizedBox(width: 10),
          const _Avatar(size: 38),
        ],
      ),
    );
  }
}

class _HeroRow extends StatelessWidget {
  const _HeroRow();

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 300,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: const <Widget>[
          Expanded(child: _Hero()),
          SizedBox(width: 13),
          SizedBox(width: 292, child: _Summary()),
        ],
      ),
    );
  }
}

class _Hero extends StatelessWidget {
  const _Hero();

  @override
  Widget build(BuildContext context) {
    return _Panel(
      clip: true,
      padding: EdgeInsets.zero,
      child: Stack(
        fit: StackFit.expand,
        children: <Widget>[
          Image.asset(
            'assets/images/professor_dashboard_hero.webp',
            fit: BoxFit.cover,
            alignment: Alignment.centerRight,
            errorBuilder: (_, __, ___) => const ColoredBox(color: _surface),
          ),
          const DecoratedBox(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.centerLeft,
                end: Alignment.centerRight,
                stops: <double>[0, .50, 1],
                colors: <Color>[Color(0xFF080808), Color(0xEA080808), Color(0x16080808)],
              ),
            ),
          ),
          Positioned(
            right: 25,
            top: 14,
            child: Text(
              'X',
              style: TextStyle(
                color: _goldSoft.withValues(alpha: .34),
                fontSize: 116,
                fontWeight: FontWeight.w200,
                shadows: const <Shadow>[Shadow(color: _gold, blurRadius: 25)],
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(28, 22, 20, 22),
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
                          TextSpan(text: 'sob controle.', style: TextStyle(color: _goldSoft)),
                        ],
                      ),
                      style: TextStyle(
                        fontSize: 34,
                        height: 1.02,
                        fontWeight: FontWeight.w900,
                        letterSpacing: -1,
                      ),
                    ),
                    const SizedBox(height: 11),
                    const Text(
                      'Alunos mais ativos, treinos entregues e resultados reais. Continue assim!',
                      style: TextStyle(color: Color(0xFFE0E0E0), fontSize: 12.3, height: 1.35),
                    ),
                    const SizedBox(height: 17),
                    Row(
                      children: <Widget>[
                        FilledButton.icon(
                          onPressed: () => Navigator.of(context).pushNamed('/start'),
                          icon: const Icon(Icons.play_arrow_rounded),
                          label: const Text('Começar treino'),
                          style: FilledButton.styleFrom(
                            backgroundColor: _goldSoft,
                            foregroundColor: Colors.black,
                            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                            textStyle: const TextStyle(fontSize: 11.5, fontWeight: FontWeight.w900),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                          ),
                        ),
                        const SizedBox(width: 9),
                        OutlinedButton.icon(
                          onPressed: () => Navigator.of(context).pushNamed('/start'),
                          icon: const Icon(Icons.add_rounded, size: 18),
                          label: const Text('Novo aluno'),
                          style: OutlinedButton.styleFrom(
                            foregroundColor: Colors.white,
                            side: const BorderSide(color: Color(0xFF777777)),
                            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 13),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
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

class _Summary extends StatelessWidget {
  const _Summary();

  @override
  Widget build(BuildContext context) {
    return const _Panel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text('Resumo da semana', style: TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w800)),
          SizedBox(height: 12),
          Row(
            children: <Widget>[
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text('5/6', style: TextStyle(color: Colors.white, fontSize: 28, fontWeight: FontWeight.w900)),
                    Text('treinos concluídos', style: TextStyle(color: _muted, fontSize: 9.5)),
                  ],
                ),
              ),
              _ProgressRing(),
            ],
          ),
          SizedBox(height: 12),
          Divider(color: Color(0xFF2B2B2B), height: 1),
          SizedBox(height: 10),
          _SummaryItem(Icons.local_fire_department_outlined, '2.450 kcal', 'ingestão média', '▲ 12%'),
          SizedBox(height: 9),
          _SummaryItem(Icons.monitor_weight_outlined, '78,4 kg', 'peso atual', '▼ 0,6 kg'),
          SizedBox(height: 9),
          _SummaryItem(Icons.spa_outlined, '72%', 'progresso geral', '▲ 8%'),
        ],
      ),
    );
  }
}

class _ProgressRing extends StatelessWidget {
  const _ProgressRing();

  @override
  Widget build(BuildContext context) {
    return const SizedBox(
      width: 62,
      height: 62,
      child: Stack(
        fit: StackFit.expand,
        children: <Widget>[
          CircularProgressIndicator(
            value: .83,
            strokeWidth: 7,
            backgroundColor: Color(0xFF2A2418),
            valueColor: AlwaysStoppedAnimation<Color>(_goldSoft),
          ),
          Center(
            child: Text('83%', style: TextStyle(color: _goldSoft, fontSize: 11, fontWeight: FontWeight.w900)),
          ),
        ],
      ),
    );
  }
}

class _SummaryItem extends StatelessWidget {
  const _SummaryItem(this.icon, this.value, this.caption, this.trend);

  final IconData icon;
  final String value;
  final String caption;
  final String trend;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: <Widget>[
        Icon(icon, color: _goldSoft, size: 19),
        const SizedBox(width: 8),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(value, style: const TextStyle(color: Colors.white, fontSize: 12.5, fontWeight: FontWeight.w800)),
              Text(caption, style: const TextStyle(color: _muted, fontSize: 8.8)),
            ],
          ),
        ),
        Text(trend, style: const TextStyle(color: _green, fontSize: 9, fontWeight: FontWeight.w800)),
      ],
    );
  }
}

class _ModuleRow extends StatelessWidget {
  const _ModuleRow();

  static const List<(IconData, String, String)> _modules = <(IconData, String, String)>[
    (Icons.people_alt_outlined, 'Alunos', '24 ativos'),
    (Icons.fitness_center_rounded, 'Treinos', 'Planos e templates'),
    (Icons.ramen_dining_outlined, 'Nutrição', 'Planos alimentares'),
    (Icons.calendar_month_outlined, 'Agenda', 'Compromissos e treinos'),
  ];

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 146,
      child: Row(
        children: List<Widget>.generate(_modules.length * 2 - 1, (int index) {
          if (index.isOdd) return const SizedBox(width: 11);
          final data = _modules[index ~/ 2];
          return Expanded(child: _Module(data: data));
        }),
      ),
    );
  }
}

class _Module extends StatelessWidget {
  const _Module({required this.data});

  final (IconData, String, String) data;

  @override
  Widget build(BuildContext context) {
    return _Panel(
      clip: true,
      padding: EdgeInsets.zero,
      child: InkWell(
        onTap: () => Navigator.of(context).pushNamed('/start'),
        child: Stack(
          fit: StackFit.expand,
          children: <Widget>[
            Opacity(
              opacity: .16,
              child: Image.asset(
                'assets/images/hero_bg.webp',
                fit: BoxFit.cover,
                errorBuilder: (_, __, ___) => const SizedBox.shrink(),
              ),
            ),
            const DecoratedBox(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: <Color>[Color(0x11000000), Color(0xF5090909)],
                ),
              ),
            ),
            Positioned(
              right: 4,
              top: 3,
              child: Icon(data.$1, size: 62, color: _goldSoft.withValues(alpha: .10)),
            ),
            Padding(
              padding: const EdgeInsets.all(14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Icon(data.$1, color: _goldSoft, size: 23),
                  const Spacer(),
                  Text(data.$2, style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w900)),
                  const SizedBox(height: 3),
                  Text(data.$3, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(color: _muted, fontSize: 9.5)),
                  const SizedBox(height: 5),
                  const Text('Acessar  →', style: TextStyle(color: _goldSoft, fontSize: 9, fontWeight: FontWeight.w700)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _AnalyticsRow extends StatelessWidget {
  const _AnalyticsRow();

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 262,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: const <Widget>[
          Expanded(flex: 5, child: _EvolutionPanel()),
          SizedBox(width: 11),
          Expanded(flex: 4, child: _DistributionPanel()),
          SizedBox(width: 11),
          Expanded(flex: 5, child: _ActionsPanel()),
        ],
      ),
    );
  }
}

class _EvolutionPanel extends StatelessWidget {
  const _EvolutionPanel();

  @override
  Widget build(BuildContext context) {
    const heights = <double>[.42, .55, .47, .66, .61, .75, .70, .84, .78, .91];
    return _Panel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const Row(
            children: <Widget>[
              Expanded(child: Text('Evolução dos alunos', style: TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w800))),
              Text('Últimos 30 dias', style: TextStyle(color: _muted, fontSize: 9)),
            ],
          ),
          const SizedBox(height: 15),
          const Row(
            children: <Widget>[
              _Legend(_goldSoft, 'Peso'),
              SizedBox(width: 12),
              _Legend(Color(0xFF4FAEFF), 'Treinos'),
              SizedBox(width: 12),
              _Legend(_green, 'Aderência'),
            ],
          ),
          const Spacer(),
          SizedBox(
            height: 116,
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: List<Widget>.generate(heights.length, (int index) {
                return Expanded(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 3),
                    child: FractionallySizedBox(
                      heightFactor: heights[index],
                      alignment: Alignment.bottomCenter,
                      child: Container(
                        decoration: BoxDecoration(
                          color: index.isEven ? _goldSoft : const Color(0xFF4FAEFF),
                          borderRadius: BorderRadius.circular(5),
                        ),
                      ),
                    ),
                  ),
                );
              }),
            ),
          ),
          const SizedBox(height: 9),
          const Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: <Widget>[
              Text('04/08', style: TextStyle(color: _muted, fontSize: 8.5)),
              Text('11/08', style: TextStyle(color: _muted, fontSize: 8.5)),
              Text('18/08', style: TextStyle(color: _muted, fontSize: 8.5)),
              Text('25/08', style: TextStyle(color: _muted, fontSize: 8.5)),
              Text('01/09', style: TextStyle(color: _muted, fontSize: 8.5)),
            ],
          ),
        ],
      ),
    );
  }
}

class _DistributionPanel extends StatelessWidget {
  const _DistributionPanel();

  @override
  Widget build(BuildContext context) {
    return const _Panel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text('Distribuição de treinos', style: TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w800)),
          Spacer(),
          Center(
            child: SizedBox(
              width: 116,
              height: 116,
              child: Stack(
                fit: StackFit.expand,
                children: <Widget>[
                  CircularProgressIndicator(
                    value: .72,
                    strokeWidth: 20,
                    backgroundColor: Color(0xFF1C3950),
                    valueColor: AlwaysStoppedAnimation<Color>(_goldSoft),
                  ),
                  Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: <Widget>[
                        Text('186', style: TextStyle(color: Colors.white, fontSize: 23, fontWeight: FontWeight.w900)),
                        Text('treinos', style: TextStyle(color: _muted, fontSize: 9)),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
          Spacer(),
          Wrap(
            spacing: 10,
            runSpacing: 5,
            children: <Widget>[
              _Legend(_goldSoft, 'Força 42%'),
              _Legend(Color(0xFF4FAEFF), 'Hipertrofia 30%'),
              _Legend(_green, 'Funcional 15%'),
            ],
          ),
        ],
      ),
    );
  }
}

class _Legend extends StatelessWidget {
  const _Legend(this.color, this.label);

  final Color color;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: <Widget>[
        Container(width: 7, height: 7, decoration: BoxDecoration(color: color, shape: BoxShape.circle)),
        const SizedBox(width: 4),
        Text(label, style: const TextStyle(color: _muted, fontSize: 8.8)),
      ],
    );
  }
}

class _ActionsPanel extends StatelessWidget {
  const _ActionsPanel();

  @override
  Widget build(BuildContext context) {
    return const _Panel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            children: <Widget>[
              Expanded(child: Text('Ações sugeridas (IA Coach)', style: TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w800))),
              CircleAvatar(radius: 10, backgroundColor: _goldSoft, child: Text('3', style: TextStyle(color: Colors.black, fontSize: 9, fontWeight: FontWeight.w900))),
            ],
          ),
          SizedBox(height: 13),
          _Action(Icons.hourglass_bottom_rounded, Color(0xFF8A7BFF), 'João está há 5 dias sem registrar treino', 'Sugerir nova prescrição'),
          SizedBox(height: 8),
          _Action(Icons.person_outline_rounded, _green, 'Ana evoluiu 12% na carga', 'Considerar ajuste de volume'),
          SizedBox(height: 8),
          _Action(Icons.warning_amber_rounded, Color(0xFFFF9E42), 'Lucas relatou fadiga alta', 'Revisar intensidade da semana'),
          Spacer(),
          Text('IA sugere. O profissional decide.', style: TextStyle(color: _goldSoft, fontSize: 9, fontWeight: FontWeight.w700)),
        ],
      ),
    );
  }
}

class _Action extends StatelessWidget {
  const _Action(this.icon, this.color, this.title, this.subtitle);

  final IconData icon;
  final Color color;
  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(9),
      decoration: BoxDecoration(
        color: _surface2,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: const Color(0xFF2D2D2D)),
      ),
      child: Row(
        children: <Widget>[
          Icon(icon, color: color, size: 18),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(title, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(color: Colors.white, fontSize: 9.8, fontWeight: FontWeight.w700)),
                const SizedBox(height: 2),
                Text(subtitle, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(color: _muted, fontSize: 8.7)),
              ],
            ),
          ),
          const Icon(Icons.chevron_right_rounded, color: _muted, size: 16),
        ],
      ),
    );
  }
}

class _Panel extends StatelessWidget {
  const _Panel({required this.child, this.padding = const EdgeInsets.all(15), this.clip = false});

  final Widget child;
  final EdgeInsetsGeometry padding;
  final bool clip;

  @override
  Widget build(BuildContext context) {
    return Container(
      clipBehavior: clip ? Clip.antiAlias : Clip.none,
      padding: padding,
      decoration: BoxDecoration(
        color: _surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF5C3F0E)),
        boxShadow: const <BoxShadow>[
          BoxShadow(color: Color(0x55000000), blurRadius: 16, offset: Offset(0, 7)),
        ],
      ),
      child: child,
    );
  }
}
