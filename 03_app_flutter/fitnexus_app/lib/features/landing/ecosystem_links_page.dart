import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:url_launcher/url_launcher.dart';

class EcosystemLinksPage extends StatelessWidget {
  const EcosystemLinksPage({super.key});

  static const String hubUrl =
      'https://projetoscosanostra.github.io/FitNexus_Coach_BlackGold/#/links';

  static const List<_EcoLink> _mainLinks = <_EcoLink>[
    _EcoLink(
      title: 'Loja Oficial',
      badge: 'Vitrine',
      description: 'Achados selecionados, curadoria premium e produtos úteis.',
      handle: 'La Famiglia Links',
      url: 'https://projetoscosanostra.github.io/La_Famiglia_Links/',
      icon: Icons.storefront_rounded,
    ),
    _EcoLink(
      title: 'FitNexus Coach',
      badge: 'SaaS Fitness',
      description:
          'Sistema fitness para personal, professor, aluno e academia.',
      handle: 'Projeto BlackGold',
      url: 'https://projetoscosanostra.github.io/FitNexus_Coach_BlackGold/',
      icon: Icons.fitness_center_rounded,
    ),
  ];

  static const List<_EcoLink> _socialLinks = <_EcoLink>[
    _EcoLink(
      title: 'Instagram',
      badge: 'Rede social',
      description: 'Stories, criativos, novidades e vitrine visual.',
      handle: '@cosanostra.blackgold',
      url: 'https://www.instagram.com/cosanostra.blackgold/',
      icon: Icons.photo_camera_rounded,
    ),
    _EcoLink(
      title: 'Telegram',
      badge: 'Canal',
      description: 'Atualizações rápidas e achados.',
      handle: '@BlackGoldSociety',
      url: 'https://t.me/BlackGoldSociety',
      icon: Icons.send_rounded,
    ),
    _EcoLink(
      title: 'YouTube',
      badge: 'Conteúdo',
      description: 'Vídeos, bastidores e projetos.',
      handle: '@cosanostra.blackgold',
      url: 'https://www.youtube.com/@cosanostra.blackgold',
      icon: Icons.play_arrow_rounded,
    ),
    _EcoLink(
      title: 'TikTok',
      badge: 'Shorts',
      description: 'Tendências, cortes e divulgação.',
      handle: '@cosanostra.blackgold',
      url:
          'https://www.tiktok.com/@cosanostra.blackgold?_r=1&_t=ZS-97W9QcZEfcw',
      icon: Icons.music_note_rounded,
    ),
    _EcoLink(
      title: 'Kwai',
      badge: 'Vídeos',
      description: 'Canal extra para vídeos curtos.',
      handle: '@cosanostra.blackgold',
      url: 'https://kwai-video.com/u/@cosanostra.blackgold/CwdSwBPA',
      icon: Icons.video_library_rounded,
    ),
    _EcoLink(
      title: 'Facebook',
      badge: 'Rede social',
      description: 'Página social da marca.',
      handle: 'cosanostra.blackgold',
      url: 'https://www.facebook.com/cosanostra.blackgold',
      icon: Icons.facebook_rounded,
    ),
  ];

  static const List<_EcoLink> _professionalLinks = <_EcoLink>[
    _EcoLink(
      title: 'GitHub',
      badge: 'Código',
      description: 'Repositórios, páginas públicas e projetos digitais.',
      handle: 'ProjetosCosaNostra',
      url: 'https://github.com/ProjetosCosaNostra',
      icon: Icons.code_rounded,
    ),
    _EcoLink(
      title: 'LinkedIn',
      badge: 'Profissional',
      description: 'Perfil profissional, tecnologia, automação e projetos.',
      handle: 'Felipe Rosa Gomes',
      url: 'https://www.linkedin.com/in/felipe-projetoscosanostra/',
      icon: Icons.work_rounded,
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _K.black,
      body: Stack(
        children: const <Widget>[
          _BackgroundGlow(),
          SafeArea(
            child: _PageBody(),
          ),
        ],
      ),
    );
  }
}

