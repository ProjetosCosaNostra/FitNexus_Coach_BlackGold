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
    ),
    _OfficialLink(
      title: 'FitNexus Coach',
      description: 'Sistema fitness para personal, professor e academia',
      url: 'https://projetoscosanostra.github.io/FitNexus_Coach_BlackGold/',
      icon: Icons.fitness_center,
    ),
    _OfficialLink(
      title: 'Instagram',
      description: 'Stories, criativos e novidades',
      url: 'https://www.instagram.com/cosanostra.blackgold/',
      icon: Icons.camera_alt,
    ),
    _OfficialLink(
      title: 'Telegram',
      description: 'Achados e avisos rápidos',
      url: 'https://t.me/BlackGoldSociety',
      icon: Icons.send,
    ),
    _OfficialLink(
      title: 'YouTube',
      description: 'Conteúdo longo, bastidores e vídeos',
      url: 'https://www.youtube.com/@cosanostra.blackgold',
      icon: Icons.ondemand_video,
    ),
    _OfficialLink(
      title: 'TikTok',
      description: 'Shorts, tendências e divulgação',
      url: 'https://www.tiktok.com/@cosanostra.blackgold?_r=1&_t=ZS-97W9QcZEfcw',
      icon: Icons.music_note,
    ),
    _OfficialLink(
      title: 'Kwai',
      description: 'Distribuição extra de vídeos',
      url: 'https://kwai-video.com/u/@cosanostra.blackgold/CwdSwBPA',
      icon: Icons.video_library,
    ),
    _OfficialLink(
      title: 'GitHub',
      description: 'Projetos, códigos e repositórios',
      url: 'https://github.com/ProjetosCosaNostra',
      icon: Icons.code,
    ),
    _OfficialLink(
      title: 'LinkedIn',
      description: 'Perfil profissional e projetos digitais',
      url: 'https://www.linkedin.com/in/felipe-projetoscosanostra/',
      icon: Icons.work,
    ),
    _OfficialLink(
      title: 'Facebook',
      description: 'Página social e presença da marca',
      url: 'https://www.facebook.com/cosanostra.blackgold',
      icon: Icons.facebook,
    ),
  ];

  @override
  Widget build(BuildContext context) {
    final double width = MediaQuery.sizeOf(context).width;
    final bool isMobile = width < 720;

    return Scaffold(
      backgroundColor: AppColors.black,
      body: SafeArea(
        child: SingleChildScrollView(
          child: Padding(
            padding: EdgeInsets.symmetric(horizontal: isMobile ? 18 : 64, vertical: isMobile ? 24 : 36),
            child: Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 1320),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.center,
                      children: <Widget>[
                        Container(
                          width: 44,
                          height: 44,
                          decoration: BoxDecoration(
                            borderRadius: BorderRadius.circular(16),
                            gradient: const LinearGradient(
                              colors: <Color>[AppColors.goldSoft, AppColors.gold],
                            ),
                          ),
                          child: const Icon(Icons.fitness_center, color: Colors.black, size: 24),
                        ),
                        const SizedBox(width: 14),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: const <Widget>[
                            Text(
                              'Ecossistema BlackGold',
                              style: TextStyle(
                                color: AppColors.text,
                                fontSize: 22,
                                fontWeight: FontWeight.w900,
                              ),
                            ),
                            SizedBox(height: 2),
                            Text(
                              'CANAIS OFICIAIS',
                              style: TextStyle(
                                color: AppColors.goldSoft,
                                fontSize: 11,
                                fontWeight: FontWeight.w900,
                                letterSpacing: 1.3,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                    const SizedBox(height: 18),
                    const Text(
                      'Todos os canais oficiais da Cosa Nostra Black & Gold em um só lugar.',
                      style: TextStyle(
                        color: AppColors.muted,
                        fontSize: 16,
                        height: 1.6,
                      ),
                    ),
                    const SizedBox(height: 32),
                    LayoutBuilder(
                      builder: (BuildContext context, BoxConstraints constraints) {
                        final int columns = constraints.maxWidth < 720
                            ? 1
                            : constraints.maxWidth < 1080
                                ? 2
                                : 3;

                        return GridView.builder(
                          shrinkWrap: true,
                          physics: const NeverScrollableScrollPhysics(),
                          itemCount: _officialLinks.length,
                          gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                            crossAxisCount: columns,
                            crossAxisSpacing: 20,
                            mainAxisSpacing: 20,
                            childAspectRatio: 1.15,
                          ),
                          itemBuilder: (BuildContext context, int index) {
                            return _LinkCard(link: _officialLinks[index]);
                          },
                        );
                      },
                    ),
                    const SizedBox(height: 40),
                    Text(
                      'Acesse os destinos oficiais com estilo BlackGold, sem formulários ou contato direto.',
                      style: TextStyle(
                        color: AppColors.muted.withValues(alpha: 0.86),
                        fontSize: 14,
                        height: 1.5,
                      ),
                    ),
                    const SizedBox(height: 12),
                    const Text(
                      'Todos os links abrem em nova aba no navegador para manter sua navegação principal segura.',
                      style: TextStyle(
                        color: AppColors.muted,
                        fontSize: 14,
                        height: 1.5,
                      ),
                    ),
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

class _OfficialLink {
  final String title;
  final String description;
  final String url;
  final IconData icon;

  const _OfficialLink({
    required this.title,
    required this.description,
    required this.url,
    required this.icon,
  });
}

class _LinkCard extends StatelessWidget {
  final _OfficialLink link;

  const _LinkCard({required this.link});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.blackSoft,
      borderRadius: BorderRadius.circular(24),
      child: InkWell(
        borderRadius: BorderRadius.circular(24),
        onTap: () => _openLink(link.url),
        child: Container(
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(24),
            border: Border.all(color: AppColors.goldSoft.withValues(alpha: 0.18)),
            boxShadow: <BoxShadow>[
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.22),
                blurRadius: 22,
                offset: const Offset(0, 10),
              ),
            ],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: AppColors.goldSoft.withValues(alpha: 0.16),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Icon(link.icon, color: AppColors.gold, size: 24),
              ),
              const SizedBox(height: 22),
              Text(
                link.title,
                style: const TextStyle(
                  color: AppColors.text,
                  fontSize: 18,
                  fontWeight: FontWeight.w900,
                ),
              ),
              const SizedBox(height: 10),
              Text(
                link.description,
                style: const TextStyle(
                  color: AppColors.muted,
                  fontSize: 14,
                  height: 1.65,
                ),
              ),
              const Spacer(),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: <Widget>[
                  Text(
                    'Abrir',
                    style: TextStyle(
                      color: AppColors.goldSoft,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  Icon(
                    Icons.open_in_new,
                    color: AppColors.goldSoft,
                    size: 18,
                  ),
                ],
              ),
            ],
          ),
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
