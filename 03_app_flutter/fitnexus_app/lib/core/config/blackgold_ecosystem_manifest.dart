import 'dart:convert';

import 'package:crypto/crypto.dart';
import 'package:flutter/services.dart';

class BlackGoldEcosystemManifest {
  BlackGoldEcosystemManifest({
    required this.schema,
    required this.version,
    required this.effectiveDate,
    required this.checksum,
    required this.entries,
    required this.isBootstrapFallback,
  });

  static const String assetPath =
      'assets/config/blackgold_ecosystem_manifest_v2_1.json';
  static const String expectedSchema = 'blackgold.ecosystem.manifest';
  static const String expectedVersion = '2.1';

  final String schema;
  final String version;
  final String effectiveDate;
  final String checksum;
  final List<BlackGoldEcosystemEntry> entries;
  final bool isBootstrapFallback;

  List<BlackGoldEcosystemEntry> get activeEntries {
    final items = entries.where((entry) => entry.status == 'active').toList();
    items.sort((a, b) => a.order.compareTo(b.order));
    return items;
  }

  List<BlackGoldEcosystemEntry> group(String group) => activeEntries
      .where((entry) => entry.group == group)
      .toList(growable: false);

  BlackGoldEcosystemEntry? byId(String id) {
    for (final entry in entries) {
      if (entry.id == id) return entry;
    }
    return null;
  }

  bool get checksumValid => checksum == _checksumFor(activeEntries);

  static Future<BlackGoldEcosystemManifest> load() async {
    try {
      final raw = await rootBundle.loadString(assetPath);
      final decoded = jsonDecode(raw);
      if (decoded is! Map<String, dynamic>) {
        throw const FormatException('Manifest root must be an object.');
      }
      final manifest = _fromMap(decoded, isBootstrapFallback: false);
      manifest.validate();
      return manifest;
    } catch (_) {
      final fallback = _bootstrap();
      fallback.validate();
      return fallback;
    }
  }

  static BlackGoldEcosystemManifest parseForTest(String raw) {
    final decoded = jsonDecode(raw);
    if (decoded is! Map<String, dynamic>) {
      throw const FormatException('Manifest root must be an object.');
    }
    final manifest = _fromMap(decoded, isBootstrapFallback: false);
    manifest.validate();
    return manifest;
  }

  void validate() {
    if (schema != expectedSchema) {
      throw FormatException('Unexpected ecosystem schema: $schema');
    }
    if (version != expectedVersion) {
      throw FormatException('Unexpected ecosystem version: $version');
    }
    if (entries.isEmpty) {
      throw const FormatException('Ecosystem manifest is empty.');
    }
    if (!checksumValid) {
      throw const FormatException('Ecosystem manifest checksum mismatch.');
    }

    const requiredLocales = <String>{'pt-BR', 'en', 'es'};
    const allowedStatuses = <String>{
      'active',
      'maintenance',
      'deprecated',
      'blocked',
    };

    final ids = <String>{};
    for (final entry in entries) {
      if (!ids.add(entry.id)) {
        throw FormatException('Duplicate ecosystem id: ${entry.id}');
      }
      if (!allowedStatuses.contains(entry.status)) {
        throw FormatException('Invalid status for ${entry.id}: ${entry.status}');
      }
      if (!requiredLocales.every(entry.labels.containsKey)) {
        throw FormatException('Missing labels for ${entry.id}');
      }
      if (!requiredLocales.every(entry.descriptions.containsKey)) {
        throw FormatException('Missing descriptions for ${entry.id}');
      }
      final uri = Uri.tryParse(entry.canonicalUrl);
      final scheme = uri?.scheme.toLowerCase();
      if (uri == null ||
          (scheme != 'https' && !(entry.type == 'contact' && scheme == 'mailto'))) {
        throw FormatException('Unsafe canonical URL for ${entry.id}');
      }
    }
  }

  static BlackGoldEcosystemManifest _fromMap(
    Map<String, dynamic> map, {
    required bool isBootstrapFallback,
  }) {
    final rawEntries = map['entries'];
    if (rawEntries is! List) {
      throw const FormatException('Manifest entries must be a list.');
    }
    return BlackGoldEcosystemManifest(
      schema: map['schema'] as String? ?? '',
      version: map['version'] as String? ?? '',
      effectiveDate: map['effective_date'] as String? ?? '',
      checksum: map['checksum'] as String? ?? '',
      entries: rawEntries
          .map((item) => BlackGoldEcosystemEntry.fromMap(
                Map<String, dynamic>.from(item as Map),
              ))
          .toList(growable: false),
      isBootstrapFallback: isBootstrapFallback,
    );
  }

  static String _checksumFor(List<BlackGoldEcosystemEntry> entries) {
    final sorted = entries.toList()..sort((a, b) => a.id.compareTo(b.id));
    final scope = sorted
        .map((entry) => '${entry.id}=${entry.canonicalUrl}')
        .join('\n');
    return sha256.convert(utf8.encode(scope)).toString();
  }