class _PageBody extends StatelessWidget {
  const _PageBody();

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(22, 22, 22, 34),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 1180),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: const <Widget>[
              _Header(),
              SizedBox(height: 42),
              _Hero(),
              SizedBox(height: 34),
              _SectionTitle('Principal'),
              SizedBox(height: 10),
              _LinksGrid(
                  items: EcosystemLinksPage._mainLinks, desktopColumns: 2),
              SizedBox(height: 22),
              _SectionTitle('Redes oficiais'),
              SizedBox(height: 10),
              _LinksGrid(
                  items: EcosystemLinksPage._socialLinks, desktopColumns: 3),
              SizedBox(height: 22),
              _SectionTitle('Profissional'),
              SizedBox(height: 10),
              _LinksGrid(
                items: EcosystemLinksPage._professionalLinks,
                desktopColumns: 2,
              ),
              SizedBox(height: 24),
              _FinalCallout(),
            ],
          ),
        ),
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header();

  @override
  Widget build(BuildContext context) {
    return Row(
      children: <Widget>[
        Container(
          width: 58,
          height: 58,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(18),
            gradient: const LinearGradient(
              colors: <Color>[_K.gold, _K.goldLight],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            boxShadow: <BoxShadow>[
              BoxShadow(
                color: _K.gold.withValues(alpha: 0.30),
                blurRadius: 24,
                offset: const Offset(0, 10),
              ),
            ],
          ),
          child: const Icon(Icons.link_rounded, color: Colors.black, size: 30),
        ),
        const SizedBox(width: 16),
        const Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(
                'Ecossistema BlackGold',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  color: _K.text,
                  fontSize: 28,
                  fontWeight: FontWeight.w900,
                  height: 1,
                ),
              ),
              SizedBox(height: 6),
              Text(
                'Todos os canais oficiais em um só lugar.',
                style: TextStyle(
                  color: _K.muted,
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(width: 14),
        _SmallRouteButton(
          text: 'Landing',
          icon: Icons.home_rounded,
          route: '/',
        ),
      ],
    );
  }
}

class _Hero extends StatelessWidget {
  const _Hero();

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (BuildContext context, BoxConstraints constraints) {
        final bool narrow = constraints.maxWidth < 820;

        final Widget textBlock = Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment:
              narrow ? CrossAxisAlignment.center : CrossAxisAlignment.start,
          children: <Widget>[
            const _Badge(text: 'CANAIS OFICIAIS'),
            const SizedBox(height: 18),
            RichText(
              textAlign: narrow ? TextAlign.center : TextAlign.left,
              text: const TextSpan(
                style: TextStyle(
                  color: _K.text,
                  fontSize: 34,
                  height: 0.98,
                  fontWeight: FontWeight.w900,
                  letterSpacing: -1,
                ),
                children: <TextSpan>[
                  TextSpan(text: 'Um hub único para loja,\n'),
                  TextSpan(text: 'projetos, conteúdo e\n'),
                  TextSpan(
                    text: 'presença digital.',
                    style: TextStyle(color: _K.gold),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            Text(
              'A pessoa chega aqui e escolhe para onde quer ir: loja, redes sociais, projeto fitness ou perfil profissional.',
              textAlign: narrow ? TextAlign.center : TextAlign.left,
              style: const TextStyle(
                color: _K.muted,
                fontSize: 15,
                fontWeight: FontWeight.w700,
                height: 1.45,
              ),
            ),
            const SizedBox(height: 18),
            Wrap(
              alignment: narrow ? WrapAlignment.center : WrapAlignment.start,
              spacing: 10,
              runSpacing: 10,
              children: <Widget>[
                _HeroButton(
                  text: 'Copiar link',
                  icon: Icons.copy_rounded,
                  filled: true,
                  onPressed: () => _copyHub(context),
                ),
                _HeroButton(
                  text: 'Instagram',
                  icon: Icons.photo_camera_rounded,
                  onPressed: () => _openLink(
                    'https://www.instagram.com/cosanostra.blackgold/',
                  ),
                ),
                _HeroButton(
                  text: 'Loja oficial',
                  icon: Icons.storefront_rounded,
                  onPressed: () => _openLink(
                    'https://projetoscosanostra.github.io/La_Famiglia_Links/',
                  ),
                ),
              ],
            ),
          ],
        );

        final Widget heroImage = const _HeroImage();

        if (narrow) {
          return Column(
            children: <Widget>[
              textBlock,
              const SizedBox(height: 24),
              heroImage,
            ],
          );
        }

        return Row(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: <Widget>[
            Expanded(flex: 9, child: textBlock),
            const SizedBox(width: 34),
            Expanded(flex: 10, child: heroImage),
          ],
        );
      },
    );
  }
}

class _HeroImage extends StatelessWidget {
  const _HeroImage();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Container(
        constraints: const BoxConstraints(
          maxWidth: 540,
        ),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(26),
          boxShadow: <BoxShadow>[
            BoxShadow(
              color: _K.gold.withValues(alpha: 0.12),
              blurRadius: 44,
              offset: const Offset(0, 22),
            ),
          ],
        ),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(26),
          child: Image.asset(
            'assets/images/ecosistema_blackgold.png',
            fit: BoxFit.contain,
            filterQuality: FilterQuality.high,
            errorBuilder: (
              BuildContext context,
              Object error,
              StackTrace? stackTrace,
            ) {
              return Container(
                height: 360,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(26),
                  border: Border.all(color: _K.gold.withValues(alpha: 0.24)),
                  color: _K.card,
                ),
                child: const Text(
                  'BLACKGOLD\nECOSYSTEM',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: _K.gold,
                    fontSize: 28,
                    fontWeight: FontWeight.w900,
                    height: 0.95,
                  ),
                ),
              );
            },
          ),
        ),
      ),
    );
  }
}

