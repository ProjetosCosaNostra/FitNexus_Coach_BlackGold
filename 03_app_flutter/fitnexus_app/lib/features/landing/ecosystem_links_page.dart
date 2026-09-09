import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/config/blackgold_ecosystem_manifest.dart';

class EcosystemLinksPage extends StatefulWidget {
  const EcosystemLinksPage({super.key});

  @override
  State<EcosystemLinksPage> createState() => _EcosystemLinksPageState();
}

class _EcosystemLinksPageState extends State<EcosystemLinksPage> {
  static const String _localePreferenceKey = 'blackgold_ecosystem_locale';

  late final Future<BlackGoldEcosystemManifest> _manifestFuture;
  String? _preferredLocale;

  @override
  void initState() {
    super.initState();
    _manifestFuture = BlackGoldEcosystemManifest.load();
    _loadPreferredLocale();
  }

  Future<void> _loadPreferredLocale() async {
    final preferences = await SharedPreferences.getInstance();
    final value = preferences.getString(_localePreferenceKey);
    if (!mounted || value == null || !const {'pt-BR', 'en', 'es'}.contains(value)) {
      return;
    }
    setState(() => _preferredLocale = value);
  }

  Future<void> _setPreferredLocale(String value) async {
    final preferences = await SharedPreferences.getInstance();
    await preferences.setString(_localePreferenceKey, value);
    if (mounted) setState(() => _preferredLocale = value);
  }

  String _effectiveLocale(BuildContext context) {
    if (_preferredLocale != null) return _preferredLocale!;
    final language = Localizations.localeOf(context).languageCode.toLowerCase();
    if (language == 'pt') return 'pt-BR';
    if (language == 'es') return 'es';
    return 'en';
  }