  // Bootstrap permitido pela Regra Oficial V2.1: somente destinos mínimos e
  // atuais para evitar tela vazia se o asset canônico não puder ser carregado.
  static BlackGoldEcosystemManifest _bootstrap() {
    const owner = 'Cosa Nostra BlackGold';
    const contact = 'projetoscosanostra@gmail.com';
    const fallback =
        'https://projetoscosanostra.github.io/FitNexus_Coach_BlackGold/#/links';
    final entries = <BlackGoldEcosystemEntry>[
      BlackGoldEcosystemEntry.bootstrap(
        id: 'official_store',
        type: 'store',
        group: 'projects',
        order: 10,
        pt: 'Loja Oficial',
        en: 'Official Store',
        es: 'Tienda Oficial',
        url: 'https://blackgold-beauty-finds-br.pages.dev/',
        fallbackUrl: fallback,
        owner: owner,
        contact: contact,
      ),
      BlackGoldEcosystemEntry.bootstrap(
        id: 'appevidex',
        type: 'app',
        group: 'projects',
        order: 20,
        pt: 'AppEvidex',
        en: 'AppEvidex',
        es: 'AppEvidex',
        url: 'https://appevidex.pages.dev/',
        fallbackUrl: fallback,
        owner: owner,
        contact: contact,
      ),
      BlackGoldEcosystemEntry.bootstrap(
        id: 'fitnexus_coach',
        type: 'app',
        group: 'projects',
        order: 30,
        pt: 'FitNexus Coach',
        en: 'FitNexus Coach',
        es: 'FitNexus Coach',
        url: 'https://projetoscosanostra.github.io/FitNexus_Coach_BlackGold/',
        fallbackUrl: fallback,
        owner: owner,
        contact: contact,
      ),
    ];
    return BlackGoldEcosystemManifest(
      schema: expectedSchema,
      version: expectedVersion,
      effectiveDate: '2026-09-05',
      checksum: _checksumFor(entries),
      entries: entries,
      isBootstrapFallback: true,
    );
  }
}

class BlackGoldEcosystemEntry {
  const BlackGoldEcosystemEntry({
    required this.id,
    required this.type,
    required this.group,
    required this.order,
    required this.labels,
    required this.descriptions,
    required this.canonicalUrl,
    required this.status,
    required this.markets,
    required this.locales,
    required this.lastVerifiedAt,
    required this.fallbackUrl,
    required this.owner,
    required this.contact,
  });

  factory BlackGoldEcosystemEntry.fromMap(Map<String, dynamic> map) {
    Map<String, String> strings(String key) => Map<String, String>.from(
          (map[key] as Map?)?.map(
                (key, value) => MapEntry(key.toString(), value.toString()),
              ) ??
              const <String, String>{},
        );

    List<String> list(String key) =>
        (map[key] as List? ?? const <dynamic>[])
            .map((item) => item.toString())
            .toList(growable: false);

    return BlackGoldEcosystemEntry(
      id: map['id'] as String? ?? '',
      type: map['type'] as String? ?? '',
      group: map['group'] as String? ?? '',
      order: (map['order'] as num?)?.toInt() ?? 999,
      labels: strings('labels'),
      descriptions: strings('descriptions'),
      canonicalUrl: map['canonical_url'] as String? ?? '',
      status: map['status'] as String? ?? '',
      markets: list('markets'),
      locales: list('locales'),
      lastVerifiedAt: map['last_verified_at'] as String? ?? '',
      fallbackUrl: map['fallback_url'] as String? ?? '',
      owner: map['owner'] as String? ?? '',
      contact: map['contact'] as String? ?? '',
    );
  }

  factory BlackGoldEcosystemEntry.bootstrap({
    required String id,
    required String type,
    required String group,
    required int order,
    required String pt,
    required String en,
    required String es,
    required String url,
    required String fallbackUrl,
    required String owner,
    required String contact,
  }) {
    final labels = <String, String>{'pt-BR': pt, 'en': en, 'es': es};
    return BlackGoldEcosystemEntry(
      id: id,
      type: type,
      group: group,
      order: order,
      labels: labels,
      descriptions: labels,
      canonicalUrl: url,
      status: 'active',
      markets: const <String>['global'],
      locales: const <String>['pt-BR', 'en', 'es'],
      lastVerifiedAt: '2026-09-05T00:00:00Z',
      fallbackUrl: fallbackUrl,
      owner: owner,
      contact: contact,
    );
  }

  final String id;
  final String type;
  final String group;
  final int order;
  final Map<String, String> labels;
  final Map<String, String> descriptions;
  final String canonicalUrl;
  final String status;
  final List<String> markets;
  final List<String> locales;
  final String lastVerifiedAt;
  final String fallbackUrl;
  final String owner;
  final String contact;

  String label(String localeTag) => _localized(labels, localeTag);
  String description(String localeTag) => _localized(descriptions, localeTag);

  static String _localized(Map<String, String> values, String localeTag) {
    if (values.containsKey(localeTag)) return values[localeTag]!;
    final language = localeTag.split('-').first;
    if (values.containsKey(language)) return values[language]!;
    return values['en'] ?? values.values.firstOrNull ?? '';
  }
}
