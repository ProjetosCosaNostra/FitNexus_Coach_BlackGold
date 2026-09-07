import 'package:flutter/material.dart';

/// Bootstrap authority for the BlackGold Ecosystem V2.1.
///
/// The UI must consume this class instead of duplicating links inside feature
/// pages. The next infrastructure step is to hydrate the same model from the
/// canonical remote manifest, preserving this file only as the safe fallback.
enum BlackGoldLocale { ptBr, en, es }

enum BlackGoldEcoGroup { projects, social, professional, contact }

class BlackGoldEcoEntry {
  const BlackGoldEcoEntry({
    required this.id,
    required this.group,
    required this.icon,
    required this.labels,
    required this.descriptions,
    required this.canonicalUrl,
    this.handle,
    this.badge,
  });

  final String id;
  final BlackGoldEcoGroup group;
  final IconData icon;
  final Map<BlackGoldLocale, String> labels;
  final Map<BlackGoldLocale, String> descriptions;
  final String canonicalUrl;
  final String? handle;
  final String? badge;

  String label(BlackGoldLocale locale) =>
      labels[locale] ?? labels[BlackGoldLocale.en] ?? id;

  String description(BlackGoldLocale locale) =>
      descriptions[locale] ?? descriptions[BlackGoldLocale.en] ?? '';
}

class BlackGoldEcosystemManifest {
  const BlackGoldEcosystemManifest._();

  static const String version = '2.1';
  static const String effectiveDate = '2026-09-05';
  static const String contactEmail = 'projetoscosanostra@gmail.com';

