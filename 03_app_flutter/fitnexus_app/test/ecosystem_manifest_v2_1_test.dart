import 'dart:io';

import 'package:fitnexus_app/core/config/blackgold_ecosystem_manifest.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('BlackGold ecosystem V2.1 canonical cutover is valid', () async {
    final raw = await rootBundle.loadString(
      BlackGoldEcosystemManifest.assetPath,
    );
    final manifest = BlackGoldEcosystemManifest.parseForTest(raw);

    expect(manifest.version, '2.1');
    expect(manifest.checksumValid, isTrue);

    final store = manifest.byId('official_store');
    expect(store, isNotNull);
    expect(store!.status, 'active');
    expect(store.canonicalUrl, 'https://blackgold-beauty-finds-br.pages.dev/');

    final appEvidex = manifest.byId('appevidex');
    expect(appEvidex, isNotNull);
    expect(appEvidex!.status, 'active');
    expect(appEvidex.canonicalUrl, 'https://appevidex.pages.dev/');

    final tiktok = manifest.byId('tiktok');
    expect(tiktok, isNotNull);
    expect(tiktok!.canonicalUrl, contains('@cosanostraresolve'));

    final legacyStore = manifest.byId('official_store_legacy_github_pages');
    expect(legacyStore, isNotNull);
    expect(legacyStore!.status, 'deprecated');
    expect(
      legacyStore.fallbackUrl,
      'https://blackgold-beauty-finds-br.pages.dev/',
    );

    for (final entry in manifest.activeEntries) {
      expect(entry.labels.keys, containsAll(<String>['pt-BR', 'en', 'es']));
      expect(
        entry.descriptions.keys,
        containsAll(<String>['pt-BR', 'en', 'es']),
      );
      final uri = Uri.parse(entry.canonicalUrl);
      expect(
        uri.scheme == 'https' ||
            (entry.type == 'contact' && uri.scheme == 'mailto'),
        isTrue,
        reason: entry.id,
      );
    }
  });

  test('Flutter source does not hardcode retired active destinations', () {
    const retiredStore =
        'https://projetoscosanostra.github.io/La_Famiglia_Links/';
    const retiredTikTokMarker = 'tiktok.com/@cosanostra.blackgold';

    final dartFiles = Directory('lib')
        .listSync(recursive: true)
        .whereType<File>()
        .where((file) => file.path.endsWith('.dart'));

    for (final file in dartFiles) {
      final source = file.readAsStringSync();
      expect(source.contains(retiredStore), isFalse, reason: file.path);
      expect(source.contains(retiredTikTokMarker), isFalse, reason: file.path);
    }
  });
}