class _SectionTitle extends StatelessWidget {
  const _SectionTitle(this.text);

  final String text;

  @override
  Widget build(BuildContext context) {
    return Text(
      '✦ $text',
      style: const TextStyle(
        color: _K.text,
        fontSize: 23,
        fontWeight: FontWeight.w900,
        height: 1,
      ),
    );
  }
}

class _LinksGrid extends StatelessWidget {
  const _LinksGrid({
    required this.items,
    required this.desktopColumns,
  });

  final List<_EcoLink> items;
  final int desktopColumns;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (BuildContext context, BoxConstraints constraints) {
        final double width = constraints.maxWidth;
        final int columns = width >= 980
            ? desktopColumns
            : width >= 680
                ? 2
                : 1;

        final double gap = width >= 980 ? 14 : 12;
        final double itemWidth = (width - (gap * (columns - 1))) / columns;

        return Wrap(
          spacing: gap,
          runSpacing: gap,
          children: items
              .map(
                (item) => SizedBox(
                  width: itemWidth,
                  child: _LinkCard(item: item),
                ),
              )
              .toList(),
        );
      },
    );
  }
}

class _LinkCard extends StatelessWidget {
  const _LinkCard({required this.item});

  final _EcoLink item;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        borderRadius: BorderRadius.circular(20),
        onTap: () => _openLink(item.url),
        child: Container(
          constraints: const BoxConstraints(minHeight: 104),
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
          decoration: BoxDecoration(
            color: _K.card.withValues(alpha: 0.95),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: _K.gold.withValues(alpha: 0.36)),
            boxShadow: <BoxShadow>[
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.24),
                blurRadius: 22,
                offset: const Offset(0, 12),
              ),
            ],
          ),
          child: Row(
            children: <Widget>[
              Container(
                width: 54,
                height: 54,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: const LinearGradient(
                    colors: <Color>[_K.gold, _K.goldDark],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  boxShadow: <BoxShadow>[
                    BoxShadow(
                      color: _K.gold.withValues(alpha: 0.18),
                      blurRadius: 18,
                      offset: const Offset(0, 8),
                    ),
                  ],
                ),
                child: Icon(item.icon, color: Colors.black, size: 28),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Row(
                      children: <Widget>[
                        Expanded(
                          child: Text(
                            item.title,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                              color: _K.text,
                              fontSize: 17,
                              fontWeight: FontWeight.w900,
                              height: 1.05,
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        _TinyBadge(text: item.badge),
                      ],
                    ),
                    const SizedBox(height: 7),
                    Text(
                      item.description,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: _K.muted,
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                        height: 1.2,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      item.handle,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: _K.gold,
                        fontSize: 12.5,
                        fontWeight: FontWeight.w900,
                        height: 1.1,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 12),
              Container(
                width: 36,
                height: 36,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: _K.gold.withValues(alpha: 0.50)),
                  color: _K.gold.withValues(alpha: 0.08),
                ),
                child: const Icon(
                  Icons.north_east_rounded,
                  color: _K.gold,
                  size: 21,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _FinalCallout extends StatelessWidget {
  const _FinalCallout();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: _K.card.withValues(alpha: 0.96),
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: _K.gold.withValues(alpha: 0.35)),
      ),
      child: Row(
        children: <Widget>[
          Container(
            width: 56,
            height: 56,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: _K.gold.withValues(alpha: 0.38)),
              color: _K.gold.withValues(alpha: 0.10),
            ),
            child: const Icon(Icons.link_rounded, color: _K.gold, size: 31),
          ),
          const SizedBox(width: 16),
          const Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  'Divulgue tudo com um único link.',
                  style: TextStyle(
                    color: _K.text,
                    fontSize: 18,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                SizedBox(height: 6),
                Text(
                  'Use este hub em bio, QR Code, criativos, vídeos, perfis sociais e páginas dos projetos.',
                  style: TextStyle(
                    color: _K.muted,
                    fontSize: 13.5,
                    fontWeight: FontWeight.w600,
                    height: 1.35,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 14),
          _HeroButton(
            text: 'Copiar link do ecossistema',
            icon: Icons.copy_rounded,
            filled: true,
            onPressed: null,
          ),
        ],
      ),
    );
  }
}

class _HeroButton extends StatelessWidget {
  const _HeroButton({
    required this.text,
    required this.icon,
    this.filled = false,
    this.onPressed,
  });

  final String text;
  final IconData icon;
  final bool filled;
  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) {
    return TextButton.icon(
      onPressed: onPressed ?? () => _copyHub(context),
      icon: Icon(icon, size: 16),
      label: Text(text),
      style: TextButton.styleFrom(
        backgroundColor: filled ? _K.gold : Colors.transparent,
        foregroundColor: filled ? Colors.black : _K.text,
        side: BorderSide(
            color: filled ? _K.gold : _K.gold.withValues(alpha: 0.72)),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(999)),
        textStyle: const TextStyle(
          fontWeight: FontWeight.w900,
          fontSize: 13.5,
        ),
      ),
    );
  }
}

