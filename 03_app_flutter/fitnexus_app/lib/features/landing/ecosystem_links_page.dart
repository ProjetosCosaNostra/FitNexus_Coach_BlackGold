import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/config/blackgold_ecosystem_manifest.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/blackgold_tokens.dart';
import '../shared/fitnexus_ui.dart';

class EcosystemLinksPage extends StatefulWidget {
  const EcosystemLinksPage({super.key});

  @override
  State<EcosystemLinksPage> createState() => _EcosystemLinksPageState();
}

class _EcosystemLinksPageState extends State<EcosystemLinksPage> {
  BlackGoldLocale _locale = BlackGoldLocale.ptBr;

  String _t(String pt, String en, String es) {
    switch (_locale) {
      case BlackGoldLocale.ptBr:
        return pt;
      case BlackGoldLocale.en:
        return en;
      case BlackGoldLocale.es:
        return es;
    }
  }

  Future<void> _openEntry(BlackGoldEcoEntry entry) async {
    final Uri uri = Uri.parse(entry.canonicalUrl);
    final bool launched = await launchUrl(
      uri,
      mode: LaunchMode.externalApplication,
    );

    if (!launched && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            _t(
              'Não foi possível abrir ${entry.label(_locale)} agora.',
              'Could not open ${entry.label(_locale)} right now.',
              'No fue posible abrir ${entry.label(_locale)} ahora.',
            ),
          ),
        ),
      );
    }
  }

  Future<void> _copyContact() async {
    await Clipboard.setData(
      const ClipboardData(text: BlackGoldEcosystemManifest.contactEmail),
    );
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          _t('Contato copiado.', 'Contact copied.', 'Contacto copiado.'),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return FitShell(
      maxWidth: 1180,
      showHeader: false,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          _EcosystemTopBar(
            locale: _locale,
            onLocaleChanged: (BlackGoldLocale value) {
              setState(() => _locale = value);
            },
          ),
          const SizedBox(height: BlackGoldSpace.xxl),
          _EcosystemHero(locale: _locale, translate: _t),
          const SizedBox(height: BlackGoldSpace.xxl),
          _EcosystemSection(
            title: _t('Projetos ativos', 'Active projects', 'Proyectos activos'),
            subtitle: _t(
              'Produtos e ativos oficiais do ecossistema BlackGold.',
              'Official products and assets from the BlackGold ecosystem.',
              'Productos y activos oficiales del ecosistema BlackGold.',
            ),
            entries: BlackGoldEcosystemManifest.byGroup(
              BlackGoldEcoGroup.projects,
            ),
            locale: _locale,
            onOpen: _openEntry,
            featured: true,
          ),
          const SizedBox(height: BlackGoldSpace.xxl),
          _EcosystemSection(
            title: _t('Redes oficiais', 'Official channels', 'Canales oficiales'),
            subtitle: _t(
              'Conteúdo, comunidade e presença digital oficial.',
              'Official content, community and digital presence.',
              'Contenido, comunidad y presencia digital oficial.',
            ),
            entries: BlackGoldEcosystemManifest.byGroup(
              BlackGoldEcoGroup.social,
            ),
            locale: _locale,
            onOpen: _openEntry,
          ),
          const SizedBox(height: BlackGoldSpace.xxl),
          _EcosystemSection(
            title: _t('Profissional', 'Professional', 'Profesional'),
            subtitle: _t(
              'Engenharia, perfil profissional e projetos públicos.',
              'Engineering, professional profile and public projects.',
              'Ingeniería, perfil profesional y proyectos públicos.',
            ),
            entries: BlackGoldEcosystemManifest.byGroup(
              BlackGoldEcoGroup.professional,
            ),
            locale: _locale,
            onOpen: _openEntry,
          ),
          const SizedBox(height: BlackGoldSpace.xxl),
          _ContactCallout(
            translate: _t,
            onOpen: () => _openEntry(
              BlackGoldEcosystemManifest.byGroup(
                BlackGoldEcoGroup.contact,
              ).first,
            ),
            onCopy: _copyContact,
          ),
          const SizedBox(height: BlackGoldSpace.xxl),
          _ManifestFooter(translate: _t),
        ],
      ),
    );
  }
}

class _EcosystemTopBar extends StatelessWidget {
  const _EcosystemTopBar({
    required this.locale,
    required this.onLocaleChanged,
  });

