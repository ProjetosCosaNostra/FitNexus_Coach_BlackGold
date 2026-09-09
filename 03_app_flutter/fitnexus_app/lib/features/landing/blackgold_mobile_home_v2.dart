import 'package:flutter/material.dart';

const Color _bg = Color(0xFF050505);
const Color _panel = Color(0xFF0B0B0B);
const Color _gold = Color(0xFFF2C94C);
const Color _gold2 = Color(0xFFFFD45B);
const Color _muted = Color(0xFFB9B9B9);
const Color _line = Color(0xFF5B4310);
const Color _green = Color(0xFF3DDC84);

class LandingPage extends StatelessWidget {
  const LandingPage({super.key});

  static const Color canvas = _bg;

  @override
  Widget build(BuildContext context) {
    return MediaQuery(
      data: MediaQuery.of(context).copyWith(textScaler: TextScaler.noScaling),
      child: Scaffold(
        backgroundColor: _bg,
        body: SafeArea(
          bottom: false,
          child: LayoutBuilder(
            builder: (context, constraints) {
              final widthScale = (constraints.maxWidth / 390).clamp(.86, 1.08);
              return Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 430),
                  child: SingleChildScrollView(
                    padding: EdgeInsets.fromLTRB(
                      14 * widthScale,
                      8 * widthScale,
                      14 * widthScale,
                      18 * widthScale,
                    ),
                    child: Column(
                      children: [
                        _header(context, widthScale),
                        _gap(widthScale, 7),
                        _identity(context, widthScale),
                        _gap(widthScale, 3),
                        _hero(context, widthScale),
                        _gap(widthScale, 7),
                        _stats(widthScale),
                        _gap(widthScale, 7),
                        _modules(context, widthScale),
                        _gap(widthScale, 7),
                        _progress(widthScale),
                      ],
                    ),
                  ),
                ),
              );
            },
          ),
        ),
        bottomNavigationBar: LayoutBuilder(
          builder: (context, constraints) {
            final u = (constraints.maxWidth / 390).clamp(.86, 1.08);
            return _nav(context, u);
          },
        ),
      ),
    );
  }

  Widget _gap(double u, double h) => SizedBox(height: h * u);

  Widget _header(BuildContext context, double u) {
    return SizedBox(
      height: 48 * u,
      child: Row(
        children: [
          Expanded(child: _brand(u)),
          _topButton(
            context,
            u,
            width: 91,
            text: 'Ecossistema',
            icon: Icons.hub_outlined,
            route: '/links',
          ),
          SizedBox(width: 6 * u),
          _topButton(
            context,
            u,
            width: 72,
            text: 'Criar conta',
            route: '/start',
            filled: true,
            key: const ValueKey<String>('public-signup-entry'),
          ),
        ],
      ),
    );
  }

  Widget _brand(double u) {
    return Align(
      alignment: Alignment.centerLeft,
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text.rich(
            const TextSpan(
              children: [
                TextSpan(
                  text: 'FIT',
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                TextSpan(
                  text: 'NEXUS',
                  style: TextStyle(
                    color: _gold2,
                    fontWeight: FontWeight.w400,
                  ),
                ),
              ],
            ),
            maxLines: 1,
            style: TextStyle(
              fontSize: 22 * u,
              letterSpacing: 1.5,
              height: .95,
            ),
          ),
          SizedBox(height: 5 * u),
          Text(
            'COACH  BLACKGOLD',
            maxLines: 1,
            style: TextStyle(
              color: Colors.white,
              fontSize: 7.2 * u,
              letterSpacing: 2.6,
              fontWeight: FontWeight.w600,
              height: 1,
            ),
          ),
        ],
      ),
    );
  }

  Widget _topButton(
    BuildContext context,
    double u, {
    required double width,
    required String text,
    required String route,
    IconData? icon,
    bool filled = false,
    Key? key,
  }) {
    return SizedBox(
      key: key,
      width: width * u,
      height: 35 * u,
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(9 * u),
        child: InkWell(
          onTap: () => Navigator.of(context).pushNamed(route),
          borderRadius: BorderRadius.circular(9 * u),
          child: Ink(
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(9 * u),
              border: Border.all(color: _gold, width: 1),
              gradient: filled
                  ? const LinearGradient(
                      colors: [Color(0xFFFFDD73), Color(0xFFE3AA24)],
                    )
                  : const LinearGradient(
                      colors: [Color(0xFF090909), Color(0xFF111111)],
                    ),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                if (icon != null) ...[
                  Icon(icon, size: 14 * u, color: filled ? Colors.black : _gold),
                  SizedBox(width: 5 * u),
                ],
                Flexible(
                  child: FittedBox(
                    fit: BoxFit.scaleDown,
                    child: Text(
                      text,
                      maxLines: 1,
                      style: TextStyle(
                        color: filled ? Colors.black : _gold,
                        fontSize: 9.5 * u,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _identity(BuildContext context, double u) {
    return Container(
      height: 58 * u,
      decoration: const BoxDecoration(
        border: Border(bottom: BorderSide(color: Color(0xFF242424))),
      ),
      child: Row(
        children: [
          GestureDetector(
            key: const ValueKey<String>('public-login-entry'),
            onTap: () => Navigator.of(context).pushNamed('/auth'),
            child: Container(
              width: 52 * u,
              height: 52 * u,
              padding: EdgeInsets.all(2 * u),
              decoration: const BoxDecoration(
                shape: BoxShape.circle,
                border: Border.fromBorderSide(BorderSide(color: _gold)),
              ),
              child: ClipOval(
                child: Image.asset(
                  'assets/images/fitnexus_mobile_approved_profile.webp',
                  fit: BoxFit.cover,
                ),
              ),
            ),
          ),
          SizedBox(width: 11 * u),
          Expanded(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Bom dia,',
                  style: TextStyle(color: _muted, fontSize: 12 * u, height: 1),
                ),
                SizedBox(height: 4 * u),
                Text(
                  'Felipe',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 21 * u,
                    fontWeight: FontWeight.w800,
                    height: 1,
                  ),
                ),
              ],
            ),
          ),
          Container(
            width: 96 * u,
            height: 47 * u,
            padding: EdgeInsets.symmetric(horizontal: 9 * u, vertical: 7 * u),
            decoration: BoxDecoration(
              color: const Color(0xFF090909),
              borderRadius: BorderRadius.circular(8 * u),
              border: Border.all(color: const Color(0xFF292929)),
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      width: 7 * u,
                      height: 7 * u,
                      decoration: const BoxDecoration(
                        shape: BoxShape.circle,
                        color: _gold2,
                      ),
                    ),
                    SizedBox(width: 5 * u),
                    Text(
                      'Em dia',
                      style: TextStyle(
                        color: _gold2,
                        fontSize: 9.2 * u,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ],
                ),
                SizedBox(height: 2 * u),
                FittedBox(
                  fit: BoxFit.scaleDown,
                  alignment: Alignment.centerLeft,
                  child: Text(
                    'Continue assim!',
                    maxLines: 1,
                    style: TextStyle(color: _muted, fontSize: 8 * u),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _hero(BuildContext context, double u) {
    return SizedBox(
      key: const ValueKey<String>('blackgold-home-hero'),
      width: double.infinity,
      height: 216 * u,
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          Positioned.fill(
            child: Container(
              decoration: BoxDecoration(
                color: _panel,
                borderRadius: BorderRadius.circular(10 * u),
                border: Border.all(color: _line),
                boxShadow: const [
                  BoxShadow(
                    color: Color(0x33000000),
                    blurRadius: 14,
                    offset: Offset(0, 8),
                  ),
                ],
              ),
            ),
          ),
          Positioned(
            top: -48 * u,
            right: 18 * u,
            width: 174 * u,
            height: 250 * u,
            child: ClipRRect(
              borderRadius: BorderRadius.only(
                topRight: Radius.circular(10 * u),
                bottomRight: Radius.circular(10 * u),
              ),
              child: Image.asset(
                'assets/images/fitnexus_mobile_approved_hero_v3.png',
                fit: BoxFit.cover,
                alignment: Alignment.centerRight,
              ),
            ),
          ),
          Positioned.fill(
            child: IgnorePointer(
              child: DecoratedBox(
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(10 * u),
                  gradient: const LinearGradient(
                    begin: Alignment.centerLeft,
                    end: Alignment.centerRight,
                    stops: [0, .46, .70, 1],
                    colors: [
                      Color(0xFF080808),
                      Color(0xF2080808),
                      Color(0x48080808),
                      Color(0x00080808),
                    ],
                  ),
                ),
              ),
            ),
          ),
          Padding(
            padding: EdgeInsets.fromLTRB(14 * u, 15 * u, 8 * u, 11 * u),
            child: SizedBox(
              width: 178 * u,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Sua evolução',
                    maxLines: 1,
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 23 * u,
                      fontWeight: FontWeight.w800,
                      letterSpacing: -.5,
                      height: 1,
                    ),
                  ),
                  Text(
                    'sob controle.',
                    maxLines: 1,
                    style: TextStyle(
                      color: _gold2,
                      fontSize: 23 * u,
                      fontWeight: FontWeight.w800,
                      letterSpacing: -.5,
                      height: 1.03,
                    ),
                  ),
                  SizedBox(height: 9 * u),
                  Text(
                    'Treino, alimentação, progresso e\n'
                    'acompanhamento em um só lugar para\n'
                    'transformar sua rotina.',
                    maxLines: 3,
                    style: TextStyle(
                      color: Colors.white.withValues(alpha: .94),
                      fontSize: 9 * u,
                      height: 1.32,
                    ),
                  ),
                  const Spacer(),
                  _heroButton(
                    context,
                    u,
                    'Começar treino',
                    Icons.play_arrow_rounded,
                    true,
                    '/start',
                  ),
                  SizedBox(height: 5 * u),
                  _heroButton(
                    context,
                    u,
                    'Plano alimentar',
                    Icons.restaurant_outlined,
                    false,
                    '/start',
                  ),
                  SizedBox(height: 5 * u),
                  _heroButton(
                    context,
                    u,
                    'Falar com coach',
                    Icons.chat_bubble_outline_rounded,
                    false,
                    '/support',
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _heroButton(
    BuildContext context,
    double u,
    String text,
    IconData icon,
    bool filled,
    String route,
  ) {
    return SizedBox(
      width: 164 * u,
      height: 29 * u,
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(7 * u),
        child: InkWell(
          onTap: () => Navigator.of(context).pushNamed(route),
          borderRadius: BorderRadius.circular(7 * u),
          child: Ink(
            padding: EdgeInsets.symmetric(horizontal: 9 * u),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(7 * u),
              border: Border.all(color: _gold),
              gradient: filled
                  ? const LinearGradient(
                      colors: [Color(0xFFFFD967), Color(0xFFE5AB27)],
                    )
                  : const LinearGradient(
                      colors: [Color(0xE6080808), Color(0xD00B0B0B)],
                    ),
            ),
            child: Row(
              children: [
                Icon(icon, size: 14 * u, color: filled ? Colors.black : _gold),
                SizedBox(width: 7 * u),
                Expanded(
                  child: FittedBox(
                    fit: BoxFit.scaleDown,
                    alignment: Alignment.centerLeft,
                    child: Text(
                      text,
                      maxLines: 1,
                      style: TextStyle(
                        color: filled ? Colors.black : Colors.white,
                        fontSize: 9.5 * u,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _stats(double u) {
    final items = <(IconData, String, String, String, Color)>[
      (Icons.fitness_center_rounded, 'Treinos da semana', '5/6', '83%', _gold),
      (Icons.local_fire_department_outlined, 'Calorias', '2.450', '▲ 12%', _green),
      (Icons.monitor_weight_outlined, 'Peso', '78,4', '▼ 0,6 kg', _green),
      (Icons.stacked_line_chart_rounded, 'Progresso', '72%', '⌁⌁⌁', _gold2),
    ];
    return Row(
      children: List.generate(items.length, (index) {
        final item = items[index];
        return Expanded(
          child: Padding(
            padding: EdgeInsets.only(right: index == items.length - 1 ? 0 : 7 * u),
            child: Container(
              height: 82 * u,
              padding: EdgeInsets.all(8 * u),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(8 * u),
                border: Border.all(color: const Color(0xFF4E3A10)),
                gradient: const LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [Color(0xFF111111), Color(0xFF070707)],
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  SizedBox(
                    height: 22 * u,
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Icon(item.$1, color: _gold, size: 14 * u),
                        SizedBox(width: 5 * u),
                        Expanded(
                          child: Text(
                            item.$2,
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                            style: TextStyle(color: Colors.white, fontSize: 8.1 * u, height: 1.04),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const Spacer(),
                  Text(
                    item.$3,
                    maxLines: 1,
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 17 * u,
                      fontWeight: FontWeight.w800,
                      height: 1,
                    ),
                  ),
                  SizedBox(height: 5 * u),
                  FittedBox(
                    fit: BoxFit.scaleDown,
                    alignment: Alignment.centerLeft,
                    child: Text(
                      item.$4,
                      maxLines: 1,
                      style: TextStyle(color: item.$5, fontSize: 8 * u, fontWeight: FontWeight.w700),
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      }),
    );
  }

  Widget _modules(BuildContext context, double u) {
    final items = <(String, String, IconData, Alignment)>[
      ('Treinos', 'Planos personalizados', Icons.fitness_center_rounded, const Alignment(-1, 0)),
      ('Nutrição', 'Alimentação inteligente', Icons.ramen_dining_outlined, const Alignment(-.6, 0)),
      ('Agenda', 'Compromissos e treinos', Icons.calendar_month_outlined, const Alignment(-.2, 0)),
      ('Resultados', 'Acompanhe sua evolução', Icons.bar_chart_rounded, const Alignment(.2, 0)),
      ('Hábitos', 'Constância que transforma', Icons.spa_outlined, const Alignment(.6, 0)),
      ('Comunidade', 'Conecte-se e evolua', Icons.groups_2_outlined, const Alignment(1, 0)),
    ];
    return GridView.builder(
      itemCount: items.length,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 3,
        crossAxisSpacing: 8 * u,
        mainAxisSpacing: 8 * u,
        childAspectRatio: 1.49,
      ),
      itemBuilder: (context, index) {
        final item = items[index];
        return Material(
          color: Colors.transparent,
          borderRadius: BorderRadius.circular(8 * u),
          child: InkWell(
            onTap: () => Navigator.of(context).pushNamed('/start'),
            borderRadius: BorderRadius.circular(8 * u),
            child: Ink(
              decoration: BoxDecoration(
                color: _panel,
                borderRadius: BorderRadius.circular(8 * u),
                border: Border.all(color: _line),
              ),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(7 * u),
                child: Stack(
                  fit: StackFit.expand,
                  children: [
                    Align(
                      alignment: Alignment.centerRight,
                      child: FractionallySizedBox(
                        widthFactor: .62,
                        heightFactor: 1,
                        child: Image.asset(
                          'assets/images/fitnexus_mobile_approved_modules.webp',
                          fit: BoxFit.cover,
                          alignment: item.$4,
                        ),
                      ),
                    ),
                    const DecoratedBox(
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          begin: Alignment.centerLeft,
                          end: Alignment.centerRight,
                          stops: [0, .48, .82, 1],
                          colors: [
                            Color(0xFF090909),
                            Color(0xD6090909),
                            Color(0x45090909),
                            Color(0x00090909),
                          ],
                        ),
                      ),
                    ),
                    Padding(
                      padding: EdgeInsets.fromLTRB(8 * u, 7 * u, 5 * u, 6 * u),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Icon(item.$3, color: _gold, size: 16 * u),
                          const Spacer(),
                          Text(
                            item.$1,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: TextStyle(color: Colors.white, fontSize: 10.4 * u, fontWeight: FontWeight.w800, height: 1),
                          ),
                          SizedBox(height: 3 * u),
                          FittedBox(
                            fit: BoxFit.scaleDown,
                            alignment: Alignment.centerLeft,
                            child: Text(
                              item.$2,
                              maxLines: 1,
                              style: TextStyle(color: _muted, fontSize: 6.8 * u),
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
        );
      },
    );
  }

  Widget _progress(double u) {
    const days = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'];
    return Container(
      height: 98 * u,
      padding: EdgeInsets.fromLTRB(10 * u, 9 * u, 10 * u, 8 * u),
      decoration: BoxDecoration(
        color: _panel,
        borderRadius: BorderRadius.circular(9 * u),
        border: Border.all(color: _line),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Icon(Icons.show_chart_rounded, color: _gold, size: 16 * u),
              SizedBox(width: 6 * u),
              Expanded(
                child: Text(
                  'Seu progresso semanal',
                  maxLines: 1,
                  style: TextStyle(color: Colors.white, fontSize: 10.5 * u, fontWeight: FontWeight.w700),
                ),
              ),
              Text('Ver detalhes', style: TextStyle(color: _muted, fontSize: 7.8 * u)),
              Icon(Icons.chevron_right_rounded, color: _gold, size: 14 * u),
            ],
          ),
          const Spacer(),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: List.generate(days.length, (index) {
              final done = index < 3;
              final current = index == 3;
              return SizedBox(
                width: 38 * u,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      width: 30 * u,
                      height: 30 * u,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        border: Border.all(
                          color: done || current ? _gold2 : const Color(0xFF777777),
                          width: 1.5,
                        ),
                        gradient: current
                            ? const SweepGradient(
                                colors: [_gold2, _gold2, Color(0xFF252525), Color(0xFF252525)],
                                stops: [0, .55, .56, 1],
                              )
                            : null,
                      ),
                      child: done ? Icon(Icons.check_rounded, color: _gold2, size: 18 * u) : null,
                    ),
                    SizedBox(height: 4 * u),
                    Text(days[index], maxLines: 1, style: TextStyle(color: _muted, fontSize: 7.7 * u)),
                  ],
                ),
              );
            }),
          ),
        ],
      ),
    );
  }

  Widget _nav(BuildContext context, double u) {
    const items = <(IconData, String)>[
      (Icons.home_rounded, 'Início'),
      (Icons.fitness_center_rounded, 'Treinos'),
      (Icons.assignment_outlined, 'Plano'),
      (Icons.bar_chart_rounded, 'Progresso'),
      (Icons.grid_view_rounded, 'Mais'),
    ];
    return SafeArea(
      top: false,
      child: Container(
        height: 72 * u,
        padding: EdgeInsets.symmetric(horizontal: 12 * u, vertical: 8 * u),
        decoration: const BoxDecoration(
          color: Color(0xFF080808),
          border: Border(top: BorderSide(color: Color(0xFF3A2B0C))),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: List.generate(items.length, (index) {
            final active = index == 0;
            final item = items[index];
            return Expanded(
              child: InkWell(
                onTap: index == 0 ? null : () => Navigator.of(context).pushNamed('/start'),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(item.$1, color: active ? _gold2 : Colors.white60, size: 20 * u),
                    SizedBox(height: 4 * u),
                    Text(
                      item.$2,
                      maxLines: 1,
                      style: TextStyle(
                        color: active ? _gold2 : Colors.white60,
                        fontSize: 7.6 * u,
                        fontWeight: active ? FontWeight.w700 : FontWeight.w500,
                      ),
                    ),
                  ],
                ),
              ),
            );
          }),
        ),
      ),
    );
  }
}