class _SmallRouteButton extends StatelessWidget {
  const _SmallRouteButton({
    required this.text,
    required this.icon,
    required this.route,
  });

  final String text;
  final IconData icon;
  final String route;

  @override
  Widget build(BuildContext context) {
    return TextButton.icon(
      onPressed: () => Navigator.of(context).pushNamed(route),
      icon: Icon(icon, size: 16),
      label: Text(text),
      style: TextButton.styleFrom(
        foregroundColor: _K.text,
        side: BorderSide(color: _K.gold.withValues(alpha: 0.55)),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 11),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(999)),
        textStyle: const TextStyle(fontWeight: FontWeight.w900),
      ),
    );
  }
}

class _Badge extends StatelessWidget {
  const _Badge({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      decoration: BoxDecoration(
        color: _K.gold.withValues(alpha: 0.20),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        text,
        style: const TextStyle(
          color: _K.gold,
          fontSize: 12,
          fontWeight: FontWeight.w900,
          letterSpacing: 0.5,
        ),
      ),
    );
  }
}

class _TinyBadge extends StatelessWidget {
  const _TinyBadge({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: _K.gold.withValues(alpha: 0.16),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        text,
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
        style: const TextStyle(
          color: _K.gold,
          fontSize: 10,
          fontWeight: FontWeight.w900,
          height: 1,
        ),
      ),
    );
  }
}

class _BackgroundGlow extends StatelessWidget {
  const _BackgroundGlow();

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: <Widget>[
        Container(color: _K.black),
        Positioned(
          top: 90,
          left: -220,
          child: _Glow(size: 520, opacity: 0.10),
        ),
        Positioned(
          top: 120,
          right: -180,
          child: _Glow(size: 560, opacity: 0.12),
        ),
        Positioned(
          bottom: -260,
          right: 160,
          child: _Glow(size: 520, opacity: 0.06),
        ),
      ],
    );
  }
}

class _Glow extends StatelessWidget {
  const _Glow({required this.size, required this.opacity});

  final double size;
  final double opacity;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: RadialGradient(
          colors: <Color>[
            _K.gold.withValues(alpha: opacity),
            Colors.transparent,
          ],
        ),
      ),
    );
  }
}

class _EcoLink {
  const _EcoLink({
    required this.title,
    required this.badge,
    required this.description,
    required this.handle,
    required this.url,
    required this.icon,
  });

  final String title;
  final String badge;
  final String description;
  final String handle;
  final String url;
  final IconData icon;
}

class _K {
  static const Color black = Color(0xFF050505);
  static const Color card = Color(0xFF111111);
  static const Color text = Color(0xFFF8F6EF);
  static const Color muted = Color(0xFFC1B9AA);
  static const Color gold = Color(0xFFFFC83D);
  static const Color goldLight = Color(0xFFFFD96B);
  static const Color goldDark = Color(0xFF9D7410);
}

Future<void> _copyHub(BuildContext context) async {
  await Clipboard.setData(
    const ClipboardData(text: EcosystemLinksPage.hubUrl),
  );

  if (!context.mounted) return;

  ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(
      content: const Text('Link do ecossistema copiado.'),
      backgroundColor: _K.card,
      behavior: SnackBarBehavior.floating,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
    ),
  );
}

Future<void> _openLink(String url) async {
  final Uri uri = Uri.parse(url);

  final bool opened = await launchUrl(
    uri,
    mode: LaunchMode.externalApplication,
    webOnlyWindowName: '_blank',
  );

  if (!opened) {
    throw Exception('Não foi possível abrir o link oficial.');
  }
}
