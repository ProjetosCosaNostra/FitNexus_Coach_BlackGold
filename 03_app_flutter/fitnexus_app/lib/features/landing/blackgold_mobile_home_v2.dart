import 'package:flutter/material.dart';

const Color _bg = Color(0xFF050505);
const Color _panel = Color(0xFF0B0B0B);
const Color _gold = Color(0xFFF2C94C);
const Color _gold2 = Color(0xFFFFD45B);
const Color _muted = Color(0xFFB9B9B9);
const Color _line = Color(0xFF5B4310);
const Color _green = Color(0xFF3DDC84);

/// Mobile surface rebuilt from the frozen BlackGold mockup.
///
/// The decorative imagery comes from the approved reference, while every CTA,
/// metric, module, progress item and navigation target remains a native Flutter
/// widget. The layout deliberately disables external font scaling because this
/// screen is a pixel-sensitive visual-approval surface.
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
              final double u = (constraints.maxWidth / 390).clamp(.82, 1.08);
              return Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 430),
                  child: SingleChildScrollView(
                    padding: EdgeInsets.fromLTRB(14 * u, 7 * u, 14 * u, 22 * u),
                    child: Column(
                      children: [
                        _header(context, u),
                        _gap(u),
                        _identity(context, u),
                        _gap(u),
                        _hero(context, u),
                        _gap(u),
                        _stats(u),
                        _gap(u),
                        _modules(context, u),
                        _gap(u),
                        _progress(u),
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
            final double u = (constraints.maxWidth / 390).clamp(.82, 1.08);
            return _nav(context, u);
          },
        ),
      ),
    );
  }

  Widget _gap(double u) => SizedBox(height: 7 * u);

  Widget _header(BuildContext context, double u) {
    return SizedBox(
      height: 46 * u,
      child: Row(
        children: [
          Expanded(child: _brand(u)),
          SizedBox(width: 5 * u),
          _topButton(
            context,
            u,
            width: 86,
            text: 'Ecossistema',
            icon: Icons.hub_outlined,
            route: '/links',
          ),
          SizedBox(width: 5 * u),
          _topButton(
            context,
            u,
            width: 68,
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
      child: SizedBox(
        height: 38 * u,
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            SizedBox(
              height: 23 * u,
              child: FittedBox(
                fit: BoxFit.scaleDown,
                alignment: Alignment.centerLeft,
                child: Text.rich(
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
                  style: TextStyle(
                    fontSize: 21 * u,
                    letterSpacing: 1.2,
                    height: 1,
                  ),
                ),
              ),
            ),
            SizedBox(height: 3 * u),
            SizedBox(
              height: 9 * u,
              child: FittedBox(
                fit: BoxFit.scaleDown,
                alignment: Alignment.centerLeft,
                child: Text(
                  'COACH  BLACKGOLD',
                  maxLines: 1,
                  style: TextStyle(
                    color: Colors.white70,
                    fontSize: 7.2 * u,
                    letterSpacing: 2.2,
                    fontWeight: FontWeight.w600,
                    height: 1,
                  ),
                ),
              ),
            ),
          ],
        ),
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
      height: 32 * u,
      child: Material(
        color: filled ? _gold2 : Colors.transparent,
        borderRadius: BorderRadius.circular(8 * u),
        child: InkWell(
          onTap: () => Navigator.of(context).pushNamed(route),
          borderRadius: BorderRadius.circular(8 * u),
          child: Ink(
            padding: EdgeInsets.symmetric(horizontal: 6 * u),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(8 * u),
              border: Border.all(color: _gold),
              gradient: filled
                  ? const LinearGradient(
                      colors: [Color(0xFFFFDD73), Color(0xFFE3AA24)],
                    )
                  : null,
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                if (icon != null) ...[
                  Icon(icon, size: 12 * u, color: filled ? Colors.black : _gold),
                  SizedBox(width: 4 * u),
                ],
                Flexible(
                  child: FittedBox(
                    fit: BoxFit.scaleDown,
                    child: Text(
                      text,
                      maxLines: 1,
                      style: TextStyle(
                        color: filled ? Colors.black : _gold,
                        fontWeight: FontWeight.w700,
                        fontSize: 8.7 * u,
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
    return SizedBox(
      height: 54 * u,
      child: Row(
        children: [
          GestureDetector(
            key: const ValueKey<String>('public-login-entry'),
            onTap: () => Navigator.of(context).pushNamed('/auth'),
            child: Container(
              width: 48 * u,
              height: 48 * u,
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
          SizedBox(width: 10 * u),
          Expanded(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Bom dia,',
                  style: TextStyle(color: _muted, fontSize: 11 * u, height: 1),
                ),
                SizedBox(height: 3 * u),
                Text(
                  'Felipe',
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.w800,
                    fontSize: 20 * u,
                    height: 1,
                  ),
                ),
              ],
            ),
          ),
          Container(
            width: 92 * u,
            height: 43 * u,
            padding: EdgeInsets.symmetric(horizontal: 8 * u, vertical: 6 * u),
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
                      width: 6 * u,
                      height: 6 * u,
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
                        fontWeight: FontWeight.w700,
                        fontSize: 8.7 * u,
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
                    style: TextStyle(color: _muted, fontSize: 7.5 * u),
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
    return Container(
      height: 198 * u,
      clipBehavior: Clip.antiAlias,
      decoration: BoxDecoration(
        color: _panel,
        borderRadius: BorderRadius.circular(10 * u),
        border: Border.all(color: _line),
        boxShadow: const [
          BoxShadow(color: Color(0x33000000), blurRadius: 12, offset: Offset(0, 8)),
        ],
      ),
      child: Stack(
        fit: StackFit.expand,
        children: [
          Positioned(
            top: 0,
            right: 0,
            bottom: 0,
            width: 174 * u,
            child: Image.asset(
              'assets/images/fitnexus_mobile_approved_hero.webp',
              fit: BoxFit.cover,
              alignment: Alignment.centerRight,
            ),
          ),
          const DecoratedBox(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.centerLeft,
                end: Alignment.centerRight,
                stops: [0, .48, .78, 1],
                colors: [
                  Color(0xFF080808),
                  Color(0xF5080808),
                  Color(0x87080808),
                  Color(0x08080808),
                ],
              ),
            ),
          ),
          Padding(
            padding: EdgeInsets.fromLTRB(13 * u, 11 * u, 9 * u, 10 * u),
            child: Align(
              alignment: Alignment.centerLeft,
              child: SizedBox(
                width: 160 * u,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Sua evolução',
                      maxLines: 1,
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 20 * u,
                        height: 1,
                        fontWeight: FontWeight.w800,
                        letterSpacing: -.4,
                      ),
                    ),
                    Text(
                      'sob controle.',
                      maxLines: 1,
                      style: TextStyle(
                        color: _gold2,
                        fontSize: 20 * u,
                        height: 1.03,
                        fontWeight: FontWeight.w800,
                        letterSpacing: -.4,
                      ),
                    ),
                    SizedBox(height: 7 * u),
                    Text(
                      'Treino, alimentação, progresso e\nacompanhamento em um só lugar para\ntransformar sua rotina.',
                      maxLines: 3,
                      overflow: TextOverflow.fade,
                      style: TextStyle(
                        color: Colors.white.withValues(alpha: .92),
                        fontSize: 7.5 * u,
                        height: 1.25,
                      ),
                    ),
                    SizedBox(height: 8 * u),
                    _heroButton(
                      context,
                      u,
                      'Começar treino',
                      Icons.play_arrow_rounded,
                      true,
                      '/start',
                    ),
                    SizedBox(height: 4 * u),
                    _heroButton(
                      context,
                      u,
                      'Plano alimentar',
                      Icons.restaurant_outlined,
                      false,
                      '/start',
                    ),
                    SizedBox(height: 4 * u),
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
      width: 142 * u,
      height: 23 * u,
      child: Material(
        color: filled ? _gold2 : const Color(0xD0080808),
        borderRadius: BorderRadius.circular(6 * u),
        child: InkWell(
          onTap: () => Navigator.of(context).pushNamed(route),
          borderRadius: BorderRadius.circular(6 * u),
          child: Ink(
            padding: EdgeInsets.symmetric(horizontal: 8 * u),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(6 * u),
              border: Border.all(color: _gold),
              gradient: filled
                  ? const LinearGradient(
                      colors: [Color(0xFFFFD967), Color(0xFFE5AB27)],
                    )
                  : null,
            ),
            child: Row(
              children: [
                Icon(icon, color: filled ? Colors.black : _gold, size: 12 * u),
                SizedBox(width: 6 * u),
                Expanded(
                  child: FittedBox(
                    fit: BoxFit.scaleDown,
                    alignment: Alignment.centerLeft,
                    child: Text(
                      text,
                      maxLines: 1,
                      style: TextStyle(
                        color: filled ? Colors.black : Colors.white,
                        fontWeight: FontWeight.w700,
                        fontSize: 8.2 * u,
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
            padding: EdgeInsets.only(right: index == items.length - 1 ? 0 : 6 * u),
            child: Container(
              height: 74 * u,
              padding: EdgeInsets.all(6 * u),
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
                    height: 20 * u,
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Icon(item.$1, color: _gold, size: 12 * u),
                        SizedBox(width: 4 * u),
                        Expanded(
                          child: Text(
                            item.$2,
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 7.1 * u,
                              height: 1.05,
                            ),
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
                      fontWeight: FontWeight.w800,
                      fontSize: 15.5 * u,
                      height: 1,
                    ),
                  ),
                  SizedBox(height: 4 * u),
                  FittedBox(
                    fit: BoxFit.scaleDown,
                    alignment: Alignment.centerLeft,
                    child: Text(
                      item.$4,
                      maxLines: 1,
                      style: TextStyle(
                        color: item.$5,
                        fontWeight: FontWeight.w700,
                        fontSize: 7.2 * u,
                      ),
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
        crossAxisSpacing: 7 * u,
        mainAxisSpacing: 7 * u,
        childAspectRatio: 1.60,
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
                        widthFactor: .53,
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
                          stops: [0, .58, 1],
                          colors: [
                            Color(0xFF090909),
                            Color(0xE6090909),
                            Color(0x10090909),
                          ],
                        ),
                      ),
                    ),
                    Padding(
                      padding: EdgeInsets.fromLTRB(7 * u, 6 * u, 4 * u, 5 * u),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Icon(item.$3, color: _gold, size: 15 * u),
                          const Spacer(),
                          FittedBox(
                            fit: BoxFit.scaleDown,
                            alignment: Alignment.centerLeft,
                            child: Text(
                              item.$1,
                              maxLines: 1,
                              style: TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.w800,
                                fontSize: 10 * u,
                              ),
                            ),
                          ),
                          SizedBox(height: 1 * u),
                          FittedBox(
                            fit: BoxFit.scaleDown,
                            alignment: Alignment.centerLeft,
                            child: Text(
                              item.$2,
                              maxLines: 1,
                              style: TextStyle(color: _muted, fontSize: 6.5 * u),
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
      padding: EdgeInsets.fromLTRB(10 * u, 8 * u, 10 * u, 7 * u),
      decoration: BoxDecoration(
        color: _panel,
        borderRadius: BorderRadius.circular(9 * u),
        border: Border.all(color: _line),
      ),
      child: Column(
        children: [
          SizedBox(
            height: 19 * u,
            child: Row(
              children: [
                Icon(Icons.show_chart_rounded, color: _gold, size: 15 * u),
                SizedBox(width: 6 * u),
                Expanded(
                  child: FittedBox(
                    fit: BoxFit.scaleDown,
                    alignment: Alignment.centerLeft,
                    child: Text(
                      'Seu progresso semanal',
                      maxLines: 1,
                      style: TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.w700,
                        fontSize: 10 * u,
                      ),
                    ),
                  ),
                ),
                SizedBox(width: 7 * u),
                FittedBox(
                  fit: BoxFit.scaleDown,
                  child: Row(
                    children: [
                      Text('Ver detalhes', style: TextStyle(color: _muted, fontSize: 7.4 * u)),
                      Icon(Icons.chevron_right_rounded, color: _gold, size: 13 * u),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const Spacer(),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: List.generate(days.length, (index) {
              final bool done = index < 3;
              final bool current = index == 3;
              return SizedBox(
                width: 36 * u,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      width: 28 * u,
                      height: 28 * u,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        border: Border.all(
                          color: done || current ? _gold2 : const Color(0xFF777777),
                          width: 1.4,
                        ),
                        gradient: current
                            ? const SweepGradient(
                                colors: [_gold2, Color(0xFF2A210C), _gold2],
                              )
                            : null,
                      ),
                      child: done
                          ? Icon(Icons.check_rounded, color: _gold2, size: 16 * u)
                          : null,
                    ),
                    SizedBox(height: 3 * u),
                    Text(days[index], style: TextStyle(color: _muted, fontSize: 7 * u)),
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
    final items = <(IconData, String)>[
      (Icons.home_rounded, 'Início'),
      (Icons.fitness_center_rounded, 'Treinos'),
      (Icons.assignment_outlined, 'Plano'),
      (Icons.bar_chart_rounded, 'Progresso'),
      (Icons.grid_view_rounded, 'Mais'),
    ];

    return SafeArea(
      top: false,
      child: Container(
        height: 64 * u,
        decoration: const BoxDecoration(
          color: Color(0xFF0A0A0A),
          border: Border(top: BorderSide(color: Color(0xFF4C3810))),
          boxShadow: [
            BoxShadow(color: Color(0x66000000), blurRadius: 16, offset: Offset(0, -4)),
          ],
        ),
        child: Row(
          children: List.generate(items.length, (index) {
            final item = items[index];
            final bool selected = index == 0;
            return Expanded(
              child: InkWell(
                onTap: selected ? null : () => Navigator.of(context).pushNamed('/start'),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      item.$1,
                      color: selected ? _gold2 : const Color(0xFFAAAAAA),
                      size: 19 * u,
                    ),
                    SizedBox(height: 3 * u),
                    Text(
                      item.$2,
                      maxLines: 1,
                      style: TextStyle(
                        color: selected ? _gold2 : const Color(0xFFAAAAAA),
                        fontSize: 8 * u,
                        fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
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
