import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/theme/app_colors.dart';

class EcosystemLinksPage extends StatelessWidget {
  const EcosystemLinksPage({super.key});

  static const List<_OfficialLink> _officialLinks = <_OfficialLink>[
    _OfficialLink(
      title: 'Loja Oficial',
      description: 'Vitrine de produtos e achados selecionados',
      url: 'https://projetoscosanostra.github.io/La_Famiglia_Links/',
      icon: Icons.storefront,
      badge: 'Loja',
      group: 'Principal',
    ),
    _OfficialLink(
      title: 'FitNexus Coach',
      description: 'Sistema fitness para personal, professor e academia',
      url: 'https://projetoscosanostra.github.io/FitNexus_Coach_BlackGold/',
      icon: Icons.fitness_center,
      badge: 'Projeto',
      group: 'Principal',
    ),
    _OfficialLink(
      title: 'Instagram',
      description: 'Stories, criativos e novidades',
      url: 'https://www.instagram.com/cosanostra.blackgold/',
      icon: Icons.camera_alt,
      badge: 'Rede social',
      group: 'Redes',
    ),
    _OfficialLink(
      title: 'Telegram',
      description: 'Achados e avisos rápidos',
      url: 'https://t.me/BlackGoldSociety',
      icon: Icons.send,
      badge: 'Rede social',
      group: 'Redes',
    ),
    _OfficialLink(
      title: 'YouTube',
      description: 'Conteúdo longo, bastidores e vídeos',
      url: 'https://www.youtube.com/@cosanostra.blackgold',
      icon: Icons.ondemand_video,
      badge: 'Rede social',
      group: 'Redes',
    ),
    _OfficialLink(
      title: 'TikTok',
      description: 'Shorts, tendências e divulgação',
      url: 'https://www.tiktok.com/@cosanostra.blackgold?_r=1&_t=ZS-97W9QcZEfcw',
      icon: Icons.music_note,
      badge: 'Rede social',
      group: 'Redes',
    ),
    _OfficialLink(
      title: 'Kwai',
      description: 'Distribuição extra de vídeos',
      url: 'https://kwai-video.com/u/@cosanostra.blackgold/CwdSwBPA',
      icon: Icons.video_library,
      badge: 'Rede social',
      group: 'Redes',
    ),
    _OfficialLink(
      title: 'GitHub',
      description: 'Projetos, códigos e repositórios',
      url: 'https://github.com/ProjetosCosaNostra',
      icon: Icons.code,
      badge: 'Profissional',
      group: 'Profissional',
    ),
    _OfficialLink(
      title: 'LinkedIn',
      description: 'Perfil profissional e projetos digitais',
      url: 'https://www.linkedin.com/in/felipe-projetoscosanostra/',
      icon: Icons.work,
      badge: 'Profissional',
      group: 'Profissional',
    ),
    _OfficialLink(
      title: 'Facebook',
      description: 'Página social e presença da marca',
      url: 'https://www.facebook.com/cosanostra.blackgold',
      icon: Icons.facebook,
      badge: 'Rede social',
      group: 'Redes',
    ),
  ];