  final BlackGoldLocale locale;
  final ValueChanged<BlackGoldLocale> onLocaleChanged;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (BuildContext context, BoxConstraints constraints) {
        final bool compact = constraints.maxWidth < 720;
        final Widget brand = const _EcosystemBrand();
        final Widget controls = Wrap(
          spacing: BlackGoldSpace.xs,
          runSpacing: BlackGoldSpace.xs,
          crossAxisAlignment: WrapCrossAlignment.center,
          children: <Widget>[
            _LocaleSelector(locale: locale, onChanged: onLocaleChanged),
            OutlinedButton.icon(
              onPressed: () => Navigator.of(context).pushNamedAndRemoveUntil(
                '/',
                (Route<dynamic> route) => false,
              ),
              icon: const Icon(Icons.home_rounded, size: 17),
              label: Text(
                locale == BlackGoldLocale.ptBr
                    ? 'Início'
                    : locale == BlackGoldLocale.en
                        ? 'Home'
                        : 'Inicio',
              ),
            ),
          ],
        );

        if (compact) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              brand,
              const SizedBox(height: BlackGoldSpace.md),
              controls,
            ],
          );
        }

        return Row(
          children: <Widget>[
            brand,
            const Spacer(),
            controls,
          ],
        );
      },
    );
  }
}

class _EcosystemBrand extends StatelessWidget {
  const _EcosystemBrand();

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: <Widget>[
        Container(
          width: 44,
          height: 44,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: AppColors.card,
            borderRadius: BorderRadius.circular(BlackGoldRadius.card),
            border: Border.all(
              color: AppColors.gold.withValues(alpha: 0.58),
              width: BlackGoldStroke.regular,
            ),
            boxShadow: BlackGoldEffects.goldGlow,
          ),
          child: const Icon(
            Icons.hub_rounded,
            color: AppColors.goldSoft,
            size: 22,
          ),
        ),
        const SizedBox(width: BlackGoldSpace.sm),
        const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text.rich(
              TextSpan(
                children: <InlineSpan>[
                  TextSpan(
                    text: 'FIT',
                    style: TextStyle(color: AppColors.text),
                  ),
                  TextSpan(
                    text: 'NEXUS',
                    style: TextStyle(color: AppColors.goldSoft),
                  ),
                ],
              ),
              style: TextStyle(
                fontSize: 22,
                height: 1,
                fontWeight: FontWeight.w900,
                letterSpacing: 1.1,
              ),
            ),
            SizedBox(height: 5),
            Text(
              'B L A C K G O L D   E C O S Y S T E M',
              style: TextStyle(
                color: AppColors.muted,
                fontSize: 7.5,
                fontWeight: FontWeight.w700,
                letterSpacing: 1.15,
              ),
            ),
          ],
        ),
      ],
    );
  }
}

class _LocaleSelector extends StatelessWidget {
  const _LocaleSelector({
    required this.locale,
    required this.onChanged,
  });

  final BlackGoldLocale locale;
  final ValueChanged<BlackGoldLocale> onChanged;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 42,
      padding: const EdgeInsets.all(3),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(BlackGoldRadius.control),
        border: Border.all(
          color: AppColors.borderGold,
          width: BlackGoldStroke.hairline,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          _LanguageChip(
            label: 'PT',
            selected: locale == BlackGoldLocale.ptBr,
            onTap: () => onChanged(BlackGoldLocale.ptBr),
          ),
          _LanguageChip(
            label: 'EN',
            selected: locale == BlackGoldLocale.en,
            onTap: () => onChanged(BlackGoldLocale.en),
          ),
          _LanguageChip(
            label: 'ES',
            selected: locale == BlackGoldLocale.es,
            onTap: () => onChanged(BlackGoldLocale.es),
          ),
        ],
      ),
    );
  }
}

class _LanguageChip extends StatelessWidget {
  const _LanguageChip({
    required this.label,
    required this.selected,
    required this.onTap,
  });

  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      selected: selected,
      label: label,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(8),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 150),
          constraints: const BoxConstraints(minWidth: 42, minHeight: 34),
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: selected ? AppColors.gold : Colors.transparent,
            borderRadius: BorderRadius.circular(8),
          ),
          child: Text(
            label,
            style: TextStyle(
              color: selected ? Colors.black : AppColors.muted,
              fontSize: 11,
              fontWeight: FontWeight.w900,
            ),
          ),
        ),
      ),
    );
  }
}

