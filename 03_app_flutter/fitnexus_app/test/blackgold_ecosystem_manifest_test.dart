import 'package:fitnexus_app/core/config/blackgold_ecosystem_manifest.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  Future<BlackGoldEcosystemManifest> loadManifest() async {
    final raw = await rootBundle.loadString(BlackGoldEcosystemManifest.assetPath);
    return BlackGoldEcosystemManifest.parseForTest(raw);
  }

  test('BlackGold ecosystem V2.1 matches canonical destinations', () async {
    final manifest = await loadManifest();
    expect(manifest.version, '2.1');
    expect(manifest.effectiveDate, '2026-09-05');

    final byId = <String, BlackGoldEcosystemEntry>{
      for (final entry in manifest.activeEntries) entry.id: entry,
    };
    expect(byId['official_store']?.canonicalUrl, 'https://blackgold-beauty-finds-br.pages.dev/');
    expect(byId['fitnexus_coach']?.canonicalUrl, 'https://projetoscosanostra.github.io/FitNexus_Coach_BlackGold/');
    expect(byId['appevidex']?.canonicalUrl, 'https://appevidex.pages.dev/');
    expect(byId['preco_no_ponto_play']?.canonicalUrl, contains('br.com.lafamigliaplayworks.preconoponto'));
    expect(byId['tiktok']?.canonicalUrl, contains('@cosanostraresolve'));
    expect(manifest.activeEntries.map((entry) => entry.canonicalUrl).join('\n'), isNot(contains('La_Famiglia_Links')));
  });

  test('every active ecosystem entry provides PT-BR EN and ES labels', () async {
    final manifest = await loadManifest();
    for (final entry in manifest.activeEntries) {
      expect(entry.labels.keys, containsAll(<String>['pt-BR', 'en', 'es']), reason: entry.id);
      expect(entry.descriptions.keys, containsAll(<String>['pt-BR', 'en', 'es']), reason: entry.id);
    }
  });

  test('projects remain first in canonical manifest order', () async {
    final manifest = await loadManifest();
    expect(
      manifest.group('projects').map((entry) => entry.id).toList(),
      <String>['official_store', 'appevidex', 'fitnexus_coach', 'preco_no_ponto_play'],
    );
  });
}