  @override
  Widget build(BuildContext context) {
    final double width = MediaQuery.of(context).size.width;
    final bool isMobile = width < 720;
    final bool isTablet = width < 1080;
    final double horizontalPadding = isMobile ? 18 : 28;
    final double sectionSpacing = isMobile ? 28 : 36;

    final List<_GroupSection> sections = <_GroupSection>[
      _GroupSection(
        title: 'Principal',
        links: _officialLinks.where((link) => link.group == 'Principal').toList(),
      ),
      _GroupSection(
        title: 'Redes',
        links: _officialLinks.where((link) => link.group == 'Redes').toList(),
      ),
      _GroupSection(
        title: 'Profissional',
        links: _officialLinks.where((link) => link.group == 'Profissional').toList(),
      ),
    ];

    return Scaffold(
      backgroundColor: AppColors.black,
      body: SafeArea(
        child: SingleChildScrollView(
          child: Padding(
            padding: EdgeInsets.symmetric(horizontal: horizontalPadding, vertical: 24),
            child: Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 1180),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.center,
                      children: <Widget>[
                        Container(
                          width: 52,
                          height: 52,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            gradient: const RadialGradient(
                              colors: <Color>[AppColors.gold, AppColors.goldSoft],
                              center: Alignment(-0.4, -0.4),
                              radius: 0.85,
                            ),
                            boxShadow: <BoxShadow>[
                              BoxShadow(
                                color: AppColors.gold.withValues(alpha: 0.28),
                                blurRadius: 20,
                                offset: const Offset(0, 8),
                              ),
                            ],
                          ),
                          child: const Icon(Icons.link, color: Colors.black, size: 28),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: const <Widget>[
                              Text(
                                'Ecossistema BlackGold',
                                style: TextStyle(
                                  color: AppColors.text,
                                  fontSize: 32,
                                  fontWeight: FontWeight.w900,
                                ),
                              ),
                              SizedBox(height: 6),
                              Text(
                                'Todos os canais oficiais em um só lugar.',
                                style: TextStyle(
                                  color: AppColors.muted,
                                  fontSize: 15,
                                  height: 1.5,
                                ),
                              ),
                            ],
                          ),
                        ),
                        TextButton.icon(
                          style: TextButton.styleFrom(
                            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                            side: BorderSide(color: AppColors.goldSoft.withValues(alpha: 0.28)),
                            foregroundColor: AppColors.text,
                            textStyle: const TextStyle(fontWeight: FontWeight.w700),
                          ),
                          onPressed: () => Navigator.of(context).pushNamed('/'),
                          icon: const Icon(Icons.home, size: 18),
                          label: const Text('Landing'),
                        ),
                      ],
                    ),
                    const SizedBox(height: 24),
                    Container(
                      width: double.infinity,
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(28),
                        gradient: LinearGradient(
                          colors: <Color>[
                            AppColors.blackSoft,
                            AppColors.black.withValues(alpha: 0.88),
                          ],
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                        ),
                        border: Border.all(color: AppColors.goldSoft.withValues(alpha: 0.18)),
                        boxShadow: <BoxShadow>[
                          BoxShadow(
                            color: AppColors.gold.withValues(alpha: 0.08),
                            blurRadius: 32,
                            offset: const Offset(0, 16),
                          ),
                        ],
                      ),
                      child: Stack(
                        children: <Widget>[
                          Positioned(
                            right: -40,
                            top: -40,
                            child: Container(
                              width: 220,
                              height: 220,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                gradient: RadialGradient(
                                  colors: <Color>[
                                    AppColors.gold.withValues(alpha: 0.18),
                                    Colors.transparent,
                                  ],
                                ),
                              ),
                            ),
                          ),
                          Positioned(
                            left: -44,
                            bottom: -24,
                            child: Container(
                              width: 180,
                              height: 180,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                gradient: RadialGradient(
                                  colors: <Color>[
                                    AppColors.goldSoft.withValues(alpha: 0.16),
                                    Colors.transparent,
                                  ],
                                ),
                              ),
                            ),
                          ),
                          Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 26, vertical: 28),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: const <Widget>[
                                _SectionBadge(label: 'CANAIS OFICIAIS'),
                                SizedBox(height: 16),
                                Text(
                                  'CosaNostra Black & Gold reúne loja, projetos, conteúdo, redes sociais e produtos digitais em um ecossistema único.',
                                  style: TextStyle(
                                    color: AppColors.text,
                                    fontSize: 17,
                                    height: 1.65,
                                    fontWeight: FontWeight.w500,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                    SizedBox(height: sectionSpacing),
                    ...sections.expand((section) => <Widget>[
                          Text(
                            section.title,
                            style: const TextStyle(
                              color: AppColors.text,
                              fontSize: 20,
                              fontWeight: FontWeight.w900,
                            ),
                          ),
                          const SizedBox(height: 16),
                          _LinksGrid(
                            links: section.links,
                            columns: isMobile ? 1 : isTablet ? 2 : 3,
                          ),
                          SizedBox(height: sectionSpacing),
                        ]),
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.symmetric(horizontal: 26, vertical: 24),
                      decoration: BoxDecoration(
                        color: AppColors.blackSoft.withValues(alpha: 0.96),
                        borderRadius: BorderRadius.circular(26),
                        border: Border.all(color: AppColors.goldSoft.withValues(alpha: 0.14)),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: <Widget>[
                          const Text(
                            'Siga o ecossistema BlackGold',
                            style: TextStyle(
                              color: AppColors.text,
                              fontSize: 20,
                              fontWeight: FontWeight.w900,
                            ),
                          ),
                          const SizedBox(height: 12),
                          const Text(
                            'Conteúdo direto no Instagram oficial para acompanhar lançamentos, tendências e novidades do ecossistema.',
                            style: TextStyle(
                              color: AppColors.muted,
                              fontSize: 15,
                              height: 1.6,
                            ),
                          ),
                          const SizedBox(height: 20),
                          SizedBox(
                            width: isMobile ? double.infinity : 220,
                            child: OutlinedButton(
                              style: OutlinedButton.styleFrom(
                                side: BorderSide(color: AppColors.goldSoft.withValues(alpha: 0.32)),
                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                                padding: const EdgeInsets.symmetric(vertical: 16),
                                foregroundColor: AppColors.text,
                                backgroundColor: AppColors.gold.withValues(alpha: 0.08),
                              ),
                              onPressed: () => _openLink('https://www.instagram.com/cosanostra.blackgold/'),
                              child: const Text('Ir ao Instagram'),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 24),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _LinksGrid extends StatelessWidget {
  const _LinksGrid({
    required this.links,
    required this.columns,
  });

  final List<_OfficialLink> links;
  final int columns;

  @override
  Widget build(BuildContext context) {
    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: links.length,
      gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: columns,
        crossAxisSpacing: 18,
        mainAxisSpacing: 18,
        childAspectRatio: 1.1,
      ),
      itemBuilder: (BuildContext context, int index) {
        return _LinkCard(link: links[index]);
      },
    );
  }
}

class _SectionBadge extends StatelessWidget {
  const _SectionBadge({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      decoration: BoxDecoration(
        color: AppColors.goldSoft.withValues(alpha: 0.16),
        borderRadius: BorderRadius.circular(14),
      ),
      child: Text(
        label,
        style: const TextStyle(
          color: AppColors.goldSoft,
          fontSize: 12,
          fontWeight: FontWeight.w800,
          letterSpacing: 1.2,
        ),
      ),
    );
  }
}

class _OfficialLink {
  final String title;
  final String description;
  final String url;
  final IconData icon;
  final String badge;
  final String group;

  const _OfficialLink({
    required this.title,
    required this.description,
    required this.url,
    required this.icon,
    required this.badge,
    required this.group,
  });
}

class _GroupSection {
  final String title;
  final List<_OfficialLink> links;

  const _GroupSection({required this.title, required this.links});
}

class _LinkCard extends StatefulWidget {
  const _LinkCard({required this.link});

  final _OfficialLink link;

  @override
  State<_LinkCard> createState() => _LinkCardState();
}

class _LinkCardState extends State<_LinkCard> {
  bool _hovered = false;

  void _onHover(bool hover) {
    setState(() {
      _hovered = hover;
    });
  }

  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      onEnter: (_) => _onHover(true),
      onExit: (_) => _onHover(false),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 220),
        transform: Matrix4.translationValues(0, _hovered ? -6 : 0, 0),
        decoration: BoxDecoration(
          color: AppColors.blackSoft.withValues(alpha: _hovered ? 0.98 : 0.94),
          borderRadius: BorderRadius.circular(24),
          border: Border.all(color: AppColors.goldSoft.withValues(alpha: _hovered ? 0.24 : 0.18)),
          boxShadow: <BoxShadow>[
            BoxShadow(
              color: Colors.black.withValues(alpha: _hovered ? 0.28 : 0.20),
              blurRadius: _hovered ? 26 : 18,
              offset: const Offset(0, 12),
            ),
          ],
        ),
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            borderRadius: BorderRadius.circular(24),
            onTap: () => _openLink(widget.link.url),
            child: Padding(
              padding: const EdgeInsets.all(22),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Row(
                    children: <Widget>[
                      Container(
                        width: 42,
                        height: 42,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: AppColors.goldSoft.withValues(alpha: 0.16),
                        ),
                        child: Icon(widget.link.icon, color: AppColors.gold, size: 22),
                      ),
                      const SizedBox(width: 12),
                      _Badge(label: widget.link.badge),
                    ],
                  ),
                  const SizedBox(height: 20),
                  Text(
                    widget.link.title,
                    style: const TextStyle(
                      color: AppColors.text,
                      fontSize: 18,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                  const SizedBox(height: 10),
                  Text(
                    widget.link.description,
                    style: const TextStyle(
                      color: AppColors.muted,
                      fontSize: 14,
                      height: 1.6,
                    ),
                  ),
                  const Spacer(),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: <Widget>[
                      const SizedBox.shrink(),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                        decoration: BoxDecoration(
                          color: AppColors.gold.withValues(alpha: 0.08),
                          borderRadius: BorderRadius.circular(14),
                        ),
                        child: const Text(
                          'Abrir',
                          style: TextStyle(
                            color: AppColors.goldSoft,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ),
                      const Icon(Icons.open_in_new, color: AppColors.goldSoft, size: 18),
                    ],
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

class _Badge extends StatelessWidget {
  const _Badge({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: AppColors.goldSoft.withValues(alpha: 0.16),
        borderRadius: BorderRadius.circular(14),
      ),
      child: Text(
        label,
        style: const TextStyle(
          color: AppColors.goldSoft,
          fontSize: 12,
          fontWeight: FontWeight.w800,
        ),
      ),
    );
  }
}

Future<void> _openLink(String url) async {
  final Uri uri = Uri.parse(url);
  if (!await launchUrl(
    uri,
    mode: LaunchMode.externalApplication,
    webOnlyWindowName: '_blank',
  )) {
    throw Exception('Não foi possível abrir o link oficial.');
  }
}