class _EcosystemHero extends StatelessWidget {
  const _EcosystemHero({
    required this.locale,
    required this.translate,
  });

  final BlackGoldLocale locale;
  final String Function(String, String, String) translate;

  @override
  Widget build(BuildContext context) {
    return FitCard(
      highlight: true,
      padding: EdgeInsets.zero,
      child: LayoutBuilder(
        builder: (BuildContext context, BoxConstraints constraints) {
          final bool compact = constraints.maxWidth < 820;
          final Widget copy = Padding(
            padding: EdgeInsets.all(
              compact ? BlackGoldSpace.lg : BlackGoldSpace.xxl,
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                SectionLabel(
                  translate(
                    'Ecossistema BlackGold',
                    'BlackGold Ecosystem',
                    'Ecosistema BlackGold',
                  ),
                ),
                const SizedBox(height: BlackGoldSpace.md),
                Text.rich(
                  TextSpan(
                    children: <InlineSpan>[
                      TextSpan(
                        text: translate(
                          'Um sistema.\n',
                          'One system.\n',
                          'Un sistema.\n',
                        ),
                      ),
                      TextSpan(
                        text: translate(
                          'Todos os caminhos oficiais.',
                          'Every official path.',
                          'Todos los caminos oficiales.',
                        ),
                        style: const TextStyle(color: AppColors.goldSoft),
                      ),
                    ],
                  ),
                  style: Theme.of(context).textTheme.displayMedium,
                ),
                const SizedBox(height: BlackGoldSpace.md),
                Text(
                  translate(
                    'Escolha o destino. Nenhum redirecionamento oculto: projetos, loja, canais e contato permanecem separados e claros.',
                    'Choose the destination. No hidden redirects: projects, store, channels and contact stay separate and clear.',
                    'Elige el destino. Sin redirecciones ocultas: proyectos, tienda, canales y contacto permanecen separados y claros.',
                  ),
                  style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                        color: AppColors.muted,
                      ),
                ),
                const SizedBox(height: BlackGoldSpace.xl),
                Wrap(
                  spacing: BlackGoldSpace.xs,
                  runSpacing: BlackGoldSpace.xs,
                  children: <Widget>[
                    _HeroBadge(
                      icon: Icons.verified_rounded,
                      text: 'V${BlackGoldEcosystemManifest.version}',
                    ),
                    _HeroBadge(
                      icon: Icons.language_rounded,
                      text: locale == BlackGoldLocale.ptBr
                          ? 'PT-BR'
                          : locale == BlackGoldLocale.en
                              ? 'EN'
                              : 'ES',
                    ),
                    const _HeroBadge(
                      icon: Icons.lock_outline_rounded,
                      text: 'HTTPS',
                    ),
                  ],
                ),
              ],
            ),
          );

          final Widget artwork = ClipRRect(
            borderRadius: BorderRadius.only(
              topRight: Radius.circular(
                compact ? 0 : BlackGoldRadius.panel,
              ),
              bottomRight: const Radius.circular(BlackGoldRadius.panel),
              bottomLeft: Radius.circular(
                compact ? BlackGoldRadius.panel : 0,
              ),
            ),
            child: Container(
              constraints: BoxConstraints(
                minHeight: compact ? 260 : 390,
              ),
              decoration: const BoxDecoration(
                color: Color(0xFF050505),
              ),
              child: Image.asset(
                'assets/images/ecosistema_blackgold.png',
                fit: BoxFit.cover,
                alignment: Alignment.center,
                filterQuality: FilterQuality.high,
                errorBuilder: (
                  BuildContext context,
                  Object error,
                  StackTrace? stackTrace,
                ) {
                  return const _EcosystemArtworkFallback();
                },
              ),
            ),
          );

          if (compact) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: <Widget>[copy, artwork],
            );
          }

          return Row(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              Expanded(flex: 10, child: copy),
              Expanded(flex: 9, child: artwork),
            ],
          );
        },
      ),
    );
  }
}