  static const List<BlackGoldEcoEntry> entries = <BlackGoldEcoEntry>[
    BlackGoldEcoEntry(
      id: 'official_store',
      group: BlackGoldEcoGroup.projects,
      icon: Icons.storefront_rounded,
      badge: 'Cloudflare Pages',
      labels: <BlackGoldLocale, String>{
        BlackGoldLocale.ptBr: 'Loja Oficial',
        BlackGoldLocale.en: 'Official Store',
        BlackGoldLocale.es: 'Tienda Oficial',
      },
      descriptions: <BlackGoldLocale, String>{
        BlackGoldLocale.ptBr: 'Curadoria BlackGold de beleza feminina e vitrine oficial.',
        BlackGoldLocale.en: 'BlackGold women’s beauty curation and official storefront.',
        BlackGoldLocale.es: 'Curaduría BlackGold de belleza femenina y escaparate oficial.',
      },
      canonicalUrl: 'https://blackgold-beauty-finds-br.pages.dev/',
    ),
    BlackGoldEcoEntry(
      id: 'fitnexus_coach',
      group: BlackGoldEcoGroup.projects,
      icon: Icons.fitness_center_rounded,
      badge: 'SaaS Fitness',
      labels: <BlackGoldLocale, String>{
        BlackGoldLocale.ptBr: 'FitNexus Coach',
        BlackGoldLocale.en: 'FitNexus Coach',
        BlackGoldLocale.es: 'FitNexus Coach',
      },
      descriptions: <BlackGoldLocale, String>{
        BlackGoldLocale.ptBr: 'Sistema operacional do personal trainer: alunos, treinos e evolução.',
        BlackGoldLocale.en: 'Personal trainer operating system for clients, training and progress.',
        BlackGoldLocale.es: 'Sistema operativo del entrenador para alumnos, entrenamientos y progreso.',
      },
      canonicalUrl: 'https://projetoscosanostra.github.io/FitNexus_Coach_BlackGold/',
    ),
    BlackGoldEcoEntry(
      id: 'appevidex',
      group: BlackGoldEcoGroup.projects,
      icon: Icons.fact_check_rounded,
      badge: 'BlackGold',
      labels: <BlackGoldLocale, String>{
        BlackGoldLocale.ptBr: 'AppEvidex',
        BlackGoldLocale.en: 'AppEvidex',
        BlackGoldLocale.es: 'AppEvidex',
      },
      descriptions: <BlackGoldLocale, String>{
        BlackGoldLocale.ptBr: 'Ativo oficial BlackGold para evidência, processo e serviço digital.',
        BlackGoldLocale.en: 'Official BlackGold asset for evidence, process and digital services.',
        BlackGoldLocale.es: 'Activo oficial BlackGold para evidencia, proceso y servicios digitales.',
      },
      canonicalUrl: 'https://appevidex.pages.dev/',
    ),
    BlackGoldEcoEntry(
      id: 'preco_no_ponto',
      group: BlackGoldEcoGroup.projects,
      icon: Icons.price_check_rounded,
      badge: 'Play Store',
      labels: <BlackGoldLocale, String>{
        BlackGoldLocale.ptBr: 'Preço no Ponto',
        BlackGoldLocale.en: 'Preço no Ponto',
        BlackGoldLocale.es: 'Preço no Ponto',
      },
      descriptions: <BlackGoldLocale, String>{
        BlackGoldLocale.ptBr: 'Aplicativo utilitário BlackGold disponível na Google Play.',
        BlackGoldLocale.en: 'BlackGold utility app available on Google Play.',
        BlackGoldLocale.es: 'Aplicación utilitaria BlackGold disponible en Google Play.',
      },
      canonicalUrl: 'https://play.google.com/store/apps/details?id=br.com.lafamigliaplayworks.preconoponto&pcampaignid=web_share',
    ),
    BlackGoldEcoEntry(
      id: 'instagram',
      group: BlackGoldEcoGroup.social,
      icon: Icons.photo_camera_rounded,
      handle: '@cosanostra.blackgold',
      labels: <BlackGoldLocale, String>{
        BlackGoldLocale.ptBr: 'Instagram',
        BlackGoldLocale.en: 'Instagram',
        BlackGoldLocale.es: 'Instagram',
      },
      descriptions: <BlackGoldLocale, String>{
        BlackGoldLocale.ptBr: 'Criativos, novidades e presença visual oficial.',
        BlackGoldLocale.en: 'Creative work, updates and official visual presence.',
        BlackGoldLocale.es: 'Creatividades, novedades y presencia visual oficial.',
      },
      canonicalUrl: 'https://www.instagram.com/cosanostra.blackgold/',
    ),
    BlackGoldEcoEntry(
      id: 'tiktok',
      group: BlackGoldEcoGroup.social,
      icon: Icons.music_note_rounded,
      handle: '@cosanostraresolve',
      labels: <BlackGoldLocale, String>{
        BlackGoldLocale.ptBr: 'TikTok',
        BlackGoldLocale.en: 'TikTok',
        BlackGoldLocale.es: 'TikTok',
      },
      descriptions: <BlackGoldLocale, String>{
        BlackGoldLocale.ptBr: 'Canal oficial de vídeos curtos da Cosa Nostra BlackGold.',
        BlackGoldLocale.en: 'Official short-form video channel for Cosa Nostra BlackGold.',
        BlackGoldLocale.es: 'Canal oficial de videos cortos de Cosa Nostra BlackGold.',
      },
      canonicalUrl: 'https://www.tiktok.com/@cosanostraresolve?_r=1&_t=ZS-99Gu6t5IHQY',
    ),
    BlackGoldEcoEntry(
      id: 'kwai',
      group: BlackGoldEcoGroup.social,
      icon: Icons.video_library_rounded,
      handle: '@cosanostra.blackgold',
      labels: <BlackGoldLocale, String>{
        BlackGoldLocale.ptBr: 'Kwai',
        BlackGoldLocale.en: 'Kwai',
        BlackGoldLocale.es: 'Kwai',
      },
      descriptions: <BlackGoldLocale, String>{
        BlackGoldLocale.ptBr: 'Vídeos curtos e distribuição complementar.',
        BlackGoldLocale.en: 'Short-form video and complementary distribution.',
        BlackGoldLocale.es: 'Videos cortos y distribución complementaria.',
      },
      canonicalUrl: 'https://kwai-video.com/u/@cosanostra.blackgold/CwdSwBPA',
    ),
    BlackGoldEcoEntry(
      id: 'youtube',
      group: BlackGoldEcoGroup.social,
      icon: Icons.play_circle_fill_rounded,
      handle: '@cosanostra.blackgold',
      labels: <BlackGoldLocale, String>{
        BlackGoldLocale.ptBr: 'YouTube',
        BlackGoldLocale.en: 'YouTube',
        BlackGoldLocale.es: 'YouTube',
      },
      descriptions: <BlackGoldLocale, String>{
        BlackGoldLocale.ptBr: 'Vídeos, demonstrações e projetos do ecossistema.',
        BlackGoldLocale.en: 'Videos, demos and projects from the ecosystem.',
        BlackGoldLocale.es: 'Videos, demostraciones y proyectos del ecosistema.',
      },
      canonicalUrl: 'https://www.youtube.com/@cosanostra.blackgold',
    ),
    BlackGoldEcoEntry(
      id: 'facebook',
      group: BlackGoldEcoGroup.social,
      icon: Icons.facebook_rounded,
      handle: 'cosanostra.blackgold',
      labels: <BlackGoldLocale, String>{
        BlackGoldLocale.ptBr: 'Facebook',
        BlackGoldLocale.en: 'Facebook',
        BlackGoldLocale.es: 'Facebook',
      },
      descriptions: <BlackGoldLocale, String>{
        BlackGoldLocale.ptBr: 'Página social oficial da marca.',
        BlackGoldLocale.en: 'Official social page for the brand.',
        BlackGoldLocale.es: 'Página social oficial de la marca.',
      },
      canonicalUrl: 'https://www.facebook.com/cosanostra.blackgold/',
    ),
    BlackGoldEcoEntry(
      id: 'telegram',
      group: BlackGoldEcoGroup.social,
      icon: Icons.send_rounded,
      handle: '@BlackGoldSociety',
      labels: <BlackGoldLocale, String>{
        BlackGoldLocale.ptBr: 'Telegram',
        BlackGoldLocale.en: 'Telegram',
        BlackGoldLocale.es: 'Telegram',
      },
      descriptions: <BlackGoldLocale, String>{
        BlackGoldLocale.ptBr: 'Canal de comunidade e atualizações rápidas.',
        BlackGoldLocale.en: 'Community channel and quick updates.',
        BlackGoldLocale.es: 'Canal de comunidad y actualizaciones rápidas.',
      },
      canonicalUrl: 'https://t.me/BlackGoldSociety',
    ),
    BlackGoldEcoEntry(
      id: 'github',
      group: BlackGoldEcoGroup.professional,
      icon: Icons.code_rounded,
      handle: 'ProjetosCosaNostra',
      labels: <BlackGoldLocale, String>{
        BlackGoldLocale.ptBr: 'GitHub',
        BlackGoldLocale.en: 'GitHub',
        BlackGoldLocale.es: 'GitHub',
      },
      descriptions: <BlackGoldLocale, String>{
        BlackGoldLocale.ptBr: 'Repositórios, engenharia e projetos públicos.',
        BlackGoldLocale.en: 'Repositories, engineering and public projects.',
        BlackGoldLocale.es: 'Repositorios, ingeniería y proyectos públicos.',
      },
      canonicalUrl: 'https://github.com/ProjetosCosaNostra',
    ),
    BlackGoldEcoEntry(
      id: 'linkedin',
      group: BlackGoldEcoGroup.professional,
      icon: Icons.work_rounded,
      handle: 'Felipe Rosa Gomes',
      labels: <BlackGoldLocale, String>{
        BlackGoldLocale.ptBr: 'LinkedIn',
        BlackGoldLocale.en: 'LinkedIn',
        BlackGoldLocale.es: 'LinkedIn',
      },
      descriptions: <BlackGoldLocale, String>{
        BlackGoldLocale.ptBr: 'Perfil profissional, tecnologia, automação e projetos.',
        BlackGoldLocale.en: 'Professional profile, technology, automation and projects.',
        BlackGoldLocale.es: 'Perfil profesional, tecnología, automatización y proyectos.',
      },
      canonicalUrl: 'https://www.linkedin.com/in/felipe-projetoscosanostra/',
    ),
    BlackGoldEcoEntry(
      id: 'contact',
      group: BlackGoldEcoGroup.contact,
      icon: Icons.alternate_email_rounded,
      handle: contactEmail,
      labels: <BlackGoldLocale, String>{
        BlackGoldLocale.ptBr: 'Contato',
        BlackGoldLocale.en: 'Contact',
        BlackGoldLocale.es: 'Contacto',
      },
      descriptions: <BlackGoldLocale, String>{
        BlackGoldLocale.ptBr: 'Canal oficial para suporte, privacidade e projetos.',
        BlackGoldLocale.en: 'Official channel for support, privacy and projects.',
        BlackGoldLocale.es: 'Canal oficial para soporte, privacidad y proyectos.',
      },
      canonicalUrl: 'mailto:projetoscosanostra@gmail.com',
    ),
  ];

  static List<BlackGoldEcoEntry> byGroup(BlackGoldEcoGroup group) =>
      entries.where((BlackGoldEcoEntry entry) => entry.group == group).toList(growable: false);
}