  Future<void> _openEntry(
    BuildContext context,
    BlackGoldEcosystemEntry entry,
    String locale,
  ) async {
    final canonical = Uri.tryParse(entry.canonicalUrl);
    if (canonical != null && await launchUrl(canonical, mode: LaunchMode.platformDefault)) {
      return;
    }

    final fallback = Uri.tryParse(entry.fallbackUrl);
    if (fallback != null &&
        fallback.toString() != canonical?.toString() &&
        await launchUrl(fallback, mode: LaunchMode.platformDefault)) {
      return;
    }

    if (!context.mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(_copy(locale, 'unavailable')),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final locale = _effectiveLocale(context);
    return Scaffold(
      backgroundColor: _Palette.black,
      body: Stack(
        children: <Widget>[
          const _Background(),
          SafeArea(
            child: FutureBuilder<BlackGoldEcosystemManifest>(
              future: _manifestFuture,
              builder: (context, snapshot) {
                if (!snapshot.hasData) {
                  return const Center(
                    child: CircularProgressIndicator(color: _Palette.gold),
                  );
                }
                final manifest = snapshot.data!;
                return _Page(
                  manifest: manifest,
                  locale: locale,
                  onLocaleChanged: _setPreferredLocale,
                  onOpen: (entry) => _openEntry(context, entry, locale),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _Page extends StatelessWidget {
  const _Page({
    required this.manifest,
    required this.locale,
    required this.onLocaleChanged,
    required this.onOpen,
  });

  final BlackGoldEcosystemManifest manifest;
  final String locale;
  final ValueChanged<String> onLocaleChanged;
  final ValueChanged<BlackGoldEcosystemEntry> onOpen;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(20, 18, 20, 36),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 1120),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              _Header(
                locale: locale,
                version: manifest.version,
                onLocaleChanged: onLocaleChanged,
              ),
              const SizedBox(height: 28),
              _Hero(
                locale: locale,
                bootstrap: manifest.isBootstrapFallback,
              ),
              const SizedBox(height: 28),
              _Section(
                title: _copy(locale, 'projects'),
                entries: manifest.group('projects'),
                locale: locale,
                onOpen: onOpen,
              ),
              _Section(
                title: _copy(locale, 'social'),
                entries: manifest.group('social'),
                locale: locale,
                onOpen: onOpen,
              ),
              _Section(
                title: _copy(locale, 'community'),
                entries: <BlackGoldEcosystemEntry>[
                  ...manifest.group('community'),
                  ...manifest.group('professional'),
                ],
                locale: locale,
                onOpen: onOpen,
              ),
              _Section(
                title: _copy(locale, 'contact'),
                entries: manifest.group('contact'),
                locale: locale,
                onOpen: onOpen,
              ),
              const SizedBox(height: 6),
              _Footer(
                locale: locale,
                checksumOk: manifest.checksumValid,
                bootstrap: manifest.isBootstrapFallback,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({
    required this.locale,
    required this.version,
    required this.onLocaleChanged,
  });

  final String locale;
  final String version;
  final ValueChanged<String> onLocaleChanged;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final compact = constraints.maxWidth < 610;
        final brand = Row(
          children: <Widget>[
            Container(
              width: 54,
              height: 54,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(17),
                gradient: const LinearGradient(
                  colors: <Color>[_Palette.gold, _Palette.goldLight],
                ),
                boxShadow: <BoxShadow>[
                  BoxShadow(
                    color: _Palette.gold.withValues(alpha: .24),
                    blurRadius: 24,
                    offset: const Offset(0, 10),
                  ),
                ],
              ),
              child: const Icon(Icons.hub_rounded, color: Colors.black, size: 28),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text(
                    _copy(locale, 'title'),
                    style: const TextStyle(
                      color: _Palette.text,
                      fontSize: 23,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                  const SizedBox(height: 3),
                  Text(
                    '${_copy(locale, 'manifest')} v$version',
                    style: const TextStyle(
                      color: _Palette.muted,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ],
              ),
            ),
          ],
        );

        final actions = Row(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            _LocaleMenu(
              locale: locale,
              onChanged: onLocaleChanged,
            ),
            const SizedBox(width: 8),
            IconButton.filledTonal(
              tooltip: _copy(locale, 'home'),
              onPressed: () => Navigator.of(context).pushReplacementNamed('/'),
              icon: const Icon(Icons.home_rounded),
              style: IconButton.styleFrom(
                foregroundColor: _Palette.gold,
                minimumSize: const Size(48, 48),
              ),
            ),
          ],
        );

        if (compact) {
          return Column(
            children: <Widget>[
              brand,
              const SizedBox(height: 14),
              Align(alignment: Alignment.centerRight, child: actions),
            ],
          );
        }
        return Row(children: <Widget>[Expanded(child: brand), actions]);
      },
    );
  }
}

class _LocaleMenu extends StatelessWidget {
  const _LocaleMenu({required this.locale, required this.onChanged});

  final String locale;
  final ValueChanged<String> onChanged;

  @override
  Widget build(BuildContext context) {
    return PopupMenuButton<String>(
      tooltip: _copy(locale, 'language'),
      onSelected: onChanged,
      itemBuilder: (_) => const <PopupMenuEntry<String>>[
        PopupMenuItem(value: 'pt-BR', child: Text('PT-BR')),
        PopupMenuItem(value: 'en', child: Text('EN')),
        PopupMenuItem(value: 'es', child: Text('ES')),
      ],
      child: Container(
        constraints: const BoxConstraints(minWidth: 78, minHeight: 48),
        padding: const EdgeInsets.symmetric(horizontal: 13),
        decoration: BoxDecoration(
          color: _Palette.card,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: _Palette.gold.withValues(alpha: .38)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            const Icon(Icons.language_rounded, color: _Palette.gold, size: 20),
            const SizedBox(width: 8),
            Text(
              locale == 'pt-BR' ? 'PT' : locale.toUpperCase(),
              style: const TextStyle(
                color: _Palette.text,
                fontWeight: FontWeight.w800,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Hero extends StatelessWidget {
  const _Hero({required this.locale, required this.bootstrap});

  final String locale;
  final bool bootstrap;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(28),
        color: _Palette.card.withValues(alpha: .94),
        border: Border.all(color: _Palette.gold.withValues(alpha: .32)),
        boxShadow: <BoxShadow>[
          BoxShadow(
            color: Colors.black.withValues(alpha: .35),
            blurRadius: 32,
            offset: const Offset(0, 16),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: <Widget>[
              const _Badge(text: 'BLACKGOLD'),
              _Badge(text: _copy(locale, 'officialLinks')),
              if (bootstrap) _Badge(text: 'SAFE FALLBACK'),
            ],
          ),
          const SizedBox(height: 16),
          Text(
            _copy(locale, 'heroTitle'),
            style: const TextStyle(
              color: _Palette.text,
              fontSize: 32,
              height: 1.04,
              fontWeight: FontWeight.w900,
              letterSpacing: -.8,
            ),
          ),
          const SizedBox(height: 12),
          Text(
            _copy(locale, 'heroBody'),
            style: const TextStyle(
              color: _Palette.muted,
              fontSize: 15,
              height: 1.5,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}

class _Section extends StatelessWidget {
  const _Section({
    required this.title,
    required this.entries,
    required this.locale,
    required this.onOpen,
  });

  final String title;
  final List<BlackGoldEcosystemEntry> entries;
  final String locale;
  final ValueChanged<BlackGoldEcosystemEntry> onOpen;

  @override
  Widget build(BuildContext context) {
    if (entries.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(bottom: 26),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(
            '✦ $title',
            style: const TextStyle(
              color: _Palette.text,
              fontSize: 21,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 11),
          LayoutBuilder(
            builder: (context, constraints) {
              final columns = constraints.maxWidth >= 900
                  ? 3
                  : constraints.maxWidth >= 620
                      ? 2
                      : 1;
              const gap = 12.0;
              final width =
                  (constraints.maxWidth - gap * (columns - 1)) / columns;
              return Wrap(
                spacing: gap,
                runSpacing: gap,
                children: entries
                    .map(
                      (entry) => SizedBox(
                        width: width,
                        child: _EntryCard(
                          entry: entry,
                          locale: locale,
                          onTap: () => onOpen(entry),
                        ),
                      ),
                    )
                    .toList(growable: false),
              );
            },
          ),
        ],
      ),
    );
  }
}

class _EntryCard extends StatelessWidget {
  const _EntryCard({
    required this.entry,
    required this.locale,
    required this.onTap,
  });

  final BlackGoldEcosystemEntry entry;
  final String locale;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(19),
        child: Container(
          constraints: const BoxConstraints(minHeight: 112),
          padding: const EdgeInsets.all(15),
          decoration: BoxDecoration(
            color: _Palette.card,
            borderRadius: BorderRadius.circular(19),
            border: Border.all(color: _Palette.gold.withValues(alpha: .25)),
          ),
          child: Row(
            children: <Widget>[
              Container(
                width: 50,
                height: 50,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: const LinearGradient(
                    colors: <Color>[_Palette.gold, _Palette.goldDark],
                  ),
                ),
                child: Icon(_iconFor(entry), color: Colors.black, size: 25),
              ),
              const SizedBox(width: 13),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: <Widget>[
                    Text(
                      entry.label(locale),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: _Palette.text,
                        fontWeight: FontWeight.w900,
                        fontSize: 16,
                      ),
                    ),
                    const SizedBox(height: 5),
                    Text(
                      entry.description(locale),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: _Palette.muted,
                        height: 1.32,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              const Icon(Icons.arrow_outward_rounded, color: _Palette.gold),
            ],
          ),
        ),
      ),
    );
  }
}

class _Footer extends StatelessWidget {
  const _Footer({
    required this.locale,
    required this.checksumOk,
    required this.bootstrap,
  });

  final String locale;
  final bool checksumOk;
  final bool bootstrap;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(15),
      decoration: BoxDecoration(
        color: _Palette.card.withValues(alpha: .8),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: _Palette.gold.withValues(alpha: .18)),
      ),
      child: Row(
        children: <Widget>[
          Icon(
            checksumOk ? Icons.verified_rounded : Icons.warning_amber_rounded,
            color: checksumOk ? _Palette.gold : Colors.orangeAccent,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              bootstrap
                  ? _copy(locale, 'fallbackStatus')
                  : _copy(locale, 'verifiedStatus'),
              style: const TextStyle(
                color: _Palette.muted,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ],
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
      padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 7),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(999),
        color: _Palette.gold.withValues(alpha: .1),
        border: Border.all(color: _Palette.gold.withValues(alpha: .35)),
      ),
      child: Text(
        text,
        style: const TextStyle(
          color: _Palette.goldLight,
          fontSize: 11,
          fontWeight: FontWeight.w900,
          letterSpacing: .55,
        ),
      ),
    );
  }
}

class _Background extends StatelessWidget {
  const _Background();

  @override
  Widget build(BuildContext context) {
    return Positioned.fill(
      child: DecoratedBox(
        decoration: BoxDecoration(
          gradient: RadialGradient(
            center: const Alignment(.7, -.8),
            radius: 1.2,
            colors: <Color>[
              _Palette.gold.withValues(alpha: .12),
              _Palette.black,
              _Palette.black,
            ],
          ),
        ),
      ),
    );
  }
}

IconData _iconFor(BlackGoldEcosystemEntry entry) {
  switch (entry.id) {
    case 'official_store':
      return Icons.storefront_rounded;
    case 'appevidex':
      return Icons.verified_user_rounded;
    case 'fitnexus_coach':
      return Icons.fitness_center_rounded;
    case 'preco_no_ponto_play':
      return Icons.shopping_bag_rounded;
    case 'instagram':
      return Icons.photo_camera_rounded;
    case 'tiktok':
      return Icons.music_note_rounded;
    case 'kwai':
      return Icons.video_library_rounded;
    case 'youtube':
      return Icons.play_circle_fill_rounded;
    case 'facebook':
      return Icons.facebook_rounded;
    case 'telegram':
      return Icons.send_rounded;
    case 'github':
      return Icons.code_rounded;
    case 'linkedin':
      return Icons.work_rounded;
    case 'contact':
      return Icons.mail_rounded;
    default:
      return entry.type == 'app' ? Icons.apps_rounded : Icons.link_rounded;
  }
}

String _copy(String locale, String key) {
  const values = <String, Map<String, String>>{
    'title': {
      'pt-BR': 'Ecossistema BlackGold',
      'en': 'BlackGold Ecosystem',
      'es': 'Ecosistema BlackGold',
    },
    'manifest': {
      'pt-BR': 'Manifesto oficial',
      'en': 'Official manifest',
      'es': 'Manifiesto oficial',
    },
    'officialLinks': {
      'pt-BR': 'LINKS OFICIAIS',
      'en': 'OFFICIAL LINKS',
      'es': 'ENLACES OFICIALES',
    },
    'heroTitle': {
      'pt-BR': 'Um ecossistema. Vários ativos. Você escolhe o destino.',
      'en': 'One ecosystem. Multiple assets. You choose the destination.',
      'es': 'Un ecosistema. Varios activos. Tú eliges el destino.',
    },
    'heroBody': {
      'pt-BR': 'A navegação institucional agora usa destinos canônicos versionados, com fallback seguro e sem redirecionamento automático para a loja.',
      'en': 'Institutional navigation now uses versioned canonical destinations, safe fallback and no automatic store redirect.',
      'es': 'La navegación institucional usa destinos canónicos versionados, fallback seguro y sin redirección automática a la tienda.',
    },
    'projects': {'pt-BR': 'Projetos e loja', 'en': 'Projects and store', 'es': 'Proyectos y tienda'},
    'social': {'pt-BR': 'Redes oficiais', 'en': 'Official social channels', 'es': 'Redes oficiales'},
    'community': {'pt-BR': 'Comunidade e profissional', 'en': 'Community and professional', 'es': 'Comunidad y profesional'},
    'contact': {'pt-BR': 'Contato', 'en': 'Contact', 'es': 'Contacto'},
    'language': {'pt-BR': 'Idioma', 'en': 'Language', 'es': 'Idioma'},
    'home': {'pt-BR': 'Voltar para início', 'en': 'Back to home', 'es': 'Volver al inicio'},
    'unavailable': {'pt-BR': 'Destino temporariamente indisponível.', 'en': 'Destination temporarily unavailable.', 'es': 'Destino temporalmente no disponible.'},
    'verifiedStatus': {'pt-BR': 'Manifesto V2.1 carregado e checksum validado.', 'en': 'Manifest V2.1 loaded and checksum verified.', 'es': 'Manifiesto V2.1 cargado y checksum verificado.'},
    'fallbackStatus': {'pt-BR': 'Manifesto indisponível: bootstrap seguro V2.1 ativo.', 'en': 'Manifest unavailable: safe V2.1 bootstrap active.', 'es': 'Manifiesto no disponible: bootstrap seguro V2.1 activo.'},
  };
  return values[key]?[locale] ?? values[key]?['en'] ?? key;
}

class _Palette {
  static const black = Color(0xFF050505);
  static const card = Color(0xFF111111);
  static const gold = Color(0xFFE1B92F);
  static const goldLight = Color(0xFFFFD96A);
  static const goldDark = Color(0xFF9C7610);
  static const text = Color(0xFFF7F3E8);
  static const muted = Color(0xFFB6B0A1);
}