class _HeroBadge extends StatelessWidget {
  const _HeroBadge({required this.icon, required this.text});

  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: const BoxConstraints(minHeight: 36),
      padding: const EdgeInsets.symmetric(
        horizontal: BlackGoldSpace.sm,
        vertical: BlackGoldSpace.xs,
      ),
      decoration: BoxDecoration(
        color: AppColors.gold.withValues(alpha: 0.07),
        borderRadius: BorderRadius.circular(BlackGoldRadius.pill),
        border: Border.all(
          color: AppColors.gold.withValues(alpha: 0.34),
          width: BlackGoldStroke.hairline,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          Icon(icon, color: AppColors.goldSoft, size: 15),
          const SizedBox(width: 6),
          Text(
            text,
            style: const TextStyle(
              color: AppColors.text,
              fontSize: 11,
              fontWeight: FontWeight.w800,
            ),
          ),
        ],
      ),
    );
  }
}

class _EcosystemArtworkFallback extends StatelessWidget {
  const _EcosystemArtworkFallback();

  @override
  Widget build(BuildContext context) {
    return const DecoratedBox(
      decoration: BoxDecoration(
        gradient: RadialGradient(
          center: Alignment.center,
          radius: 0.95,
          colors: <Color>[
            Color(0x44382109),
            Color(0xFF050505),
          ],
        ),
      ),
      child: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            Icon(Icons.hub_rounded, color: AppColors.goldSoft, size: 68),
            SizedBox(height: BlackGoldSpace.md),
            Text(
              'BLACKGOLD\nECOSYSTEM',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: AppColors.goldSoft,
                fontSize: 26,
                height: 0.95,
                fontWeight: FontWeight.w900,
                letterSpacing: 1.2,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _EcosystemSection extends StatelessWidget {
  const _EcosystemSection({
    required this.title,
    required this.subtitle,
    required this.entries,
    required this.locale,
    required this.onOpen,
    this.featured = false,
  });

  final String title;
  final String subtitle;
  final List<BlackGoldEcoEntry> entries;
  final BlackGoldLocale locale;
  final ValueChanged<BlackGoldEcoEntry> onOpen;
  final bool featured;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        FitPageTitle(
          eyebrow: featured ? 'BlackGold' : 'Links oficiais',
          title: title,
          description: subtitle,
        ),
        const SizedBox(height: BlackGoldSpace.lg),
        LayoutBuilder(
          builder: (BuildContext context, BoxConstraints constraints) {
            final int columns = constraints.maxWidth >= 980
                ? (featured ? 2 : 3)
                : constraints.maxWidth >= 650
                    ? 2
                    : 1;
            const double gap = BlackGoldSpace.sm;
            final double itemWidth =
                (constraints.maxWidth - gap * (columns - 1)) / columns;

            return Wrap(
              spacing: gap,
              runSpacing: gap,
              children: entries
                  .map(
                    (BlackGoldEcoEntry entry) => SizedBox(
                      width: itemWidth,
                      child: _EcosystemLinkCard(
                        entry: entry,
                        locale: locale,
                        onTap: () => onOpen(entry),
                        featured: featured,
                      ),
                    ),
                  )
                  .toList(growable: false),
            );
          },
        ),
      ],
    );
  }
}

class _EcosystemLinkCard extends StatelessWidget {
  const _EcosystemLinkCard({
    required this.entry,
    required this.locale,
    required this.onTap,
    required this.featured,
  });

  final BlackGoldEcoEntry entry;
  final BlackGoldLocale locale;
  final VoidCallback onTap;
  final bool featured;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      link: true,
      label: entry.label(locale),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(BlackGoldRadius.panel),
          child: FitCard(
            highlight: featured,
            padding: const EdgeInsets.all(BlackGoldSpace.lg),
            child: ConstrainedBox(
              constraints: BoxConstraints(minHeight: featured ? 144 : 126),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Container(
                    width: featured ? 48 : 42,
                    height: featured ? 48 : 42,
                    alignment: Alignment.center,
                    decoration: BoxDecoration(
                      color: AppColors.gold.withValues(alpha: 0.09),
                      borderRadius: BorderRadius.circular(BlackGoldRadius.card),
                      border: Border.all(
                        color: AppColors.gold.withValues(alpha: 0.42),
                        width: BlackGoldStroke.hairline,
                      ),
                    ),
                    child: Icon(
                      entry.icon,
                      color: AppColors.goldSoft,
                      size: featured ? 24 : 21,
                    ),
                  ),
                  const SizedBox(width: BlackGoldSpace.md),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Row(
                          children: <Widget>[
                            Expanded(
                              child: Text(
                                entry.label(locale),
                                style: TextStyle(
                                  color: AppColors.text,
                                  fontSize: featured ? 17 : 15,
                                  height: 1.15,
                                  fontWeight: FontWeight.w900,
                                ),
                              ),
                            ),
                            const Icon(
                              Icons.arrow_outward_rounded,
                              color: AppColors.gold,
                              size: 17,
                            ),
                          ],
                        ),
                        if (entry.badge != null || entry.handle != null) ...<Widget>[
                          const SizedBox(height: 6),
                          Text(
                            entry.badge ?? entry.handle!,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                              color: AppColors.goldSoft,
                              fontSize: 10.5,
                              fontWeight: FontWeight.w800,
                              letterSpacing: 0.2,
                            ),
                          ),
                        ],
                        const SizedBox(height: BlackGoldSpace.xs),
                        Text(
                          entry.description(locale),
                          maxLines: 3,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            color: AppColors.muted,
                            fontSize: 12.5,
                            height: 1.4,
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
      ),
    );
  }
}

