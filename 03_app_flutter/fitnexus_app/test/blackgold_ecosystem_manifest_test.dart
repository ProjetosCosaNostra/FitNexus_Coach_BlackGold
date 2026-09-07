import 'package:fitnexus_app/core/config/blackgold_ecosystem_manifest.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('BlackGold ecosystem bootstrap matches V2.1 canonical destinations', () {
    expect(BlackGoldEcosystemManifest.version, '2.1');
    expect(BlackGoldEcosystemManifest.effectiveDate, '2026-09-05');

    final Map<String, BlackGoldEcoEntry> byId = <String, BlackGoldEcoEntry>{
      for (final BlackGoldEcoEntry entry in BlackGoldEcosystemManifest.entries)
        entry.id: entry,
    };

    expect(
      byId['official_store']?.canonicalUrl,
      'https://blackgold-beauty-finds-br.pages.dev/',
    );
    expect(
      byId['fitnexus_coach']?.canonicalUrl,
      'https://projetoscosanostra.github.io/FitNexus_Coach_BlackGold/',
    );
    expect(
      byId['appevidex']?.canonicalUrl,
      'https://appevidex.pages.dev/',
    );
    expect(
      byId['preco_no_ponto']?.canonicalUrl,
      contains('br.com.lafamigliaplayworks.preconoponto'),
    );
    expect(byId['tiktok']?.handle, '@cosanostraresolve');
    expect(
      byId['tiktok']?.canonicalUrl,
      contains('@cosanostraresolve'),
    );
    expect(
      BlackGoldEcosystemManifest.entries
          .map((BlackGoldEcoEntry entry) => entry.canonicalUrl)
          .join('\n'),
      isNot(contains('La_Famiglia_Links')),
    );
  });

  test('every ecosystem entry provides PT-BR EN and ES labels', () {
    for (final BlackGoldEcoEntry entry in BlackGoldEcosystemManifest.entries) {
      expect(entry.labels.containsKey(BlackGoldLocale.ptBr), isTrue, reason: entry.id);
      expect(entry.labels.containsKey(BlackGoldLocale.en), isTrue, reason: entry.id);
      expect(entry.labels.containsKey(BlackGoldLocale.es), isTrue, reason: entry.id);
      expect(entry.descriptions.containsKey(BlackGoldLocale.ptBr), isTrue, reason: entry.id);
      expect(entry.descriptions.containsKey(BlackGoldLocale.en), isTrue, reason: entry.id);
      expect(entry.descriptions.containsKey(BlackGoldLocale.es), isTrue, reason: entry.id);
    }
  });

  test('projects remain first in the canonical bootstrap order', () {
    final List<BlackGoldEcoEntry> projects =
        BlackGoldEcosystemManifest.byGroup(BlackGoldEcoGroup.projects);

    expect(
      projects.map((BlackGoldEcoEntry entry) => entry.id).toList(),
      <String>[
        'official_store',
        'fitnexus_coach',
        'appevidex',
        'preco_no_ponto',
      ],
    );
  });
}
