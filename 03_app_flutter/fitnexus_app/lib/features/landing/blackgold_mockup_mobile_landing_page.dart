import 'package:flutter/material.dart';

const _bg = Color(0xFF050505);
const _panel = Color(0xFF0B0B0B);
const _gold = Color(0xFFF2C94C);
const _gold2 = Color(0xFFFFD45B);
const _muted = Color(0xFFB9B9B9);
const _line = Color(0xFF5B4310);
const _green = Color(0xFF3DDC84);

class LandingPage extends StatelessWidget {
  const LandingPage({super.key});
  static const Color canvas = _bg;

  double s(BuildContext c) => (MediaQuery.sizeOf(c).width / 390).clamp(.88, 1.08);

  @override
  Widget build(BuildContext context) {
    final q = MediaQuery.of(context);
    final k = s(context);
    return MediaQuery(
      data: q.copyWith(textScaler: TextScaler.linear(q.textScaler.scale(1).clamp(.9, 1.0))),
      child: Scaffold(
        backgroundColor: _bg,
        body: SafeArea(
          bottom: false,
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 430),
              child: SingleChildScrollView(
                padding: EdgeInsets.fromLTRB(14 * k, 8, 14 * k, 88),
                child: Column(children: [
                  _header(context, k),
                  const SizedBox(height: 10),
                  _identity(context, k),
                  const SizedBox(height: 10),
                  _hero(context, k),
                  const SizedBox(height: 10),
                  _stats(k),
                  const SizedBox(height: 10),
                  _modules(context, k),
                  const SizedBox(height: 10),
                  _progress(k),
                ]),
              ),
            ),
          ),
        ),
        bottomNavigationBar: _nav(context, k),
      ),
    );
  }

  Widget _header(BuildContext c, double k) => SizedBox(
        height: 50 * k,
        child: Row(children: [
          Expanded(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text.rich(
                  const TextSpan(children: [
                    TextSpan(text: 'FIT', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w800)),
                    TextSpan(text: 'NEXUS', style: TextStyle(color: _gold2, fontWeight: FontWeight.w400)),
                  ]),
                  style: TextStyle(fontSize: 22 * k, letterSpacing: 1.3, height: 1),
                ),
                const SizedBox(height: 5),
                Text('COACH  BLACKGOLD',
                    style: TextStyle(color: Colors.white70, fontSize: 7.3 * k, letterSpacing: 2.5, fontWeight: FontWeight.w600)),
              ],
            ),
          ),
          _topButton(c, k, 'Ecossistema', Icons.hub_outlined, false, '/links'),
          SizedBox(width: 6 * k),
          _topButton(c, k, 'Criar conta', null, true, '/start',
              key: const ValueKey<String>('public-signup-entry')),
        ]),
      );

  Widget _topButton(BuildContext c, double k, String text, IconData? icon, bool fill, String route, {Key? key}) =>
      Material(
        key: key,
        color: fill ? _gold2 : Colors.transparent,
        borderRadius: BorderRadius.circular(9),
        child: InkWell(
          onTap: () => Navigator.of(c).pushNamed(route),
          borderRadius: BorderRadius.circular(9),
          child: Container(
            height: 35 * k,
            padding: EdgeInsets.symmetric(horizontal: 9 * k),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(9),
              border: Border.all(color: _gold),
              gradient: fill ? const LinearGradient(colors: [Color(0xFFFFDD73), Color(0xFFE3AA24)]) : null,
            ),
            child: Row(mainAxisSize: MainAxisSize.min, children: [
              if (icon != null) ...[
                Icon(icon, size: 14 * k, color: fill ? Colors.black : _gold),
                SizedBox(width: 5 * k),
              ],
              Text(text,
                  style: TextStyle(color: fill ? Colors.black : _gold, fontWeight: FontWeight.w700, fontSize: 9.5 * k)),
            ]),
          ),
        ),
      );

  Widget _identity(BuildContext c, double k) => Container(
        height: 58 * k,
        decoration: const BoxDecoration(border: Border(bottom: BorderSide(color: Color(0xFF242424)))),
        child: Row(children: [
          GestureDetector(
            key: const ValueKey<String>('public-login-entry'),
            onTap: () => Navigator.of(c).pushNamed('/auth'),
            child: Container(
              width: 52 * k,
              height: 52 * k,
              padding: const EdgeInsets.all(2),
              decoration: const BoxDecoration(shape: BoxShape.circle, border: Border.fromBorderSide(BorderSide(color: _gold))),
              child: ClipOval(
                child: Image.asset('assets/images/fitnexus_mobile_approved_profile.webp', fit: BoxFit.cover),
              ),
            ),
          ),
          SizedBox(width: 11 * k),
          Expanded(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Bom dia,', style: TextStyle(color: _muted, fontSize: 12 * k, height: 1)),
                SizedBox(height: 4 * k),
                Text('Felipe',
                    style: TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 21 * k, height: 1)),
              ],
            ),
          ),
          Container(
            padding: EdgeInsets.symmetric(horizontal: 9 * k, vertical: 7 * k),
            decoration: BoxDecoration(
                color: const Color(0xFF090909), borderRadius: BorderRadius.circular(8), border: Border.all(color: const Color(0xFF292929))),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(mainAxisSize: MainAxisSize.min, children: [
                Container(width: 7 * k, height: 7 * k, decoration: const BoxDecoration(shape: BoxShape.circle, color: _gold2)),
                SizedBox(width: 5 * k),
                Text('Em dia', style: TextStyle(color: _gold2, fontWeight: FontWeight.w700, fontSize: 9.5 * k)),
              ]),
              Text('Continue assim!', style: TextStyle(color: _muted, fontSize: 8 * k)),
            ]),
          ),
        ]),
      );

  Widget _hero(BuildContext c, double k) => Container(
        height: 215 * k,
        clipBehavior: Clip.antiAlias,
        decoration: BoxDecoration(
          color: _panel,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: _line),
          boxShadow: const [BoxShadow(color: Color(0x33000000), blurRadius: 12, offset: Offset(0, 8))],
        ),
        child: Stack(fit: StackFit.expand, children: [
          Positioned(
            top: 0,
            right: 0,
            bottom: 0,
            width: 198 * k,
            child: Image.asset('assets/images/fitnexus_mobile_approved_hero.webp',
                fit: BoxFit.cover, alignment: Alignment.centerRight),
          ),
          const DecoratedBox(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.centerLeft,
                end: Alignment.centerRight,
                stops: [0, .5, .78, 1],
                colors: [Color(0xFF080808), Color(0xF5080808), Color(0x8B080808), Color(0x08080808)],
              ),
            ),
          ),
          Padding(
            padding: EdgeInsets.fromLTRB(14 * k, 15 * k, 10 * k, 11 * k),
            child: Align(
              alignment: Alignment.centerLeft,
              child: SizedBox(
                width: 188 * k,
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text('Sua evolução',
                      style: TextStyle(color: Colors.white, fontSize: 24 * k, height: 1, fontWeight: FontWeight.w800, letterSpacing: -.5)),
                  Text('sob controle.',
                      style: TextStyle(color: _gold2, fontSize: 24 * k, height: 1.03, fontWeight: FontWeight.w800, letterSpacing: -.5)),
                  SizedBox(height: 9 * k),
                  Text('Treino, alimentação, progresso e\nacompanhamento em um só lugar para\ntransformar sua rotina.',
                      style: TextStyle(color: Colors.white.withValues(alpha: .92), fontSize: 9.2 * k, height: 1.32)),
                  const Spacer(),
                  _heroButton(c, k, 'Começar treino', Icons.play_arrow_rounded, true, '/start'),
                  SizedBox(height: 4 * k),
                  _heroButton(c, k, 'Plano alimentar', Icons.restaurant_outlined, false, '/start'),
                  SizedBox(height: 4 * k),
                  _heroButton(c, k, 'Falar com coach', Icons.chat_bubble_outline_rounded, false, '/support'),
                ]),
              ),
            ),
          ),
        ]),
      );

  Widget _heroButton(BuildContext c, double k, String text, IconData icon, bool fill, String route) => SizedBox(
        width: 166 * k,
        height: 30 * k,
        child: Material(
          color: fill ? _gold2 : const Color(0xC7080808),
          borderRadius: BorderRadius.circular(7),
          child: InkWell(
            onTap: () => Navigator.of(c).pushNamed(route),
            borderRadius: BorderRadius.circular(7),
            child: Container(
              padding: EdgeInsets.symmetric(horizontal: 9 * k),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(7),
                border: Border.all(color: _gold),
                gradient: fill ? const LinearGradient(colors: [Color(0xFFFFD967), Color(0xFFE5AB27)]) : null,
              ),
              child: Row(children: [
                Icon(icon, color: fill ? Colors.black : _gold, size: 14 * k),
                SizedBox(width: 7 * k),
                Text(text,
                    style: TextStyle(color: fill ? Colors.black : Colors.white, fontWeight: FontWeight.w700, fontSize: 9 * k)),
              ]),
            ),
          ),
        ),
      );

  Widget _stats(double k) {
    final d = <(IconData, String, String, String, Color)>[
      (Icons.fitness_center_rounded, 'Treinos da\nsemana', '5/6', '83%', _gold),
      (Icons.local_fire_department_outlined, 'Calorias', '2.450', '▲ 12%', _green),
      (Icons.monitor_weight_outlined, 'Peso', '78,4', '▼ 0,6 kg', _green),
      (Icons.stacked_line_chart_rounded, 'Progresso', '72%', '⌁⌁⌁', _gold2),
    ];
    return Row(
      children: List.generate(
        d.length,
        (i) => Expanded(
          child: Padding(
            padding: EdgeInsets.only(right: i == d.length - 1 ? 0 : 7 * k),
            child: Container(
              height: 82 * k,
              padding: EdgeInsets.all(8 * k),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: const Color(0xFF4E3A10)),
                gradient: const LinearGradient(begin: Alignment.topLeft, end: Alignment.bottomRight, colors: [Color(0xFF111111), Color(0xFF070707)]),
              ),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Row(children: [
                  Icon(d[i].$1, color: _gold, size: 14 * k),
                  SizedBox(width: 5 * k),
                  Expanded(child: Text(d[i].$2, maxLines: 2, style: TextStyle(color: Colors.white, fontSize: 8.3 * k, height: 1.05))),
                ]),
                const Spacer(),
                Text(d[i].$3, style: TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 17 * k, height: 1)),
                SizedBox(height: 5 * k),
                Text(d[i].$4, style: TextStyle(color: d[i].$5, fontWeight: FontWeight.w700, fontSize: 8 * k)),
              ]),
            ),
          ),
        ),
      ),
    );
  }

  Widget _modules(BuildContext c, double k) {
    final d = <(String, String, IconData, Alignment)>[
      ('Treinos', 'Planos personalizados', Icons.fitness_center_rounded, const Alignment(-1, 0)),
      ('Nutrição', 'Alimentação inteligente', Icons.ramen_dining_outlined, const Alignment(-.6, 0)),
      ('Agenda', 'Compromissos e treinos', Icons.calendar_month_outlined, const Alignment(-.2, 0)),
      ('Resultados', 'Acompanhe sua evolução', Icons.bar_chart_rounded, const Alignment(.2, 0)),
      ('Hábitos', 'Constância que transforma', Icons.spa_outlined, const Alignment(.6, 0)),
      ('Comunidade', 'Conecte-se e evolua', Icons.groups_2_outlined, const Alignment(1, 0)),
    ];
    return GridView.builder(
      itemCount: d.length,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: 3, crossAxisSpacing: 8 * k, mainAxisSpacing: 8 * k, childAspectRatio: 1.48),
      itemBuilder: (_, i) => Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(8),
        child: InkWell(
          onTap: () => Navigator.of(c).pushNamed('/start'),
          borderRadius: BorderRadius.circular(8),
          child: Ink(
            decoration: BoxDecoration(color: _panel, borderRadius: BorderRadius.circular(8), border: Border.all(color: _line)),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(7),
              child: Stack(fit: StackFit.expand, children: [
                Align(
                  alignment: Alignment.centerRight,
                  child: FractionallySizedBox(
                    widthFactor: .53,
                    heightFactor: 1,
                    child: Image.asset('assets/images/fitnexus_mobile_approved_modules.webp',
                        fit: BoxFit.cover, alignment: d[i].$4),
                  ),
                ),
                const DecoratedBox(
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.centerLeft,
                      end: Alignment.centerRight,
                      stops: [0, .58, 1],
                      colors: [Color(0xFF090909), Color(0xE6090909), Color(0x10090909)],
                    ),
                  ),
                ),
                Padding(
                  padding: EdgeInsets.fromLTRB(8 * k, 7 * k, 5 * k, 6 * k),
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Icon(d[i].$3, color: _gold, size: 17 * k),
                    const Spacer(),
                    Text(d[i].$1,
                        maxLines: 1, style: TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 11 * k)),
                    SizedBox(height: 2 * k),
                    Text(d[i].$2,
                        maxLines: 1, overflow: TextOverflow.ellipsis, style: TextStyle(color: _muted, fontSize: 7 * k)),
                  ]),
                ),
              ]),
            ),
          ),
        ),
      ),
    );
  }

  Widget _progress(double k) {
    const days = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'];
    return Container(
      height: 110 * k,
      padding: EdgeInsets.fromLTRB(12 * k, 9 * k, 12 * k, 8 * k),
      decoration: BoxDecoration(color: _panel, borderRadius: BorderRadius.circular(9), border: Border.all(color: _line)),
      child: Column(children: [
        Row(children: [
          Icon(Icons.show_chart_rounded, color: _gold, size: 17 * k),
          SizedBox(width: 7 * k),
          Text('Seu progresso semanal', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 11 * k)),
          const Spacer(),
          Text('Ver detalhes', style: TextStyle(color: _muted, fontSize: 8 * k)),
          Icon(Icons.chevron_right_rounded, color: _gold, size: 14 * k),
        ]),
        const Spacer(),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: List.generate(days.length, (i) {
            final done = i < 3;
            final current = i == 3;
            return Column(children: [
              Container(
                width: 31 * k,
                height: 31 * k,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(color: done || current ? _gold2 : const Color(0xFF777777), width: 1.5),
                  gradient: current ? const SweepGradient(colors: [_gold2, Color(0xFF2A210C), _gold2]) : null,
                ),
                child: done ? Icon(Icons.check_rounded, color: _gold2, size: 18 * k) : null,
              ),
              SizedBox(height: 4 * k),
              Text(days[i], style: TextStyle(color: _muted, fontSize: 7.5 * k)),
            ]);
          }),
        ),
      ]),
    );
  }

  Widget _nav(BuildContext c, double k) {
    final d = <(IconData, String)>[
      (Icons.home_rounded, 'Início'),
      (Icons.fitness_center_rounded, 'Treinos'),
      (Icons.assignment_outlined, 'Plano'),
      (Icons.bar_chart_rounded, 'Progresso'),
      (Icons.grid_view_rounded, 'Mais'),
    ];
    return SafeArea(
      top: false,
      child: Container(
        height: 70 * k,
        decoration: const BoxDecoration(
          color: Color(0xFF0A0A0A),
          border: Border(top: BorderSide(color: Color(0xFF4C3810))),
          boxShadow: [BoxShadow(color: Color(0x66000000), blurRadius: 16, offset: Offset(0, -4))],
        ),
        child: Row(
          children: List.generate(
            d.length,
            (i) => Expanded(
              child: InkWell(
                onTap: i == 0 ? null : () => Navigator.of(c).pushNamed('/start'),
                child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                  Icon(d[i].$1, color: i == 0 ? _gold2 : const Color(0xFFAAAAAA), size: 21 * k),
                  SizedBox(height: 4 * k),
                  Text(d[i].$2,
                      style: TextStyle(color: i == 0 ? _gold2 : const Color(0xFFAAAAAA), fontSize: 8.5 * k, fontWeight: i == 0 ? FontWeight.w700 : FontWeight.w500)),
                ]),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