class _ContactCallout extends StatelessWidget {
  const _ContactCallout({
    required this.translate,
    required this.onOpen,
    required this.onCopy,
  });

  final String Function(String, String, String) translate;
  final VoidCallback onOpen;
  final VoidCallback onCopy;

  @override
  Widget build(BuildContext context) {
    return FitCard(
      child: LayoutBuilder(
        builder: (BuildContext context, BoxConstraints constraints) {
          final bool compact = constraints.maxWidth < 700;
          final Widget copy = Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              SectionLabel(
                translate('Contato oficial', 'Official contact', 'Contacto oficial'),
              ),
              const SizedBox(height: BlackGoldSpace.sm),
              Text(
                BlackGoldEcosystemManifest.contactEmail,
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: BlackGoldSpace.xs),
              Text(
                translate(
                  'Suporte, privacidade, cobrança e projetos.',
                  'Support, privacy, billing and projects.',
                  'Soporte, privacidad, facturación y proyectos.',
                ),
                style: Theme.of(context).textTheme.bodyMedium,
              ),
            ],
          );
          final Widget actions = Wrap(
            spacing: BlackGoldSpace.xs,
            runSpacing: BlackGoldSpace.xs,
            children: <Widget>[
              OutlinedButton.icon(
                onPressed: onCopy,
                icon: const Icon(Icons.copy_rounded, size: 17),
                label: Text(translate('Copiar', 'Copy', 'Copiar')),
              ),
              GoldButton(
                label: translate('Enviar e-mail', 'Send email', 'Enviar correo'),
                icon: Icons.mail_rounded,
                onTap: onOpen,
              ),
            ],
          );

          if (compact) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                copy,
                const SizedBox(height: BlackGoldSpace.lg),
                actions,
              ],
            );
          }

          return Row(
            children: <Widget>[
              Expanded(child: copy),
              const SizedBox(width: BlackGoldSpace.xl),
              actions,
            ],
          );
        },
      ),
    );
  }
}

class _ManifestFooter extends StatelessWidget {
  const _ManifestFooter({required this.translate});

  final String Function(String, String, String) translate;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(
        horizontal: BlackGoldSpace.md,
        vertical: BlackGoldSpace.sm,
      ),
      decoration: BoxDecoration(
        color: AppColors.card.withValues(alpha: 0.58),
        borderRadius: BorderRadius.circular(BlackGoldRadius.control),
        border: Border.all(
          color: AppColors.borderGold.withValues(alpha: 0.48),
          width: BlackGoldStroke.hairline,
        ),
      ),
      child: Wrap(
        spacing: BlackGoldSpace.md,
        runSpacing: BlackGoldSpace.xs,
        alignment: WrapAlignment.spaceBetween,
        crossAxisAlignment: WrapCrossAlignment.center,
        children: <Widget>[
          const Text(
            'BLACKGOLD ECOSYSTEM • V${BlackGoldEcosystemManifest.version} • ${BlackGoldEcosystemManifest.effectiveDate}',
            style: TextStyle(
              color: AppColors.muted,
              fontSize: 10,
              fontWeight: FontWeight.w800,
              letterSpacing: 0.55,
            ),
          ),
          Text(
            translate(
              'Links oficiais • sem redirecionamento oculto',
              'Official links • no hidden redirect',
              'Enlaces oficiales • sin redirección oculta',
            ),
            style: const TextStyle(
              color: AppColors.goldSoft,
              fontSize: 10,
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }
}
